#!/usr/bin/env python3
"""Fetch sprint data from Google Sheets and output standardized JSON for weekly report generator.

Supports 3 formats (same templates as fetch_excel_data.py):
  - sprint_backlog: Sprint Backlog template (output of sprint-planning skill, US + Task hierarchy)
  - jira:           Jira export format
  - generic:        Any other header layout, best-effort column matching - as long as
                    the sheet has recognizable task/summary, status, estimate, and
                    start/due date columns

Usage:
    python fetch_gsheet_data.py --sheet-id <SPREADSHEET_ID> --service-account <path_to_key.json> \
        --sprint-name <Sprint Name> --today <YYYY-MM-DD> --output-dir <dir>

Requires: pip install gspread google-auth
"""
import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone, timedelta, date

try:
    import gspread
    from google.auth.transport.requests import AuthorizedSession
    from google.oauth2.service_account import Credentials
except ImportError:
    print("❌ Cần cài đặt thư viện: pip install gspread google-auth")
    sys.exit(1)

from network_utils import configure_session_proxy_fallback, timeout_for_url

GOOGLE_URL_HINT = "https://www.googleapis.com"


def authorize_gspread_client(service_account_path, scopes):
    """gspread + timeout + tự thử direct/proxy; cache mode OK cho request sau.
    Hỗ trợ cả User OAuth Token (tài khoản cá nhân/nội bộ) và Service Account JSON file.
    """
    user_token = (
        os.environ.get("GOOGLE_SHEETS_ACCESS_TOKEN")
        or os.environ.get("GOOGLE_ACCESS_TOKEN")
        or os.environ.get("GMAIL_ACCESS_TOKEN")
    )
    if user_token and user_token.strip():
        from google.oauth2.credentials import Credentials as UserCredentials
        creds = UserCredentials(user_token.strip())
    elif service_account_path and os.path.exists(service_account_path):
        creds = Credentials.from_service_account_file(service_account_path, scopes=scopes)
    else:
        if service_account_path:
            raise ValueError(f"Không tìm thấy file Service Account: {service_account_path}")
        raise ValueError(
            "Chưa có xác thực Google Sheets: vui lòng kết nối tài khoản Google trong Cài đặt Webapp hoặc cấu hình Service Account JSON."
        )

    session = AuthorizedSession(creds)
    original_request = session.request
    google_timeout = timeout_for_url(GOOGLE_URL_HINT)

    def request_with_timeout(*args, **kwargs):
        kwargs.setdefault("timeout", google_timeout)
        return original_request(*args, **kwargs)

    session.request = request_with_timeout
    configure_session_proxy_fallback(session, GOOGLE_URL_HINT, timeout=google_timeout)
    return gspread.Client(auth=creds, session=session)

VN_TZ = timezone(timedelta(hours=7))

# ──────────────────── DYNAMIC HEADER MATCHING ──────────────────
# Field → keyword patterns (ordered most → least specific)
# Build_column_index matches headers to fields by longest keyword match.
# This makes the script resilient to header variations.

SPRINT_FIELD_PATTERNS = {
    "us_id":           ["user story id", "story id", "us id", "id"],
    "module":          ["module/feature", "module/ feat", "module", "feature"],
    "description":     ["user story/description", "user story desc", "description",
                        "user story", "story description"],
    "story_point":     ["story point", "point", "sp"],
    "priority":        ["priority"],
    "task_name":       ["task"],
    "pic":             ["pic", "assignee", "person in charge", "person"],
    "status":          ["status"],
    "start_date":      ["start date", "start"],
    "due_date":        ["due date", "due", "end date"],
    "working_day":     ["working day", "work day", "workingdays", "workdays"],
    "effort_hour":     ["estimated effort (hour)", "estimated effort hour",
                        "effort (hour)", "effort hour", "hour", "man-hour"],
    "notes":           ["notes", "note", "comment"],
    "task_process":    ["task process", "process"],
    "task_priority":   ["task priority"],
    "complexity":      ["complexity", "task complexity"],
    "type_of_work":    ["type of work", "work type"],
    "estimated_manday": ["estimated effort (story manday)", "estimated effort",
                         "story manday", "manday", "man-day"],
    "task_manday":     ["estimated effort (task manday)", "task manday"],
}

JIRA_FIELD_PATTERNS = {
    "summary":          ["summary"],
    "id":               ["issue key", "key", "issue id", "id"],
    "issue_type":       ["issue type", "type"],
    "status":           ["status"],
    "priority":         ["priority"],
    "resolution":       ["resolution"],
    "assignee":         ["assignee name", "assignee"],
    "due_date":         ["due date", "due"],
    "description":      ["description", "desc"],
    "original_estimate": ["original estimate", "original estimate", "estimate"],
    "remaining_estimate": ["remaining estimate"],
    "time_spent":       ["time spent", "time spent"],
    "work_ratio":       ["work ratio"],
    "parent_key":       ["parent key", "parent"],
    "start_date":       ["start date", "start"],
    "task_process":     ["task process", "process"],
    "complexity":       ["complexity"],
}

# Fallback for any other template - as long as the sheet has recognizable
# task/summary, status, estimate, and start/due date columns.
GENERIC_FIELD_PATTERNS = {
    "id":               ["issue key", "us id", "story id", "task id", "key", "id"],
    "summary":          ["summary", "task name", "user story", "description", "task", "title"],
    "status":           ["status", "state"],
    "assignee":         ["assignee", "pic", "person in charge", "owner"],
    "priority":         ["priority"],
    "start_date":       ["start date", "start"],
    "due_date":         ["due date", "due", "end date", "deadline"],
    "estimate":         ["original estimate", "estimate", "effort (hour)", "effort hour",
                         "effort", "story point", "man-day", "manday", "hour"],
    "time_spent":       ["time spent"],
    "parent_key":       ["parent key", "parent"],
}

# ──────────────────── FORMAT DETECTION KEYWORDS ──────────────
SPRINT_KEYS = {
    "user story id", "module/feature", "module/ feature", "user story/description",
    "story point", "estimated effort", "task", "pic", "status",
    "start date", "due date", "working day", "task process", "task priority",
    "complexity", "notes", "type of work",
}

JIRA_KEYS = {
    "summary", "issue key", "issue type", "status", "priority",
    "resolution", "assignee", "due date", "description",
    "original estimate", "remaining estimate", "time spent",
    "work ratio", "parent key",
}


def build_column_index(headers, field_patterns):
    """Build a dynamic column index: field_name → column_index.
    
    Each header is matched against keyword patterns for each field.
    The longest matching pattern wins (more specific = better).
    Once a column is assigned to a field, it cannot be reused.
    """
    import re
    normalized = {}
    for i, h in enumerate(headers):
        if h:
            normalized[i] = re.sub(r'\s+', ' ', h.lower().replace("\n", " ").replace("\r", " ")).strip()
    
    col_idx = {}
    used = set()
    
    for field, patterns in field_patterns.items():
        best_score, best_col = 0, None
        for col, text in normalized.items():
            if col in used:
                continue
            for p in patterns:
                if p in text and len(p) > best_score:
                    best_score = len(p)
                    best_col = col
        if best_col is not None:
            col_idx[field] = best_col
            used.add(best_col)
    
    if col_idx:
        print(f"  → Column index: {dict(sorted(col_idx.items(), key=lambda x: x[1]))}")
    else:
        print("  → Warning: no columns matched! Using all headers as raw.")
    return col_idx


def detect_format(headers):
    """Detect Google Sheet format from headers. Returns 'sprint_backlog', 'jira', or 'generic'."""
    import re
    header_lower = set()
    for h in headers:
        if h:
            normalized = h.lower().replace("\n", " ").strip()
            normalized = re.sub(r'\s+', ' ', normalized)
            header_lower.add(normalized)

    sprint_matches = sum(1 for kw in SPRINT_KEYS for hl in header_lower if kw in hl)
    jira_matches = sum(1 for kw in JIRA_KEYS for hl in header_lower if kw in hl)

    print(f"  → format scores - sprint_backlog:{sprint_matches}  jira:{jira_matches}")

    if sprint_matches >= jira_matches and sprint_matches >= 6:
        return "sprint_backlog"
    elif jira_matches >= 5:
        return "jira"
    return "generic"

def parse_date_from_str(date_str):
    """Parse various date formats"""
    if not date_str or not isinstance(date_str, str):
        return None
    date_str = date_str.strip()
    if not date_str:
        return None
    
    formats = [
        "%d/%b/%y %I:%M %p",   # 03/Jul/26 12:00 AM
        "%d-%b-%Y",             # 10-Mar-2026
        "%d/%m/%Y",             # 10/03/2026
        "%Y-%m-%d",             # 2026-03-10
        "%d %b %Y",             # 10 Mar 2026
        "%m/%d/%Y",             # 03/10/2026
    ]
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue
    return None

def parse_estimate_to_hours(val):
    """Convert estimate value to hours (handles seconds string like '14400' or hours like '4h')"""
    if not val:
        return 0
    val = str(val).strip()
    if not val:
        return 0
    try:
        num = float(val.replace(",", ""))
        # If value is large (>1000), assume seconds
        if num > 1000:
            return round(num / 3600, 1)
        else:
            return num
    except ValueError:
        return 0

def parse_pct_done(val):
    """Parse percentage string like '100%' or '50%' to float"""
    if not val:
        return 0
    val = str(val).strip().replace("%", "")
    try:
        return float(val)
    except ValueError:
        return 0


def str_cell(val):
    """Safely convert a cell value to string, stripping whitespace."""
    if val is None:
        return ""
    return str(val).strip()


def safe_float(val):
    """Safely convert a cell value to float."""
    if val is None:
        return 0.0
    if isinstance(val, (int, float)):
        return float(val)
    s = str(val).strip().replace(",", "").replace(" ", "")
    try:
        return float(s)
    except ValueError:
        return 0.0


def _slugify(text):
    """Create a simple slug from text."""
    import re
    slug = re.sub(r'[^a-zA-Z0-9]+', '_', text.lower()).strip('_')
    return slug[:30] if slug else "task"


# ──────────────── FORMAT-SPECIFIC PARSERS ────────────────

def parse_sprint_backlog(rows, headers):
    """Parse Sprint Backlog format with US → Sub-task hierarchy using dynamic column index."""
    col = build_column_index(headers, SPRINT_FIELD_PATTERNS)
    if not col:
        print("  ⚠️ Không detect được cột, dùng raw headers")
        return parse_raw(rows, headers)

    stories = []
    current_story = None

    def cv(field, default=""):
        c = col.get(field)
        if c is not None and c < len(row):
            return str_cell(row[c])
        return default

    def cvn(field, default=0.0):
        c = col.get(field)
        if c is not None and c < len(row):
            return safe_float(row[c])
        return default

    for row_idx, row in enumerate(rows):
        if not any(str_cell(v) for v in row):
            continue

        us_id = cv("us_id")
        module = cv("module")
        desc = cv("description")
        task_name = cv("task_name")

        is_epic = (not us_id and module.upper().startswith("EPIC"))
        is_us = bool(us_id)

        if is_epic:
            print(f"  [EPIC] Row {row_idx+2}: {module[:60]}")
            current_story = None
            continue

        if is_us:
            priority_val = cv("priority", "2-Medium")
            story_point = cvn("story_point")
            effort_hour = cvn("effort_hour")

            current_story = {
                "id": us_id,
                "summary": desc[:200] if desc else f"{module} - {task_name}",
                "status": "To Do",
                "assignee": "Unassigned",
                "priority": priority_val,
                "issue_type": "Story",
                "start_date": None,
                "due_date": None,
                "task_process": "",
                "original_estimate_h": effort_hour if effort_hour > 0 else story_point * 8,
                "time_spent_h": 0,
                "remaining_estimate_h": 0,
                "parent_key": "",
                "pct_done": 0,
                "module": module,
                "subtasks": [],
            }

            if task_name:
                subtask = _parse_sb_task(row, us_id, col)
                if subtask:
                    current_story["subtasks"].append(subtask)

            stories.append(current_story)
            print(f"  [US]  {us_id}: {desc[:50] if desc else task_name[:50]}... ({len(current_story['subtasks'])} tasks)")

        elif task_name and current_story is not None:
            subtask = _parse_sb_task(row, current_story["id"], col)
            if subtask:
                current_story["subtasks"].append(subtask)

    print(f"\n✅ Sprint Backlog: {len(stories)} stories, {sum(len(s['subtasks']) for s in stories)} subtasks")
    return stories, []


def _parse_sb_task(row, parent_us_id, col):
    """Parse a single task row using dynamic column index."""
    def cv(field, default=""):
        c = col.get(field)
        return str_cell(row[c]) if c is not None and c < len(row) else default

    def cvn(field, default=0.0):
        c = col.get(field)
        return safe_float(row[c]) if c is not None and c < len(row) else default

    task_name = cv("task_name")
    if not task_name:
        return None

    pic = cv("pic", "Unassigned")
    status = cv("status", "To Do")
    effort_hour = cvn("effort_hour")
    task_process = cv("task_process")
    task_priority = cv("task_priority", "Medium")
    notes = cv("notes")
    working_day = cvn("working_day")

    c = col.get("start_date")
    start_dt = parse_date_from_str(row[c]) if c is not None and c < len(row) else None
    c = col.get("due_date")
    due_dt = parse_date_from_str(row[c]) if c is not None and c < len(row) else None

    status_lower = status.lower()
    if status_lower in ("done", "completed", "closed", "resolved"):
        pct_done = 100
    elif status_lower in ("in progress", "doing", "inreview", "in review"):
        pct_done = 50
    else:
        pct_done = 0

    if effort_hour == 0 and working_day > 0:
        effort_hour = working_day * 8

    return {
        "id": f"{parent_us_id}_{_slugify(task_name[:20])}",
        "summary": task_name[:200],
        "status": status,
        "assignee": pic,
        "priority": task_priority or "Medium",
        "issue_type": "Sub-task",
        "start_date": start_dt,
        "due_date": due_dt,
        "task_process": task_process,
        "original_estimate_h": effort_hour,
        "time_spent_h": 0,
        "remaining_estimate_h": effort_hour,
        "parent_key": parent_us_id,
        "pct_done": pct_done,
        "notes": notes,
        "working_day": working_day,
    }


def parse_jira(rows, headers):
    """Parse Jira export format using dynamic column index."""
    col = build_column_index(headers, JIRA_FIELD_PATTERNS)
    if not col:
        print("  ⚠️ Không detect được cột Jira, dùng raw headers")
        return parse_raw(rows, headers)
    
    stories, subtasks = [], []
    
    for row in rows:
        if not any(str_cell(v) for v in row):
            continue
        
        def cv(field, default=""):
            c = col.get(field)
            return str_cell(row[c]) if c is not None and c < len(row) else default
        
        def cvn(field, default=0.0):
            c = col.get(field)
            return safe_float(row[c]) if c is not None and c < len(row) else default
        
        issue_id = cv("id")
        issue_type = cv("issue_type")
        parent_key = cv("parent_key")
        status = cv("status", "To Do") or "To Do"
        summary = cv("summary")
        assignee = cv("assignee", "Unassigned") or "Unassigned"
        priority = cv("priority", "Medium") or "Medium"
        
        start_date = cv("start_date")
        due_date = cv("due_date")
        task_process = cv("task_process")
        
        original_estimate = parse_estimate_to_hours(cv("original_estimate"))
        time_spent = parse_estimate_to_hours(cv("time_spent"))
        remaining_estimate = parse_estimate_to_hours(cv("remaining_estimate"))
        pct_done = parse_pct_done(cv("work_ratio", "0%"))
        
        task = {
            "id": issue_id,
            "summary": summary[:200],
            "status": status,
            "assignee": assignee,
            "priority": priority,
            "issue_type": issue_type,
            "start_date": parse_date_from_str(start_date),
            "due_date": parse_date_from_str(due_date),
            "task_process": task_process,
            "original_estimate_h": original_estimate,
            "time_spent_h": time_spent,
            "remaining_estimate_h": remaining_estimate,
            "parent_key": parent_key,
            "pct_done": pct_done,
        }
        
        if issue_type in ("Story", "Epic"):
            stories.append(task)
        elif issue_type in ("Sub-task", "Subtask", "Subtask"):
            subtasks.append(task)
        elif issue_type == "Bug":
            stories.append(task)  # Treat bugs as stories
    
    print(f"\n✅ Jira format: {len(stories)} stories, {len(subtasks)} subtasks")
    return stories, subtasks


def parse_raw(rows, headers):
    """Generic fallback for any other template: best-effort column matching against
    GENERIC_FIELD_PATTERNS (task/summary, status, estimate, start/due date, assignee).
    Falls back to raw positional columns only if no header matches at all."""
    col = build_column_index(headers, GENERIC_FIELD_PATTERNS)
    stories = []

    if not col:
        print("  ⚠️ Không detect được cột nào, dùng vị trí cột thô")
        for row in rows:
            values = [str_cell(v) for v in row]
            if any(values):
                stories.append({
                    "id": values[0] if values else "",
                    "summary": values[1] if len(values) > 1 else "",
                    "status": values[2] if len(values) > 2 else "To Do",
                    "assignee": "Unassigned",
                    "priority": "Medium",
                    "issue_type": "Story",
                    "start_date": None,
                    "due_date": None,
                    "task_process": "",
                    "original_estimate_h": 0,
                    "time_spent_h": 0,
                    "remaining_estimate_h": 0,
                    "parent_key": "",
                    "pct_done": 0,
                })
        print(f"\n✅ Raw format: {len(stories)} stories")
        return stories, []

    for row in rows:
        if not any(str_cell(v) for v in row):
            continue

        def cv(field, default=""):
            c = col.get(field)
            return str_cell(row[c]) if c is not None and c < len(row) else default

        summary = cv("summary")
        if not summary:
            continue

        task_id = cv("id") or summary[:30]
        status = cv("status", "To Do") or "To Do"
        assignee = cv("assignee", "Unassigned") or "Unassigned"
        priority = cv("priority", "Medium") or "Medium"
        estimate_h = parse_estimate_to_hours(cv("estimate"))
        time_spent_h = parse_estimate_to_hours(cv("time_spent"))

        stories.append({
            "id": task_id,
            "summary": summary[:200],
            "status": status,
            "assignee": assignee,
            "priority": priority,
            "issue_type": "Story",
            "start_date": parse_date_from_str(cv("start_date")),
            "due_date": parse_date_from_str(cv("due_date")),
            "task_process": "",
            "original_estimate_h": estimate_h,
            "time_spent_h": time_spent_h,
            "remaining_estimate_h": max(estimate_h - time_spent_h, 0),
            "parent_key": cv("parent_key"),
            "pct_done": 100 if status.lower() in ("done", "completed", "closed", "resolved") else 0,
        })
    print(f"\n✅ Generic format: {len(stories)} stories")
    return stories, []


ISSUE_KEY_RE = re.compile(r"^([A-Z][A-Z0-9]+)-\d+$", re.IGNORECASE)


def infer_project_key(stories, subtasks):
    counts = {}
    for item in list(stories) + list(subtasks):
        issue_id = (item.get("id") or "").strip().upper()
        m = ISSUE_KEY_RE.match(issue_id)
        if m:
            key = m.group(1).upper()
            counts[key] = counts.get(key, 0) + 1
    if not counts:
        return None
    return max(counts.items(), key=lambda x: x[1])[0]


def load_sprint_info(path):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    info = data.get("sprint_info") or data
    sprint_start = data.get("sprint_start") or info.get("start_date")
    sprint_end = data.get("sprint_end") or info.get("end_date")
    if sprint_start:
        sprint_start = str(sprint_start)[:10]
    if sprint_end:
        sprint_end = str(sprint_end)[:10]
    return {
        "project_key": data.get("project_key"),
        "sprint_name": data.get("sprint_name") or info.get("sprint_name"),
        "sprint_start": sprint_start,
        "sprint_end": sprint_end,
        "sprint_info": info if isinstance(info, dict) else None,
    }


def fetch_and_process(sheet_id, service_account_path, sprint_name, today_str, output_dir, sprint_info_path=None, start_date=None, end_date=None):
    """Main function to fetch Google Sheet data and output standardized JSON"""
    today = date.fromisoformat(today_str) if today_str else date.today()
    
    # Authenticate
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    client = authorize_gspread_client(service_account_path, scope)
    
    # Open sheet
    print(f"📡 Đang kết nối Google Sheet: {sheet_id}")
    spreadsheet = client.open_by_key(sheet_id)
    worksheets = spreadsheet.worksheets()
    print(f"  → Sheet: {spreadsheet.title} ({len(worksheets)} worksheets)")
    
    # Process each worksheet (or just the first one)
    all_stories = []
    all_subtasks = []
    
    for ws in worksheets:
        print(f"\n📋 Đọc worksheet: {ws.title} ({ws.row_count} rows, {ws.col_count} cols)")
        data = ws.get_all_values()
        if len(data) < 2:
            print(f"  → Skipping (no data rows)")
            continue
        
        headers = data[0]
        rows = data[1:]  # skip header
        
        # Detect format + build dynamic column index
        fmt = detect_format(headers)
        print(f"  → Detected format: {fmt}")
        
        if fmt == "sprint_backlog":
            stories, _ = parse_sprint_backlog(rows, headers)
            all_stories.extend(stories)
        elif fmt == "jira":
            stories, subtasks = parse_jira(rows, headers)
            all_stories.extend(stories)
            all_subtasks.extend(subtasks)
        else:
            stories, _ = parse_raw(rows, headers)
            all_stories.extend(stories)
    
    print(f"\n✅ Đã đọc {len(all_stories)} stories, {len(all_subtasks)} subtasks")

    project_key = infer_project_key(all_stories, all_subtasks)
    sprint_meta = load_sprint_info(sprint_info_path) if sprint_info_path else {}
    if sprint_meta.get("project_key"):
        project_key = sprint_meta["project_key"]
    if sprint_meta.get("sprint_name") and not sprint_name:
        sprint_name = sprint_meta["sprint_name"]

    # Build standardized output
    output = {
        "source": "google_sheet",
        "sheet_id": sheet_id,
        "sheet_name": spreadsheet.title,
        "sprint_name": sprint_name or spreadsheet.title,
        "today": today.isoformat(),
        "exported_at": datetime.now(VN_TZ).isoformat(),
        "stories": [],
        "subtasks": all_subtasks,
    }
    if project_key:
        output["project_key"] = project_key
    if sprint_meta.get("sprint_start"):
        output["sprint_start"] = sprint_meta["sprint_start"]
    elif start_date:
        output["sprint_start"] = start_date
    if sprint_meta.get("sprint_end"):
        output["sprint_end"] = sprint_meta["sprint_end"]
    elif end_date:
        output["sprint_end"] = end_date
    if sprint_meta.get("sprint_info"):
        output["sprint_info"] = sprint_meta["sprint_info"]
    
    # Attach subtasks to stories (Jira format)
    subtask_map = {}
    for sub in all_subtasks:
        pk = sub.get("parent_key", "")
        if pk:
            if pk not in subtask_map:
                subtask_map[pk] = []
            subtask_map[pk].append(sub)
    
    for story in all_stories:
        story_copy = dict(story)
        if "subtasks" in story_copy:
            # Sprint Backlog format: subtasks already nested during parsing
            pass
        elif story_copy["id"] in subtask_map:
            story_copy["subtasks"] = subtask_map[story_copy["id"]]
        else:
            story_copy["subtasks"] = []
        output["stories"].append(story_copy)
    
    # Save
    os.makedirs(output_dir, exist_ok=True)
    out_path = os.path.join(output_dir, f"gsheet_data_{sprint_name.replace(' ', '_')}.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"✅ Đã xuất JSON: {out_path}")
    return out_path

def main():
    parser = argparse.ArgumentParser(description="Fetch Google Sheet data for weekly report")
    parser.add_argument("--sheet-id", required=True, help="Google Spreadsheet ID")
    parser.add_argument("--service-account", required=True, help="Path to service account JSON key")
    parser.add_argument("--sprint-name", default="Current Sprint", help="Sprint name hoặc Milestone")
    parser.add_argument("--start-date", default=None, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end-date", default=None, help="End date (YYYY-MM-DD)")
    parser.add_argument("--today", default=date.today().isoformat(), help="Report date (YYYY-MM-DD)")
    parser.add_argument("--output-dir", default=os.environ.get("REPORT_OUTPUT_DIR", "/mnt/Data/ai/pm"), help="Output directory")
    parser.add_argument(
        "--sprint-info",
        default=None,
        help="JSON từ jira_sprint_fetcher.py - merge sprint_start/sprint_end vào output",
    )
    args = parser.parse_args()

    fetch_and_process(
        args.sheet_id,
        args.service_account,
        args.sprint_name,
        args.today,
        args.output_dir,
        sprint_info_path=args.sprint_info,
        start_date=args.start_date,
        end_date=args.end_date,
    )

if __name__ == "__main__":
    main()

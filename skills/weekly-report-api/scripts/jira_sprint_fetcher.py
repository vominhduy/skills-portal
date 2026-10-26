#!/usr/bin/env python3
"""Fetch sprint metadata (and optionally issues) from Jira - project/sprint via CLI args."""
import argparse
import base64
import json
import os
import sys
import time
from typing import Dict, List, Optional

from network_utils import request_with_proxy_fallback, requests

JIRA_BASE = os.environ.get("JIRA_SITE", "https://foxproject.atlassian.net").rstrip("/")

# Jira agile API trả timestamp UTC (vd "2026-08-13T22:30:00.000Z" = 14/08 5h30 VN).
# Phải convert sang VN_TZ trước khi lấy date, nếu không ngày bị lùi 1 ngày.
from datetime import datetime as _dt, timezone as _tz, timedelta as _td
VN_TZ = _tz(_td(hours=7))


def parse_hours(seconds) -> float:
    if not seconds:
        return 0.0
    if isinstance(seconds, (int, float)):
        v = float(seconds)
        return round(v / 3600, 2) if v > 48 else v
    return 0.0


def parse_task_process(fields: Dict) -> str:
    raw = fields.get("customfield_10790")
    if isinstance(raw, dict):
        return raw.get("value") or raw.get("name") or ""
    return str(raw) if raw else ""


def get_auth_header(email: str, api_token: str) -> Dict:
    auth = f"{email}:{api_token}"
    encoded = base64.b64encode(auth.encode("utf-8")).decode("utf-8")
    return {
        "Authorization": f"Basic {encoded}",
        "Content-Type": "application/json",
    }


def verify_project_and_auth(headers: Dict, jira_base: str, project_key: str, email: str = "") -> tuple[str, Dict]:
    """
    Kiểm tra tính hợp lệ của token và dự án Jira trước khi truy vấn Board/Sprint/Issues.
    Trả về (status, data):
      - ("OK", project_dict): Token hợp lệ và dự án tồn tại, user có quyền truy cập.
      - ("PROJECT_NOT_FOUND", {}): Token hợp lệ nhưng mã dự án không tồn tại hoặc user không có quyền xem dự án.
      - ("AUTH_ERROR", {}): Token không hợp lệ hoặc đã hết hạn.
    """
    project_url = f"{jira_base}/rest/api/3/project/{project_key}"
    try:
        resp = request_with_proxy_fallback("GET", project_url, headers=headers)
        if resp.status_code == 200:
            return "OK", resp.json()
        if resp.status_code == 404:
            return "PROJECT_NOT_FOUND", {}

        # Nếu gặp 401 hoặc 403, kiểm tra /myself xem token có thực sự hết hạn hay do project
        if resp.status_code in (401, 403):
            myself_url = f"{jira_base}/rest/api/3/myself"
            m_resp = request_with_proxy_fallback("GET", myself_url, headers=headers)
            if m_resp.status_code == 200:
                # Token HOÀN TOÀN HỢP LỆ! Nhưng không tìm thấy hoặc không có quyền với project_key này
                return "PROJECT_NOT_FOUND", {}
            elif m_resp.status_code == 404:
                # Fallback API v2 myself
                m_resp2 = request_with_proxy_fallback("GET", f"{jira_base}/rest/api/2/myself", headers=headers)
                if m_resp2.status_code == 200:
                    return "PROJECT_NOT_FOUND", {}
            # myself cũng trả về 401/403 => Token thực sự không hợp lệ
            return "AUTH_ERROR", {}
    except Exception as e:
        print(f"  [WARN] Không thể kiểm tra dự án trước: {e}")

    return "OK", {}


def make_request(
    method: str,
    url: str,
    headers: Dict,
    json_data=None,
    params=None,
    max_retries=2,
) -> Dict:
    for attempt in range(max_retries):
        try:
            response = request_with_proxy_fallback(
                method, url, headers=headers, json=json_data,
                params=params,
            )
            if response.status_code == 429:
                wait = int(response.headers.get("Retry-After", 5))
                print(f"  [RATE LIMIT] Chờ {wait}s...")
                time.sleep(wait)
                continue
            if 400 <= response.status_code < 500 and response.status_code != 429:
                body = (response.text or "")[:800]
                print(f"  [HTTP {response.status_code}] {method} {url}")
                if body:
                    print(f"  [RESPONSE] {body}")
                # Không retry các lỗi 401, 403, 404
                if response.status_code in (401, 403, 404):
                    return {"error": f"[HTTP {response.status_code}] {body or response.reason}", "status_code": response.status_code}
            if 500 <= response.status_code < 600:
                wait = 2 ** attempt + 1
                print(f"  [SERVER ERROR] {response.status_code} - Chờ {wait}s...")
                time.sleep(wait)
                continue
            response.raise_for_status()
            return response.json() if response.content else {}
        except requests.exceptions.RequestException as e:
            if hasattr(e, "response") and e.response is not None:
                if e.response.status_code == 429:
                    continue
                if 400 <= e.response.status_code < 500:
                    body = (e.response.text or "")[:800]
                    if body:
                        print(f"  [RESPONSE] {body}")
                    if e.response.status_code in (401, 403, 404):
                        return {"error": f"[HTTP {e.response.status_code}] {body or str(e)}", "status_code": e.response.status_code}
                if 500 <= e.response.status_code < 600:
                    wait = 2 ** attempt + 1
                    time.sleep(wait)
                    continue
            if attempt < max_retries - 1:
                wait = 2 ** attempt + 1
                print(f"  [NETWORK ERROR] Chờ {wait}s...")
                time.sleep(wait)
                continue
            print(f"  [ERROR] {str(e)}")
            return {"error": str(e)}
    return {"error": "Max retries exceeded"}


def api_failed(result: Dict, context: str) -> bool:
    if not isinstance(result, dict):
        print(f"  ❌ {context}: phản hồi không hợp lệ")
        return True
    if result.get("error"):
        print(f"  ❌ {context}: {result['error']}")
        return True
    return False


def pick_sprint_match(candidates: List[Dict], keyword: str) -> Optional[Dict]:
    """Ưu tiên khớp tên sprint chính xác, sau đó partial match."""
    if not candidates:
        return None
    key = keyword.strip().lower()
    for s in candidates:
        if s.get("name", "").strip().lower() == key:
            return s
    for s in candidates:
        if key in s.get("name", "").lower():
            return s
    return None


def iso_date_only(value: Optional[str]) -> Optional[str]:
    """Lấy phần date (YYYY-MM-DD) từ ISO timestamp Jira, convert sang VN_TZ trước.

    Jira agile API trả UTC (vd "2026-08-13T22:30:00.000Z" = 14/08 5h30 VN).
    Cut naive [:10] sẽ ra 13/08 (sai) → phải astimezone(VN_TZ) rồi mới lấy date.
    """
    if not value:
        return None
    s = str(value).strip()
    if not s:
        return None
    try:
        if "T" in s:
            dt = _dt.fromisoformat(s.replace("Z", "+00:00"))
            if dt.tzinfo is None:
                # naive timestamp - Jira thường là UTC, gán UTC rồi convert.
                dt = dt.replace(tzinfo=_tz.utc)
            return dt.astimezone(VN_TZ).date().isoformat()
        # date-only (vd "2026-08-14") - giữ nguyên.
        return s[:10]
    except Exception:
        return s[:10]


def sprint_info_from_api(s: Dict, board_id=None, board_name=None) -> Dict:
    return {
        "board_id": board_id,
        "board_name": board_name,
        "sprint_id": s.get("id"),
        "sprint_name": s.get("name"),
        "sprint_state": s.get("state"),
        "start_date": s.get("startDate"),
        "end_date": s.get("endDate"),
        "goal": s.get("goal"),
    }


def fetch_sprint_by_id(headers: Dict, jira_base: str, sprint_id: int) -> Optional[Dict]:
    print(f"\n🔍 Đang lấy sprint ID {sprint_id}...")
    url = f"{jira_base}/rest/agile/1.0/sprint/{sprint_id}"
    result = make_request("GET", url, headers)
    if api_failed(result, f"Không lấy được sprint ID {sprint_id}") or not result.get("id"):
        return None
    info = sprint_info_from_api(result)
    print(f"  ✅ Sprint: {info['sprint_name']} ({info['start_date']} → {info['end_date']})")
    return info


def find_sprint(
    headers: Dict,
    jira_base: str,
    project_key: str,
    sprint_keyword: Optional[str] = None,
    sprint_id: Optional[int] = None,
) -> Optional[Dict]:
    if sprint_id:
        return fetch_sprint_by_id(headers, jira_base, sprint_id)

    keyword = (sprint_keyword or "").strip()
    if not keyword:
        print("❌ Cần --sprint-name hoặc --sprint-id")
        return None

    print(f"\n🔍 Đang tìm Board cho dự án {project_key}...")
    board_url = f"{jira_base}/rest/agile/1.0/board"
    board_result = make_request(
        "GET", board_url, headers,
        params={"projectKeyOrId": project_key, "maxResults": 50},
    )

    if api_failed(board_result, f"Không kết nối được Jira board API cho {project_key}"):
        err_msg = str(board_result.get("error", ""))
        if "401" in err_msg or "403" in err_msg:
            p_st, _ = verify_project_and_auth(headers, jira_base, project_key)
            if p_st == "PROJECT_NOT_FOUND":
                print(f"  ❌ LỖI MÃ DỰ ÁN: Mã dự án '{project_key}' không có board Agile hoặc tài khoản không có quyền truy cập.")
            elif p_st == "AUTH_ERROR":
                print(f"  ❌ LỖI XÁC THỰC JIRA: Token không hợp lệ hoặc đã hết hạn.")
        return None

    boards = board_result.get("values", [])
    if not boards:
        print(f"  ❌ Không tìm thấy board nào cho {project_key}!")
        return None

    print(f"  ✅ Tìm thấy {len(boards)} board:")
    for b in boards:
        print(
            f"     - Board ID: {b['id']} | Name: {b.get('name', 'N/A')} "
            f"| Type: {b.get('type', 'N/A')}"
        )

    target_board = boards[0]
    key_upper = project_key.upper()
    for b in boards:
        name = b.get("name", "").upper()
        if key_upper in name or "SCRUM" in name:
            target_board = b
            break

    board_id = target_board["id"]
    print(
        f"\n🔍 Đang tìm Sprint '{keyword}' trên Board {board_id} "
        f"({target_board.get('name')})..."
    )

    matches: List[Dict] = []
    for state in ["active,future", "closed"]:
        sprint_url = f"{jira_base}/rest/agile/1.0/board/{board_id}/sprint"
        sprint_result = make_request("GET", sprint_url, headers, params={"state": state})
        if api_failed(sprint_result, f"Không lấy được danh sách sprint (state={state})"):
            continue
        for s in sprint_result.get("values", []):
            sname = s.get("name", "")
            if keyword.lower() in sname.lower():
                matches.append(s)

    picked = pick_sprint_match(matches, keyword)
    if picked:
        sname = picked.get("name", "")
        print(
            f"  ✅ Tìm thấy Sprint: {sname} (ID: {picked['id']}) "
            f"- State: {picked.get('state')}"
        )
        return sprint_info_from_api(
            picked, board_id=board_id, board_name=target_board.get("name"),
        )

    print(f"  ⚠️ Không tìm thấy sprint chứa '{keyword}'!")
    print(f"\n📋 Các sprint hiện có trên Board {board_id}:")
    for state in ["active,future", "closed"]:
        sprint_url = f"{jira_base}/rest/agile/1.0/board/{board_id}/sprint"
        sprint_result = make_request("GET", sprint_url, headers, params={"state": state})
        for s in sprint_result.get("values", []):
            print(f"     - ID: {s['id']} | {s.get('name')} | State: {s.get('state')}")

    return None


ISSUE_FIELDS = [
    "summary", "status", "assignee", "issuetype", "priority", "parent",
    "customfield_10033", "customfield_10015", "duedate", "created", "updated",
    "timeoriginalestimate", "timespent", "customfield_10867",
    "customfield_10972", "customfield_10791", "customfield_10790",
]

SUBTASK_TYPE_NAMES = {"sub-task", "subtask", "sub task"}


def is_subtask_issue(issue_type: str, has_parent: bool) -> bool:
    """Nhận diện sub-task / task con của story (một số board dùng Task thay Sub-task)."""
    t = (issue_type or "").strip().lower()
    if t in SUBTASK_TYPE_NAMES:
        return True
    return has_parent and t in ("task", "technical task", "technical sub-task")


def issue_to_data(issue: Dict) -> Dict:
    fields = issue.get("fields", {})
    issue_type = fields.get("issuetype", {}).get("name", "Unknown")
    status = fields.get("status", {}).get("name", "Unknown")
    assignee = fields.get("assignee")
    assignee_name = assignee.get("displayName") if assignee else "Unassigned"
    parent = fields.get("parent")
    issue_data = {
        "key": issue["key"],
        "id": issue["key"],
        "summary": fields.get("summary", ""),
        "status": status,
        "assignee": assignee_name,
        "issue_type": issue_type,
        "priority": fields.get("priority", {}).get("name", "N/A") if fields.get("priority") else "N/A",
        "story_points": fields.get("customfield_10033"),
        "start_date": fields.get("customfield_10015"),
        "due_date": fields.get("duedate"),
        "created": fields.get("created"),
        "updated": fields.get("updated"),
        "effort_plan": fields.get("customfield_10867"),
        "task_process": parse_task_process(fields),
        "original_estimate": fields.get("timeoriginalestimate"),
        "time_spent": fields.get("timespent"),
        "original_estimate_h": parse_hours(fields.get("timeoriginalestimate")),
        "time_spent_h": parse_hours(fields.get("timespent")),
    }
    if parent:
        issue_data["parent_key"] = parent.get("key") if isinstance(parent, dict) else str(parent)
    return issue_data


def fetch_issues_by_jql(headers: Dict, jira_base: str, jql: str, label: str = "") -> List[Dict]:
    """Fetch issues qua POST /rest/api/3/search/jql (pagination: nextPageToken, không dùng startAt)."""
    url = f"{jira_base}/rest/api/3/search/jql"
    all_issues: List[Dict] = []
    next_token = None
    page_size = 100
    ctx = label or "JQL search"
    while True:
        payload: Dict = {
            "jql": jql,
            "maxResults": page_size,
            "fields": ISSUE_FIELDS,
        }
        if next_token:
            payload["nextPageToken"] = next_token
        result = make_request("POST", url, headers, json_data=payload)
        if api_failed(result, ctx):
            break
        batch = result.get("issues", [])
        all_issues.extend(batch)
        if result.get("isLast", True) or not result.get("nextPageToken"):
            break
        next_token = result.get("nextPageToken")
    return all_issues


def fetch_issues_by_jql_legacy(headers: Dict, jira_base: str, jql: str, label: str = "") -> List[Dict]:
    """Fallback: POST /rest/api/3/search (startAt) - một số site vẫn hoạt động."""
    url = f"{jira_base}/rest/api/3/search"
    all_issues: List[Dict] = []
    start_at = 0
    page_size = 100
    total = None
    ctx = label or "legacy JQL search"
    while total is None or start_at < total:
        payload = {
            "jql": jql,
            "startAt": start_at,
            "maxResults": page_size,
            "fields": ISSUE_FIELDS,
        }
        result = make_request("POST", url, headers, json_data=payload)
        if api_failed(result, ctx):
            break
        batch = result.get("issues", [])
        total = result.get("total", len(batch))
        all_issues.extend(batch)
        if not batch:
            break
        start_at += len(batch)
    return all_issues


def fetch_sprint_issues_agile(
    headers: Dict,
    jira_base: str,
    sprint_id: int,
    sprint_name: str,
) -> List[Dict]:
    """Primary: GET /rest/agile/1.0/sprint/{sprintId}/issue - đúng cho Scrum board."""
    print(f"\n🔍 Đang lấy issues sprint '{sprint_name}' (Agile API, sprint {sprint_id})...")
    url = f"{jira_base}/rest/agile/1.0/sprint/{sprint_id}/issue"
    all_issues: List[Dict] = []
    start_at = 0
    page_size = 100
    total = None
    while total is None or start_at < total:
        result = make_request(
            "GET", url, headers,
            params={"startAt": start_at, "maxResults": page_size},
        )
        if api_failed(result, "Agile sprint issues"):
            break
        batch = result.get("issues", [])
        total = result.get("total", len(batch))
        all_issues.extend(batch)
        if not batch:
            break
        start_at += len(batch)
    print(f"  ✅ Agile API: {len(all_issues)} issues")
    return all_issues


def issue_needs_field_enrich(issue: Dict) -> bool:
    fields = issue.get("fields") or {}
    return fields.get("timeoriginalestimate") is None and fields.get("customfield_10790") is None


def enrich_issues_by_keys(headers: Dict, jira_base: str, issue_keys: List[str]) -> Dict[str, Dict]:
    """Bổ sung fields đầy đủ khi Agile API trả về tối thiểu."""
    if not issue_keys:
        return {}
    enriched: Dict[str, Dict] = {}
    batch_size = 50
    unique_keys = sorted(set(issue_keys))
    for i in range(0, len(unique_keys), batch_size):
        batch = unique_keys[i:i + batch_size]
        jql = f"key in ({', '.join(batch)}) ORDER BY issuekey"
        batch_issues = fetch_issues_by_jql(headers, jira_base, jql, "enrich issue fields")
        if not batch_issues:
            batch_issues = fetch_issues_by_jql_legacy(headers, jira_base, jql, "enrich issue fields (legacy)")
        for issue in batch_issues:
            enriched[issue["key"]] = issue
    return enriched


def merge_enriched_issues(issues: List[Dict], enriched: Dict[str, Dict]) -> List[Dict]:
    if not enriched:
        return issues
    out: List[Dict] = []
    for issue in issues:
        key = issue.get("key")
        full = enriched.get(key)
        if full and issue_needs_field_enrich(issue):
            out.append(full)
        else:
            out.append(issue)
    return out


def fetch_sprint_issues(
    headers: Dict,
    jira_base: str,
    sprint_id: int,
    sprint_name: str,
) -> List[Dict]:
    """Lấy issues trong sprint: Agile API → JQL search/jql → legacy search."""
    issues = fetch_sprint_issues_agile(headers, jira_base, sprint_id, sprint_name)

    if not issues:
        print("  ⚠️ Agile API trả 0 - thử JQL search/jql...")
        jql = f"sprint = {sprint_id} ORDER BY issuekey"
        issues = fetch_issues_by_jql(headers, jira_base, jql, "sprint issues (JQL)")

    if not issues:
        print("  ⚠️ search/jql trả 0 - thử legacy /rest/api/3/search...")
        jql = f"sprint = {sprint_id} ORDER BY issuekey"
        issues = fetch_issues_by_jql_legacy(headers, jira_base, jql, "sprint issues (legacy)")

    if issues and any(issue_needs_field_enrich(i) for i in issues):
        print("  ℹ️ Bổ sung custom fields qua JQL key in (...)...")
        keys = [i["key"] for i in issues if i.get("key")]
        enriched = enrich_issues_by_keys(headers, jira_base, keys)
        issues = merge_enriched_issues(issues, enriched)

    print(f"  ✅ Tổng số issues trong sprint: {len(issues)}")
    return issues


def fetch_child_issues(
    headers: Dict,
    jira_base: str,
    parent_keys: List[str],
) -> List[Dict]:
    """Lấy sub-task/task con theo parent - nhiều sub-task không nằm trong sprint JQL."""
    if not parent_keys:
        return []
    unique_keys = sorted(set(parent_keys))
    print(f"\n🔍 Đang lấy sub-task theo parent ({len(unique_keys)} stories)...")
    all_children: List[Dict] = []
    batch_size = 50
    for i in range(0, len(unique_keys), batch_size):
        batch = unique_keys[i:i + batch_size]
        jql = f"parent in ({', '.join(batch)}) ORDER BY issuekey"
        children = fetch_issues_by_jql(headers, jira_base, jql, "child issues")
        if not children:
            children = fetch_issues_by_jql_legacy(headers, jira_base, jql, "child issues (legacy)")
        all_children.extend(children)
    print(f"  ✅ Sub-task/task con tìm thấy: {len(all_children)}")
    return all_children


def merge_issues_by_key(*issue_lists: List[Dict]) -> List[Dict]:
    merged: Dict[str, Dict] = {}
    for issues in issue_lists:
        for issue in issues or []:
            merged[issue["key"]] = issue
    return list(merged.values())


def analyze_sprint(issues: List[Dict]) -> Dict:
    """Analyze sprint issues and print report."""
    stories = []
    subtasks = []
    bugs = []
    others = []

    status_counts = {}
    assignee_counts = {}
    type_counts = {}

    for issue in issues:
        fields = issue.get("fields", {})
        issue_type = fields.get("issuetype", {}).get("name", "Unknown")
        status = fields.get("status", {}).get("name", "Unknown")
        assignee = fields.get("assignee")
        assignee_name = assignee.get("displayName") if assignee else "Unassigned"
        has_parent = bool(fields.get("parent"))

        type_counts[issue_type] = type_counts.get(issue_type, 0) + 1
        status_counts[status] = status_counts.get(status, 0) + 1
        assignee_counts[assignee_name] = assignee_counts.get(assignee_name, 0) + 1

        issue_data = issue_to_data(issue)

        if issue_type == "Story":
            stories.append(issue_data)
        elif is_subtask_issue(issue_type, has_parent):
            subtasks.append(issue_data)
        elif issue_type in ("Bug", "Defect"):
            bugs.append(issue_data)
        else:
            others.append(issue_data)

    total = len(issues)
    done_statuses = ["Done", "Closed", "Resolved", "Completed"]
    in_progress_statuses = ["In Progress", "In Review", "Review", "Testing", "QA"]

    print(f"\n{'=' * 80}")
    print("📊 BÁO CÁO SPRINT - Tổng quan")
    print(f"{'=' * 80}")
    print(f"\n📈 Tổng số issues: {total}")

    all_items = stories + subtasks + bugs
    done_all = sum(1 for i in all_items if i["status"] in done_statuses)
    pct_all = round(done_all / len(all_items) * 100, 1) if all_items else 0
    print(f"   Hoàn thành: {done_all}/{len(all_items)} ({pct_all}%)")

    return {
        "stories": stories,
        "subtasks": subtasks,
        "bugs": bugs,
        "others": others,
        "total": len(all_items),
        "done": done_all,
        "completion_pct": pct_all,
        "status_counts": status_counts,
        "assignee_counts": assignee_counts,
        "type_counts": type_counts,
        "done_statuses": done_statuses,
        "in_progress_statuses": in_progress_statuses,
    }


def fetch_issue_by_key(headers: Dict, jira_base: str, issue_key: str) -> Optional[Dict]:
    """Fetch single issue by key: /rest/api/3/issue/{key}."""
    url = f"{jira_base}/rest/api/3/issue/{issue_key}"
    result = make_request(
        "GET", url, headers,
        params={"fields": "summary,status,issuetype,duedate,created,updated,customfield_10015,customfield_10014,customfield_10033"},
    )
    if api_failed(result, f"Fetch parent issue {issue_key}") or not result.get("key"):
        return None
    return result


def extract_issue_dates(issue: Dict) -> tuple[Optional[str], Optional[str]]:
    """Lấy start date và due date từ issue."""
    fields = issue.get("fields") or {}
    start_raw = (
        fields.get("customfield_10015")
        or fields.get("customfield_10014")
        or fields.get("startdate")
        or fields.get("created")
    )
    due_raw = (
        fields.get("duedate")
        or fields.get("customfield_10033")
    )
    start_date = iso_date_only(start_raw)
    due_date = iso_date_only(due_raw)
    return start_date, due_date


def fetch_waterfall_issues(
    headers: Dict,
    jira_base: str,
    project_key: str,
    custom_jql: Optional[str] = None,
    fix_version: Optional[str] = None,
    epic_key: Optional[str] = None,
) -> List[Dict]:
    """Fetch issues cho dự án Waterfall qua JQL search."""
    if custom_jql:
        jql = custom_jql
    else:
        clauses = [f'project = "{project_key}"']
        if fix_version:
            clauses.append(f'fixVersion = "{fix_version}"')
        if epic_key:
            clauses.append(f'(parent = "{epic_key}" OR "Epic Link" = "{epic_key}")')
        jql = " AND ".join(clauses) + " ORDER BY updated DESC"

    print(f"\n🔍 Đang lấy issues Waterfall qua JQL: {jql}...")
    issues = fetch_issues_by_jql(headers, jira_base, jql, "waterfall issues (JQL)")
    if not issues:
        print("  ⚠️ search/jql trả 0 - thử legacy /rest/api/3/search...")
        issues = fetch_issues_by_jql_legacy(headers, jira_base, jql, "waterfall issues (legacy)")

    if issues and any(issue_needs_field_enrich(i) for i in issues):
        print("  ℹ️ Bổ sung custom fields qua JQL key in (...)...")
        keys = [i["key"] for i in issues if i.get("key")]
        enriched = enrich_issues_by_keys(headers, jira_base, keys)
        issues = merge_enriched_issues(issues, enriched)

    print(f"  ✅ Tổng số issues Waterfall: {len(issues)}")
    return issues


def write_json(path: str, data: Dict) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False, default=str)
    print(f"\n💾 Đã export dữ liệu ra: {path}")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Fetch Jira sprint/waterfall metadata and optionally issues",
    )
    parser.add_argument(
        "--project-key", required=True,
        help="Jira project key (VD: FSM, FCR)",
    )
    parser.add_argument(
        "--sprint-name",
        help="Tên sprint hoặc keyword (partial match, VD: 'Sprint 3'). Không bắt buộc nếu dùng --waterfall",
    )
    parser.add_argument(
        "--sprint-id", type=int,
        help="Sprint ID - bỏ qua tìm kiếm theo tên nếu đã biết ID",
    )
    parser.add_argument(
        "--waterfall", action="store_true",
        help="Chế độ Waterfall (không cần sprint, lấy issues qua JQL/project/parent)",
    )
    parser.add_argument(
        "--parent-key",
        help="Parent Request / Epic key (VD: 'FSM-20'). Tự động lấy Start Date, Due Date và toàn bộ task con của parent này",
    )
    parser.add_argument(
        "--start-date",
        help="Start date cho kỳ báo cáo / milestone (YYYY-MM-DD)",
    )
    parser.add_argument(
        "--end-date",
        help="End date cho kỳ báo cáo / milestone (YYYY-MM-DD)",
    )
    parser.add_argument(
        "--jql",
        help="Custom JQL filter cho luồng Waterfall (VD: 'fixVersion = \"v1.0\"')",
    )
    parser.add_argument(
        "--fix-version",
        help="Tên Fix Version / Release (dùng filter JQL trong Waterfall)",
    )
    parser.add_argument(
        "--epic-key",
        help="Epic key cha (alias của --parent-key)",
    )
    parser.add_argument(
        "--email",
        default=os.environ.get("JIRA_EMAIL"),
        help="Jira email (mặc định: JIRA_EMAIL)",
    )
    parser.add_argument(
        "--api-token",
        default=os.environ.get("JIRA_API_TOKEN") or os.environ.get("JIRA_TOKEN"),
        help="Jira API token (mặc định: JIRA_API_TOKEN hoặc JIRA_TOKEN)",
    )
    parser.add_argument(
        "--output-dir",
        default=os.environ.get("REPORT_OUTPUT_DIR", "."),
        help="Thư mục ghi JSON (mặc định: REPORT_OUTPUT_DIR)",
    )
    parser.add_argument(
        "--fetch-issues", action="store_true",
        help="Lấy thêm danh sách issues (mặc định: chỉ sprint/waterfall info/dates)",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    jira_base = JIRA_BASE

    if not args.email or not args.api_token:
        print("❌ Thiếu credential. Truyền --email/--api-token hoặc set JIRA_EMAIL, JIRA_API_TOKEN.")
        sys.exit(1)

    parent_key = args.parent_key or args.epic_key
    is_waterfall = args.waterfall or bool(parent_key) or (not args.sprint_id and not args.sprint_name)

    headers = get_auth_header(args.email, args.api_token)
    print(f"✅ Kết nối Jira với user: {args.email}")
    print(f"   Base URL: {jira_base}")
    print(f"   Project  : {args.project_key}")
    print(f"   Mode     : {'Waterfall (không sprint)' if is_waterfall else 'Agile/Scrum (có sprint)'}")

    # 1. Kiểm tra tính hợp lệ của Token và Dự án trước khi chạy pipeline
    print(f"\n🔍 Đang kiểm tra tính hợp lệ của dự án '{args.project_key}' trên Jira...")
    project_status, project_info = verify_project_and_auth(headers, jira_base, args.project_key, args.email)
    if project_status == "PROJECT_NOT_FOUND":
        print(f"\n❌ LỖI MÃ DỰ ÁN:")
        print(f"   Mã dự án '{args.project_key}' không tồn tại trên hệ thống Jira hoặc tài khoản '{args.email}' chưa được cấp quyền truy cập vào dự án này.")
        print(f"   👉 Vui lòng kiểm tra lại mã dự án (VD: FCR, FSM, ISC, SAL...) và thử lại!")
        sys.exit(2)
    elif project_status == "AUTH_ERROR":
        print(f"\n❌ LỖI XÁC THỰC JIRA (HTTP 401 Unauthorized):")
        print(f"   Thông tin xác thực (Jira Email / API Token) của tài khoản '{args.email}' chưa được cấu hình hoặc đã hết hạn.")
        print(f"   👉 Vui lòng vào mục Cài đặt cá nhân để cập nhật token hợp lệ.")
        sys.exit(1)
    elif project_info.get("name"):
        print(f"  ✅ Dự án hợp lệ: {project_info.get('name')} ({args.project_key})")

    if is_waterfall:
        sprint_name = args.sprint_name
        today_dt = _dt.now(VN_TZ).date()
        sprint_start = args.start_date
        sprint_end = args.end_date
        parent_info = None

        if parent_key:
            print(f"\n🔍 Đang lấy thông tin Parent Request / Epic: {parent_key}...")
            parent_issue = fetch_issue_by_key(headers, jira_base, parent_key)
            if parent_issue:
                p_fields = parent_issue.get("fields") or {}
                p_summary = p_fields.get("summary", "")
                p_start, p_due = extract_issue_dates(parent_issue)
                print(f"  ✅ Parent: [{parent_key}] {p_summary}")
                print(f"     Start Date : {p_start or 'N/A'}")
                print(f"     Due Date   : {p_due or 'N/A'}")
                parent_info = {
                    "key": parent_key,
                    "summary": p_summary,
                    "start_date": p_start,
                    "due_date": p_due,
                }
                if not sprint_start and p_start:
                    sprint_start = p_start
                if not sprint_end and p_due:
                    sprint_end = p_due
                if not sprint_name:
                    sprint_name = f"[{parent_key}] {p_summary}" if p_summary else parent_key
            else:
                print(f"  ⚠️ Không tìm thấy issue {parent_key}, sẽ filter theo JQL parent = '{parent_key}'")
                if not sprint_name:
                    sprint_name = parent_key

        if not sprint_name:
            sprint_name = f"FixVersion_{args.fix_version}" if args.fix_version else "Waterfall"
        if not sprint_start:
            sprint_start = (today_dt - _td(days=14)).isoformat()
        if not sprint_end:
            sprint_end = (today_dt + _td(days=14)).isoformat()

        sprint_info = {
            "board_id": None,
            "board_name": "Waterfall Project",
            "sprint_id": None,
            "sprint_name": sprint_name,
            "sprint_state": "active",
            "start_date": sprint_start,
            "end_date": sprint_end,
            "is_waterfall": True,
            "parent_info": parent_info,
        }

        export_data = {
            "project_key": args.project_key,
            "jira_base": jira_base,
            "sprint_name": sprint_name,
            "sprint_start": sprint_start,
            "sprint_end": sprint_end,
            "sprint_info": sprint_info,
            "is_waterfall": True,
            "parent_key": parent_key,
            "parent_info": parent_info,
        }

        if args.fetch_issues:
            waterfall_issues = fetch_waterfall_issues(
                headers,
                jira_base,
                args.project_key,
                custom_jql=args.jql,
                fix_version=args.fix_version,
                epic_key=parent_key,
            )
            story_keys = [
                issue["key"]
                for issue in waterfall_issues
                if issue.get("fields", {}).get("issuetype", {}).get("name") in ("Story", "Epic", "Task")
            ]
            child_issues = fetch_child_issues(headers, jira_base, story_keys)
            issues = merge_issues_by_key(waterfall_issues, child_issues)
            analysis = analyze_sprint(issues)
            export_data["source"] = "jira"
            export_data["analysis"] = {
                "total": analysis["total"],
                "done": analysis["done"],
                "completion_pct": analysis["completion_pct"],
            }
            export_data["issues"] = issues
            export_data["subtasks"] = analysis["subtasks"]
            export_data["bugs"] = analysis["bugs"]
            subtask_map: Dict[str, List] = {}
            for sub in analysis["subtasks"]:
                pk = sub.get("parent_key", "")
                if pk:
                    subtask_map.setdefault(pk, []).append(sub)
            export_data["stories"] = [
                {**story, "subtasks": subtask_map.get(story["key"], [])}
                for story in analysis["stories"]
            ]

        safe_name = str(sprint_name).replace(" ", "_").replace("/", "-")
        suffix = "sprint_data" if args.fetch_issues else "sprint_info"
        out_name = f"{args.project_key}_{safe_name}_{suffix}.json"
        out_path = os.path.join(args.output_dir, out_name)
        write_json(out_path, export_data)

        if sprint_start and sprint_end:
            print(f"\n📅 Dùng cho generate_report_from_json:")
            print(f"   --sprint-start {sprint_start} --sprint-end {sprint_end}")
            print(f"   --project-key {args.project_key} --sprint-name \"{sprint_name}\"")
        return

    # Luồng Scrum/Agile bình thường
    if not args.sprint_id and not args.sprint_name:
        print("❌ Cần --sprint-name hoặc --sprint-id (hoặc dùng --waterfall)")
        sys.exit(1)

    sprint_info = find_sprint(
        headers,
        jira_base,
        args.project_key,
        sprint_keyword=args.sprint_name,
        sprint_id=args.sprint_id,
    )
    if not sprint_info:
        print(f"\n❌ Không tìm thấy sprint cho project {args.project_key}!")
        sys.exit(1)

    print("\n📋 Sprint Info:")
    print(f"   Board     : {sprint_info.get('board_name', 'N/A')} (ID: {sprint_info.get('board_id', 'N/A')})")
    print(f"   Sprint    : {sprint_info['sprint_name']} (ID: {sprint_info['sprint_id']})")
    print(f"   State     : {sprint_info.get('sprint_state')}")
    print(f"   Start     : {sprint_info.get('start_date', 'N/A')}")
    print(f"   End       : {sprint_info.get('end_date', 'N/A')}")

    sprint_start = iso_date_only(sprint_info.get("start_date"))
    sprint_end = iso_date_only(sprint_info.get("end_date"))

    export_data = {
        "project_key": args.project_key,
        "jira_base": jira_base,
        "sprint_name": sprint_info["sprint_name"],
        "sprint_start": sprint_start,
        "sprint_end": sprint_end,
        "sprint_info": sprint_info,
    }

    if args.fetch_issues:
        sprint_issues = fetch_sprint_issues(
            headers,
            jira_base,
            sprint_info["sprint_id"],
            sprint_info["sprint_name"],
        )
        story_keys = [
            issue["key"]
            for issue in sprint_issues
            if issue.get("fields", {}).get("issuetype", {}).get("name") == "Story"
        ]
        child_issues = fetch_child_issues(headers, jira_base, story_keys)
        issues = merge_issues_by_key(sprint_issues, child_issues)
        analysis = analyze_sprint(issues)
        export_data["source"] = "jira"
        export_data["analysis"] = {
            "total": analysis["total"],
            "done": analysis["done"],
            "completion_pct": analysis["completion_pct"],
        }
        export_data["issues"] = issues
        export_data["subtasks"] = analysis["subtasks"]
        export_data["bugs"] = analysis["bugs"]
        subtask_map: Dict[str, List] = {}
        for sub in analysis["subtasks"]:
            pk = sub.get("parent_key", "")
            if pk:
                subtask_map.setdefault(pk, []).append(sub)
        export_data["stories"] = [
            {**story, "subtasks": subtask_map.get(story["key"], [])}
            for story in analysis["stories"]
        ]

    safe_name = str(sprint_info["sprint_name"]).replace(" ", "_").replace("/", "-")
    suffix = "sprint_data" if args.fetch_issues else "sprint_info"
    out_name = f"{args.project_key}_{safe_name}_{suffix}.json"
    out_path = os.path.join(args.output_dir, out_name)
    write_json(out_path, export_data)

    # In dates dạng dễ copy sang generate_report_from_json
    if sprint_start and sprint_end:
        print(f"\n📅 Dùng cho generate_report_from_json:")
        print(f"   --sprint-start {sprint_start} --sprint-end {sprint_end}")
        print(f"   --project-key {args.project_key} --sprint-name \"{sprint_info['sprint_name']}\"")
        print(f"   Hoặc: fetch_gsheet_data.py ... --sprint-info {out_path}")


if __name__ == "__main__":
    main()

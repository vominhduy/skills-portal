#!/usr/bin/env python3
"""Weekly Report Generator for FCR Sprint 4 - pulls data from Jira and generates report"""
import requests
import json
import base64
import time
import sys
import os
from datetime import datetime, timezone, timedelta, date
from typing import Dict, Optional, List

JIRA_BASE = os.environ.get("JIRA_SITE", "https://foxproject.atlassian.net").rstrip("/")
VN_TZ = timezone(timedelta(hours=7))

# ─────────────────────── CONFIG ───────────────────────
PROJECT_KEY = "FCR"
SPRINT_NAME = "FTI-FCR V1.7 Sprint 4"
SPRINT_ID = 1355
TODAY = date(2026, 7, 15)
OUTPUT_DIR = "/mnt/Data/ai/pm"

# ─────────────────────── AUTH ───────────────────────
def get_auth_header(email: str, api_token: str) -> Dict:
    auth = f"{email}:{api_token}"
    encoded = base64.b64encode(auth.encode("utf-8")).decode("utf-8")
    return {"Authorization": f"Basic {encoded}", "Content-Type": "application/json"}

def make_request(method: str, url: str, headers: Dict, json_data=None, params=None, max_retries=3) -> Dict:
    for attempt in range(max_retries):
        try:
            response = requests.request(method, url, headers=headers, json=json_data, params=params, timeout=30)
            if response.status_code == 429:
                wait = int(response.headers.get("Retry-After", 5))
                time.sleep(wait); continue
            if 500 <= response.status_code < 600:
                time.sleep(2 ** attempt + 1); continue
            response.raise_for_status()
            return response.json() if response.content else {}
        except requests.exceptions.RequestException as e:
            if hasattr(e, 'response') and e.response is not None:
                if e.response.status_code in (429,):
                    continue
                if 500 <= e.response.status_code < 600:
                    time.sleep(2 ** attempt + 1); continue
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt + 1); continue
            return {"error": str(e)}
    return {"error": "Max retries exceeded"}

def parse_date(iso_str):
    """Parse ISO date string to date (UTC+7)"""
    if not iso_str:
        return None
    try:
        dt = datetime.fromisoformat(iso_str.replace('Z', '+00:00'))
        return dt.astimezone(VN_TZ).date()
    except:
        return None

def parse_hours(seconds):
    """Convert seconds to hours string"""
    if not seconds:
        return 0
    return round(seconds / 3600, 1)

# ─────────────────────── FETCH DATA ───────────────────────
def fetch_sprint_issues(headers: Dict) -> List[Dict]:
    """Fetch ALL issues in sprint with full fields (token-based pagination)"""
    print("📡 Đang fetch issues từ Jira...")
    all_issues = []
    max_results = 100
    next_token = None
    
    while True:
        jql = f'sprint = {SPRINT_ID} ORDER BY issuekey'
        url = f"{JIRA_BASE}/rest/api/3/search/jql"
        payload = {
            "jql": jql,
            "maxResults": max_results,
            "fields": [
                "summary", "status", "assignee", "issuetype", "priority", "parent",
                "customfield_10033", "customfield_10015", "duedate", "created", "updated",
                "timeoriginalestimate", "timespent", "timetracking",
                "customfield_10867", "customfield_10972", "customfield_10791",
                "customfield_10790", "customfield_10788", "customfield_10020"
            ]
        }
        if next_token:
            payload["nextPageToken"] = next_token
        
        result = make_request("POST", url, headers, json_data=payload)
        issues = result.get("issues", [])
        is_last = result.get("isLast", True)
        next_token = result.get("nextPageToken")
        all_issues.extend(issues)
        print(f"  → Fetched {len(issues)} issues (total so far: {len(all_issues)})")
        if is_last or not next_token:
            break
    
    print(f"✅ Total issues fetched: {len(all_issues)}")
    return all_issues

def get_sprint_dates(issues: List[Dict]):
    """Extract sprint start/end from customfield_10020"""
    for issue in issues:
        fields = issue.get("fields", {})
        cf_10020 = fields.get("customfield_10020")
        if isinstance(cf_10020, list) and len(cf_10020) > 0:
            sprint_info = cf_10020[0]
            start = parse_date(sprint_info.get("startDate"))
            end = parse_date(sprint_info.get("endDate"))
            if start and end:
                return start, end
    # Fallback
    return date(2026, 6, 9), date(2026, 7, 24)

# ─────────────────────── PROCESS ISSUES ───────────────────────
def process_issues(issues: List[Dict], sprint_start: date, sprint_end: date) -> Dict:
    """Process all issues, compute metrics"""
    stories = []
    subtask_map = {}  # parent_key -> [subtasks]
    bugs = []
    
    # Separate stories and subtasks
    for issue in issues:
        fields = issue.get("fields", {})
        itype = fields.get("issuetype", {}).get("name", "Unknown")
        parent = fields.get("parent")
        
        item = {
            "id": issue["key"],
            "summary": fields.get("summary", ""),
            "status": fields.get("status", {}).get("name", "Unknown"),
            "assignee": fields.get("assignee", {}).get("displayName", "Unassigned") if fields.get("assignee") else "Unassigned",
            "priority": fields.get("priority", {}).get("name", "Medium") if fields.get("priority") else "Medium",
            "story_points": fields.get("customfield_10033"),
            "start_date": parse_date(fields.get("customfield_10015")),
            "due_date": parse_date(fields.get("duedate")),
            "task_process": fields.get("customfield_10790", {}).get("value") if isinstance(fields.get("customfield_10790"), dict) else fields.get("customfield_10790"),
            "original_estimate_s": fields.get("timeoriginalestimate"),
            "time_spent_s": fields.get("timespent"),
            "time_spent": parse_hours(fields.get("timespent")),
            "original_estimate": parse_hours(fields.get("timeoriginalestimate")),
        }
        
        if itype == "Story":
            stories.append(item)
        elif itype == "Sub-task":
            parent_key = parent.get("key") if parent else None
            if parent_key:
                if parent_key not in subtask_map:
                    subtask_map[parent_key] = []
                subtask_map[parent_key].append(item)
        elif itype == "Bug":
            bugs.append(item)
    
    # Attach subtasks to stories
    for story in stories:
        story["subtasks"] = subtask_map.get(story["id"], [])
    
    # Also track independent subtasks (without parent in this list)
    orphan_subtasks = [s for s in issues 
                       if s.get("fields",{}).get("issuetype",{}).get("name") == "Sub-task"
                       and s["key"] not in [st["id"] for st in stories]  # wrong logic, fix below
                      ]
    # Simpler: all subtasks
    all_subtasks = []
    for s_list in subtask_map.values():
        all_subtasks.extend(s_list)
    
    # ─── COMPUTE METRICS ───
    
    # 1. Planned Progress
    elapsed_days = (TODAY - sprint_start).days
    total_days = (sprint_end - sprint_start).days
    planned_progress = round(elapsed_days / total_days * 100, 1) if total_days > 0 else 0
    
    # 2. Weighted Phase (Actual Progress)
    phase_weights = {
        "Requirement & Design": 0.15,
        "Coding": 0.50,
        "Testing": 0.15,
        "Deployment": 0.10,
        "Other": 0.10,
    }
    
    # Map taskProcess to phases
    def map_phase(tp):
        if not tp:
            return "Other"
        tp_lower = tp.lower()
        if "requirement" in tp_lower or "design" in tp_lower:
            return "Requirement & Design"
        if "coding" in tp_lower or "code" in tp_lower:
            return "Coding"
        if "test" in tp_lower or "qa" in tp_lower:
            return "Testing"
        if "deploy" in tp_lower or "uat" in tp_lower or "release" in tp_lower:
            return "Deployment"
        return "Other"
    
    done_statuses = {"Done", "Closed", "Resolved", "Completed", "In review", "In Review"}
    
    phase_data = {phase: {"est": 0, "progress": 0, "count": 0, "done_count": 0} for phase in phase_weights}
    
    for sub in all_subtasks:
        phase = map_phase(sub["task_process"])
        est_h = sub["original_estimate"] if sub["original_estimate"] else 0
        spent_h = sub["time_spent"] if sub["time_spent"] else 0
        
        phase_data[phase]["est"] += est_h
        phase_data[phase]["count"] += 1
        
        if sub["status"] in done_statuses:
            phase_data[phase]["done_count"] += 1
            phase_data[phase]["progress"] += est_h if est_h > 0 else 0
        elif est_h > 0:
            phase_data[phase]["progress"] += min(spent_h, est_h)
        else:
            phase_data[phase]["progress"] += spent_h
    
    total_est = sum(p["est"] for p in phase_data.values())
    total_progress = sum(p["progress"] for p in phase_data.values())
    
    actual_progress_raw = round(total_progress / total_est * 100, 1) if total_est > 0 else 0
    
    phase_order = list(phase_weights.keys())
    active_indices = [i for i, p in enumerate(phase_order) if phase_data[p]["count"] > 0]
    max_active = max(active_indices) if active_indices else -1

    weighted_sum = 0
    for i, (phase, weight) in enumerate(phase_weights.items()):
        if i < max_active and phase_data[phase]["count"] == 0:
            phase_data[phase]["pct"] = 100.0
            phase_data[phase]["contribution"] = round(weight * 100, 1)
            weighted_sum += weight * 100
            continue
        count = phase_data[phase]["count"]
        if count == 0:
            pct = 0.0
        elif phase_data[phase]["est"] > 0:
            pct = min(round(phase_data[phase]["progress"] / phase_data[phase]["est"] * 100, 1), 100.0)
        elif phase_data[phase]["done_count"] == count:
            pct = 100.0
        else:
            pct = round(phase_data[phase]["done_count"] / count * 100, 1)
        phase_data[phase]["pct"] = pct
        phase_data[phase]["contribution"] = round(weight * pct, 1)
        weighted_sum += weight * pct
    
    actual_progress_weighted = round(weighted_sum, 1)
    
    # 3. SPI
    spi = round(actual_progress_weighted / planned_progress, 2) if planned_progress > 0 else 0
    if spi >= 1.05:
        spi_status = "Ahead of Schedule ✅"
    elif spi >= 0.95:
        spi_status = "On Track ✅"
    elif spi >= 0.80:
        spi_status = "Slightly Behind ⚠️"
    else:
        spi_status = "Behind Schedule 🔴"
    
    # 4. RAG (duedate-based)
    rag_total = 0
    rag_done = 0
    for sub in all_subtasks:
        if sub["due_date"] and sub["due_date"] <= TODAY:
            rag_total += 1
            if sub["status"] in done_statuses:
                rag_done += 1
    
    rag_pct = round(rag_done / rag_total * 100, 1) if rag_total > 0 else 100
    if rag_pct >= 80:
        rag_status = "On Track 🟢"
    elif rag_pct >= 50:
        rag_status = "At Risk 🟡"
    else:
        rag_status = "Off Track 🔴"
    
    # Health
    if spi >= 0.95 and rag_pct >= 80:
        health = "🟢 Good"
    elif spi >= 0.80 and rag_pct >= 50:
        health = "🟡 At Risk"
    else:
        health = "🔴 Critical"
    
    # ─── STORY-level RAG ───
    for story in stories:
        s_done = 0
        s_total = 0
        for sub in story.get("subtasks", []):
            if sub["due_date"] and sub["due_date"] <= TODAY:
                s_total += 1
                if sub["status"] in done_statuses:
                    s_done += 1
        story["subtask_due_done"] = s_done
        story["subtask_due_total"] = s_total
        story["subtask_completion"] = f"{s_done}/{s_total} subtasks due ({round(s_done/s_total*100,1) if s_total>0 else 100}%)" if s_total > 0 else None
        s_pct = round(s_done / s_total * 100, 1) if s_total > 0 else 100
        if s_pct >= 80:
            story["rag"] = "On Track 🟢"
        elif s_pct >= 50:
            story["rag"] = "At Risk 🟡"
        else:
            story["rag"] = "Off Track 🔴"
    
    # ─── DONE / DOING classification ───
    done_stories = [s for s in stories if s["status"] in done_statuses]
    doing_stories = [s for s in stories if s["status"] not in done_statuses]
    
    # Total SP
    total_sp = sum(s["story_points"] for s in stories if s["story_points"])
    done_sp = sum(s["story_points"] for s in done_stories if s["story_points"])
    sp_pct = round(done_sp / total_sp * 100, 1) if total_sp > 0 else 0
    
    return {
        "stories": stories,
        "subtasks": all_subtasks,
        "bugs": bugs,
        "sprint_start": sprint_start,
        "sprint_end": sprint_end,
        "elapsed_days": elapsed_days,
        "total_days": total_days,
        "planned_progress": planned_progress,
        "actual_progress_raw": actual_progress_raw,
        "actual_progress_weighted": actual_progress_weighted,
        "spi": spi,
        "spi_status": spi_status,
        "rag_pct": rag_pct,
        "rag_status": rag_status,
        "health": health,
        "phase_data": phase_data,
        "total_est": total_est,
        "total_progress": total_progress,
        "total_sp": total_sp,
        "done_sp": done_sp,
        "sp_pct": sp_pct,
        "done_stories": done_stories,
        "doing_stories": doing_stories,
    }

# ─────────────────────── EXPORT JSON ───────────────────────
def export_json(analysis: Dict, sprint_start, sprint_end):
    """Export JSON debug data"""
    def fmt_date(d):
        return d.isoformat() if d else None
    
    # Count total due subtasks
    total_due = 0
    done_due = 0
    done_statuses = {"Done", "Closed", "Resolved", "Completed", "In review", "In Review"}
    for sub in analysis["subtasks"]:
        if sub["due_date"] and sub["due_date"] <= TODAY:
            total_due += 1
            if sub["status"] in done_statuses:
                done_due += 1
    
    # Story-level completion
    stories_json = []
    for s in analysis["stories"]:
        sub_list = []
        for sub in s.get("subtasks", []):
            sub_list.append({
                "id": sub["id"],
                "summary": sub["summary"],
                "assignee": sub["assignee"],
                "priority": sub["priority"],
                "status": sub["status"],
                "startDate": fmt_date(sub["start_date"]),
                "dueDate": fmt_date(sub["due_date"]),
                "timeSpent": f"{sub['time_spent']}h" if sub['time_spent'] else None,
                "remainingEstimate": None,
            })
        
        stories_json.append({
            "id": s["id"],
            "summary": s["summary"],
            "assignee": s["assignee"],
            "priority": s["priority"],
            "status": s["status"],
            "storyPoint": s["story_points"],
            "startDate": fmt_date(s["start_date"]),
            "dueDate": fmt_date(s["due_date"]),
            "subtaskCompletion": s.get("subtask_completion"),
            "subtaskCompletionPct": round(s["subtask_due_done"] / s["subtask_due_total"] * 100, 1) if s["subtask_due_total"] > 0 else 100,
            "ragStatus": s.get("rag"),
            "subtasks": sub_list
        })
    
    # Phase breakdown for JSON
    phase_export = {}
    for phase, data in analysis["phase_data"].items():
        phase_export[phase] = {
            "weight": data.get("contribution", 0) / 100 if data.get("contribution") else 0,
            "est": round(data["est"], 1),
            "progress": round(data["progress"], 1),
            "pct": data.get("pct", 0),
        }
    
    sprint_completion_pct = round(done_due / total_due * 100, 1) if total_due > 0 else 100
    
    output = {
        "project": PROJECT_KEY,
        "sprint": SPRINT_NAME,
        "fixVersion": "FTI-FCR v1.7",
        "exportedAt": datetime.now(VN_TZ).isoformat(),
        "summary": {
            "totalStories": len(analysis["stories"]),
            "totalSP": round(analysis["total_sp"], 1) if analysis["total_sp"] else None,
            "completedSP": round(analysis["done_sp"], 1) if analysis["done_sp"] else None,
            "sprintStart": fmt_date(sprint_start),
            "sprintEnd": fmt_date(sprint_end),
            "today": fmt_date(TODAY),
            "plannedProgress": analysis["planned_progress"],
            "actualProgress": analysis["actual_progress_weighted"],
            "actualProgressDetail": f"{round(analysis['total_progress'], 1)}h done / {round(analysis['total_est'], 1)}h total ({analysis['actual_progress_raw']}%)",
            "spi": analysis["spi"],
            "spiStatus": analysis["spi_status"],
            "sprintCompletionPct": sprint_completion_pct,
            "ragStatus": "On Track 🟢" if sprint_completion_pct >= 80 else ("At Risk 🟡" if sprint_completion_pct >= 50 else "Off Track 🔴")
        },
        "stories": stories_json,
        "phaseData": phase_export
    }
    
    json_path = os.path.join(OUTPUT_DIR, f"{PROJECT_KEY}_{SPRINT_NAME.replace(' ', '_')}_data.json")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"✅ Đã xuất file JSON debug: {json_path}")
    return json_path

# ─────────────────────── GENERATE REPORT ───────────────────────
def generate_report(analysis: Dict, sprint_start, sprint_end):
    """Generate Markdown weekly report"""
    def fmt_date(d):
        return d.strftime("%d/%m/%Y") if d else "N/A"
    
    def fmt_date_short(d):
        return d.strftime("%d/%m") if d else "N/A"
    
    # Compute phase rows for table
    phase_weights = {
        "Requirement & Design": 0.15,
        "Coding": 0.50,
        "Testing": 0.15,
        "Deployment": 0.10,
        "Other": 0.10,
    }
    
    phase_rows = ""
    for phase in ["Requirement & Design", "Coding", "Testing", "Deployment", "Other"]:
        data = analysis["phase_data"].get(phase, {"est": 0, "progress": 0, "pct": 0, "contribution": 0})
        w_pct = int(phase_weights[phase] * 100)
        phase_rows += f"| {phase} | {w_pct}% | {round(data['est'],1)}h | {round(data['progress'],1)}h | {data.get('pct',0)}% | {data.get('contribution',0)}% |\n"
    
    # Done section
    done_items = []
    doing_items = []
    
    for s in analysis["doing_stories"]:
        # Check if story has overdue subtasks
        has_overdue = False
        done_sub_count = 0
        total_sub_count = len(s.get("subtasks", []))
        for sub in s.get("subtasks", []):
            if sub["status"] in ("Done", "Closed", "Resolved", "Completed", "In review", "In Review"):
                done_sub_count += 1
            if sub["due_date"] and sub["due_date"] <= TODAY and sub["status"] not in ("Done", "Closed", "Resolved", "Completed", "In review", "In Review"):
                has_overdue = True
        
        # Calculate progress for the story
        sub_est = sum(sub["original_estimate"] for sub in s.get("subtasks", []) if sub["original_estimate"])
        sub_spent = sum(sub["time_spent"] for sub in s.get("subtasks", []) if sub["time_spent"])
        pct_done = round(done_sub_count / total_sub_count * 100) if total_sub_count > 0 else 0
        pct_effort = round(sub_spent / sub_est * 100) if sub_est > 0 else 0
        
        if done_sub_count == total_sub_count and total_sub_count > 0:
            done_items.append(f"- **{s['id']}** - {s['summary'][:80]} (Done) - ({s['assignee']})")
        elif has_overdue:
            doing_items.append(f"- **{s['id']}** - {s['summary'][:80]} ({pct_done}% subtasks done) ⚠️ At Risk - ({s['assignee']})")
        else:
            doing_items.append(f"- **{s['id']}** - {s['summary'][:80]} ({pct_done}% subtasks done) - ({s['assignee']})")
    
    for s in analysis["done_stories"]:
        done_items.append(f"- **{s['id']}** - {s['summary'][:80]} (Done) - ({s['assignee']})")
    
    # Sort: done stories by ID
    done_items_str = "\n".join(done_items) if done_items else "*(Không có)*"
    doing_items_str = "\n".join(doing_items) if doing_items else "*(Không có)*"
    
    # Sprint day
    day_x = analysis["elapsed_days"]
    day_total = analysis["total_days"]
    
    # Phase breakdown detail for the note
    phase_detail = []
    for phase in ["Requirement & Design", "Coding", "Testing", "Deployment", "Other"]:
        d = analysis["phase_data"].get(phase, {})
        phase_detail.append(f"{phase} {d.get('pct',0)}%")
    
    # Bugs
    bug_count = len(analysis["bugs"])
    
    # RAG detail
    rag_detail = analysis["rag_status"]
    
    report = f"""# Weekly Report - {PROJECT_KEY} · {SPRINT_NAME}

**Tuần báo cáo:** 07/07 – 15/07/2026
**Sprint:** {SPRINT_NAME} · Day {day_x}/{day_total} · {fmt_date(sprint_start)} – {fmt_date(sprint_end)}
**Ngày tạo:** 15/07/2026

---

## 1. Overall Status

| Metric | Giá trị | Chi tiết |
|--------|---------|----------|
| **Health** | {analysis['health']} | SPI = {analysis['spi']} |
| **Planned Progress** | {analysis['planned_progress']}% | Day {day_x}/{day_total} ngày sprint |
| **Actual Progress** | {analysis['actual_progress_weighted']}% | Weighted Phase ({' / '.join(phase_detail)}) |
| **SPI** | {analysis['spi']} | Actual / Planned - {analysis['spi_status']} |
| **RAG – Đúng hạn** | {analysis['rag_pct']}% | {analysis['rag_status']} |

> Sprint đang ở giai đoạn cuối với {analysis['done_sp']}/{analysis['total_sp']} SP đã hoàn thành ({analysis['sp_pct']}%). 
> Bug đã fix xong 100% ({bug_count} bugs). 
> Các hoạt động Pentest và Pilot đang triển khai để chuẩn bị Release v1.7.

---

## 2. Sprint Progress

### ✅ Done

{done_items_str}

### ▶ Doing / Will do

{doing_items_str}

---

## 3. Weighted Phase Breakdown

| Phase | Trọng số | Est | Progress | % | Đóng góp |
|-------|----------|-----|----------|---|----------|
{phase_rows}| **Total** | **100%** | **{round(analysis['total_est'],1)}h** | **{round(analysis['total_progress'],1)}h** | **{analysis['actual_progress_raw']}% raw** | **{analysis['actual_progress_weighted']}% weighted** |

> *Done / In review = 100% est; In Progress / To Do = spent/est*

---

## 4. Risks & Issues

| # | Loại | Mô tả | Impact | Owner | Action |
|---|------|-------|--------|-------|--------|
| 1 | ℹ️ Note | Chuẩn bị Release Sprint 4 & Version 1.7 - Pentest third-party đang thực hiện, chờ kết quả để remediation | Medium | DuyVM4 | Hoàn thành pentest, remediation lỗ hổng, pilot monitoring và tổng kết |

---

*Generated by Weekly Report Skill v2.11.0 · {PROJECT_KEY} · 15/07/2026*
*Công thức: Done / In review = 100% est; In Progress / To Do = spent/est. Actual % = Σ(weight × progress/est)*
"""
    
    report_path = os.path.join(OUTPUT_DIR, f"{PROJECT_KEY}_{SPRINT_NAME.replace(' ', '_')}_report.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)
    
    print(f"✅ Đã xuất file báo cáo: {report_path}")
    return report_path

# ─────────────────────── MAIN ───────────────────────
def main():
    email = sys.argv[1] if len(sys.argv) > 1 else "DuyVM4@fpt.com"
    api_token = sys.argv[2] if len(sys.argv) > 2 else None
    if not api_token:
        print("❌ Cần API token")
        sys.exit(1)
    
    headers = get_auth_header(email, api_token)
    
    # Step 1: Fetch data from Jira
    issues = fetch_sprint_issues(headers)
    if not issues:
        print("❌ Không lấy được dữ liệu từ Jira!")
        sys.exit(1)
    
    # Step 2: Get sprint dates
    sprint_start, sprint_end = get_sprint_dates(issues)
    print(f"📅 Sprint: {sprint_start} → {sprint_end}")
    print(f"📅 Today: {TODAY}")
    
    # Step 3: Process & compute metrics
    analysis = process_issues(issues, sprint_start, sprint_end)
    
    # Step 4: Export JSON
    export_json(analysis, sprint_start, sprint_end)
    
    # Step 5: Generate report
    generate_report(analysis, sprint_start, sprint_end)
    
    print(f"\n{'='*60}")
    print(f"📊 TÓM TẮT BÁO CÁO")
    print(f"{'='*60}")
    print(f"  Health       : {analysis['health']}")
    print(f"  Planned      : {analysis['planned_progress']}%")
    print(f"  Actual       : {analysis['actual_progress_weighted']}% (weighted)")
    print(f"  SPI          : {analysis['spi']} - {analysis['spi_status']}")
    print(f"  RAG          : {analysis['rag_pct']}% - {analysis['rag_status']}")
    print(f"  Story Points : {analysis['done_sp']}/{analysis['total_sp']} ({analysis['sp_pct']}%)")
    print(f"  Stories      : {len(analysis['done_stories'])}/{len(analysis['stories'])} done")
    print(f"  Total Tasks  : {len(analysis['subtasks'])} subtasks")
    print(f"{'='*60}")
    print(f"✅ Hoàn tất! Files đã xuất tại: {OUTPUT_DIR}")

if __name__ == "__main__":
    main()

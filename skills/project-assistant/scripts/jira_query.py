#!/usr/bin/env python3
"""Query Jira REST API cho project-assistant: tra cứu issues, JQL, active sprint, my tasks, backlog."""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import date
from typing import Any, Dict, List, Optional

# Thêm _shared và scripts hiện tại vào sys.path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SHARED_DIR = os.path.join(SCRIPT_DIR, "..", "..", "_shared")
if SHARED_DIR not in sys.path:
    sys.path.insert(0, SHARED_DIR)
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

try:
    from jira_client import JiraClient, get_credentials, is_error, make_request
    from output_path import next_version_number, now_hhmmss
except ImportError as e:
    print(f"❌ Không import được shared jira_client: {e}", file=sys.stderr)
    sys.exit(1)

STORY_POINT_FIELDS = ["customfield_10016", "customfield_10033", "customfield_10026", "customfield_10028"]


def get_story_points(fields: Dict[str, Any]) -> Optional[float]:
    for cf in STORY_POINT_FIELDS:
        val = fields.get(cf)
        if val is not None:
            try:
                return float(val)
            except (ValueError, TypeError):
                continue
    return None


def next_version(out_dir: str, slug: str) -> int:
    return next_version_number(out_dir, slug, extensions=".json")



def parse_issue_fields(raw_issue: Dict[str, Any]) -> Dict[str, Any]:
    """Trích xuất các thông tin quan trọng từ 1 Jira issue."""
    fields = raw_issue.get("fields", {}) or {}
    status_obj = fields.get("status", {}) or {}
    assignee_obj = fields.get("assignee", {}) or {}
    reporter_obj = fields.get("reporter", {}) or {}
    issuetype_obj = fields.get("issuetype", {}) or {}
    priority_obj = fields.get("priority", {}) or {}

    subtasks = []
    for st in fields.get("subtasks", []) or []:
        st_fields = st.get("fields", {}) or {}
        st_status = st_fields.get("status", {}) or {}
        subtasks.append({
            "key": st.get("key"),
            "summary": st_fields.get("summary"),
            "status": st_status.get("name"),
        })

    # Description text extraction
    desc = fields.get("description")
    desc_text = ""
    if isinstance(desc, str):
        desc_text = desc
    elif isinstance(desc, dict):
        # Atlassian Document Format (ADF) basic extract
        def extract_text(node):
            if not isinstance(node, dict):
                return ""
            if node.get("type") == "text":
                return node.get("text", "")
            content = node.get("content", [])
            return " ".join(extract_text(c) for c in content if isinstance(c, dict)).strip()
        desc_text = extract_text(desc)

    return {
        "key": raw_issue.get("key"),
        "id": raw_issue.get("id"),
        "summary": fields.get("summary", ""),
        "type": issuetype_obj.get("name", ""),
        "status": status_obj.get("name", ""),
        "status_category": status_obj.get("statusCategory", {}).get("name", ""),
        "assignee": assignee_obj.get("displayName") or assignee_obj.get("emailAddress") or "Unassigned",
        "reporter": reporter_obj.get("displayName") or reporter_obj.get("emailAddress") or "Unknown",
        "priority": priority_obj.get("name", "Medium"),
        "story_points": get_story_points(fields),
        "created": fields.get("created"),
        "updated": fields.get("updated"),
        "due_date": fields.get("duedate"),
        "description": desc_text[:1000] if desc_text else "",
        "subtasks_count": len(subtasks),
        "subtasks": subtasks,
    }


def query_single_issue(client: JiraClient, issue_key: str) -> Dict[str, Any]:
    url = f"{client.site}/rest/api/3/issue/{issue_key.strip()}"
    res = make_request("GET", url, client.headers)
    if is_error(res):
        raise RuntimeError(f"Không lấy được issue {issue_key}: {res.get('error')}")
    return parse_issue_fields(res)


def query_active_sprint(client: JiraClient, project_key: str, max_results: int) -> Dict[str, Any]:
    board = client.find_board(project_key)
    if not board:
        raise RuntimeError(f"Không tìm thấy Scrum board cho project '{project_key}'")

    sprints = client.get_board_sprints(board["id"], state="active")
    if not sprints:
        return {
            "project_key": project_key,
            "board_name": board.get("name"),
            "active_sprint": None,
            "message": f"Không có sprint nào đang active trong project {project_key}",
            "issues": [],
        }

    active_sprint = sprints[0]
    sprint_id = active_sprint.get("id")
    sprint_name = active_sprint.get("name")

    jql = f'project = "{project_key}" AND sprint = {sprint_id} ORDER BY status ASC, priority DESC'
    raw_issues = client.search(jql)
    parsed_issues = [parse_issue_fields(i) for i in raw_issues[:max_results]]

    total_sp = sum(i["story_points"] for i in parsed_issues if i["story_points"])
    done_sp = sum(i["story_points"] for i in parsed_issues if i["status_category"].lower() == "done" and i["story_points"])

    return {
        "project_key": project_key,
        "board_name": board.get("name"),
        "active_sprint": {
            "id": sprint_id,
            "name": sprint_name,
            "start_date": active_sprint.get("startDate"),
            "end_date": active_sprint.get("endDate"),
            "goal": active_sprint.get("goal"),
        },
        "stats": {
            "total_issues": len(raw_issues),
            "returned_issues": len(parsed_issues),
            "total_story_points": total_sp,
            "done_story_points": done_sp,
            "completion_rate": f"{(done_sp / total_sp * 100):.1f}%" if total_sp > 0 else "0%",
        },
        "issues": parsed_issues,
    }


def query_jql(client: JiraClient, jql: str, max_results: int) -> Dict[str, Any]:
    raw_issues = client.search(jql)
    parsed_issues = [parse_issue_fields(i) for i in raw_issues[:max_results]]

    # Thống kê nhanh theo status category
    status_stats: Dict[str, int] = {}
    for i in parsed_issues:
        cat = i["status_category"] or i["status"]
        status_stats[cat] = status_stats.get(cat, 0) + 1

    return {
        "jql": jql,
        "total_matches": len(raw_issues),
        "returned_count": len(parsed_issues),
        "status_breakdown": status_stats,
        "issues": parsed_issues,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Tra cứu Jira REST API cho Trợ lý dự án (Project Assistant)")
    parser.add_argument("--output-dir", required=True, help="Thư mục ghi output ($REPORT_OUTPUT_DIR)")
    parser.add_argument("--jql", default="", help="JQL query tùy chỉnh")
    parser.add_argument("--issue", default="", help="Mã issue cụ thể (VD: FCR-123)")
    parser.add_argument("--project", default="", help="Project Key (VD: FCR)")
    parser.add_argument("--active-sprint", action="store_true", help="Lấy sprint đang chạy của project")
    parser.add_argument("--my-tasks", action="store_true", help="Lấy danh sách task được giao cho user")
    parser.add_argument("--assignee", default="", help="Lọc theo email hoặc display name assignee")
    parser.add_argument("--recent-updates", action="store_true", help="Lấy các issue cập nhật trong 7 ngày qua")
    parser.add_argument("--max-results", type=int, default=25, help="Số kết quả tối đa (mặc định 25)")
    parser.add_argument("--slug", default="jira_query", help="Prefix tên file JSON output")
    parser.add_argument("--user-request", default="", help="Ghi chú yêu cầu của user")
    args = parser.parse_args()

    # Kiểm tra credentials
    email = os.environ.get("JIRA_EMAIL", "").strip()
    token = os.environ.get("JIRA_API_TOKEN", "").strip()
    if not email or not token:
        print("❌ Chưa cấu hình Jira credentials (JIRA_EMAIL / JIRA_API_TOKEN).", file=sys.stderr)
        print("💡 Hướng dẫn user: Vào Cài đặt → tab Jira → nhập Jira Email và API Token.", file=sys.stderr)
        sys.exit(2)

    out = os.path.abspath(args.output_dir)
    os.makedirs(out, exist_ok=True)

    print(f"\n{'=' * 60}\n▶ Project Assistant: Tra cứu Jira\n{'=' * 60}")
    print(f"  User:        {email}")
    print(f"  Max results: {args.max_results}")
    print(f"  Output dir:  {out}")

    try:
        client = JiraClient()
    except Exception as e:
        print(f"❌ Không khởi tạo được JiraClient: {e}", file=sys.stderr)
        sys.exit(1)

    result_data: Dict[str, Any] = {}
    query_type = "custom"

    try:
        if args.issue:
            query_type = "single_issue"
            print(f"  Tra cứu issue: {args.issue.upper()}")
            issue_detail = query_single_issue(client, args.issue)
            result_data = {
                "query_type": query_type,
                "target_issue": args.issue.upper(),
                "issue": issue_detail,
            }
        elif args.project and args.active_sprint:
            query_type = "active_sprint"
            print(f"  Tra cứu active sprint cho project: {args.project.upper()}")
            result_data = query_active_sprint(client, args.project.upper(), args.max_results)
            result_data["query_type"] = query_type
        elif args.my_tasks or args.assignee:
            query_type = "assigned_tasks"
            pk = f'project = "{args.project.upper()}" AND ' if args.project else ""
            assignee_filter = f'assignee = "{args.assignee}"' if args.assignee else "assignee = currentUser()"
            jql = f"{pk}{assignee_filter} AND statusCategory != Done ORDER BY updated DESC"
            print(f"  Tra cứu task được giao: {jql}")
            result_data = query_jql(client, jql, args.max_results)
            result_data["query_type"] = query_type
        elif args.project and args.recent_updates:
            query_type = "recent_updates"
            jql = f'project = "{args.project.upper()}" AND updated >= -7d ORDER BY updated DESC'
            print(f"  Tra cứu cập nhật gần đây: {jql}")
            result_data = query_jql(client, jql, args.max_results)
            result_data["query_type"] = query_type
        elif args.jql:
            query_type = "jql"
            print(f"  Thực thi JQL: {args.jql}")
            result_data = query_jql(client, args.jql, args.max_results)
            result_data["query_type"] = query_type
        elif args.project:
            query_type = "project_overview"
            jql = f'project = "{args.project.upper()}" ORDER BY updated DESC'
            print(f"  Tra cứu tổng quan project: {jql}")
            result_data = query_jql(client, jql, args.max_results)
            result_data["query_type"] = query_type
        else:
            # Mặc định lấy open tasks của user
            query_type = "default_open_tasks"
            jql = "assignee = currentUser() AND statusCategory != Done ORDER BY priority DESC, updated DESC"
            print(f"  Tra cứu open tasks mặc định: {jql}")
            result_data = query_jql(client, jql, args.max_results)
            result_data["query_type"] = query_type

    except Exception as e:
        print(f"❌ Lỗi khi truy vấn Jira: {e}", file=sys.stderr)
        sys.exit(1)

    ver = next_version(out, args.slug)
    hhmmss = now_hhmmss()
    json_file = os.path.join(out, f"{args.slug}_v{ver}_{hhmmss}.json")

    payload = {
        "schema_version": "1.0",
        "version": ver,
        "fetch_date": str(date.today()),
        "user_request": args.user_request,
        "query_type": query_type,
        "data": result_data,
    }

    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    # In tóm tắt kết quả ra console
    print(f"\n✅ Đã lấy dữ liệu Jira thành công.")
    if "issues" in result_data:
        print(f"  → Tổng số issues khớp: {result_data.get('total_matches', len(result_data['issues']))}")
        for i, issue in enumerate(result_data["issues"][:5], 1):
            print(f"    {i}. [{issue['key']}] ({issue['status']}) {issue['summary']} (Assignee: {issue['assignee']})")
        if len(result_data["issues"]) > 5:
            print(f"    ... và {len(result_data['issues']) - 5} issues khác.")
    elif "issue" in result_data:
        iss = result_data["issue"]
        print(f"  → [{iss['key']}] {iss['summary']} | Status: {iss['status']} | Assignee: {iss['assignee']}")

    print(f"  → File JSON: {json_file}")
    print(f"{'=' * 60}\n")


if __name__ == "__main__":
    main()

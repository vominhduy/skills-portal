#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
run_story_today_check.py - Tự động rà soát các Story có Start Date là hôm nay và đang ở trạng thái To Do trên Jira Cloud.

Pipeline thực thi:
1. Xác định ngày kiểm tra (mặc định: ngày hiện tại YYYY-MM-DD).
2. Xây dựng JQL theo đúng chuẩn người dùng chỉ định:
   type = Story and creator = currentUser() and status = "To Do" and "start date[date]" = "YYYY-MM-DD" ORDER BY "cf[10015]" ASC, created DESC
3. Gọi Jira REST API v3 để lấy danh sách Story.
4. Xuất kết quả ra file story_today_review_v{N}.json và story_today_review_v{N}.md trong $REPORT_OUTPUT_DIR.
"""

import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime, date
from typing import Dict, List, Optional, Any

# Đảm bảo import được thư viện dùng chung từ skills/_shared/
SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_ROOT = SCRIPT_DIR.parent
SHARED_DIR = SKILL_ROOT.parent / "_shared"
if str(SHARED_DIR) not in sys.path:
    sys.path.insert(0, str(SHARED_DIR))

try:
    from jira_client import JiraClient
except ImportError as e:
    print(f"[!] Không thể import jira_client từ {SHARED_DIR}: {e}", file=sys.stderr)
    sys.exit(1)


def parse_args():
    parser = argparse.ArgumentParser(description="Rà soát các Story Jira có Start Date là hôm nay đang ở trạng thái To Do.")
    parser.add_argument("--output-dir", default=os.environ.get("REPORT_OUTPUT_DIR", "outputs"),
                        help="Thư mục chứa kết quả (mặc định: $REPORT_OUTPUT_DIR hoặc 'outputs')")
    parser.add_argument("--date", default=None,
                        help="Ngày kiểm tra (định dạng YYYY-MM-DD, mặc định: hôm nay)")
    parser.add_argument("--creator", default="currentUser()",
                        help="Người tạo Story (mặc định: currentUser())")
    parser.add_argument("--project-key", default=None,
                        help="Lọc theo Project Key cụ thể (nếu có)")
    parser.add_argument("--jql", default=None,
                        help="Ghi đè hoàn toàn câu lệnh JQL tùy biến")
    return parser.parse_args()


def get_next_report_version(output_dir: Path) -> int:
    """Xác định version tiếp theo cho file story_today_review_vN.json."""
    if not output_dir.exists():
        return 1
    existing = list(output_dir.glob("story_today_review_v*.json"))
    if not existing:
        return 1
    max_v = 0
    for p in existing:
        stem = p.stem  # story_today_review_v1
        try:
            v_str = stem.split("_v")[-1]
            max_v = max(max_v, int(v_str))
        except (ValueError, IndexError):
            continue
    return max_v + 1


def build_jql_candidates(target_date: str, creator: str, project_key: Optional[str] = None) -> List[str]:
    """Tạo danh sách câu truy vấn JQL ưu tiên từ chuẩn yêu cầu đến các fallback."""
    proj_clause = f"project = {project_key} and " if project_key else ""

    # 1. JQL chuẩn xác theo yêu cầu người dùng
    jql_1 = (
        f'{proj_clause}type = Story and creator = {creator} and status = "To Do" '
        f'and "start date[date]" = "{target_date}" ORDER BY "cf[10015]" ASC, created DESC'
    )
    # 2. Fallback: trường "Start date" không có [date]
    jql_2 = (
        f'{proj_clause}type = Story and creator = {creator} and status in ("To Do", "TODO", "Open", "Backlog") '
        f'and "Start date" = "{target_date}" ORDER BY "cf[10015]" ASC, created DESC'
    )
    # 3. Fallback: dùng mã cf[10015]
    jql_3 = (
        f'{proj_clause}type = Story and creator = {creator} and status in ("To Do", "TODO", "Open", "Backlog") '
        f'and cf[10015] = "{target_date}" ORDER BY created DESC'
    )
    # 4. Fallback rộng hơn nếu status name khác: statusCategory = "To Do"
    jql_4 = (
        f'{proj_clause}type = Story and creator = {creator} and statusCategory = "To Do" '
        f'and ("start date[date]" = "{target_date}" or "Start date" = "{target_date}" or cf[10015] = "{target_date}") '
        f'ORDER BY created DESC'
    )

    return [jql_1, jql_2, jql_3, jql_4]


def search_stories_with_fallback(client: JiraClient, jql_candidates: List[str], fields: List[str]) -> tuple[List[Dict[str, Any]], str]:
    """Tìm kiếm issues với cơ chế tự động thử fallback nếu JQL báo lỗi cú pháp trường."""
    last_error = None
    for idx, jql in enumerate(jql_candidates):
        try:
            print(f"[*] Thử JQL [{idx + 1}]: {jql}")
            results = client.search(jql=jql, fields=fields)
            print(f"[+] Tìm thấy {len(results)} Story thỏa điều kiện.")
            return results, jql
        except Exception as e:
            err_msg = str(e)
            print(f"[-] JQL [{idx + 1}] gặp lỗi: {err_msg}")
            last_error = e
            # Nếu là lỗi 400 hoặc syntax, tiếp tục thử candidate tiếp theo
            continue

    if last_error:
        raise last_error
    return [], jql_candidates[0]


def main():
    args = parse_args()
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. Xác định ngày kiểm tra
    if args.date:
        target_date = args.date.strip()
    else:
        target_date = date.today().strftime("%Y-%m-%d")

    print(f"[*] Phạm vi kiểm tra Story bắt đầu hôm nay: {target_date}")
    print(f"[*] Creator: {args.creator}")

    # 2. Khởi tạo JiraClient
    try:
        client = JiraClient()
    except Exception as e:
        print(f"[!] Không thể khởi tạo JiraClient: {e}", file=sys.stderr)
        sys.exit(1)

    # 3. Fields cần lấy
    fields = [
        "summary",
        "status",
        "issuetype",
        "assignee",
        "creator",
        "parent",
        "duedate",
        "created",
        "updated",
        "timeoriginalestimate",
        "timespent",
        "timetracking",
        "customfield_10015",
        "priority",
        "project",
    ]

    # 4. Thực thi truy vấn JQL
    if args.jql:
        jql_used = args.jql.strip()
        print(f"[*] Sử dụng JQL chỉ định: {jql_used}")
        stories_raw = client.search_all(jql=jql_used, fields=fields)
    else:
        candidates = build_jql_candidates(target_date, args.creator, args.project_key)
        stories_raw, jql_used = search_stories_with_fallback(client, candidates, fields)

    # 5. Xử lý & Chuẩn hóa dữ liệu Story
    stories: List[Dict[str, Any]] = []
    total_est_seconds = 0

    for issue in stories_raw:
        key = issue.get("key")
        f = issue.get("fields", {})

        summary = f.get("summary", "(Không có tiêu đề)")
        status_obj = f.get("status") or {}
        status_name = status_obj.get("name", "Unknown")

        assignee_obj = f.get("assignee") or {}
        assignee_name = assignee_obj.get("displayName") or assignee_obj.get("name") or "Chưa gán"

        creator_obj = f.get("creator") or {}
        creator_name = creator_obj.get("displayName") or creator_obj.get("name") or "Unknown"

        priority_obj = f.get("priority") or {}
        priority_name = priority_obj.get("name", "Medium")

        project_obj = f.get("project") or {}
        project_name = project_obj.get("name") or project_obj.get("key", "")

        due_date = f.get("duedate") or "-"
        start_date = f.get("customfield_10015") or target_date

        timetracking = f.get("timetracking") or {}
        orig_est_sec = f.get("timeoriginalestimate") or timetracking.get("originalEstimateSeconds") or 0
        total_est_seconds += orig_est_sec

        stories.append({
            "key": key,
            "summary": summary,
            "status": status_name,
            "assignee": assignee_name,
            "creator": creator_name,
            "priority": priority_name,
            "project": project_name,
            "start_date": start_date,
            "due_date": due_date,
            "original_estimate_hours": round(orig_est_sec / 3600.0, 2),
            "original_estimate_seconds": orig_est_sec,
            "url": f"{client.site}/browse/{key}",
        })

    # 6. Xác định version file
    version = get_next_report_version(output_dir)
    json_path = output_dir / f"story_today_review_v{version}.json"
    md_path = output_dir / f"story_today_review_v{version}.md"

    # 7. Ghi file JSON
    payload = {
        "metadata": {
            "version": version,
            "created_at": datetime.now().isoformat(),
            "target_date": target_date,
            "creator": args.creator,
            "jql": jql_used,
            "total_stories": len(stories),
            "total_estimate_hours": round(total_est_seconds / 3600.0, 2),
        },
        "stories": stories,
    }

    with open(json_path, "w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=2)
    print(f"[+] Đã lưu file JSON: {json_path.name}")

    # 8. Ghi file Markdown chi tiết
    total_est_h = round(total_est_seconds / 3600.0, 2)
    md_lines = [
        f"# Báo Cáo Rà Soát Story Bắt Đầu Hôm Nay ({target_date})",
        "",
        f"- **Ngày kiểm tra:** `{target_date}`",
        f"- **Điều kiện lọc:** `type = Story and creator = {args.creator} and status = 'To Do' and start_date = '{target_date}'`",
        f"- **Tổng số Story tìm thấy:** **{len(stories)}** Story",
        f"- **Tổng quỹ Estimate:** **{total_est_h}h**",
        "",
        "---",
        "",
        "## 📋 Danh Sách Story Sẵn Sàng Bắt Đầu (To Do -> In Progress)",
        "",
        "| Key | Tiêu Đề Story | Assignee | Priority | Estimate | Due Date | Link |",
        "|---|---|---|---|---|---|---|",
    ]

    if not stories:
        md_lines.append("| - | *Không có Story nào có Start Date hôm nay ở trạng thái To Do* | - | - | - | - | - |")
    else:
        for s in stories:
            key_link = f"[{s['key']}]({s['url']})"
            md_lines.append(
                f"| {key_link} | {s['summary']} | {s['assignee']} | {s['priority']} | {s['original_estimate_hours']}h | {s['due_date']} | [Mở Jira]({s['url']}) |"
            )

    md_lines.extend([
        "",
        "---",
        "",
        "### 💡 Hướng Dẫn Chuyển Trạng Thái",
        f"Để chuyển tất cả **{len(stories)}** Story trên sang trạng thái `In Progress`, nhấn nút **`Xác nhận chuyển In Progress các Story hôm nay`** trên giao diện hoặc gửi tin nhắn xác nhận trong chat.",
        "",
    ])

    with open(md_path, "w", encoding="utf-8") as fp:
        fp.write("\n".join(md_lines) + "\n")
    print(f"[+] Đã lưu file Markdown: {md_path.name}")

    print(f"[*] Hoàn tất rà soát Story hôm nay: {len(stories)} Story (File: {md_path.name})")


if __name__ == "__main__":
    main()

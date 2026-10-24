#!/usr/bin/env python3
"""Skill Jira Sub-task Reviewer - Rà soát các sub-task Jira (status In Review, Original Estimate == Time Spent).

JQL mẫu:
    due >= "2026-09-01" and due <= "2026-09-30" and type IN subTaskIssueTypes() and creator = currentUser() ORDER BY "cf[10015]" ASC, created DESC

Mặc định:
    Khoảng ngày tuần hiện tại (Thứ Hai đến Thứ Sáu).
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

# Nạp module dùng chung từ skills/_shared/
SHARED_DIR = Path(__file__).resolve().parent.parent.parent / "_shared"
if str(SHARED_DIR) not in sys.path:
    sys.path.insert(0, str(SHARED_DIR))

try:
    from jira_client import JiraClient, escape_jql_string  # type: ignore
    from date_util import parse_date, to_iso, to_dmy  # type: ignore
    from agile_status import is_in_review  # type: ignore
except ImportError as e:
    print(f"[ERROR] Không thể nạp module shared: {e}", file=sys.stderr)
    sys.exit(1)


def get_current_week_bounds() -> tuple[str, str]:
    """Lấy ngày Thứ Hai (bắt đầu) và Thứ Sáu (kết thúc) của tuần hiện tại dạng YYYY-MM-DD."""
    today = datetime.now().date()
    # today.weekday(): 0 = Monday, 4 = Friday, 6 = Sunday
    monday = today - timedelta(days=today.weekday())
    friday = monday + timedelta(days=4)
    return str(monday), str(friday)


def get_next_version_path(output_dir: Path, base_name: str, ext: str) -> tuple[Path, int]:
    """Tìm version tiếp theo (_v1, _v2, ...) cho file output để tránh ghi đè theo chuẩn guardrails."""
    v = 1
    while True:
        target = output_dir / f"{base_name}_v{v}.{ext.lstrip('.')}"
        if not target.exists():
            return target, v
        v += 1


def parse_jira_hours(seconds: Optional[int | float]) -> float:
    """Chuyển đổi giây sang giờ (làm tròn 2 chữ số thập phân)."""
    if not seconds:
        return 0.0
    return round(float(seconds) / 3600.0, 2)


def check_status_in_review(status_name: str) -> bool:
    """Kiểm tra xem status có thuộc nhóm In Review không."""
    if not status_name:
        return False
    if is_in_review(status_name):
        return True
    s = status_name.strip().lower().replace(" ", "").replace("-", "").replace("_", "")
    return s in {
        "inreview",
        "review",
        "readyforreview",
        "underreview",
        "qa",
        "inqa",
        "codeeeview",
        "peerreview",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Jira Sub-task Reviewer - Rà soát sub-task In Review có Org Est == Time Spent")
    parser.add_argument("--output-dir", default=os.environ.get("REPORT_OUTPUT_DIR", "."), help="Thư mục ghi file kết quả")
    parser.add_argument("--from-date", default=None, help="Ngày bắt đầu due date (YYYY-MM-DD), mặc định Thứ 2 tuần này")
    parser.add_argument("--to-date", default=None, help="Ngày kết thúc due date (YYYY-MM-DD), mặc định Thứ 6 tuần này")
    parser.add_argument("--creator", default="currentUser()", help="Creator lọc JQL, mặc định currentUser()")
    parser.add_argument("--project-key", default=None, help="Lọc theo project key cụ thể (nếu có)")
    parser.add_argument("--jql", default=None, help="Tùy chỉnh toàn bộ câu JQL (ghi đè cấu trúc mặc định)")

    args = parser.parse_args()

    out_dir = Path(args.output_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1. Xác định khoảng ngày
    def_mon, def_fri = get_current_week_bounds()
    from_date = str(parse_date(args.from_date)) if args.from_date else def_mon
    to_date = str(parse_date(args.to_date)) if args.to_date else def_fri

    # 2. Xây dựng câu JQL
    if args.jql:
        jql = args.jql.strip()
    else:
        conditions = [
            f'due >= "{from_date}"',
            f'due <= "{to_date}"',
            "type IN subTaskIssueTypes()",
        ]
        if args.creator and args.creator.strip():
            c = args.creator.strip()
            if c.lower() == "currentuser()":
                conditions.append("creator = currentUser()")
            else:
                conditions.append(f'creator = "{escape_jql_string(c)}"')
        if args.project_key and args.project_key.strip():
            conditions.append(f'project = "{escape_jql_string(args.project_key.strip())}"')

        jql = " and ".join(conditions) + ' ORDER BY "cf[10015]" ASC, created DESC'

    print(f"[*] Khởi tạo JiraClient và thực thi truy vấn...")
    print(f"[*] Phạm vi Due Date: {from_date} -> {to_date}")
    print(f"[*] JQL: {jql}")

    # 3. Gọi Jira API
    client = JiraClient()
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

    try:
        raw_issues = client.search(jql, fields=fields)
    except Exception as e:
        print(f"[ERROR] Truy vấn Jira thất bại: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"[*] Tổng số sub-task tìm thấy từ Jira: {len(raw_issues)}")

    # 4. Lọc toàn bộ sub-task có status In Review, phân loại Highlight (Est != Spent) và Đủ ĐK Done (Est == Spent)
    all_inreview_subtasks: List[Dict[str, Any]] = []
    done_eligible_subtasks: List[Dict[str, Any]] = []
    discrepancy_subtasks: List[Dict[str, Any]] = []

    total_est_seconds = 0
    total_spent_seconds = 0
    done_est_seconds = 0
    done_spent_seconds = 0

    for issue in raw_issues:
        key = issue.get("key", "")
        f = issue.get("fields", {}) or {}

        status_obj = f.get("status") or {}
        status_name = status_obj.get("name", "") if isinstance(status_obj, dict) else str(status_obj)

        timetracking = f.get("timetracking") or {}
        orig_sec = f.get("timeoriginalestimate") or timetracking.get("originalEstimateSeconds") or 0
        spent_sec = f.get("timespent") or timetracking.get("timeSpentSeconds") or 0

        # Kiểm tra điều kiện: status = inreview
        is_review_status = check_status_in_review(status_name)
        if not is_review_status:
            continue

        parent_obj = f.get("parent") or {}
        parent_key = parent_obj.get("key", "")
        parent_fields = parent_obj.get("fields") or {}
        parent_summary = parent_fields.get("summary", "")

        assignee_obj = f.get("assignee") or {}
        assignee_name = assignee_obj.get("displayName", "Unassigned") if isinstance(assignee_obj, dict) else "Unassigned"

        due_date = f.get("duedate") or ""
        start_date = f.get("customfield_10015") or ""

        orig_hours = parse_jira_hours(orig_sec)
        spent_hours = parse_jira_hours(spent_sec)

        total_est_seconds += orig_sec
        total_spent_seconds += spent_sec

        # Kiểm tra điều kiện: Org Est == Time Spent (> 0)
        is_est_equal_spent = (orig_sec > 0 and orig_sec == spent_sec)

        diff_sec = spent_sec - orig_sec
        diff_hours = parse_jira_hours(abs(diff_sec))

        if is_est_equal_spent:
            match_status = "KHỚP (Est == Spent)"
            match_badge = "🟢 KHỚP 100%"
            risk_level = "HIGH"
            risk_reason = "Sub-task đang In Review và đã log 100% thời gian ước tính ban đầu (Remaining = 0h)."
            discrepancy_type = "NONE"
            discrepancy_desc = "Khớp 100% (Đủ điều kiện đánh Done)"
        elif orig_sec == 0 and spent_sec == 0:
            match_status = "LỆCH (Chưa Estimate & Chưa Log)"
            match_badge = "⚪ CHƯA LOG & EST"
            risk_level = "MEDIUM"
            risk_reason = "Sub-task chưa có Estimate và chưa log thời gian làm việc."
            discrepancy_type = "NO_EST_NO_SPENT"
            discrepancy_desc = "Chưa nhập Estimate và chưa log time"
        elif orig_sec == 0 and spent_sec > 0:
            match_status = f"LỆCH (Chưa Estimate, đã log {spent_hours}h)"
            match_badge = f"🟡 KHÔNG CÓ EST (+{spent_hours}h)"
            risk_level = "HIGH"
            risk_reason = f"Sub-task chưa có Estimate ban đầu nhưng đã log {spent_hours}h."
            discrepancy_type = "NO_ESTIMATE"
            discrepancy_desc = f"Chưa có Estimate nhưng đã log {spent_hours}h"
        elif spent_sec == 0 and orig_sec > 0:
            match_status = f"LỆCH (Chưa log time, Est {orig_hours}h)"
            match_badge = f"⚪ CHƯA LOG TIME (0/{orig_hours}h)"
            risk_level = "HIGH"
            risk_reason = f"Sub-task đã lên In Review nhưng chưa log giờ nào (0/{orig_hours}h)."
            discrepancy_type = "NOT_LOGGED"
            discrepancy_desc = f"Chưa log giờ nào (Est {orig_hours}h)"
        elif spent_sec < orig_sec:
            match_status = f"LỆCH (Thiếu log time: Spent {spent_hours}h < Est {orig_hours}h)"
            match_badge = f"🟡 THIẾU LOG (-{diff_hours}h)"
            risk_level = "MEDIUM"
            risk_reason = f"Đã log {spent_hours}h / {orig_hours}h (còn dư {diff_hours}h estimate)."
            discrepancy_type = "UNDER_ESTIMATE"
            discrepancy_desc = f"Log thiếu {diff_hours}h so với estimate ({spent_hours}h/{orig_hours}h)"
        else: # spent_sec > orig_sec
            match_status = f"LỆCH (Vượt estimate: Spent {spent_hours}h > Est {orig_hours}h)"
            match_badge = f"🔴 VƯỢT ESTIMATE (+{diff_hours}h)"
            risk_level = "CRITICAL"
            risk_reason = f"Đã log {spent_hours}h vượt quá estimate {orig_hours}h (+{diff_hours}h)."
            discrepancy_type = "OVER_ESTIMATE"
            discrepancy_desc = f"Vượt estimate +{diff_hours}h ({spent_hours}h/{orig_hours}h)"

        item_data = {
            "key": key,
            "summary": f.get("summary", ""),
            "parent_key": parent_key,
            "parent_summary": parent_summary,
            "status": status_name,
            "assignee": assignee_name,
            "due_date": due_date,
            "due_date_dmy": to_dmy(parse_date(due_date)) if due_date else "",
            "start_date": start_date,
            "start_date_dmy": to_dmy(parse_date(start_date)) if start_date else "",
            "original_estimate_seconds": orig_sec,
            "time_spent_seconds": spent_sec,
            "original_estimate_hours": orig_hours,
            "time_spent_hours": spent_hours,
            "diff_hours": diff_hours if not is_est_equal_spent else 0.0,
            "is_done_eligible": is_est_equal_spent,
            "match_status": match_status,
            "match_badge": match_badge,
            "discrepancy_type": discrepancy_type,
            "discrepancy_desc": discrepancy_desc,
            "url": f"{client.site}/browse/{key}",
            "risk_level": risk_level,
            "risk_reason": risk_reason,
        }

        all_inreview_subtasks.append(item_data)

        if is_est_equal_spent:
            done_est_seconds += orig_sec
            done_spent_seconds += spent_sec
            done_eligible_subtasks.append(item_data)
        else:
            discrepancy_subtasks.append(item_data)

    print(f"[*] Tổng số sub-task In Review: {len(all_inreview_subtasks)}")
    print(f"[*] Số sub-task khớp 100% (Est == Spent, Đủ điều kiện đánh Done): {len(done_eligible_subtasks)}")
    print(f"[*] Số sub-task lệch giờ (Est != Spent, Cần Highlight): {len(discrepancy_subtasks)}")

    # 5. Xuất file kết quả JSON & Markdown
    json_path, version = get_next_version_path(out_dir, "subtask_review", "json")
    md_path, _ = get_next_version_path(out_dir, "subtask_review", "md")

    total_est_hours = parse_jira_hours(total_est_seconds)
    total_spent_hours = parse_jira_hours(total_spent_seconds)
    done_est_hours = parse_jira_hours(done_est_seconds)
    done_spent_hours = parse_jira_hours(done_spent_seconds)

    report_data = {
        "metadata": {
            "skill_id": "jira-subtask-reviewer",
            "version": version,
            "generated_at": datetime.now().isoformat(),
            "date_range": {
                "from_date": from_date,
                "to_date": to_date,
                "from_date_dmy": to_dmy(parse_date(from_date)),
                "to_date_dmy": to_dmy(parse_date(to_date)),
            },
            "jql_executed": jql,
            "total_searched": len(raw_issues),
            "total_inreview": len(all_inreview_subtasks),
            "total_done_eligible": len(done_eligible_subtasks),
            "total_discrepancy": len(discrepancy_subtasks),
        },
        "summary_metrics": {
            "total_inreview_count": len(all_inreview_subtasks),
            "done_eligible_count": len(done_eligible_subtasks),
            "discrepancy_highlight_count": len(discrepancy_subtasks),
            "total_original_estimate_hours": total_est_hours,
            "total_time_spent_hours": total_spent_hours,
            "done_eligible_estimate_hours": done_est_hours,
            "done_eligible_spent_hours": done_spent_hours,
        },
        "all_inreview_subtasks": all_inreview_subtasks,
        "done_eligible_subtasks": done_eligible_subtasks,
        "matched_subtasks": done_eligible_subtasks,  # Alias tương thích ngược cho transition_subtasks_done.py
        "discrepancy_subtasks": discrepancy_subtasks, # Danh sách task highlight
    }

    with open(json_path, "w", encoding="utf-8") as fp:
        json.dump(report_data, fp, ensure_ascii=False, indent=2)
    print(f"[+] Đã ghi file JSON: {json_path.name}")

    # Sinh nội dung Markdown
    md_lines: List[str] = [
        f"# Báo Cáo Rà Soát Sub-task Jira In Review (Phiên bản _v{version})",
        "",
        f"- **Thời gian tạo:** {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}",
        f"- **Khoảng ngày rà soát (Due Date):** {to_dmy(parse_date(from_date))} – {to_dmy(parse_date(to_date))}",
        f"- **Phạm vi lấy dữ liệu:** Toàn bộ sub-task có `status = In Review`",
        f"- **Tổng sub-task In Review:** **{len(all_inreview_subtasks)}**",
        f"- **🟢 Khớp 100% (Est == Spent - Đủ điều kiện đánh Done):** **{len(done_eligible_subtasks)}** sub-task ({done_est_hours}h)",
        f"- **🔥 Lệch giờ cần Highlight (Est != Spent):** **{len(discrepancy_subtasks)}** sub-task",
        f"- **Tổng thời gian In Review:** Estimate: **{total_est_hours}h** | Đã log: **{total_spent_hours}h**",
        "",
        "---",
        "",
    ]

    # PHẦN 1: HIGHLIGHT CÁC SUB-TASK LỆCH GIỜ (Est != Spent)
    md_lines.extend([
        "## 🔥 CÁC SUB-TASK CẦN HIGHLIGHT (Org Est != Time Spent)",
        "",
        "> ⚠️ **Lưu ý:** Các sub-task dưới đây đang ở trạng thái `In Review` nhưng có thời gian log **không khớp** với Estimate ban đầu. Cần được PM/Tech Lead rà soát đối soát trước khi duyệt hoàn thành.",
        "",
    ])

    if not discrepancy_subtasks:
        md_lines.append("> ✅ **Tuyệt vời!** Không có sub-task In Review nào bị lệch thời gian (100% task đều khớp Est == Spent).")
    else:
        md_lines.extend([
            "| Key | Tiêu Đề Sub-task | Người Thực Hiện | Est (h) | Spent (h) | Chênh Lệch | Đánh Giá Tình Trạng |",
            "|---|---|---|---|---|---|---|",
        ])
        for item in discrepancy_subtasks:
            key_link = f"[{item['key']}]({item['url']})"
            badge = item.get("match_badge", "")
            desc = item.get("discrepancy_desc", "")
            md_lines.append(
                f"| **{key_link}** | {item['summary']} | {item['assignee']} | **{item['original_estimate_hours']}** | **{item['time_spent_hours']}** | {badge} | {desc} |"
            )

    md_lines.extend([
        "",
        "---",
        "",
        "## ✅ CÁC SUB-TASK ĐỦ ĐIỀU KIỆN ĐÁNH DONE (Org Est == Time Spent)",
        "",
        "> ℹ️ **Thông tin:** Các sub-task dưới đây đã log đủ 100% thời gian estimate và đang chờ hoàn tất. **Nút xác nhận đánh Done trên chat sẽ chỉ áp dụng chuyển trạng thái cho nhóm task này.**",
        "",
    ])

    if not done_eligible_subtasks:
        md_lines.append("> ℹ️ Không có sub-task nào khớp điều kiện `Est == Spent > 0` để đánh Done tự động.")
    else:
        md_lines.extend([
            "| Key | Tiêu Đề Sub-task | Story Cha | Người Thực Hiện | Est (h) | Spent (h) | Due Date | Trạng Thái |",
            "|---|---|---|---|---|---|---|---|",
        ])
        for item in done_eligible_subtasks:
            key_link = f"[{item['key']}]({item['url']})"
            parent_text = item['parent_key'] if item['parent_key'] else "-"
            due_text = item['due_date_dmy'] if item['due_date_dmy'] else "-"
            md_lines.append(
                f"| {key_link} | {item['summary']} | {parent_text} | {item['assignee']} | {item['original_estimate_hours']} | {item['time_spent_hours']} | {due_text} | 🟢 Sẵn sàng Done |"
            )

    md_lines.extend([
        "",
        "---",
        "",
        "## 📋 Bảng Toàn Bộ Sub-task In Review",
        "",
        "| Key | Tiêu Đề Sub-task | Người Thực Hiện | Est (h) | Spent (h) | Phân Loại Thời Gian | Đủ ĐK Đánh Done? |",
        "|---|---|---|---|---|---|---|",
    ])

    for item in all_inreview_subtasks:
        key_link = f"[{item['key']}]({item['url']})"
        eligible_text = "✅ Có (Est == Spent)" if item["is_done_eligible"] else "❌ Không (Lệch giờ)"
        md_lines.append(
            f"| {key_link} | {item['summary']} | {item['assignee']} | {item['original_estimate_hours']} | {item['time_spent_hours']} | {item['match_badge']} | {eligible_text} |"
        )

    md_lines.extend([
        "",
        "---",
        "",
        "## 💡 Khuyến Nghị Vận Hành PM / Tech Lead",
        "",
        "1. **Đối với các task Lệch Giờ (Highlight):**",
        "   - Yêu cầu Assignee log bù giờ (nếu thiếu) hoặc cập nhật giải trình (nếu vượt estimate).",
        "   - Không đánh Done vội vàng các task chưa log đủ giờ để đảm bảo báo cáo Timesheet chính xác.",
        "2. **Đối với các task Khớp Giờ (Est == Spent):**",
        "   - Nhấn nút **`Xác nhận đánh Done tất cả sub-task`** trên khung chat để tự động transition lên Jira Cloud.",
    ])

    with open(md_path, "w", encoding="utf-8") as fp:
        fp.write("\n".join(md_lines) + "\n")
    print(f"[+] Đã ghi file Markdown: {md_path.name}")
    print(f"[*] Hoàn tất rà soát sub-task!")


if __name__ == "__main__":
    main()

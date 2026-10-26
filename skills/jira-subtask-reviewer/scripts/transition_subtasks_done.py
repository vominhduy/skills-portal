#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
transition_subtasks_done.py - Tự động transition các sub-task Jira sang trạng thái Done / Closed.

Pipeline thực thi:
1. Đọc danh sách sub-task từ file subtask_review_v*.json mới nhất trong output_dir (hoặc qua --input-json/--keys).
2. Gọi Jira API v3 lấy workflow transitions khả dụng cho từng sub-task và chuyển sang Done.
3. Ghi kết quả vào subtask_done_v{N}.json và subtask_done_v{N}.md trong $REPORT_OUTPUT_DIR.
"""

import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any

# Đảm bảo import được thư viện dùng chung từ skills/_shared/
SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_ROOT = SCRIPT_DIR.parent
SHARED_DIR = SKILL_ROOT.parent / "_shared"
if str(SHARED_DIR) not in sys.path:
    sys.path.insert(0, str(SHARED_DIR))

try:
    from jira_client import JiraClient
    from output_path import next_version_number, now_hhmmss, resolve_input_path, split_version_and_time
except ImportError as e:
    print(f"[!] Không thể import jira_client từ {SHARED_DIR}: {e}", file=sys.stderr)
    sys.exit(1)


def parse_args():
    parser = argparse.ArgumentParser(description="Chuyển trạng thái các sub-task Jira sang Done.")
    parser.add_argument("--output-dir", default=os.environ.get("REPORT_OUTPUT_DIR", "outputs"),
                        help="Thư mục chứa kết quả (mặc định: $REPORT_OUTPUT_DIR hoặc 'outputs')")
    parser.add_argument("--input-json", default=None,
                        help="Đường dẫn file subtask_review_v*.json cần xử lý")
    parser.add_argument("--keys", default=None,
                        help="Danh sách issue keys cách nhau bởi dấu phẩy (nếu không dùng file JSON)")
    return parser.parse_args()


def find_latest_subtask_json(output_dir: Path) -> Optional[Path]:
    """Tìm file subtask_review_v*.json có version mới nhất trong output_dir."""
    if not output_dir.exists():
        return None
    files = list(output_dir.glob("subtask_review_v*.json"))
    if not files:
        return None
    files.sort(
        key=lambda f: (split_version_and_time(f.stem)[1] or 0, f.stat().st_mtime),
        reverse=True,
    )
    return files[0]


def get_next_done_version(output_dir: Path) -> int:
    """Xác định version tiếp theo cho subtask_done_vN_HHMMSS.json."""
    return next_version_number(output_dir, "subtask_done", extensions=[".json", ".md"])



def main():
    args = parse_args()
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    target_keys = []
    source_info = ""

    if args.keys:
        target_keys = [k.strip().upper() for k in args.keys.split(",") if k.strip()]
        source_info = f"Chỉ định trực tiếp ({len(target_keys)} keys)"
    else:
        json_file = Path(resolve_input_path(args.input_json, output_dir)).resolve() if args.input_json else find_latest_subtask_json(output_dir)
        if not json_file or not json_file.exists():
            print(f"[!] Không tìm thấy file dữ liệu sub-task JSON nào trong {output_dir}")
            sys.exit(1)

        source_info = f"File {json_file.name}"
        try:
            with open(json_file, "r", encoding="utf-8") as fp:
                data = json.load(fp)

            # Ưu tiên lấy từ done_eligible_subtasks hoặc matched_subtasks hoặc lọc từ all_inreview_subtasks
            candidates = (
                data.get("done_eligible_subtasks")
                or data.get("matched_subtasks")
                or data.get("all_inreview_subtasks", [])
            )

            for item in candidates:
                k = item.get("key")
                # Bắt buộc kiểm tra điều kiện: Org Est == Time Spent (> 0)
                orig = item.get("original_estimate_seconds") or 0
                spent = item.get("time_spent_seconds") or 0
                is_eligible = item.get("is_done_eligible")
                if is_eligible is None:
                    is_eligible = (orig > 0 and orig == spent)

                if k and is_eligible:
                    target_keys.append(k.strip().upper())
        except Exception as e:
            print(f"[!] Lỗi khi đọc {json_file}: {e}", file=sys.stderr)
            sys.exit(1)

    if not target_keys:
        print(f"[*] Không có sub-task nào cần đánh Done.")
        sys.exit(0)

    print(f"[*] Bắt đầu chuyển {len(target_keys)} sub-task sang trạng thái Done (Nguồn: {source_info})...")

    client = JiraClient()
    results: List[Dict[str, Any]] = []
    success_count = 0
    fail_count = 0

    for idx, key in enumerate(target_keys, 1):
        print(f"    [{idx}/{len(target_keys)}] Đang xử lý {key}...", end=" ", flush=True)
        try:
            res = client.mark_issue_done(key)
            if res.get("success"):
                success_count += 1
                to_st = res.get("to_status") or "Done"
                print(f"-> THÀNH CÔNG ({to_st})")
                results.append({
                    "key": key,
                    "success": True,
                    "to_status": to_st,
                    "transition_name": res.get("transition_name"),
                    "url": f"{client.site}/browse/{key}"
                })
            else:
                fail_count += 1
                err_msg = res.get("error") or "Không rõ nguyên nhân"
                print(f"-> THẤT BẠI: {err_msg}")
                results.append({
                    "key": key,
                    "success": False,
                    "error": err_msg,
                    "url": f"{client.site}/browse/{key}"
                })
        except Exception as e:
            fail_count += 1
            print(f"-> LỖI: {e}")
            results.append({
                "key": key,
                "success": False,
                "error": str(e),
                "url": f"{client.site}/browse/{key}"
            })

    version = get_next_done_version(output_dir)
    hhmmss = now_hhmmss()
    json_path = output_dir / f"subtask_done_v{version}_{hhmmss}.json"
    md_path = output_dir / f"subtask_done_v{version}_{hhmmss}.md"

    output_payload = {
        "metadata": {
            "version": version,
            "created_at": datetime.now().isoformat(),
            "source": source_info,
            "total_processed": len(target_keys),
            "success_count": success_count,
            "fail_count": fail_count,
        },
        "results": results
    }

    with open(json_path, "w", encoding="utf-8") as fp:
        json.dump(output_payload, fp, ensure_ascii=False, indent=2)
    print(f"[+] Đã lưu file JSON: {json_path.name}")

    md_lines = [
        f"# Kết Quả Đánh Done Sub-task Jira (Phiên bản _v{version})",
        "",
        f"- **Thời gian thực hiện:** {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}",
        f"- **Nguồn dữ liệu:** {source_info}",
        f"- **Tổng số sub-task xử lý:** {len(target_keys)} | **Thành công:** {success_count} | **Thất bại:** {fail_count}",
        "",
        "---",
        "",
        "## Chi Tiết Trạng Thái Từng Sub-task",
        "",
        "| Key | Trạng Thái Mới | Kết Quả | Chi Tiết |",
        "|---|---|---|---|",
    ]

    for r in results:
        key_link = f"[{r['key']}]({r['url']})"
        if r.get("success"):
            md_lines.append(f"| {key_link} | {r.get('to_status', 'Done')} | ✅ Thành công | Đã transition thành công |")
        else:
            md_lines.append(f"| {key_link} | - | ❌ Thất bại | {r.get('error', 'Lỗi')} |")

    with open(md_path, "w", encoding="utf-8") as fp:
        fp.write("\n".join(md_lines) + "\n")
    print(f"[+] Đã lưu file Markdown: {md_path.name}")
    print(f"[*] Hoàn tất chuyển trạng thái! ({success_count}/{len(target_keys)} thành công)")


if __name__ == "__main__":
    main()

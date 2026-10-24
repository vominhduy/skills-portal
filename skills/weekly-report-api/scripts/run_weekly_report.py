#!/usr/bin/env python3
"""Pipeline weekly report - 1 lệnh Bash thay vì 3–5 vòng tool Claude."""
from __future__ import annotations

import argparse
import glob
import json
import os
import shutil
import subprocess
import sys
from datetime import date


def scripts_dir() -> str:
    return os.path.dirname(os.path.abspath(__file__))


def safe_name(text: str) -> str:
    return text.replace(" ", "_").replace("/", "-")


def run_step(label: str, cmd: list[str]) -> None:
    print(f"\n{'=' * 60}\n▶ {label}\n{'=' * 60}")
    print(" ", " ".join(cmd))
    result = subprocess.run(cmd)
    if result.returncode != 0:
        print(f"\n❌ {label} thất bại (exit {result.returncode})")
        sys.exit(result.returncode)


def find_jira_data_json(out: str, project_key: str, sprint_name: str) -> str | None:
    expected = os.path.join(out, f"{project_key}_{safe_name(sprint_name)}_sprint_data.json")
    if os.path.isfile(expected):
        return expected
    matches = sorted(
        glob.glob(os.path.join(out, f"{project_key}_*_sprint_data.json")),
        key=os.path.getmtime,
    )
    if matches:
        return matches[-1]
    parent_out = os.path.dirname(os.path.abspath(out))
    if os.path.isdir(parent_out):
        cached_matches = sorted(
            glob.glob(os.path.join(parent_out, "*", f"{project_key}_{safe_name(sprint_name)}_sprint_data.json")),
            key=os.path.getmtime,
        )
        if cached_matches:
            latest_cache = cached_matches[-1]
            shutil.copyfile(latest_cache, expected)
            print(f"  [CACHE] Đã nạp dữ liệu sprint cached từ: {latest_cache}")
            return expected
    return None


def find_sprint_info_json(out: str, project_key: str, sprint_name: str) -> str | None:
    expected = os.path.join(out, f"{project_key}_{safe_name(sprint_name)}_sprint_info.json")
    if os.path.isfile(expected):
        return expected
    matches = sorted(
        glob.glob(os.path.join(out, f"{project_key}_*_sprint_info.json")),
        key=os.path.getmtime,
    )
    return matches[-1] if matches else None


def load_sprint_dates(sprint_info_path: str | None) -> tuple[str | None, str | None]:
    if not sprint_info_path or not os.path.isfile(sprint_info_path):
        return None, None
    with open(sprint_info_path, encoding="utf-8") as f:
        si = json.load(f)
    sprint_start = (si.get("sprint_start") or "")[:10] or None
    sprint_end = (si.get("sprint_end") or "")[:10] or None
    return sprint_start, sprint_end


def generate_report(
    py: str,
    sd: str,
    out: str,
    data_json: str,
    args: argparse.Namespace,
    sprint_start: str | None,
    sprint_end: str | None,
    label: str,
) -> None:
    gen_cmd = [
        py,
        os.path.join(sd, "generate_report_from_json.py"),
        "--input",
        data_json,
        "--output-dir",
        out,
        "--project-key",
        args.project_key,
        "--sprint-name",
        args.sprint_name,
        "--today",
        args.today,
    ]
    if sprint_start and sprint_end:
        gen_cmd.extend(["--sprint-start", sprint_start, "--sprint-end", sprint_end])
    run_step(label, gen_cmd)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Chạy pipeline weekly report: Jira-only hoặc Jira dates + Sheet/Excel → report .md (Agile & Waterfall)",
    )
    parser.add_argument("--project-key", required=True)
    parser.add_argument("--sprint-name", help="Tên sprint (Agile). Với Waterfall có thể bỏ trống hoặc đặt tên Milestone/Parent")
    parser.add_argument("--waterfall", action="store_true", help="Chế độ Waterfall (không cần sprint)")
    parser.add_argument("--parent-key", help="Parent Request / Epic key (VD: 'FSM-20'). Tự động lấy Start/Due Date và task con")
    parser.add_argument("--start-date", help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end-date", help="End date (YYYY-MM-DD)")
    parser.add_argument("--jql", help="Custom JQL filter cho Jira")
    parser.add_argument("--fix-version", help="Fix Version filter cho Jira")
    parser.add_argument("--epic-key", help="Epic key filter cho Jira (alias của --parent-key)")
    parser.add_argument("--today", default=date.today().isoformat())
    parser.add_argument("--output-dir", default=os.environ.get("REPORT_OUTPUT_DIR", "."))
    parser.add_argument("--sheet-id", help="Google Spreadsheet ID (backlog từ Sheet)")
    parser.add_argument(
        "--service-account",
        default=os.environ.get("GOOGLE_SERVICE_ACCOUNT_PATH"),
        help="Service account JSON (mặc định: GOOGLE_SERVICE_ACCOUNT_PATH)",
    )
    parser.add_argument("--excel", help="Đường dẫn file .xlsx (backlog từ Excel)")
    parser.add_argument("--excel-url", help="Link SharePoint/OneDrive Excel (Microsoft Graph API)")
    parser.add_argument("--share-url", help="Alias của --excel-url")
    parser.add_argument(
        "--jira-only",
        action="store_true",
        help="Chỉ lấy backlog từ Jira API (--fetch-issues), không cần Sheet/Excel",
    )
    parser.add_argument("--skip-jira", action="store_true", help="Bỏ bước lấy sprint dates từ Jira")
    args = parser.parse_args()
    if not args.excel and (args.excel_url or args.share_url):
        args.excel = args.excel_url or args.share_url

    parent_key = args.parent_key or args.epic_key
    is_waterfall = args.waterfall or bool(parent_key) or (not args.sprint_name and not args.sheet_id and not args.excel)
    if is_waterfall and not args.sprint_name:
        if parent_key:
            args.sprint_name = parent_key
        elif args.fix_version:
            args.sprint_name = f"FixVersion_{args.fix_version}"
        else:
            args.sprint_name = "Waterfall"
    elif not args.sprint_name:
        args.sprint_name = "Waterfall"

    jira_only = args.jira_only or (not args.sheet_id and not args.excel)
    if args.sheet_id and not args.service_account:
        print("❌ Thiếu --service-account hoặc GOOGLE_SERVICE_ACCOUNT_PATH")
        sys.exit(1)

    py = sys.executable
    sd = scripts_dir()
    out = args.output_dir
    os.makedirs(out, exist_ok=True)

    sprint_info_path: str | None = None
    sprint_start = args.start_date
    sprint_end = args.end_date

    if jira_only:
        jira_cmd = [
            py,
            os.path.join(sd, "jira_sprint_fetcher.py"),
            "--project-key",
            args.project_key,
            "--fetch-issues",
            "--output-dir",
            out,
        ]
        if args.sprint_name:
            jira_cmd.extend(["--sprint-name", args.sprint_name])
        if is_waterfall:
            jira_cmd.append("--waterfall")
        if parent_key:
            jira_cmd.extend(["--parent-key", parent_key])
        if args.start_date:
            jira_cmd.extend(["--start-date", args.start_date])
        if args.end_date:
            jira_cmd.extend(["--end-date", args.end_date])
        if args.jql:
            jira_cmd.extend(["--jql", args.jql])
        if args.fix_version:
            jira_cmd.extend(["--fix-version", args.fix_version])

        print(f"\n{'=' * 60}\n▶ Bước 1/2 - Jira (fetch issues & dates)\n{'=' * 60}")
        print(" ", " ".join(jira_cmd))
        jira_res = subprocess.run(jira_cmd)
        if jira_res.returncode != 0:
            print(f"\n⚠️ Bước 1/2 - Jira API gặp lỗi (exit {jira_res.returncode}). Đang tìm bản cached...")
            data_json = find_jira_data_json(out, args.project_key, args.sprint_name)
            if not data_json:
                print(f"\n❌ Bước 1/2 - Jira (fetch issues & dates) thất bại (exit {jira_res.returncode})")
                sys.exit(jira_res.returncode)
            print("  ✅ Tìm thấy dữ liệu cached, tiếp tục bước 2/2 tạo báo cáo.")
        else:
            data_json = find_jira_data_json(out, args.project_key, args.sprint_name)
            if not data_json:
                print("❌ Không tìm thấy JSON sprint_data từ Jira")
                sys.exit(1)
        with open(data_json, encoding="utf-8") as f:
            payload = json.load(f)
        sprint_start = sprint_start or (payload.get("sprint_start") or "")[:10] or None
        sprint_end = sprint_end or (payload.get("sprint_end") or "")[:10] or None
        if payload.get("sprint_name"):
            args.sprint_name = payload["sprint_name"]
        generate_report(
            py, sd, out, data_json, args, sprint_start, sprint_end,
            "Bước 2/2 - Generate report",
        )
    else:
        if not args.skip_jira and not is_waterfall:
            run_step(
                "Bước 1/3 - Jira sprint dates",
                [
                    py,
                    os.path.join(sd, "jira_sprint_fetcher.py"),
                    "--project-key",
                    args.project_key,
                    "--sprint-name",
                    args.sprint_name,
                    "--output-dir",
                    out,
                ],
            )
            sprint_info_path = find_sprint_info_json(out, args.project_key, args.sprint_name)
            s_start, s_end = load_sprint_dates(sprint_info_path)
            sprint_start = sprint_start or s_start
            sprint_end = sprint_end or s_end

        if args.sheet_id:
            cmd = [
                py,
                os.path.join(sd, "fetch_gsheet_data.py"),
                "--sheet-id",
                args.sheet_id,
                "--service-account",
                args.service_account,
                "--sprint-name",
                args.sprint_name,
                "--today",
                args.today,
                "--output-dir",
                out,
            ]
            if sprint_info_path:
                cmd.extend(["--sprint-info", sprint_info_path])
            if sprint_start and sprint_end:
                cmd.extend(["--start-date", sprint_start, "--end-date", sprint_end])
            run_step("Bước 2/3 - Google Sheet", cmd)
            data_json = os.path.join(out, f"gsheet_data_{args.sprint_name.replace(' ', '_')}.json")
        else:
            excel_cmd = [
                py,
                os.path.join(sd, "fetch_excel_data.py"),
                "--file",
                args.excel,
                "--sprint-name",
                args.sprint_name,
                "--today",
                args.today,
                "--output-dir",
                out,
            ]
            if sprint_start and sprint_end:
                excel_cmd.extend(["--start-date", sprint_start, "--end-date", sprint_end])
            run_step("Bước 2/3 - Excel", excel_cmd)
            data_json = os.path.join(out, f"excel_data_{safe_name(args.sprint_name)}.json")

        if not os.path.isfile(data_json):
            print(f"❌ Không tìm thấy JSON: {data_json}")
            sys.exit(1)

        generate_report(
            py, sd, out, data_json, args, sprint_start, sprint_end,
            "Bước 3/3 - Generate report",
        )

    txt_path = ""
    report_path = os.path.join(out, f"{args.project_key}_{safe_name(args.sprint_name)}_report_latest.json")
    if os.path.isfile(report_path):
        try:
            with open(report_path, encoding="utf-8") as f:
                manifest = json.load(f)
            md_name = manifest.get("md", "")
            txt_name = manifest.get("txt", "") or manifest.get("txtExpected", "")
            report_path = os.path.join(out, md_name) if md_name else ""
            txt_path = os.path.join(out, txt_name) if txt_name else ""
        except (json.JSONDecodeError, OSError):
            report_path = ""
            txt_path = ""

    if not report_path or not os.path.isfile(report_path):
        matches = sorted(
            glob.glob(os.path.join(out, "*_report_v*.md")) + glob.glob(os.path.join(out, "*_report.md")),
            key=os.path.getmtime,
        )
        report_path = matches[-1] if matches else report_path

    if not txt_path or not os.path.isfile(txt_path):
        matches_txt = sorted(
            glob.glob(os.path.join(out, "*_report_v*.txt")) + glob.glob(os.path.join(out, "*_report.txt")),
            key=os.path.getmtime,
        )
        txt_path = matches_txt[-1] if matches_txt else txt_path

    print(f"\n{'='*60}")
    print(f"✅ PIPELINE HOÀN TẤT THÀNH CÔNG")
    print(f"{'='*60}")
    print(f"   Báo cáo chi tiết (.md)  : {report_path}")
    print(f"   Bản tóm tắt PO/PMO (.txt): {txt_path}")
    print(f"\n→ Trợ lý AI: Hãy phản hồi ngắn gọn cho User tóm tắt Health/SPI/RAG và nêu rõ tên cả 2 file kết quả {os.path.basename(report_path)} & {os.path.basename(txt_path)} (KHÔNG in toàn bộ nội dung file .txt ra tin nhắn chat).")


if __name__ == "__main__":
    main()

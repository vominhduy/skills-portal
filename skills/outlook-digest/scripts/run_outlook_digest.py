#!/usr/bin/env python3
"""Pipeline Outlook Digest - fetch + tổng hợp metadata."""
from __future__ import annotations

import argparse
import os
import subprocess
import sys


def scripts_dir() -> str:
    return os.path.dirname(os.path.abspath(__file__))


def main() -> None:
    parser = argparse.ArgumentParser(description="Pipeline Outlook Digest")
    parser.add_argument("--output-dir", required=True, help="Thư mục ghi output ($REPORT_OUTPUT_DIR)")
    parser.add_argument("--query", default="", help="Tìm kiếm từ khóa Outlook")
    parser.add_argument("--days", type=int, default=7, help="Số ngày gần nhất")
    parser.add_argument("--max-results", type=int, default=30, help="Số email tối đa")
    parser.add_argument("--subject", default="", help="Lọc theo subject")
    parser.add_argument("--from-addr", default="", help="Lọc theo người gửi")
    parser.add_argument("--slug", default="outlook_digest", help="Prefix tên file output")
    parser.add_argument("--user-request", default="", help="Yêu cầu tổng hợp của user")
    args = parser.parse_args()

    sd = scripts_dir()
    py = sys.executable
    cmd = [
        py,
        os.path.join(sd, "fetch_outlook.py"),
        "--output-dir",
        args.output_dir,
        "--days",
        str(args.days),
        "--max-results",
        str(args.max_results),
        "--slug",
        args.slug,
    ]
    if args.query:
        cmd.extend(["--query", args.query])
    if args.subject:
        cmd.extend(["--subject", args.subject])
    if args.from_addr:
        cmd.extend(["--from-addr", args.from_addr])
    if args.user_request:
        cmd.extend(["--user-request", args.user_request])

    print(f"\n{'=' * 60}\n▶ Outlook Digest Pipeline\n{'=' * 60}")
    print(" ", " ".join(cmd))
    result = subprocess.run(cmd)
    if result.returncode != 0:
        sys.exit(result.returncode)
    print("\n✅ Pipeline xong - AI Read file *_safe.json rồi tổng hợp theo user_request.")


if __name__ == "__main__":
    main()

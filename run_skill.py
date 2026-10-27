#!/usr/bin/env python3
"""
Skills Portal - Universal Skill Runner
Cho phép thực thi các skill trực tiếp từ dòng lệnh ở bất kỳ đâu.
Tự động nạp file .env, cấu hình PYTHONPATH, SKILL_DIR và REPORT_OUTPUT_DIR.
"""

import os
import sys
import subprocess
import argparse

HERE = os.path.dirname(os.path.abspath(__file__))
SKILLS_DIR = os.path.join(HERE, "skills")
OUTPUT_DIR = os.path.join(HERE, "outputs")
ENV_FILE = os.path.join(HERE, ".env")

# Entry point mapping cho các skill có script thực thi
SKILL_ENTRYPOINTS = {
    "jira-story-today-reviewer": {
        "script": "scripts/run_story_today_check.py",
        "desc": "Rà soát các Story có Start Date là hôm nay và chuyển In Progress"
    },
    "jira-subtask-reviewer": {
        "script": "scripts/run_subtask_check.py",
        "desc": "Rà soát các sub-task Jira (status In Review, Est == Spent)"
    },
    "jira-import": {
        "script": "scripts/jira_rest_importer.py",
        "desc": "Import Sprint Backlog từ JSON/Excel lên Jira"
    },
    "hrm-weekly-report": {
        "script": "scripts/run_hrm_report.py",
        "desc": "Chạy weekly report HRM và đồng bộ vào Excel Online / Google Sheets"
    },
    "weekly-report-api": {
        "script": "scripts/run_weekly_report.py",
        "desc": "Tạo báo cáo tiến độ tuần từ Jira / Google Sheets / Excel"
    },
    "outlook-digest": {
        "script": "scripts/run_outlook_digest.py",
        "desc": "Đọc email Outlook/Office 365, redact nội dung nhạy cảm và tổng hợp"
    },
    "project-assistant": {
        "script": "scripts/jira_query.py",
        "desc": "Tra cứu Jira (JQL, issue, active sprint) và email"
    },
    "prd-testcase-reviewer": {
        "script": "scripts/export_review_report.py",
        "desc": "Review Test Cases và xuất báo cáo so khớp PRD"
    },
    "vn-stock-advisor": {
        "script": "scripts/finbox_client.py",
        "desc": "Truy vấn tín hiệu và dữ liệu chứng khoán Finbox"
    },
    "sprint-planning": {
        "script": "scripts/build_sprint3.py",
        "desc": "Tạo Sprint Backlog FTI-SAL v3.1 Sprint 3, validate cache và xuất bộ file Excel & Markdown"
    }
}

def load_env_file(filepath):
    """Nạp file .env thủ công (không bắt buộc cài python-dotenv)."""
    if not os.path.isfile(filepath):
        return False
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                k, v = line.split("=", 1)
                k = k.strip()
                v = v.strip().strip("'\"")
                if k not in os.environ:
                    os.environ[k] = v
    return True

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # 1. Nạp file .env nếu có
    has_env = load_env_file(ENV_FILE)
    if not has_env:
        print("[!] Không tìm thấy file .env tại thư mục hiện hành.")
        print("    Mẹo: Bạn hãy mở file 'index.html' trên trình duyệt để cấu hình và bấm 'Xuất .env' lưu tại đây.\n")

    # 2. Xử lý tham số dòng lệnh
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help", "help", "list"):
        print("=" * 70)
        print("🎯 SKILLS PORTAL - UNIVERSAL RUNNER")
        print("=" * 70)
        print("\nCách sử dụng:")
        print("  python run_skill.py <tên-skill> [các tham số khác của script...]\n")
        print("Danh sách skill có script thực thi:")
        for name, meta in SKILL_ENTRYPOINTS.items():
            print(f"  • {name:<28} : {meta['desc']}")
        print("\nCác skill dạng guideline / prompt: pm-sprint-summary, product-backlog,")
        print("sprint-planning, sprint-timeline-chart (xem hướng dẫn tại index.html).")
        print("=" * 70)
        return

    skill_name = sys.argv[1].strip()
    extra_args = sys.argv[2:]

    if skill_name not in SKILL_ENTRYPOINTS:
        # Kiểm tra xem có phải thư mục trong skills/ không
        target_skill_dir = os.path.join(SKILLS_DIR, skill_name)
        if not os.path.isdir(target_skill_dir):
            print(f"[X] Không tìm thấy skill '{skill_name}'. Chạy 'python run_skill.py list' để xem danh sách.")
            sys.exit(1)
        else:
            print(f"[!] Skill '{skill_name}' không có script thực thi tự động mặc định.")
            print(f"    Bạn có thể mở index.html để xem quy trình thực hiện.")
            sys.exit(1)

    entry = SKILL_ENTRYPOINTS[skill_name]
    target_skill_dir = os.path.join(SKILLS_DIR, skill_name)
    script_path = os.path.join(target_skill_dir, entry["script"])

    if not os.path.isfile(script_path):
        print(f"[X] Script '{entry['script']}' không tồn tại tại {target_skill_dir}")
        sys.exit(1)

    # 3. Chuẩn bị môi trường (SKILL_DIR, REPORT_OUTPUT_DIR, PYTHONPATH)
    env = os.environ.copy()
    env["SKILL_DIR"] = target_skill_dir
    env["REPORT_OUTPUT_DIR"] = OUTPUT_DIR

    # Thêm skills vào PYTHONPATH để import _shared hoạt động mượt mà
    pythonpath = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = SKILLS_DIR + (os.pathsep + pythonpath if pythonpath else "")

    # Mặc định thêm tham số --output-dir nếu script hỗ trợ và chưa có trong args
    cmd = [sys.executable, script_path] + extra_args
    if "--output-dir" not in extra_args and "-o" not in extra_args:
        # Kiểm tra nếu script chấp nhận --output-dir
        cmd.extend(["--output-dir", OUTPUT_DIR])

    print("=" * 70)
    print(f"🚀 Đang chạy Skill: {skill_name}")
    print(f"📁 Thư mục Skill:   {target_skill_dir}")
    print(f"💾 Thư mục Output:  {OUTPUT_DIR}")
    print(f"⚙️  Lệnh thực thi:  {' '.join(cmd)}")
    print("=" * 70)

    try:
        proc = subprocess.run(cmd, cwd=target_skill_dir, env=env)
        sys.exit(proc.returncode)
    except KeyboardInterrupt:
        print("\n[!] Đã dừng thực thi.")
    except Exception as e:
        print(f"\n[X] Lỗi khi chạy skill: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

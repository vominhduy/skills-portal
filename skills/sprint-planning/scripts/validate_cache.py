#!/usr/bin/env python3
"""
validate_cache.py - Sprint Planning Skill
Đọc file JSON từ cache, validate cấu trúc + encoding, re-save đảm bảo UTF-8.

Usage:
    python3 scripts/validate_cache.py sprint{N}_backlog.json

Output:
    - In-place fix encoding
    - In ra summary: sprint_goal, số EPIC, số task, max effort, cross-month check
    - Exit code 0 nếu OK, 1 nếu có lỗi nghiêm trọng
"""

import json
import sys
import os
from datetime import datetime

WEEKDAYS = {"Mon", "Tue", "Wed", "Thu", "Fri"}


def check_weekends(data):
    """Kiểm tra start_date/due_date không rơi vào T7/CN."""
    issues = []
    for e in data.get("epics", []):
        for us in e.get("user_stories", []):
            for t in us.get("tasks", []):
                for field in ("start_date", "due_date"):
                    raw = t.get(field, "")
                    if not raw:
                        continue
                    try:
                        dt = datetime.strptime(raw, "%d/%m/%Y")
                        if dt.weekday() >= 5:
                            issues.append(
                                f"  ❌ [{t['pic']}] {t['task_name'][:50]} → {field}={raw} (T{dt.weekday()+2})"
                            )
                    except ValueError:
                        issues.append(f"  ❌ Sai format ngày: {field}={raw}")
    return issues


def check_cross_month(data):
    """Kiểm tra start_date và due_date phải cùng tháng (rule: không span qua tháng)."""
    issues = []
    for e in data.get("epics", []):
        for us in e.get("user_stories", []):
            for t in us.get("tasks", []):
                sd = t.get("start_date", "")
                dd = t.get("due_date", "")
                if not sd or not dd:
                    continue
                try:
                    s = datetime.strptime(sd, "%d/%m/%Y")
                    d = datetime.strptime(dd, "%d/%m/%Y")
                    if s.month != d.month or s.year != d.year:
                        issues.append(
                            f"  ❌ [{t['pic']}] {t['task_name'][:50]} → span qua tháng: {sd} → {dd}"
                        )
                except ValueError:
                    pass
    return issues


def check_weekend_span(data):
    """Kiểm tra task không span qua weekend (start và due phải cùng tuần LV T2–T6)."""
    from datetime import timedelta
    issues = []
    for e in data.get("epics", []):
        for us in e.get("user_stories", []):
            for t in us.get("tasks", []):
                sd = t.get("start_date", "")
                dd = t.get("due_date", "")
                if not sd or not dd:
                    continue
                try:
                    s = datetime.strptime(sd, "%d/%m/%Y")
                    d = datetime.strptime(dd, "%d/%m/%Y")
                    # Nếu start và due khác tuần ISO -> span qua weekend
                    if s.isocalendar()[1] != d.isocalendar()[1] or s.isocalendar()[0] != d.isocalendar()[0]:
                        issues.append(
                            f"  ❌ [{t['pic']}] {t['task_name'][:50]} → span qua weekend: {sd} → {dd}"
                        )
                except ValueError:
                    pass
    return issues


def check_effort(data):
    """Kiểm tra effort mỗi task không vượt 24h và thời lượng không quá 3 ngày làm việc."""
    from datetime import timedelta
    issues = []
    for e in data.get("epics", []):
        for us in e.get("user_stories", []):
            for t in us.get("tasks", []):
                h = t.get("est_effort_hour", 0)
                pic = t.get("pic", "?")
                task_name = t.get("task_name", "")[:50]
                if h > 24:
                    issues.append(
                        f"  ❌ [{pic}] {task_name} → est_effort_hour={h}h (> 24h)"
                    )
                sd = t.get("start_date", "")
                dd = t.get("due_date", "")
                if sd and dd:
                    try:
                        s = datetime.strptime(sd, "%d/%m/%Y")
                        d = datetime.strptime(dd, "%d/%m/%Y")
                        cur = s
                        wds = 0
                        while cur <= d:
                            if cur.weekday() < 5:
                                wds += 1
                            cur += timedelta(days=1)
                        if wds > 3:
                            issues.append(
                                f"  ❌ [{pic}] {task_name} → kéo dài {wds} ngày làm việc (> 3 working days: {sd} → {dd})"
                            )
                    except ValueError:
                        pass
    return issues


def check_even_effort(data):
    """Kiểm tra tất cả est_effort_hour phải là 4, 8, 16 hoặc 24 (ưu tiên 8h) (v2.10)."""
    issues = []
    for e in data.get("epics", []):
        for us in e.get("user_stories", []):
            for t in us.get("tasks", []):
                h = t.get("est_effort_hour", 0)
                if h not in {4, 8, 16, 24}:
                    issues.append(
                        f"  ❌ [{t['pic']}] {t['task_name'][:50]} → est_effort_hour={h}h (chỉ được 4, 8, 16 hoặc 24, ưu tiên 8h)"
                    )
    return issues


def check_ba_in_init_sprint(data):
    """
    Quy tắc Feature-Centric v2.10: Các phase (init, QC test, pentest, UAT, pilot) đều nằm trong Story tính năng.
    Không còn hạn chế task BA chỉ được ở EPIC-0.
    """
    return []


def check_epic0_exists(data):
    """
    Quy tắc Feature-Centric v2.10: Story là tính năng lớn (tương đương EPIC).
    Các task init (BA analysis, DEV setup, PM kick-off) được tích hợp trực tiếp vào Story tính năng,
    không bắt buộc phải có EPIC-0 độc lập.
    """
    return []


def check_roles(data):
    """Kiểm tra mọi User Story tính năng lớn đều có task của DEV."""
    issues = []
    epics = data.get("epics", [])
    if not epics:
        return issues
    for e in epics:
        epic_name = e.get("epic", "") or ""
        for us in e.get("user_stories", []):
            pics = {(t.get("pic", "") or "") for t in us.get("tasks", [])}
            # Skip US thuần documentation (nếu có)
            if pics == {"BA"} or pics == {"PM"}:
                continue
            has_dev = any(p.startswith("DEV") for p in pics)
            if not has_dev:
                issues.append(f"  ⚠️  {us.get('us_id', '?')} thiếu task DEV")
    return issues

def check_us_description(data):
    """Kiểm tra description của User Story: không dùng 'Là [Role]...', độ dài súc tích ~8-12 từ."""
    issues = []
    warnings = []
    for e in data.get("epics", []):
        for us in e.get("user_stories", []):
            desc = (us.get("description", "") or "").strip()
            us_id = us.get("us_id", "?")
            if not desc:
                continue
            # Rule 1: Không dùng dạng persona agile
            if desc.lower().startswith("là ") or "tôi muốn" in desc.lower():
                issues.append(f"  ❌ [{us_id}] description dùng dạng persona 'Là [Role]...': \"{desc[:50]}...\"")
            # Rule 2: Độ dài tầm 8-12 từ (cảnh báo nếu > 15 từ)
            words = desc.split()
            if len(words) > 15:
                warnings.append(f"  ⚠️  [{us_id}] description dài ({len(words)} từ, chuẩn: 8-12 từ): \"{desc[:50]}...\"")
    return issues, warnings


def summarize(data):
    from collections import defaultdict
    hours = defaultdict(float)
    total_tasks = 0
    max_h = 0
    for e in data.get("epics", []):
        for us in e.get("user_stories", []):
            for t in us.get("tasks", []):
                total_tasks += 1
                h = t.get("est_effort_hour", 0) or 0
                max_h = max(max_h, h)
                role = t.get("pic", "") or ""
                if role.startswith("DEV"):
                    role = "DEV"
                elif role.startswith("QA") or role.startswith("QC"):
                    role = "QC"
                hours[role] += h

    subtotal_h = sum(hours.values())
    subtotal_md = subtotal_h / 8
    buffer_md = subtotal_md * 0.10
    total_net_md = subtotal_md + buffer_md

    print(f"\n{'='*55}")
    print(f"  Sprint {data.get('sprint_number')} - {data.get('project', '')[:40]}")
    print(f"{'='*55}")
    print(f"  Goal   : {data.get('sprint_goal', '')[:70]}")
    print(f"  Stories: {len(data.get('epics', []))}")
    print(f"  Tasks  : {total_tasks}  |  Max effort/task: {max_h}h")
    print(f"\n  Manday Summary:")
    for r in ["PM", "BA", "DEV", "QC"]:
        h = hours.get(r, 0)
        md = h / 8
        pct = (h / subtotal_h * 100) if subtotal_h else 0
        print(f"    {r:4s} : {h:6.1f}h = {md:5.2f} MD ({pct:.1f}%)")
    print(f"    {'─'*36}")
    print(f"    Sub  : {subtotal_h:6.1f}h = {subtotal_md:5.2f} MD")
    print(f"    +10% :        +{buffer_md:5.2f} MD")
    print(f"    Net  :         {total_net_md:5.2f} MD → Sprint ~{total_net_md/3:.1f} ngày")
    print(f"{'='*55}\n")


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 validate_cache.py <path_to_json>")
        sys.exit(1)

    path = sys.argv[1]
    if not os.path.exists(path):
        print(f"❌ File không tồn tại: {path}")
        sys.exit(1)

    # 1. Đọc file (detect encoding issues)
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            raw = f.read()
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"❌ JSON không hợp lệ: {e}")
        sys.exit(1)

    # 2. Re-save đảm bảo UTF-8 + ensure_ascii=False
    with open(path, "w", encoding="utf-8", errors="replace") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    # 3. Kiểm tra các ràng buộc
    errors = []
    errors += check_weekends(data)
    errors += check_effort(data)
    errors += check_even_effort(data)
    errors += check_cross_month(data)
    errors += check_weekend_span(data)
    errors += check_ba_in_init_sprint(data)
    errors += check_epic0_exists(data)
    desc_errors, desc_warnings = check_us_description(data)
    errors += desc_errors
    warnings = check_roles(data) + desc_warnings

    # 4. In summary
    summarize(data)

    if warnings:
        print("⚠️  Warnings:")
        for w in warnings:
            print(w)
        print()

    if errors:
        print("❌ Lỗi cần sửa trước khi xuất Excel:")
        for err in errors:
            print(err)
        sys.exit(1)

    print("✅ Cache hợp lệ - sẵn sàng xuất Excel.")


if __name__ == "__main__":
    main()

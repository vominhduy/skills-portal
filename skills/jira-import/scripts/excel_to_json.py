#!/usr/bin/env python3
"""
Script chuyển đổi sheet Sprint từ Excel Product Backlog sang JSON
Tác giả: Grok Assistant
Cập nhật: 2026-05-07
"""

import sys
import os
import json
import warnings
from datetime import datetime
from pathlib import Path
from openpyxl import load_workbook

# ============================================================
# CẤU HÌNH MẶC ĐỊNH (sẽ bị ghi đè nếu truyền argv)
# ============================================================
DEFAULT_EXCEL = "ISC_FTI-SAL_v3.1 Sprint 2_Project Plan_v1.0.xlsx"
DEFAULT_OUTPUT = "FTI-SAL_Sprint2.json"
DEFAULT_SHEET = "Plan"

# Các tham số bạn vừa gửi
DEFAULT_PROJECT        = "FSM"
DEFAULT_PARENT_REQUEST = "FSM-104"
DEFAULT_FIX_VERSION    = "Release - v2.0 Sprint 2"
DEFAULT_DIVISION       = "FTI"
DEFAULT_SPRINT_NAME    = "Sprint - v2.0 Sprint 2"

# ==================== CỘT TRONG EXCEL ====================
COL_US_ID            = 1
COL_MODULE           = 2   # B MODULE
COL_TASK             = 3   # C TASK NAME
COL_DESCRIPTION      = 4   # D DESCRIPTION
COL_PIC              = 5   # E PIC
COL_START_DATE       = 7   # G START DATE
COL_DUE_DATE         = 8   # H DUE DATE
COL_EFFORT_HOUR      = 9   # I EFFORT (Hour)
COL_NOTE             = 10  # J NOTE
COL_TASK_COMPLEXITY  = 11  # K TASK COMPLEXITY
COL_TYPE_OF_WORK     = 12  # L Type OF WORK
COL_TASK_PROCESS     = 13  # M TASK PROCESS
COL_TASK_PRIORITY    = 14  # N TASK PRIORITY


def parse_date(d):
    if isinstance(d, datetime):
        return d.strftime("%Y-%m-%d")
    if d:
        return str(d)[:10]
    return None


def map_priority(p):
    if not p:
        return "Medium"
    p = str(p).strip().lower()
    if "highest" in p or "4-" in p or "critical" in p:
        return "Highest"
    if "high" in p or "hight" in p or "3-" in p:
        return "High"
    if "medium" in p or "2-" in p:
        return "Medium"
    if "low" in p or "1-" in p:
        return "Low"
    if "lowest" in p:
        return "Lowest"
    return "Medium"


def format_estimate(hours):
    if not hours:
        return "0h"
    try:
        val = float(hours)
        s = f"{val:.2f}".rstrip("0").rstrip(".")
        return f"{s}h"
    except:
        return "0h"


def calculate_story_point(sum_hour, prio_raw, comp_raw):
    e = (float(sum_hour) / 8) if sum_hour else 0.0
    try:
        p_digit = int(str(prio_raw).strip()[0]) if str(prio_raw).strip() else 2
        p = p_digit * 2
    except:
        p = 4
    try:
        c_digit = int(str(comp_raw).strip()[0]) if str(comp_raw).strip() else 2
        c = c_digit * 2
    except:
        c = 4
    avg = (e + p + c) / 3
    return round(avg, 1)


def infer_task_process(module, task):
    m = (module or "").lower().strip()
    t = (task or "").lower().strip()

    # 1. Unit Test luôn có độ ưu tiên cao
    if "unit test" in t or "unit test" in m:
        return "Unit Test"

    # 2. Match theo module trước
    if "project management" in m:
        return "Project Management"
    if "sprint ceremonies" in m:
        if any(k in t for k in ["đóng gói", "release package", "deploy", "build"]):
            return "Deployment"
        return "Project Management"
    if any(k in m for k in ["requirement", "analysis", "architecture", "database", "design"]):
        return "Requirement & Design"
    if "uat" in m or "user guide" in m or "user doc" in m:
        return "UAT"
    if "qc" in m or "test" in m or "testing" in m:
        if any(k in t for k in ["deploy", "build staging"]):
            return "Deployment"
        return "Testing"

    # 3. Phân loại theo task nếu module là generic dev
    if any(k in t for k in ["viết testcase", "testcase", "qc test", "regression test"]):
        return "Testing"
    if any(k in t for k in ["uat", "user guide"]):
        return "UAT"
    if any(k in t for k in ["thiết kế wireframe", "thiết kế ui", "thiết kế database", "phân tích yêu cầu", "viết prd"]):
        return "Requirement & Design"
    if any(k in t for k in ["đóng gói", "deploy", "release"]):
        return "Deployment"

    return "Coding"


def infer_type_of_work(task):
    t = (task or "").lower()
    if "review" in t:
        return "Review"
    if any(k in t for k in ["fix bug", "rework", "sửa lỗi", "recheck bug"]):
        return "Fix/Rework"
    if any(k in t for k in ["nghiên cứu", "tìm hiểu", "study", "research"]):
        return "Study"
    return "Do"


def main():
    warnings.filterwarnings("ignore")

    # ==================== NHẬN THAM SỐ TỪ ARGV ====================
    excel_path  = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_EXCEL
    output_json = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_OUTPUT
    sheet_name  = sys.argv[3] if len(sys.argv) > 3 and sys.argv[3].strip() else DEFAULT_SHEET

    # 5 tham số bạn yêu cầu (tất cả đều là argv)
    PROJECT        = sys.argv[4] if len(sys.argv) > 4 else DEFAULT_PROJECT
    PARENT_REQUEST = sys.argv[5] if len(sys.argv) > 5 else DEFAULT_PARENT_REQUEST
    FIX_VERSION    = sys.argv[6] if len(sys.argv) > 6 else DEFAULT_FIX_VERSION
    DIVISION       = sys.argv[7] if len(sys.argv) > 7 else DEFAULT_DIVISION
    SPRINT_NAME    = sys.argv[8] if len(sys.argv) > 8 else DEFAULT_SPRINT_NAME
    # Board name (tùy chọn) - dùng khi sprint rỗng, JQL không tìm được sprint ID.
    BOARD_NAME     = sys.argv[9] if len(sys.argv) > 9 else None

    print(f"📖 Đang đọc Excel : {excel_path}")
    print(f"   Sheet         : {sheet_name}")
    print(f"   Project       : {PROJECT}")
    print(f"   Parent        : {PARENT_REQUEST}")
    print(f"   FixVersion    : {FIX_VERSION}")
    print(f"   Division      : {DIVISION}")
    print(f"   Sprint        : {SPRINT_NAME}")
    if BOARD_NAME:
        print(f"   Board         : {BOARD_NAME}\n")
    else:
        print()

    if not os.path.exists(excel_path):
        print(f"❌ Không tìm thấy file: {excel_path}")
        return

    wb = load_workbook(excel_path, data_only=False)

    # Validate & resolve sheet: Ưu tiên sheet_name nếu có, fallback "Plan" hoặc case-insensitive
    target_sheet = None
    if sheet_name in wb.sheetnames:
        target_sheet = sheet_name
    else:
        for s in wb.sheetnames:
            if s.strip().lower() == sheet_name.strip().lower():
                target_sheet = s
                break
        if not target_sheet:
            for s in wb.sheetnames:
                if s.strip().lower() == "plan":
                    target_sheet = s
                    break
        if not target_sheet and len(wb.sheetnames) > 0:
            for s in wb.sheetnames:
                if "plan" in s.lower():
                    target_sheet = s
                    break

    if not target_sheet:
        print(f"❌ Sheet '{sheet_name}' không tồn tại. Các sheet có: {wb.sheetnames}")
        return
    ws = wb[target_sheet]
    if target_sheet != sheet_name:
        print(f"   ℹ️ Đã tự động chọn sheet: '{target_sheet}'")

    # Tự động tìm dòng header (quét dòng 1-15)
    header_row_idx = None
    for r in range(1, 15):
        row_text = " ".join(str(ws.cell(row=r, column=c).value or "").lower() for c in range(1, 12))
        if ("module" in row_text or "main task" in row_text) and ("task name" in row_text or "description" in row_text):
            header_row_idx = r
            break
        if "user story id" in row_text or "us_id" in row_text:
            header_row_idx = r
            break

    if not header_row_idx:
        header_row_idx = 8 if ws.max_row >= 8 else 6
    print(f"   Dòng Header   : Dòng {header_row_idx}")

    stories = []
    current_story = None
    current_sum_hour = 0.0
    current_priority = "Medium"
    current_prio_raw = None
    current_comp_raw = None
    current_start_dates = []
    current_due_dates = []

    start_row = header_row_idx + 1
    for row_idx in range(start_row, ws.max_row + 1):
        module = ws.cell(row=row_idx, column=COL_MODULE).value or ""
        task = ws.cell(row=row_idx, column=COL_TASK).value or ""
        module_str = str(module).strip()
        task_str = str(task).strip()

        # Dừng nếu gặp section Timeline & Milestones hoặc kết thúc danh sách task
        if module_str.lower().startswith("timeline"):
            break

        if not module_str and not task_str:
            continue

        col_i = ws.cell(row=row_idx, column=COL_EFFORT_HOUR).value or ""
        is_epic = (isinstance(col_i, str) and "SUM" in col_i.upper()) or (module_str.upper().startswith("EPIC") and not task_str)

        if is_epic:
            if current_story:
                # Lấy trung bình priority/complexity từ các subtask đã có
                if current_story.get("subtasks"):
                    priorities = []
                    complexities = []
                    for sub in current_story["subtasks"]:
                        p_raw = sub.get("priority", "Medium")
                        if isinstance(p_raw, int):
                            priorities.append(p_raw)
                        elif isinstance(p_raw, str) and p_raw.strip().isdigit():
                            priorities.append(int(p_raw.strip()))
                        else:
                            mapped = map_priority(p_raw)
                            priorities.append({"Lowest":1,"Low":2,"Medium":3,"High":4,"Highest":5}.get(mapped,3))
                        c_raw = sub.get("complexity", 3)
                        if isinstance(c_raw, int):
                            complexities.append(c_raw)
                        elif isinstance(c_raw, str) and c_raw.replace('.','',1).isdigit():
                            complexities.append(int(float(c_raw)))
                        else:
                            complexities.append(3)
                    avg_p = sum(priorities)/len(priorities) if priorities else 2
                    avg_c = sum(complexities)/len(complexities) if complexities else 3
                    current_prio_raw = int(round(avg_p))
                    current_comp_raw = int(round(avg_c))
                current_story["storyPoint"] = calculate_story_point(current_sum_hour, current_prio_raw, current_comp_raw)
                current_story["effortPlan"] = current_sum_hour
                current_story["originalEstimate"] = format_estimate(current_sum_hour)
                if current_start_dates: current_story["startDate"] = min(d for d in current_start_dates if d)
                if current_due_dates: current_story["dueDate"] = max(d for d in current_due_dates if d)
                stories.append(current_story)

            epic_raw = module_str
            epic_summary = epic_raw.split(". ", 1)[-1].strip() if ". " in epic_raw else epic_raw
            current_story = {"summary": epic_summary, "description": epic_raw, "subtasks": [], "priority": "Medium"}
            current_sum_hour = 0.0
            current_priority = "Medium"
            current_prio_raw = None
            current_comp_raw = None
            current_start_dates = []
            current_due_dates = []
            continue

        if current_story and task_str:
            try:
                current_sum_hour += float(ws.cell(row=row_idx, column=COL_EFFORT_HOUR).value or 0)
            except:
                pass
            s_d = parse_date(ws.cell(row=row_idx, column=COL_START_DATE).value)
            d_d = parse_date(ws.cell(row=row_idx, column=COL_DUE_DATE).value)
            if s_d: current_start_dates.append(s_d)
            if d_d: current_due_dates.append(d_d)
            current_story["subtasks"].append(create_subtask(ws, row_idx, current_priority, module=module_str))

    # Lưu User Story cuối cùng
    if current_story:
        story_point = calculate_story_point(current_sum_hour, current_prio_raw, current_comp_raw)
        current_story["storyPoint"] = story_point
        current_story["effortPlan"] = current_sum_hour
        current_story["originalEstimate"] = format_estimate(current_sum_hour)

        if current_start_dates:
            current_story["startDate"] = min(d for d in current_start_dates if d)
        if current_due_dates:
            current_story["dueDate"] = max(d for d in current_due_dates if d)
        # Thêm Review Complexity cho Story từ trung bình subtask
        if current_story.get("subtasks"):
            comp_vals = [sub.get("complexity", 3) for sub in current_story["subtasks"]]
            current_story["customfield_10824"] = sum(comp_vals)/len(comp_vals) if comp_vals else 3
        else:
            current_story["customfield_10824"] = (current_comp_raw if current_comp_raw is not None else 3)

        stories.append(current_story)

    # ==================== XUẤT JSON ====================
    # Nếu SPRINT_NAME rỗng hoặc "không" → không gán Sprint (import dưới Epic)
    sprint_value = None if (not SPRINT_NAME or str(SPRINT_NAME).strip().lower() == "không") else SPRINT_NAME
    result = {
        "project": PROJECT,
        "parentRequest": PARENT_REQUEST,
        "fixVersion": FIX_VERSION,
        "division": DIVISION,
        "sprint": sprint_value,
        "boardName": BOARD_NAME if sprint_value else None,
        "stories": stories
    }

    Path(output_json).parent.mkdir(parents=True, exist_ok=True)
    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"\n✅ HOÀN TẤT!")
    print(f"   File JSON     : {output_json}")
    print(f"   Số User Story : {len(stories)}")
    total_tasks = sum(len(s.get("subtasks", [])) for s in stories)
    print(f"   Tổng Sub-task : {total_tasks}")


def create_subtask(ws, row_idx, default_priority, module=""):
    # Lấy effort (I) - phải là float cho customfield_10867
    try:
        eff_val = float(ws.cell(row=row_idx, column=COL_EFFORT_HOUR).value or 0)
    except:
        eff_val = 0.0
    # Lấy complexity (K) - phải là int/float cho customfield_10824
    comp_raw = ws.cell(row=row_idx, column=COL_TASK_COMPLEXITY).value
    if isinstance(comp_raw, (int, float)):
        comp_val = int(comp_raw)
    elif isinstance(comp_raw, str) and comp_raw.strip().replace('.','',1).isdigit():
        comp_val = int(float(comp_raw))
    else:
        comp_val = 3

    task_name = str(ws.cell(row=row_idx, column=COL_TASK).value or "").strip()
    desc_val = str(ws.cell(row=row_idx, column=COL_DESCRIPTION).value or "").strip()
    note_val = str(ws.cell(row=row_idx, column=COL_NOTE).value or "").strip()
    if note_val:
        full_desc = f"{desc_val}\n\nNote: {note_val}" if desc_val else f"Note: {note_val}"
    else:
        full_desc = desc_val

    raw_process = ws.cell(row=row_idx, column=COL_TASK_PROCESS).value
    task_process = str(raw_process).strip() if raw_process else infer_task_process(module, task_name)

    raw_work = ws.cell(row=row_idx, column=COL_TYPE_OF_WORK).value
    type_of_work = str(raw_work).strip() if raw_work else infer_type_of_work(task_name)

    raw_priority = ws.cell(row=row_idx, column=COL_TASK_PRIORITY).value
    priority = map_priority(raw_priority) if raw_priority else default_priority

    return {
        "summary": task_name,                                       # C (TASK NAME)
        "description": full_desc,                                   # D (DESCRIPTION) + J (NOTE)
        "assignee": str(ws.cell(row=row_idx, column=COL_PIC).value or "").strip(),  # E (PIC)
        "startDate": parse_date(ws.cell(row=row_idx, column=COL_START_DATE).value), # G
        "dueDate": parse_date(ws.cell(row=row_idx, column=COL_DUE_DATE).value),     # H
        "originalEstimate": eff_val,  # I (EFFORT) - số (float) cho Plan Effort
        "effortPlan": eff_val,        # alias cho customfield_10867
        "customfield_10824": comp_val,  # Review Complexity (số)
        "customfield_10867": eff_val,   # Plan Effort (số)
        "priority": priority,         # N (TASK PRIORITY) hoặc default
        "type": "Normal",
        "typeOfWork": type_of_work,   # L hoặc infer ("Do", "Review", "Fix/Rework")
        "taskProcess": task_process,  # M hoặc infer ("Coding", "Testing", "Project Management", ...)
        "complexity": comp_val
    }


if __name__ == "__main__":
    main()

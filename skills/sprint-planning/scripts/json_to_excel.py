#!/usr/bin/env python3
"""
json_to_excel.py - Convert sprint backlog JSON to Excel.
Supports two formats:
  - New: Matching "Plan" sheet template (default) but each epic = phase
  - Old: Legacy format (with --old-format flag)
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill, Border, Side
from openpyxl.formatting.rule import CellIsRule
from openpyxl.worksheet.datavalidation import DataValidation

# ====================== CẤU HÌNH ======================
def parse_args():
    parser = argparse.ArgumentParser(description='Convert sprint backlog JSON to Excel')
    parser.add_argument('json_file', nargs='?', default='sprint1_backlog.json',
                        help='Path to sprint backlog JSON file')
    parser.add_argument('output_file', nargs='?', default=None,
                        help='Optional positional output Excel file path')
    parser.add_argument('-o', '--output', default=None,
                        help='Output Excel file path (default: Sprint_Plan_Raw.xlsx)')
    parser.add_argument('--old-format', action='store_true',
                        help='Output in legacy format (default: new template format)')
    parser.add_argument('--output-dir', default=None,
                        help='Output directory injected by webapp')
    return parser.parse_known_args()[0]

_shared_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "_shared"))
if _shared_dir not in sys.path:
    sys.path.insert(0, _shared_dir)
from output_path import ensure_versioned_path, resolve_input_path

args = parse_args()
JSON_FILE = resolve_input_path(args.json_file)
USE_OLD_FORMAT = args.old_format

# Auto-create sheet name from JSON file (sprint1_backlog.json → Sprint 1)
_match = re.search(r'sprint(\d+)', JSON_FILE, re.IGNORECASE)
_sprint_num = _match.group(1) if _match else "1"
NEW_SHEET_NAME = f"Sprint {_sprint_num}"
_raw_excel_file = args.output or args.output_file or "Sprint_Plan_Raw.xlsx"
if args.output_dir and not os.path.isabs(_raw_excel_file):
    _raw_excel_file = os.path.join(args.output_dir, os.path.basename(_raw_excel_file))
EXCEL_FILE = ensure_versioned_path(_raw_excel_file)


try:
    from openpyxl.cell.rich_text import CellRichText, TextBlock, InlineFont
    HAS_RICH_TEXT = True
except (ImportError, ModuleNotFoundError):
    HAS_RICH_TEXT = False
    CellRichText = None
    TextBlock = None
    InlineFont = None

def optimize_for_excel_online(file_path):
    try:
        _shared_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "_shared"))
        if _shared_dir not in sys.path:
            sys.path.insert(0, _shared_dir)
        from xlsx_normalizer import normalize_xlsx_file
        normalize_xlsx_file(file_path)
    except Exception:
        pass

# ==================== MÀU SẮC ====================
# Colors for new template format
COLOR_DARK_BLUE = PatternFill(start_color="0B5394", end_color="0B5394", fill_type="solid")  # Row 7
COLOR_LIGHT_GRAY = PatternFill(start_color="F3F3F3", end_color="F3F3F3", fill_type="solid")   # Row 8
COLOR_PHASE_GRAY = PatternFill(start_color="CCCCCC", end_color="CCCCCC", fill_type="solid")  # Phase headers
FONT_WHITE_BOLD = Font(bold=True, color="FFFFFF", size=13, name="Calibri")
FONT_DARK_BLUE_BOLD = Font(bold=True, color="0B5394", size=12, name="Calibri")
FONT_PHASE_BOLD = Font(bold=True, color="000000", size=13, name="Calibri")
FONT_NORMAL = Font(color="000000", size=11, name="Calibri")
FONT_PROJECT_TITLE = Font(bold=True, size=14, color="0B5394", name="Calibri")
FONT_HEADER_LABEL = Font(bold=True, size=11, color="0B5394", name="Calibri")

# Colors for legacy format (from original script)
COLOR_HEADER_LEGACY = PatternFill(start_color="D6DCE4", end_color="D6DCE4", fill_type="solid")
COLOR_EPIC_LEGACY = PatternFill(start_color="FFE598", end_color="FFE598", fill_type="solid")
COLOR_DONE_LEGACY = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
COLOR_INPROGRESS_LEGACY = PatternFill(start_color="F4B084", end_color="F4B084", fill_type="solid")
COLOR_PENDING_LEGACY = PatternFill(start_color="A6A6A6", end_color="A6A6A6", fill_type="solid")
COLOR_NOTSTARTED_LEGACY = PatternFill(start_color="EFF6FB", end_color="EFF6FB", fill_type="solid")
COLOR_CRITICAL_LEGACY = PatternFill(start_color="FF0000", end_color="FF0000", fill_type="solid")
COLOR_HIGH_LEGACY = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")
COLOR_MEDIUM_LEGACY = PatternFill(start_color="FFF2CC", end_color="FFF2CC", fill_type="solid")
COLOR_LOW_LEGACY = PatternFill(start_color="DDEBF7", end_color="DDEBF7", fill_type="solid")
COLOR_DARK_HEADER_LEGACY = PatternFill(start_color="305496", end_color="305496", fill_type="solid")

# ==================== BORDER ====================
thin = Side(style='thin')
dashed = Side(style='dashed')
thin_border = Border(left=thin, right=thin, top=thin, bottom=thin)
hair = Side(style='hair')
hair_border = Border(left=hair, right=hair, top=hair, bottom=hair)

dashed_border = Border(left=dashed, right=dashed, top=dashed, bottom=dashed)

DATE_FORMAT = 'ddd, MMM D, YY'

# ==================== HÀM HỖ TRỢ ====================
def clean_text(text):
    if isinstance(text, str):
        return (text
                .replace("—", "-")
                .replace("–", "-")
                .replace("‐", "-")
                .replace("‑", "-"))
    return text

def clean_json_data(obj):
    if isinstance(obj, str):
        return clean_text(obj)
    elif isinstance(obj, list):
        return [clean_json_data(item) for item in obj]
    elif isinstance(obj, dict):
        return {key: clean_json_data(value) for key, value in obj.items()}
    else:
        return obj

def parse_date(date_str):
    if not date_str or str(date_str).strip() == "":
        return None
    try:
        return datetime.strptime(str(date_str).strip(), "%d/%m/%Y")
    except:
        return None

def load_backlog_data():
    if not os.path.exists(JSON_FILE):
        print(f"❌ Không tìm thấy file JSON: {JSON_FILE}")
        return None
    with open(JSON_FILE, 'r', encoding='utf-8') as f:
        raw_json = f.read()
        cleaned_json = clean_text(raw_json)
        data = json.loads(cleaned_json)
    data = clean_json_data(data)
    return data

# ==================== NEW FORMAT (EPIC AS PHASE) ====================
def create_plan_sheet_excel():
    """Create Excel in new template format where each epic = a phase"""
    data = load_backlog_data()
    if not data:
        return

    wb = Workbook()
    ws = wb.active
    ws.title = NEW_SHEET_NAME

    # ==================== COLUMN WIDTHS (theo template) ====================
    ws.column_dimensions['A'].width = 3
    ws.column_dimensions['B'].width = 21.57
    ws.column_dimensions['C'].width = 36.43
    ws.column_dimensions['D'].width = 41.14
    ws.column_dimensions['E'].width = 15
    ws.column_dimensions['F'].width = 11
    ws.column_dimensions['G'].width = 18.71
    ws.column_dimensions['H'].width = 18.71
    ws.column_dimensions['I'].width = 13.57
    ws.column_dimensions['J'].width = 24
    ws.column_dimensions['K'].width = 12
    ws.column_dimensions['L'].width = 12
    ws.column_dimensions['M'].width = 12
    ws.column_dimensions['N'].width = 12

    # ==================== HEADER AREA (Rows 1-6) ====================
    project_name = data.get("project", "Project")
    sprint_goal = data.get("sprint_goal", "")
    sprint_number = data.get("sprint_number", _sprint_num)

    # Row 1: Project name - rich text: [] đỏ ED7D31, Project Planning ➜ xanh 0B5394
    if HAS_RICH_TEXT:
        ws['B1'] = CellRichText(
            TextBlock(InlineFont(sz=24, b=True, color="ED7D31"), f"[{project_name} Sprint {sprint_number}] "),
            TextBlock(InlineFont(sz=24, b=True, color="0B5394"), "Project Planning ➜")
        )
    else:
        ws['B1'] = f"[{project_name} Sprint {sprint_number}] Project Planning ➜"
        ws['B1'].font = Font(name="Calibri", sz=18, bold=True, color="0B5394")
    ws['B1'].alignment = Alignment(horizontal="left", vertical="center")
    ws['B1'].alignment = Alignment(horizontal="left", vertical="center")
    ws.merge_cells('B1:J1')

    # Row 3: Goal / Start Date
    ws['B3'] = "Goal"
    ws['B3'].font = Font(name="Calibri", bold=True, size=14, color="000000")
    ws.merge_cells('C3:F3')
    ws['C3'] = sprint_goal
    ws['C3'].font = FONT_NORMAL
    ws['C3'].alignment = Alignment(wrap_text=True, vertical="top")
    ws['G3'] = "Start Date"
    ws['G3'].font = Font(name="Calibri", bold=True, size=14, color="000000")
    ws['G3'].alignment = Alignment(horizontal="left", vertical="center")
    ws['H3'] = '=MIN(G9:G{last_row})'  # placeholder, will update later
    ws['H3'].font = FONT_NORMAL
    ws['H3'].number_format = DATE_FORMAT
    ws['H3'].alignment = Alignment(horizontal="center", vertical="center")

    # Row 4: Output/Module / Due Date
    ws['B4'] = "Output/ Module"
    ws['B4'].font = Font(name="Calibri", bold=True, size=14, color="000000")
    ws.merge_cells('C4:F4')
    time_box = data.get("time_box", "Sprint Backlog")
    time_box_text = "\n".join(str(item).strip() for item in time_box) if isinstance(time_box, list) else str(time_box)
    ws['C4'] = time_box_text
    ws['C4'].font = FONT_NORMAL
    ws['C4'].alignment = Alignment(wrap_text=True, vertical="top")
    ws['G4'] = "Due Date"
    ws['G4'].font = Font(name="Calibri", bold=True, size=14, color="000000")
    ws['G4'].alignment = Alignment(horizontal="left", vertical="center")
    ws['H4'] = '=MAX(G9:G{last_row})'  # placeholder
    ws['H4'].font = FONT_NORMAL
    ws['H4'].number_format = DATE_FORMAT
    ws['H4'].alignment = Alignment(horizontal="center", vertical="center")

    # Row 5: Description / Total Effort
    ws['B5'] = "Description"
    ws['B5'].font = Font(name="Calibri", bold=True, size=14, color="000000")
    ws.merge_cells('C5:F5')
    ws['C5'] = sprint_goal
    ws['C5'].font = FONT_NORMAL
    ws['C5'].alignment = Alignment(wrap_text=True, vertical="top")
    ws['G5'] = "Total Effort"
    ws['G5'].font = Font(name="Calibri", bold=True, size=14, color="000000")
    ws['G5'].alignment = Alignment(horizontal="left", vertical="center")
    ws['H5'] = '=SUM(I9:I{last_row})/2'  # placeholder
    ws['H5'].font = FONT_NORMAL
    ws['H5'].number_format = '0.0'
    ws['H5'].alignment = Alignment(horizontal="center", vertical="center")

    ws.row_dimensions[3].height = 30
    ws.row_dimensions[4].height = 30
    ws.row_dimensions[5].height = 30

    # Row 6: Empty spacer
    ws.row_dimensions[6].height = 10

    # Row 7: PROJECT DETAILS header
    for col in range(2, 15):  # B-N
        cell = ws.cell(row=7, column=col)
        cell.fill = COLOR_DARK_BLUE
        cell.font = FONT_WHITE_BOLD
        cell.alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)
        # Plan: no border for row 7
    ws['B7'] = "PROJECT DETAILS"
    ws['B7'].alignment = Alignment(horizontal="left", vertical="center")
    ws.merge_cells('B7:N7')
    ws.row_dimensions[7].height = 25
    # Plan: no border for row 7 / 8 header area

    # Row 8: Column headers
    headers = [
        "MODULE/ MAIN TASK",   # B
        "TASK NAME",            # C
        "DESCRIPTION",           # D (fill từ user story description)
        "PIC",                  # E
        "% DONE",               # F
        "START DATE",           # G
        "DUE DATE",             # H
        "EFFORT (Hour)",        # I
        "NOTE",                 # J (task note)
        "TASK COMPLEXITY",      # K
        "Type OF WORK",         # L
        "TASK PROCESS",         # M
        "TASK PRIORITY",        # N
    ]
    for idx, header in enumerate(headers, start=2):  # B=2
        cell = ws.cell(row=8, column=idx, value=header)
        cell.fill = COLOR_LIGHT_GRAY
        cell.font = FONT_DARK_BLUE_BOLD
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        # Plan: no border for row 8 (column headers)
    ws.row_dimensions[8].height = 25

    # ==================== BUILD EPIC TASKS ====================
    # Group tasks by epic
    epic_tasks = {}  # epic_name -> list of tasks
    for epic in data.get("epics", []):
        epic_name = epic.get("epic", "")
        epic_tasks[epic_name] = []
        for us in epic.get("user_stories", []):
            us_module = us.get("module", "")
            us_description = us.get("description", "")
            for task in us.get("tasks", []):
                epic_tasks[epic_name].append({
                    "epic": epic_name,
                    "us_module": us_module,
                    "us_description": us_description,
                    "pic": task.get("pic", ""),
                    "task_name": task.get("task_name", ""),
                    "start_date": parse_date(task.get("start_date")),
                    "due_date": parse_date(task.get("due_date")),
                    "est_effort_hour": float(task.get("est_effort_hour", 0)),
                    "notes": task.get("notes", ""),
                    "status": task.get("status", "Not Started"),
                    "task_complexity": task.get("task_complexity", ""),
                    "type_of_work": task.get("type_of_work", ""),
                    "task_process": task.get("task_process", ""),
                    "task_priority": task.get("task_priority", ""),
                })

    # Determine order of epics as they appear in JSON
    epic_order = [epic.get("epic", "") for epic in data.get("epics", [])]

    # Write phases (epics) starting from row 9
    current_row = 9
    all_task_rows = []  # track all task rows for header formulas

    for epic_name in epic_order:
        if epic_name not in epic_tasks:
            continue
        tasks = epic_tasks[epic_name]
        if not tasks:
            # still write header maybe? but skip for now
            continue

        # Phase header row (merged B-E)
        ws.cell(row=current_row, column=2, value=epic_name)  # Column B
        ws.cell(row=current_row, column=2).font = FONT_PHASE_BOLD
        ws.cell(row=current_row, column=2).alignment = Alignment(horizontal="left", vertical="center")

        # Apply phase header formatting to entire row B-J
        for col in range(2, 11):
            cell = ws.cell(row=current_row, column=col)
            cell.fill = COLOR_PHASE_GRAY
            # Không có border mặc định
            if col > 2:
                cell.font = FONT_PHASE_BOLD
                cell.alignment = Alignment(horizontal="center", vertical="center")

        # Merge B-E for epic name
        ws.merge_cells(start_row=current_row, start_column=2, end_row=current_row, end_column=5)

        first_task_row = current_row + 1
        last_task_row = current_row + len(tasks)

        first_task_in_epic = None
        last_task_in_epic = None

        # Write tasks for this epic
        for idx, task in enumerate(tasks):
            task_row = current_row + 1 + idx
            if first_task_in_epic is None:
                first_task_in_epic = task_row
            last_task_in_epic = task_row
            all_task_rows.append(task_row)

            ws.cell(row=task_row, column=2, value=task["us_module"])
            ws.cell(row=task_row, column=2).font = FONT_NORMAL
            ws.cell(row=task_row, column=2).alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)

            # C: TASK NAME
            ws.cell(row=task_row, column=3, value=task["task_name"])
            ws.cell(row=task_row, column=3).font = FONT_NORMAL
            ws.cell(row=task_row, column=3).alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)

            # D: DESCRIPTION (từ user story description)
            ws.cell(row=task_row, column=4, value=task.get("us_description", ""))
            ws.cell(row=task_row, column=4).font = FONT_NORMAL
            ws.cell(row=task_row, column=4).alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)

            # E: PIC
            ws.cell(row=task_row, column=5, value=task["pic"])
            ws.cell(row=task_row, column=5).font = FONT_NORMAL
            ws.cell(row=task_row, column=5).alignment = Alignment(horizontal="center", vertical="center")

            # F: % DONE (default 0)
            ws.cell(row=task_row, column=6, value=0.0)
            ws.cell(row=task_row, column=6).font = FONT_NORMAL
            ws.cell(row=task_row, column=6).number_format = '0%'
            ws.cell(row=task_row, column=6).alignment = Alignment(horizontal="center", vertical="center")

            # G: START DATE
            if task["start_date"]:
                ws.cell(row=task_row, column=7, value=task["start_date"])
                ws.cell(row=task_row, column=7).number_format = DATE_FORMAT
            ws.cell(row=task_row, column=7).font = FONT_NORMAL
            ws.cell(row=task_row, column=7).alignment = Alignment(horizontal="center", vertical="center")

            # H: DUE DATE
            if task["due_date"]:
                ws.cell(row=task_row, column=8, value=task["due_date"])
                ws.cell(row=task_row, column=8).number_format = DATE_FORMAT
            ws.cell(row=task_row, column=8).font = FONT_NORMAL
            ws.cell(row=task_row, column=8).alignment = Alignment(horizontal="center", vertical="center")

            # I: EFFORT (Hour)
            ws.cell(row=task_row, column=9, value=task["est_effort_hour"])
            ws.cell(row=task_row, column=9).font = FONT_NORMAL
            ws.cell(row=task_row, column=9).number_format = '0.0'
            ws.cell(row=task_row, column=9).alignment = Alignment(horizontal="center", vertical="center")

            # J: NOTE (task note)
            ws.cell(row=task_row, column=10, value=task.get("notes", ""))
            ws.cell(row=task_row, column=10).font = FONT_NORMAL
            ws.cell(row=task_row, column=10).alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)

            # K: TASK COMPLEXITY
            ws.cell(row=task_row, column=11, value=task.get("task_complexity", ""))
            ws.cell(row=task_row, column=11).font = FONT_NORMAL
            ws.cell(row=task_row, column=11).alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)

            # L: Type OF WORK
            ws.cell(row=task_row, column=12, value=task.get("type_of_work", ""))
            ws.cell(row=task_row, column=12).font = FONT_NORMAL
            ws.cell(row=task_row, column=12).alignment = Alignment(horizontal="center", vertical="center")

            # M: TASK PROCESS
            ws.cell(row=task_row, column=13, value=task.get("task_process", ""))
            ws.cell(row=task_row, column=13).font = FONT_NORMAL
            ws.cell(row=task_row, column=13).alignment = Alignment(horizontal="center", vertical="center")

            # N: TASK PRIORITY
            ws.cell(row=task_row, column=14, value=task.get("task_priority", ""))
            ws.cell(row=task_row, column=14).font = FONT_NORMAL
            ws.cell(row=task_row, column=14).alignment = Alignment(horizontal="center", vertical="center")

        # Write rollup formulas in phase header row (G, H, I)
        if first_task_in_epic and last_task_in_epic:
            # G: =MIN(start dates)
            ws.cell(row=current_row, column=7).value = f'=MIN(G{first_task_in_epic}:G{last_task_in_epic})'
            ws.cell(row=current_row, column=7).number_format = DATE_FORMAT
            ws.cell(row=current_row, column=7).font = FONT_PHASE_BOLD
            ws.cell(row=current_row, column=7).alignment = Alignment(horizontal="center", vertical="center")

            # H: =MAX(due dates)
            ws.cell(row=current_row, column=8).value = f'=MAX(H{first_task_in_epic}:H{last_task_in_epic})'
            ws.cell(row=current_row, column=8).number_format = DATE_FORMAT
            ws.cell(row=current_row, column=8).font = FONT_PHASE_BOLD
            ws.cell(row=current_row, column=8).alignment = Alignment(horizontal="center", vertical="center")

            # I: =SUM(effort)
            ws.cell(row=current_row, column=9).value = f'=SUM(I{first_task_in_epic}:I{last_task_in_epic})'
            ws.cell(row=current_row, column=9).number_format = '0.0'
            ws.cell(row=current_row, column=9).font = FONT_PHASE_BOLD
            ws.cell(row=current_row, column=9).alignment = Alignment(horizontal="center", vertical="center")

        # Update current_row for next epic (after last task row)
        current_row = last_task_in_epic + 1 if last_task_in_epic is not None else current_row + len(tasks) + 1

        # Set phase header row height (the row where epic name is)
        ws.row_dimensions[current_row - len(tasks) - 1].height = 36.75

        # Set task row heights
        if first_task_in_epic and last_task_in_epic:
            for r in range(first_task_in_epic, last_task_in_epic + 1):
                ws.row_dimensions[r].height = 30

        # Set phase header row height (the row where epic name is)
        ws.row_dimensions[current_row].height = 36.75

        # Set task row heights
        if first_task_in_epic and last_task_in_epic:
            for r in range(first_task_in_epic, last_task_in_epic + 1):
                ws.row_dimensions[r].height = 30

    # Update header formulas (rows 3-5) to use actual last row
    last_task_row = all_task_rows[-1] if all_task_rows else 50
    ws['H3'] = f'=MIN(G9:G{last_task_row})'
    ws['H4'] = f'=MAX(H9:H{last_task_row})'
    ws['H5'] = f'=SUM(I9:I{last_task_row})/2'

    # ==================== FREEZE PANES ====================
    ws.freeze_panes = 'B9'  # Freeze above first phase header

    # ==================== SAVE ====================
    wb.save(EXCEL_FILE)
    try:
        _script_dir = os.path.dirname(os.path.abspath(__file__))
        if _script_dir not in sys.path:
            sys.path.insert(0, _script_dir)
        from generate_xlsxwriter import build_project_plan
        build_project_plan(data, EXCEL_FILE)
    except Exception as e:
        print(f"Warning: XlsxWriter fallback error: {e}")
    optimize_for_excel_online(EXCEL_FILE)
    print(f"✅ Đã tạo thành công file Excel (mẫu mới - mỗi epic là phase): {EXCEL_FILE}")
    print(f" → Sheet: '{NEW_SHEET_NAME}'")
    print(f" → Số epic (phase): {len(epic_order)}")
    total_tasks = sum(len(epic_tasks[epic]) for epic in epic_order if epic in epic_tasks)
    print(f" → Tổng task: {total_tasks}")
    print(f" → Hàng cuối dữ liệu: {last_task_row}")

# ==================== LEGACY FORMAT ====================
def create_legacy_sheet_excel():
    """Create Excel in legacy format (original script behavior)"""
    data = load_backlog_data()
    if not data:
        return

    wb = Workbook()
    ws = wb.active
    ws.title = NEW_SHEET_NAME

    # ==================== HEADER ====================
    ws['B1'] = f"SPRINT BACKLOG #{_sprint_num}"
    ws['B1'].font = Font(bold=True, size=28, color="ED7D31")
    ws['B1'].alignment = Alignment(horizontal="left", vertical="center")

    ws['B3'] = "SPRINT GOAL"
    ws['B3'].fill = COLOR_DARK_HEADER_LEGACY
    ws['B3'].font = Font(bold=True, color="FFFFFF")
    ws['B3'].alignment = Alignment(horizontal="left", vertical="center")
    ws.merge_cells('C3:G3')
    ws['C3'] = data.get("sprint_goal", "")
    ws['C3'].font = Font(color="C65911")
    ws['C3'].alignment = Alignment(wrap_text=True, vertical="top", horizontal="left")

    ws['B4'] = "TIME BOX"
    ws['B4'].fill = COLOR_DARK_HEADER_LEGACY
    ws['B4'].font = Font(bold=True, color="FFFFFF")
    ws['B4'].alignment = Alignment(horizontal="left", vertical="center")
    ws.merge_cells('C4:G4')
    time_box = data.get("time_box", "")
    time_box_text = "\n".join(str(item).strip() for item in time_box) if isinstance(time_box, list) else str(time_box).replace("\\n", "\n")
    ws['C4'] = time_box_text
    ws['C4'].alignment = Alignment(wrap_text=True, vertical="top", horizontal="left")

    ws.row_dimensions[3].height = 30
    ws.row_dimensions[4].height = 75

    ws['H3'] = "STORY POINT OF THIS SPRINT"
    ws['H3'].fill = COLOR_DARK_HEADER_LEGACY
    ws['H3'].font = Font(bold=True, color="FFFFFF")
    ws['H3'].alignment = Alignment(horizontal="center", vertical="center")

    ws['I3'] = "MANDAY"
    ws['I3'].fill = COLOR_DARK_HEADER_LEGACY
    ws['I3'].font = Font(bold=True, color="FFFFFF", size=12)
    ws['I3'].alignment = Alignment(horizontal="center", vertical="center")

    for row in range(3, 5):
        for col in range(2, 10):
            ws.cell(row=row, column=col).border = dashed_border

    # ==================== TABLE HEADER ====================
    start_row = 6
    headers = ["User\nStory\nID", "MODULE/ FEATURE", "USER STORY/DESCRIPTION",
               "STORY\nPOINT", "ESTIMATED\nEFFORT\n(Story\nManday)", "Priority",
               "Complexity", "TASK", "PIC", "ESTIMATED\nEFFORT\n(Task\nManday)",
               "STATUS", "START DATE", "DUE DATE", "WORKING\nDAY", "ESTIMATED\nEFFORT\n(HOUR)",
               "NOTES",
               "TASK COMPLEXITY", "Type OF WORK", "TASK PROCESS", "TASK PRIORITY"]

    for col, header in enumerate(headers, start=1):
        cell = ws.cell(row=start_row, column=col, value=header)
        cell.font = Font(bold=True)
        if col > 10:
            cell.fill = PatternFill(start_color="002060", end_color="002060", fill_type="solid")
            cell.font = Font(bold=True, color="FFFFFF")
        else:
            cell.fill = COLOR_HEADER_LEGACY

        if col == 10 or col == 14:
            cell.fill = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
            cell.font = Font(bold=True, color="000000")

        if col > 15:
            cell.font = Font(bold=True, color="FFD965")
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = hair_border

    # ==================== GHI DỮ LIỆU ====================
    current_row = start_row + 1
    first_data_row = current_row
    first_epic_row = None
    epic_rows = []

    for epic in data.get("epics", []):
        epic_row = current_row
        if first_epic_row is None:
            first_epic_row = epic_row

        epic_rows.append(epic_row)

        # Dòng Epic
        epic_id_cell = ws.cell(row=epic_row, column=2, value=epic.get("epic", ""))
        epic_id_cell.font = Font(bold=True)
        epic_id_cell.alignment = Alignment(horizontal="left", vertical="center", wrap_text=False)

        for c in range(1, 21):
            cell = ws.cell(row=epic_row, column=c)
            cell.fill = COLOR_EPIC_LEGACY
            cell.font = Font(bold=True)
            cell.border = dashed_border

            if c == 2:
                cell.alignment = Alignment(horizontal="left", vertical="center", wrap_text=False)
            elif c in [12, 13]:
                cell.alignment = Alignment(horizontal="center", vertical="center")
            else:
                cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

        ws.cell(row=epic_row, column=1).value = None
        current_row += 1

        epic_us_start_row = current_row
        epic_tasks_start = None

        for us in epic.get("user_stories", []):
            us_start_row = current_row

            # User Story
            ws.cell(row=us_start_row, column=1, value=us.get("us_id"))
            ws.cell(row=us_start_row, column=2, value=us.get("module"))
            ws.cell(row=us_start_row, column=3, value=us.get("description"))
            ws.cell(row=us_start_row, column=4).value = f'=AVERAGE(E{us_start_row},(2*LEFT(F{us_start_row},1)),(2*LEFT(G{us_start_row},1)))'
            ws.cell(row=us_start_row, column=4).number_format = '0.0'
            ws.cell(row=us_start_row, column=5).number_format = '0.0'
            ws.cell(row=us_start_row, column=6, value=us.get("priority", ""))
            ws.cell(row=us_start_row, column=7, value=us.get("complexity", ""))

            tasks = us.get("tasks", [])
            if tasks:
                if epic_tasks_start is None:
                    epic_tasks_start = current_row

                first_task = tasks[0]
                ws.cell(row=us_start_row, column=8, value=first_task.get("task_name"))
                ws.cell(row=us_start_row, column=9, value=first_task.get("pic"))
                ws.cell(row=us_start_row, column=10).value = f"=O{us_start_row}/8"
                ws.cell(row=us_start_row, column=11, value=first_task.get("status"))
                ws.cell(row=us_start_row, column=12, value=parse_date(first_task.get("start_date")))
                ws.cell(row=us_start_row, column=13, value=parse_date(first_task.get("due_date")))
                ws.cell(row=us_start_row, column=12).number_format = DATE_FORMAT
                ws.cell(row=us_start_row, column=13).number_format = DATE_FORMAT
                ws.cell(row=us_start_row, column=14).value = f"=NETWORKDAYS(L{us_start_row},M{us_start_row})"
                ws.cell(row=us_start_row, column=15, value=float(first_task.get("est_effort_hour", 0)))
                ws.cell(row=us_start_row, column=16, value=first_task.get("notes"))
                ws.cell(row=us_start_row, column=17, value=first_task.get("task_complexity"))
                ws.cell(row=us_start_row, column=18, value=first_task.get("type_of_work"))
                ws.cell(row=us_start_row, column=19, value=first_task.get("task_process"))
                ws.cell(row=us_start_row, column=20, value=first_task.get("task_priority"))

                for task in tasks[1:]:
                    current_row += 1
                    ws.cell(row=current_row, column=8, value=task.get("task_name"))
                    ws.cell(row=current_row, column=9, value=task.get("pic"))
                    ws.cell(row=current_row, column=10).value = f"=O{current_row}/8"
                    ws.cell(row=current_row, column=11, value=task.get("status"))
                    ws.cell(row=current_row, column=12, value=parse_date(task.get("start_date")))
                    ws.cell(row=current_row, column=13, value=parse_date(task.get("due_date")))
                    ws.cell(row=current_row, column=12).number_format = DATE_FORMAT
                    ws.cell(row=current_row, column=13).number_format = DATE_FORMAT
                    ws.cell(row=current_row, column=14).value = f"=NETWORKDAYS(L{current_row},M{current_row})"
                    ws.cell(row=current_row, column=15, value=float(task.get("est_effort_hour", 0)))
                    ws.cell(row=current_row, column=16, value=task.get("notes"))
                    ws.cell(row=current_row, column=17, value=task.get("task_complexity"))
                    ws.cell(row=current_row, column=18, value=task.get("type_of_work"))
                    ws.cell(row=current_row, column=19, value=task.get("task_process"))
                    ws.cell(row=current_row, column=20, value=task.get("task_priority"))

            us_end_row = current_row

            # Merge cột A-G cho User Story
            if us_end_row > us_start_row:
                for col in range(1, 8):
                    ws.merge_cells(start_row=us_start_row, start_column=col, end_row=us_end_row, end_column=col)

            # Alignment User Story
            for col in range(1, 8):
                ws.cell(row=us_start_row, column=col).alignment = Alignment(vertical="center", wrap_text=True)

            if tasks:
                ws.cell(row=us_start_row, column=5).value = f"=SUM(J{us_start_row}:J{us_end_row})"

            current_row += 1

        # Tính toán dòng Epic
        epic_end_row = current_row - 1
        if epic_us_start_row <= epic_end_row:
            ws.cell(row=epic_row, column=4).value = f"=SUM(D{epic_us_start_row}:D{epic_end_row})"
            ws.cell(row=epic_row, column=4).number_format = '0.0'
            ws.cell(row=epic_row, column=5).value = f"=SUM(E{epic_us_start_row}:E{epic_end_row})"
            ws.cell(row=epic_row, column=5).number_format = '0.0'

        if epic_tasks_start and epic_tasks_start <= epic_end_row:
            ws.cell(row=epic_row, column=15).value = f"=SUM(O{epic_tasks_start}:O{epic_end_row})"
            ws.cell(row=epic_row, column=15).font = Font(bold=True)
            ws.cell(row=epic_row, column=10).value = f"=O{epic_row}/8"
            ws.cell(row=epic_row, column=10).font = Font(bold=True)
            ws.cell(row=epic_row, column=12).value = f"=MIN(L{epic_tasks_start}:L{epic_end_row})"
            ws.cell(row=epic_row, column=13).value = f"=MAX(M{epic_tasks_start}:M{epic_end_row})"
            ws.cell(row=epic_row, column=12).number_format = DATE_FORMAT
            ws.cell(row=epic_row, column=13).number_format = DATE_FORMAT
            ws.cell(row=epic_row, column=14).value = f"=NETWORKDAYS(L{epic_row},M{epic_row})"
            ws.cell(row=epic_row, column=14).font = Font(bold=True)

    # ==================== TỔNG STORY POINT & MANDAY ====================
    last_row = current_row - 1
    if first_epic_row:
        ws['I4'].value = f"=SUM(O{first_epic_row}:O{last_row})/8/2"
        ws['I4'].font = Font(bold=True, size=26, color="ED7D31")
        ws['I4'].alignment = Alignment(horizontal="center", vertical="center")
        ws['I4'].number_format = '0.0'

        ws['H4'].value = f'=SUM(D{first_data_row}:D{last_row})/2'
        ws['H4'].font = Font(bold=True, size=26, color="ED7D31")
        ws['H4'].alignment = Alignment(horizontal="center", vertical="center")
        ws['H4'].number_format = '0.0'

    # ==================== ALIGNMENT & BORDER ====================
    for row in range(start_row + 1, current_row):
        ws.cell(row=row, column=2).alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)
        ws.cell(row=row, column=8).alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)
        ws.cell(row=row, column=9).alignment = Alignment(horizontal="center", vertical="center")

    for epic_row in epic_rows:
        ws.cell(row=epic_row, column=2).alignment = Alignment(horizontal="left", vertical="center", wrap_text=False)

    center_align = Alignment(horizontal="center", vertical="center")
    for row in range(start_row + 1, current_row):
        for col in [4, 5, 6, 7, 10, 11, 12, 13, 14, 15]:
            cell = ws.cell(row=row, column=col)
            if cell.value is not None or col in [12, 13]:
                cell.alignment = center_align

    # Border
    for row in range(start_row, current_row):
        for col in range(1, 21):
            ws.cell(row=row, column=col).border = dashed_border

    # Wrap text cho cột Notes (P)
    for row in range(start_row + 1, current_row):
        cell = ws.cell(row=row, column=16)
        cell.alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)

    # ==================== DATA VALIDATION & CONDITIONAL FORMATTING ====================
    max_row = current_row + 50

    dv_priority = DataValidation(type="list", formula1='"4-Critical,3-High,2-Medium,1-Low"', allow_blank=True)
    ws.add_data_validation(dv_priority)
    dv_priority.add(f'F{start_row+1}:F{max_row}')

    dv_complexity = DataValidation(type="list", formula1='"3-High,2-Medium,1-Low"', allow_blank=True)
    ws.add_data_validation(dv_complexity)
    dv_complexity.add(f'G{start_row+1}:G{max_row}')

    dv_status = DataValidation(type="list", formula1='"Done,In Progress,Not Started,Pending"', allow_blank=True)
    ws.add_data_validation(dv_status)
    dv_status.add(f'K{start_row+1}:K{max_row}')

    # Conditional Formatting
    cf_p = f'F{start_row+1}:F{max_row}'
    ws.conditional_formatting.add(cf_p, CellIsRule(operator='equal', formula=['"4-Critical"'], fill=COLOR_CRITICAL_LEGACY, font=Font(color="FFFFFF")))
    ws.conditional_formatting.add(cf_p, CellIsRule(operator='equal', formula=['"3-High"'], fill=COLOR_HIGH_LEGACY, font=Font(color="9C0006")))
    ws.conditional_formatting.add(cf_p, CellIsRule(operator='equal', formula=['"2-Medium"'], fill=COLOR_MEDIUM_LEGACY, font=Font(color="9C5700")))
    ws.conditional_formatting.add(cf_p, CellIsRule(operator='equal', formula=['"1-Low"'], fill=COLOR_LOW_LEGACY, font=Font(color="1F497D")))

    cf_c = f'G{start_row+1}:G{max_row}'
    ws.conditional_formatting.add(cf_c, CellIsRule(operator='equal', formula=['"3-High"'], fill=COLOR_HIGH_LEGACY, font=Font(color="9C0006")))
    ws.conditional_formatting.add(cf_c, CellIsRule(operator='equal', formula=['"2-Medium"'], fill=COLOR_MEDIUM_LEGACY, font=Font(color="9C5700")))
    ws.conditional_formatting.add(cf_c, CellIsRule(operator='equal', formula=['"1-Low"'], fill=COLOR_LOW_LEGACY, font=Font(color="1F497D")))

    cf_k = f'K{start_row+1}:K{max_row}'
    ws.conditional_formatting.add(cf_k, CellIsRule(operator='equal', formula=['"Done"'], fill=COLOR_DONE_LEGACY, font=Font(color="006100")))
    ws.conditional_formatting.add(cf_k, CellIsRule(operator='equal', formula=['"In Progress"'], fill=COLOR_INPROGRESS_LEGACY, font=Font(color="D55709")))
    ws.conditional_formatting.add(cf_k, CellIsRule(operator='equal', formula=['"Pending"'], fill=COLOR_PENDING_LEGACY, font=Font(color="262626")))
    # ws.conditional_formatting.add(cf_k, CellIsRule(operator='equal', formula=['"Not Started"'], fill=COLOR_NOTSTARTED_LEGACY))

    ws.freeze_panes = 'H7'

    # Column Widths
    ws.column_dimensions['A'].width = 8
    ws.column_dimensions['B'].width = 24
    ws.column_dimensions['C'].width = 50
    ws.column_dimensions['D'].width = 10
    ws.column_dimensions['E'].width = 12
    ws.column_dimensions['F'].width = 10
    ws.column_dimensions['G'].width = 10
    ws.column_dimensions['H'].width = 50
    ws.column_dimensions['I'].width = 16
    ws.column_dimensions['J'].width = 12
    ws.column_dimensions['K'].width = 12
    ws.column_dimensions['L'].width = 15
    ws.column_dimensions['M'].width = 15
    ws.column_dimensions['N'].width = 10
    ws.column_dimensions['O'].width = 12
    ws.column_dimensions['P'].width = 50
    ws.column_dimensions['Q'].width = 10
    ws.column_dimensions['R'].width = 10
    ws.column_dimensions['S'].width = 10
    ws.column_dimensions['T'].width = 10

    # Lưu file Excel mới
    wb.save(EXCEL_FILE)
    optimize_for_excel_online(EXCEL_FILE)
    print(f"✅ Đã tạo thành công file Excel (mẫu cũ): {EXCEL_FILE}")
    print(f" → Sheet: '{NEW_SHEET_NAME}'")
    print(f" → Số dòng Epic: {len(epic_rows)}")

# ==================== MAIN ====================
if __name__ == "__main__":
    if USE_OLD_FORMAT:
        create_legacy_sheet_excel()
    else:
        create_plan_sheet_excel()
#!/usr/bin/env python3
"""
generate_xlsxwriter.py - Generate 100% Microsoft Excel & Excel Online compatible spreadsheets.
Uses XlsxWriter with pre-calculated cached formula values for strict OpenXML compliance.
"""
import json
import os
import sys
from datetime import datetime, timedelta
import xlsxwriter


def calc_networkdays(start_dt, end_dt):
    days = 0
    cur = start_dt
    while cur <= end_dt:
        if cur.weekday() < 5:
            days += 1
        cur += timedelta(days=1)
    return days


def excel_date_serial(dt):
    return (dt - datetime(1899, 12, 30)).days


def build_project_plan(data, output_path):
    workbook = xlsxwriter.Workbook(output_path, {
        'default_date_format': 'dd/mm/yyyy',
        'strings_to_numbers': False
    })
    workbook.set_properties({
        'title': f"{data.get('project', 'Project')} - Sprint {data.get('sprint_number', 3)} Project Plan",
        'subject': 'Sprint Project Plan',
        'author': 'FTI-SAL PMO',
        'company': 'FPT Telecom International (FTI)'
    })
    sheet_name = f"Sprint {data.get('sprint_number', 3)}"
    ws = workbook.add_worksheet(sheet_name)

    # Formats
    title_fmt = workbook.add_format({
        'font_name': 'Calibri', 'font_size': 18, 'bold': True, 'font_color': '#0B5394',
        'align': 'left', 'valign': 'vcenter'
    })
    label_fmt = workbook.add_format({
        'font_name': 'Calibri', 'font_size': 12, 'bold': True, 'font_color': '#000000',
        'align': 'left', 'valign': 'vcenter'
    })
    text_wrap_fmt = workbook.add_format({
        'font_name': 'Calibri', 'font_size': 11, 'text_wrap': True, 'valign': 'top'
    })
    date_val_fmt = workbook.add_format({
        'font_name': 'Calibri', 'font_size': 11, 'num_format': 'dd/mm/yyyy',
        'align': 'center', 'valign': 'vcenter'
    })
    num_fmt = workbook.add_format({
        'font_name': 'Calibri', 'font_size': 11, 'num_format': '#,##0.0',
        'align': 'center', 'valign': 'vcenter'
    })
    proj_header_fmt = workbook.add_format({
        'font_name': 'Calibri', 'font_size': 13, 'bold': True, 'font_color': '#FFFFFF',
        'bg_color': '#0B5394', 'align': 'left', 'valign': 'vcenter'
    })
    col_header_fmt = workbook.add_format({
        'font_name': 'Calibri', 'font_size': 11, 'bold': True, 'font_color': '#0B5394',
        'bg_color': '#F3F3F3', 'align': 'center', 'valign': 'vcenter', 'text_wrap': True,
        'border': 1, 'border_color': '#D9D9D9'
    })
    epic_hdr_fmt = workbook.add_format({
        'font_name': 'Calibri', 'font_size': 12, 'bold': True, 'font_color': '#000000',
        'bg_color': '#D9E1F2', 'align': 'left', 'valign': 'vcenter',
        'border': 1, 'border_color': '#B4C6E7'
    })
    epic_date_fmt = workbook.add_format({
        'font_name': 'Calibri', 'font_size': 11, 'bold': True, 'font_color': '#000000',
        'bg_color': '#D9E1F2', 'align': 'center', 'valign': 'vcenter', 'num_format': 'dd/mm/yyyy',
        'border': 1, 'border_color': '#B4C6E7'
    })
    epic_num_fmt = workbook.add_format({
        'font_name': 'Calibri', 'font_size': 11, 'bold': True, 'font_color': '#000000',
        'bg_color': '#D9E1F2', 'align': 'center', 'valign': 'vcenter', 'num_format': '#,##0',
        'border': 1, 'border_color': '#B4C6E7'
    })
    cell_text_fmt = workbook.add_format({
        'font_name': 'Calibri', 'font_size': 11, 'valign': 'vcenter',
        'border': 1, 'border_color': '#E0E0E0'
    })
    cell_center_fmt = workbook.add_format({
        'font_name': 'Calibri', 'font_size': 11, 'align': 'center', 'valign': 'vcenter',
        'border': 1, 'border_color': '#E0E0E0'
    })
    cell_date_fmt = workbook.add_format({
        'font_name': 'Calibri', 'font_size': 11, 'align': 'center', 'valign': 'vcenter',
        'num_format': 'dd/mm/yyyy', 'border': 1, 'border_color': '#E0E0E0'
    })
    cell_num_fmt = workbook.add_format({
        'font_name': 'Calibri', 'font_size': 11, 'align': 'center', 'valign': 'vcenter',
        'num_format': '#,##0', 'border': 1, 'border_color': '#E0E0E0'
    })
    cell_pct_fmt = workbook.add_format({
        'font_name': 'Calibri', 'font_size': 11, 'align': 'center', 'valign': 'vcenter',
        'num_format': '0%', 'border': 1, 'border_color': '#E0E0E0'
    })

    # Set column widths
    ws.set_column('A:A', 3)
    ws.set_column('B:B', 30)
    ws.set_column('C:C', 45)
    ws.set_column('D:D', 45)
    ws.set_column('E:E', 12)
    ws.set_column('F:F', 10)
    ws.set_column('G:G', 14)
    ws.set_column('H:H', 14)
    ws.set_column('I:I', 14)
    ws.set_column('J:J', 35)
    ws.set_column('K:K', 12)
    ws.set_column('L:L', 14)
    ws.set_column('M:M', 20)
    ws.set_column('N:N', 14)

    # Row 1 (index 0) Title
    proj_name = data.get('project', 'Project')
    sprint_no = data.get('sprint_number', 3)
    ws.set_row(0, 32)
    ws.merge_range('B1:J1', f"[{proj_name} Sprint {sprint_no}] Project Planning ➜", title_fmt)

    # Row 3 (index 2) Goal & Start Date
    ws.set_row(2, 35)
    ws.write('B3', 'Goal', label_fmt)
    ws.merge_range('C3:F3', data.get('sprint_goal', ''), text_wrap_fmt)
    ws.write('G3', 'Start Date', label_fmt)

    # Row 4 (index 3) Time Box & Due Date
    ws.set_row(3, 75)
    ws.write('B4', 'Output/ Module', label_fmt)
    timebox_str = '\n'.join(data.get('time_box', [])) if isinstance(data.get('time_box'), list) else str(data.get('time_box', ''))
    ws.merge_range('C4:F4', timebox_str, text_wrap_fmt)
    ws.write('G4', 'Due Date', label_fmt)

    # Row 5 (index 4) Description & Total Effort
    ws.set_row(4, 35)
    ws.write('B5', 'Description', label_fmt)
    ws.merge_range('C5:F5', data.get('sprint_goal', ''), text_wrap_fmt)
    ws.write('G5', 'Total Effort', label_fmt)

    # Row 7 (index 6) PROJECT DETAILS
    ws.set_row(6, 26)
    ws.merge_range('B7:N7', '  PROJECT DETAILS', proj_header_fmt)

    # Row 8 (index 7) Headers
    ws.set_row(7, 24)
    headers = [
        ("B8", "MODULE/ MAIN TASK"), ("C8", "TASK NAME"), ("D8", "DESCRIPTION"),
        ("E8", "PIC"), ("F8", "% DONE"), ("G8", "START DATE"), ("H8", "DUE DATE"),
        ("I8", "EFFORT (Hour)"), ("J8", "NOTE"), ("K8", "TASK COMPLEXITY"),
        ("L8", "Type OF WORK"), ("M8", "TASK PROCESS"), ("N8", "TASK PRIORITY")
    ]
    for cell_ref, text in headers:
        ws.write(cell_ref, text, col_header_fmt)

    # Data Rows
    current_row = 8  # 0-indexed, so row 9 in 1-indexed
    epic_ranges = []
    all_task_rows = []
    overall_min_dt = None
    overall_max_dt = None
    overall_effort = 0

    for epic in data.get('epics', []):
        epic_name = epic.get('epic', '')
        epic_row = current_row
        ws.set_row(epic_row, 24)
        current_row += 1

        epic_start_task_row = current_row + 1  # 1-indexed
        epic_min_dt = None
        epic_max_dt = None
        epic_effort = 0

        for us in epic.get('user_stories', []):
            module = us.get('module', '')
            us_desc = us.get('description', '')
            for t in us.get('tasks', []):
                r = current_row
                ws.set_row(r, 20)
                ws.write(r, 1, module, cell_text_fmt)
                ws.write(r, 2, t.get('task_name', ''), cell_text_fmt)
                ws.write(r, 3, us_desc, cell_text_fmt)
                ws.write(r, 4, t.get('pic', ''), cell_center_fmt)
                ws.write(r, 5, 1.0 if t.get('status') == 'Done' else 0.0, cell_pct_fmt)

                # Dates
                sd_dt = datetime.strptime(t['start_date'], '%d/%m/%Y')
                dd_dt = datetime.strptime(t['due_date'], '%d/%m/%Y')
                if epic_min_dt is None or sd_dt < epic_min_dt:
                    epic_min_dt = sd_dt
                if epic_max_dt is None or dd_dt > epic_max_dt:
                    epic_max_dt = dd_dt
                if overall_min_dt is None or sd_dt < overall_min_dt:
                    overall_min_dt = sd_dt
                if overall_max_dt is None or dd_dt > overall_max_dt:
                    overall_max_dt = dd_dt

                eff = int(t.get('est_effort_hour', 0))
                epic_effort += eff
                overall_effort += eff

                ws.write_datetime(r, 6, sd_dt, cell_date_fmt)
                ws.write_datetime(r, 7, dd_dt, cell_date_fmt)
                ws.write_number(r, 8, eff, cell_num_fmt)
                ws.write(r, 9, t.get('notes', ''), cell_text_fmt)
                ws.write_number(r, 10, int(t.get('task_complexity', 6)), cell_center_fmt)
                ws.write(r, 11, t.get('type_of_work', 'Do'), cell_center_fmt)
                ws.write(r, 12, t.get('task_process', ''), cell_center_fmt)
                ws.write(r, 13, t.get('task_priority', 'Medium'), cell_center_fmt)

                all_task_rows.append(current_row + 1)
                current_row += 1

        epic_end_task_row = current_row  # 1-indexed
        # Write Epic row with cached values
        ws.merge_range(epic_row, 1, epic_row, 5, epic_name, epic_hdr_fmt)
        ws.write_formula(epic_row, 6, f"=MIN(G{epic_start_task_row}:G{epic_end_task_row})", epic_date_fmt, excel_date_serial(epic_min_dt))
        ws.write_formula(epic_row, 7, f"=MAX(H{epic_start_task_row}:H{epic_end_task_row})", epic_date_fmt, excel_date_serial(epic_max_dt))
        ws.write_formula(epic_row, 8, f"=SUM(I{epic_start_task_row}:I{epic_end_task_row})", epic_num_fmt, epic_effort)
        for c in range(9, 14):
            ws.write_blank(epic_row, c, None, epic_hdr_fmt)
        epic_ranges.append(epic_row + 1)

    # Top summary formulas with cached values
    first_task = min(all_task_rows)
    last_task = max(all_task_rows)
    ws.write_formula('H3', f'=MIN(G{first_task}:G{last_task})', date_val_fmt, excel_date_serial(overall_min_dt))
    ws.write_formula('H4', f'=MAX(H{first_task}:H{last_task})', date_val_fmt, excel_date_serial(overall_max_dt))
    epic_sum_formula = '+'.join([f'I{r}' for r in epic_ranges])
    ws.write_formula('H5', f'={epic_sum_formula}', num_fmt, overall_effort)

    ws.freeze_panes(8, 0)  # freeze above row 9
    workbook.close()
    print(f"Generated Project Plan with XlsxWriter: {output_path}")


def build_sprint_backlog(data, output_path):
    workbook = xlsxwriter.Workbook(output_path, {
        'default_date_format': 'dd/mm/yyyy',
        'strings_to_numbers': False
    })
    workbook.set_properties({
        'title': f"{data.get('project', 'Project')} - Sprint {data.get('sprint_number', 3)} Backlog",
        'subject': 'Detailed Sprint Backlog',
        'author': 'FTI-SAL PMO',
        'company': 'FPT Telecom International (FTI)'
    })
    sheet_name = f"Sprint {data.get('sprint_number', 3)}"
    ws = workbook.add_worksheet(sheet_name)

    # Formats
    title_fmt = workbook.add_format({
        'font_name': 'Calibri', 'font_size': 24, 'bold': True, 'font_color': '#ED7D31',
        'align': 'left', 'valign': 'vcenter'
    })
    dark_hdr_fmt = workbook.add_format({
        'font_name': 'Calibri', 'font_size': 11, 'bold': True, 'font_color': '#FFFFFF',
        'bg_color': '#305496', 'align': 'center', 'valign': 'vcenter', 'border': 1
    })
    desc_val_fmt = workbook.add_format({
        'font_name': 'Calibri', 'font_size': 11, 'font_color': '#C65911',
        'text_wrap': True, 'valign': 'top', 'border': 1
    })
    timebox_fmt = workbook.add_format({
        'font_name': 'Calibri', 'font_size': 10, 'text_wrap': True, 'valign': 'top', 'border': 1
    })
    sp_sum_fmt = workbook.add_format({
        'font_name': 'Calibri', 'font_size': 24, 'bold': True, 'font_color': '#ED7D31',
        'align': 'center', 'valign': 'vcenter', 'border': 1, 'num_format': '#,##0.0'
    })
    md_sum_fmt = workbook.add_format({
        'font_name': 'Calibri', 'font_size': 24, 'bold': True, 'font_color': '#ED7D31',
        'align': 'center', 'valign': 'vcenter', 'border': 1, 'num_format': '#,##0.0'
    })

    # Table Header formats
    col_hdr_std = workbook.add_format({
        'font_name': 'Calibri', 'font_size': 10, 'bold': True, 'bg_color': '#D6DCE4',
        'align': 'center', 'valign': 'vcenter', 'text_wrap': True, 'border': 1
    })
    col_hdr_dark = workbook.add_format({
        'font_name': 'Calibri', 'font_size': 10, 'bold': True, 'font_color': '#FFFFFF',
        'bg_color': '#002060', 'align': 'center', 'valign': 'vcenter', 'text_wrap': True, 'border': 1
    })
    col_hdr_green = workbook.add_format({
        'font_name': 'Calibri', 'font_size': 10, 'bold': True, 'font_color': '#000000',
        'bg_color': '#C6EFCE', 'align': 'center', 'valign': 'vcenter', 'text_wrap': True, 'border': 1
    })
    col_hdr_yellow = workbook.add_format({
        'font_name': 'Calibri', 'font_size': 10, 'bold': True, 'font_color': '#FFD965',
        'bg_color': '#002060', 'align': 'center', 'valign': 'vcenter', 'text_wrap': True, 'border': 1
    })

    # Epic formats
    epic_fmt = workbook.add_format({
        'font_name': 'Calibri', 'font_size': 11, 'bold': True, 'bg_color': '#FFE598',
        'valign': 'vcenter', 'border': 1
    })
    epic_center_fmt = workbook.add_format({
        'font_name': 'Calibri', 'font_size': 11, 'bold': True, 'bg_color': '#FFE598',
        'align': 'center', 'valign': 'vcenter', 'border': 1, 'num_format': '#,##0.0'
    })
    epic_date_fmt = workbook.add_format({
        'font_name': 'Calibri', 'font_size': 11, 'bold': True, 'bg_color': '#FFE598',
        'align': 'center', 'valign': 'vcenter', 'border': 1, 'num_format': 'dd/mm/yyyy'
    })
    epic_int_fmt = workbook.add_format({
        'font_name': 'Calibri', 'font_size': 11, 'bold': True, 'bg_color': '#FFE598',
        'align': 'center', 'valign': 'vcenter', 'border': 1, 'num_format': '#,##0'
    })

    # Task formats
    cell_text = workbook.add_format({'font_name': 'Calibri', 'font_size': 10, 'valign': 'vcenter', 'border': 1})
    cell_center = workbook.add_format({'font_name': 'Calibri', 'font_size': 10, 'align': 'center', 'valign': 'vcenter', 'border': 1})
    cell_num1 = workbook.add_format({'font_name': 'Calibri', 'font_size': 10, 'align': 'center', 'valign': 'vcenter', 'num_format': '#,##0.0', 'border': 1})
    cell_num0 = workbook.add_format({'font_name': 'Calibri', 'font_size': 10, 'align': 'center', 'valign': 'vcenter', 'num_format': '#,##0', 'border': 1})
    cell_date = workbook.add_format({'font_name': 'Calibri', 'font_size': 10, 'align': 'center', 'valign': 'vcenter', 'num_format': 'dd/mm/yyyy', 'border': 1})

    # Status formatting
    status_done = workbook.add_format({'font_name': 'Calibri', 'font_size': 10, 'align': 'center', 'valign': 'vcenter', 'bg_color': '#C6EFCE', 'font_color': '#006100', 'border': 1})
    status_inprog = workbook.add_format({'font_name': 'Calibri', 'font_size': 10, 'align': 'center', 'valign': 'vcenter', 'bg_color': '#F4B084', 'border': 1})
    status_notstart = workbook.add_format({'font_name': 'Calibri', 'font_size': 10, 'align': 'center', 'valign': 'vcenter', 'bg_color': '#EFF6FB', 'border': 1})

    # Column widths
    ws.set_column('A:A', 10)
    ws.set_column('B:B', 24)
    ws.set_column('C:C', 35)
    ws.set_column('D:D', 10)
    ws.set_column('E:E', 12)
    ws.set_column('F:F', 10)
    ws.set_column('G:G', 12)
    ws.set_column('H:H', 40)
    ws.set_column('I:I', 14)
    ws.set_column('J:J', 12)
    ws.set_column('K:K', 14)
    ws.set_column('L:L', 14)
    ws.set_column('M:M', 14)
    ws.set_column('N:N', 12)
    ws.set_column('O:O', 12)
    ws.set_column('P:P', 35)
    ws.set_column('Q:Q', 10)
    ws.set_column('R:R', 10)
    ws.set_column('S:S', 18)
    ws.set_column('T:T', 12)

    sprint_no = data.get('sprint_number', 3)
    ws.set_row(0, 32)
    ws.write('B1', f"SPRINT BACKLOG #{sprint_no}", title_fmt)

    # Row 3 (index 2) Goal & Story Points
    ws.set_row(2, 35)
    ws.write('B3', 'SPRINT GOAL', dark_hdr_fmt)
    ws.merge_range('C3:G3', data.get('sprint_goal', ''), desc_val_fmt)
    ws.write('H3', 'STORY POINT OF THIS SPRINT', dark_hdr_fmt)
    ws.write('I3', 'MANDAY', dark_hdr_fmt)

    # Row 4 (index 3) Time Box
    ws.set_row(3, 75)
    ws.write('B4', 'TIME BOX', dark_hdr_fmt)
    timebox_str = '\n'.join(data.get('time_box', [])) if isinstance(data.get('time_box'), list) else str(data.get('time_box', ''))
    ws.merge_range('C4:G4', timebox_str, timebox_fmt)

    # Row 6 (index 5) Table Header
    ws.set_row(5, 26)
    headers = [
        ("A6", "User\nStory\nID", col_hdr_std),
        ("B6", "MODULE/ FEATURE", col_hdr_std),
        ("C6", "USER STORY/DESCRIPTION", col_hdr_std),
        ("D6", "STORY\nPOINT", col_hdr_std),
        ("E6", "ESTIMATED\nEFFORT\n(Story\nManday)", col_hdr_std),
        ("F6", "Priority", col_hdr_std),
        ("G6", "Complexity", col_hdr_std),
        ("H6", "TASK", col_hdr_std),
        ("I6", "PIC", col_hdr_std),
        ("J6", "ESTIMATED\nEFFORT\n(Task\nManday)", col_hdr_green),
        ("K6", "STATUS", col_hdr_dark),
        ("L6", "START DATE", col_hdr_dark),
        ("M6", "DUE DATE", col_hdr_dark),
        ("N6", "WORKING\nDAY", col_hdr_green),
        ("O6", "ESTIMATED\nEFFORT\n(HOUR)", col_hdr_dark),
        ("P6", "NOTES", col_hdr_yellow),
        ("Q6", "TASK COMPLEXITY", col_hdr_yellow),
        ("R6", "Type OF WORK", col_hdr_yellow),
        ("S6", "TASK PROCESS", col_hdr_yellow),
        ("T6", "TASK PRIORITY", col_hdr_yellow)
    ]
    for cell_ref, text, fmt in headers:
        ws.write(cell_ref, text, fmt)

    current_row = 6  # 0-indexed, so row 7 in 1-indexed
    epic_rows = []
    total_sp_all = 0.0
    total_effort_all = 0

    for epic in data.get('epics', []):
        epic_name = epic.get('epic', '')
        epic_row = current_row
        ws.set_row(epic_row, 24)
        current_row += 1

        epic_start_task_row = current_row + 1  # 1-indexed
        epic_sp_sum = 0.0
        epic_md_sum = 0.0
        epic_effort_sum = 0
        epic_min_dt = None
        epic_max_dt = None

        for us in epic.get('user_stories', []):
            us_id = us.get('us_id', '')
            module = us.get('module', '')
            desc = us.get('description', '')
            prio = us.get('priority', '3-High')
            comp = us.get('complexity', '2-Medium')
            tasks = us.get('tasks', [])
            total_us_effort = sum(int(t.get('est_effort_hour', 0)) for t in tasks)
            us_manday = round(total_us_effort / 8.0, 2)
            prio_num = int(str(prio).split('-')[0]) if '-' in str(prio) and str(prio).split('-')[0].isdigit() else 2
            comp_num = int(str(comp).split('-')[0]) if '-' in str(comp) and str(comp).split('-')[0].isdigit() else 2
            us_story_point = round((us_manday + (prio_num * 2) + (comp_num * 2)) / 3.0, 1)
            us_start_row_1idx = current_row + 1
            us_end_row_1idx = current_row + len(tasks)

            for idx_t, t in enumerate(tasks):
                r = current_row
                ws.set_row(r, 20)
                ws.write(r, 0, us_id, cell_center)
                ws.write(r, 1, module, cell_text)
                ws.write(r, 2, desc, cell_text)
                if idx_t == 0:
                    ws.write_formula(r, 3, f'=AVERAGE(E{us_start_row_1idx},(2*LEFT(F{us_start_row_1idx},1)),(2*LEFT(G{us_start_row_1idx},1)))', cell_num1, us_story_point)
                    ws.write_formula(r, 4, f'=SUM(J{us_start_row_1idx}:J{us_end_row_1idx})', cell_num1, round(us_manday, 1))
                    epic_sp_sum += us_story_point
                    epic_md_sum += us_manday
                else:
                    ws.write_number(r, 3, 0.0, cell_num1)
                    ws.write_number(r, 4, 0.0, cell_num1)

                ws.write(r, 5, prio, cell_center)
                ws.write(r, 6, comp, cell_center)
                ws.write(r, 7, t.get('task_name', ''), cell_text)
                ws.write(r, 8, t.get('pic', ''), cell_center)

                eff_hr = int(t.get('est_effort_hour', 0))
                epic_effort_sum += eff_hr
                row_1idx = r + 1
                ws.write_formula(r, 9, f'=O{row_1idx}/8', cell_num1, round(eff_hr / 8.0, 2))

                st = t.get('status', 'Not Started')
                st_fmt = status_done if st == 'Done' else (status_inprog if st == 'In Progress' else status_notstart)
                ws.write(r, 10, st, st_fmt)

                # Dates
                sd_dt = datetime.strptime(t['start_date'], '%d/%m/%Y')
                dd_dt = datetime.strptime(t['due_date'], '%d/%m/%Y')
                if epic_min_dt is None or sd_dt < epic_min_dt:
                    epic_min_dt = sd_dt
                if epic_max_dt is None or dd_dt > epic_max_dt:
                    epic_max_dt = dd_dt

                ws.write_datetime(r, 11, sd_dt, cell_date)
                ws.write_datetime(r, 12, dd_dt, cell_date)

                # Networkdays
                net_days = calc_networkdays(sd_dt, dd_dt)
                ws.write_formula(r, 13, f'=NETWORKDAYS(L{row_1idx},M{row_1idx})', cell_num0, net_days)
                ws.write_number(r, 14, eff_hr, cell_num0)
                ws.write(r, 15, t.get('notes', ''), cell_text)
                ws.write_number(r, 16, int(t.get('task_complexity', 6)), cell_center)
                ws.write(r, 17, t.get('type_of_work', 'Do'), cell_center)
                ws.write(r, 18, t.get('task_process', ''), cell_center)
                ws.write(r, 19, t.get('task_priority', 'Medium'), cell_center)

                current_row += 1

        epic_end_task_row = current_row  # 1-indexed
        total_sp_all += epic_sp_sum
        total_effort_all += epic_effort_sum

        # Write Epic row with cached values
        ws.write_blank(epic_row, 0, None, epic_fmt)
        ws.merge_range(epic_row, 1, epic_row, 2, epic_name, epic_fmt)
        epic_1idx = epic_row + 1
        ws.write_formula(epic_row, 3, f'=SUM(D{epic_start_task_row}:D{epic_end_task_row})', epic_center_fmt, round(epic_sp_sum, 1))
        ws.write_formula(epic_row, 4, f'=SUM(E{epic_start_task_row}:E{epic_end_task_row})', epic_center_fmt, round(epic_md_sum, 1))
        ws.write_blank(epic_row, 5, None, epic_fmt)
        ws.write_blank(epic_row, 6, None, epic_fmt)
        ws.write_blank(epic_row, 7, None, epic_fmt)
        ws.write_blank(epic_row, 8, None, epic_fmt)
        ws.write_formula(epic_row, 9, f'=O{epic_1idx}/8', epic_center_fmt, round(epic_effort_sum / 8.0, 1))
        ws.write_blank(epic_row, 10, None, epic_fmt)
        ws.write_formula(epic_row, 11, f'=MIN(L{epic_start_task_row}:L{epic_end_task_row})', epic_date_fmt, excel_date_serial(epic_min_dt))
        ws.write_formula(epic_row, 12, f'=MAX(M{epic_start_task_row}:M{epic_end_task_row})', epic_date_fmt, excel_date_serial(epic_max_dt))
        ws.write_formula(epic_row, 13, f'=NETWORKDAYS(L{epic_1idx},M{epic_1idx})', epic_int_fmt, calc_networkdays(epic_min_dt, epic_max_dt))
        ws.write_formula(epic_row, 14, f'=SUM(O{epic_start_task_row}:O{epic_end_task_row})', epic_int_fmt, epic_effort_sum)
        for c in range(15, 20):
            ws.write_blank(epic_row, c, None, epic_fmt)
        epic_rows.append(epic_1idx)

    # Top summary formulas: H4 = sum of epic SP, I4 = sum of epic manday
    epic_sp_formula = '+'.join([f'D{r}' for r in epic_rows])
    epic_md_formula = '+'.join([f'O{r}/8' for r in epic_rows])
    ws.write_formula('H4', f'={epic_sp_formula}', sp_sum_fmt, round(total_sp_all, 1))
    ws.write_formula('I4', f'={epic_md_formula}', md_sum_fmt, round(total_effort_all / 8.0, 1))

    ws.freeze_panes(6, 0)
    workbook.close()
    print(f"Generated Detailed Sprint Backlog with XlsxWriter: {output_path}")


if __name__ == '__main__':
    json_path = 'outputs/.tmp/sprint3_backlog.json'
    if len(sys.argv) > 1:
        json_path = sys.argv[1]
    with open(json_path, encoding='utf-8') as f:
        data = json.load(f)

    os.makedirs('outputs', exist_ok=True)
    build_project_plan(data, 'outputs/sprint3_Project_Plan.xlsx')
    build_sprint_backlog(data, 'outputs/sprint3_Sprint_Backlog.xlsx')
    # Also sync to /outputs
    os.makedirs('/outputs', exist_ok=True)
    build_project_plan(data, '/outputs/sprint3_Project_Plan.xlsx')
    build_sprint_backlog(data, '/outputs/sprint3_Sprint_Backlog.xlsx')
    print("All spreadsheets successfully generated using XlsxWriter!")

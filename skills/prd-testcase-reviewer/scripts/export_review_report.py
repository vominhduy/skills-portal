#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
export_review_report.py
-----------------------
Script tự động tạo file Excel Báo cáo Review Test Case 3 sheet chuẩn:
  1. Sheet 'Review TC' (Toàn bộ testcase và kết quả đối chiếu PRD)
  2. Sheet 'QC Action List' (Chỉ các dòng MODIFY / DELETE / ADD cần xử lý)
  3. Sheet 'Summary' (Bảng thống kê tỷ lệ, Action, Priority, Traceability Gaps)

Đồng thời xuất file Markdown tóm tắt versioned (_vN.md).

Sử dụng:
  python3 scripts/export_review_report.py --review-json "<path_to_review_json>" --output-dir "<output_dir>"
"""

import os
import sys
import json
import argparse
import re
from typing import List, Dict, Any

try:
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter
except ImportError:
    openpyxl = None


def get_next_version_filename(directory: str, base_name: str, ext: str) -> str:
    """Tìm số version kế tiếp chưa tồn tại trong thư mục output (_v1, _v2...)."""
    pattern = re.compile(rf"^{re.escape(base_name)}_v(\d+)\.{re.escape(ext)}$", re.IGNORECASE)
    highest = 0
    if os.path.exists(directory):
        for fname in os.listdir(directory):
            m = pattern.match(fname)
            if m:
                highest = max(highest, int(m.group(1)))
    v_next = highest + 1
    return f"{base_name}_v{v_next}.{ext}"


def create_excel_report(review_data: Dict[str, Any], output_path: str):
    if not openpyxl:
        raise ImportError("openpyxl chưa được cài đặt. Chạy `pip install openpyxl`.")

    wb = openpyxl.Workbook()
    # Xóa default sheet
    default_sheet = wb.active

    items: List[Dict[str, Any]] = review_data.get("review_items", [])
    summary: Dict[str, Any] = review_data.get("summary", {})
    prd_title: str = review_data.get("prd_title", "PRD Requirements")

    # Font & Styles
    font_family = "Segoe UI"
    font_title = Font(name=font_family, size=14, bold=True, color="1F4E79")
    font_subtitle = Font(name=font_family, size=10, italic=True, color="595959")
    font_header = Font(name=font_family, size=10, bold=True, color="FFFFFF")
    font_cell = Font(name=font_family, size=9.5)
    font_bold = Font(name=font_family, size=9.5, bold=True)
    font_stat_num = Font(name=font_family, size=11, bold=True)

    fill_header = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
    fill_sub_header = PatternFill(start_color="2F5597", end_color="2F5597", fill_type="solid")

    # Action Fills & Colors
    action_styles = {
        "KEEP": {
            "fill": PatternFill(start_color="E2EFDA", end_color="E2EFDA", fill_type="solid"),
            "font": Font(name=font_family, size=9.5, bold=True, color="375623")
        },
        "MODIFY": {
            "fill": PatternFill(start_color="FFF2CC", end_color="FFF2CC", fill_type="solid"),
            "font": Font(name=font_family, size=9.5, bold=True, color="B25900")
        },
        "DELETE": {
            "fill": PatternFill(start_color="FCE4D6", end_color="FCE4D6", fill_type="solid"),
            "font": Font(name=font_family, size=9.5, bold=True, color="C65911")
        },
        "ADD": {
            "fill": PatternFill(start_color="DDEBF7", end_color="DDEBF7", fill_type="solid"),
            "font": Font(name=font_family, size=9.5, bold=True, color="1F4E79")
        },
        "MERGE": {
            "fill": PatternFill(start_color="EDEDED", end_color="EDEDED", fill_type="solid"),
            "font": Font(name=font_family, size=9.5, bold=True, color="595959")
        }
    }

    # Priority Fills & Colors
    priority_styles = {
        "P0": {
            "fill": PatternFill(start_color="F8CBAD", end_color="F8CBAD", fill_type="solid"),
            "font": Font(name=font_family, size=9.5, bold=True, color="C00000")
        },
        "P1": {
            "fill": PatternFill(start_color="FFE699", end_color="FFE699", fill_type="solid"),
            "font": Font(name=font_family, size=9.5, bold=True, color="ED7D31")
        },
        "P2": {
            "fill": PatternFill(start_color="F2F2F2", end_color="F2F2F2", fill_type="solid"),
            "font": Font(name=font_family, size=9.5, color="595959")
        }
    }

    # Borders
    thin_border_side = Side(style="thin", color="D9D9D9")
    cell_border = Border(left=thin_border_side, right=thin_border_side, top=thin_border_side, bottom=thin_border_side)
    thick_bottom = Border(left=thin_border_side, right=thin_border_side, top=thin_border_side, bottom=Side(style="medium", color="1F4E79"))

    # Alignments
    align_left = Alignment(horizontal="left", vertical="top", wrap_text=True)
    align_center = Alignment(horizontal="center", vertical="top")
    align_header = Alignment(horizontal="center", vertical="center", wrap_text=True)

    headers = [
        ("STT", 6, align_center),
        ("Sheet / Module", 16, align_left),
        ("TC ID", 14, align_center),
        ("Req ID", 22, align_center),
        ("Nội dung Test Case", 30, align_left),
        ("Issue / Vấn đề phát hiện", 35, align_left),
        ("PRD Reference", 22, align_left),
        ("Expected hiện tại", 35, align_left),
        ("Expected chuẩn theo PRD", 35, align_left),
        ("Action", 12, align_center),
        ("Priority", 10, align_center)
    ]

    # ─────────────────────────────────────────────────────────────
    # SHEET 1: Review TC (Tất cả TCs)
    # ─────────────────────────────────────────────────────────────
    ws1 = wb.create_sheet(title="Review TC")
    ws1.views.sheetView[0].showGridLines = True

    # Title Banner
    ws1.merge_cells("A1:K1")
    ws1["A1"] = f"BÁO CÁO REVIEW VÀ ĐỐI CHIẾU TEST CASE THEO PRD: {prd_title.upper()}"
    ws1["A1"].font = font_title
    ws1["A1"].alignment = Alignment(horizontal="left", vertical="center")
    ws1.row_dimensions[1].height = 28

    ws1.merge_cells("A2:K2")
    ws1["A2"] = "Single Source of Truth: PRD > Acceptance Criteria / Business Rules > UI Spec > Current Test Cases"
    ws1["A2"].font = font_subtitle
    ws1.row_dimensions[2].height = 18

    # Headers at Row 4
    ws1.row_dimensions[4].height = 26
    for col_idx, (h_title, w, al) in enumerate(headers, start=1):
        cell = ws1.cell(row=4, column=col_idx, value=h_title)
        cell.font = font_header
        cell.fill = fill_header
        cell.alignment = align_header
        cell.border = cell_border
        col_letter = get_column_letter(col_idx)
        ws1.column_dimensions[col_letter].width = w

    # Data Rows
    current_row = 5
    for idx, item in enumerate(items, start=1):
        ws1.row_dimensions[current_row].height = 22
        action_val = str(item.get("action", "KEEP")).upper()
        prio_val = str(item.get("priority", "P2")).upper()

        row_vals = [
            idx,
            item.get("sheet", ""),
            item.get("tc_id", ""),
            item.get("req_id", ""),
            item.get("title", ""),
            item.get("issue", "Phù hợp PRD"),
            item.get("prd_ref", "PRD"),
            item.get("expected_current", ""),
            item.get("expected_correct", item.get("expected_current", "")),
            action_val,
            prio_val
        ]

        for col_idx, val in enumerate(row_vals, start=1):
            c = ws1.cell(row=current_row, column=col_idx, value=val)
            c.font = font_cell
            c.border = cell_border
            c.alignment = headers[col_idx - 1][2]

            # Style Action column
            if col_idx == 10 and action_val in action_styles:
                c.fill = action_styles[action_val]["fill"]
                c.font = action_styles[action_val]["font"]

            # Style Priority column
            if col_idx == 11 and prio_val in priority_styles:
                c.fill = priority_styles[prio_val]["fill"]
                c.font = priority_styles[prio_val]["font"]

        current_row += 1

    ws1.freeze_panes = "A5"
    ws1.auto_filter.ref = f"A4:K{current_row - 1}"

    # ─────────────────────────────────────────────────────────────
    # SHEET 2: QC Action List (Chỉ MODIFY, DELETE, ADD, MERGE)
    # ─────────────────────────────────────────────────────────────
    ws2 = wb.create_sheet(title="QC Action List")
    ws2.views.sheetView[0].showGridLines = True

    ws2.merge_cells("A1:K1")
    ws2["A1"] = f"DANH SÁCH TEST CASE CẦN THỰC HIỆN HÀNH ĐỘNG (MODIFY / DELETE / ADD)"
    ws2["A1"].font = font_title
    ws2.row_dimensions[1].height = 28

    ws2.merge_cells("A2:K2")
    ws2["A2"] = "Dành cho QC/Tester cập nhật bộ Test Case theo chuẩn PRD. Sắp xếp theo mức độ ưu tiên P0 -> P1 -> P2."
    ws2["A2"].font = font_subtitle
    ws2.row_dimensions[2].height = 18

    # Headers at Row 4
    ws2.row_dimensions[4].height = 26
    for col_idx, (h_title, w, al) in enumerate(headers, start=1):
        cell = ws2.cell(row=4, column=col_idx, value=h_title)
        cell.font = font_header
        cell.fill = fill_sub_header
        cell.alignment = align_header
        cell.border = cell_border
        col_letter = get_column_letter(col_idx)
        ws2.column_dimensions[col_letter].width = w

    qc_items = [it for it in items if str(it.get("action", "")).upper() in ["MODIFY", "DELETE", "ADD", "MERGE"]]
    # Sort QC items: P0 first, then P1, then P2
    prio_order = {"P0": 0, "P1": 1, "P2": 2}
    qc_items.sort(key=lambda x: prio_order.get(str(x.get("priority", "P2")).upper(), 9))

    current_row = 5
    for idx, item in enumerate(qc_items, start=1):
        ws2.row_dimensions[current_row].height = 24
        action_val = str(item.get("action", "MODIFY")).upper()
        prio_val = str(item.get("priority", "P1")).upper()

        row_vals = [
            idx,
            item.get("sheet", ""),
            item.get("tc_id", ""),
            item.get("req_id", ""),
            item.get("title", ""),
            item.get("issue", ""),
            item.get("prd_ref", ""),
            item.get("expected_current", ""),
            item.get("expected_correct", ""),
            action_val,
            prio_val
        ]

        for col_idx, val in enumerate(row_vals, start=1):
            c = ws2.cell(row=current_row, column=col_idx, value=val)
            c.font = font_cell
            c.border = cell_border
            c.alignment = headers[col_idx - 1][2]

            if col_idx == 10 and action_val in action_styles:
                c.fill = action_styles[action_val]["fill"]
                c.font = action_styles[action_val]["font"]

            if col_idx == 11 and prio_val in priority_styles:
                c.fill = priority_styles[prio_val]["fill"]
                c.font = priority_styles[prio_val]["font"]

        current_row += 1

    ws2.freeze_panes = "A5"
    ws2.auto_filter.ref = f"A4:K{max(5, current_row - 1)}"

    # ─────────────────────────────────────────────────────────────
    # SHEET 3: Summary & Metrics
    # ─────────────────────────────────────────────────────────────
    ws3 = wb.create_sheet(title="Summary")
    ws3.views.sheetView[0].showGridLines = True

    ws3["A1"] = "BẢNG TỔNG HỢP VÀ ĐÁNH GIÁ CHẤT LƯỢNG TEST SUITE (EXECUTIVE SUMMARY)"
    ws3["A1"].font = font_title
    ws3.row_dimensions[1].height = 28

    # Table 1: Phân loại Action
    ws3.merge_cells("A3:D3")
    ws3["A3"] = "1. THỐNG KÊ PHÂN LOẠI HÀNH ĐỘNG (ACTION BREAKDOWN)"
    ws3["A3"].font = Font(name=font_family, size=11, bold=True, color="1F4E79")

    ws3.row_dimensions[4].height = 22
    summary_headers = ["Phân loại Action", "Số lượng (TCs)", "Tỷ lệ (%)", "Mô tả / Hướng xử lý"]
    ws3.column_dimensions["A"].width = 24
    ws3.column_dimensions["B"].width = 16
    ws3.column_dimensions["C"].width = 14
    ws3.column_dimensions["D"].width = 50

    for col_idx, h_text in enumerate(summary_headers, start=1):
        c = ws3.cell(row=4, column=col_idx, value=h_text)
        c.font = font_header
        c.fill = fill_header
        c.alignment = align_header
        c.border = cell_border

    total_tcs = len(items)
    action_counts = {"KEEP": 0, "MODIFY": 0, "DELETE": 0, "ADD": 0, "MERGE": 0}
    priority_counts = {"P0": 0, "P1": 0, "P2": 0}

    for it in items:
        a = str(it.get("action", "KEEP")).upper()
        p = str(it.get("priority", "P2")).upper()
        action_counts[a] = action_counts.get(a, 0) + 1
        priority_counts[p] = priority_counts.get(p, 0) + 1

    action_descriptions = {
        "KEEP": "Khớp hoàn toàn với PRD, Expected đúng, giữ nguyên để thực thi.",
        "MODIFY": "Có giá trị nhưng cần chỉnh sửa Expected, mapping, precondition hoặc trigger.",
        "DELETE": "Ngoài scope PRD, thao tác sai spec, hoặc trùng lặp hoàn toàn.",
        "ADD": "Yêu cầu rõ ràng trong PRD nhưng bộ testcase chưa bao phủ (Coverage Gap).",
        "MERGE": "Gộp các testcase trùng lặp logic."
    }

    r_idx = 5
    for a_name in ["KEEP", "MODIFY", "DELETE", "ADD"]:
        cnt = action_counts.get(a_name, 0)
        pct = (cnt / total_tcs * 100) if total_tcs > 0 else 0
        desc = action_descriptions.get(a_name, "")
        ws3.cell(row=r_idx, column=1, value=a_name).font = font_bold
        ws3.cell(row=r_idx, column=2, value=cnt).font = font_stat_num
        ws3.cell(row=r_idx, column=3, value=f"{pct:.1f}%").font = font_cell
        ws3.cell(row=r_idx, column=4, value=desc).font = font_cell
        for c in range(1, 5):
            ws3.cell(row=r_idx, column=c).border = cell_border
        r_idx += 1

    # Total Row
    ws3.cell(row=r_idx, column=1, value="TỔNG CỘNG").font = font_bold
    ws3.cell(row=r_idx, column=2, value=total_tcs).font = font_stat_num
    ws3.cell(row=r_idx, column=3, value="100.0%").font = font_bold
    ws3.cell(row=r_idx, column=4, value="Toàn bộ testcase đã được đối chiếu 100%").font = font_bold
    for c in range(1, 5):
        ws3.cell(row=r_idx, column=c).fill = PatternFill(start_color="F2F2F2", end_color="F2F2F2", fill_type="solid")
        ws3.cell(row=r_idx, column=c).border = thick_bottom

    # Table 2: Priority Breakdown
    r_idx += 3
    ws3.merge_cells(f"A{r_idx}:D{r_idx}")
    ws3[f"A{r_idx}"] = "2. PHÂN LOẠI THEO MỨC ĐỘ ƯU TIÊN (PRIORITY DISTRIBUTION)"
    ws3[f"A{r_idx}"].font = Font(name=font_family, size=11, bold=True, color="1F4E79")

    r_idx += 1
    prio_headers = ["Priority", "Số lượng (TCs)", "Mức độ ảnh hưởng & Tiêu chí đánh giá", ""]
    for col_idx, h_text in enumerate(prio_headers[:3], start=1):
        c = ws3.cell(row=r_idx, column=col_idx, value=h_text)
        c.font = font_header
        c.fill = fill_sub_header
        c.alignment = align_header
        c.border = cell_border

    prio_descriptions = {
        "P0 (Nghiêm trọng)": (priority_counts.get("P0", 0), "Sai logic phê duyệt, quyền hạn, dữ liệu, thao tác trái UI Spec."),
        "P1 (Quan trọng)": (priority_counts.get("P1", 0), "Thiếu coverage chức năng/NFR quan trọng, sai traceability, missing edge case."),
        "P2 (Trung bình / Nhẹ)": (priority_counts.get("P2", 0), "Wording, kiểm thử QA bổ trợ (SQLi, XSS, chuỗi dài), format.")
    }

    r_idx += 1
    for p_label, (cnt, desc) in prio_descriptions.items():
        ws3.cell(row=r_idx, column=1, value=p_label).font = font_bold
        ws3.cell(row=r_idx, column=2, value=cnt).font = font_stat_num
        ws3.cell(row=r_idx, column=3, value=desc).font = font_cell
        for c in range(1, 4):
            ws3.cell(row=r_idx, column=c).border = cell_border
        r_idx += 1

    # Table 3: Gaps & Inconsistencies
    gaps: List[str] = summary.get("requirement_gaps", [])
    inconsistencies: List[str] = summary.get("prd_inconsistencies", [])

    if gaps or inconsistencies:
        r_idx += 2
        ws3.merge_cells(f"A{r_idx}:D{r_idx}")
        ws3[f"A{r_idx}"] = "3. LỖ HỔNG BAO PHỦ & MÂU THUẪN NỘI TẠI PRD (GAPS & INCONSISTENCIES)"
        ws3[f"A{r_idx}"].font = Font(name=font_family, size=11, bold=True, color="1F4E79")

        r_idx += 1
        if gaps:
            ws3.cell(row=r_idx, column=1, value="Coverage Gaps:").font = font_bold
            for gap in gaps:
                ws3.cell(row=r_idx, column=2, value=f"• {gap}").font = font_cell
                ws3.merge_cells(f"B{r_idx}:D{r_idx}")
                r_idx += 1
        if inconsistencies:
            ws3.cell(row=r_idx, column=1, value="PRD Inconsistencies:").font = font_bold
            for inc in inconsistencies:
                ws3.cell(row=r_idx, column=2, value=f"• {inc}").font = font_cell
                ws3.merge_cells(f"B{r_idx}:D{r_idx}")
                r_idx += 1

    # Xóa default sheet
    if default_sheet in wb.worksheets:
        wb.remove(default_sheet)

    wb.save(output_path)
    print(f"[export_review_report] Đã tạo thành công file Excel 3 sheet tại: {output_path}")


def export_markdown_summary(review_data: Dict[str, Any], output_path: str):
    items = review_data.get("review_items", [])
    summary = review_data.get("summary", {})
    prd_title = review_data.get("prd_title", "PRD Requirements")
    excel_filename = review_data.get("excel_filename", "TC_Review_Report.xlsx")

    total_tcs = len(items)
    action_counts = {"KEEP": 0, "MODIFY": 0, "DELETE": 0, "ADD": 0, "MERGE": 0}
    priority_counts = {"P0": 0, "P1": 0, "P2": 0}

    for it in items:
        a = str(it.get("action", "KEEP")).upper()
        p = str(it.get("priority", "P2")).upper()
        action_counts[a] = action_counts.get(a, 0) + 1
        priority_counts[p] = priority_counts.get(p, 0) + 1

    qc_items = [it for it in items if str(it.get("action", "")).upper() in ["MODIFY", "DELETE", "ADD", "MERGE"]]
    prio_order = {"P0": 0, "P1": 1, "P2": 2}
    qc_items.sort(key=lambda x: prio_order.get(str(x.get("priority", "P2")).upper(), 9))

    lines = []
    lines.append(f"# BÁO CÁO REVIEW VÀ ĐỐI CHIẾU TEST CASE THEO PRD: {prd_title}\n")
    lines.append(f"> **Single Source of Truth (SSOT):** `{review_data.get('prd_file', 'Tài liệu PRD')}`  ")
    lines.append(f"> **Tổng số Test Cases đã review:** **{total_tcs} TCs** (100% test case đã được đối chiếu)  ")
    lines.append(f"> **File Excel chi tiết 3 sheet:** `{excel_filename}`\n")
    lines.append("---\n")

    lines.append("## I. TỔNG HỢP KẾT QUẢ REVIEW\n")
    lines.append("### 1. Thống kê theo Action\n")
    lines.append("| Phân loại Action | Số lượng (TCs) | Tỷ lệ (%) | Mô tả & Hướng xử lý |")
    lines.append("|---|:---:|:---:|---|")
    lines.append(f"| **KEEP** | **{action_counts.get('KEEP', 0)}** | {action_counts.get('KEEP', 0)/max(1, total_tcs)*100:.1f}% | Test case bám sát PRD/AC/BR, Expected đúng, giữ nguyên để thực thi. |")
    lines.append(f"| **MODIFY** | **{action_counts.get('MODIFY', 0)}** | {action_counts.get('MODIFY', 0)/max(1, total_tcs)*100:.1f}% | Cần điều chỉnh Expected, mapping hoặc precondition theo PRD. |")
    lines.append(f"| **DELETE** | **{action_counts.get('DELETE', 0)}** | {action_counts.get('DELETE', 0)/max(1, total_tcs)*100:.1f}% | Thao tác sai so với UI Spec / ngoài scope PRD / duplicate. |")
    lines.append(f"| **ADD (Bổ sung)** | **{action_counts.get('ADD', 0)}** | - | Bổ sung coverage cho các yêu cầu PRD chưa có TC. |")
    if action_counts.get("MERGE", 0) > 0:
        lines.append(f"| **MERGE** | **{action_counts.get('MERGE', 0)}** | {action_counts.get('MERGE', 0)/max(1, total_tcs)*100:.1f}% | Gộp các test case trùng lặp logic. |")
    lines.append(f"| **TỔNG CỘNG** | **{total_tcs}** | **100%** | **Đã hoàn tất đối chiếu toàn diện.** |\n")

    lines.append("### 2. Thống kê theo Mức độ ưu tiên (Priority)\n")
    lines.append("| Mức độ Priority | Số lượng | Tiêu chí đánh giá |")
    lines.append("|---|:---:|---|")
    lines.append(f"| **P0 (Nghiêm trọng)** | **{priority_counts.get('P0', 0)} TCs** | Sai lệch logic phê duyệt, quyền hạn, CRUD behavior, thao tác vi phạm UI Spec. |")
    lines.append(f"| **P1 (Quan trọng)** | **{priority_counts.get('P1', 0)} TCs** | Thiếu coverage NFR, sai traceability, missing edge case lớn. |")
    lines.append(f"| **P2 (Trung bình / Nhẹ)** | **{priority_counts.get('P2', 0)} TCs** | Wording, ca kiểm thử bổ trợ QA Supplementary (SQLi, XSS, chuỗi dài). |\n")
    lines.append("---\n")

    lines.append("## II. DANH SÁCH TEST CASE CẦN THỰC HIỆN HÀNH ĐỘNG (QC ACTION LIST)\n")
    if qc_items:
        lines.append("| TC ID | Req ID | Issue / Vấn đề phát hiện | PRD Reference | Expected hiện tại | Expected chuẩn theo PRD | Action | Priority |")
        lines.append("|---|---|---|---|---|---|:---:|:---:|")

        for it in qc_items:
            t_id = it.get("tc_id", "")
            r_id = it.get("req_id", "")
            iss = it.get("issue", "").replace("\n", " ")
            pref = it.get("prd_ref", "").replace("\n", " ")
            exp_cur = it.get("expected_current", "").replace("\n", " ")
            exp_cor = it.get("expected_correct", "").replace("\n", " ")
            act = it.get("action", "")
            prio = it.get("priority", "")
            lines.append(f"| **{t_id}** | {r_id} | {iss} | {pref} | {exp_cur} | **{exp_cor}** | **{act}** | **{prio}** |")
    else:
        lines.append("*Không có Test Case nào cần chỉnh sửa (100% Test Case đều đạt chuẩn KEEP).*")

    gaps = summary.get("requirement_gaps", [])
    inconsistencies = summary.get("prd_inconsistencies", [])
    if gaps or inconsistencies:
        lines.append("\n---\n")
        lines.append("## III. LỖ HỔNG BAO PHỦ & MÂU THUẪN PRD (GAPS & INCONSISTENCIES)\n")
        if gaps:
            lines.append("### 1. Coverage Gaps (Yêu cầu PRD chưa có TC)")
            for g in gaps:
                lines.append(f"- **{g}**")
            lines.append("")
        if inconsistencies:
            lines.append("### 2. PRD Inconsistencies (Mâu thuẫn nội tại PRD cần PO/BA xác nhận)")
            for inc in inconsistencies:
                lines.append(f"- **{inc}**")
            lines.append("")

    lines.append("\n---\n")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"[export_review_report] Đã tạo thành công file Markdown tại: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Xuất báo cáo review Test Case ra file Excel 3 sheet và Markdown.")
    parser.add_argument("--review-json", "-r", required=True, help="Đường dẫn file JSON chứa kết quả review")
    parser.add_argument("--output-dir", "-o", default=os.environ.get("REPORT_OUTPUT_DIR", "/tmp"), help="Thư mục xuất file")
    parser.add_argument("--output-name", default="TC_Review_Report", help="Tên file Excel kết quả (không kèm đuôi)")
    parser.add_argument("--export-md", dest="export_md", action="store_true", default=True, help="Có xuất kèm file Markdown hay không (mặc định: True)")
    parser.add_argument("--no-export-md", dest="export_md", action="store_false", help="Không xuất file Markdown")
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)

    with open(args.review_json, "r", encoding="utf-8") as f:
        review_data = json.load(f)

    excel_file = get_next_version_filename(args.output_dir, args.output_name, "xlsx")
    excel_full_path = os.path.join(args.output_dir, excel_file)
    review_data["excel_filename"] = excel_file

    create_excel_report(review_data, excel_full_path)

    # Dọn dẹp các file JSON trung gian trong output_dir để kết quả chỉ còn duy nhất file deliverables
    for temp_name in ["parsed_testcases.json", "review_results.json", "all_tcs.json"]:
        temp_path = os.path.join(args.output_dir, temp_name)
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except OSError:
                pass

    if args.export_md:
        md_file = re.sub(r"\.xlsx$", ".md", excel_file, flags=re.IGNORECASE)
        md_full_path = os.path.join(args.output_dir, md_file)
        export_markdown_summary(review_data, md_full_path)
        print(f"[export_review_report] Hoàn tất! File Excel: {excel_file}, File Markdown: {md_file}")
    else:
        print(f"[export_review_report] Hoàn tất! File Excel: {excel_file}")


if __name__ == "__main__":
    main()

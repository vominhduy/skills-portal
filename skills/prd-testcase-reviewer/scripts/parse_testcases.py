#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
parse_testcases.py
------------------
Script chuẩn hóa việc đọc và trích xuất Test Case từ file Excel (.xlsx), CSV (.csv) hoặc Markdown.
Tự động nhận diện header, trích xuất tất cả sheet/module và xuất dữ liệu ra file JSON có cấu trúc.

Sử dụng:
  python3 scripts/parse_testcases.py --input-file "<path_to_excel_or_csv>" --output-dir "<output_dir>"
"""

import os
import sys
import json
import argparse
import re
from typing import List, Dict, Any, Optional

try:
    import openpyxl
except ImportError:
    openpyxl = None


def normalize_header(name: Optional[str]) -> str:
    if not name:
        return ""
    s = str(name).strip().lower()
    s = re.sub(r'[\r\n\t]+', ' ', s)
    s = re.sub(r'\s+', ' ', s)
    return s


def find_header_row(ws, max_scan_rows=15):
    """
    Tìm dòng chứa header cột testcase theo template chuẩn.
    Chỉ công nhận dòng header nếu có đầy đủ các cột bắt buộc:
    - Test Title / Nội dung test
    - Expected Result / Kết quả mong đợi
    - Và ít nhất một trong các cột: Testcase ID, Req ID, hoặc Test Steps.
    """
    best_row = None
    best_score = 0
    header_map = {}

    keywords = {
        'tc_id': ['testcase id', 'test case id', 'tc id', 'mã testcase', 'mã tc', 'id'],
        'req_id': ['req id', 'requirement id', 'mã yêu cầu', 'mã req', 'req_id', 'traceability'],
        'doc_source': ['doc source', 'nguồn tài liệu', 'doc_source'],
        'group': ['group', 'nhóm', 'loại', 'category'],
        'priority': ['priority', 'độ ưu tiên', 'mức ưu tiên', 'prio'],
        'title': ['test title', 'nội dung test', 'tên testcase', 'tiêu đề', 'title', 'test name', 'nội dung'],
        'precondition': ['pre-condition', 'precondition', 'điều kiện', 'tiền điều kiện', 'dữ liệu test', 'test data'],
        'steps': ['test steps', 'các bước', 'bước thực hiện', 'steps', 'hành động', 'action'],
        'expected': ['expected result', 'kết quả mong đợi', 'kết quả kỳ vọng', 'expected', 'kết quả'],
        'origin': ['origin', 'nguồn gốc'],
        'review': ['review', 'đánh giá'],
        'automated': ['automated', 'tự động hóa'],
    }

    for r in range(1, min(max_scan_rows + 1, ws.max_row + 1)):
        row_cells = [ws.cell(row=r, column=c).value for c in range(1, min(30, ws.max_column + 1))]
        normalized = [normalize_header(c) for c in row_cells]
        
        current_map = {}
        score = 0
        for col_idx, text in enumerate(normalized, start=1):
            if not text:
                continue
            for field, aliases in keywords.items():
                if field not in current_map:
                    for alias in aliases:
                        if alias in text:
                            current_map[field] = col_idx
                            score += 1
                            break

        # BẮT BUỘC: Phải có cả cột 'title' và 'expected' VÀ có ít nhất một trong ('tc_id', 'req_id', 'steps')
        is_valid_tc_header = ('title' in current_map and 'expected' in current_map and
                              ('tc_id' in current_map or 'req_id' in current_map or 'steps' in current_map))

        if is_valid_tc_header and score > best_score:
            best_score = score
            best_row = r
            header_map = current_map

    return best_row, header_map


def extract_from_excel(file_path: str) -> List[Dict[str, Any]]:
    if not openpyxl:
        raise ImportError("openpyxl chưa được cài đặt. Chạy `pip install openpyxl`.")

    wb_val = openpyxl.load_workbook(file_path, data_only=True)
    all_testcases = []

    for sheet_name in wb_val.sheetnames:
        ws = wb_val[sheet_name]
        if ws.sheet_state == 'hidden':
            print(f"[parse_testcases] Bỏ qua sheet ẩn: '{sheet_name}'")
            continue

        header_row, hmap = find_header_row(ws)
        if not header_row or not hmap:
            print(f"[parse_testcases] Bỏ qua sheet '{sheet_name}' (không khớp cấu trúc cột Test Case template chuẩn).")
            continue

        # Lấy module name / function code nếu có ở các dòng đầu
        module_code = ""
        module_name = sheet_name
        for r in range(1, header_row):
            for c in range(1, 10):
                val = ws.cell(row=r, column=c).value
                if val:
                    v_str = str(val).strip()
                    if v_str.lower() in ['mã chức năng', 'function id', 'module id']:
                        next_val = ws.cell(row=r, column=c+2).value or ws.cell(row=r, column=c+1).value
                        if next_val:
                            module_code = str(next_val).strip()
                    elif v_str.lower() in ['tên chức năng', 'function name', 'module name']:
                        next_val = ws.cell(row=r, column=c+2).value or ws.cell(row=r, column=c+1).value
                        if next_val:
                            module_name = str(next_val).strip()

        col_id = hmap.get('tc_id', 1)
        col_req = hmap.get('req_id', 2)
        col_doc = hmap.get('doc_source')
        col_grp = hmap.get('group')
        col_prio = hmap.get('priority')
        col_title = hmap.get('title')
        col_pre = hmap.get('precondition')
        col_steps = hmap.get('steps')
        col_exp = hmap.get('expected')

        sheet_tc_count = 0
        for r in range(header_row + 1, ws.max_row + 1):
            raw_id = ws.cell(row=r, column=col_id).value
            raw_title = ws.cell(row=r, column=col_title).value if col_title else None
            raw_steps = ws.cell(row=r, column=col_steps).value if col_steps else None
            raw_exp = ws.cell(row=r, column=col_exp).value if col_exp else None

            # Kiểm tra dòng trống
            if not raw_id and not raw_title and not raw_steps and not raw_exp:
                continue

            # Bỏ qua các dòng phân cách / banner (ví dụ: '▬▬  A. Danh sách ứng dụng  ')
            first_non_empty = ""
            for c in range(1, 6):
                val = ws.cell(row=r, column=c).value
                if val and str(val).strip():
                    first_non_empty = str(val).strip()
                    break
            if first_non_empty.startswith('▬▬') or first_non_empty.startswith('==='):
                continue

            sheet_tc_count += 1

            # Chuẩn hóa TC ID
            tc_id = str(raw_id).strip() if raw_id is not None else ""
            if not tc_id or tc_id.startswith('='):
                prefix = module_code or f"TC_{len(all_testcases)+1:02d}"
                tc_id = f"{prefix}.{sheet_tc_count}"

            req_id = str(ws.cell(row=r, column=col_req).value or '').strip() if col_req else ''
            doc_source = str(ws.cell(row=r, column=col_doc).value or '').strip() if col_doc else ''
            group = str(ws.cell(row=r, column=col_grp).value or '').strip() if col_grp else ''
            priority = str(ws.cell(row=r, column=col_prio).value or '').strip() if col_prio else ''
            title = str(raw_title or '').strip()
            precondition = str(raw_pre or '').strip() if (col_pre and (raw_pre := ws.cell(row=r, column=col_pre).value)) else ''
            steps = str(raw_steps or '').strip()
            expected = str(raw_exp or '').strip()

            # Nếu cả title, steps, expected đều rỗng thì không phải TC hợp lệ
            if not title and not steps and not expected:
                continue

            all_testcases.append({
                "sheet": sheet_name,
                "module_name": module_name,
                "module_code": module_code,
                "row_index": r,
                "tc_id": tc_id,
                "req_id": req_id,
                "doc_source": doc_source,
                "group": group,
                "priority": priority,
                "title": title,
                "precondition": precondition,
                "steps": steps,
                "expected": expected
            })

    return all_testcases


def extract_from_csv(file_path: str) -> List[Dict[str, Any]]:
    import csv
    all_testcases = []
    with open(file_path, mode='r', encoding='utf-8-sig', errors='replace') as f:
        reader = csv.DictReader(f)
        for idx, row in enumerate(reader, start=1):
            normalized_row = {normalize_header(k): v for k, v in row.items()}
            tc_id = normalized_row.get('testcase id') or normalized_row.get('tc id') or normalized_row.get('id') or f"TC_{idx:03d}"
            req_id = normalized_row.get('req id') or normalized_row.get('requirement id') or ""
            title = normalized_row.get('test title') or normalized_row.get('nội dung test') or normalized_row.get('title') or ""
            steps = normalized_row.get('test steps') or normalized_row.get('các bước') or normalized_row.get('steps') or ""
            expected = normalized_row.get('expected result') or normalized_row.get('kết quả mong đợi') or normalized_row.get('expected') or ""
            group = normalized_row.get('group') or normalized_row.get('nhóm') or ""
            priority = normalized_row.get('priority') or normalized_row.get('độ ưu tiên') or ""
            precondition = normalized_row.get('pre-condition') or normalized_row.get('điều kiện') or ""

            if title or steps or expected:
                all_testcases.append({
                    "sheet": "CSV",
                    "module_name": "CSV",
                    "module_code": "",
                    "row_index": idx + 1,
                    "tc_id": str(tc_id).strip(),
                    "req_id": str(req_id).strip(),
                    "doc_source": "",
                    "group": str(group).strip(),
                    "priority": str(priority).strip(),
                    "title": str(title).strip(),
                    "precondition": str(precondition).strip(),
                    "steps": str(steps).strip(),
                    "expected": str(expected).strip()
                })
    return all_testcases


def main():
    parser = argparse.ArgumentParser(description="Trích xuất danh sách Test Case từ file Excel/CSV.")
    parser.add_argument("--input-file", "-i", required=True, help="Đường dẫn file Test Case Excel (.xlsx) hoặc CSV")
    parser.add_argument("--output-dir", "-o", default=os.environ.get("REPORT_OUTPUT_DIR", "/tmp"), help="Thư mục xuất file JSON")
    parser.add_argument("--output-name", default="parsed_testcases.json", help="Tên file JSON kết quả")
    args = parser.parse_args()

    input_file = os.path.abspath(args.input_file)
    if not os.path.exists(input_file):
        print(f"[ERROR] File không tồn tại: {input_file}", file=sys.stderr)
        sys.exit(1)

    os.makedirs(args.output_dir, exist_ok=True)
    out_json_path = os.path.join(args.output_dir, args.output_name)

    print(f"[parse_testcases] Đang đọc file: {input_file}")

    if input_file.lower().endswith(('.xlsx', '.xlsm', '.xltx')):
        testcases = extract_from_excel(input_file)
    elif input_file.lower().endswith('.csv'):
        testcases = extract_from_csv(input_file)
    else:
        print(f"[ERROR] Định dạng file không được hỗ trợ (cần .xlsx hoặc .csv): {input_file}", file=sys.stderr)
        sys.exit(1)

    if not testcases:
        print("[WARN] Không trích xuất được Test Case nào từ file.", file=sys.stderr)

    # Thống kê theo sheet
    sheet_stats = {}
    for tc in testcases:
        s = tc.get("sheet", "Unknown")
        sheet_stats[s] = sheet_stats.get(s, 0) + 1

    summary_data = {
        "source_file": input_file,
        "total_testcases": len(testcases),
        "sheets": sheet_stats,
        "testcases": testcases
    }

    with open(out_json_path, "w", encoding="utf-8") as f:
        json.dump(summary_data, f, ensure_ascii=False, indent=2)

    print(f"[parse_testcases] Thành công! Tổng cộng: {len(testcases)} Test Cases.")
    for s, cnt in sheet_stats.items():
        print(f"  - Sheet '{s}': {cnt} TCs")
    print(f"[parse_testcases] JSON kết quả đã ghi tại: {out_json_path}")


if __name__ == "__main__":
    main()

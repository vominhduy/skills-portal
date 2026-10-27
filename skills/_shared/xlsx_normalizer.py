#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
xlsx_normalizer.py
------------------
Bộ chuẩn hóa OpenXML (.xlsx) toàn cục (Universal OpenXML Sanitizer & Normalizer)
cho tất cả các Skills trong hệ thống (sprint-planning, prd-testcase-reviewer,
hrm-weekly-report, product-backlog, jira-import, v.v.).

Đảm bảo 100% file .xlsx sinh ra (dù bằng openpyxl, xlsxwriter, exceljs hay chỉnh sửa XML):
1. Có cấu trúc ZIP chuẩn OpenXML với `[Content_Types].xml` nằm ở đầu tiên, không chứa entry thư mục rỗng (`/`).
2. Chuyển toàn bộ chuỗi `t="inlineStr"` (do openpyxl sinh ra) sang bảng `xl/sharedStrings.xml` (`t="s"`)
   và đăng ký đầy đủ trong `[Content_Types].xml` + `xl/_rels/workbook.xml.rels`.
3. Chuẩn hóa mọi ô công thức (`<f>`): loại bỏ dấu `=` thừa ở đầu công thức trong XML, và đảm bảo luôn có thẻ `<v>` (cached value).
4. Loại bỏ các thẻ `<dataValidation>` trùng lặp/chồng lấn `sqref` (nguyên nhân khiến Excel báo lỗi Unreadable Content).
"""

import io
import os
import re
import sys
import zipfile
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional, Tuple

NS_MAIN = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
NS_REL_OFFICE = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
NS_PKG_REL = "http://schemas.openxmlformats.org/package/2006/relationships"
NS_CONTENT_TYPES = "http://schemas.openxmlformats.org/package/2006/content-types"
NS_XML = "http://www.w3.org/XML/1998/namespace"


def _extract_inline_text(is_elem: ET.Element) -> str:
    """Trích xuất toàn bộ text từ thẻ <is> (hỗ trợ cả <t> đơn và rich text <r><t>)."""
    parts: List[str] = []
    for t_el in is_elem.iter(f"{{{NS_MAIN}}}t"):
        if t_el.text:
            parts.append(t_el.text)
    return "".join(parts)


def _load_existing_shared_strings(xml_bytes: Optional[bytes]) -> Tuple[List[str], Dict[str, int]]:
    strings_list: List[str] = []
    string_to_idx: Dict[str, int] = {}
    if not xml_bytes:
        return strings_list, string_to_idx
    try:
        root = ET.fromstring(xml_bytes)
        for si in root.findall(f"{{{NS_MAIN}}}si"):
            text = _extract_inline_text(si)
            idx = len(strings_list)
            strings_list.append(text)
            if text not in string_to_idx:
                string_to_idx[text] = idx
    except Exception:
        pass
    return strings_list, string_to_idx


def _get_or_add_shared_string(text: str, strings_list: List[str], string_to_idx: Dict[str, int]) -> int:
    if text in string_to_idx:
        return string_to_idx[text]
    idx = len(strings_list)
    strings_list.append(text)
    string_to_idx[text] = idx
    return idx


def _build_shared_strings_xml(strings_list: List[str], total_refs: int) -> bytes:
    ET.register_namespace("", NS_MAIN)
    root = ET.Element(
        f"{{{NS_MAIN}}}sst",
        {
            "count": str(max(total_refs, len(strings_list))),
            "uniqueCount": str(len(strings_list)),
        },
    )
    for s in strings_list:
        si = ET.SubElement(root, f"{{{NS_MAIN}}}si")
        t = ET.SubElement(si, f"{{{NS_MAIN}}}t")
        if s and (s[0].isspace() or s[-1].isspace() or "\n" in s or "\r" in s or "\t" in s):
            t.set(f"{{{NS_XML}}}space", "preserve")
        t.text = s
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def _normalize_worksheet_xml(
    xml_bytes: bytes,
    strings_list: List[str],
    string_to_idx: Dict[str, int],
) -> Tuple[bytes, int]:
    """Chuẩn hóa 1 sheet XML:
    - Chuyển inlineStr -> sharedStrings (t="s")
    - Chuẩn hóa công thức <f> và đảm bảo có <v>
    - Khử trùng lặp <dataValidation>
    """
    ET.register_namespace("", NS_MAIN)
    ET.register_namespace("r", NS_REL_OFFICE)
    root = ET.fromstring(xml_bytes)
    shared_ref_count = 0

    # 1. Duyệt các ô <c> trong sheetData
    sheet_data = root.find(f"{{{NS_MAIN}}}sheetData")
    if sheet_data is not None:
        for row_el in sheet_data.findall(f"{{{NS_MAIN}}}row"):
            for c_el in row_el.findall(f"{{{NS_MAIN}}}c"):
                c_type = c_el.attrib.get("t", "")
                f_el = c_el.find(f"{{{NS_MAIN}}}f")
                is_el = c_el.find(f"{{{NS_MAIN}}}is")
                v_el = c_el.find(f"{{{NS_MAIN}}}v")

                # Nếu là ô công thức <f>
                if f_el is not None:
                    if f_el.text:
                        clean_f = f_el.text.strip()
                        if clean_f.startswith("="):
                            clean_f = clean_f.lstrip("=")
                        f_el.text = clean_f
                    # Xóa <is> nếu có trên ô công thức
                    if is_el is not None:
                        c_el.remove(is_el)
                    if c_type == "inlineStr":
                        del c_el.attrib["t"]
                    if v_el is None:
                        v_el = ET.SubElement(c_el, f"{{{NS_MAIN}}}v")
                        v_el.text = "0"
                elif c_type == "inlineStr" or is_el is not None:
                    text_val = _extract_inline_text(is_el) if is_el is not None else (v_el.text if v_el is not None and v_el.text else "")
                    if is_el is not None:
                        c_el.remove(is_el)
                    s_idx = _get_or_add_shared_string(text_val, strings_list, string_to_idx)
                    c_el.attrib["t"] = "s"
                    if v_el is None:
                        v_el = ET.SubElement(c_el, f"{{{NS_MAIN}}}v")
                    v_el.text = str(s_idx)
                    shared_ref_count += 1
                elif c_type == "s":
                    shared_ref_count += 1

    # 2. Khử trùng lặp <dataValidation>
    for dvals_el in root.findall(f"{{{NS_MAIN}}}dataValidations"):
        seen_sqrefs = set()
        unique_dvs = []
        for dv in list(dvals_el.findall(f"{{{NS_MAIN}}}dataValidation")):
            sqref = " ".join(sorted(dv.attrib.get("sqref", "").split()))
            if not sqref or sqref in seen_sqrefs:
                dvals_el.remove(dv)
            else:
                seen_sqrefs.add(sqref)
                unique_dvs.append(dv)
        if len(unique_dvs) == 0:
            root.remove(dvals_el)
        else:
            dvals_el.attrib["count"] = str(len(unique_dvs))

    return ET.tostring(root, encoding="utf-8", xml_declaration=True), shared_ref_count


def _ensure_content_types_shared_strings(xml_bytes: bytes) -> bytes:
    ET.register_namespace("", NS_CONTENT_TYPES)
    root = ET.fromstring(xml_bytes)
    has_ss = False
    for ov in root.findall(f"{{{NS_CONTENT_TYPES}}}Override"):
        if ov.attrib.get("PartName") == "/xl/sharedStrings.xml":
            has_ss = True
            break
    if not has_ss:
        ET.SubElement(
            root,
            f"{{{NS_CONTENT_TYPES}}}Override",
            {
                "PartName": "/xl/sharedStrings.xml",
                "ContentType": "application/vnd.openxmlformats-officedocument.spreadsheetml.sharedStrings+xml",
            },
        )
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def _ensure_workbook_rels_shared_strings(xml_bytes: bytes) -> bytes:
    ET.register_namespace("", NS_PKG_REL)
    root = ET.fromstring(xml_bytes)
    has_ss = False
    existing_ids = set()
    for rel in root.findall(f"{{{NS_PKG_REL}}}Relationship"):
        rid = rel.attrib.get("Id", "")
        existing_ids.add(rid)
        target = rel.attrib.get("Target", "")
        if "sharedStrings.xml" in target:
            has_ss = True
    if not has_ss:
        next_num = 1
        while f"rId{next_num}" in existing_ids:
            next_num += 1
        ET.SubElement(
            root,
            f"{{{NS_PKG_REL}}}Relationship",
            {
                "Id": f"rId{next_num}",
                "Type": "http://schemas.openxmlformats.org/officeDocument/2006/relationships/sharedStrings",
                "Target": "sharedStrings.xml",
            },
        )
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def normalize_xlsx_bytes(orig_bytes: bytes) -> bytes:
    """Nhận bytes của file .xlsx bất kỳ và trả về bytes .xlsx đạt chuẩn OpenXML nghiêm ngặt."""
    if not orig_bytes or len(orig_bytes) < 4 or orig_bytes[:4] != b"PK\x03\x04":
        raise ValueError("Dữ liệu không phải file ZIP/XLSX hợp lệ (thiếu chữ ký PK\\x03\\x04).")

    zin = zipfile.ZipFile(io.BytesIO(orig_bytes), "r")
    namelist = [n for n in zin.namelist() if not n.endswith("/")]

    files_map: Dict[str, bytes] = {}
    for name in namelist:
        files_map[name] = zin.read(name)
    zin.close()

    # Load existing sharedStrings if present
    strings_list, string_to_idx = _load_existing_shared_strings(files_map.get("xl/sharedStrings.xml"))
    total_shared_refs = 0

    # Normalize all worksheet XMLs
    for name in list(files_map.keys()):
        if re.match(r"^xl/worksheets/sheet\d+\.xml$", name):
            norm_xml, refs = _normalize_worksheet_xml(files_map[name], strings_list, string_to_idx)
            files_map[name] = norm_xml
            total_shared_refs += refs

    # Always write xl/sharedStrings.xml if there are strings or if it didn't exist
    if len(strings_list) == 0:
        strings_list.append("")
        string_to_idx[""] = 0
    files_map["xl/sharedStrings.xml"] = _build_shared_strings_xml(strings_list, total_shared_refs)

    if "[Content_Types].xml" in files_map:
        files_map["[Content_Types].xml"] = _ensure_content_types_shared_strings(files_map["[Content_Types].xml"])
    if "xl/_rels/workbook.xml.rels" in files_map:
        files_map["xl/_rels/workbook.xml.rels"] = _ensure_workbook_rels_shared_strings(files_map["xl/_rels/workbook.xml.rels"])

    # Remove calcChain.xml if present so Excel recalculates cleanly without stale chain mismatch
    if "xl/calcChain.xml" in files_map:
        del files_map["xl/calcChain.xml"]

    # Order entries with [Content_Types].xml first per OpenXML convention
    priority_order = [
        "[Content_Types].xml",
        "_rels/.rels",
        "xl/workbook.xml",
        "xl/_rels/workbook.xml.rels",
    ]
    ordered_names: List[str] = []
    for p in priority_order:
        if p in files_map:
            ordered_names.append(p)
    for k in sorted(files_map.keys()):
        if k not in ordered_names:
            ordered_names.append(k)

    zout_buf = io.BytesIO()
    with zipfile.ZipFile(zout_buf, "w", zipfile.ZIP_DEFLATED) as zout:
        for name in ordered_names:
            zout.writestr(name, files_map[name])

    return zout_buf.getvalue()


def normalize_xlsx_file(file_path: str) -> bool:
    """Chuẩn hóa trực tiếp file .xlsx trên đĩa (giữ nguyên mtime gốc của file)."""
    if not os.path.exists(file_path) or not os.path.isfile(file_path):
        return False
    st = os.stat(file_path)
    with open(file_path, "rb") as f:
        orig = f.read()
    norm = normalize_xlsx_bytes(orig)
    with open(file_path, "wb") as f:
        f.write(norm)
    try:
        os.utime(file_path, (st.st_atime, st.st_mtime))
    except Exception:
        pass
    return True


if __name__ == "__main__":
    for arg in sys.argv[1:]:
        if os.path.exists(arg):
            ok = normalize_xlsx_file(arg)
            print(f"✅ Normalized OpenXML: {arg} ({os.path.getsize(arg)} bytes)")
        else:
            print(f"❌ File not found: {arg}", file=sys.stderr)

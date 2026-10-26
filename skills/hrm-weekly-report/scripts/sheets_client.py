"""Client đọc/ghi bảng tính cho HRM Weekly Report:

1. PHẦN MICROSOFT EXCEL ONLINE (SharePoint / OneDrive qua Graph API):
   - Cấu trúc 19 cột A–S theo đúng file Excel SharePoint mới (ISC _KEY PROJECT_2026.xlsx / Sheet FTI):
     A (0) : Project Group                              -> "FTI" / division
     B (1) : Tool/ Application                          -> p["projectCode"]
     C (2) : Module/Parent Task/Epic                    -> p["displayName"] (Match key)
     D (3) : Feature/Task/User Story                    -> p["mainFeature"] (escape '-' -> "'-")
     E (4) : Description                                -> p["goal"] (escape '-' -> "'-")
     F (5) : PIC                                        -> p["pm"]
     G (6) : Priority                                   -> preserved / "3 - High"
     H (7) : %Done                                      -> p["progress"]
     I (8) : Status                                     -> p["projectPhase"]
     J (9) : Project Health                             -> p["projectHealth"]
     K (10): Release Date                               -> p["planDueDate"]
     L (11): This Week [Done]                           -> p["done"] (escape '-' -> "'-")
     M (12): Next Week Plan [Doing/Will Do]             -> p["continuationPlan"] (escape '-' -> "'-")
     N (13): Issues & Actions                           -> p["riskOrIssues"] (escape '-' -> "'-")
     O (14): RELEASE NOTE (Output - Module - Function)  -> p["releaseNote"] (escape '-' -> "'-")
     P (15): OKR/KEY BENEFIT-VALUE (Số liệu cụ thể)     -> preserved / p["valueMetric"] (escape '-' -> "'-")
     Q (16): NOTES                                      -> preserved (escape '-' -> "'-")
     R (17): LAUNCHING                                  -> p["quarter"]
     S (18): Report Date (Ngày báo cáo)                 -> _today_str() (DD-Mon-YYYY)
   - Ưu tiên Cell-level PATCH Range trực tiếp (Graph Workbook API).
   - Tự động fallback sang Content API có eTag (If-Match) khi file chứa Pivot Table / lỗi 501.

2. PHẦN GOOGLE SHEETS LEGACY:
   - Sheet 1 (27 cột A–AA): Division | ProjectCode | DisplayName | MainFeature | Goal | PM | "" | "" | Progress | ProjectPhase | ProjectHealth | PlanStartDate | PlanDueDate | PlanDueDate | Quarter | "" | "" | "" | "" | Value Code | Value Metric | Business Impact | Lasted Updated | Done | Doing/Will Do | Issues & Actions | ReleaseNote
   - Sheet 2 (19 cột A–S - File 13ENSxJkc9lL43lmofw9HIxF9sdR_cElNtW2D581KIkw): Division | ProjectCode | DisplayName | MainFeature | Goal | PM | "" | Progress | ProjectPhase | ProjectHealth | PlanDueDate | Done | ContinuationPlan | RiskOrIssues | Release Note | "" | "" | Quarter | Report Date (Cột S)
"""
from __future__ import annotations

import io
import os
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional

_HERE = os.path.dirname(os.path.abspath(__file__))
_SHARED_DIR = os.path.join(_HERE, "..", "..", "_shared")
if _SHARED_DIR not in sys.path:
    sys.path.insert(0, _SHARED_DIR)

try:
    import ms_graph_client as mg
except ImportError:
    mg = None

try:
    import openpyxl
except ImportError:
    openpyxl = None

import requests
from google.auth.transport.requests import Request as GoogleAuthRequest
from google.oauth2 import service_account

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
API_BASE = "https://sheets.googleapis.com/v4/spreadsheets"

# ═════════════════════════════════════════════════════════════
# 1. CẤU TRÚC CHO GOOGLE SHEETS LEGACY
# ═════════════════════════════════════════════════════════════

# Header khớp 100% với extension gốc (27 cột A–AA). W = "Lasted Updated" ghi ngày chạy.
HEADER_ROW = [
    "Division", "ProjectCode", "DisplayName", "MainFeature", "Goal", "PM", "", "",
    "Progress", "ProjectPhase", "ProjectHealth", "PlanStartDate", "PlanDueDate", "PlanDueDate",
    "Quarter", "", "", "", "", "Value Code", "Value Metric", "Business Impact", "Lasted Updated",
    "Done", "Doing/Will Do", "Issues & Actions", "ReleaseNote",
]
PRESERVED_COLS = [0, 6, 7, 15, 16, 17, 18]

# Schema 19 cột A–S - giống file Google Sheet (13ENSxJkc9lL43lmofw9HIxF9sdR_cElNtW2D581KIkw) có thêm Cột S
HEADER_ROW_V2 = [
    "Division", "ProjectCode", "DisplayName", "MainFeature", "Goal", "PM", "",
    "Progress", "ProjectPhase", "ProjectHealth", "PlanDueDate",
    "Done", "ContinuationPlan", "RiskOrIssues", "Release Note", "", "", "Quarter",
    "Report Date",  # Cột S (index 18) - Ngày báo cáo
]
PRESERVED_COLS_V2 = [0, 6]


# ═════════════════════════════════════════════════════════════
# 2. CẤU TRÚC CHO FILE EXCEL SHAREPOINT MỚI
# ═════════════════════════════════════════════════════════════

# Header dòng 1 cho Sheet Project2026 (78 cột A–BZ)
EXCEL_PROJECT2026_HEADER_R1 = [
    "PROJECT", "", "", "", "",
    "OWNERSHIP", "", "",
    "DELIVERY", "", "", "", "",
    "BUSINESS OUTCOME", "", "",
    "VALUES", "",
    "RESOURCE", "", "", "",
    # 48 cột Resource (12 tháng x PM, BA, DEV, QC)
    "PM", "BA", "DEV", "QC",  # Jan
    "PM", "BA", "DEV", "QC",  # Feb
    "PM", "BA", "DEV", "QC",  # Mar
    "PM", "BA", "DEV", "QC",  # Apr
    "PM", "BA", "DEV", "QC",  # May
    "PM", "BA", "DEV", "QC",  # Jun
    "PM", "BA", "DEV", "QC",  # Jul
    "PM", "BA", "DEV", "QC",  # Aug
    "PM", "BA", "DEV", "QC",  # Sep
    "PM", "BA", "DEV", "QC",  # Oct
    "PM", "BA", "DEV", "QC",  # Nov
    "PM", "BA", "DEV", "QC",  # Dec
    "", "", "", "", "", "", "", "",
]

# Header dòng 2 cho Sheet Project2026 (78 cột A–BZ - 2026_SU02_Resource_Planning.xlsx)
EXCEL_PROJECT2026_HEADER = [
    "No.",                                         # A (0)
    "Project/Version",                             # B (1) - DisplayName (Match Key)
    "Release/Sprint",                              # C (2) - Release/Sprint (Preserved)
    "Application",                                 # D (3) - ProjectCode
    "Project Type",                                # E (4) - Preserved
    "Business Owner",                              # F (5) - Division / Business Owner
    "Product Owner",                               # G (6) - PO (Preserved)
    "PM",                                          # H (7) - PM
    "Project Status",                              # I (8) - Status / ProjectPhase
    "Priority",                                    # J (9) - Priority (Preserved)
    "Start date\n(MM/dd/yyyy)",                    # K (10) - PlanStartDate
    "Target Go-live\n(MM/dd/yyyy)",                # L (11) - PlanDueDate
    "Actual Go-live\n(MM/dd/yyyy)",                # M (12) - Preserved
    "Business Problem",                            # N (13) - MainFeature
    "Business Outcome",                            # O (14) - Goal
    "Key Scope/Sprint Goal",                       # P (15) - Preserved
    "Value Dimension",                             # Q (16) - ValueCodes (Preserved)
    "Primary Value Metric",                        # R (17) - ValueMetric / BusinessImpact
    "Estimated Effort (MD)",                       # S (18) - Preserved
    "Actual Effort (MD)",                          # T (19) - Preserved
    "QC Defect Rate (%)",                          # U (20) - Preserved
    "UAT Defect Rate (%)",                         # V (21) - Preserved
    # Resource allocations (Jan..Dec x 4 roles = 48 cột W..BR, index 22..69) -> 100% PRESERVED
    *[f"Resource_{i}" for i in range(48)],
    "%Done",                                       # BS (70) - Progress
    "Status",                                      # BT (71) - ProjectPhase
    "Project Health",                              # BU (72) - ProjectHealth
    "Release Date",                                # BV (73) - PlanDueDate
    "This Week [Done]",                            # BW (74) - Done
    "Next Week Plan [Doing/Will Do]",              # BX (75) - ContinuationPlan
    "Issues & Actions",                            # BY (76) - RiskOrIssues
    "RELEASE NOTE\n(Output - Module - Function)",  # BZ (77) - ReleaseNote
]

# Header cho Sheet 1 (Portfolio 2026 - 27 cột A–AA)
EXCEL_PORTFOLIO_HEADER = [
    "Unit",                                        # A (0)
    "Product",                                     # B (1) - ProjectCode
    "Project",                                     # C (2) - DisplayName (Match Key)
    "Business Problem/User Story",                 # D (3) - MainFeature
    "Solution/Project Goal",                       # E (4) - Goal
    "PM",                                          # F (5) - PM
    "PO",                                          # G (6) - PO (Preserved)
    "Priority",                                    # H (7) - Priority (Preserved)
    "%Done",                                       # I (8) - Progress
    "Status",                                      # J (9) - ProjectPhase
    "Project Health",                              # K (10) - ProjectHealth
    "Start date",                                  # L (11) - PlanStartDate
    "End Date",                                    # M (12) - PlanDueDate
    "Released Date",                               # N (13) - PlanDueDate
    "LAUNCHING",                                   # O (14) - Quarter
    "Estimated Total Effort (man-day)",            # P (15) - Preserved
    "Actual Effort\n(man-day)",                    # Q (16) - Preserved
    "Tỉ lệ bug QC\n(Tổng bug/TC)",                 # R (17) - Preserved
    "Tỉ lệ bug UAT\n(Tổng bug/TC)",                # S (18) - Preserved
    "VALUE CODE\n(chọn từ Dictionary)",            # T (19) - Value Code
    "VALUE METRIC\n(số liệu + đơn vị)",            # U (20) - Value Metric
    "BUSINESS IMPACT\n(tầng tác động)",            # V (21) - Business Impact
    "Lasted Updated",                              # W (22) - Ngày chạy (DD-Mon-YYYY)
    "Done",                                        # X (23) - Done
    "Doing/Will Do",                               # Y (24) - ContinuationPlan
    "Issues & Actions",                            # Z (25) - RiskOrIssues
    "Release Note\n(Output - Module - Function)",  # AA (26) - ReleaseNote
]
PRESERVED_EXCEL_PORTFOLIO_COLS = {0, 6, 7, 15, 16, 17, 18}
DASH_ESCAPE_PORTFOLIO_COLS = {3, 4, 23, 24, 25, 26}

# Header cho Sheet 2 (FTI - 19 cột A–S)
EXCEL_FTI_HEADER = [
    "Project Group",                               # A (0)
    "Tool/ Application",                           # B (1) - ProjectCode
    "Module/Parent Task/Epic",                     # C (2) - DisplayName (Match Key)
    "Feature/Task/User Story",                     # D (3) - MainFeature
    "Description",                                 # E (4) - Goal / Description
    "PIC",                                         # F (5) - PM / PIC
    "Priority",                                    # G (6) - Priority (Preserved)
    "%Done",                                       # H (7) - Progress
    "Status",                                      # I (8) - ProjectPhase
    "Project Health",                              # J (9) - ProjectHealth
    "Release Date",                                # K (10) - PlanDueDate
    "This Week [Done]",                            # L (11) - Done
    "Next Week Plan [Doing/Will Do]",              # M (12) - ContinuationPlan
    "Issues & Actions",                            # N (13) - RiskOrIssues
    "RELEASE NOTE \n(Output - Module - Function)", # O (14) - Release Note
    "OKR/KEY BENEFIT-VALUE\n(Số liệu cụ thể)",    # P (15) - OKR / Value (Preserved)
    "NOTES",                                       # Q (16) - Notes (Preserved)
    "LAUNCHING",                                   # R (17) - Quarter
    "Report Date",                                 # S (18) - Ngày báo cáo
]
PRESERVED_EXCEL_COLS = {6, 15, 16}

# Các cột D, E, L, M, N, O, P, Q cần thêm dấu ' ở đầu nếu bắt đầu bằng '-' để tránh lỗi công thức Excel
DASH_ESCAPE_EXCEL_COLS = {3, 4, 11, 12, 13, 14, 15, 16}
DASH_ESCAPE_PROJECT2026_COLS = {13, 14, 17, 74, 75, 76, 77}

MONTH_ABBR = [
    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
]


def _today_str() -> str:
    """Ngày hôm nay định dạng DD-Mon-YYYY (VD '08-Oct-2026')."""
    t = datetime.now()
    return f"{t.day:02d}-{MONTH_ABBR[t.month - 1]}-{t.year}"


def _escape_excel_dash(val: Any) -> Any:
    """Nếu giá trị chuỗi có ký tự '-' đầu tiên thì thêm dấu ' ở đầu để tránh lỗi công thức Excel (#NAME? / Formula error)."""
    if val is None:
        return ""
    if isinstance(val, str):
        if not val or val.startswith("'"):
            return val
        if val.startswith("-") or val.lstrip().startswith("-"):
            return f"'{val}"
        return val
    val_str = str(val)
    if val_str.startswith("-") or val_str.lstrip().startswith("-"):
        return f"'{val_str}"
    return val


def is_excel_target(target: Optional[str]) -> bool:
    if not target:
        return False
    t = target.strip().lower()
    return (
        t.startswith("http://")
        or t.startswith("https://")
        or t.startswith("u!")
        or "sharepoint.com" in t
        or "1drv.ms" in t
        or t.endswith(".xlsx")
    )


def build_excel_row_project2026(p: Dict[str, Any], existing_row: Optional[List[Any]] = None, next_stt: int = 1) -> List[Any]:
    """Tạo dòng dữ liệu 78 cột (A–BZ) cho sheet Project2026 (2026_SU02_Resource_Planning.xlsx).
    Bảo toàn 100% 48 cột Resource (Jan..Dec x PM, BA, DEV, QC - Col W..BR) và các số liệu Effort/QC/UAT của PMO.
    """
    row: List[Any] = [""] * 78

    if existing_row:
        for idx in range(min(len(existing_row), 78)):
            row[idx] = existing_row[idx]

    # STT (Col 0 - A)
    if row[0] in (None, ""):
        row[0] = next_stt

    # Project/Version (Col 1 - B): DisplayName (Match Key)
    row[1] = p.get("displayName", "") or row[1]

    # Release/Sprint (Col 2 - C): Giữ nguyên nếu có, nếu chưa có thì gán "Version"
    if row[2] in (None, ""):
        row[2] = "Version"

    # Application (Col 3 - D): projectCode
    if row[3] in (None, "") or p.get("projectCode"):
        row[3] = p.get("projectCode", "") or row[3]

    # Project Type (Col 4 - E): Giữ nguyên nếu có, nếu mới gán "Enhancement"
    if row[4] in (None, ""):
        row[4] = "Enhancement"

    # Business Owner (Col 5 - F): Division
    if row[5] in (None, ""):
        row[5] = p.get("division", "") or "FTI"

    # Product Owner (Col 6 - G): Giữ nguyên nếu có

    # PM (Col 7 - H)
    if p.get("pm"):
        row[7] = p.get("pm")

    # Project Status (Col 8 - I)
    if p.get("projectPhase"):
        row[8] = p.get("projectPhase")

    # Priority (Col 9 - J): Giữ nguyên nếu có, nếu mới gán High
    if row[9] in (None, ""):
        row[9] = p.get("priority", "High")

    # Start date (Col 10 - K)
    if row[10] in (None, "") and p.get("planStartDate"):
        row[10] = p.get("planStartDate")

    # Target Go-live (Col 11 - L)
    if p.get("planDueDate"):
        row[11] = p.get("planDueDate")

    # Actual Go-live (Col 12 - M): Giữ nguyên

    # Business Problem (Col 13 - N): MainFeature
    if p.get("mainFeature"):
        row[13] = p.get("mainFeature")

    # Business Outcome (Col 14 - O): Goal
    if p.get("goal"):
        row[14] = p.get("goal")

    # Key Scope/Sprint Goal (Col 15 - P): Giữ nguyên

    # Value Dimension (Col 16 - Q)
    if row[16] in (None, "") and p.get("valueCodes"):
        row[16] = p.get("valueCodes")

    # Primary Value Metric (Col 17 - R)
    if row[17] in (None, ""):
        row[17] = p.get("valueMetric", "") or p.get("businessImpact", "")

    # Cột 18..21 (S..V): Effort & Defect rates -> Giữ nguyên 100%

    # Cột 22..69 (W..BR): 48 cột Resource (Jan..Dec x PM, BA, DEV, QC) -> Giữ nguyên 100%

    # Cột 70..77 (BS..BZ): Weekly Report Fields
    row[70] = p.get("progress", "")             # BS (70): %Done
    row[71] = p.get("projectPhase", "")         # BT (71): Status
    row[72] = p.get("projectHealth", "")        # BU (72): Project Health
    row[73] = p.get("planDueDate", "")          # BV (73): Release Date
    row[74] = p.get("done", "")                 # BW (74): This Week [Done]
    row[75] = p.get("continuationPlan", "")     # BX (75): Next Week Plan [Doing/Will Do]
    row[76] = p.get("riskOrIssues", "")         # BY (76): Issues & Actions
    row[77] = p.get("releaseNote", "")          # BZ (77): RELEASE NOTE (Output - Module - Function)

    for col_idx in DASH_ESCAPE_PROJECT2026_COLS:
        if col_idx < len(row):
            row[col_idx] = _escape_excel_dash(row[col_idx])

    return row


def build_excel_row_27col(p: Dict[str, Any], existing_row: Optional[List[Any]] = None) -> List[Any]:
    """Tạo dòng dữ liệu 27 cột (A–AA) cho sheet Portfolio 2026."""
    div_val = p.get("divisionCode", "") or "FTI"
    po_val = ""
    priority_val = p.get("priority", "3 - High")
    effort_est = ""
    effort_act = ""
    qc_bug = ""
    uat_bug = ""
    today_str = _today_str()

    if existing_row:
        if len(existing_row) > 0 and existing_row[0] not in (None, ""):
            div_val = existing_row[0]
        if len(existing_row) > 6 and existing_row[6] not in (None, ""):
            po_val = existing_row[6]
        if len(existing_row) > 7 and existing_row[7] not in (None, ""):
            priority_val = existing_row[7]
        if len(existing_row) > 15 and existing_row[15] not in (None, ""):
            effort_est = existing_row[15]
        if len(existing_row) > 16 and existing_row[16] not in (None, ""):
            effort_act = existing_row[16]
        if len(existing_row) > 17 and existing_row[17] not in (None, ""):
            qc_bug = existing_row[17]
        if len(existing_row) > 18 and existing_row[18] not in (None, ""):
            uat_bug = existing_row[18]

    row = [
        div_val,                                           # A (0): Unit / Division
        p.get("projectCode", ""),                          # B (1): Product / ProjectCode
        p.get("displayName", ""),                          # C (2): Project / DisplayName (Match Key)
        p.get("mainFeature", ""),                          # D (3): Business Problem / User Story
        p.get("goal", ""),                                 # E (4): Solution / Project Goal
        p.get("pm", ""),                                   # F (5): PM
        po_val,                                            # G (6): PO (Preserved)
        priority_val,                                      # H (7): Priority (Preserved)
        p.get("progress", ""),                             # I (8): %Done
        p.get("projectPhase", ""),                         # J (9): Status
        p.get("projectHealth", ""),                        # K (10): Project Health
        p.get("planStartDate", ""),                        # L (11): Start date
        p.get("planDueDate", ""),                          # M (12): End Date
        p.get("planDueDate", ""),                          # N (13): Released Date
        p.get("quarter", ""),                              # O (14): LAUNCHING
        effort_est,                                        # P (15): Estimated Total Effort (Preserved)
        effort_act,                                        # Q (16): Actual Effort (Preserved)
        qc_bug,                                            # R (17): Tỉ lệ bug QC (Preserved)
        uat_bug,                                           # S (18): Tỉ lệ bug UAT (Preserved)
        p.get("valueCodes", ""),                           # T (19): VALUE CODE
        p.get("valueMetric", ""),                          # U (20): VALUE METRIC
        p.get("businessImpact", ""),                       # V (21): BUSINESS IMPACT
        today_str,                                         # W (22): Lasted Updated
        p.get("done", ""),                                 # X (23): Done
        p.get("continuationPlan", ""),                     # Y (24): Doing/Will Do
        p.get("riskOrIssues", ""),                         # Z (25): Issues & Actions
        p.get("releaseNote", ""),                          # AA (26): Release Note
    ]

    for col_idx in DASH_ESCAPE_PORTFOLIO_COLS:
        if col_idx < len(row):
            row[col_idx] = _escape_excel_dash(row[col_idx])

    return row


def build_excel_row(p: Dict[str, Any], existing_row: Optional[List[Any]] = None) -> List[Any]:
    """Tạo dòng dữ liệu 19 cột (A–S) khớp chính xác với cấu trúc sheet FTI."""
    priority_val = p.get("priority", "3 - High")
    okr_val = p.get("valueCodes", "") or p.get("valueMetric", "") or p.get("businessImpact", "")
    notes_val = p.get("notes", "")
    today_str = _today_str()

    if existing_row:
        if len(existing_row) > 6 and existing_row[6] not in (None, ""):
            priority_val = existing_row[6]
        if len(existing_row) > 15 and existing_row[15] not in (None, ""):
            okr_val = existing_row[15]
        if len(existing_row) > 16 and existing_row[16] not in (None, ""):
            notes_val = existing_row[16]

    row = [
        "FTI",                                             # A (0): Project Group
        p.get("projectCode", ""),                          # B (1): Tool/ Application
        p.get("displayName", ""),                          # C (2): Module/Parent Task/Epic (Match key)
        p.get("mainFeature", ""),                          # D (3): Feature/Task/User Story
        p.get("goal", ""),                                 # E (4): Description
        p.get("pm", ""),                                   # F (5): PIC
        priority_val,                                      # G (6): Priority (Preserved)
        p.get("progress", ""),                             # H (7): %Done
        p.get("projectPhase", ""),                         # I (8): Status
        p.get("projectHealth", ""),                        # J (9): Project Health
        p.get("planDueDate", ""),                          # K (10): Release Date
        p.get("done", ""),                                 # L (11): This Week [Done]
        p.get("continuationPlan", ""),                     # M (12): Next Week Plan [Doing/Will Do]
        p.get("riskOrIssues", ""),                         # N (13): Issues & Actions
        p.get("releaseNote", ""),                          # O (14): RELEASE NOTE (Output - Module - Function)
        okr_val,                                           # P (15): OKR/KEY BENEFIT-VALUE (Preserved)
        notes_val,                                         # Q (16): NOTES (Preserved)
        p.get("quarter", ""),                              # R (17): LAUNCHING
        today_str,                                         # S (18): Report Date (Ngày báo cáo)
    ]

    # Các cột D, E, L, M, N, O, P, Q (index 3, 4, 11, 12, 13, 14, 15, 16):
    # Nếu có ký tự '-' đầu tiên thì phải thêm dấu "'" ở đầu để Excel không bị lỗi công thức.
    for col_idx in DASH_ESCAPE_EXCEL_COLS:
        if col_idx < len(row):
            row[col_idx] = _escape_excel_dash(row[col_idx])

    return row


# ═════════════════════════════════════════════════════════════
# 3. THAO TÁC FILE EXCEL SHAREPOINT MỚI (GRAPH WORKBOOK API + ZIP PRESERVING)
# ═════════════════════════════════════════════════════════════

def _col_idx_to_letter(idx: int) -> str:
    res = ""
    idx += 1
    while idx > 0:
        idx, rem = divmod(idx - 1, 26)
        res = chr(65 + rem) + res
    return res


def _update_excel_zip_preserving(orig_bytes: bytes, sheet_name: str, row_updates: Dict[int, List[Any]]) -> bytes:
    """Cập nhật trực tiếp XML của sheet mục tiêu bên trong file ZIP .xlsx,
    bảo toàn 100% tất cả các file khác (calcChain.xml, metadata.xml, pivotTables, pivotCaches, và các sheet khác).
    Tự động sao chép toàn bộ format (style ID) và mở rộng Data Validation (Select Box / Dropdown) từ dòng trên khi chèn dòng mới.
    """
    import zipfile
    import re
    import xml.etree.ElementTree as ET

    zin = zipfile.ZipFile(io.BytesIO(orig_bytes), "r")

    wb_tree = ET.fromstring(zin.read("xl/workbook.xml"))
    rels_tree = ET.fromstring(zin.read("xl/_rels/workbook.xml.rels"))
    rel_map = {rel.attrib["Id"]: rel.attrib["Target"] for rel in rels_tree.findall(".//{http://schemas.openxmlformats.org/package/2006/relationships}Relationship")}

    target_sheet_file = None
    for s in wb_tree.findall(".//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}sheet"):
        if s.attrib.get("name") == sheet_name:
            rId = s.attrib.get("{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id")
            target_path = rel_map.get(rId, "")
            if not target_path.startswith("xl/"):
                target_path = "xl/" + target_path
            target_sheet_file = target_path
            break

    if not target_sheet_file or target_sheet_file not in zin.namelist():
        raise KeyError(f"Không tìm thấy file XML cho sheet '{sheet_name}'.")

    ns = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
    ET.register_namespace("", ns)
    tree = ET.fromstring(zin.read(target_sheet_file))
    sheetData = tree.find(f"{{{ns}}}sheetData")
    if sheetData is None:
        sheetData = ET.SubElement(tree, f"{{{ns}}}sheetData")

    row_elem_map = {}
    for r_elem in sheetData.findall(f"{{{ns}}}row"):
        r_num = int(r_elem.attrib.get("r", 0))
        if r_num > 0:
            row_elem_map[r_num] = r_elem

    for r_num, row_vals in row_updates.items():
        # Tìm style của dòng ngay phía trên để sao chép format và select box
        prev_style_map = {}
        for candidate_prev in range(r_num - 1, 0, -1):
            if candidate_prev in row_elem_map:
                prev_row_el = row_elem_map[candidate_prev]
                for c_el in prev_row_el.findall(f"{{{ns}}}c"):
                    r_attr = c_el.attrib.get("r", "")
                    s_attr = c_el.attrib.get("s")
                    col_let = re.sub(r"\d+", "", r_attr)
                    if col_let and s_attr:
                        prev_style_map[col_let] = s_attr
                if prev_style_map:
                    break

        if r_num in row_elem_map:
            r_elem = row_elem_map[r_num]
            # Lưu lại style hiện có của chính dòng này nếu có
            for c_el in r_elem.findall(f"{{{ns}}}c"):
                r_attr = c_el.attrib.get("r", "")
                s_attr = c_el.attrib.get("s")
                col_let = re.sub(r"\d+", "", r_attr)
                if col_let and s_attr:
                    prev_style_map[col_let] = s_attr
            for old_c in list(r_elem.findall(f"{{{ns}}}c")):
                r_elem.remove(old_c)
        else:
            r_elem = ET.SubElement(sheetData, f"{{{ns}}}row", {"r": str(r_num)})
            row_elem_map[r_num] = r_elem

        for col_idx, val in enumerate(row_vals):
            col_letter = _col_idx_to_letter(col_idx)
            cell_ref = f"{col_letter}{r_num}"
            s_style = prev_style_map.get(col_letter)

            # Tạo cell element và sao chép style index từ dòng trên
            c_elem = ET.SubElement(r_elem, f"{{{ns}}}c", {"r": cell_ref})
            if s_style:
                c_elem.attrib["s"] = s_style

            if val is None or val == "":
                continue

            if isinstance(val, (int, float)):
                c_elem.attrib["t"] = "n"
                v_elem = ET.SubElement(c_elem, f"{{{ns}}}v")
                v_elem.text = str(val)
            else:
                val_str = str(val)
                c_elem.attrib["t"] = "inlineStr"
                is_elem = ET.SubElement(c_elem, f"{{{ns}}}is")
                t_elem = ET.SubElement(is_elem, f"{{{ns}}}t")
                t_elem.text = val_str

        # Tự động mở rộng dataValidations (Select Box / Dropdown) để bao gồm dòng mới r_num
        dvals = tree.findall(f".//{{{ns}}}dataValidation")
        for dv in dvals:
            sqref = dv.attrib.get("sqref", "")
            tokens = sqref.split()
            new_tokens = []
            for tok in tokens:
                m = re.match(r"^([A-Z]+)(\d+):([A-Z]+)(\d+)$", tok)
                if m:
                    c1, r1, c2, r2 = m.groups()
                    r1_n, r2_n = int(r1), int(r2)
                    if r1_n <= r_num and r_num > r2_n:
                        new_tokens.append(f"{c1}{r1}:{c2}{r_num}")
                    else:
                        new_tokens.append(tok)
                else:
                    new_tokens.append(tok)
            dv.attrib["sqref"] = " ".join(new_tokens)

    sorted_rows = sorted(sheetData.findall(f"{{{ns}}}row"), key=lambda el: int(el.attrib.get("r", 0)))
    sheetData[:] = sorted_rows

    modified_xml = ET.tostring(tree, encoding="utf-8", xml_declaration=True)

    zout_buf = io.BytesIO()
    zout = zipfile.ZipFile(zout_buf, "w", zipfile.ZIP_DEFLATED)
    for item in zin.infolist():
        if item.filename == target_sheet_file:
            zout.writestr(item, modified_xml)
        else:
            zout.writestr(item, zin.read(item.filename))

    zout.close()
    zin.close()
    raw_out = zout_buf.getvalue()
    try:
        _shared_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "_shared"))
        if _shared_dir not in sys.path:
            sys.path.insert(0, _shared_dir)
        from xlsx_normalizer import normalize_xlsx_bytes
        return normalize_xlsx_bytes(raw_out)
    except Exception:
        return raw_out


def _normalize_name_key(s: Any) -> str:
    if not s:
        return ""
    import re
    s_str = str(s).lower().strip()
    return re.sub(r"[\s\-_]+", " ", s_str)


def _find_matching_row(
    p_name: str,
    rows: List[List[Any]],
    match_col_idx: int,
    header_row_count: int,
    schema_type: str = "project2026",
) -> int:
    """So khớp dòng thông minh:
    1. So khớp chính xác hoặc chuẩn hóa (bỏ khoảng trắng thừa/dấu gạch).
    2. Riêng cho Project2026 (78 cột):
       - Hỗ trợ ghép Cột B (Project/Version) + Cột C (Release/Sprint) (ví dụ: 'FTI SM v2.1' + 'Sprint 3' -> 'FTI SM v2.1 Sprint 3').
       - Hỗ trợ fuzzy match bỏ tiền tố 'v' (ví dụ: 'FTI SM 2.3' khớp 'FTI SM v2.3').
    """
    import re
    p_norm = _normalize_name_key(p_name)
    if not p_norm:
        return -1

    # 1. Exact / Normalized match trên match_col_idx
    for i in range(header_row_count, len(rows)):
        r = rows[i]
        if len(r) > match_col_idx and r[match_col_idx] is not None:
            if _normalize_name_key(r[match_col_idx]) == p_norm:
                return i

    # 2. Match kết hợp cho Project2026 (Col B + Col C)
    if schema_type == "project2026":
        for i in range(header_row_count, len(rows)):
            r = rows[i]
            if len(r) > 2 and r[1] and r[2]:
                combined = _normalize_name_key(f"{r[1]} {r[2]}")
                if combined == p_norm or combined.replace(" v", " ") == p_norm.replace(" v", " "):
                    return i

        # 3. Fuzzy match bỏ tiền tố 'v' (VD 'FTI SM 2.3' vs 'FTI SM v2.3')
        p_nov = re.sub(r"\bv(\d)", r"\1", p_norm)
        for i in range(header_row_count, len(rows)):
            r = rows[i]
            if len(r) > 1 and r[1]:
                r_nov = re.sub(r"\bv(\d)", r"\1", _normalize_name_key(r[1]))
                if r_nov == p_nov:
                    return i

    return -1


def _is_fti_project(p: Dict[str, Any]) -> bool:
    div = str(p.get("division", "")).upper()
    code = str(p.get("projectCode", "")).upper()
    name = str(p.get("displayName", "")).upper()
    return "FTI" in div or code.startswith("FTI") or name.startswith("FTI")


def _find_insert_slot(
    p: Dict[str, Any],
    rows: List[List[Any]],
    schema_type: str,
    header_row_count: int,
) -> Tuple[int, int]:
    """Tìm chỉ số dòng trống thích hợp theo phân vùng để chèn dự án mới:
    - Đối với Project2026:
      + Nếu là dự án FTI -> chèn vào dòng trống trong khối FTI (trước marker #FTI, bắt đầu từ Dòng 61).
      + Nếu là dự án FTEL/khác -> chèn vào dòng trống trong khối FTEL (trước marker #FTEL, bắt đầu từ Dòng 106).
    - Các schema khác -> chèn tiếp nối vào cuối bảng tính (len(rows)).
    Trả về: (row_idx_0_indexed, next_stt)
    """
    if schema_type == "project2026":
        is_fti = _is_fti_project(p)
        marker_keyword = "#FTI" if is_fti else "#FTEL"

        marker_idx = -1
        for idx, r in enumerate(rows):
            if len(r) > 0 and marker_keyword in str(r[0]):
                marker_idx = idx
                break

        if marker_idx > 0:
            start_idx = 2 if is_fti else 65
            for i in range(start_idx, marker_idx):
                r = rows[i]
                name_val = str(r[1]).strip() if len(r) > 1 and r[1] is not None else ""
                if not name_val:
                    prev_stt = 0
                    for prev_i in range(i - 1, start_idx - 1, -1):
                        if len(rows[prev_i]) > 0 and isinstance(rows[prev_i][0], (int, float)):
                            prev_stt = int(rows[prev_i][0])
                            break
                    return i, prev_stt + 1

    # Fallback chèn ở cuối
    target_idx = len(rows)
    next_stt = len(rows) - header_row_count + 1
    return target_idx, next_stt


def _update_excel_via_content_api(
    drive_id: str,
    item_id: str,
    sheet_name: str,
    projects: List[Dict[str, Any]],
    row_builder: Any,
    default_headers: List[List[str]],
    token: str,
    match_col_idx: int = 2,
    header_row_count: int = 1,
    schema_type: str = "project2026",
    max_retries: int = 3,
) -> Dict[str, Any]:
    """Cập nhật an toàn với kiểm soát eTag (If-Match) bảo toàn 100% cấu trúc ZIP khi file chứa Pivot Table (501)."""
    if openpyxl is None:
        raise ImportError("Cần cài đặt openpyxl: pip install openpyxl")

    for attempt in range(1, max_retries + 1):
        print(f"[HRM-Excel] Đang cập nhật an toàn qua XML ZIP '{sheet_name}' (Lần thử {attempt}/{max_retries})...", file=sys.stderr)
        file_bytes, etag = mg.download_file_content(drive_id, item_id, token=token)
        wb = openpyxl.load_workbook(io.BytesIO(file_bytes), read_only=True, data_only=True)

        if sheet_name not in wb.sheetnames:
            raise KeyError(f"Không tìm thấy sheet '{sheet_name}' trong file Excel.")
        ws = wb[sheet_name]
        raw_rows = [list(r) for r in ws.iter_rows(values_only=True)]
        wb.close()

        if not raw_rows:
            raw_rows = [list(h) for h in default_headers]

        updated_list: List[Dict[str, str]] = []
        inserted_list: List[Dict[str, str]] = []
        row_updates: Dict[int, List[Any]] = {}

        for p in projects:
            p_name = str(p.get("displayName", "")).strip()

            idx = _find_matching_row(p_name, raw_rows, match_col_idx, header_row_count, schema_type=schema_type)

            if idx >= 0:
                target_row_num = idx + 1
                existing_row = list(raw_rows[idx])
                row_data = row_builder(p, existing_row=existing_row)
                raw_rows[idx] = row_data
                row_updates[target_row_num] = row_data
                updated_list.append({"code": p["projectCode"], "name": p["displayName"]})
            else:
                target_idx, next_stt = _find_insert_slot(p, raw_rows, schema_type, header_row_count)
                target_row_num = target_idx + 1
                row_data = row_builder(p, next_stt=next_stt) if "next_stt" in getattr(row_builder, "__code__", object()).co_varnames else row_builder(p)
                if target_idx < len(raw_rows):
                    raw_rows[target_idx] = row_data
                else:
                    raw_rows.append(row_data)
                row_updates[target_row_num] = row_data
                inserted_list.append({"code": p["projectCode"], "name": p["displayName"]})

        new_file_bytes = _update_excel_zip_preserving(file_bytes, sheet_name, row_updates)

        try:
            mg.upload_file_content(drive_id, item_id, new_file_bytes, if_match_etag=etag, token=token)
            print(f"[HRM-Excel] Đã cập nhật thành công sheet '{sheet_name}' (ZIP Preserved): {len(updated_list)} updated, {len(inserted_list)} inserted.")
            return {"updatedList": updated_list, "insertedList": inserted_list}
        except RuntimeError as re_err:
            if "CONCURRENCY_CONFLICT" in str(re_err) and attempt < max_retries:
                time.sleep(2)
                continue
            raise re_err

    raise RuntimeError("Không thể cập nhật file do có quá nhiều xung đột chỉnh sửa.")


def update_excel_sheets(projects: List[Dict[str, Any]], config: Dict[str, Any], token: Optional[str] = None) -> Dict[str, Any]:
    """Cập nhật dữ liệu vào bảng tính Excel Online trên SharePoint / OneDrive qua Microsoft Graph API.
    Sử dụng Cell-level PATCH Range hoặc XML ZIP Preserving, bảo vệ 100% các sheet khác, Pivot Table và co-authoring metadata.
    Hỗ trợ 3 schema:
      - Project2026 (78 cột A–BZ, 2 dòng header, Match Key ở Cột B: Project/Version)
      - Portfolio 2026 (27 cột A–AA, 1 dòng header, Match Key ở Cột C: Project)
      - FTI (19 cột A–S, 1 dòng header, Match Key ở Cột C: Module/Parent Task/Epic)
    """
    if mg is None:
        raise ImportError("Thiếu module ms_graph_client. Vui lòng kiểm tra skills/_shared/ms_graph_client.py")

    excel_target = config.get("excelUrl") or config.get("sheetId")
    sheet_name = config.get("sheetName") or "Project2026"

    tok = token or mg.get_ms_graph_token(scopes=["User.Read", "Files.ReadWrite"])
    drive_id, item_id, _ = mg.resolve_drive_item(excel_target, token=tok)

    used_range = mg.get_worksheet_used_range(drive_id, item_id, sheet_name, token=tok)
    rows: List[List[Any]] = used_range.get("values") or []

    # Nhận diện schema dựa trên cấu hình, tên sheet hoặc số cột hiện có
    schema_cfg = str(config.get("schema", "")).strip().lower()
    sheet_lower = sheet_name.lower()

    if schema_cfg in ("78", "project2026", "78 cột a–bz") or "project2026" in sheet_lower or (rows and len(rows[0]) >= 60):
        schema_type = "project2026"
        col_end = "BZ"
        match_col_idx = 1  # Cột B: Project/Version
        header_row_count = 2
        row_builder = build_excel_row_project2026
        default_headers = [EXCEL_PROJECT2026_HEADER_R1, EXCEL_PROJECT2026_HEADER]
    elif schema_cfg in ("27", "portfolio", "portfolio 2026", "27 cột a–aa") or "portfolio" in sheet_lower or (rows and len(rows[0]) >= 25 and "fti" not in sheet_lower):
        schema_type = "portfolio2026"
        col_end = "AA"
        match_col_idx = 2  # Cột C: Project
        header_row_count = 1
        row_builder = build_excel_row_27col
        default_headers = [EXCEL_PORTFOLIO_HEADER]
    else:
        schema_type = "fti"
        col_end = "S"
        match_col_idx = 2  # Cột C: Module/Parent Task/Epic
        header_row_count = 1
        row_builder = build_excel_row
        default_headers = [EXCEL_FTI_HEADER]

    try:
        mg.ensure_worksheet(drive_id, item_id, sheet_name, token=tok)

        if not rows:
            rows = [list(h) for h in default_headers]
            for h_idx, h_row in enumerate(default_headers):
                mg.update_worksheet_range(drive_id, item_id, sheet_name, f"A{h_idx+1}:{col_end}{h_idx+1}", [h_row], token=tok)

        updated_list: List[Dict[str, str]] = []
        inserted_list: List[Dict[str, str]] = []
        next_insert_row = len(rows) + 1

        for p in projects:
            p_name = str(p.get("displayName", "")).strip()

            idx = _find_matching_row(p_name, rows, match_col_idx, header_row_count, schema_type=schema_type)

            if idx >= 0:
                target_row_num = idx + 1
                existing_row = list(rows[idx])
                row_data = row_builder(p, existing_row=existing_row)
                range_addr = f"A{target_row_num}:{col_end}{target_row_num}"
                mg.update_worksheet_range(drive_id, item_id, sheet_name, range_addr, [row_data], token=tok)
                rows[idx] = row_data
                updated_list.append({"code": p["projectCode"], "name": p["displayName"]})
            else:
                target_idx, next_stt = _find_insert_slot(p, rows, schema_type, header_row_count)
                target_row_num = target_idx + 1
                row_data = row_builder(p, next_stt=next_stt) if "next_stt" in getattr(row_builder, "__code__", object()).co_varnames else row_builder(p)
                range_addr = f"A{target_row_num}:{col_end}{target_row_num}"
                mg.update_worksheet_range(drive_id, item_id, sheet_name, range_addr, [row_data], token=tok)
                if target_idx < len(rows):
                    rows[target_idx] = row_data
                else:
                    rows.append(row_data)
                inserted_list.append({"code": p["projectCode"], "name": p["displayName"]})

        print(f"[HRM-Excel] Cập nhật thành công (Cell-level PATCH {col_end}, Schema: {schema_type}): {len(updated_list)} updated, {len(inserted_list)} inserted vào '{sheet_name}'.")
        return {"updatedList": updated_list, "insertedList": inserted_list}

    except Exception as e:
        err_str = str(e)
        if "501" in err_str or "unsupportedWorkbook" in err_str or "FileCorruptTryRepair" in err_str:
            print(f"[HRM-Excel] File chứa cấu trúc phức tạp (501), chuyển sang cơ chế ZIP XML Preserving cho '{sheet_name}'...", file=sys.stderr)
            return _update_excel_via_content_api(
                drive_id, item_id, sheet_name, projects, row_builder, default_headers,
                token=tok, match_col_idx=match_col_idx, header_row_count=header_row_count, schema_type=schema_type
            )
        raise e


def update_excel_sheets_v2(projects: List[Dict[str, Any]], config: Dict[str, Any], token: Optional[str] = None) -> Dict[str, Any]:
    """Cập nhật Sheet 2 (schema 19 cột A–S cho FTI) trên Excel Online."""
    cfg = dict(config)
    if config.get("excelUrl2"):
        cfg["excelUrl"] = config["excelUrl2"]
    if config.get("sheetName2"):
        cfg["sheetName"] = config["sheetName2"]
    cfg["schema"] = "19"
    return update_excel_sheets(projects, cfg, token=token)


# ═════════════════════════════════════════════════════════════
# 4. THAO TÁC GOOGLE SHEETS LEGACY
# ═════════════════════════════════════════════════════════════

class UserOAuthCredentials:
    def __init__(self, token: str):
        self.token = token
        self.valid = True

    def refresh(self, request=None):
        pass


def get_credentials(service_account_json_path=None):
    user_token = (
        os.environ.get("GOOGLE_SHEETS_ACCESS_TOKEN")
        or os.environ.get("GOOGLE_ACCESS_TOKEN")
        or os.environ.get("GMAIL_ACCESS_TOKEN")
    )
    if user_token and user_token.strip():
        print("[HRM] 🔑 Sử dụng User OAuth Access Token từ tài khoản Google của bạn.")
        return UserOAuthCredentials(user_token.strip())

    sa_path = service_account_json_path or os.environ.get("GOOGLE_SERVICE_ACCOUNT_PATH")
    if sa_path and os.path.exists(sa_path):
        print(f"[HRM] 🔑 Sử dụng Service Account: {sa_path}")
        creds = service_account.Credentials.from_service_account_file(sa_path, scopes=SCOPES)
        creds.refresh(GoogleAuthRequest())
        return creds

    raise ValueError(
        "Chưa có xác thực Google để truy cập Google Sheets!\n"
        "👉 Cách 1: Cung cấp URL file Excel trên SharePoint/OneDrive (HRM_EXCEL_URL / MS Graph API).\n"
        "👉 Cách 2: Kết nối tài khoản Google trong Cài đặt Webapp hoặc đặt GOOGLE_SERVICE_ACCOUNT_PATH."
    )


def get_service_account_email(sa_path: str) -> str:
    if not sa_path or not os.path.exists(sa_path):
        return ""
    try:
        import json as _json
        with open(sa_path, encoding="utf-8") as f:
            data = _json.load(f)
        return data.get("client_email", "")
    except Exception:
        return ""


def _headers(creds):
    if hasattr(creds, "valid") and not creds.valid:
        creds.refresh(GoogleAuthRequest())
    return {"Authorization": f"Bearer {creds.token}", "Content-Type": "application/json"}


def quote_sheet_name(sheet_name):
    return "'" + sheet_name.replace("'", "''") + "'"


def ensure_sheet(creds, spreadsheet_id, sheet_name):
    res = requests.get(f"{API_BASE}/{spreadsheet_id}", headers=_headers(creds))
    res.raise_for_status()
    meta = res.json()

    sheet = next((s for s in meta.get("sheets", []) if s["properties"]["title"] == sheet_name), None)
    if not sheet:
        res = requests.post(
            f"{API_BASE}/{spreadsheet_id}:batchUpdate",
            headers=_headers(creds),
            json={"requests": [{"addSheet": {"properties": {"title": sheet_name}}}]},
        )
        res.raise_for_status()
        sheet = res.json()["replies"][0]["addSheet"]
    return sheet["properties"]


def ensure_row_count(creds, spreadsheet_id, grid_sheet_id, required_rows, current_row_count):
    if required_rows <= current_row_count:
        return
    res = requests.post(
        f"{API_BASE}/{spreadsheet_id}:batchUpdate",
        headers=_headers(creds),
        json={"requests": [{
            "appendDimension": {
                "sheetId": grid_sheet_id,
                "dimension": "ROWS",
                "length": required_rows - current_row_count,
            },
        }]},
    )
    res.raise_for_status()


def get_sheet_data(creds, spreadsheet_id, sheet_name):
    range_ = f"{quote_sheet_name(sheet_name)}!A:AA"
    res = requests.get(f"{API_BASE}/{spreadsheet_id}/values/{range_}", headers=_headers(creds))
    res.raise_for_status()
    return res.json().get("values", [])


def update_rows(creds, spreadsheet_id, sheet_name, updates):
    data = [{
        "range": f"{quote_sheet_name(sheet_name)}!A{u['rowIndex']}:AA{u['rowIndex']}",
        "values": [u["values"]],
    } for u in updates]
    res = requests.post(
        f"{API_BASE}/{spreadsheet_id}/values:batchUpdate",
        headers=_headers(creds),
        json={"valueInputOption": "USER_ENTERED", "data": data},
    )
    res.raise_for_status()


def update_google_sheets(projects, config, creds):
    spreadsheet_id = config["sheetId"]
    sheet_name = config.get("sheetName") or "Portfolio 2026"

    sheet_props = ensure_sheet(creds, spreadsheet_id, sheet_name)
    rows = get_sheet_data(creds, spreadsheet_id, sheet_name)

    print(f"[HRM] Sheet rows: {len(rows)} ({max(len(rows) - 1, 0)} data rows + header)")

    if not rows:
        rows = [HEADER_ROW]

    updated_list, inserted_list = [], []
    write_payload = []
    next_insert_row = len(rows) + 1
    today_str = _today_str()

    for p in projects:
        row = [
            "FTI", p["projectCode"], p["displayName"], p["mainFeature"], p["goal"], p["pm"],
            "", "",
            p["progress"], p["projectPhase"], p["projectHealth"],
            p["planStartDate"], p["planDueDate"], p["planDueDate"],
            p["quarter"],
            "", "", "", "",
            p["valueCodes"], p["valueMetric"], p["businessImpact"],
            today_str,
            p["done"], p["continuationPlan"], p["riskOrIssues"],
            p["releaseNote"],
        ]

        idx = next((i for i, r in enumerate(rows) if i > 0 and len(r) > 2 and r[2] == p["displayName"]), -1)
        if idx >= 0:
            for c in PRESERVED_COLS:
                if c < len(rows[idx]):
                    row[c] = rows[idx][c]
            write_payload.append({"rowIndex": idx + 1, "values": row})
            updated_list.append({"code": p["projectCode"], "name": p["displayName"]})
        else:
            write_payload.append({"rowIndex": next_insert_row, "values": row})
            next_insert_row += 1
            inserted_list.append({"code": p["projectCode"], "name": p["displayName"]})

    print(f"[HRM] Sheet matching: {len(updated_list)} updated, {len(inserted_list)} inserted")

    last_row_needed = next_insert_row - 1
    ensure_row_count(creds, spreadsheet_id, sheet_props["sheetId"], last_row_needed,
                      (sheet_props.get("gridProperties") or {}).get("rowCount", 0))

    if write_payload:
        update_rows(creds, spreadsheet_id, sheet_name, write_payload)

    return {"updatedList": updated_list, "insertedList": inserted_list}


def update_google_sheets_v2(projects, config, creds):
    """Ghi vào Google Sheet thứ hai (file 13ENSxJkc9lL43lmofw9HIxF9sdR_cElNtW2D581KIkw) theo schema 19 cột A–S."""
    spreadsheet_id = config["sheetId2"]
    sheet_name = config.get("sheetName2") or "FTI"

    sheet_props = ensure_sheet(creds, spreadsheet_id, sheet_name)
    range_ = f"{quote_sheet_name(sheet_name)}!A:S"
    res = requests.get(f"{API_BASE}/{spreadsheet_id}/values/{range_}", headers=_headers(creds))
    res.raise_for_status()
    rows = res.json().get("values", [])

    print(f"[HRM-v2] Sheet rows: {len(rows)} ({max(len(rows) - 1, 0)} data rows + header)")

    if not rows:
        rows = [HEADER_ROW_V2]

    updated_list, inserted_list = [], []
    write_payload = []
    next_insert_row = len(rows) + 1
    today_str = _today_str()

    for p in projects:
        row = [
            "FTI",
            p["projectCode"],
            p["displayName"],
            p["mainFeature"],
            p["goal"],
            p["pm"],
            "",
            p["progress"],
            p["projectPhase"],
            p["projectHealth"],
            p["planDueDate"],
            p["done"],
            p["continuationPlan"],
            p["riskOrIssues"],
            p["releaseNote"],
            "",
            "",
            p["quarter"],
            today_str,  # Cột S: Ngày báo cáo
        ]

        idx = next((i for i, r in enumerate(rows) if i > 0 and len(r) > 2 and r[2] == p["displayName"]), -1)
        if idx >= 0:
            for c in PRESERVED_COLS_V2:
                if c < len(rows[idx]):
                    row[c] = rows[idx][c]
            write_payload.append({"rowIndex": idx + 1, "values": row, "range_end": "S"})
            updated_list.append({"code": p["projectCode"], "name": p["displayName"]})
        else:
            write_payload.append({"rowIndex": next_insert_row, "values": row, "range_end": "S"})
            next_insert_row += 1
            inserted_list.append({"code": p["projectCode"], "name": p["displayName"]})

    print(f"[HRM-v2] Sheet matching: {len(updated_list)} updated, {len(inserted_list)} inserted")

    last_row_needed = next_insert_row - 1
    ensure_row_count(creds, spreadsheet_id, sheet_props["sheetId"], last_row_needed,
                     (sheet_props.get("gridProperties") or {}).get("rowCount", 0))

    if write_payload:
        data = [{
            "range": f"{quote_sheet_name(sheet_name)}!A{u['rowIndex']}:S{u['rowIndex']}",
            "values": [u["values"]],
        } for u in write_payload]
        res = requests.post(
            f"{API_BASE}/{spreadsheet_id}/values:batchUpdate",
            headers=_headers(creds),
            json={"valueInputOption": "USER_ENTERED", "data": data},
        )
        res.raise_for_status()

    return {"updatedList": updated_list, "insertedList": inserted_list}

"""CLI orchestrator: HRM login (env) -> scrape API -> ghi Excel (MS Graph API) / Google Sheets -> ghi summary JSON.

Tất cả config đọc từ biến môi trường do webapp inject hoặc qua CLI arguments:
  - HRM_USERNAME / HRM_PASSWORD        : credential login HRM (hoặc HRM_ACCESS_TOKEN có sẵn)
  - HRM_EXCEL_URL / HRM_EXCEL_SHARE_URL : Link file Excel trên SharePoint/OneDrive (Graph API)
  - HRM_SHEET_ID / HRM_SHEET_NAME       : Sheet đích (schema 27 cột A–AA; có thể là Google Sheet ID hoặc SharePoint URL)
  - HRM_SHEET2_ID / HRM_SHEET2_NAME     : (tuỳ chọn) Sheet thứ 2 - schema 18 cột A–R
  - HRM_DIVISION_CODE                   : filter division (VD "FTI"), để trống = tất cả
  - GOOGLE_SERVICE_ACCOUNT_PATH         : path tới JSON key service account (nếu dùng Google Sheets)

Usage:
    python3 scripts/run_hrm_report.py --output-dir "$REPORT_OUTPUT_DIR"
    python3 scripts/run_hrm_report.py --excel-url "https://...sharepoint.com/..." --output-dir "$REPORT_OUTPUT_DIR"
    python3 scripts/run_hrm_report.py --week-start 2026-07-20 --week-end 2026-07-26 --output-dir "$REPORT_OUTPUT_DIR"
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path

def _load_env_fallback():
    for parent in [Path(__file__).resolve().parents[2], Path(__file__).resolve().parents[3]]:
        env_file = parent / ".env"
        if env_file.exists():
            try:
                with open(env_file, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            k, v = line.split("=", 1)
                            k = k.strip()
                            v = v.strip()
                            if (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
                                v = v[1:-1]
                            elif " #" in v or "\t#" in v:
                                v = re.split(r"\s+#", v, 1)[0].strip()
                            v = v.strip().strip("'\"")
                            os.environ[k] = v
            except Exception:
                pass
            break

_load_env_fallback()

import hrm_auth
import hrm_client
import sheets_client
import vpn_manager


def default_week_range():
    """Tuần hiện tại: Thứ Hai → Chủ Nhật (ISO week)."""
    today = datetime.now().date()
    monday = today - timedelta(days=today.weekday())  # weekday(): Mon=0..Sun=6
    sunday = monday + timedelta(days=6)
    return monday.isoformat(), sunday.isoformat()


SHARED_DIR = Path(__file__).resolve().parents[2] / "_shared"
if str(SHARED_DIR) not in sys.path:
    sys.path.insert(0, str(SHARED_DIR))
from output_path import next_version_number, now_hhmmss, resolve_input_path


def next_version_path(output_dir, base_name, ext):
    """Tìm version tiếp theo: hrm_weekly_report_v1_HHMMSS.json, _v2_HHMMSS.json, ... (không ghi đè)."""
    next_v = next_version_number(output_dir, base_name, extensions=f".{ext.lstrip('.')}")
    hhmmss = now_hhmmss()
    return os.path.join(output_dir, f"{base_name}_v{next_v}_{hhmmss}.{ext.lstrip('.')}"), next_v



def is_project_in_division(project: dict, target_div: str) -> bool:
    """Kiểm tra dự án có thuộc division mục tiêu hay không (in-memory filter)."""
    if not target_div or not target_div.strip():
        return True
    target = target_div.strip().upper()
    div = (project.get("division") or "").strip().upper()
    if div:
        return target == div or target in div
    code = (project.get("projectCode") or "").strip().upper()
    name = (project.get("displayName") or "").strip().upper()
    return code.startswith(target) or name.startswith(target) or f" {target} " in f" {name} " or f" {target}-" in f" {name}-"


def main():
    parser = argparse.ArgumentParser(description="Chạy weekly report HRM -> Excel (Graph API) / Google Sheets")
    parser.add_argument("--week-start", help="Ngày bắt đầu tuần (YYYY-MM-DD). Mặc định: Thứ 2 tuần hiện tại.")
    parser.add_argument("--week-end", help="Ngày kết thúc tuần (YYYY-MM-DD). Mặc định: Chủ Nhật tuần hiện tại.")
    parser.add_argument("--token", help="access_token có sẵn (bỏ qua bước login HRM)")
    parser.add_argument("--output-dir", required=True, help="Thư mục ghi file summary (REPORT_OUTPUT_DIR)")
    parser.add_argument("--excel-url", help="SharePoint/OneDrive Sharing URL file Excel (Microsoft Graph API)")
    parser.add_argument("--excel-url2", help="SharePoint/OneDrive Sharing URL cho Sheet 2 (nếu tách file)")
    parser.add_argument("--share-url", help="Alias của --excel-url")
    parser.add_argument("--vpn", choices=["auto", "true", "false"], help="Chế độ VPN (auto: bật khi chưa vào được mạng nội bộ, true: ép bật, false: tắt)")
    parser.add_argument("--vpn-type", help="Loại VPN (openconnect, openfortivpn, openvpn, wireguard, ssh_tunnel, custom)")
    parser.add_argument("--vpn-host", help="Địa chỉ máy chủ VPN (ví dụ csocvpn.fpt.net hoặc vpn.fpt.net)")
    parser.add_argument("--vpn-user", help="Tài khoản VPN (mặc định lấy theo HRM_USERNAME)")
    parser.add_argument("--vpn-otp", help="Mã xác thực OTP 6 số (cho 2FA của OpenVPN csocvpn.fpt.net)")
    parser.add_argument("--vpn-totp-secret", help="Khóa bí mật TOTP (Base32) để tự động sinh mã OTP")
    parser.add_argument("--vpn-config", help="Đường dẫn file cấu hình VPN (.ovpn)")
    parser.add_argument("--vpn-keep-alive", action="store_true", help="Giữ kết nối VPN sau khi hoàn thành scrape")
    parser.add_argument("--input-json", help="Đường dẫn file JSON chứa danh sách projects đã cào sẵn (bỏ qua bước gọi API HRM)")
    args = parser.parse_args()

    output_dir = os.path.abspath(args.output_dir)
    os.makedirs(output_dir, exist_ok=True)

    week_start = args.week_start
    week_end = args.week_end
    if not week_start or not week_end:
        ws, we = default_week_range()
        week_start = week_start or ws
        week_end = week_end or we

    excel_url_arg = args.excel_url or args.share_url or os.environ.get("HRM_EXCEL_URL") or os.environ.get("HRM_EXCEL_SHARE_URL") or ""
    excel_url2_arg = args.excel_url2 or os.environ.get("HRM_EXCEL2_URL") or os.environ.get("HRM_EXCEL_URL2") or os.environ.get("HRM_EXCEL2_SHARE_URL") or os.environ.get("HRM_EXCEL_SHARE_URL2") or ""

    sheet_id_env = os.environ.get("HRM_SHEET_ID", "")
    sheet_id2_env = os.environ.get("HRM_SHEET2_ID", "")

    # Tự động nhận diện nếu HRM_SHEET_ID là link SharePoint / OneDrive
    if not excel_url_arg and sheets_client.is_excel_target(sheet_id_env):
        excel_url_arg = sheet_id_env
    if not excel_url2_arg and sheets_client.is_excel_target(sheet_id2_env):
        excel_url2_arg = sheet_id2_env

    sheet1_name = os.environ.get("HRM_SHEET_NAME", "Project2026")
    config = {
        "divisionCode": os.environ.get("HRM_DIVISION_CODE", ""),
        "startOfWeek": week_start,
        "endOfWeek": week_end,
        # Excel Microsoft Graph target
        "excelUrl": excel_url_arg,
        "excelUrl2": excel_url2_arg,
        # Sheet 1 - schema Project2026 (78 cột A–BZ) / Portfolio 2026 (27 cột A–AA)
        "sheetId": sheet_id_env,
        "sheetName": sheet1_name,
        # Sheet 2 - schema 19 cột A–S (FTI)
        "sheetId2": sheet_id2_env,
        "sheetName2": os.environ.get("HRM_SHEET2_NAME", "FTI"),
        "divisionCode2": os.environ.get("HRM_SHEET2_DIVISION_CODE", "FTI"),
    }

    has_target = bool(config["excelUrl"] or config["sheetId"] or config["excelUrl2"] or config["sheetId2"])
    if not has_target:
        print("[HRM] Lỗi: Chưa cấu hình đích đến (HRM_EXCEL_URL hoặc HRM_SHEET_ID).", file=sys.stderr)
        sys.exit(1)

    # 1 & 2: Lấy dữ liệu danh sách dự án (từ file JSON truyền vào hoặc qua API HRM)
    if args.input_json:
        resolved_input = resolve_input_path(args.input_json, output_dir)
        print(f"[HRM] Nạp danh sách dự án từ file JSON: {resolved_input}...")
        with open(resolved_input, "r", encoding="utf-8") as f:
            raw_data = json.load(f)
            if isinstance(raw_data, dict) and "projects" in raw_data:
                projects = raw_data["projects"]
            elif isinstance(raw_data, list):
                projects = raw_data
            else:
                projects = []
        print(f"[HRM] Đã nạp {len(projects)} dự án từ JSON (bỏ qua bước gọi API HRM).")
    else:
        # Cấu hình VPN kết nối mạng nội bộ
        vpn_cfg = {}
        if args.vpn:
            vpn_cfg["enabled"] = args.vpn
        if args.vpn_type:
            vpn_cfg["type"] = args.vpn_type
        if args.vpn_host:
            vpn_cfg["host"] = args.vpn_host
        if args.vpn_user:
            vpn_cfg["username"] = args.vpn_user
        if args.vpn_otp:
            vpn_cfg["otp"] = args.vpn_otp
        if args.vpn_totp_secret:
            vpn_cfg["totp_secret"] = args.vpn_totp_secret
        if args.vpn_config:
            vpn_cfg["config_path"] = args.vpn_config
        if args.vpn_keep_alive:
            vpn_cfg["auto_disconnect"] = False

        with vpn_manager.managed_vpn(vpn_cfg):
            # 1. Lấy access_token HRM
            token = args.token or os.environ.get("HRM_ACCESS_TOKEN", "")
            if not token:
                print("[HRM] Lấy access_token (login HRM)...")
                token = hrm_auth.login()

            # 2. Scrape API HRM 1 lần duy nhất (toàn bộ dự án)
            print(f"[HRM] Đang gọi API HRM (tuần {week_start} → {week_end})...")
            projects = hrm_client.scrape_projects(
                token, config,
                on_progress=lambda p: print(f"[HRM]  ({p['current']}/{p['total']}) {p['name']}"),
            )

    # 2b. Lọc in-memory cho Sheet 2 (chỉ lấy dự án thuộc division FTI)
    projects2 = projects
    has_sheet2 = bool(config["excelUrl2"] or config["sheetId2"] or (config["excelUrl"] and config["sheetName2"]))
    if has_sheet2:
        div2 = config.get("divisionCode2", "FTI")
        projects2 = [p for p in projects if is_project_in_division(p, div2)]
        print(f"[HRM] Lọc Sheet 2 ({div2}): {len(projects2)}/{len(projects)} dự án phù hợp.")

    # 3. Ghi Sheet 1
    result1 = {"updatedList": [], "insertedList": [], "error": None}
    use_excel_1 = bool(config["excelUrl"] or sheets_client.is_excel_target(config["sheetId"]))

    s1_schema_label = "78 cột A–BZ" if "project2026" in config["sheetName"].lower() else "27 cột A–AA"

    if use_excel_1:
        print(f"[HRM] Đang cập nhật Sheet 1 trên Excel Online qua Microsoft Graph API ({config['sheetName']}, {s1_schema_label})...")
        try:
            r = sheets_client.update_excel_sheets(projects, config)
            result1.update(r)
            print(f"[HRM] Sheet 1 Excel xong - Updated: {len(result1['updatedList'])}, Inserted: {len(result1['insertedList'])}")
        except Exception as e:
            result1["error"] = str(e)
            print(f"[HRM] ⚠️  Sheet 1 Excel lỗi: {e}", file=sys.stderr)
    elif config["sheetId"]:
        print(f"[HRM] Đang cập nhật Sheet 1 trên Google Sheets ({config['sheetName']}, {s1_schema_label})...")
        try:
            creds = sheets_client.get_credentials()
            r = sheets_client.update_google_sheets(projects, config, creds)
            result1.update(r)
            print(f"[HRM] Sheet 1 Google Sheets xong - Updated: {len(result1['updatedList'])}, Inserted: {len(result1['insertedList'])}")
        except Exception as e:
            result1["error"] = str(e)
            print(f"[HRM] ⚠️  Sheet 1 Google Sheets lỗi: {e}", file=sys.stderr)
    else:
        print("[HRM] Bỏ qua Sheet 1 (không có cấu hình).")

    # 4. Ghi Sheet 2 (schema 19 cột A–S - Sheet FTI)
    result2 = {"updatedList": [], "insertedList": [], "error": None}
    use_excel_2 = bool(config["excelUrl2"] or sheets_client.is_excel_target(config["sheetId2"]) or (use_excel_1 and config["sheetName2"]))

    if use_excel_2:
        print(f"[HRM] Đang cập nhật Sheet 2 trên Excel Online qua Microsoft Graph API ({config['sheetName2']}, 19 cột A–S)...")
        try:
            r = sheets_client.update_excel_sheets_v2(projects2, config)
            result2.update(r)
            print(f"[HRM] Sheet 2 Excel xong - Updated: {len(result2['updatedList'])}, Inserted: {len(result2['insertedList'])}")
        except Exception as e:
            result2["error"] = str(e)
            print(f"[HRM] ⚠️  Sheet 2 Excel lỗi: {e}", file=sys.stderr)
    elif config["sheetId2"]:
        print(f"[HRM] Đang cập nhật Sheet 2 trên Google Sheets ({config['sheetName2']}, 19 cột A–S)...")
        try:
            creds = sheets_client.get_credentials()
            r = sheets_client.update_google_sheets_v2(projects2, config, creds)
            result2.update(r)
            print(f"[HRM] Sheet 2 Google Sheets xong - Updated: {len(result2['updatedList'])}, Inserted: {len(result2['insertedList'])}")
        except Exception as e:
            result2["error"] = str(e)
            print(f"[HRM] ⚠️  Sheet 2 Google Sheets lỗi: {e}", file=sys.stderr)
    else:
        print("[HRM] Bỏ qua Sheet 2 (không có cấu hình).")

    # 5. Ghi summary JSON (versioned) vào output dir
    summary_path, version = next_version_path(output_dir, "hrm_weekly_report", "json")
    summary = {
        "weekStart": week_start,
        "weekEnd": week_end,
        "divisionCode": config["divisionCode"],
        "projectCount": len(projects),
        "targetType": "excel_ms_graph" if (use_excel_1 or use_excel_2) else "google_sheets",
        "sheet1": {
            "target": config["excelUrl"] or config["sheetId"],
            "sheetName": config["sheetName"],
            "divisionCode": config["divisionCode"] or "(all)",
            "projectCount": len(projects),
            "schema": s1_schema_label,
            "updatedCount": len(result1["updatedList"]),
            "insertedCount": len(result1["insertedList"]),
            "updatedList": result1["updatedList"],
            "insertedList": result1["insertedList"],
            "error": result1["error"],
        },
        "sheet2": {
            "target": config["excelUrl2"] or config["sheetId2"] or config["excelUrl"],
            "sheetName": config["sheetName2"],
            "divisionCode": config["divisionCode2"],
            "projectCount": len(projects2) if has_sheet2 else 0,
            "schema": "19 cột A–S",
            "updatedCount": len(result2["updatedList"]),
            "insertedCount": len(result2["insertedList"]),
            "updatedList": result2["updatedList"],
            "insertedList": result2["insertedList"],
            "error": result2["error"],
        },
        "generatedAt": datetime.now().isoformat(),
    }
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    total_updated = len(result1["updatedList"]) + len(result2["updatedList"])
    total_inserted = len(result1["insertedList"]) + len(result2["insertedList"])
    print(f"[HRM] Xong! Sheet 1: {len(projects)} dự án | Sheet 2: {len(projects2)} dự án (FTI) - Updated: {total_updated}, Inserted: {total_inserted}")
    print(f"[HRM] Summary: {summary_path} (v{version})")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"[HRM] Lỗi: {e}", file=sys.stderr)
        sys.exit(1)

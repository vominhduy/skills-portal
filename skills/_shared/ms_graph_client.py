"""Microsoft Graph API Client dùng chung cho các skill (Outlook, Excel/SharePoint, HRM).
Module hỗ trợ tích hợp Microsoft Graph API qua MSAL token cache:
- Public Client Application với cache đa tầng (token_cache.bin).
- Ưu tiên acquire_token_silent từ token_cache.bin (tự động refresh access_token khi hết hạn).
- Tự động phục hồi/retry khi token gặp lỗi 401 Unauthorized hoặc 403 Forbidden.
- Hỗ trợ giải mã liên kết chia sẻ SharePoint / OneDrive (encode_share_url).
- Cơ chế ghi chuẩn: PATCH dải ô trực tiếp (Cell-level update) qua Graph Workbook API,
  tuyệt đối không đụng đến các sheet khác hoặc chỉnh sửa của người dùng đồng thời (Co-authoring safe).
- Cơ chế dự phòng khi gặp 501 unsupportedWorkbook: Tải file, chỉnh sửa đúng sheet mục tiêu,
  và cập nhật kèm khóa phiên eTag (If-Match) để chống ghi đè phiên bản cũ của người khác.
"""
from __future__ import annotations

import base64
import io
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

try:
    import msal
except ImportError:
    msal = None

try:
    import requests
except ImportError:
    requests = None

try:
    import openpyxl
except ImportError:
    openpyxl = None

CLIENT_ID_DEFAULT = "14d82eec-204b-4c2f-b7e8-296a70dab67e"
AUTHORITY_DEFAULT = "https://login.microsoftonline.com/organizations"
GRAPH_BASE = "https://graph.microsoft.com/v1.0"

_ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

CACHE_SEARCH_PATHS = [
    os.environ.get("MS_GRAPH_CACHE_FILE"),
    os.path.join(_ROOT_DIR, "data", "token_cache.bin"),
    "/app/data/token_cache.bin",
    os.path.join(os.getcwd(), "data", "token_cache.bin"),
    "token_cache.bin",
    os.path.expanduser("~/.cache/msal/token_cache.bin"),
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "token_cache.bin"),
    os.path.join(os.getcwd(), "token_cache.bin"),
]


def get_cache_file_path(prefer_write_path: bool = False) -> str:
    data_dir = os.path.join(_ROOT_DIR, "data")
    if prefer_write_path:
        if os.path.isdir(data_dir):
            return os.path.join(data_dir, "token_cache.bin")
        if os.path.isdir("/app/data"):
            return "/app/data/token_cache.bin"

    for p in CACHE_SEARCH_PATHS:
        if p and os.path.isfile(p):
            return os.path.abspath(p)

    if os.path.isdir(data_dir):
        return os.path.join(data_dir, "token_cache.bin")
    if os.path.isdir("/app/data"):
        return "/app/data/token_cache.bin"

    target = os.path.expanduser("~/.cache/msal/token_cache.bin")
    os.makedirs(os.path.dirname(target), exist_ok=True)
    return target


def get_ms_graph_token(
    scopes: Optional[List[str]] = None,
    client_id: Optional[str] = None,
    authority: Optional[str] = None,
    cache_file: Optional[str] = None,
    interactive: bool = True,
    force_cache: bool = False,
) -> str:
    if scopes is None:
        scopes = ["User.Read", "Files.ReadWrite", "Mail.Read"]

    cid = client_id or os.environ.get("MS_GRAPH_CLIENT_ID") or CLIENT_ID_DEFAULT
    auth = authority or os.environ.get("MS_GRAPH_AUTHORITY") or AUTHORITY_DEFAULT
    cpath = cache_file or get_cache_file_path()

    if msal is not None and cpath and os.path.isfile(cpath):
        try:
            cache = msal.SerializableTokenCache()
            with open(cpath, "r", encoding="utf-8") as f:
                cache.deserialize(f.read())

            app = msal.PublicClientApplication(cid, authority=auth, token_cache=cache)
            accounts = app.get_accounts()

            if accounts:
                result = app.acquire_token_silent(scopes, account=accounts[0])
                if not result and scopes:
                    for s in scopes:
                        r_single = app.acquire_token_silent([s], account=accounts[0])
                        if r_single and "access_token" in r_single:
                            result = r_single
                            break

                if result and "access_token" in result:
                    if cache.has_state_changed:
                        try:
                            with open(cpath, "w", encoding="utf-8") as f:
                                f.write(cache.serialize())
                        except Exception:
                            pass
                    return result["access_token"]
        except Exception as e:
            print(f"[MS Graph] Cảnh báo đọc token cache: {e}", file=sys.stderr)

    if not force_cache:
        env_token = (
            os.environ.get("MS_GRAPH_ACCESS_TOKEN")
            or os.environ.get("OUTLOOK_ACCESS_TOKEN")
            or ""
        ).strip()
        if env_token:
            return env_token

    if msal is not None and interactive:
        # Nếu đang chạy ngầm trong backend/docker (không có TTY), không block 15 phút mà báo lỗi hướng dẫn ngay
        if not sys.stdin.isatty() and not os.environ.get("FORCE_DEVICE_FLOW"):
            raise PermissionError(
                "Không thể lấy token xác thực Microsoft Graph API (chưa có token_cache.bin). "
                "Hệ thống không thể mở Device Flow tương tác vì tiến trình chạy ở chế độ nền. "
                "Vui lòng chạy 'python3 scripts/outlook-device-login.py' trên terminal hoặc đặt file token_cache.bin vào thư mục data/."
            )

        print("\n[MS Graph] Cần xác thực Microsoft 365 (Device Flow)...", flush=True)
        cache = msal.SerializableTokenCache()
        if cpath and os.path.isfile(cpath):
            try:
                with open(cpath, "r", encoding="utf-8") as f:
                    cache.deserialize(f.read())
            except Exception:
                pass

        app = msal.PublicClientApplication(cid, authority=auth, token_cache=cache)
        flow = app.initiate_device_flow(scopes=scopes)
        if "user_code" not in flow:
            raise RuntimeError(f"Lỗi khởi tạo luồng Device Flow: {flow}")

        print(flow.get("message", "Vui lòng đăng nhập theo chỉ dẫn trên màn hình"), flush=True)
        result = app.acquire_token_by_device_flow(flow)

        if result and "access_token" in result:
            if cache.has_state_changed and cpath:
                try:
                    os.makedirs(os.path.dirname(cpath), exist_ok=True)
                    with open(cpath, "w", encoding="utf-8") as f:
                        f.write(cache.serialize())
                except Exception:
                    pass
            return result["access_token"]

    raise PermissionError(
        "Không thể lấy token xác thực Microsoft Graph API. "
        "Vui lòng đảm bảo token_cache.bin hợp lệ hoặc chạy 'python3 scripts/outlook-device-login.py' để xác thực."
    )


def get_auth_headers(token: Optional[str] = None, scopes: Optional[List[str]] = None) -> Dict[str, str]:
    tok = token or get_ms_graph_token(scopes=scopes)
    return {
        "Authorization": f"Bearer {tok}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


def encode_share_url(url: str) -> str:
    clean_url = url.strip()
    encoded = base64.urlsafe_b64encode(clean_url.encode("utf-8")).decode("utf-8")
    return "u!" + encoded.rstrip("=")


def resolve_drive_item(
    share_url_or_id: Optional[str] = None,
    drive_id: Optional[str] = None,
    item_id: Optional[str] = None,
    token: Optional[str] = None,
) -> Tuple[str, str, Dict[str, Any]]:
    if drive_id and item_id:
        headers = get_auth_headers(token=token, scopes=["User.Read", "Files.ReadWrite"])
        res = requests.get(f"{GRAPH_BASE}/drives/{drive_id}/items/{item_id}", headers=headers, timeout=20)
        item_meta = res.json() if res.ok else {}
        return drive_id, item_id, item_meta

    if not share_url_or_id:
        raise ValueError("Cần cung cấp sharing URL hoặc cặp (drive_id, item_id)")

    clean = share_url_or_id.strip()
    share_id = clean if clean.startswith("u!") else encode_share_url(clean)

    headers = get_auth_headers(token=token, scopes=["User.Read", "Files.ReadWrite"])
    url = f"{GRAPH_BASE}/shares/{share_id}/driveItem"
    res = requests.get(url, headers=headers, timeout=30)

    if res.status_code in (401, 403):
        fresh_token = get_ms_graph_token(scopes=["User.Read", "Files.ReadWrite"], force_cache=True, interactive=False)
        headers["Authorization"] = f"Bearer {fresh_token}"
        res = requests.get(url, headers=headers, timeout=30)

    if not res.ok:
        raise RuntimeError(f"Lỗi phân giải share link ({res.status_code}): {res.text}")

    item = res.json()
    resolved_item_id = item.get("id")
    resolved_drive_id = item.get("parentReference", {}).get("driveId")
    if not resolved_drive_id or not resolved_item_id:
        raise RuntimeError(f"Không tìm thấy driveId/itemId trong kết quả driveItem: {item}")

    return resolved_drive_id, resolved_item_id, item


def get_item_metadata(drive_id: str, item_id: str, token: Optional[str] = None) -> Dict[str, Any]:
    """Lấy thông tin metadata mới nhất của file (bao gồm eTag và cTag)."""
    headers = get_auth_headers(token=token, scopes=["User.Read", "Files.ReadWrite"])
    url = f"{GRAPH_BASE}/drives/{drive_id}/items/{item_id}"
    res = requests.get(url, headers=headers, timeout=20)
    if not res.ok:
        return {}
    return res.json()


def download_file_content(drive_id: str, item_id: str, token: Optional[str] = None) -> Tuple[bytes, str]:
    """Tải nội dung nhị phân của file kèm eTag hiện tại để bảo vệ kiểm soát đồng thời."""
    headers = get_auth_headers(token=token, scopes=["User.Read", "Files.ReadWrite"])
    url = f"{GRAPH_BASE}/drives/{drive_id}/items/{item_id}/content"
    res = requests.get(url, headers=headers, timeout=60)

    if res.status_code in (401, 403):
        fresh_token = get_ms_graph_token(scopes=["User.Read", "Files.ReadWrite"], force_cache=True, interactive=False)
        headers["Authorization"] = f"Bearer {fresh_token}"
        res = requests.get(url, headers=headers, timeout=60)

    if not res.ok:
        raise RuntimeError(f"Lỗi tải nội dung file Excel ({res.status_code}): {res.text}")

    etag = res.headers.get("ETag") or res.headers.get("eTag") or ""
    return res.content, etag


def upload_file_content(
    drive_id: str,
    item_id: str,
    content: bytes,
    if_match_etag: Optional[str] = None,
    token: Optional[str] = None,
) -> Dict[str, Any]:
    """Ghi đè nội dung file lên SharePoint / OneDrive có kiểm soát eTag (If-Match) chống ghi đè phiên bản cũ."""
    tok = token or get_ms_graph_token(scopes=["User.Read", "Files.ReadWrite"])
    headers = {
        "Authorization": f"Bearer {tok}",
        "Content-Type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    }
    if if_match_etag:
        headers["If-Match"] = if_match_etag

    url = f"{GRAPH_BASE}/drives/{drive_id}/items/{item_id}/content"
    res = requests.put(url, headers=headers, data=content, timeout=60)

    if res.status_code == 412:
        raise RuntimeError("CONCURRENCY_CONFLICT: Tệp Excel đã bị chỉnh sửa bởi người dùng khác trong lúc xử lý (412 Precondition Failed).")

    if res.status_code in (401, 403):
        fresh_token = get_ms_graph_token(scopes=["User.Read", "Files.ReadWrite"], force_cache=True, interactive=False)
        headers["Authorization"] = f"Bearer {fresh_token}"
        res = requests.put(url, headers=headers, data=content, timeout=60)
        if res.status_code == 412:
            raise RuntimeError("CONCURRENCY_CONFLICT: Tệp Excel đã bị chỉnh sửa bởi người dùng khác trong lúc xử lý (412 Precondition Failed).")

    if not res.ok:
        raise RuntimeError(f"Lỗi upload file Excel lên SharePoint ({res.status_code}): {res.text}")
    return res.json()


def list_worksheets(
    drive_id: str,
    item_id: str,
    token: Optional[str] = None,
) -> List[Dict[str, Any]]:
    headers = get_auth_headers(token=token, scopes=["User.Read", "Files.ReadWrite"])
    url = f"{GRAPH_BASE}/drives/{drive_id}/items/{item_id}/workbook/worksheets"
    res = requests.get(url, headers=headers, timeout=30)

    if res.status_code in (401, 403):
        fresh_token = get_ms_graph_token(scopes=["User.Read", "Files.ReadWrite"], force_cache=True, interactive=False)
        headers["Authorization"] = f"Bearer {fresh_token}"
        res = requests.get(url, headers=headers, timeout=30)

    if res.ok:
        return res.json().get("value", [])

    if res.status_code == 501 or "unsupportedWorkbook" in res.text or "FileCorruptTryRepair" in res.text:
        if openpyxl is None:
            raise ImportError("Cần cài đặt openpyxl để xử lý file Excel này.")
        file_bytes, _ = download_file_content(drive_id, item_id, token=token)
        wb = openpyxl.load_workbook(io.BytesIO(file_bytes), data_only=True)
        sheets_list = [{"id": s, "name": s, "visibility": "Visible"} for s in wb.sheetnames]
        wb.close()
        return sheets_list

    raise RuntimeError(f"Lỗi lấy danh sách worksheet ({res.status_code}): {res.text}")


def ensure_worksheet(
    drive_id: str,
    item_id: str,
    sheet_name: str,
    token: Optional[str] = None,
) -> Dict[str, Any]:
    quoted_name = sheet_name.replace("'", "''")
    headers = get_auth_headers(token=token, scopes=["User.Read", "Files.ReadWrite"])
    url = f"{GRAPH_BASE}/drives/{drive_id}/items/{item_id}/workbook/worksheets('{quoted_name}')"
    res = requests.get(url, headers=headers, timeout=30)
    if res.status_code in (401, 403):
        fresh_token = get_ms_graph_token(scopes=["User.Read", "Files.ReadWrite"], force_cache=True, interactive=False)
        headers["Authorization"] = f"Bearer {fresh_token}"
        res = requests.get(url, headers=headers, timeout=30)
    if res.ok:
        return res.json()

    # Nếu chưa có, tạo mới qua Graph API
    url_create = f"{GRAPH_BASE}/drives/{drive_id}/items/{item_id}/workbook/worksheets"
    res_create = requests.post(url_create, headers=headers, json={"name": sheet_name}, timeout=30)
    if res_create.status_code in (401, 403):
        fresh_token = get_ms_graph_token(scopes=["User.Read", "Files.ReadWrite"], force_cache=True, interactive=False)
        headers["Authorization"] = f"Bearer {fresh_token}"
        res_create = requests.post(url_create, headers=headers, json={"name": sheet_name}, timeout=30)
    if not res_create.ok:
        raise RuntimeError(f"Lỗi tạo worksheet '{sheet_name}' trên Excel Online ({res_create.status_code}): {res_create.text}")
    return res_create.json()


def get_worksheet_used_range(
    drive_id: str,
    item_id: str,
    sheet_name: str,
    token: Optional[str] = None,
) -> Dict[str, Any]:
    headers = get_auth_headers(token=token, scopes=["User.Read", "Files.ReadWrite"])
    quoted_name = sheet_name.replace("'", "''")
    url = f"{GRAPH_BASE}/drives/{drive_id}/items/{item_id}/workbook/worksheets('{quoted_name}')/usedRange"

    res = None
    for attempt in range(4):
        res = requests.get(url, headers=headers, timeout=45)

        if res.status_code in (401, 403) and attempt == 0:
            fresh_token = get_ms_graph_token(scopes=["User.Read", "Files.ReadWrite"], force_cache=True, interactive=False)
            headers["Authorization"] = f"Bearer {fresh_token}"
            continue

        if res.status_code in (429, 503) and attempt < 3:
            retry_after = int(res.headers.get("Retry-After", 2))
            time.sleep(max(retry_after, 2))
            continue

        if res.ok:
            return res.json()
        break

    if res is not None and (res.status_code == 501 or "unsupportedWorkbook" in res.text or "FileCorruptTryRepair" in res.text):
        file_bytes, _ = download_file_content(drive_id, item_id, token=token)
        wb = openpyxl.load_workbook(io.BytesIO(file_bytes), data_only=True)
        if sheet_name not in wb.sheetnames:
            raise KeyError(f"Không tìm thấy sheet '{sheet_name}' trong file Excel.")
        ws = wb[sheet_name]
        raw_rows = list(ws.iter_rows(values_only=True))
        values = []
        for r in raw_rows:
            values.append([c if c is not None else "" for c in r])
        wb.close()
        return {"address": f"'{sheet_name}'!A1", "values": values}

    err_text = res.text if res is not None else "No response"
    status = res.status_code if res is not None else 0
    raise RuntimeError(f"Lỗi đọc usedRange sheet '{sheet_name}' ({status}): {err_text}")


def update_worksheet_range(
    drive_id: str,
    item_id: str,
    sheet_name: str,
    range_address: str,
    values: List[List[Any]],
    token: Optional[str] = None,
) -> Dict[str, Any]:
    """Cập nhật dữ liệu vào dải ô Excel qua PATCH (Cell-level update).
    Chỉ tác động đến đúng dải ô và sheet được chỉ định, bảo vệ 100% các sheet khác và chỉnh sửa đồng thời.
    """
    headers = get_auth_headers(token=token, scopes=["User.Read", "Files.ReadWrite"])
    quoted_name = sheet_name.replace("'", "''")
    url = f"{GRAPH_BASE}/drives/{drive_id}/items/{item_id}/workbook/worksheets('{quoted_name}')/range(address='{range_address}')"
    payload = {"values": values}

    res = None
    for attempt in range(4):
        res = requests.patch(url, headers=headers, json=payload, timeout=45)

        if res.status_code in (401, 403) and attempt == 0:
            fresh_token = get_ms_graph_token(scopes=["User.Read", "Files.ReadWrite"], force_cache=True, interactive=False)
            headers["Authorization"] = f"Bearer {fresh_token}"
            continue

        if res.status_code in (429, 503) and attempt < 3:
            retry_after = int(res.headers.get("Retry-After", 2))
            time.sleep(max(retry_after, 2))
            continue

        if res.ok:
            return res.json()
        break

    err_text = res.text if res is not None else "No response"
    status = res.status_code if res is not None else 0
    raise RuntimeError(f"Lỗi cập nhật range '{range_address}' ({status}): {err_text}")


def get_outlook_messages(
    top: int = 30,
    query: Optional[str] = None,
    unread_only: bool = False,
    token: Optional[str] = None,
) -> List[Dict[str, Any]]:
    headers = get_auth_headers(token=token, scopes=["User.Read", "Mail.Read"])
    headers["Prefer"] = 'outlook.body-content-type="text"'

    params: Dict[str, str] = {
        "$top": str(min(top, 100)),
        "$select": "id,conversationId,receivedDateTime,from,toRecipients,ccRecipients,subject,bodyPreview,body,hasAttachments,isRead",
    }
    if unread_only:
        params["$filter"] = "isRead eq false"

    if query and query.strip():
        params["$search"] = f'"{query.strip()}"'
    else:
        params["$orderby"] = "receivedDateTime desc"

    url = f"{GRAPH_BASE}/me/mailFolders/Inbox/messages"
    res = requests.get(url, headers=headers, params=params, timeout=30)

    if res.status_code in (401, 403):
        fresh_token = get_ms_graph_token(scopes=["User.Read", "Mail.Read"], force_cache=True, interactive=False)
        headers["Authorization"] = f"Bearer {fresh_token}"
        res = requests.get(url, headers=headers, params=params, timeout=30)

    if not res.ok:
        url_fallback = f"{GRAPH_BASE}/me/messages"
        res = requests.get(url_fallback, headers=headers, params=params, timeout=30)
        if res.status_code in (401, 403):
            fresh_token = get_ms_graph_token(scopes=["User.Read", "Mail.Read"], force_cache=True, interactive=False)
            headers["Authorization"] = f"Bearer {fresh_token}"
            res = requests.get(url_fallback, headers=headers, params=params, timeout=30)

        if not res.ok:
            raise RuntimeError(f"Lỗi đọc email qua Microsoft Graph ({res.status_code}): {res.text}")

    return res.json().get("value", [])


def get_outlook_message_body(message_id: str, token: Optional[str] = None) -> Optional[str]:
    headers = get_auth_headers(token=token, scopes=["User.Read", "Mail.Read"])
    headers["Prefer"] = 'outlook.body-content-type="text"'
    url = f"{GRAPH_BASE}/me/messages/{message_id}?$select=id,subject,body"
    res = requests.get(url, headers=headers, timeout=30)
    if res.status_code in (401, 403):
        fresh_token = get_ms_graph_token(scopes=["User.Read", "Mail.Read"], force_cache=True, interactive=False)
        headers["Authorization"] = f"Bearer {fresh_token}"
        res = requests.get(url, headers=headers, timeout=30)
    if not res.ok:
        return None
    return res.json().get("body", {}).get("content", "")

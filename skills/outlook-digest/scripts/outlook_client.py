"""Outlook / Office 365 Client - kết nối qua Microsoft Graph API (MSAL Device Flow / Token Cache)
và IMAP SSL dự phòng (có HTTP CONNECT Proxy Tunneling).

"""
from __future__ import annotations

import base64
import email
from email.header import decode_header
import html
import imaplib
import os
import re
import socket
import ssl
import sys
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import quote, urlencode, urlparse

# Đặt timeout mặc định cho toàn bộ socket là 10 giây
socket.setdefaulttimeout(10.0)

_HERE = os.path.dirname(os.path.abspath(__file__))
_SHARED_DIR = os.path.join(_HERE, "..", "..", "_shared")
_SHARED_NET = os.path.join(_HERE, "..", "..", "weekly-report-api", "scripts")
for p in (_SHARED_DIR, _SHARED_NET):
    if p not in sys.path:
        sys.path.insert(0, p)

try:
    from network_utils import request_with_proxy_fallback  # type: ignore
except ImportError:
    import requests

    def request_with_proxy_fallback(method: str, url: str, **kwargs: Any):
        return requests.request(method, url, **kwargs)

try:
    import ms_graph_client as mg
except ImportError:
    mg = None


MS_GRAPH_API = "https://graph.microsoft.com/v1.0"


def _clean_html(raw_html: str) -> str:
    """Loại bỏ thẻ HTML và chuẩn hóa khoảng trắng."""
    if not raw_html:
        return ""
    text = re.sub(r"<(?:br|/p|/div|/tr)>", "\n", raw_html, flags=re.IGNORECASE)
    text = re.sub(r"<style[\s\S]*?</style>", "", text, flags=re.IGNORECASE)
    text = re.sub(r"<script[\s\S]*?</script>", "", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _decode_mime_str(val: Optional[str]) -> str:
    """Giải mã MIME header text (RFC 2047)."""
    if not val:
        return ""
    parts = decode_header(val)
    decoded_fragments = []
    for text, enc in parts:
        if isinstance(text, bytes):
            charset = enc or "utf-8"
            try:
                decoded_fragments.append(text.decode(charset, errors="replace"))
            except (LookupError, UnicodeDecodeError):
                decoded_fragments.append(text.decode("utf-8", errors="replace"))
        else:
            decoded_fragments.append(str(text))
    return "".join(decoded_fragments).strip()


# ── Lớp IMAP hỗ trợ HTTP CONNECT Proxy Tunneling ──

class ProxiedIMAP4_SSL(imaplib.IMAP4):
    """IMAP client kết nối qua HTTP CONNECT Proxy Tunnel và mã hoá SSL."""

    def __init__(self, host: str, port: int = 993, proxy_url: Optional[str] = None, timeout: float = 10.0):
        self.target_host = host
        self.target_port = port
        self.proxy_url = proxy_url
        self.sock_timeout = timeout
        super().__init__(host, port)

    def _create_socket(self, timeout=None):
        t = timeout or self.sock_timeout
        if self.proxy_url:
            p = urlparse(self.proxy_url)
            proxy_host = p.hostname or "127.0.0.1"
            proxy_port = p.port or 8080

            raw_sock = socket.create_connection((proxy_host, proxy_port), timeout=t)
            raw_sock.settimeout(t)

            connect_req = f"CONNECT {self.target_host}:{self.target_port} HTTP/1.1\r\nHost: {self.target_host}:{self.target_port}\r\n"
            if p.username:
                pwd = p.password or ""
                auth_str = f"{p.username}:{pwd}"
                b64_auth = base64.b64encode(auth_str.encode()).decode("ascii")
                connect_req += f"Proxy-Authorization: Basic {b64_auth}\r\n"
            connect_req += "\r\n"

            raw_sock.sendall(connect_req.encode("latin-1"))

            response = b""
            while b"\r\n\r\n" not in response:
                chunk = raw_sock.recv(1024)
                if not chunk:
                    break
                response += chunk

            first_line = response.split(b"\r\n")[0].decode("latin-1", errors="ignore")
            if " 200 " not in first_line and not first_line.startswith("HTTP/1.0 200") and not first_line.startswith("HTTP/1.1 200"):
                raw_sock.close()
                raise OSError(f"Proxy HTTP CONNECT bị từ chối ({first_line})")

            ssl_ctx = ssl.create_default_context()
            return ssl_ctx.wrap_socket(raw_sock, server_hostname=self.target_host)
        else:
            raw_sock = socket.create_connection((self.target_host, self.target_port), timeout=t)
            raw_sock.settimeout(t)
            ssl_ctx = ssl.create_default_context()
            return ssl_ctx.wrap_socket(raw_sock, server_hostname=self.target_host)


# ── 1. Microsoft Graph API Provider (Kế thừa /outlook_mail.py) ──

def _fetch_graph_messages(query: str, max_results: int = 15, unread_only: bool = False, direct_only: bool = False) -> Tuple[bool, List[Dict[str, Any]], str]:
    """Lấy danh sách email qua Microsoft Graph API ."""
    if mg is None:
        return False, [], "Không tìm thấy module ms_graph_client"

    try:
        # Gọi trực tiếp qua mg.get_outlook_messages (đã tích hợp MSAL cache, silent acquire, và tự động phục hồi khi lỗi 401/403)
        items = mg.get_outlook_messages(top=max_results, query=query, unread_only=unread_only, direct_only=direct_only)
        out: List[Dict[str, Any]] = []

        for item in items:
            mid = item.get("id") or ""
            conv_id = item.get("conversationId") or ""
            date_str = item.get("receivedDateTime") or ""
            subject = item.get("subject") or "(Không có tiêu đề)"

            from_obj = item.get("from", {}).get("emailAddress", {})
            from_name = from_obj.get("name") or ""
            from_addr = from_obj.get("address") or ""
            from_str = f"{from_name} <{from_addr}>".strip() if from_name and from_addr else (from_addr or from_name)

            to_recipients = item.get("toRecipients") or []
            to_list = []
            for r in to_recipients:
                addr = r.get("emailAddress", {}).get("address") or ""
                name = r.get("emailAddress", {}).get("name") or ""
                to_list.append(f"{name} <{addr}>".strip() if name and addr else (addr or name))
            to_str = ", ".join(to_list)

            cc_recipients = item.get("ccRecipients") or []
            cc_list = []
            for r in cc_recipients:
                addr = r.get("emailAddress", {}).get("address") or ""
                name = r.get("emailAddress", {}).get("name") or ""
                cc_list.append(f"{name} <{addr}>".strip() if name and addr else (addr or name))
            cc_str = ", ".join(cc_list)

            snippet = item.get("bodyPreview") or ""
            body_obj = item.get("body") or {}
            raw_body = body_obj.get("content") or ""
            if body_obj.get("contentType") == "html":
                clean_body = _clean_html(raw_body)
            else:
                clean_body = raw_body.strip()

            out.append({
                "id": mid,
                "thread_id": conv_id,
                "date": date_str,
                "from": from_str,
                "to": to_str,
                "cc": cc_str,
                "direct_type": item.get("_direct_type") or "",
                "subject": subject,
                "snippet": snippet,
                "body": clean_body or snippet,
                "has_attachments": bool(item.get("hasAttachments")),
                "is_read": bool(item.get("isRead", False)),
            })

        print(f"[+] Lấy thành công {len(out)} email qua Microsoft Graph API.")
        return True, out, ""
    except Exception as e:
        return False, [], str(e)


# ── 2. IMAP Provider (Exchange / Office 365 có Proxy Tunnel) ──

def _fetch_imap_messages(query: str, max_results: int = 15) -> Tuple[bool, List[Dict[str, Any]], str]:
    user = (os.environ.get("OUTLOOK_USERNAME") or os.environ.get("OUTLOOK_EMAIL") or "").strip()
    pwd = (os.environ.get("OUTLOOK_PASSWORD") or "").strip()
    pwd = pwd.replace(" ", "").strip()

    if not user or not pwd:
        return False, [], "Thiếu email hoặc mật khẩu ứng dụng Outlook (App Password)"

    server_host = os.environ.get("OUTLOOK_IMAP_SERVER", "outlook.office365.com").strip()
    server_port = int(os.environ.get("OUTLOOK_IMAP_PORT", "993"))
    proxy_url = (
        os.environ.get("HTTPS_PROXY")
        or os.environ.get("HTTP_PROXY")
        or os.environ.get("https_proxy")
        or os.environ.get("http_proxy")
        or ""
    ).strip() or None

    print(f"[*] Đang kết nối Outlook qua IMAP SSL ({server_host}:{server_port}) - Tài khoản: {user}...")
    if proxy_url:
        p_parsed = urlparse(proxy_url)
        print(f"[*] Áp dụng HTTP Proxy Tunnel: {p_parsed.hostname}:{p_parsed.port or 8080}")

    mail = None
    last_err = None

    if proxy_url:
        try:
            mail = ProxiedIMAP4_SSL(server_host, server_port, proxy_url=proxy_url, timeout=10.0)
        except Exception as e:
            print(f"[-] Kết nối IMAP qua Proxy Tunnel thất bại: {e}. Đang thử kết nối trực tiếp...", file=sys.stderr)
            last_err = e

    if not mail:
        try:
            socket.setdefaulttimeout(10.0)
            mail = imaplib.IMAP4_SSL(server_host, server_port)
        except Exception as e:
            last_err = e

    if not mail:
        err_msg = str(last_err or "Không thể khởi tạo kết nối IMAP")
        if "AUTHENTICATIONFAILED" in err_msg.upper() or "LOGIN FAILED" in err_msg.upper():
            return False, [], "Xác thực IMAP thất bại: Sai email hoặc sai Mật khẩu ứng dụng (App Password)."
        return False, [], f"Không thể kết nối đến máy chủ IMAP {server_host}:{server_port} ({err_msg})"

    try:
        mail.login(user, pwd)
        mail.select("INBOX", readonly=True)

        search_criteria = "ALL"
        if query:
            clean_q = re.sub(r'["\\]', '', query.strip())
            search_criteria = f'(OR (SUBJECT "{clean_q}") (BODY "{clean_q}"))'

        typ, data = mail.search(None, search_criteria)
        if typ != "OK" or not data[0]:
            mail.logout()
            print("[+] Kết nối IMAP thành công: Hòm thư INBOX không có email nào thỏa điều kiện tìm kiếm.")
            return True, [], ""

        msg_ids = data[0].split()
        msg_ids.reverse()
        selected_ids = msg_ids[:max_results]

        out: List[Dict[str, Any]] = []
        for mid_bytes in selected_ids:
            mid_str = mid_bytes.decode()
            typ, mdata = mail.fetch(mid_bytes, "(RFC822)")
            if typ != "OK" or not mdata or not mdata[0]:
                continue

            raw_email = mdata[0][1]
            msg = email.message_from_bytes(raw_email)

            subject = _decode_mime_str(msg.get("Subject")) or "(Không có tiêu đề)"
            from_str = _decode_mime_str(msg.get("From")) or ""
            to_str = _decode_mime_str(msg.get("To")) or ""
            cc_str = _decode_mime_str(msg.get("Cc")) or ""
            date_str = msg.get("Date") or ""

            body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    content_type = part.get_content_type()
                    content_disp = str(part.get("Content-Disposition") or "")
                    if "attachment" in content_disp:
                        continue
                    if content_type == "text/plain":
                        payload = part.get_payload(decode=True)
                        if payload:
                            body = payload.decode(part.get_content_charset() or "utf-8", errors="replace")
                            break
                    elif content_type == "text/html" and not body:
                        payload = part.get_payload(decode=True)
                        if payload:
                            body = _clean_html(payload.decode(part.get_content_charset() or "utf-8", errors="replace"))
            else:
                payload = msg.get_payload(decode=True)
                if payload:
                    body = payload.decode(msg.get_content_charset() or "utf-8", errors="replace")
                    if msg.get_content_type() == "text/html":
                        body = _clean_html(body)

            snippet = (body[:200] + "...") if len(body) > 200 else body
            out.append({
                "id": mid_str,
                "thread_id": msg.get("Message-ID") or mid_str,
                "date": date_str,
                "from": from_str,
                "to": to_str,
                "cc": cc_str,
                "subject": subject,
                "snippet": snippet.strip(),
                "body": body.strip() or snippet.strip(),
                "has_attachments": False,
            })

        mail.logout()
        print(f"[+] Đã tải thành công {len(out)} email qua IMAP Outlook.")
        return True, out, ""
    except Exception as e:
        err_msg = str(e)
        if "AUTHENTICATIONFAILED" in err_msg.upper() or "LOGIN FAILED" in err_msg.upper():
            return False, [], "Xác thực IMAP thất bại: Sai email hoặc sai Mật khẩu ứng dụng (App Password). Vui lòng kiểm tra lại trong Cài đặt."
        return False, [], f"Lỗi truy vấn IMAP Outlook: {err_msg}"


def fetch_messages(query: str = "", max_results: int = 15, unread_only: bool = False, direct_only: bool = False) -> List[Dict[str, Any]]:
    """Lấy danh sách email từ Outlook:
    1. Ưu tiên Microsoft Graph API (MSAL Device Flow / token cache ).
    2. Fallback sang IMAP SSL nếu có App Password và Graph API không sẵn sàng.
    """
    print("[*] Đang kết nối Outlook qua Microsoft Graph API (MSAL / token cache)...")
    ok, messages, err = _fetch_graph_messages(query, max_results, unread_only=unread_only, direct_only=direct_only)
    if ok:
        return messages
    print(f"[-] Microsoft Graph API không kết nối được: {err}", file=sys.stderr)

    has_imap_creds = bool((os.environ.get("OUTLOOK_USERNAME") or os.environ.get("OUTLOOK_EMAIL")) and os.environ.get("OUTLOOK_PASSWORD"))
    if has_imap_creds:
        print("[*] Chuyển hướng thử IMAP SSL...")
        ok, messages, err = _fetch_imap_messages(query, max_results)
        if ok:
            return messages
        print(f"[-] IMAP Outlook không thể kết nối: {err}", file=sys.stderr)

    print(
        "❌ Không thể kết nối tới tài khoản Outlook qua Microsoft Graph API hoặc IMAP.\n"
        "Gợi ý:\n"
        "1. Chạy xác thực Microsoft: python3 scripts/outlook-device-login.py hoặc kiểm tra token_cache.bin.\n"
        "2. Hoặc cấu hình Email & Mật khẩu ứng dụng (App Password) trong Cài đặt webapp.",
        file=sys.stderr,
    )
    sys.exit(2)

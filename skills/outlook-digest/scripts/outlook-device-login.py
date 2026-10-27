#!/usr/bin/env python3
"""Microsoft 365 / Outlook Device Code Flow Login Script.
Sử dụng thư viện chuẩn urllib.request (không phụ thuộc requests/msal bên ngoài).
Hỗ trợ:
  --init-only    : Khởi tạo Device Code, lưu trạng thái vào data/device_flow_pending.json và in mã ngay.
  --poll-pending : Chạy nền kiểm tra (poll) mã Device Code đã khởi tạo cho đến khi đăng nhập thành công và lưu data/token_cache.bin.
  (mặc định)     : Chạy khởi tạo mã + tự động fork tiến trình nền chờ đăng nhập.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

CLIENT_ID_DEFAULT = "14d82eec-204b-4c2f-b7e8-296a70dab67e"
AUTHORITY_DEFAULT = "https://login.microsoftonline.com/organizations"
SCOPES = ["User.Read", "Mail.Read", "Files.ReadWrite", "offline_access"]

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
DATA_DIR = os.path.join(ROOT_DIR, "data")
CACHE_PATH = os.path.join(DATA_DIR, "token_cache.bin")
CACHE_JSON_PATH = os.path.join(DATA_DIR, "token_cache.json")
PENDING_PATH = os.path.join(DATA_DIR, "device_flow_pending.json")


def _http_post_form(url: str, form_data: dict, timeout: int = 20) -> tuple[int, dict, str]:
    encoded = urllib.parse.urlencode(form_data).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=encoded,
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            try:
                return resp.status, json.loads(raw), raw
            except Exception:
                return resp.status, {}, raw
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", errors="replace")
        try:
            return e.code, json.loads(raw), raw
        except Exception:
            return e.code, {}, raw


def init_flow(client_id: str, authority: str) -> dict:
    os.makedirs(DATA_DIR, exist_ok=True)
    device_code_url = f"{authority}/oauth2/v2.0/devicecode"
    status, flow, raw = _http_post_form(
        device_code_url,
        {"client_id": client_id, "scope": " ".join(SCOPES)},
        timeout=20,
    )
    if status >= 400 or "device_code" not in flow:
        print(f"❌ Không thể khởi tạo Device Code Flow ({status}): {raw}", file=sys.stderr)
        sys.exit(1)

    flow["_client_id"] = client_id
    flow["_authority"] = authority
    flow["_created_at"] = time.time()
    with open(PENDING_PATH, "w", encoding="utf-8") as f:
        json.dump(flow, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 65)
    print("🔐 ĐĂNG NHẬP MICROSOFT 365 / OUTLOOK (DEVICE CODE FLOW)")
    print("=" * 65)
    print(flow.get("message") or f"Mở {flow.get('verification_uri')} và nhập mã: {flow.get('user_code')}")
    print(f"🔗 Link xác thực : {flow.get('verification_uri', 'https://microsoft.com/devicelogin')}")
    print(f"🔑 Mã của bạn    : {flow.get('user_code')}")
    print("=" * 65 + "\n", flush=True)
    return flow


def poll_flow(flow: dict) -> None:
    os.makedirs(DATA_DIR, exist_ok=True)
    client_id = flow.get("_client_id") or CLIENT_ID_DEFAULT
    authority = (flow.get("_authority") or AUTHORITY_DEFAULT).rstrip("/")
    token_url = f"{authority}/oauth2/v2.0/token"

    interval = int(flow.get("interval", 5))
    expires_in = int(flow.get("expires_in", 900))
    created_at = float(flow.get("_created_at") or time.time())
    deadline = created_at + expires_in
    device_code = flow["device_code"]

    while time.time() < deadline:
        time.sleep(interval)
        try:
            status, data, _ = _http_post_form(
                token_url,
                {
                    "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
                    "client_id": client_id,
                    "device_code": device_code,
                },
                timeout=20,
            )
        except Exception:
            continue

        if 200 <= status < 300 and "access_token" in data:
            cache_obj = {
                "AccessToken": {
                    "default": {
                        "secret": data["access_token"],
                        "expires_on": str(int(time.time()) + int(data.get("expires_in", 3600))),
                    }
                },
                "RefreshToken": {
                    "default": {
                        "secret": data.get("refresh_token", ""),
                    }
                },
                "client_id": client_id,
                "authority": authority,
            }
            for target_path in (CACHE_PATH, CACHE_JSON_PATH):
                try:
                    with open(target_path, "w", encoding="utf-8") as f:
                        json.dump(cache_obj, f, ensure_ascii=False, indent=2)
                except Exception:
                    pass
            try:
                if os.path.isfile(PENDING_PATH):
                    os.remove(PENDING_PATH)
            except Exception:
                pass
            print(f"✅ Xác thực thành công! Đã lưu token cache tại: {CACHE_JSON_PATH}", flush=True)
            return

        err = data.get("error")
        if err in ("authorization_pending", "slow_down"):
            if err == "slow_down":
                interval += 2
            continue
        print(f"❌ Xác thực thất bại: {data.get('error_description') or err}", file=sys.stderr, flush=True)
        sys.exit(1)

    print("❌ Đã hết thời gian chờ xác thực Device Code.", file=sys.stderr, flush=True)
    sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Microsoft 365 Device Code Login")
    parser.add_argument("--init-only", action="store_true", help="Khởi tạo mã Device Code, in ra màn hình và chạy nền tiến trình chờ xác thực")
    parser.add_argument("--poll-pending", action="store_true", help="Chờ người dùng xác thực từ file pending")
    args = parser.parse_args()

    client_id = os.environ.get("MS_GRAPH_CLIENT_ID") or CLIENT_ID_DEFAULT
    authority = (os.environ.get("MS_GRAPH_AUTHORITY") or AUTHORITY_DEFAULT).rstrip("/")

    if args.poll_pending:
        if not os.path.isfile(PENDING_PATH):
            print("❌ Không tìm thấy phiên Device Code đang chờ.", file=sys.stderr)
            sys.exit(1)
        with open(PENDING_PATH, "r", encoding="utf-8") as f:
            flow = json.load(f)
        poll_flow(flow)
        return

    flow = init_flow(client_id, authority)
    if args.init_only:
        # Tự động khởi chạy tiến trình nền (detached) để chờ user nhập mã và lưu token_cache.bin
        log_path = os.path.join(DATA_DIR, "device_flow_poll.log")
        with open(log_path, "w", encoding="utf-8") as log_fp:
            subprocess.Popen(
                [sys.executable, os.path.abspath(__file__), "--poll-pending"],
                stdout=log_fp,
                stderr=log_fp,
                stdin=subprocess.DEVNULL,
                start_new_session=True,
            )
        print("⏳ Hệ thống đang chạy nền chờ bạn xác thực trên trình duyệt...", flush=True)
        return

    poll_flow(flow)


if __name__ == "__main__":
    main()

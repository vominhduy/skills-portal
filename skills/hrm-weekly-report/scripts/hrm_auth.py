"""Đăng nhập hệ thống HRM (apis.fpt.net) bằng username/password để lấy access_token.

Port từ `.claude/skills/hrm-weekly-report/scripts/hrm_auth.py` - giữ nguyên hành vi.
Credential đọc từ biến môi trường (HRM_USERNAME/HRM_PASSWORD) do webapp inject.
"""

import os

import requests

LOGIN_URL = "https://apis.fpt.net/hrm/administration-service/api/auth"

# apis.fpt.net không qua được proxy công ty (DNS fail) - mặc định gọi trực tiếp,
# trừ khi được chỉ định proxy nội bộ / VPN proxy qua HRM_PROXY_URL.
NO_PROXY = {"http": None, "https": None}


def get_hrm_proxies():
    proxy_url = os.environ.get("HRM_PROXY_URL", "").strip()
    if proxy_url:
        return {"http": proxy_url, "https": proxy_url}
    return NO_PROXY


def get_login_url():
    custom_base = os.environ.get("HRM_API_BASE") or os.environ.get("HRM_BASE_URL", "").strip()
    if custom_base:
        return f"{custom_base.rstrip('/')}/hrm/administration-service/api/auth"
    return LOGIN_URL


def _decrypt_password_if_needed(password):
    if password:
        return password

    enc_pw = os.environ.get("HRM_PASSWORD_ENC")
    enc_key = os.environ.get("CREDENTIALS_ENCRYPTION_KEY")

    if not enc_pw or not enc_key:
        # Thử đọc trực tiếp .env ở root project nếu chưa inject vào env
        try:
            from pathlib import Path
            for parent in [Path(__file__).resolve().parents[2], Path(__file__).resolve().parents[3]]:
                env_file = parent / ".env"
                if env_file.exists():
                    with open(env_file, "r", encoding="utf-8") as f:
                        for line in f:
                            line = line.strip()
                            if line and not line.startswith("#") and "=" in line:
                                k, v = line.split("=", 1)
                                k, v = k.strip(), v.strip().strip("'\"")
                                if k == "HRM_PASSWORD" and not password:
                                    password = v
                                elif k == "HRM_PASSWORD_ENC" and not enc_pw:
                                    enc_pw = v
                                elif k == "CREDENTIALS_ENCRYPTION_KEY" and not enc_key:
                                    enc_key = v
                    break
        except Exception:
            pass

    if password:
        return password

    if enc_pw and enc_key:
        try:
            import base64
            import hashlib
            from cryptography.hazmat.primitives.ciphers.aead import AESGCM

            if len(enc_key) == 64:
                key_bytes = bytes.fromhex(enc_key)
            else:
                key_bytes = hashlib.sha256(enc_key.encode("utf-8")).digest()
            buf = base64.b64decode(enc_pw)
            if len(buf) >= 28:
                try:
                    # Layout 1: iv (12 bytes) + tag (16 bytes) + ciphertext (crypto-util.js chuẩn)
                    iv = buf[:12]
                    tag = buf[12:28]
                    ct = buf[28:]
                    aes = AESGCM(key_bytes)
                    return aes.decrypt(iv, ct + tag, None).decode("utf-8")
                except Exception:
                    # Layout 2: iv (16 bytes) + tag (16 bytes) + ciphertext
                    if len(buf) >= 32:
                        from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
                        iv = buf[:16]
                        tag = buf[16:32]
                        ct = buf[32:]
                        cipher = Cipher(algorithms.AES(key_bytes), modes.GCM(iv, tag))
                        decryptor = cipher.decryptor()
                        return (decryptor.update(ct) + decryptor.finalize()).decode("utf-8")
        except Exception:
            pass

    return None


def login(username=None, password=None, login_url=None):
    """Trả về access_token (str).

    username/password mặc định lấy từ env HRM_USERNAME/HRM_PASSWORD nếu không truyền.
    """
    username = username or os.environ.get("HRM_USERNAME")
    password = password or _decrypt_password_if_needed(os.environ.get("HRM_PASSWORD"))
    if not username or not password:
        raise ValueError("Thiếu HRM_USERNAME/HRM_PASSWORD (chưa cấu hình trong .env).")

    res = requests.post(
        login_url or get_login_url(),
        json={"userName": username, "password": password},
        proxies=get_hrm_proxies(),
    )
    res.raise_for_status()
    body = res.json()

    if body.get("statusCode") != 200 or not body.get("data"):
        raise RuntimeError(f"Login HRM thất bại: {body.get('message') or body}")

    token = body["data"].get("accessToken")
    if not token:
        raise RuntimeError(f"Không tìm thấy accessToken trong response: {body}")
    return token

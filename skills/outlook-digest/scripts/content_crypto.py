"""AES-256-GCM vault - tương thích format crypto-util.js (webapp)."""
from __future__ import annotations

import base64
import os
import sys

from cryptography.hazmat.primitives.ciphers.aead import AESGCM


def _load_key() -> bytes:
    raw = (os.environ.get("OUTLOOK_VAULT_KEY") or os.environ.get("GMAIL_VAULT_KEY") or "").strip()
    if not raw:
        print("❌ Thiếu OUTLOOK_VAULT_KEY - server chưa inject vault key.", file=sys.stderr)
        sys.exit(2)
    try:
        key = bytes.fromhex(raw)
    except ValueError:
        print("❌ OUTLOOK_VAULT_KEY không hợp lệ (cần 64 ký tự hex).", file=sys.stderr)
        sys.exit(2)
    if len(key) != 32:
        print("❌ OUTLOOK_VAULT_KEY phải là 32 byte (64 hex).", file=sys.stderr)
        sys.exit(2)
    return key


def encrypt_text(plain: str) -> str:
    key = _load_key()
    iv = os.urandom(12)
    aes = AESGCM(key)
    ct = aes.encrypt(iv, plain.encode("utf-8"), None)
    # Layout: iv(12) + tag(16) + ciphertext - giống crypto-util.js
    tag, body = ct[-16:], ct[:-16]
    blob = iv + tag + body
    return base64.b64encode(blob).decode("ascii")


def decrypt_text(blob_b64: str) -> str:
    key = _load_key()
    buf = base64.b64decode(blob_b64)
    iv, tag, body = buf[:12], buf[12:28], buf[28:]
    aes = AESGCM(key)
    pt = aes.decrypt(iv, body + tag, None)
    return pt.decode("utf-8")

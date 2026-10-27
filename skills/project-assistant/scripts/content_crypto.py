"""AES-256-GCM vault - tương thích format crypto-util.js (webapp)."""
from __future__ import annotations

import base64
import hashlib
import hmac
import os
import sys

try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM  # type: ignore
except ImportError:
    AESGCM = None

_EPHEMERAL_KEY_HEX: str | None = None


def _load_key() -> bytes:
    global _EPHEMERAL_KEY_HEX
    raw = (os.environ.get("OUTLOOK_VAULT_KEY") or os.environ.get("GMAIL_VAULT_KEY") or "").strip()
    if not raw:
        if not _EPHEMERAL_KEY_HEX:
            _EPHEMERAL_KEY_HEX = os.urandom(32).hex()
            os.environ["OUTLOOK_VAULT_KEY"] = _EPHEMERAL_KEY_HEX
        raw = _EPHEMERAL_KEY_HEX
    try:
        key = bytes.fromhex(raw)
    except ValueError:
        print("❌ OUTLOOK_VAULT_KEY không hợp lệ (cần 64 ký tự hex).", file=sys.stderr)
        sys.exit(2)
    if len(key) != 32:
        print("❌ OUTLOOK_VAULT_KEY phải là 32 byte (64 hex).", file=sys.stderr)
        sys.exit(2)
    return key


def _stream_xor(key: bytes, iv: bytes, data: bytes) -> bytes:
    out = bytearray(len(data))
    block_idx = 0
    offset = 0
    while offset < len(data):
        ks = hashlib.sha256(key + iv + block_idx.to_bytes(4, "big")).digest()
        take = min(len(ks), len(data) - offset)
        for i in range(take):
            out[offset + i] = data[offset + i] ^ ks[i]
        offset += take
        block_idx += 1
    return bytes(out)


def encrypt_text(plain: str) -> str:
    key = _load_key()
    iv = os.urandom(12)
    pt = plain.encode("utf-8")
    if AESGCM is not None:
        aes = AESGCM(key)
        ct = aes.encrypt(iv, pt, None)
        # Layout: iv(12) + tag(16) + ciphertext - giống crypto-util.js
        tag, body = ct[-16:], ct[:-16]
    else:
        body = _stream_xor(key, iv, pt)
        tag = hmac.new(key, iv + body, hashlib.sha256).digest()[:16]
    blob = iv + tag + body
    return base64.b64encode(blob).decode("ascii")


def decrypt_text(blob_b64: str) -> str:
    key = _load_key()
    buf = base64.b64decode(blob_b64)
    iv, tag, body = buf[:12], buf[12:28], buf[28:]
    if AESGCM is not None:
        aes = AESGCM(key)
        pt = aes.decrypt(iv, body + tag, None)
    else:
        expected_tag = hmac.new(key, iv + body, hashlib.sha256).digest()[:16]
        if not hmac.compare_digest(tag, expected_tag):
            raise ValueError("Authentication tag mismatch")
        pt = _stream_xor(key, iv, body)
    return pt.decode("utf-8")


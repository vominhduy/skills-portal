"""Phát hiện và redact nội dung nhạy cảm trong email trước khi AI đọc."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Tuple


@dataclass
class RedactionItem:
    ref: str
    reason: str
    original: str


@dataclass
class RedactionResult:
    safe_text: str
    items: List[RedactionItem] = field(default_factory=list)
    is_sensitive: bool = False


PATTERNS: List[Tuple[str, re.Pattern[str]]] = [
    ("private_key", re.compile(r"-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----[\s\S]*?-----END (?:RSA |OPENSSH |EC )?PRIVATE KEY-----", re.I)),
    ("api_token", re.compile(r"\b(?:sk-[A-Za-z0-9]{20,}|xox[baprs]-[A-Za-z0-9-]{10,}|ghp_[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16})\b")),
    ("bearer_token", re.compile(r"\bBearer\s+[A-Za-z0-9\-._~+/]+=*\b", re.I)),
    ("password_field", re.compile(r"(?i)(?:password|passwd|pwd|mật\s*khẩu|mk)\s*[:=]\s*\S+")),
    ("otp_code", re.compile(r"(?i)(?:otp|mã\s*(?:xác\s*thực|otp|pin)|verification\s*code)\s*[:#]?\s*\d{4,8}\b")),
    ("credit_card", re.compile(r"\b(?:\d[ -]*?){13,19}\b")),
    ("cccd_id", re.compile(r"\b\d{9,12}\b")),
    ("bank_account", re.compile(r"(?i)(?:stk|số\s*tài\s*khoản|account\s*(?:no|number)?)\s*[:#]?\s*\d{6,20}")),
    ("salary_amount", re.compile(r"(?i)(?:lương|salary|thu\s*nhập|compensation)\s*[:#]?\s*[\d.,]+\s*(?:vnd|usd|triệu|tr)?")),
    ("secret_field", re.compile(r"(?i)(?:api[_-]?key|client[_-]?secret|access[_-]?token|refresh[_-]?token)\s*[:=]\s*\S+")),
]

SENSITIVE_SUBJECT_RE = re.compile(
    r"(?i)\b(?:mật\s*khẩu|password|otp|payroll|lương|salary|hợp\s*đồng\s*bảo\s*mật|"
    r"confidential|nội\s*bộ\s*mt|internal\s*only|nda|bank\s*transfer|chuyển\s*khoản)\b"
)


def _luhn_ok(digits: str) -> bool:
    if len(digits) < 13:
        return False
    total = 0
    rev = digits[::-1]
    for i, ch in enumerate(rev):
        n = int(ch)
        if i % 2 == 1:
            n *= 2
            if n > 9:
                n -= 9
        total += n
    return total % 10 == 0


def _validate_match(reason: str, text: str) -> bool:
    if reason != "credit_card":
        return True
    digits = re.sub(r"\D", "", text)
    return 13 <= len(digits) <= 19 and _luhn_ok(digits)


def redact_text(text: str, ref_prefix: str = "sens") -> RedactionResult:
    if not text:
        return RedactionResult(safe_text="", items=[], is_sensitive=False)

    items: List[RedactionItem] = []
    safe = text
    counter = 0

    for reason, pattern in PATTERNS:
        for m in list(pattern.finditer(safe)):
            chunk = m.group(0)
            if not _validate_match(reason, chunk):
                continue
            counter += 1
            ref = f"{ref_prefix}#{counter}"
            items.append(RedactionItem(ref=ref, reason=reason, original=chunk))
            safe = safe[: m.start()] + f"[REDACTED:{ref}:{reason}]" + safe[m.end() :]

    return RedactionResult(
        safe_text=safe,
        items=items,
        is_sensitive=bool(items),
    )


def subject_is_sensitive(subject: str) -> bool:
    return bool(SENSITIVE_SUBJECT_RE.search(subject or ""))


def process_message(subject: str, body: str, snippet: str, msg_id: str) -> dict:
    subj_res = redact_text(subject, ref_prefix=f"{msg_id}_subj")
    vault_items = list(subj_res.items)

    if subject_is_sensitive(subject):
        reason = "sensitive_subject"
        if body:
            ref_b = f"{msg_id}_body#1"
            vault_items.append(RedactionItem(ref=ref_b, reason=reason, original=body))
        if snippet:
            ref_s = f"{msg_id}_snip#1"
            vault_items.append(RedactionItem(ref=ref_s, reason=reason, original=snippet))
        return {
            "safe_subject": subj_res.safe_text,
            "safe_body": f"[REDACTED:{msg_id}_body#1:{reason}]",
            "safe_snippet": f"[REDACTED:{msg_id}_snip#1:{reason}]",
            "vault_items": [
                {"ref": item.ref, "reason": item.reason, "original": item.original}
                for item in vault_items
            ],
            "is_sensitive": True,
        }

    body_res = redact_text(body, ref_prefix=f"{msg_id}_body")
    snip_res = redact_text(snippet, ref_prefix=f"{msg_id}_snip")
    vault_items.extend(body_res.items)
    vault_items.extend(snip_res.items)

    return {
        "safe_subject": subj_res.safe_text,
        "safe_body": body_res.safe_text,
        "safe_snippet": snip_res.safe_text,
        "vault_items": [
            {"ref": item.ref, "reason": item.reason, "original": item.original}
            for item in vault_items
        ],
        "is_sensitive": bool(vault_items),
    }

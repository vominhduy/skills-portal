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


# (reason, compiled regex) - thứ tự ưu tiên
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

# Subject/from chứa keyword nhạy cảm → redact toàn bộ body
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
    """Trả về dict gồm safe fields + vault items.

    Subject luôn được giữ visible (chỉ redact pattern secret thực sự trong subject
    như API key/password) để AI/user nhận diện được email. Khi subject chứa keyword
    nhạy cảm (password, payroll, lương...) → redact toàn body/snippet, nhưng vẫn giữ
    subject (đã qua redact_text) cho phép hiển thị.
    """
    prefix = f"msg-{msg_id[:8]}"
    subj_r = redact_text(subject or "", f"{prefix}-subj")

    if subject_is_sensitive(subject):
        # Subject nhạy cảm → redact toàn body/snippet, nhưng GIỮ subject visible
        # (chỉ redact pattern secret thực sự trong subject qua redact_text ở trên).
        return {
            "subject_safe": subj_r.safe_text or "(no subject)",
            "body_safe": "[REDACTED:full_body:sensitive_subject]",
            "snippet_safe": "[REDACTED:snippet:sensitive_subject]",
            "vault_items": [
                {"ref": f"{prefix}-full", "reason": "sensitive_subject", "original": body or snippet or subject},
                *[{"ref": it.ref, "reason": it.reason, "original": it.original} for it in subj_r.items],
            ],
            "is_sensitive": True,
        }

    body_r = redact_text(body or "", f"{prefix}-body")
    snip_r = redact_text(snippet or "", f"{prefix}-snip")

    vault_items = []
    for r in (subj_r, body_r, snip_r):
        for item in r.items:
            vault_items.append({"ref": item.ref, "reason": item.reason, "original": item.original})

    return {
        "subject_safe": subj_r.safe_text,
        "body_safe": body_r.safe_text,
        "snippet_safe": snip_r.safe_text,
        "vault_items": vault_items,
        "is_sensitive": bool(vault_items) or subj_r.is_sensitive or body_r.is_sensitive,
    }

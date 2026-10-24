#!/usr/bin/env python3
"""Shared date util - parse đa format (dd/mm/yyyy + ISO + dd-mm-yyyy), thống nhất cho mọi skill.
Thay vì mỗi script tự strptime/format khác nhau.
"""
from __future__ import annotations
import re
from datetime import datetime, date
from typing import Optional

_ISO_RE = re.compile(r"^(\d{4})-(\d{1,2})-(\d{1,2})")
_DMY_RE = re.compile(r"^(\d{1,2})[/-](\d{1,2})[/-](\d{4})")


def parse_date(value, default: Optional[date] = None) -> Optional[date]:
    """Parse date từ string - hỗ trợ ISO (YYYY-MM-DD) + DMY (DD/MM/YYYY hoặc DD-MM-YYYY)."""
    if value is None:
        return default
    if isinstance(value, date):
        return value
    if isinstance(value, datetime):
        return value.date()
    s = str(value).strip()
    if not s:
        return default
    m = _ISO_RE.match(s)
    if m:
        try:
            return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        except ValueError:
            return default
    m = _DMY_RE.match(s)
    if m:
        try:
            return date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
        except ValueError:
            return default
    return default


def to_iso(d: Optional[date]) -> str:
    return d.isoformat() if d else ""


def to_dmy(d: Optional[date]) -> str:
    return d.strftime("%d/%m/%Y") if d else ""


def today_iso() -> str:
    return date.today().isoformat()

#!/usr/bin/env python3
"""Shared output path helper - dùng $REPORT_OUTPUT_DIR thay hardcode /mnt/user-data/outputs/
hoặc /home/claude/ (fix vi phạm CLAUDE.md:6 cho mọi skill).
"""
from __future__ import annotations
import os
from pathlib import Path

REPORT_OUTPUT_DIR = os.environ.get("REPORT_OUTPUT_DIR", "")
SKILL_DIR = os.environ.get("SKILL_DIR", "")


def output_dir() -> str:
    """Trả về REPORT_OUTPUT_DIR - throw nếu chưa đặt (skill bắt buộc có)."""
    if not REPORT_OUTPUT_DIR:
        raise RuntimeError("Thiếu env REPORT_OUTPUT_DIR - webapp inject khi chạy skill.")
    return REPORT_OUTPUT_DIR


def skill_dir() -> str:
    if not SKILL_DIR:
        raise RuntimeError("Thiếu env SKILL_DIR - webapp inject khi chạy skill.")
    return SKILL_DIR


def ensure_output_dir() -> str:
    d = output_dir()
    Path(d).mkdir(parents=True, exist_ok=True)
    return d


def join_output(*parts: str) -> str:
    """Join path an toàn dưới REPORT_OUTPUT_DIR - chèn path traversal."""
    base = Path(ensure_output_dir()).resolve()
    target = base.joinpath(*parts).resolve()
    if not str(target).startswith(str(base)):
        raise RuntimeError(f"Path traversal chặn: {parts}")
    return str(target)


def safe_name(name: str) -> str:
    """Sanitize tên file - chỉ giữ [A-Za-z0-9._-], thay còn lại bằng '_'."""
    return "".join(c if c.isalnum() or c in "._-" else "_" for c in (name or "output")).strip("._") or "output"

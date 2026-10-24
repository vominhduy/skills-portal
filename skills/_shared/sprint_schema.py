#!/usr/bin/env python3
"""Shared sprint schema + validator - schema thống nhất cho sprint data JSON.
Dùng cho sprint-planning (sprint1_backlog.json).
"""
from __future__ import annotations
from typing import Dict, List, Any

REQUIRED_SPRINT_FIELDS = {"sprint_name", "team_size"}
OPTIONAL_SPRINT_FIELDS = {"start_date", "end_date", "goal", "velocity"}


def validate_sprint_data(data: Dict[str, Any]) -> List[str]:
    """Trả về danh sách lỗi (rỗng nếu hợp lệ). Kiểm tra schema sprint data."""
    errors: List[str] = []
    if not isinstance(data, dict):
        return ["Sprint data phải là dict"]
    for f in REQUIRED_SPRINT_FIELDS:
        if f not in data:
            errors.append(f"Thiếu field bắt buộc: {f}")
    ts = data.get("team_size")
    if ts is not None and (not isinstance(ts, (int, float)) or ts <= 0):
        errors.append("team_size phải là số dương")
    stories = data.get("stories", [])
    if not isinstance(stories, list):
        errors.append("stories phải là list")
    else:
        for i, s in enumerate(stories):
            if not isinstance(s, dict):
                errors.append(f"story[{i}] phải là dict")
                continue
            if "title" not in s and "summary" not in s:
                errors.append(f"story[{i}] thiếu title/summary")
            if "points" in s and not isinstance(s["points"], (int, float)):
                errors.append(f"story[{i}].points phải là số")
            if "status" in s and not isinstance(s["status"], str):
                errors.append(f"story[{i}].status phải là string")
    return errors


def is_valid(data: Dict[str, Any]) -> bool:
    return not validate_sprint_data(data)

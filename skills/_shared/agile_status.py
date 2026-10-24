#!/usr/bin/env python3
"""Shared Agile status mapping - 1 source of truth cho Done/In review/Blocked/Cancelled/Not started.
Gộp STORY_STATUS_MAPPING (sprint_health_scorer) + COMPLETION_STATUS_MAPPING (retrospective_analyzer).
"""
from __future__ import annotations
from typing import Dict, List

# Thống nhất 2 mapping cũ - thêm "cancelled" (retro có) + "in review" (weekly-report).
STATUS_MAPPING: Dict[str, List[str]] = {
    "completed": ["done", "completed", "finished", "resolved", "closed", "achieved"],
    "in_review": ["in review", "review", "ready for review", "in qa", "qa"],
    "in_progress": ["in progress", "in_progress", "ongoing", "working on", "started",
                    "partial", "development", "testing", "dev", "test"],
    "blocked": ["blocked", "stuck", "waiting", "dependent", "impediment"],
    "cancelled": ["cancelled", "dropped", "abandoned", "not needed", "deprioritized"],
    "not_started": ["not started", "pending", "todo", "to do", "planned", "upcoming",
                    "backlog", "new", "open"],
}

# Lookup đảo: status thường → category
_LOWER_TO_CATEGORY = {s.lower(): cat for cat, statuses in STATUS_MAPPING.items() for s in statuses}


def categorize(status: str) -> str:
    """Map 1 status string → category (completed/in_review/in_progress/blocked/cancelled/not_started)."""
    if not status:
        return "not_started"
    s = status.strip().lower()
    return _LOWER_TO_CATEGORY.get(s, "not_started")


def is_done(status: str) -> bool:
    return categorize(status) == "completed"


def is_in_review(status: str) -> bool:
    return categorize(status) == "in_review"


def is_blocked(status: str) -> bool:
    return categorize(status) == "blocked"


def is_cancelled(status: str) -> bool:
    return categorize(status) == "cancelled"


def is_active(status: str) -> bool:
    """Story đang làm (in_progress/in_review/blocked) - chưa done, chưa cancelled."""
    return categorize(status) in ("in_progress", "in_review", "blocked")

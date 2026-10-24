#!/usr/bin/env python3
"""Shared Story Point formula - 1 bản duy nhất (thay vì duplicate trong product-backlog +
sprint-planning/references/backlog-guide.md).

Formula: Story Point = Priority × Complexity
- Priority scale: 1 (thấp) → 3 (cao)
- Complexity scale: 1 (đơn giản) → 5 (phức tạp)
- Fibonacci rounding về {1, 2, 3, 5, 8, 13}
"""
from __future__ import annotations
import math

PRIORITY_SCALE = {1: 1, 2: 2, 3: 3}
COMPLEXITY_SCALE = {1: 1, 2: 2, 3: 3, 4: 5, 5: 8}
FIBONACCI = [1, 2, 3, 5, 8, 13, 21]


def _to_fibonacci(value: float) -> int:
    """Làm tròn lên giá trị Fibonacci gần nhất (không vượt quá 21)."""
    v = max(1, min(21, int(round(value))))
    return min(FIBONACCI, key=lambda f: abs(f - v))


def story_point(priority: int, complexity: int) -> int:
    """Tính Story Point = Priority × Complexity, làm tròn Fibonacci."""
    if priority not in PRIORITY_SCALE:
        raise ValueError(f"Priority phải 1-3, nhận {priority}")
    if complexity not in COMPLEXITY_SCALE:
        raise ValueError(f"Complexity phải 1-5, nhận {complexity}")
    raw = PRIORITY_SCALE[priority] * COMPLEXITY_SCALE[complexity]
    return _to_fibonacci(raw)


def priority_label(priority: int) -> str:
    return {1: "Thấp", 2: "Trung bình", 3: "Cao"}.get(priority, "Không xác định")


def complexity_label(complexity: int) -> str:
    return {1: "Đơn giản", 2: "Dễ", 3: "Trung bình", 4: "Khó", 5: "Phức tạp"}.get(complexity, "Không xác định")

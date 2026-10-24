#!/usr/bin/env python3
"""Generate weekly report Markdown from standardized JSON data (from Jira, Excel, or Google Sheet).

Usage:
    python generate_report_from_json.py --input <data.json> --output-dir <dir> \
        [--sprint-start YYYY-MM-DD] [--sprint-end YYYY-MM-DD] [--today YYYY-MM-DD]

This script reads the standardized JSON output from:
  - weekly_report_generator.py (Jira source)
  - fetch_gsheet_data.py (Google Sheet source)
  - fetch_excel_data.py (Excel source)

And generates a Markdown weekly report with the same format.
"""
import argparse
import json
import os
import re
import shutil
import sys
from datetime import datetime, timezone, timedelta, date
from typing import Dict, List, Optional

VN_TZ = timezone(timedelta(hours=7))

# ─────────────────────── CONSTANTS ───────────────────────
# Phase display names (taskProcess → phase → weight)
PHASE_WEIGHTS = {
    "Requirement": 0.15,
    "Development": 0.50,
    "Testing": 0.15,
    "Deployment": 0.10,
    "Other": 0.10,
}

PHASE_ORDER = list(PHASE_WEIGHTS.keys())

# Done/In review = 100% est cho Actual Progress và RAG duedate-based
PROGRESS_COMPLETE_STATUSES = {"Done", "In review", "In Review"}
RAG_COMPLETE_STATUSES = PROGRESS_COMPLETE_STATUSES

def parse_jira_hours(value) -> float:
    """Chuyển originalEstimate/timeSpent Jira (giây) hoặc giờ đã parse sẵn."""
    if value is None:
        return 0.0
    if isinstance(value, (int, float)):
        v = float(value)
        return round(v / 3600, 2) if v > 48 else v
    return 0.0

def get_estimate_hours(sub: Dict) -> float:
    est = sub.get("original_estimate_h")
    if est:
        return float(est)
    if sub.get("original_estimate") is not None:
        return parse_jira_hours(sub.get("original_estimate"))
    return 0.0

def get_spent_hours(sub: Dict) -> float:
    spent = sub.get("time_spent_h")
    if spent:
        return float(spent)
    if sub.get("time_spent") is not None:
        return parse_jira_hours(sub.get("time_spent"))
    return 0.0

def new_phase_stats() -> Dict:
    return {"est": 0.0, "progress": 0.0, "count": 0, "done_count": 0}

def compute_phase_pct(stats: Dict) -> Optional[float]:
    """% hoàn thành phase. None = phase không có task trong sprint."""
    count = stats["count"]
    if count == 0:
        return None
    est = stats["est"]
    if est > 0:
        return min(round(stats["progress"] / est * 100, 1), 100.0)
    if stats["done_count"] == count:
        return 100.0
    return round(stats["done_count"] / count * 100, 1)

def impute_completed_prior_phases(phase_data: Dict) -> None:
    """Phase trước đã xong (không còn task) nhưng sprint đã sang phase sau → credit 100%."""
    active_indices = [i for i, p in enumerate(PHASE_ORDER) if phase_data[p]["count"] > 0]
    if not active_indices:
        return
    max_active = max(active_indices)
    for i, phase in enumerate(PHASE_ORDER):
        if i >= max_active:
            break
        if phase_data[phase]["count"] == 0:
            phase_data[phase]["pct"] = 100.0
            phase_data[phase]["contribution"] = round(PHASE_WEIGHTS[phase] * 100, 1)
            phase_data[phase]["imputed"] = True

def finalize_weighted_phases(phase_data: Dict) -> float:
    weighted_sum = 0.0
    for phase, weight in PHASE_WEIGHTS.items():
        if phase_data[phase].get("imputed"):
            weighted_sum += phase_data[phase]["contribution"]
            continue
        pct = compute_phase_pct(phase_data[phase])
        if pct is None:
            phase_data[phase]["pct"] = 0.0
            phase_data[phase]["contribution"] = 0.0
            continue
        phase_data[phase]["pct"] = pct
        phase_data[phase]["contribution"] = round(weight * pct, 1)
        weighted_sum += weight * pct
    return round(weighted_sum, 1)

def normalize_status(status: Optional[str]) -> str:
    return (status or "To Do").strip()

def is_progress_complete(status: Optional[str]) -> bool:
    return normalize_status(status) in PROGRESS_COMPLETE_STATUSES

def is_rag_complete(status: Optional[str]) -> bool:
    return normalize_status(status) in RAG_COMPLETE_STATUSES

def rag_label_from_pct(pct: float) -> str:
    if pct >= 80:
        return "On Track 🟢"
    if pct >= 50:
        return "At Risk 🟡"
    return "Off Track 🔴"

def subtask_key(sub: Dict) -> str:
    return str(sub.get("key") or sub.get("id") or "")

def collect_all_subtasks(stories: List, subtasks: List, bugs: List) -> List:
    """Metrics chỉ tính trên sub-task; dedupe key (flat list + nested story.subtasks)."""
    seen: set[str] = set()
    all_subs: List = []
    for sub in list(subtasks or []):
        key = subtask_key(sub)
        if key:
            if key in seen:
                continue
            seen.add(key)
        all_subs.append(sub)
    for story in stories or []:
        for sub in story.get("subtasks") or []:
            key = subtask_key(sub)
            if key:
                if key in seen:
                    continue
                seen.add(key)
            all_subs.append(sub)
    return all_subs

def subtask_progress_hours(sub: Dict) -> tuple[float, float]:
    """Return (progress_hours, estimate_hours) cho một sub-task."""
    est_h = get_estimate_hours(sub)
    spent_h = get_spent_hours(sub)
    if is_progress_complete(sub.get("status")):
        return est_h, est_h
    if est_h > 0:
        return min(spent_h, est_h), est_h
    return spent_h, 0.0

def map_phase(tp) -> str:
    """Map customfield_10790 taskProcess → phase (trọng số cố định)."""
    if not tp:
        return "Other"
    tp_norm = str(tp).strip()
    tp_lower = tp_norm.lower()
    if tp_norm == "Requirement & Design" or "requirement" in tp_lower or "design" in tp_lower:
        return "Requirement"
    if tp_norm == "Coding" or "coding" in tp_lower or tp_lower == "code":
        return "Development"
    if tp_lower in ("testing", "test") or ("test" in tp_lower and "latest" not in tp_lower):
        return "Testing"
    if any(k in tp_lower for k in ("deployment", "deploy", "uat")):
        return "Deployment"
    return "Other"

def subtask_progress_pct(sub: Dict) -> int:
    est_h = get_estimate_hours(sub)
    spent_h = get_spent_hours(sub)
    if est_h > 0:
        return min(100, round(spent_h / est_h * 100))
    return 0

def subtask_status_tag(sub: Dict) -> str:
    if is_progress_complete(sub.get("status")):
        return "(Done)"
    est_h = get_estimate_hours(sub)
    spent_h = get_spent_hours(sub)
    status = normalize_status(sub.get("status"))
    if est_h <= 0 and spent_h <= 0 and status in ("To Do", "Open", "Backlog"):
        return "(Will do)"
    return f"({subtask_progress_pct(sub)}%)"

def subtask_is_at_risk(sub: Dict, today: date) -> bool:
    due = parse_date(sub.get("due_date"))
    return bool(due and due <= today and not is_rag_complete(sub.get("status")))

def subtask_belongs_done(sub: Dict, cycle_start: date, cycle_end: date) -> bool:
    if not is_progress_complete(sub.get("status")):
        return False
    due = parse_date(sub.get("due_date"))
    if due:
        return cycle_start <= due <= cycle_end
    return True

def subtask_belongs_doing(
    sub: Dict,
    cycle_start: date,
    cycle_end: date,
    next_start: date,
    next_end: date,
) -> bool:
    if is_progress_complete(sub.get("status")):
        return False
    due = parse_date(sub.get("due_date"))
    if due:
        if cycle_start <= due <= cycle_end:
            return True
        if next_start <= due <= next_end:
            return True
        if due <= cycle_end:
            return True
        return False
    return True

def format_assignees(items: List[Dict]) -> str:
    names: List[str] = []
    seen: set[str] = set()
    for item in items:
        a = (item.get("assignee") or "").strip()
        if a and a != "Unassigned" and a not in seen:
            seen.add(a)
            names.append(a)
    return ", ".join(names) if names else "Unassigned"


def cluster_title_from_story(story: Dict) -> str:
    """Tên cụm nghiệp vụ từ story summary - không dùng Jira key."""
    s = (story.get("summary") or "Khác").strip()
    lower = s.lower()
    if "core engine" in lower:
        m = re.search(r"core engine[^;,]*", s, re.I)
        if m:
            title = m.group(0).strip()
            if "zns" not in title.lower() and "zns" in lower:
                title += " ZNS"
            return title
    if lower.startswith("ba:") and "uat" in lower:
        return "BA: UAT Scenario & Demo QC"
    if "kick-off" in lower or ("daily progress" in lower and "sprint planning" in lower):
        return "Kick-off & Daily Progress"
    if "qc test" in lower or (lower.startswith("qc ") and "sprint" in lower):
        return "QC Nghiệp vụ Sprint 1"
    if "import" in lower and ("zns" in lower or "oracle" in lower):
        return "Import ZNS/Table Oracle"
    if "công trực" in lower:
        return "Công trực"
    if "đồng bộ" in lower and "ihub" in lower:
        return "Job đồng bộ IHUB"
    if "user acceptance" in lower or ("uat" in lower and "sign-off" in lower):
        return "User Acceptance Testing"
    parts = [p.strip() for p in re.split(r"[;]", s) if p.strip()]
    if len(parts) >= 2:
        pick = parts[-1] if len(parts[-1]) <= 55 else parts[0]
        return pick
    return s


def shorten_subtask_phrase(summary: str) -> str:
    t = (summary or "").strip()
    t = re.sub(r"^(Implement|Unit Test|Tạo|Viết|Demo\s*&?\s*|Gen)\s+", "", t, flags=re.I)
    return t


def summarize_done_subtasks(subs: List[Dict]) -> str:
    phrases = [shorten_subtask_phrase(s.get("summary") or "") for s in subs if s.get("summary")]
    phrases = [p for p in phrases if p]
    if not phrases:
        return "Hoàn thành"
    if len(phrases) == 1:
        text = phrases[0]
        if "daily progress" in text.lower():
            return f"{text} tuần này hoàn tất"
        return text
    return "; ".join(phrases)


def to_done_outcome_phrase(phrase: str) -> str:
    """Chuyển tên sub-task sang câu kết quả nghiệp vụ cho PO/PMO."""
    p = (phrase or "").strip()
    if not p:
        return "Hoàn thành theo kế hoạch"
    lower = p.lower()
    if any(lower.startswith(s) for s in ("hoàn thành", "đã ", "hoàn tất", "xong ")):
        return p[0].upper() + p[1:] if len(p) > 1 else p.upper()
    if "daily progress" in lower:
        return f"{p} tuần này hoàn tất"
    verb_map = (
        ("unit test ", "Hoàn tất unit test "),
        ("tạo ", "Đã tạo "),
        ("viết ", "Đã hoàn thành "),
        ("demo ", "Đã demo "),
        ("gen ", "Đã gen "),
        ("implement ", "Đã triển khai "),
    )
    for prefix, outcome in verb_map:
        if lower.startswith(prefix):
            rest = p[len(prefix):].strip()
            return f"{outcome}{rest}" if rest else outcome.strip()
    return f"Hoàn thành {p[0].lower() + p[1:]}" if p else "Hoàn thành"


def unique_preserve_order(items: List[str]) -> List[str]:
    seen: set[str] = set()
    out: List[str] = []
    for item in items:
        key = item.lower().strip()
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(item)
    return out


def summarize_done_subtasks_pmo(subs: List[Dict]) -> str:
    """Một câu kết quả nghiệp vụ gộp sub-task - không liệt kê từng dòng."""
    outcomes = unique_preserve_order([
        to_done_outcome_phrase(shorten_subtask_phrase(s.get("summary") or ""))
        for s in subs
        if s.get("summary")
    ])
    outcomes = [o for o in outcomes if o]
    if not outcomes:
        return "Hoàn thành theo kế hoạch tuần"
    if len(outcomes) == 1:
        return outcomes[0]
    merged = "; ".join(outcomes)
    if len(merged) > 130:
        merged = "; ".join(outcomes[:2])
        if len(outcomes) > 2:
            merged += " và các hạng mục liên quan"
    return merged


def group_doing_by_parent(
    doing_items: List[tuple[int, int, str, Dict]],
) -> Dict[str, List[Dict]]:
    grouped: Dict[str, List[Dict]] = {}
    for _, _, parent, sub in sorted(doing_items, key=lambda x: (x[0], x[1], x[2])):
        grouped.setdefault(parent, []).append(sub)
    return grouped


def summarize_doing_cluster_pmo(subs: List[Dict], today: date) -> str:
    """Một câu tiến độ nghiệp vụ gộp sub-task trong cùng cụm."""
    if not subs:
        return "Đang thực hiện"
    at_risk = [s for s in subs if subtask_is_at_risk(s, today)]
    if at_risk and len(at_risk) == len(subs):
        due_dates = sorted(
            {parse_date(s.get("due_date")) for s in at_risk if parse_date(s.get("due_date"))},
        )
        if due_dates:
            due_str = ", ".join(d.strftime("%d/%m") for d in due_dates[:2])
            return f"Chưa khởi động, quá hạn {due_str}"
        return "Chưa khởi động"

    parts: List[str] = []
    for sub in subs:
        phrase = shorten_subtask_phrase(sub.get("summary") or "Task")
        due = parse_date(sub.get("due_date"))
        due_str = due.strftime("%d/%m") if due else ""
        if subtask_is_at_risk(sub, today):
            suffix = f", quá hạn {due_str}" if due_str else ""
            parts.append(f"{phrase} - chưa bắt đầu{suffix}")
        elif subtask_progress_pct(sub) > 0:
            parts.append(f"{phrase} - đang thực hiện")
        elif due_str:
            parts.append(f"{phrase} - kế hoạch {due_str}")
        else:
            parts.append(phrase)

    parts = unique_preserve_order(parts)
    if len(parts) == 1:
        return parts[0]
    return "; ".join(parts[:3])


def build_executive_snapshot(analysis: Dict, sprint_name: str) -> List[str]:
    day_x = analysis["elapsed_days"]
    day_total = analysis["total_days"]
    return [
        f"Sprint: {sprint_name} · Ngày {day_x}/{day_total}",
        (
            f"Tóm tắt: {analysis['health']} · SPI {analysis['spi']} · "
            f"Thực tế {analysis['actual_progress_weighted']}% / "
            f"Kế hoạch {analysis['planned_progress']}% · RAG {analysis['rag_pct']}%"
        ),
        "",
    ]


def sprint_short_label(sprint_name: str) -> str:
    m = re.search(r"Sprint\s+(\d+)", sprint_name or "", re.I)
    return f"Sprint {m.group(1)}" if m else "Sprint"


def collect_pmo_match_text(cluster_title: str, subs: List[Dict]) -> str:
    parts = [cluster_title or ""]
    for sub in subs or []:
        parts.append(sub.get("summary") or "")
    return " ".join(parts).lower()


def cluster_title_for_pmo(story: Optional[Dict], subs: List[Dict]) -> str:
    """Tên cụm cho .txt PMO - lấy từ story summary thực tế, không heuristic FSAL."""
    if story and (story.get("summary") or "").strip():
        return story["summary"].strip()
    if subs:
        return shorten_subtask_phrase(subs[0].get("summary") or "Khác")
    return "Khác"


PMO_CATEGORY_ORDER = (
    ("development", "Development"),
    ("ba_qc", "BA & QC"),
    ("qc_uat", "QC & UAT"),
)


def classify_pmo_category(text: str, section: str = "done") -> str:
    """Phân nhóm PO/PMO theo nội dung thực tế - không dùng template cố định theo dự án."""
    t = (text or "").lower()
    if section == "done" and any(k in t for k in ("kick-off", "daily progress", "sprint planning")):
        return "skip"
    if any(k in t for k in (
        "ba:", "uat scenario", "demo qc", "qc nghiệp", "đọc urd", "viết test case",
        "clear nghiệp vụ", "testcase và review",
    )):
        return "ba_qc"
    if section == "doing" and any(k in t for k in (
        "uat planning", "tổ chức uat", "theo dõi uat", "user acceptance",
        "qc testing", "update tc", "setup data", "test case",
    )):
        return "qc_uat"
    return "development"


def compose_pmo_done_bullet(title: str, subs: List[Dict]) -> str:
    """Một bullet Done từ cụm thực tế - title + kết quả gộp sub-task."""
    title = (title or "Khác").strip()
    detail = summarize_done_subtasks_pmo(subs)
    if not detail or detail in ("Hoàn thành theo kế hoạch tuần", "Hoàn thành"):
        return title
    if title.lower() in detail.lower():
        return detail
    if detail.lower() in title.lower():
        return title
    combined = f"{title} - {detail}"
    return combined if len(combined) <= 100 else title


def compose_pmo_doing_phrase(sub: Dict, cluster_title: str, today: date) -> str:
    """Một cụm từ Doing từ sub-task thực tế - không chèn mốc due date."""
    phrase = shorten_subtask_phrase(sub.get("summary") or cluster_title or "Task")
    return phrase


def consolidate_pmo_bullets(phrases: List[str], max_bullets: int = 2, max_len: int = 110) -> List[str]:
    """Gom nhiều cụm thành vài bullet - nội dung lấy từ sprint, không template FSAL."""
    cleaned = unique_preserve_order([p.strip() for p in phrases if p and p.strip()])
    if not cleaned:
        return []
    if len(cleaned) <= max_bullets:
        return cleaned
    chunk = max(1, (len(cleaned) + max_bullets - 1) // max_bullets)
    out: List[str] = []
    for i in range(0, len(cleaned), chunk):
        part = cleaned[i:i + chunk]
        merged = "; ".join(part)
        if len(merged) > max_len:
            merged = "; ".join(part[:2])
            if len(part) > 2:
                merged += " và các hạng mục liên quan"
        out.append(merged)
        if len(out) >= max_bullets:
            break
    return out[:max_bullets]


def build_done_pmo_bullets(
    done_by_parent: Dict[str, List[Dict]],
    story_map: Dict[str, Dict],
    sprint_name: str,
) -> Dict[str, List[str]]:
    """Gom Done thành vài bullet theo nhóm PO/PMO - nội dung từ cụm sprint."""
    by_cat: Dict[str, List[str]] = {cat: [] for cat, _ in PMO_CATEGORY_ORDER}

    for parent in sorted(done_by_parent.keys()):
        subs = done_by_parent[parent]
        story = story_map.get(parent) if parent != "_orphan" else None
        title = (
            cluster_title_for_pmo(story, subs)
            if story or subs
            else "Khác"
        )
        text = collect_pmo_match_text(title, subs)
        cat = classify_pmo_category(text, "done")
        if cat == "skip":
            continue
        by_cat[cat].append(compose_pmo_done_bullet(title, subs))

    return {
        cat: consolidate_pmo_bullets(by_cat[cat], max_bullets=2)
        for cat, _ in PMO_CATEGORY_ORDER
    }


def build_doing_pmo_bullets(
    doing_items: List[tuple[int, int, str, Dict]],
    story_map: Dict[str, Dict],
    today: date,
) -> Dict[str, List[str]]:
    """Gom Doing/Will do thành vài bullet theo nhóm PO/PMO - nội dung từ sub-task sprint."""
    by_cat: Dict[str, List[str]] = {cat: [] for cat, _ in PMO_CATEGORY_ORDER}

    for _, _, parent, sub in sorted(doing_items, key=lambda x: (x[0], x[1], x[2])):
        story = story_map.get(parent) if parent != "_orphan" else None
        cluster = (
            cluster_title_for_pmo(story, [sub])
            if story or sub
            else shorten_subtask_phrase(sub.get("summary") or "Khác")
        )
        text = collect_pmo_match_text(cluster, [sub])
        cat = classify_pmo_category(text, "doing")
        by_cat[cat].append(compose_pmo_doing_phrase(sub, cluster, today))

    return {
        cat: consolidate_pmo_bullets(by_cat[cat], max_bullets=2)
        for cat, _ in PMO_CATEGORY_ORDER
    }


def format_pmo_grouped_section(
    section_title: str,
    bullets_by_cat: Dict[str, List[str]],
) -> List[str]:
    lines = [section_title, ""]
    has_content = False
    for cat_id, cat_label in PMO_CATEGORY_ORDER:
        items = bullets_by_cat.get(cat_id) or []
        if not items:
            continue
        has_content = True
        lines.append(cat_label)
        lines.append("")
        for item in items:
            lines.append(f"* {item}")
        lines.append("")
    if not has_content:
        lines.append("  (Không có)")
        lines.append("")
    return lines


def build_risks_txt_lines_pmo(
    analysis: Dict,
    doing_items: List[tuple[int, int, str, Dict]],
    today: date,
) -> List[str]:
    risks: List[str] = []
    at_risk = [sub for _, _, _, sub in doing_items if subtask_is_at_risk(sub, today)]
    if at_risk:
        due_dates = sorted(
            {parse_date(s.get("due_date")) for s in at_risk if parse_date(s.get("due_date"))},
        )
        due_str = due_dates[0].strftime("%d/%m") if due_dates else ""
        suffix = f" {due_str}" if due_str else ""
        risks.append(f"{len(at_risk)} hạng mục 0% đang quá hạn{suffix}")

    has_qc_uat = any(
        any(k in (sub.get("summary") or "").lower() for k in ("qc", "uat", "test case"))
        for _, _, _, sub in doing_items
    )
    if at_risk and has_qc_uat:
        risks.append("Có nguy cơ ảnh hưởng tiến độ QC và UAT")
    elif analysis.get("spi", 1) < 0.8:
        risks.append(f"Sprint chậm so với kế hoạch (SPI {analysis['spi']})")
    if not risks:
        risks.append("Tiếp tục theo dõi tiến độ các hạng mục còn lại")
    return risks[:3]


def format_subtask_progress_line(sub: Dict, today: Optional[date] = None) -> str:
    """Format 1 subtask cho Section 2: <tên subtask> (<%>%) - <PIC> - <ngày>."""
    title = (sub.get("summary") or "Task").strip()
    pic = (sub.get("assignee") or "Unassigned").strip()

    due = parse_date(sub.get("due_date"))
    date_str = fmt_date(due) if due else "-"

    if is_progress_complete(sub.get("status")):
        pct_str = "100%"
        at_risk_tag = ""
    else:
        pct = subtask_progress_pct(sub)
        pct_str = f"{pct}%"
        at_risk_tag = " ⚠️ At Risk" if (today and subtask_is_at_risk(sub, today)) else ""

    return f"- {title} ({pct_str}){at_risk_tag} - {pic} - {date_str}"


def format_done_cluster_line(story: Optional[Dict], subs: List[Dict]) -> str:
    title = cluster_title_from_story(story) if story else shorten_subtask_phrase(subs[0].get("summary") or "Khác")
    detail = summarize_done_subtasks(subs)
    assignees = format_assignees(subs)
    return f"- {title} - {detail} (Done) - ({assignees})"


def format_doing_line(sub: Dict, today: date) -> str:
    return format_subtask_progress_line(sub, today)


def collect_sprint_progress(
    all_subtasks: List[Dict],
    stories: List[Dict],
    today: date,
) -> tuple[Dict[str, List[Dict]], List[tuple[int, int, str, Dict]], Dict[str, Dict]]:
    """Gom sub-task Done/Doing theo story parent (dedupe theo key)."""
    cycle_start = today - timedelta(days=7)
    cycle_end = today
    next_start = today + timedelta(days=1)
    next_end = today + timedelta(days=7)

    story_map = {(s.get("id") or s.get("key")): s for s in stories or []}
    done_by_parent: Dict[str, List[Dict]] = {}
    doing_items: List[tuple[int, int, str, Dict]] = []
    seen_done: set[str] = set()
    seen_doing: set[str] = set()

    for sub in all_subtasks:
        key = subtask_key(sub)
        parent = sub.get("parent_key") or "_orphan"

        if subtask_belongs_done(sub, cycle_start, cycle_end):
            if key and key in seen_done:
                continue
            if key:
                seen_done.add(key)
            done_by_parent.setdefault(parent, []).append(sub)
        elif subtask_belongs_doing(sub, cycle_start, cycle_end, next_start, next_end):
            if key and key in seen_doing:
                continue
            if key:
                seen_doing.add(key)
            sort_key = 0 if subtask_is_at_risk(sub, today) else 1
            due = parse_date(sub.get("due_date"))
            due_ord = due.toordinal() if due else 999999
            doing_items.append((sort_key, due_ord, parent, sub))

    return done_by_parent, doing_items, story_map


def build_sprint_progress_sections(
    all_subtasks: List[Dict],
    stories: List[Dict],
    today: date,
) -> tuple[str, str, Dict[str, List[Dict]], List[tuple[int, int, str, Dict]], Dict[str, Dict]]:
    """Section 2 MD (chỉ liệt kê sub-task, %, PIC, ngày - không lấy story) + buckets cho .txt."""
    done_by_parent, doing_items, story_map = collect_sprint_progress(all_subtasks, stories, today)

    # Done: Liệt kê trực tiếp từng subtask (%, PIC, ngày), sắp xếp theo due_date tăng dần
    all_done_subs: List[Dict] = []
    for parent in sorted(done_by_parent.keys()):
        all_done_subs.extend(done_by_parent[parent])

    def done_sort_key(sub: Dict) -> int:
        d = parse_date(sub.get("due_date"))
        return d.toordinal() if d else 999999

    done_lines: List[str] = [
        format_subtask_progress_line(sub, today)
        for sub in sorted(all_done_subs, key=done_sort_key)
    ]

    # Doing / Will do: Liệt kê từng subtask theo thứ tự ưu tiên (at risk trước, due_date tăng dần)
    doing_lines: List[str] = []
    for _, _, _, sub in sorted(doing_items, key=lambda x: (x[0], x[1], x[2])):
        doing_lines.append(format_doing_line(sub, today))

    done_str = "\n".join(done_lines) if done_lines else "*(Không có)*"
    doing_str = "\n".join(doing_lines) if doing_lines else "*(Không có)*"
    return done_str, doing_str, done_by_parent, doing_items, story_map


def format_doing_txt_line(sub: Dict, today: date) -> str:
    """Dòng Doing cho .txt - không assignee, không (Will do), không mốc due date."""
    title = shorten_subtask_phrase(sub.get("summary") or "Task")
    pct = subtask_progress_pct(sub)
    if pct > 0:
        return f"  - {title} ({pct}%)"
    return f"  - {title}"


def build_risks_txt_lines(
    analysis: Dict,
    doing_by_parent: Optional[Dict[str, List[Dict]]] = None,
    story_map: Optional[Dict[str, Dict]] = None,
    today: Optional[date] = None,
) -> List[str]:
    risks: List[str] = []
    spi = analysis.get("spi", 1)
    rag = analysis.get("rag_pct", 100)
    actual = analysis.get("actual_progress_weighted", 0)
    planned = analysis.get("planned_progress", 0)

    if spi < 0.8:
        risks.append(
            f"Sprint chậm so với kế hoạch (SPI {spi}, thực tế {actual}% / kế hoạch {planned}%)",
        )
    if rag < 80:
        risks.append(f"Nhiều hạng mục quá hạn chưa hoàn tất (RAG {rag}%)")

    if doing_by_parent and story_map and today:
        overdue_clusters: List[str] = []
        for parent, subs in doing_by_parent.items():
            if not any(subtask_is_at_risk(s, today) for s in subs):
                continue
            story = story_map.get(parent) if parent != "_orphan" else None
            title = (
                cluster_title_from_story(story)
                if story
                else shorten_subtask_phrase(subs[0].get("summary") or "Khác")
            )
            overdue_clusters.append(title)
        if overdue_clusters:
            if len(overdue_clusters) <= 3:
                risks.append(f"Hạng mục chưa khởi động hoặc quá hạn: {', '.join(overdue_clusters)}")
            else:
                risks.append(
                    f"{len(overdue_clusters)} hạng mục chưa khởi động hoặc quá hạn trong sprint",
                )

    if not risks:
        risks.append("Không có rủi ro nghiêm trọng - tiếp tục theo dõi các hạng mục còn lại")
    return risks[:5]


def report_base_name(project_key: str, sprint_name: str) -> str:
    safe_sprint = sprint_name.replace(" ", "_").replace("/", "-")
    return f"{project_key}_{safe_sprint}_report"


def next_report_version(output_dir: str, base: str) -> int:
    """Version tiếp theo - không ghi đè file report cũ (kể cả legacy không _vN)."""
    max_v = 0
    legacy_md = os.path.join(output_dir, f"{base}.md")
    if os.path.isfile(legacy_md):
        max_v = max(max_v, 1)
    pat = re.compile(rf"^{re.escape(base)}_v(\d+)\.md$")
    try:
        for name in os.listdir(output_dir):
            m = pat.match(name)
            if m:
                max_v = max(max_v, int(m.group(1)))
    except OSError:
        pass
    return max_v + 1


TRAILING_CONNECTORS = {
    "và", "&", "cho", "với", "của", "để", "trong", "về", "theo", "kèm",
    "bởi", "do", "tại", "từ", "lên", "xuống", "sang", "vào", "ra", "như",
    "các", "trên", "dưới", "cùng", "qua", "hoặc", "hay", "ở"
}

LEADING_CONNECTORS = {
    "và", "&", "cho", "với", "của", "để", "trong", "về", "theo", "kèm",
    "bởi", "do", "tại", "từ", "lên", "xuống", "sang", "vào", "ra", "như",
    "thực", "hiện", "tiến", "hành", "các", "trên", "ở"
}


def clean_pm_phrase(text: str) -> str:
    """TỔNG HỢP & RÚT GỌN CÔ ĐỌNG (Synthesize PM Deliverable):
    Đảm bảo deliverable cấp Lãnh đạo/PO, câu hoàn chỉnh, súc tích (khoảng 3-8 từ, tối đa <= 12 từ),
    TUYỆT ĐỐI KHÔNG cắt cụt từ/ngữ và KHÔNG để câu dài lê thê."""
    if not text:
        return ""
    
    t = text.strip()
    
    # 1. Bỏ Jira issue key dạng ABC-123 hoặc [ABC-123]
    t = re.sub(r"\[?[A-Z][A-Z0-9]{1,9}-\d+\]?", "", t)
    
    # 2. Bỏ assignee trong ngoặc tròn dạng (DuyVM4, VuNT60) hoặc (Done), (Will do)
    t = re.sub(r"\([^)]*\)", "", t)
    
    # 3. Bỏ tag trong ngoặc vuông như [FE], [BE], [QC], [Dev], [BA], [Staging]
    t = re.sub(r"\[(?:FE|BE|QC|QA|DEV|BA|PM|PO|DESIGN|UI/UX|TEST|STAGING|PROD|HOTFIX|BUG)\]", "", t, flags=re.I)
    
    # 4. Bỏ mốc ngày dạng due DD/MM hoặc DD/MM - DD/MM hoặc Hạn DD/MM
    t = re.sub(r"(?:due|hạn|từ|ngày)\s*\d{1,2}[/-]\d{1,2}(?:\s*-\s*\d{1,2}[/-]\d{1,2})?", "", t, flags=re.I)
    
    # 5. Chuẩn hóa markdown và em-dash
    t = t.replace("**", "").replace("#", "").replace("`", "").replace("—", "-")
    
    # 6. Xử lý dấu phân cách ' - ' hoặc ';'
    if " - " in t:
        parts = [p.strip() for p in t.split(" - ") if p.strip()]
        if len(parts) >= 2:
            t = parts[1] if len(parts[0].split()) <= 2 else parts[0]
        elif parts:
            t = parts[0]
            
    if ";" in t:
        parts = [p.strip() for p in t.split(";") if p.strip()]
        if parts:
            t = parts[0]

    # 7. Rút gọn thuật ngữ và loại bỏ từ đệm rườm rà
    tech_replacements = [
        (r"\btoàn bộ hệ thống cơ sở dữ liệu\b", "hệ thống CSDL"),
        (r"\bhệ thống cơ sở dữ liệu\b", "CSDL"),
        (r"\bcơ sở dữ liệu\b", "CSDL"),
        (r"\bmôi trường\s+(Staging|UAT|Production|Prod|Dev)\b", r"\1"),
        (r"\bmôi trường\b", ""),
        (r"\bfile\s+excel\b", "Excel"),
        (r"\btừ file\b", ""),
        (r"\bcho phép\b", ""),
        (r"\bhoàn thiện\b", ""),
        (r"\bchi tiết\b", ""),
        (r"\bphân hệ\b", ""),
        (r"\bnội bộ\b", ""),
        (r"\btrong quá trình\b", ""),
        (r"\btrong\s+Sprint\s+\d+\b", ""),
        (r"\bthực hiện kiểm thử\b", "Kiểm thử"),
        (r"\bthực hiện\s+Unit\s*test\b", "Unit test"),
        (r"\bthực hiện\b", ""),
        (r"\btiến hành\b", ""),
        (r"\bbản build\b", "build"),
        (r"\btối ưu hóa\b", "Tối ưu"),
        (r"\bhiệu năng hệ thống\b", "hiệu năng"),
        (r"\bbộ nhớ đệm\b", ""),
        (r"\bvới tải\s+\d+[\d,\.]*\s*\w*\b", ""),
        (r"\bvà phân tách bảng\b", ""),
    ]
    for pattern, repl in tech_replacements:
        t = re.sub(pattern, repl, t, flags=re.I)

    # 8. Loại bỏ tiền tố hành vi phụ ở đầu câu
    prefixes = [
        r"^(?:Nghiên cứu\s+URD\s*&?\s*)+(?:Viết\s+)?",
        r"^(?:Phát triển|Xây dựng|Triển khai)\s+(?:tính năng|chức năng|module|giao diện)?\s*",
        r"^(?:Chuẩn bị|Viết|Tạo|Soạn thảo)\s+(?:kịch bản|tài liệu)?\s*(?:và|&)?\s*",
    ]
    for p in prefixes:
        t = re.sub(p, "", t, flags=re.I)

    # 9. Nếu có dấu phẩy (theo sau là khoảng trắng) và câu dài > 8 từ, ưu tiên mệnh đề chính
    if re.search(r",\s+", t) and len(t.split()) > 8:
        parts = [p.strip() for p in re.split(r",\s+", t) if p.strip()]
        if any(k in parts[0].lower() for k in ("hỗ trợ", "nghiên cứu", "đọc hiểu")) and len(parts) > 1:
            t = parts[1]
        else:
            t = parts[0]

    # 10. Lọc bỏ liên từ/giới từ lơ lửng ở ĐẦU câu
    tokens = t.split()
    while tokens and tokens[0].lower() in LEADING_CONNECTORS:
        tokens.pop(0)
    t = " ".join(tokens)

    # 11. Chuẩn hóa ' và ' thành ' & '
    t = re.sub(r"\s+và\s+", " & ", t)
    t = re.sub(r"\s+", " ", t).strip(" .,-:;")

    # 12. Nếu vẫn dài > 12 từ và có ' & ', chỉ lấy vế đầu chính (hoặc vế dài hơn có ý nghĩa)
    words = t.split()
    if len(words) > 12 and " & " in t:
        parts = [p.strip() for p in t.split(" & ") if p.strip()]
        if parts and len(parts[0].split()) >= 3:
            t = parts[0]

    # 13. Dọn dẹp liên từ/giới từ ở ĐUÔI câu
    tokens = t.split()
    while tokens and tokens[-1].lower() in TRAILING_CONNECTORS:
        tokens.pop()

    # 14. Giới hạn độ dài tối đa <= 12 từ (ưu tiên 3-8 từ, không vượt quá 12 từ):
    # nếu dài hơn, cắt tại ranh giới từ an toàn và loại bỏ connectors ở đuôi
    if len(tokens) > 12:
        tokens = tokens[:12]
        while tokens and tokens[-1].lower() in TRAILING_CONNECTORS:
            tokens.pop()

    t = " ".join(tokens).strip(" .,-:;")
    if t:
        t = t[0].upper() + t[1:]
    return t


def generate_pm_sprint_summary_txt(
    analysis: Dict,
    project_key: str,
    sprint_name: str,
    done_by_parent: Dict[str, List[Dict]],
    doing_items: List[tuple[int, int, str, Dict]],
    story_map: Dict[str, Dict],
    output_dir: str,
    version: int,
) -> str:
    """Tạo file .txt PM Sprint Summary chuẩn 100% (Cấu trúc 3) ngay trong pipeline."""
    base = report_base_name(project_key, sprint_name)
    txt_name = f"{base}_v{version}.txt"
    txt_path = os.path.join(output_dir, txt_name)
    
    sprint_start_str = fmt_date(analysis.get("sprint_start")) if analysis.get("sprint_start") else ""
    sprint_end_str = fmt_date(analysis.get("sprint_end")) if analysis.get("sprint_end") else ""
    date_range_str = f" - {sprint_start_str} - {sprint_end_str}" if sprint_start_str and sprint_end_str else ""
    
    lines = [
        "Overall Status",
        f"{project_key} · {sprint_name}{date_range_str}",
        f"- Health: {analysis.get('health', '🟢 On Track')} (SPI = {analysis.get('spi', 1.0)})",
        f"- Tiến độ: {analysis.get('actual_progress_weighted', 0)}% / kế hoạch {analysis.get('planned_progress', 0)}%",
        f"- Đúng hạn (RAG): {analysis.get('rag_pct', 100)}%",
        "",
        "---",
        "",
        "✅ Done",
    ]
    
    # 1. Done items (3-5 bullets): Tổng hợp trực tiếp từ các sub-task Done trong kỳ (khớp 100% với Section 2 MD)
    # Tuyệt đối không lấy story.get("summary") vì Story cha thường chứa tên khởi tạo (VD: Khởi động Sprint...) gây lệch pha với file .md.
    all_done_subs: List[Dict] = []
    for parent in sorted(done_by_parent.keys()):
        all_done_subs.extend(done_by_parent[parent])

    def done_sort_key(sub: Dict) -> int:
        d = parse_date(sub.get("due_date"))
        return d.toordinal() if d else 999999

    done_bullets = []
    seen_done = set()
    for sub in sorted(all_done_subs, key=done_sort_key):
        s_title = sub.get("summary") or ""
        clean_title = clean_pm_phrase(s_title)
        if clean_title and clean_title not in seen_done:
            seen_done.add(clean_title)
            done_bullets.append(clean_title)
            if len(done_bullets) >= 5:
                break
                
    if not done_bullets:
        done_bullets.append("Hoàn thành các hạng mục theo kế hoạch sprint")
        
    for b in done_bullets[:5]:
        lines.append(f"- {b}")
        
    lines.extend(["", "▶ Doing / Will do"])
    
    # 2. Doing items (3-5 bullets)
    doing_bullets = []
    seen_doing = set()
    for _, _, parent, sub in sorted(doing_items, key=lambda x: (x[0], x[1], x[2])):
        s_title = sub.get("summary") or ""
        clean_s = clean_pm_phrase(s_title)
        if clean_s and clean_s not in seen_doing:
            seen_doing.add(clean_s)
            doing_bullets.append(clean_s)
            if len(doing_bullets) >= 5:
                break
                
    if not doing_bullets:
        doing_bullets.append("Tiếp tục triển khai các hạng mục theo tiến độ")
        
    for b in doing_bullets[:5]:
        lines.append(f"- {b}")
        
    lines.extend(["", "⚠️ Risks & Issues"])
    
    # 3. Risks & Issues (1-3 bullets)
    risks = []
    at_risk = [sub for _, _, _, sub in doing_items if subtask_is_at_risk(sub, analysis.get("today", date.today()))]
    if at_risk:
        risks.append(f"{len(at_risk)} hạng mục có nguy cơ trễ hạn")
    if analysis.get("spi", 1.0) < 0.8:
        risks.append(f"Tiến độ sprint chậm so với kế hoạch (SPI {analysis['spi']})")
    if analysis.get("rag_pct", 100) < 80 and not at_risk:
        risks.append(f"Tỷ lệ đúng hạn thấp (RAG {analysis['rag_pct']}%)")
        
    if not risks:
        risks.append("Không có rủi ro nghiêm trọng ảnh hưởng tiến độ chung")
        
    for r in risks[:3]:
        lines.append(f"- {r}")
        
    content = "\n".join(lines).strip() + "\n"
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(content)
        
    print(f"✅ Đã xuất file tóm tắt v{version}: {txt_path}")
    return txt_path


def write_report_manifest(
    output_dir: str,
    project_key: str,
    sprint_name: str,
    version: int,
    today: date,
) -> str:
    base = report_base_name(project_key, sprint_name)
    safe_sprint = sprint_name.replace(" ", "_").replace("/", "-")
    md_name = f"{base}_v{version}.md"
    txt_name = f"{base}_v{version}.txt"
    manifest = {
        "version": version,
        "projectKey": project_key,
        "sprintName": sprint_name,
        "md": md_name,
        "txt": txt_name,
        "txtExpected": txt_name,
        "summaryWorkflow": [
            "Read md (Section 1 + 2 + 4)",
            "Write txtExpected",
        ],
        "generatedAt": datetime.now(VN_TZ).isoformat(),
        "reportDate": today.isoformat(),
    }
    manifest_path = os.path.join(output_dir, f"{project_key}_{safe_sprint}_report_latest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    return manifest_path

def parse_date(d):
    """Parse date from various formats.

    Jira timestamps are UTC (trailing "Z") - a naive split on "T" keeps the UTC calendar
    day, which is wrong once local time crosses midnight (e.g. "17:00:06.175Z" is already
    "2026-07-01T00:00:06" in UTC+7, not the 30th). Always convert to VN_TZ before taking
    the date part.
    """
    if d is None:
        return None
    if isinstance(d, datetime):
        return d.astimezone(VN_TZ).date() if d.tzinfo else d.date()
    if isinstance(d, date):
        return d
    if isinstance(d, str):
        try:
            if "T" in d:
                dt = datetime.fromisoformat(d.replace("Z", "+00:00"))
                return dt.astimezone(VN_TZ).date() if dt.tzinfo else dt.date()
            return date.fromisoformat(d)
        except:
            pass
    return None

def fmt_date(d):
    """Format date for display (dd/mm/yyyy)"""
    if d is None:
        return "N/A"
    parsed = parse_date(d) if not isinstance(d, date) or isinstance(d, datetime) else d
    return parsed.strftime("%d/%m/%Y") if parsed else str(d)

def fmt_date_short(d):
    """Format date short (dd/mm)"""
    if d is None:
        return "N/A"
    parsed = parse_date(d) if not isinstance(d, date) or isinstance(d, datetime) else d
    return parsed.strftime("%d/%m") if parsed else str(d)

# ─────────────────────── ANALYSIS ───────────────────────
def analyze_data(data: Dict, today: date, sprint_start: date, sprint_end: date) -> Dict:
    """Compute all metrics from standardized JSON data"""
    stories = data.get("stories", [])
    subtasks = data.get("subtasks", [])
    bugs = data.get("bugs", [])

    all_subtasks = collect_all_subtasks(stories, subtasks, bugs)

    elapsed_days = (today - sprint_start).days
    total_days = (sprint_end - sprint_start).days
    planned_progress = round(elapsed_days / total_days * 100, 1) if total_days > 0 else 0

    phase_data = {phase: new_phase_stats() for phase in PHASE_WEIGHTS}
    has_phase_info = any(s.get("task_process") for s in all_subtasks)

    if has_phase_info:
        for sub in all_subtasks:
            phase = map_phase(sub.get("task_process"))
            prog_h, est_h = subtask_progress_hours(sub)
            phase_data[phase]["est"] += est_h
            phase_data[phase]["progress"] += prog_h
            phase_data[phase]["count"] += 1
            if is_progress_complete(sub.get("status")):
                phase_data[phase]["done_count"] += 1
    else:
        # Fallback: effort-based thuần trên toàn bộ sub-task (không weighted phase)
        prog_sum = est_sum = 0.0
        for sub in all_subtasks:
            prog_h, est_h = subtask_progress_hours(sub)
            prog_sum += prog_h
            est_sum += est_h
            phase_data["Other"]["est"] += est_h
            phase_data["Other"]["progress"] += prog_h
            phase_data["Other"]["count"] += 1
            if is_progress_complete(sub.get("status")):
                phase_data["Other"]["done_count"] += 1

    total_est = sum(p["est"] for p in phase_data.values())
    total_progress = sum(p["progress"] for p in phase_data.values())
    actual_progress_raw = round(total_progress / total_est * 100, 1) if total_est > 0 else 0

    if has_phase_info:
        impute_completed_prior_phases(phase_data)
        actual_progress_weighted = finalize_weighted_phases(phase_data)
    else:
        for phase in PHASE_WEIGHTS:
            pct = compute_phase_pct(phase_data[phase])
            phase_data[phase]["pct"] = pct if pct is not None else 0.0
            phase_data[phase]["contribution"] = 0.0
        actual_progress_weighted = actual_progress_raw
    
    # SPI
    spi = round(actual_progress_weighted / planned_progress, 2) if planned_progress > 0 else 0
    if spi >= 1.05:
        spi_status = "Ahead of Schedule ✅"
    elif spi >= 0.95:
        spi_status = "On Track ✅"
    elif spi >= 0.80:
        spi_status = "Slightly Behind ⚠️"
    else:
        spi_status = "Behind Schedule 🔴"
    
    # RAG (duedate-based) - chỉ sub-task level
    rag_total = 0
    rag_done = 0
    for sub in all_subtasks:
        due = parse_date(sub.get("due_date"))
        if due and due <= today:
            rag_total += 1
            if is_rag_complete(sub.get("status")):
                rag_done += 1

    rag_pct = round(rag_done / rag_total * 100, 1) if rag_total > 0 else 100
    rag_status = rag_label_from_pct(rag_pct)
    
    # Health
    if spi >= 0.95 and rag_pct >= 80:
        health = "🟢 Good"
    elif spi >= 0.80 and rag_pct >= 50:
        health = "🟡 At Risk"
    else:
        health = "🔴 Critical"
    
    # Story-level RAG (roll-up từ sub-task; story chỉ để group)
    for story in stories:
        subs = story.get("subtasks") or []
        s_done = 0
        s_total = 0
        for sub in subs:
            due = parse_date(sub.get("due_date"))
            if due and due <= today:
                s_total += 1
                if is_rag_complete(sub.get("status")):
                    s_done += 1

        if s_total > 0:
            s_pct = round(s_done / s_total * 100, 1)
            story["subtask_completion"] = f"{s_done}/{s_total} subtasks due ({s_pct}%)"
            story["rag"] = rag_label_from_pct(s_pct)
        else:
            story["subtask_completion"] = None
            story["rag"] = "On Track 🟢"

        story["subtask_due_done"] = s_done
        story["subtask_due_total"] = s_total

    return {
        "stories": stories,
        "subtasks": all_subtasks,
        "bugs": bugs,
        "sprint_start": sprint_start,
        "sprint_end": sprint_end,
        "today": today,
        "elapsed_days": elapsed_days,
        "total_days": total_days,
        "planned_progress": planned_progress,
        "actual_progress_raw": actual_progress_raw,
        "actual_progress_weighted": actual_progress_weighted,
        "spi": spi,
        "spi_status": spi_status,
        "rag_pct": rag_pct,
        "rag_status": rag_status,
        "health": health,
        "phase_data": phase_data,
        "total_est": total_est,
        "total_progress": total_progress,
    }

# ─────────────────────── GENERATE REPORT ───────────────────────
def generate_report(analysis: Dict, project_key: str, sprint_name: str, output_dir: str) -> str:
    """Generate Markdown report (.md). PMO .txt do Claude Write sau khi Read .md."""
    phase_rows = ""
    for phase in PHASE_ORDER:
        data = analysis["phase_data"].get(phase, {"est": 0, "progress": 0, "pct": 0, "contribution": 0})
        w_pct = int(PHASE_WEIGHTS[phase] * 100)
        phase_rows += f"| {phase} | {w_pct}% | {round(data['est'],1)}h | {round(data['progress'],1)}h | {data.get('pct',0)}% | {data.get('contribution',0)}% |\n"

    phase_detail = []
    for phase in PHASE_ORDER:
        d = analysis["phase_data"].get(phase, {})
        phase_detail.append(f"{phase} {d.get('pct',0)}%")

    today = analysis["today"]
    done_items_str, doing_items_str, done_by_parent, doing_items, story_map = build_sprint_progress_sections(
        analysis["subtasks"],
        analysis["stories"],
        today,
    )

    week_start = today - timedelta(days=7)
    week_end = today
    day_x = analysis["elapsed_days"]
    day_total = analysis["total_days"]
    is_wf = analysis.get("is_waterfall", False) or "waterfall" in str(sprint_name).lower() or "fixversion" in str(sprint_name).lower()

    period_label = "Giai đoạn / Dự án" if is_wf else "Sprint"
    period_planned_detail = f"Day {day_x}/{day_total} ngày kỳ báo cáo" if is_wf else f"Day {day_x}/{day_total} ngày sprint"

    report = f"""# Weekly Report - {project_key} · {sprint_name}

**Tuần báo cáo:** {fmt_date_short(week_start)} - {fmt_date(week_end)}
**{period_label}:** {sprint_name} · Day {day_x}/{day_total} · {fmt_date(analysis['sprint_start'])} - {fmt_date(analysis['sprint_end'])}
**Ngày tạo:** {fmt_date(today)}

---

## 1. Overall Status

| Metric | Giá trị | Chi tiết |
|--------|---------|----------|
| **Health** | {analysis['health']} | SPI = {analysis['spi']} |
| **Planned Progress** | {analysis['planned_progress']}% | {period_planned_detail} |
| **Actual Progress** | {analysis['actual_progress_weighted']}% | Weighted Phase ({' / '.join(phase_detail)}) |
| **SPI** | {analysis['spi']} | Actual / Planned - {analysis['spi_status']} |
| **RAG – Đúng hạn** | {analysis['rag_pct']}% | {analysis['rag_status']} |

---

## 2. Sprint Progress

### ✅ Done

{done_items_str}

### ▶ Doing / Will do

{doing_items_str}

---

## 3. Weighted Phase Breakdown

| Phase | Trọng số | Est | Progress | % | Đóng góp |
|-------|----------|-----|----------|---|----------|
{phase_rows}| **Total** | **100%** | **{round(analysis['total_est'],1)}h** | **{round(analysis['total_progress'],1)}h** | **{analysis['actual_progress_raw']}% raw** | **{analysis['actual_progress_weighted']}% weighted** |

> *Actual Progress = Σ(weight × pct_phase) trên **sub-task** (taskProcess). Done/In review = 100% est; còn lại = spent (cap est). Story chỉ group.*
> *RAG = sub-task có duedate ≤ today và status Done/In review / tổng sub-task due × 100.*

---

## 4. Risks & Issues

| # | Loại | Mô tả | Impact | Owner | Action |
|---|------|-------|--------|-------|--------|
| 1 | ℹ️ Note | *(Cần cập nhật từ Jira/Google Sheet hoặc input thủ công)* | Medium | - | - |

---

*Generated by Weekly Report Skill v3.0.0 · {project_key} · {fmt_date(today)}*
*Công thức: sub-task only · Done/In review = 100% est · Weighted = Σ(trọng số × %phase) · RAG duedate sub-task.*
"""

    os.makedirs(output_dir, exist_ok=True)
    base = report_base_name(project_key, sprint_name)
    version = next_report_version(output_dir, base)
    report_path = os.path.join(output_dir, f"{base}_v{version}.md")
    
    # Replace em dash với hyphen để đảm bảo plain text format nhất quán
    report = report.replace("—", "-")
    
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)

    manifest_path = write_report_manifest(output_dir, project_key, sprint_name, version, today)
    txt_path = generate_pm_sprint_summary_txt(
        analysis, project_key, sprint_name, done_by_parent, doing_items, story_map, output_dir, version
    )

    print(f"✅ Đã xuất file báo cáo v{version}: {report_path}")
    print(f"✅ Đã xuất file tóm tắt v{version}: {txt_path}")
    print(f"✅ Manifest: {manifest_path} (txt: {base}_v{version}.txt)")
    return report_path

def main():
    parser = argparse.ArgumentParser(description="Generate weekly report from standardized JSON")
    parser.add_argument("--input", required=True, help="Path to input JSON file")
    parser.add_argument("--output-dir", default="/mnt/Data/ai/pm", help="Output directory")
    parser.add_argument("--sprint-start", default=None, help="Sprint start date (YYYY-MM-DD)")
    parser.add_argument("--sprint-end", default=None, help="Sprint end date (YYYY-MM-DD)")
    parser.add_argument("--today", default=None, help="Report date (YYYY-MM-DD)")
    parser.add_argument("--project-key", default=None, help="Project key (default: auto-detect)")
    parser.add_argument("--sprint-name", default=None, help="Sprint name (default: auto-detect)")
    parser.add_argument("--waterfall", action="store_true", help="Chế độ Waterfall")
    args = parser.parse_args()
    
    # Load data
    with open(args.input, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # Detect parameters
    today = date.fromisoformat(args.today) if args.today else date.today()
    project_key = args.project_key or data.get("project", data.get("project_key", "PROJECT"))
    sprint_name = args.sprint_name or data.get("sprint_name", data.get("sprint", "Current Sprint"))
    is_waterfall = args.waterfall or bool(data.get("is_waterfall"))
    
    # Sprint dates
    if args.sprint_start and args.sprint_end:
        sprint_start = date.fromisoformat(args.sprint_start)
        sprint_end = date.fromisoformat(args.sprint_end)
    else:
        # Try to detect from data
        sprint_start_str = data.get("summary", {}).get("sprintStart") or data.get("sprint_start")
        sprint_end_str = data.get("summary", {}).get("sprintEnd") or data.get("sprint_end")
        
        if sprint_start_str and sprint_end_str:
            sprint_start = parse_date(sprint_start_str)
            sprint_end = parse_date(sprint_end_str)
        else:
            # Default: 2-week sprint ending 2 weeks from today
            sprint_end = today + timedelta(days=(14 - today.weekday()))
            sprint_start = sprint_end - timedelta(days=14)
            print(f"⚠️ Không tìm thấy sprint dates, dùng mặc định: {sprint_start} → {sprint_end}")
    
    print(f"📅 Kỳ báo cáo: {sprint_start} → {sprint_end}")
    print(f"📅 Today: {today}")
    
    # Analyze
    analysis = analyze_data(data, today, sprint_start, sprint_end)
    analysis["is_waterfall"] = is_waterfall
    
    # Generate report (.md - .txt do Claude Write sau khi Read .md)
    report_path = generate_report(analysis, project_key, sprint_name, args.output_dir)
    
    # Print summary
    print(f"\n{'='*60}")
    print(f"📊 TÓM TẮT BÁO CÁO")
    print(f"{'='*60}")
    print(f"  Health       : {analysis['health']}")
    print(f"  Planned      : {analysis['planned_progress']}%")
    print(f"  Actual       : {analysis['actual_progress_weighted']}% (weighted)")
    print(f"  SPI          : {analysis['spi']} - {analysis['spi_status']}")
    print(f"  RAG          : {analysis['rag_pct']}% - {analysis['rag_status']}")
    print(f"  Sub-tasks    : {len(analysis['subtasks'])} (metrics + Sprint Progress)")
    print(f"  Stories      : {len(analysis['stories'])} (group only)")
    print(f"{'='*60}")
    print(f"✅ Hoàn tất! MD: {report_path}")

if __name__ == "__main__":
    main()

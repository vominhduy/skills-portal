"""Port của background.js (HRM API scraping) sang Python.

Giữ nguyên hành vi so với extension gốc: hardcode "FTI" ở cột Division, chỉ fetch
page=1 (không phân trang) của danh sách project. Token truyền vào qua tham số.
"""

import os
import re
from datetime import datetime

import requests

API_BASE = "https://apis.fpt.net/hrm/resource-service/api"

# apis.fpt.net không qua được proxy công ty (DNS fail) - mặc định gọi trực tiếp,
# trừ khi được cấu hình proxy nội bộ / VPN SOCKS tunnel qua HRM_PROXY_URL.
NO_PROXY = {"http": None, "https": None}


def get_hrm_proxies():
    proxy_url = os.environ.get("HRM_PROXY_URL", "").strip()
    if proxy_url:
        return {"http": proxy_url, "https": proxy_url}
    return NO_PROXY


def get_api_base():
    custom_base = os.environ.get("HRM_API_BASE") or os.environ.get("HRM_BASE_URL", "").strip()
    if custom_base:
        return f"{custom_base.rstrip('/')}/hrm/resource-service/api"
    return API_BASE

VALUE_CODE_LABELS = {
    "EFF": "Hiệu suất vận hành",
    "PRD": "Năng suất lao động (NSLĐ)",
    "DAT": "Chất lượng & độ tin cậy dữ liệu",
    "EXP": "Trải nghiệm (internal user)",
    "RSK": "Kiểm soát rủi ro & tuân thủ",
    "REV": "Doanh thu & đảm bảo cước",
    "AGI": "Time-to-Market / năng lực kinh doanh",
    "DEC": "Hỗ trợ ra quyết định & phân tích",
    "COST": "Tối ưu chi phí hệ thống & hạ tầng",
    "PLT": "Nền tảng, tích hợp & mở rộng",
    "ENG": "Gắn kết nội bộ & Văn hóa doanh nghiệp",
}

HEALTH_LABELS = {
    "OnTrack": "On Track", "On Track": "On Track",
    "OffTrack": "Off Track", "Off Track": "Off Track",
    "AtRisk": "At Risk", "At Risk": "At Risk",
    "AtIssue": "At Issue", "At Issue": "At Issue",
}


# ─── Helpers ────────────────────────────────────────────────

def html_to_text(html):
    if not html:
        return ""
    t = re.sub(r"</(p|div|li|br)[^>]*>", "\n", html, flags=re.IGNORECASE)
    t = re.sub(r"<[^>]+>", "", t)
    t = (t.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
           .replace("&nbsp;", " ").replace("&#39;", "'").replace("&quot;", '"'))
    return re.sub(r"\n+", "\n", t).strip()


def format_username(full_name, username):
    if not full_name or not username:
        return username or ""
    last_name = full_name.strip().split(" ")[-1]
    name_part = username[:len(last_name)]
    remain_part = username[len(last_name):].upper()
    return name_part[:1].upper() + name_part[1:] + remain_part


def _parse_date(date_str):
    # API trả ISO 8601; fromisoformat xử lý được cả có/không có 'Z' sau khi thay thế.
    return datetime.fromisoformat(date_str.replace("Z", "+00:00"))


def get_quarter(date_str):
    if not date_str:
        return ""
    month = _parse_date(date_str).month
    return f"Quarter {((month - 1) // 3 + 1):02d}"


def map_health(health):
    return HEALTH_LABELS.get(health) or health or ""


def map_value_code(key):
    if not key:
        return ""
    label = VALUE_CODE_LABELS.get(key)
    if not label:
        return key
    text = f"{key} - {label}"
    return f'"{text}"' if "," in text else text


def format_date(date_str):
    if not date_str:
        return ""
    d = _parse_date(date_str)
    return f"{d.day:02d}/{d.month:02d}/{d.year}"


MONTH_ABBR = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def format_date_long(date_str):
    if not date_str:
        return ""
    d = _parse_date(date_str)
    return f"{d.day:02d}-{MONTH_ABBR[d.month - 1]}-{d.year}"


def format_risks(risks):
    if not risks:
        return ""
    parts = []
    for r in risks:
        t = f"{r.get('tracker_name') or ''} - {r.get('status_name') or ''}"
        if r.get("fromDate") or r.get("toDate"):
            t += f"\n\n[{format_date(r.get('fromDate'))} - {format_date(r.get('toDate'))}]"
        if r.get("title"):
            t += f"\n\n{r['title']}"
        if r.get("impact"):
            t += f"\n\nImpact:\n{r['impact']}"
        if r.get("action"):
            t += f"\n\nAction:\n{r['action']}"
        parts.append(t)
    return "\n\n".join(parts)


# ─── API calls ──────────────────────────────────────────────

def fetch_projects_list(token, config):
    # Khớp extension gốc: KHÔNG gửi divisionCode khi trống (extension không gửi param này).
    params = {
        "fetch": 25,
        "page": 1,
        "isExport": "false",
        "startOfWeek": config.get("startOfWeek", ""),
        "endOfWeek": config.get("endOfWeek", ""),
    }
    if config.get("divisionCode"):
        params["divisionCode"] = config["divisionCode"]
    list_api = f"{get_api_base()}/projects/weekly-reports"
    res = requests.get(list_api, params=params, headers={"Authorization": f"Bearer {token}"}, proxies=get_hrm_proxies())
    if not res.ok:
        raise RuntimeError(f"List API error: {res.status_code}")
    data = res.json()
    items = (data.get("data") or {}).get("items") or []
    print(f"[HRM] fetchProjectsList: {len(items)} items returned")
    return items


def fetch_project_detail(token, project_id, report_view_id):
    detail_api = f"{get_api_base()}/projects/{project_id}/weekly-reports/{report_view_id}"
    res = requests.get(
        detail_api,
        headers={"Authorization": f"Bearer {token}"},
        proxies=get_hrm_proxies(),
    )
    if not res.ok:
        return None
    json_body = res.json()
    d = json_body.get("data") or {}

    risks = [{
        "tracker_name": (r.get("tracker") or {}).get("name"),
        "status_name": (r.get("status") or {}).get("name"),
        "title": r.get("title"),
        "impact": r.get("impact"),
        "action": r.get("action"),
        "fromDate": r.get("fromDate"),
        "toDate": r.get("toDate"),
    } for r in (d.get("riskOrIssues") or [])]

    return {
        "displayName": d.get("displayName"),
        "progress": d.get("progress"),
        "projectPhase": d.get("projectPhase"),
        "projectHealth": (d.get("projectHeath") or {}).get("name"),
        "done": d.get("done"),
        "continuationPlan": d.get("continuationPlan"),
        "riskOrIssues": risks,
        "planStartDate": d.get("planStartDate"),
        "valueCodes": d.get("valueCodes"),
        "valueMetric": d.get("valueMetric"),
        "businessImpact": d.get("businessImpact"),
    }


def scrape_projects(token, config, on_progress=None):
    project_list = fetch_projects_list(token, config)
    results = []

    for i, project in enumerate(project_list):
        report_view_dto = project.get("reportViewDto")
        if not report_view_dto:
            print(f"[HRM]  SKIP {i + 1}/{len(project_list)}: "
                  f"{project.get('displayName') or (project.get('project') or {}).get('name') or '?'} "
                  f"(no reportViewDto)")
            continue

        project_id = project.get("id")
        report_view_id = report_view_dto.get("id")

        if on_progress:
            on_progress({"current": i + 1, "total": len(project_list), "name": project.get("displayName")})

        detail = fetch_project_detail(token, project_id, report_view_id)
        if not detail:
            print(f"[HRM]  SKIP {i + 1}/{len(project_list)}: "
                  f"{project.get('displayName')} (fetchProjectDetail returned null)")
            continue

        progress = f"{detail['progress']}%" if detail.get("progress") is not None else ""

        raw_value_codes = project.get("valueCodes")
        if isinstance(raw_value_codes, list):
            value_codes = ", ".join(
                map_value_code(v.get("key") if isinstance(v, dict) else v) for v in raw_value_codes
            )
        else:
            value_codes = map_value_code(raw_value_codes)

        pm_employee = project.get("pmEmployee") or {}

        # Trích xuất division từ project object
        div_raw = project.get("division")
        div_code = ""
        if isinstance(div_raw, dict):
            div_code = div_raw.get("code") or div_raw.get("name") or ""
        elif isinstance(div_raw, str):
            div_code = div_raw

        if not div_code:
            p_obj = project.get("project") or {}
            p_div = p_obj.get("division")
            if isinstance(p_div, dict):
                div_code = p_div.get("code") or p_div.get("name") or ""
            elif isinstance(p_div, str):
                div_code = p_div
            if not div_code:
                div_code = project.get("divisionCode") or p_obj.get("divisionCode") or ""

        results.append({
            "division": div_code,
            "displayName": project.get("displayName") or detail.get("displayName"),
            "projectCode": (project.get("project") or {}).get("name") or "",
            "mainFeature": html_to_text(project.get("mainFeature")),
            "goal": html_to_text(project.get("goal")),
            "pm": format_username(pm_employee.get("fullName") or "", pm_employee.get("userName") or ""),
            "planDueDate": format_date_long(project.get("planDueDate")),
            "progress": progress,
            "projectPhase": detail.get("projectPhase") or "",
            "projectHealth": map_health(detail.get("projectHealth")),
            "done": detail.get("done") or "",
            "continuationPlan": detail.get("continuationPlan") or "",
            "riskOrIssues": format_risks(detail.get("riskOrIssues")),
            "quarter": get_quarter(project.get("planDueDate")),
            "planStartDate": format_date_long(detail.get("planStartDate")),
            "valueCodes": value_codes,
            "valueMetric": project.get("valueMetric") or "",
            "businessImpact": project.get("businessImpact") or "",
            "releaseNote": html_to_text(project.get("releaseNote")),
        })

    print(f"[HRM] scrapeProjects done: {len(results)} projects scraped successfully")
    return results

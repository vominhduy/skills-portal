#!/usr/bin/env python3
"""Shared Jira REST client - 1 chỗ handle credential (env var, KHÔNG qua CLI arg),
retry 429/5xx, pagination, JQL escape. Dùng chung cho jira-import / weekly-report.

Credential: đọc từ env JIRA_EMAIL + JIRA_API_TOKEN (webapp inject, không leak qua ps/history).
JIRA_SITE: domain Atlassian (VD https://foxproject.atlassian.net) - đọc từ env JIRA_SITE hoặc tham số.
"""
from __future__ import annotations
import base64
import os
import time
from typing import Dict, List, Optional, Any
import requests

DEFAULT_TIMEOUT = 30

# Proxy fallback (direct → proxy → env) - dùng chung network_utils của weekly-report-api nếu có.
# Tránh jira_client chết ở direct khi máy chỉ reach Jira qua proxy (VD proxy FPT).
try:
    from network_utils import request_with_proxy_fallback as _fb_request  # type: ignore
    _HAS_NETUTILS = True
except Exception:  # noqa: BLE001
    _HAS_NETUTILS = False
    _fb_request = None  # type: ignore


def get_credentials() -> tuple[str, str]:
    """Lấy Jira credential từ env - KHÔNG nhận qua CLI arg (chống leak qua ps)."""
    email = os.environ.get("JIRA_EMAIL", "").strip()
    token = os.environ.get("JIRA_API_TOKEN", "").strip()
    if not email or not token:
        raise RuntimeError("Thiếu JIRA_EMAIL / JIRA_API_TOKEN (env) - webapp inject khi chạy skill.")
    return email, token


def auth_header(email: str, token: str) -> Dict[str, str]:
    encoded = base64.b64encode(f"{email}:{token}".encode("utf-8")).decode("utf-8")
    return {"Authorization": f"Basic {encoded}", "Content-Type": "application/json"}


def _do_request(method: str, url: str, headers: Dict, json_data=None, params=None,
                 timeout: int = DEFAULT_TIMEOUT) -> requests.Response:
    """Gọi HTTP - có proxy fallback (direct→proxy→env) nếu network_utils sẵn có, ngược lại requests thường."""
    if _HAS_NETUTILS and _fb_request is not None:
        return _fb_request(method, url, headers=headers, json=json_data,
                            params=params, timeout=timeout)
    return requests.request(method, url, headers=headers, json=json_data,
                             params=params, timeout=timeout)


def make_request(method: str, url: str, headers: Dict, json_data=None, params=None,
                 max_retries: int = 5, timeout: int = DEFAULT_TIMEOUT) -> Dict:
    """Request với proxy fallback + retry 429 (Retry-After) + 5xx (exponential) + network error."""
    for attempt in range(max_retries):
        try:
            resp = _do_request(method, url, headers, json_data=json_data,
                               params=params, timeout=timeout)
            if resp.status_code == 429:
                retry_after = resp.headers.get("Retry-After", 5)
                wait = int(retry_after) if str(retry_after).isdigit() else 2 ** attempt + 1
                print(f"[RATE LIMIT] 429 - chờ {wait}s (lần {attempt+1}/{max_retries})")
                time.sleep(wait)
                continue
            if 500 <= resp.status_code < 600:
                wait = 2 ** attempt + 1
                print(f"[SERVER ERROR] {resp.status_code} - chờ {wait}s (lần {attempt+1}/{max_retries})")
                time.sleep(wait)
                continue
            resp.raise_for_status()
            return resp.json() if resp.content else {}
        except requests.exceptions.RequestException as e:
            # 4xx (trừ 429) là lỗi auth/not-found - không retry, trả lỗi ngay (tránh waste 20s).
            if hasattr(e, "response") and e.response is not None:
                sc = e.response.status_code
                if sc != 429 and not (500 <= sc < 600):
                    print(f"[ERROR] {method} {url} → HTTP {sc}")
                    return {"error": str(e)}
            # Proxy fallback đã thử hết các mode (nếu có network_utils) → retry không giúp kết nối.
            # Chỉ retry khi còn lượt và là lỗi có thể phục hồi (network/5xx/429).
            if attempt < max_retries - 1:
                wait = 2 ** attempt + 1
                print(f"[NETWORK ERROR] {e} - chờ {wait}s (lần {attempt+1}/{max_retries})")
                time.sleep(wait)
                continue
            print(f"[ERROR] {method} {url} → {e}")
            return {"error": str(e)}
    print(f"[ERROR] Đã retry {max_retries} lần mà vẫn thất bại")
    return {"error": "Max retries exceeded"}


def is_error(result: Dict) -> bool:
    """Kiểm tra result có lỗi không - thay cho `if "key" in result` dễ nuốt error."""
    return isinstance(result, dict) and "error" in result


def escape_jql_string(value: str) -> str:
    """Escape giá trị string trong JQL - chống JQL injection qua sprint_name/project_key."""
    return value.replace("\\", "\\\\").replace('"', '\\"')


def build_jql(project_key: str, sprint_name: Optional[str] = None) -> str:
    """Build JQL an toàn - escape sprint_name."""
    pk = escape_jql_string(project_key)
    if sprint_name:
        return f'project = {pk} AND sprint = "{escape_jql_string(sprint_name)}"'
    return f'project = {pk}'


def search_all(jira_site: str, headers: Dict, jql: str, fields: Optional[List[str]] = None,
               page_size: int = 100) -> List[Dict]:
    """Pagination loop - lấy toàn bộ issues (>100), không truncate im lặng."""
    issues: List[Dict] = []
    url = f"{jira_site}/rest/api/3/search/jql"
    next_page_token: Optional[str] = None
    target_fields = fields if fields is not None else ["*navigable"]
    while True:
        body: Dict[str, Any] = {"jql": jql, "maxResults": page_size, "fields": target_fields}
        if next_page_token:
            body["nextPageToken"] = next_page_token
        result = make_request("POST", url, headers, json_data=body)
        if is_error(result):
            raise RuntimeError(f"Jira search failed: {result.get('error')}")
        batch = result.get("issues", [])
        issues.extend(batch)
        is_last = result.get("isLast", True)
        next_page_token = result.get("nextPageToken")
        if is_last or not next_page_token or not batch:
            break
    return issues


class JiraClient:
    def __init__(self, jira_site: Optional[str] = None):
        self.email, self.token = get_credentials()
        self.headers = auth_header(self.email, self.token)
        self.site = (jira_site or os.environ.get("JIRA_SITE") or "https://foxproject.atlassian.net").rstrip("/")

    def search(self, jql: str, fields: Optional[List[str]] = None) -> List[Dict]:
        return search_all(self.site, self.headers, jql, fields=fields)

    def get_sprint_issues(self, project_key: str, sprint_name: str, fields: Optional[List[str]] = None) -> List[Dict]:
        return self.search(build_jql(project_key, sprint_name), fields=fields)

    def create_issue(self, payload: Dict) -> Dict:
        url = f"{self.site}/rest/api/3/issue"
        return make_request("POST", url, self.headers, json_data=payload)

    # ── Agile API: board + sprint metadata (start/end dates) ──
    def find_board(self, project_key: str, board_name: Optional[str] = None) -> Optional[Dict]:
        """Tìm Scrum board cho project.
        - Nếu có board_name: ưu tiên board có tên khớp (contains, case-insensitive).
        - Không: ưu tiên board có tên chứa project key hoặc 'SCRUM', fallback board đầu tiên."""
        url = f"{self.site}/rest/agile/1.0/board"
        result = make_request("GET", url, self.headers,
                              params={"projectKeyOrId": project_key, "maxResults": 50})
        if is_error(result):
            raise RuntimeError(f"Không lấy được board cho {project_key}: {result.get('error')}")
        boards = result.get("values", [])
        if not boards:
            return None
        if board_name:
            kw = board_name.strip().lower()
            for b in boards:
                if kw and kw in b.get("name", "").lower():
                    return b
            # Không khớp tên - fallback heuristic bên dưới (không ném, có thể user ghi sai tên).
        key_upper = project_key.upper()
        for b in boards:
            name = b.get("name", "").upper()
            if key_upper in name or "SCRUM" in name:
                return b
        return boards[0]

    def get_board_sprints(self, board_id: int, state: str = "closed") -> List[Dict]:
        """Lấy danh sách sprint của board theo state (active/future/closed)."""
        url = f"{self.site}/rest/agile/1.0/board/{board_id}/sprint"
        result = make_request("GET", url, self.headers, params={"state": state, "maxResults": 100})
        if is_error(result):
            raise RuntimeError(f"Không lấy được sprint (board {board_id}, state={state}): {result.get('error')}")
        return result.get("values", [])

    def get_closed_sprints(self, project_key: str, limit: int = 6) -> List[Dict]:
        """Lấy N sprint đã đóng gần nhất (sorted by startDate desc)."""
        board = self.find_board(project_key)
        if not board:
            raise RuntimeError(f"Không tìm thấy board cho project {project_key}")
        sprints = self.get_board_sprints(board["id"], state="closed")
        # Bỏ sprint chưa có startDate (sprint bị lỗi), sort theo startDate desc
        valid = [s for s in sprints if s.get("startDate")]
        valid.sort(key=lambda s: s.get("startDate", ""), reverse=True)
        return valid[:limit]

    def find_sprint_by_name(self, project_key: str, sprint_name: str) -> Optional[Dict]:
        """Tìm sprint theo tên (partial match, case-insensitive) trong closed + active/future."""
        board = self.find_board(project_key)
        if not board:
            return None
        kw = sprint_name.lower()
        for state in ("closed", "active,future"):
            for s in self.get_board_sprints(board["id"], state=state):
                if kw in s.get("name", "").lower():
                    return s
        return None

    # ── Transitions API (chuyển trạng thái issue sang Done/Closed/Resolved) ──
    def get_issue_transitions(self, issue_id_or_key: str) -> List[Dict]:
        """Lấy danh sách các transition workflow khả dụng cho issue."""
        url = f"{self.site}/rest/api/3/issue/{issue_id_or_key}/transitions"
        result = make_request("GET", url, self.headers)
        if is_error(result):
            raise RuntimeError(f"Không lấy được transitions cho {issue_id_or_key}: {result.get('error')}")
        return result.get("transitions", [])

    def transition_issue(self, issue_id_or_key: str, transition_id: str) -> Dict:
        """Thực hiện chuyển trạng thái issue bằng transition_id."""
        url = f"{self.site}/rest/api/3/issue/{issue_id_or_key}/transitions"
        payload = {"transition": {"id": str(transition_id)}}
        result = make_request("POST", url, self.headers, json_data=payload)
        return result

    def mark_issue_done(self, issue_id_or_key: str) -> Dict:
        """Tự động tìm và thực hiện transition sang trạng thái Done/Closed/Resolved."""
        transitions = self.get_issue_transitions(issue_id_or_key)
        target_trans = None

        # 1. Tìm theo statusCategory == 'done'
        for t in transitions:
            to_cat = (t.get("to", {}).get("statusCategory", {}).get("key") or "").lower()
            if to_cat == "done":
                target_trans = t
                break

        # 2. Heuristic tìm theo tên transition nếu chưa thấy
        if not target_trans:
            keywords = ["done", "hoàn thành", "close", "closed", "resolve", "resolved", "finish", "finished"]
            for t in transitions:
                name = (t.get("name") or "").strip().lower()
                to_name = (t.get("to", {}).get("name") or "").strip().lower()
                if any(kw in name or kw in to_name for kw in keywords):
                    target_trans = t
                    break

        if not target_trans:
            available = [f"{t.get('name')} (id: {t.get('id')})" for t in transitions]
            return {
                "success": False,
                "error": f"Không tìm thấy transition hợp lệ sang 'Done'. Các transition khả dụng: {', '.join(available) or 'None'}",
            }

        res = self.transition_issue(issue_id_or_key, target_trans["id"])
        if is_error(res):
            return {"success": False, "error": res.get("error")}

        return {
            "success": True,
            "transition_id": target_trans["id"],
            "transition_name": target_trans.get("name"),
            "to_status": target_trans.get("to", {}).get("name"),
        }

    def mark_issue_in_progress(self, issue_id_or_key: str) -> Dict:
        """Tự động tìm và thực hiện transition sang trạng thái In Progress."""
        transitions = self.get_issue_transitions(issue_id_or_key)
        target_trans = None

        # 1. Tìm theo statusCategory == 'indeterminate' (tiêu chuẩn Jira cho In Progress)
        for t in transitions:
            to_cat = (t.get("to", {}).get("statusCategory", {}).get("key") or "").lower()
            if to_cat == "indeterminate":
                target_trans = t
                break

        # 2. Heuristic tìm theo tên transition / trạng thái đích nếu chưa thấy
        if not target_trans:
            keywords = ["in progress", "start progress", "tiến hành", "in-progress", "start work", "đang làm", "đang thực hiện", "in development", "developing"]
            for t in transitions:
                name = (t.get("name") or "").strip().lower()
                to_name = (t.get("to", {}).get("name") or "").strip().lower()
                if any(kw in name or kw in to_name for kw in keywords):
                    target_trans = t
                    break

        if not target_trans:
            available = [f"{t.get('name')} (id: {t.get('id')})" for t in transitions]
            return {
                "success": False,
                "error": f"Không tìm thấy transition hợp lệ sang 'In Progress'. Các transition khả dụng: {', '.join(available) or 'None'}",
            }

        res = self.transition_issue(issue_id_or_key, target_trans["id"])
        if is_error(res):
            return {"success": False, "error": res.get("error")}

        return {
            "success": True,
            "transition_id": target_trans["id"],
            "transition_name": target_trans.get("name"),
            "to_status": target_trans.get("to", {}).get("name"),
        }

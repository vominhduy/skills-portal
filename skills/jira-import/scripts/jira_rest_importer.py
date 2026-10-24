#!/usr/bin/env python3
import requests
import json
import sys
import os
import base64
import time
from typing import Dict, Optional, List
import argparse
from pathlib import Path

# Shared client - credential qua env (KHÔNG qua CLI arg, chống leak qua ps/history).
# Dùng _shared cạnh skill (webapp/skills/_shared) - không phụ thuộc ~/.claude/skills (bản cũ có thể lệch version).
_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "..", "_shared"))
from jira_client import get_credentials, auth_header, make_request, is_error, build_jql, _do_request  # noqa: E402

JIRA_SITE = os.environ.get("JIRA_SITE", "https://foxproject.atlassian.net").rstrip("/")

def _fmt_date(d):
    if not d:
        return None
    s = str(d).strip()
    if "T" in s:
        return s
    try:
        from datetime import datetime
        dt = datetime.strptime(s, "%Y-%m-%d")
        return dt.strftime("%Y-%m-%dT%H:%M:%S.000+0000")
    except:
        return s

# ================== ASSIGNEE CACHE ==================
ASSIGNEE_CACHE: Dict[str, str] = {
}

def get_auth_header(email: str, api_token: str) -> Dict:
    # Giữ lại cho backward-compat - nhưng nên dùng auth_header từ shared.
    return auth_header(email, api_token)

def make_request(method: str, url: str, headers: Dict, json_data=None, params=None, max_retries=5) -> Dict:
    for attempt in range(max_retries):
        try:
            response = _do_request(method, url, headers=headers, json_data=json_data,
                                   params=params, timeout=30)
            # === Rate limit (429) ===
            if response.status_code == 429:
                retry_after = response.headers.get("Retry-After", 5)
                wait = int(retry_after) if str(retry_after).isdigit() else (2 ** attempt + 1)
                print(f"[RATE LIMIT] 429 - Chờ {wait}s (lần {attempt+1}/{max_retries})")
                time.sleep(wait)
                continue

            # === Server errors (5xx) ===
            if 500 <= response.status_code < 600:
                wait = 2 ** attempt + 1
                print(f"[SERVER ERROR] {response.status_code} - Chờ {wait}s (lần {attempt+1}/{max_retries})")
                time.sleep(wait)
                continue

            response.raise_for_status()
            return response.json() if response.content else {}

        except requests.exceptions.RequestException as e:
            # === Rate limit / server error từ exception ===
            if hasattr(e, 'response') and e.response is not None:
                if e.response.status_code == 429:
                    continue
                if 500 <= e.response.status_code < 600:
                    wait = 2 ** attempt + 1
                    print(f"[SERVER ERROR] {e.response.status_code} - Chờ {wait}s (lần {attempt+1}/{max_retries})")
                    time.sleep(wait)
                    continue
                # 4xx khác (401/403/404…) - không retry, trả lỗi ngay
                print(f"[ERROR] {method} {url} → HTTP {e.response.status_code}")
                try:
                    err_body = e.response.json()
                    print(f"[ERROR DETAIL] {json.dumps(err_body, ensure_ascii=False, indent=2)}")
                    return {"error": str(e), "detail": err_body}
                except Exception:
                    print(f"[ERROR DETAIL] {e.response.text[:500]}")
                    return {"error": str(e)}

            # === Network errors (ConnectionError, Timeout, etc.) ===
            if attempt < max_retries - 1:
                wait = 2 ** attempt + 1
                print(f"[NETWORK ERROR] {str(e)} - Chờ {wait}s (lần {attempt+1}/{max_retries})")
                time.sleep(wait)
                continue

            print(f"[ERROR] {method} {url} → {str(e)}")
            return {"error": str(e)}

    print(f"[ERROR] Đã retry {max_retries} lần mà vẫn thất bại")
    return {"error": "Max retries exceeded"}

# ================== VERSION CACHE ==================
_VERSION_CACHE: Dict[str, Optional[str]] = {}  # project_key -> {short_name: full_name}

def resolve_fix_version(project_key: str, version_name: str, headers: Dict) -> Optional[str]:
    """Tìm tên version đúng trong Jira (hỗ trợ prefix như 'FTI-SAL v3.1' vs 'v3.1')."""
    if not version_name:
        return None
    cache_key = project_key
    if cache_key not in _VERSION_CACHE:
        url = f"{JIRA_SITE}/rest/api/3/project/{project_key}/versions"
        result = make_request("GET", url, headers)
        mapping = {}
        if isinstance(result, list):
            for v in result:
                name = v.get("name", "")
                mapping[name] = name           # exact match
                mapping[name.lower()] = name   # case-insensitive
                # short suffix match: "FTI-SAL v3.1" -> "v3.1"
                parts = name.split()
                if parts:
                    mapping[parts[-1].lower()] = name
        _VERSION_CACHE[cache_key] = mapping
        print(f" [VERSION] Project {project_key} versions: {list(set(mapping.values()))}")
    mapping = _VERSION_CACHE[cache_key]
    resolved = mapping.get(version_name) or mapping.get(version_name.lower())
    if resolved:
        print(f" [VERSION] '{version_name}' → '{resolved}'")
    else:
        print(f" [WARN] Version '{version_name}' không tìm thấy trong project {project_key}")
    return resolved

def get_sprint_id(project_key: str, sprint_name: str, headers: Dict,
                  board_name: Optional[str] = None) -> Optional[int]:
    print(f"[SEARCH] Tìm Sprint ID cho {project_key} - {sprint_name}"
          + (f" (board={board_name})" if board_name else ""))

    # === CÁCH 1: JQL - escape qua build_jql chống JQL injection qua sprint_name ===
    jql = build_jql(project_key, sprint_name)
    url = f"{JIRA_SITE}/rest/api/3/search/jql"
    result = make_request("POST", url, headers, json_data={"jql": jql, "maxResults": 5, "fields": ["customfield_10020"]})

    if result and result.get("issues"):
        sprint_field = result["issues"][0]["fields"].get("customfield_10020")
        if isinstance(sprint_field, list) and sprint_field:
            sprint_id = sprint_field[0].get("id")
            print(f"[OK] Tìm thấy Sprint ID qua JQL: {sprint_id}")
            return sprint_id

    # === CÁCH 2: Agile API (fallback) - cần đúng board khi sprint rỗng (chưa có issue) ===
    print(" → Thử Agile API...")
    board_url = f"{JIRA_SITE}/rest/agile/1.0/board?projectKeyOrId={project_key}"
    board_result = make_request("GET", board_url, headers)
    if board_result and board_result.get("values"):
        boards = board_result["values"]
        # Ưu tiên board khớp board_name (contains, case-insensitive); không thì heuristic (project key/SCRUM).
        board_id = None
        if board_name:
            kw = board_name.strip().lower()
            for b in boards:
                if kw and kw in b.get("name", "").lower():
                    board_id = b["id"]
                    print(f" [OK] Dùng board khớp '{board_name}': {b.get('name')} (id={board_id})")
                    break
        if board_id is None:
            key_upper = project_key.upper()
            for b in boards:
                name = b.get("name", "").upper()
                if key_upper in name or "SCRUM" in name:
                    board_id = b["id"]
                    break
            if board_id is None:
                board_id = boards[0]["id"]
        sprint_url = f"{JIRA_SITE}/rest/agile/1.0/board/{board_id}/sprint?state=active,future"
        sprint_result = make_request("GET", sprint_url, headers)
        if sprint_result and sprint_result.get("values"):
            for s in sprint_result["values"]:
                if s.get("name") == sprint_name:
                    sprint_id = s.get("id")
                    print(f"[OK] Tìm thấy Sprint ID qua Agile: {sprint_id}")
                    return sprint_id

    print("[ERROR] Không tìm thấy Sprint ID")
    return None

def resolve_assignee(name: str, headers: Dict) -> Optional[str]:
    if not name or str(name).strip() == "":
        return None
    name = str(name).strip()
    if name in ASSIGNEE_CACHE:
        print(f" [CACHE] Assignee '{name}' → {ASSIGNEE_CACHE[name]}")
        return ASSIGNEE_CACHE[name]
    url = f"{JIRA_SITE}/rest/api/3/user/search"
    result = make_request("GET", url, headers, params={"query": name})
    if isinstance(result, list) and result:
        account_id = result[0].get("accountId")
        ASSIGNEE_CACHE[name] = account_id
        print(f" [OK] Assignee '{name}' → {account_id} (đã cache)")
        return account_id
    print(f" [WARNING] Không tìm thấy assignee: {name}")
    return None

def build_fields(base: Dict, extra: Dict) -> Dict:
    """Xây dựng fields an toàn cho Jira"""
    fields = base.copy()
   
    for key, value in extra.items():
        if value is None or value == "" or value == []:
            continue
           
        # === XỬ LÝ CÁC CUSTOM FIELD LÀ SELECT LIST ===
        if key in ["customfield_10972", "customfield_10791", "customfield_10790",
                   "customfield_10825", "customfield_10788"]:
            fields[key] = {"value": str(value)}
               
        elif key == "fixVersions":
            fields[key] = [{"name": value}] if isinstance(value, str) else value
           
        elif key == "customfield_10033": # Story Points
            try:
                fields[key] = float(value)
            except (ValueError, TypeError):
                continue
               
        else:
            fields[key] = value
           
    return fields

def create_issue(payload: Dict, headers: Dict, dry_run: bool = False) -> Optional[str]:
    summary = payload["fields"].get("summary", "N/A")
    issue_type = payload["fields"].get("issuetype", {}).get("name", "Unknown")

    if dry_run:
        print(f" [DRY-RUN] Sẽ tạo {issue_type}: {summary}")
        return f"DRYRUN-{int(time.time())}"

    url = f"{JIRA_SITE}/rest/api/3/issue"
    result = make_request("POST", url, headers, json_data=payload)

    if not is_error(result) and result and "key" in result:
        print(f" [OK] Tạo thành công {issue_type}: {result['key']}")
        return result["key"]

    # === Auto-retry khi fixVersions không tồn tại trong project ===
    detail = result.get("detail", {})
    errors = detail.get("errors", {})
    if "fixVersions" in errors and "fixVersions" in payload.get("fields", {}):
        fix_ver = payload["fields"].pop("fixVersions")
        print(f" [WARN] fixVersions '{fix_ver}' không hợp lệ trong project → bỏ qua và thử lại")
        result2 = make_request("POST", url, headers, json_data=payload)
        if not is_error(result2) and result2 and "key" in result2:
            print(f" [OK] Tạo thành công {issue_type} (không có fixVersions): {result2['key']}")
            return result2["key"]
        result = result2  # cập nhật result để in lỗi mới nhất

    print(f" [ERROR] Tạo {issue_type} thất bại: {summary}")
    detail2 = result.get("detail", {})
    if detail2:
        print(f" Jira lỗi: {json.dumps(detail2, ensure_ascii=False, indent=2)}")
    else:
        print(f" Chi tiết: {result.get('error', result)}")
    return None

# ================== SUB-TASK PROCESSOR ==================
def process_subtask(sub: Dict, story_key: str, project: str, data: Dict,
                    headers: Dict, dry_run: bool) -> tuple:
    """Tạo một sub-task, trả về (sub_key, success_bool)."""
    assignee_id = resolve_assignee(sub.get("assignee"), headers)
    desc_text = sub.get("description") or "No description"

    sub_base = {
        "project": {"key": project},
        "issuetype": {"name": "Sub-task"},
        "summary": sub["summary"],
        "description": {
            "type": "doc", "version": 1,
            "content": [{"type": "paragraph", "content": [{"type": "text", "text": desc_text}]}]
        },
        "parent": {"key": story_key},
        "priority": {"name": sub.get("priority", "Medium")},
        "customfield_10015": sub.get("startDate"),
        "duedate": sub.get("dueDate"),
        "timetracking": {"originalEstimate": sub.get("originalEstimate", "0h")},
    }
    complexity_val = int(sub.get("complexity", 5) or 5)
    review_complexity = sub.get("reviewComplexity", "Normal") or "Normal"
    # Resolve version name về đúng tên trong Jira (tránh 400 fixVersions invalid)
    raw_version = data.get("fixVersion")
    resolved_version = resolve_fix_version(project, raw_version, headers) if raw_version else None
    sub_extra = {
        "customfield_10972": sub.get("type", "Normal"),
        "customfield_10791": sub.get("typeOfWork", "Do"),
        "customfield_10790": sub.get("taskProcess", "Coding"),
        "customfield_10788": str(complexity_val),   # Complexity - select list {value: "N"}
        "customfield_10824": review_complexity,      # Review Complexity - plain string
        "customfield_10867": float(sub.get("effortPlan") or 0),
        "customfield_10825": data.get("division"),
        "fixVersions": resolved_version,  # đã resolve về tên đúng
    }
    sub_fields = build_fields(sub_base, sub_extra)
    sub_payload = {"fields": sub_fields}
    if assignee_id:
        sub_payload["fields"]["assignee"] = {"accountId": assignee_id}

    sub_key = create_issue(sub_payload, headers, dry_run)

    # Thử lại nếu lỗi do assignee không hợp lệ
    if not sub_key and assignee_id:
        print(" → Thử lại Sub-task không có assignee...")
        del sub_payload["fields"]["assignee"]
        sub_key = create_issue(sub_payload, headers, dry_run)
        if sub_key:
            return sub_key, False  # tạo được nhưng thiếu assignee

    if sub_key:
        if not assignee_id and sub.get("assignee") and not dry_run:
            return sub_key, False  # tạo được nhưng thiếu assignee
        return sub_key, True

    return None, False


# ================== STATE FILE (chống duplicate) ==================
def get_state_path(input_file: str) -> str:
    """Đường dẫn file state, đặt cạnh file input."""
    return str(Path(input_file).with_suffix(".state.json"))


def load_state(state_path: str) -> Dict:
    """Load state từ file, nếu chưa có thì trả về state rỗng."""
    if os.path.exists(state_path):
        with open(state_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"stories": {}}  # story_summary -> {key, subtasks: [summary]}


def save_state(state_path: str, state: Dict):
    """Ghi state ra file."""
    Path(state_path).parent.mkdir(parents=True, exist_ok=True)
    with open(state_path, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)


def main():
    parser = argparse.ArgumentParser(description="Jira Bulk Import Tool (pure requests)")
    parser.add_argument("input_file", help="Đường dẫn file JSON dữ liệu")
    parser.add_argument("--email", "-e", default=None, help="JIRA Email (nếu omit, đọc từ env JIRA_EMAIL)")
    parser.add_argument("--api-token", "-t", default=None, help="JIRA API Token (nếu omit, đọc từ env JIRA_API_TOKEN)")
    parser.add_argument("--dry-run", action="store_true", help="Chạy thử, không tạo thật")
    parser.add_argument("--resume", action="store_true",
                        help="Tiếp tục từ lần chạy trước (dùng state file), bỏ qua issue đã tạo")
    parser.add_argument("--state-file", type=str, default=None,
                        help="Đường dẫn state file (mặc định: <input_file>.state.json)")
    parser.add_argument("--board-name", type=str, default=None,
                        help="Tên Scrum board (khi sprint rỗng, JQL không tìm được - dùng Agile API với board này)")
    args = parser.parse_args()

    # Credential: ưu tiên CLI arg (backward-compat), fallback env (webapp inject - không leak qua ps).
    if args.email and args.api_token:
        email, token = args.email, args.api_token
    else:
        email, token = get_credentials()
    HEADERS = auth_header(email, token)
    print(f"✅ Kết nối Jira với user: {email.split('@')[0]}@***")  # không in full email
    print(f"\n{'='*90}")
    print(f"🚀 JIRA IMPORTER - Mode: {'DRY-RUN' if args.dry_run else 'CREATE MODE'}")
    print(f"{'='*90}\n")

    with open(args.input_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    project = data.get("project", "FSM")
    sprint_name = data.get("sprint")
    parent = data.get("parentRequest")
    # Board name: ưu tiên CLI arg, fallback JSON (do excel_to_json ghi), fallback None.
    board_name = args.board_name or data.get("boardName")

    print(f"Project : {project}")
    print(f"Sprint  : {sprint_name}")
    print(f"Parent  : {parent}")
    if board_name:
        print(f"Board   : {board_name}")
    print(f"Số Story: {len(data.get('stories', []))}\n")

    sprint_id = get_sprint_id(project, sprint_name, HEADERS, board_name=board_name) if sprint_name else None
    if sprint_name and not sprint_id and not args.dry_run:
        print("❌ Không tìm thấy Sprint ID → Dừng import.")
        return

    # ================== STATE FILE (chống duplicate) ==================
    state_path = args.state_file or get_state_path(args.input_file)
    state = load_state(state_path) if args.resume else {"stories": {}}
    if args.resume:
        print(f"📂 Đã tìm thấy {len(state['stories'])} story trong state file: {state_path}")
        print(f"   → Sẽ bỏ qua các story/sub-task đã tạo trước đó.\n")

    created_stories = []
    successful_subtasks = 0
    total_subtasks = 0
    unresolved_subtasks: List[Dict] = []
    skipped_stories = 0

    for idx, story in enumerate(data.get("stories", []), 1):
        story_summary = story["summary"]

        # ================== KIỂM TRA RESUME ==================
        existing = state["stories"].get(story_summary) if args.resume else None
        if existing:
            story_key = existing["key"]
            created_subtasks = set(existing.get("subtasks", []))
            print(f"\n[{idx}/{len(data['stories'])}] [SKIP] Story đã tạo: {story_key}")
            created_stories.append({"key": story_key, "summary": story_summary})
            skipped_stories += 1

            # Vẫn xử lý các sub-task chưa tạo
            for sub in story.get("subtasks", []):
                total_subtasks += 1
                if sub["summary"] in created_subtasks:
                    print(f"  [SKIP] Sub-task đã tạo: {sub['summary']}")
                    successful_subtasks += 1
                    continue
                # Tạo sub-task còn thiếu
                sub_key, sub_ok = process_subtask(
                    sub, story_key, project, data, HEADERS, args.dry_run
                )
                if sub_ok:
                    successful_subtasks += 1
                    existing.setdefault("subtasks", []).append(sub["summary"])
                    save_state(state_path, state)
                if sub_key and not sub_ok:
                    unresolved_subtasks.append({"key": sub_key, "assignee": sub.get("assignee")})
            continue

        # ================== TẠO STORY MỚI ==================
        print(f"\n[{idx}/{len(data['stories'])}] Đang xử lý Story: {story_summary}")

        story_base = {
            "project": {"key": project},
            "issuetype": {"name": "Story"},
            "summary": story_summary,
            "description": {
                "type": "doc",
                "version": 1,
                "content": [{"type": "paragraph", "content": [{"type": "text", "text": story.get("description", "")}]}]
            },
            "priority": {"name": story.get("priority", "Medium")},
            "customfield_10015": story.get("startDate"),
            "duedate": story.get("dueDate"),
        }
        # Chỉ thêm parent nếu có giá trị (tránh gửi {"key": None} lên Jira)
        if parent:
            story_base["parent"] = {"key": parent}
        story_extra = {
            "customfield_10033": story.get("storyPoint"),
            "customfield_10867": story.get("effortPlan"),
            "fixVersions": resolve_fix_version(project, data.get("fixVersion"), HEADERS),
            "customfield_10825": data.get("division"),
            # Chỉ thêm sprint khi sprint_id có giá trị - build_fields sẽ bỏ qua None
            "customfield_10020": sprint_id,
        }
        story_fields = build_fields(story_base, story_extra)
        story_payload = {"fields": story_fields}

        story_key = story.get("storyKey") or create_issue(story_payload, HEADERS, args.dry_run)
        if story.get("storyKey"):
            print(f" [REUSE] Dùng lại Story key: {story_key}")

        if story_key and not args.dry_run:
            created_stories.append({"key": story_key, "summary": story_summary})

            # ================== SUB-TASKS ==================
            state["stories"][story_summary] = {"key": story_key, "subtasks": []}

            for sub in story.get("subtasks", []):
                total_subtasks += 1
                sub_key, sub_ok = process_subtask(
                    sub, story_key, project, data, HEADERS, args.dry_run
                )
                if sub_ok:
                    successful_subtasks += 1
                    state["stories"][story_summary]["subtasks"].append(sub["summary"])
                if sub_key and not sub_ok:
                    unresolved_subtasks.append({"key": sub_key, "assignee": sub.get("assignee")})

            # Lưu state ngay sau mỗi story
            save_state(state_path, state)

    # ================== BÁO CÁO ==================
    total_stories = len(data.get('stories', []))
    print("\n" + "="*90)
    print("✅ IMPORT HOÀN TẤT")
    print("="*90)
    
    if args.dry_run:
        print("🔍 DRY-RUN MODE - Không có issue nào được tạo thật.")
    else:
        print(f"📊 Stories  : {len(created_stories)}/{total_stories}")
        print(f"   - Tạo mới: {len(created_stories) - skipped_stories}")
        print(f"   - Đã skip: {skipped_stories}")
        print(f"📊 Sub-tasks: {successful_subtasks}/{total_subtasks} thành công")
        
        if created_stories:
            print("\nDANH SÁCH STORIES:")
            for i, s in enumerate(created_stories, 1):
                print(f"{i:2d}. {s['key']} - {s['summary']}")
                print(f"    Link: {JIRA_SITE}/browse/{s['key']}")
        
        if unresolved_subtasks:
            print("\n⚠️ SUB-TASK CẦN GÁN ASSIGNEE THỦ CÔNG:")
            for i, item in enumerate(unresolved_subtasks, 1):
                print(f" {i}. {item['key']} ← {item['assignee']}")
        
        if args.resume and state_path:
            print(f"\n💾 State file: {state_path}")
            print(f"   Dùng '--resume' ở lần chạy sau để tiếp tục từ tiến trình này.")

    print(f"\n⏱ Hoàn thành lúc: {time.strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""Check required fields for Sub-task in project FSM"""
import requests, base64, json, sys, os

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "..", "_shared"))
from jira_client import get_credentials, auth_header  # noqa: E402

JIRA_SITE = os.environ.get("JIRA_SITE", "https://foxproject.atlassian.net").rstrip("/")
project_key = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("JIRA_PROJECT", "FSM")

# Credential: ưu tiên arg (backward-compat), fallback env.
if len(sys.argv) >= 4:
    email, api_token = sys.argv[2], sys.argv[3]
else:
    email, api_token = get_credentials()
headers = auth_header(email, api_token)

# Get create metadata for project (expanded)
url = f"{JIRA_SITE}/rest/api/3/issue/createmeta"
params = {
    "projectKeys": project_key,
    "expand": "projects.issuetypes.fields"
}
r = requests.get(url, headers=headers, params=params, timeout=30)
data = r.json()

for project in data.get("projects", []):
    print(f"Project: {project.get('key')} (id: {project.get('id')})")
    for it in project.get("issuetypes", []):
        name = it.get("name", "")
        print(f"\n  Issue type: {name} (id: {it.get('id')})")
        if "Sub" in name or "sub" in name.lower():
            for field_key, field in it.get("fields", {}).items():
                if isinstance(field, dict):
                    fname = field.get("name", "")
                    fid = field.get("fieldId", field_key)
                    req = field.get("required", False)
                    if req:
                        print(f"    REQUIRED: {fname} (fieldId: {fid})")
                    if fid in ["customfield_10824", "customfield_10788"] or "Review" in fname or "review" in fname or "Complexity" in fname or "complexity" in fname.lower():
                        print(f"    FIELD: {fname} (fieldId: {fid}, required: {req})")
                        print(f"      Schema: {json.dumps(field.get('schema', {}), ensure_ascii=False)}")
                        allowed = field.get("allowedValues", [])
                        if allowed:
                            vals = []
                            for v in allowed:
                                if isinstance(v, dict):
                                    vals.append(v.get("value", str(v)))
                                else:
                                    vals.append(str(v))
                            print(f"      Allowed values: {vals}")
                    # Also print if required and not standard
                    if req and fname not in ["Summary", "Issue Type", "Parent", "Project"]:
                        print(f"    OTHER REQUIRED: {fname} (fieldId: {fid})")
            break

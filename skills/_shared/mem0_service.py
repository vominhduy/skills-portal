#!/usr/bin/env python3
"""
Mem0 Shared Long-Term Memory Service
Manages 3-Tier persistent memory:
- project_context: Project domain, architecture, constraints
- user_preference: User roles, tone, conventions
- decisions_history: Approved decisions, architecture choices, sprint agreements
"""
import os
import sys
import json
import sqlite3
import argparse
import uuid
import re
from datetime import datetime, timezone

STORAGE_DIR = os.environ.get('MEM0_STORAGE_DIR') or os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    'data', 'mem0_storage'
)
DB_PATH = os.path.join(STORAGE_DIR, 'memories.db')

VALID_CATEGORIES = {'project_context', 'user_preference', 'decisions_history'}
CATEGORY_LABELS = {
    'project_context': 'Project Context',
    'user_preference': 'User Preference',
    'decisions_history': 'Decisions History',
}

def ensure_db():
    os.makedirs(STORAGE_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS memories (
            id TEXT PRIMARY KEY,
            content TEXT NOT NULL,
            category TEXT NOT NULL,
            user_id TEXT DEFAULT 'global',
            project_id TEXT DEFAULT 'default',
            metadata TEXT DEFAULT '{}',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    ''')
    cur.execute('CREATE INDEX IF NOT EXISTS idx_mem_category ON memories (category)')
    cur.execute('CREATE INDEX IF NOT EXISTS idx_mem_user ON memories (user_id)')
    cur.execute('CREATE INDEX IF NOT EXISTS idx_mem_project ON memories (project_id)')
    conn.commit()
    conn.close()

def add_memory(content: str, category: str = 'project_context', user_id: str = 'global', project_id: str = 'default', metadata: dict = None) -> dict:
    if not content or not content.strip():
        raise ValueError("Memory content cannot be empty")
    
    category = category.lower().strip()
    if category not in VALID_CATEGORIES:
        category = 'project_context'

    ensure_db()
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Check for duplicate or near-identical memory in same category
    cur.execute('''
        SELECT id, content FROM memories 
        WHERE category = ? AND user_id = ? AND project_id = ?
    ''', (category, str(user_id), str(project_id)))
    existing = cur.fetchall()

    content_clean = content.strip()
    for row in existing:
        if row[1].strip().lower() == content_clean.lower():
            # Already exists
            conn.close()
            return {
                "id": row[0],
                "content": row[1],
                "category": category,
                "user_id": str(user_id),
                "project_id": str(project_id),
                "action": "existing",
                "message": "Memory already exists"
            }

    mem_id = f"mem_{uuid.uuid4().hex[:12]}"
    now = datetime.now(timezone.utc).isoformat()
    meta_json = json.dumps(metadata or {}, ensure_ascii=False)

    cur.execute('''
        INSERT INTO memories (id, content, category, user_id, project_id, metadata, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (mem_id, content_clean, category, str(user_id), str(project_id), meta_json, now, now))
    conn.commit()
    conn.close()

    return {
        "id": mem_id,
        "content": content_clean,
        "category": category,
        "category_label": CATEGORY_LABELS.get(category, category),
        "user_id": str(user_id),
        "project_id": str(project_id),
        "metadata": metadata or {},
        "created_at": now,
        "action": "created"
    }

def tokenize(text: str) -> set:
    if not text:
        return set()
    words = re.findall(r'[\w]+', text.lower())
    return set(words)

def search_memories(query: str, user_id: str = None, project_id: str = None, category: str = None, limit: int = 5) -> list:
    ensure_db()
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    sql = "SELECT id, content, category, user_id, project_id, metadata, created_at, updated_at FROM memories WHERE 1=1"
    params = []

    if category and category in VALID_CATEGORIES:
        sql += " AND category = ?"
        params.append(category)

    cur.execute(sql, params)
    rows = cur.fetchall()
    conn.close()

    if not rows:
        return []

    if not query or not query.strip():
        # Return recent
        results = []
        for r in rows[:limit]:
            try:
                meta = json.loads(r[5])
            except:
                meta = {}
            results.append({
                "id": r[0],
                "content": r[1],
                "category": r[2],
                "category_label": CATEGORY_LABELS.get(r[2], r[2]),
                "user_id": r[3],
                "project_id": r[4],
                "metadata": meta,
                "created_at": r[6],
                "score": 1.0
            })
        return results

    query_tokens = tokenize(query)
    scored = []

    for r in rows:
        content = r[1]
        content_tokens = tokenize(content)
        category_tokens = tokenize(r[2])
        all_tokens = content_tokens | category_tokens

        # Jaccard / Overlap score
        overlap = len(query_tokens & all_tokens)
        if overlap > 0:
            score = overlap / (len(query_tokens) + len(content_tokens) - overlap + 1e-5)
            # Boost if query appears verbatim
            if query.lower() in content.lower():
                score += 1.5
            scored.append((score, r))
        else:
            # Substring match bonus
            for q_tok in query_tokens:
                if len(q_tok) > 2 and q_tok in content.lower():
                    scored.append((0.2, r))
                    break

    scored.sort(key=lambda x: x[0], reverse=True)

    results = []
    for score, r in scored[:limit]:
        try:
            meta = json.loads(r[5])
        except:
            meta = {}
        results.append({
            "id": r[0],
            "content": r[1],
            "category": r[2],
            "category_label": CATEGORY_LABELS.get(r[2], r[2]),
            "user_id": r[3],
            "project_id": r[4],
            "metadata": meta,
            "created_at": r[6],
            "score": round(score, 3)
        })

    return results

def list_memories(category: str = None, user_id: str = None, project_id: str = None) -> list:
    ensure_db()
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    sql = "SELECT id, content, category, user_id, project_id, metadata, created_at, updated_at FROM memories WHERE 1=1"
    params = []

    if category and category in VALID_CATEGORIES:
        sql += " AND category = ?"
        params.append(category)
    if user_id:
        sql += " AND (user_id = ? OR user_id = 'global')"
        params.append(str(user_id))
    if project_id:
        sql += " AND (project_id = ? OR project_id = 'default')"
        params.append(str(project_id))

    sql += " ORDER BY created_at DESC"
    cur.execute(sql, params)
    rows = cur.fetchall()
    conn.close()

    memories = []
    for r in rows:
        try:
            meta = json.loads(r[5])
        except:
            meta = {}
        memories.append({
            "id": r[0],
            "content": r[1],
            "category": r[2],
            "category_label": CATEGORY_LABELS.get(r[2], r[2]),
            "user_id": r[3],
            "project_id": r[4],
            "metadata": meta,
            "created_at": r[6],
            "updated_at": r[7]
        })
    return memories

def delete_memory(memory_id: str) -> bool:
    ensure_db()
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
    deleted = cur.rowcount > 0
    conn.commit()
    conn.close()
    return deleted

def get_stats() -> dict:
    ensure_db()
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT category, count(*) FROM memories GROUP BY category")
    counts = dict(cur.fetchall())
    cur.execute("SELECT count(*) FROM memories")
    total = cur.fetchone()[0]
    conn.close()

    return {
        "total": total,
        "by_category": {
            "project_context": counts.get("project_context", 0),
            "user_preference": counts.get("user_preference", 0),
            "decisions_history": counts.get("decisions_history", 0),
        },
        "storage_path": DB_PATH
    }

def auto_extract_memories(user_message: str, assistant_response: str, user_id: str = 'global', project_id: str = 'default') -> list:
    """
    Heuristic rule-based extraction for fast offline memory storage
    """
    extracted = []
    text_pair = f"{user_message}\n{assistant_response}"

    # 1. User preferences (ví dụ: "tôi muốn...", "từ giờ hãy...", "nhớ là...", "prefer...")
    pref_patterns = [
        r'(?:từ giờ|từ nay|luôn luôn|hãy nhớ|quy định là|sở thích của tôi là)\s+([^.\n]+)',
        r'(?:luôn trả lời bằng|định dạng bằng|ưu tiên dùng)\s+([^.\n]+)',
    ]
    for pat in pref_patterns:
        matches = re.findall(pat, user_message, re.IGNORECASE)
        for m in matches:
            if len(m.strip()) > 5:
                res = add_memory(f"Quy tắc/Sở thích: {m.strip()}", category='user_preference', user_id=user_id, project_id=project_id)
                extracted.append(res)

    # 2. Decision patterns (ví dụ: "chúng ta thống nhất...", "quyết định dùng...", "chốt phương án...")
    decision_patterns = [
        r'(?:thống nhất|quyết định|đã chốt|đồng ý phương án|lựa chọn kiến trúc)\s+([^.\n]+)',
    ]
    for pat in decision_patterns:
        matches = re.findall(pat, text_pair, re.IGNORECASE)
        for m in matches:
            if len(m.strip()) > 8:
                res = add_memory(f"Quyết định kỹ thuật: {m.strip()}", category='decisions_history', user_id=user_id, project_id=project_id)
                extracted.append(res)

    return extracted

def main():
    parser = argparse.ArgumentParser(description="Mem0 Shared Long-Term Memory Service")
    parser.add_argument('--action', choices=['add', 'search', 'list', 'delete', 'stats', 'extract'], required=True)
    parser.add_argument('--content', type=str, help="Memory text content")
    parser.add_argument('--category', type=str, default=None, choices=['project_context', 'user_preference', 'decisions_history'])
    parser.add_argument('--user_id', type=str, default='global')
    parser.add_argument('--project_id', type=str, default='default')
    parser.add_argument('--query', type=str, default='')
    parser.add_argument('--limit', type=int, default=5)
    parser.add_argument('--id', type=str, help="Memory ID for delete")
    parser.add_argument('--user_message', type=str, help="User message for extract")
    parser.add_argument('--assistant_response', type=str, help="Assistant response for extract")

    args = parser.parse_args()

    if args.action == 'add':
        cat = args.category or 'project_context'
        res = add_memory(args.content, cat, args.user_id, args.project_id)
        print(json.dumps(res, ensure_ascii=False))
    elif args.action == 'search':
        res = search_memories(args.query, args.user_id, args.project_id, args.category, args.limit)
        print(json.dumps(res, ensure_ascii=False))
    elif args.action == 'list':
        res = list_memories(args.category, args.user_id, args.project_id)
        print(json.dumps(res, ensure_ascii=False))
    elif args.action == 'delete':
        if not args.id:
            print(json.dumps({"error": "Missing --id"}))
            sys.exit(1)
        ok = delete_memory(args.id)
        print(json.dumps({"ok": ok, "id": args.id}))
    elif args.action == 'stats':
        res = get_stats()
        print(json.dumps(res, ensure_ascii=False))
    elif args.action == 'extract':
        res = auto_extract_memories(args.user_message or '', args.assistant_response or '', args.user_id, args.project_id)
        print(json.dumps(res, ensure_ascii=False))

if __name__ == '__main__':
    main()

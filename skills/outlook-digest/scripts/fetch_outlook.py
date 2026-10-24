#!/usr/bin/env python3
"""Fetch Outlook → redact/encrypt sensitive → ghi safe JSON + vault.enc.
Hỗ trợ cả kết nối trực tiếp tới máy chủ Outlook và đọc từ file email đính kèm (.eml, .txt).
"""
from __future__ import annotations

import argparse
import email
from email.header import decode_header
import glob
import json
import os
import re
import sys
from datetime import date
from typing import Any, Dict, List

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from content_crypto import encrypt_text  # noqa: E402
from outlook_client import fetch_messages, _decode_mime_str, _clean_html  # noqa: E402
from sensitive_filter import process_message  # noqa: E402


def next_version(out_dir: str, slug: str) -> int:
    v = 1
    while os.path.isfile(os.path.join(out_dir, f"{slug}_v{v}_safe.json")):
        v += 1
    return v


def build_query(args: argparse.Namespace) -> str:
    parts: list[str] = []
    if args.query:
        parts.append(args.query.strip())
    if args.subject:
        parts.append(f"subject:{args.subject.strip()}")
    if args.from_addr:
        parts.append(f"from:{args.from_addr.strip()}")
    return " ".join(parts).strip()


def parse_local_email_file(file_path: str) -> List[Dict[str, Any]]:
    """Phân tích file email nội bộ (.eml, .txt, .json)."""
    if not os.path.isfile(file_path):
        return []

    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".eml":
        try:
            with open(file_path, "rb") as fp:
                msg = email.message_from_binary_file(fp)
            subject = _decode_mime_str(msg.get("Subject")) or os.path.basename(file_path)
            from_str = _decode_mime_str(msg.get("From")) or ""
            to_str = _decode_mime_str(msg.get("To")) or ""
            date_str = msg.get("Date") or date.today().isoformat()

            body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    ct = part.get_content_type()
                    cd = str(part.get("Content-Disposition") or "")
                    if "attachment" in cd:
                        continue
                    if ct == "text/plain":
                        payload = part.get_payload(decode=True)
                        if payload:
                            body = payload.decode(part.get_content_charset() or "utf-8", errors="replace")
                            break
                    elif ct == "text/html" and not body:
                        payload = part.get_payload(decode=True)
                        if payload:
                            body = _clean_html(payload.decode(part.get_content_charset() or "utf-8", errors="replace"))
            else:
                payload = msg.get_payload(decode=True)
                if payload:
                    body = payload.decode(msg.get_content_charset() or "utf-8", errors="replace")
                    if msg.get_content_type() == "text/html":
                        body = _clean_html(body)

            snippet = (body[:200] + "...") if len(body) > 200 else body
            return [{
                "id": os.path.basename(file_path),
                "thread_id": msg.get("Message-ID") or os.path.basename(file_path),
                "date": date_str,
                "from": from_str,
                "to": to_str,
                "cc": _decode_mime_str(msg.get("Cc")) or "",
                "subject": subject,
                "snippet": snippet.strip(),
                "body": body.strip() or snippet.strip(),
                "has_attachments": False,
            }]
        except Exception as e:
            print(f"[-] Lỗi đọc file .eml {file_path}: {e}", file=sys.stderr)
            return []

    elif ext in [".txt", ".md"]:
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as fp:
                raw_text = fp.read()
            return [{
                "id": os.path.basename(file_path),
                "thread_id": os.path.basename(file_path),
                "date": date.today().isoformat(),
                "from": "File đính kèm",
                "to": "Tôi",
                "cc": "",
                "subject": os.path.basename(file_path),
                "snippet": raw_text[:200],
                "body": raw_text.strip(),
                "has_attachments": False,
            }]
        except Exception:
            return []

    return []


def find_uploaded_email_files(out_dir: str) -> List[str]:
    """Tìm các file email được user đính kèm trong thư mục uploads hoặc thư mục output."""
    found: List[str] = []
    # 1. Thư mục out_dir
    found.extend(glob.glob(os.path.join(out_dir, "*.eml")))
    found.extend(glob.glob(os.path.join(out_dir, "*.msg")))
    # 2. Thư mục uploads anh em nếu có
    parent = os.path.dirname(out_dir)
    uploads_dir = os.path.join(parent, "uploads")
    if os.path.isdir(uploads_dir):
        found.extend(glob.glob(os.path.join(uploads_dir, "*.eml")))
        found.extend(glob.glob(os.path.join(uploads_dir, "*.msg")))
    return list(set(found))


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch Outlook và redact nội dung nhạy cảm")
    parser.add_argument("--output-dir", required=True, help="Thư mục xuất file ($REPORT_OUTPUT_DIR)")
    parser.add_argument("--query", default="", help="Tìm kiếm từ khóa Outlook")
    parser.add_argument("--days", type=int, default=7, help="Số ngày gần nhất")
    parser.add_argument("--max-results", type=int, default=30, help="Số email tối đa")
    parser.add_argument("--subject", default="", help="Lọc theo subject")
    parser.add_argument("--from-addr", default="", help="Lọc theo người gửi")
    parser.add_argument("--slug", default="outlook_digest", help="Prefix tên file output")
    parser.add_argument("--user-request", default="", help="Yêu cầu tổng hợp của user")
    parser.add_argument("--input-file", default="", help="Đường dẫn file email (.eml / .txt) cục bộ")
    args = parser.parse_args()

    out = os.path.abspath(args.output_dir)
    os.makedirs(out, exist_ok=True)

    query = build_query(args)
    print(f"\n{'=' * 60}\n▶ Outlook Email Fetch\n{'=' * 60}")
    print(f"  Query:       {query or '(all recent)'}")
    print(f"  Max results: {args.max_results}")
    print(f"  Output dir:  {out}")

    messages: List[Dict[str, Any]] = []

    # 1. Nếu có chỉ định file đính kèm trực tiếp
    if args.input_file and os.path.isfile(args.input_file):
        print(f"[*] Đọc email từ file chỉ định: {args.input_file}")
        messages = parse_local_email_file(args.input_file)
    else:
        # 2. Kiểm tra xem user có đính kèm file .eml nào trong thư mục làm việc không
        local_files = find_uploaded_email_files(out)
        if local_files:
            print(f"[*] Phát hiện {len(local_files)} file email đính kèm trong phiên: {[os.path.basename(f) for f in local_files]}")
            for lf in local_files:
                messages.extend(parse_local_email_file(lf))

    # 3. Nếu chưa có email từ file, kết nối qua máy chủ Outlook (Graph API / IMAP)
    if not messages:
        try:
            messages = fetch_messages(query, args.max_results)
        except SystemExit as se:
            # Nếu fetch thất bại vì mạng bị chặn, kiểm tra lại xem có file nào khác không
            if not messages:
                sys.exit(se.code)
        except Exception as e:
            print(f"❌ Lỗi khi lấy email từ Outlook: {e}", file=sys.stderr)
            sys.exit(1)

    if not messages:
        print("[!] Không tìm thấy email nào phù hợp.", file=sys.stderr)

    vault_entries = []
    safe_messages = []
    redacted_count = 0

    for msg in messages:
        processed = process_message(
            msg.get("subject") or "",
            msg.get("body") or "",
            msg.get("snippet") or "",
            msg.get("id") or "unknown",
        )
        refs = []
        for item in processed["vault_items"]:
            refs.append(item["ref"])
            vault_entries.append(
                {
                    "ref": item["ref"],
                    "message_id": msg.get("id"),
                    "reason": item["reason"],
                    "ciphertext": encrypt_text(item["original"]),
                }
            )
        if processed["is_sensitive"]:
            redacted_count += 1

        safe_messages.append(
            {
                "id": msg.get("id"),
                "thread_id": msg.get("thread_id"),
                "date": msg.get("date"),
                "from": msg.get("from"),
                "to": msg.get("to"),
                "cc": msg.get("cc", ""),
                "subject": processed["subject_safe"],
                "snippet": processed["snippet_safe"],
                "body": processed["body_safe"],
                "has_attachments": msg.get("has_attachments", False),
                "is_sensitive": processed["is_sensitive"],
                "redaction_refs": refs,
            }
        )

    version = next_version(out, args.slug)
    base = f"{args.slug}_v{version}"

    safe_doc = {
        "version": version,
        "fetched_at": date.today().isoformat(),
        "query": query,
        "user_request": args.user_request,
        "stats": {
            "total_messages": len(safe_messages),
            "sensitive_messages": redacted_count,
            "vault_items": len(vault_entries),
        },
        "messages": safe_messages,
        "_notice": "File này đã redact nội dung nhạy cảm. KHÔNG Read file *_vault.enc.",
    }

    safe_path = os.path.join(out, f"{base}_safe.json")
    with open(safe_path, "w", encoding="utf-8") as f:
        json.dump(safe_doc, f, ensure_ascii=False, indent=2)

    vault_path = os.path.join(out, f"{base}_vault.enc")
    vault_doc = {"version": 1, "items": vault_entries}
    with open(vault_path, "w", encoding="utf-8") as f:
        f.write(encrypt_text(json.dumps(vault_doc, ensure_ascii=False)))

    meta_path = os.path.join(out, f"{base}_meta.json")
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "safe_json": os.path.basename(safe_path),
                "vault_enc": os.path.basename(vault_path),
                "stats": safe_doc["stats"],
            },
            f,
            ensure_ascii=False,
            indent=2,
        )

    print(f"\n✅ Safe JSON:  {safe_path}")
    print(f"🔒 Vault:      {vault_path} (AI KHÔNG được Read)")
    print(f"📊 Stats:      {safe_doc['stats']}")


if __name__ == "__main__":
    main()

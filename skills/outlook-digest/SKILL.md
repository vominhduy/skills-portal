---
name: outlook-digest
description: "Đọc email Outlook/Office 365 qua Microsoft Graph API (MSAL / token cache) hoặc IMAP, redact/mã hoá nội dung nhạy cảm, và tổng hợp theo yêu cầu người dùng. Sử dụng khi cần: tổng hợp email, digest Outlook, recap inbox, tóm tắt mail tuần, theo dõi thread email dự án. Trigger khi user nói: đọc outlook, tổng hợp email outlook, digest outlook, recap inbox outlook, tóm tắt email, mail tuần này, email từ khách hàng, hay bất kỳ yêu cầu nào liên quan đến đọc và tổng hợp Outlook."
---

# Outlook Digest

Skill đọc email Outlook / Office 365 qua **Microsoft Graph REST API** (cơ chế xác thực MSAL Device Flow / token cache ) hoặc IMAP Exchange dự phòng, **tự động redact + mã hoá** nội dung nhạy cảm (password, OTP, token, số thẻ, lương...) trước khi AI xử lý.

## Quy tắc bảo mật (BẮT BUỘC)

1. **CHỈ Read** file `*_safe.json` và `*_meta.json` trong `$REPORT_OUTPUT_DIR`
2. **CẤM Read** file `*_vault.enc` - chứa nội dung gốc đã mã hoá, AI không được truy cập
3. **CẤM** cố decode placeholder `[REDACTED:ref:reason]` hoặc vault
4. Khi tổng hợp, **không suy diễn** nội dung đã redact - chỉ ghi "nội dung nhạy cảm đã ẩn"
5. Kết nối Outlook: Ưu tiên dùng Microsoft Graph API qua tài khoản Office 365 / `token_cache.bin` (hoặc cấu hình App Password IMAP trong Cài đặt webapp)

## Quy trình

### Bước 0 - Kiểm tra yêu cầu user

Thu thập (hỏi 1 lần nếu thiếu):
- **Phạm vi thời gian** (mặc định 7 ngày)
- **Bộ lọc** (từ khóa, người gửi, subject)
- **Mục tiêu tổng hợp** (VD: "email về sprint FSM", "mail khách hàng cần follow-up")

### Bước 1 - Fetch (1 lệnh Bash)

> ⚠️ **FORMAT BẮT BUỘC** - guardrail chặn nếu thiếu prefix:

```bash
cd "$SKILL_DIR" && python3 scripts/run_outlook_digest.py \
  --days 7 --max-results 30 \
  --query "sprint OR client" \
  --user-request "Tổng hợp email sprint FSM, liệt kê action items" \
  --output-dir "$REPORT_OUTPUT_DIR"
```

| Tham số | Mô tả |
|---------|-------|
| `--days N` | Email N ngày gần nhất |
| `--max-results N` | Giới hạn số mail (mặc định 30) |
| `--query "..."` | Từ khóa tìm kiếm |
| `--from-addr "x@y.com"` | Lọc người gửi |
| `--subject "..."` | Lọc tiêu đề |
| `--user-request "..."` | Yêu cầu tổng hợp - ghi vào safe JSON |
| `--slug name` | Prefix file output (mặc định `outlook_digest`) |

### Bước 2 - Read safe JSON

> ⚠️ **CẤM** `wc`, `cat`, `python3 -c` để đọc JSON - guardrail chặn hoặc không cần thiết.  
> **CHỈ dùng tool Read** file trong `$REPORT_OUTPUT_DIR`:

```
outlook_digest_v1_safe.json   ← nội dung email đã redact
outlook_digest_v1_meta.json   ← stats (total_messages, sensitive_messages, …)
```

Không cần đếm dòng hay parse JSON bằng Bash - Read xong tổng hợp trực tiếp.

File safe chứa:
- Metadata email (from, date, subject - giữ visible, chỉ redact pattern secret thực sự)
- Body/snippet đã redact - placeholder `[REDACTED:ref:reason]` thay cho nội dung nhạy cảm
- `stats.sensitive_messages` - số mail có redaction
- `user_request` - yêu cầu tổng hợp

### Bước 3 - Tổng hợp + Write report

1. Read `$SKILL_DIR/assets/output_template.md` (format gợi ý)
2. Phân nhóm email theo chủ đề/thread
3. Tóm tắt theo `user_request`
4. **Write** `outlook_digest_vN_summary.md` vào `$REPORT_OUTPUT_DIR`

## Nội dung được coi là nhạy cảm (auto-redact)

| Loại | Ví dụ |
|------|-------|
| Password | `password: xxx`, `mật khẩu: xxx` |
| OTP/PIN | `OTP: 123456`, `mã xác thực` |
| API token | `sk-...`, `ghp_...`, `Bearer ...` |
| Private key | `-----BEGIN PRIVATE KEY-----` |
| Số thẻ | 13-19 chữ số (Luhn valid) |
| Lương/thu nhập | `lương: 30 triệu`, `salary:` |
| STK ngân hàng | `STK: 1234567890` |
| Subject nhạy cảm | password, payroll, confidential, NDA... → redact toàn body, **giữ subject visible** (để nhận diện email) |

## Môi trường runtime (webapp)

- **KHÔNG** `pip install` - dùng `.venv-skills` (requests, cryptography, msal)
- **KHÔNG** `curl` test Outlook thủ công
- **KHÔNG** Read `*_vault.enc`
- **KHÔNG** `wc` / `cat` / `python3 -c` để đọc JSON - **CHỈ tool Read** `*_safe.json` / `*_meta.json`
- Env có sẵn: `OUTLOOK_ACCESS_TOKEN`, `OUTLOOK_VAULT_KEY`, `REPORT_OUTPUT_DIR`, `SKILL_DIR`

## Giao tiếp với user

- Không tường thuật chi tiết kỹ thuật redact/vault
- Báo 2 mốc: đang fetch → kết quả (tên file summary + số email + số mail redact)
- Nếu chưa kết nối Outlook → hướng dẫn đăng nhập Microsoft Graph (Device Flow) hoặc Cài đặt webapp

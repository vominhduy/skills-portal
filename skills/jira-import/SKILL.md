---
name: jira-import
description: >
  Import Sprint Backlog hoặc Waterfall Backlog từ file Excel lên Jira tự động bằng 2 script Python thuần.
  Skill sẽ chạy: Excel → excel_to_json.py → JSON → jira_rest_importer.py (tạo Stories + Sub-tasks).
  Trigger ngay khi user nói: "import sprint backlog", "tạo task trên jira từ excel", "upload backlog lên jira",
  "import excel jira", "tạo sprint trên jira", "cập nhật backlog jira", "import waterfall", hoặc gắn file Excel và nhờ tạo Jira issues.
---

# Jira Import (Python Scripts)

Skill sử dụng **2 script Python thuần** thay vì MCP Jira tools.
Hỗ trợ **2 luồng import**:
- 🟢 **Có Sprint (Agile)** - Story được gán vào Sprint + Epic parent
- 🔵 **Không Sprint (Waterfall / chưa có sprint)** - Story được tạo thẳng dưới Epic, không gán sprint

## Thông tin cố định

| Thông số          | Giá trị                          |
|-------------------|----------------------------------|
| Jira Site         | foxproject.atlassian.net        |
| Scripts           | `scripts/excel_to_json.py` và `scripts/jira_rest_importer.py` |
| JSON tạm          | `$REPORT_OUTPUT_DIR/sprint_data.json` |
| Jira credentials  | Biến môi trường `JIRA_EMAIL`, `JIRA_API_TOKEN` (webapp inject từ Cài đặt - KHÔNG hỏi user, KHÔNG truyền `--email`/`--api-token`) |

## Quy trình

```
[Excel file] → [Bước 0: hỏi user thông tin cấu hình]
                                    ↓
               [Bước 1: chạy excel_to_json.py] → [output JSON]
                                                        ↓
                              ┌─────────────────────────┴──────────────────────────┐
                     sprint có giá trị?                                   sprint trống / "không"
                              │                                                     │
             🟢 [Luồng AGILE] │                                  🔵 [Luồng WATERFALL]
         Tìm Sprint ID → gán sprint                           Bỏ qua sprint → tạo Story
         Story + Sub-tasks trong Sprint                       thẳng dưới Epic (không sprint)
                              └─────────────────────────┬──────────────────────────┘
                                                        ↓
                                           [Bước 3: báo cáo kết quả]
```

---

## Bước 0 - Hỏi user các giá trị cấu hình

**Trước khi làm bất cứ điều gì**, hỏi user xác nhận các giá trị sau. Hỏi dưới dạng danh sách rõ ràng:

> Trước khi import, bạn xác nhận các thông tin nhé:
>
> 1. **Project key** (ví dụ: `FCR`)
> 2. **Parent Request** - issue cha của các Story (ví dụ: `FCR-20`)
> 3. **Fix Version** - tên version trên Jira (ví dụ: `FTI-FCR v1.7 Sprint 3`)
> 4. **Division** - đơn vị (ví dụ: `FTI`)
> 5. **Loại dự án / có gán Sprint không?**
>    - Nếu **Agile (có sprint)**: cung cấp **Sprint name** (ví dụ: `FTI-FCR V1.7 Sprint 3`)
>    - Nếu **Waterfall** hoặc **không gán sprint**: để trống hoặc ghi `không`
>    → Khi không có sprint, Story được tạo thẳng dưới Epic mà không cần Sprint.
> 6. **Board name** *(chỉ cần khi Agile)* - tên Scrum board (ví dụ: `FCR board`). Bỏ trống nếu chỉ có 1 board. Cần khi sprint mới rỗng (chưa có issue) → JQL không tìm được sprint ID → dùng Agile API với board này. Nếu Waterfall → bỏ trống.
>
> Và tên sheet trong file Excel? (mặc định là: `Plan`)

Chờ user trả lời đầy đủ rồi mới chuyển sang Bước 1.

### Xác định luồng sau Bước 0

| Điều kiện | Luồng | SPRINT_NAME truyền vào script |
|-----------|-------|-------------------------------|
| User cung cấp Sprint name (không rỗng, không phải "không") | 🟢 **Agile** | Tên sprint thật |
| User để trống Sprint, ghi "không", hoặc nói "waterfall" | 🔵 **Waterfall** | `""` (chuỗi rỗng) |

Board name chỉ có nghĩa khi **Agile**. Nếu Waterfall → truyền `""` cho cả BOARD_NAME.

---

## ⛔ Quy tắc bắt buộc - KHÔNG đọc file Excel

**Claude KHÔNG ĐƯỢC dùng bất kỳ tool nào để đọc, mở, hoặc parse file Excel trực tiếp.**

- ❌ Không dùng `view`, `bash_tool`, `create_file` hay bất kỳ tool nào để đọc nội dung file `.xlsx`
- ❌ Không dùng Python/pandas/openpyxl trong context của Claude để đọc Excel
- ✅ Toàn bộ dữ liệu từ Excel chỉ được lấy qua file JSON output của script ở Bước 1 - **excel_to_json.py**
- Không dùng MCP Jira tools (`createJiraIssue`, `lookupJiraAccountId`, `searchJiraIssuesUsingJql`, …).

Mục đích: tránh tốn token không cần thiết. Script Python đã xử lý Excel và chuẩn hóa dữ liệu - Claude chỉ việc đọc JSON kết quả.

---

## Bước 1 - Chạy Python script

Script nằm tại `scripts/excel_to_json.py` trong thư mục skill (`$SKILL_DIR`). Chạy bằng Bash:

```bash
cd "$SKILL_DIR" && python3 scripts/excel_to_json.py \
  "<đường dẫn file Excel>" \
  "$REPORT_OUTPUT_DIR/sprint_data.json" \
  "<sheet name>" \
  "<PROJECT>" \
  "<PARENT_REQUEST>" \
  "<FIX_VERSION>" \
  "<DIVISION>" \
  "<SPRINT_NAME hoặc '' nếu Waterfall>" \
  "<BOARD_NAME hoặc '' nếu không dùng>"
```

Script nhận **9 arguments** theo thứ tự:

```
argv[1] = đường dẫn file Excel
argv[2] = đường dẫn output JSON
argv[3] = tên sheet trong Excel
argv[4] = PROJECT        (từ Bước 0)
argv[5] = PARENT_REQUEST (từ Bước 0)
argv[6] = FIX_VERSION    (từ Bước 0)
argv[7] = DIVISION       (từ Bước 0)
argv[8] = SPRINT_NAME    (từ Bước 0 - để "" nếu Waterfall/không sprint)
argv[9] = BOARD_NAME     (từ Bước 0 - để "" nếu Waterfall hoặc không cần)
```

> **Quy tắc truyền SPRINT_NAME:**
> - 🟢 Agile: truyền tên sprint thật, ví dụ `"FTI-FCR V1.7 Sprint 3"`
> - 🔵 Waterfall: truyền `""` - script sẽ ghi `"sprint": null` vào JSON → importer bỏ qua sprint

**Ví dụ lệnh Waterfall:**
```bash
cd "$SKILL_DIR" && python3 scripts/excel_to_json.py \
  "/path/to/project_plan.xlsx" \
  "$REPORT_OUTPUT_DIR/sprint_data.json" \
  "Plan" \
  "FCR" "FCR-20" "FTI-FCR v1.7" "FTI" "" ""
```

**Lưu ý:**
- **KHÔNG** `pip install` - dependency (`openpyxl`, `requests`…) đã cài sẵn trong `webapp/.venv-skills`.
- **KHÔNG** `find /mnt/skills /mnt/user-data` - dùng trực tiếp `$SKILL_DIR/scripts/excel_to_json.py`.
- Output JSON luôn ghi vào `$REPORT_OUTPUT_DIR/sprint_data.json`.
- Script tự động nhận diện header ở dòng 8 (hoặc 6), đọc sheet `Plan` (hoặc sheet được chỉ định), tự động map Story (theo SUM/EPIC) và Sub-tasks, dừng trước section `Timeline & Milestones`.

Sau khi chạy, đọc output JSON (`$REPORT_OUTPUT_DIR/sprint_data.json`) và thông báo cho user:
- Số stories và tổng số tasks tìm được
- **Xác nhận luồng đang dùng**: 🟢 Agile (sprint: `<tên>`) hoặc 🔵 Waterfall (không sprint)

---

## Bước 2 - Chạy jira_rest_importer.py

Script tự đọc field `"sprint"` từ JSON để quyết định luồng tự động:

| Giá trị `"sprint"` trong JSON | Hành vi |
|-------------------------------|---------|
| `"v3.1 Sprint 2"` (có giá trị) | 🟢 Tìm Sprint ID → gán Story vào Sprint |
| `null` | 🔵 Bỏ qua sprint hoàn toàn, tạo Story thẳng dưới Epic |

Chạy script bằng Bash - **KHÔNG truyền `--email`/`--api-token`**:

```bash
cd "$SKILL_DIR" && python3 scripts/jira_rest_importer.py "$REPORT_OUTPUT_DIR/sprint_data.json"
```

Hoặc ghi đè board name (chỉ cần cho Agile khi sprint rỗng chưa có issue):

```bash
cd "$SKILL_DIR" && python3 scripts/jira_rest_importer.py "$REPORT_OUTPUT_DIR/sprint_data.json" --board-name "<BOARD_NAME>"
```

**Tùy chọn:**
- `--dry-run` - chạy thử, không tạo thật (nên chạy trước nếu user yêu cầu kiểm tra).
- `--resume` + `--state-file "$REPORT_OUTPUT_DIR/import_state.json"` - tiếp tục import nếu bị gián đoạn.

```bash
cd "$SKILL_DIR" && python3 scripts/jira_rest_importer.py "$REPORT_OUTPUT_DIR/sprint_data.json" --dry-run
```

**Dọn dẹp JSON sau import:** Nếu cả 2 script đều chạy thành công (exit code 0, không có dòng `[ERROR]` trong output), xóa file JSON trung gian:

```bash
rm -f "$REPORT_OUTPUT_DIR/sprint_data.json" "$REPORT_OUTPUT_DIR/sprint_data.state.json"
```

Nếu import thất bại một phần hoặc có lỗi → **giữ lại** JSON để có thể `--resume` lần sau.

**Xử lý thiếu credentials:** Nếu script báo lỗi `Thiếu JIRA_EMAIL / JIRA_API_TOKEN (env)` → thông báo user:
> Chưa lưu Jira credentials. Bạn vào **Cài đặt** nhập Email Jira + API Token (tạo tại https://id.atlassian.com/manage-profile/security/api-tokens), lưu lại rồi chạy lại skill.

**KHÔNG** tự hỏi user nhập email/token trực tiếp trong chat - credentials phải lưu qua Cài đặt để webapp inject an toàn qua env (không leak qua `ps`/history).

---

## Bước 3 - Báo cáo kết quả

Sau khi hoàn tất toàn bộ import, tổng hợp và trình bày kết quả theo format sau:

### Dòng tóm tắt

```
✅ Import hoàn tất [🟢 Agile - Sprint: <tên sprint> | 🔵 Waterfall]: X/Y Stories thành công | Z/W Sub-tasks thành công
```

### Bảng Stories đã tạo

| # | Story Key | Summary | Sub-tasks | Link |
|---|-----------|---------|-----------|------|
| 1 | FCR-25 | Tạo mới yêu cầu thanh lý... | 5/5 ✅ | [FCR-25](https://foxproject.atlassian.net/browse/FCR-25) |
| 2 | FCR-26 | Phê duyệt yêu cầu... | 3/4 ⚠️ | [FCR-26](https://foxproject.atlassian.net/browse/FCR-26) |

Link format: `https://foxproject.atlassian.net/browse/<issue-key>`

### Cảnh báo (nếu có)

**Stories thất bại** (nếu `failed_stories` không rỗng):
```
❌ Stories không tạo được:
- "Tên story" - Lý do lỗi
```

**Sub-tasks thất bại** (nếu `failed_subtasks` không rỗng):
```
❌ Sub-tasks không tạo được:
- "Tên subtask" (thuộc FCR-XX) - Lý do lỗi
```

**Assignee không resolve được** (nếu `unresolved_assignees` không rỗng):
```
⚠️ Assignee chưa gán được (sub-tasks vẫn tạo thành công, không có assignee):
- Nguyen Van A
- Tran Thi B
```

Nếu không có lỗi và không có unresolved assignee → kết thúc bằng:
```
🎉 Tất cả issues đã được tạo thành công!
```

---
name: "weekly-report-api"
description: "Tạo báo cáo tiến độ tuần (Weekly Report) cho cả dự án Agile/Scrum (có sprint) và dự án Waterfall/Kanban (không sprint). Sử dụng khi cần: báo cáo tuần, báo cáo sprint, tổng kết tiến độ, weekly status update, sprint progress report, waterfall status report. Hỗ trợ 3 nguồn dữ liệu: Jira REST API, Google Sheets (service account), và Excel (.xlsx). Trigger khi user nói: báo cáo tuần, làm weekly report, tổng kết tuần, update tiến độ, làm report sprint, report waterfall, báo cáo cho stakeholder, hay bất kỳ yêu cầu nào liên quan đến tạo báo cáo tuần."
---

## ⚠️ CẢNH BÁO QUAN TRỌNG - Đọc TRƯỚC KHI CHẠY

**PHẢI** kiểm tra input của user về:
1. **Loại dự án / Phương pháp quản lý:**
   - **🟢 Agile / Scrum (có sprint)**: Cần `project-key` + `sprint-name` (hoặc `sprint-id`).
   - **🔵 Waterfall / Kanban (không có sprint)**: **KHÔNG ĐƯỢC HỎI SPRINT NAME/ID**. Dùng cờ `--waterfall`. Có thể kèm theo `--fix-version` / `--jql` / `--start-date` / `--end-date` nếu user cung cấp.
2. **Nguồn dữ liệu:**
   - **NẾU user cung cấp Google Sheet ID** (ví dụ: "1lYJrm...", "sheet id là...", "đọc từ Sheet...", **"data google sheet"**) → **BẮT BUỘC** dùng `--sheet-id`
   - **NẾU user gửi file Excel** (.xlsx) → **BẮT BUỘC** dùng `--excel`
   - **NẾU không có Sheet/Excel** → Mặc định Jira API

Script `run_weekly_report.py` sẽ tự động fallback về Jira-only nếu thiếu `--sheet-id`/`--excel`.

> ⚠️ **TRƯỜNG HỢP ĐẶC BIỆT**: Nếu user nói **"data google sheet (ID), start/due sprint lấy từ jira"** → vẫn **PHẢI dùng `--sheet-id`** vì backlog từ Sheet! Script sẽ tự động lấy sprint dates từ Jira trước, rồi lấy backlog từ Sheet (Bước 1/3 + 2/3).

> 🛑 **XỬ LÝ LỖI XÁC THỰC & MÃ DỰ ÁN**:
> - Nếu pipeline báo lỗi `LỖI MÃ DỰ ÁN` (mã dự án không tồn tại trên Jira hoặc tài khoản chưa được cấp quyền truy cập): **DỪNG LẠI** và thông báo người dùng kiểm tra lại mã dự án chính xác (ví dụ: FCR, FSM, ISC, SAL...). **TUYỆT ĐỐI KHÔNG** báo nhầm sang lỗi hết hạn token.
> - Nếu pipeline báo lỗi `Thiếu credential`, `LỖI XÁC THỰC JIRA`, hoặc `HTTP 401 Unauthorized` khi kiểm tra auth: **DỪNG LẠI NGAY LẬP TỨC**. Thông báo lịch sự cho người dùng: *"Không thể kết nối tới Jira do thông tin xác thực (Jira Email / API Token) chưa được cấu hình hoặc đã hết hạn. Vui lòng vào mục Cài đặt cá nhân để cập nhật token hợp lệ."*
> - **TUYỆT ĐỐI CẤM** chạy lệnh Bash để truy vấn database (`psql`, `mysql`...), đọc file cấu hình hệ thống (`.env`, backend source code), hoặc gọi công cụ email (`mcp__outlook_*`, `mcp__gmail_*`) để tìm kiếm token. Mọi hành vi này đều vi phạm nghiêm trọng chính sách bảo mật của hệ thống.

## Nguồn dữ liệu hỗ trợ

| Nguồn | Yêu cầu |
|-------|---------|
| Jira REST API | Email + API token (Agile: Sprint; Waterfall: JQL / FixVersion / Project) |
| Google Sheets | Service account JSON key |
| Excel (.xlsx / SharePoint) | File .xlsx cục bộ hoặc link chia sẻ SharePoint/OneDrive (Microsoft Graph API) |

---

## Quy tắc bắt buộc - Kiểm tra nguồn dữ liệu TRƯỚC KHI CHẠY

KHÔNG bao giờ tự động bắt đầu tạo output khi user mới đặt yêu cầu.

Quy trình chuẩn:
1. **TRƯỚC TIÊN**: Kiểm tra xem user có cung cấp Google Sheet ID hoặc file Excel không
   - Tìm keyword: "google sheet", "sheet id", **"data google sheet"**, "spreadsheet", "1lYJrm...", ".xlsx"
   - **NẾU có Sheet ID/Excel → BẮT BUỘC dùng `--sheet-id` hoặc `--excel`**
   - **NẾU không có → Mặc định dùng Jira API**
2. **Kiểm tra phương pháp quản lý**:
   - Nếu user nói **"waterfall"**, **"không sprint"**, **"không có sprint"**, **"kanban"** → Chạy luồng **Waterfall**.
   - **⚠️ NẾU input có `parent_id: XYZ`** (ví dụ: "project key ISC, parent_id: ISC-20. Báo cáo tiến độ dự án Waterfall") → **BẮT BUỘC** dùng `--parent-key ISC-20`. Script sẽ tự động lấy `startDate` và `dueDate` từ Epic/Parent đó trên Jira để xác định timeline dự án. **KHÔNG** dùng `--waterfall` riêng lẻ khi đã có `parent_id`.
   - Nếu Waterfall nhưng **không có `parent_id`** → Dùng `--waterfall` (không hỏi sprint).
   - Nếu là Agile mà thiếu sprint name → hỏi sprint name.
3. Fetch data tự động (không cần xác nhận thêm) và tạo report.

---

## Môi trường runtime (webapp)

> ⚠️ **FORMAT COMMAND BẮT BUỘC**: Mọi lệnh Bash trong webapp **PHẢI** có prefix đầy đủ:
> ```bash
> cd "$SKILL_DIR" && python3 scripts/run_weekly_report.py ...
> ```

### Fast path - 1 lệnh Bash (ưu tiên, nhanh nhất)

#### 1. Luồng Agile (có sprint)
**Nguồn Jira (mặc định)**:
```bash
cd "$SKILL_DIR" && python3 scripts/run_weekly_report.py \
  --project-key FSM --sprint-name "Sprint 3" --today 2026-07-23 \
  --output-dir "$REPORT_OUTPUT_DIR"
```

**Nguồn Google Sheet / Excel**:
```bash
cd "$SKILL_DIR" && python3 scripts/run_weekly_report.py \
  --project-key FSM --sprint-name "Sprint 3" --today 2026-07-23 \
  --sheet-id "SHEET_ID" --service-account "$GOOGLE_SERVICE_ACCOUNT_PATH" \
  --output-dir "$REPORT_OUTPUT_DIR"
```

#### 2. Luồng Waterfall (không có sprint)
**Nguồn Jira - Theo Parent Request / Epic (Khuyến nghị)**:
Tự động lấy **Start Date**, **Due Date** và toàn bộ task con từ Parent Request / Epic:
```bash
cd "$SKILL_DIR" && python3 scripts/run_weekly_report.py \
  --project-key FSM --parent-key FSM-20 --today 2026-07-23 \
  --output-dir "$REPORT_OUTPUT_DIR"
```

**Nguồn Jira - Tổng quan toàn bộ project hoặc theo Version**:
```bash
cd "$SKILL_DIR" && python3 scripts/run_weekly_report.py \
  --project-key FSM --waterfall --today 2026-07-23 \
  --output-dir "$REPORT_OUTPUT_DIR"
```
*(Tùy chọn: có thể thêm `--fix-version "v1.0"`, `--start-date 2026-07-01`, `--end-date 2026-08-30`, hoặc `--jql "..."`)*

**Nguồn Google Sheet / Excel (Waterfall)**:
```bash
cd "$SKILL_DIR" && python3 scripts/run_weekly_report.py \
  --project-key FSM --waterfall --sheet-id "SHEET_ID" \
  --service-account "$GOOGLE_SERVICE_ACCOUNT_PATH" --today 2026-07-23 \
  --output-dir "$REPORT_OUTPUT_DIR"
```

Sau khi chạy pipeline xong và file `.md` được tạo, **tạo ngay bản tóm tắt rút gọn `.txt`** (`txtExpected`) theo **Quy tắc PM Sprint Summary** (xem mục bên dưới) trong cùng một lượt. **KHÔNG** gửi tin nhắn dở dang giữa chừng (như "file .md đã xong, bản .txt sẽ tạo ở bước sau"). Sau khi cả 2 file `.md` và `.txt` đã được tạo xong, gửi **1 tin nhắn báo cáo kết quả duy nhất** tóm tắt Health/SPI/RAG và nêu tên cả 2 file kết quả.

---
- **KHÔNG** `pip install` - dependency Python đã cài sẵn trong `webapp/.venv-skills` (`requests`, `openpyxl`, `gspread`, `google-auth`).
- **KHÔNG** `curl` / test mạng thủ công - script Python tự thử direct/proxy (`network_utils.py`); guardrail chặn curl.
- **KHÔNG** `unset` proxy - script tự fallback; webapp giữ HTTP_PROXY cho Google.
- **KHÔNG** Read `/tmp/claude-*` và **KHÔNG** dùng Glob/ls tìm kiếm ngoài `$REPORT_OUTPUT_DIR` (như `/data/outputs/*`). Mọi JSON/log/report nằm trong `$REPORT_OUTPUT_DIR`.
- **Chỉ** chạy script bằng Bash (`$SKILL_DIR` có sẵn trong env).

---

## Giao tiếp với user - không kể lể bước xử lý nội bộ

**CHECKLIST TRƯỚC KHI CHẠY SCRIPT:**
1. ✅ Đã kiểm tra xem user có cung cấp Google Sheet ID hoặc file Excel không?
2. ✅ Dự án là Agile (cần sprint) hay Waterfall (dùng `--waterfall` hoặc `--parent-key`)?
3. ✅ **NẾU input có `parent_id: XYZ`** → BẮT BUỘC dùng `--parent-key XYZ` (script tự lấy `startDate`/`dueDate` của Epic/Parent từ Jira để tính timeline dự án)!
4. ✅ Nếu có Parent Request / Epic key riêng biệt (VD: `FSM-20`, `parent FSM-20`, `parent_id: FSM-20`) → thêm `--parent-key FSM-20`!
5. ✅ Nếu có Sheet ID → đã thêm `--sheet-id` vào command?
6. ✅ Nếu có file Excel → đã thêm `--excel` vào command?
7. ✅ Nếu Waterfall / Parent Request → KHÔNG hỏi Sprint Name/ID!

Tuyệt đối **KHÔNG** tường thuật lại tên bước/thuật ngữ nội bộ của skill này trong câu trả lời cho user.

---

## Scripts

| Script | Nguồn | Mô tả |
|--------|-------|-------|
| `scripts/jira_sprint_fetcher.py` | Jira REST API | Lấy metadata & issues (hỗ trợ cả Agile Sprint & Waterfall JQL) |
| `scripts/weekly_report_generator.py` | Jira REST API | Fetch Jira → tính metrics → xuất JSON + Markdown (legacy) |
| `scripts/fetch_gsheet_data.py` | Google Sheets | Đọc Google Sheet qua service account → xuất JSON |
| `scripts/fetch_excel_data.py` | Excel (.xlsx) | Đọc file Excel → xuất JSON |
| `scripts/generate_report_from_json.py` | Tất cả | Đọc standardized JSON → generate Markdown (Agile & Waterfall) |
| `scripts/run_weekly_report.py` | Tất cả | 1 lệnh chạy toàn bộ pipeline tuần tự |
  --today 2026-07-23 \
  --output-dir "$REPORT_OUTPUT_DIR"
```

Script tự gọi `jira_sprint_fetcher.py --fetch-issues` rồi `generate_report_from_json.py`.

### Chỉ lấy sprint dates (không generate report)

```bash
python3 scripts/jira_sprint_fetcher.py \
    --project-key FSM \
    --sprint-name "Sprint 3" \
    --output-dir "$REPORT_OUTPUT_DIR"
```

Hoặc khi đã biết sprint ID:

```bash
python3 scripts/jira_sprint_fetcher.py \
    --project-key FSM \
    --sprint-id 1234 \
    --output-dir "$REPORT_OUTPUT_DIR"
```

Thêm `--fetch-issues` nếu cần export issues thủ công (thường không cần - dùng `run_weekly_report.py`).

### Kết hợp Jira dates + Google Sheet backlog

**Trường hợp phổ biến**: User nói *"data google sheet (ID), start/due sprint lấy từ jira"*

→ Backlog từ Sheet, sprint dates từ Jira → **PHẢI dùng `--sheet-id`**

```bash
cd "$SKILL_DIR" && python3 scripts/run_weekly_report.py \
  --project-key FSM \
  --sprint-name "Sprint 3" \
  --sheet-id "1lYJrm30p8cUqSuDFzsfAF7DYE5nDlmsv36JrRc2ZNQM" \
  --service-account "$GOOGLE_SERVICE_ACCOUNT_PATH" \
  --today 2026-07-28 \
  --output-dir "$REPORT_OUTPUT_DIR"
```

Pipeline tự động:
1. **Bước 1/3** - Lấy sprint start/end từ Jira (`jira_sprint_fetcher.py`)
2. **Bước 2/3** - Lấy backlog từ Google Sheet (`fetch_gsheet_data.py`)
3. **Bước 3/3** - Generate report kết hợp

> **KHÔNG** được bỏ qua `--sheet-id` chỉ vì user nhắc "start/due từ jira" - đó chỉ là hướng dẫn cho sprint dates, backlog vẫn từ Sheet!

### Kết hợp Jira dates + Google Sheet backlog (cách thủ công, 2 script riêng)

Chỉ khi backlog nằm trên Sheet, sprint dates vẫn lấy từ Jira:

```bash
python3 scripts/fetch_gsheet_data.py \
    --sheet-id 1lYJrm30p8cUqSuDFzsfAF7DYE5nDlmsv36JrRc2ZNQM \
    --service-account "$GOOGLE_SERVICE_ACCOUNT_PATH" \
    --sprint-name "Sprint 3" \
    --today 2026-07-23 \
    --output-dir "$REPORT_OUTPUT_DIR" \
    --sprint-info "$REPORT_OUTPUT_DIR/FSM_Sprint_3_sprint_info.json"
```

Rồi generate report - JSON đã có `sprint_start`/`sprint_end`/`project_key`, không cần truyền lại:

```bash
python3 scripts/generate_report_from_json.py \
    --input "$REPORT_OUTPUT_DIR/gsheet_data_Sprint_3.json" \
    --output-dir "$REPORT_OUTPUT_DIR" \
    --today 2026-07-23
```

### Cấu hình & Chạy (legacy all-in-one)

```python
# weekly_report_generator.py vẫn hardcode FCR - ưu tiên jira_sprint_fetcher + generate_report_from_json
PROJECT_KEY = "FCR"
SPRINT_NAME = "FTI-FCR V1.7 Sprint 4"
SPRINT_ID = 1355
OUTPUT_DIR = os.environ["REPORT_OUTPUT_DIR"]
```

```bash
python3 scripts/weekly_report_generator.py "$JIRA_EMAIL" "$JIRA_API_TOKEN"
```

### API Endpoints

| Mục đích | Method | Endpoint |
|----------|--------|----------|
| Tìm board | GET | `/rest/agile/1.0/board?projectKeyOrId={key}` |
| Tìm sprint | GET | `/rest/agile/1.0/board/{id}/sprint?state=active,future,closed` |
| Search issues | POST | `/rest/api/3/search/jql` |
| Auth | - | Basic Auth: `base64(email:api_token)` |

> API `/rest/api/3/search/jql` dùng token-based pagination (`nextPageToken` + `isLast`).

> **Múi giờ:** mọi timestamp Jira trả về (`startDate`, `endDate`, `duedate`, `resolutiondate`...) là
> UTC (hậu tố `Z`). `parse_date()`/`fmt_date()` trong `generate_report_from_json.py` đã tự convert sang
> UTC+7 trước khi lấy phần ngày - KHÔNG bao giờ cắt chuỗi ISO tại `"T"` để lấy ngày trực tiếp, vì giờ
> UTC ≥ 17:00 sẽ lệch sang ngày hôm sau ở VN (VD `"...T17:00:06Z"` = `00:00` giờ VN ngày kế tiếp).

---

## Nguồn 2: Google Sheets

### Yêu cầu
- Service account JSON key file (đã cấp quyền Viewer cho sheet)
- Google Sheet ID

### Cấu hình & Chạy

```bash
python scripts/fetch_gsheet_data.py \
    --sheet-id <SPREADSHEET_ID> \
    --service-account "$GOOGLE_SERVICE_ACCOUNT_PATH" \
    --sprint-name "Sprint 3" \
    --today 2026-07-21 \
    --output-dir "$REPORT_OUTPUT_DIR"
```

### Tự động nhận diện format

Script tự phát hiện format sheet dựa trên header (giống hệt logic của `fetch_excel_data.py` - cùng 1 template có thể upload dạng Excel hoặc chia sẻ dạng Google Sheet link, kết quả JSON như nhau):

| Format | Dấu hiệu nhận biết | Output |
|--------|-------------------|--------|
| **Sprint Backlog** | Có cột "US ID", "Module/Feature", "Task", "PIC" | Input trực tiếp từ output của skill `sprint-planning` - không cần convert |
| **Jira Export** | Có cột "Issue key", "Issue Type", "Status" | Stories + Subtasks chi tiết |
| **Generic (template khác)** | Header không khớp 2 format trên, nhưng vẫn nhận diện được cột task/summary, status, estimate, start/due date, assignee qua từ khoá gần đúng | Stories dạng flat (không phân cấp subtask) |

> Nếu 1 sheet không match được cột nào theo header (kể cả generic), script fallback về đọc theo vị trí cột thô (cột 1 = id, cột 2 = summary, cột 3 = status).

### Setup Service Account

1. Tạo Service Account trên Google Cloud Console
2. Download JSON key file
3. Chia sẻ Google Sheet với email của Service Account (quyền Viewer)
4. Truyền path JSON key qua `--service-account`

---

## Nguồn 3: Excel (.xlsx)

### Yêu cầu
- File Excel (.xlsx) - export từ Jira hoặc spreadsheet thủ công
- File .xlsx upload qua webapp hoặc path trong uploads/

### Cấu hình & Chạy

```bash
python scripts/fetch_excel_data.py \
    --file <path_to_excel.xlsx> \
    --sprint-name "Sprint 3" \
    --today 2026-07-21 \
    --output-dir "$REPORT_OUTPUT_DIR" \
    --sheet-name "Sheet1"  # tùy chọn
```

### Hỗ trợ nhiều format

Tự nhận diện qua header:

| Format | Dấu hiệu nhận biết | Ghi chú |
|--------|-------------------|---------|
| **Sprint Backlog** | Có cột "US ID", "Module/Feature", "Task", "PIC" | Input trực tiếp từ output của skill `sprint-planning` - không cần convert |
| **Jira Export** | Có cột "Issue key", "Issue Type", "Status" | Stories + Subtasks chi tiết |
| **Generic (template khác)** | Header không khớp 2 format trên, nhưng vẫn nhận diện được cột task/summary, status, estimate, start/due date, assignee qua từ khoá gần đúng | Stories dạng flat (không phân cấp subtask) |

---

## Bước 3: Generate Report từ JSON

Sau khi có file JSON từ bất kỳ nguồn nào:

```bash
python scripts/generate_report_from_json.py \
    --input <data.json> \
    --output-dir "$REPORT_OUTPUT_DIR" \
    --sprint-start 2026-07-01 \
    --sprint-end 2026-08-05 \
    --today 2026-07-21 \
    --project-key FSM \
    --sprint-name "Sprint 3"
```

Nếu không truyền `--sprint-start/end`, script tự detect từ JSON (Jira format có sẵn).

---

## Metrics - sub-task only (story = group)

Mọi metric **Actual Progress**, **Weighted Phase**, **RAG** tính trên **sub-task** (`issuetype = Sub-task`).
Story/Epic chỉ dùng để **group** trong Sprint Progress và roll-up RAG story-level.

---

## ② Actual Progress - Weighted Phase (taskProcess từ Jira `customfield_10790`)

| taskProcess value | Phase (báo cáo) | Trọng số |
|-------------------|-----------------|----------|
| Requirement & Design | Requirement | 15% |
| Coding | Development | 50% |
| Testing / Test | Testing | 15% |
| Deployment / Deploy / UAT | Deployment | 10% |
| Khác / null | Other | 10% |

**Progress từng sub-task:**

| Status sub-task | Progress tính vào phase |
|-----------------|---------------------------|
| **Done** | `originalEstimate` (100%) |
| **In review** | `originalEstimate` (100%) |
| In Progress / To Do / RE WORK / Blocked / ... | `timeSpent / originalEstimate × originalEstimate` (= spent, cap est) |

> Done và In review **luôn** 100% est - **KHÔNG** dùng timeSpent.

```python
for subtask in phase_subtasks:
    if subtask.status in ("Done", "In review", "In Review"):
        progress_phase += est_hours
    else:
        progress_phase += min(spent_hours, est_hours) if est_hours else spent_hours
pct_phase = progress_phase / total_est_phase * 100
Actual Progress = Σ (weight_phase × pct_phase)
```

**Fallback:** Không có `taskProcess` trên sub-task → effort-based thuần `progress / total est` (không weighted phase).

Phase trước đã xong (imputed): không còn sub-task phase trước nhưng sprint đã có phase sau → credit 100% phase trước.

---

## ④ RAG (duedate-based) - sub-task level

```
RAG % = (# sub-task có duedate ≤ today AND status Done/In review)
      / (# sub-task có duedate ≤ today) × 100
```

| RAG % | Status |
|-------|--------|
| ≥ 80% | On Track 🟢 |
| 50–79% | At Risk 🟡 |
| < 50% | Off Track 🔴 |

- **Story-level RAG**: roll-up từ sub-task của story đó
- **Sprint-level RAG**: aggregate toàn bộ sub-task sprint
- Blocked issues liệt kê trong Risks & Issues, không tự override RAG

---

## Phase Weights (legacy reference - xem bảng trên)

## Báo cáo Output

Markdown gồm 4 phần:
1. **Overall Status** - Health, Planned/Actual Progress, SPI, RAG
2. **Sprint Progress** - Done + Doing/Will do, viết theo quy tắc ở mục [Quy tắc viết Sprint Progress](#quy-tắc-viết-sprint-progress)
3. **Weighted Phase Breakdown** - Bảng 5 phase + tổng
4. **Risks & Issues** - tóm tắt ngắn gọn cùng quy tắc với phần 2

---

## Capacity table - Bắt buộc khi có overload

Khi có member nào có **total est trong kỳ tới > 40h** (capacity net 1 tuần), bắt buộc thêm bảng Capacity:

| Member | Tasks | Est (h) | Ghi chú |
|--------|-------|---------|---------|
| ...    | ...   | ...     | ⚠️ Overloaded nếu >40h |

Đề xuất redistribute cụ thể: task nào, chuyển sang ai, lý do.

---

## Chu kỳ báo cáo - cửa sổ trượt ±7 ngày quanh hôm nay

Mặc định KHÔNG snap về tuần lịch (T2–T6) - luôn tính theo ngày hiện tại, bất kể hôm nay là thứ mấy:

```
Cycle (Done)              = [today - 7 ngày, today]
Next window (Doing/Will do) = [today + 1 ngày, today + 7 ngày]
```

Nếu user chỉ định mốc bắt đầu khác (VD: "từ thứ 4 tuần trước", "từ 15/07"), dùng đúng ngày đó làm
`cycle_start` thay vì `today - 7`, các phần còn lại tính tương tự:

```
Cycle (Done) = [ngày user chỉ định, today]
Next window  = [cycle_end + 1 ngày, cycle_end + 7 ngày]
```

Ghi rõ trong header báo cáo:
```
> 📌 Chu kỳ báo cáo: {cycle_start} – {cycle_end} (hôm nay).
> Chu kỳ tiếp theo: {next_start} – {next_end}.
```

---

## Quy tắc viết Sprint Progress

**Format mỗi dòng (chỉ liệt kê sub-task, %, PIC, ngày hoàn thành/hạn chót - không lấy story):**
```
- <Tên sub-task> (<% hoàn thành>%) - <PIC> - <DD/MM/YYYY>
```
- Nếu status = Done hoặc In review → ghi `(100%)`
- Nếu đang làm / chưa xong → ghi `(X%)` với X = round(spent/est × 100)
- Thêm `⚠️ At Risk` nếu due <= today và chưa Done/In review
- PIC: Tên người phụ trách (assignee)
- Ngày: Ngày kết thúc / hạn hoàn thành (`DD/MM/YYYY`)

**Ví dụ:**
```markdown
### ✅ Done
- Hỗ trợ nghiệm thu UAT - Đợt 1 (100%) - OanhNTK35 - 15/09/2026
- Regression & Vibe Test Round 2 & Report (100%) - AnhDC4 - 15/09/2026

### ▶ Doing / Will do
- Deploy Production & Smoke test (0%) - VuNT60 - 23/09/2026
- Monitor logs/performance & Hotfix background (0%) - huynt78 - 25/09/2026
```

**### ✅ Done**
- Các sub-task đã Done hoặc In review trong chu kỳ báo cáo (tính theo duedate trong kỳ)

**### ▶ Doing / Will do**
- Tất cả sub-task đang In Progress, To Do có duedate trong kỳ hoặc kỳ tới - gộp chung một section
- Sắp xếp: overdue/at-risk trước, due date tăng dần
---

## Versioning output - không ghi đè

Mỗi lần generate report **bắt buộc tăng version** - **không ghi đè** file `.md`/`.txt` cũ.

| Thành phần | Quy tắc |
|------------|---------|
| Markdown | `{PROJECT}_{SPRINT}_report_v{N}.md` - script tự chọn N tiếp theo |
| Manifest | `{PROJECT}_{SPRINT}_report_latest.json` - trỏ `md`, `txtExpected`, `version` |
| PM Summary .txt | `{PROJECT}_{SPRINT}_report_v{N}.txt` - tạo ngay sau khi có `.md` (cùng version N theo `txtExpected`) |
| Legacy | File cũ `*_report.md` (không _vN) được coi là v1 khi đếm version |

> 📌 **Output của skill gồm 2 file chính thức**:
> 1. **File `.md`**: Báo cáo chi tiết đầy đủ (được tạo bởi pipeline Python).
> 2. **File `.txt`**: Bản tóm tắt rút gọn PO/PMO (được viết ngay sau khi có `.md` theo quy tắc bên dưới).

---

## Bản .txt - PM Sprint Summary (Quy tắc tạo bản rút gọn)

Ngay sau khi script xuất `{PROJECT}_{SPRINT}_report_v{N}.md`, lấy dữ liệu từ Section 1 (Metrics), Section 2 (Sprint Progress) và Section 4 (Risks & Issues) trong file `.md` vừa tạo để viết file `{PROJECT}_{SPRINT}_report_v{N}.txt` (đúng tên `txtExpected` trong log/manifest) bằng công cụ `Write` (hoặc `write_to_file`).

### Quy tắc biên soạn (Cấp Lãnh đạo & PO)
- **Định dạng Bullet bắt buộc**: Mọi dòng nội dung trong các mục (Done, Doing/Will do, Risks) **BẮT BUỘC** có tiền tố `- `.
- **Ngôn ngữ quản trị, đắt giá & ngắn gọn (Rule tóm tắt chuẩn)**: Mỗi dòng súc tích, **tối đa 12 từ** (khoảng 3–10 từ, tuyệt đối không vượt quá 12 từ), đi thẳng vào deliverable/kết quả hoặc trọng tâm kế hoạch. Tối đa 3–5 dòng cho mỗi mục.
- **TỔNG HỢP & VIẾT LẠI CÔ ĐỌNG (Synthesize / Paraphrase)**: Thay vì sao chép cả câu dài từ Jira, **bắt buộc tự tổng hợp và viết lại thành cụm danh từ ngắn gọn** (nhỏ hơn 12 từ), đủ nghĩa, đúng chuẩn ngữ pháp PM và truyền tải trọn vẹn kết quả.
- **TUYỆT ĐỐI KHÔNG ĐỂ CÂU DÀI THÔ & KHÔNG CẮT CỤT CƠ HỌC**:
  - **Không** giữ nguyên câu dài thô từ Jira/Backlog vào bản tóm tắt.
  - **Không** ngắt cứng cơ học làm đứt đoạn từ ghép / ngữ nghĩa / bổ ngữ cuối câu (ví dụ: không để câu bị cụt lửng như `... log server & Hỗ`, `... Phê duyệt điều kiện`, `... Test Scenarios chi tiết cho`, `... thực hiện kiểm thử chức`).

#### 💡 Bảng đối chiếu viết lại (Synthesize vs Lỗi câu dài / Cắt cụt cơ học):
| Input thô từ Jira / File .md | ❌ Lỗi câu dài / Hard Truncation | ✅ Viết lại chuẩn PM (Synthesize <= 12 từ) |
| :--- | :--- | :--- |
| *Hỗ trợ nghiệp vụ cho DEV và QC, chuẩn bị kịch bản UAT và tài liệu HDSD...* | `- Hỗ trợ nghiệp vụ cho DEV và QC, chuẩn bị` *(Cụt chữ)*<br>`- Hỗ trợ nghiệp vụ cho DEV và QC, chuẩn bị tài liệu bàn giao UAT và quy trình hướng dẫn` *(Quá dài: > 12 từ)* | `- Nghiệm thu UAT & tài liệu HDSD` *(7 từ)* |
| *Chuẩn bị test case và thực hiện kiểm thử chức năng cho Sprint 4...* | `- Chuẩn bị test case và thực hiện kiểm thử chức` *(Cụt chữ)*<br>`- Chuẩn bị test case & thực hiện kiểm thử chức năng phân hệ ZNS nâng cao` *(Quá dài: > 12 từ)* | `- Kiểm thử chức năng Sprint 4` *(5 từ)* |
| *Chuẩn bị môi trường và tài liệu phục vụ CSOC Pentest...* | `- Chuẩn bị môi trường và tài liệu phục vụ CSOC` *(Cụt chữ)* | `- Chuẩn bị môi trường Pentest CSOC` *(5 từ)* |
| *Hỗ trợ CSOC pentest và phân loại các lỗ hổng bảo mật phát hiện được...* | `- Hỗ trợ CSOC pentest và phân loại các lỗ hổng` *(Cụt chữ)* | `- Hỗ trợ Pentest & phân loại lỗ hổng` *(7 từ)* |
| *Thực hiện Unit test, deploy staging và fix bug trong quá trình...* | `- Thực hiện Unit test, deploy staging và fix bug` *(Cụt chữ)* | `- Deploy Staging & xử lý lỗi QC` *(7 từ)* |
| *Deploy bản build hoàn thiện Sprint 2 lên môi trường Staging và nghiệm thu nội bộ...* | `- Deploy bản build hoàn thiện Sprint 2 lên môi trường Staging và nghiệm thu nội bộ` *(Quá dài: 16 từ)* | `- Nghiệm thu bản build Sprint 2 Staging` *(7 từ)* |

- **Loại bỏ toàn bộ Jira ID** (FSM-xxx, FCR-xxx, DEV-xxx, PROJ-xxx...).
- **Loại bỏ tên account/người thực hiện** (kể cả trong ngoặc đơn ở cuối dòng).
- **Mục DONE (Kết quả bàn giao)**: 
  - **Nguồn trích xuất bắt buộc**: Tổng hợp trực tiếp từ danh sách các **sub-task Done trong chu kỳ báo cáo** (khớp 100% với các sub-task tại Section 2 `### ✅ Done` của file `.md`).
  - **TUYỆT ĐỐI KHÔNG lấy tên User Story cha (Parent Issue)**: Không tự tiện bốc tên User Story cha từ Jira (ví dụ: `Khởi động Sprint...`, `Setup ban đầu...`) nếu nó không đại diện cho sub-task hoàn thành trong tuần. Việc này gây ra lỗi lệch pha, đưa deliverable ngoại lai vào file `.txt` mà file `.md` hoàn toàn không có, hoặc sai lệch ngữ cảnh thời gian (như báo cáo "khởi động sprint" khi sprint đã ở giai đoạn giữa/cuối).
  - Viết dạng danh từ / danh ngữ chỉ kết quả/sản phẩm (tối đa 12 từ/dòng), cực kỳ súc tích.
  - **KHÔNG** lặp từ "Hoàn thành..." một cách máy móc ở đầu mỗi dòng.
  - **KHÔNG** kể lể thao tác kỹ thuật con của dev/tester, không ghép câu dài lê thê.
- **Mục DOING / WILL DO (Kế hoạch & Trọng tâm)**:
  - Nêu rõ 3–5 đầu việc/mục tiêu trọng tâm tiếp theo từ các sub-task Doing/Will do tại Section 2 của file `.md` (tối đa 12 từ/dòng, trọn vẹn ngữ nghĩa).
  - **KHÔNG** đưa mốc ngày hoặc khoảng ngày (ví dụ `(due 09/09 - 10/09)`, `(Hạn 07/09)`) vào từng dòng.
- **Mục RISKS & ISSUES**: Tóm tắt tối đa 1 câu/rủi ro (tối đa 12 từ), ưu tiên rủi ro ảnh hưởng tiến độ chung hoặc go-live.

### Cấu trúc định dạng (Templates)

**Dạng 1 (Tiêu đề done: / doing:)**:
```
done:
- {Deliverable / Hạng mục hoàn thành 1 (nhỏ hơn 12 từ)}
- {Deliverable / Hạng mục hoàn thành 2 (nhỏ hơn 12 từ)}
- {Deliverable / Hạng mục hoàn thành 3 (nhỏ hơn 12 từ)}
doing: 
- {Đầu việc trọng tâm 1 (nhỏ hơn 12 từ)}
- {Đầu việc trọng tâm 2 (nhỏ hơn 12 từ)}
- {Kế hoạch / đầu việc tiếp theo (nhỏ hơn 12 từ)}
```

**Dạng 2 (Tiêu đề (Done) / (Doing/Will do))**:
```
(Done)
- {Deliverable / Hạng mục hoàn thành 1 (nhỏ hơn 12 từ)}
- {Deliverable / Hạng mục hoàn thành 2 (nhỏ hơn 12 từ)}
- {Deliverable / Hạng mục hoàn thành 3 (nhỏ hơn 12 từ)}
(Doing/Will do)
- {Đầu việc trọng tâm 1 (nhỏ hơn 12 từ)}
- {Đầu việc trọng tâm 2 (nhỏ hơn 12 từ)}
- {Kế hoạch / đầu việc tiếp theo (nhỏ hơn 12 từ)}
```

**Dạng 3 (Tiêu đề đầy đủ có Overall Status - Mặc định khuyến nghị)**:
```
Overall Status
{Tên dự án} · {Tên Sprint} - {ngày bắt đầu} - {ngày kết thúc}
- Health: {🟢 On Track / 🟡 At Risk / 🔴 Off Track} (SPI = {X.XX})
- Tiến độ: {Actual X%} / kế hoạch {Planned X%}
- Đúng hạn (RAG): {X%}

---

✅ Done
- {Deliverable / Kết quả hoàn thành 1 (nhỏ hơn 12 từ)}
- {Deliverable / Kết quả hoàn thành 2 (nhỏ hơn 12 từ)}
- {Deliverable / Kết quả hoàn thành 3 (nhỏ hơn 12 từ)}

▶ Doing / Will do
- {Đầu việc trọng tâm 1 (nhỏ hơn 12 từ)}
- {Đầu việc trọng tâm 2 (nhỏ hơn 12 từ)}
- {Kế hoạch / đầu việc tiếp theo (nhỏ hơn 12 từ)}

⚠️ Risks & Issues
- {Rủi ro 1 ảnh hưởng tiến độ hoặc go-live}
- {Rủi ro 2}
```

### 🛫 Preflight Checklist (Bắt buộc tự kiểm tra trước khi ghi file .txt)

Trước khi dùng `Write` / `write_to_file` xuất file `.txt`, **BẮT BUỘC** đối chiếu toàn bộ nội dung với checklist sau:

- [ ] **1. Giới hạn độ dài chuẩn tóm tắt (tối đa 12 từ/dòng)**: Đếm số từ từng dòng trong mục Done và Doing. Tuyệt đối **KHÔNG vượt quá 12 từ**, **KHÔNG giữ nguyên câu dài thô** từ Jira, và **KHÔNG cắt cụt từ/ngữ cơ học**.
- [ ] **2. Không cắt cụt chữ (Zero Truncation)**: Mỗi dòng là một cụm danh từ hoàn chỉnh ngữ nghĩa, không đứt đoạn từ ghép, không lửng câu, không sót từ nối ở đuôi (`&`, `và`, `cho`, `với`, `của`, `để`, `hỗ`, `chuẩn bị`, `chức`...).
- [ ] **3. Chuẩn hóa Deliverable (Outcome-based)**: Tóm tắt cô đọng thành kết quả/bàn giao (VD: `Nghiệm thu UAT & Sign-off`, `Kiểm thử chức năng Sprint 4`), không kể lể thao tác dev/QC con.
- [ ] **4. Làm sạch 100%**: Đã loại bỏ hoàn toàn Jira ID (FSM-xxx, DEV-xxx...), tên người thực hiện (Account/Assignee), và ký tự markdown thô (`**`, `###`).
- [ ] **5. Định dạng Bullet `- `**: Mỗi dòng trong Done, Doing/Will do, Risks bắt buộc bắt đầu bằng `- `.
- [ ] **6. Số lượng dòng**: Mỗi mục Done và Doing chỉ chứa từ **3 đến 5 dòng**.
- [ ] **7. Tính nhất quán 100% với file `.md` (Zero Hallucination / No Foreign Story Names)**: Toàn bộ deliverable trong `Done` và đầu việc trong `Doing` của file `.txt` phải có nguồn gốc trực tiếp từ các sub-task tại Section 2 của file `.md`. Tuyệt đối không xuất hiện hạng mục lạ hoặc bốc tên Story cha ngoài lề (như "Khởi động Sprint" khi file `.md` không có hoặc sprint đã ở giữa/cuối).

---

## Quy trình đầy đủ (Step-by-Step)

### Ví dụ Input → Command

| Câu hỏi của user | Command phải chạy |
|------------------|-------------------|
| "Làm weekly report cho FSM Sprint 3" | `run_weekly_report.py --project-key FSM --sprint-name "Sprint 3"` (Jira-only) |
| "Làm report FSM Sprint 3, dữ liệu từ Sheet ID 1abc..." | `run_weekly_report.py --project-key FSM --sprint-name "Sprint 3" --sheet-id "1abc..."` |
| "Report Sprint 3, đọc từ file Excel này" + file upload | `run_weekly_report.py --project-key FSM --sprint-name "Sprint 3" --excel "/path/to/file.xlsx"` |
| "FSM Sprint 3, Sheet 1abc... có backlog mới nhất" | `run_weekly_report.py --project-key FSM --sprint-name "Sprint 3" --sheet-id "1abc..."` |
| **"FSM Sprint 3, data google sheet (1abc...), start/due sprint lấy từ jira"** | `run_weekly_report.py --project-key FSM --sprint-name "Sprint 3" --sheet-id "1abc..."` **(vẫn cần --sheet-id!)** |

### Step 1 - Kiểm tra nguồn dữ liệu và thông tin bắt buộc

**TRƯỚC TIÊN**: Kiểm tra xem user có cung cấp Sheet ID/Excel không.

| Input từ user | Hành động |
|-------|-----------|
| User cung cấp Google Sheet ID, spreadsheet link, hoặc nhắc "Google Sheet" / **"data google sheet"** | **BẮT BUỘC** thêm `--sheet-id <SHEET_ID>` vào command |
| User gửi file `.xlsx` hoặc nhắc Excel | **BẮT BUỘC** thêm `--excel <PATH>` vào command |
| Chỉ có project key + sprint name, không nhắc Sheet/Excel | Dùng Jira-only (mặc định) |
| Thiếu project key hoặc sprint name | Hỏi 2 thông tin này |

> ⚠️ **LƯU Ý**: Logic fallback trong `run_weekly_report.py` là `jira_only = not args.sheet_id and not args.excel`. Nếu không truyền `--sheet-id` dù user có cung cấp Sheet ID, script sẽ tự động bỏ qua và chạy Jira-only.

> ⚠️ **PATTERN MATCHING**: 
> - User nói **"data google sheet (ID)"** → Có Sheet ID → **PHẢI `--sheet-id`**
> - User nói **"start/due sprint lấy từ jira"** → Chỉ là hướng dẫn lấy sprint dates, **KHÔNG** thay đổi nguồn backlog
> - Kết hợp cả 2 câu → Backlog từ Sheet + Sprint dates từ Jira → Vẫn **PHẢI `--sheet-id`** (script tự động kết hợp)

### Step 2 - Fetch data

Tùy nguồn, chạy script tương ứng → xuất JSON standardized.

Script xuất `{PROJECT}_{SPRINT}_report_v{N}.md` + `{PROJECT}_{SPRINT}_report_latest.json`. **Không** ghi đè bản cũ.

### Step 3 - Generate report (.md)

```bash
python3 scripts/generate_report_from_json.py --input <json_file> --output-dir "$REPORT_OUTPUT_DIR"
```

### Step 4 - Tạo bản PM Sprint Summary (.txt)

Ngay sau khi script xuất file `.md`:
1. Đọc Section 1 (Metrics), Section 2 (Sprint Progress) và Section 4 (Risks) từ file `.md` vừa tạo.
2. **BẮT BUỘC DÙNG NĂNG LỰC TỔNG HỢP CỦA AI (LLM) ĐỂ VIẾT LẠI (SYNTHESIZE / PARAPHRASE)**:
   - **Tuyệt đối KHÔNG** sao chép câu thô từ `.md` rồi cắt ngang lưng chừng làm cụt từ, đứt đoạn ngữ nghĩa.
   - Phải tự viết lại từng bullet thành một cụm danh từ chỉ kết quả/kế hoạch ngắn gọn (khoảng 5–12 từ, tối đa 15 từ), trọn vẹn ngữ nghĩa và bắt đầu bằng `- `.
   - Tham chiếu bảng đối chiếu ở mục [Quy tắc biên soạn](#quy-tắc-biên-soạn-cấp-lãnh-đạo--po).
3. **Thực hiện Preflight Check**: Tự kiểm tra 6 tiêu chí trong [Preflight Checklist](#-preflight-checklist-bắt-buộc-tự-kiểm-tra-trước-khi-ghi-file-txt) (độ dài súc tích 5–12 từ/dòng, không cắt cụt từ, không để câu dài thô, format `- `).
4. Dùng công cụ `Write` (hoặc `write_to_file`) viết hoàn thiện file `.txt` vào `$REPORT_OUTPUT_DIR` với đúng tên `txtExpected` (ví dụ `{PROJECT}_{SPRINT}_report_v{N}.txt`).

### Step 5 - Báo cáo kết quả

Gửi **1 tin nhắn duy nhất** sau khi đã hoàn thành cả file `.md` và file `.txt`:
- Tóm tắt Health, SPI, RAG, **version** (_vN).
- Nêu rõ tên cả 2 file:
  - File `.md` (báo cáo chi tiết)
  - File `.txt` (bản tóm tắt rút gọn)
- Tuyệt đối **không** gửi tin nhắn phân tách thành nhiều đoạn dở dang để đảm bảo các chip file đính kèm hiển thị đúng vào tin nhắn kết quả này.

## Xử lý lỗi thường gặp

| Lỗi | Nguyên nhân | Xử lý |
|-----|-------------|-------|
| 410 Gone trên `/rest/api/3/search` | API cũ deprecated | Dùng `POST /rest/api/3/search/jql` |
| `ModuleNotFoundError: gspread/openpyxl` | Venv webapp thiếu package | Báo admin restart webapp (server tự cài `.venv-skills`) |
| `403 Forbidden` Google Sheet | Service account chưa được cấp quyền | Chia sẻ sheet với email service account |
| Timeout / ConnectTimeout khi gọi Jira/Google | Proxy FPT không thống nhất theo host | **Chạy lại script** - tự thử direct → proxy → env (log `[NET]`). Không dùng curl |
| Proxy error khi fetch Google Sheet | Thiếu proxy hoặc direct bị chặn | Script tự fallback; nếu vẫn lỗi thêm `HTTP_PROXY`/`HTTPS_PROXY` vào `.env` webapp |
| 401 Unauthorized | Token hết hạn / sai | Kiểm tra email + API token |
| `total: None` | API mới dùng token pagination | Dùng `isLast` + `nextPageToken` để paginate |

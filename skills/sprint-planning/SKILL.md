---
name: sprint-planning
description: Tạo Sprint Backlog và lên kế hoạch Sprint cho dự án Agile/Scrum. Sử dụng khi cần lập kế hoạch sprint - tạo sprint backlog, phân công task, ước tính capacity, gán PIC cho task, lập sprint goal. Kích hoạt khi user yêu cầu lên sprint, sprint planning, tạo sprint backlog, phân công task sprint, ước tính story point cho sprint, commitment ceiling hoặc bất kỳ yêu cầu lập kế hoạch sprint cụ thể nào.
license: MIT
metadata:
  version: 2.10.0
  category: project-management
  domain: agile-development
  updated: 2026-07-10
  parent-skill: scrum-master
---

# Sprint Planning Skill v2.10

Tạo Sprint Backlog chi tiết với task breakdown, phân công PIC cụ thể, ước tính effort, milestone timeline, tổng hợp manday theo role, và tự tính duration sprint dựa trên effort thực tế.

**⛔ CẤM (headless):** KHÔNG chạy Bash `mkdir`, `mkdir -p`, `ls`, `echo OK` cho `$REPORT_OUTPUT_DIR/.tmp` / `TMPDIR`. Webapp đã tạo thư mục đó. Bắt đầu bằng Read tài liệu rồi Write JSON thẳng vào `$REPORT_OUTPUT_DIR/.tmp/sprint{N}_backlog.json`.

**⚠️ BẮT BUỘC:** Trước khi thực thi bất kỳ bước nào, **phải đọc đầy đủ** các tài liệu tham khảo bên dưới.

## Tài nguyên cần đọc (BẮT BUỘC)

- `$SKILL_DIR/references/backlog-guide.md` - Quy tắc tính Story Point, Priority/Complexity scale, Task Status. **KHÔNG đưa nội dung này vào output cuối cùng.**
- `$SKILL_DIR/references/sprint-planning-instructions.md` - **TÀI LIỆU CHÍNH** (workflow chi tiết, Story tính năng lớn tương đương EPIC, move các phase init/QC test/pentest/UAT/pilot vào story, task splitting <=24h & <=3 working days, sequential per member, Pre-flight Checklist đầy đủ, Limitations).
- `$SKILL_DIR/assets/sprint_backlog_template.md` - Template output chuẩn (section 4 SPRINT BACKLOG).

**Sau khi đọc xong 3 file trên (dùng đường dẫn `$SKILL_DIR/...` - webapp inject sẵn), mới bắt đầu thu thập input từ user và tạo output. KHÔNG dùng `~/.claude/skills/...` (bị guardrail chặn).**

## Workflow tổng quát (tóm tắt - chi tiết đầy đủ trong `$SKILL_DIR/references/sprint-planning-instructions.md`)

### Bước 0: Xác nhận đầu vào trước khi bắt đầu (Pre-flight)
- **KHÔNG tự động tạo output.** Hỏi user → chờ xác nhận rõ ràng ("ok làm đi", "bắt đầu", "go").
- **Luôn hỏi các câu này trước:**
  1. Dự án đã có nguồn lực (nhân sự) chưa? (list cụ thể DEV1/QC1... hay dùng role generic `PM`/`TL`/`Dev`/`BA`/`QC`?)
  2. Ngày bắt đầu Sprint là khi nào? (Duration sẽ tự tính dựa trên effort)
  3. Danh sách User Story / Product Backlog đã có chưa?
  4. Sprint này có giai đoạn **pentest** (CSOC pentest) không? Nếu có: scope pentest là gì, do đơn vị nào thực hiện (nội bộ hay third-party)?
  5. Sprint này có giai đoạn **pilot** sau go-live không?
- Xử lý kết quả theo đúng quy tắc chi tiết trong `$SKILL_DIR/references/sprint-planning-instructions.md` (có nguồn lực cụ thể → dùng label DEV1, QC1...; có pentest/pilot → đưa các task pentest, pilot vào trực tiếp các Story tính năng tương ứng theo đúng timeline).

### Bước 1: Thu thập input
- **BẮT BUỘC:** Sprint number + danh sách User Story / Product Backlog.
- **TÙY CHỌN:** Sprint Goal (tự đề xuất nếu thiếu), team capacity (số người, ngày làm việc), complexity/priority per story (mặc định 2-Medium), sprint data JSON để chạy velocity analysis & lấy commitment ceiling.

### Bước 2: Xây dựng Sprint Backlog chi tiết
- **Story là tính năng lớn (tương đương định nghĩa EPIC)**: Mỗi User Story là một tính năng lớn cần phát triển trong sprint/version.
- **Tích hợp toàn bộ phase vào Story tính năng**: Các task và các phase như `init`, `QC test/testing`, `pentest`, `UAT`, `pilot` đều được **move vào bên trong các Story tính năng** dựa vào độ phù hợp nghiệp vụ và thời gian ngay giai đoạn đó (không tách rời thành các EPIC kỹ thuật/phase riêng biệt).
- Break thành Tasks cụ thể với PIC, effort (Manday/Hour), status, start/end date.
- Tính Story Point theo công thức trong `$SKILL_DIR/references/backlog-guide.md`.
- **Tuân thủ nghiêm ngặt** các quy tắc BẮT BUỘC trong `$SKILL_DIR/references/sprint-planning-instructions.md`:
  - **Story Description ngắn gọn (tầm 8–12 từ)**: Mô tả nghiệp vụ trung tính, súc tích (khoảng **8–12 từ/story**), không dùng dạng "Là [Role], tôi muốn...", không viết dài dòng hay giải thích chi tiết.
  - **Thời lượng task tối đa 3 ngày làm việc (≤ 3 working days & ≤ 24h)**: Áp dụng cho **tất cả các role (bao gồm cả PM, BA, DEV, QC)**. Khoảng cách giữa `start_date` và `due_date` không được vượt quá 3 ngày làm việc. Task PM phải chia nhỏ theo tuần (`Theo dõi tiến độ & Quản trị rủi ro – Tuần N`) hoặc theo mốc sự kiện (Kick-off, UAT Coordination, Review/Retro), **CẤM** tạo task PM kéo dài toàn sprint hoặc > 3 ngày làm việc.
  - **Phân bổ task các phase vào Story tính năng**:
    - **Init phase** (W1): BA phân tích yêu cầu, thiết kế Wireframe, viết URD; DEV/TL setup môi trường, review kiến trúc, technical design; PM kick-off & planning (gắn vào Story 1 hoặc Story trọng tâm).
    - **Development phase**: DEV coding, unit test, staging deploy.
    - **QC test/testing phase**: BA demo & clear nghiệp vụ cho QC, QC onboarding (W2+ sau khi URD hoàn tất), QC test/testing, DEV fix bug QC, QC recheck sau fix.
    - **Pentest & UAT phase**: BA viết UAT Scenario, User Guide, hỗ trợ UAT; DEV chuẩn bị môi trường pentest, hỗ trợ pentest, DEV fix bug pentest, DEV fix bug UAT, QC recheck pentest, Security sign-off.
    - **Deploy & Pilot phase**: Production deploy (Thứ 2 hoặc Thứ 4), QC post-deploy smoke test, DEV monitor log & hotfix, BA thu thập feedback pilot, PM tổng kết pilot & đóng sprint.
  - Mỗi task **tối đa 24 giờ** effort - nếu >24h bắt buộc tách task nhỏ hơn, tên task phải self-descriptive.
  - **Story Sequential per Member**: Trong cùng 1 nhóm tính năng lớn, mỗi PIC không được start task ở US tiếp theo trước khi hoàn thành task cuối cùng của họ ở US hiện tại (PM tracking tasks được miễn sequential nhưng vẫn phải tuân thủ max 3 working days/task & chia theo tuần). Sau khi shift → re-sort tasks theo start_date.

### Bước 3: Tính toán Timeline, Capacity & Phases
- Tự tính duration sprint dựa trên tổng effort thực tế + số nhân sự.
- Tạo bảng Phase & Key Milestone Timeline (Requirements & URD → QC Onboarding → Development → QC Testing → Pentest & UAT → Deploy & Pilot).
- Tổng hợp manday theo role (DEV / BA / QC / PM / TL).

### Bước 4: Format & Xuất Output
- Sử dụng đúng cấu trúc từ `$SKILL_DIR/assets/sprint_backlog_template.md` (section 4 SPRINT BACKLOG).
- Tạo file JSON `sprint{N}_backlog.json` (xem cấu trúc mẫu trong `$SKILL_DIR/scripts/sprint1_backlog.json`). **Ghi vào `$REPORT_OUTPUT_DIR/.tmp/` (cache ẩn, webapp đã tạo sẵn thư mục - KHÔNG mkdir). KHÔNG ghi vào top-level `$REPORT_OUTPUT_DIR/` để tránh hiện chip file JSON cho user.**
- Chạy cả 2 script xuất Excel: `$SKILL_DIR/scripts/json_to_excel.py` (Mẫu Project Plan) và `$SKILL_DIR/scripts/json_to_excel_v2.py` (Mẫu Detailed Sprint Backlog).
- **⛔ KHÔNG đưa bảng chi tiết từng task (Task Breakdown / per-task table) vào file `.md`.** Chi tiết từng task đã có trong `sprint{N}_backlog.json` và các file Excel (`sprint{N}_Project_Plan.xlsx`, `sprint{N}_Sprint_Backlog.xlsx`) - file `.md` chỉ chứa phần tóm tắt: Tổng quan Sprint, Phân bổ nhân sự & Manday summary, Phase & Milestone Timeline, Danh sách Output Deliverables, Pre-flight Checklist. Tuyệt đối không có section "Chi Tiết Sprint Backlog & Task Breakdown" hay bất kỳ bảng liệt kê từng task nào trong `.md`.

### Bước 5: Pre-flight Checklist & Final Review
- **BẮT BUỘC** chạy đầy đủ Pre-flight Checklist trong `$SKILL_DIR/references/sprint-planning-instructions.md` trước khi giao output cho user.
- Kiểm tra các lỗi thường gặp: effort task >24h, thiếu PIC, vi phạm sequential rule, thiếu các phase init/QC test/UAT/pilot trong story, missing URD sign-off, v.v.
- **⛔ Weekly Balance 40h/tuần cho DEV/TL là rule chặn cứng, không phải gợi ý** - phải **thực sự chạy script WEEKLY BALANCE CHECK** (không suy đoán bằng mắt) và xác nhận không còn `⚠️ UNDER` hay `❌ OVERLOAD` ngoài ngoại lệ hợp lệ, trước khi xuất file cho user. Nếu phát hiện vi phạm → nén timeline hoặc bổ sung task thực tế (xem chi tiết trong references), rồi chạy lại để xác nhận, không giao output khi chưa đạt.

## Lưu ý quan trọng
- **Chỉ đưa task pentest / pilot vào Story khi user XÁC NHẬN RÕ RÀNG "có"** và cung cấp scope cụ thể. Nếu không đề cập hoặc trả lời "không" → bỏ qua.
- **Chuẩn hóa thuật ngữ chung (text general)**:
  - `kiểm thử` $\rightarrow$ `test/testing`
  - `kiểm thử bảo mật` hoặc `an toàn thông tin` $\rightarrow$ `pentest`
  - `Vận hành thử nghiệm` $\rightarrow$ `pilot`
  - `khắc phục lỗi` $\rightarrow$ `fix bug`
- Output phải **actionable, cụ thể, có PIC rõ ràng, effort thực tế**.
- Nếu input thiếu (backlog, nguồn lực, ngày bắt đầu) → **hỏi thêm**, không tự bịa đặt.
- Sau khi generate, user có thể yêu cầu chỉnh sửa task/ngày/effort → dùng cache JSON + str_replace + re-run Bước 2–4 (không cần re-generate toàn bộ).

## Quy tắc Lịch & Ràng buộc Ngày tháng (BẮT BUỘC)

### 1. Even Number Rule
- **Tất cả** `est_effort_hour` phải là 4, 8, 16 hoặc 24 (ưu tiên 8h).
- Tuyệt đối **không làm tròn số lẻ thành chẵn một cách khiên cưỡng**. Nếu task có effort lẻ (vd 3h), phải: (a) phân tích lại complexity để justify lên/chẵn hợp lý, hoặc (b) gộp với task khác cùng PIC để thành số chẵn.

### 2. Calendar Constraints
- **Thời lượng tối đa 3 ngày làm việc (≤ 3 working days)**: Khoảng thời gian từ `start_date` đến `due_date` (Mon–Fri) của mọi task không được vượt quá 3 ngày làm việc.
- **Không có ngày Thứ 7 / Chủ Nhật** trong `start_date` hoặc `due_date`.
- **Cùng tháng**: `start_date` và `due_date` phải cùng tháng (không span qua tháng, vd 31/07→03/08 không hợp lệ).
- **Cùng ISO week**: `start_date` và `due_date` phải cùng ISO week (không span qua weekend, vd Fri→Mon không hợp lệ).
- **Production Deploy**: Chỉ được đặt vào Thứ 2 (Mon) hoặc Thứ 4 (Wed).

### 3. Weekly Capacity (Fixed 40h/tuần)
- Mỗi member có **capacity cố định 40h/tuần** (gross), 32h/tuần (net ~80%).
- Tuần có 4 ngày làm việc (vd T28: 07-10/07) → cap **32h**.
- Tổng capacity sprint = tổng capacity các tuần. Nếu tổng effort của 1 member **vượt quá tổng capacity** → phải giảm scope hoặc tăng nhân sự.
- **Không dồn effort**: cố gắng phân bổ đều, tránh 1 member có >60% effort trong 2 tuần cuối.

### 4. Weekly Balancing & Redistribution

Khi 1 member có tổng effort vượt quá capacity của tuần đó, các kỹ thuật sau được phép áp dụng:

| Kỹ thuật | Mô tả | Ví dụ |
|----------|-------|-------|
| **Cross-week split** | Chia task chạy qua ranh giới tuần (nhưng không qua tháng/week) | Task 8h split thành 4h cuối tuần này + 4h đầu tuần sau |
| **Compression** | Dồn task trong ít ngày hơn (effort giữ nguyên) | Task 8h/2 ngày → 8h/1 ngày |
| **Cross-EPIC overlap** | Task từ EPIC khác nhau có thể chạy song song trong cùng PIC | 1 DEV làm task của 2 EPIC khác nhau cùng lúc |
| **Tech debt relocation** | Chuyển technical debt xuống tuần đầu/rỗi | Dời task tech debt từ tuần cuối sang tuần còn dư capacity |

**Giới hạn:** Không thể ép task dependency cứng (pentest chờ findings, export chờ unit test) vào tuần sớm hơn.

### 5. Locked Dependencies (End-of-Sprint)
Khi sprint có **CSOC Pentest** hoặc các luồng phụ thuộc chuỗi (export → phê duyệt, pentest → fix findings), tuần cuối sprint thường bị khoá bởi các dependency dạng:
```
[Pentest] Fix findings          ← chỉ bắt đầu sau khi có kết quả pentest
[Dev] Export báo cáo             ← chỉ bắt đầu sau khi Unit Test hoàn tất
      Phê duyệt                  ← chỉ bắt đầu sau khi Export xong
[Pilot] Monitor sau go-live      ← chỉ bắt đầu sau go-live
```
→ Luôn kiểm tra: task nào ở tuần cuối có thể đẩy lên tuần trước đó? Nếu dependency không cho phép → chấp nhận overload ≤44h ở tuần đó hoặc báo user.

### 6. Monitor Task - Passive / Background
- Task dạng "Monitor log/performance/alert sau go-live" trong giai đoạn Pilot là **passive/on-call**.
- Effort ghi nhận (vd 12h) là thời gian trực, không phải làm việc liên tục.
- Có thể coi là background task và không tính vào active effort khi báo cáo weekly.

## Validation & Xuất File


### Bắt buộc sau mỗi lần chỉnh sửa
1. **Sort tasks** theo `start_date` trong mỗi user_story.
2. **Validate**: chạy `python3 scripts/validate_cache.py sprint{N}_backlog.json`
   - Đảm bảo: không weekend date, cùng tháng, cùng ISO week, max 24h/task, even effort.
3. **Export Excel**: chạy cả 2 script:
   - Project Plan: `python3 scripts/json_to_excel.py sprint{N}_backlog.json -o sprint{N}_Project_Plan.xlsx`
   - Detailed Sprint Backlog: `python3 scripts/json_to_excel_v2.py sprint{N}_backlog.json -o sprint{N}_Sprint_Backlog.xlsx`
4. **Generate Markdown**: tạo `sprint{N}_backlog.md` với bảng weekly + EPIC breakdown.

### Cấu trúc Output Files
- `sprint{N}_backlog.json` - Source of truth nội bộ (định dạng JSON, UTF-8) - **ghi vào `$REPORT_OUTPUT_DIR/.tmp/` (ẩn, không hiện chip/file list), KHÔNG share cho user, KHÔNG liệt kê trong output deliverables**
- `sprint{N}_Project_Plan.xlsx` - Excel Project Plan (Sheet: Sprint N, template `json_to_excel.py`) - share cho user
- `sprint{N}_Sprint_Backlog.xlsx` - Excel Detailed Sprint Backlog (Sheet: Sprint N, template `json_to_excel_v2.py`) - share cho user
- `sprint{N}_backlog.md` - Báo cáo Markdown (weekly summary + phase/milestone) - share cho user

> **⛔ Chỉ share 3 file cho user: `sprint{N}_Project_Plan.xlsx` + `sprint{N}_Sprint_Backlog.xlsx` + `sprint{N}_backlog.md`.** File `sprint{N}_backlog.json` là source of truth nội bộ (dùng để validate + export Excel), tồn tại ẩn trong `$REPORT_OUTPUT_DIR/.tmp/` - không `present_files`, không liệt kê trong phần "Danh sách Output Deliverables" của `.md`, không copy ra top-level `$REPORT_OUTPUT_DIR/`.
>
> **⛔ File `sprint{N}_backlog.md` KHÔNG chứa bảng chi tiết từng task (Task Breakdown).** Chỉ gồm các phần tóm tắt: (1) Tổng quan Sprint, (2) Phân bổ nhân sự & Manday summary, (3) Phase & Milestone Timeline, (4) Danh sách Output Deliverables, (5) Pre-flight Checklist Verification. Chi tiết từng task (task name, PIC, effort, start/end date, notes) chỉ nằm trong `.json` và các file `.xlsx` - không lặp lại trong `.md`.

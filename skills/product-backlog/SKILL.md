---
name: "product-backlog"
description: "Tạo Product Backlog Agile/Scrum cho dự án. Sử dụng khi cần: tạo danh sách User Story, phân EPIC, gán Story Point, phân Sprint, lập roadmap backlog. Trigger khi user nói: làm backlog, tạo product backlog, lên backlog dự án, user story, phân EPIC, gán sprint cho backlog, lập danh sách yêu cầu dự án, hay bất kỳ yêu cầu nào liên quan đến tạo hoặc cập nhật Product Backlog."
license: MIT
metadata:
  version: 1.0.0
  category: project-management
  domain: agile-development
  updated: 2026-04-02
  parent-skill: scrum-master
---

# Product Backlog Skill

Tạo Product Backlog Agile chuẩn với User Stories, EPIC grouping, Story Point, phân Sprint và Roadmap.

---

## ⚠️ Quy tắc bắt buộc - Chờ lệnh trước khi thực thi

**KHÔNG bao giờ tự động bắt đầu tạo output** khi user mới đặt yêu cầu.

Quy trình chuẩn:
1. **Hỏi** các thông tin còn thiếu
2. **Chờ** user ra lệnh rõ ràng: *"ok làm đi"*, *"bắt đầu"*, *"go"* hoặc tương đương
3. **Khi đó mới** tạo output

---

## Tài nguyên

- `$SKILL_DIR/references/backlog-guide.md` - Quy tắc tính Story Point và convention (**KHÔNG đưa vào output**)
- `$SKILL_DIR/assets/product_backlog_template.md` - Template output (sections 1–3)

**Đọc cả hai file trên (dùng đường dẫn `$SKILL_DIR/...` - webapp inject sẵn) trước khi bắt đầu bất kỳ output nào. KHÔNG dùng `~/.claude/skills/...` (bị guardrail chặn).**

---

## Workflow

### Step 0 - Hỏi trước khi bắt đầu

**Luôn hỏi 3 câu này trước**, dù user đã cung cấp thông tin khác:

> 1. Dự án đã có nguồn lực (nhân sự) chưa?
> 2. Ngày bắt đầu và kết thúc dự án là khi nào?
> 3. Danh sách yêu cầu hoặc User Story là gì?

**Xử lý kết quả:**
- **Có nguồn lực** → dùng tên thật vào cột PIC/PO
- **Chưa có nguồn lực** → điền role: `PM` / `TL` / `Dev` / `BA` / `QA`
- **Có ngày** → điền ngày thực tế vào cột date và Roadmap
- **Chưa có ngày** → để `<DD/MM/YY>`
- **Có User Story** → dùng để phân tích EPIC và Sprint
- **Chưa có User Story** → chờ, không tiếp tục

### Step 1 - Thu thập input

**BẮT BUỘC (chờ user cung cấp, không tiếp tục nếu thiếu):**
- ✅ Danh sách yêu cầu hoặc User Story

**TÙY CHỌN (dùng placeholder nếu thiếu):**
- Tên project / KEY PO / Division / Domain / Platform / Staging & Production links → `<Not provided>`
- Priority → mặc định `2-Medium`

### Step 2 - Phân tích User Stories

Tự động:
1. Gom thành **EPIC** theo domain/chức năng
2. Gán **User Story ID** theo convention `US_{EPIC}.{STORY}` (ví dụ: US_1.1, US_2.1…)
3. Tính **Story Point** theo quy tắc trong `$SKILL_DIR/references/backlog-guide.md`
4. Phân Sprint dự kiến theo priority (Critical/High → Sprint 1 trước)

### Step 3 - Output

Điền sections 1–3 theo `assets/product_backlog_template.md`. Output file `.md` hoàn chỉnh.

---

## Limitations

- Nếu thiếu danh sách yêu cầu → không thể tạo backlog. Dừng và yêu cầu user cung cấp.
- Story Point chỉ là ước tính - luôn note để team review lại trong Sprint Planning.

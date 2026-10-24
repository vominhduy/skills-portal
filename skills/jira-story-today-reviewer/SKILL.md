---
name: jira-story-today-reviewer
description: Rà soát các Story Jira có Start Date là hôm nay đang ở trạng thái To Do và hỗ trợ chuyển sang In Progress.
---

# Jira Story Today Reviewer & In Progress Starter

Kỹ năng tự động rà soát toàn bộ các Story có ngày bắt đầu (`Start Date`) là hôm nay và đang ở trạng thái `To Do` do người dùng tạo trên Jira Cloud, đồng thời hỗ trợ chuyển nhanh toàn bộ sang `In Progress`.

## Mục Tiêu & Nghiệp Vụ
- **JQL Truy Vấn:**
  ```sql
  type = Story and creator = currentUser() and status = "To Do" and "start date[date]" = "{today}" ORDER BY "cf[10015]" ASC, created DESC
  ```
- **Phạm Vi Lấy Dữ Liệu:**
  - Lấy các Story có `status = "To Do"` (hoặc biến thể `statusCategory = "To Do"`) có ngày bắt đầu là hôm nay (mặc định lấy theo ngày hiện tại của hệ thống, hoặc ngày người dùng chỉ định).
- **Nút Chuyển In Progress Nhanh:**
  - Cung cấp nút xác nhận chuyển trạng thái toàn bộ các Story này sang `In Progress` để bắt đầu làm việc.

---

## Quy Trình Thực Thi (BẮT BUỘC)

> ⚠️ **QUY TẮC THỰC THI QUAN TRỌNG:**
> - **Chạy lệnh đồng bộ:** Khi gọi tool Bash/run_command, luôn chạy lệnh trực tiếp và đợi kết quả hoàn tất trong cùng một lượt. KHÔNG chạy ngầm hay background.
> - **KHÔNG gửi tin nhắn dở dang trước khi chạy:** Tuyệt đối KHÔNG xuất các câu thông báo trung gian như *"Đang tiến hành chạy pipeline rà soát..."* rồi dừng/kết thúc lượt. Bạn phải gọi tool Bash ngay lập tức và chỉ trả lời duy nhất một tin nhắn sau khi pipeline đã tạo xong file báo cáo.

### Bước 1: Chạy Pipeline Python (MỘT Lệnh Bash Duy Nhất)
Webapp đã tự cấp quyền chạy bash trong sandbox. Trợ lý AI thực thi 1 lệnh duy nhất:

```bash
cd "$SKILL_DIR" && python3 scripts/run_story_today_check.py --output-dir "$REPORT_OUTPUT_DIR"
```

- Nếu người dùng chỉ định ngày cụ thể (ví dụ: `2026-09-16`), truyền thêm tham số:
  ```bash
  cd "$SKILL_DIR" && python3 scripts/run_story_today_check.py --output-dir "$REPORT_OUTPUT_DIR" --date "2026-09-16"
  ```
- Nếu người dùng muốn lọc theo Project Key hoặc Creator cụ thể:
  ```bash
  cd "$SKILL_DIR" && python3 scripts/run_story_today_check.py --output-dir "$REPORT_OUTPUT_DIR" --project-key "PROJ" --creator "duyvm4"
  ```

---

### Bước 2: Đọc Tóm Tắt Kết Quả & Phản Hồi Ngắn Gọn
Sau khi script hoàn thành, đọc nhanh file kết quả JSON hoặc MD trong `$REPORT_OUTPUT_DIR` để lấy số liệu tổng kết.

### Bước 3: Xuất Báo Cáo Tóm Tắt Trong Chat (TIẾT KIỆM TOKEN)
> ⚠️ **QUY TẮC BẮT BUỘC:** File `.md` chi tiết (kèm bảng danh sách đầy đủ Story, Assignee, Priority, Estimate, Due Date) đã được sinh tự động trong `$REPORT_OUTPUT_DIR`. Webapp sẽ tự động phát hiện tên file để người dùng xem preview ở panel bên phải hoặc tải về. **TUYỆT ĐỐI KHÔNG in lại toàn bộ nội dung hay bảng danh sách chi tiết của file `.md` ra tin nhắn AI** nhằm tiết kiệm tối đa token.

Chỉ trả lời ngắn gọn (5-7 dòng) theo mẫu chuẩn sau:

```markdown
### 🚀 Hoàn Tất Rà Soát Story Bắt Đầu Hôm Nay ({today_date})

- **Phạm vi kiểm tra:** Story có Start Date là `{today_date}` và trạng thái `To Do`
- **Tổng số Story tìm thấy:** **{total_stories}** Story
- **Tổng quỹ thời gian Estimate:** **{total_est}h**
- **File báo cáo chi tiết:** `story_today_review_v{N}.md` *(nhấp vào file chip để xem danh sách chi tiết)*

👉 *Gợi ý:* Nhấn nút **`Xác nhận chuyển In Progress các Story hôm nay`** bên dưới để chuyển trạng thái In Progress cho tất cả **{total_stories}** Story trên Jira.
```

---

### Bước 4: Xử Lý Chuyển In Progress (Khi Người Dùng Xác Nhận)
Khi người dùng bấm nút xác nhận trên giao diện hoặc gửi yêu cầu (ví dụ: *"chuyển in progress"*, *"đánh in progress"*, *"start in progress"*, *"xác nhận chuyển in progress tất cả story"*):

1. **Trợ lý AI thực thi script transition bằng MỘT lệnh Bash duy nhất:**
   ```bash
   cd "$SKILL_DIR" && python3 scripts/transition_stories_inprogress.py --output-dir "$REPORT_OUTPUT_DIR"
   ```
2. **Đọc tóm tắt file kết quả:**
   Script sẽ tự động tìm transition `In Progress` và chuyển trạng thái trên Jira, lưu file `story_inprogress_v{N}.json` + `story_inprogress_v{N}.md`.
3. **Xuất phản hồi ngắn gọn trong chat (TIẾT KIỆM TOKEN):**
   > ⚠️ **TUYỆT ĐỐI KHÔNG in lại toàn bộ bảng chi tiết ra tin nhắn.** Chỉ trả lời ngắn gọn:
   ```markdown
   ### ✅ Đã Chuyển Trạng Thái In Progress Thành Công ({success_count}/{total_processed})

   - **Tổng số Story đã xử lý:** {total_processed}
   - **Chuyển sang In Progress thành công:** **{success_count}** Story
   - **Thất bại:** {fail_count} Story
   - **Báo cáo chi tiết:** `story_inprogress_v{N}.md` *(nhấp vào file chip để xem chi tiết trạng thái từng Story)*
   ```

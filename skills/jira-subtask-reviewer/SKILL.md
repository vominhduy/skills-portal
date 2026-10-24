---
name: jira-subtask-reviewer
description: Rà soát các sub-task Jira (status In Review, Original Estimate == Time Spent) theo tuần hoặc khoảng ngày.
---

# Jira Sub-task Reviewer

Kỹ năng tự động rà soát toàn bộ các sub-task có trạng thái `In Review` trên Jira Cloud theo phạm vi thời gian (mặc định Thứ 2 – Thứ 6 tuần hiện tại, hoặc khoảng ngày tùy biến).

## Mục Tiêu & Nghiệp Vụ
- **JQL Truy Vấn:**
  ```sql
  due >= "{from_date}" and due <= "{to_date}" and type IN subTaskIssueTypes() and creator = currentUser() ORDER BY "cf[10015]" ASC, created DESC
  ```
- **Phạm Vi Lấy Dữ Liệu:**
  - Lấy **TOÀN BỘ** các sub-task có `status = inreview` (hoặc các biến thể: In Review, Ready for Review, QA, In QA...).
- **Phân Loại & Đánh Giá:**
  1. **🟢 Khớp 100% (Original Estimate == Time Spent > 0):**
     - Sub-task đã hoàn thành 100% thời gian estimate và đang chờ hoàn tất.
     - **Đây là nhóm duy nhất đủ điều kiện chuyển trạng thái khi bấm nút xác nhận đánh Done.**
  2. **🔥 Lệch Giờ Cần Highlight (Original Estimate != Time Spent):**
     - Đánh dấu nổi bật để PM/Tech Lead lưu ý:
       - Sub-task chưa estimate hoặc chưa log time.
       - Sub-task log thiếu giờ (`Spent < Est`).
       - Sub-task vượt estimate (`Spent > Est`).
- **Nút Xác Nhận Đánh Done:**
  - Nút xác nhận trên UI và script transition **chỉ áp dụng đánh Done cho nhóm task có Est == Spent**. Các task lệch giờ sẽ được giữ nguyên trạng thái để đối soát.

---

## Quy Trình Thực Thi (BẮT BUỘC)

### Bước 1: Chạy Pipeline Python (MỘT Lệnh Bash Duy Nhất)
Webapp đã tự cấp quyền chạy bash trong sandbox. Trợ lý AI thực thi 1 lệnh duy nhất:

```bash
cd "$SKILL_DIR" && python3 scripts/run_subtask_check.py --output-dir "$REPORT_OUTPUT_DIR"
```

- Nếu người dùng chỉ định khoảng ngày cụ thể (ví dụ: `2026-09-01` đến `2026-09-30`), truyền thêm tham số:
  ```bash
  cd "$SKILL_DIR" && python3 scripts/run_subtask_check.py --output-dir "$REPORT_OUTPUT_DIR" --from-date "2026-09-01" --to-date "2026-09-30"
  ```
- Nếu người dùng muốn lọc theo Project Key hoặc Creator cụ thể:
  ```bash
  cd "$SKILL_DIR" && python3 scripts/run_subtask_check.py --output-dir "$REPORT_OUTPUT_DIR" --project-key "PROJ" --creator "currentUser()"
  ```

---

### Bước 2: Đọc Tóm Tắt Kết Quả & Phản Hồi Ngắn Gọn
Sau khi script hoàn thành, đọc nhanh file kết quả JSON hoặc MD trong `$REPORT_OUTPUT_DIR` để lấy số liệu tổng kết.

### Bước 3: Xuất Báo Cáo Tóm Tắt Trong Chat (TIẾT KIỆM TOKEN)
> ⚠️ **QUY TẮC BẮT BUỘC:** File `.md` chi tiết (kèm bảng danh sách đầy đủ, bảng highlight lệch giờ và bảng task sẵn sàng Done) đã được sinh tự động trong `$REPORT_OUTPUT_DIR`. Webapp sẽ tự động phát hiện tên file để người dùng xem preview ở panel bên phải hoặc tải về. **TUYỆT ĐỐI KHÔNG in lại toàn bộ nội dung hay bảng danh sách chi tiết của file `.md` ra tin nhắn AI** nhằm tiết kiệm tối đa token.

Chỉ trả lời ngắn gọn (5-7 dòng) theo mẫu chuẩn sau:

```markdown
### 🔍 Hoàn Tất Rà Soát Sub-task Jira In Review ({from_date} – {to_date})

- **Tổng sub-task In Review:** **{total_inreview}** sub-task (Tổng Est: {total_est}h | Log: {total_spent}h)
- **🟢 Khớp 100% (Est == Spent):** **{total_done_eligible}** sub-task *(Sẵn sàng đánh Done)*
- **🔥 Lệch giờ cần Highlight (Est != Spent):** **{total_discrepancy}** sub-task *(Cần đối soát log time)*
- **File báo cáo chi tiết:** `subtask_review_v{N}.md` *(nhấp vào file chip để xem bảng highlight chi tiết)*

👉 *Gợi ý:* Nhấn nút **`Xác nhận đánh Done tất cả sub-task`** bên dưới để chuyển trạng thái Done cho **{total_done_eligible}** sub-task đã khớp 100% estimate (các task lệch giờ sẽ được giữ nguyên).
```

---

### Bước 4: Xử Lý Đánh Done Sub-task (Khi Người Dùng Xác Nhận)
Khi người dùng bấm nút xác nhận đánh Done trên giao diện hoặc gửi yêu cầu (ví dụ: *"đánh done"*, *"chuyển sang done"*, *"xác nhận đánh done tất cả sub-task này"*, *"mark done"*):

1. **Trợ lý AI thực thi script transition bằng MỘT lệnh Bash duy nhất:**
   ```bash
   cd "$SKILL_DIR" && python3 scripts/transition_subtasks_done.py --output-dir "$REPORT_OUTPUT_DIR"
   ```
2. **Đọc tóm tắt file kết quả:**
   Script sẽ tự động lọc chỉ chuyển trạng thái những sub-task có `Est == Spent > 0` sang `Done` trên Jira và lưu file `subtask_done_v{N}.json` + `subtask_done_v{N}.md`.
3. **Xuất phản hồi ngắn gọn trong chat (TIẾT KIỆM TOKEN):**
   > ⚠️ **TUYỆT ĐỐI KHÔNG in lại toàn bộ bảng chi tiết ra tin nhắn.** Chỉ trả lời ngắn gọn:
   ```markdown
   ### ✅ Đã Chuyển Trạng Thái Done Thành Công ({success_count}/{total_processed})

   - **Tổng số sub-task đã xử lý:** {total_processed} (các task có Est == Spent)
   - **Chuyển sang Done thành công:** **{success_count}** sub-task
   - **Thất bại:** {fail_count} sub-task
   - **Báo cáo chi tiết:** `subtask_done_v{N}.md` *(nhấp vào file chip để xem chi tiết trạng thái từng sub-task)*
   ```


# Response Templates

Template gợi ý cấu trúc phản hồi khi tổng hợp dữ liệu hoặc trả lời câu hỏi chuyên sâu.

## 1. Mẫu Tóm tắt Tiến độ / Sprint

```markdown
### 📊 Tổng quan Sprint: {Sprint Name} ({Project Key})
- **Thời gian**: {Start Date} ➔ {End Date}
- **Tiến độ Story Points**: {Done SP} / {Total SP} ({Completion Rate}%)
- **Trạng thái**: {RAG Status / Đánh giá ngắn gọn}

#### 📋 Danh sách Task nổi bật:
| Key | Loại | Tóm tắt | Người phụ trách | Trạng thái | Điểm |
|---|---|---|---|---|---|
| FCR-101 | Story | Tích hợp OAuth | Nguyen Van A | In Progress | 5 |
| FCR-102 | Bug | Sửa lỗi render table | Tran Van B | Done | 3 |

#### ⚠️ Điểm cần lưu ý / Rủi ro:
- {Ghi chú rủi ro, task bị nghẽn nếu có}
```

---

## 2. Mẫu Tóm tắt Email (Outlook Email Digest)

```markdown
### 📬 Tóm tắt Email: {Chủ đề / Yêu cầu}
- **Tổng số email tìm thấy**: {Total} ({Sensitive} email đã ẩn thông tin nhạy cảm)
- **Thời gian**: {Khoảng thời gian tra cứu}

#### 📌 Nội dung chính & Action Items:
1. **{Email Subject 1}** *(Người gửi: {From} - {Date})*
   - Tóm tắt: {Nội dung cốt lõi}
   - **Action item**: {Việc cần làm, người phụ trách, deadline}

2. **{Email Subject 2}** *(Người gửi: {From} - {Date})*
   - Tóm tắt: {Nội dung cốt lõi}
```

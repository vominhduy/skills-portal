---
name: pm-sprint-summary
description: "Tổng hợp task list thô (backlog, Jira export dạng text, ghi chú sprint dán tay) thành báo cáo PM Sprint Summary rút gọn, sạch, theo góc nhìn Project Manager - dùng để gửi PO/PMO/Sponsor/Steering Committee hoặc báo cáo tuần nói chung. Dùng skill này bất cứ khi nào user dán một danh sách task có kèm Jira ID, tên account, % tiến độ và muốn có bản tóm tắt sạch, loại bỏ ID/tên người thực hiện/chi tiết kỹ thuật. Trigger khi user nói: 'tổng hợp sprint summary', 'làm PM sprint summary', 'tóm tắt task cho sếp', 'báo cáo PO/PMO', 'báo cáo steering committee', 'rút gọn báo cáo tuần', 'chuyển task list này thành báo cáo', hoặc dán một khối task có Jira ID kèm yêu cầu tóm tắt/report - kể cả khi không dùng đúng các từ khóa trên."
license: MIT
metadata:
  version: 2.0.0
  category: project-management
  domain: agile-development
  updated: 2026-07-30
---

# PM Sprint Summary

Chuyển đổi task list thô (backlog, Jira export dán tay, ghi chú sprint) thành **một bản báo cáo rút gọn duy nhất** theo góc nhìn Senior IT Project Manager, dùng để gửi PO, PMO, Sponsor hoặc Steering Committee.

---

## Quy tắc làm sạch

- Loại bỏ toàn bộ Jira ID (FSM-xxx, FCR-xxx, DEV-xxx, PROJ-xxx...)
- Loại bỏ tên account/người thực hiện (kể cả trong ngoặc đơn ở cuối dòng)
- Loại bỏ thông tin kỹ thuật không cần thiết (issuetype Story/Task/Subtask, trạng thái Jira chi tiết...)
- **Dấu tiếng Việt**: source từ Jira/Excel thường bị gõ KHÔNG dấu - viết lại output TIẾNG VIỆT CÓ DẤU ĐÚNG (VD "theo doi tien do" → "theo dõi tiến độ", "chuan bi" → "chuẩn bị", "tong ket" → "tổng kết", "rui ro" → "rủi ro"). Tái cấu trúc dấu cho mọi câu tiếng Việt.
- Gộp các task liên quan thành **1 dòng ý gộp** theo kết quả nghiệp vụ - không chia thành nhiều cụm/tiêu đề con
- **TỔNG HỢP & VIẾT LẠI CÔ ĐỌNG (Synthesize / Paraphrase)**: Giữ nguyên vẹn cụm danh từ chỉ kết quả/deliverable, đảm bảo câu văn gãy gọn, đủ nghĩa và đúng chuẩn ngữ pháp PM (khoảng **3–8 từ/dòng**, tuyệt đối không quá 10 từ).
- **TUYỆT ĐỐI KHÔNG ĐỂ CÂU DÀI THÔ & KHÔNG CẮT CỤT CƠ HỌC**:
  - **Không** giữ nguyên câu dài 12–20 từ từ Jira/Backlog vào bản tóm tắt.
  - **Không** ngắt cứng cơ học tại số từ cố định làm đứt đoạn từ ghép / ngữ nghĩa / bổ ngữ cuối câu (ví dụ: không để câu bị cụt lửng như `... log server & Hỗ`, `... Phê duyệt điều kiện`, `... Test Scenarios chi tiết cho`, `... thực hiện kiểm thử chức`).

#### 💡 Bảng đối chiếu viết lại (Synthesize vs Lỗi câu dài / Cắt cụt cơ học):
| Input thô từ Jira / File .md | ❌ Lỗi câu dài / Hard Truncation | ✅ Viết lại chuẩn PM (Synthesize 3–8 từ) |
| :--- | :--- | :--- |
| *Hỗ trợ nghiệp vụ cho DEV và QC, chuẩn bị kịch bản UAT và tài liệu HDSD...* | `- Hỗ trợ nghiệp vụ cho DEV và QC, chuẩn bị` *(Cụt chữ)*<br>`- Hỗ trợ nghiệp vụ cho DEV và QC, chuẩn bị tài liệu bàn giao UAT` *(Quá dài)* | `- Nghiệm thu UAT & tài liệu HDSD` *(7 từ)* |
| *Chuẩn bị test case và thực hiện kiểm thử chức năng cho Sprint 4...* | `- Chuẩn bị test case và thực hiện kiểm thử chức` *(Cụt chữ)*<br>`- Chuẩn bị test case & thực hiện kiểm thử chức năng phân hệ ZNS` *(Quá dài)* | `- Kiểm thử chức năng Sprint 4` *(5 từ)* |
| *Chuẩn bị môi trường và tài liệu phục vụ CSOC Pentest...* | `- Chuẩn bị môi trường và tài liệu phục vụ CSOC` *(Cụt chữ)* | `- Chuẩn bị môi trường Pentest CSOC` *(5 từ)* |
| *Hỗ trợ CSOC pentest và phân loại các lỗ hổng bảo mật phát hiện được...* | `- Hỗ trợ CSOC pentest và phân loại các lỗ hổng` *(Cụt chữ)* | `- Hỗ trợ Pentest & phân loại lỗ hổng` *(7 từ)* |
| *Thực hiện Unit test, deploy staging và fix bug trong quá trình...* | `- Thực hiện Unit test, deploy staging và fix bug` *(Cụt chữ)* | `- Deploy Staging & xử lý lỗi QC` *(7 từ)* |
| *Deploy bản build hoàn thiện Sprint 2 lên môi trường Staging và nghiệm thu nội bộ...* | `- Deploy bản build hoàn thiện Sprint 2 lên môi trường Staging và nghiệm thu nội bộ` *(Quá dài: 16 từ)* | `- Nghiệm thu bản build Sprint 2 Staging` *(7 từ)* |

- Viết theo góc nhìn PM, ưu tiên kết quả/nghiệp vụ hơn chi tiết kỹ thuật
- Mỗi dòng tối đa 1 câu, ngắn gọn súc tích (khoảng 3–8 từ, tối đa 10 từ), ưu tiên dạng danh ngữ. Bắt buộc có dấu gạch đầu dòng `- ` ở đầu mỗi dòng.

### Quy tắc riêng cho mục DONE
- Viết dạng danh ngữ hoặc kết quả đã đạt được
- Không ghi "(Done)"

### Quy tắc riêng cho mục DOING / WILL DO
- Tập trung vào việc cần làm và kế hoạch tiếp theo
- Không giữ %, chỉ giữ mốc due date/sự kiện quan trọng nếu có (ví dụ "Sprint Review ngày 06/08")
- Nếu có due date quá hạn (due date <= hôm nay và task chưa Done) → thêm cảnh báo `⚠️ Trễ hạn {ngày}`

### Quy tắc riêng cho Risks & Issues
- Tóm tắt tối đa 1 câu/rủi ro, ưu tiên rủi ro ảnh hưởng tiến độ chung hoặc go-live
- Ưu tiên các dấu hiệu: task quá hạn, SPI thấp, capacity overload, testing/QC delay

### Giới hạn độ dài
- Mỗi mục (Done / Doing-Will do / Risks) TỐI ĐA ~5 DÒNG - BẮT BUỘC. Nếu input có nhiều task, GỘP các task liên quan thành 1 dòng ý nghiệp vụ, KHÔNG liệt kê từng task. Vượt 5 dòng → gộp thêm cho đến khi ≤5. Ưu tiên ngắn gọn và thông tin có tác động tới quyết định của người nhận (PO/PMO/Sponsor), gộp nhiều task liên quan thành 1 dòng

---

## Header tùy chọn - Overall Status

Nếu user cung cấp (hoặc đã có sẵn trong hội thoại) các thông tin: tên dự án/sprint, ngày báo cáo, health status, Planned/Actual Progress, SPI, RAG % - thêm header này lên **đầu output**, trước mục "✅ Done". Nếu user không cung cấp số liệu này, **bỏ qua header, không tự bịa số liệu**.

Chỉ tóm tắt các ý chính bằng gạch đầu dòng, **không dùng bảng markdown**:

```
{Tên dự án} · {Tên Sprint} - {ngày bắt đầu} – {ngày kết thúc}

- Health: {🟢 On Track / 🟡 At Risk / 🔴 Off Track} (SPI = {X.XX})
- Tiến độ: {Actual X%} / kế hoạch {Planned X%}
- Đúng hạn (RAG): {X%}

---
```

Quy tắc:
- Header là **bổ sung**, không thay thế phần "✅ Done / ▶ Doing-Will do / ⚠️ Risks & Issues" phía sau.
- Số liệu do user cung cấp trực tiếp hoặc lấy sẵn từ report khác (ví dụ đã tính trong skill `weekly-report`) - skill này chỉ format lại, không tự tính SPI/Weighted Progress.
- Nếu chỉ có một phần số liệu → vẫn thêm header nhưng bỏ dòng thiếu, không để trống hoặc ghi "N/A".
- Không liệt kê breakdown theo từng phase (Requirement/Development/Testing/...) - chỉ giữ % tổng thể.

---

## Format output

```
✅ Done
- Kết quả nghiệp vụ 1 (gộp nhiều task liên quan thành 1 dòng)
- Kết quả nghiệp vụ 2

▶ Doing / Will do
- Việc đang làm/kế hoạch tiếp theo, giữ mốc due date/sự kiện quan trọng nếu có
- ...

⚠️ Risks & Issues
- Rủi ro quan trọng nhất, ưu tiên rủi ro ảnh hưởng tiến độ chung hoặc go-live
```

Toàn bộ output là plain text, không dùng markdown heading (#) hay bảng bên trong 3 mục Done/Doing/Risks (chỉ header Overall Status ở trên mới dùng bảng markdown).

---

## 🛫 Preflight Checklist (Bắt buộc kiểm tra trước khi tạo file .txt)

- [ ] **1. Giới hạn độ dài chuẩn tóm tắt (3 – 8 từ/dòng, tối đa 10 từ)**: Đếm số từ từng dòng trong mục Done và Doing. Tuyệt đối **KHÔNG vượt quá 10 từ**, **KHÔNG giữ nguyên câu dài thô** từ Jira/Backlog, và **KHÔNG cắt cụt từ/ngữ cơ học**.
- [ ] **2. Không cắt cụt chữ (Zero Truncation)**: Mỗi dòng là một cụm danh từ hoàn chỉnh ngữ nghĩa, không đứt đoạn từ ghép, không lửng câu, không sót từ nối ở đuôi (`&`, `và`, `cho`, `với`, `của`, `để`, `hỗ`, `chuẩn bị`, `chức`...).
- [ ] **3. Chuẩn hóa Deliverable (Outcome-based)**: Tóm tắt cô đọng thành kết quả/bàn giao (VD: `Nghiệm thu UAT & Sign-off`, `Kiểm thử chức năng Sprint 4`), không kể lể thao tác dev/QC con.
- [ ] **4. Làm sạch 100%**: Đã loại bỏ hoàn toàn Jira ID (FSM-xxx, DEV-xxx...), tên người thực hiện (Account/Assignee), và ký tự markdown thô (`**`, `###`).
- [ ] **5. Định dạng Bullet `- `**: Mỗi dòng trong Done, Doing/Will do, Risks bắt buộc bắt đầu bằng `- `.
- [ ] **6. Số lượng dòng**: Mỗi mục Done và Doing chỉ chứa từ **3 đến 5 dòng**.

---

## Workflow

1. Nhận task list thô từ user (dán trực tiếp trong chat).
2. Áp dụng quy tắc làm sạch, dùng năng lực AI tổng hợp (Synthesize / Paraphrase) toàn bộ các task thành danh ngữ deliverable/kế hoạch hoàn chỉnh (khoảng 3–8 từ, tối đa 10 từ, tuyệt đối không ngắt cụt câu), và thêm header Overall Status nếu có đủ số liệu.
3. Thực hiện kiểm tra toàn bộ 6 tiêu chí trong **Preflight Checklist**.
4. Tạo file `.txt` theo đúng "Format output" ở trên bằng `create_file`, lưu vào thư mục làm việc.
   - Tên file mặc định: `pmo_sprint_summary.txt` (đổi tên nếu user chỉ định, hoặc dùng `{ten_du_an}_pmo_summary.txt` nếu có tên dự án cụ thể)
   - Extension bắt buộc là `.txt`
   - KHÔNG in lại toàn bộ nội dung file trong code block ở chat - chỉ present file, health (On/Off track/At issue).

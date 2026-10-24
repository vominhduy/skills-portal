# Hướng dẫn Cấu trúc Template PRD và Test Case Chuẩn

## 1. Cấu trúc File Test Case Chuẩn (.xlsx)

File Excel Test Case chuẩn có thể gồm nhiều Sheet đại diện cho từng chức năng/màn hình.
Mỗi Sheet hợp lệ **BẮT BUỘC** phải có các cột tiêu chuẩn sau:

| STT Cột | Tên Cột Chuẩn | Tên Khác / Nhận diện | Bắt buộc? | Ý nghĩa |
|---|---|---|:---:|---|
| 1 | **Testcase ID** | `Mã testcase`, `TC ID`, `ID` | Có | Mã định danh duy nhất (VD: `TC_01.1`, `TC_02.5`) |
| 2 | **Req ID** | `Mã yêu cầu`, `Requirement ID`, `Traceability` | Có | Mã yêu cầu tương ứng trong PRD (VD: `REQ-QUANLYUNGDUNG-001`) |
| 3 | **DOC Source** | `Nguồn tài liệu` | Không | Mã tài liệu tham chiếu (VD: `DOC-v3.7-01`) |
| 4 | **Group** | `Nhóm`, `Loại test` | Không | Phân loại testcase (VD: `Functional`, `Security`, `Portal`) |
| 5 | **Priority** | `Độ ưu tiên`, `Mức ưu tiên` | Không | Mức độ ưu tiên gốc (VD: `High`, `Medium`, `Low`) |
| 6 | **Test Title** | `Nội dung test`, `Tên testcase`, `Tiêu đề` | **Có** | Mô tả tóm tắt mục tiêu kiểm thử |
| 7 | **Pre-condition** | `Điều kiện/Dữ liệu`, `Tiền điều kiện` | Không | Actor, quyền hạn, dữ liệu chuẩn bị trước test |
| 8 | **Test Steps** | `Các bước`, `Bước thực hiện`, `Steps` | **Có** | Các bước hành động trên giao diện (1., 2., 3...) |
| 9 | **Expected Result** | `Kết quả mong đợi`, `Expected` | **Có** | Kết quả kỳ vọng quan sát được (Pass/Fail) |
| 10 | **Origin** | `Nguồn gốc` | Không | `AI`, `QC`, `Dev`... |

### ⛔ Quy tắc lọc Sheet của Script
- Script `scripts/parse_testcases.py` **CHỈ đọc các sheet có đầy đủ các cột Test Case như trên**.
- Các sheet không chứa bảng testcase (như `Cover`, `Summary`, `Change Log`, `Guidelines`, `Config`, `History`, `Dashboard`...) sẽ **tự động bị bỏ qua** để tránh dữ liệu rác.

---

## 2. Cấu trúc Tài liệu PRD Chuẩn (.docx / .md)

Tài liệu PRD là **Single Source of Truth (SSOT)**, bao gồm:
1. **Mục tiêu & Phạm vi (Scope & Out of Scope)**.
2. **Danh sách yêu cầu chức năng (Functional Requirements - FR)** kèm mã Req ID (`REQ-XXX-NNN`).
3. **Tiêu chí chấp nhận & Quy tắc nghiệp vụ (Acceptance Criteria - AC / Business Rules - BR)**:
   - Các quy tắc ràng buộc dữ liệu (tên trùng, mã sinh tự động, điều kiện xóa...).
   - Ma trận phê duyệt (*Approval Decision Matrix*): Thêm mới vs Sửa vs Đổi Hyperlink vs Xóa.
4. **Đặc tả giao diện (UI Specification & Field Rules)**:
   - Danh sách trường, kiểu dữ liệu, bắt buộc, độ dài, placeholder.
   - Thao tác trên Grid/Bảng: Ẩn/hiện nút Sửa/Xóa tùy trạng thái phê duyệt.
   - Nội dung thông báo hiển thị (Toast / Popup).
5. **Yêu cầu phi chức năng (Non-Functional Requirements - NFR)**:
   - `NFR-01 Availability`, `NFR-02 Security (Phân quyền/Role-based URL direct access)`, `NFR-03 Compatibility (Chrome, Edge, Firefox)`.

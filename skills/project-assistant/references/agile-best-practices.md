# Agile & Scrum Best Practices Guide

Tài liệu tham khảo nghiệp vụ Agile/Scrum dành cho Trợ lý dự án.

## 1. Scrum Roles & Responsibilities

- **Product Owner (PO)**: Quản lý Product Backlog, định hình tầm nhìn sản phẩm, tối ưu hóa giá trị mang lại, ưu tiên các User Stories.
- **Scrum Master (SM)**: Người dẫn dắt quy trình Scrum, loại bỏ trở ngại (impediments/blockers), thúc đẩy cải tiến liên tục, bảo vệ team khỏi xao nhãng.
- **Developers (Team)**: Tự tổ chức, đa chức năng, chịu trách nhiệm chuyển giao Increment có thể sử dụng được vào cuối mỗi Sprint.

---

## 2. Scrum Ceremonies (Sự kiện Scrum)

| Sự kiện | Thời lượng khuyến nghị (Sprint 2 tuần) | Mục tiêu chính |
|---|---|---|
| **Sprint Planning** | 2-4 giờ | Xác định Sprint Goal, chọn User Stories và chia nhỏ thành Sub-tasks |
| **Daily Scrum** | 15 phút hàng ngày | Đồng bộ tiến độ 24h qua, kế hoạch 24h tới, nhận diện blockers |
| **Sprint Review** | 1-2 giờ cuối Sprint | Demo sản phẩm hoàn thành, thu thập feedback từ Stakeholders |
| **Sprint Retrospective** | 1-1.5 giờ cuối Sprint | Đánh giá cách làm việc (What went well, What can improve, Action items) |
| **Backlog Refinement** | 1-2 giờ giữa Sprint | Làm mịn backlog, phân tích, ước lượng story points cho sprint kế tiếp |

---

## 3. User Story & INVEST Criteria

Cấu trúc chuẩn:
> *Là một [vai trò người dùng], tôi muốn [tính năng/hành động] để [lợi ích/mục tiêu đạt được].*

**INVEST Criteria:**
- **I**ndependent (Độc lập)
- **N**egotiable (Có thể thương lượng)
- **V**aluable (Mang lại giá trị)
- **E**stimable (Có thể ước lượng)
- **S**mall (Đủ nhỏ, hoàn thành trong 1 Sprint)
- **T**estable (Có thể kiểm thử được - kèm Acceptance Criteria rõ ràng)

---

## 4. Definition of Done (DoD) & Definition of Ready (DoR)

- **Definition of Ready (DoR)**: Tiêu chuẩn để 1 story được đưa vào Sprint Planning:
  - Có User Story rõ ràng + Acceptance Criteria.
  - Đã có Story Point ước lượng.
  - Phụ thuộc (dependencies) đã được giải quyết hoặc kiểm soát.
  - Đã có UI/UX mockup / API specs (nếu cần).
- **Definition of Done (DoD)**: Tiêu chuẩn để 1 story được xem là hoàn thành:
  - Code hoàn thiện, pass Unit Tests & Integration Tests.
  - Đã qua Code Review & Merge vào nhánh chính.
  - Đã pass kiểm thử QA/QC trên môi trường Staging.
  - Tài liệu/release note cập nhật.

---

## 5. Estimation & Story Points

- **Fibonacci Sequence**: 1, 2, 3, 5, 8, 13, 21 (Điểm phản ánh: Độ phức tạp + Khối lượng công việc + Mức độ rủi ro/bất định).
- **Quy tắc vàng**: Nếu story >= 13 điểm → Bắt buộc chia nhỏ (split) thành các stories 3-5-8 điểm.

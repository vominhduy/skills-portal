# Product Backlog & Sprint Planning - Internal Guide v2.0

> **INTERNAL REFERENCE ONLY** - Không đưa nội dung này vào output cuối cùng.  
> Scrum Master **bắt buộc đọc file này** trước khi tạo bất kỳ Sprint Backlog nào.

---

## STORY POINT GUIDELINE

### Story Point Formula (v2.0)

**Story Point = Trung bình của 3 giá trị:**  
`(Total Story Manday + (Priority × 2) + (Complexity × 2)) / 3`

| Thành phần          | Định nghĩa |
|---------------------|----------|
| **Total Story Manday** | Tổng effort (Manday) của tất cả tasks thuộc User Story |
| **Priority**        | Mức độ ưu tiên (1-4) |
| **Complexity**      | Độ phức tạp kỹ thuật (1-3) |

**Lưu ý quan trọng:**  
- Story Point chỉ dùng để ước tính kích thước tương đối và tính velocity.  
- Effort (Manday/Hour) là giá trị thực tế dùng để tính duration và phân công PIC.

### Priority Scale `priority`

| Level | Name     | Định nghĩa |
|-------|----------|----------|
| 4     | Critical | Cấp bách, chỉ đạo từ lãnh đạo, phải làm ngay |
| 3     | High     | Must have – chức năng quan trọng nhất sprint |
| 2     | Medium   | Should have – quan trọng nhưng có thể linh hoạt |
| 1     | Low      | Could have – mong muốn, không bắt buộc |

### Complexity Scale `complexity`

| Level | Name | Định nghĩa |
|------|------|------------|
| 3 | High | Liên quan nhiều module/hệ thống (> 3), có tích hợp hoặc phụ thuộc chéo; sử dụng công nghệ mới/chưa quen; logic xử lý phức tạp, nhiều luồng (branch), edge case; rủi ro cao |
| 2 | Medium | Liên quan 2–3 module; công nghệ quen thuộc; logic xử lý ở mức trung bình, có một số điều kiện/branch; rủi ro ở mức vừa |
| 1 | Low | Phạm vi độc lập hoặc 1 module; không phụ thuộc hệ thống khác; logic đơn giản, ít điều kiện; rủi ro thấp |

### Task Status `status`

| Value | Name | Định nghĩa |
|------|------|------------|
| `Not Started` | Not Started | Chưa bắt đầu |
| `In Progress` | In Progress | Đang thực hiện |
| `Done` | Done | Hoàn thành |
| `Pending` | Pending | Task bị chặn do dependency, thiếu thông tin hoặc issue |
| `Blocked` | Blocked | Bị block bởi yếu tố ngoài, cần escalate |
| `Cancelled` | Cancelled | Đã loại khỏi scope |

### Task Process `task_process`

| Name | Định nghĩa |
|----------------|----------------------|
| Requirement & Design | Phân tích, xác định yêu cầu của dự án (chức năng và phi chức năng) & thiết kế kiến trúc hệ thống, DB, giao diện và các Task liên quan process/giai đoạn Requirement & Design |
| Coding | Coding và các Task liên quan process/giai đoạn Coding |
| Unit Test | Unit Test và các Task liên quan process/giai đoạn Unit Test |
| Testing | Các task IT, System Test, Performance Test, Pentest và các Task liên quan process/giai đoạn test/testing |
| UAT | Các Task liên quan process/giai đoạn UAT (kèm fix bug) |
| Deployment | Task Deployment, Pilot và các Task liên quan process/giai đoạn Deployment/Pilot |
| Project Management | Các task quản lý dự án |
| Monitor, Audit | Các task liên quan review, audit, monitor dự án của QA |
| Hot Request | Các yêu cầu gấp (liên quan chiến lược công ty/các yêu cầu gấp từ BĐH, BGĐ…) |
| Service Request | Các yêu cầu support như tạo account, phân quyền, xử lý dữ liệu, cung cấp data, check số liệu, các yêu cầu nhỏ không ảnh hưởng/thay đổi business, nghiệp vụ, low-risk & ảnh hưởng ít user |
| Maintenance | Liên quan đến việc monitor, duy trì và hỗ trợ hệ thống, ứng dụng hoặc dịch vụ hiện có. Bao gồm: hot fix, fix bug, cập nhật phần mềm, backup - restore và bảo trì hạ tầng |
| R&D | Các task research liên quan việc nghiên cứu và phát triển các sản phẩm, dịch vụ hoặc công nghệ mới: Product, Technology, Framework, Process, Model |
| Non-Project | Các task không thuộc dự án, liên quan đào tạo, tham gia phong trào (đi học, seminar, team building, khám sức khỏe…) |

### Type of Work `type_of_work`

| Name | Định nghĩa |
|------|------------|
| Study | Học, tìm hiểu thông tin dự án, các Task Support liên quan process/giai đoạn trong dự án |
| Do | Task phụ trách thực thi công việc trong từng process/giai đoạn |
| Review | Task review tài liệu/sourcecode |
| Fix/Rework | Task thực hiện lại công việc đã làm trước đó (update tài liệu, fix bug) |

### Task Complexity Criteria

| Tiêu chí | 0 điểm | 1 điểm | 2 điểm |
|---------|--------|--------|--------|
| Scope (module/system) | 1 module | 2–3 module | > 3 module / cross-system |
| Logic | Đơn giản, ít điều kiện | Có nhiều điều kiện/branch | Phức tạp, nhiều luồng + edge case |
| Dependency | Không phụ thuộc | Phụ thuộc nhẹ (API nội bộ) | Phụ thuộc ngoài / team khác |
| Tech/Risk | Công nghệ quen thuộc | Có phần chưa rõ | Công nghệ mới / unknown |

### Mapping Score → Task Complexity `task_complexity`

| Tổng điểm | Task Complexity |
|----------|----------------|
| 0 – 2 | 6 |
| 3 – 5 | 7 |
| 6 – 8 | 8 |

### Task Priority Scale

| Level | Name | Định nghĩa |
|------|------|------------|
| 4 | Critical | Blocker hoặc bắt buộc để tiếp tục (dependency); ảnh hưởng trực tiếp tiến độ hoặc release |
| 3 | High | Quan trọng trong flow chính; cần hoàn thành sớm để unlock task khác |
| 2 | Medium | Task hỗ trợ; không block; có thể làm sau |
| 1 | Low | Nice-to-have; không ảnh hưởng tiến độ |

### Task Priority Criteria

| Tiêu chí | 0 điểm | 1 điểm | 2 điểm |
|---------|--------|--------|--------|
| Blocker | Không | Block nhẹ | Block nhiều task / team |
| Business Impact | Thấp | Trung bình | Cao |
| Urgency (deadline) | Không gấp | Cần sớm | Gấp / release |
| Dependency | Không | Có phụ thuộc | Là tiền đề cho nhiều task |

### Mapping Score → Priority `task_priority`

| Tổng điểm | Priority |
|----------|----------|
| 0 – 2 | Low |
| 3 – 4 | Medium |
| 5 – 6 | High |
| 7 – 8 | Critical |

## CAPACITY DEFAULTS (khi user chưa cung cấp thông tin)

| Quy tắc                          | Giá trị mặc định          |
|----------------------------------|---------------------------|
| Giờ làm việc / tuần / member     | 40 giờ (full-time)        |
| Giờ làm việc / ngày / member     | 8 giờ                     |
| Overhead (meeting, review, admin)| **20%** → Net capacity = **32h/tuần/member** |
| 1 Manday                         | 8 giờ                     |

**Lưu ý:** Overhead 20% dùng để kiểm tra capacity thực tế. Duration Sprint vẫn tính theo công thức Total Manday Net ở trên.


---

> **QA Timeline & Phase/Milestone:** Xem quy tắc chi tiết tại **SKILL.md Step 6 và Step 7**.

---


## USAGE GUIDE

### How to Use This Template

1. **Fill in Project Information** (Section 1) - complete before project kickoff
2. **Define the Roadmap** (Section 2) - align with stakeholders
3. **Build the Product Backlog** (Section 3) - PO owns and prioritizes
4. **Maintain Sprint Backlogs** (Section 4) - Scrum Master + Team update each Sprint
5. **Apply Story Point Guideline** (above) - reference during Sprint Planning

### User Story ID Convention

```
US_{EPIC_NUMBER}.{STORY_NUMBER}
Example: US_1.1, US_1.2, US_2.1, US_2.2
```

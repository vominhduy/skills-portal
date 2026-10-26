const fs = require('fs');
const path = require('path');
const ExcelJS = require('exceljs');

const backlogData = {
  project: "FTI-SAL v3.1 - Salary Management System (FTI Salary)",
  sprint_number: 3,
  sprint_goal: "Hoàn thiện số hóa tính lương nhóm dịch vụ Kênh thuê riêng (code đến 10/11), QC kiểm thử toàn diện theo kế hoạch thỏa thuận (13/11-26/11), CSOC Pentest độc lập sau QC (27/11-01/12), nghiệm thu UAT, deploy production Thứ 2 (07/12) và vận hành pilot (07-11/12).",
  time_box: [
    "1. Sprint Timeline: From 13/10/2026 To 11/12/2026 (9 weeks / 44 working days)",
    "2. Daily Scrum: 15 min/ngay (9:00 AM)",
    "3. Dev Complete: 10/11/2026 (Staging Deploy)",
    "4. QC Testing Phase (Theo thỏa thuận QC): 13/11/2026 - 26/11/2026 (QC Sign-off 26/11)",
    "5. CSOC Pentest Phase (Staging - Sau QC): 27/11/2026 - 01/12/2026",
    "6. Pentest Remediation & UAT Phase: 02/12/2026 - 04/12/2026 (Security & UAT Sign-off)",
    "7. Production Deploy: 07/12/2026 (Mon - T2 Rule)",
    "8. Pilot & Sprint Close: 07/12/2026 - 11/12/2026 (Sprint Review & Retro 11/12)"
  ],
  epics: [
    {
      epic: "EPIC-1: Thu thập yêu cầu, kiến trúc hệ thống và phân tích dữ liệu lương KTR",
      user_stories: [
        {
          us_id: "US_3.1",
          module: "Requirement & Setup",
          description: "Phân tích nghiệp vụ hóa đơn lương tay GB và thiết kế URD",
          priority: "3-High",
          complexity: "2-Medium",
          tasks: [
            {
              pic: "PM",
              task_name: "Tổ chức Kick-off, lập Sprint Planning & thiết lập Risk Register",
              status: "Not Started",
              start_date: "13/10/2026",
              due_date: "13/10/2026",
              est_effort_hour: 8,
              notes: "PM kick-off sprint",
              task_complexity: 6,
              type_of_work: "Do",
              task_process: "Project Management",
              task_priority: "High"
            },
            {
              pic: "BA",
              task_name: "Khảo sát và thu thập yêu cầu tính lương dịch vụ Kênh thuê riêng",
              status: "Not Started",
              start_date: "13/10/2026",
              due_date: "14/10/2026",
              est_effort_hour: 16,
              notes: "Làm việc với stakeholder và khối kinh doanh",
              task_complexity: 6,
              type_of_work: "Do",
              task_process: "Requirement & Design",
              task_priority: "High"
            },
            {
              pic: "DEV",
              task_name: "Review kiến trúc Core lương v3.1 & thiết lập môi trường Dev",
              status: "Not Started",
              start_date: "13/10/2026",
              due_date: "14/10/2026",
              est_effort_hour: 16,
              notes: "Setup local/dev environment",
              task_complexity: 6,
              type_of_work: "Do",
              task_process: "Coding",
              task_priority: "High"
            },
            {
              pic: "BA",
              task_name: "Phân tích dữ liệu hóa đơn và quy tắc tính lương tay GB",
              status: "Not Started",
              start_date: "15/10/2026",
              due_date: "15/10/2026",
              est_effort_hour: 8,
              notes: "Phân tích số liệu hóa đơn đối soát",
              task_complexity: 6,
              type_of_work: "Do",
              task_process: "Requirement & Design",
              task_priority: "Medium"
            },
            {
              pic: "DEV",
              task_name: "Thiết kế cấu trúc Database bảng lương KTR và dữ liệu mẫu",
              status: "Not Started",
              start_date: "15/10/2026",
              due_date: "16/10/2026",
              est_effort_hour: 16,
              notes: "DB Schema & Migration script",
              task_complexity: 6,
              type_of_work: "Do",
              task_process: "Coding",
              task_priority: "High"
            },
            {
              pic: "BA",
              task_name: "Xây dựng Wireframe và hoàn tất tài liệu URD phân hệ KTR",
              status: "Not Started",
              start_date: "16/10/2026",
              due_date: "16/10/2026",
              est_effort_hour: 8,
              notes: "Hoàn tất URD bàn giao cho DEV và QC",
              task_complexity: 6,
              type_of_work: "Do",
              task_process: "Requirement & Design",
              task_priority: "High"
            }
          ]
        }
      ]
    },
    {
      epic: "EPIC-2: Phát triển phân hệ Nhập liệu CID và Phân quyền thao tác TDV",
      user_stories: [
        {
          us_id: "US_3.2",
          module: "CID Management",
          description: "Xây dựng giao diện nhập liệu và phân quyền dữ liệu CID",
          priority: "3-High",
          complexity: "3-High",
          tasks: [
            {
              pic: "PM",
              task_name: "Theo dõi tiến độ phát triển & Risk Tracking – Tuần 2",
              status: "Not Started",
              start_date: "19/10/2026",
              due_date: "19/10/2026",
              est_effort_hour: 8,
              notes: "PM tracking tuần 2",
              task_complexity: 6,
              type_of_work: "Do",
              task_process: "Project Management",
              task_priority: "Medium"
            },
            {
              pic: "BA",
              task_name: "Làm rõ chi tiết nghiệp vụ luồng nhập CID và xác thực dữ liệu",
              status: "Not Started",
              start_date: "19/10/2026",
              due_date: "19/10/2026",
              est_effort_hour: 8,
              notes: "Nghiệp vụ luồng nhập CID",
              task_complexity: 6,
              type_of_work: "Do",
              task_process: "Requirement & Design",
              task_priority: "Medium"
            },
            {
              pic: "DEV",
              task_name: "Xây dựng Backend API kiểm tra và nhập danh sách CID",
              status: "Not Started",
              start_date: "19/10/2026",
              due_date: "20/10/2026",
              est_effort_hour: 16,
              notes: "Backend API validation CID",
              task_complexity: 6,
              type_of_work: "Do",
              task_process: "Coding",
              task_priority: "High"
            },
            {
              pic: "BA",
              task_name: "Chi tiết hóa ma trận phân quyền dữ liệu thao tác CID theo vai trò",
              status: "Not Started",
              start_date: "20/10/2026",
              due_date: "21/10/2026",
              est_effort_hour: 16,
              notes: "Ma trận RBAC phân quyền TDV",
              task_complexity: 6,
              type_of_work: "Do",
              task_process: "Requirement & Design",
              task_priority: "High"
            },
            {
              pic: "DEV",
              task_name: "Phát triển giao diện nhập và xác thực danh sách CID cho TDV",
              status: "Not Started",
              start_date: "21/10/2026",
              due_date: "22/10/2026",
              est_effort_hour: 16,
              notes: "UI Webapp CID entry",
              task_complexity: 6,
              type_of_work: "Do",
              task_process: "Coding",
              task_priority: "High"
            },
            {
              pic: "DEV",
              task_name: "Xây dựng màn hình xem và cơ chế phân quyền dữ liệu thao tác CID",
              status: "Not Started",
              start_date: "23/10/2026",
              due_date: "23/10/2026",
              est_effort_hour: 8,
              notes: "View & Permission management",
              task_complexity: 6,
              type_of_work: "Do",
              task_process: "Coding",
              task_priority: "High"
            },
            {
              pic: "PM",
              task_name: "Theo dõi tiến độ phát triển phân quyền CID – Tuần 3",
              status: "Not Started",
              start_date: "26/10/2026",
              due_date: "26/10/2026",
              est_effort_hour: 8,
              notes: "PM tracking tuần 3",
              task_complexity: 6,
              type_of_work: "Do",
              task_process: "Project Management",
              task_priority: "Medium"
            },
            {
              pic: "DEV",
              task_name: "Phát triển tính năng Import Excel danh sách CID khối lượng lớn",
              status: "Not Started",
              start_date: "26/10/2026",
              due_date: "27/10/2026",
              est_effort_hour: 16,
              notes: "Batch import Excel CID",
              task_complexity: 6,
              type_of_work: "Do",
              task_process: "Coding",
              task_priority: "High"
            },
            {
              pic: "BA",
              task_name: "Soạn thảo kịch bản UAT Scenario phân hệ quản lý và nhập CID",
              status: "Not Started",
              start_date: "26/10/2026",
              due_date: "27/10/2026",
              est_effort_hour: 16,
              notes: "Kịch bản UAT CID",
              task_complexity: 6,
              type_of_work: "Do",
              task_process: "Requirement & Design",
              task_priority: "High"
            },
            {
              pic: "BA",
              task_name: "Soạn thảo User Guide hướng dẫn nhập và quản lý CID cho TDV",
              status: "Not Started",
              start_date: "28/10/2026",
              due_date: "28/10/2026",
              est_effort_hour: 8,
              notes: "Tài liệu HDSD CID",
              task_complexity: 6,
              type_of_work: "Do",
              task_process: "Requirement & Design",
              task_priority: "Medium"
            },
            {
              pic: "DEV",
              task_name: "Hoàn thiện API phân quyền động và viết Unit Test phân hệ CID",
              status: "Not Started",
              start_date: "28/10/2026",
              due_date: "29/10/2026",
              est_effort_hour: 16,
              notes: "Unit test CID & RBAC",
              task_complexity: 6,
              type_of_work: "Do",
              task_process: "Coding",
              task_priority: "High"
            },
            {
              pic: "DEV",
              task_name: "Tối ưu hiệu năng xử lý dữ liệu CID và đóng gói phần 1",
              status: "Not Started",
              start_date: "30/10/2026",
              due_date: "30/10/2026",
              est_effort_hour: 8,
              notes: "Performance & Refactor CID",
              task_complexity: 6,
              type_of_work: "Do",
              task_process: "Coding",
              task_priority: "High"
            }
          ]
        }
      ]
    },
    {
      epic: "EPIC-3: Core giải thuật tính lương KTR và Bảng lương (Dev đến 10/11)",
      user_stories: [
        {
          us_id: "US_3.3",
          module: "Salary Engine & Payroll",
          description: "Xây dựng engine tính lương KTR và xuất báo cáo bảng lương",
          priority: "3-High",
          complexity: "3-High",
          tasks: [
            {
              pic: "PM",
              task_name: "Theo dõi tiến độ phát triển Core lương KTR – Tuần 4",
              status: "Not Started",
              start_date: "02/11/2026",
              due_date: "02/11/2026",
              est_effort_hour: 8,
              notes: "PM tracking tuần 4",
              task_complexity: 6,
              type_of_work: "Do",
              task_process: "Project Management",
              task_priority: "Medium"
            },
            {
              pic: "BA",
              task_name: "Làm rõ công thức tính lương nâng cao cho dịch vụ Kênh thuê riêng",
              status: "Not Started",
              start_date: "02/11/2026",
              due_date: "02/11/2026",
              est_effort_hour: 8,
              notes: "Công thức chi tiết KTR",
              task_complexity: 6,
              type_of_work: "Do",
              task_process: "Requirement & Design",
              task_priority: "High"
            },
            {
              pic: "DEV",
              task_name: "Phát triển Core giải thuật tính lương KTR theo quy tắc mới",
              status: "Not Started",
              start_date: "02/11/2026",
              due_date: "03/11/2026",
              est_effort_hour: 16,
              notes: "Core engine calculation KTR",
              task_complexity: 8,
              type_of_work: "Do",
              task_process: "Coding",
              task_priority: "High"
            },
            {
              pic: "BA",
              task_name: "Thiết kế mẫu bảng lương và định dạng xuất Excel KTR",
              status: "Not Started",
              start_date: "03/11/2026",
              due_date: "04/11/2026",
              est_effort_hour: 16,
              notes: "Mẫu báo cáo bảng lương Excel",
              task_complexity: 6,
              type_of_work: "Do",
              task_process: "Requirement & Design",
              task_priority: "High"
            },
            {
              pic: "DEV",
              task_name: "Xây dựng bảng hiển thị chi tiết kết quả lương KTR trên web",
              status: "Not Started",
              start_date: "04/11/2026",
              due_date: "05/11/2026",
              est_effort_hour: 16,
              notes: "UI bảng lương KTR",
              task_complexity: 6,
              type_of_work: "Do",
              task_process: "Coding",
              task_priority: "High"
            },
            {
              pic: "DEV",
              task_name: "Phát triển tính năng xuất file Excel bảng lương KTR chuẩn format",
              status: "Not Started",
              start_date: "06/11/2026",
              due_date: "06/11/2026",
              est_effort_hour: 8,
              notes: "Export Excel bảng lương KTR",
              task_complexity: 6,
              type_of_work: "Do",
              task_process: "Coding",
              task_priority: "High"
            },
            {
              pic: "PM",
              task_name: "Thẩm định mốc Dev Complete 10/11 & điều phối triển khai Staging",
              status: "Not Started",
              start_date: "09/11/2026",
              due_date: "09/11/2026",
              est_effort_hour: 8,
              notes: "Review mốc dev complete",
              task_complexity: 6,
              type_of_work: "Do",
              task_process: "Project Management",
              task_priority: "High"
            },
            {
              pic: "BA",
              task_name: "Soạn thảo kịch bản UAT Scenario cho phân hệ tính lương KTR",
              status: "Not Started",
              start_date: "09/11/2026",
              due_date: "10/11/2026",
              est_effort_hour: 16,
              notes: "Kịch bản UAT lương KTR",
              task_complexity: 6,
              type_of_work: "Do",
              task_process: "Requirement & Design",
              task_priority: "High"
            },
            {
              pic: "DEV",
              task_name: "Viết Unit Test toàn diện Core lương KTR và giải thuật tính",
              status: "Not Started",
              start_date: "09/11/2026",
              due_date: "09/11/2026",
              est_effort_hour: 8,
              notes: "Unit test Core lương",
              task_complexity: 6,
              type_of_work: "Do",
              task_process: "Coding",
              task_priority: "High"
            },
            {
              pic: "DEV",
              task_name: "Đóng gói mã nguồn bản build hoàn thiện và Deploy lên Staging (Dev Complete)",
              status: "Not Started",
              start_date: "10/11/2026",
              due_date: "10/11/2026",
              est_effort_hour: 8,
              notes: "Dev Complete 10/11 & Staging Deploy",
              task_complexity: 6,
              type_of_work: "Do",
              task_process: "Deployment",
              task_priority: "Critical"
            }
          ]
        }
      ]
    },
    {
      epic: "EPIC-4: QC Testing (13-26/11), CSOC Pentest sau QC, UAT, Deploy Production & Pilot",
      user_stories: [
        {
          us_id: "US_3.4",
          module: "Testing, Security, Release & Pilot",
          description: "QC testing thỏa thuận CSOC pentest sau QC nghiệm thu UAT deploy và pilot",
          priority: "3-High",
          complexity: "3-High",
          tasks: [
            {
              pic: "BA",
              task_name: "Demo & Clear nghiệp vụ chi tiết cho QC trên môi trường Staging",
              status: "Not Started",
              start_date: "11/11/2026",
              due_date: "12/11/2026",
              est_effort_hour: 16,
              notes: "BA demo nghiệp vụ chi tiết cho QC",
              task_complexity: 6,
              type_of_work: "Do",
              task_process: "Requirement & Design",
              task_priority: "High"
            },
            {
              pic: "DEV",
              task_name: "Tối ưu câu truy vấn bảng lương và chuẩn bị môi trường Staging sạch",
              status: "Not Started",
              start_date: "11/11/2026",
              due_date: "12/11/2026",
              est_effort_hour: 16,
              notes: "DEV chuẩn bị testbed Staging",
              task_complexity: 6,
              type_of_work: "Do",
              task_process: "Coding",
              task_priority: "High"
            },
            {
              pic: "QC",
              task_name: "Nghiên cứu tài liệu URD nghiệp vụ phân hệ KTR và làm rõ Q&A cùng BA",
              status: "Not Started",
              start_date: "13/11/2026",
              due_date: "13/11/2026",
              est_effort_hour: 8,
              notes: "QC bắt đầu sprint 13/11: đọc nghiệp vụ",
              task_complexity: 6,
              type_of_work: "Do",
              task_process: "Testing",
              task_priority: "High"
            },
            {
              pic: "DEV",
              task_name: "Hỗ trợ QC onboarding nghiệp vụ phân hệ KTR và chuẩn bị dữ liệu mẫu",
              status: "Not Started",
              start_date: "13/11/2026",
              due_date: "13/11/2026",
              est_effort_hour: 8,
              notes: "DEV hỗ trợ QC onboarding 13/11",
              task_complexity: 6,
              type_of_work: "Do",
              task_process: "Coding",
              task_priority: "High"
            },
            {
              pic: "BA",
              task_name: "Hỗ trợ QC giải đáp nghiệp vụ và làm rõ các ca tính lương phức tạp",
              status: "Not Started",
              start_date: "13/11/2026",
              due_date: "13/11/2026",
              est_effort_hour: 8,
              notes: "BA hỗ trợ QC đọc nghiệp vụ",
              task_complexity: 6,
              type_of_work: "Do",
              task_process: "Requirement & Design",
              task_priority: "Medium"
            },
            {
              pic: "PM",
              task_name: "Theo dõi tiến độ QC viết Testcase & chuẩn bị kiểm thử Staging – Tuần 6",
              status: "Not Started",
              start_date: "16/11/2026",
              due_date: "16/11/2026",
              est_effort_hour: 8,
              notes: "PM tracking tuần 6",
              task_complexity: 6,
              type_of_work: "Do",
              task_process: "Project Management",
              task_priority: "High"
            },
            {
              pic: "QC",
              task_name: "Xây dựng và update Test Cases phân hệ CID, import Excel và phân quyền TDV",
              status: "Not Started",
              start_date: "16/11/2026",
              due_date: "17/11/2026",
              est_effort_hour: 16,
              notes: "QC viết & update TC phân hệ CID",
              task_complexity: 6,
              type_of_work: "Do",
              task_process: "Testing",
              task_priority: "High"
            },
            {
              pic: "DEV",
              task_name: "Review mã nguồn và tối ưu hiệu năng tính toán giải thuật lương KTR",
              status: "Not Started",
              start_date: "16/11/2026",
              due_date: "17/11/2026",
              est_effort_hour: 16,
              notes: "DEV code review & tuning",
              task_complexity: 6,
              type_of_work: "Do",
              task_process: "Coding",
              task_priority: "High"
            },
            {
              pic: "BA",
              task_name: "Hoàn thiện tài liệu User Guide hướng dẫn tính lương KTR cho khối nghiệp vụ",
              status: "Not Started",
              start_date: "16/11/2026",
              due_date: "17/11/2026",
              est_effort_hour: 16,
              notes: "User Guide lương KTR",
              task_complexity: 6,
              type_of_work: "Do",
              task_process: "Requirement & Design",
              task_priority: "High"
            },
            {
              pic: "QC",
              task_name: "Xây dựng và update Test Cases phân hệ Core giải thuật lương KTR & đối soát",
              status: "Not Started",
              start_date: "18/11/2026",
              due_date: "19/11/2026",
              est_effort_hour: 16,
              notes: "QC viết & update TC Core lương",
              task_complexity: 6,
              type_of_work: "Do",
              task_process: "Testing",
              task_priority: "High"
            },
            {
              pic: "DEV",
              task_name: "Xây dựng bộ Integration Tests kiểm tra các trường hợp biên đối soát lương",
              status: "Not Started",
              start_date: "18/11/2026",
              due_date: "19/11/2026",
              est_effort_hour: 16,
              notes: "Integration tests lương KTR",
              task_complexity: 6,
              type_of_work: "Do",
              task_process: "Coding",
              task_priority: "High"
            },
            {
              pic: "BA",
              task_name: "Chuẩn bị bộ dữ liệu mẫu nghiệm thu UAT với đại diện các khối nghiệp vụ",
              status: "Not Started",
              start_date: "18/11/2026",
              due_date: "19/11/2026",
              est_effort_hour: 16,
              notes: "Dữ liệu mẫu UAT",
              task_complexity: 6,
              type_of_work: "Do",
              task_process: "Requirement & Design",
              task_priority: "High"
            },
            {
              pic: "QC",
              task_name: "Review Test Cases, chuẩn bị test data và bắt đầu kiểm thử Staging đợt 1",
              status: "Not Started",
              start_date: "20/11/2026",
              due_date: "20/11/2026",
              est_effort_hour: 8,
              notes: "QC review TC & bắt đầu test đợt 1",
              task_complexity: 6,
              type_of_work: "Do",
              task_process: "Testing",
              task_priority: "High"
            },
            {
              pic: "DEV",
              task_name: "Standby hỗ trợ QC kiểm thử đợt 1 và theo dõi rà soát logs hệ thống Staging",
              status: "Not Started",
              start_date: "20/11/2026",
              due_date: "20/11/2026",
              est_effort_hour: 8,
              notes: "DEV standby hỗ trợ QC test",
              task_complexity: 6,
              type_of_work: "Do",
              task_process: "Coding",
              task_priority: "High"
            },
            {
              pic: "BA",
              task_name: "Hỗ trợ QC kiểm tra chéo các ca đối soát hóa đơn lương phức tạp",
              status: "Not Started",
              start_date: "20/11/2026",
              due_date: "20/11/2026",
              est_effort_hour: 8,
              notes: "BA hỗ trợ kiểm tra chéo",
              task_complexity: 6,
              type_of_work: "Do",
              task_process: "Requirement & Design",
              task_priority: "Medium"
            },
            {
              pic: "PM",
              task_name: "Theo dõi QC Testing thực thi & điều phối lịch bàn giao CSOC Pentest – Tuần 7",
              status: "Not Started",
              start_date: "23/11/2026",
              due_date: "23/11/2026",
              est_effort_hour: 8,
              notes: "PM tracking tuần 7",
              task_complexity: 6,
              type_of_work: "Do",
              task_process: "Project Management",
              task_priority: "High"
            },
            {
              pic: "QC",
              task_name: "Thực thi kiểm thử chức năng & tính toán lương trên Staging và log bugs",
              status: "Not Started",
              start_date: "23/11/2026",
              due_date: "24/11/2026",
              est_effort_hour: 16,
              notes: "QC thực thi test chính thức",
              task_complexity: 6,
              type_of_work: "Do",
              task_process: "Testing",
              task_priority: "High"
            },
            {
              pic: "DEV",
              task_name: "Điều tra lỗi và khắc phục các bug phát sinh từ đợt kiểm thử của QC",
              status: "Not Started",
              start_date: "23/11/2026",
              due_date: "24/11/2026",
              est_effort_hour: 16,
              notes: "DEV fix bug QC đợt 1",
              task_complexity: 6,
              type_of_work: "Do",
              task_process: "Coding",
              task_priority: "High"
            },
            {
              pic: "BA",
              task_name: "Hỗ trợ làm rõ các ca tính lương phức tạp trong quá trình QC Testing",
              status: "Not Started",
              start_date: "23/11/2026",
              due_date: "24/11/2026",
              est_effort_hour: 16,
              notes: "BA hỗ trợ QC test",
              task_complexity: 6,
              type_of_work: "Do",
              task_process: "Requirement & Design",
              task_priority: "High"
            },
            {
              pic: "QC",
              task_name: "Phối hợp DEV fix bug QC round 1 và recheck toàn bộ các lỗi đã khắc phục",
              status: "Not Started",
              start_date: "25/11/2026",
              due_date: "25/11/2026",
              est_effort_hour: 8,
              notes: "QC recheck bug fix round 1",
              task_complexity: 6,
              type_of_work: "Do",
              task_process: "Testing",
              task_priority: "High"
            },
            {
              pic: "DEV",
              task_name: "Hoàn tất fix bug QC round 1 và deploy bản vá ổn định lên Staging",
              status: "Not Started",
              start_date: "25/11/2026",
              due_date: "25/11/2026",
              est_effort_hour: 8,
              notes: "DEV hoàn tất fix bug QC",
              task_complexity: 6,
              type_of_work: "Do",
              task_process: "Coding",
              task_priority: "High"
            },
            {
              pic: "BA",
              task_name: "Rà soát báo cáo lỗi từ QC và cập nhật ma trận yêu cầu nghiệm thu",
              status: "Not Started",
              start_date: "25/11/2026",
              due_date: "25/11/2026",
              est_effort_hour: 8,
              notes: "BA rà soát kết quả test",
              task_complexity: 6,
              type_of_work: "Do",
              task_process: "Requirement & Design",
              task_priority: "Medium"
            },
            {
              pic: "QC",
              task_name: "Thực hiện Regression Test toàn diện hệ thống & hoàn tất QC Sign-off",
              status: "Not Started",
              start_date: "26/11/2026",
              due_date: "26/11/2026",
              est_effort_hour: 8,
              notes: "QC Sign-off kết thúc đợt test 13-26/11",
              task_complexity: 6,
              type_of_work: "Do",
              task_process: "Testing",
              task_priority: "Critical"
            },
            {
              pic: "DEV",
              task_name: "Hỗ trợ QC Regression Test và đóng băng Staging build chuẩn bị cho CSOC",
              status: "Not Started",
              start_date: "26/11/2026",
              due_date: "26/11/2026",
              est_effort_hour: 8,
              notes: "Freeze build Staging sẵn sàng cho CSOC",
              task_complexity: 6,
              type_of_work: "Do",
              task_process: "Coding",
              task_priority: "High"
            },
            {
              pic: "DEV",
              task_name: "Thiết lập môi trường pentest riêng biệt và hỗ trợ CSOC Kick-off",
              status: "Not Started",
              start_date: "27/11/2026",
              due_date: "27/11/2026",
              est_effort_hour: 8,
              notes: "CSOC Pentest bắt đầu sau QC",
              task_complexity: 6,
              type_of_work: "Do",
              task_process: "Coding",
              task_priority: "High"
            },
            {
              pic: "QC",
              task_name: "Bàn giao Staging testbed và phân loại phạm vi kiểm thử bảo mật với CSOC",
              status: "Not Started",
              start_date: "27/11/2026",
              due_date: "27/11/2026",
              est_effort_hour: 8,
              notes: "QC bàn giao testbed cho CSOC",
              task_complexity: 6,
              type_of_work: "Do",
              task_process: "Testing",
              task_priority: "Medium"
            },
            {
              pic: "PM",
              task_name: "Điều phối CSOC Pentest, giám sát UAT & chuẩn bị Release Gate – Tuần 8",
              status: "Not Started",
              start_date: "30/11/2026",
              due_date: "30/11/2026",
              est_effort_hour: 8,
              notes: "PM tracking tuần 8 (cuối tháng 11)",
              task_complexity: 6,
              type_of_work: "Do",
              task_process: "Project Management",
              task_priority: "High"
            },
            {
              pic: "DEV",
              task_name: "Standby hỗ trợ kỹ thuật và rà soát hạ tầng trong đợt CSOC Pentest",
              status: "Not Started",
              start_date: "30/11/2026",
              due_date: "30/11/2026",
              est_effort_hour: 8,
              notes: "DEV hỗ trợ CSOC pentest (30/11)",
              task_complexity: 6,
              type_of_work: "Do",
              task_process: "Coding",
              task_priority: "High"
            },
            {
              pic: "BA",
              task_name: "Cập nhật tài liệu kỹ thuật phân hệ KTR và chuẩn bị phiên nghiệm thu UAT",
              status: "Not Started",
              start_date: "30/11/2026",
              due_date: "30/11/2026",
              est_effort_hour: 8,
              notes: "BA chuẩn bị phiên UAT (30/11)",
              task_complexity: 6,
              type_of_work: "Do",
              task_process: "Requirement & Design",
              task_priority: "Medium"
            },
            {
              pic: "DEV",
              task_name: "Khắc phục và fix các findings từ báo cáo CSOC Pentest đợt 1",
              status: "Not Started",
              start_date: "01/12/2026",
              due_date: "02/12/2026",
              est_effort_hour: 16,
              notes: "DEV fix findings pentest",
              task_complexity: 6,
              type_of_work: "Do",
              task_process: "Coding",
              task_priority: "High"
            },
            {
              pic: "BA",
              task_name: "Hướng dẫn người dùng các khối thực hiện UAT phân hệ KTR trên Staging",
              status: "Not Started",
              start_date: "01/12/2026",
              due_date: "02/12/2026",
              est_effort_hour: 16,
              notes: "BA hướng dẫn UAT",
              task_complexity: 6,
              type_of_work: "Do",
              task_process: "Requirement & Design",
              task_priority: "High"
            },
            {
              pic: "DEV",
              task_name: "Hoàn tất vá lỗi an toàn thông tin, hỗ trợ UAT và phối hợp CSOC re-test",
              status: "Not Started",
              start_date: "03/12/2026",
              due_date: "04/12/2026",
              est_effort_hour: 16,
              notes: "DEV hoàn tất fix pentest & UAT support",
              task_complexity: 6,
              type_of_work: "Do",
              task_process: "Coding",
              task_priority: "High"
            },
            {
              pic: "QC",
              task_name: "Recheck các lỗ hổng bảo mật sau khi DEV fix & xác nhận Security Sign-off",
              status: "Not Started",
              start_date: "03/12/2026",
              due_date: "04/12/2026",
              est_effort_hour: 16,
              notes: "Security Sign-off CSOC",
              task_complexity: 6,
              type_of_work: "Do",
              task_process: "Testing",
              task_priority: "Critical"
            },
            {
              pic: "BA",
              task_name: "Tổng hợp kết quả nghiệm thu người dùng và hoàn tất biên bản UAT Sign-off",
              status: "Not Started",
              start_date: "03/12/2026",
              due_date: "04/12/2026",
              est_effort_hour: 16,
              notes: "UAT Sign-off",
              task_complexity: 6,
              type_of_work: "Do",
              task_process: "Requirement & Design",
              task_priority: "Critical"
            },
            {
              pic: "DEV",
              task_name: "Triển khai Production Deploy vào Thứ 2 và theo dõi hệ thống ban đầu",
              status: "Not Started",
              start_date: "07/12/2026",
              due_date: "07/12/2026",
              est_effort_hour: 8,
              notes: "Deploy Production Thứ 2",
              task_complexity: 6,
              type_of_work: "Do",
              task_process: "Deployment",
              task_priority: "Critical"
            },
            {
              pic: "QC",
              task_name: "Thực hiện Smoke Test sau Deploy Production trên môi trường thật",
              status: "Not Started",
              start_date: "07/12/2026",
              due_date: "07/12/2026",
              est_effort_hour: 8,
              notes: "Smoke test sau deploy prod",
              task_complexity: 6,
              type_of_work: "Do",
              task_process: "Testing",
              task_priority: "Critical"
            },
            {
              pic: "PM",
              task_name: "Điều phối triển khai Go-live Production Thứ 2 và giám sát vận hành Pilot",
              status: "Not Started",
              start_date: "07/12/2026",
              due_date: "07/12/2026",
              est_effort_hour: 8,
              notes: "PM điều phối Go-live",
              task_complexity: 6,
              type_of_work: "Do",
              task_process: "Project Management",
              task_priority: "High"
            },
            {
              pic: "BA",
              task_name: "Thu thập phản hồi từ người dùng thực tế trong giai đoạn vận hành Pilot",
              status: "Not Started",
              start_date: "07/12/2026",
              due_date: "08/12/2026",
              est_effort_hour: 16,
              notes: "Pilot feedback đợt 1",
              task_complexity: 6,
              type_of_work: "Do",
              task_process: "Requirement & Design",
              task_priority: "High"
            },
            {
              pic: "DEV",
              task_name: "Monitor log/performance phân hệ KTR và hotfix trong giai đoạn Pilot",
              status: "Not Started",
              start_date: "08/12/2026",
              due_date: "09/12/2026",
              est_effort_hour: 16,
              notes: "Pilot monitor & hotfix standby",
              task_complexity: 6,
              type_of_work: "Do",
              task_process: "Coding",
              task_priority: "High"
            },
            {
              pic: "QC",
              task_name: "Theo dõi kiểm thử vận hành pilot và đối soát dữ liệu lương thực tế",
              status: "Not Started",
              start_date: "08/12/2026",
              due_date: "10/12/2026",
              est_effort_hour: 24,
              notes: "Pilot verification (3 ngày làm việc)",
              task_complexity: 6,
              type_of_work: "Do",
              task_process: "Testing",
              task_priority: "Medium"
            },
            {
              pic: "BA",
              task_name: "Phân tích dữ liệu phản hồi và hỗ trợ kế toán đối soát lương Pilot",
              status: "Not Started",
              start_date: "09/12/2026",
              due_date: "10/12/2026",
              est_effort_hour: 16,
              notes: "Đối soát lương Pilot",
              task_complexity: 6,
              type_of_work: "Do",
              task_process: "Requirement & Design",
              task_priority: "High"
            },
            {
              pic: "DEV",
              task_name: "Đóng gói tài liệu bàn giao kỹ thuật và hỗ trợ tổng kết vận hành Pilot",
              status: "Not Started",
              start_date: "10/12/2026",
              due_date: "11/12/2026",
              est_effort_hour: 16,
              notes: "Bàn giao kỹ thuật hệ thống",
              task_complexity: 6,
              type_of_work: "Do",
              task_process: "Coding",
              task_priority: "High"
            },
            {
              pic: "BA",
              task_name: "Tổng kết báo cáo đánh giá kết quả vận hành thử nghiệm Pilot",
              status: "Not Started",
              start_date: "11/12/2026",
              due_date: "11/12/2026",
              est_effort_hour: 8,
              notes: "Báo cáo tổng kết pilot",
              task_complexity: 6,
              type_of_work: "Do",
              task_process: "Requirement & Design",
              task_priority: "High"
            },
            {
              pic: "PM",
              task_name: "Tổ chức Sprint Review, Retrospective & Tổng kết vận hành Pilot",
              status: "Not Started",
              start_date: "11/12/2026",
              due_date: "11/12/2026",
              est_effort_hour: 8,
              notes: "Sprint Ceremonies & Close sprint",
              task_complexity: 6,
              type_of_work: "Do",
              task_process: "Project Management",
              task_priority: "High"
            }
          ]
        }
      ]
    }
  ]
};

// Write JSON to cache
const jsonPath = path.join(__dirname, 'outputs', '.tmp', 'sprint3_backlog.json');
fs.writeFileSync(jsonPath, JSON.stringify(backlogData, null, 2), 'utf-8');
console.log('Saved replanned JSON to', jsonPath);

// Generate Excel Files
async function generateExcelFiles() {
  const allTasks = [];
  backlogData.epics.forEach(epic => {
    epic.user_stories.forEach(us => {
      us.tasks.forEach(task => {
        allTasks.push({
          epic: epic.epic,
          us_id: us.us_id,
          us_desc: us.description,
          priority: us.priority,
          complexity: us.complexity,
          ...task
        });
      });
    });
  });

  // 1. Project Plan Excel
  const wbPlan = new ExcelJS.Workbook();
  const wsPlan = wbPlan.addWorksheet('Sprint 3');
  
  wsPlan.columns = [
    { header: 'No.', key: 'no', width: 6 },
    { header: 'Phase / Module', key: 'phase', width: 28 },
    { header: 'Task Name', key: 'task_name', width: 50 },
    { header: 'PIC', key: 'pic', width: 12 },
    { header: 'Process', key: 'process', width: 22 },
    { header: 'Start Date', key: 'start_date', width: 14 },
    { header: 'Due Date', key: 'due_date', width: 14 },
    { header: 'Effort (Hours)', key: 'effort_hour', width: 16 },
    { header: 'Effort (Manday)', key: 'effort_md', width: 16 },
    { header: 'Status', key: 'status', width: 14 },
    { header: 'Notes', key: 'notes', width: 35 }
  ];

  const headerRow = wsPlan.getRow(1);
  headerRow.font = { bold: true, color: { argb: 'FFFFFFFF' } };
  headerRow.fill = {
    type: 'pattern',
    pattern: 'solid',
    fgColor: { argb: 'FF1E40AF' }
  };
  headerRow.alignment = { vertical: 'middle', horizontal: 'center' };

  allTasks.forEach((t, idx) => {
    const row = wsPlan.addRow({
      no: idx + 1,
      phase: t.us_id + ' - ' + t.us_desc,
      task_name: t.task_name,
      pic: t.pic,
      process: t.task_process,
      start_date: t.start_date,
      due_date: t.due_date,
      effort_hour: t.est_effort_hour,
      effort_md: (t.est_effort_hour / 8.0).toFixed(2),
      status: t.status,
      notes: t.notes
    });

    row.alignment = { vertical: 'middle' };
    row.getCell('no').alignment = { horizontal: 'center' };
    row.getCell('pic').alignment = { horizontal: 'center' };
    row.getCell('start_date').alignment = { horizontal: 'center' };
    row.getCell('due_date').alignment = { horizontal: 'center' };
    row.getCell('effort_hour').alignment = { horizontal: 'right' };
    row.getCell('effort_md').alignment = { horizontal: 'right' };
    row.getCell('status').alignment = { horizontal: 'center' };
  });

  const totalHours = allTasks.reduce((sum, t) => sum + t.est_effort_hour, 0);
  const totalMD = (totalHours / 8.0).toFixed(2);
  const summaryRow = wsPlan.addRow({
    no: '',
    phase: 'TỔNG CỘNG EFFORT',
    task_name: `${allTasks.length} Tasks`,
    pic: '4 Roles',
    process: '',
    start_date: '13/10/2026',
    due_date: '11/12/2026',
    effort_hour: totalHours,
    effort_md: totalMD,
    status: 'In Planning',
    notes: 'Buffer 10% = ' + (totalHours * 0.1).toFixed(1) + 'h (' + (totalMD * 0.1).toFixed(2) + ' MD) -> Net = ' + (totalHours * 1.1).toFixed(1) + 'h (' + (totalMD * 1.1).toFixed(2) + ' MD)'
  });
  summaryRow.font = { bold: true };
  summaryRow.fill = {
    type: 'pattern',
    pattern: 'solid',
    fgColor: { argb: 'FFF1F5F9' }
  };

  const planPath = path.join(__dirname, 'outputs', 'sprint3_Project_Plan.xlsx');
  await wbPlan.xlsx.writeFile(planPath);
  console.log('Saved replanned Project Plan to', planPath);

  // 2. Sprint Backlog Excel
  const wbBacklog = new ExcelJS.Workbook();
  const wsBacklog = wbBacklog.addWorksheet('Sprint 3');

  wsBacklog.columns = [
    { header: 'US ID', key: 'us_id', width: 10 },
    { header: 'User Story / Feature', key: 'us_title', width: 36 },
    { header: 'Task Name', key: 'task_name', width: 48 },
    { header: 'Assignee (PIC)', key: 'pic', width: 14 },
    { header: 'Priority', key: 'priority', width: 12 },
    { header: 'Complexity', key: 'complexity', width: 14 },
    { header: 'Start Date', key: 'start_date', width: 14 },
    { header: 'Due Date', key: 'due_date', width: 14 },
    { header: 'Effort (Hours)', key: 'effort_hour', width: 16 },
    { header: 'Effort (MD)', key: 'effort_md', width: 14 },
    { header: 'Status', key: 'status', width: 14 },
    { header: 'Notes / Scope', key: 'notes', width: 36 }
  ];

  const bHeaderRow = wsBacklog.getRow(1);
  bHeaderRow.font = { bold: true, color: { argb: 'FFFFFFFF' } };
  bHeaderRow.fill = {
    type: 'pattern',
    pattern: 'solid',
    fgColor: { argb: 'FF0D9488' }
  };
  bHeaderRow.alignment = { vertical: 'middle', horizontal: 'center' };

  allTasks.forEach(t => {
    const row = wsBacklog.addRow({
      us_id: t.us_id,
      us_title: t.us_desc,
      task_name: t.task_name,
      pic: t.pic,
      priority: t.task_priority,
      complexity: t.task_complexity,
      start_date: t.start_date,
      due_date: t.due_date,
      effort_hour: t.est_effort_hour,
      effort_md: (t.est_effort_hour / 8.0).toFixed(2),
      status: t.status,
      notes: t.notes
    });

    row.alignment = { vertical: 'middle' };
    row.getCell('us_id').alignment = { horizontal: 'center' };
    row.getCell('pic').alignment = { horizontal: 'center' };
    row.getCell('priority').alignment = { horizontal: 'center' };
    row.getCell('complexity').alignment = { horizontal: 'center' };
    row.getCell('start_date').alignment = { horizontal: 'center' };
    row.getCell('due_date').alignment = { horizontal: 'center' };
    row.getCell('effort_hour').alignment = { horizontal: 'right' };
    row.getCell('effort_md').alignment = { horizontal: 'right' };
    row.getCell('status').alignment = { horizontal: 'center' };
  });

  const bSummaryRow = wsBacklog.addRow({
    us_id: 'TOTAL',
    us_title: 'TỔNG CỘNG BACKLOG',
    task_name: `${allTasks.length} Tasks`,
    pic: '4 Roles',
    priority: 'High',
    complexity: '-',
    start_date: '13/10/2026',
    due_date: '11/12/2026',
    effort_hour: totalHours,
    effort_md: totalMD,
    status: 'In Planning',
    notes: 'Buffer 10% = ' + (totalHours * 0.1).toFixed(1) + 'h -> Net = ' + (totalHours * 1.1).toFixed(1) + 'h'
  });
  bSummaryRow.font = { bold: true };
  bSummaryRow.fill = {
    type: 'pattern',
    pattern: 'solid',
    fgColor: { argb: 'FFF0FDFA' }
  };

  const backlogPath = path.join(__dirname, 'outputs', 'sprint3_Sprint_Backlog.xlsx');
  await wbBacklog.xlsx.writeFile(backlogPath);
  console.log('Saved replanned Sprint Backlog to', backlogPath);
}

generateExcelFiles().then(() => console.log('Replanning complete.'));

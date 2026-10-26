const fs = require('fs');
const path = require('path');
const ExcelJS = require('exceljs');

const backlogData = {
  project: "FTI-SAL v3.1 - Salary Management System (FTI Salary)",
  sprint_number: 3,
  sprint_goal: "Hoàn thiện số hóa tính lương nhóm dịch vụ Kênh thuê riêng (code đến 10/11), hoàn tất QC Testing Staging (17/11), thực hiện CSOC Pentest độc lập sau QC (18/11-20/11), nghiệm thu UAT, deploy production Thứ 4 (25/11) và vận hành pilot (25-27/11).",
  time_box: [
    "1. Sprint Timeline: From 13/10/2026 To 27/11/2026 (7 weeks / 34 working days)",
    "2. Daily Scrum: 15 min/ngay (9:00 AM)",
    "3. Dev Complete: 10/11/2026 (Staging Deploy)",
    "4. QC Testing Phase (Staging): 11/11/2026 - 17/11/2026 (QC Sign-off 17/11)",
    "5. CSOC Pentest Phase (Staging - After QC): 18/11/2026 - 20/11/2026",
    "6. Pentest Remediation & UAT Phase: 23/11/2026 - 24/11/2026 (Security & UAT Sign-off)",
    "7. Production Deploy: 25/11/2026 (Wed - T4 Rule)",
    "8. Pilot & Sprint Close: 25/11/2026 - 27/11/2026"
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
              task_name: "Demo và làm rõ nghiệp vụ CID cho đội ngũ QC",
              status: "Not Started",
              start_date: "19/10/2026",
              due_date: "19/10/2026",
              est_effort_hour: 8,
              notes: "Clear nghiệp vụ phân hệ CID",
              task_complexity: 6,
              type_of_work: "Do",
              task_process: "Requirement & Design",
              task_priority: "Medium"
            },
            {
              pic: "QC",
              task_name: "Nghiên cứu URD & Viết kịch bản kiểm thử giao diện nhập CID",
              status: "Not Started",
              start_date: "19/10/2026",
              due_date: "20/10/2026",
              est_effort_hour: 16,
              notes: "QC Onboarding testcases",
              task_complexity: 6,
              type_of_work: "Do",
              task_process: "Testing",
              task_priority: "High"
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
              pic: "QC",
              task_name: "Xây dựng kịch bản kiểm thử phân quyền và bảo mật dữ liệu CID",
              status: "Not Started",
              start_date: "21/10/2026",
              due_date: "22/10/2026",
              est_effort_hour: 16,
              notes: "Testcases phân quyền RBAC",
              task_complexity: 6,
              type_of_work: "Do",
              task_process: "Testing",
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
              pic: "QC",
              task_name: "Viết kịch bản kiểm thử tính năng Import Excel và đối soát CID",
              status: "Not Started",
              start_date: "26/10/2026",
              due_date: "27/10/2026",
              est_effort_hour: 16,
              notes: "Testcases import Excel CID",
              task_complexity: 6,
              type_of_work: "Do",
              task_process: "Testing",
              task_priority: "Medium"
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
              pic: "QC",
              task_name: "Review chéo Testcases và chuẩn bị dữ liệu kiểm thử mẫu CID",
              status: "Not Started",
              start_date: "28/10/2026",
              due_date: "28/10/2026",
              est_effort_hour: 8,
              notes: "Data mẫu cho staging test",
              task_complexity: 6,
              type_of_work: "Do",
              task_process: "Testing",
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
              pic: "QC",
              task_name: "Xây dựng kịch bản kiểm thử công thức và ma trận tính lương KTR",
              status: "Not Started",
              start_date: "02/11/2026",
              due_date: "03/11/2026",
              est_effort_hour: 16,
              notes: "Testcases công thức lương KTR",
              task_complexity: 6,
              type_of_work: "Do",
              task_process: "Testing",
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
              pic: "QC",
              task_name: "Chuẩn bị bộ dữ liệu mẫu tính lương thực tế phục vụ kiểm thử",
              status: "Not Started",
              start_date: "04/11/2026",
              due_date: "04/11/2026",
              est_effort_hour: 8,
              notes: "Data mẫu đối soát lương",
              task_complexity: 6,
              type_of_work: "Do",
              task_process: "Testing",
              task_priority: "Medium"
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
      epic: "EPIC-4: QC Testing, CSOC Pentest sau QC, Nghiệm thu UAT, Production Deploy & Pilot",
      user_stories: [
        {
          us_id: "US_3.4",
          module: "Testing, Release & Pilot",
          description: "QC testing CSOC pentest sau QC nghiệm thu UAT deploy và pilot",
          priority: "3-High",
          complexity: "3-High",
          tasks: [
            {
              pic: "BA",
              task_name: "Demo & Clear nghiệp vụ cho QC và hỗ trợ làm rõ ca tính lương phức tạp",
              status: "Not Started",
              start_date: "11/11/2026",
              due_date: "11/11/2026",
              est_effort_hour: 8,
              notes: "BA demo & clear nghiệp vụ trên Staging",
              task_complexity: 6,
              type_of_work: "Do",
              task_process: "Requirement & Design",
              task_priority: "High"
            },
            {
              pic: "QC",
              task_name: "Thực hiện QC Testing phân hệ nhập liệu và phân quyền CID trên Staging",
              status: "Not Started",
              start_date: "11/11/2026",
              due_date: "12/11/2026",
              est_effort_hour: 16,
              notes: "QC testing nhập liệu CID & phân quyền",
              task_complexity: 6,
              type_of_work: "Do",
              task_process: "Testing",
              task_priority: "High"
            },
            {
              pic: "DEV",
              task_name: "Hỗ trợ dữ liệu kiểm thử QC và tối ưu câu truy vấn bảng lương KTR",
              status: "Not Started",
              start_date: "11/11/2026",
              due_date: "12/11/2026",
              est_effort_hour: 16,
              notes: "DEV hỗ trợ QC đợt 1 trên Staging",
              task_complexity: 6,
              type_of_work: "Do",
              task_process: "Coding",
              task_priority: "High"
            },
            {
              pic: "BA",
              task_name: "Hỗ trợ QC kiểm tra chéo các ca biên đối soát hóa đơn KTR",
              status: "Not Started",
              start_date: "13/11/2026",
              due_date: "13/11/2026",
              est_effort_hour: 8,
              notes: "Hỗ trợ QC kiểm tra đối soát",
              task_complexity: 6,
              type_of_work: "Do",
              task_process: "Requirement & Design",
              task_priority: "Medium"
            },
            {
              pic: "QC",
              task_name: "Thực hiện QC Testing phân hệ Core tính lương KTR và xuất Excel",
              status: "Not Started",
              start_date: "13/11/2026",
              due_date: "13/11/2026",
              est_effort_hour: 8,
              notes: "QC testing Core lương & đối soát",
              task_complexity: 6,
              type_of_work: "Do",
              task_process: "Testing",
              task_priority: "High"
            },
            {
              pic: "DEV",
              task_name: "Hỗ trợ điều tra lỗi phát sinh từ QC Testing và tinh chỉnh hiệu năng",
              status: "Not Started",
              start_date: "13/11/2026",
              due_date: "13/11/2026",
              est_effort_hour: 8,
              notes: "DEV bug investigation & tuning",
              task_complexity: 6,
              type_of_work: "Do",
              task_process: "Coding",
              task_priority: "High"
            },
            {
              pic: "PM",
              task_name: "Đánh giá kết quả QC Testing và chuẩn bị bàn giao môi trường CSOC",
              status: "Not Started",
              start_date: "16/11/2026",
              due_date: "16/11/2026",
              est_effort_hour: 8,
              notes: "PM điều phối QC sign-off & CSOC handover",
              task_complexity: 6,
              type_of_work: "Do",
              task_process: "Project Management",
              task_priority: "High"
            },
            {
              pic: "DEV",
              task_name: "Khắc phục và fix các lỗi phát sinh từ đợt kiểm thử chức năng QC",
              status: "Not Started",
              start_date: "16/11/2026",
              due_date: "16/11/2026",
              est_effort_hour: 8,
              notes: "Fix bug QC đợt 1",
              task_complexity: 6,
              type_of_work: "Do",
              task_process: "Coding",
              task_priority: "High"
            },
            {
              pic: "QC",
              task_name: "Recheck lỗi sau fix của DEV và kiểm tra hồi quy đợt 1",
              status: "Not Started",
              start_date: "16/11/2026",
              due_date: "16/11/2026",
              est_effort_hour: 8,
              notes: "QC recheck sau fix",
              task_complexity: 6,
              type_of_work: "Do",
              task_process: "Testing",
              task_priority: "High"
            },
            {
              pic: "BA",
              task_name: "Hoàn thiện tài liệu User Guide hướng dẫn tính lương KTR cho người dùng",
              status: "Not Started",
              start_date: "16/11/2026",
              due_date: "17/11/2026",
              est_effort_hour: 16,
              notes: "User guide tài liệu tính lương",
              task_complexity: 6,
              type_of_work: "Do",
              task_process: "Requirement & Design",
              task_priority: "High"
            },
            {
              pic: "QC",
              task_name: "Thực hiện Regression Test toàn diện hệ thống & hoàn tất QC Sign-off",
              status: "Not Started",
              start_date: "17/11/2026",
              due_date: "17/11/2026",
              est_effort_hour: 8,
              notes: "QC Sign-off hoàn tất giai đoạn QC",
              task_complexity: 6,
              type_of_work: "Do",
              task_process: "Testing",
              task_priority: "High"
            },
            {
              pic: "DEV",
              task_name: "Hỗ trợ QC Regression Test và đóng gói Staging build chuẩn bị cho CSOC",
              status: "Not Started",
              start_date: "17/11/2026",
              due_date: "17/11/2026",
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
              start_date: "18/11/2026",
              due_date: "18/11/2026",
              est_effort_hour: 8,
              notes: "Bắt đầu CSOC Pentest sau khi QC xong",
              task_complexity: 6,
              type_of_work: "Do",
              task_process: "Coding",
              task_priority: "High"
            },
            {
              pic: "QC",
              task_name: "Bàn giao testbed dữ liệu sạch và tài liệu phân quyền cho CSOC",
              status: "Not Started",
              start_date: "18/11/2026",
              due_date: "18/11/2026",
              est_effort_hour: 8,
              notes: "Hỗ trợ CSOC chuẩn bị test",
              task_complexity: 6,
              type_of_work: "Do",
              task_process: "Testing",
              task_priority: "Medium"
            },
            {
              pic: "DEV",
              task_name: "Standby hỗ trợ kỹ thuật và rà soát hạ tầng trong đợt CSOC Pentest",
              status: "Not Started",
              start_date: "19/11/2026",
              due_date: "20/11/2026",
              est_effort_hour: 16,
              notes: "Hỗ trợ CSOC pentest thực thi",
              task_complexity: 6,
              type_of_work: "Do",
              task_process: "Coding",
              task_priority: "High"
            },
            {
              pic: "QC",
              task_name: "Phối hợp CSOC phân loại phạm vi kiểm thử an toàn thông tin",
              status: "Not Started",
              start_date: "19/11/2026",
              due_date: "20/11/2026",
              est_effort_hour: 16,
              notes: "Phối hợp cùng CSOC pentest",
              task_complexity: 6,
              type_of_work: "Do",
              task_process: "Testing",
              task_priority: "High"
            },
            {
              pic: "BA",
              task_name: "Chuẩn bị bộ dữ liệu mẫu nghiệm thu UAT với đại diện các khối",
              status: "Not Started",
              start_date: "19/11/2026",
              due_date: "20/11/2026",
              est_effort_hour: 16,
              notes: "Chuẩn bị dữ liệu UAT",
              task_complexity: 6,
              type_of_work: "Do",
              task_process: "Requirement & Design",
              task_priority: "High"
            },
            {
              pic: "PM",
              task_name: "Điều phối khắc phục Pentest, hoàn tất UAT & chuẩn bị Release Gate",
              status: "Not Started",
              start_date: "23/11/2026",
              due_date: "23/11/2026",
              est_effort_hour: 8,
              notes: "PM điều phối tuần Go-live",
              task_complexity: 6,
              type_of_work: "Do",
              task_process: "Project Management",
              task_priority: "High"
            },
            {
              pic: "DEV",
              task_name: "Khắc phục và fix các findings từ báo cáo CSOC Pentest",
              status: "Not Started",
              start_date: "23/11/2026",
              due_date: "23/11/2026",
              est_effort_hour: 8,
              notes: "Fix findings CSOC",
              task_complexity: 6,
              type_of_work: "Do",
              task_process: "Coding",
              task_priority: "High"
            },
            {
              pic: "QC",
              task_name: "Phối hợp phân loại findings CSOC và recheck sau khi DEV fix",
              status: "Not Started",
              start_date: "23/11/2026",
              due_date: "23/11/2026",
              est_effort_hour: 8,
              notes: "Recheck pentest fix",
              task_complexity: 6,
              type_of_work: "Do",
              task_process: "Testing",
              task_priority: "High"
            },
            {
              pic: "BA",
              task_name: "Hướng dẫn người dùng thực hiện UAT và lấy UAT Sign-off",
              status: "Not Started",
              start_date: "23/11/2026",
              due_date: "24/11/2026",
              est_effort_hour: 16,
              notes: "UAT execution & Sign-off",
              task_complexity: 6,
              type_of_work: "Do",
              task_process: "Requirement & Design",
              task_priority: "High"
            },
            {
              pic: "DEV",
              task_name: "Hoàn tất vá lỗi an toàn thông tin, hỗ trợ UAT và phối hợp CSOC re-test",
              status: "Not Started",
              start_date: "24/11/2026",
              due_date: "24/11/2026",
              est_effort_hour: 8,
              notes: "Hoàn tất fix pentest & hỗ trợ UAT",
              task_complexity: 6,
              type_of_work: "Do",
              task_process: "Coding",
              task_priority: "High"
            },
            {
              pic: "QC",
              task_name: "Recheck toàn diện các lỗ hổng pentest & xác nhận Security Sign-off",
              status: "Not Started",
              start_date: "24/11/2026",
              due_date: "24/11/2026",
              est_effort_hour: 8,
              notes: "Security sign-off CSOC",
              task_complexity: 6,
              type_of_work: "Do",
              task_process: "Testing",
              task_priority: "Critical"
            },
            {
              pic: "DEV",
              task_name: "Triển khai Production Deploy vào Thứ 4 và theo dõi hệ thống",
              status: "Not Started",
              start_date: "25/11/2026",
              due_date: "25/11/2026",
              est_effort_hour: 8,
              notes: "Deploy Production Thứ 4",
              task_complexity: 6,
              type_of_work: "Do",
              task_process: "Deployment",
              task_priority: "Critical"
            },
            {
              pic: "QC",
              task_name: "Thực hiện Smoke Test sau Deploy Production trên môi trường thật",
              status: "Not Started",
              start_date: "25/11/2026",
              due_date: "25/11/2026",
              est_effort_hour: 8,
              notes: "Smoke test sau deploy prod",
              task_complexity: 6,
              type_of_work: "Do",
              task_process: "Testing",
              task_priority: "Critical"
            },
            {
              pic: "PM",
              task_name: "Điều phối triển khai Go-live Production Thứ 4 và giám sát Pilot",
              status: "Not Started",
              start_date: "25/11/2026",
              due_date: "25/11/2026",
              est_effort_hour: 8,
              notes: "PM điều phối Go-live",
              task_complexity: 6,
              type_of_work: "Do",
              task_process: "Project Management",
              task_priority: "High"
            },
            {
              pic: "DEV",
              task_name: "Monitor log/performance phân hệ KTR và hỗ trợ vận hành Pilot",
              status: "Not Started",
              start_date: "26/11/2026",
              due_date: "27/11/2026",
              est_effort_hour: 16,
              notes: "Pilot monitor & hotfix standby",
              task_complexity: 6,
              type_of_work: "Do",
              task_process: "Coding",
              task_priority: "High"
            },
            {
              pic: "QC",
              task_name: "Theo dõi kiểm thử vận hành pilot và kiểm tra tính nhất quán số liệu",
              status: "Not Started",
              start_date: "26/11/2026",
              due_date: "27/11/2026",
              est_effort_hour: 16,
              notes: "Pilot verification",
              task_complexity: 6,
              type_of_work: "Do",
              task_process: "Testing",
              task_priority: "Medium"
            },
            {
              pic: "BA",
              task_name: "Thu thập phản hồi từ người dùng thực tế trong giai đoạn vận hành Pilot",
              status: "Not Started",
              start_date: "25/11/2026",
              due_date: "26/11/2026",
              est_effort_hour: 16,
              notes: "Pilot feedback collection",
              task_complexity: 6,
              type_of_work: "Do",
              task_process: "Requirement & Design",
              task_priority: "High"
            },
            {
              pic: "BA",
              task_name: "Tổng kết báo cáo đánh giá kết quả vận hành thử nghiệm Pilot",
              status: "Not Started",
              start_date: "27/11/2026",
              due_date: "27/11/2026",
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
              start_date: "27/11/2026",
              due_date: "27/11/2026",
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
console.log('Saved JSON to', jsonPath);

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
  
  // Headers
  wsPlan.columns = [
    { header: 'No.', key: 'no', width: 6 },
    { header: 'Phase / Module', key: 'phase', width: 28 },
    { header: 'Task Name', key: 'task_name', width: 48 },
    { header: 'PIC', key: 'pic', width: 12 },
    { header: 'Process', key: 'process', width: 22 },
    { header: 'Start Date', key: 'start_date', width: 14 },
    { header: 'Due Date', key: 'due_date', width: 14 },
    { header: 'Effort (Hours)', key: 'effort_hour', width: 16 },
    { header: 'Effort (Manday)', key: 'effort_md', width: 16 },
    { header: 'Status', key: 'status', width: 14 },
    { header: 'Notes', key: 'notes', width: 35 }
  ];

  // Styling header row
  const headerRow = wsPlan.getRow(1);
  headerRow.font = { bold: true, color: { argb: 'FFFFFFFF' } };
  headerRow.fill = {
    type: 'pattern',
    pattern: 'solid',
    fgColor: { argb: 'FF1E40AF' } // Deep Blue
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

  // Total summary row
  const totalHours = allTasks.reduce((sum, t) => sum + t.est_effort_hour, 0);
  const totalMD = (totalHours / 8.0).toFixed(2);
  const summaryRow = wsPlan.addRow({
    no: '',
    phase: 'TỔNG CỘNG EFFORT',
    task_name: `${allTasks.length} Tasks`,
    pic: '',
    process: '',
    start_date: '13/10/2026',
    due_date: '27/11/2026',
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
  console.log('Saved Project Plan to', planPath);

  // 2. Sprint Backlog Excel
  const wbBacklog = new ExcelJS.Workbook();
  const wsBacklog = wbBacklog.addWorksheet('Sprint 3');

  wsBacklog.columns = [
    { header: 'US ID', key: 'us_id', width: 10 },
    { header: 'User Story / Feature', key: 'us_title', width: 36 },
    { header: 'Task Name', key: 'task_name', width: 46 },
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
    fgColor: { argb: 'FF0D9488' } // Teal / Emerald
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
    due_date: '27/11/2026',
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
  console.log('Saved Sprint Backlog to', backlogPath);
}

generateExcelFiles().then(() => console.log('Excel generation complete.'));

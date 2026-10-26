#!/usr/bin/env python3
"""Build sprint3_backlog.json for FTI-SAL v3.1 Sprint 3, validate it, and export Excel files."""
import json
import os
from datetime import datetime

data = {
  "project": "FTI-SAL v3.1",
  "sprint_number": 3,
  "sprint_goal": "Hoàn thiện cụm tính năng Import lương Kênh khối ngoại, HĐ Tân Thuận theo vai trò TĐV/TPP và Nhân viên KD; tự động xác định loại doanh thu theo Circuit ID, tính lương sản phẩm, hoàn tất QC testing, CSOC pentest, UAT và pilot.",
  "time_box": [
    "1. Sprint Timeline: 13/10/2026 - 11/12/2026 (9 tuần, 44 ngày làm việc)",
    "2. Sprint Planning: 13/10/2026",
    "3. Daily Scrum: 09:00 - 09:15 hằng ngày làm việc",
    "4. Dev Complete & Staging Deploy: 12/11/2026",
    "5. QC test/testing: 13/11/2026 - 26/11/2026 (QC join 13/11, end 26/11)",
    "6. UAT & CSOC pentest: 27/11/2026 - 04/12/2026",
    "7. Production Release: 07/12/2026 (Thứ Hai)",
    "8. Pilot: 07/12/2026 - 11/12/2026 (5 ngày làm việc)",
    "9. Sprint Review & Retrospective: 11/12/2026"
  ],
  "epics": [
    {
      "epic": "EPIC-1. Phân quyền Menu & Khai báo CID khối ngoại (FR01, FR02)",
      "user_stories": [
        {
          "us_id": "US_1.1",
          "module": "Menu & Khai báo CID khối ngoại",
          "description": "Tách menu theo vai trò và khai báo CID khối ngoại",
          "priority": "3-High",
          "complexity": "2-Medium",
          "tasks": [
            {
              "pic": "PM",
              "task_name": "Kick-off & Lập kế hoạch Sprint 3",
              "status": "Not Started",
              "start_date": "13/10/2026",
              "due_date": "13/10/2026",
              "est_effort_hour": 4,
              "notes": "Họp kick-off dự án FTI-SAL v3.1 Sprint 3, thống nhất scope FR01-FR05 và Risk Register",
              "task_complexity": 6,
              "type_of_work": "Do",
              "task_process": "Project Management",
              "task_priority": "High"
            },
            {
              "pic": "BA",
              "task_name": "Phân tích yêu cầu tách menu vai trò và khai báo CID khối ngoại",
              "status": "Not Started",
              "start_date": "13/10/2026",
              "due_date": "14/10/2026",
              "est_effort_hour": 16,
              "notes": "Làm rõ luồng TĐV/TPP khai báo CID quản lý tay và Nhân viên KD import lương theo hóa đơn + CID",
              "task_complexity": 7,
              "type_of_work": "Do",
              "task_process": "Requirement & Design",
              "task_priority": "High"
            },
            {
              "pic": "DEV1",
              "task_name": "Setup môi trường & Review kiến trúc phân hệ Import lương FTI-SAL",
              "status": "Not Started",
              "start_date": "13/10/2026",
              "due_date": "14/10/2026",
              "est_effort_hour": 16,
              "notes": "Khảo sát source code hiện tại của màn hình Import lương Kênh khối ngoại, HĐ Tân Thuận",
              "task_complexity": 7,
              "type_of_work": "Do",
              "task_process": "Coding",
              "task_priority": "High"
            },
            {
              "pic": "PM",
              "task_name": "Theo dõi tiến độ & Quản trị rủi ro - Tuần 1",
              "status": "Not Started",
              "start_date": "14/10/2026",
              "due_date": "16/10/2026",
              "est_effort_hour": 4,
              "notes": "Theo dõi tiến độ hoàn thiện URD và chốt các giả định nghiệp vụ tuần 1",
              "task_complexity": 6,
              "type_of_work": "Do",
              "task_process": "Project Management",
              "task_priority": "Medium"
            },
            {
              "pic": "BA",
              "task_name": "Thiết kế Wireframe & Viết URD cụm tính năng CID khối ngoại, Tân Thuận",
              "status": "Not Started",
              "start_date": "15/10/2026",
              "due_date": "16/10/2026",
              "est_effort_hour": 16,
              "notes": "Output: URD đầy đủ cho FR01-FR05, ký duyệt URD Sign-off vào 16/10/2026",
              "task_complexity": 7,
              "type_of_work": "Do",
              "task_process": "Requirement & Design",
              "task_priority": "Critical"
            },
            {
              "pic": "DEV1",
              "task_name": "Technical design & Thiết kế DB bảng CID khối ngoại, lương KNg/TT",
              "status": "Not Started",
              "start_date": "15/10/2026",
              "due_date": "16/10/2026",
              "est_effort_hour": 16,
              "notes": "Thiết kế schema lưu Đối tác, Circuit ID, Ngày nghiệm thu CID, Phân loại doanh thu và index tra cứu",
              "task_complexity": 7,
              "type_of_work": "Do",
              "task_process": "Coding",
              "task_priority": "High"
            },
            {
              "pic": "PM",
              "task_name": "Theo dõi tiến độ & Quản trị rủi ro - Tuần 2",
              "status": "Not Started",
              "start_date": "19/10/2026",
              "due_date": "21/10/2026",
              "est_effort_hour": 8,
              "notes": "Giám sát tiến độ phát triển FR01 và FR02 trong tuần 2",
              "task_complexity": 6,
              "type_of_work": "Do",
              "task_process": "Project Management",
              "task_priority": "Medium"
            },
            {
              "pic": "BA",
              "task_name": "Chi tiết hóa Acceptance Criteria cho FR01 Menu và FR02 Khai báo CID",
              "status": "Not Started",
              "start_date": "19/10/2026",
              "due_date": "20/10/2026",
              "est_effort_hour": 16,
              "notes": "Quy định chi tiết quyền truy cập menu theo role TĐV/TPP và định dạng file import CID",
              "task_complexity": 7,
              "type_of_work": "Do",
              "task_process": "Requirement & Design",
              "task_priority": "High"
            },
            {
              "pic": "DEV1",
              "task_name": "Cập nhật phân quyền menu riêng cho TĐV/TPP và Nhân viên KD (FR01)",
              "status": "Not Started",
              "start_date": "19/10/2026",
              "due_date": "19/10/2026",
              "est_effort_hour": 8,
              "notes": "Thêm menu Import lương > Khai báo CID khối ngoại cho TĐV/TPP; giữ menu cũ cho Nhân viên KD",
              "task_complexity": 6,
              "type_of_work": "Do",
              "task_process": "Coding",
              "task_priority": "High"
            },
            {
              "pic": "DEV1",
              "task_name": "Xây dựng API và màn hình danh sách, bộ lọc, xóa CID khối ngoại (FR02)",
              "status": "Not Started",
              "start_date": "20/10/2026",
              "due_date": "21/10/2026",
              "est_effort_hour": 16,
              "notes": "Quản lý thông tin Đối tác, Circuit ID, Ngày nghiệm thu CID, Phân loại doanh thu cho TĐV/TPP",
              "task_complexity": 7,
              "type_of_work": "Do",
              "task_process": "Coding",
              "task_priority": "High"
            },
            {
              "pic": "DEV1",
              "task_name": "Phát triển chức năng Import và Xuất Excel khai báo CID khối ngoại (FR02)",
              "status": "Not Started",
              "start_date": "22/10/2026",
              "due_date": "22/10/2026",
              "est_effort_hour": 8,
              "notes": "Kiểm tra trùng lặp Circuit ID, định dạng ngày nghiệm thu và xuất danh sách ra Excel",
              "task_complexity": 7,
              "type_of_work": "Do",
              "task_process": "Coding",
              "task_priority": "High"
            },
            {
              "pic": "DEV1",
              "task_name": "Viết Unit Test cho luồng phân quyền menu và khai báo CID khối ngoại",
              "status": "Not Started",
              "start_date": "23/10/2026",
              "due_date": "23/10/2026",
              "est_effort_hour": 8,
              "notes": "Đảm bảo pass 100% unit test cho các API thuộc FR01 và FR02",
              "task_complexity": 6,
              "type_of_work": "Do",
              "task_process": "Coding",
              "task_priority": "Medium"
            },
            {
              "pic": "QC1",
              "task_name": "QC - Nghiệp vụ: Đọc URD và nắm luồng Khai báo CID khối ngoại, Tân Thuận",
              "status": "Not Started",
              "start_date": "13/11/2026",
              "due_date": "13/11/2026",
              "est_effort_hour": 8,
              "notes": "QC bắt đầu tham gia sprint ngày 13/11: nghiên cứu URD FR01-FR05 và chuẩn bị kế hoạch test",
              "task_complexity": 6,
              "type_of_work": "Study",
              "task_process": "Testing",
              "task_priority": "High"
            },
            {
              "pic": "QC1",
              "task_name": "QC - Nghiệp vụ: Thiết kế testcase phân quyền menu và khai báo CID (FR01, FR02)",
              "status": "Not Started",
              "start_date": "16/11/2026",
              "due_date": "17/11/2026",
              "est_effort_hour": 16,
              "notes": "Bao phủ các case phân quyền TĐV/TPP, Nhân viên KD và import/xuất/xóa CID khối ngoại",
              "task_complexity": 7,
              "type_of_work": "Do",
              "task_process": "Testing",
              "task_priority": "High"
            },
            {
              "pic": "QC1",
              "task_name": "QC - testing: Thực hiện test phân quyền menu và khai báo CID trên Staging",
              "status": "Not Started",
              "start_date": "20/11/2026",
              "due_date": "20/11/2026",
              "est_effort_hour": 8,
              "notes": "Thực thi bộ testcase FR01, FR02 trên môi trường Staging và log bug lên Jira",
              "task_complexity": 6,
              "type_of_work": "Do",
              "task_process": "Testing",
              "task_priority": "High"
            }
          ]
        }
      ]
    },
    {
      "epic": "EPIC-2. Import lương Kênh khối ngoại, HĐ Tân Thuận & Tự động xác định theo CID (FR03, FR04)",
      "user_stories": [
        {
          "us_id": "US_2.1",
          "module": "Import lương KNg/TT & Map CID",
          "description": "Import lương kênh khối ngoại, Tân Thuận và tự động map CID",
          "priority": "3-High",
          "complexity": "3-High",
          "tasks": [
            {
              "pic": "PM",
              "task_name": "Theo dõi tiến độ & Quản trị rủi ro - Tuần 3",
              "status": "Not Started",
              "start_date": "26/10/2026",
              "due_date": "28/10/2026",
              "est_effort_hour": 8,
              "notes": "Theo dõi tiến độ phát triển chức năng Import lương Kênh khối ngoại, HĐ Tân Thuận (FR03)",
              "task_complexity": 6,
              "type_of_work": "Do",
              "task_process": "Project Management",
              "task_priority": "Medium"
            },
            {
              "pic": "BA",
              "task_name": "Đặc tả template import mới và rule kiểm tra hóa đơn U, M, TTTT (FR03)",
              "status": "Not Started",
              "start_date": "26/10/2026",
              "due_date": "27/10/2026",
              "est_effort_hour": 16,
              "notes": "Quy định cấu trúc template mới, kiểm tra Circuit ID, mẫu số HĐơn/HĐ, 1 hóa đơn - 1 dịch vụ",
              "task_complexity": 7,
              "type_of_work": "Do",
              "task_process": "Requirement & Design",
              "task_priority": "High"
            },
            {
              "pic": "DEV1",
              "task_name": "Cập nhật màn hình, bộ lọc Circuit ID, cột Phân loại DT và Loại dịch vụ (FR03)",
              "status": "Not Started",
              "start_date": "26/10/2026",
              "due_date": "27/10/2026",
              "est_effort_hour": 16,
              "notes": "Bổ sung bộ lọc và cột hiển thị Circuit ID, Phân loại doanh thu, Loại dịch vụ cho Nhân viên KD",
              "task_complexity": 7,
              "type_of_work": "Do",
              "task_process": "Coding",
              "task_priority": "High"
            },
            {
              "pic": "DEV1",
              "task_name": "Xây dựng API import, validate template mới và chặn file lỗi HĐơn/CID (FR03)",
              "status": "Not Started",
              "start_date": "28/10/2026",
              "due_date": "29/10/2026",
              "est_effort_hour": 16,
              "notes": "Kiểm tra hóa đơn U, M, TTTT gắn với Circuit ID đã khai báo; file có lỗi phải chặn import toàn bộ",
              "task_complexity": 8,
              "type_of_work": "Do",
              "task_process": "Coding",
              "task_priority": "High"
            },
            {
              "pic": "DEV1",
              "task_name": "Phát triển chức năng Xuất Excel, xóa dữ liệu lương KNg/TT và Unit Test (FR03)",
              "status": "Not Started",
              "start_date": "30/10/2026",
              "due_date": "30/10/2026",
              "est_effort_hour": 8,
              "notes": "Hoàn tất chức năng xuất file Excel, xóa dữ liệu lương theo kỳ và unit test FR03",
              "task_complexity": 6,
              "type_of_work": "Do",
              "task_process": "Coding",
              "task_priority": "High"
            },
            {
              "pic": "PM",
              "task_name": "Theo dõi tiến độ & Quản trị rủi ro - Tuần 4",
              "status": "Not Started",
              "start_date": "02/11/2026",
              "due_date": "04/11/2026",
              "est_effort_hour": 8,
              "notes": "Theo dõi tiến độ phát triển engine tự động xác định theo CID (FR04)",
              "task_complexity": 6,
              "type_of_work": "Do",
              "task_process": "Project Management",
              "task_priority": "Medium"
            },
            {
              "pic": "BA",
              "task_name": "Đặc tả quy tắc tự động xác định Loại doanh thu và ngày nghiệm thu theo CID (FR04)",
              "status": "Not Started",
              "start_date": "02/11/2026",
              "due_date": "03/11/2026",
              "est_effort_hour": 16,
              "notes": "Chi tiết hóa công thức tính Ký mới / Gia hạn dựa trên Ngày nghiệm thu CID thay cho FTI-CM",
              "task_complexity": 7,
              "type_of_work": "Do",
              "task_process": "Requirement & Design",
              "task_priority": "High"
            },
            {
              "pic": "DEV1",
              "task_name": "Xây dựng engine tự động tính Loại doanh thu Ký mới/Gia hạn theo CID (FR04)",
              "status": "Not Started",
              "start_date": "02/11/2026",
              "due_date": "03/11/2026",
              "est_effort_hour": 16,
              "notes": "Xử lý logic tự tính Loại doanh thu cho các CID quản lý tay chưa có trên FTI-CM",
              "task_complexity": 8,
              "type_of_work": "Do",
              "task_process": "Coding",
              "task_priority": "High"
            },
            {
              "pic": "DEV1",
              "task_name": "Tự động map Phân loại doanh thu và Ngày nghiệm thu từ CID khai báo (FR04)",
              "status": "Not Started",
              "start_date": "04/11/2026",
              "due_date": "04/11/2026",
              "est_effort_hour": 8,
              "notes": "Ánh xạ tự động thông tin CID do TĐV/TPP khai báo vào bản ghi lương import của Nhân viên KD",
              "task_complexity": 7,
              "type_of_work": "Do",
              "task_process": "Coding",
              "task_priority": "High"
            },
            {
              "pic": "DEV1",
              "task_name": "Tích hợp luồng import hóa đơn U, M, TTTT với bộ map CID và viết Unit Test",
              "status": "Not Started",
              "start_date": "05/11/2026",
              "due_date": "06/11/2026",
              "est_effort_hour": 16,
              "notes": "Kiểm tra tích hợp xuyên suốt từ bước khai báo CID đến bước import hóa đơn và tự động map",
              "task_complexity": 7,
              "type_of_work": "Do",
              "task_process": "Coding",
              "task_priority": "High"
            },
            {
              "pic": "QC1",
              "task_name": "QC - Nghiệp vụ: Thiết kế testcase Import lương KNg/TT và tự động map CID",
              "status": "Not Started",
              "start_date": "18/11/2026",
              "due_date": "19/11/2026",
              "est_effort_hour": 16,
              "notes": "Viết testcase cho FR03, FR04, FR05: kiểm tra template mới, chặn file lỗi và tự động tính Ký mới/Gia hạn",
              "task_complexity": 7,
              "type_of_work": "Do",
              "task_process": "Testing",
              "task_priority": "High"
            },
            {
              "pic": "DEV1",
              "task_name": "Fix bug QC đợt 1 cho luồng khai báo CID và validate file import hóa đơn",
              "status": "Not Started",
              "start_date": "18/11/2026",
              "due_date": "20/11/2026",
              "est_effort_hour": 24,
              "notes": "Xử lý triệt để các bug phát sinh đợt 1 ở màn hình Khai báo CID và Import lương KNg/TT",
              "task_complexity": 7,
              "type_of_work": "Fix/Rework",
              "task_process": "Coding",
              "task_priority": "High"
            },
            {
              "pic": "QC1",
              "task_name": "QC - testing: Thực hiện test Import lương KNg/TT và tự động xác định theo CID",
              "status": "Not Started",
              "start_date": "23/11/2026",
              "due_date": "23/11/2026",
              "est_effort_hour": 8,
              "notes": "Test các kịch bản hóa đơn U, M, TTTT, kiểm tra 1 hóa đơn - 1 dịch vụ và map CID",
              "task_complexity": 7,
              "type_of_work": "Do",
              "task_process": "Testing",
              "task_priority": "High"
            }
          ]
        }
      ]
    },
    {
      "epic": "EPIC-3. Tính lương SP, Bảng lương nhân viên & Chi tiết lương dịch vụ (FR05)",
      "user_stories": [
        {
          "us_id": "US_3.1",
          "module": "Bảng lương & Chi tiết lương dịch vụ",
          "description": "Tính lương sản phẩm từ CID và khóa kỳ lương đã gửi",
          "priority": "3-High",
          "complexity": "3-High",
          "tasks": [
            {
              "pic": "PM",
              "task_name": "Theo dõi tiến độ & Điều phối Staging Deploy - Tuần 5",
              "status": "Not Started",
              "start_date": "09/11/2026",
              "due_date": "11/11/2026",
              "est_effort_hour": 8,
              "notes": "Rà soát điều kiện Dev Complete và điều phối deploy môi trường Staging trước khi QC join",
              "task_complexity": 6,
              "type_of_work": "Do",
              "task_process": "Project Management",
              "task_priority": "High"
            },
            {
              "pic": "BA",
              "task_name": "Viết kịch bản UAT Scenario cho luồng CID khối ngoại, Tân Thuận và Bảng lương",
              "status": "Not Started",
              "start_date": "09/11/2026",
              "due_date": "10/11/2026",
              "est_effort_hour": 16,
              "notes": "Xây dựng bộ kịch bản nghiệm thu UAT cho TĐV/TPP, Nhân viên KD, BOD và HR",
              "task_complexity": 7,
              "type_of_work": "Do",
              "task_process": "Requirement & Design",
              "task_priority": "High"
            },
            {
              "pic": "DEV1",
              "task_name": "Cập nhật tính lương SP cộng vào nhóm KTR, KTR khối ngoại, Server, HIGIO Cloud (FR05)",
              "status": "Not Started",
              "start_date": "09/11/2026",
              "due_date": "10/11/2026",
              "est_effort_hour": 16,
              "notes": "Tổng hợp dữ liệu sau map CID để tính lương sản phẩm và cộng vào đúng nhóm dịch vụ trên Bảng lương",
              "task_complexity": 8,
              "type_of_work": "Do",
              "task_process": "Coding",
              "task_priority": "High"
            },
            {
              "pic": "DEV1",
              "task_name": "Hiển thị dòng nguồn Import KNg/TT và khóa import/xóa khi bảng lương đã gửi (FR05)",
              "status": "Not Started",
              "start_date": "11/11/2026",
              "due_date": "11/11/2026",
              "est_effort_hour": 8,
              "notes": "Thêm dòng nguồn Import KNg/TT ở Chi tiết lương dịch vụ; chặn import/xóa nếu kỳ lương đã gửi",
              "task_complexity": 7,
              "type_of_work": "Do",
              "task_process": "Coding",
              "task_priority": "High"
            },
            {
              "pic": "DEV1",
              "task_name": "Unit Test tích hợp toàn luồng & Deploy bản build lên Staging",
              "status": "Not Started",
              "start_date": "12/11/2026",
              "due_date": "12/11/2026",
              "est_effort_hour": 8,
              "notes": "Hoàn tất Dev Complete (12/11) và triển khai bản build ổn định lên Staging trước ngày QC join (13/11)",
              "task_complexity": 7,
              "type_of_work": "Do",
              "task_process": "Deployment",
              "task_priority": "Critical"
            },
            {
              "pic": "BA",
              "task_name": "Demo & Clear nghiệp vụ cho QC trên môi trường Staging",
              "status": "Not Started",
              "start_date": "13/11/2026",
              "due_date": "13/11/2026",
              "est_effort_hour": 8,
              "notes": "Demo trực tiếp luồng FR01-FR05 trên Staging và giải đáp thắc mắc cho QC ngày đầu onboarding",
              "task_complexity": 6,
              "type_of_work": "Do",
              "task_process": "Requirement & Design",
              "task_priority": "High"
            },
            {
              "pic": "DEV1",
              "task_name": "Chuẩn bị dữ liệu testbed hóa đơn U, M, TTTT và hỗ trợ QC onboarding",
              "status": "Not Started",
              "start_date": "13/11/2026",
              "due_date": "13/11/2026",
              "est_effort_hour": 8,
              "notes": "Khởi tạo bộ dữ liệu mẫu Circuit ID, hóa đơn U, M, TTTT trên Staging phục vụ QC testing",
              "task_complexity": 6,
              "type_of_work": "Do",
              "task_process": "Coding",
              "task_priority": "High"
            },
            {
              "pic": "PM",
              "task_name": "Theo dõi tiến độ QC testing & Quản trị rủi ro - Tuần 6",
              "status": "Not Started",
              "start_date": "16/11/2026",
              "due_date": "18/11/2026",
              "est_effort_hour": 8,
              "notes": "Theo dõi tiến độ thiết kế testcase và thực hiện testing của QC trong tuần 6",
              "task_complexity": 6,
              "type_of_work": "Do",
              "task_process": "Project Management",
              "task_priority": "Medium"
            },
            {
              "pic": "BA",
              "task_name": "Viết tài liệu User Guide cho TĐV/TPP và Nhân viên KD",
              "status": "Not Started",
              "start_date": "16/11/2026",
              "due_date": "17/11/2026",
              "est_effort_hour": 16,
              "notes": "Soạn thảo tài liệu hướng dẫn sử dụng màn hình Khai báo CID khối ngoại và Import lương KNg/TT",
              "task_complexity": 6,
              "type_of_work": "Do",
              "task_process": "Requirement & Design",
              "task_priority": "Medium"
            },
            {
              "pic": "DEV1",
              "task_name": "Rà soát code & Tối ưu hiệu năng truy vấn tổng hợp bảng lương SP",
              "status": "Not Started",
              "start_date": "16/11/2026",
              "due_date": "17/11/2026",
              "est_effort_hour": 16,
              "notes": "Tối ưu tốc độ xử lý batch import hóa đơn và truy vấn cộng lương SP các nhóm dịch vụ",
              "task_complexity": 7,
              "type_of_work": "Review",
              "task_process": "Coding",
              "task_priority": "Medium"
            },
            {
              "pic": "BA",
              "task_name": "Hỗ trợ QC testing & Clarify các ca biên validate hóa đơn, tính lương SP",
              "status": "Not Started",
              "start_date": "18/11/2026",
              "due_date": "19/11/2026",
              "est_effort_hour": 16,
              "notes": "Xác nhận kết quả mong đợi cho các ca biên 1 hóa đơn - 1 dịch vụ và khóa kỳ lương",
              "task_complexity": 7,
              "type_of_work": "Do",
              "task_process": "Requirement & Design",
              "task_priority": "High"
            },
            {
              "pic": "PM",
              "task_name": "Theo dõi hoàn tất QC Sign-off & Phối hợp CSOC pentest - Tuần 7",
              "status": "Not Started",
              "start_date": "23/11/2026",
              "due_date": "25/11/2026",
              "est_effort_hour": 8,
              "notes": "Giám sát tiến độ đóng bug QC trước mốc 26/11 và điều phối lịch CSOC pentest từ 27/11",
              "task_complexity": 6,
              "type_of_work": "Do",
              "task_process": "Project Management",
              "task_priority": "High"
            },
            {
              "pic": "BA",
              "task_name": "Hỗ trợ đối soát số liệu Bảng lương SP và chuẩn bị dữ liệu CSOC pentest",
              "status": "Not Started",
              "start_date": "23/11/2026",
              "due_date": "24/11/2026",
              "est_effort_hour": 16,
              "notes": "Đối chiếu số liệu lương SP nhóm KTR, KTR khối ngoại, Server, HIGIO Cloud và chuẩn bị hồ sơ pentest",
              "task_complexity": 7,
              "type_of_work": "Do",
              "task_process": "Requirement & Design",
              "task_priority": "High"
            },
            {
              "pic": "DEV1",
              "task_name": "Fix bug QC đợt 2 cho logic map CID, tổng hợp lương SP và khóa kỳ lương",
              "status": "Not Started",
              "start_date": "23/11/2026",
              "due_date": "24/11/2026",
              "est_effort_hour": 16,
              "notes": "Fix triệt để các bug tính toán lương SP và hiển thị Chi tiết lương dịch vụ do QC ghi nhận",
              "task_complexity": 7,
              "type_of_work": "Fix/Rework",
              "task_process": "Coding",
              "task_priority": "High"
            },
            {
              "pic": "QC1",
              "task_name": "QC - testing: Thực hiện test Bảng lương nhân viên, Chi tiết lương và khóa kỳ lương",
              "status": "Not Started",
              "start_date": "24/11/2026",
              "due_date": "24/11/2026",
              "est_effort_hour": 8,
              "notes": "Test cộng lương vào nhóm KTR, KTR khối ngoại, Server, HIGIO Cloud và dòng nguồn Import KNg/TT",
              "task_complexity": 7,
              "type_of_work": "Do",
              "task_process": "Testing",
              "task_priority": "High"
            },
            {
              "pic": "DEV1",
              "task_name": "Đóng băng source code & Đóng gói bản build Staging phục vụ Regression",
              "status": "Not Started",
              "start_date": "25/11/2026",
              "due_date": "26/11/2026",
              "est_effort_hour": 16,
              "notes": "Cập nhật bản vá cuối lên Staging, hỗ trợ QC regression test và freeze code ngày 26/11",
              "task_complexity": 7,
              "type_of_work": "Do",
              "task_process": "Deployment",
              "task_priority": "High"
            },
            {
              "pic": "QC1",
              "task_name": "QC - testing: Recheck toàn bộ bug sau fix, Regression test và ký QC Sign-off",
              "status": "Not Started",
              "start_date": "25/11/2026",
              "due_date": "26/11/2026",
              "est_effort_hour": 16,
              "notes": "Verify toàn bộ bug đã đóng, hoàn tất Regression test và ký QC Sign-off đúng hạn 26/11/2026",
              "task_complexity": 7,
              "type_of_work": "Do",
              "task_process": "Testing",
              "task_priority": "Critical"
            },
            {
              "pic": "DEV1",
              "task_name": "Chuẩn bị môi trường Staging và cấu hình tài khoản cho đợt CSOC pentest",
              "status": "Not Started",
              "start_date": "27/11/2026",
              "due_date": "27/11/2026",
              "est_effort_hour": 8,
              "notes": "Bàn giao môi trường Staging đã freeze và tài khoản các role TĐV/TPP, NVKD cho đội CSOC pentest",
              "task_complexity": 6,
              "type_of_work": "Do",
              "task_process": "Coding",
              "task_priority": "High"
            },
            {
              "pic": "PM",
              "task_name": "Theo dõi tiến độ CSOC pentest cuối tháng 11 - Phần T11",
              "status": "Not Started",
              "start_date": "30/11/2026",
              "due_date": "30/11/2026",
              "est_effort_hour": 4,
              "notes": "Phối hợp cùng đội CSOC rà soát tiến độ pentest ngày cuối tháng 11",
              "task_complexity": 6,
              "type_of_work": "Do",
              "task_process": "Project Management",
              "task_priority": "High"
            },
            {
              "pic": "BA",
              "task_name": "Phối hợp làm rõ phân quyền vai trò TĐV/TPP, NVKD cùng CSOC - Phần T11",
              "status": "Not Started",
              "start_date": "30/11/2026",
              "due_date": "30/11/2026",
              "est_effort_hour": 8,
              "notes": "Hỗ trợ CSOC đối chiếu ma trận phân quyền menu và thao tác dữ liệu theo vai trò",
              "task_complexity": 6,
              "type_of_work": "Do",
              "task_process": "Requirement & Design",
              "task_priority": "High"
            },
            {
              "pic": "DEV1",
              "task_name": "Hỗ trợ kỹ thuật CSOC pentest và trích xuất log hệ thống - Phần T11",
              "status": "Not Started",
              "start_date": "30/11/2026",
              "due_date": "30/11/2026",
              "est_effort_hour": 8,
              "notes": "Standby hỗ trợ kỹ thuật và theo dõi log API trong quá trình CSOC thực hiện pentest",
              "task_complexity": 6,
              "type_of_work": "Do",
              "task_process": "Coding",
              "task_priority": "High"
            },
            {
              "pic": "PM",
              "task_name": "Điều phối UAT, nghiệm thu Security Sign-off & UAT Sign-off - Phần T12",
              "status": "Not Started",
              "start_date": "01/12/2026",
              "due_date": "03/12/2026",
              "est_effort_hour": 4,
              "notes": "Điều phối đóng toàn bộ findings pentest, hoàn tất Security Sign-off và UAT Sign-off trước 04/12",
              "task_complexity": 6,
              "type_of_work": "Do",
              "task_process": "Project Management",
              "task_priority": "High"
            },
            {
              "pic": "DEV1",
              "task_name": "Hỗ trợ ngày cuối CSOC pentest và tiếp nhận báo cáo findings - Phần T12",
              "status": "Not Started",
              "start_date": "01/12/2026",
              "due_date": "01/12/2026",
              "est_effort_hour": 8,
              "notes": "Tiếp nhận danh sách findings từ CSOC và phân tích phương án xử lý kỹ thuật",
              "task_complexity": 6,
              "type_of_work": "Do",
              "task_process": "Coding",
              "task_priority": "High"
            },
            {
              "pic": "BA",
              "task_name": "Hướng dẫn TĐV/TPP, Nhân viên KD thực hiện UAT và ký UAT Sign-off",
              "status": "Not Started",
              "start_date": "02/12/2026",
              "due_date": "03/12/2026",
              "est_effort_hour": 16,
              "notes": "Hướng dẫn người dùng test thực tế trên Staging, tổng hợp biên bản UAT Sign-off",
              "task_complexity": 7,
              "type_of_work": "Do",
              "task_process": "Requirement & Design",
              "task_priority": "Critical"
            },
            {
              "pic": "DEV1",
              "task_name": "Fix bug các findings từ báo cáo CSOC pentest và phối hợp recheck",
              "status": "Not Started",
              "start_date": "02/12/2026",
              "due_date": "03/12/2026",
              "est_effort_hour": 16,
              "notes": "Xử lý các lỗ hổng phân quyền/injection từ CSOC pentest và phối hợp CSOC verify Security Sign-off",
              "task_complexity": 7,
              "type_of_work": "Fix/Rework",
              "task_process": "Coding",
              "task_priority": "Critical"
            },
            {
              "pic": "DEV1",
              "task_name": "Fix bug phát sinh trong đợt UAT và đóng gói bản Release Production",
              "status": "Not Started",
              "start_date": "04/12/2026",
              "due_date": "04/12/2026",
              "est_effort_hour": 8,
              "notes": "Hoàn tất tinh chỉnh theo góp ý UAT, đóng gói Release Candidate và chuẩn bị kịch bản Rollback",
              "task_complexity": 6,
              "type_of_work": "Fix/Rework",
              "task_process": "Coding",
              "task_priority": "High"
            },
            {
              "pic": "PM",
              "task_name": "Điều phối Production Deploy và khởi động giai đoạn pilot",
              "status": "Not Started",
              "start_date": "07/12/2026",
              "due_date": "07/12/2026",
              "est_effort_hour": 4,
              "notes": "Điều phối triển khai Go-Live vào Thứ Hai 07/12/2026 và thông báo kế hoạch vận hành pilot",
              "task_complexity": 6,
              "type_of_work": "Do",
              "task_process": "Project Management",
              "task_priority": "High"
            },
            {
              "pic": "DEV1",
              "task_name": "Triển khai bản build lên môi trường Production và smoke test kỹ thuật",
              "status": "Not Started",
              "start_date": "07/12/2026",
              "due_date": "07/12/2026",
              "est_effort_hour": 8,
              "notes": "Deploy Production ngày Thứ Hai 07/12/2026 theo đúng quy tắc T2/T4; kiểm tra kết nối DB và phân quyền",
              "task_complexity": 7,
              "type_of_work": "Do",
              "task_process": "Deployment",
              "task_priority": "Critical"
            },
            {
              "pic": "BA",
              "task_name": "Thu thập feedback từ TĐV/TPP và Nhân viên KD trong giai đoạn pilot",
              "status": "Not Started",
              "start_date": "08/12/2026",
              "due_date": "09/12/2026",
              "est_effort_hour": 16,
              "notes": "Theo dõi người dùng khai báo CID khối ngoại và import hóa đơn U, M, TTTT thực tế trên Production",
              "task_complexity": 7,
              "type_of_work": "Do",
              "task_process": "Requirement & Design",
              "task_priority": "High"
            },
            {
              "pic": "DEV1",
              "task_name": "Monitor log/performance hệ thống và trực hotfix giai đoạn pilot - Đợt 1",
              "status": "Not Started",
              "start_date": "08/12/2026",
              "due_date": "09/12/2026",
              "est_effort_hour": 16,
              "notes": "Giám sát log import hóa đơn, hiệu năng tính lương SP và trực xử lý hotfix trong giai đoạn pilot",
              "task_complexity": 7,
              "type_of_work": "Do",
              "task_process": "Deployment",
              "task_priority": "High"
            },
            {
              "pic": "BA",
              "task_name": "Đối soát dữ liệu lương thực tế và lập báo cáo tổng kết kết quả pilot",
              "status": "Not Started",
              "start_date": "10/12/2026",
              "due_date": "11/12/2026",
              "est_effort_hour": 16,
              "notes": "Đối soát số liệu Bảng lương nhân viên, Chi tiết lương dịch vụ nguồn Import KNg/TT và nghiệm thu pilot",
              "task_complexity": 7,
              "type_of_work": "Do",
              "task_process": "Requirement & Design",
              "task_priority": "High"
            },
            {
              "pic": "DEV1",
              "task_name": "Monitor log/performance hệ thống và bàn giao vận hành sau pilot - Đợt 2",
              "status": "Not Started",
              "start_date": "10/12/2026",
              "due_date": "11/12/2026",
              "est_effort_hour": 16,
              "notes": "Theo dõi ổn định hệ thống đến kết thúc pilot và hoàn tất tài liệu bàn giao vận hành",
              "task_complexity": 6,
              "type_of_work": "Do",
              "task_process": "Deployment",
              "task_priority": "Medium"
            },
            {
              "pic": "PM",
              "task_name": "Tổng kết pilot, tổ chức Sprint Review & Retrospective đóng Sprint 3",
              "status": "Not Started",
              "start_date": "11/12/2026",
              "due_date": "11/12/2026",
              "est_effort_hour": 4,
              "notes": "Chủ trì buổi họp Sprint Review, Retrospective và chính thức đóng FTI-SAL v3.1 Sprint 3",
              "task_complexity": 6,
              "type_of_work": "Do",
              "task_process": "Project Management",
              "task_priority": "High"
            }
          ]
        }
      ]
    }
  ]
}


def sort_key(t):
    sd = t.get("start_date", "01/01/2099")
    dd = t.get("due_date", "01/01/2099")
    return (datetime.strptime(sd, "%d/%m/%Y"), datetime.strptime(dd, "%d/%m/%Y"))


for epic in data["epics"]:
    for us in epic["user_stories"]:
        us["tasks"] = sorted(us["tasks"], key=sort_key)

import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
SKILLS_DIR = os.path.join(ROOT_DIR, "skills")
OUTPUT_DIR = os.environ.get("REPORT_OUTPUT_DIR") or os.path.join(ROOT_DIR, "outputs")

if SKILLS_DIR not in sys.path:
    sys.path.insert(0, SKILLS_DIR)

from _shared.output_path import resolve_versioned_output_path

tmp_dir = os.path.join(OUTPUT_DIR, ".tmp")
os.makedirs(tmp_dir, exist_ok=True)
cache_json_path = os.path.join(tmp_dir, "sprint3_backlog.json")
with open(cache_json_path, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"Saved {cache_json_path} successfully.")

batch_hhmmss = sys.argv[1] if len(sys.argv) > 1 else datetime.now().strftime("%H%M%S")
plan_xlsx_path = resolve_versioned_output_path("sprint3_Project_Plan.xlsx", out_dir=OUTPUT_DIR, hhmmss=batch_hhmmss)
backlog_xlsx_path = resolve_versioned_output_path("sprint3_Sprint_Backlog.xlsx", out_dir=OUTPUT_DIR, hhmmss=batch_hhmmss)
backlog_md_path = resolve_versioned_output_path("sprint3_backlog.md", out_dir=OUTPUT_DIR, hhmmss=batch_hhmmss)

plan_xlsx_name = os.path.basename(plan_xlsx_path)
backlog_xlsx_name = os.path.basename(backlog_xlsx_path)
backlog_md_name = os.path.basename(backlog_md_path)

subprocess.run([sys.executable, os.path.join(HERE, "validate_cache.py"), cache_json_path], check=True)
subprocess.run([sys.executable, os.path.join(HERE, "json_to_excel.py"), cache_json_path, plan_xlsx_path], check=True)
subprocess.run([sys.executable, os.path.join(HERE, "json_to_excel_v2.py"), cache_json_path, backlog_xlsx_path], check=True)

md_content = f"""# SPRINT BACKLOG - FTI-SAL v3.1 Sprint 3

## 4. SPRINT BACKLOG

### 4.1 Sprint 3 – Import lương Kênh khối ngoại, HĐ Tân Thuận

> 📁 **Sprint Backlog Data:** file JSON nội bộ (source of truth, dùng ẩn để validate + export Excel - không share cho user).

#### 🎯 Tổng quan Sprint & Phạm vi Nghiệp vụ (FR01 – FR05)

- **Dự án:** FTI-SAL v3.1 (Salary Management System) – **Sprint 3**
- **Sprint Goal:** Hoàn thiện cụm tính năng Import lương Kênh khối ngoại, HĐ Tân Thuận theo vai trò TĐV/TPP và Nhân viên KD; tự động xác định loại doanh thu theo Circuit ID, tính lương sản phẩm, hoàn tất QC testing, CSOC pentest, UAT và pilot.
- **Nhân sự (4 thành viên):** `PM` (1), `BA` (1), `DEV1` (1), `QC1` (1 – tham gia từ `13/11/2026` đến `26/11/2026`).
- **Phạm vi 3 Nhóm tính năng lớn (tương đương EPIC / User Story):**
  1. **EPIC-1 (`US_1.1`) – Phân quyền Menu & Khai báo CID khối ngoại (FR01, FR02):**
     - **FR01:** Tách menu và màn hình theo vai trò (`TĐV / TPP`: *Import lương › Khai báo CID khối ngoại*; `Nhân viên KD`: giữ menu *Import lương › Kênh khối ngoại, HĐ Tân Thuận*).
     - **FR02:** Chức năng mới cho `TĐV / TPP` xem, import, xuất Excel, xóa thông tin CID quản lý tay (*Đối tác, Circuit ID, Ngày nghiệm thu CID, Phân loại doanh thu*) trước khi Nhân viên KD import lương.
  2. **EPIC-2 (`US_2.1`) – Import lương Kênh khối ngoại, HĐ Tân Thuận & Tự động xác định theo CID (FR03, FR04):**
     - **FR03:** Cập nhật màn hình cho `Nhân viên KD` xem, import, xuất Excel, xóa dữ liệu lương theo hóa đơn `U`, `M` và `TTTT` gắn với `Circuit ID` đã khai báo; bổ sung bộ lọc và cột *Circuit ID, Phân loại doanh thu, Loại dịch vụ*; áp dụng template mới, kiểm tra mẫu số HĐơn/HĐ, quy tắc *1 hóa đơn – 1 dịch vụ* (file có lỗi chặn import).
     - **FR04:** Hệ thống tự động tính *Loại doanh thu (Ký mới / Gia hạn)*, map *Phân loại doanh thu* và *Ngày nghiệm thu* theo `Circuit ID` do TĐV/TPP khai báo (thay cho FTI-CM).
  3. **EPIC-3 (`US_3.1`) – Tính lương SP, Bảng lương nhân viên & Chi tiết lương dịch vụ (FR05):**
     - **FR05:** Tính lương sản phẩm sau khi map `Circuit ID`, cộng vào nhóm *KTR, KTR khối ngoại, Server, HIGIO Cloud*; bổ sung dòng nguồn `Import KNg/TT` trên Chi tiết lương dịch vụ; tự động khóa import/xóa đối với kỳ lương có bảng lương đã gửi.

---

### Phase & Milestone Timeline

**Bảng Phases:**

| # | Phase | Mô tả | Start Date | End Date | Duration (ngày LV) |
|---|---|---|---|---|---|
| 1 | 📋 Requirements & URD | Phân tích yêu cầu FR01–FR05, thiết kế Wireframe & hoàn tất URD | 13/10/2026 | 16/10/2026 | 4 |
| 2 | ⚙️ Development | DEV1 coding FR01–FR05, viết Unit Test & triển khai bản build lên Staging (12/11) | 19/10/2026 | 12/11/2026 | 19 |
| 3 | 📚 QC Onboarding | BA demo luồng nghiệp vụ; QC1 join (13/11), đọc URD & thiết kế bộ testcase FR01–FR05 | 13/11/2026 | 19/11/2026 | 5 |
| 4 | 🧪 QC Testing | QC1 thực hiện testing trên Staging, DEV1 fix bug QC, Regression test & ký QC Sign-off (26/11) | 20/11/2026 | 26/11/2026 | 5 |
| 5 | 🛡️ Pentest & UAT | CSOC thực hiện pentest độc lập sau QC, người dùng thực hiện UAT, DEV1 fix bug & ký Sign-off | 27/11/2026 | 04/12/2026 | 6 |
| 6 | 🚀 Deploy & Pilot | Production Deploy (Thứ Hai 07/12/2026), smoke test, vận hành pilot 5 ngày & đóng Sprint | 07/12/2026 | 11/12/2026 | 5 |
| - | **Tổng cộng** | **Khớp chính xác tổng thời lượng Sprint (9 tuần)** | **13/10/2026** | **11/12/2026** | **44** |

**Bảng Key Milestones:**

| # | Milestone | Mô tả | Target Date |
|---|---|---|---|
| 1 | 🏁 Sprint Start | Sprint 3 chính thức bắt đầu, Kick-off & ban hành Risk Register | 13/10/2026 |
| 2 | 📄 URD Sign-off | Tài liệu URD & Wireframe cụm tính năng FR01–FR05 được ký duyệt | 16/10/2026 |
| 3 | ⚙️ Dev Complete | DEV1 hoàn tất coding FR01–FR05, pass Unit Test & deploy lên môi trường Staging | 12/11/2026 |
| 4 | 🔍 QC Join & Onboarding | QC1 chính thức tham gia Sprint, nhận bàn giao môi trường Staging & tài liệu URD | 13/11/2026 |
| 5 | ✅ Testing Complete | QC1 hoàn tất testing, verify toàn bộ bug fix, ký QC Sign-off & kết thúc lịch QC | 26/11/2026 |
| 6 | 🤝 UAT & Pentest Sign-off | Hoàn tất xử lý findings CSOC pentest, người dùng nghiệm thu UAT Sign-off | 04/12/2026 |
| 7 | 🎉 Go-Live & Pilot | Production Deploy Thứ Hai (07/12), vận hành pilot 5 ngày & đóng Sprint (11/12) | 07/12/2026 |

---

#### 📊 Tổng hợp Manday group theo Role (PM, BA, DEV, QC)

| Role | PIC | Giờ (Hours) | Manday (MD) | % | Ghi chú phân bổ nguồn lực |
|---|---|---:|---:|---:|---|
| **PM** | `PM` | 72.0 | 9.0 | 10.1% | Kick-off, theo dõi tiến độ từng tuần (≤ 3 ngày LV/task), điều phối UAT/Pentest & đóng Sprint |
| **BA** | `BA` | 208.0 | 26.0 | 29.2% | Phân tích & viết URD FR01–FR05, AC, UAT Scenario, User Guide, hỗ trợ QC, UAT & pilot |
| **DEV** | `DEV1` | 352.0 | 44.0 | 49.4% | Cố định chuẩn 40h/tuần liên tục 9 tuần (W42 4 ngày: 32h; W43–W50: 40h/tuần), 0 ngày trống |
| **QC** | `QC1` | 80.0 | 10.0 | 11.2% | Tham gia đúng khung `13/11/2026 – 26/11/2026` (10 ngày làm việc liên tục × 8h/ngày) |
| **Subtotal** | **4 Roles** | **712.0** | **89.0** | **100.0%** | **Tổng cộng 61 Tasks chi tiết trong 3 Feature Stories** |
| **Buffer 10%** | - | **+71.2** | **+8.9** | - | Buffer dự phòng chuẩn theo quy tắc Sprint Planning |
| **Total Manday Net** | - | **783.2** | **97.9** | - | **Thời lượng Sprint: 44 ngày làm việc (13/10/2026 – 11/12/2026)** |

**Bảng cân bằng tải theo tuần (Weekly Capacity Balance – Giờ):**

| Role / PIC | W42 (13-16/10) | W43 (19-23/10) | W44 (26-30/10) | W45 (02-06/11) | W46 (09-13/11) | W47 (16-20/11) | W48 (23-27/11) | W49 (30/11-04/12) | W50 (07-11/12) | Tổng (Giờ) | Tổng (MD) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **PM** (`PM`) | 8h | 8h | 8h | 8h | 8h | 8h | 8h | 8h | 8h | **72h** | **9.0 MD** |
| **BA** (`BA`) | 32h | 16h | 16h | 16h | 24h | 32h | 16h | 24h | 32h | **208h** | **26.0 MD** |
| **DEV** (`DEV1`) | 32h | 40h | 40h | 40h | 40h | 40h | 40h | 40h | 40h | **352h** | **44.0 MD** |
| **QC** (`QC1`) | 0h | 0h | 0h | 0h | 8h | 40h | 32h | 0h | 0h | **80h** | **10.0 MD** |
| **Tổng tuần** | **72h** | **64h** | **64h** | **64h** | **80h** | **120h** | **96h** | **72h** | **80h** | **712h** | **89.0 MD** |

---

### Danh sách Output Deliverables

1. **`{plan_xlsx_name}`**: File Excel Project Plan (Sheet `Sprint 3`, xuất từ script chuẩn `json_to_excel.py`, cấu trúc theo từng Feature EPIC, tự động tính công thức `MIN`, `MAX`, `SUM`).
2. **`{backlog_xlsx_name}`**: File Excel Detailed Sprint Backlog (Sheet `Sprint 3`, xuất từ script chuẩn `json_to_excel_v2.py`, đầy đủ Story Points theo công thức chuẩn, Effort Manday, Networkdays, Complexity, Process & Priority).
3. **`{backlog_md_name}`**: Báo cáo tổng hợp kế hoạch Sprint 3, Timeline các Phase, Key Milestones, bảng cân bằng tải nhân sự và kết quả đối chiếu Pre-flight Checklist.

---

### Pre-flight Checklist Verification

| # | Hạng mục kiểm tra | Trạng thái |
|---|---|---|
| 1 | **Story là tính năng lớn (tương đương EPIC)** – 3 User Stories (`US_1.1`, `US_2.1`, `US_3.1`) đại diện cho 3 cụm tính năng nghiệp vụ cốt lõi (FR01–FR05) | ✅ |
| 2 | **Tích hợp các phase vào Story tính năng** – Toàn bộ các phase `init`, `QC test/testing`, `pentest`, `UAT`, `pilot` được tích hợp trực tiếp vào bên trong các Story tính năng, không tách EPIC kỹ thuật riêng | ✅ |
| 3 | **Đầy đủ task phase Init tuần đầu (W1)** – BA phân tích/URD, DEV1 setup môi trường/technical design, PM kick-off & planning tuần 1 nằm trong `US_1.1` (W42); QC1 không có task ở W1 | ✅ |
| 4 | **Mọi Story tính năng đều có task của DEV (`DEV1`)** – Cả 3 Story đều có đầy đủ task coding, unit test, fix bug của `DEV1` | ✅ |
| 5 | **Label PIC cụ thể** – Sử dụng `PM`, `BA`, `DEV1`, `QC1`; không chứa label PIC trong `task_name` hoặc `notes` | ✅ |
| 6 | **JSON hợp lệ** – Đã kiểm tra bằng `validate_cache.py`, đạt exit code `0` (`✅ Cache hợp lệ - sẵn sàng xuất Excel.`) | ✅ |
| 7 | **Bảng Manday cập nhật đúng tổng giờ cho tất cả role** – PM: 9.0 MD, BA: 26.0 MD, DEV: 44.0 MD, QC: 10.0 MD; Subtotal: 89.0 MD, Buffer 10%: +8.9 MD, Total Net: 97.9 MD | ✅ |
| 8 | **Giới hạn effort & thời lượng mỗi task** – Toàn bộ 61 task đều có `est_effort_hour <= 24` và thời lượng `≤ 3 ngày làm việc` (working days ≤ 3), kể cả PM | ✅ |
| 9 | **Không rơi vào Thứ 7 / Chủ Nhật** – 100% `start_date` và `due_date` là ngày làm việc từ Thứ 2 đến Thứ 6 | ✅ |
| 10 | **Không span qua weekend và không span qua tháng** – Mọi task nằm gọn trong cùng 1 ISO week và cùng 1 tháng (tuần giao tháng W49 được tách rõ ngày `30/11` và `01/12–04/12`) | ✅ |
| 11 | **Chuẩn hóa thuật ngữ chung (Text General)** – Sử dụng chuẩn `test/testing`, `pentest`, `pilot`, `fix bug` | ✅ |
| 12 | **Even Number Effort** – 100% task có `est_effort_hour` thuộc tập `{4, 8, 16, 24}` | ✅ |
| 13 | **Weekly Balance Fixed 40h** – Đã chạy script kiểm tra: `DEV1` đạt chuẩn `32h/32h` (W42 4 ngày) và `40h/40h` liên tục từ W43 đến W50 (không OVERLOAD, không UNDERLOAD) | ✅ |
| 14 | **No-gap Check** – Đã chạy script kiểm tra: `DEV1` phủ kín `44/44` ngày làm việc; `QC1` phủ kín `10/10` ngày làm việc trong đúng khung `13/11/2026 – 26/11/2026` | ✅ |
| 15 | **Tasks đã sort** – Toàn bộ task trong từng User Story đã được sắp xếp theo `start_date`, `due_date` tăng dần | ✅ |
| 16 | **US sequential per member** – Mỗi PIC thực hiện tuần tự các task không chồng chéo thời gian | ✅ |
| 17 | **US description đúng format & độ dài** – Mô tả nghiệp vụ trung tính, độ dài 11–12 từ/story, không dùng cấu trúc *"Là [Role]..."* | ✅ |
| 18 | **Staging deploy & Production deploy đúng quy định** – Staging deploy (`12/11/2026`) hoàn tất trước khi QC bắt đầu (`13/11/2026`); Production deploy rơi vào Thứ Hai (`07/12/2026`); thứ tự chuẩn: Dev Complete → Staging Deploy → QC testing → Pentest & UAT → Production Deploy → Pilot | ✅ |

---

*Generated by Senior PM Skill - ISC Project Management Framework v2.10*
"""

with open(backlog_md_path, "w", encoding="utf-8") as f:
    f.write(md_content)

print(f"✅ Generated versioned outputs in {OUTPUT_DIR}:")
print(f"  - {plan_xlsx_name}")
print(f"  - {backlog_xlsx_name}")
print(f"  - {backlog_md_name}")


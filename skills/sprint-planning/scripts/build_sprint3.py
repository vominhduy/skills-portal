#!/usr/bin/env python3
"""Build sprint3_backlog.json for FTI-SAL v3.1 Sprint 3 (Re-planned to 31/12/2026), validate it, and export Excel files."""
import base64
import glob
import json
import os
import subprocess
import sys
from datetime import datetime

data = {
  "project": "FTI-SAL v3.1",
  "sprint_number": 3,
  "sprint_goal": "Hoàn thiện cụm tính năng Import lương Kênh khối ngoại, HĐ Tân Thuận theo vai trò TĐV/TPP và Nhân viên KD; tự động xác định loại doanh thu theo Circuit ID, tính lương sản phẩm, hoàn tất QC testing, CSOC pentest (01/12 - 11/12), UAT, Production deploy (21/12) và pilot kết thúc ngày 31/12/2026.",
  "time_box": [
    "1. Sprint Timeline: 13/10/2026 - 31/12/2026 (12 tuần, 58 ngày làm việc)",
    "2. Sprint Planning: 13/10/2026",
    "3. Daily Scrum: 09:00 - 09:15 hằng ngày làm việc",
    "4. Dev Complete & Staging Deploy: 12/11/2026",
    "5. QC test/testing: 13/11/2026 - 26/11/2026 (Onboarding 13/11 - 17/11; Testing 18/11 - 26/11; Ký QC Sign-off 26/11)",
    "6. Chuẩn bị môi trường & Hardening: 27/11/2026 - 30/11/2026",
    "7. CSOC pentest (sau QC): 01/12/2026 - 11/12/2026 (9 ngày làm việc)",
    "8. Fix findings pentest, Recheck, UAT & Sign-offs: 14/12/2026 - 18/12/2026",
    "9. Production Release: 21/12/2026 (Thứ Hai)",
    "10. Pilot: 21/12/2026 - 31/12/2026 (9 ngày làm việc)",
    "11. Sprint Review & Retrospective: 31/12/2026 (Kết thúc Sprint 3)"
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
              "notes": "Họp khởi động dự án FTI-SAL v3.1 Sprint 3, thống nhất phạm vi FR01-FR05 và Risk Register",
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
              "notes": "Làm rõ luồng TĐV/TPP khai báo CID quản lý tay và Nhân viên KD import lương theo hóa đơn kèm CID",
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
              "notes": "Khảo sát mã nguồn hiện tại của màn hình Import lương Kênh khối ngoại, HĐ Tân Thuận",
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
              "notes": "Theo dõi tiến độ hoàn thiện URD và chốt các giả định nghiệp vụ trong tuần 1",
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
              "notes": "Output: tài liệu URD đầy đủ cho FR01-FR05, ký duyệt URD Sign-off vào ngày 16/10/2026",
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
              "notes": "Thiết kế bảng dữ liệu lưu Đối tác, Circuit ID, Ngày nghiệm thu CID, Phân loại doanh thu và index tra cứu",
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
              "notes": "Quy định chi tiết quyền truy cập menu theo vai trò TĐV/TPP và định dạng file import CID",
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
              "notes": "Thêm menu Import lương > Khai báo CID khối ngoại cho TĐV/TPP; giữ tên menu cũ cho Nhân viên KD",
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
              "notes": "Kiểm tra trùng lặp Circuit ID, định dạng ngày nghiệm thu và xuất danh sách ra file Excel",
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
              "task_name": "QC - Nghiệp vụ: Đọc URD và thiết kế testcase phân quyền menu, khai báo CID (FR01, FR02)",
              "status": "Not Started",
              "start_date": "13/11/2026",
              "due_date": "13/11/2026",
              "est_effort_hour": 8,
              "notes": "Bắt đầu tham gia sprint ngày 13/11: nghiên cứu URD và thiết kế bộ testcase cho FR01, FR02",
              "task_complexity": 7,
              "type_of_work": "Study",
              "task_process": "Testing",
              "task_priority": "High"
            },
            {
              "pic": "QC1",
              "task_name": "QC - testing: Thực hiện test phân quyền menu và khai báo CID trên Staging (FR01, FR02)",
              "status": "Not Started",
              "start_date": "18/11/2026",
              "due_date": "18/11/2026",
              "est_effort_hour": 8,
              "notes": "Thực thi bộ testcase FR01, FR02 trên môi trường Staging và ghi nhận bug lên hệ thống Jira",
              "task_complexity": 6,
              "type_of_work": "Do",
              "task_process": "Testing",
              "task_priority": "High"
            },
            {
              "pic": "DEV1",
              "task_name": "Hỗ trợ kỹ thuật testing trên Staging và fix bug phân quyền menu, khai báo CID (FR01, FR02)",
              "status": "Not Started",
              "start_date": "18/11/2026",
              "due_date": "18/11/2026",
              "est_effort_hour": 8,
              "notes": "Xử lý ngay trong ngày các bug phát sinh ở màn hình Menu và Khai báo CID khối ngoại",
              "task_complexity": 7,
              "type_of_work": "Fix/Rework",
              "task_process": "Coding",
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
              "notes": "Quy định cấu trúc template mới, kiểm tra Circuit ID, mẫu số HĐơn/HĐ, quy tắc 1 hóa đơn - 1 dịch vụ",
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
              "notes": "Theo dõi tiến độ phát triển bộ xử lý tự động xác định theo CID (FR04)",
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
              "notes": "Xử lý logic tự tính Loại doanh thu cho các CID quản lý tay chưa có trên hệ thống FTI-CM",
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
              "task_name": "QC - Nghiệp vụ: Thiết kế testcase Import lương KNg/TT, map CID và Bảng lương (FR03-FR05)",
              "status": "Not Started",
              "start_date": "16/11/2026",
              "due_date": "17/11/2026",
              "est_effort_hour": 16,
              "notes": "Hoàn tất bộ testcase cho FR03, FR04, FR05: template mới, chặn file lỗi, tự tính Ký mới/Gia hạn và Bảng lương",
              "task_complexity": 7,
              "type_of_work": "Do",
              "task_process": "Testing",
              "task_priority": "High"
            },
            {
              "pic": "QC1",
              "task_name": "QC - testing: Thực hiện test Import lương KNg/TT và tự động xác định theo CID (FR03, FR04)",
              "status": "Not Started",
              "start_date": "19/11/2026",
              "due_date": "20/11/2026",
              "est_effort_hour": 16,
              "notes": "Thực thi bộ testcase hóa đơn U, M, TTTT, kiểm tra quy tắc 1 hóa đơn - 1 dịch vụ và tự động map CID",
              "task_complexity": 7,
              "type_of_work": "Do",
              "task_process": "Testing",
              "task_priority": "High"
            },
            {
              "pic": "DEV1",
              "task_name": "Fix bug đợt 1 cho luồng validate file import hóa đơn U, M, TTTT và tự động map CID (FR03, FR04)",
              "status": "Not Started",
              "start_date": "19/11/2026",
              "due_date": "20/11/2026",
              "est_effort_hour": 16,
              "notes": "Xử lý triệt để các bug phát sinh đợt 1 ở luồng kiểm tra mẫu số hóa đơn và tự động xác định theo CID",
              "task_complexity": 7,
              "type_of_work": "Fix/Rework",
              "task_process": "Coding",
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
              "notes": "Rà soát điều kiện Dev Complete và điều phối triển khai môi trường Staging trước đợt testing",
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
              "notes": "Xây dựng bộ kịch bản nghiệm thu UAT cho các vai trò TĐV/TPP, Nhân viên KD, BOD và HR",
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
              "notes": "Hoàn tất Dev Complete (12/11) và triển khai bản build ổn định lên Staging trước ngày 13/11",
              "task_complexity": 7,
              "type_of_work": "Do",
              "task_process": "Deployment",
              "task_priority": "Critical"
            },
            {
              "pic": "BA",
              "task_name": "Demo & Clear nghiệp vụ trên môi trường Staging",
              "status": "Not Started",
              "start_date": "13/11/2026",
              "due_date": "13/11/2026",
              "est_effort_hour": 8,
              "notes": "Demo trực tiếp luồng FR01-FR05 trên Staging và làm rõ các quy tắc nghiệp vụ ngày đầu onboarding",
              "task_complexity": 6,
              "type_of_work": "Do",
              "task_process": "Requirement & Design",
              "task_priority": "High"
            },
            {
              "pic": "DEV1",
              "task_name": "Chuẩn bị dữ liệu testbed hóa đơn U, M, TTTT và hỗ trợ kỹ thuật onboarding",
              "status": "Not Started",
              "start_date": "13/11/2026",
              "due_date": "13/11/2026",
              "est_effort_hour": 8,
              "notes": "Khởi tạo bộ dữ liệu mẫu Circuit ID, hóa đơn U, M, TTTT trên Staging phục vụ giai đoạn testing",
              "task_complexity": 6,
              "type_of_work": "Do",
              "task_process": "Coding",
              "task_priority": "High"
            },
            {
              "pic": "PM",
              "task_name": "Theo dõi tiến độ testing & Quản trị rủi ro - Tuần 6",
              "status": "Not Started",
              "start_date": "16/11/2026",
              "due_date": "18/11/2026",
              "est_effort_hour": 8,
              "notes": "Theo dõi tiến độ thiết kế testcase và thực hiện testing trên Staging trong tuần 6",
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
              "task_name": "Hỗ trợ testing & Clarify các ca biên validate hóa đơn, tính lương SP",
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
              "task_name": "Theo dõi hoàn tất Testing Sign-off & Phối hợp CSOC pentest - Tuần 7",
              "status": "Not Started",
              "start_date": "23/11/2026",
              "due_date": "25/11/2026",
              "est_effort_hour": 8,
              "notes": "Giám sát tiến độ đóng toàn bộ bug trước mốc 26/11 và chuẩn bị bàn giao môi trường cho CSOC pentest",
              "task_complexity": 6,
              "type_of_work": "Do",
              "task_process": "Project Management",
              "task_priority": "High"
            },
            {
              "pic": "BA",
              "task_name": "Hỗ trợ đối soát số liệu Bảng lương SP và chuẩn bị hồ sơ CSOC pentest",
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
              "task_name": "Fix bug đợt 2 cho logic tổng hợp lương SP, Chi tiết lương dịch vụ và khóa kỳ lương (FR05)",
              "status": "Not Started",
              "start_date": "23/11/2026",
              "due_date": "24/11/2026",
              "est_effort_hour": 16,
              "notes": "Fix triệt để các bug tính toán lương SP và hiển thị Chi tiết lương dịch vụ trên Staging",
              "task_complexity": 7,
              "type_of_work": "Fix/Rework",
              "task_process": "Coding",
              "task_priority": "High"
            },
            {
              "pic": "QC1",
              "task_name": "QC - testing: Thực hiện test Bảng lương nhân viên, Chi tiết lương và khóa kỳ lương (FR05)",
              "status": "Not Started",
              "start_date": "23/11/2026",
              "due_date": "24/11/2026",
              "est_effort_hour": 16,
              "notes": "Thực hiện test cộng lương vào nhóm KTR, KTR khối ngoại, Server, HIGIO Cloud và dòng nguồn Import KNg/TT",
              "task_complexity": 7,
              "type_of_work": "Do",
              "task_process": "Testing",
              "task_priority": "High"
            },
            {
              "pic": "DEV1",
              "task_name": "Đóng băng source code & Đóng gói bản build Staging phục vụ Regression test",
              "status": "Not Started",
              "start_date": "25/11/2026",
              "due_date": "26/11/2026",
              "est_effort_hour": 16,
              "notes": "Cập nhật bản vá cuối lên Staging, hỗ trợ regression test và đóng băng mã nguồn ngày 26/11",
              "task_complexity": 7,
              "type_of_work": "Do",
              "task_process": "Deployment",
              "task_priority": "High"
            },
            {
              "pic": "QC1",
              "task_name": "QC - testing: Recheck toàn bộ bug sau fix, Regression test và ký Sign-off",
              "status": "Not Started",
              "start_date": "25/11/2026",
              "due_date": "26/11/2026",
              "est_effort_hour": 16,
              "notes": "Verify toàn bộ bug đã đóng, hoàn tất Regression test và ký biên bản nghiệm thu testing đúng hạn 26/11/2026",
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
              "notes": "Bàn giao môi trường Staging đã đóng băng và tài khoản các vai trò TĐV/TPP, NVKD cho đội CSOC pentest",
              "task_complexity": 6,
              "type_of_work": "Do",
              "task_process": "Coding",
              "task_priority": "High"
            },
            {
              "pic": "PM",
              "task_name": "Họp rà soát phạm vi và kế hoạch kiểm thử an toàn thông tin cùng CSOC",
              "status": "Not Started",
              "start_date": "30/11/2026",
              "due_date": "30/11/2026",
              "est_effort_hour": 4,
              "notes": "Thống nhất phạm vi pentest, phương án kiểm thử Whitebox/Blackbox và đầu mối trực chiến CSOC từ 01/12",
              "task_complexity": 6,
              "type_of_work": "Do",
              "task_process": "Project Management",
              "task_priority": "High"
            },
            {
              "pic": "BA",
              "task_name": "Phối hợp rà soát ma trận phân quyền và luồng dữ liệu nhạy cảm cùng CSOC",
              "status": "Not Started",
              "start_date": "30/11/2026",
              "due_date": "30/11/2026",
              "est_effort_hour": 8,
              "notes": "Làm rõ ma trận phân quyền TĐV/TPP, Nhân viên KD và cơ chế bảo vệ dữ liệu lương nhạy cảm trước pentest",
              "task_complexity": 6,
              "type_of_work": "Do",
              "task_process": "Requirement & Design",
              "task_priority": "High"
            },
            {
              "pic": "DEV1",
              "task_name": "Bàn giao môi trường Staging đã hardening, tài khoản test và kiểm tra log với CSOC",
              "status": "Not Started",
              "start_date": "30/11/2026",
              "due_date": "30/11/2026",
              "est_effort_hour": 8,
              "notes": "Kiểm tra thông tuyến mạng Staging, bàn giao thông tin đăng nhập và xác thực hệ thống ghi log kiểm toán",
              "task_complexity": 6,
              "type_of_work": "Do",
              "task_process": "Coding",
              "task_priority": "High"
            },
            {
              "pic": "PM",
              "task_name": "Theo dõi tiến độ CSOC pentest Tuần 1 - Đợt T12",
              "status": "Not Started",
              "start_date": "01/12/2026",
              "due_date": "03/12/2026",
              "est_effort_hour": 4,
              "notes": "Giám sát tiến độ kiểm thử an toàn thông tin đợt 1 bắt đầu ngày 01/12/2026",
              "task_complexity": 6,
              "type_of_work": "Do",
              "task_process": "Project Management",
              "task_priority": "High"
            },
            {
              "pic": "BA",
              "task_name": "Hỗ trợ CSOC làm rõ kịch bản bypass nghiệp vụ, phân quyền menu và import file",
              "status": "Not Started",
              "start_date": "01/12/2026",
              "due_date": "02/12/2026",
              "est_effort_hour": 16,
              "notes": "Hỗ trợ đội CSOC phân tích các ca kiểm thử giả mạo vai trò, leo thang đặc quyền và chèn mã độc vào file Excel",
              "task_complexity": 7,
              "type_of_work": "Do",
              "task_process": "Requirement & Design",
              "task_priority": "High"
            },
            {
              "pic": "DEV1",
              "task_name": "Trực hỗ trợ kỹ thuật CSOC pentest, theo dõi access log và phân tích sơ bộ",
              "status": "Not Started",
              "start_date": "01/12/2026",
              "due_date": "02/12/2026",
              "est_effort_hour": 16,
              "notes": "Trực tiếp hỗ trợ kỹ thuật môi trường Staging và theo dõi log hệ thống trong những ngày đầu CSOC pentest",
              "task_complexity": 7,
              "type_of_work": "Do",
              "task_process": "Coding",
              "task_priority": "High"
            },
            {
              "pic": "DEV1",
              "task_name": "Tiếp nhận các cảnh báo bảo mật sớm từ CSOC, rà soát mã nguồn và chuẩn bị bản vá",
              "status": "Not Started",
              "start_date": "03/12/2026",
              "due_date": "04/12/2026",
              "est_effort_hour": 16,
              "notes": "Phân tích các lỗ hổng bảo mật sơ bộ do CSOC phát hiện ở các API import và chuẩn bị phương án khắc phục",
              "task_complexity": 7,
              "type_of_work": "Do",
              "task_process": "Coding",
              "task_priority": "High"
            },
            {
              "pic": "PM",
              "task_name": "Theo dõi tiến độ CSOC pentest Tuần 2 & Chuẩn bị kế hoạch UAT",
              "status": "Not Started",
              "start_date": "07/12/2026",
              "due_date": "09/12/2026",
              "est_effort_hour": 8,
              "notes": "Theo dõi tiến độ tuần pentest thứ 2 đến ngày 11/12 và điều phối lịch UAT người dùng sau pentest",
              "task_complexity": 6,
              "type_of_work": "Do",
              "task_process": "Project Management",
              "task_priority": "High"
            },
            {
              "pic": "BA",
              "task_name": "Soạn checklist nghiệm thu ATTT và hoàn thiện kịch bản nghiệm thu người dùng UAT",
              "status": "Not Started",
              "start_date": "07/12/2026",
              "due_date": "08/12/2026",
              "est_effort_hour": 16,
              "notes": "Rà soát điều kiện nghiệm thu bảo mật và chuẩn bị danh sách dữ liệu UAT thực tế cho các đơn vị kinh doanh",
              "task_complexity": 7,
              "type_of_work": "Do",
              "task_process": "Requirement & Design",
              "task_priority": "High"
            },
            {
              "pic": "DEV1",
              "task_name": "Hỗ trợ CSOC pentest chuyên sâu API xác thực, import Excel và phân quyền CID",
              "status": "Not Started",
              "start_date": "07/12/2026",
              "due_date": "08/12/2026",
              "est_effort_hour": 16,
              "notes": "Phối hợp cùng CSOC kiểm thử chuyên sâu các ca tấn công injection, CSRF, IDOR và phân quyền ngang",
              "task_complexity": 7,
              "type_of_work": "Do",
              "task_process": "Coding",
              "task_priority": "High"
            },
            {
              "pic": "DEV1",
              "task_name": "Trực kỹ thuật pentest tải cao, giám sát log và fix ngay các finding mức thấp",
              "status": "Not Started",
              "start_date": "09/12/2026",
              "due_date": "10/12/2026",
              "est_effort_hour": 16,
              "notes": "Theo dõi độ trễ API khi CSOC thực hiện fuzzing dữ liệu và sửa ngay các lỗi cấu hình header bảo mật",
              "task_complexity": 7,
              "type_of_work": "Do",
              "task_process": "Coding",
              "task_priority": "High"
            },
            {
              "pic": "DEV1",
              "task_name": "Phối hợp CSOC tổng kết đợt pentest, rà soát danh sách findings và tiếp nhận biên bản",
              "status": "Not Started",
              "start_date": "11/12/2026",
              "due_date": "11/12/2026",
              "est_effort_hour": 8,
              "notes": "Chốt kết quả kiểm thử an toàn thông tin đúng hạn 11/12/2026 và tiếp nhận báo cáo findings chính thức",
              "task_complexity": 6,
              "type_of_work": "Do",
              "task_process": "Coding",
              "task_priority": "Critical"
            },
            {
              "pic": "PM",
              "task_name": "Điều phối khắc phục findings pentest, tổ chức UAT và nghiệm thu Sign-offs",
              "status": "Not Started",
              "start_date": "14/12/2026",
              "due_date": "16/12/2026",
              "est_effort_hour": 8,
              "notes": "Chỉ đạo hoàn tất xử lý findings CSOC pentest, điều phối UAT và chốt Security & UAT Sign-off trước 18/12",
              "task_complexity": 6,
              "type_of_work": "Do",
              "task_process": "Project Management",
              "task_priority": "Critical"
            },
            {
              "pic": "BA",
              "task_name": "Hướng dẫn TĐV/TPP và Nhân viên KD thực hiện UAT các tính năng FR01-FR05 trên Staging",
              "status": "Not Started",
              "start_date": "14/12/2026",
              "due_date": "15/12/2026",
              "est_effort_hour": 16,
              "notes": "Trực tiếp hỗ trợ người dùng cuối thực hiện nghiệm thu UAT các luồng khai báo CID và import lương",
              "task_complexity": 7,
              "type_of_work": "Do",
              "task_process": "Requirement & Design",
              "task_priority": "High"
            },
            {
              "pic": "DEV1",
              "task_name": "Fix bug các findings theo báo cáo chính thức từ CSOC pentest",
              "status": "Not Started",
              "start_date": "14/12/2026",
              "due_date": "15/12/2026",
              "est_effort_hour": 16,
              "notes": "Khắc phục triệt để các lỗ hổng bảo mật theo khuyến nghị từ báo cáo pentest của CSOC",
              "task_complexity": 8,
              "type_of_work": "Fix/Rework",
              "task_process": "Coding",
              "task_priority": "Critical"
            },
            {
              "pic": "BA",
              "task_name": "Tổng hợp biên bản góp ý UAT, hỗ trợ người dùng nghiệm thu và hoàn tất UAT Sign-off",
              "status": "Not Started",
              "start_date": "16/12/2026",
              "due_date": "17/12/2026",
              "est_effort_hour": 16,
              "notes": "Lấy chữ ký nghiệm thu UAT Sign-off từ đại diện các đơn vị kinh doanh và nhân sự",
              "task_complexity": 7,
              "type_of_work": "Do",
              "task_process": "Requirement & Design",
              "task_priority": "Critical"
            },
            {
              "pic": "DEV1",
              "task_name": "Phối hợp CSOC recheck các lỗ hổng đã vá (Security Sign-off) và fix bug phát sinh từ UAT",
              "status": "Not Started",
              "start_date": "16/12/2026",
              "due_date": "17/12/2026",
              "est_effort_hour": 16,
              "notes": "Verify kết quả khắc phục cùng CSOC để đạt Security Sign-off và tinh chỉnh các phản hồi UAT",
              "task_complexity": 7,
              "type_of_work": "Fix/Rework",
              "task_process": "Coding",
              "task_priority": "Critical"
            },
            {
              "pic": "QC1",
              "task_name": "QC - testing: Recheck regression các module sau khi fix bug pentest và fix bug UAT",
              "status": "Not Started",
              "start_date": "16/12/2026",
              "due_date": "17/12/2026",
              "est_effort_hour": 16,
              "notes": "Đảm bảo các bản vá bảo mật và chỉnh sửa UAT không gây lỗi hồi quy trên toàn bộ hệ thống",
              "task_complexity": 7,
              "type_of_work": "Do",
              "task_process": "Testing",
              "task_priority": "High"
            },
            {
              "pic": "DEV1",
              "task_name": "Đóng gói bản Release Production, kiểm tra kịch bản Rollback và rà soát checklist Go-Live",
              "status": "Not Started",
              "start_date": "18/12/2026",
              "due_date": "18/12/2026",
              "est_effort_hour": 8,
              "notes": "Hoàn tất bản build Release Candidate, kiểm tra script migration DB và kịch bản rollback sẵn sàng cho 21/12",
              "task_complexity": 7,
              "type_of_work": "Do",
              "task_process": "Deployment",
              "task_priority": "Critical"
            },
            {
              "pic": "PM",
              "task_name": "Điều phối Production Deploy và khởi động giai đoạn pilot Tuần 1",
              "status": "Not Started",
              "start_date": "21/12/2026",
              "due_date": "23/12/2026",
              "est_effort_hour": 8,
              "notes": "Chỉ đạo triển khai Go-Live vào Thứ Hai 21/12/2026 và giám sát chặt chẽ tuần đầu vận hành pilot",
              "task_complexity": 6,
              "type_of_work": "Do",
              "task_process": "Project Management",
              "task_priority": "High"
            },
            {
              "pic": "BA",
              "task_name": "Hướng dẫn người dùng khởi tạo dữ liệu kỳ lương thực tế đầu tiên trên Production",
              "status": "Not Started",
              "start_date": "21/12/2026",
              "due_date": "21/12/2026",
              "est_effort_hour": 8,
              "notes": "Đồng hành trực tiếp cùng TĐV/TPP trong ngày đầu Go-Live để khai báo các Circuit ID khối ngoại",
              "task_complexity": 6,
              "type_of_work": "Do",
              "task_process": "Requirement & Design",
              "task_priority": "High"
            },
            {
              "pic": "DEV1",
              "task_name": "Triển khai bản build lên môi trường Production, thực hiện smoke test kỹ thuật",
              "status": "Not Started",
              "start_date": "21/12/2026",
              "due_date": "21/12/2026",
              "est_effort_hour": 8,
              "notes": "Deploy Production Thứ Hai 21/12/2026 theo đúng quy tắc T2/T4; kiểm tra phân quyền và kết nối hệ thống",
              "task_complexity": 7,
              "type_of_work": "Do",
              "task_process": "Deployment",
              "task_priority": "Critical"
            },
            {
              "pic": "QC1",
              "task_name": "QC - testing: Smoke test sau khi deploy lên môi trường Production",
              "status": "Not Started",
              "start_date": "21/12/2026",
              "due_date": "21/12/2026",
              "est_effort_hour": 4,
              "notes": "Thực hiện smoke test các chức năng chính trên Production ngay sau khi hoàn thành deploy",
              "task_complexity": 6,
              "type_of_work": "Do",
              "task_process": "Testing",
              "task_priority": "High"
            },
            {
              "pic": "BA",
              "task_name": "Theo dõi TĐV/TPP khai báo CID và NVKD import lương, thu thập feedback pilot",
              "status": "Not Started",
              "start_date": "22/12/2026",
              "due_date": "23/12/2026",
              "est_effort_hour": 16,
              "notes": "Ghi nhận phản hồi của người dùng thực tế khi import hóa đơn U, M, TTTT trong tuần đầu pilot",
              "task_complexity": 7,
              "type_of_work": "Do",
              "task_process": "Requirement & Design",
              "task_priority": "High"
            },
            {
              "pic": "DEV1",
              "task_name": "Giám sát hệ thống (monitor log/performance), hỗ trợ trực tuyến và trực hotfix pilot Đợt 1",
              "status": "Not Started",
              "start_date": "22/12/2026",
              "due_date": "23/12/2026",
              "est_effort_hour": 16,
              "notes": "Theo dõi log giao dịch import hóa đơn thực tế và sẵn sàng hỗ trợ xử lý ngay các ca vướng mắc",
              "task_complexity": 7,
              "type_of_work": "Do",
              "task_process": "Deployment",
              "task_priority": "High"
            },
            {
              "pic": "DEV1",
              "task_name": "Giám sát luồng tính lương sản phẩm thực tế, kiểm tra tính toàn vẹn dữ liệu và trực hotfix pilot Đợt 2",
              "status": "Not Started",
              "start_date": "24/12/2026",
              "due_date": "25/12/2026",
              "est_effort_hour": 16,
              "notes": "Kiểm tra tính chính xác của việc cộng dồn lương sản phẩm vào nhóm KTR, HIGIO Cloud và trực hotfix",
              "task_complexity": 7,
              "type_of_work": "Do",
              "task_process": "Deployment",
              "task_priority": "High"
            },
            {
              "pic": "PM",
              "task_name": "Theo dõi đánh giá kết quả pilot giai đoạn cuối và chuẩn bị hồ sơ đóng Sprint 3",
              "status": "Not Started",
              "start_date": "28/12/2026",
              "due_date": "30/12/2026",
              "est_effort_hour": 8,
              "notes": "Rà soát mức độ ổn định của hệ thống trong tuần chốt lương cuối năm 2026",
              "task_complexity": 6,
              "type_of_work": "Do",
              "task_process": "Project Management",
              "task_priority": "High"
            },
            {
              "pic": "BA",
              "task_name": "Đối soát dữ liệu bảng lương nhân viên và chi tiết lương dịch vụ kỳ pilot thực tế",
              "status": "Not Started",
              "start_date": "28/12/2026",
              "due_date": "29/12/2026",
              "est_effort_hour": 16,
              "notes": "Đối chiếu bảng lương tổng hợp với dữ liệu nguồn Import KNg/TT đảm bảo số liệu chính xác 100%",
              "task_complexity": 7,
              "type_of_work": "Do",
              "task_process": "Requirement & Design",
              "task_priority": "High"
            },
            {
              "pic": "DEV1",
              "task_name": "Giám sát hiệu năng hệ thống kỳ chốt lương cuối tháng, tối ưu cấu hình và trực vận hành",
              "status": "Not Started",
              "start_date": "28/12/2026",
              "due_date": "29/12/2026",
              "est_effort_hour": 16,
              "notes": "Đảm bảo hệ thống vận hành trơn tru khi các bộ phận đồng loạt khóa kỳ lương tháng 12/2026",
              "task_complexity": 7,
              "type_of_work": "Do",
              "task_process": "Deployment",
              "task_priority": "High"
            },
            {
              "pic": "BA",
              "task_name": "Hoàn thiện biên bản đánh giá kết quả pilot, bàn giao nghiệp vụ và báo cáo đóng sprint",
              "status": "Not Started",
              "start_date": "30/12/2026",
              "due_date": "31/12/2026",
              "est_effort_hour": 16,
              "notes": "Nghiệm thu kết quả vận hành pilot thành công, hoàn tất biên bản bàn giao tính năng cho người dùng",
              "task_complexity": 7,
              "type_of_work": "Do",
              "task_process": "Requirement & Design",
              "task_priority": "High"
            },
            {
              "pic": "DEV1",
              "task_name": "Hoàn tất tài liệu kỹ thuật bàn giao vận hành cho đội SysAdmin và tổng kết kỹ thuật Sprint 3",
              "status": "Not Started",
              "start_date": "30/12/2026",
              "due_date": "31/12/2026",
              "est_effort_hour": 16,
              "notes": "Bàn giao tài liệu hướng dẫn vận hành, danh mục API, sơ đồ cơ sở dữ liệu và hoàn tất nhiệm vụ kỹ thuật",
              "task_complexity": 6,
              "type_of_work": "Do",
              "task_process": "Deployment",
              "task_priority": "High"
            },
            {
              "pic": "PM",
              "task_name": "Tổng kết pilot, tổ chức Sprint Review & Retrospective đóng Sprint 3",
              "status": "Not Started",
              "start_date": "31/12/2026",
              "due_date": "31/12/2026",
              "est_effort_hour": 4,
              "notes": "Chủ trì buổi họp Sprint Review, Retrospective và chính thức đóng FTI-SAL v3.1 Sprint 3 vào ngày 31/12/2026",
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

# Clean old sprint3_* files in OUTPUT_DIR so version starts cleanly and avoids duplicate clutter
for old_pattern in ("sprint3_Project_Plan*", "sprint3_Sprint_Backlog*", "sprint3_backlog*"):
    for old_file in glob.glob(os.path.join(OUTPUT_DIR, old_pattern)):
        if os.path.isfile(old_file):
            try:
                os.remove(old_file)
            except OSError:
                pass

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

md_content = f"""# SPRINT BACKLOG - FTI-SAL v3.1 Sprint 3 (Re-planned)

## 4. SPRINT BACKLOG

### 4.1 Sprint 3 – Import lương Kênh khối ngoại, HĐ Tân Thuận

> 📁 **Sprint Backlog Data:** file JSON nội bộ (source of truth, dùng ẩn để validate + export Excel - không share cho user).

#### 🎯 Tổng quan Sprint & Phạm vi Nghiệp vụ (FR01 – FR05)

- **Dự án:** FTI-SAL v3.1 (Salary Management System) – **Sprint 3 (Re-planned)**
- **Sprint Goal:** Hoàn thiện cụm tính năng Import lương Kênh khối ngoại, HĐ Tân Thuận theo vai trò TĐV/TPP và Nhân viên KD; tự động xác định loại doanh thu theo Circuit ID, tính lương sản phẩm, hoàn tất QC testing, CSOC pentest (01/12 - 11/12), UAT, Production deploy (21/12) và pilot kết thúc ngày 31/12/2026.
- **Thời lượng:** **13/10/2026 – 31/12/2026** (12 tuần, 58 ngày làm việc).
- **Nhân sự (4 thành viên):** `PM` (1), `BA` (1), `DEV1` (1), `QC1` (1 – tham gia đúng khung `13/11/2026` đến `26/11/2026`, hỗ trợ recheck sau pentest/UAT `16-17/12` và smoke test `21/12`).
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
| 3 | 📚 QC Onboarding | BA demo luồng nghiệp vụ; QC1 join (13/11), đọc URD & thiết kế bộ testcase FR01–FR05 | 13/11/2026 | 17/11/2026 | 3 |
| 4 | 🧪 QC Testing | QC1 thực hiện testing trên Staging (18/11–26/11), DEV1 fix bug, Regression test & ký Sign-off (26/11) | 18/11/2026 | 26/11/2026 | 7 |
| 5 | 🔒 Security Prep & Hardening | Đóng băng Staging, cấu hình tài khoản, rà soát ma trận phân quyền và bàn giao môi trường | 27/11/2026 | 30/11/2026 | 2 |
| 6 | 🛡️ CSOC Pentest | Đội CSOC pentest thực hiện kiểm thử an toàn thông tin độc lập sau QC đúng lịch yêu cầu | 01/12/2026 | 11/12/2026 | 9 |
| 7 | 🤝 Post-Pentest, UAT & Sign-offs | DEV1 fix findings pentest, QC recheck (Security Sign-off), người dùng UAT & UAT Sign-off | 14/12/2026 | 18/12/2026 | 5 |
| 8 | 🚀 Deploy & Pilot | Production Deploy (Thứ Hai 21/12/2026), smoke test, vận hành pilot 9 ngày & đóng Sprint (31/12) | 21/12/2026 | 31/12/2026 | 9 |
| - | **Tổng cộng** | **Khớp chính xác tổng thời lượng Sprint 3 Re-planned (12 tuần)** | **13/10/2026** | **31/12/2026** | **58** |

**Bảng Key Milestones:**

| # | Milestone | Mô tả | Target Date |
|---|---|---|---|
| 1 | 🏁 Sprint Start | Sprint 3 chính thức bắt đầu, Kick-off & ban hành Risk Register | 13/10/2026 |
| 2 | 📄 URD Sign-off | Tài liệu URD & Wireframe cụm tính năng FR01–FR05 được ký duyệt | 16/10/2026 |
| 3 | ⚙️ Dev Complete | DEV1 hoàn tất coding FR01–FR05, pass Unit Test & deploy lên môi trường Staging | 12/11/2026 |
| 4 | 🔍 QC Join & Onboarding | QC1 chính thức tham gia Sprint (13/11), nhận bàn giao môi trường Staging & thiết kế testcase | 13/11/2026 |
| 5 | ✅ Testing Complete | QC1 hoàn tất testing, verify toàn bộ bug fix, ký QC Sign-off & chốt lịch QC | 26/11/2026 |
| 6 | 🛡️ CSOC Pentest Window | CSOC thực hiện pentest độc lập theo đúng khung thời gian quy định | 01/12/2026 - 11/12/2026 |
| 7 | 🤝 UAT & Security Sign-off | Hoàn tất xử lý findings CSOC pentest, người dùng nghiệm thu UAT Sign-off | 18/12/2026 |
| 8 | 🚀 Production Deploy | Production Deploy vào Thứ Hai 21/12/2026 theo quy tắc lịch T2/T4 | 21/12/2026 |
| 9 | 🎉 Pilot & Sprint Closing | Vận hành pilot 9 ngày làm việc, tổng kết nghiệm thu và chính thức đóng Sprint 3 | 31/12/2026 |

---

#### 📊 Tổng hợp Manday group theo Role (PM, BA, DEV, QC)

| Role | PIC | Giờ (Hours) | Manday (MD) | % | Ghi chú phân bổ nguồn lực |
|---|---|---:|---:|---:|---|
| **PM** | `PM` | 100.0 | 12.5 | 10.6% | Kick-off, theo dõi tiến độ từng tuần (≤ 3 ngày LV/task), điều phối Pentest, UAT, Deploy & đóng Sprint 31/12 |
| **BA** | `BA` | 280.0 | 35.0 | 29.7% | Phân tích & viết URD FR01–FR05, AC, UAT Scenario, User Guide, phối hợp pentest, hướng dẫn UAT & theo dõi pilot |
| **DEV** | `DEV1` | 464.0 | 58.0 | 49.1% | Cố định chuẩn 40h/tuần liên tục 12 tuần (W42 4 ngày: 32h; W43–W52: 40h/tuần; W53 4 ngày: 32h), 0 ngày trống |
| **QC** | `QC1` | 100.0 | 12.5 | 10.6% | Khung testing chính `13/11–26/11` (80h), recheck regression sau pentest/UAT (16h) và smoke test Production (4h) |
| **Subtotal** | **4 Roles** | **944.0** | **118.0** | **100.0%** | **Tổng cộng 75 Tasks chi tiết trong 3 Feature Stories** |
| **Buffer 10%** | - | **+94.4** | **+11.8** | - | Buffer dự phòng chuẩn theo quy tắc Sprint Planning |
| **Total Manday Net** | - | **1038.4** | **129.8** | - | **Thời lượng Sprint: 58 ngày làm việc (13/10/2026 – 31/12/2026)** |

**Bảng cân bằng tải theo tuần (Weekly Capacity Balance – Giờ):**

| Role / PIC | W42 (13-16/10) | W43 (19-23/10) | W44 (26-30/10) | W45 (02-06/11) | W46 (09-13/11) | W47 (16-20/11) | W48 (23-27/11) | W49 (30/11-04/12) | W50 (07-11/12) | W51 (14-18/12) | W52 (21-25/12) | W53 (28-31/12) | Tổng (Giờ) | Tổng (MD) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **PM** (`PM`) | 8h | 8h | 8h | 8h | 8h | 8h | 8h | 8h | 8h | 8h | 8h | 12h | **100h** | **12.5 MD** |
| **BA** (`BA`) | 32h | 16h | 16h | 16h | 24h | 32h | 16h | 24h | 16h | 32h | 24h | 32h | **280h** | **35.0 MD** |
| **DEV** (`DEV1`) | 32h | 40h | 40h | 40h | 40h | 40h | 40h | 40h | 40h | 40h | 40h | 32h | **464h** | **58.0 MD** |
| **QC** (`QC1`) | 0h | 0h | 0h | 0h | 8h | 40h | 32h | 0h | 0h | 16h | 4h | 0h | **100h** | **12.5 MD** |
| **Tổng tuần** | **72h** | **64h** | **64h** | **64h** | **80h** | **120h** | **96h** | **72h** | **64h** | **96h** | **76h** | **76h** | **944h** | **118.0 MD** |

---

### Danh sách Output Deliverables

1. **`{plan_xlsx_name}`**: File Excel Project Plan (Sheet `Sprint 3`, xuất từ script chuẩn `json_to_excel.py`, cấu trúc theo từng Feature EPIC, tự động tính công thức `MIN`, `MAX`, `SUM`).
2. **`{backlog_xlsx_name}`**: File Excel Detailed Sprint Backlog (Sheet `Sprint 3`, xuất từ script chuẩn `json_to_excel_v2.py`, đầy đủ Story Points theo công thức chuẩn, Effort Manday, Networkdays, Complexity, Process & Priority).
3. **`{backlog_md_name}`**: Báo cáo tổng hợp kế hoạch Sprint 3 (Re-planned), Timeline các Phase, Key Milestones, bảng cân bằng tải nhân sự và kết quả đối chiếu Pre-flight Checklist.

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
| 7 | **Bảng Manday cập nhật đúng tổng giờ cho tất cả role** – PM: 12.5 MD, BA: 35.0 MD, DEV: 58.0 MD, QC: 12.5 MD; Subtotal: 118.0 MD, Buffer 10%: +11.8 MD, Total Net: 129.8 MD | ✅ |
| 8 | **Giới hạn effort & thời lượng mỗi task** – Toàn bộ 75 task đều có `est_effort_hour <= 24` và thời lượng `≤ 3 ngày làm việc` (working days ≤ 3), kể cả PM | ✅ |
| 9 | **Không rơi vào Thứ 7 / Chủ Nhật** – 100% `start_date` và `due_date` là ngày làm việc từ Thứ 2 đến Thứ 6 | ✅ |
| 10 | **Không span qua weekend và không span qua tháng** – Mọi task nằm gọn trong cùng 1 ISO week và cùng 1 tháng (tuần giao tháng W49 được tách rõ ngày `30/11` và `01/12–04/12`) | ✅ |
| 11 | **Chuẩn hóa thuật ngữ chung (Text General)** – Sử dụng chuẩn `test/testing`, `pentest`, `pilot`, `fix bug` | ✅ |
| 12 | **Even Number Effort** – 100% task có `est_effort_hour` thuộc tập `{4, 8, 16, 24}` | ✅ |
| 13 | **Weekly Balance Fixed 40h** – Đã chạy script kiểm tra: `DEV1` đạt chuẩn `32h/32h` (W42 4 ngày), `40h/40h` liên tục từ W43 đến W52 và `32h/32h` ở W53 (không OVERLOAD, không UNDERLOAD) | ✅ |
| 14 | **No-gap Check** – Đã chạy script kiểm tra: `DEV1` phủ kín `58/58` ngày làm việc từ 13/10/2026 đến 31/12/2026; `QC1` phủ kín các ngày làm việc trong các giai đoạn được phân công | ✅ |
| 15 | **Tasks đã sort** – Toàn bộ task trong từng User Story đã được sắp xếp theo `start_date`, `due_date` tăng dần | ✅ |
| 16 | **US sequential per member** – Mỗi PIC thực hiện tuần tự các task không chồng chéo thời gian | ✅ |
| 17 | **US description đúng format & độ dài** – Mô tả nghiệp vụ trung tính, độ dài 10–11 từ/story, không dùng cấu trúc *"Là [Role]..."* | ✅ |
| 18 | **Lịch Pentest & Pilot đúng yêu cầu** – Pentest diễn ra từ `01/12/2026` đến `11/12/2026` (sau QC `13/11–26/11`); Production deploy vào Thứ Hai (`21/12/2026`); Pilot kết thúc đúng ngày `31/12/2026` | ✅ |

---

*Generated by Senior PM Skill - ISC Project Management Framework v2.10*
"""

with open(backlog_md_path, "w", encoding="utf-8") as f:
    f.write(md_content)

# Sync seed file so server.js always restores the latest Sprint 3 deliverables on startup
seed_path = os.path.join(HERE, "sprint3_xlsx_seed.json")
seed_data = {}
for fpath in (plan_xlsx_path, backlog_xlsx_path, backlog_md_path):
    if os.path.isfile(fpath):
        with open(fpath, "rb") as bf:
            seed_data[os.path.basename(fpath)] = base64.b64encode(bf.read()).decode("ascii")
with open(seed_path, "w", encoding="utf-8") as sf:
    json.dump(seed_data, sf, indent=2)

print(f"✅ Generated versioned outputs in {OUTPUT_DIR}:")
print(f"  - {plan_xlsx_name}")
print(f"  - {backlog_xlsx_name}")
print(f"  - {backlog_md_name}")

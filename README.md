# Skills Portal & .env Studio (Trọn bộ All-in-One)

Một package hoàn toàn độc lập, tách biệt khỏi mã nguồn chính. Bạn có thể **di chuyển (copy/move) toàn bộ thư mục `skills-portal` này đi bất kỳ máy tính nào** để vừa xem tài liệu/guideline, vừa cấu hình file `.env` trực quan trên web, vừa chạy trực tiếp các script kỹ năng bằng CLI/Python.

---

## 📁 Cấu Trúc Trọn Gói

```
skills-portal/
├── index.html                  # Giao diện web HTML5 xem Guideline, File Explorer & cấu hình .env (Mở trực tiếp)
├── css/
│   └── style.css               # Hệ thống giao diện Glassmorphism (Dark / Light mode, Tree styles)
├── js/
│   ├── skills-data.js          # Dữ liệu 13 skills và định nghĩa biến môi trường
│   ├── skills-files.js         # 🌲 Cây thư mục và mã nguồn đầy đủ của toàn bộ file trong skills/
│   ├── markdown-parser.js      # Bộ parser render Markdown độc lập
│   └── app.js                  # Logic ứng dụng, Explorer tree, lưu LocalStorage, import/export .env
│
├── skills/                     # 🌟 TRỌN BỘ MÃ NGUỒN CÁC SKILLS (ĐÃ COPY ĐỦ)
│   ├── _shared/                # Thư viện dùng chung (Jira, MS Graph, Mem0, Network...)
│   ├── hrm-weekly-report/      # Báo cáo tuần HRM FPT -> Excel Online / Google Sheets
│   ├── jira-import/            # Import Backlog Excel lên Jira
│   ├── jira-story-today-reviewer/ # Rà soát Story hôm nay & chuyển In Progress
│   ├── jira-subtask-reviewer/  # Rà soát Sub-task Jira In Review (Est == Spent)
│   ├── outlook-digest/         # Đọc email Outlook an toàn (auto-redact)
│   ├── pm-sprint-summary/      # Báo cáo tóm tắt sprint góc nhìn PM
│   ├── prd-testcase-reviewer/  # Review Test Cases theo PRD
│   ├── product-backlog/        # Lập kế hoạch Product Backlog
│   ├── project-assistant/      # Trợ lý dự án, tra cứu Jira & Outlook
│   ├── sprint-planning/        # Lập kế hoạch Sprint Backlog
│   ├── sprint-timeline-chart/  # Xuất biểu đồ Timeline Gantt HTML
│   ├── vn-stock-advisor/       # Phân tích chứng khoán Finbox đa tầng
│   └── weekly-report-api/      # Báo cáo tiến độ tuần từ Jira / Sheets / Excel
│
├── requirements.txt            # Thư viện Python cần thiết (requests, openpyxl, pandas, msal...)
├── run_skill.py                # 🚀 Script Python điều phối chạy mọi skill tự động
├── run.ps1                     # Script tiện ích chạy skill trên Windows (PowerShell)
├── run.sh                      # Script tiện ích chạy skill trên Linux / macOS / Git Bash
├── outputs/                    # Thư mục lưu kết quả báo cáo khi chạy skill
└── .env                        # File biến môi trường (xuất từ index.html lưu tại đây)
```

---

## 🚀 Hướng Dẫn Sử Dụng Khi Mang Đi Máy Khác

### Bước 1: Mở Web Cấu Hình & Xuất File `.env`
1. Nhấp đúp chuột vào file **`index.html`** để mở trên trình duyệt (Chrome, Edge, Firefox...).
2. Xem hướng dẫn, guideline và từ khóa kích hoạt của 13 skills.
3. Chuyển sang tab **"Toàn bộ Biến .env"** hoặc **"Cài đặt Env Skill"** để điền các thông tin:
   - Jira: `JIRA_BASE_URL`, `JIRA_EMAIL`, `JIRA_API_TOKEN`
   - HRM: `HRM_USERNAME`, `HRM_PASSWORD`, `HRM_EXCEL_URL`
   - Outlook: `OUTLOOK_EMAIL`, `OUTLOOK_PASSWORD`, `MS_GRAPH_ACCESS_TOKEN`
4. Bấm **"Xuất .env"** và lưu file `.env` vào ngay thư mục gốc `skills-portal/`.

### Bước 2: Cài Đặt Thư Viện Python (Chỉ làm 1 lần)
Mở Terminal trong thư mục `skills-portal` và cài các thư viện phụ thuộc:
```bash
pip install -r requirements.txt
```

### Bước 3: Chạy Skill Trực Tiếp

#### Cách 1: Dùng lệnh Python Universal Runner (`run_skill.py`)
Tự động nạp `.env`, cấu hình đường dẫn `SKILL_DIR` và `REPORT_OUTPUT_DIR`, đưa kết quả vào thư mục `outputs/`:

```bash
# Xem danh sách các skill có thể chạy
python run_skill.py list

# Chạy skill rà soát Story hôm nay
python run_skill.py jira-story-today-reviewer

# Chạy skill rà soát subtask
python run_skill.py jira-subtask-reviewer

# Chạy skill báo cáo tuần Jira/Sheet
python run_skill.py weekly-report-api --project-key FCR --sprint-name "Sprint 3"

# Chạy skill HRM Weekly Report
python run_skill.py hrm-weekly-report
```

#### Cách 2: Dùng Helper Script
- Trên **Windows (PowerShell)**:
  ```powershell
  .\run.ps1
  # Hoặc: .\run.ps1 jira-story-today-reviewer
  ```
- Trên **Linux / macOS**:
  ```bash
  chmod +x run.sh
  ./run.sh
  # Hoặc: ./run.sh jira-story-today-reviewer
  ```

---

## 🔒 Tính Năng Nổi Bật
- **100% Độc lập**: Không phụ thuộc vào source webapp chính hay database.
- **Offline First**: Xem guideline và tài liệu không cần internet.
- **Bảo mật**: Các biến môi trường nhạy cảm được quản lý cục bộ trong file `.env` trên máy của bạn, có nút ẩn/hiện mắt xem mật khẩu.

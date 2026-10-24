/**
 * Pre-compiled skills and environment variable definitions
 * Namespace: SKILLS_PORTAL_DATA
 * Completely standalone, no backend required.
 */
window.SKILLS_PORTAL_DATA = {
  "skills": [
    {
      "id": "hrm-weekly-report",
      "name": "hrm-weekly-report",
      "category": "HRM & Reporting",
      "icon": "bi-file-earmark-spreadsheet",
      "description": "\"Chạy weekly report HRM (apis.fpt.net) và ghi vào Microsoft Excel Online (SharePoint / OneDrive qua Graph API) hoặc Google Sheets. Login HRM bằng username/password (từ env) lấy access_token, scrape API weekly-reports, ghi bảng tính. Trigger khi user nói: báo cáo HRM, weekly report HRM, cập nhật sheet HRM, cập nhật excel HRM, lấy dữ liệu tuần HRM, hoặc yêu cầu tổng hợp tiến độ dự án từ hệ thống HRM FPT.\"",
      "triggers": [
        "báo cáo HRM",
        "weekly report HRM",
        "cập nhật sheet HRM",
        "cập nhật excel HRM",
        "lấy dữ liệu tuần HRM"
      ],
      "guidelineMarkdown": "# HRM Weekly Report (Python, gọi API trực tiếp)\n\nLấy dữ liệu báo cáo tuần từ HRM FPT (`apis.fpt.net`) qua REST API và ghi vào **Microsoft Excel Online (SharePoint / OneDrive)** hoặc **Google Sheets**.\n\n- **Xác thực Microsoft Excel Online (SharePoint / OneDrive)**:\n  - Sử dụng **Microsoft Graph API** với cơ chế MSAL Token Cache (`token_cache.bin`) / Device Code Flow.\n  - Hỗ trợ trực tiếp đường dẫn chia sẻ (Sharing URL) trên SharePoint hoặc OneDrive (`HRM_EXCEL_URL` hoặc tham số `--excel-url`).\n  - Hỗ trợ đầy đủ các schema:\n    - **Sheet Project2026** (78 cột A–BZ của file `2026_SU02_Resource_Planning.xlsx`): Match Key tại Cột B (`Project/Version`), bảo toàn 100% 48 cột Resource 12 tháng (W–BR) và các số liệu PMO (Effort/Defect).\n    - **Sheet Portfolio 2026** (27 cột A–AA của file `Duy_Test_2026_SU02_KEY_PROJECTS.xlsx`).\n    - **Sheet FTI** (19 cột A–S của file `ISC _KEY PROJECT_2026.xlsx`).\n- **Xác thực Google Sheets (Dự phòng tương thích ngược cho file cũ)**:\n  - Giữ nguyên 100% logic và mapping cho file Google Sheets (`13ENSxJkc9lL43lmofw9HIxF9sdR_cElNtW2D581KIkw`), có cập nhật Cột S là Ngày báo cáo.\n  - Dùng **User OAuth Access Token** hoặc Google Service Account JSON key (`GOOGLE_SERVICE_ACCOUNT_PATH`).\n\n## Pipeline (MỘT lệnh Bash duy nhất)\n\n```bash\ncd \"$SKILL_DIR\" && python3 scripts/run_hrm_report.py --output-dir \"$REPORT_OUTPUT_DIR\"\n```\n\nTuỳ chọn:\n- `--excel-url \"https://...sharepoint.com/...\"` - chỉ định link chia sẻ file Excel trên SharePoint/OneDrive (Graph API).\n- `--excel-url2 \"https://...sharepoint.com/...\"` - chỉ định link chia sẻ file Excel cho Sheet 2 (nếu tách riêng).\n- `--week-start YYYY-MM-DD --week-end YYYY-MM-DD` - chỉ định tuần (mặc định: Thứ 2→Chủ Nhật tuần hiện tại).\n- `--token \"<access_token>\"` - dùng token có sẵn, bỏ qua bước login.\n- `--vpn {auto,true,false}` - cơ chế VPN (`auto`: tự động bật khi chưa vào được mạng nội bộ FPT, `true`: ép bật, `false`: tắt).\n- `--vpn-type {openvpn,openconnect,openfortivpn,wireguard,ssh_tunnel,custom}` - loại VPN (mặc định `openvpn` cho OpenVPN Connect).\n- `--vpn-host <host>` - địa chỉ máy chủ VPN (ví dụ: `csocvpn.fpt.net`).\n- `--vpn-user <account>` - tài khoản công ty FPT.\n- `--vpn-otp <otp>` - mã OTP 6 số từ Authenticator (nếu nhập trực tiếp).\n- `--vpn-totp-secret <secret>` - khóa bí mật Base32 từ Authenticator để tự động sinh mã OTP 6 số.\n- `--vpn-config <path>` - file cấu hình `.ovpn` (nếu có, ví dụ `data/csocvpn.ovpn`).\n- `--vpn-keep-alive` - giữ kết nối VPN sau khi hoàn thành scrape (không tự ngắt).\n\n> Webapp tự chạy pipeline (auto-remedy) - KHÔNG hỏi user cấp quyền Bash.\n\n## Cơ chế OpenVPN & Mạng nội bộ FPT (`csocvpn.fpt.net`)\n\nDo hệ thống HRM FPT (`apis.fpt.net` / `hrm.fpt.net`) nằm trong mạng nội bộ FPT Telecom, khi chạy báo cáo từ xa (máy cá nhân ở nhà, VPS cloud hoặc Docker), script hỗ trợ **tự động kiểm tra và kết nối OpenVPN**:\n1. **Tự động chẩn đoán**: Kiểm tra trước xem `apis.fpt.net:443` hoặc `hrm.fpt.net:443` đã thông mạng chưa. Nếu đã ở trong mạng FPT hoặc VPN đã bật ngoài máy -> bỏ qua bước VPN.\n2. **Kích hoạt tự động**: Nếu chưa thông mạng và có cấu hình VPN (`HRM_VPN_ENABLED=auto` hoặc `true`), script tự động bật OpenVPN kết nối tới `csocvpn.fpt.net`.\n3. **Cơ chế xác thực 2FA OTP thông minh**:\n   - **Tự động sinh OTP (Khuyên dùng)**: Cấu hình `HRM_VPN_TOTP_SECRET=<key_base32>` (lấy từ mã QR / Authenticator app khi thiết lập 2FA công ty). Mỗi lần chạy, script tự động tính mã 6 số chuẩn RFC 6238 theo giờ hệ thống mà không cần mở điện thoại lấy mã!\n   - **Nhập OTP trực tiếp**: Truyền qua CLI `--vpn-otp 123456` hoặc nhập trực tiếp khi được hỏi trên terminal.\n4. **File cấu hình `.ovpn`**:\n   - Nếu bạn đã export file `.ovpn` từ app OpenVPN Connect trên điện thoại, hãy đặt vào thư mục `data/csocvpn.ovpn`.\n   - Nếu chưa có file `.ovpn`, script sẽ tự động tạo file cấu hình kết nối chuẩn tới `csocvpn.fpt.net:443` (TCP/UDP).\n5. **Tự dọn dẹp (Context Manager)**: Sau khi cào xong dữ liệu HRM, VPN tự động được ngắt kết nối an toàn để trả lại đường truyền mạng bình thường.\n6. **Kiểm tra nhanh kết nối**:\n   ```bash\n   python3 scripts/test_vpn.py               # Chẩn đoán trạng thái mạng nội bộ & cấu hình VPN\n   python3 scripts/test_vpn.py --test-connect # Thử nghiệm kết nối VPN thực tế\n   ```\n\n## Biến môi trường (server đã inject hoặc cấu hình trong .env)\n\n| Biến | Vai trò |\n|---|---|\n| `HRM_USERNAME` / `HRM_PASSWORD` | credential login HRM (POST /auth) → access_token |\n| `HRM_ACCESS_TOKEN` | (tuỳ chọn) token có sẵn, bỏ qua login |\n| `HRM_EXCEL_URL` / `HRM_EXCEL_SHARE_URL` | Link file Excel đích (Sheet 1) trên SharePoint/OneDrive |\n| `HRM_EXCEL2_URL` / `HRM_EXCEL_URL2` | Link file Excel thứ hai (Sheet 2) trên SharePoint/OneDrive |\n| `HRM_SHEET_NAME` | tên sheet/tab Excel (mặc định \"Project2026\") |\n| `HRM_SHEET2_ID` | ID Google Sheet cũ (13ENSxJkc9lL43lmofw9HIxF9sdR_cElNtW2D581KIkw) |\n| `HRM_SHEET2_NAME` | tên sheet/tab Google Sheet cũ (mặc định \"FTI\") |\n| `HRM_DIVISION_CODE` | filter division (để trống = lấy tất cả division) |\n| `HRM_SHEET2_DIVISION_CODE` | filter division cho Sheet 2 (mặc định \"FTI\") |\n| `HRM_VPN_ENABLED` | Bật/tắt VPN (`auto`: tự động khi cần, `true`, `false`) |\n| `HRM_VPN_TYPE` | Loại VPN (`openvpn` cho csocvpn, hoặc `openconnect`, `openfortivpn`, `wireguard`, `ssh_tunnel`) |\n| `HRM_VPN_HOST` | Địa chỉ máy chủ VPN gateway (mặc định: `csocvpn.fpt.net`) |\n| `HRM_VPN_PORT` | Cổng máy chủ VPN (mặc định `443`) |\n| `HRM_VPN_USERNAME` | Tài khoản công ty FPT (mặc định lấy theo `HRM_USERNAME`) |\n| `HRM_VPN_PASSWORD` | Mật khẩu tài khoản (hỗ trợ mã hoá qua `HRM_PASSWORD_ENC`) |\n| `HRM_VPN_TOTP_SECRET` | Khóa bí mật Base32 từ Authenticator để **tự động tính mã OTP 6 số** |\n| `HRM_VPN_OTP` | (Tuỳ chọn) Mã OTP cố định nếu truyền qua env |\n| `HRM_VPN_CONFIG_PATH` | Đường dẫn file profile `.ovpn` (ví dụ `data/csocvpn.ovpn`) |\n| `HRM_VPN_AUTO_DISCONNECT` | Tự động ngắt VPN sau khi cào xong (`true`/`false`, mặc định `true`) |\n| `HRM_PROXY_URL` | URL proxy nội bộ nếu dùng HTTP/SOCKS proxy (ví dụ `socks5h://127.0.0.1:10808`) |\n\n## Output\n\n- File `hrm_weekly_report_vN.json` trong `$REPORT_OUTPUT_DIR` (versioned, không ghi đè):\n  - `projectCount`, `updatedCount`, `insertedCount`\n  - `updatedList` / `insertedList` (code + name từng dự án)\n  - `weekStart`, `weekEnd`, `targetType`\n\n## Schema Bảng tính Sheet Project2026 (78 cột A–BZ)\n\n> **Lưu ý an toàn dữ liệu**: 48 cột **RESOURCE** từ W đến BR (12 tháng x PM, BA, DEV, QC) và các cột **Effort / QC Defect / UAT Defect** từ S đến V được **bảo toàn 100%** (không bao giờ ghi đè).\n> **Xử lý công thức Excel**: Các cột text **N, O, R, BW, BX, BY, BZ** nếu bắt đầu bằng dấu `-` sẽ tự động thêm dấu `'` ở đầu (ví dụ: `'- Task 1...`) để tránh lỗi `#NAME?` / formula error.\n\n| Dải Cột | Tiêu đề cột trên file Excel | Dữ liệu HRM tương ứng | Ghi chú |\n|:---:|---|---|---|\n| **A (0)** | No. | STT | Giữ nguyên nếu dòng đã có, tạo mới STT tiếp theo |\n| **B (1)** | Project/Version | `displayName` | **Khóa khớp dòng (Match Key chính)** |\n| **C (2)** | Release/Sprint | `Release/Sprint` | **Giữ nguyên (Preserved)** |\n| **D (3)** | Application | `projectCode` | Cập nhật |\n| **E (4)** | Project Type | `Project Type` | **Giữ nguyên (Preserved)** (Mặc định \"Enhancement\") |\n| **F (5)** | Business Owner | `division` | **Giữ nguyên** / Mặc định \"FTI\" |\n| **G (6)** | Product Owner | `Product Owner` | **Giữ nguyên (Preserved)** |\n| **H (7)** | PM | `pm` | Cập nhật |\n| **I (8)** | Project Status | `projectPhase` | Cập nhật |\n| **J (9)** | Priority | `priority` | **Giữ nguyên nếu dòng đã có** |\n| **K (10)** | Start date (MM/dd/yyyy) | `planStartDate` | Cập nhật (hoặc giữ nguyên nếu đã có) |\n| **L (11)** | Target Go-live (MM/dd/yyyy) | `planDueDate` | Cập nhật |\n| **M (12)** | Actual Go-live (MM/dd/yyyy) | `Actual Go-live` | **Giữ nguyên (Preserved)** |\n| **N (13)** | Business Problem | `mainFeature` | Cập nhật (thêm `'` nếu bắt đầu bằng `-`) |\n| **O (14)** | Business Outcome | `goal` | Cập nhật (thêm `'` nếu bắt đầu bằng `-`) |\n| **P (15)** | Key Scope/Sprint Goal | `Key Scope/Sprint Goal` | **Giữ nguyên (Preserved)** |\n| **Q (16)** | Value Dimension | `valueCodes` | **Giữ nguyên** / Cập nhật nếu mới |\n| **R (17)** | Primary Value Metric | `valueMetric` / `businessImpact` | **Giữ nguyên** / Cập nhật nếu mới |\n| **S–V (18–21)** | Estimated/Actual Effort, QC/UAT Defect | Effort & Defect rates | **100% Giữ nguyên (Preserved)** |\n| **W–BR (22–69)** | 48 cột RESOURCE (Jan..Dec x PM, BA, DEV, QC) | Phân bổ Resource hàng tháng | **100% Giữ nguyên (Preserved)** |\n| **BS (70)** | %Done | `progress` | Cập nhật |\n| **BT (71)** | Status | `projectPhase` | Cập nhật |\n| **BU (72)** | Project Health | `projectHealth` | Cập nhật |\n| **BV (73)** | Release Date | `planDueDate` | Cập nhật |\n| **BW (74)** | This Week [Done] | `done` | Cập nhật (thêm `'` nếu bắt đầu bằng `-`) |\n| **BX (75)** | Next Week Plan [Doing/Will Do] | `continuationPlan` | Cập nhật (thêm `'` nếu bắt đầu bằng `-`) |\n| **BY (76)** | Issues & Actions | `riskOrIssues` | Cập nhật (thêm `'` nếu bắt đầu bằng `-`) |\n| **BZ (77)** | RELEASE NOTE (Output - Module - Function) | `releaseNote` | Cập nhật (thêm `'` nếu bắt đầu bằng `-`) |",
      "envVars": [
        {
          "name": "HRM_USERNAME",
          "description": "Tài khoản đăng nhập hệ thống HRM FPT (apis.fpt.net)",
          "default": "admin@hrm.fpt.net",
          "category": "HRM",
          "isSecret": false
        },
        {
          "name": "HRM_PASSWORD",
          "description": "Mật khẩu đăng nhập hệ thống HRM FPT (plain text)",
          "default": "",
          "category": "HRM",
          "isSecret": true
        },
        {
          "name": "HRM_PASSWORD_ENC",
          "description": "Mật khẩu HRM FPT đã mã hoá AES-256",
          "default": "",
          "category": "HRM",
          "isSecret": true
        },
        {
          "name": "HRM_ACCESS_TOKEN",
          "description": "(Tùy chọn) Access Token HRM có sẵn nếu không muốn login lại",
          "default": "",
          "category": "HRM",
          "isSecret": true
        },
        {
          "name": "HRM_EXCEL_URL",
          "description": "Link chia sẻ file Excel Online (SharePoint / OneDrive) cho Sheet 1 (Project2026)",
          "default": "https://fpt-my.sharepoint.com/:x:/g/personal/...",
          "category": "HRM",
          "isSecret": false
        },
        {
          "name": "HRM_EXCEL2_URL",
          "description": "Link chia sẻ file Excel Online cho Sheet 2 (nếu tách file riêng)",
          "default": "",
          "category": "HRM",
          "isSecret": false
        },
        {
          "name": "HRM_SHEET_NAME",
          "description": "Tên tab/sheet Excel cần ghi dữ liệu HRM (mặc định: Project2026)",
          "default": "Project2026",
          "category": "HRM",
          "isSecret": false
        },
        {
          "name": "HRM_SHEET2_ID",
          "description": "ID Google Sheet dự phòng cho Sheet 2 FTI",
          "default": "13ENSxJkc9lL43lmofw9HIxF9sdR_cElNtW2D581KIkw",
          "category": "HRM",
          "isSecret": false
        },
        {
          "name": "HRM_SHEET2_NAME",
          "description": "Tên tab/sheet Google Sheet 2 (mặc định: FTI)",
          "default": "FTI",
          "category": "HRM",
          "isSecret": false
        },
        {
          "name": "HRM_DIVISION_CODE",
          "description": "Mã bộ phận lọc báo cáo HRM (để trống = lấy tất cả)",
          "default": "",
          "category": "HRM",
          "isSecret": false
        },
        {
          "name": "HRM_SHEET2_DIVISION_CODE",
          "description": "Mã bộ phận lọc cho Sheet 2 (mặc định: FTI)",
          "default": "FTI",
          "category": "HRM",
          "isSecret": false
        },
        {
          "name": "HRM_VPN_ENABLED",
          "description": "Cơ chế kết nối VPN (auto: tự bật khi ngoài FPT; true: luôn bật; false: tắt)",
          "default": "auto",
          "category": "HRM VPN",
          "isSecret": false
        },
        {
          "name": "HRM_VPN_TYPE",
          "description": "Loại VPN (openvpn cho csocvpn.fpt.net, wireguard, v.v.)",
          "default": "openvpn",
          "category": "HRM VPN",
          "isSecret": false
        },
        {
          "name": "HRM_VPN_HOST",
          "description": "Địa chỉ máy chủ VPN Gateway FPT (csocvpn.fpt.net)",
          "default": "csocvpn.fpt.net",
          "category": "HRM VPN",
          "isSecret": false
        },
        {
          "name": "HRM_VPN_PORT",
          "description": "Cổng kết nối VPN Gateway (443 hoặc 1194)",
          "default": "443",
          "category": "HRM VPN",
          "isSecret": false
        },
        {
          "name": "HRM_VPN_USERNAME",
          "description": "Tài khoản VPN FPT (mặc định dùng HRM_USERNAME)",
          "default": "",
          "category": "HRM VPN",
          "isSecret": false
        },
        {
          "name": "HRM_VPN_PASSWORD",
          "description": "Mật khẩu VPN FPT",
          "default": "",
          "category": "HRM VPN",
          "isSecret": true
        },
        {
          "name": "HRM_VPN_TOTP_SECRET",
          "description": "Khóa bí mật Base32 từ Authenticator để tự động tính mã OTP 6 số",
          "default": "",
          "category": "HRM VPN",
          "isSecret": true
        },
        {
          "name": "HRM_VPN_CONFIG_PATH",
          "description": "Đường dẫn file cấu hình .ovpn (ví dụ: data/csocvpn.ovpn)",
          "default": "data/csocvpn.ovpn",
          "category": "HRM VPN",
          "isSecret": false
        },
        {
          "name": "HRM_VPN_AUTO_DISCONNECT",
          "description": "Tự động ngắt kết nối VPN sau khi cào xong (true/false)",
          "default": "true",
          "category": "HRM VPN",
          "isSecret": false
        },
        {
          "name": "GOOGLE_SERVICE_ACCOUNT_PATH",
          "description": "Đường dẫn file JSON Service Account Google Cloud để đọc/ghi Google Sheets",
          "default": "meta-gear-328801-4ff82b2ad59e.json",
          "category": "Google Sheets",
          "isSecret": false
        },
        {
          "name": "REPORT_OUTPUT_DIR",
          "description": "Thư mục xuất các file báo cáo, biểu đồ, kết quả chạy skill",
          "default": "outputs",
          "category": "System",
          "isSecret": false
        },
        {
          "name": "SKILL_DIR",
          "description": "Đường dẫn thư mục skill hiện hành (hệ thống tự inject)",
          "default": "./skills",
          "category": "System",
          "isSecret": false
        },
        {
          "name": "HRM_VPN_OTP",
          "description": "(Tùy chọn) Mã OTP cố định nếu nhập trực tiếp",
          "default": "",
          "category": "HRM VPN",
          "isSecret": false
        },
        {
          "name": "HRM_PROXY_URL",
          "description": "URL Proxy nội bộ nếu dùng proxy",
          "default": "",
          "category": "Network",
          "isSecret": false
        }
      ]
    },
    {
      "id": "jira-import",
      "name": "jira-import",
      "category": "Jira & Automation",
      "icon": "bi-upload",
      "description": "Import Sprint Backlog hoặc Waterfall Backlog từ file Excel lên Jira tự động bằng 2 script Python thuần. Skill sẽ chạy: Excel → excel_to_json.py → JSON → jira_rest_importer.py (tạo Stories + Sub-tasks). Trigger ngay khi user nói: \"import sprint backlog\", \"tạo task trên jira từ excel\", \"upload backlog lên jira\", \"import excel jira\", \"tạo sprint trên jira\", \"cập nhật backlog jira\", \"import waterfall\", hoặc gắn file Excel và nhờ tạo Jira issues.",
      "triggers": [
        "import sprint backlog",
        "tạo task trên jira từ excel",
        "upload backlog lên jira",
        "import excel jira",
        "tạo sprint trên jira",
        "cập nhật backlog jira",
        "import waterfall",
        "gắn file Excel và nhờ tạo Jira issues"
      ],
      "guidelineMarkdown": "# Jira Import (Python Scripts)\n\nSkill sử dụng **2 script Python thuần** thay vì MCP Jira tools.\nHỗ trợ **2 luồng import**:\n- 🟢 **Có Sprint (Agile)** - Story được gán vào Sprint + Epic parent\n- 🔵 **Không Sprint (Waterfall / chưa có sprint)** - Story được tạo thẳng dưới Epic, không gán sprint\n\n## Thông tin cố định\n\n| Thông số          | Giá trị                          |\n|-------------------|----------------------------------|\n| Jira Site         | foxproject.atlassian.net        |\n| Scripts           | `scripts/excel_to_json.py` và `scripts/jira_rest_importer.py` |\n| JSON tạm          | `$REPORT_OUTPUT_DIR/sprint_data.json` |\n| Jira credentials  | Biến môi trường `JIRA_EMAIL`, `JIRA_API_TOKEN` (webapp inject từ Cài đặt - KHÔNG hỏi user, KHÔNG truyền `--email`/`--api-token`) |\n\n## Quy trình\n\n```\n[Excel file] → [Bước 0: hỏi user thông tin cấu hình]\n                                    ↓\n               [Bước 1: chạy excel_to_json.py] → [output JSON]\n                                                        ↓\n                              ┌─────────────────────────┴──────────────────────────┐\n                     sprint có giá trị?                                   sprint trống / \"không\"\n                              │                                                     │\n             🟢 [Luồng AGILE] │                                  🔵 [Luồng WATERFALL]\n         Tìm Sprint ID → gán sprint                           Bỏ qua sprint → tạo Story\n         Story + Sub-tasks trong Sprint                       thẳng dưới Epic (không sprint)\n                              └─────────────────────────┬──────────────────────────┘\n                                                        ↓\n                                           [Bước 3: báo cáo kết quả]\n```\n\n---\n\n## Bước 0 - Hỏi user các giá trị cấu hình\n\n**Trước khi làm bất cứ điều gì**, hỏi user xác nhận các giá trị sau. Hỏi dưới dạng danh sách rõ ràng:\n\n> Trước khi import, bạn xác nhận các thông tin nhé:\n>\n> 1. **Project key** (ví dụ: `FCR`)\n> 2. **Parent Request** - issue cha của các Story (ví dụ: `FCR-20`)\n> 3. **Fix Version** - tên version trên Jira (ví dụ: `FTI-FCR v1.7 Sprint 3`)\n> 4. **Division** - đơn vị (ví dụ: `FTI`)\n> 5. **Loại dự án / có gán Sprint không?**\n>    - Nếu **Agile (có sprint)**: cung cấp **Sprint name** (ví dụ: `FTI-FCR V1.7 Sprint 3`)\n>    - Nếu **Waterfall** hoặc **không gán sprint**: để trống hoặc ghi `không`\n>    → Khi không có sprint, Story được tạo thẳng dưới Epic mà không cần Sprint.\n> 6. **Board name** *(chỉ cần khi Agile)* - tên Scrum board (ví dụ: `FCR board`). Bỏ trống nếu chỉ có 1 board. Cần khi sprint mới rỗng (chưa có issue) → JQL không tìm được sprint ID → dùng Agile API với board này. Nếu Waterfall → bỏ trống.\n>\n> Và tên sheet trong file Excel? (mặc định là: `Plan`)\n\nChờ user trả lời đầy đủ rồi mới chuyển sang Bước 1.\n\n### Xác định luồng sau Bước 0\n\n| Điều kiện | Luồng | SPRINT_NAME truyền vào script |\n|-----------|-------|-------------------------------|\n| User cung cấp Sprint name (không rỗng, không phải \"không\") | 🟢 **Agile** | Tên sprint thật |\n| User để trống Sprint, ghi \"không\", hoặc nói \"waterfall\" | 🔵 **Waterfall** | `\"\"` (chuỗi rỗng) |\n\nBoard name chỉ có nghĩa khi **Agile**. Nếu Waterfall → truyền `\"\"` cho cả BOARD_NAME.\n\n---\n\n## ⛔ Quy tắc bắt buộc - KHÔNG đọc file Excel\n\n**Claude KHÔNG ĐƯỢC dùng bất kỳ tool nào để đọc, mở, hoặc parse file Excel trực tiếp.**\n\n- ❌ Không dùng `view`, `bash_tool`, `create_file` hay bất kỳ tool nào để đọc nội dung file `.xlsx`\n- ❌ Không dùng Python/pandas/openpyxl trong context của Claude để đọc Excel\n- ✅ Toàn bộ dữ liệu từ Excel chỉ được lấy qua file JSON output của script ở Bước 1 - **excel_to_json.py**\n- Không dùng MCP Jira tools (`createJiraIssue`, `lookupJiraAccountId`, `searchJiraIssuesUsingJql`, …).\n\nMục đích: tránh tốn token không cần thiết. Script Python đã xử lý Excel và chuẩn hóa dữ liệu - Claude chỉ việc đọc JSON kết quả.\n\n---\n\n## Bước 1 - Chạy Python script\n\nScript nằm tại `scripts/excel_to_json.py` trong thư mục skill (`$SKILL_DIR`). Chạy bằng Bash:\n\n```bash\ncd \"$SKILL_DIR\" && python3 scripts/excel_to_json.py \\\n  \"<đường dẫn file Excel>\" \\\n  \"$REPORT_OUTPUT_DIR/sprint_data.json\" \\\n  \"<sheet name>\" \\\n  \"<PROJECT>\" \\\n  \"<PARENT_REQUEST>\" \\\n  \"<FIX_VERSION>\" \\\n  \"<DIVISION>\" \\\n  \"<SPRINT_NAME hoặc '' nếu Waterfall>\" \\\n  \"<BOARD_NAME hoặc '' nếu không dùng>\"\n```\n\nScript nhận **9 arguments** theo thứ tự:\n\n```\nargv[1] = đường dẫn file Excel\nargv[2] = đường dẫn output JSON\nargv[3] = tên sheet trong Excel\nargv[4] = PROJECT        (từ Bước 0)\nargv[5] = PARENT_REQUEST (từ Bước 0)\nargv[6] = FIX_VERSION    (từ Bước 0)\nargv[7] = DIVISION       (từ Bước 0)\nargv[8] = SPRINT_NAME    (từ Bước 0 - để \"\" nếu Waterfall/không sprint)\nargv[9] = BOARD_NAME     (từ Bước 0 - để \"\" nếu Waterfall hoặc không cần)\n```\n\n> **Quy tắc truyền SPRINT_NAME:**\n> - 🟢 Agile: truyền tên sprint thật, ví dụ `\"FTI-FCR V1.7 Sprint 3\"`\n> - 🔵 Waterfall: truyền `\"\"` - script sẽ ghi `\"sprint\": null` vào JSON → importer bỏ qua sprint\n\n**Ví dụ lệnh Waterfall:**\n```bash\ncd \"$SKILL_DIR\" && python3 scripts/excel_to_json.py \\\n  \"/path/to/project_plan.xlsx\" \\\n  \"$REPORT_OUTPUT_DIR/sprint_data.json\" \\\n  \"Plan\" \\\n  \"FCR\" \"FCR-20\" \"FTI-FCR v1.7\" \"FTI\" \"\" \"\"\n```\n\n**Lưu ý:**\n- **KHÔNG** `pip install` - dependency (`openpyxl`, `requests`…) đã cài sẵn trong `webapp/.venv-skills`.\n- **KHÔNG** `find /mnt/skills /mnt/user-data` - dùng trực tiếp `$SKILL_DIR/scripts/excel_to_json.py`.\n- Output JSON luôn ghi vào `$REPORT_OUTPUT_DIR/sprint_data.json`.\n- Script tự động nhận diện header ở dòng 8 (hoặc 6), đọc sheet `Plan` (hoặc sheet được chỉ định), tự động map Story (theo SUM/EPIC) và Sub-tasks, dừng trước section `Timeline & Milestones`.\n\nSau khi chạy, đọc output JSON (`$REPORT_OUTPUT_DIR/sprint_data.json`) và thông báo cho user:\n- Số stories và tổng số tasks tìm được\n- **Xác nhận luồng đang dùng**: 🟢 Agile (sprint: `<tên>`) hoặc 🔵 Waterfall (không sprint)\n\n---\n\n## Bước 2 - Chạy jira_rest_importer.py\n\nScript tự đọc field `\"sprint\"` từ JSON để quyết định luồng tự động:\n\n| Giá trị `\"sprint\"` trong JSON | Hành vi |\n|-------------------------------|---------|\n| `\"v3.1 Sprint 2\"` (có giá trị) | 🟢 Tìm Sprint ID → gán Story vào Sprint |\n| `null` | 🔵 Bỏ qua sprint hoàn toàn, tạo Story thẳng dưới Epic |\n\nChạy script bằng Bash - **KHÔNG truyền `--email`/`--api-token`**:\n\n```bash\ncd \"$SKILL_DIR\" && python3 scripts/jira_rest_importer.py \"$REPORT_OUTPUT_DIR/sprint_data.json\"\n```\n\nHoặc ghi đè board name (chỉ cần cho Agile khi sprint rỗng chưa có issue):\n\n```bash\ncd \"$SKILL_DIR\" && python3 scripts/jira_rest_importer.py \"$REPORT_OUTPUT_DIR/sprint_data.json\" --board-name \"<BOARD_NAME>\"\n```\n\n**Tùy chọn:**\n- `--dry-run` - chạy thử, không tạo thật (nên chạy trước nếu user yêu cầu kiểm tra).\n- `--resume` + `--state-file \"$REPORT_OUTPUT_DIR/import_state.json\"` - tiếp tục import nếu bị gián đoạn.\n\n```bash\ncd \"$SKILL_DIR\" && python3 scripts/jira_rest_importer.py \"$REPORT_OUTPUT_DIR/sprint_data.json\" --dry-run\n```\n\n**Dọn dẹp JSON sau import:** Nếu cả 2 script đều chạy thành công (exit code 0, không có dòng `[ERROR]` trong output), xóa file JSON trung gian:\n\n```bash\nrm -f \"$REPORT_OUTPUT_DIR/sprint_data.json\" \"$REPORT_OUTPUT_DIR/sprint_data.state.json\"\n```\n\nNếu import thất bại một phần hoặc có lỗi → **giữ lại** JSON để có thể `--resume` lần sau.\n\n**Xử lý thiếu credentials:** Nếu script báo lỗi `Thiếu JIRA_EMAIL / JIRA_API_TOKEN (env)` → thông báo user:\n> Chưa lưu Jira credentials. Bạn vào **Cài đặt** nhập Email Jira + API Token (tạo tại https://id.atlassian.com/manage-profile/security/api-tokens), lưu lại rồi chạy lại skill.\n\n**KHÔNG** tự hỏi user nhập email/token trực tiếp trong chat - credentials phải lưu qua Cài đặt để webapp inject an toàn qua env (không leak qua `ps`/history).\n\n---\n\n## Bước 3 - Báo cáo kết quả\n\nSau khi hoàn tất toàn bộ import, tổng hợp và trình bày kết quả theo format sau:\n\n### Dòng tóm tắt\n\n```\n✅ Import hoàn tất [🟢 Agile - Sprint: <tên sprint> | 🔵 Waterfall]: X/Y Stories thành công | Z/W Sub-tasks thành công\n```\n\n### Bảng Stories đã tạo\n\n| # | Story Key | Summary | Sub-tasks | Link |\n|---|-----------|---------|-----------|------|\n| 1 | FCR-25 | Tạo mới yêu cầu thanh lý... | 5/5 ✅ | [FCR-25](https://foxproject.atlassian.net/browse/FCR-25) |\n| 2 | FCR-26 | Phê duyệt yêu cầu... | 3/4 ⚠️ | [FCR-26](https://foxproject.atlassian.net/browse/FCR-26) |\n\nLink format: `https://foxproject.atlassian.net/browse/<issue-key>`\n\n### Cảnh báo (nếu có)\n\n**Stories thất bại** (nếu `failed_stories` không rỗng):\n```\n❌ Stories không tạo được:\n- \"Tên story\" - Lý do lỗi\n```\n\n**Sub-tasks thất bại** (nếu `failed_subtasks` không rỗng):\n```\n❌ Sub-tasks không tạo được:\n- \"Tên subtask\" (thuộc FCR-XX) - Lý do lỗi\n```\n\n**Assignee không resolve được** (nếu `unresolved_assignees` không rỗng):\n```\n⚠️ Assignee chưa gán được (sub-tasks vẫn tạo thành công, không có assignee):\n- Nguyen Van A\n- Tran Thi B\n```\n\nNếu không có lỗi và không có unresolved assignee → kết thúc bằng:\n```\n🎉 Tất cả issues đã được tạo thành công!\n```",
      "envVars": [
        {
          "name": "JIRA_EMAIL",
          "description": "Email tài khoản Jira dùng để xác thực API",
          "default": "user@company.com",
          "category": "Jira",
          "isSecret": false
        },
        {
          "name": "JIRA_API_TOKEN",
          "description": "API Token của Atlassian Jira Cloud (tạo tại Atlassian Account Settings)",
          "default": "",
          "category": "Jira",
          "isSecret": true
        },
        {
          "name": "JIRA_SITE",
          "description": "Jira Site host name hoặc base URL (ví dụ: foxproject.atlassian.net)",
          "default": "foxproject.atlassian.net",
          "category": "Jira",
          "isSecret": false
        },
        {
          "name": "REPORT_OUTPUT_DIR",
          "description": "Thư mục xuất các file báo cáo, biểu đồ, kết quả chạy skill",
          "default": "outputs",
          "category": "System",
          "isSecret": false
        },
        {
          "name": "HTTP_PROXY",
          "description": "Proxy HTTP mạng nội bộ doanh nghiệp",
          "default": "http://proxy.hcm.fpt.vn:80",
          "category": "Network",
          "isSecret": false
        },
        {
          "name": "HTTPS_PROXY",
          "description": "Proxy HTTPS mạng nội bộ doanh nghiệp",
          "default": "http://proxy.hcm.fpt.vn:80",
          "category": "Network",
          "isSecret": false
        },
        {
          "name": "SKILL_DIR",
          "description": "Đường dẫn thư mục skill hiện hành (hệ thống tự inject)",
          "default": "./skills",
          "category": "System",
          "isSecret": false
        }
      ]
    },
    {
      "id": "jira-story-today-reviewer",
      "name": "jira-story-today-reviewer",
      "category": "Jira & Automation",
      "icon": "bi-clock-history",
      "description": "Rà soát các Story Jira có Start Date là hôm nay đang ở trạng thái To Do và hỗ trợ chuyển sang In Progress.",
      "triggers": [],
      "guidelineMarkdown": "# Jira Story Today Reviewer & In Progress Starter\n\nKỹ năng tự động rà soát toàn bộ các Story có ngày bắt đầu (`Start Date`) là hôm nay và đang ở trạng thái `To Do` do người dùng tạo trên Jira Cloud, đồng thời hỗ trợ chuyển nhanh toàn bộ sang `In Progress`.\n\n## Mục Tiêu & Nghiệp Vụ\n- **JQL Truy Vấn:**\n  ```sql\n  type = Story and creator = currentUser() and status = \"To Do\" and \"start date[date]\" = \"{today}\" ORDER BY \"cf[10015]\" ASC, created DESC\n  ```\n- **Phạm Vi Lấy Dữ Liệu:**\n  - Lấy các Story có `status = \"To Do\"` (hoặc biến thể `statusCategory = \"To Do\"`) có ngày bắt đầu là hôm nay (mặc định lấy theo ngày hiện tại của hệ thống, hoặc ngày người dùng chỉ định).\n- **Nút Chuyển In Progress Nhanh:**\n  - Cung cấp nút xác nhận chuyển trạng thái toàn bộ các Story này sang `In Progress` để bắt đầu làm việc.\n\n---\n\n## Quy Trình Thực Thi (BẮT BUỘC)\n\n> ⚠️ **QUY TẮC THỰC THI QUAN TRỌNG:**\n> - **Chạy lệnh đồng bộ:** Khi gọi tool Bash/run_command, luôn chạy lệnh trực tiếp và đợi kết quả hoàn tất trong cùng một lượt. KHÔNG chạy ngầm hay background.\n> - **KHÔNG gửi tin nhắn dở dang trước khi chạy:** Tuyệt đối KHÔNG xuất các câu thông báo trung gian như *\"Đang tiến hành chạy pipeline rà soát...\"* rồi dừng/kết thúc lượt. Bạn phải gọi tool Bash ngay lập tức và chỉ trả lời duy nhất một tin nhắn sau khi pipeline đã tạo xong file báo cáo.\n\n### Bước 1: Chạy Pipeline Python (MỘT Lệnh Bash Duy Nhất)\nWebapp đã tự cấp quyền chạy bash trong sandbox. Trợ lý AI thực thi 1 lệnh duy nhất:\n\n```bash\ncd \"$SKILL_DIR\" && python3 scripts/run_story_today_check.py --output-dir \"$REPORT_OUTPUT_DIR\"\n```\n\n- Nếu người dùng chỉ định ngày cụ thể (ví dụ: `2026-09-16`), truyền thêm tham số:\n  ```bash\n  cd \"$SKILL_DIR\" && python3 scripts/run_story_today_check.py --output-dir \"$REPORT_OUTPUT_DIR\" --date \"2026-09-16\"\n  ```\n- Nếu người dùng muốn lọc theo Project Key hoặc Creator cụ thể:\n  ```bash\n  cd \"$SKILL_DIR\" && python3 scripts/run_story_today_check.py --output-dir \"$REPORT_OUTPUT_DIR\" --project-key \"PROJ\" --creator \"duyvm4\"\n  ```\n\n---\n\n### Bước 2: Đọc Tóm Tắt Kết Quả & Phản Hồi Ngắn Gọn\nSau khi script hoàn thành, đọc nhanh file kết quả JSON hoặc MD trong `$REPORT_OUTPUT_DIR` để lấy số liệu tổng kết.\n\n### Bước 3: Xuất Báo Cáo Tóm Tắt Trong Chat (TIẾT KIỆM TOKEN)\n> ⚠️ **QUY TẮC BẮT BUỘC:** File `.md` chi tiết (kèm bảng danh sách đầy đủ Story, Assignee, Priority, Estimate, Due Date) đã được sinh tự động trong `$REPORT_OUTPUT_DIR`. Webapp sẽ tự động phát hiện tên file để người dùng xem preview ở panel bên phải hoặc tải về. **TUYỆT ĐỐI KHÔNG in lại toàn bộ nội dung hay bảng danh sách chi tiết của file `.md` ra tin nhắn AI** nhằm tiết kiệm tối đa token.\n\nChỉ trả lời ngắn gọn (5-7 dòng) theo mẫu chuẩn sau:\n\n```markdown\n### 🚀 Hoàn Tất Rà Soát Story Bắt Đầu Hôm Nay ({today_date})\n\n- **Phạm vi kiểm tra:** Story có Start Date là `{today_date}` và trạng thái `To Do`\n- **Tổng số Story tìm thấy:** **{total_stories}** Story\n- **Tổng quỹ thời gian Estimate:** **{total_est}h**\n- **File báo cáo chi tiết:** `story_today_review_v{N}.md` *(nhấp vào file chip để xem danh sách chi tiết)*\n\n👉 *Gợi ý:* Nhấn nút **`Xác nhận chuyển In Progress các Story hôm nay`** bên dưới để chuyển trạng thái In Progress cho tất cả **{total_stories}** Story trên Jira.\n```\n\n---\n\n### Bước 4: Xử Lý Chuyển In Progress (Khi Người Dùng Xác Nhận)\nKhi người dùng bấm nút xác nhận trên giao diện hoặc gửi yêu cầu (ví dụ: *\"chuyển in progress\"*, *\"đánh in progress\"*, *\"start in progress\"*, *\"xác nhận chuyển in progress tất cả story\"*):\n\n1. **Trợ lý AI thực thi script transition bằng MỘT lệnh Bash duy nhất:**\n   ```bash\n   cd \"$SKILL_DIR\" && python3 scripts/transition_stories_inprogress.py --output-dir \"$REPORT_OUTPUT_DIR\"\n   ```\n2. **Đọc tóm tắt file kết quả:**\n   Script sẽ tự động tìm transition `In Progress` và chuyển trạng thái trên Jira, lưu file `story_inprogress_v{N}.json` + `story_inprogress_v{N}.md`.\n3. **Xuất phản hồi ngắn gọn trong chat (TIẾT KIỆM TOKEN):**\n   > ⚠️ **TUYỆT ĐỐI KHÔNG in lại toàn bộ bảng chi tiết ra tin nhắn.** Chỉ trả lời ngắn gọn:\n   ```markdown\n   ### ✅ Đã Chuyển Trạng Thái In Progress Thành Công ({success_count}/{total_processed})\n\n   - **Tổng số Story đã xử lý:** {total_processed}\n   - **Chuyển sang In Progress thành công:** **{success_count}** Story\n   - **Thất bại:** {fail_count} Story\n   - **Báo cáo chi tiết:** `story_inprogress_v{N}.md` *(nhấp vào file chip để xem chi tiết trạng thái từng Story)*\n   ```",
      "envVars": [
        {
          "name": "JIRA_EMAIL",
          "description": "Email tài khoản Jira dùng để xác thực API",
          "default": "user@company.com",
          "category": "Jira",
          "isSecret": false
        },
        {
          "name": "JIRA_API_TOKEN",
          "description": "API Token của Atlassian Jira Cloud (tạo tại Atlassian Account Settings)",
          "default": "",
          "category": "Jira",
          "isSecret": true
        },
        {
          "name": "JIRA_SITE",
          "description": "Jira Site host name hoặc base URL (ví dụ: foxproject.atlassian.net)",
          "default": "foxproject.atlassian.net",
          "category": "Jira",
          "isSecret": false
        },
        {
          "name": "JIRA_PROJECT_KEY",
          "description": "Mã Project Key Jira mặc định (ví dụ: FCR, FSM, ISC, SAL)",
          "default": "FCR",
          "category": "Jira",
          "isSecret": false
        },
        {
          "name": "REPORT_OUTPUT_DIR",
          "description": "Thư mục xuất các file báo cáo, biểu đồ, kết quả chạy skill",
          "default": "outputs",
          "category": "System",
          "isSecret": false
        },
        {
          "name": "SKILL_DIR",
          "description": "Đường dẫn thư mục skill hiện hành (hệ thống tự inject)",
          "default": "./skills",
          "category": "System",
          "isSecret": false
        }
      ]
    },
    {
      "id": "jira-subtask-reviewer",
      "name": "jira-subtask-reviewer",
      "category": "Jira & Automation",
      "icon": "bi-check2-all",
      "description": "Rà soát các sub-task Jira (status In Review, Original Estimate == Time Spent) theo tuần hoặc khoảng ngày.",
      "triggers": [],
      "guidelineMarkdown": "# Jira Sub-task Reviewer\n\nKỹ năng tự động rà soát toàn bộ các sub-task có trạng thái `In Review` trên Jira Cloud theo phạm vi thời gian (mặc định Thứ 2 – Thứ 6 tuần hiện tại, hoặc khoảng ngày tùy biến).\n\n## Mục Tiêu & Nghiệp Vụ\n- **JQL Truy Vấn:**\n  ```sql\n  due >= \"{from_date}\" and due <= \"{to_date}\" and type IN subTaskIssueTypes() and creator = currentUser() ORDER BY \"cf[10015]\" ASC, created DESC\n  ```\n- **Phạm Vi Lấy Dữ Liệu:**\n  - Lấy **TOÀN BỘ** các sub-task có `status = inreview` (hoặc các biến thể: In Review, Ready for Review, QA, In QA...).\n- **Phân Loại & Đánh Giá:**\n  1. **🟢 Khớp 100% (Original Estimate == Time Spent > 0):**\n     - Sub-task đã hoàn thành 100% thời gian estimate và đang chờ hoàn tất.\n     - **Đây là nhóm duy nhất đủ điều kiện chuyển trạng thái khi bấm nút xác nhận đánh Done.**\n  2. **🔥 Lệch Giờ Cần Highlight (Original Estimate != Time Spent):**\n     - Đánh dấu nổi bật để PM/Tech Lead lưu ý:\n       - Sub-task chưa estimate hoặc chưa log time.\n       - Sub-task log thiếu giờ (`Spent < Est`).\n       - Sub-task vượt estimate (`Spent > Est`).\n- **Nút Xác Nhận Đánh Done:**\n  - Nút xác nhận trên UI và script transition **chỉ áp dụng đánh Done cho nhóm task có Est == Spent**. Các task lệch giờ sẽ được giữ nguyên trạng thái để đối soát.\n\n---\n\n## Quy Trình Thực Thi (BẮT BUỘC)\n\n### Bước 1: Chạy Pipeline Python (MỘT Lệnh Bash Duy Nhất)\nWebapp đã tự cấp quyền chạy bash trong sandbox. Trợ lý AI thực thi 1 lệnh duy nhất:\n\n```bash\ncd \"$SKILL_DIR\" && python3 scripts/run_subtask_check.py --output-dir \"$REPORT_OUTPUT_DIR\"\n```\n\n- Nếu người dùng chỉ định khoảng ngày cụ thể (ví dụ: `2026-09-01` đến `2026-09-30`), truyền thêm tham số:\n  ```bash\n  cd \"$SKILL_DIR\" && python3 scripts/run_subtask_check.py --output-dir \"$REPORT_OUTPUT_DIR\" --from-date \"2026-09-01\" --to-date \"2026-09-30\"\n  ```\n- Nếu người dùng muốn lọc theo Project Key hoặc Creator cụ thể:\n  ```bash\n  cd \"$SKILL_DIR\" && python3 scripts/run_subtask_check.py --output-dir \"$REPORT_OUTPUT_DIR\" --project-key \"PROJ\" --creator \"currentUser()\"\n  ```\n\n---\n\n### Bước 2: Đọc Tóm Tắt Kết Quả & Phản Hồi Ngắn Gọn\nSau khi script hoàn thành, đọc nhanh file kết quả JSON hoặc MD trong `$REPORT_OUTPUT_DIR` để lấy số liệu tổng kết.\n\n### Bước 3: Xuất Báo Cáo Tóm Tắt Trong Chat (TIẾT KIỆM TOKEN)\n> ⚠️ **QUY TẮC BẮT BUỘC:** File `.md` chi tiết (kèm bảng danh sách đầy đủ, bảng highlight lệch giờ và bảng task sẵn sàng Done) đã được sinh tự động trong `$REPORT_OUTPUT_DIR`. Webapp sẽ tự động phát hiện tên file để người dùng xem preview ở panel bên phải hoặc tải về. **TUYỆT ĐỐI KHÔNG in lại toàn bộ nội dung hay bảng danh sách chi tiết của file `.md` ra tin nhắn AI** nhằm tiết kiệm tối đa token.\n\nChỉ trả lời ngắn gọn (5-7 dòng) theo mẫu chuẩn sau:\n\n```markdown\n### 🔍 Hoàn Tất Rà Soát Sub-task Jira In Review ({from_date} – {to_date})\n\n- **Tổng sub-task In Review:** **{total_inreview}** sub-task (Tổng Est: {total_est}h | Log: {total_spent}h)\n- **🟢 Khớp 100% (Est == Spent):** **{total_done_eligible}** sub-task *(Sẵn sàng đánh Done)*\n- **🔥 Lệch giờ cần Highlight (Est != Spent):** **{total_discrepancy}** sub-task *(Cần đối soát log time)*\n- **File báo cáo chi tiết:** `subtask_review_v{N}.md` *(nhấp vào file chip để xem bảng highlight chi tiết)*\n\n👉 *Gợi ý:* Nhấn nút **`Xác nhận đánh Done tất cả sub-task`** bên dưới để chuyển trạng thái Done cho **{total_done_eligible}** sub-task đã khớp 100% estimate (các task lệch giờ sẽ được giữ nguyên).\n```\n\n---\n\n### Bước 4: Xử Lý Đánh Done Sub-task (Khi Người Dùng Xác Nhận)\nKhi người dùng bấm nút xác nhận đánh Done trên giao diện hoặc gửi yêu cầu (ví dụ: *\"đánh done\"*, *\"chuyển sang done\"*, *\"xác nhận đánh done tất cả sub-task này\"*, *\"mark done\"*):\n\n1. **Trợ lý AI thực thi script transition bằng MỘT lệnh Bash duy nhất:**\n   ```bash\n   cd \"$SKILL_DIR\" && python3 scripts/transition_subtasks_done.py --output-dir \"$REPORT_OUTPUT_DIR\"\n   ```\n2. **Đọc tóm tắt file kết quả:**\n   Script sẽ tự động lọc chỉ chuyển trạng thái những sub-task có `Est == Spent > 0` sang `Done` trên Jira và lưu file `subtask_done_v{N}.json` + `subtask_done_v{N}.md`.\n3. **Xuất phản hồi ngắn gọn trong chat (TIẾT KIỆM TOKEN):**\n   > ⚠️ **TUYỆT ĐỐI KHÔNG in lại toàn bộ bảng chi tiết ra tin nhắn.** Chỉ trả lời ngắn gọn:\n   ```markdown\n   ### ✅ Đã Chuyển Trạng Thái Done Thành Công ({success_count}/{total_processed})\n\n   - **Tổng số sub-task đã xử lý:** {total_processed} (các task có Est == Spent)\n   - **Chuyển sang Done thành công:** **{success_count}** sub-task\n   - **Thất bại:** {fail_count} sub-task\n   - **Báo cáo chi tiết:** `subtask_done_v{N}.md` *(nhấp vào file chip để xem chi tiết trạng thái từng sub-task)*\n   ```",
      "envVars": [
        {
          "name": "JIRA_EMAIL",
          "description": "Email tài khoản Jira dùng để xác thực API",
          "default": "user@company.com",
          "category": "Jira",
          "isSecret": false
        },
        {
          "name": "JIRA_API_TOKEN",
          "description": "API Token của Atlassian Jira Cloud (tạo tại Atlassian Account Settings)",
          "default": "",
          "category": "Jira",
          "isSecret": true
        },
        {
          "name": "JIRA_SITE",
          "description": "Jira Site host name hoặc base URL (ví dụ: foxproject.atlassian.net)",
          "default": "foxproject.atlassian.net",
          "category": "Jira",
          "isSecret": false
        },
        {
          "name": "JIRA_PROJECT_KEY",
          "description": "Mã Project Key Jira mặc định (ví dụ: FCR, FSM, ISC, SAL)",
          "default": "FCR",
          "category": "Jira",
          "isSecret": false
        },
        {
          "name": "REPORT_OUTPUT_DIR",
          "description": "Thư mục xuất các file báo cáo, biểu đồ, kết quả chạy skill",
          "default": "outputs",
          "category": "System",
          "isSecret": false
        },
        {
          "name": "SKILL_DIR",
          "description": "Đường dẫn thư mục skill hiện hành (hệ thống tự inject)",
          "default": "./skills",
          "category": "System",
          "isSecret": false
        }
      ]
    },
    {
      "id": "outlook-digest",
      "name": "outlook-digest",
      "category": "Communication & Office",
      "icon": "bi-envelope-paper",
      "description": "\"Đọc email Outlook/Office 365 qua Microsoft Graph API (MSAL / token cache) hoặc IMAP, redact/mã hoá nội dung nhạy cảm, và tổng hợp theo yêu cầu người dùng. Sử dụng khi cần: tổng hợp email, digest Outlook, recap inbox, tóm tắt mail tuần, theo dõi thread email dự án. Trigger khi user nói: đọc outlook, tổng hợp email outlook, digest outlook, recap inbox outlook, tóm tắt email, mail tuần này, email từ khách hàng, hay bất kỳ yêu cầu nào liên quan đến đọc và tổng hợp Outlook.\"",
      "triggers": [
        "đọc outlook",
        "tổng hợp email outlook",
        "digest outlook",
        "recap inbox outlook",
        "tóm tắt email",
        "mail tuần này",
        "email từ khách hàng"
      ],
      "guidelineMarkdown": "# Outlook Digest\n\nSkill đọc email Outlook / Office 365 qua **Microsoft Graph REST API** (cơ chế xác thực MSAL Device Flow / token cache ) hoặc IMAP Exchange dự phòng, **tự động redact + mã hoá** nội dung nhạy cảm (password, OTP, token, số thẻ, lương...) trước khi AI xử lý.\n\n## Quy tắc bảo mật (BẮT BUỘC)\n\n1. **CHỈ Read** file `*_safe.json` và `*_meta.json` trong `$REPORT_OUTPUT_DIR`\n2. **CẤM Read** file `*_vault.enc` - chứa nội dung gốc đã mã hoá, AI không được truy cập\n3. **CẤM** cố decode placeholder `[REDACTED:ref:reason]` hoặc vault\n4. Khi tổng hợp, **không suy diễn** nội dung đã redact - chỉ ghi \"nội dung nhạy cảm đã ẩn\"\n5. Kết nối Outlook: Ưu tiên dùng Microsoft Graph API qua tài khoản Office 365 / `token_cache.bin` (hoặc cấu hình App Password IMAP trong Cài đặt webapp)\n\n## Quy trình\n\n### Bước 0 - Kiểm tra yêu cầu user\n\nThu thập (hỏi 1 lần nếu thiếu):\n- **Phạm vi thời gian** (mặc định 7 ngày)\n- **Bộ lọc** (từ khóa, người gửi, subject)\n- **Mục tiêu tổng hợp** (VD: \"email về sprint FSM\", \"mail khách hàng cần follow-up\")\n\n### Bước 1 - Fetch (1 lệnh Bash)\n\n> ⚠️ **FORMAT BẮT BUỘC** - guardrail chặn nếu thiếu prefix:\n\n```bash\ncd \"$SKILL_DIR\" && python3 scripts/run_outlook_digest.py \\\n  --days 7 --max-results 30 \\\n  --query \"sprint OR client\" \\\n  --user-request \"Tổng hợp email sprint FSM, liệt kê action items\" \\\n  --output-dir \"$REPORT_OUTPUT_DIR\"\n```\n\n| Tham số | Mô tả |\n|---------|-------|\n| `--days N` | Email N ngày gần nhất |\n| `--max-results N` | Giới hạn số mail (mặc định 30) |\n| `--query \"...\"` | Từ khóa tìm kiếm |\n| `--from-addr \"x@y.com\"` | Lọc người gửi |\n| `--subject \"...\"` | Lọc tiêu đề |\n| `--user-request \"...\"` | Yêu cầu tổng hợp - ghi vào safe JSON |\n| `--slug name` | Prefix file output (mặc định `outlook_digest`) |\n\n### Bước 2 - Read safe JSON\n\n> ⚠️ **CẤM** `wc`, `cat`, `python3 -c` để đọc JSON - guardrail chặn hoặc không cần thiết.  \n> **CHỈ dùng tool Read** file trong `$REPORT_OUTPUT_DIR`:\n\n```\noutlook_digest_v1_safe.json   ← nội dung email đã redact\noutlook_digest_v1_meta.json   ← stats (total_messages, sensitive_messages, …)\n```\n\nKhông cần đếm dòng hay parse JSON bằng Bash - Read xong tổng hợp trực tiếp.\n\nFile safe chứa:\n- Metadata email (from, date, subject - giữ visible, chỉ redact pattern secret thực sự)\n- Body/snippet đã redact - placeholder `[REDACTED:ref:reason]` thay cho nội dung nhạy cảm\n- `stats.sensitive_messages` - số mail có redaction\n- `user_request` - yêu cầu tổng hợp\n\n### Bước 3 - Tổng hợp + Write report\n\n1. Read `$SKILL_DIR/assets/output_template.md` (format gợi ý)\n2. Phân nhóm email theo chủ đề/thread\n3. Tóm tắt theo `user_request`\n4. **Write** `outlook_digest_vN_summary.md` vào `$REPORT_OUTPUT_DIR`\n\n## Nội dung được coi là nhạy cảm (auto-redact)\n\n| Loại | Ví dụ |\n|------|-------|\n| Password | `password: xxx`, `mật khẩu: xxx` |\n| OTP/PIN | `OTP: 123456`, `mã xác thực` |\n| API token | `sk-...`, `ghp_...`, `Bearer ...` |\n| Private key | `-----BEGIN PRIVATE KEY-----` |\n| Số thẻ | 13-19 chữ số (Luhn valid) |\n| Lương/thu nhập | `lương: 30 triệu`, `salary:` |\n| STK ngân hàng | `STK: 1234567890` |\n| Subject nhạy cảm | password, payroll, confidential, NDA... → redact toàn body, **giữ subject visible** (để nhận diện email) |\n\n## Môi trường runtime (webapp)\n\n- **KHÔNG** `pip install` - dùng `.venv-skills` (requests, cryptography, msal)\n- **KHÔNG** `curl` test Outlook thủ công\n- **KHÔNG** Read `*_vault.enc`\n- **KHÔNG** `wc` / `cat` / `python3 -c` để đọc JSON - **CHỈ tool Read** `*_safe.json` / `*_meta.json`\n- Env có sẵn: `OUTLOOK_ACCESS_TOKEN`, `OUTLOOK_VAULT_KEY`, `REPORT_OUTPUT_DIR`, `SKILL_DIR`\n\n## Giao tiếp với user\n\n- Không tường thuật chi tiết kỹ thuật redact/vault\n- Báo 2 mốc: đang fetch → kết quả (tên file summary + số email + số mail redact)\n- Nếu chưa kết nối Outlook → hướng dẫn đăng nhập Microsoft Graph (Device Flow) hoặc Cài đặt webapp",
      "envVars": [
        {
          "name": "OUTLOOK_EMAIL",
          "description": "Email tài khoản Microsoft Outlook / Office 365",
          "default": "user@company.com",
          "category": "Outlook",
          "isSecret": false
        },
        {
          "name": "OUTLOOK_PASSWORD",
          "description": "Mật khẩu ứng dụng (App Password) hoặc IMAP Password của Outlook",
          "default": "",
          "category": "Outlook",
          "isSecret": true
        },
        {
          "name": "OUTLOOK_IMAP_SERVER",
          "description": "Địa chỉ máy chủ IMAP Outlook",
          "default": "outlook.office365.com",
          "category": "Outlook",
          "isSecret": false
        },
        {
          "name": "OUTLOOK_IMAP_PORT",
          "description": "Cổng kết nối IMAP SSL",
          "default": "993",
          "category": "Outlook",
          "isSecret": false
        },
        {
          "name": "MS_GRAPH_ACCESS_TOKEN",
          "description": "Access Token của Microsoft Graph API",
          "default": "",
          "category": "Outlook",
          "isSecret": true
        },
        {
          "name": "OUTLOOK_ACCESS_TOKEN",
          "description": "OAuth2 Modern Auth Access Token từ Microsoft Graph API",
          "default": "",
          "category": "Outlook",
          "isSecret": true
        },
        {
          "name": "OUTLOOK_VAULT_KEY",
          "description": "Khóa mã hóa an toàn nội dung email vault trước khi gửi AI",
          "default": "",
          "category": "Security",
          "isSecret": true
        },
        {
          "name": "REPORT_OUTPUT_DIR",
          "description": "Thư mục xuất các file báo cáo, biểu đồ, kết quả chạy skill",
          "default": "outputs",
          "category": "System",
          "isSecret": false
        },
        {
          "name": "SKILL_DIR",
          "description": "Đường dẫn thư mục skill hiện hành (hệ thống tự inject)",
          "default": "./skills",
          "category": "System",
          "isSecret": false
        }
      ]
    },
    {
      "id": "pm-sprint-summary",
      "name": "pm-sprint-summary",
      "category": "Agile & Management",
      "icon": "bi-journal-check",
      "description": "\"Tổng hợp task list thô (backlog, Jira export dạng text, ghi chú sprint dán tay) thành báo cáo PM Sprint Summary rút gọn, sạch, theo góc nhìn Project Manager - dùng để gửi PO/PMO/Sponsor/Steering Committee hoặc báo cáo tuần nói chung. Dùng skill này bất cứ khi nào user dán một danh sách task có kèm Jira ID, tên account, % tiến độ và muốn có bản tóm tắt sạch, loại bỏ ID/tên người thực hiện/chi tiết kỹ thuật. Trigger khi user nói: 'tổng hợp sprint summary', 'làm PM sprint summary', 'tóm tắt task cho sếp', 'báo cáo PO/PMO', 'báo cáo steering committee', 'rút gọn báo cáo tuần', 'chuyển task list này thành báo cáo', hoặc dán một khối task có Jira ID kèm yêu cầu tóm tắt/report - kể cả khi không dùng đúng các từ khóa trên.\"",
      "triggers": [
        "tổng hợp sprint summary",
        "làm PM sprint summary",
        "tóm tắt task cho sếp",
        "báo cáo PO/PMO",
        "báo cáo steering committee",
        "rút gọn báo cáo tuần",
        "chuyển task list này thành báo cáo"
      ],
      "guidelineMarkdown": "# PM Sprint Summary\n\nChuyển đổi task list thô (backlog, Jira export dán tay, ghi chú sprint) thành **một bản báo cáo rút gọn duy nhất** theo góc nhìn Senior IT Project Manager, dùng để gửi PO, PMO, Sponsor hoặc Steering Committee.\n\n---\n\n## Quy tắc làm sạch\n\n- Loại bỏ toàn bộ Jira ID (FSM-xxx, FCR-xxx, DEV-xxx, PROJ-xxx...)\n- Loại bỏ tên account/người thực hiện (kể cả trong ngoặc đơn ở cuối dòng)\n- Loại bỏ thông tin kỹ thuật không cần thiết (issuetype Story/Task/Subtask, trạng thái Jira chi tiết...)\n- **Dấu tiếng Việt**: source từ Jira/Excel thường bị gõ KHÔNG dấu - viết lại output TIẾNG VIỆT CÓ DẤU ĐÚNG (VD \"theo doi tien do\" → \"theo dõi tiến độ\", \"chuan bi\" → \"chuẩn bị\", \"tong ket\" → \"tổng kết\", \"rui ro\" → \"rủi ro\"). Tái cấu trúc dấu cho mọi câu tiếng Việt.\n- Gộp các task liên quan thành **1 dòng ý gộp** theo kết quả nghiệp vụ - không chia thành nhiều cụm/tiêu đề con\n- **TỔNG HỢP & VIẾT LẠI CÔ ĐỌNG (Synthesize / Paraphrase)**: Giữ nguyên vẹn cụm danh từ chỉ kết quả/deliverable, đảm bảo câu văn gãy gọn, đủ nghĩa và đúng chuẩn ngữ pháp PM (khoảng **3–8 từ/dòng**, tuyệt đối không quá 10 từ).\n- **TUYỆT ĐỐI KHÔNG ĐỂ CÂU DÀI THÔ & KHÔNG CẮT CỤT CƠ HỌC**:\n  - **Không** giữ nguyên câu dài 12–20 từ từ Jira/Backlog vào bản tóm tắt.\n  - **Không** ngắt cứng cơ học tại số từ cố định làm đứt đoạn từ ghép / ngữ nghĩa / bổ ngữ cuối câu (ví dụ: không để câu bị cụt lửng như `... log server & Hỗ`, `... Phê duyệt điều kiện`, `... Test Scenarios chi tiết cho`, `... thực hiện kiểm thử chức`).\n\n#### 💡 Bảng đối chiếu viết lại (Synthesize vs Lỗi câu dài / Cắt cụt cơ học):\n| Input thô từ Jira / File .md | ❌ Lỗi câu dài / Hard Truncation | ✅ Viết lại chuẩn PM (Synthesize 3–8 từ) |\n| :--- | :--- | :--- |\n| *Hỗ trợ nghiệp vụ cho DEV và QC, chuẩn bị kịch bản UAT và tài liệu HDSD...* | `- Hỗ trợ nghiệp vụ cho DEV và QC, chuẩn bị` *(Cụt chữ)*<br>`- Hỗ trợ nghiệp vụ cho DEV và QC, chuẩn bị tài liệu bàn giao UAT` *(Quá dài)* | `- Nghiệm thu UAT & tài liệu HDSD` *(7 từ)* |\n| *Chuẩn bị test case và thực hiện kiểm thử chức năng cho Sprint 4...* | `- Chuẩn bị test case và thực hiện kiểm thử chức` *(Cụt chữ)*<br>`- Chuẩn bị test case & thực hiện kiểm thử chức năng phân hệ ZNS` *(Quá dài)* | `- Kiểm thử chức năng Sprint 4` *(5 từ)* |\n| *Chuẩn bị môi trường và tài liệu phục vụ CSOC Pentest...* | `- Chuẩn bị môi trường và tài liệu phục vụ CSOC` *(Cụt chữ)* | `- Chuẩn bị môi trường Pentest CSOC` *(5 từ)* |\n| *Hỗ trợ CSOC pentest và phân loại các lỗ hổng bảo mật phát hiện được...* | `- Hỗ trợ CSOC pentest và phân loại các lỗ hổng` *(Cụt chữ)* | `- Hỗ trợ Pentest & phân loại lỗ hổng` *(7 từ)* |\n| *Thực hiện Unit test, deploy staging và fix bug trong quá trình...* | `- Thực hiện Unit test, deploy staging và fix bug` *(Cụt chữ)* | `- Deploy Staging & xử lý lỗi QC` *(7 từ)* |\n| *Deploy bản build hoàn thiện Sprint 2 lên môi trường Staging và nghiệm thu nội bộ...* | `- Deploy bản build hoàn thiện Sprint 2 lên môi trường Staging và nghiệm thu nội bộ` *(Quá dài: 16 từ)* | `- Nghiệm thu bản build Sprint 2 Staging` *(7 từ)* |\n\n- Viết theo góc nhìn PM, ưu tiên kết quả/nghiệp vụ hơn chi tiết kỹ thuật\n- Mỗi dòng tối đa 1 câu, ngắn gọn súc tích (khoảng 3–8 từ, tối đa 10 từ), ưu tiên dạng danh ngữ. Bắt buộc có dấu gạch đầu dòng `- ` ở đầu mỗi dòng.\n\n### Quy tắc riêng cho mục DONE\n- Viết dạng danh ngữ hoặc kết quả đã đạt được\n- Không ghi \"(Done)\"\n\n### Quy tắc riêng cho mục DOING / WILL DO\n- Tập trung vào việc cần làm và kế hoạch tiếp theo\n- Không giữ %, chỉ giữ mốc due date/sự kiện quan trọng nếu có (ví dụ \"Sprint Review ngày 06/08\")\n- Nếu có due date quá hạn (due date <= hôm nay và task chưa Done) → thêm cảnh báo `⚠️ Trễ hạn {ngày}`\n\n### Quy tắc riêng cho Risks & Issues\n- Tóm tắt tối đa 1 câu/rủi ro, ưu tiên rủi ro ảnh hưởng tiến độ chung hoặc go-live\n- Ưu tiên các dấu hiệu: task quá hạn, SPI thấp, capacity overload, testing/QC delay\n\n### Giới hạn độ dài\n- Mỗi mục (Done / Doing-Will do / Risks) TỐI ĐA ~5 DÒNG - BẮT BUỘC. Nếu input có nhiều task, GỘP các task liên quan thành 1 dòng ý nghiệp vụ, KHÔNG liệt kê từng task. Vượt 5 dòng → gộp thêm cho đến khi ≤5. Ưu tiên ngắn gọn và thông tin có tác động tới quyết định của người nhận (PO/PMO/Sponsor), gộp nhiều task liên quan thành 1 dòng\n\n---\n\n## Header tùy chọn - Overall Status\n\nNếu user cung cấp (hoặc đã có sẵn trong hội thoại) các thông tin: tên dự án/sprint, ngày báo cáo, health status, Planned/Actual Progress, SPI, RAG % - thêm header này lên **đầu output**, trước mục \"✅ Done\". Nếu user không cung cấp số liệu này, **bỏ qua header, không tự bịa số liệu**.\n\nChỉ tóm tắt các ý chính bằng gạch đầu dòng, **không dùng bảng markdown**:\n\n```\n{Tên dự án} · {Tên Sprint} - {ngày bắt đầu} – {ngày kết thúc}\n\n- Health: {🟢 On Track / 🟡 At Risk / 🔴 Off Track} (SPI = {X.XX})\n- Tiến độ: {Actual X%} / kế hoạch {Planned X%}\n- Đúng hạn (RAG): {X%}\n\n---\n```\n\nQuy tắc:\n- Header là **bổ sung**, không thay thế phần \"✅ Done / ▶ Doing-Will do / ⚠️ Risks & Issues\" phía sau.\n- Số liệu do user cung cấp trực tiếp hoặc lấy sẵn từ report khác (ví dụ đã tính trong skill `weekly-report`) - skill này chỉ format lại, không tự tính SPI/Weighted Progress.\n- Nếu chỉ có một phần số liệu → vẫn thêm header nhưng bỏ dòng thiếu, không để trống hoặc ghi \"N/A\".\n- Không liệt kê breakdown theo từng phase (Requirement/Development/Testing/...) - chỉ giữ % tổng thể.\n\n---\n\n## Format output\n\n```\n✅ Done\n- Kết quả nghiệp vụ 1 (gộp nhiều task liên quan thành 1 dòng)\n- Kết quả nghiệp vụ 2\n\n▶ Doing / Will do\n- Việc đang làm/kế hoạch tiếp theo, giữ mốc due date/sự kiện quan trọng nếu có\n- ...\n\n⚠️ Risks & Issues\n- Rủi ro quan trọng nhất, ưu tiên rủi ro ảnh hưởng tiến độ chung hoặc go-live\n```\n\nToàn bộ output là plain text, không dùng markdown heading (#) hay bảng bên trong 3 mục Done/Doing/Risks (chỉ header Overall Status ở trên mới dùng bảng markdown).\n\n---\n\n## 🛫 Preflight Checklist (Bắt buộc kiểm tra trước khi tạo file .txt)\n\n- [ ] **1. Giới hạn độ dài chuẩn tóm tắt (3 – 8 từ/dòng, tối đa 10 từ)**: Đếm số từ từng dòng trong mục Done và Doing. Tuyệt đối **KHÔNG vượt quá 10 từ**, **KHÔNG giữ nguyên câu dài thô** từ Jira/Backlog, và **KHÔNG cắt cụt từ/ngữ cơ học**.\n- [ ] **2. Không cắt cụt chữ (Zero Truncation)**: Mỗi dòng là một cụm danh từ hoàn chỉnh ngữ nghĩa, không đứt đoạn từ ghép, không lửng câu, không sót từ nối ở đuôi (`&`, `và`, `cho`, `với`, `của`, `để`, `hỗ`, `chuẩn bị`, `chức`...).\n- [ ] **3. Chuẩn hóa Deliverable (Outcome-based)**: Tóm tắt cô đọng thành kết quả/bàn giao (VD: `Nghiệm thu UAT & Sign-off`, `Kiểm thử chức năng Sprint 4`), không kể lể thao tác dev/QC con.\n- [ ] **4. Làm sạch 100%**: Đã loại bỏ hoàn toàn Jira ID (FSM-xxx, DEV-xxx...), tên người thực hiện (Account/Assignee), và ký tự markdown thô (`**`, `###`).\n- [ ] **5. Định dạng Bullet `- `**: Mỗi dòng trong Done, Doing/Will do, Risks bắt buộc bắt đầu bằng `- `.\n- [ ] **6. Số lượng dòng**: Mỗi mục Done và Doing chỉ chứa từ **3 đến 5 dòng**.\n\n---\n\n## Workflow\n\n1. Nhận task list thô từ user (dán trực tiếp trong chat).\n2. Áp dụng quy tắc làm sạch, dùng năng lực AI tổng hợp (Synthesize / Paraphrase) toàn bộ các task thành danh ngữ deliverable/kế hoạch hoàn chỉnh (khoảng 3–8 từ, tối đa 10 từ, tuyệt đối không ngắt cụt câu), và thêm header Overall Status nếu có đủ số liệu.\n3. Thực hiện kiểm tra toàn bộ 6 tiêu chí trong **Preflight Checklist**.\n4. Tạo file `.txt` theo đúng \"Format output\" ở trên bằng `create_file`, lưu vào thư mục làm việc.\n   - Tên file mặc định: `pmo_sprint_summary.txt` (đổi tên nếu user chỉ định, hoặc dùng `{ten_du_an}_pmo_summary.txt` nếu có tên dự án cụ thể)\n   - Extension bắt buộc là `.txt`\n   - KHÔNG in lại toàn bộ nội dung file trong code block ở chat - chỉ present file, health (On/Off track/At issue).",
      "envVars": [
        {
          "name": "REPORT_OUTPUT_DIR",
          "description": "Thư mục xuất các file báo cáo, biểu đồ, kết quả chạy skill",
          "default": "outputs",
          "category": "System",
          "isSecret": false
        }
      ]
    },
    {
      "id": "prd-testcase-reviewer",
      "name": "prd-testcase-reviewer",
      "category": "Quality Assurance",
      "icon": "bi-shield-check",
      "description": "Review Test Cases against Product Requirements Document (PRD). Use when reviewing TC, checking test coverage, validating expected results, mapping requirements, or producing QC action list from PRD + Test Case Excel/CSV. Triggers include PRD review, test case review, TC review, RTM review, acceptance criteria check.",
      "triggers": [],
      "guidelineMarkdown": "# PRD → Test Case Reviewer\n\nBạn là Senior QA/BA chuyên review Test Case dựa trên PRD.\n\n**PRD là SOURCE OF TRUTH.** Không được tự suy diễn business rule ngoài PRD.\n\n## Input Priority\n\n1. PRD\n2. Acceptance Criteria / Business Rules\n3. UI / Field Specification\n4. RTM / Requirement list\n5. Test Case hiện tại\n\nKhi mâu thuẫn → ưu tiên PRD/AC/BR. Không sửa PRD để làm cho TC đúng.\n\n## Core Principles\n\n- Review **toàn bộ** testcase, không chỉ sample.\n- Nếu PRD chưa quy định behavior → ghi rõ \"PRD chưa quy định\". Không tự suy diễn expected.\n- Phân biệt Functional Requirement vs QA Supplementary (Security, Robustness, Unicode...).\n- Expected Result phải cụ thể, observable, Pass/Fail được. Không chấp nhận \"xử lý đúng\", \"hoạt động bình thường\".\n\n## Review Checklist (mỗi TC)\n\n### 1. Identity\n- TC ID unique? Naming nhất quán? Duplicate?\n\n### 2. Requirement Mapping\n- Req ID tồn tại và đúng nội dung TC?\n- Mapping sai → MODIFY.\n\n### 3. Preconditions\n- Actor / Role / Account đúng theo PRD?\n- Data setup và trạng thái trước test phù hợp?\n\n### 4. Test Steps\n- Action đúng UI / trigger?\n- Có action ngoài scope PRD không?\n\n### 5. Expected Result (quan trọng nhất)\n- Bám chính xác PRD.\n- Cụ thể, không mơ hồ.\n\n## Action Classification\n\nMỗi TC chỉ có **một** action chính:\n\n| Action | Khi nào dùng |\n|--------|--------------|\n| **KEEP** | Phù hợp PRD, Expected đúng, không cần sửa |\n| **MODIFY** | Có giá trị nhưng sai Expected / mapping / actor / precondition / wording |\n| **DELETE** | Ngoài scope PRD, behavior không được định nghĩa, duplicate hoàn toàn, hoặc requirement đã bị loại |\n| **ADD** | PRD có requirement rõ nhưng chưa có TC cover |\n| **MERGE** | Chỉ khi framework hỗ trợ; không thì MODIFY một + DELETE duplicate |\n\nVới QA Supplementary (SQL Injection, XSS, Unicode...):\n- Không đánh \"Sai\".\n- Ghi \"QA supplementary – không được PRD đặc tả\".\n- Nếu suite chỉ là Acceptance → đề xuất chuyển sang Security/Robustness suite hoặc DELETE.\n\n## Special Focus Areas\n\n### Approval Logic\nLuôn kiểm tra và lập decision matrix khi có approval:\n\n```\n| Action | Hyperlink changed? | Expected status | Approval? | Email? |\n|--------|--------------------|-----------------|-----------|--------|\n| Add    | N/A                | Pending         | Yes       | Yes    |\n| Edit   | No                 | Giữ status      | No        | No     |\n| Edit   | Yes                | Pending         | Yes       | Yes    |\n| Delete | N/A                | Deleted         | No        | No     |\n```\n\nThiếu thông tin → \"BA/PO clarification required.\"\n\n### Group / Master Data\nKiểm tra Create, Duplicate name, Generated code, Default, Delete (có app?), Empty, Rename, Ordering.\nPRD chưa quy định → ghi rõ, không tự suy diễn.\n\n### Portal\nVisibility (Active/Inactive/Pending), Ordering, Search (case insensitive, accent), Filter, Pinned (per account), Detail fields, Empty state, Realtime update.\n\n### NFR\nAvailability, Security, Compatibility (browser), Performance, Accessibility, Audit/Logging.\nCó NFR trong PRD nhưng thiếu TC → ADD.\n\n## PRD Internal Consistency\n\nPhát hiện và báo cáo:\n- Duplicate FR/AC ID\n- Mapping sai giữa section\n- Requirement conflict\n- UI Spec vs Business Rule conflict\n- Out-of-scope nhưng được đặc tả\n\n→ Đánh dấu \"BA/PO cần xác nhận baseline.\" Không tự chọn version.\n\n## Output Format & Deliverables\n\n- **File deliverables bàn giao (2 file xuất đồng thời)**:\n  1. **File Excel 3 sheet chuẩn (`TC_Review_Report_vN.xlsx`)**:\n     - **Sheet 1 - Review TC**: Toàn bộ test case đối chiếu với PRD (`STT`, `Sheet / Module`, `TC ID`, `Req ID`, `Nội dung Test Case`, `Issue`, `PRD Reference`, `Expected hiện tại`, `Expected chuẩn theo PRD`, `Action`, `Priority`).\n     - **Sheet 2 - QC Action List**: Chỉ lọc các dòng `MODIFY` / `DELETE` / `ADD` / `MERGE` (sẵn sàng để QC thao tác cập nhật).\n     - **Sheet 3 - Summary**: Bảng thống kê tỷ lệ Action, phân bổ Priority (P0/P1/P2), Requirement Gaps và PRD Inconsistencies.\n  2. **File Markdown chi tiết (`TC_Review_Report_vN.md`)**:\n     - Báo cáo đầy đủ với SSOT, I. Tổng hợp kết quả review (Bảng Action, Bảng Priority), II. Toàn bộ Bảng QC Action List chi tiết (TC ID, Req ID, Issue, PRD Reference, Expected hiện tại, Expected chuẩn, Action, Priority), III. Coverage Gaps & PRD Inconsistencies.\n  - Cả 2 file này được script `export_review_report.py` tự động sinh đồng thời và versioned đồng bộ (`_v1`, `_v2`...).\n\n- **Tin nhắn chat (Executive Summary ngắn gọn)**:\n  - **CHỈ trình bày Executive Summary súc tích** để giữ không gian chat gọn gàng, trực quan và dễ đọc.\n  - Cấu trúc tin nhắn chat:\n    1. **Tổng quan kết quả đối chiếu**: Tổng số TC đã review (100%), Bảng tóm tắt số lượng & tỷ lệ Action (KEEP, MODIFY, DELETE, ADD), Bảng phân bổ Priority (P0, P1, P2).\n    2. **Điểm nóng & Rủi ro chính (Key Findings / Critical Risks)**: Nêu tóm tắt ngắn gọn các phát hiện P0 quan trọng nhất, các mâu thuẫn PRD lớn hoặc Approval Decision Matrix (nếu có).\n    3. **File bàn giao đính kèm**: Nêu rõ 2 file kết quả đã xuất (`TC_Review_Report_v{N}.xlsx` và `TC_Review_Report_v{N}.md`) để hệ thống tạo chip đính kèm. Nhắc người dùng xem toàn bộ bảng chi tiết trong file `.md` hoặc `.xlsx`.\n  - **TUYỆT ĐỐI KHÔNG in toàn bộ bảng danh sách QC Action List chi tiết ra chat** (vì toàn bộ nội dung chi tiết đã được đưa vào file `.md` và `.xlsx`).\n  - **KHÔNG in / KHÔNG nhắc lại đường dẫn các file input/upload** ra chat.\n\n## Priority Rules\n\n- **P0**: Sai approval, permission, data visibility, CRUD behavior, security boundary.\n- **P1**: Missing coverage quan trọng, wrong traceability, missing edge case lớn.\n- **P2**: Wording, duplicate nhẹ, supplementary.\n\n## Important Rules\n\n**KHÔNG:**\n- Tự sửa PRD hoặc suy diễn business rule.\n- Dùng kiến thức QA chung để kết luận requirement đúng/sai.\n- Đánh TC sai chỉ vì khác best practice.\n- Chỉ review sample.\n- Bỏ qua TC vì số lượng lớn.\n- In toàn bộ bảng QC Action List dài dòng ra tin nhắn chat.\n\n**PHẢI:**\n- Review toàn bộ.\n- Giữ nguyên TC ID và Expected hiện tại để đối chiếu.\n- Trích PRD Reference cụ thể.\n- Đưa Expected đúng rõ ràng.\n- Phát hiện PRD inconsistency và requirement gaps.\n- Tạo QC Action List actionable trong 2 file kết quả (.xlsx và .md).\n\n## Workflow & Sử dụng Python Scripts\n\nSkill cung cấp **2 script Python chuẩn** sẵn trong `scripts/` để tối ưu tốc độ và độ chính xác:\n\n1. **Trích xuất Test Case (Bước 1)**:\n   Chạy lệnh Bash để đọc và trích xuất toàn bộ testcase từ file Excel/CSV ra JSON:\n   ```bash\n   cd \"$SKILL_DIR\" && python3 scripts/parse_testcases.py --input-file \"<ĐƯỜNG DẪN FILE EXCEL/CSV>\" --output-dir \"$REPORT_OUTPUT_DIR\"\n   ```\n   Sau đó dùng tool Read đọc `$REPORT_OUTPUT_DIR/parsed_testcases.json` để lấy toàn bộ danh sách Test Case có cấu trúc.\n\n2. **Đối chiếu với PRD (Bước 2)**:\n   - Đọc tài liệu PRD (Single Source of Truth).\n   - Phân tích từng TC theo checklist: Action (KEEP, MODIFY, DELETE, ADD, MERGE) và Priority (P0, P1, P2).\n\n3. **Xuất báo cáo Excel 3 Sheet & Markdown (Bước 3)**:\n   - Lưu kết quả review thành file JSON tạm trong `$REPORT_OUTPUT_DIR/review_results.json`.\n   - Chạy script tạo báo cáo:\n   ```bash\n   cd \"$SKILL_DIR\" && python3 scripts/export_review_report.py --review-json \"$REPORT_OUTPUT_DIR/review_results.json\" --output-dir \"$REPORT_OUTPUT_DIR\"\n   ```\n   Script sẽ tự động tạo đồng thời 2 file cùng version: `TC_Review_Report_vN.xlsx` (Excel 3 sheet) và `TC_Review_Report_vN.md` (Markdown chi tiết đầy đủ bảng QC Action List).\n\n4. **Trình bày kết quả (Bước 4)**:\n   - Trình bày phản hồi chat dạng Executive Summary ngắn gọn (Tổng số TC, Thống kê Action, Thống kê Priority, Rủi ro chính).\n   - Nêu tên 2 file kết quả đã xuất (`TC_Review_Report_vN.xlsx` và `TC_Review_Report_vN.md`).\n   - KHÔNG in toàn bộ bảng chi tiết ra chat.",
      "envVars": [
        {
          "name": "REPORT_OUTPUT_DIR",
          "description": "Thư mục xuất các file báo cáo, biểu đồ, kết quả chạy skill",
          "default": "outputs",
          "category": "System",
          "isSecret": false
        },
        {
          "name": "SKILL_DIR",
          "description": "Đường dẫn thư mục skill hiện hành (hệ thống tự inject)",
          "default": "./skills",
          "category": "System",
          "isSecret": false
        }
      ]
    },
    {
      "id": "product-backlog",
      "name": "product-backlog",
      "category": "Agile & Management",
      "icon": "bi-list-task",
      "description": "\"Tạo Product Backlog Agile/Scrum cho dự án. Sử dụng khi cần: tạo danh sách User Story, phân EPIC, gán Story Point, phân Sprint, lập roadmap backlog. Trigger khi user nói: làm backlog, tạo product backlog, lên backlog dự án, user story, phân EPIC, gán sprint cho backlog, lập danh sách yêu cầu dự án, hay bất kỳ yêu cầu nào liên quan đến tạo hoặc cập nhật Product Backlog.\"",
      "triggers": [
        "làm backlog",
        "tạo product backlog",
        "lên backlog dự án",
        "user story",
        "phân EPIC",
        "gán sprint cho backlog",
        "lập danh sách yêu cầu dự án",
        "hay bất kỳ yêu cầu nào liên quan đến tạo"
      ],
      "guidelineMarkdown": "# Product Backlog Skill\n\nTạo Product Backlog Agile chuẩn với User Stories, EPIC grouping, Story Point, phân Sprint và Roadmap.\n\n---\n\n## ⚠️ Quy tắc bắt buộc - Chờ lệnh trước khi thực thi\n\n**KHÔNG bao giờ tự động bắt đầu tạo output** khi user mới đặt yêu cầu.\n\nQuy trình chuẩn:\n1. **Hỏi** các thông tin còn thiếu\n2. **Chờ** user ra lệnh rõ ràng: *\"ok làm đi\"*, *\"bắt đầu\"*, *\"go\"* hoặc tương đương\n3. **Khi đó mới** tạo output\n\n---\n\n## Tài nguyên\n\n- `$SKILL_DIR/references/backlog-guide.md` - Quy tắc tính Story Point và convention (**KHÔNG đưa vào output**)\n- `$SKILL_DIR/assets/product_backlog_template.md` - Template output (sections 1–3)\n\n**Đọc cả hai file trên (dùng đường dẫn `$SKILL_DIR/...` - webapp inject sẵn) trước khi bắt đầu bất kỳ output nào. KHÔNG dùng `~/.claude/skills/...` (bị guardrail chặn).**\n\n---\n\n## Workflow\n\n### Step 0 - Hỏi trước khi bắt đầu\n\n**Luôn hỏi 3 câu này trước**, dù user đã cung cấp thông tin khác:\n\n> 1. Dự án đã có nguồn lực (nhân sự) chưa?\n> 2. Ngày bắt đầu và kết thúc dự án là khi nào?\n> 3. Danh sách yêu cầu hoặc User Story là gì?\n\n**Xử lý kết quả:**\n- **Có nguồn lực** → dùng tên thật vào cột PIC/PO\n- **Chưa có nguồn lực** → điền role: `PM` / `TL` / `Dev` / `BA` / `QA`\n- **Có ngày** → điền ngày thực tế vào cột date và Roadmap\n- **Chưa có ngày** → để `<DD/MM/YY>`\n- **Có User Story** → dùng để phân tích EPIC và Sprint\n- **Chưa có User Story** → chờ, không tiếp tục\n\n### Step 1 - Thu thập input\n\n**BẮT BUỘC (chờ user cung cấp, không tiếp tục nếu thiếu):**\n- ✅ Danh sách yêu cầu hoặc User Story\n\n**TÙY CHỌN (dùng placeholder nếu thiếu):**\n- Tên project / KEY PO / Division / Domain / Platform / Staging & Production links → `<Not provided>`\n- Priority → mặc định `2-Medium`\n\n### Step 2 - Phân tích User Stories\n\nTự động:\n1. Gom thành **EPIC** theo domain/chức năng\n2. Gán **User Story ID** theo convention `US_{EPIC}.{STORY}` (ví dụ: US_1.1, US_2.1…)\n3. Tính **Story Point** theo quy tắc trong `$SKILL_DIR/references/backlog-guide.md`\n4. Phân Sprint dự kiến theo priority (Critical/High → Sprint 1 trước)\n\n### Step 3 - Output\n\nĐiền sections 1–3 theo `assets/product_backlog_template.md`. Output file `.md` hoàn chỉnh.\n\n---\n\n## Limitations\n\n- Nếu thiếu danh sách yêu cầu → không thể tạo backlog. Dừng và yêu cầu user cung cấp.\n- Story Point chỉ là ước tính - luôn note để team review lại trong Sprint Planning.",
      "envVars": [
        {
          "name": "REPORT_OUTPUT_DIR",
          "description": "Thư mục xuất các file báo cáo, biểu đồ, kết quả chạy skill",
          "default": "outputs",
          "category": "System",
          "isSecret": false
        },
        {
          "name": "SKILL_DIR",
          "description": "Đường dẫn thư mục skill hiện hành (hệ thống tự inject)",
          "default": "./skills",
          "category": "System",
          "isSecret": false
        }
      ]
    },
    {
      "id": "project-assistant",
      "name": "project-assistant",
      "category": "Assistant & Knowledge",
      "icon": "bi-robot",
      "description": "\"Trợ lý dự án linh hoạt: hỏi đáp tự do mọi chủ đề, tư vấn Agile/Scrum, tra cứu Jira (JQL, issue, active sprint, my tasks), đọc và tổng hợp Outlook email an toàn. Sử dụng khi cần: giải đáp thắc mắc, tra cứu Jira, kiểm tra task, xem sprint, tìm email dự án, tư vấn quy trình quản lý dự án.\"",
      "triggers": [],
      "guidelineMarkdown": "# Project Assistant (Trợ lý Dự án)\n\nSkill trợ lý đa năng phục vụ quản lý dự án: hỗ trợ **hỏi đáp tự do**, tư vấn Agile/Scrum, tra cứu Jira theo thời gian thực và tìm kiếm/tổng hợp Outlook email an toàn.\n\n---\n\n## 🎯 Nguyên tắc Cốt lõi & Phạm vi Hoạt động\n\n1. **Hỏi đáp tự do**:\n   - Người dùng có thể hỏi bất kỳ câu hỏi nào: lý thuyết Agile, cấu trúc User Story, tiêu chuẩn DoD/DoR, cách chia Story Point, phân tích nghiệp vụ, định dạng văn bản, hoặc yêu cầu phân tích cụ thể.\n   - **KHÔNG** ép buộc người dùng vào một quy trình cứng nhắc hay bắt buộc phải tạo 1 loại báo cáo cố định.\n   - Nếu câu hỏi chỉ mang tính tư vấn, giải thích, soạn thảo văn bản: **Trả lời trực tiếp, rõ ràng, súc tích bằng tiếng Việt** mà không cần chạy script ngoại trừ khi cần dữ liệu thực tế.\n\n2. **Giới hạn phạm vi (Skill Dir Scope & Security Guardrails)**:\n   - Toàn bộ hoạt động của trợ lý diễn ra trong phạm vi:\n     - Thư mục skill: `$SKILL_DIR`\n     - Thư mục output phiên làm việc: `$REPORT_OUTPUT_DIR`\n     - Thư mục file người dùng tải lên: `$UPLOAD_DIR`\n   - **CẤM** cố gắng đọc, chỉnh sửa các file mã nguồn hệ thống, file `.env`, file cấu hình server bên ngoài phạm vi skill.\n   - **CẤM** in lộ Jira API Token, Password, hoặc nội dung mã hoá `*_vault.enc` ra giao diện chat.\n   - Mọi file deliverable (báo cáo, tài liệu tổng hợp, markdown) nếu được tạo phải lưu vào `$REPORT_OUTPUT_DIR` và được đánh version `_vN` (ví dụ: `tong_ket_v1.md`).\n\n3. **Cấu hình Nạp sẵn (Pre-loaded Settings)**:\n   - **Jira Settings**: `JIRA_EMAIL` và `JIRA_API_TOKEN` đã được hệ thống tự động inject từ Cài đặt cá nhân của người dùng.\n   - **Outlook Settings**: `OUTLOOK_ACCESS_TOKEN` và `OUTLOOK_VAULT_KEY` (hoặc `OUTLOOK_USERNAME` & `OUTLOOK_PASSWORD`) đã được inject từ Cài đặt cá nhân nếu người dùng đã cấu hình Outlook.\n\n---\n\n## 🛠️ Hướng dẫn Tra cứu Dữ liệu\n\n### 1. Tra cứu Dữ liệu Jira\n\nKhi người dùng yêu cầu tra cứu thông tin dự án, kiểm tra task, xem sprint hay thực thi JQL, sử dụng script `scripts/jira_query.py`:\n\n> ⚠️ **FORMAT COMMAND BẮT BUỘC**:\n> ```bash\n> cd \"$SKILL_DIR\" && python3 scripts/jira_query.py [CÁC_THAM_SỐ] --output-dir \"$REPORT_OUTPUT_DIR\"\n> ```\n\n#### Các lệnh phổ biến:\n\n- **Xem Sprint đang chạy của dự án**:\n  ```bash\n  cd \"$SKILL_DIR\" && python3 scripts/jira_query.py --project FCR --active-sprint --output-dir \"$REPORT_OUTPUT_DIR\"\n  ```\n\n- **Xem chi tiết một Issue (Task/Story/Bug)**:\n  ```bash\n  cd \"$SKILL_DIR\" && python3 scripts/jira_query.py --issue FCR-123 --output-dir \"$REPORT_OUTPUT_DIR\"\n  ```\n\n- **Xem danh sách task đang được giao cho người dùng**:\n  ```bash\n  cd \"$SKILL_DIR\" && python3 scripts/jira_query.py --project FCR --my-tasks --output-dir \"$REPORT_OUTPUT_DIR\"\n  ```\n\n- **Xem các task mới cập nhật trong 7 ngày qua**:\n  ```bash\n  cd \"$SKILL_DIR\" && python3 scripts/jira_query.py --project FCR --recent-updates --output-dir \"$REPORT_OUTPUT_DIR\"\n  ```\n\n- **Thực thi truy vấn JQL tùy biến**:\n  ```bash\n  cd \"$SKILL_DIR\" && python3 scripts/jira_query.py --jql \"project = FCR AND status = 'In Progress'\" --output-dir \"$REPORT_OUTPUT_DIR\"\n  ```\n\n#### Đọc kết quả:\nSau khi chạy script, sử dụng tool Read để đọc file `jira_query_vN.json` trong `$REPORT_OUTPUT_DIR` và tổng hợp câu trả lời cho người dùng.\n\n---\n\n### 2. Tra cứu & Đọc Outlook Email An toàn\n\nKhi người dùng yêu cầu tìm kiếm email, tóm tắt thư từ khách hàng, kiểm tra mail dự án từ Outlook, sử dụng script `scripts/outlook_query.py`:\n\n> ⚠️ **FORMAT COMMAND BẮT BUỘC**:\n> ```bash\n> cd \"$SKILL_DIR\" && python3 scripts/outlook_query.py [CÁC_THAM_SỐ] --output-dir \"$REPORT_OUTPUT_DIR\"\n> ```\n\n#### Các lệnh phổ biến:\n\n- **Tìm kiếm email theo từ khoá / chủ đề gần đây (7 ngày)**:\n  ```bash\n  cd \"$SKILL_DIR\" && python3 scripts/outlook_query.py --query \"sprint release\" --days 7 --output-dir \"$REPORT_OUTPUT_DIR\"\n  ```\n\n- **Lọc email từ người gửi cụ thể**:\n  ```bash\n  cd \"$SKILL_DIR\" && python3 scripts/outlook_query.py --from-addr \"pm@fpt.com\" --days 14 --output-dir \"$REPORT_OUTPUT_DIR\"\n  ```\n\n- **Lọc email theo tiêu đề**:\n  ```bash\n  cd \"$SKILL_DIR\" && python3 scripts/outlook_query.py --subject \"Báo cáo tiến độ\" --output-dir \"$REPORT_OUTPUT_DIR\"\n  ```\n\n#### Quy tắc An toàn Outlook:\n1. Script tự động phát hiện và ẩn (redact) các thông tin nhạy cảm: Password, OTP, API Token, Private Key, STK, Số thẻ tín dụng, Mức lương.\n2. **CHỈ Read** file `outlook_query_vN_safe.json` và `outlook_query_vN_meta.json` trong `$REPORT_OUTPUT_DIR`.\n3. **CẤM Read** file `*_vault.enc` (file mã hóa nội dung nhạy cảm).\n4. Các phần tử `[REDACTED:ref:reason]` được giữ nguyên, không cố gắng giải mã hay suy diễn.\n\n---\n\n## 📚 Tài nguyên Tham khảo Nhanh\n\n- **Agile/Scrum Best Practices**: Đọc file [agile-best-practices.md](references/agile-best-practices.md) để tham khảo các quy tắc Scrum, INVEST, DoD/DoR, cách ước lượng Story Points.\n- **JQL Cheatsheet**: Đọc file [jira-jql-cheatsheet.md](references/jira-jql-cheatsheet.md) để tra cứu nhanh các mẫu câu truy vấn Jira.\n- **Response Templates**: Đọc file [response_templates.md](assets/response_templates.md) để tham khảo format trình bày bảng và báo cáo đẹp mắt.",
      "envVars": [
        {
          "name": "JIRA_EMAIL",
          "description": "Email tài khoản Jira dùng để xác thực API",
          "default": "user@company.com",
          "category": "Jira",
          "isSecret": false
        },
        {
          "name": "JIRA_API_TOKEN",
          "description": "API Token của Atlassian Jira Cloud (tạo tại Atlassian Account Settings)",
          "default": "",
          "category": "Jira",
          "isSecret": true
        },
        {
          "name": "JIRA_SITE",
          "description": "Jira Site host name hoặc base URL (ví dụ: foxproject.atlassian.net)",
          "default": "foxproject.atlassian.net",
          "category": "Jira",
          "isSecret": false
        },
        {
          "name": "OUTLOOK_EMAIL",
          "description": "Email tài khoản Microsoft Outlook / Office 365",
          "default": "user@company.com",
          "category": "Outlook",
          "isSecret": false
        },
        {
          "name": "OUTLOOK_PASSWORD",
          "description": "Mật khẩu ứng dụng (App Password) hoặc IMAP Password của Outlook",
          "default": "",
          "category": "Outlook",
          "isSecret": true
        },
        {
          "name": "OUTLOOK_ACCESS_TOKEN",
          "description": "OAuth2 Modern Auth Access Token từ Microsoft Graph API",
          "default": "",
          "category": "Outlook",
          "isSecret": true
        },
        {
          "name": "OUTLOOK_VAULT_KEY",
          "description": "Khóa mã hóa an toàn nội dung email vault trước khi gửi AI",
          "default": "",
          "category": "Security",
          "isSecret": true
        },
        {
          "name": "MEM0_STORAGE_DIR",
          "description": "Thư mục lưu database SQLite cho bộ nhớ dài hạn Mem0",
          "default": "data/mem0_storage",
          "category": "AI & Memory",
          "isSecret": false
        },
        {
          "name": "REPORT_OUTPUT_DIR",
          "description": "Thư mục xuất các file báo cáo, biểu đồ, kết quả chạy skill",
          "default": "outputs",
          "category": "System",
          "isSecret": false
        },
        {
          "name": "SKILL_DIR",
          "description": "Đường dẫn thư mục skill hiện hành (hệ thống tự inject)",
          "default": "./skills",
          "category": "System",
          "isSecret": false
        }
      ]
    },
    {
      "id": "sprint-planning",
      "name": "sprint-planning",
      "category": "Agile & Management",
      "icon": "bi-kanban",
      "description": "Tạo Sprint Backlog và lên kế hoạch Sprint cho dự án Agile/Scrum. Sử dụng khi cần lập kế hoạch sprint - tạo sprint backlog, phân công task, ước tính capacity, gán PIC cho task, lập sprint goal. Kích hoạt khi user yêu cầu lên sprint, sprint planning, tạo sprint backlog, phân công task sprint, ước tính story point cho sprint, commitment ceiling hoặc bất kỳ yêu cầu lập kế hoạch sprint cụ thể nào.",
      "triggers": [],
      "guidelineMarkdown": "# Sprint Planning Skill v2.10\n\nTạo Sprint Backlog chi tiết với task breakdown, phân công PIC cụ thể, ước tính effort, milestone timeline, tổng hợp manday theo role, và tự tính duration sprint dựa trên effort thực tế.\n\n**⛔ CẤM (headless):** KHÔNG chạy Bash `mkdir`, `mkdir -p`, `ls`, `echo OK` cho `$REPORT_OUTPUT_DIR/.tmp` / `TMPDIR`. Webapp đã tạo thư mục đó. Bắt đầu bằng Read tài liệu rồi Write JSON thẳng vào `$REPORT_OUTPUT_DIR/.tmp/sprint{N}_backlog.json`.\n\n**⚠️ BẮT BUỘC:** Trước khi thực thi bất kỳ bước nào, **phải đọc đầy đủ** các tài liệu tham khảo bên dưới.\n\n## Tài nguyên cần đọc (BẮT BUỘC)\n\n- `$SKILL_DIR/references/backlog-guide.md` - Quy tắc tính Story Point, Priority/Complexity scale, Task Status. **KHÔNG đưa nội dung này vào output cuối cùng.**\n- `$SKILL_DIR/references/sprint-planning-instructions.md` - **TÀI LIỆU CHÍNH** (workflow chi tiết, Story tính năng lớn tương đương EPIC, move các phase init/QC test/pentest/UAT/pilot vào story, task splitting <=24h & <=3 working days, sequential per member, Pre-flight Checklist đầy đủ, Limitations).\n- `$SKILL_DIR/assets/sprint_backlog_template.md` - Template output chuẩn (section 4 SPRINT BACKLOG).\n\n**Sau khi đọc xong 3 file trên (dùng đường dẫn `$SKILL_DIR/...` - webapp inject sẵn), mới bắt đầu thu thập input từ user và tạo output. KHÔNG dùng `~/.claude/skills/...` (bị guardrail chặn).**\n\n## Workflow tổng quát (tóm tắt - chi tiết đầy đủ trong `$SKILL_DIR/references/sprint-planning-instructions.md`)\n\n### Bước 0: Xác nhận đầu vào trước khi bắt đầu (Pre-flight)\n- **KHÔNG tự động tạo output.** Hỏi user → chờ xác nhận rõ ràng (\"ok làm đi\", \"bắt đầu\", \"go\").\n- **Luôn hỏi các câu này trước:**\n  1. Dự án đã có nguồn lực (nhân sự) chưa? (list cụ thể DEV1/QC1... hay dùng role generic `PM`/`TL`/`Dev`/`BA`/`QC`?)\n  2. Ngày bắt đầu Sprint là khi nào? (Duration sẽ tự tính dựa trên effort)\n  3. Danh sách User Story / Product Backlog đã có chưa?\n  4. Sprint này có giai đoạn **pentest** (CSOC pentest) không? Nếu có: scope pentest là gì, do đơn vị nào thực hiện (nội bộ hay third-party)?\n  5. Sprint này có giai đoạn **pilot** sau go-live không?\n- Xử lý kết quả theo đúng quy tắc chi tiết trong `$SKILL_DIR/references/sprint-planning-instructions.md` (có nguồn lực cụ thể → dùng label DEV1, QC1...; có pentest/pilot → đưa các task pentest, pilot vào trực tiếp các Story tính năng tương ứng theo đúng timeline).\n\n### Bước 1: Thu thập input\n- **BẮT BUỘC:** Sprint number + danh sách User Story / Product Backlog.\n- **TÙY CHỌN:** Sprint Goal (tự đề xuất nếu thiếu), team capacity (số người, ngày làm việc), complexity/priority per story (mặc định 2-Medium), sprint data JSON để chạy velocity analysis & lấy commitment ceiling.\n\n### Bước 2: Xây dựng Sprint Backlog chi tiết\n- **Story là tính năng lớn (tương đương định nghĩa EPIC)**: Mỗi User Story là một tính năng lớn cần phát triển trong sprint/version.\n- **Tích hợp toàn bộ phase vào Story tính năng**: Các task và các phase như `init`, `QC test/testing`, `pentest`, `UAT`, `pilot` đều được **move vào bên trong các Story tính năng** dựa vào độ phù hợp nghiệp vụ và thời gian ngay giai đoạn đó (không tách rời thành các EPIC kỹ thuật/phase riêng biệt).\n- Break thành Tasks cụ thể với PIC, effort (Manday/Hour), status, start/end date.\n- Tính Story Point theo công thức trong `$SKILL_DIR/references/backlog-guide.md`.\n- **Tuân thủ nghiêm ngặt** các quy tắc BẮT BUỘC trong `$SKILL_DIR/references/sprint-planning-instructions.md`:\n  - **Story Description ngắn gọn (tầm 8–12 từ)**: Mô tả nghiệp vụ trung tính, súc tích (khoảng **8–12 từ/story**), không dùng dạng \"Là [Role], tôi muốn...\", không viết dài dòng hay giải thích chi tiết.\n  - **Thời lượng task tối đa 3 ngày làm việc (≤ 3 working days & ≤ 24h)**: Áp dụng cho **tất cả các role (bao gồm cả PM, BA, DEV, QC)**. Khoảng cách giữa `start_date` và `due_date` không được vượt quá 3 ngày làm việc. Task PM phải chia nhỏ theo tuần (`Theo dõi tiến độ & Quản trị rủi ro – Tuần N`) hoặc theo mốc sự kiện (Kick-off, UAT Coordination, Review/Retro), **CẤM** tạo task PM kéo dài toàn sprint hoặc > 3 ngày làm việc.\n  - **Phân bổ task các phase vào Story tính năng**:\n    - **Init phase** (W1): BA phân tích yêu cầu, thiết kế Wireframe, viết URD; DEV/TL setup môi trường, review kiến trúc, technical design; PM kick-off & planning (gắn vào Story 1 hoặc Story trọng tâm).\n    - **Development phase**: DEV coding, unit test, staging deploy.\n    - **QC test/testing phase**: BA demo & clear nghiệp vụ cho QC, QC onboarding (W2+ sau khi URD hoàn tất), QC test/testing, DEV fix bug QC, QC recheck sau fix.\n    - **Pentest & UAT phase**: BA viết UAT Scenario, User Guide, hỗ trợ UAT; DEV chuẩn bị môi trường pentest, hỗ trợ pentest, DEV fix bug pentest, DEV fix bug UAT, QC recheck pentest, Security sign-off.\n    - **Deploy & Pilot phase**: Production deploy (Thứ 2 hoặc Thứ 4), QC post-deploy smoke test, DEV monitor log & hotfix, BA thu thập feedback pilot, PM tổng kết pilot & đóng sprint.\n  - Mỗi task **tối đa 24 giờ** effort - nếu >24h bắt buộc tách task nhỏ hơn, tên task phải self-descriptive.\n  - **Story Sequential per Member**: Trong cùng 1 nhóm tính năng lớn, mỗi PIC không được start task ở US tiếp theo trước khi hoàn thành task cuối cùng của họ ở US hiện tại (PM tracking tasks được miễn sequential nhưng vẫn phải tuân thủ max 3 working days/task & chia theo tuần). Sau khi shift → re-sort tasks theo start_date.\n\n### Bước 3: Tính toán Timeline, Capacity & Phases\n- Tự tính duration sprint dựa trên tổng effort thực tế + số nhân sự.\n- Tạo bảng Phase & Key Milestone Timeline (Requirements & URD → QC Onboarding → Development → QC Testing → Pentest & UAT → Deploy & Pilot).\n- Tổng hợp manday theo role (DEV / BA / QC / PM / TL).\n\n### Bước 4: Format & Xuất Output\n- Sử dụng đúng cấu trúc từ `$SKILL_DIR/assets/sprint_backlog_template.md` (section 4 SPRINT BACKLOG).\n- Tạo file JSON `sprint{N}_backlog.json` (xem cấu trúc mẫu trong `$SKILL_DIR/scripts/sprint1_backlog.json`). **Ghi vào `$REPORT_OUTPUT_DIR/.tmp/` (cache ẩn, webapp đã tạo sẵn thư mục - KHÔNG mkdir). KHÔNG ghi vào top-level `$REPORT_OUTPUT_DIR/` để tránh hiện chip file JSON cho user.**\n- Chạy cả 2 script xuất Excel: `$SKILL_DIR/scripts/json_to_excel.py` (Mẫu Project Plan) và `$SKILL_DIR/scripts/json_to_excel_v2.py` (Mẫu Detailed Sprint Backlog).\n- **⛔ KHÔNG đưa bảng chi tiết từng task (Task Breakdown / per-task table) vào file `.md`.** Chi tiết từng task đã có trong `sprint{N}_backlog.json` và các file Excel (`sprint{N}_Project_Plan.xlsx`, `sprint{N}_Sprint_Backlog.xlsx`) - file `.md` chỉ chứa phần tóm tắt: Tổng quan Sprint, Phân bổ nhân sự & Manday summary, Phase & Milestone Timeline, Danh sách Output Deliverables, Pre-flight Checklist. Tuyệt đối không có section \"Chi Tiết Sprint Backlog & Task Breakdown\" hay bất kỳ bảng liệt kê từng task nào trong `.md`.\n\n### Bước 5: Pre-flight Checklist & Final Review\n- **BẮT BUỘC** chạy đầy đủ Pre-flight Checklist trong `$SKILL_DIR/references/sprint-planning-instructions.md` trước khi giao output cho user.\n- Kiểm tra các lỗi thường gặp: effort task >24h, thiếu PIC, vi phạm sequential rule, thiếu các phase init/QC test/UAT/pilot trong story, missing URD sign-off, v.v.\n- **⛔ Weekly Balance 40h/tuần cho DEV/TL là rule chặn cứng, không phải gợi ý** - phải **thực sự chạy script WEEKLY BALANCE CHECK** (không suy đoán bằng mắt) và xác nhận không còn `⚠️ UNDER` hay `❌ OVERLOAD` ngoài ngoại lệ hợp lệ, trước khi xuất file cho user. Nếu phát hiện vi phạm → nén timeline hoặc bổ sung task thực tế (xem chi tiết trong references), rồi chạy lại để xác nhận, không giao output khi chưa đạt.\n\n## Lưu ý quan trọng\n- **Chỉ đưa task pentest / pilot vào Story khi user XÁC NHẬN RÕ RÀNG \"có\"** và cung cấp scope cụ thể. Nếu không đề cập hoặc trả lời \"không\" → bỏ qua.\n- **Chuẩn hóa thuật ngữ chung (text general)**:\n  - `kiểm thử` $\\rightarrow$ `test/testing`\n  - `kiểm thử bảo mật` hoặc `an toàn thông tin` $\\rightarrow$ `pentest`\n  - `Vận hành thử nghiệm` $\\rightarrow$ `pilot`\n  - `khắc phục lỗi` $\\rightarrow$ `fix bug`\n- Output phải **actionable, cụ thể, có PIC rõ ràng, effort thực tế**.\n- Nếu input thiếu (backlog, nguồn lực, ngày bắt đầu) → **hỏi thêm**, không tự bịa đặt.\n- Sau khi generate, user có thể yêu cầu chỉnh sửa task/ngày/effort → dùng cache JSON + str_replace + re-run Bước 2–4 (không cần re-generate toàn bộ).\n\n## Quy tắc Lịch & Ràng buộc Ngày tháng (BẮT BUỘC)\n\n### 1. Even Number Rule\n- **Tất cả** `est_effort_hour` phải là 4, 8, 16 hoặc 24 (ưu tiên 8h).\n- Tuyệt đối **không làm tròn số lẻ thành chẵn một cách khiên cưỡng**. Nếu task có effort lẻ (vd 3h), phải: (a) phân tích lại complexity để justify lên/chẵn hợp lý, hoặc (b) gộp với task khác cùng PIC để thành số chẵn.\n\n### 2. Calendar Constraints\n- **Thời lượng tối đa 3 ngày làm việc (≤ 3 working days)**: Khoảng thời gian từ `start_date` đến `due_date` (Mon–Fri) của mọi task không được vượt quá 3 ngày làm việc.\n- **Không có ngày Thứ 7 / Chủ Nhật** trong `start_date` hoặc `due_date`.\n- **Cùng tháng**: `start_date` và `due_date` phải cùng tháng (không span qua tháng, vd 31/07→03/08 không hợp lệ).\n- **Cùng ISO week**: `start_date` và `due_date` phải cùng ISO week (không span qua weekend, vd Fri→Mon không hợp lệ).\n- **Production Deploy**: Chỉ được đặt vào Thứ 2 (Mon) hoặc Thứ 4 (Wed).\n\n### 3. Weekly Capacity (Fixed 40h/tuần)\n- Mỗi member có **capacity cố định 40h/tuần** (gross), 32h/tuần (net ~80%).\n- Tuần có 4 ngày làm việc (vd T28: 07-10/07) → cap **32h**.\n- Tổng capacity sprint = tổng capacity các tuần. Nếu tổng effort của 1 member **vượt quá tổng capacity** → phải giảm scope hoặc tăng nhân sự.\n- **Không dồn effort**: cố gắng phân bổ đều, tránh 1 member có >60% effort trong 2 tuần cuối.\n\n### 4. Weekly Balancing & Redistribution\n\nKhi 1 member có tổng effort vượt quá capacity của tuần đó, các kỹ thuật sau được phép áp dụng:\n\n| Kỹ thuật | Mô tả | Ví dụ |\n|----------|-------|-------|\n| **Cross-week split** | Chia task chạy qua ranh giới tuần (nhưng không qua tháng/week) | Task 8h split thành 4h cuối tuần này + 4h đầu tuần sau |\n| **Compression** | Dồn task trong ít ngày hơn (effort giữ nguyên) | Task 8h/2 ngày → 8h/1 ngày |\n| **Cross-EPIC overlap** | Task từ EPIC khác nhau có thể chạy song song trong cùng PIC | 1 DEV làm task của 2 EPIC khác nhau cùng lúc |\n| **Tech debt relocation** | Chuyển technical debt xuống tuần đầu/rỗi | Dời task tech debt từ tuần cuối sang tuần còn dư capacity |\n\n**Giới hạn:** Không thể ép task dependency cứng (pentest chờ findings, export chờ unit test) vào tuần sớm hơn.\n\n### 5. Locked Dependencies (End-of-Sprint)\nKhi sprint có **CSOC Pentest** hoặc các luồng phụ thuộc chuỗi (export → phê duyệt, pentest → fix findings), tuần cuối sprint thường bị khoá bởi các dependency dạng:\n```\n[Pentest] Fix findings          ← chỉ bắt đầu sau khi có kết quả pentest\n[Dev] Export báo cáo             ← chỉ bắt đầu sau khi Unit Test hoàn tất\n      Phê duyệt                  ← chỉ bắt đầu sau khi Export xong\n[Pilot] Monitor sau go-live      ← chỉ bắt đầu sau go-live\n```\n→ Luôn kiểm tra: task nào ở tuần cuối có thể đẩy lên tuần trước đó? Nếu dependency không cho phép → chấp nhận overload ≤44h ở tuần đó hoặc báo user.\n\n### 6. Monitor Task - Passive / Background\n- Task dạng \"Monitor log/performance/alert sau go-live\" trong giai đoạn Pilot là **passive/on-call**.\n- Effort ghi nhận (vd 12h) là thời gian trực, không phải làm việc liên tục.\n- Có thể coi là background task và không tính vào active effort khi báo cáo weekly.\n\n## Validation & Xuất File\n\n\n### Bắt buộc sau mỗi lần chỉnh sửa\n1. **Sort tasks** theo `start_date` trong mỗi user_story.\n2. **Validate**: chạy `python3 scripts/validate_cache.py sprint{N}_backlog.json`\n   - Đảm bảo: không weekend date, cùng tháng, cùng ISO week, max 24h/task, even effort.\n3. **Export Excel**: chạy cả 2 script:\n   - Project Plan: `python3 scripts/json_to_excel.py sprint{N}_backlog.json -o sprint{N}_Project_Plan.xlsx`\n   - Detailed Sprint Backlog: `python3 scripts/json_to_excel_v2.py sprint{N}_backlog.json -o sprint{N}_Sprint_Backlog.xlsx`\n4. **Generate Markdown**: tạo `sprint{N}_backlog.md` với bảng weekly + EPIC breakdown.\n\n### Cấu trúc Output Files\n- `sprint{N}_backlog.json` - Source of truth nội bộ (định dạng JSON, UTF-8) - **ghi vào `$REPORT_OUTPUT_DIR/.tmp/` (ẩn, không hiện chip/file list), KHÔNG share cho user, KHÔNG liệt kê trong output deliverables**\n- `sprint{N}_Project_Plan.xlsx` - Excel Project Plan (Sheet: Sprint N, template `json_to_excel.py`) - share cho user\n- `sprint{N}_Sprint_Backlog.xlsx` - Excel Detailed Sprint Backlog (Sheet: Sprint N, template `json_to_excel_v2.py`) - share cho user\n- `sprint{N}_backlog.md` - Báo cáo Markdown (weekly summary + phase/milestone) - share cho user\n\n> **⛔ Chỉ share 3 file cho user: `sprint{N}_Project_Plan.xlsx` + `sprint{N}_Sprint_Backlog.xlsx` + `sprint{N}_backlog.md`.** File `sprint{N}_backlog.json` là source of truth nội bộ (dùng để validate + export Excel), tồn tại ẩn trong `$REPORT_OUTPUT_DIR/.tmp/` - không `present_files`, không liệt kê trong phần \"Danh sách Output Deliverables\" của `.md`, không copy ra top-level `$REPORT_OUTPUT_DIR/`.\n>\n> **⛔ File `sprint{N}_backlog.md` KHÔNG chứa bảng chi tiết từng task (Task Breakdown).** Chỉ gồm các phần tóm tắt: (1) Tổng quan Sprint, (2) Phân bổ nhân sự & Manday summary, (3) Phase & Milestone Timeline, (4) Danh sách Output Deliverables, (5) Pre-flight Checklist Verification. Chi tiết từng task (task name, PIC, effort, start/end date, notes) chỉ nằm trong `.json` và các file `.xlsx` - không lặp lại trong `.md`.",
      "envVars": [
        {
          "name": "REPORT_OUTPUT_DIR",
          "description": "Thư mục xuất các file báo cáo, biểu đồ, kết quả chạy skill",
          "default": "outputs",
          "category": "System",
          "isSecret": false
        },
        {
          "name": "SKILL_DIR",
          "description": "Đường dẫn thư mục skill hiện hành (hệ thống tự inject)",
          "default": "./skills",
          "category": "System",
          "isSecret": false
        }
      ]
    },
    {
      "id": "sprint-timeline-chart",
      "name": "sprint-timeline-chart",
      "category": "Visualization & Charts",
      "icon": "bi-pie-chart",
      "description": "Tạo biểu đồ Timeline Gantt + Resource Pie Chart (phân bổ effort/manday) cho sprint/dự án dưới dạng file HTML tương tác. Sử dụng khi user cung cấp thông tin sprint dưới dạng text, markdown, hoặc mô tả (kế hoạch sprint, sprint backlog tổng hợp, resource plan, effort breakdown) và muốn xuất ra file HTML dashboard trực quan gồm: Gantt chart các phase, biểu đồ tròn phân bổ manday theo role, và danh sách milestone. Trigger ngay khi user nói: tạo timeline, vẽ gantt, thống kê effort, phân bổ manday, resource chart, sprint chart, dashboard sprint, tạo biểu đồ sprint, xuất HTML timeline, hoặc gắn file/text tổng hợp sprint và nhờ tạo biểu đồ - kể cả khi không dùng đúng từ khóa trên.",
      "triggers": [
        "tạo timeline",
        "vẽ gantt",
        "thống kê effort",
        "phân bổ manday",
        "resource chart",
        "sprint chart",
        "dashboard sprint",
        "tạo biểu đồ sprint"
      ],
      "guidelineMarkdown": "# Sprint Timeline & Resource Chart Skill\n\nSkill này nhận input dạng text/markdown mô tả sprint, parse thành JSON chuẩn, rồi inject vào HTML template để tạo dashboard trực quan.\n\n## Workflow tổng quát\n\n1. **Parse input** → Trích xuất thông tin từ text/markdown/file đầu vào\n2. **Build JSON** → Tạo project JSON theo schema chuẩn\n3. **Generate HTML** → Inject JSON vào template, xuất file HTML\n4. **Present file** → Trả file cho user\n\n---\n\n## Bước 1: Parse Input\n\nInput có thể là:\n- **Text tổng hợp sprint** (mô tả tự do): trích xuất thông tin key\n- **Markdown table** (sprint backlog): đọc phases, stories, timeline\n- **Danh sách bullet**: tìm dates, roles, effort\n- **Kết hợp các format trên**\n\n### Thông tin cần trích xuất:\n\n| Field | Mô tả | Ví dụ |\n|-------|-------|-------|\n| `projectName` | Tên dự án / sprint | \"FCR Sprint 3\" |\n| `startDate` | Ngày bắt đầu (YYYY-MM-DD) | \"2026-04-20\" |\n| `endDate` | Ngày kết thúc (YYYY-MM-DD) | \"2026-05-29\" |\n| `teamSize` | Tổng số người | 6 |\n| `teamComposition` | Mô tả team | \"1 PM, 1 BA, 2 DEV, 2 QC\" |\n| `resources` | Mảng phân bổ MD theo role | xem schema |\n| `phases` | Các phase trong sprint | xem schema |\n| `milestones` | Các mốc quan trọng | xem schema |\n\n### Quy tắc parse thông minh:\n\n- Nếu chỉ có tổng MD không có breakdown: phân bổ theo tỷ lệ mặc định PM:BA:DEV:QC = 1:1.1:5:1.7\n- Nếu không có phases rõ ràng: tạo phases mặc định (Requirement & Planning, Development, Testing, UAT, Go-live)\n- Nếu milestones không có status: gán `\"notstarted\"`, trừ milestone có date ≤ ngày hiện tại → `\"done\"`\n- Dates dạng dd/mm/yyyy hoặc dd-mm-yyyy → convert sang YYYY-MM-DD\n- Nếu thiếu thông tin quan trọng: hỏi user trước khi generate\n\n---\n\n## Bước 2: Build JSON\n\nTạo JSON theo schema sau, **không thêm bất kỳ field nào ngoài schema**:\n\n```json\n{\n  \"projectName\": \"string\",\n  \"startDate\": \"YYYY-MM-DD\",\n  \"endDate\": \"YYYY-MM-DD\",\n  \"teamSize\": number,\n  \"teamComposition\": \"string\",\n  \"resources\": [\n    { \"role\": \"PM\", \"md\": number, \"color\": \"#534AB7\" },\n    { \"role\": \"BA\", \"md\": number, \"color\": \"#1D9E75\" },\n    { \"role\": \"DEV\", \"md\": number, \"color\": \"#378ADD\" },\n    { \"role\": \"QC\", \"md\": number, \"color\": \"#EF9F27\" }\n  ],\n  \"phases\": [\n    {\n      \"label\": \"string\",\n      \"start\": \"YYYY-MM-DD\",\n      \"end\": \"YYYY-MM-DD\",\n      \"color\": \"hex color\"\n    }\n  ],\n  \"milestones\": [\n    {\n      \"name\": \"string\",\n      \"date\": \"YYYY-MM-DD\",\n      \"status\": \"done|inprogress|notstarted\"\n    }\n  ]\n}\n```\n\n### Màu chuẩn cho phases:\n\n| Phase | Color |\n|-------|-------|\n| Requirement & Planning | `#378ADD` |\n| Development | `#A78FDD` |\n| Testing / QA | `#EF9F27` |\n| UAT | `#5B8FF9` |\n| Pilot / Go-live | `#639922` |\n| Bug Fix | `#E05C5C` |\n| Deployment | `#1D9E75` |\n\n### Màu chuẩn cho roles (có thể mở rộng):\n\n| Role | Color |\n|------|-------|\n| PM | `#534AB7` |\n| BA | `#1D9E75` |\n| DEV | `#378ADD` |\n| QC / QA | `#EF9F27` |\n| DevOps | `#E05C5C` |\n| Designer | `#F472B6` |\n\n---\n\n## Bước 3: Generate HTML\n\n### Template path (theo thứ tự ưu tiên):\n1. `assets/template.html` (relative, cùng thư mục SKILL.md)\n2. `/mnt/skills/user/sprint-timeline-chart/assets/template.html` (absolute fallback)\n\n> Nếu cả hai đều không đọc được → báo user, dừng lại.\n\n### Script Python inject JSON:\n\n```python\nimport json, re, os, sys\n# Dùng _shared cạnh skill (webapp/skills/_shared) - không phụ thuộc ~/.claude/skills.\n_HERE = os.path.dirname(os.path.abspath(__file__)) if '__file__' in dir() else os.environ.get(\"SKILL_DIR\", \".\")\nsys.path.insert(0, os.path.join(_HERE, \"..\", \"..\", \"_shared\"))\nfrom output_path import ensure_output_dir, safe_name\n\ntemplate_path = os.path.join(os.environ.get(\"SKILL_DIR\", \"/mnt/skills/user/sprint-timeline-chart\"), \"assets/template.html\")\n# Sanitize slug - chỉ [a-z0-9-], chống path traversal qua tên dự án.\nslug = safe_name(project_json.get(\"project_slug\") or \"project\").lower()\ndate = project_json.get(\"date\") or __import__(\"datetime\").date.today().isoformat()\noutput_path   = f\"{ensure_output_dir()}/timeline_{slug}_{date}.html\"\n\nwith open(template_path, \"r\", encoding=\"utf-8\") as f:\n    html = f.read()\n\n# Escape </script> trong JSON - chống HTML injection đóng tag script sớm.\nnew_json = json.dumps(project_json, ensure_ascii=False, indent=2).replace(\"</\", \"<\\\\/\")\npattern  = r'(<script id=\"project-data\" type=\"application/json\">)(.*?)(</script>)'\nnew_html = re.sub(pattern, lambda m: f'{m.group(1)}\\n{new_json}\\n{m.group(3)}', html, flags=re.DOTALL)\n\nwith open(output_path, \"w\", encoding=\"utf-8\") as f:\n    f.write(new_html)\n```\n\n**Quy tắc output:**\n- File output = `template.html` gốc với **duy nhất phần JSON được thay thế** - không thêm, không bớt bất cứ thứ gì khác\n- Tên file: `timeline_{project_slug}_{YYYYMMDD}.html`\n- Lưu tại: `/mnt/user-data/outputs/`\n\n---\n\n## Bước 4: Present File\n\nDùng `present_files` tool để trả file HTML cho user. **Không kèm giải thích hay tóm tắt.**\n\n---\n\n## Ví dụ Input → Output\n\n### Input (text tổng hợp):\n```\nSprint 3 - Dự án FCR\nThời gian: 20/04/2026 - 29/05/2026\nTeam: 1 PM, 1 BA, 2 DEV, 2 QC (6 người)\n\nEffort breakdown:\n- PM: 9.75 MD\n- BA: 10.75 MD  \n- DEV: 48.5 MD\n- QC: 16 MD\n\nPhases:\n- Requirement & Planning: 20/04 - 29/04\n- Development: 20/04 - 18/05\n- Testing: 15/05 - 22/05\n- UAT: 22/05 - 27/05\n- Pilot: 27/05 - 29/05\n\nMilestones:\n- Sprint Planning Complete: 29/04 (in progress)\n- Dev Complete: 18/05 (in progress)\n- Sprint Review: 25/05\n- Production Deployment: 27/05\n- Go-Live: 29/05\n```\n\n### Output JSON:\n```json\n{\n  \"projectName\": \"FCR Sprint 3\",\n  \"startDate\": \"2026-04-20\",\n  \"endDate\": \"2026-05-29\",\n  \"teamSize\": 6,\n  \"teamComposition\": \"1 PM, 1 BA, 2 DEV, 2 QC\",\n  \"resources\": [\n    { \"role\": \"PM\", \"md\": 9.75, \"color\": \"#534AB7\" },\n    { \"role\": \"BA\", \"md\": 10.75, \"color\": \"#1D9E75\" },\n    { \"role\": \"DEV\", \"md\": 48.5, \"color\": \"#378ADD\" },\n    { \"role\": \"QC\", \"md\": 16, \"color\": \"#EF9F27\" }\n  ],\n  \"phases\": [\n    { \"label\": \"Requirement & Planning\", \"start\": \"2026-04-20\", \"end\": \"2026-04-29\", \"color\": \"#378ADD\" },\n    { \"label\": \"Development\", \"start\": \"2026-04-20\", \"end\": \"2026-05-18\", \"color\": \"#A78FDD\" },\n    { \"label\": \"Testing\", \"start\": \"2026-05-15\", \"end\": \"2026-05-22\", \"color\": \"#EF9F27\" },\n    { \"label\": \"UAT\", \"start\": \"2026-05-22\", \"end\": \"2026-05-27\", \"color\": \"#5B8FF9\" },\n    { \"label\": \"Pilot\", \"start\": \"2026-05-27\", \"end\": \"2026-05-29\", \"color\": \"#639922\" }\n  ],\n  \"milestones\": [\n    { \"name\": \"Sprint Planning Complete\", \"date\": \"2026-04-29\", \"status\": \"inprogress\" },\n    { \"name\": \"Dev Complete\", \"date\": \"2026-05-18\", \"status\": \"inprogress\" },\n    { \"name\": \"Sprint Review\", \"date\": \"2026-05-25\", \"status\": \"notstarted\" },\n    { \"name\": \"Production Deployment\", \"date\": \"2026-05-27\", \"status\": \"notstarted\" },\n    { \"name\": \"Go-Live\", \"date\": \"2026-05-29\", \"status\": \"notstarted\" }\n  ]\n}\n```\n\n---\n\n## Lưu ý quan trọng\n\n- **Không hardcode** màu sắc hoặc cấu trúc layout - template đã handle tất cả\n- **Validate dates**: đảm bảo tất cả phases/milestones nằm trong khoảng `startDate` → `endDate`\n- **MD phải là số thực** (float), không phải string\n- Nếu user muốn **update** file đã có: đọc lại JSON hiện tại, merge thay đổi, generate lại\n- Nếu input có **nhiều sprint**: tạo file HTML riêng cho mỗi sprint, đặt tên khác nhau",
      "envVars": [
        {
          "name": "REPORT_OUTPUT_DIR",
          "description": "Thư mục xuất các file báo cáo, biểu đồ, kết quả chạy skill",
          "default": "outputs",
          "category": "System",
          "isSecret": false
        },
        {
          "name": "SKILL_DIR",
          "description": "Đường dẫn thư mục skill hiện hành (hệ thống tự inject)",
          "default": "./skills",
          "category": "System",
          "isSecret": false
        }
      ]
    },
    {
      "id": "vn-stock-advisor",
      "name": "vn-stock-advisor",
      "category": "Finance & Investment",
      "icon": "bi-graph-up-arrow",
      "description": "\"Phân tích đa tầng chứng khoán Việt Nam (4-Pillar Pro): Vĩ mô Liên thị trường (Yahoo Finance/News RSS) + Định giá Giá trị thực & 5 Trụ cột (Simplize) + Dòng tiền Cá mập Big Boys & Tâm lý Đám đông (TopInvest) + Tín hiệu Kỹ thuật Finbox DCS & Ma trận Siêu Hội Tụ 100 điểm với Kỷ luật Chặn Hòa Vốn (+5%).\"",
      "triggers": [
        "chứng khoán",
        "thị trường chứng khoán",
        "cổ phiếu",
        "phân tích cổ phiếu",
        "điểm mua",
        "điểm bán",
        "cắt lỗ",
        "chốt lời",
        "finbox",
        "watchlist cổ phiếu",
        "danh mục cổ phiếu",
        "khuyến nghị cổ phiếu",
        "vĩ mô",
        "simplize",
        "topinvest",
        "dòng tiền lớn",
        "cá mập"
      ],
      "guidelineMarkdown": "# Kỹ năng Phân tích Thị trường Chứng khoán Việt Nam Đa Tầng (4-Pillar Pro Edition)\n\nKỹ năng chuyên sâu hỗ trợ Nhà đầu tư và Chuyên viên phân tích thị trường chứng khoán Việt Nam (HOSE, HNX, UPCOM). Kỹ năng kết hợp sức mạnh từ 4 trụ cột định lượng độc lập:\n1. **Toàn cảnh Vĩ mô Liên thị trường & Tin tức**: DXY, Lợi suất US10Y, Tỷ giá USD/VND, Dầu Brent, Vàng, Chứng khoán Quốc tế (Yahoo Finance) và Điểm tin tài chính (Google News VN / CafeF).\n2. **Định giá Giá trị Thực & Sức khỏe Tài chính 5 Trụ cột (Mô hình Simplize Snowflake)**: P/E, P/B điều chỉnh theo ROE so với Trung vị Ngành, ước tính Fair Value và Biên an toàn (Margin of Safety %).\n3. **Dòng tiền Thông minh & Tâm lý Đám đông (Triết lý TopInvest 'Follow the Bigboys')**: Bóc tách dấu chân Cá mập gom hàng / gom ngầm nền giá / kéo xả phân phối đỉnh, Chỉ số Tâm lý Đám đông (Crowd Sentiment 0-100), Radar Luân chuyển Dòng tiền Ngành.\n4. **Hệ thống Tín hiệu Finbox DCS & Ma trận Siêu Hội Tụ 4 Lớp (Confluence Score 0-100 điểm)**: Kỷ luật quản trị rủi ro bất bại với Quy tắc Chặn Hòa Vốn (+5% Breakeven Trigger) và Chốt lời 3 nấc.\n\n---\n\n## 1. Năng Lực Cốt Lõi\n\n1. **Tổng quan thị trường & Độ rộng dòng tiền**:\n   - Thống kê tỷ lệ mã Tăng / Giảm / Tham chiếu toàn thị trường.\n   - Thống kê cán cân dòng tiền Khối Ngoại (Mua ròng / Bán ròng).\n   - Tỷ lệ tín hiệu Mua / Bán của hệ thống Finbox (`ratio`).\n   - Diễn biến các chỉ số sàn (`VNINDEX`, `VN30`, `HNX`, `UPCOM`).\n\n2. **Khuyến nghị Điểm Mua / Điểm Bán chuẩn xác**:\n   - **Vùng mua (Entry Zone)**: Quanh giá hiện tại hoặc điểm breakout/pullback (-1.5% đến +1.5%).\n   - **Cắt lỗ (Stop Loss)**: Ngưỡng rủi ro nghiêm ngặt -5% đến -7% (hoặc dưới hỗ trợ cứng).\n   - **Mục tiêu 1 (Target 1)**: +8% đến +10% (Chốt lời chủ động 50% để bảo toàn vốn).\n   - **Mục tiêu 2 (Target 2)**: +18% đến +25% (Sóng tăng trung hạn).\n   - **Tỷ lệ R:R (Risk/Reward)**: Tối thiểu 1.5:1 đến 2:1 mới kích hoạt khuyến nghị Mua mới.\n\n3. **Lọc cổ phiếu tiềm năng (Top Picks)**:\n   - Sàng lọc theo tiêu chuẩn Finbox Rating cao (`A+`, `A`, `B+`).\n   - Lọc thanh khoản an toàn: Giá trị giao dịch trung bình 20 phiên (`tbgtdd`) $\\ge$ 3 tỷ VNĐ/phiên.\n   - Bắt tín hiệu bùng nổ khối lượng (`%Vol vs 20N` $\\ge 120\\%$) hoặc tín hiệu `BIG BUY`, `PULLBACK`.\n\n4. **Theo dõi Danh mục Đầu tư (Portfolio / Watchlist)**:\n   - Tính toán lãi/lỗ theo thời gian thực (Unrealized PnL).\n   - Cảnh báo tức thì khi cổ phiếu vi phạm ngưỡng cắt lỗ (Stop Loss Triggered) hoặc chạm mục tiêu (Target Hit).\n   - Đưa ra lời khuyên cụ thể cho từng vị thế: Nắm giữ (Hold), Nâng trailing stop, Chốt lời từng phần, hoặc Cắt lỗ khẩn cấp.\n\n---\n\n## 2. Hướng Dẫn Sử Dụng\n\n### 2.1. Chạy CLI Runner\n\nScript runner chính nằm tại: `skills/vn-stock-advisor/scripts/run_stock_advisor.py`\n\n#### A. Phân tích tổng quan thị trường & Top cổ phiếu tiềm năng:\n```bash\npython3 skills/vn-stock-advisor/scripts/run_stock_advisor.py\n```\n\n#### B. Phân tích chuyên sâu 1 mã cổ phiếu (Kèm điểm mua/bán, EPS, ROE, Nợ/VCSH, lịch sử lệnh):\n```bash\npython3 skills/vn-stock-advisor/scripts/run_stock_advisor.py --ticker FPT\n```\n\n#### C. Lọc cổ phiếu chỉ có tín hiệu Mua hoặc Vol bùng nổ:\n```bash\npython3 skills/vn-stock-advisor/scripts/run_stock_advisor.py --only-signals --min-rating A\n```\n\n#### D. Theo dõi danh mục đầu tư thực tế:\n```bash\npython3 skills/vn-stock-advisor/scripts/run_stock_advisor.py --watchlist '[{\"symbol\":\"FPT\",\"buy_price\":64.0,\"quantity\":1000,\"buy_date\":\"2026-09-01\"},{\"symbol\":\"SSI\",\"buy_price\":32.5,\"quantity\":2000,\"buy_date\":\"2026-09-10\"}]'\n```\n\n#### E. Lọc cổ phiếu theo Ngôn Ngữ Tự Nhiên (Natural Language Query):\n```bash\n# Lọc ngành, sàn, rating, thanh khoản và giá:\npython3 skills/vn-stock-advisor/scripts/run_stock_advisor.py --query \"tìm cổ phiếu ngân hàng sàn HOSE rating A giá trên 20 thanh khoản trên 10 tỷ\"\n\n# Lọc cổ phiếu bắt đáy hoặc tích lũy:\npython3 skills/vn-stock-advisor/scripts/run_stock_advisor.py --query \"các mã thép đang có tín hiệu bắt đáy dip mua\"\n\n# Lọc định giá cơ bản (P/E, ROE):\npython3 skills/vn-stock-advisor/scripts/run_stock_advisor.py --query \"cổ phiếu bluechip ROE trên 15% PE dưới 15\"\n```\n\n---\n\n## 3. Đặc Tả Toàn Diện API Bộ Lọc Finbox (DCS Filter API Specification)\n\nToàn bộ các select box và thanh trượt trên màn hình `https://www.finbox.vn/signals-list` được ánh xạ về endpoint:\n- **URL**: `POST https://dcs.finbox.vn/data/filter`\n- **Headers**: `Content-Type: application/json` (Không cần Token/Auth)\n\n### 3.1. Cấu trúc Payload\n\n```json\n{\n  \"date\": \"20260408\",\n  \"values\": [\n    {\"header\": \"category\", \"value\": [\"Cổ phiếu\"]},\n    {\"header\": \"industry\", \"value\": [\"Ngân hàng\", \"Thép\", \"Bất động sản\"]},\n    {\"header\": \"rating\", \"value\": [\"A+\", \"A\", \"A-\", \"B+\"]},\n    {\"header\": \"floor\", \"value\": [\"HOSE\", \"HNX\", \"UPCOM\"]},\n    {\"header\": \"trend\", \"value\": [\"TĂNG\", \"GIẢM\", \"TRUNG LẬP\"]},\n    {\"header\": \"signal\", \"value\": [\"BUY\", \"BIG BUY\", \"SMALL BUY\", \"BIG SELL\", \"SMALL SELL\"]},\n    {\"header\": \"dip_signal\", \"value\": [\"SMALL DIP\", \"BIG DIP\", \"DIP\"]}\n  ],\n  \"conditions\": [\n    {\n      \"header\": \"priceFlat\",\n      \"id\": 9,\n      \"value\": {\"minValue\": 20.0, \"maxValue\": 50.0}\n    },\n    {\n      \"header\": \"tbgtdd\",\n      \"id\": 7,\n      \"value\": {\"singleValue\": 10.0}\n    },\n    {\n      \"header\": \"pe\",\n      \"id\": 8,\n      \"value\": {\"singleValue\": 15.0}\n    }\n  ],\n  \"sort\": [{\"volumePercent\": \"desc\"}, {\"tbgtdd\": \"desc\"}],\n  \"returns\": [\"ticker\", \"priceFlat\", \"pricePercent\", \"rating\", \"score\", \"trend\", \"volumeFlat\", \"volumePercent\", \"signal\", \"dip_signal\", \"dip_price\", \"tbgtdd\", \"vonhoa\", \"roe\", \"roa\", \"pe\", \"pb\", \"eps\", \"industry\", \"floor\"],\n  \"limit\": 50\n}\n```\n\n### 3.2. Bảng Mã Operator IDs cho `conditions` (Numeric Filters)\n- **`id = 9` (Range/Between)**: Yêu cầu object `value: {\"minValue\": X, \"maxValue\": Y}`\n- **`id = 7` (Greater than or equal $\\ge$)**: Yêu cầu object `value: {\"singleValue\": X}`\n- **`id = 8` (Less than or equal $\\le$)**: Yêu cầu object `value: {\"singleValue\": X}`\n\nCác trường số học hỗ trợ: `priceFlat`, `pricePercent`, `volumeFlat`, `volumePercent`, `tbgtdd` (tỷ VNĐ), `vonhoa` (tỷ VNĐ), `pe`, `pb`, `roe`, `roa`, `eps`.\n\n### 3.3. Endpoint Chuyên Biệt Bắt Đáy (Dip Buying API)\n- **URL**: `POST https://dcs.finbox.vn/data/dip`\n- **Mục đích**: Lọc các cổ phiếu rơi vào trạng thái quá bán, chiết khấu sâu từ đỉnh và có tín hiệu tạo đáy kỹ thuật.\n- **Trường dữ liệu độc quyền**:\n  - `low_rsi`: Chỉ số RSI thấp nhất ghi nhận tại vùng đáy.\n  - `rsi`: Chỉ số RSI hiện tại.\n  - `dip_signal`: Tín hiệu bắt đáy (`SMALL DIP`, `BIG DIP`).\n  - `dip_price`: Mức giá xuất hiện tín hiệu bắt đáy.\n  - `discount_5`, `discount_10`, `discount_20`, `discount_60`: Mức chiết khấu giá (%) so với mức đỉnh 5, 10, 20 và 60 phiên gần nhất.\n- **Cách gọi qua CLI**:\n  ```bash\n  python3 skills/vn-stock-advisor/scripts/run_stock_advisor.py --dip\n  # hoặc qua ngôn ngữ tự nhiên:\n  python3 skills/vn-stock-advisor/scripts/run_stock_advisor.py --query \"các mã có tín hiệu bắt đáy hôm nay\"\n  ```\n\n### 3.4. Cơ Chế Tín Hiệu Sớm: Pre-Buy & Pre-Sell (Chờ Mua / Chờ Bán)\n- **Bản chất**:\n  - `CHỜ MUA` (`PRE BUY`) và `CHỜ BÁN` (`PRE SELL`) là các **tín hiệu cảnh báo sớm trong phiên (Intraday Realtime Early Signals)**.\n  - Được kích hoạt khi giá tiệm cận ngưỡng Breakout mua hoặc gãy hỗ trợ bán trước khi phiên đóng cửa hoặc trước khi đạt đủ khối lượng xác nhận.\n- **Vòng đời tín hiệu (Lifecycle)**:\n  - Trong phiên: Hiển thị `CHỜ MUA` / `CHỜ BÁN` trong tab Tín hiệu cơ sở (TradingBox) và thông báo đẩy Realtime (`/notifications/list` trên `api2.finbox.vn`).\n  - Hết phiên (EOD): Khi điều kiện khối lượng & giá đóng cửa được xác nhận đầy đủ, hệ thống chuyển thành tín hiệu chính thức: `BUY`, `BIG BUY`, `SMALL BUY` hoặc `SELL`, `BIG SELL`, `SMALL SELL`. Nếu không đạt, tín hiệu tự hủy.\n- **Danh mục khuyến nghị cơ sở TradingBox (`/kn/all`)**:\n  - `top`: Top Khuyến nghị (chiến lược tỷ suất sinh lời tối ưu nhất).\n  - `tc`: Danh mục Tiêu chuẩn.\n  - `pt`: Danh mục Phổ thông.\n\n---\n\n## 4. Đầu Ra & Phản Hồi Tin Nhắn (Output Contract)\n\n- **KHÔNG tạo hay xuất file `.md`** (không ghi file báo cáo ra đĩa và không gọi tool `Write` tạo file `.md`).\n- Script `run_stock_advisor.py` in trực tiếp toàn bộ dữ liệu phân tích và bảng chỉ số ra `stdout`.\n- Sau khi chạy script, AI tổng hợp và trình bày trực tiếp báo cáo phân tích rõ ràng, đầy đủ ngay trong tin nhắn chat phản hồi cho người dùng.\n\n---\n\n## 5. Cấu Trúc Mã Nguồn\n\n- `finbox_client.py`: API Client kết nối trực tiếp `https://dcs.finbox.vn` (Dashboard, Index, Ticker Detail, History, Highlighting).\n- `signal_engine.py`: Động cơ tính toán điểm mua, điểm bán, vùng dừng lỗ, mục tiêu chốt lời và tỷ lệ R:R.\n- `portfolio_tracker.py`: Quản lý danh mục, tính PnL và phát hiện cảnh báo rủi ro vị thế.\n- `run_stock_advisor.py`: Script điều phối chính, nhận CLI arguments và in kết quả phân tích ra `stdout` để tổng hợp trực tiếp trong tin nhắn chat.",
      "envVars": [
        {
          "name": "FINBOX_TIMEOUT",
          "description": "Thời gian timeout cho các request tới Finbox API (giây)",
          "default": "15",
          "category": "Stock",
          "isSecret": false
        },
        {
          "name": "FINBOX_PROXY",
          "description": "Proxy HTTP khi truy cập API Finbox",
          "default": "http://proxy.hcm.fpt.vn:80",
          "category": "Stock",
          "isSecret": false
        },
        {
          "name": "REPORT_OUTPUT_DIR",
          "description": "Thư mục xuất các file báo cáo, biểu đồ, kết quả chạy skill",
          "default": "outputs",
          "category": "System",
          "isSecret": false
        }
      ]
    },
    {
      "id": "weekly-report-api",
      "name": "weekly-report-api",
      "category": "Jira & Reporting",
      "icon": "bi-bar-chart-line",
      "description": "\"Tạo báo cáo tiến độ tuần (Weekly Report) cho cả dự án Agile/Scrum (có sprint) và dự án Waterfall/Kanban (không sprint). Sử dụng khi cần: báo cáo tuần, báo cáo sprint, tổng kết tiến độ, weekly status update, sprint progress report, waterfall status report. Hỗ trợ 3 nguồn dữ liệu: Jira REST API, Google Sheets (service account), và Excel (.xlsx). Trigger khi user nói: báo cáo tuần, làm weekly report, tổng kết tuần, update tiến độ, làm report sprint, report waterfall, báo cáo cho stakeholder, hay bất kỳ yêu cầu nào liên quan đến tạo báo cáo tuần.\"",
      "triggers": [
        "báo cáo tuần",
        "làm weekly report",
        "tổng kết tuần",
        "update tiến độ",
        "làm report sprint",
        "report waterfall",
        "báo cáo cho stakeholder"
      ],
      "guidelineMarkdown": "## ⚠️ CẢNH BÁO QUAN TRỌNG - Đọc TRƯỚC KHI CHẠY\n\n**PHẢI** kiểm tra input của user về:\n1. **Loại dự án / Phương pháp quản lý:**\n   - **🟢 Agile / Scrum (có sprint)**: Cần `project-key` + `sprint-name` (hoặc `sprint-id`).\n   - **🔵 Waterfall / Kanban (không có sprint)**: **KHÔNG ĐƯỢC HỎI SPRINT NAME/ID**. Dùng cờ `--waterfall`. Có thể kèm theo `--fix-version` / `--jql` / `--start-date` / `--end-date` nếu user cung cấp.\n2. **Nguồn dữ liệu:**\n   - **NẾU user cung cấp Google Sheet ID** (ví dụ: \"1lYJrm...\", \"sheet id là...\", \"đọc từ Sheet...\", **\"data google sheet\"**) → **BẮT BUỘC** dùng `--sheet-id`\n   - **NẾU user gửi file Excel** (.xlsx) → **BẮT BUỘC** dùng `--excel`\n   - **NẾU không có Sheet/Excel** → Mặc định Jira API\n\nScript `run_weekly_report.py` sẽ tự động fallback về Jira-only nếu thiếu `--sheet-id`/`--excel`.\n\n> ⚠️ **TRƯỜNG HỢP ĐẶC BIỆT**: Nếu user nói **\"data google sheet (ID), start/due sprint lấy từ jira\"** → vẫn **PHẢI dùng `--sheet-id`** vì backlog từ Sheet! Script sẽ tự động lấy sprint dates từ Jira trước, rồi lấy backlog từ Sheet (Bước 1/3 + 2/3).\n\n> 🛑 **XỬ LÝ LỖI XÁC THỰC & MÃ DỰ ÁN**:\n> - Nếu pipeline báo lỗi `LỖI MÃ DỰ ÁN` (mã dự án không tồn tại trên Jira hoặc tài khoản chưa được cấp quyền truy cập): **DỪNG LẠI** và thông báo người dùng kiểm tra lại mã dự án chính xác (ví dụ: FCR, FSM, ISC, SAL...). **TUYỆT ĐỐI KHÔNG** báo nhầm sang lỗi hết hạn token.\n> - Nếu pipeline báo lỗi `Thiếu credential`, `LỖI XÁC THỰC JIRA`, hoặc `HTTP 401 Unauthorized` khi kiểm tra auth: **DỪNG LẠI NGAY LẬP TỨC**. Thông báo lịch sự cho người dùng: *\"Không thể kết nối tới Jira do thông tin xác thực (Jira Email / API Token) chưa được cấu hình hoặc đã hết hạn. Vui lòng vào mục Cài đặt cá nhân để cập nhật token hợp lệ.\"*\n> - **TUYỆT ĐỐI CẤM** chạy lệnh Bash để truy vấn database (`psql`, `mysql`...), đọc file cấu hình hệ thống (`.env`, backend source code), hoặc gọi công cụ email (`mcp__outlook_*`, `mcp__gmail_*`) để tìm kiếm token. Mọi hành vi này đều vi phạm nghiêm trọng chính sách bảo mật của hệ thống.\n\n## Nguồn dữ liệu hỗ trợ\n\n| Nguồn | Yêu cầu |\n|-------|---------|\n| Jira REST API | Email + API token (Agile: Sprint; Waterfall: JQL / FixVersion / Project) |\n| Google Sheets | Service account JSON key |\n| Excel (.xlsx / SharePoint) | File .xlsx cục bộ hoặc link chia sẻ SharePoint/OneDrive (Microsoft Graph API) |\n\n---\n\n## Quy tắc bắt buộc - Kiểm tra nguồn dữ liệu TRƯỚC KHI CHẠY\n\nKHÔNG bao giờ tự động bắt đầu tạo output khi user mới đặt yêu cầu.\n\nQuy trình chuẩn:\n1. **TRƯỚC TIÊN**: Kiểm tra xem user có cung cấp Google Sheet ID hoặc file Excel không\n   - Tìm keyword: \"google sheet\", \"sheet id\", **\"data google sheet\"**, \"spreadsheet\", \"1lYJrm...\", \".xlsx\"\n   - **NẾU có Sheet ID/Excel → BẮT BUỘC dùng `--sheet-id` hoặc `--excel`**\n   - **NẾU không có → Mặc định dùng Jira API**\n2. **Kiểm tra phương pháp quản lý**:\n   - Nếu user nói **\"waterfall\"**, **\"không sprint\"**, **\"không có sprint\"**, **\"kanban\"** → Chạy luồng **Waterfall**.\n   - **⚠️ NẾU input có `parent_id: XYZ`** (ví dụ: \"project key ISC, parent_id: ISC-20. Báo cáo tiến độ dự án Waterfall\") → **BẮT BUỘC** dùng `--parent-key ISC-20`. Script sẽ tự động lấy `startDate` và `dueDate` từ Epic/Parent đó trên Jira để xác định timeline dự án. **KHÔNG** dùng `--waterfall` riêng lẻ khi đã có `parent_id`.\n   - Nếu Waterfall nhưng **không có `parent_id`** → Dùng `--waterfall` (không hỏi sprint).\n   - Nếu là Agile mà thiếu sprint name → hỏi sprint name.\n3. Fetch data tự động (không cần xác nhận thêm) và tạo report.\n\n---\n\n## Môi trường runtime (webapp)\n\n> ⚠️ **FORMAT COMMAND BẮT BUỘC**: Mọi lệnh Bash trong webapp **PHẢI** có prefix đầy đủ:\n> ```bash\n> cd \"$SKILL_DIR\" && python3 scripts/run_weekly_report.py ...\n> ```\n\n### Fast path - 1 lệnh Bash (ưu tiên, nhanh nhất)\n\n#### 1. Luồng Agile (có sprint)\n**Nguồn Jira (mặc định)**:\n```bash\ncd \"$SKILL_DIR\" && python3 scripts/run_weekly_report.py \\\n  --project-key FSM --sprint-name \"Sprint 3\" --today 2026-07-23 \\\n  --output-dir \"$REPORT_OUTPUT_DIR\"\n```\n\n**Nguồn Google Sheet / Excel**:\n```bash\ncd \"$SKILL_DIR\" && python3 scripts/run_weekly_report.py \\\n  --project-key FSM --sprint-name \"Sprint 3\" --today 2026-07-23 \\\n  --sheet-id \"SHEET_ID\" --service-account \"$GOOGLE_SERVICE_ACCOUNT_PATH\" \\\n  --output-dir \"$REPORT_OUTPUT_DIR\"\n```\n\n#### 2. Luồng Waterfall (không có sprint)\n**Nguồn Jira - Theo Parent Request / Epic (Khuyến nghị)**:\nTự động lấy **Start Date**, **Due Date** và toàn bộ task con từ Parent Request / Epic:\n```bash\ncd \"$SKILL_DIR\" && python3 scripts/run_weekly_report.py \\\n  --project-key FSM --parent-key FSM-20 --today 2026-07-23 \\\n  --output-dir \"$REPORT_OUTPUT_DIR\"\n```\n\n**Nguồn Jira - Tổng quan toàn bộ project hoặc theo Version**:\n```bash\ncd \"$SKILL_DIR\" && python3 scripts/run_weekly_report.py \\\n  --project-key FSM --waterfall --today 2026-07-23 \\\n  --output-dir \"$REPORT_OUTPUT_DIR\"\n```\n*(Tùy chọn: có thể thêm `--fix-version \"v1.0\"`, `--start-date 2026-07-01`, `--end-date 2026-08-30`, hoặc `--jql \"...\"`)*\n\n**Nguồn Google Sheet / Excel (Waterfall)**:\n```bash\ncd \"$SKILL_DIR\" && python3 scripts/run_weekly_report.py \\\n  --project-key FSM --waterfall --sheet-id \"SHEET_ID\" \\\n  --service-account \"$GOOGLE_SERVICE_ACCOUNT_PATH\" --today 2026-07-23 \\\n  --output-dir \"$REPORT_OUTPUT_DIR\"\n```\n\nSau khi chạy pipeline xong và file `.md` được tạo, **tạo ngay bản tóm tắt rút gọn `.txt`** (`txtExpected`) theo **Quy tắc PM Sprint Summary** (xem mục bên dưới) trong cùng một lượt. **KHÔNG** gửi tin nhắn dở dang giữa chừng (như \"file .md đã xong, bản .txt sẽ tạo ở bước sau\"). Sau khi cả 2 file `.md` và `.txt` đã được tạo xong, gửi **1 tin nhắn báo cáo kết quả duy nhất** tóm tắt Health/SPI/RAG và nêu tên cả 2 file kết quả.\n\n---\n- **KHÔNG** `pip install` - dependency Python đã cài sẵn trong `webapp/.venv-skills` (`requests`, `openpyxl`, `gspread`, `google-auth`).\n- **KHÔNG** `curl` / test mạng thủ công - script Python tự thử direct/proxy (`network_utils.py`); guardrail chặn curl.\n- **KHÔNG** `unset` proxy - script tự fallback; webapp giữ HTTP_PROXY cho Google.\n- **KHÔNG** Read `/tmp/claude-*` và **KHÔNG** dùng Glob/ls tìm kiếm ngoài `$REPORT_OUTPUT_DIR` (như `/data/outputs/*`). Mọi JSON/log/report nằm trong `$REPORT_OUTPUT_DIR`.\n- **Chỉ** chạy script bằng Bash (`$SKILL_DIR` có sẵn trong env).\n\n---\n\n## Giao tiếp với user - không kể lể bước xử lý nội bộ\n\n**CHECKLIST TRƯỚC KHI CHẠY SCRIPT:**\n1. ✅ Đã kiểm tra xem user có cung cấp Google Sheet ID hoặc file Excel không?\n2. ✅ Dự án là Agile (cần sprint) hay Waterfall (dùng `--waterfall` hoặc `--parent-key`)?\n3. ✅ **NẾU input có `parent_id: XYZ`** → BẮT BUỘC dùng `--parent-key XYZ` (script tự lấy `startDate`/`dueDate` của Epic/Parent từ Jira để tính timeline dự án)!\n4. ✅ Nếu có Parent Request / Epic key riêng biệt (VD: `FSM-20`, `parent FSM-20`, `parent_id: FSM-20`) → thêm `--parent-key FSM-20`!\n5. ✅ Nếu có Sheet ID → đã thêm `--sheet-id` vào command?\n6. ✅ Nếu có file Excel → đã thêm `--excel` vào command?\n7. ✅ Nếu Waterfall / Parent Request → KHÔNG hỏi Sprint Name/ID!\n\nTuyệt đối **KHÔNG** tường thuật lại tên bước/thuật ngữ nội bộ của skill này trong câu trả lời cho user.\n\n---\n\n## Scripts\n\n| Script | Nguồn | Mô tả |\n|--------|-------|-------|\n| `scripts/jira_sprint_fetcher.py` | Jira REST API | Lấy metadata & issues (hỗ trợ cả Agile Sprint & Waterfall JQL) |\n| `scripts/weekly_report_generator.py` | Jira REST API | Fetch Jira → tính metrics → xuất JSON + Markdown (legacy) |\n| `scripts/fetch_gsheet_data.py` | Google Sheets | Đọc Google Sheet qua service account → xuất JSON |\n| `scripts/fetch_excel_data.py` | Excel (.xlsx) | Đọc file Excel → xuất JSON |\n| `scripts/generate_report_from_json.py` | Tất cả | Đọc standardized JSON → generate Markdown (Agile & Waterfall) |\n| `scripts/run_weekly_report.py` | Tất cả | 1 lệnh chạy toàn bộ pipeline tuần tự |\n  --today 2026-07-23 \\\n  --output-dir \"$REPORT_OUTPUT_DIR\"\n```\n\nScript tự gọi `jira_sprint_fetcher.py --fetch-issues` rồi `generate_report_from_json.py`.\n\n### Chỉ lấy sprint dates (không generate report)\n\n```bash\npython3 scripts/jira_sprint_fetcher.py \\\n    --project-key FSM \\\n    --sprint-name \"Sprint 3\" \\\n    --output-dir \"$REPORT_OUTPUT_DIR\"\n```\n\nHoặc khi đã biết sprint ID:\n\n```bash\npython3 scripts/jira_sprint_fetcher.py \\\n    --project-key FSM \\\n    --sprint-id 1234 \\\n    --output-dir \"$REPORT_OUTPUT_DIR\"\n```\n\nThêm `--fetch-issues` nếu cần export issues thủ công (thường không cần - dùng `run_weekly_report.py`).\n\n### Kết hợp Jira dates + Google Sheet backlog\n\n**Trường hợp phổ biến**: User nói *\"data google sheet (ID), start/due sprint lấy từ jira\"*\n\n→ Backlog từ Sheet, sprint dates từ Jira → **PHẢI dùng `--sheet-id`**\n\n```bash\ncd \"$SKILL_DIR\" && python3 scripts/run_weekly_report.py \\\n  --project-key FSM \\\n  --sprint-name \"Sprint 3\" \\\n  --sheet-id \"1lYJrm30p8cUqSuDFzsfAF7DYE5nDlmsv36JrRc2ZNQM\" \\\n  --service-account \"$GOOGLE_SERVICE_ACCOUNT_PATH\" \\\n  --today 2026-07-28 \\\n  --output-dir \"$REPORT_OUTPUT_DIR\"\n```\n\nPipeline tự động:\n1. **Bước 1/3** - Lấy sprint start/end từ Jira (`jira_sprint_fetcher.py`)\n2. **Bước 2/3** - Lấy backlog từ Google Sheet (`fetch_gsheet_data.py`)\n3. **Bước 3/3** - Generate report kết hợp\n\n> **KHÔNG** được bỏ qua `--sheet-id` chỉ vì user nhắc \"start/due từ jira\" - đó chỉ là hướng dẫn cho sprint dates, backlog vẫn từ Sheet!\n\n### Kết hợp Jira dates + Google Sheet backlog (cách thủ công, 2 script riêng)\n\nChỉ khi backlog nằm trên Sheet, sprint dates vẫn lấy từ Jira:\n\n```bash\npython3 scripts/fetch_gsheet_data.py \\\n    --sheet-id 1lYJrm30p8cUqSuDFzsfAF7DYE5nDlmsv36JrRc2ZNQM \\\n    --service-account \"$GOOGLE_SERVICE_ACCOUNT_PATH\" \\\n    --sprint-name \"Sprint 3\" \\\n    --today 2026-07-23 \\\n    --output-dir \"$REPORT_OUTPUT_DIR\" \\\n    --sprint-info \"$REPORT_OUTPUT_DIR/FSM_Sprint_3_sprint_info.json\"\n```\n\nRồi generate report - JSON đã có `sprint_start`/`sprint_end`/`project_key`, không cần truyền lại:\n\n```bash\npython3 scripts/generate_report_from_json.py \\\n    --input \"$REPORT_OUTPUT_DIR/gsheet_data_Sprint_3.json\" \\\n    --output-dir \"$REPORT_OUTPUT_DIR\" \\\n    --today 2026-07-23\n```\n\n### Cấu hình & Chạy (legacy all-in-one)\n\n```python\n# weekly_report_generator.py vẫn hardcode FCR - ưu tiên jira_sprint_fetcher + generate_report_from_json\nPROJECT_KEY = \"FCR\"\nSPRINT_NAME = \"FTI-FCR V1.7 Sprint 4\"\nSPRINT_ID = 1355\nOUTPUT_DIR = os.environ[\"REPORT_OUTPUT_DIR\"]\n```\n\n```bash\npython3 scripts/weekly_report_generator.py \"$JIRA_EMAIL\" \"$JIRA_API_TOKEN\"\n```\n\n### API Endpoints\n\n| Mục đích | Method | Endpoint |\n|----------|--------|----------|\n| Tìm board | GET | `/rest/agile/1.0/board?projectKeyOrId={key}` |\n| Tìm sprint | GET | `/rest/agile/1.0/board/{id}/sprint?state=active,future,closed` |\n| Search issues | POST | `/rest/api/3/search/jql` |\n| Auth | - | Basic Auth: `base64(email:api_token)` |\n\n> API `/rest/api/3/search/jql` dùng token-based pagination (`nextPageToken` + `isLast`).\n\n> **Múi giờ:** mọi timestamp Jira trả về (`startDate`, `endDate`, `duedate`, `resolutiondate`...) là\n> UTC (hậu tố `Z`). `parse_date()`/`fmt_date()` trong `generate_report_from_json.py` đã tự convert sang\n> UTC+7 trước khi lấy phần ngày - KHÔNG bao giờ cắt chuỗi ISO tại `\"T\"` để lấy ngày trực tiếp, vì giờ\n> UTC ≥ 17:00 sẽ lệch sang ngày hôm sau ở VN (VD `\"...T17:00:06Z\"` = `00:00` giờ VN ngày kế tiếp).\n\n---\n\n## Nguồn 2: Google Sheets\n\n### Yêu cầu\n- Service account JSON key file (đã cấp quyền Viewer cho sheet)\n- Google Sheet ID\n\n### Cấu hình & Chạy\n\n```bash\npython scripts/fetch_gsheet_data.py \\\n    --sheet-id <SPREADSHEET_ID> \\\n    --service-account \"$GOOGLE_SERVICE_ACCOUNT_PATH\" \\\n    --sprint-name \"Sprint 3\" \\\n    --today 2026-07-21 \\\n    --output-dir \"$REPORT_OUTPUT_DIR\"\n```\n\n### Tự động nhận diện format\n\nScript tự phát hiện format sheet dựa trên header (giống hệt logic của `fetch_excel_data.py` - cùng 1 template có thể upload dạng Excel hoặc chia sẻ dạng Google Sheet link, kết quả JSON như nhau):\n\n| Format | Dấu hiệu nhận biết | Output |\n|--------|-------------------|--------|\n| **Sprint Backlog** | Có cột \"US ID\", \"Module/Feature\", \"Task\", \"PIC\" | Input trực tiếp từ output của skill `sprint-planning` - không cần convert |\n| **Jira Export** | Có cột \"Issue key\", \"Issue Type\", \"Status\" | Stories + Subtasks chi tiết |\n| **Generic (template khác)** | Header không khớp 2 format trên, nhưng vẫn nhận diện được cột task/summary, status, estimate, start/due date, assignee qua từ khoá gần đúng | Stories dạng flat (không phân cấp subtask) |\n\n> Nếu 1 sheet không match được cột nào theo header (kể cả generic), script fallback về đọc theo vị trí cột thô (cột 1 = id, cột 2 = summary, cột 3 = status).\n\n### Setup Service Account\n\n1. Tạo Service Account trên Google Cloud Console\n2. Download JSON key file\n3. Chia sẻ Google Sheet với email của Service Account (quyền Viewer)\n4. Truyền path JSON key qua `--service-account`\n\n---\n\n## Nguồn 3: Excel (.xlsx)\n\n### Yêu cầu\n- File Excel (.xlsx) - export từ Jira hoặc spreadsheet thủ công\n- File .xlsx upload qua webapp hoặc path trong uploads/\n\n### Cấu hình & Chạy\n\n```bash\npython scripts/fetch_excel_data.py \\\n    --file <path_to_excel.xlsx> \\\n    --sprint-name \"Sprint 3\" \\\n    --today 2026-07-21 \\\n    --output-dir \"$REPORT_OUTPUT_DIR\" \\\n    --sheet-name \"Sheet1\"  # tùy chọn\n```\n\n### Hỗ trợ nhiều format\n\nTự nhận diện qua header:\n\n| Format | Dấu hiệu nhận biết | Ghi chú |\n|--------|-------------------|---------|\n| **Sprint Backlog** | Có cột \"US ID\", \"Module/Feature\", \"Task\", \"PIC\" | Input trực tiếp từ output của skill `sprint-planning` - không cần convert |\n| **Jira Export** | Có cột \"Issue key\", \"Issue Type\", \"Status\" | Stories + Subtasks chi tiết |\n| **Generic (template khác)** | Header không khớp 2 format trên, nhưng vẫn nhận diện được cột task/summary, status, estimate, start/due date, assignee qua từ khoá gần đúng | Stories dạng flat (không phân cấp subtask) |\n\n---\n\n## Bước 3: Generate Report từ JSON\n\nSau khi có file JSON từ bất kỳ nguồn nào:\n\n```bash\npython scripts/generate_report_from_json.py \\\n    --input <data.json> \\\n    --output-dir \"$REPORT_OUTPUT_DIR\" \\\n    --sprint-start 2026-07-01 \\\n    --sprint-end 2026-08-05 \\\n    --today 2026-07-21 \\\n    --project-key FSM \\\n    --sprint-name \"Sprint 3\"\n```\n\nNếu không truyền `--sprint-start/end`, script tự detect từ JSON (Jira format có sẵn).\n\n---\n\n## Metrics - sub-task only (story = group)\n\nMọi metric **Actual Progress**, **Weighted Phase**, **RAG** tính trên **sub-task** (`issuetype = Sub-task`).\nStory/Epic chỉ dùng để **group** trong Sprint Progress và roll-up RAG story-level.\n\n---\n\n## ② Actual Progress - Weighted Phase (taskProcess từ Jira `customfield_10790`)\n\n| taskProcess value | Phase (báo cáo) | Trọng số |\n|-------------------|-----------------|----------|\n| Requirement & Design | Requirement | 15% |\n| Coding | Development | 50% |\n| Testing / Test | Testing | 15% |\n| Deployment / Deploy / UAT | Deployment | 10% |\n| Khác / null | Other | 10% |\n\n**Progress từng sub-task:**\n\n| Status sub-task | Progress tính vào phase |\n|-----------------|---------------------------|\n| **Done** | `originalEstimate` (100%) |\n| **In review** | `originalEstimate` (100%) |\n| In Progress / To Do / RE WORK / Blocked / ... | `timeSpent / originalEstimate × originalEstimate` (= spent, cap est) |\n\n> Done và In review **luôn** 100% est - **KHÔNG** dùng timeSpent.\n\n```python\nfor subtask in phase_subtasks:\n    if subtask.status in (\"Done\", \"In review\", \"In Review\"):\n        progress_phase += est_hours\n    else:\n        progress_phase += min(spent_hours, est_hours) if est_hours else spent_hours\npct_phase = progress_phase / total_est_phase * 100\nActual Progress = Σ (weight_phase × pct_phase)\n```\n\n**Fallback:** Không có `taskProcess` trên sub-task → effort-based thuần `progress / total est` (không weighted phase).\n\nPhase trước đã xong (imputed): không còn sub-task phase trước nhưng sprint đã có phase sau → credit 100% phase trước.\n\n---\n\n## ④ RAG (duedate-based) - sub-task level\n\n```\nRAG % = (# sub-task có duedate ≤ today AND status Done/In review)\n      / (# sub-task có duedate ≤ today) × 100\n```\n\n| RAG % | Status |\n|-------|--------|\n| ≥ 80% | On Track 🟢 |\n| 50–79% | At Risk 🟡 |\n| < 50% | Off Track 🔴 |\n\n- **Story-level RAG**: roll-up từ sub-task của story đó\n- **Sprint-level RAG**: aggregate toàn bộ sub-task sprint\n- Blocked issues liệt kê trong Risks & Issues, không tự override RAG\n\n---\n\n## Phase Weights (legacy reference - xem bảng trên)\n\n## Báo cáo Output\n\nMarkdown gồm 4 phần:\n1. **Overall Status** - Health, Planned/Actual Progress, SPI, RAG\n2. **Sprint Progress** - Done + Doing/Will do, viết theo quy tắc ở mục [Quy tắc viết Sprint Progress](#quy-tắc-viết-sprint-progress)\n3. **Weighted Phase Breakdown** - Bảng 5 phase + tổng\n4. **Risks & Issues** - tóm tắt ngắn gọn cùng quy tắc với phần 2\n\n---\n\n## Capacity table - Bắt buộc khi có overload\n\nKhi có member nào có **total est trong kỳ tới > 40h** (capacity net 1 tuần), bắt buộc thêm bảng Capacity:\n\n| Member | Tasks | Est (h) | Ghi chú |\n|--------|-------|---------|---------|\n| ...    | ...   | ...     | ⚠️ Overloaded nếu >40h |\n\nĐề xuất redistribute cụ thể: task nào, chuyển sang ai, lý do.\n\n---\n\n## Chu kỳ báo cáo - cửa sổ trượt ±7 ngày quanh hôm nay\n\nMặc định KHÔNG snap về tuần lịch (T2–T6) - luôn tính theo ngày hiện tại, bất kể hôm nay là thứ mấy:\n\n```\nCycle (Done)              = [today - 7 ngày, today]\nNext window (Doing/Will do) = [today + 1 ngày, today + 7 ngày]\n```\n\nNếu user chỉ định mốc bắt đầu khác (VD: \"từ thứ 4 tuần trước\", \"từ 15/07\"), dùng đúng ngày đó làm\n`cycle_start` thay vì `today - 7`, các phần còn lại tính tương tự:\n\n```\nCycle (Done) = [ngày user chỉ định, today]\nNext window  = [cycle_end + 1 ngày, cycle_end + 7 ngày]\n```\n\nGhi rõ trong header báo cáo:\n```\n> 📌 Chu kỳ báo cáo: {cycle_start} – {cycle_end} (hôm nay).\n> Chu kỳ tiếp theo: {next_start} – {next_end}.\n```\n\n---\n\n## Quy tắc viết Sprint Progress\n\n**Format mỗi dòng (chỉ liệt kê sub-task, %, PIC, ngày hoàn thành/hạn chót - không lấy story):**\n```\n- <Tên sub-task> (<% hoàn thành>%) - <PIC> - <DD/MM/YYYY>\n```\n- Nếu status = Done hoặc In review → ghi `(100%)`\n- Nếu đang làm / chưa xong → ghi `(X%)` với X = round(spent/est × 100)\n- Thêm `⚠️ At Risk` nếu due <= today và chưa Done/In review\n- PIC: Tên người phụ trách (assignee)\n- Ngày: Ngày kết thúc / hạn hoàn thành (`DD/MM/YYYY`)\n\n**Ví dụ:**\n```markdown\n### ✅ Done\n- Hỗ trợ nghiệm thu UAT - Đợt 1 (100%) - OanhNTK35 - 15/09/2026\n- Regression & Vibe Test Round 2 & Report (100%) - AnhDC4 - 15/09/2026\n\n### ▶ Doing / Will do\n- Deploy Production & Smoke test (0%) - VuNT60 - 23/09/2026\n- Monitor logs/performance & Hotfix background (0%) - huynt78 - 25/09/2026\n```\n\n**### ✅ Done**\n- Các sub-task đã Done hoặc In review trong chu kỳ báo cáo (tính theo duedate trong kỳ)\n\n**### ▶ Doing / Will do**\n- Tất cả sub-task đang In Progress, To Do có duedate trong kỳ hoặc kỳ tới - gộp chung một section\n- Sắp xếp: overdue/at-risk trước, due date tăng dần\n---\n\n## Versioning output - không ghi đè\n\nMỗi lần generate report **bắt buộc tăng version** - **không ghi đè** file `.md`/`.txt` cũ.\n\n| Thành phần | Quy tắc |\n|------------|---------|\n| Markdown | `{PROJECT}_{SPRINT}_report_v{N}.md` - script tự chọn N tiếp theo |\n| Manifest | `{PROJECT}_{SPRINT}_report_latest.json` - trỏ `md`, `txtExpected`, `version` |\n| PM Summary .txt | `{PROJECT}_{SPRINT}_report_v{N}.txt` - tạo ngay sau khi có `.md` (cùng version N theo `txtExpected`) |\n| Legacy | File cũ `*_report.md` (không _vN) được coi là v1 khi đếm version |\n\n> 📌 **Output của skill gồm 2 file chính thức**:\n> 1. **File `.md`**: Báo cáo chi tiết đầy đủ (được tạo bởi pipeline Python).\n> 2. **File `.txt`**: Bản tóm tắt rút gọn PO/PMO (được viết ngay sau khi có `.md` theo quy tắc bên dưới).\n\n---\n\n## Bản .txt - PM Sprint Summary (Quy tắc tạo bản rút gọn)\n\nNgay sau khi script xuất `{PROJECT}_{SPRINT}_report_v{N}.md`, lấy dữ liệu từ Section 1 (Metrics), Section 2 (Sprint Progress) và Section 4 (Risks & Issues) trong file `.md` vừa tạo để viết file `{PROJECT}_{SPRINT}_report_v{N}.txt` (đúng tên `txtExpected` trong log/manifest) bằng công cụ `Write` (hoặc `write_to_file`).\n\n### Quy tắc biên soạn (Cấp Lãnh đạo & PO)\n- **Định dạng Bullet bắt buộc**: Mọi dòng nội dung trong các mục (Done, Doing/Will do, Risks) **BẮT BUỘC** có tiền tố `- `.\n- **Ngôn ngữ quản trị, đắt giá & ngắn gọn (Rule tóm tắt chuẩn)**: Mỗi dòng súc tích, **tối đa 12 từ** (khoảng 3–10 từ, tuyệt đối không vượt quá 12 từ), đi thẳng vào deliverable/kết quả hoặc trọng tâm kế hoạch. Tối đa 3–5 dòng cho mỗi mục.\n- **TỔNG HỢP & VIẾT LẠI CÔ ĐỌNG (Synthesize / Paraphrase)**: Thay vì sao chép cả câu dài từ Jira, **bắt buộc tự tổng hợp và viết lại thành cụm danh từ ngắn gọn** (nhỏ hơn 12 từ), đủ nghĩa, đúng chuẩn ngữ pháp PM và truyền tải trọn vẹn kết quả.\n- **TUYỆT ĐỐI KHÔNG ĐỂ CÂU DÀI THÔ & KHÔNG CẮT CỤT CƠ HỌC**:\n  - **Không** giữ nguyên câu dài thô từ Jira/Backlog vào bản tóm tắt.\n  - **Không** ngắt cứng cơ học làm đứt đoạn từ ghép / ngữ nghĩa / bổ ngữ cuối câu (ví dụ: không để câu bị cụt lửng như `... log server & Hỗ`, `... Phê duyệt điều kiện`, `... Test Scenarios chi tiết cho`, `... thực hiện kiểm thử chức`).\n\n#### 💡 Bảng đối chiếu viết lại (Synthesize vs Lỗi câu dài / Cắt cụt cơ học):\n| Input thô từ Jira / File .md | ❌ Lỗi câu dài / Hard Truncation | ✅ Viết lại chuẩn PM (Synthesize <= 12 từ) |\n| :--- | :--- | :--- |\n| *Hỗ trợ nghiệp vụ cho DEV và QC, chuẩn bị kịch bản UAT và tài liệu HDSD...* | `- Hỗ trợ nghiệp vụ cho DEV và QC, chuẩn bị` *(Cụt chữ)*<br>`- Hỗ trợ nghiệp vụ cho DEV và QC, chuẩn bị tài liệu bàn giao UAT và quy trình hướng dẫn` *(Quá dài: > 12 từ)* | `- Nghiệm thu UAT & tài liệu HDSD` *(7 từ)* |\n| *Chuẩn bị test case và thực hiện kiểm thử chức năng cho Sprint 4...* | `- Chuẩn bị test case và thực hiện kiểm thử chức` *(Cụt chữ)*<br>`- Chuẩn bị test case & thực hiện kiểm thử chức năng phân hệ ZNS nâng cao` *(Quá dài: > 12 từ)* | `- Kiểm thử chức năng Sprint 4` *(5 từ)* |\n| *Chuẩn bị môi trường và tài liệu phục vụ CSOC Pentest...* | `- Chuẩn bị môi trường và tài liệu phục vụ CSOC` *(Cụt chữ)* | `- Chuẩn bị môi trường Pentest CSOC` *(5 từ)* |\n| *Hỗ trợ CSOC pentest và phân loại các lỗ hổng bảo mật phát hiện được...* | `- Hỗ trợ CSOC pentest và phân loại các lỗ hổng` *(Cụt chữ)* | `- Hỗ trợ Pentest & phân loại lỗ hổng` *(7 từ)* |\n| *Thực hiện Unit test, deploy staging và fix bug trong quá trình...* | `- Thực hiện Unit test, deploy staging và fix bug` *(Cụt chữ)* | `- Deploy Staging & xử lý lỗi QC` *(7 từ)* |\n| *Deploy bản build hoàn thiện Sprint 2 lên môi trường Staging và nghiệm thu nội bộ...* | `- Deploy bản build hoàn thiện Sprint 2 lên môi trường Staging và nghiệm thu nội bộ` *(Quá dài: 16 từ)* | `- Nghiệm thu bản build Sprint 2 Staging` *(7 từ)* |\n\n- **Loại bỏ toàn bộ Jira ID** (FSM-xxx, FCR-xxx, DEV-xxx, PROJ-xxx...).\n- **Loại bỏ tên account/người thực hiện** (kể cả trong ngoặc đơn ở cuối dòng).\n- **Mục DONE (Kết quả bàn giao)**: \n  - **Nguồn trích xuất bắt buộc**: Tổng hợp trực tiếp từ danh sách các **sub-task Done trong chu kỳ báo cáo** (khớp 100% với các sub-task tại Section 2 `### ✅ Done` của file `.md`).\n  - **TUYỆT ĐỐI KHÔNG lấy tên User Story cha (Parent Issue)**: Không tự tiện bốc tên User Story cha từ Jira (ví dụ: `Khởi động Sprint...`, `Setup ban đầu...`) nếu nó không đại diện cho sub-task hoàn thành trong tuần. Việc này gây ra lỗi lệch pha, đưa deliverable ngoại lai vào file `.txt` mà file `.md` hoàn toàn không có, hoặc sai lệch ngữ cảnh thời gian (như báo cáo \"khởi động sprint\" khi sprint đã ở giai đoạn giữa/cuối).\n  - Viết dạng danh từ / danh ngữ chỉ kết quả/sản phẩm (tối đa 12 từ/dòng), cực kỳ súc tích.\n  - **KHÔNG** lặp từ \"Hoàn thành...\" một cách máy móc ở đầu mỗi dòng.\n  - **KHÔNG** kể lể thao tác kỹ thuật con của dev/tester, không ghép câu dài lê thê.\n- **Mục DOING / WILL DO (Kế hoạch & Trọng tâm)**:\n  - Nêu rõ 3–5 đầu việc/mục tiêu trọng tâm tiếp theo từ các sub-task Doing/Will do tại Section 2 của file `.md` (tối đa 12 từ/dòng, trọn vẹn ngữ nghĩa).\n  - **KHÔNG** đưa mốc ngày hoặc khoảng ngày (ví dụ `(due 09/09 - 10/09)`, `(Hạn 07/09)`) vào từng dòng.\n- **Mục RISKS & ISSUES**: Tóm tắt tối đa 1 câu/rủi ro (tối đa 12 từ), ưu tiên rủi ro ảnh hưởng tiến độ chung hoặc go-live.\n\n### Cấu trúc định dạng (Templates)\n\n**Dạng 1 (Tiêu đề done: / doing:)**:\n```\ndone:\n- {Deliverable / Hạng mục hoàn thành 1 (nhỏ hơn 12 từ)}\n- {Deliverable / Hạng mục hoàn thành 2 (nhỏ hơn 12 từ)}\n- {Deliverable / Hạng mục hoàn thành 3 (nhỏ hơn 12 từ)}\ndoing: \n- {Đầu việc trọng tâm 1 (nhỏ hơn 12 từ)}\n- {Đầu việc trọng tâm 2 (nhỏ hơn 12 từ)}\n- {Kế hoạch / đầu việc tiếp theo (nhỏ hơn 12 từ)}\n```\n\n**Dạng 2 (Tiêu đề (Done) / (Doing/Will do))**:\n```\n(Done)\n- {Deliverable / Hạng mục hoàn thành 1 (nhỏ hơn 12 từ)}\n- {Deliverable / Hạng mục hoàn thành 2 (nhỏ hơn 12 từ)}\n- {Deliverable / Hạng mục hoàn thành 3 (nhỏ hơn 12 từ)}\n(Doing/Will do)\n- {Đầu việc trọng tâm 1 (nhỏ hơn 12 từ)}\n- {Đầu việc trọng tâm 2 (nhỏ hơn 12 từ)}\n- {Kế hoạch / đầu việc tiếp theo (nhỏ hơn 12 từ)}\n```\n\n**Dạng 3 (Tiêu đề đầy đủ có Overall Status - Mặc định khuyến nghị)**:\n```\nOverall Status\n{Tên dự án} · {Tên Sprint} - {ngày bắt đầu} - {ngày kết thúc}\n- Health: {🟢 On Track / 🟡 At Risk / 🔴 Off Track} (SPI = {X.XX})\n- Tiến độ: {Actual X%} / kế hoạch {Planned X%}\n- Đúng hạn (RAG): {X%}\n\n---\n\n✅ Done\n- {Deliverable / Kết quả hoàn thành 1 (nhỏ hơn 12 từ)}\n- {Deliverable / Kết quả hoàn thành 2 (nhỏ hơn 12 từ)}\n- {Deliverable / Kết quả hoàn thành 3 (nhỏ hơn 12 từ)}\n\n▶ Doing / Will do\n- {Đầu việc trọng tâm 1 (nhỏ hơn 12 từ)}\n- {Đầu việc trọng tâm 2 (nhỏ hơn 12 từ)}\n- {Kế hoạch / đầu việc tiếp theo (nhỏ hơn 12 từ)}\n\n⚠️ Risks & Issues\n- {Rủi ro 1 ảnh hưởng tiến độ hoặc go-live}\n- {Rủi ro 2}\n```\n\n### 🛫 Preflight Checklist (Bắt buộc tự kiểm tra trước khi ghi file .txt)\n\nTrước khi dùng `Write` / `write_to_file` xuất file `.txt`, **BẮT BUỘC** đối chiếu toàn bộ nội dung với checklist sau:\n\n- [ ] **1. Giới hạn độ dài chuẩn tóm tắt (tối đa 12 từ/dòng)**: Đếm số từ từng dòng trong mục Done và Doing. Tuyệt đối **KHÔNG vượt quá 12 từ**, **KHÔNG giữ nguyên câu dài thô** từ Jira, và **KHÔNG cắt cụt từ/ngữ cơ học**.\n- [ ] **2. Không cắt cụt chữ (Zero Truncation)**: Mỗi dòng là một cụm danh từ hoàn chỉnh ngữ nghĩa, không đứt đoạn từ ghép, không lửng câu, không sót từ nối ở đuôi (`&`, `và`, `cho`, `với`, `của`, `để`, `hỗ`, `chuẩn bị`, `chức`...).\n- [ ] **3. Chuẩn hóa Deliverable (Outcome-based)**: Tóm tắt cô đọng thành kết quả/bàn giao (VD: `Nghiệm thu UAT & Sign-off`, `Kiểm thử chức năng Sprint 4`), không kể lể thao tác dev/QC con.\n- [ ] **4. Làm sạch 100%**: Đã loại bỏ hoàn toàn Jira ID (FSM-xxx, DEV-xxx...), tên người thực hiện (Account/Assignee), và ký tự markdown thô (`**`, `###`).\n- [ ] **5. Định dạng Bullet `- `**: Mỗi dòng trong Done, Doing/Will do, Risks bắt buộc bắt đầu bằng `- `.\n- [ ] **6. Số lượng dòng**: Mỗi mục Done và Doing chỉ chứa từ **3 đến 5 dòng**.\n- [ ] **7. Tính nhất quán 100% với file `.md` (Zero Hallucination / No Foreign Story Names)**: Toàn bộ deliverable trong `Done` và đầu việc trong `Doing` của file `.txt` phải có nguồn gốc trực tiếp từ các sub-task tại Section 2 của file `.md`. Tuyệt đối không xuất hiện hạng mục lạ hoặc bốc tên Story cha ngoài lề (như \"Khởi động Sprint\" khi file `.md` không có hoặc sprint đã ở giữa/cuối).\n\n---\n\n## Quy trình đầy đủ (Step-by-Step)\n\n### Ví dụ Input → Command\n\n| Câu hỏi của user | Command phải chạy |\n|------------------|-------------------|\n| \"Làm weekly report cho FSM Sprint 3\" | `run_weekly_report.py --project-key FSM --sprint-name \"Sprint 3\"` (Jira-only) |\n| \"Làm report FSM Sprint 3, dữ liệu từ Sheet ID 1abc...\" | `run_weekly_report.py --project-key FSM --sprint-name \"Sprint 3\" --sheet-id \"1abc...\"` |\n| \"Report Sprint 3, đọc từ file Excel này\" + file upload | `run_weekly_report.py --project-key FSM --sprint-name \"Sprint 3\" --excel \"/path/to/file.xlsx\"` |\n| \"FSM Sprint 3, Sheet 1abc... có backlog mới nhất\" | `run_weekly_report.py --project-key FSM --sprint-name \"Sprint 3\" --sheet-id \"1abc...\"` |\n| **\"FSM Sprint 3, data google sheet (1abc...), start/due sprint lấy từ jira\"** | `run_weekly_report.py --project-key FSM --sprint-name \"Sprint 3\" --sheet-id \"1abc...\"` **(vẫn cần --sheet-id!)** |\n\n### Step 1 - Kiểm tra nguồn dữ liệu và thông tin bắt buộc\n\n**TRƯỚC TIÊN**: Kiểm tra xem user có cung cấp Sheet ID/Excel không.\n\n| Input từ user | Hành động |\n|-------|-----------|\n| User cung cấp Google Sheet ID, spreadsheet link, hoặc nhắc \"Google Sheet\" / **\"data google sheet\"** | **BẮT BUỘC** thêm `--sheet-id <SHEET_ID>` vào command |\n| User gửi file `.xlsx` hoặc nhắc Excel | **BẮT BUỘC** thêm `--excel <PATH>` vào command |\n| Chỉ có project key + sprint name, không nhắc Sheet/Excel | Dùng Jira-only (mặc định) |\n| Thiếu project key hoặc sprint name | Hỏi 2 thông tin này |\n\n> ⚠️ **LƯU Ý**: Logic fallback trong `run_weekly_report.py` là `jira_only = not args.sheet_id and not args.excel`. Nếu không truyền `--sheet-id` dù user có cung cấp Sheet ID, script sẽ tự động bỏ qua và chạy Jira-only.\n\n> ⚠️ **PATTERN MATCHING**: \n> - User nói **\"data google sheet (ID)\"** → Có Sheet ID → **PHẢI `--sheet-id`**\n> - User nói **\"start/due sprint lấy từ jira\"** → Chỉ là hướng dẫn lấy sprint dates, **KHÔNG** thay đổi nguồn backlog\n> - Kết hợp cả 2 câu → Backlog từ Sheet + Sprint dates từ Jira → Vẫn **PHẢI `--sheet-id`** (script tự động kết hợp)\n\n### Step 2 - Fetch data\n\nTùy nguồn, chạy script tương ứng → xuất JSON standardized.\n\nScript xuất `{PROJECT}_{SPRINT}_report_v{N}.md` + `{PROJECT}_{SPRINT}_report_latest.json`. **Không** ghi đè bản cũ.\n\n### Step 3 - Generate report (.md)\n\n```bash\npython3 scripts/generate_report_from_json.py --input <json_file> --output-dir \"$REPORT_OUTPUT_DIR\"\n```\n\n### Step 4 - Tạo bản PM Sprint Summary (.txt)\n\nNgay sau khi script xuất file `.md`:\n1. Đọc Section 1 (Metrics), Section 2 (Sprint Progress) và Section 4 (Risks) từ file `.md` vừa tạo.\n2. **BẮT BUỘC DÙNG NĂNG LỰC TỔNG HỢP CỦA AI (LLM) ĐỂ VIẾT LẠI (SYNTHESIZE / PARAPHRASE)**:\n   - **Tuyệt đối KHÔNG** sao chép câu thô từ `.md` rồi cắt ngang lưng chừng làm cụt từ, đứt đoạn ngữ nghĩa.\n   - Phải tự viết lại từng bullet thành một cụm danh từ chỉ kết quả/kế hoạch ngắn gọn (khoảng 5–12 từ, tối đa 15 từ), trọn vẹn ngữ nghĩa và bắt đầu bằng `- `.\n   - Tham chiếu bảng đối chiếu ở mục [Quy tắc biên soạn](#quy-tắc-biên-soạn-cấp-lãnh-đạo--po).\n3. **Thực hiện Preflight Check**: Tự kiểm tra 6 tiêu chí trong [Preflight Checklist](#-preflight-checklist-bắt-buộc-tự-kiểm-tra-trước-khi-ghi-file-txt) (độ dài súc tích 5–12 từ/dòng, không cắt cụt từ, không để câu dài thô, format `- `).\n4. Dùng công cụ `Write` (hoặc `write_to_file`) viết hoàn thiện file `.txt` vào `$REPORT_OUTPUT_DIR` với đúng tên `txtExpected` (ví dụ `{PROJECT}_{SPRINT}_report_v{N}.txt`).\n\n### Step 5 - Báo cáo kết quả\n\nGửi **1 tin nhắn duy nhất** sau khi đã hoàn thành cả file `.md` và file `.txt`:\n- Tóm tắt Health, SPI, RAG, **version** (_vN).\n- Nêu rõ tên cả 2 file:\n  - File `.md` (báo cáo chi tiết)\n  - File `.txt` (bản tóm tắt rút gọn)\n- Tuyệt đối **không** gửi tin nhắn phân tách thành nhiều đoạn dở dang để đảm bảo các chip file đính kèm hiển thị đúng vào tin nhắn kết quả này.\n\n## Xử lý lỗi thường gặp\n\n| Lỗi | Nguyên nhân | Xử lý |\n|-----|-------------|-------|\n| 410 Gone trên `/rest/api/3/search` | API cũ deprecated | Dùng `POST /rest/api/3/search/jql` |\n| `ModuleNotFoundError: gspread/openpyxl` | Venv webapp thiếu package | Báo admin restart webapp (server tự cài `.venv-skills`) |\n| `403 Forbidden` Google Sheet | Service account chưa được cấp quyền | Chia sẻ sheet với email service account |\n| Timeout / ConnectTimeout khi gọi Jira/Google | Proxy FPT không thống nhất theo host | **Chạy lại script** - tự thử direct → proxy → env (log `[NET]`). Không dùng curl |\n| Proxy error khi fetch Google Sheet | Thiếu proxy hoặc direct bị chặn | Script tự fallback; nếu vẫn lỗi thêm `HTTP_PROXY`/`HTTPS_PROXY` vào `.env` webapp |\n| 401 Unauthorized | Token hết hạn / sai | Kiểm tra email + API token |\n| `total: None` | API mới dùng token pagination | Dùng `isLast` + `nextPageToken` để paginate |",
      "envVars": [
        {
          "name": "JIRA_SITE",
          "description": "Jira Site host name hoặc base URL (ví dụ: foxproject.atlassian.net)",
          "default": "foxproject.atlassian.net",
          "category": "Jira",
          "isSecret": false
        },
        {
          "name": "JIRA_EMAIL",
          "description": "Email tài khoản Jira dùng để xác thực API",
          "default": "user@company.com",
          "category": "Jira",
          "isSecret": false
        },
        {
          "name": "JIRA_API_TOKEN",
          "description": "API Token của Atlassian Jira Cloud (tạo tại Atlassian Account Settings)",
          "default": "",
          "category": "Jira",
          "isSecret": true
        },
        {
          "name": "JIRA_TOKEN",
          "description": "Alias của JIRA_API_TOKEN (dự phòng tương thích ngược)",
          "default": "",
          "category": "Jira",
          "isSecret": true
        },
        {
          "name": "GOOGLE_SERVICE_ACCOUNT_PATH",
          "description": "Đường dẫn file JSON Service Account Google Cloud để đọc/ghi Google Sheets",
          "default": "meta-gear-328801-4ff82b2ad59e.json",
          "category": "Google Sheets",
          "isSecret": false
        },
        {
          "name": "GOOGLE_SHEETS_ACCESS_TOKEN",
          "description": "(Tùy chọn) Google OAuth Access Token truy vấn Google Sheets API",
          "default": "",
          "category": "Google Sheets",
          "isSecret": true
        },
        {
          "name": "HRM_SHEET_ID",
          "description": "ID Google Sheet cho Portfolio (Schema 27 cột)",
          "default": "1QDfYT34pZIxcvSg7HHcg2WlAS0YQFF72vjUZfnl-1HA",
          "category": "Google Sheets",
          "isSecret": false
        },
        {
          "name": "REPORT_OUTPUT_DIR",
          "description": "Thư mục xuất các file báo cáo, biểu đồ, kết quả chạy skill",
          "default": "outputs",
          "category": "System",
          "isSecret": false
        },
        {
          "name": "HTTP_PROXY",
          "description": "Proxy HTTP mạng nội bộ doanh nghiệp",
          "default": "http://proxy.hcm.fpt.vn:80",
          "category": "Network",
          "isSecret": false
        },
        {
          "name": "HTTPS_PROXY",
          "description": "Proxy HTTPS mạng nội bộ doanh nghiệp",
          "default": "http://proxy.hcm.fpt.vn:80",
          "category": "Network",
          "isSecret": false
        },
        {
          "name": "SKILL_DIR",
          "description": "Đường dẫn thư mục skill hiện hành (hệ thống tự inject)",
          "default": "./skills",
          "category": "System",
          "isSecret": false
        }
      ]
    }
  ],
  "globalEnvDefinitions": {
    "JIRA_BASE_URL": {
      "description": "URL của Jira Cloud hoặc Server (ví dụ: https://foxproject.atlassian.net)",
      "default": "https://foxproject.atlassian.net",
      "category": "Jira",
      "isSecret": false
    },
    "JIRA_SITE": {
      "description": "Jira Site host name hoặc base URL (ví dụ: foxproject.atlassian.net)",
      "default": "foxproject.atlassian.net",
      "category": "Jira",
      "isSecret": false
    },
    "JIRA_EMAIL": {
      "description": "Email tài khoản Jira dùng để xác thực API",
      "default": "user@company.com",
      "category": "Jira",
      "isSecret": false
    },
    "JIRA_API_TOKEN": {
      "description": "API Token của Atlassian Jira Cloud (tạo tại Atlassian Account Settings)",
      "default": "",
      "category": "Jira",
      "isSecret": true
    },
    "JIRA_TOKEN": {
      "description": "Alias của JIRA_API_TOKEN (dự phòng tương thích ngược)",
      "default": "",
      "category": "Jira",
      "isSecret": true
    },
    "JIRA_PROJECT_KEY": {
      "description": "Mã Project Key Jira mặc định (ví dụ: FCR, FSM, ISC, SAL)",
      "default": "FCR",
      "category": "Jira",
      "isSecret": false
    },
    "HRM_USERNAME": {
      "description": "Tài khoản đăng nhập hệ thống HRM FPT (apis.fpt.net)",
      "default": "admin@hrm.fpt.net",
      "category": "HRM",
      "isSecret": false
    },
    "HRM_PASSWORD": {
      "description": "Mật khẩu đăng nhập hệ thống HRM FPT (plain text)",
      "default": "",
      "category": "HRM",
      "isSecret": true
    },
    "HRM_PASSWORD_ENC": {
      "description": "Mật khẩu HRM FPT đã mã hoá AES-256",
      "default": "",
      "category": "HRM",
      "isSecret": true
    },
    "HRM_ACCESS_TOKEN": {
      "description": "(Tùy chọn) Access Token HRM có sẵn nếu không muốn login lại",
      "default": "",
      "category": "HRM",
      "isSecret": true
    },
    "HRM_EXCEL_URL": {
      "description": "Link chia sẻ file Excel Online (SharePoint / OneDrive) cho Sheet 1 (Project2026)",
      "default": "https://fpt-my.sharepoint.com/:x:/g/personal/...",
      "category": "HRM",
      "isSecret": false
    },
    "HRM_EXCEL2_URL": {
      "description": "Link chia sẻ file Excel Online cho Sheet 2 (nếu tách file riêng)",
      "default": "",
      "category": "HRM",
      "isSecret": false
    },
    "HRM_SHEET_NAME": {
      "description": "Tên tab/sheet Excel cần ghi dữ liệu HRM (mặc định: Project2026)",
      "default": "Project2026",
      "category": "HRM",
      "isSecret": false
    },
    "HRM_SHEET2_ID": {
      "description": "ID Google Sheet dự phòng cho Sheet 2 FTI",
      "default": "13ENSxJkc9lL43lmofw9HIxF9sdR_cElNtW2D581KIkw",
      "category": "HRM",
      "isSecret": false
    },
    "HRM_SHEET2_NAME": {
      "description": "Tên tab/sheet Google Sheet 2 (mặc định: FTI)",
      "default": "FTI",
      "category": "HRM",
      "isSecret": false
    },
    "HRM_DIVISION_CODE": {
      "description": "Mã bộ phận lọc báo cáo HRM (để trống = lấy tất cả)",
      "default": "",
      "category": "HRM",
      "isSecret": false
    },
    "HRM_SHEET2_DIVISION_CODE": {
      "description": "Mã bộ phận lọc cho Sheet 2 (mặc định: FTI)",
      "default": "FTI",
      "category": "HRM",
      "isSecret": false
    },
    "HRM_VPN_ENABLED": {
      "description": "Cơ chế kết nối VPN (auto: tự bật khi ngoài FPT; true: luôn bật; false: tắt)",
      "default": "auto",
      "category": "HRM VPN",
      "isSecret": false
    },
    "HRM_VPN_TYPE": {
      "description": "Loại VPN (openvpn cho csocvpn.fpt.net, wireguard, v.v.)",
      "default": "openvpn",
      "category": "HRM VPN",
      "isSecret": false
    },
    "HRM_VPN_HOST": {
      "description": "Địa chỉ máy chủ VPN Gateway FPT (csocvpn.fpt.net)",
      "default": "csocvpn.fpt.net",
      "category": "HRM VPN",
      "isSecret": false
    },
    "HRM_VPN_PORT": {
      "description": "Cổng kết nối VPN Gateway (443 hoặc 1194)",
      "default": "443",
      "category": "HRM VPN",
      "isSecret": false
    },
    "HRM_VPN_USERNAME": {
      "description": "Tài khoản VPN FPT (mặc định dùng HRM_USERNAME)",
      "default": "",
      "category": "HRM VPN",
      "isSecret": false
    },
    "HRM_VPN_PASSWORD": {
      "description": "Mật khẩu VPN FPT",
      "default": "",
      "category": "HRM VPN",
      "isSecret": true
    },
    "HRM_VPN_TOTP_SECRET": {
      "description": "Khóa bí mật Base32 từ Authenticator để tự động tính mã OTP 6 số",
      "default": "",
      "category": "HRM VPN",
      "isSecret": true
    },
    "HRM_VPN_OTP": {
      "description": "(Tùy chọn) Mã OTP cố định nếu nhập trực tiếp",
      "default": "",
      "category": "HRM VPN",
      "isSecret": false
    },
    "HRM_VPN_CONFIG_PATH": {
      "description": "Đường dẫn file cấu hình .ovpn (ví dụ: data/csocvpn.ovpn)",
      "default": "data/csocvpn.ovpn",
      "category": "HRM VPN",
      "isSecret": false
    },
    "HRM_VPN_AUTO_DISCONNECT": {
      "description": "Tự động ngắt kết nối VPN sau khi cào xong (true/false)",
      "default": "true",
      "category": "HRM VPN",
      "isSecret": false
    },
    "HRM_PROXY_URL": {
      "description": "URL Proxy nội bộ nếu dùng proxy",
      "default": "",
      "category": "Network",
      "isSecret": false
    },
    "OUTLOOK_EMAIL": {
      "description": "Email tài khoản Microsoft Outlook / Office 365",
      "default": "user@company.com",
      "category": "Outlook",
      "isSecret": false
    },
    "OUTLOOK_PASSWORD": {
      "description": "Mật khẩu ứng dụng (App Password) hoặc IMAP Password của Outlook",
      "default": "",
      "category": "Outlook",
      "isSecret": true
    },
    "OUTLOOK_IMAP_SERVER": {
      "description": "Địa chỉ máy chủ IMAP Outlook",
      "default": "outlook.office365.com",
      "category": "Outlook",
      "isSecret": false
    },
    "OUTLOOK_IMAP_PORT": {
      "description": "Cổng kết nối IMAP SSL",
      "default": "993",
      "category": "Outlook",
      "isSecret": false
    },
    "OUTLOOK_ACCESS_TOKEN": {
      "description": "OAuth2 Modern Auth Access Token từ Microsoft Graph API",
      "default": "",
      "category": "Outlook",
      "isSecret": true
    },
    "MS_GRAPH_ACCESS_TOKEN": {
      "description": "Access Token của Microsoft Graph API",
      "default": "",
      "category": "Outlook",
      "isSecret": true
    },
    "OUTLOOK_VAULT_KEY": {
      "description": "Khóa mã hóa an toàn nội dung email vault trước khi gửi AI",
      "default": "",
      "category": "Security",
      "isSecret": true
    },
    "GOOGLE_SERVICE_ACCOUNT_PATH": {
      "description": "Đường dẫn file JSON Service Account Google Cloud để đọc/ghi Google Sheets",
      "default": "meta-gear-328801-4ff82b2ad59e.json",
      "category": "Google Sheets",
      "isSecret": false
    },
    "GOOGLE_SHEETS_ACCESS_TOKEN": {
      "description": "(Tùy chọn) Google OAuth Access Token truy vấn Google Sheets API",
      "default": "",
      "category": "Google Sheets",
      "isSecret": true
    },
    "HRM_SHEET_ID": {
      "description": "ID Google Sheet cho Portfolio (Schema 27 cột)",
      "default": "1QDfYT34pZIxcvSg7HHcg2WlAS0YQFF72vjUZfnl-1HA",
      "category": "Google Sheets",
      "isSecret": false
    },
    "FINBOX_TIMEOUT": {
      "description": "Thời gian timeout cho các request tới Finbox API (giây)",
      "default": "15",
      "category": "Stock",
      "isSecret": false
    },
    "FINBOX_PROXY": {
      "description": "Proxy HTTP khi truy cập API Finbox",
      "default": "http://proxy.hcm.fpt.vn:80",
      "category": "Stock",
      "isSecret": false
    },
    "MEM0_STORAGE_DIR": {
      "description": "Thư mục lưu database SQLite cho bộ nhớ dài hạn Mem0",
      "default": "data/mem0_storage",
      "category": "AI & Memory",
      "isSecret": false
    },
    "REPORT_OUTPUT_DIR": {
      "description": "Thư mục xuất các file báo cáo, biểu đồ, kết quả chạy skill",
      "default": "outputs",
      "category": "System",
      "isSecret": false
    },
    "SKILL_DIR": {
      "description": "Đường dẫn thư mục skill hiện hành (hệ thống tự inject)",
      "default": "./skills",
      "category": "System",
      "isSecret": false
    },
    "HTTP_PROXY": {
      "description": "Proxy HTTP mạng nội bộ doanh nghiệp",
      "default": "http://proxy.hcm.fpt.vn:80",
      "category": "Network",
      "isSecret": false
    },
    "HTTPS_PROXY": {
      "description": "Proxy HTTPS mạng nội bộ doanh nghiệp",
      "default": "http://proxy.hcm.fpt.vn:80",
      "category": "Network",
      "isSecret": false
    }
  }
};

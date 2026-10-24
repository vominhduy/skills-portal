---
name: "hrm-weekly-report"
description: "Chạy weekly report HRM (apis.fpt.net) và ghi vào Microsoft Excel Online (SharePoint / OneDrive qua Graph API) hoặc Google Sheets. Login HRM bằng username/password (từ env) lấy access_token, scrape API weekly-reports, ghi bảng tính. Trigger khi user nói: báo cáo HRM, weekly report HRM, cập nhật sheet HRM, cập nhật excel HRM, lấy dữ liệu tuần HRM, hoặc yêu cầu tổng hợp tiến độ dự án từ hệ thống HRM FPT."
---

# HRM Weekly Report (Python, gọi API trực tiếp)

Lấy dữ liệu báo cáo tuần từ HRM FPT (`apis.fpt.net`) qua REST API và ghi vào **Microsoft Excel Online (SharePoint / OneDrive)** hoặc **Google Sheets**.

- **Xác thực Microsoft Excel Online (SharePoint / OneDrive)**:
  - Sử dụng **Microsoft Graph API** với cơ chế MSAL Token Cache (`token_cache.bin`) / Device Code Flow.
  - Hỗ trợ trực tiếp đường dẫn chia sẻ (Sharing URL) trên SharePoint hoặc OneDrive (`HRM_EXCEL_URL` hoặc tham số `--excel-url`).
  - Hỗ trợ đầy đủ các schema:
    - **Sheet Project2026** (78 cột A–BZ của file `2026_SU02_Resource_Planning.xlsx`): Match Key tại Cột B (`Project/Version`), bảo toàn 100% 48 cột Resource 12 tháng (W–BR) và các số liệu PMO (Effort/Defect).
    - **Sheet Portfolio 2026** (27 cột A–AA của file `Duy_Test_2026_SU02_KEY_PROJECTS.xlsx`).
    - **Sheet FTI** (19 cột A–S của file `ISC _KEY PROJECT_2026.xlsx`).
- **Xác thực Google Sheets (Dự phòng tương thích ngược cho file cũ)**:
  - Giữ nguyên 100% logic và mapping cho file Google Sheets (`13ENSxJkc9lL43lmofw9HIxF9sdR_cElNtW2D581KIkw`), có cập nhật Cột S là Ngày báo cáo.
  - Dùng **User OAuth Access Token** hoặc Google Service Account JSON key (`GOOGLE_SERVICE_ACCOUNT_PATH`).

## Pipeline (MỘT lệnh Bash duy nhất)

```bash
cd "$SKILL_DIR" && python3 scripts/run_hrm_report.py --output-dir "$REPORT_OUTPUT_DIR"
```

Tuỳ chọn:
- `--excel-url "https://...sharepoint.com/..."` - chỉ định link chia sẻ file Excel trên SharePoint/OneDrive (Graph API).
- `--excel-url2 "https://...sharepoint.com/..."` - chỉ định link chia sẻ file Excel cho Sheet 2 (nếu tách riêng).
- `--week-start YYYY-MM-DD --week-end YYYY-MM-DD` - chỉ định tuần (mặc định: Thứ 2→Chủ Nhật tuần hiện tại).
- `--token "<access_token>"` - dùng token có sẵn, bỏ qua bước login.
- `--vpn {auto,true,false}` - cơ chế VPN (`auto`: tự động bật khi chưa vào được mạng nội bộ FPT, `true`: ép bật, `false`: tắt).
- `--vpn-type {openvpn,openconnect,openfortivpn,wireguard,ssh_tunnel,custom}` - loại VPN (mặc định `openvpn` cho OpenVPN Connect).
- `--vpn-host <host>` - địa chỉ máy chủ VPN (ví dụ: `csocvpn.fpt.net`).
- `--vpn-user <account>` - tài khoản công ty FPT.
- `--vpn-otp <otp>` - mã OTP 6 số từ Authenticator (nếu nhập trực tiếp).
- `--vpn-totp-secret <secret>` - khóa bí mật Base32 từ Authenticator để tự động sinh mã OTP 6 số.
- `--vpn-config <path>` - file cấu hình `.ovpn` (nếu có, ví dụ `data/csocvpn.ovpn`).
- `--vpn-keep-alive` - giữ kết nối VPN sau khi hoàn thành scrape (không tự ngắt).

> Webapp tự chạy pipeline (auto-remedy) - KHÔNG hỏi user cấp quyền Bash.

## Cơ chế OpenVPN & Mạng nội bộ FPT (`csocvpn.fpt.net`)

Do hệ thống HRM FPT (`apis.fpt.net` / `hrm.fpt.net`) nằm trong mạng nội bộ FPT Telecom, khi chạy báo cáo từ xa (máy cá nhân ở nhà, VPS cloud hoặc Docker), script hỗ trợ **tự động kiểm tra và kết nối OpenVPN**:
1. **Tự động chẩn đoán**: Kiểm tra trước xem `apis.fpt.net:443` hoặc `hrm.fpt.net:443` đã thông mạng chưa. Nếu đã ở trong mạng FPT hoặc VPN đã bật ngoài máy -> bỏ qua bước VPN.
2. **Kích hoạt tự động**: Nếu chưa thông mạng và có cấu hình VPN (`HRM_VPN_ENABLED=auto` hoặc `true`), script tự động bật OpenVPN kết nối tới `csocvpn.fpt.net`.
3. **Cơ chế xác thực 2FA OTP thông minh**:
   - **Tự động sinh OTP (Khuyên dùng)**: Cấu hình `HRM_VPN_TOTP_SECRET=<key_base32>` (lấy từ mã QR / Authenticator app khi thiết lập 2FA công ty). Mỗi lần chạy, script tự động tính mã 6 số chuẩn RFC 6238 theo giờ hệ thống mà không cần mở điện thoại lấy mã!
   - **Nhập OTP trực tiếp**: Truyền qua CLI `--vpn-otp 123456` hoặc nhập trực tiếp khi được hỏi trên terminal.
4. **File cấu hình `.ovpn`**:
   - Nếu bạn đã export file `.ovpn` từ app OpenVPN Connect trên điện thoại, hãy đặt vào thư mục `data/csocvpn.ovpn`.
   - Nếu chưa có file `.ovpn`, script sẽ tự động tạo file cấu hình kết nối chuẩn tới `csocvpn.fpt.net:443` (TCP/UDP).
5. **Tự dọn dẹp (Context Manager)**: Sau khi cào xong dữ liệu HRM, VPN tự động được ngắt kết nối an toàn để trả lại đường truyền mạng bình thường.
6. **Kiểm tra nhanh kết nối**:
   ```bash
   python3 scripts/test_vpn.py               # Chẩn đoán trạng thái mạng nội bộ & cấu hình VPN
   python3 scripts/test_vpn.py --test-connect # Thử nghiệm kết nối VPN thực tế
   ```

## Biến môi trường (server đã inject hoặc cấu hình trong .env)

| Biến | Vai trò |
|---|---|
| `HRM_USERNAME` / `HRM_PASSWORD` | credential login HRM (POST /auth) → access_token |
| `HRM_ACCESS_TOKEN` | (tuỳ chọn) token có sẵn, bỏ qua login |
| `HRM_EXCEL_URL` / `HRM_EXCEL_SHARE_URL` | Link file Excel đích (Sheet 1) trên SharePoint/OneDrive |
| `HRM_EXCEL2_URL` / `HRM_EXCEL_URL2` | Link file Excel thứ hai (Sheet 2) trên SharePoint/OneDrive |
| `HRM_SHEET_NAME` | tên sheet/tab Excel (mặc định "Project2026") |
| `HRM_SHEET2_ID` | ID Google Sheet cũ (13ENSxJkc9lL43lmofw9HIxF9sdR_cElNtW2D581KIkw) |
| `HRM_SHEET2_NAME` | tên sheet/tab Google Sheet cũ (mặc định "FTI") |
| `HRM_DIVISION_CODE` | filter division (để trống = lấy tất cả division) |
| `HRM_SHEET2_DIVISION_CODE` | filter division cho Sheet 2 (mặc định "FTI") |
| `HRM_VPN_ENABLED` | Bật/tắt VPN (`auto`: tự động khi cần, `true`, `false`) |
| `HRM_VPN_TYPE` | Loại VPN (`openvpn` cho csocvpn, hoặc `openconnect`, `openfortivpn`, `wireguard`, `ssh_tunnel`) |
| `HRM_VPN_HOST` | Địa chỉ máy chủ VPN gateway (mặc định: `csocvpn.fpt.net`) |
| `HRM_VPN_PORT` | Cổng máy chủ VPN (mặc định `443`) |
| `HRM_VPN_USERNAME` | Tài khoản công ty FPT (mặc định lấy theo `HRM_USERNAME`) |
| `HRM_VPN_PASSWORD` | Mật khẩu tài khoản (hỗ trợ mã hoá qua `HRM_PASSWORD_ENC`) |
| `HRM_VPN_TOTP_SECRET` | Khóa bí mật Base32 từ Authenticator để **tự động tính mã OTP 6 số** |
| `HRM_VPN_OTP` | (Tuỳ chọn) Mã OTP cố định nếu truyền qua env |
| `HRM_VPN_CONFIG_PATH` | Đường dẫn file profile `.ovpn` (ví dụ `data/csocvpn.ovpn`) |
| `HRM_VPN_AUTO_DISCONNECT` | Tự động ngắt VPN sau khi cào xong (`true`/`false`, mặc định `true`) |
| `HRM_PROXY_URL` | URL proxy nội bộ nếu dùng HTTP/SOCKS proxy (ví dụ `socks5h://127.0.0.1:10808`) |

## Output

- File `hrm_weekly_report_vN.json` trong `$REPORT_OUTPUT_DIR` (versioned, không ghi đè):
  - `projectCount`, `updatedCount`, `insertedCount`
  - `updatedList` / `insertedList` (code + name từng dự án)
  - `weekStart`, `weekEnd`, `targetType`

## Schema Bảng tính Sheet Project2026 (78 cột A–BZ)

> **Lưu ý an toàn dữ liệu**: 48 cột **RESOURCE** từ W đến BR (12 tháng x PM, BA, DEV, QC) và các cột **Effort / QC Defect / UAT Defect** từ S đến V được **bảo toàn 100%** (không bao giờ ghi đè).
> **Xử lý công thức Excel**: Các cột text **N, O, R, BW, BX, BY, BZ** nếu bắt đầu bằng dấu `-` sẽ tự động thêm dấu `'` ở đầu (ví dụ: `'- Task 1...`) để tránh lỗi `#NAME?` / formula error.

| Dải Cột | Tiêu đề cột trên file Excel | Dữ liệu HRM tương ứng | Ghi chú |
|:---:|---|---|---|
| **A (0)** | No. | STT | Giữ nguyên nếu dòng đã có, tạo mới STT tiếp theo |
| **B (1)** | Project/Version | `displayName` | **Khóa khớp dòng (Match Key chính)** |
| **C (2)** | Release/Sprint | `Release/Sprint` | **Giữ nguyên (Preserved)** |
| **D (3)** | Application | `projectCode` | Cập nhật |
| **E (4)** | Project Type | `Project Type` | **Giữ nguyên (Preserved)** (Mặc định "Enhancement") |
| **F (5)** | Business Owner | `division` | **Giữ nguyên** / Mặc định "FTI" |
| **G (6)** | Product Owner | `Product Owner` | **Giữ nguyên (Preserved)** |
| **H (7)** | PM | `pm` | Cập nhật |
| **I (8)** | Project Status | `projectPhase` | Cập nhật |
| **J (9)** | Priority | `priority` | **Giữ nguyên nếu dòng đã có** |
| **K (10)** | Start date (MM/dd/yyyy) | `planStartDate` | Cập nhật (hoặc giữ nguyên nếu đã có) |
| **L (11)** | Target Go-live (MM/dd/yyyy) | `planDueDate` | Cập nhật |
| **M (12)** | Actual Go-live (MM/dd/yyyy) | `Actual Go-live` | **Giữ nguyên (Preserved)** |
| **N (13)** | Business Problem | `mainFeature` | Cập nhật (thêm `'` nếu bắt đầu bằng `-`) |
| **O (14)** | Business Outcome | `goal` | Cập nhật (thêm `'` nếu bắt đầu bằng `-`) |
| **P (15)** | Key Scope/Sprint Goal | `Key Scope/Sprint Goal` | **Giữ nguyên (Preserved)** |
| **Q (16)** | Value Dimension | `valueCodes` | **Giữ nguyên** / Cập nhật nếu mới |
| **R (17)** | Primary Value Metric | `valueMetric` / `businessImpact` | **Giữ nguyên** / Cập nhật nếu mới |
| **S–V (18–21)** | Estimated/Actual Effort, QC/UAT Defect | Effort & Defect rates | **100% Giữ nguyên (Preserved)** |
| **W–BR (22–69)** | 48 cột RESOURCE (Jan..Dec x PM, BA, DEV, QC) | Phân bổ Resource hàng tháng | **100% Giữ nguyên (Preserved)** |
| **BS (70)** | %Done | `progress` | Cập nhật |
| **BT (71)** | Status | `projectPhase` | Cập nhật |
| **BU (72)** | Project Health | `projectHealth` | Cập nhật |
| **BV (73)** | Release Date | `planDueDate` | Cập nhật |
| **BW (74)** | This Week [Done] | `done` | Cập nhật (thêm `'` nếu bắt đầu bằng `-`) |
| **BX (75)** | Next Week Plan [Doing/Will Do] | `continuationPlan` | Cập nhật (thêm `'` nếu bắt đầu bằng `-`) |
| **BY (76)** | Issues & Actions | `riskOrIssues` | Cập nhật (thêm `'` nếu bắt đầu bằng `-`) |
| **BZ (77)** | RELEASE NOTE (Output - Module - Function) | `releaseNote` | Cập nhật (thêm `'` nếu bắt đầu bằng `-`) |

# Sprint Planning - Detailed Instructions, Rules & Checklist v2.10

> **INTERNAL REFERENCE ONLY** - Scrum Master **bắt buộc đọc toàn bộ file này** trước khi tạo bất kỳ Sprint Backlog nào.  
> File này chứa toàn bộ quy tắc chi tiết, workflow 6 bước, EPIC-0 rules, task splitting, sequential assignment, xử lý Pentest/Pilot, Pre-flight Checklist và Limitations.  
> **KHÔNG tóm tắt** nội dung khi sử dụng - đọc đầy đủ để đảm bảo output đúng chuẩn.

> **QUY ƯỚC ĐƯỜNG DẪN (BẮT BUỘC):** Mọi path trong file này dùng biến môi trường, KHÔNG hardcode:
> - Thay mọi `/home/claude/` bằng `$REPORT_OUTPUT_DIR/.tmp/` (cache ẩn - thư mục `.tmp` bị `/api/list-files` bỏ qua vì là dotdir, nên JSON KHÔNG hiện chip/file list cho user).
> - File cache ghi vào `$REPORT_OUTPUT_DIR/.tmp/sprint{N}_backlog.json` - **TUYỆT ĐỐI KHÔNG ghi `.json` vào `$REPORT_OUTPUT_DIR/` trực tiếp** (nếu ở top-level outputs, frontend sẽ hiện chip file JSON cho user).
> - Script Python nằm trong `$SKILL_DIR/scripts/` - chạy `cd "$SKILL_DIR" && python3 scripts/<name>.py "$REPORT_OUTPUT_DIR/.tmp/sprint{N}_backlog.json"`.
> - Khi copy file output cho user (chỉ `.xlsx` + `.md`): `cp <src> "$REPORT_OUTPUT_DIR/<dest>"` - **KHÔNG copy `.json` ra `$REPORT_OUTPUT_DIR/`**.
> - Có thể dùng helper (path tương đối theo script, không dùng `~/.claude/skills`): `import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "_shared")); from output_path import ensure_output_dir, join_output, safe_name`.

## Mục lục

- [Workflow chi tiết](#workflow)
- [Quy tắc EPIC-0 Init Sprint (BẮT BUỘC)](#quy-tắc-epic-0-init-sprint--bắt-buộc)
- [Quy tắc giới hạn effort mỗi task](#quy-tắc-giới-hạn-effort-mỗi-task--bắt-buộc)
- [Quy tắc Story Sequential per Member](#quy-tắc-story-sequential-per-member--bắt-buộc)
- [Xử lý CSOC Pentest & Pilot](#xử-lý-csoc-pentest--pilot)
- [Pre-flight Checklist (BẮT BUỘC trước khi xuất file)](#pre-flight-checklist--bắt-buộc-trước-khi-xuất-file)
- [Limitations](#limitations)
- [Hướng dẫn chỉnh sửa sau khi generate](#chỉnh-sửa-sau-khi-generate)

---


## Workflow

### Step 0 - Hỏi trước khi bắt đầu

> ⚠️ **KHÔNG tự động tạo output.** Hỏi → chờ user xác nhận (*"ok làm đi"*, *"bắt đầu"*, *"go"*) → mới thực thi.

**Luôn hỏi các câu này trước:**

> 1. Dự án đã có nguồn lực (nhân sự) chưa? Nếu có, liệt kê rõ từng người và role (VD: 2 DEV, 1 QC, 1 PM).
> 2. Ngày bắt đầu Sprint là khi nào? (Duration sẽ tự tính dựa trên effort)
> 3. Danh sách User Story hoặc Product Backlog đã có chưa?
> 4. Sprint này có giai đoạn **pentest** (CSOC pentest) không? Nếu có: scope pentest là gì (tính năng nào / sprint nào), do đơn vị nào thực hiện (nội bộ hay third-party)?
> 5. Sprint này có giai đoạn **pilot** sau go-live không?

> ⚠️ Câu 4 và 5 là **tùy chọn** - nếu user không đề cập hoặc trả lời "không" → bỏ qua, không đưa task pentest / pilot vào story. Chỉ đưa vào khi user xác nhận **có**.

**Xử lý kết quả:**
- **Có nguồn lực cụ thể** → dùng label cụ thể: `DEV1`, `DEV2`, `QC1`, v.v. (xem rule phân công tại Step 5)
- **Chưa có nguồn lực** → điền role: `PM` / `TL` / `Dev` / `BA` / `QC`
- **Có ngày bắt đầu** → tự tính ngày kết thúc dựa trên tổng effort và số lượng nhân sự
- **Chưa có ngày** → để `<DD/MM/YY>`
- **Có User Story / Backlog** → dùng để lên Sprint Backlog theo định nghĩa Story là tính năng lớn (tương đương EPIC)
- **Chưa có** → chờ, không tiếp tục
- **Có pentest** → phân bổ các task pentest (chuẩn bị môi trường, hỗ trợ pentest, DEV fix bug pentest, QC recheck pentest, security sign-off) trực tiếp vào các Story tính năng tương ứng
- **Có pilot** → phân bổ các task pilot (monitor log, smoke test sau deploy, feedback, tổng kết) trực tiếp vào các Story tính năng tương ứng

### Step 1 - Thu thập input

**BẮT BUỘC:**
- ✅ Danh sách User Story hoặc Product Backlog đã có
- ✅ Sprint number

**TÙY CHỌN:**
- Sprint Goal → tự đề xuất nếu không có
- Team capacity (số người, ngày làm việc) → nếu thiếu, **tự áp dụng default 40h/tuần/member** - xem chi tiết trong `references/backlog-guide.md`
- Complexity / Priority từng story → mặc định `2-Medium`
- Sprint data JSON (nếu có) → chạy velocity analysis để lấy commitment ceiling

### Step 2 - Lên Sprint Backlog

1. **User Story là tính năng lớn (tương đương định nghĩa EPIC)**: Mỗi User Story là một tính năng lớn cần phát triển trong sprint/version.
2. **Tích hợp toàn bộ phase vào Story tính năng**: Các task và các phase như `init`, `QC test/testing`, `pentest`, `UAT`, `pilot` đều được **move vào bên trong các Story tính năng** dựa vào độ phù hợp nghiệp vụ và thời gian ngay giai đoạn đó (không tách rời thành các EPIC kỹ thuật/phase riêng biệt).
3. Break thành Tasks cụ thể với PIC và effort (Manday/Hour).
4. Tính Story Point theo công thức trong `backlog-guide.md`.
5. Sắp xếp theo Story tính năng lớn → Tasks.

> **⛔ QUY TẮC PHÂN BỔ CÁC PHASE VÀO STORY TÍNH NĂNG LỚN - BẮT BUỘC:**
>
> Toàn bộ các phase từ khởi động đến release đều được tổ chức khép kín bên trong các Story tính năng lớn:
> - **Init phase (W1):** 
>   - **PM:** Kick-off, Sprint Planning, Risk tracking tuần 1 (gắn vào Story 1 hoặc Story trọng tâm)
>   - **BA:** Phân tích yêu cầu + Wireframe + Viết URD cho Story tính năng (hoàn thành trong W1)
>   - **DEV:** Setup môi trường, Review hệ thống hiện tại, Technical design, Refactor codebase
>   - ⛔ **QC không có task ở W1** - QC onboarding bắt đầu từ W2 trở đi sau khi BA hoàn tất URD
> - **Development phase:** DEV coding, unit test, staging deploy cho từng tính năng.
> - **QC test/testing phase:** 
>   - BA demo & clear nghiệp vụ cho QC, hỗ trợ QC test/testing
>   - QC onboarding (hiểu nghiệp vụ, viết test case)
>   - QC thực hiện test/testing chính thức sau khi DEV hoàn tất coding
>   - DEV fix bug QC (`task_process = Coding`), QC recheck sau fix
> - **Pentest & UAT phase:**
>   - BA viết UAT scenario, user guide, hỗ trợ UAT
>   - DEV chuẩn bị môi trường pentest, hỗ trợ pentest, DEV fix bug pentest & UAT
>   - QC recheck pentest, Security sign-off
> - **Deploy & Pilot phase:**
>   - Staging deploy trước QC test/testing
>   - Production deploy (Thứ 2 hoặc Thứ 4) sau khi hoàn tất QC test/testing, UAT và pentest sign-off
>   - QC post-deploy smoke test, DEV monitor log & hotfix, BA feedback pilot, PM tổng kết pilot & đóng sprint

> **⛔ QUY TẮC GIỚI HẠN EFFORT VÀ THỜI LƯỢNG MỖI TASK (≤ 3 WORKING DAYS) - BẮT BUỘC:**
>
> - Mỗi task **tối đa 24 giờ** (`est_effort_hour <= 24`) và **thời lượng tối đa 3 ngày làm việc** (working days Mon–Fri `≤ 3 ngày`).
> - Nếu effort ước tính > 24h hoặc thời lượng > 3 ngày làm việc → **bắt buộc tách thành nhiều task nhỏ hơn**.
> - Tên task sau khi tách phải rõ phạm vi: ví dụ `"Implement UI - Phần 1: Danh sách"` / `"Implement UI - Phần 2: Form xử lý"`.
> - **Không được** dùng tên chung chung như `"Phần 1"`, `"Phần 2"` - mỗi task phải đứng độc lập, tên tự mô tả được nội dung.
> - **QUY TẮC ĐẶC THÙ CHO ROLE PM (CẤM VI PHẠM):**
>   - ⛔ **CẤM TUYỆT ĐỐI** tạo 1 task PM dạng "Quản lý / theo dõi tiến độ" kéo dài xuyên suốt toàn sprint (ví dụ: `start_date` đầu sprint, `due_date` cuối sprint) hoặc kéo dài > 3 ngày làm việc.
>   - ✅ **PHẢI** chia nhỏ task của PM theo từng tuần (Weekly) hoặc theo sự kiện/milestone cụ thể, mỗi task **tối đa 3 ngày làm việc** (`est_effort_hour <= 24`, thường 4h–8h):
>     - `"Kick-off & Lập kế hoạch Sprint"` (W1, 8h, 1 ngày làm việc)
>     - `"Theo dõi tiến độ & Quản trị rủi ro – Tuần 1"` (W1, 4-8h, ≤ 3 ngày làm việc)
>     - `"Theo dõi tiến độ & Quản trị rủi ro – Tuần 2"` (W2, 4-8h, ≤ 3 ngày làm việc)
>     - `"Điều phối UAT & Chuẩn bị Release"` (tuần UAT, 4-8h, ≤ 3 ngày làm việc)
>     - `"Sprint Review & Retrospective"` (tuần cuối, 4-8h, 1 ngày làm việc)

> **⛔ QUY TẮC STORY SEQUENTIAL PER MEMBER - BẮT BUỘC:**
>
> Trong cùng 1 EPIC, mỗi PIC **không được start task ở US tiếp theo trước khi hoàn thành task cuối cùng của họ ở US hiện tại**.
>
> - Áp dụng **per-member**: DEV1 xong US_1.1 mới được start US_1.2; BA xong phân tích US_1.1 mới sang US_1.2
> - DEV1 và DEV2 làm **khác US trong cùng EPIC** → parallel OK (không conflict)
> - PM tracking tasks: được miễn quy tắc tuần tự (sequential per member) giữa các US, nhưng **BẮT BUỘC** phải tuân thủ quy tắc thời lượng (tối đa 3 ngày làm việc, nằm trong cùng tuần LV và cùng tháng); phải chia nhỏ theo từng tuần (Tuần 1, Tuần 2...), **CẤM** tạo 1 task kéo dài toàn sprint
> - Sau khi shift, bắt buộc **re-sort** tasks theo start_date tăng dần (xem Bước 2b)


>
> - `start_date` và `due_date` của mọi task **phải nằm trong cùng một tuần làm việc** (thứ 2 → thứ 6)
> - **Cấm** để một task có `start_date` tuần này và `due_date` tuần sau (tức span qua Thứ 7/CN)
> - Ví dụ vi phạm: task 2 ngày bắt đầu thứ 6 → due thứ 2 tuần sau → **phải break**
> - Cách xử lý khi task span weekend:
>   1. Tính số giờ còn lại từ start_date đến hết thứ 6 → tạo task Phần 1 (due_date = thứ 6)
>   2. Phần effort còn lại → tạo task Phần 2 (start_date = thứ 2 tuần sau)
>   3. Lặp lại nếu Phần 2 vẫn còn span tiếp
> - Tên task sau khi tách phải mô tả rõ nội dung: `"Implement API - Tuần 1"` / `"Implement API - Tuần 2"`
> - **Áp dụng cho mọi task của mọi role** (BA, DEV, QC, PM)

> **⛔ QUY TẮC EVEN NUMBER EFFORT - BẮT BUỘC (v2.10):**
>
> - **Tất cả** `est_effort_hour` phải là 4, 8, 16 hoặc 24 (ưu tiên 8h)
> - **KHÔNG làm tròn số lẻ thành chẵn một cách khiên cưỡng** (vd 3h→4h chỉ vì cho chẵn)
> - Cách xử lý effort lẻ:
>   1. Phân tích lại complexity để justify mức chẵn hợp lý (vd 3h → phân tích lại task có complexity 7 thay vì 6 → lên 4h)
>   2. Gộp với task cùng PIC để tổng effort số chẵn
>   3. Chia subtask: 1h+1h+1h=3h nhưng 3 subtask mỗi cái 1h (số lẻ) → không được, phải gộp thành 2h+2h=4h và điều chỉnh complexity
> - **Bắt buộc kiểm tra** trong validate script (xem Step 2b)

> **⛔ QUY TẮC TASK KHÔNG ĐƯỢC SPAN QUA THÁNG - BẮT BUỘC:**
>
> - `start_date` và `due_date` của mọi task **phải nằm trong cùng một tháng**
> - **Cấm** để một task có `start_date` tháng này và `due_date` tháng sau
> - Ví dụ vi phạm: task bắt đầu 29/06 → due 01/07 → **phải tách**
> - Cách xử lý khi task span qua tháng:
>   1. **Phần tháng hiện tại:** `start_date` giữ nguyên, `due_date` = ngày làm việc cuối cùng của tháng, effort tính theo số ngày LV trong tháng đó, thêm suffix `– Phần T{MM}` vào tên task
>   2. **Phần tháng tiếp theo:** `start_date` = ngày làm việc đầu tiên tháng sau, `due_date` giữ nguyên, effort = phần còn lại, thêm suffix `– Phần T{MM+1}` vào tên task
>   3. Lặp lại nếu task span qua nhiều tháng
> - Tên task sau khi tách phải mô tả rõ nội dung: `"Implement API – Phần T06"` / `"Implement API – Phần T07"`
> - **Áp dụng cho mọi task của mọi role** (BA, DEV, QC, PM)

### Step 3 - Tính Manday Net với Buffer 10%

> **QUY TẮC BẮT BUỘC:** Manday net = 100% effort + 10% buffer dự phòng
>
> ```
> Total Manday Net = Σ(effort tất cả task) × 1.10
> ```
>
> - Áp dụng buffer 10% trên **tổng effort**, không phải từng task
> - Ghi rõ trong bảng tổng hợp: Subtotal + Buffer 10% + Total Manday Net

### Step 4 - Tự tính Duration Sprint

> **QUY TẮC:** Duration sprint KHÔNG cố định 2 tuần hay 3 tuần. Tính dựa trên effort thực tế.
>
> ```
> Duration (ngày) = Total Manday Net / số_member_dev_chính
> ```
>
> - Làm tròn lên ngày làm việc gần nhất
> - ⛔ **BẮT BUỘC:** `start_date` và `due_date` của mọi task **KHÔNG ĐƯỢC rơi vào Thứ 7, Chủ nhật hoặc ngày lễ** - nếu tính ra ngày đó, tự động đẩy sang ngày làm việc tiếp theo.
> - ⛔ **BẮT BUỘC:** Mọi task phải nằm gọn trong **cùng một tuần làm việc** (T2–T6) **và cùng tháng**. Task span qua weekend phải tách theo tuần; task span qua tháng phải tách theo tháng - xem chi tiết tại Step 2.
> - **Nếu user chỉ định cố định số tuần** (VD: "code trong 2 tuần") → dùng số tuần đó, tính Dev Complete = start_date + số ngày LV tương ứng (trừ ngày nghỉ lễ nếu có), reschedule toàn bộ downstream phases (QC, UAT, Deploy) từ Dev Complete mới.
> - **Nếu user khai báo ngày nghỉ lễ** → loại khỏi ngày LV khi tính duration và shift toàn bộ task bị ảnh hưởng sang ngày LV tiếp theo.
>
> **⛔ QUY TẮC DEPLOY - BẮT BUỘC:**
>
> **Production deploy:**
> - Chỉ được deploy production vào **Thứ 2 hoặc Thứ 4**
> - Nếu ngày tính ra không phải T2/T4 → tự động đẩy sang T2 hoặc T4 gần nhất (ưu tiên T2 nếu khoảng cách bằng nhau)
> - Production deploy phải sau khi **tất cả các phase đã done**: QC Testing ✅ + UAT ✅ + Pentest Remediation ✅ (nếu có) + Security Sign-off ✅
>
> **Staging deploy:**
> - **Không có rule ngày** (không bắt buộc T2/T4)
> - ⛔ **BẮT BUỘC:** Staging deploy phải xảy ra **TRƯỚC KHI QC Testing bắt đầu** - đây là điều kiện tiên quyết
> - Thời điểm chuẩn: **ngày làm việc cuối cùng của Dev Complete** (sau khi DEV hoàn tất coding)
> - QC Testing, UAT và Pentest (nếu có) đều thực hiện trên môi trường **staging**, không phải production
>
> **Thứ tự đúng bắt buộc:**
> ```
> Dev Complete → Staging Deploy → QC Testing → UAT + Pentest (song song, trên staging)
>             → Remediation (nếu có) → Security Sign-off → Production Deploy (T2/T4) → Pilot
> ```

### Step 5 - Phân công PIC cụ thể

> **QUY TẮC PHÂN CÔNG - BẮT BUỘC:**
> - Nếu user cung cấp **2 DEV** → phân công rõ: `DEV1`, `DEV2` (hoặc tên thật nếu có)
> - Nếu **3 DEV** → `DEV1`, `DEV2`, `DEV3` - và cứ thế
> - **KHÔNG ĐƯỢC** dùng label chung `DEV` khi số lượng đã xác định
> - Phân chia task hợp lý, tránh một người quá tải so với người khác (target **~40h/tuần**, không dưới 36h và không vượt 44h)

> **⛔ QUY TẮC PHÂN BỔ TASK THEO ROLE - VI PHẠM = OUTPUT SAI:**
>
> **1. Mọi role đều phải có task trong backlog:**
> - `PM` → task: kick-off, theo dõi tiến độ định kỳ (chia theo tuần ≤ 3 working days), risk tracking, điều phối UAT & pentest, Sprint Review, Retrospective, tổng kết pilot (gắn vào Story 1 hoặc Story release).
> - `BA` → task bắt buộc gồm **các loại chia theo phase trong từng Story tính năng lớn**:
>
>   **Tuần đầu - Init Phase (hoàn thành trước khi DEV bắt đầu coding, gắn vào Story tính năng lớn W1):**
>   - `Phân tích yêu cầu` (`task_process = Requirement & Design`): phân tích tính năng, viết Acceptance Criteria
>   - `Thiết kế Wireframe` (`task_process = Requirement & Design`): wireframe / mockup cho tính năng
>   - `Viết URD` (`task_process = Requirement & Design`): tổng hợp URD cho Story tính năng (hoàn thành ≤ thứ 6 tuần đầu)
>
>   **Trước QC test/testing (cuối coding phase, song song Dev finishing):**
>   - `Viết UAT Scenario` (`task_process = Requirement & Design`): kịch bản UAT cho Story tính năng
>   - `Viết User Guide` (`task_process = Requirement & Design`): tài liệu hướng dẫn sử dụng tính năng mới
>
>   **Đầu giai đoạn QC test/testing:**
>   - `Demo & Clear nghiệp vụ cho QC` (`task_process = Requirement & Design`): BA demo từng luồng, giải đáp trước khi QC test chính thức
>   - `Hỗ trợ QC test/testing` (`task_process = Requirement & Design`): BA standby, xác nhận AC, clarify edge case, verify bug report
>
>   **Cuối sprint - UAT & Release phase:**
>   - `Hỗ trợ UAT` (`task_process = Requirement & Design`): hướng dẫn user test, tổng hợp feedback, sign-off
>   - `Thu thập feedback pilot` (`task_process = Requirement & Design`): theo dõi người dùng vận hành pilot thực tế
>
> - `DEV1`, `DEV2` → task: setup môi trường & review kiến trúc (W1) + implement coding (`task_process = Coding`) + **fix bug QC** (`task_process = Coding`) + chuẩn bị môi trường pentest + **fix bug pentest** (`task_process = Coding`) + **fix bug UAT** (`task_process = Coding`) + deploy staging/production + monitor log & hotfix pilot.
> - `QC1`, `QC2` → task: hiểu nghiệp vụ (sau khi BA hoàn tất URD) + test/testing chính thức (sau Dev Complete) + **recheck sau fix bug QC** (`task_process = Testing`) + recheck pentest.
>
> ⚠️ **Fix bug luôn do DEV thực hiện → `task_process = Coding`. QC chỉ verify/recheck → `task_process = Testing`.**
>
> **2. Tích hợp trọn vẹn các phase vào Story tính năng lớn (Feature-Centric):**
> - **KHÔNG tách rời thành các EPIC kỹ thuật riêng biệt** (như EPIC-0 Init Sprint, EPIC QC/UAT riêng, EPIC Pentest riêng, EPIC Pilot riêng).
> - Mỗi User Story đại diện cho một **tính năng lớn** (tương đương EPIC) và bao gồm trọn vẹn vòng đời phát triển của tính năng đó:
>   - Task Init (BA phân tích/URD, DEV setup, PM kick-off) nằm ngay trong Story tính năng ở tuần 1 (W1).
>   - Task Coding & Unit test nằm ở giai đoạn Development của Story.
>   - Task QC Onboarding, QC test/testing, DEV fix bug QC, QC recheck nằm ở giai đoạn test/testing của Story.
>   - Task Pentest & UAT (kèm DEV fix bug pentest/UAT và QC recheck) nằm ở giai đoạn nghiệm thu của Story.
>   - Task Deploy (staging trước QC, production T2/T4) và Pilot (monitor, hotfix, feedback) nằm ở giai đoạn release của Story.
>
> **3. Xử lý Pentest (khi user xác nhận có pentest):**
> - Phân bổ các task pentest trực tiếp vào Story tính năng liên quan:
>   - PM: Phối hợp đơn vị pentest, theo dõi tiến độ pentest
>   - DEV: Chuẩn bị môi trường staging cho pentest, hỗ trợ kỹ thuật trong quá trình pentest
>   - DEV: Fix bug pentest (các finding Critical/High/Medium)
>   - QC: Phối hợp phân loại finding và recheck sau khi DEV fix bug pentest
>   - Security Sign-off là điều kiện tiên quyết trước khi production deploy
> - Thực hiện song song với UAT trên môi trường staging
>
> **4. Xử lý Pilot (khi user xác nhận có pilot):**
> - Phân bổ các task pilot trực tiếp vào Story tính năng liên quan sau production deploy:
>   - Bắt đầu ngay ngày Production Deploy (Thứ 2 hoặc Thứ 4), kéo dài 3–5 ngày làm việc
>   - DEV: Monitor log/performance/alert + Hotfix nếu có sự cố
>   - QC: Post-deploy smoke test trên production
>   - BA: Thu thập feedback người dùng thực tế trong giai đoạn pilot
>   - PM: Tổng kết pilot, bàn giao chính thức, đóng sprint

> **⛔ WEEKLY BALANCE CHECK - BẮT BUỘC sau khi phân công:**
>
> Sau khi gán task xong, chạy bash để kiểm tra giờ từng DEV theo tuần:
>
> ```bash
> cd "$SKILL_DIR" && python3 -c "
> import json, sys, os
> from datetime import datetime, timedelta
> from collections import defaultdict
> 
> path = os.environ['REPORT_OUTPUT_DIR'] + '/.tmp/sprint{N}_backlog.json'
> if len(sys.argv) > 1: path = sys.argv[1]
> with open(path, encoding='utf-8') as f:
>     data = json.load(f)
> 
> def parse_date(s): return datetime.strptime(s, '%d/%m/%Y')
> 
> weekly = defaultdict(lambda: defaultdict(float))
> caps = {28:32,29:40,30:40,31:40,32:40,33:40}
> 
> for epic in data['epics']:
>     for us in epic['user_stories']:
>         for t in us['tasks']:
>             pic = t.get('pic','')
>             sd = parse_date(t['start_date'])
>             dd = parse_date(t['due_date'])
>             h = t.get('est_effort_hour', 0)
>             d = sd; wds = []
>             while d <= dd:
>                 if d.weekday() < 5: wds.append(d)
>                 d += timedelta(days=1)
>             if wds:
>                 hpd = h / len(wds)
>                 for wd in wds:
>                     iso = wd.isocalendar()
>                     weekly[pic][(iso[0],iso[1])] += hpd
> 
> weeks = [(2026,28),(2026,29),(2026,30),(2026,31),(2026,32),(2026,33)]
> for pic in sorted(weekly.keys()):
>     print(f'\\n{pic}:')
>     for wk in weeks:
>         v = round(weekly[pic][wk], 1)
>         cap = caps.get(wk[1], 40)
>         if v > cap: flag = ' ❌ OVERLOAD'
>         elif v == cap: flag = ' ✅'
>         elif v >= cap * 0.8: flag = ' ✅ (80%+)'
>         else: flag = f' ⚠️ UNDER ({v:.0f}h < {cap}h)'
>         print(f'  T{wk[1]}: {v:5.1f}h / {cap}h{flag}')
>     total = sum(weekly[pic][wk] for wk in weeks)
>     cap_total = sum(caps.get(wk[1],40) for wk in weeks)
>     print(f'  TOTAL: {total:.0f}h / {cap_total}h')
> "
> ```
>
> **Tiêu chí đạt (v2.9 - Fixed 40h/tuần):**
> - Mỗi member mỗi tuần: **target = capacity cố định** (40h cho tuần 5 ngày, 32h cho tuần 4 ngày)
> - **Không có OVERLOAD** (> capacity) - ngoại trừ trường hợp dependency cứng không thể dịch chuyển
> - **Không có UNDERLOAD** (< 80% capacity) - ngoại trừ tuần cuối sprint (QC/UAT/Deploy phase)
> - Chênh lệch tổng effort giữa các DEV: **≤ 15%**
> - Nếu có OVERLOAD → áp dụng các kỹ thuật trong [Weekly Balancing & Redistribution](#quy-tắc-weekly-balancing--redistribution-v29)
>
> **⛔ BẮT BUỘC - không được bỏ qua bước này:**
> Script trên phải **thực sự được chạy và output phải được đọc** trước khi xuất file - không suy đoán, không giả định số liệu đạt chuẩn. Nếu có bất kỳ dòng nào hiện `⚠️ UNDER` hoặc `❌ OVERLOAD` ngoài các ngoại lệ hợp lệ bên dưới, đây là **lỗi chặn xuất file** - phải sửa xong và chạy lại script để xác nhận `✅` trước khi tiếp tục Bước tiếp theo. Tự kiểm tra bằng mắt không thay thế được việc chạy script.
>
> **Xử lý khi phát hiện UNDERLOAD (< 80% capacity) ở tuần Development, không thuộc ngoại lệ:**
> Đây là tín hiệu effort thực tế của DEV/TL/thành viên đó **chưa đủ để lấp đầy 40h/tuần trong khung thời gian đã chọn** - không tự động chấp nhận, xử lý theo thứ tự ưu tiên:
> 1. **Nén timeline (ưu tiên trước):** Nếu tổng effort của member đó chia cho 40h/tuần cho ra số tuần lẻ nhỏ hơn khung thời gian hiện tại → rút ngắn Development phase tương ứng (dời task ở các tuần sau lên sớm hơn), tính lại Dev Complete mới, reschedule QC/UAT/Deploy theo dependency.
> 2. **Bổ sung task thực tế** (không phải task giả) nếu nén timeline không khả thi do dependency cứng: thêm các hạng mục hợp lệ theo vai trò - chuẩn bị test data mẫu, setup CI/CD, khảo sát tài liệu API/hệ thống liên quan, integration test, code review sâu hơn (performance, security, retry/error handling), viết technical documentation. Mỗi task bổ sung phải gắn với scope thực của sprint, không lặp lại nội dung đã có.
> 3. Nếu cả hai cách trên đều không áp dụng được (VD: role đó chỉ hoạt động ở giai đoạn cuối sprint như QC/UAT) → được coi là ngoại lệ hợp lệ, ghi rõ lý do trong output thay vì âm thầm bỏ qua.
>
> **Ngoại lệ hợp lệ (không cần điều chỉnh):**
> - Tuần có **ngày nghỉ lễ** → capacity thực tế thấp hơn tương ứng số ngày nghỉ
> - Tuần cuối sprint có **locked dependencies** (pentest findings fix, export chờ unit test, phê duyệt sau export) → chấp nhận overload ≤ 44h
> - Task **Monitor** (passive/on-call) không tính vào active effort
> - Vai trò chỉ hoạt động ở giai đoạn cuối/đầu sprint theo đặc thù (PM, BA, QC) - rule 40h/tuần **chỉ bắt buộc áp dụng cho DEV và TL**, các role khác dùng tiêu chí effort thực tế theo scope, không cần lấp đủ 40h/tuần

> **⛔ NO-GAP CHECK - BẮT BUỘC sau khi xếp lịch task:**
>
> Mỗi DEV phải có task liên tục mỗi ngày làm việc trong sprint - **không được có ngày trống** giữa các task.
>
> ```bash
> cd "$SKILL_DIR" && python3 -c "
> import json, os
> from datetime import datetime, timedelta
> from collections import defaultdict
> HOLIDAYS = set()  # Thêm ngày nghỉ lễ nếu có, VD: {datetime(2026,6,17).date()}
> path = os.environ['REPORT_OUTPUT_DIR'] + '/.tmp/sprint{N}_backlog.json'
> with open(path, encoding='utf-8') as f:
>     data = json.load(f)
> def workdays(start_str, due_str):
>     s = datetime.strptime(start_str, '%d/%m/%Y')
>     e = datetime.strptime(due_str, '%d/%m/%Y')
>     days = set()
>     cur = s
>     while cur <= e:
>         if cur.weekday() < 5 and cur.date() not in HOLIDAYS:
>             days.add(cur.date())
>         cur += timedelta(days=1)
>     return days
> coverage = defaultdict(set)
> sprint_start = sprint_end = None
> for epic in data['epics']:
>     for us in epic['user_stories']:
>         for t in us['tasks']:
>             if t.get('pic','').startswith('DEV') and t.get('start_date') and t.get('due_date'):
>                 covered = workdays(t['start_date'], t['due_date'])
>                 coverage[t['pic']].update(covered)
>                 if sprint_start is None or min(covered) < sprint_start:
>                     sprint_start = min(covered)
>                 if sprint_end is None or max(covered) > sprint_end:
>                     sprint_end = max(covered)
> if sprint_start:
>     all_workdays = set()
>     cur = sprint_start
>     while cur <= sprint_end:
>         if cur.weekday() < 5 and cur not in HOLIDAYS:
>             all_workdays.add(cur)
>         cur += timedelta(days=1)
>     for dev, covered in sorted(coverage.items()):
>         gaps = sorted(all_workdays - covered)
>         if gaps:
>             print(f'{dev}: GAP DETECTED on {[d.strftime(\"%d/%m/%Y\") for d in gaps]}')
>         else:
>             print(f'{dev}: OK - no gaps')
> "
> ```
>
> **Tiêu chí đạt:**
> - Mỗi DEV: **không có ngày làm việc nào trống** trong sprint (từ ngày đầu đến ngày cuối của dev đó)
> - Ngày nghỉ lễ đã khai báo **không tính là gap** - hệ thống tự bỏ qua
> - Nếu có GAP → điều chỉnh start_date/due_date task liền kề để lấp đầy khoảng trống trước khi tiếp tục
>
> **Cách xử lý gap:**
> 1. Kéo due_date task trước sang để phủ kín ngày trống, hoặc
> 2. Kéo start_date task sau lên sớm hơn, hoặc
> 3. Thêm task nhỏ (code review, technical documentation, hỗ trợ QC, refactor) để lấp gap

> **BẢNG ESTIMATE THEO COMPLEXITY - Tham chiếu khi ước tính giờ:**
>
> | task_complexity | API (BE) | UI (FE) | Unit Test | Integration Test | Code Review |
> |-----------------|----------|---------|-----------|------------------|-------------|
> | **6** (Medium)  | 6h       | 5h      | 2h        | 3h               | 1h          |
> | **7** (High)    | 10h      | 8h      | 3h        | 5h               | 2h          |
> | **8** (Very High)| 16h     | 12h     | 4h        | 7h               | 3h          |
>
> ⚠️ Đây là mức tham chiếu - điều chỉnh theo đặc thù từng task. Nhớ rule tối đa 16h/task (Step 2).

### Step 6 - Lịch QC (bắt buộc tách biệt)

> **QUY TẮC QC TIMELINE - BẮT BUỘC:**
> 1. **QC Onboarding / Nghiệp vụ** → chỉ bắt đầu sau khi BA hoàn tất **3 task chính** (Phân tích yêu cầu, Wireframe, URD) - thường từ đầu tuần 2 của sprint
> 2. **QC test/testing chính thức** → CHỈ sau khi DEV hoàn tất **coding + integration** (không phải sau unit test). Unit test của DEV **có thể overlap với QC 1–2 ngày đầu** - không cần chờ unit test xong 100% mới cho QC bắt đầu.
> 3. Thời gian QC test/testing tách riêng, không chồng lấp DEV coding; thường chiếm **15–30% thời gian Development**
> 4. Tên task QC phải rõ loại: `"QC – Nghiệp vụ"` và `"QC – test/testing"`
> 5. Thể hiện QC timeline trong bảng Milestone (Step 7)
> 6. **QC phase không được có gap** - các bước phải liên tục:
>    - Fix bug bắt đầu **ngay ngày làm việc tiếp theo** sau khi QC test/testing xong
>    - Recheck → UAT & Pentest → Deploy & Pilot phải nối tiếp nhau, không để khoảng trống
>    - Nếu Fix bug và Recheck xong trước cuối sprint → UAT bắt đầu ngay, không chờ
> 7. **Dependency check bắt buộc khi xác định QC start date:**
>    - QC start > (coding done + integration done) ✅
>    - QC start > unit test done ❌ (không dùng mốc này - unit test có thể overlap)
>    - Kiểm tra: `QC_start_date > max(due_date của task Coding + Integration của mọi DEV)`

### Step 7 - Phase & Milestone Timeline

> **BẮT BUỘC** tạo **2 bảng riêng biệt** để phân biệt rõ ràng Milestone và Phase theo template file `assets/sprint_backlog_template.md`:

**1. Phases (Giai đoạn chính)** – Có Start Date, End Date, Duration:
- Phase 1: 📋 Requirements & URD (W1)
- Phase 2: 📚 QC Onboarding (W2+)
- Phase 3: ⚙️ Development
- Phase 4: 🧪 QC Testing (QC test/testing chính thức)
- Phase 5: 🛡️ Pentest & UAT (kèm fix bug)
- Phase 6: 🚀 Deploy & Pilot (production deploy T2/T4 + pilot)

**2. Key Milestones** – Chỉ có Target Date (điểm mốc quan trọng):
- 1: 📄 URD Sign-off
- 2: 🏁 Sprint Start
- 3: ⚙️ Dev Complete
- 4: ✅ Testing Complete (QC hoàn tất test/testing & fix bug closed)
- 5: 🤝 UAT & Pentest Sign-off
- 6: 🎉 Go-Live & Pilot (Release và vận hành pilot)

**Hướng dẫn tính Phase (bắt buộc):**
- Duration của từng Phase = tổng effort task thuộc giai đoạn đó / số người tham gia (làm tròn lên).
- Start Date của Phase sau = End Date của Phase trước (liên tục).
- Sử dụng Total Manday Net (Step 3) để đảm bảo tổng duration các Phase chính khớp với Sprint Duration (Step 4).
- Best practice mặc định nếu chưa có effort chi tiết:
  - Requirements + URD: 2–4 ngày
  - QC Onboarding: 1–2 ngày
  - Development: 70–80% tổng effort DEV
  - QC Testing: 15–30% thời gian Development
  - UAT + Pentest + Deploy + Pilot: 3–6 ngày

**Lưu ý:** Mỗi Milestone thường trùng với End Date của một Phase quan trọng.
> ⚠️ **BẮT BUỘC:** Tổng Duration của tất cả Phases phải **khớp chính xác** với Sprint Duration đã tính ở Step 4.

### Step 8 - Tổng hợp Manday theo Role

> **BẮT BUỘC** tạo bảng tổng hợp manday cuối output. Gộp chung theo role:

> ⚠️ **Ghi chú:** QC Onboarding (hiểu nghiệp vụ) được tính sau khi BA hoàn tất URD. QC Testing chính thức bắt đầu sau khi Dev Complete.

### Phần trăm phân bổ effort hợp lý theo role (Best Practice)

| Role | Phần trăm hợp lý | Ghi chú |
|------|------------------|---------|
| PM   | 7–12%            | Quản lý sprint, rủi ro, release & pilot |
| BA   | 10-15%           | Phân tích, URD, hỗ trợ test & UAT/pilot |
| DEV  | 50–60%           | Coding, unit test, staging deploy & fix bug |
| QC   | 20–25%           | Onboarding + test/testing + recheck |


---

> **⛔ MONITOR TASK - PASSIVE / BACKGROUND (v2.10):**
> - Task "Monitor log/performance/alert sau go-live" trong giai đoạn Pilot là **passive/on-call**
> - Effort ghi nhận (vd 8h–12h) là thời gian trực, không phải làm việc liên tục
> - Có thể coi là background task và **không tính vào active effort** khi báo cáo weekly
> - Nếu không có sự cố → effort thực tế ~0h; nếu có sự cố → chuyển thành active + fix bug hotfix

> **⛔ QUY TẮC WEEKLY BALANCING & REDISTRIBUTION (v2.10):**
>
> Khi 1 member có tổng effort vượt quá capacity các tuần, áp dụng các kỹ thuật sau:
>
> | Kỹ thuật | Mô tả | Ví dụ |
> |----------|-------|-------|
> | **Cross-week split** | Chia task chạy qua ranh giới tuần (nhưng không qua tháng/week) | Task 8h split thành 4h cuối tuần này + 4h đầu tuần sau |
> | **Compression** | Dồn task trong ít ngày hơn (effort giữ nguyên) | Task 8h/2 ngày → 8h/1 ngày |
> | **Cross-Story overlap** | Task từ Story tính năng khác nhau chạy song song trong cùng PIC | 1 DEV làm task của 2 Story tính năng khác nhau cùng lúc |
> | **Tech debt relocation** | Chuyển technical debt xuống tuần đầu/rỗi | Dời task tech debt từ tuần cuối sang tuần còn dư capacity |
>
> **Giới hạn:** Không thể ép task dependency cứng (pentest chờ findings, export chờ unit test) vào tuần sớm hơn.

> **⛔ LOCKED DEPENDENCIES END-OF-SPRINT (v2.10):**
>
> Khi sprint có **pentest** hoặc luồng phụ thuộc chuỗi, tuần cuối sprint thường bị khoá bởi dependency cứng dạng:
> ```
> [Pentest] DEV fix bug findings    ← chỉ bắt đầu sau khi có kết quả pentest
> [Dev] Export báo cáo              ← chỉ bắt đầu sau khi Unit Test hoàn tất
>       Phê duyệt                   ← chỉ bắt đầu sau khi Export xong
> [Pilot] Monitor sau go-live       ← chỉ bắt đầu sau go-live
> ```
> → Luôn kiểm tra: task nào ở tuần cuối có thể đẩy lên tuần trước đó? Nếu dependency không cho phép → chấp nhận overload ≤44h ở tuần đó hoặc báo user.

## ✅ PRE-FLIGHT CHECKLIST - BẮT BUỘC TRƯỚC KHI XUẤT FILE

**Dừng lại. Tự kiểm tra toàn bộ draft trước khi ghi file.** Nếu bất kỳ ô nào chưa ✅ → sửa trước, không xuất.

| # | Kiểm tra | Trạng thái |
|---|---|---|
| 1 | **Story là tính năng lớn (tương đương EPIC)** - Mỗi User Story đại diện cho một tính năng lớn cần phát triển trong sprint/version | ☐ |
| 2 | **Tích hợp các phase vào Story tính năng** - Các task và phase như `init`, `QC test/testing`, `pentest`, `UAT`, `pilot` đều được move vào bên trong Story tính năng lớn phù hợp, không tách thành các EPIC kỹ thuật riêng | ☐ |
| 3 | **Đầy đủ task phase Init tuần đầu (W1)** - BA phân tích/URD, DEV setup môi trường/technical design, PM kick-off & planning tuần 1 nằm trong Story tính năng W1; QC không có task W1 | ☐ |
| 4 | Mọi Story tính năng đều có task của **DEV** (implement, staging deploy, fix bug QC, fix bug UAT/pentest) | ☐ |
| 5 | Label PIC cụ thể: `DEV1`, `DEV2`, `QC1`, `QC2` - không dùng label chung | ☐ |
| 6 | JSON hợp lệ: không có trailing comma, đóng ngoặc đúng | ☐ |
| 7 | Bảng Manday đã cập nhật đúng tổng giờ cho tất cả role, group theo role, kể cả PM | ☐ |
| 8 | **Không có task nào có `est_effort_hour > 24` HOẶC kéo dài > 3 ngày làm việc (working days ≤ 3)** - mọi task (kể cả PM) tối đa 3 ngày làm việc; nếu có, tách task trước khi xuất | ☐ |
| 9 | `start_date` và `due_date` toàn bộ task không rơi vào Thứ 7, Chủ nhật hoặc ngày lễ đã khai báo | ☐ |
| 10 | **Không span qua weekend và không span qua tháng** - `start_date` và `due_date` phải trong cùng tuần LV (T2–T6) **và** cùng tháng; nếu vi phạm → tách task trước khi xuất | ☐ |
| 11 | **Chuẩn hóa thuật ngữ chung (Text General)** - `test/testing` thay cho kiểm thử; `pentest` thay cho kiểm thử bảo mật / an toàn thông tin; `pilot` thay cho vận hành thử nghiệm; `fix bug` thay cho khắc phục lỗi | ☐ |
| 12 | **Even Number Effort** - tất cả `est_effort_hour` là 4, 8, 16 hoặc 24 (ưu tiên 8h) | ☐ |
| 13 | **Weekly Balance Fixed 40h** - đã **thực sự chạy** WEEKLY BALANCE CHECK và đọc output (không suy đoán); DEV/TL không OVERLOAD (trừ locked dependencies cuối sprint) và không UNDERLOAD (trừ ngoại lệ hợp lệ) | ☐ |
| 14 | **No-gap** - chạy NO-GAP CHECK (có khai báo HOLIDAYS); mọi DEV không có ngày làm việc trống trong sprint; không có GAP DETECTED | ☐ |
| 15 | **Tasks đã sort** - chạy Bước 2b; mọi task trong từng US được sắp xếp theo `start_date`, `due_date` tăng dần | ☐ |
| 16 | **US sequential per member** - trong cùng Story/tính năng, mỗi PIC không start task tiếp theo trước khi xong task trước; PM tracking tasks được miễn sequential nhưng vẫn tuân thủ max 3 working days/task & chia theo tuần | ☐ |
| 17 | **US description đúng format & độ dài** - mô tả nghiệp vụ trung tính, không dùng "Là [Role]...", độ dài ngắn gọn tầm 8–12 từ | ☐ |
| 18 | **Staging deploy đúng vị trí** - staging deploy nằm TRƯỚC QC test/testing start date; production deploy rơi vào Thứ 2 hoặc Thứ 4; thứ tự: Dev Complete → Staging Deploy → QC test/testing → UAT & Pentest → Production Deploy → Pilot | ☐ |

> Chỉ khi **tất cả 18 ô đều ✅** mới được xuất file output.

> Chỉ khi **tất cả 18 ô đều ✅** mới được xuất file output.

---

### Step 9 - Sprint Header & Output

#### Quy tắc Sprint Header & Backlog Items
1. **Root Object:**
   - `sprint_goal`: string
   - `time_box`: **array of strings** (mỗi dòng là 1 phần tử), đảm bảo đủ các thành phần chính: 1. Sprint Timeline, 2. Sprint Planning, 3. Daily Scrum, 4. Dev Complete, 5. QC test/testing, 6. UAT & Pentest, 7. Production Release, 8. Pilot, 9. Sprint Review & Retrospective
   - `epics`: array (đại diện cho các nhóm tính năng lớn / User Stories lớn)
2. **Epic / Story tính năng lớn:**
   - `epic`: string bao gồm số thứ tự và tên tính năng lớn (tương đương EPIC). Mỗi EPIC chứa các User Story tính năng lớn khép kín trọn vẹn các phase (Init, Coding, QC test/testing, UAT/Pentest, Release/Pilot)
   - Ví dụ: `"EPIC-1. Quản lý phân hệ Bán hàng nâng cao"`, `"EPIC-2. Tích hợp cổng thanh toán & đối soát"`
   - `user_stories`: array
3. **User Story:**
   - `us_id`, `module`, `description`, `priority`: string gồm `level`-`name`, `complexity`: string gồm `level`-`name`, `tasks`
   - **`description` - QUY TẮC FORMAT BẮT BUỘC:**
     - ⛔ **KHÔNG ĐƯỢC** dùng dạng "Là [Role], tôi muốn... để..."
     - ✅ **PHẢI** dùng dạng **mô tả nghiệp vụ trung tính**: diễn đạt cực kỳ ngắn gọn, súc tích (khoảng **8–12 từ**), nêu rõ tính năng/phạm vi cốt lõi của Story.
     - ⛔ **KHÔNG** viết câu văn dài dòng, không giải thích chi tiết giải thuật hay liệt kê danh sách điều kiện.
     - Ví dụ SAI (dạng persona): `"Là AM/Sale, tôi muốn tạo yêu cầu Nâng cấp..."`
     - Ví dụ SAI (quá dài): `"Cải tiến luồng tạo yêu cầu Nâng cấp: bỏ ràng buộc bắt buộc nhập đồng thời NIX và GIA, chỉ validate BW NIX khi thực sự có nâng NIX. Hiển thị Bảng thông số dịch vụ động theo từng loại dịch vụ."` (36 từ)
     - Ví dụ ĐÚNG (8–12 từ):
       - `"Cải tiến luồng tạo yêu cầu nâng cấp không bắt buộc NIX"` (10 từ)
       - `"Cấu hình công thức lương mới cho dịch vụ ZNS"` (9 từ)
       - `"Tạo giao diện hiển thị chi tiết công thức lương mới"` (10 từ)
       - `"Xử lý logic core lương tính toán tỉ lệ CTL mới"` (10 từ)
       - `"Bổ sung chức năng gửi bảng lương lên cấp phê duyệt"` (10 từ)
       - `"Thêm mới logic xử lý import giá vốn và doanh thu"` (10 từ)
       - `"Đồng bộ dữ liệu bảng chấm công nhân sự từ IHUB"` (10 từ) 
4. **Task:**
   - `pic`: người được assign
   - `task_name`: string, thuần mô tả task - ⛔ **KHÔNG được chứa label PIC** (DEV1, DEV2, QC1, QC2...) trong task_name hoặc notes; label PIC chỉ dùng ở field `pic`
   - `status`, `start_date`, `due_date`, `est_effort_hour`
   - `notes`: ghi chú bổ sung cho task - **nên có** cho phần lớn task (output mong muốn, điều kiện pass/fail, SLA xử lý, dependency quan trọng, edge case cần chú ý). Để `""` chỉ khi task thực sự không có gì cần lưu ý thêm. Một số ví dụ notes tốt:
     - BA task: `"Output: URD đầy đủ, PO sign-off trước 11/06; là điều kiện để DEV bắt đầu"`
     - DEV task: `"Critical bug phải fix trong ngày; không deploy nếu còn Critical open"`
     - QC task: `"Log bug trên Jira; severity Critical/High notify DEV ngay trong ngày"`
     - Deploy task: `"Maintenance window 22:00–01:00; rollback plan sẵn sàng trước khi deploy"` 
   - `task_complexity`: dựa vào độ khó của task
   - `type_of_work`: type of work
   - `task_process`: task process - **xem bảng định nghĩa bắt buộc bên dưới**
   - `task_priority`: task priority

**Bảng định nghĩa `task_process` - BẮT BUỘC tuân theo:**

| Giá trị | Áp dụng cho | Ví dụ task |
|---------|-------------|------------|
| `Requirement & Design` | BA phân tích, viết AC, vẽ wireframe, thiết kế DB/API, URD | "Phân tích luồng nghiệp vụ", "Viết Acceptance Criteria", "Thiết kế API endpoint" |
| `Coding` | DEV implement feature, **fix bug** (dù bug phát sinh từ QC hay UAT), refactor, viết unit test, code review | "Implement UI form", "Fix bug QC round 1", "Fix bug UAT", "Refactor service layer" |
| `Testing` | QC viết testcase, **thực hiện test** (manual/automation), recheck bug sau khi DEV fix xong | "Viết testcase", "QC Testing round 1", "Recheck bug sau fix", "Regression test" |
| `Deployment` | DEV/DevOps deploy lên môi trường (staging/prod), smoke test sau deploy, go-live | "Deploy staging", "Smoke test production", "Go-live & monitor" |
| `Project Management` | PM/TL: kick-off, theo dõi tiến độ, risk tracking, burndown, sprint ceremonies | "Sprint kick-off", "Theo dõi tiến độ", "Risk tracking", "Sprint Review", "Retrospective" |

> ⚠️ **QUY TẮC CỐT LÕI:**
> - **Fix bug** (dù do QC hay UAT phát hiện) → **luôn là `Coding`**, không phải `Testing`
> - **QC test** (dù test feature hay test sau fix) → **luôn là `Testing`**
> - Không nhầm lẫn người thực hiện (DEV fix = Coding, QC verify = Testing)
5. Định dạng ngày tháng: dd/MM/yyyy
#### Output Format (BẮT BUỘC) - 4 bước theo đúng thứ tự

> **Nguyên tắc Cache-First:** JSON data được ghi trực tiếp ra file cache (`$REPORT_OUTPUT_DIR/.tmp/sprint{N}_backlog.json`) bằng `create_file`, sau đó script Python đọc từ cache để validate và export. Không nhúng data vào Python heredoc. **Cache `.json` nằm trong `.tmp/` (ẩn) - KHÔNG bao giờ ghi `.json` ra top-level `$REPORT_OUTPUT_DIR/`.**

---

**Bước 1 - Ghi JSON vào cache bằng `create_file`:**

Dùng `create_file` / Write tool để ghi raw JSON trực tiếp ra `$REPORT_OUTPUT_DIR/.tmp/sprint{N}_backlog.json`. **CẤM Bash `mkdir` / `mkdir -p` / `echo OK` / `ls` cho `.tmp`** - webapp đã tạo sẵn. Ghi file thẳng vào path đó.

Cấu trúc JSON (ghi đúng format, không dùng Python dict syntax):
```json
{
  "project": "...",
  "sprint_number": N,
  "sprint_goal": "Tiếng Việt đầy đủ dấu...",
  "time_box": ["1. Sprint Timeline: ...", "2. Sprint Planning: ...", ...],
  "epics": [
    {
      "epic": "EPIC-1. Tên epic",
      "user_stories": [
        {
          "us_id": "US_1.1",
          "module": "...",
          "description": "...",
          "priority": "3-High",
          "complexity": "2-Medium",
          "story_point": 4,
          "tasks": [
            {
              "pic": "BA",
              "task_name": "...",
              "status": "Not Started",
              "start_date": "dd/MM/yyyy",
              "due_date": "dd/MM/yyyy",
              "est_effort_hour": 8,
              "notes": "",
              "task_complexity": 7,
              "type_of_work": "Do",
              "task_process": "Requirement & Design",
              "task_priority": "High"
            }
          ]
        }
      ]
    }
  ]
}
```

> ⚠️ Ghi trực tiếp tiếng Việt có dấu trong JSON - **không** dùng `\uXXXX` escape. `create_file` hỗ trợ UTF-8 đầy đủ.

---

**Bước 2 - Validate cache và fix encoding bằng `bash_tool`:**

```bash
cd "$SKILL_DIR" && python3 scripts/validate_cache.py "$REPORT_OUTPUT_DIR/.tmp/sprint{N}_backlog.json"
```

Script này tự động:
- Re-save với `ensure_ascii=False` đảm bảo UTF-8
- Kiểm tra task effort > 24h
- Kiểm tra ngày T7/CN
- Kiểm tra task span qua weekend
- Kiểm tra task span qua tháng
- Kiểm tra mọi US có task BA + DEV
- In Manday summary để xác nhận số liệu

Nếu có lỗi → sửa file JSON bằng `str_replace` → chạy lại validate.

---

**Bước 2b - Sort tasks theo start_date, due_date tăng dần:**

> ⚠️ **BẮT BUỘC** chạy sau validate, trước khi copy ra output. Đảm bảo task trong mỗi US được sắp xếp theo thứ tự thời gian, dễ kiểm soát.

```bash
cd "$SKILL_DIR" && python3 -c "
import json, sys, os
from datetime import datetime

path = os.environ['REPORT_OUTPUT_DIR'] + '/.tmp/sprint{N}_backlog.json'
with open(path, encoding='utf-8') as f:
    data = json.load(f)

def sort_key(t):
    sd = t.get('start_date','01/01/2099')
    dd = t.get('due_date','01/01/2099')
    return (datetime.strptime(sd,'%d/%m/%Y'), datetime.strptime(dd,'%d/%m/%Y'))

for epic in data['epics']:
    for us in epic['user_stories']:
        us['tasks'] = sorted(us['tasks'], key=sort_key)

with open(path,'w',encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
print('Tasks sorted by start_date, due_date asc ✅')
"
```

---

**Bước 3 - Tạo Markdown (JSON cache ở lại `.tmp/`, KHÔNG copy ra output):**

> ⛔ **KHÔNG copy `sprint{N}_backlog.json` ra `$REPORT_OUTPUT_DIR/`.** File JSON cache nằm ẩn trong `$REPORT_OUTPUT_DIR/.tmp/` - chỉ `.xlsx` + `.md` mới ra top-level `$REPORT_OUTPUT_DIR/` để share cho user.

> ⛔ **TUYỆT ĐỐI KHÔNG tự ước đoán hay viết tay ngày trong Phase & Milestone Timeline.** Mọi ngày (Start Date, End Date, Target Date) phải được derive trực tiếp từ JSON cache bằng cách chạy bash trước khi viết Markdown:
>
> ```bash
> cd "$SKILL_DIR" && python3 -c "
> import json, os
> from datetime import datetime
> path = os.environ['REPORT_OUTPUT_DIR'] + '/.tmp/sprint{N}_backlog.json'
> with open(path, encoding='utf-8') as f:
>     data = json.load(f)
> # In min/max date theo từng EPIC để map vào Phase
> for epic in data['epics']:
>     dates = [t[k] for us in epic['user_stories'] for t in us['tasks'] for k in ('start_date','due_date') if t.get(k)]
>     parsed = sorted(datetime.strptime(d,'%d/%m/%Y') for d in dates)
>     print(f\"{epic['epic'][:40]}: {parsed[0].strftime('%d/%m/%Y')} -> {parsed[-1].strftime('%d/%m/%Y')}\")
> "
> ```
>
> Dùng kết quả in ra để điền vào bảng Phase & Milestone - không được dùng ngày từ trí nhớ hay suy luận.

Sau đó dùng `create_file` tạo `$REPORT_OUTPUT_DIR/sprint{N}_backlog.md` theo `assets/sprint_backlog_template.md`:
1. Tham chiếu Sprint Backlog Data (ghi chung "file JSON nội bộ", KHÔNG ghi tên file `sprint{N}_backlog.json` - giữ json ẩn)
2. Phase & Milestone Timeline
3. Bảng tổng hợp Manday theo Role + Buffer 10%

> **⛔ KHÔNG tạo section "Chi Tiết Sprint Backlog & Task Breakdown" hay bất kỳ bảng liệt kê từng task (task name / PIC / effort / start-end date / notes) nào trong `.md`.** File `.md` chỉ chứa phần tóm tắt (Tổng quan, Manday summary, Phase/Milestone Timeline, Output Deliverables, Pre-flight Checklist). Chi tiết từng task đã có trong `.json` + `.xlsx` - không lặp lại trong `.md`. Nếu đang định viết bảng task breakdown → dừng lại, bỏ qua.
>
> **⛔ Trong phần "Danh sách Output Deliverables" của `.md` chỉ liệt kê 3 file: `sprint{N}_Project_Plan.xlsx`, `sprint{N}_Sprint_Backlog.xlsx` và `sprint{N}_backlog.md`.** KHÔNG liệt kê `sprint{N}_backlog.json` (file JSON là nội bộ, dùng ẩn làm source of truth, không phải deliverable cho user).

---

**Bước 4 - Export Excel bằng `bash_tool`:**

> ⛔ **TUYỆT ĐỐI KHÔNG tự viết code Python/openpyxl để tạo Excel.** Dù validate lỗi hay bất kỳ lý do nào, CHỈ được dùng đúng các script của skill:
>
> - **Sửa lỗi** → dùng `str_replace` trên file JSON cache → chạy lại `validate_cache.py`
> - **Xuất Excel** → luôn luôn chạy cả 2 script `json_to_excel.py` (Mẫu Project Plan) và `json_to_excel_v2.py` (Mẫu Detailed Sprint Backlog), không thay thế bằng code inline
>
> Script `json_to_excel.py` và `json_to_excel_v2.py` có format riêng (conditional formatting, data validation, merge cells, NETWORKDAYS formula) mà code tự viết không thể tái tạo đúng.

```bash
cd "$REPORT_OUTPUT_DIR/.tmp"
python3 "$SKILL_DIR/scripts/json_to_excel.py" "$REPORT_OUTPUT_DIR/.tmp/sprint{N}_backlog.json" -o "$REPORT_OUTPUT_DIR/.tmp/Sprint_Plan_Raw.xlsx"
python3 "$SKILL_DIR/scripts/json_to_excel_v2.py" "$REPORT_OUTPUT_DIR/.tmp/sprint{N}_backlog.json" -o "$REPORT_OUTPUT_DIR/.tmp/Sprint_Backlog_Raw.xlsx"
cp "$REPORT_OUTPUT_DIR/.tmp/Sprint_Plan_Raw.xlsx" "$REPORT_OUTPUT_DIR/sprint{N}_Project_Plan.xlsx"
cp "$REPORT_OUTPUT_DIR/.tmp/Sprint_Backlog_Raw.xlsx" "$REPORT_OUTPUT_DIR/sprint{N}_Sprint_Backlog.xlsx"
```

Sau đó dùng `present_files` để share **3 file** cho user theo đúng thứ tự:
1. `sprint{N}_Project_Plan.xlsx` (Mẫu Project Plan)
2. `sprint{N}_Sprint_Backlog.xlsx` (Mẫu Detailed Sprint Backlog)
3. `sprint{N}_backlog.md`

> **⛔ KHÔNG share `sprint{N}_backlog.json` cho user.** File JSON là source of truth nội bộ (dùng để validate + export Excel), chỉ tồn tại ẩn trong `$REPORT_OUTPUT_DIR/.tmp/`, không present_files, không liệt kê trong phần "Danh sách Output Deliverables" của `.md`.

---

> **Chỉnh sửa sau khi generate:** Nếu user yêu cầu sửa task/ngày/effort → dùng `str_replace` trên file cache `$REPORT_OUTPUT_DIR/.tmp/sprint{N}_backlog.json` → chạy lại Bước 2–4. Không cần re-generate toàn bộ JSON.
---

## Limitations

- Story Point là ước tính - team review lại trong session planning thực tế.
- Nếu thiếu User Story / Backlog → không thể tạo Sprint Backlog. Dừng và yêu cầu user cung cấp.

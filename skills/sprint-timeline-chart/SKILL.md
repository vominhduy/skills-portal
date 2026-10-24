---
name: sprint-timeline-chart
description: >
  Tạo biểu đồ Timeline Gantt + Resource Pie Chart (phân bổ effort/manday) cho sprint/dự án dưới dạng file HTML tương tác.
  Sử dụng khi user cung cấp thông tin sprint dưới dạng text, markdown, hoặc mô tả (kế hoạch sprint, sprint backlog tổng hợp,
  resource plan, effort breakdown) và muốn xuất ra file HTML dashboard trực quan gồm: Gantt chart các phase, biểu đồ tròn
  phân bổ manday theo role, và danh sách milestone. Trigger ngay khi user nói: tạo timeline, vẽ gantt, thống kê effort,
  phân bổ manday, resource chart, sprint chart, dashboard sprint, tạo biểu đồ sprint, xuất HTML timeline, hoặc gắn
  file/text tổng hợp sprint và nhờ tạo biểu đồ - kể cả khi không dùng đúng từ khóa trên.
---

# Sprint Timeline & Resource Chart Skill

Skill này nhận input dạng text/markdown mô tả sprint, parse thành JSON chuẩn, rồi inject vào HTML template để tạo dashboard trực quan.

## Workflow tổng quát

1. **Parse input** → Trích xuất thông tin từ text/markdown/file đầu vào
2. **Build JSON** → Tạo project JSON theo schema chuẩn
3. **Generate HTML** → Inject JSON vào template, xuất file HTML
4. **Present file** → Trả file cho user

---

## Bước 1: Parse Input

Input có thể là:
- **Text tổng hợp sprint** (mô tả tự do): trích xuất thông tin key
- **Markdown table** (sprint backlog): đọc phases, stories, timeline
- **Danh sách bullet**: tìm dates, roles, effort
- **Kết hợp các format trên**

### Thông tin cần trích xuất:

| Field | Mô tả | Ví dụ |
|-------|-------|-------|
| `projectName` | Tên dự án / sprint | "FCR Sprint 3" |
| `startDate` | Ngày bắt đầu (YYYY-MM-DD) | "2026-04-20" |
| `endDate` | Ngày kết thúc (YYYY-MM-DD) | "2026-05-29" |
| `teamSize` | Tổng số người | 6 |
| `teamComposition` | Mô tả team | "1 PM, 1 BA, 2 DEV, 2 QC" |
| `resources` | Mảng phân bổ MD theo role | xem schema |
| `phases` | Các phase trong sprint | xem schema |
| `milestones` | Các mốc quan trọng | xem schema |

### Quy tắc parse thông minh:

- Nếu chỉ có tổng MD không có breakdown: phân bổ theo tỷ lệ mặc định PM:BA:DEV:QC = 1:1.1:5:1.7
- Nếu không có phases rõ ràng: tạo phases mặc định (Requirement & Planning, Development, Testing, UAT, Go-live)
- Nếu milestones không có status: gán `"notstarted"`, trừ milestone có date ≤ ngày hiện tại → `"done"`
- Dates dạng dd/mm/yyyy hoặc dd-mm-yyyy → convert sang YYYY-MM-DD
- Nếu thiếu thông tin quan trọng: hỏi user trước khi generate

---

## Bước 2: Build JSON

Tạo JSON theo schema sau, **không thêm bất kỳ field nào ngoài schema**:

```json
{
  "projectName": "string",
  "startDate": "YYYY-MM-DD",
  "endDate": "YYYY-MM-DD",
  "teamSize": number,
  "teamComposition": "string",
  "resources": [
    { "role": "PM", "md": number, "color": "#534AB7" },
    { "role": "BA", "md": number, "color": "#1D9E75" },
    { "role": "DEV", "md": number, "color": "#378ADD" },
    { "role": "QC", "md": number, "color": "#EF9F27" }
  ],
  "phases": [
    {
      "label": "string",
      "start": "YYYY-MM-DD",
      "end": "YYYY-MM-DD",
      "color": "hex color"
    }
  ],
  "milestones": [
    {
      "name": "string",
      "date": "YYYY-MM-DD",
      "status": "done|inprogress|notstarted"
    }
  ]
}
```

### Màu chuẩn cho phases:

| Phase | Color |
|-------|-------|
| Requirement & Planning | `#378ADD` |
| Development | `#A78FDD` |
| Testing / QA | `#EF9F27` |
| UAT | `#5B8FF9` |
| Pilot / Go-live | `#639922` |
| Bug Fix | `#E05C5C` |
| Deployment | `#1D9E75` |

### Màu chuẩn cho roles (có thể mở rộng):

| Role | Color |
|------|-------|
| PM | `#534AB7` |
| BA | `#1D9E75` |
| DEV | `#378ADD` |
| QC / QA | `#EF9F27` |
| DevOps | `#E05C5C` |
| Designer | `#F472B6` |

---

## Bước 3: Generate HTML

### Template path (theo thứ tự ưu tiên):
1. `assets/template.html` (relative, cùng thư mục SKILL.md)
2. `/mnt/skills/user/sprint-timeline-chart/assets/template.html` (absolute fallback)

> Nếu cả hai đều không đọc được → báo user, dừng lại.

### Script Python inject JSON:

```python
import json, re, os, sys
# Dùng _shared cạnh skill (webapp/skills/_shared) - không phụ thuộc ~/.claude/skills.
_HERE = os.path.dirname(os.path.abspath(__file__)) if '__file__' in dir() else os.environ.get("SKILL_DIR", ".")
sys.path.insert(0, os.path.join(_HERE, "..", "..", "_shared"))
from output_path import ensure_output_dir, safe_name

template_path = os.path.join(os.environ.get("SKILL_DIR", "/mnt/skills/user/sprint-timeline-chart"), "assets/template.html")
# Sanitize slug - chỉ [a-z0-9-], chống path traversal qua tên dự án.
slug = safe_name(project_json.get("project_slug") or "project").lower()
date = project_json.get("date") or __import__("datetime").date.today().isoformat()
output_path   = f"{ensure_output_dir()}/timeline_{slug}_{date}.html"

with open(template_path, "r", encoding="utf-8") as f:
    html = f.read()

# Escape </script> trong JSON - chống HTML injection đóng tag script sớm.
new_json = json.dumps(project_json, ensure_ascii=False, indent=2).replace("</", "<\\/")
pattern  = r'(<script id="project-data" type="application/json">)(.*?)(</script>)'
new_html = re.sub(pattern, lambda m: f'{m.group(1)}\n{new_json}\n{m.group(3)}', html, flags=re.DOTALL)

with open(output_path, "w", encoding="utf-8") as f:
    f.write(new_html)
```

**Quy tắc output:**
- File output = `template.html` gốc với **duy nhất phần JSON được thay thế** - không thêm, không bớt bất cứ thứ gì khác
- Tên file: `timeline_{project_slug}_{YYYYMMDD}.html`
- Lưu tại: `/mnt/user-data/outputs/`

---

## Bước 4: Present File

Dùng `present_files` tool để trả file HTML cho user. **Không kèm giải thích hay tóm tắt.**

---

## Ví dụ Input → Output

### Input (text tổng hợp):
```
Sprint 3 - Dự án FCR
Thời gian: 20/04/2026 - 29/05/2026
Team: 1 PM, 1 BA, 2 DEV, 2 QC (6 người)

Effort breakdown:
- PM: 9.75 MD
- BA: 10.75 MD  
- DEV: 48.5 MD
- QC: 16 MD

Phases:
- Requirement & Planning: 20/04 - 29/04
- Development: 20/04 - 18/05
- Testing: 15/05 - 22/05
- UAT: 22/05 - 27/05
- Pilot: 27/05 - 29/05

Milestones:
- Sprint Planning Complete: 29/04 (in progress)
- Dev Complete: 18/05 (in progress)
- Sprint Review: 25/05
- Production Deployment: 27/05
- Go-Live: 29/05
```

### Output JSON:
```json
{
  "projectName": "FCR Sprint 3",
  "startDate": "2026-04-20",
  "endDate": "2026-05-29",
  "teamSize": 6,
  "teamComposition": "1 PM, 1 BA, 2 DEV, 2 QC",
  "resources": [
    { "role": "PM", "md": 9.75, "color": "#534AB7" },
    { "role": "BA", "md": 10.75, "color": "#1D9E75" },
    { "role": "DEV", "md": 48.5, "color": "#378ADD" },
    { "role": "QC", "md": 16, "color": "#EF9F27" }
  ],
  "phases": [
    { "label": "Requirement & Planning", "start": "2026-04-20", "end": "2026-04-29", "color": "#378ADD" },
    { "label": "Development", "start": "2026-04-20", "end": "2026-05-18", "color": "#A78FDD" },
    { "label": "Testing", "start": "2026-05-15", "end": "2026-05-22", "color": "#EF9F27" },
    { "label": "UAT", "start": "2026-05-22", "end": "2026-05-27", "color": "#5B8FF9" },
    { "label": "Pilot", "start": "2026-05-27", "end": "2026-05-29", "color": "#639922" }
  ],
  "milestones": [
    { "name": "Sprint Planning Complete", "date": "2026-04-29", "status": "inprogress" },
    { "name": "Dev Complete", "date": "2026-05-18", "status": "inprogress" },
    { "name": "Sprint Review", "date": "2026-05-25", "status": "notstarted" },
    { "name": "Production Deployment", "date": "2026-05-27", "status": "notstarted" },
    { "name": "Go-Live", "date": "2026-05-29", "status": "notstarted" }
  ]
}
```

---

## Lưu ý quan trọng

- **Không hardcode** màu sắc hoặc cấu trúc layout - template đã handle tất cả
- **Validate dates**: đảm bảo tất cả phases/milestones nằm trong khoảng `startDate` → `endDate`
- **MD phải là số thực** (float), không phải string
- Nếu user muốn **update** file đã có: đọc lại JSON hiện tại, merge thay đổi, generate lại
- Nếu input có **nhiều sprint**: tạo file HTML riêng cho mỗi sprint, đặt tên khác nhau

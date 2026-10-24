# Product Backlog - Internal Guide

> **INTERNAL REFERENCE ONLY** - Do not include this content in generated output.  
> Read this file before generating a Product Backlog to understand scoring rules and conventions.

---

## STORY POINT GUIDELINE

### Story Point Formula

> **Story Point = Average of 3 values:**  
> `(Total Story Manday + Priority × 2 + Complexity × 2) / 3`

| Component | Definition |
|---|---|
| **Total Story Manday** | Sum of all task mandays within the User Story |
| **Priority** | Urgency level of the User Story |
| **Complexity** | Technical complexity of the User Story |

### Priority Scale

| Level | Name | Definition |
|---|---|---|
| 4 | Critical | Urgent interrupt requests requiring immediate action (executive directive) |
| 3 | High | Must have - critical functionality that must be delivered in the Sprint |
| 2 | Medium | Should have - important but not urgent; solution is still viable without it |
| 1 | Low | Could have - desired or expected but not essential |

### Complexity Scale

| Level | Name | Definition |
|---|---|---|
| 3 | High | - Involves more than 3 other functions/stories<br>- Requires new/unfamiliar technology<br>- Complex logic or calculations |
| 2 | Medium | - Involves up to 3 other functions/stories<br>- Moderately complex logic or calculations |
| 1 | Low | - Standalone story with no dependencies<br>- Simple business logic |

---

## CAPACITY DEFAULTS

> Áp dụng khi user **không cung cấp** thông tin capacity. Dùng các giá trị này để tính toán, **không hỏi lại**.

| Quy tắc | Giá trị mặc định |
|---|---|
| Giờ làm việc / tuần / member | **40 giờ** (full-time) |
| Giờ làm việc / ngày / member | **8 giờ** |
| Buffer overhead (meeting, review, admin) | **20%** → capacity thực = 40h × 80% = **32h/tuần/member** |
| 1 Manday | **8 giờ** |
| Sprint 2 tuần (10 ngày làm việc) / member | **80h gross → 64h net** |

**Cách tính capacity sprint:**
```
Capacity (h) = số_member × số_ngày_làm_việc × 8h × 80%
Ví dụ: 3 member × 10 ngày × 8h × 80% = 192h net
```

Nếu user cung cấp số ngày/giờ thực tế → ưu tiên dùng số thực tế thay cho mặc định.

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

### STATUS Convention

| Status | Meaning |
|---|---|
| `Not Started` | Work has not begun |
| `In Progress` | Currently being worked on |
| `Done` | Completed |
| `Blocked` | Blocked, requires escalation |
| `Cancelled` | Removed from scope |

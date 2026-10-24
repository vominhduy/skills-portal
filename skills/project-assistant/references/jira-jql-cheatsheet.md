# Jira JQL Cheatsheet

Hướng dẫn cú pháp JQL (Jira Query Language) thông dụng để tra cứu dữ liệu Jira.

## 1. Tìm kiếm theo Dự án & Sprint

```jql
# Tất cả issue trong project
project = "FCR"

# Issue trong sprint hiện tại đang active
project = "FCR" AND sprint in openSprints()

# Issue trong sprint theo tên cụ thể
project = "FCR" AND sprint = "Sprint 24"

# Issue thuộc Backlog (chưa vào sprint nào)
project = "FCR" AND sprint is EMPTY
```

---

## 2. Tìm kiếm theo Người thực hiện (Assignee) & Trạng thái

```jql
# Task được giao cho chính mình chưa hoàn thành
assignee = currentUser() AND statusCategory != Done

# Task được giao cho người khác
assignee = "nguyenvana@fpt.com" AND statusCategory != Done

# Task chưa có người nhận (Unassigned)
project = "FCR" AND assignee is EMPTY

# Task đang trong trạng thái In Progress
project = "FCR" AND status = "In Progress"

# Bug đang mở trong project
project = "FCR" AND issuetype = "Bug" AND statusCategory != Done
```

---

## 3. Tìm kiếm theo Thời gian & Cập nhật

```jql
# Cập nhật trong 7 ngày gần nhất
project = "FCR" AND updated >= -7d ORDER BY updated DESC

# Quá hạn (Overdue)
project = "FCR" AND duedate < now() AND statusCategory != Done

# Tạo mới trong 24 giờ qua
project = "FCR" AND created >= -24h
```

---

## 4. Tìm kiếm theo Text & Ưu tiên

```jql
# Tìm trong Summary / Description
project = "FCR" AND text ~ "login"

# Task có độ ưu tiên cao nhất
project = "FCR" AND priority in (High, Highest) AND statusCategory != Done
```

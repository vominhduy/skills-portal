#!/usr/bin/env bash
# Bash Helper to run skills easily on Linux / macOS / Git Bash

if [ -z "$1" ]; then
    python3 run_skill.py list
    echo ""
    read -p "Nhập tên skill bạn muốn chạy: " skill_name
    if [ -z "$skill_name" ]; then
        exit 0
    fi
    python3 run_skill.py "$skill_name"
else
    python3 run_skill.py "$@"
fi

#!/usr/bin/env python3
"""
SQLite Storage Module for VN Stock Advisor Screener.
Database file is persistently stored in /data/stock_screener.db.
"""

import os
import json
import sqlite3
from datetime import datetime
from typing import Any, Dict, List, Optional

# Workspace root data folder
WORKSPACE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
DATA_DIR = os.path.join(WORKSPACE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "stock_screener.db")


def get_db_connection() -> sqlite3.Connection:
    os.makedirs(DATA_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS screener_presets (
        preset_key TEXT PRIMARY KEY,
        preset_title TEXT,
        latest_trading_date TEXT,
        total_matched INTEGER,
        stocks_json TEXT,
        market_summary_json TEXT,
        updated_at TEXT
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS stock_details (
        ticker TEXT PRIMARY KEY,
        company_name TEXT,
        floor TEXT,
        industry TEXT,
        detail_json TEXT,
        signals_history_json TEXT,
        trade_plan_json TEXT,
        updated_at TEXT
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS screener_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        preset_key TEXT,
        total_matched INTEGER,
        created_at TEXT
    );
    """)

    conn.commit()
    conn.close()


def save_preset_results(
    preset_key: str,
    preset_title: str,
    latest_trading_date: str,
    total_matched: int,
    stocks: List[Dict[str, Any]],
    market_summary: Dict[str, Any]
) -> str:
    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    stocks_json = json.dumps(stocks, ensure_ascii=False)
    summary_json = json.dumps(market_summary, ensure_ascii=False)

    cursor.execute("""
    INSERT INTO screener_presets (
        preset_key, preset_title, latest_trading_date, total_matched,
        stocks_json, market_summary_json, updated_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(preset_key) DO UPDATE SET
        preset_title = excluded.preset_title,
        latest_trading_date = excluded.latest_trading_date,
        total_matched = excluded.total_matched,
        stocks_json = excluded.stocks_json,
        market_summary_json = excluded.market_summary_json,
        updated_at = excluded.updated_at;
    """, (preset_key, preset_title, latest_trading_date, total_matched, stocks_json, summary_json, now_str))

    cursor.execute("""
    INSERT INTO screener_logs (preset_key, total_matched, created_at)
    VALUES (?, ?, ?);
    """, (preset_key, total_matched, now_str))

    conn.commit()
    conn.close()
    return now_str


def get_preset_results(preset_key: str) -> Optional[Dict[str, Any]]:
    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM screener_presets WHERE preset_key = ?", (preset_key,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    try:
        stocks = json.loads(row["stocks_json"])
    except Exception:
        stocks = []

    try:
        market_summary = json.loads(row["market_summary_json"])
    except Exception:
        market_summary = {}

    return {
        "ok": True,
        "is_cached": True,
        "from_sqlite": True,
        "db_path": "data/stock_screener.db",
        "preset": row["preset_key"],
        "preset_title": row["preset_title"],
        "latest_date": row["latest_trading_date"],
        "total_matched": row["total_matched"],
        "stocks": stocks,
        "market_summary": market_summary,
        "updated_at": row["updated_at"]
    }


def save_stock_detail(
    ticker: str,
    company: str,
    floor: str,
    industry: str,
    detail: Dict[str, Any],
    history: List[Dict[str, Any]],
    trade_plan: Dict[str, Any]
) -> str:
    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()

    ticker = ticker.upper()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
    INSERT INTO stock_details (
        ticker, company_name, floor, industry, detail_json,
        signals_history_json, trade_plan_json, updated_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(ticker) DO UPDATE SET
        company_name = excluded.company_name,
        floor = excluded.floor,
        industry = excluded.industry,
        detail_json = excluded.detail_json,
        signals_history_json = excluded.signals_history_json,
        trade_plan_json = excluded.trade_plan_json,
        updated_at = excluded.updated_at;
    """, (
        ticker,
        company,
        floor,
        industry,
        json.dumps(detail, ensure_ascii=False),
        json.dumps(history, ensure_ascii=False),
        json.dumps(trade_plan, ensure_ascii=False),
        now_str
    ))

    conn.commit()
    conn.close()
    return now_str


def get_stock_detail(ticker: str) -> Optional[Dict[str, Any]]:
    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()

    ticker = ticker.upper()
    cursor.execute("SELECT * FROM stock_details WHERE ticker = ?", (ticker,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    try:
        detail = json.loads(row["detail_json"])
    except Exception:
        detail = {}

    try:
        history = json.loads(row["signals_history_json"])
    except Exception:
        history = []

    try:
        trade_plan = json.loads(row["trade_plan_json"])
    except Exception:
        trade_plan = {}

    return {
        "ok": True,
        "is_cached": True,
        "from_sqlite": True,
        "ticker": ticker,
        "company_name": row["company_name"],
        "floor": row["floor"],
        "industry": row["industry"],
        "detail": detail,
        "signals_history": history,
        "trade_plan": trade_plan,
        "updated_at": row["updated_at"]
    }


if __name__ == "__main__":
    init_db()
    print("SQLite DB initialized at:", DB_PATH)

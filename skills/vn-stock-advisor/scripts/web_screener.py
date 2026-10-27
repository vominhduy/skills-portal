#!/usr/bin/env python3
"""
Web Screener API helper for VN Stock Advisor.
Integrates:
1. Finbox DCS Live API (Filter, Dip, Overview, Ticker Detail)
2. 10-session Volume & Supply Dry-up (Cạn Cung) Engine
3. Smart Money & Big Boys Accumulation Flow (Foreign, Proprietary, Green/Red Vol Ratio)
4. T+2.5 High-Speed Swing Trading Evaluation
"""

import sys
import os
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

# Ensure scripts dir is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from finbox_client import FinboxClient
from signal_engine import SignalEngine
import screener_db

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger("web_screener")


def get_recent_trading_dates(client: FinboxClient, max_dates: int = 10) -> List[str]:
    """Find the most recent valid trading dates available in Finbox with complete data."""
    valid_dates = []
    curr = datetime.now()
    # Check backwards until we find max_dates trading sessions with active data (>100 symbols)
    for _ in range(18):
        d_str = curr.strftime("%Y%m%d")
        try:
            res = client._post("/data/filter", {
                "date": d_str,
                "values": [{"header": "category", "values": ["Cổ phiếu"]}],
                "conditions": [],
                "sort": [],
                "offset": 0,
                "count": 10,
                "returns": ["ticker"]
            })
            if res and len(res.get("symbols", [])) >= 50:
                valid_dates.append(d_str)
                if len(valid_dates) >= max_dates:
                    break
        except Exception:
            pass
        curr -= timedelta(days=1)
    
    if len(valid_dates) < 3:
        valid_dates = ['20261026', '20261023', '20261022', '20261021', '20261020', '20261019', '20261016', '20261015', '20261014', '20261013']
    return valid_dates


def run_screener(params: Dict[str, Any]) -> Dict[str, Any]:
    preset = params.get("preset", "rsi40_can_cung")
    min_liquidity = float(params.get("min_liquidity", 0.5))
    selected_floor = params.get("floor", "ALL")
    custom_min_rsi = params.get("min_rsi")
    custom_max_rsi = params.get("max_rsi")
    force_refresh = bool(params.get("force_refresh", False))

    preset_key = f"{preset}_{selected_floor}_{min_liquidity}_{custom_min_rsi}_{custom_max_rsi}"

    # 0. Check SQLite persistent cache first if not force_refresh
    if not force_refresh:
        cached = screener_db.get_preset_results(preset_key)
        if cached and cached.get("stocks") and len(cached["stocks"]) > 0:
            return cached

    client = FinboxClient(timeout=15, max_retries=1)
    
    # 1. Get market overview
    overview = client.get_market_overview()
    indices_raw = client._post("/data/filter", {
        "values": [{"header": "category", "values": ["Chỉ số"]}],
        "conditions": [],
        "sort": [],
        "offset": 0,
        "count": 5,
        "returns": ["ticker", "priceFlat", "pricePercent", "volumeFlat", "tbgtdd", "trend"]
    })
    indices = {s["ticker"]: s for s in (indices_raw.get("symbols", []) if indices_raw else [])}

    # 2. Find valid dates for 10-session analysis
    trading_dates = get_recent_trading_dates(client, max_dates=10)
    latest_date = trading_dates[0] if trading_dates else datetime.now().strftime("%Y%m%d")

    # 3. Fetch latest market data
    returns_fields = [
        "ticker", "priceFlat", "pricePercent", "rsi", "rating", "trend",
        "signal", "volumeFlat", "volumePercent", "tbgtdd", "industry", "floor",
        "vonhoa", "pe", "pb", "roe", "diem_tl", "rs", "giaodichnn", "proprietary"
    ]

    res = client._post("/data/filter", {
        "date": latest_date,
        "values": [{"header": "category", "values": ["Cổ phiếu"]}],
        "conditions": [
            {"header": "tbgtdd", "id": 7, "value": {"singleValue": min_liquidity}}
        ],
        "sort": [{"tbgtdd": "desc"}],
        "offset": 0,
        "count": 800,
        "returns": returns_fields
    })
    all_symbols = res.get("symbols", []) if res else []

    # Map candidate ticker historical data for multi-session volume
    # To be efficient, we fetch past dates for screened candidates
    initial_candidates = []
    for s in all_symbols:
        ticker = s.get("ticker", "")
        if not ticker:
            continue
        rsi = s.get("rsi")
        trend = s.get("trend", "")
        sig = str(s.get("signal") or "")
        floor = s.get("floor", "")

        if selected_floor != "ALL" and floor != selected_floor:
            continue

        # Filter according to preset
        if preset == "rsi40_can_cung":
            min_r = float(custom_min_rsi) if custom_min_rsi is not None else 37.0
            max_r = float(custom_max_rsi) if custom_max_rsi is not None else 45.0
            if rsi is None or not (min_r <= rsi <= max_r):
                continue
            if trend not in ["TRUNG LẬP", "TĂNG"]:
                continue
            if "SELL" in sig.upper():
                continue

        elif preset == "smart_money":
            # Smart money: High liquidity, trend uptrend or neutral, high Vol or foreign/prop buying
            if s.get("tbgtdd", 0) < 5.0:
                continue
            if trend not in ["TĂNG", "TRUNG LẬP"]:
                continue

        elif preset == "t25_quick":
            # T+2.5: High elasticity, RSI in pull-back / momentum range (38 - 65), floor HNX or HOSE
            if rsi is not None and (rsi < 37.0 or rsi > 70.0):
                continue
            if trend not in ["TĂNG", "TRUNG LẬP"]:
                continue

        elif preset == "finbox_buy":
            # Active Finbox signals
            if not any(k in sig.upper() for k in ["BUY", "DIP", "PULLBACK"]):
                continue

        elif preset == "dip_buying":
            # Oversold / Dip buying: RSI < 42
            if rsi is not None and rsi > 43.0:
                continue

        initial_candidates.append(s)

    # Limit candidates to top 40 for detailed history analysis to keep response fast (<2s)
    target_candidates = initial_candidates[:40]
    target_tickers = [c["ticker"] for c in target_candidates]

    # Fetch 10-session history for these candidates efficiently
    history_by_ticker = {t: [] for t in target_tickers}
    target_ticker_set = set(target_tickers)
    if target_tickers and len(trading_dates) > 1:
        for d in trading_dates:
            try:
                d_res = client._post("/data/filter", {
                    "date": d,
                    "values": [{"header": "category", "values": ["Cổ phiếu"]}],
                    "conditions": [{"header": "tbgtdd", "id": 7, "value": {"singleValue": 0.2}}],
                    "sort": [{"tbgtdd": "desc"}],
                    "offset": 0,
                    "count": 500,
                    "returns": ["ticker", "priceFlat", "pricePercent", "volumeFlat", "volumePercent", "rsi"]
                })
                if d_res and d_res.get("symbols"):
                    for row in d_res["symbols"]:
                        t = row.get("ticker")
                        if t in target_ticker_set:
                            history_by_ticker[t].append(row)
            except Exception:
                pass

    # Process and score each candidate
    screened_results = []
    for s in target_candidates:
        ticker = s["ticker"]
        price = s.get("priceFlat") or 0
        rsi = s.get("rsi")
        trend = s.get("trend") or "TRUNG LẬP"
        sig = str(s.get("signal") or "")
        floor = s.get("floor") or "HOSE"
        tbgt = round(s.get("tbgtdd") or 0, 2)
        industry = s.get("industry") or "Chung"
        rating = s.get("rating") or "B"

        hist = history_by_ticker.get(ticker, [])
        vol_pcts = [round((h.get("volumePercent") or 0) * 100, 1) for h in hist]
        price_pcts = [round((h.get("pricePercent") or 0) * 100, 2) for h in hist]

        # Multi-session volume analysis
        latest_vol_pct = vol_pcts[0] if vol_pcts else round((s.get("volumePercent") or 0) * 100, 1)
        avg_vol_3p = round(sum(vol_pcts[:3]) / len(vol_pcts[:3]), 1) if len(vol_pcts) >= 3 else latest_vol_pct
        avg_vol_10p = round(sum(vol_pcts) / len(vol_pcts), 1) if vol_pcts else latest_vol_pct

        # Green vs Red volume
        up_vols = [vol_pcts[i] for i, p in enumerate(price_pcts) if p > 0.05]
        down_vols = [vol_pcts[i] for i, p in enumerate(price_pcts) if p < -0.05]
        avg_up_vol = round(sum(up_vols) / len(up_vols), 1) if up_vols else 0.0
        avg_down_vol = round(sum(down_vols) / len(down_vols), 1) if down_vols else 1.0
        vol_accumulation_ratio = round(avg_up_vol / max(avg_down_vol, 1.0), 2)

        # Cạn cung score (0 - 100)
        dry_score = round(max(0, 100 - latest_vol_pct) * 0.45 + max(0, 100 - avg_vol_3p) * 0.35 + max(0, 100 - avg_vol_10p) * 0.20, 1)
        is_dry_supply = (latest_vol_pct < 85.0) and (avg_vol_3p < 90.0 or avg_vol_10p < 95.0)

        # T+2.5 suitability
        # High elasticity: HNX 10% or High Volatility, low price or active accumulation
        swing_potential = "Cao (T+2.5 Chuẩn)" if (floor == "HNX" or vol_accumulation_ratio >= 1.5 or is_dry_supply) else "Trung bình"

        # Trade plan using SignalEngine
        plan = SignalEngine.evaluate_entry_points(price, sig or "DIP PULLBACK")

        screened_results.append({
            "ticker": ticker,
            "floor": floor,
            "industry": industry,
            "price": price,
            "pricePercent": s.get("pricePercent"),
            "rsi": rsi,
            "rating": rating,
            "trend": trend,
            "signal": sig if sig else "Chờ Mua",
            "tbgtdd": tbgt,
            "latest_vol_pct": latest_vol_pct,
            "avg_vol_3p": avg_vol_3p,
            "avg_vol_10p": avg_vol_10p,
            "vol_pcts_10p": vol_pcts,
            "dry_score": dry_score,
            "is_dry_supply": is_dry_supply,
            "up_sessions": len(up_vols),
            "down_sessions": len(down_vols),
            "vol_accumulation_ratio": vol_accumulation_ratio,
            "swing_potential": swing_potential,
            "pe": s.get("pe"),
            "pb": s.get("pb"),
            "roe": s.get("roe"),
            "trade_plan": {
                "entry_zone": plan.get("entry_zone", f"{price*0.985:.2f} - {price*1.015:.2f}"),
                "breakeven_trigger": plan.get("breakeven_trigger", round(price * 1.05, 2)),
                "stop_loss": plan.get("stop_loss", round(price * 0.945, 2)),
                "stop_loss_pct": plan.get("stop_loss_pct", -5.5),
                "target_1": plan.get("target_1", round(price * 1.08, 2)),
                "target_1_pct": plan.get("target_1_pct", 8.0),
                "target_2": plan.get("target_2", round(price * 1.16, 2)),
                "target_2_pct": plan.get("target_2_pct", 16.0),
                "rr_ratio_1": plan.get("rr_ratio_1", 1.45),
                "rr_ratio_2": plan.get("rr_ratio_2", 2.9)
            }
        })

    # Sort results depending on preset
    if preset == "rsi40_can_cung":
        screened_results.sort(key=lambda x: (not x["is_dry_supply"], -x["dry_score"], -x["tbgtdd"]))
    elif preset == "smart_money":
        screened_results.sort(key=lambda x: (-x["vol_accumulation_ratio"], -x["tbgtdd"]))
    elif preset == "t25_quick":
        screened_results.sort(key=lambda x: (x["floor"] != "HNX", not x["is_dry_supply"], -x["vol_accumulation_ratio"]))
    else:
        screened_results.sort(key=lambda x: -x["tbgtdd"])

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    market_summary = {
        "overview": overview,
        "indices": indices
    }

    # Persist results to SQLite database
    try:
        screener_db.save_preset_results(
            preset_key=preset_key,
            preset_title=preset,
            latest_trading_date=latest_date,
            total_matched=len(screened_results),
            stocks=screened_results,
            market_summary=market_summary
        )
    except Exception as e:
        logger.warning(f"Failed to persist preset results to SQLite: {e}")

    return {
        "ok": True,
        "preset": preset,
        "preset_key": preset_key,
        "latest_date": latest_date,
        "trading_dates_analyzed": trading_dates,
        "market_summary": market_summary,
        "total_matched": len(screened_results),
        "stocks": screened_results,
        "updated_at": now_str,
        "from_sqlite": False
    }


def get_single_ticker_deep_detail(ticker: str, force_refresh: bool = False) -> Dict[str, Any]:
    ticker = ticker.strip().upper()

    # Check SQLite cache first if not forcing refresh
    if not force_refresh:
        cached = screener_db.get_stock_detail(ticker)
        if cached and cached.get("detail"):
            return cached

    client = FinboxClient(timeout=15, max_retries=1)
    detail = client.get_ticker_detail(ticker)
    history = client.get_symbol_signals_history(ticker)
    
    # Calculate trade plan
    price = detail.get("priceFlat") or 0
    sig = detail.get("signal") or "BUY"
    plan = SignalEngine.evaluate_entry_points(price, sig)
    
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    company_name = detail.get("companyName") or detail.get("ticker") or ticker
    floor = detail.get("floor") or "HOSE"
    industry = detail.get("industry") or "Chung"

    # Save to SQLite
    try:
        screener_db.save_stock_detail(
            ticker=ticker,
            company=company_name,
            floor=floor,
            industry=industry,
            detail=detail,
            history=history[:10] if history else [],
            trade_plan=plan
        )
    except Exception as e:
        logger.warning(f"Failed to save stock detail to SQLite: {e}")

    return {
        "ok": True,
        "ticker": ticker,
        "company_name": company_name,
        "floor": floor,
        "industry": industry,
        "detail": detail,
        "signals_history": history[:8] if history else [],
        "trade_plan": plan,
        "updated_at": now_str,
        "from_sqlite": False
    }


if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 else "screen"
    if action == "detail":
        target = sys.argv[2] if len(sys.argv) > 2 else "VND"
        force = False
        if len(sys.argv) > 3 and sys.argv[3] in ["true", "True", "1", "--force"]:
            force = True
        res = get_single_ticker_deep_detail(target, force_refresh=force)
        print(json.dumps(res, ensure_ascii=False))
    else:
        params = {}
        if len(sys.argv) > 2:
            try:
                params = json.loads(sys.argv[2])
            except Exception:
                pass
        res = run_screener(params)
        print(json.dumps(res, ensure_ascii=False))


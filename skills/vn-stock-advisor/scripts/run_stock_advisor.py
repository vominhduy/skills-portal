#!/usr/bin/env python3
"""
Main Execution Script for VN Stock Market Advisor Skill (4-Pillar Pro Edition).
Combines:
1. Macro & Intermarket + Real-time Financial News (MacroClient)
2. Simplize.vn Fundamental Valuation, Fair Value, Margin of Safety & Financial Health
3. TopInvest.vn Smart Money ("Follow the Bigboys"), Crowd Sentiment & Sector Rotation
4. Finbox DCS Real-time Technical Signals + 4-Layer High-Conviction Confluence Engine (0-100 pts)
Prints structured Markdown analysis directly to stdout for chat synthesis (no .md file generated).
"""

import argparse
import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from finbox_client import FinboxClient
from macro_client import MacroClient
from portfolio_tracker import PortfolioTracker
from signal_engine import SignalEngine

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("vn_stock_advisor")


def format_currency(val: Optional[float]) -> str:
    if val is None:
        return "N/A"
    return f"{val:,.2f}"


def generate_markdown_report(
    overview: Dict[str, Any],
    indices: Dict[str, Any],
    confluence_picks: List[Dict[str, Any]],
    smart_money_radar: Dict[str, List[Dict[str, Any]]],
    market_regime: Dict[str, Any],
    sector_rankings: List[Dict[str, Any]],
    sector_benchmarks: Dict[str, Dict[str, float]],
    daily_signals: Dict[str, List[Dict[str, Any]]],
    macro_data: Optional[Dict[str, Any]] = None,
    portfolio_eval: Optional[Dict[str, Any]] = None,
    ticker_detail: Optional[Dict[str, Any]] = None,
    ticker_history: Optional[List[Dict[str, Any]]] = None,
    target_symbol: Optional[str] = None,
    nl_query_result: Optional[Dict[str, Any]] = None,
    dip_stocks: Optional[List[Dict[str, Any]]] = None,
    trading_box_recs: Optional[List[Dict[str, Any]]] = None,
    target_symbol_row: Optional[Dict[str, Any]] = None,
) -> str:
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = []

    lines.append("# 📈 BÁO CÁO PHÂN TÍCH ĐA TẦNG CHỨNG KHOÁN VIỆT NAM (4-PILLAR PRO)")
    lines.append(f"> **Thời điểm cập nhật**: `{now_str}` | **Hệ thống Phân tích**: `Vĩ mô Liên thị trường + Định giá Simplize + Dòng tiền Big Boys TopInvest + Tín hiệu Finbox`")
    lines.append("")

    # =========================================================================
    # 1. PHÂN TÍCH VĨ MÔ LIÊN THỊ TRƯỜNG & TIN TỨC KINH TẾ
    # =========================================================================
    if macro_data:
        intermarket = macro_data.get("intermarket", [])
        synthesis = macro_data.get("synthesis", {})
        news_data = macro_data.get("news", {})

        lines.append("## 1. 🌍 Toàn Cảnh Vĩ Mô Liên Thị Trường & Tin Tức Kinh Tế")
        lines.append(f"- **Trạng thái Vĩ mô Tổng hợp**: **{synthesis.get('macro_regime', 'N/A')}** *(Điểm thuận lợi Vĩ mô: `{synthesis.get('macro_score', 50)}/100`)*")
        favored_secs = synthesis.get("favored_sectors", [])
        if favored_secs:
            lines.append(f"- **Nhóm ngành hưởng lợi vĩ mô**: `{', '.join(favored_secs)}`")
        for drv in synthesis.get("drivers", []):
            lines.append(f"  - 💡 {drv}")
        lines.append("")

        if intermarket:
            lines.append("### 📊 Bảng Chỉ Số Liên Thị Trường Quốc Tế & Tiền Tệ (Real-time)")
            lines.append("| Chỉ số Liên thị trường | Nhóm | Giá trị hiện tại | Biến động | Đánh giá Tác động tới TTCK Việt Nam |")
            lines.append("| :--- | :--- | :---: | :---: | :--- |")
            for item in intermarket:
                chg_pct = item.get("change_pct", 0.0)
                icon = "🟢" if chg_pct > 0 else ("🔴" if chg_pct < 0 else "🟡")
                lines.append(
                    f"| **{item['name']}** | {item['category']} | `{item['price']:,.2f}` {item['unit']} | {icon} `{chg_pct:+.2f}%` | {item.get('impact_note', '')} |"
                )
            lines.append("")

        macro_headlines = news_data.get("macro_headlines", [])
        if macro_headlines:
            lines.append("### 📰 Điểm Tin Vĩ Mô & Thị Trường Tài Chính Nổi Bật")
            for h in macro_headlines[:5]:
                pub_info = f" *({h['source']} - {h['published']})*" if h.get("published") else f" *({h.get('source', '')})*"
                lines.append(f"- [{h.get('sentiment', '⚪')}] **{h.get('title', '')}**{pub_info}")
            lines.append("")

    # =========================================================================
    # 2. TỔNG QUAN THỊ TRƯỜNG, TÂM LÝ ĐÁM ĐÔNG (TOPINVEST) & CHU KỲ ĐỊNH GIÁ (SIMPLIZE)
    # =========================================================================
    lines.append("## 2. 🧭 Tổng Quan Thị Trường, Tâm Lý Đám Đông & Chu Kỳ Định Giá")

    pos_pct = overview.get("pos_pct", 0)
    neu_pct = overview.get("neu_pct", 0)
    neg_pct = overview.get("neg_pct", 0)
    ratio = overview.get("ratio", 0)
    foreign_buy = overview.get("foreign_buy", 0)
    foreign_sell = overview.get("foreign_sell", 0)
    foreign_net = overview.get("foreign_net", 0)

    lines.append("### 🏛️ Bảng Chỉ Số Các Sàn & Độ Rộng Dòng Tiền")
    if indices:
        lines.append("| Chỉ số | Điểm số | Thay đổi | % Thay đổi | Khối lượng | Giá trị (Tỷ VNĐ) | Xếp hạng | Xu hướng |")
        lines.append("| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |")
        for idx_name in ["VNINDEX", "VN30", "HNX", "UPCOM"]:
            idx = indices.get(idx_name)
            if idx:
                p = idx.get("price", 0)
                chg = idx.get("change", 0)
                pct = idx.get("change_pct", 0)
                vol = idx.get("volume", 0)
                val = idx.get("value", 0)
                rt = idx.get("rating", "N/A")
                sig = idx.get("signal", "N/A")
                trend_icon = "🟢" if pct > 0 else ("🔴" if pct < 0 else "🟡")
                lines.append(f"| **{idx_name}** | **{p:,.2f}** | {chg:+.2f} | {trend_icon} `{pct:+.2f}%` | {int(vol):,} | {val:,.1f} | **{rt}** | `{sig}` |")
        lines.append("")

    net_str = f"Mua ròng `+{foreign_net:,.2f}` tỷ VNĐ 🟢" if foreign_net >= 0 else f"Bán ròng `{foreign_net:,.2f}` tỷ VNĐ 🔴"
    lines.append(f"- **Độ rộng thị trường**: 🟢 Tăng `{pos_pct}%` | 🟡 Tham chiếu `{neu_pct}%` | 🔴 Giảm `{neg_pct}%` | **Tỷ lệ lệnh Mua/Bán Finbox**: `{ratio:.2f}`")
    lines.append(f"- **Giao dịch Khối ngoại**: {net_str} *(Mua: `{foreign_buy:,.1f}` tỷ - Bán: `{foreign_sell:,.1f}` tỷ)*")
    lines.append("")

    if market_regime:
        lines.append("### 🧠 Chỉ Số Tâm Lý Đám Đông (TopInvest Crowd Sentiment) & Định Giá Thị Trường (Simplize Cycle)")
        lines.append(f"- **Chỉ số Tâm lý Đám đông (Fear & Greed)**: **`{market_regime['crowd_score']}/100`** $\\rightarrow$ **{market_regime['crowd_state']}**")
        lines.append(f"- **Độ phủ Xu hướng Tăng (Uptrend Breadth)**: `{market_regime['uptrend_pct']}%` cổ phiếu có thanh khoản giữ cấu trúc Tăng (`{market_regime['vol_surge_up_count']}` mã nổ Vol tăng vs `{market_regime['vol_surge_down_count']}` mã nổ Vol giảm)")
        lines.append(f"- **Định giá Trung vị Toàn Thị Trường (Simplize Market Valuation)**: `P/E = {market_regime['market_pe']}x` | `P/B = {market_regime['market_pb']}x` | `ROE = {market_regime['market_roe']}%` $\\rightarrow$ **{market_regime['valuation_zone']}**")
        lines.append(f"- **Khuyến nghị Phân bổ Tỷ trọng Vốn**: **{market_regime['recommended_allocation']}**")
        lines.append(f"- **Hành động Chiến lược**: *{market_regime['action_advice']}*")
        lines.append("")

    # =========================================================================
    # 3. RADAR LUÂN CHUYỂN DÒNG TIỀN NGÀNH (SECTOR MONEY FLOW ROTATION)
    # =========================================================================
    if sector_rankings:
        lines.append("## 3. 🔄 Radar Luân Chuyển Dòng Tiền Ngành & Định Giá Ngành (TopInvest x Simplize)")
        lines.append("| Hạng | Nhóm Ngành | Điểm Dòng Tiền | Trạng Thái Sóng Ngành | % Giá TB | % Vol (20N) | % Mã Tăng | P/E Ngành | P/B Ngành | ROE Ngành | Cổ Phiếu Dẫn Dắt |")
        lines.append("| :---: | :--- | :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |")
        for i, sec in enumerate(sector_rankings[:8], 1):
            lines.append(
                f"| {i} | **{sec['industry']}** | **`{sec['flow_score']}/100`** | {sec['flow_status']} | `{sec['avg_price_pct']:+.2f}%` | `{sec['avg_vol_pct']:.0f}%` | `{sec['up_ratio']:.0f}%` | {sec['median_pe']:.1f}x | {sec['median_pb']:.2f}x | {sec['median_roe']:.1f}% | **{sec['leaders']}** |"
            )
        lines.append("")

    # =========================================================================
    # 4. PHÂN TÍCH CHUYÊN SÂU 360° MÃ CỔ PHIẾU CỤ THỂ (NẾU CÓ --ticker)
    # =========================================================================
    if target_symbol and ticker_detail:
        d_data = ticker_detail.get("data", ticker_detail) if isinstance(ticker_detail, dict) else {}
        sym_price = float(d_data.get("close", 0) or (target_symbol_row or {}).get("priceFlat", 0) or 0)
        sym_change_pct = float(d_data.get("changePercent", 0) or (target_symbol_row or {}).get("pricePercent", 0) or 0)
        sym_rating = d_data.get("rating") or (target_symbol_row or {}).get("rating") or "N/A"
        sym_signal = d_data.get("signal") or (target_symbol_row or {}).get("signal") or "NONE"
        sym_industry = (target_symbol_row or {}).get("industry") or d_data.get("industry") or "Khác"

        # Ghép thông tin từ bảng filter và detail để chấm điểm Hội tụ 4 lớp chính xác nhất
        merged_stock = dict(target_symbol_row or {})
        merged_stock.setdefault("ticker", target_symbol)
        merged_stock["priceFlat"] = sym_price
        merged_stock["pricePercent"] = sym_change_pct
        merged_stock["rating"] = sym_rating
        merged_stock["signal"] = sym_signal
        merged_stock["industry"] = sym_industry

        leading_sector_names = [s["industry"] for s in sector_rankings[:6]] if sector_rankings else []
        conf = SignalEngine.calculate_confluence_score(
            merged_stock,
            sector_benchmarks=sector_benchmarks,
            leading_sectors=leading_sector_names,
            detail_data=ticker_detail
        )
        sm = conf["smart_money"]
        simp = conf["simplize"]
        bd = conf["breakdown"]

        lines.append(f"## 4. 🎯 Phân Tích Chuyên Sâu 360° Cổ Phiếu: `{target_symbol}` ({sym_industry})")
        lines.append(f"### 🏆 Điểm Siêu Hội Tụ 4 Lớp (Confluence Score): **`{conf['confluence_score']}/100`** — {conf['conviction_tier']}")
        lines.append(f"- **Khuyến nghị Hành động**: **{conf['action_verdict']}**")
        lines.append(
            f"- **Cấu trúc Điểm Hội Tụ**: Kỹ thuật Finbox `{bd['ta_finbox']}` | "
            f"Dòng tiền Big Boys `{bd['smart_money_topinvest']}` | "
            f"Định giá & Cơ bản Simplize `{bd['fundamental_simplize']}` | "
            f"Sóng Ngành & Vĩ mô `{bd['sector_macro']}`"
        )
        lines.append("")

        lines.append("### 🐳 A. Bóc Tách Dấu Chân Dòng Tiền Lớn (TopInvest 'Follow the Bigboys')")
        lines.append(f"- **Trạng thái Dòng tiền Tổ chức**: **{sm['label']}**")
        lines.append(f"- **Phân tích Hành vi Giá - Khối lượng**: {sm['note']}")
        lines.append(f"- **Xếp hạng Sức mạnh Giá (Finbox Rating)**: **`{sym_rating}`** | **Tín hiệu kỹ thuật**: `{sym_signal}`")
        lines.append("")

        lines.append("### ❄️ B. Định Giá Giá Trị Thực & Sức Khỏe Tài Chính 5 Trụ Cột (Simplize Snowflake)")
        lines.append(f"- **Giá thị trường hiện tại**: **`{sym_price:,.2f}`** ({sym_change_pct:+.2f}%)")
        lines.append(f"- **Giá trị hợp lý tham chiếu (Fair Value)**: **`{simp['fair_value']:,.2f}`** $\\rightarrow$ **{simp['valuation_label']}**")
        lines.append("| Chỉ số Cơ bản | Giá trị Cổ phiếu | Trung vị Ngành | Đánh giá Chuẩn Simplize |")
        lines.append("| :--- | :---: | :---: | :--- |")
        pe_cmp = "Rẻ hơn ngành 🟢" if (0 < simp["pe"] < simp["sector_pe"]) else ("Cao hơn ngành 🟡" if simp["pe"] > simp["sector_pe"] else "N/A")
        pb_cmp = "Hợp lý 🟢" if (0 < simp["pb"] <= simp["sector_pb"] * 1.15) else "Cao hơn trung vị ngành 🟡"
        roe_cmp = "Sinh lời xuất sắc 🔥" if simp["roe"] >= 18 else ("Hiệu quả tốt 🟢" if simp["roe"] >= 12 else "Hiệu quả thấp 🔴")
        lines.append(f"| **P/E (Hệ số Giá/Thu nhập)** | `{simp['pe']}x` | `{simp['sector_pe']}x` | {pe_cmp} |")
        lines.append(f"| **P/B (Hệ số Giá/Sổ sách)** | `{simp['pb']}x` | `{simp['sector_pb']}x` | {pb_cmp} |")
        lines.append(f"| **ROE (Tỷ suất sinh lời/VCSH)** | `{simp['roe']}%` | `{sector_benchmarks.get(sym_industry, {}).get('roe', 13.0)}%` | {roe_cmp} |")
        lines.append(f"| **EPS (Thu nhập mỗi CP)** | `{simp['eps']:,.0f}` VNĐ | - | {'Tích cực 🟢' if simp['eps'] >= 1500 else 'Cần cải thiện 🟡'} |")
        lines.append(f"| **Đòn bẩy Nợ / VCSH** | `{simp['no_vcsh']}x` | - | {'An toàn 🟢' if simp['no_vcsh'] <= 1.5 else 'Đòn bẩy cao ⚠️'} |")
        lines.append(f"| **Tăng trưởng DT / LN Quý gần nhất** | `DT: {simp['rev_growth']:+.1f}%` | `LN: {simp['profit_growth']:+.1f}%` | {'Tăng trưởng mạnh 🔥' if simp['profit_growth'] > 15 else 'Ổn định'} |")
        lines.append("")

        if simp["warnings"]:
            lines.append("- **⚠️ Cảnh báo Rủi ro Tài chính (Simplize Red Flags)**:")
            for w in simp["warnings"]:
                lines.append(f"  - 🔸 {w}")
            lines.append("")

        plan = SignalEngine.evaluate_entry_points(sym_price, str(sym_signal))
        if plan:
            lines.append("### 🎯 C. Kế Hoạch Giao Dịch & Quản Trị Rủi Ro Chủ Động 3 Nấc (100% Kỷ Luật)")
            lines.append(f"- **Vùng Mua Khuyến Nghị (Entry Zone)**: **`{plan['entry_zone']}`** *(Chia làm 2 lần giải ngân: 50% tại nền giá, 50% khi xác nhận dòng tiền)*")
            lines.append(f"- **🛡️ Điểm Kích Hoạt Chặn Hòa Vốn (+5% Breakeven Trigger)**: **`{plan['breakeven_trigger']}`** *(Ngay khi giá chạm `{plan['breakeven_trigger']}`, tự động nâng Stop Loss về Giá mua để đảm bảo thương vụ **100% bất bại / không thể lỗ**)*")
            lines.append(f"- **🛑 Điểm Cắt Lỗ Tuyệt Đối (Stop Loss)**: **`{plan['stop_loss']}`** (`{plan['stop_loss_pct']}%`)")
            lines.append(f"- **💰 Mục tiêu Chốt lời 1 (Target 1 - Chốt 50% vị thế)**: **`{plan['target_1']}`** (`+{plan['target_1_pct']}%` | R:R = `{plan['rr_ratio_1']}:1`)")
            lines.append(f"- **🚀 Mục tiêu Chốt lời 2 (Target 2 - Gồng lãi theo sóng)**: **`{plan['target_2']}`** (`+{plan['target_2_pct']}%` | R:R = `{plan['rr_ratio_2']}:1`)")
            lines.append("")

        # Tin tức riêng của mã cổ phiếu (nếu có)
        if macro_data and macro_data.get("news", {}).get("specific_headlines"):
            spec_news = macro_data["news"]["specific_headlines"]
            lines.append(f"### 🗞️ D. Tin Tức & Sự Kiện Doanh Nghiệp Mới Nhất Về `{target_symbol}`")
            for hn in spec_news:
                lines.append(f"- [{hn.get('sentiment', '⚪')}] **{hn.get('title', '')}** *({hn.get('source', '')} - {hn.get('published', '')})*")
            lines.append("")

        if ticker_history:
            lines.append(f"### 📜 E. Lịch Sử Tín Hiệu Giao Dịch Finbox Của `{target_symbol}`")
            lines.append("| Ngày Tín Hiệu | Hành Động | Giá Khuyến Nghị | Lợi Nhuận Ghi Nhận (%) |")
            lines.append("| :---: | :---: | :---: | :---: |")
            for h in ticker_history[:6]:
                dt = str(h.get("date", "N/A"))[:10]
                act = h.get("action") or h.get("signal") or "BUY"
                pr = h.get("price") or h.get("buyPrice") or 0
                pf = h.get("profit") or h.get("profitPercent") or 0
                lines.append(f"| {dt} | `{act}` | {pr} | `{pf}%` |")
            lines.append("")

    # =========================================================================
    # 5. KẾT QUẢ TRUY VẤN NGÔN NGỮ TỰ NHIÊN / BẮT ĐÁY (NẾU CÓ)
    # =========================================================================
    if nl_query_result:
        q_text = nl_query_result.get("query", "")
        ep = nl_query_result.get("endpoint", "/data/filter")
        q_stocks = nl_query_result.get("results", [])
        lines.append(f"## 5. 🔍 Kết Quả Sàng Lọc Theo Yêu Cầu: *\"{q_text}\"*")
        lines.append(f"- **Endpoint sử dụng**: `{ep}` | **Số lượng mã thỏa mãn**: `{len(q_stocks)}` mã")
        lines.append("")
        if q_stocks:
            if ep == "/data/dip":
                lines.append("| Mã CP | Sàn | Ngành | Giá | % Thay Đổi | Rating | Tín Hiệu Đáy | Giá Đáy | RSI Hiện Tại | Chiết Khấu 20N | Thanh Khoản (Tỷ) |")
                lines.append("| :--- | :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |")
                for s in q_stocks[:20]:
                    tk = s.get("ticker", "")
                    fl = s.get("floor", "")
                    ind = s.get("industry", "")
                    pr = SignalEngine._safe_float(s.get("priceFlat", 0))
                    pct = SignalEngine._safe_float(s.get("pricePercent", 0))
                    rt = s.get("rating", "N/A")
                    dsig = s.get("dip_signal", "N/A")
                    dpr = SignalEngine._safe_float(s.get("dip_price", 0))
                    rsi = SignalEngine._safe_float(s.get("rsi", 0))
                    d20 = SignalEngine._safe_float(s.get("discount_20", 0))
                    liq = SignalEngine._safe_float(s.get("tbgtdd", 0))
                    lines.append(f"| **{tk}** | {fl} | {ind} | {pr:,.2f} | `{pct:+.2f}%` | **{rt}** | `{dsig}` | {dpr:,.2f} | {rsi:.1f} | `{d20:.1f}%` | {liq:.1f} |")
            else:
                leading_sector_names = [s["industry"] for s in sector_rankings[:6]] if sector_rankings else []
                lines.append("| Mã CP | Sàn | Ngành | Giá | % Giá | Điểm Hội Tụ | Dấu Chân Big Boys | Định Giá Simplize | Vùng Mua | Chặn Hòa Vốn (+5%) | Cắt Lỗ | Target 1 -> 2 |")
                lines.append("| :--- | :---: | :--- | :---: | :---: | :---: | :--- | :--- | :---: | :---: | :---: | :---: |")
                for s in q_stocks[:20]:
                    tk = s.get("ticker", "")
                    fl = s.get("floor", "")
                    ind = s.get("industry", "")
                    pr = SignalEngine._safe_float(s.get("priceFlat", 0))
                    pct = SignalEngine._safe_float(s.get("pricePercent", 0))
                    sig = s.get("signal") or s.get("dip_signal") or "TÍCH LŨY"
                    conf = SignalEngine.calculate_confluence_score(s, sector_benchmarks, leading_sector_names)
                    tp = SignalEngine.evaluate_entry_points(pr, str(sig))
                    lines.append(
                        f"| **{tk}** | {fl} | {ind} | {pr:,.2f} | `{pct:+.2f}%` | **`{conf['confluence_score']}/100`** | "
                        f"{conf['smart_money']['label']} | {conf['simplize']['valuation_label']} | "
                        f"`{tp.get('entry_zone', 'N/A')}` | `{tp.get('breakeven_trigger', 'N/A')}` | "
                        f"`{tp.get('stop_loss', 'N/A')}` | `{tp.get('target_1', 'N/A')}` -> `{tp.get('target_2', 'N/A')}` |"
                    )
            lines.append("")
        else:
            lines.append("*Không tìm thấy cổ phiếu nào thỏa mãn đồng thời tất cả các điều kiện lọc khắt khe trên.*")
            lines.append("")

    if dip_stocks and not nl_query_result:
        lines.append("## 5. 🛟 Danh Sách Cổ Phiếu Tín Hiệu Bắt Đáy (Dip Buying `/data/dip`)")
        lines.append("| Mã CP | Sàn | Ngành | Giá Hiện Tại | % Hôm Nay | Rating | Tín Hiệu Đáy | Giá Đáy | RSI Đáy -> Hiện Tại | Chiết Khấu 20N / 60N | Thanh Khoản (Tỷ) |")
        lines.append("| :--- | :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |")
        for s in dip_stocks[:15]:
            tk = s.get("ticker", "")
            fl = s.get("floor", "")
            ind = s.get("industry", "")
            pr = SignalEngine._safe_float(s.get("priceFlat", 0))
            pct = SignalEngine._safe_float(s.get("pricePercent", 0))
            rt = s.get("rating", "N/A")
            dsig = s.get("dip_signal", "N/A")
            dpr = SignalEngine._safe_float(s.get("dip_price", 0))
            lrsi = SignalEngine._safe_float(s.get("low_rsi", 0))
            rsi = SignalEngine._safe_float(s.get("rsi", 0))
            d20 = SignalEngine._safe_float(s.get("discount_20", 0))
            d60 = SignalEngine._safe_float(s.get("discount_60", 0))
            liq = SignalEngine._safe_float(s.get("tbgtdd", 0))
            lines.append(f"| **{tk}** | {fl} | {ind} | {pr:,.2f} | `{pct:+.2f}%` | **{rt}** | `{dsig}` | {dpr:,.2f} | {lrsi:.1f} -> **{rsi:.1f}** | `{d20:.1f}%` / `{d60:.1f}%` | {liq:.1f} |")
        lines.append("")

    # =========================================================================
    # 6. BẢNG XẾP HẠNG CỔ PHIẾU "SIÊU HỘI TỤ 4 LỚP" (HIGH-CONVICTION TOP PICKS)
    # =========================================================================
    if confluence_picks:
        lines.append("## 6. 🏆 Bảng Xếp Hạng Cổ Phiếu 'Siêu Hội Tụ 4 Lớp' (Mua Chuẩn Xác Suất Thắng Cao Nhất)")
        lines.append("> *Chọn lọc khắt khe các mã hội tụ đủ 4 yếu tố: **Xếp hạng Kỹ thuật Finbox cao + Cá mập Big Boys đang gom (TopInvest) + Định giá có biên an toàn & ROE tốt (Simplize) + Thuộc nhóm Ngành dẫn dắt**.*")
        lines.append("")
        lines.append("| Hạng | Mã CP | Ngành | Giá (`%`) | Điểm Hội Tụ | Dấu Chân Big Boys (TopInvest) | Định Giá & Hợp Lý (Simplize) | ROE / P/E | Vùng Mua | Chặn Hòa Vốn (+5%) | Cắt Lỗ | Target 1 -> Target 2 |")
        lines.append("| :---: | :--- | :--- | :---: | :---: | :--- | :--- | :---: | :---: | :---: | :---: | :---: |")

        for idx, p in enumerate(confluence_picks, 1):
            tp = p["trade_plan"]
            lines.append(
                f"| {idx} | **{p['ticker']}** | {p['industry']} | **{p['price']:,.2f}** (`{p['price_pct']:+.2f}%`) | "
                f"**`{p['confluence_score']}/100`** | {p['smart_money_label']} | "
                f"FV: `{p['fair_value']:,.1f}` ({p['mos_pct']:+.1f}%) | `{p['roe']:.1f}%` / `{p['pe']:.1f}x` | "
                f"`{tp['entry_zone']}` | **`{tp['breakeven_trigger']}`** | `{tp['stop_loss']}` (`{tp['stop_loss_pct']}%`) | "
                f"`{tp['target_1']}` -> `{tp['target_2']}` |"
            )
        lines.append("")

    # =========================================================================
    # 7. RADAR DÒNG TIỀN LỚN "FOLLOW THE BIGBOYS" (TOPINVEST SMART MONEY)
    # =========================================================================
    if smart_money_radar:
        acc_list = smart_money_radar.get("accumulating", [])
        dist_list = smart_money_radar.get("distributing", [])

        lines.append("## 7. 🐳 Radar Dòng Tiền Lớn 'Follow The Bigboys' (TopInvest Smart Money)")
        if acc_list:
            lines.append("### 🟢 Top Cổ Phiếu Cá Mập Đang Gom Hàng Mạnh / Gom Ngầm Nền Giá")
            lines.append("| Mã CP | Ngành | Giá | % Hôm Nay | % Vol (vs 20N) | Thanh Khoản (Tỷ) | Rating | Hành Vi Dòng Tiền Lớn | Phân Tích Chi Tiết |")
            lines.append("| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :--- | :--- |")
            for item in acc_list[:8]:
                lines.append(
                    f"| **{item['ticker']}** | {item['industry']} | {item['price']:,.2f} | `{item['price_pct']:+.2f}%` | "
                    f"**`{item['vol_pct']:.0f}%`** | {item['tbgtdd']:,.1f} | **{item['rating']}** | "
                    f"{item['footprint_label']} | {item['footprint_note']} |"
                )
            lines.append("")

        if dist_list:
            lines.append("### 🚨 Cảnh Báo Cổ Phiếu Có Dấu Hiệu Kéo Xả / Phân Phối Đỉnh (Tránh Mua Đuổi)")
            lines.append("| Mã CP | Ngành | Giá | % Hôm Nay | % Vol (vs 20N) | Thanh Khoản (Tỷ) | Tín Hiệu | Cảnh Báo Hành Vi Tay To |")
            lines.append("| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :--- |")
            for item in dist_list[:5]:
                lines.append(
                    f"| **{item['ticker']}** | {item['industry']} | {item['price']:,.2f} | 🔴 `{item['price_pct']:+.2f}%` | "
                    f"**`{item['vol_pct']:.0f}%`** | {item['tbgtdd']:,.1f} | `{item['signal'] or 'PHÂN PHỐI'}` | {item['footprint_note']} |"
                )
            lines.append("")

    # =========================================================================
    # 8. TÍN HIỆU MUA / BÁN TRỰC TIẾP TRONG PHIÊN & TRADINGBOX
    # =========================================================================
    buy_sigs = daily_signals.get("buy_signals", [])
    sell_sigs = daily_signals.get("sell_signals", [])

    lines.append("## 8. ⚡ Tín Hiệu Mua / Bán Tự Động Trong Phiên (Finbox Real-time Signals)")
    if buy_sigs:
        lines.append("### 🟢 Tín Hiệu MUA (Buy Signals)")
        lines.append("| Mã CP | Giá | % Hôm Nay | Rating | Tín Hiệu | %Vol (20N) | Vùng Mua | Chặn Hòa Vốn (+5%) | Cắt Lỗ | Chốt Lời 1 -> 2 |")
        lines.append("| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |")
        for b in buy_sigs[:10]:
            tp = b["trade_plan"]
            lines.append(
                f"| **{b['ticker']}** | {b['price']:,.2f} | `{b['price_pct']:+.2f}%` | **{b['rating']}** | "
                f"`{b['signal']}` | {b['vol_pct']:.0f}% | `{tp['entry_zone']}` | `{tp['breakeven_trigger']}` | `{tp['stop_loss']}` | `{tp['target_1']}` -> `{tp['target_2']}` |"
            )
        lines.append("")
    else:
        lines.append("- *Hiện chưa ghi nhận thêm tín hiệu MUA trực tiếp mới trong phiên.*")
        lines.append("")

    if sell_sigs:
        lines.append("### 🔴 Tín Hiệu BÁN / Chốt Lời / Hạ Tỷ Trọng (Sell Signals)")
        lines.append("| Mã CP | Giá | % Hôm Nay | Rating | Tín Hiệu | %Vol (20N) | Khuyến Nghị Hành Động |")
        lines.append("| :--- | :---: | :---: | :---: | :---: | :---: | :--- |")
        for s in sell_sigs[:10]:
            lines.append(
                f"| **{s['ticker']}** | {s['price']:,.2f} | `{s['price_pct']:+.2f}%` | {s['rating']} | "
                f"`{s['signal']}` | {s['vol_pct']:.0f}% | Chủ động chốt lời / Cơ cấu hạ tỷ trọng |"
            )
        lines.append("")

    if trading_box_recs:
        lines.append("## 9. 📦 Danh Mục Khuyến Nghị Cơ Sở Finbox (TradingBox Recommendations)")
        lines.append("| Nhóm | Mã CP | Hành Động | Trạng Thái | Ngày Mua | Giá Mua | Giá Hiện Tại | Lãi/Lỗ (%) |")
        lines.append("| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: |")
        for rec in trading_box_recs[:15]:
            cat = rec.get("category", "TOP")
            tk = rec.get("symbol", "")
            sig = rec.get("signal", "BUY")
            st = rec.get("status", "Nắm giữ")
            bdate = str(rec.get("buy_date", ""))[:10]
            bprice = SignalEngine._safe_float(rec.get("buy_price", 0))
            cprice = SignalEngine._safe_float(rec.get("current_price", 0))
            profit = SignalEngine._safe_float(rec.get("profit_pct", 0))
            p_icon = "🟢" if profit > 0 else ("🔴" if profit < 0 else "🟡")
            lines.append(f"| `{cat}` | **{tk}** | `{sig}` | {st} | {bdate} | {bprice:,.2f} | {cprice:,.2f} | {p_icon} `{profit:+.2f}%` |")
        lines.append("")

    # =========================================================================
    # 10. THEO DÕI DANH MỤC ĐẦU TƯ (PORTFOLIO TRACKER + BREAKEVEN +5%)
    # =========================================================================
    if portfolio_eval and portfolio_eval.get("positions"):
        lines.append("## 10. 💼 Theo Dõi Danh Mục Đầu Tư & Cảnh Báo Vị Thế (Watchlist / Portfolio)")
        lines.append(f"- **Tổng giá trị vốn đầu tư**: `{portfolio_eval['total_cost']:,.2f}`")
        lines.append(f"- **Tổng giá trị thị trường hiện tại**: `{portfolio_eval['total_market_value']:,.2f}`")
        pnl_sign = "+" if portfolio_eval["total_pnl"] >= 0 else ""
        lines.append(f"- **Tổng Lãi/Lỗ tạm tính**: `{pnl_sign}{portfolio_eval['total_pnl']:,.2f}` (`{pnl_sign}{portfolio_eval['total_pnl_pct']:.2f}%`)")
        lines.append("")

        if portfolio_eval.get("alerts"):
            lines.append("### 🔔 Cảnh Báo Hành Động Tức Thì Cho Danh Mục:")
            for al in portfolio_eval["alerts"]:
                lines.append(f"- {al}")
            lines.append("")

        lines.append("| Mã CP | Giá Mua | Giá Hiện Tại | Lãi/Lỗ (%) | Mốc Hòa Vốn (+5%) | Cắt Lỗ | Target 1 / 2 | Trạng Thái | Hành Động Khuyến Nghị |")
        lines.append("| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- | :--- |")
        for pos in portfolio_eval["positions"]:
            p_icon = "🟢" if pos["pnl_pct"] > 0 else ("🔴" if pos["pnl_pct"] < 0 else "🟡")
            lines.append(
                f"| **{pos['symbol']}** | {pos['buy_price']:,.2f} | **{pos['current_price']:,.2f}** | "
                f"{p_icon} `{pos['pnl_pct']:+.2f}%` | `{pos['breakeven_trigger']}` | `{pos['stop_loss']}` | `{pos['target_1']}` / `{pos['target_2']}` | "
                f"**{pos['status']}** | {pos['action']} |"
            )
        lines.append("")

    # =========================================================================
    # 11. NGUYÊN TẮC QUẢN TRỊ RỦI RO BẤT BẠI (3-TIER PROACTIVE RISK CONTROL)
    # =========================================================================
    lines.append("## 🛡️ Kỷ Luật Quản Trị Rủi Ro 'Bảo Toàn Vốn Tuyệt Đối' (Simplize x TopInvest)")
    lines.append("1. **Chỉ mua khi Hội Tụ 4 Lớp**: Ưu tiên giải ngân vào các cổ phiếu có **Điểm Hội Tụ $\\ge 75/100$** (Vĩ mô/Ngành ủng hộ + Định giá hợp lý Simplize + Cá mập Big Boys gom hàng + Kỹ thuật Finbox Rating `A/A+`).")
    lines.append("2. **Quy tắc Chặn Hòa Vốn +5% (100% Không Thể Lỗ Khi Đã Đúng Sóng)**: Ngay khi cổ phiếu tăng đạt mốc **`+5.0%`** từ điểm mua, lập tức dời điểm Cắt lỗ (Stop Loss) về bằng **Giá Mua**. Từ thời điểm đó, vị thế của bạn an toàn tuyệt đối trước mọi biến động bất ngờ của thị trường.")
    lines.append("3. **Chốt lời Chủ động 3 Nấc**: Chốt `40% - 50%` tại **Target 1 (`+8% đến +10%`)** để đút túi lợi nhuận; chốt tiếp `30%` tại **Target 2 (`+18% đến +20%`)**; phần còn lại giữ theo đường xu hướng và bán ngay khi xuất hiện cảnh báo **Kéo xả / Phân phối (`%Vol >= 135%` kèm giá giảm)**.")
    lines.append("4. **Kỷ luật Cắt lỗ Sắt đá**: Nếu cổ phiếu đi ngược dự kiến và chạm ngưỡng Stop Loss (`-5.5% đến -6.5%`), hạ tỷ trọng/cắt lỗ dứt khoát, tuyệt đối không bình quân giá xuống ở cổ phiếu đang gãy xu hướng.")
    lines.append("")
    lines.append("*Lưu ý: Báo cáo kết hợp dữ liệu định lượng thời gian thực từ Finbox DCS, chỉ số liên thị trường quốc tế, mô hình định giá Simplize và thuật toán dòng tiền lớn TopInvest nhằm hỗ trợ ra quyết định kỷ luật cao nhất.*")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="VN Stock Market Advisor Runner (4-Pillar Pro)")
    parser.add_argument("--ticker", type=str, default=None, help="Mã cổ phiếu cần phân tích sâu (VD: FPT, SSI, HPG)")
    parser.add_argument("--query", type=str, default=None, help="Câu truy vấn lọc cổ phiếu bằng ngôn ngữ tự nhiên")
    parser.add_argument("--dip", action="store_true", help="Lọc danh sách cổ phiếu bắt đáy (Dip Buying API /data/dip)")
    parser.add_argument("--min-rating", type=str, default="B+", help="Xếp hạng Finbox tối thiểu (A+, A, A-, B+, B)")
    parser.add_argument("--min-liquidity", type=float, default=5.0, help="Thanh khoản TB 20 phiên tối thiểu (tỷ VNĐ)")
    parser.add_argument("--only-signals", action="store_true", help="Chỉ lọc các mã có tín hiệu mua hoặc nổ Vol hôm nay")
    parser.add_argument("--top-n", type=int, default=12, help="Số lượng cổ phiếu khuyến nghị tối đa")
    parser.add_argument("--no-macro", action="store_true", help="Bỏ qua bước thu thập dữ liệu Vĩ mô & Tin tức")
    parser.add_argument("--watchlist", type=str, default=None, help="JSON string hoặc đường dẫn file JSON chứa danh mục")
    parser.add_argument("--output-dir", type=str, default=".", help="Tham số tương thích ngược (không ghi file .md)")

    args = parser.parse_args()

    client = FinboxClient()

    # 1. Lấy dữ liệu tổng quan thị trường & bảng cổ phiếu toàn sàn từ Finbox
    logger.info("Fetching market overview and indices from Finbox DCS...")
    overview = client.get_market_overview()
    indices = client.get_market_indices()

    logger.info("Fetching all tickers filter table (19 quantitative fields)...")
    all_tickers = client.get_all_tickers_filter()

    # 2. Phân tích Tâm lý Đám đông (TopInvest), Định giá Thị trường (Simplize) & Sóng Ngành
    logger.info("Analyzing crowd sentiment, market valuation cycle, and sector money flow rotation...")
    market_regime = SignalEngine.analyze_market_regime_and_crowd(overview, all_tickers)
    sector_rankings, sector_benchmarks = SignalEngine.analyze_sector_rotation(all_tickers)
    leading_sector_names = [s["industry"] for s in sector_rankings[:6]]

    # 3. Thu thập dữ liệu Vĩ mô Liên thị trường & Tin tức Kinh tế / Cổ phiếu
    macro_data = None
    if not args.no_macro:
        logger.info("Fetching real-time intermarket indicators and economic/stock news...")
        macro_client = MacroClient(timeout=5)
        intermarket = macro_client.fetch_intermarket_indicators()
        news_data = macro_client.fetch_macro_and_stock_news(
            ticker=args.ticker,
            custom_query=args.query
        )
        foreign_net = SignalEngine._safe_float(overview.get("foreign_net", 0.0))
        synthesis = MacroClient.evaluate_macro_synthesis(intermarket, news_data, foreign_net_value=foreign_net)
        macro_data = {
            "intermarket": intermarket,
            "news": news_data,
            "synthesis": synthesis,
        }

    # 4. Sàng lọc Bảng Xếp Hạng Cổ Phiếu "Siêu Hội Tụ 4 Lớp" & Radar Dòng Tiền Big Boys
    confluence_picks = SignalEngine.filter_high_conviction_stocks(
        all_tickers=all_tickers,
        sector_benchmarks=sector_benchmarks,
        leading_sectors=leading_sector_names,
        min_liquidity=args.min_liquidity,
        top_n=args.top_n
    )
    smart_money_radar = SignalEngine.filter_smart_money_radar(
        all_tickers=all_tickers,
        min_liquidity=max(args.min_liquidity, 8.0),
        top_n=8
    )

    daily_signals = SignalEngine.extract_daily_signals(all_tickers, min_liquidity=args.min_liquidity)

    # 5. Xử lý truy vấn ngôn ngữ tự nhiên (--query) hoặc bắt đáy (--dip)
    nl_query_result = None
    if args.query:
        logger.info(f"Executing natural language filter query: {args.query}")
        nl_raw = client.query_by_natural_language(args.query)
        nl_query_result = {
            "query": args.query,
            "endpoint": "/data/dip" if nl_raw.get("is_dip_endpoint") else "/data/filter",
            "results": nl_raw.get("symbols", [])
        }

    dip_stocks = None
    if args.dip:
        logger.info("Fetching dip buying stocks (/data/dip)...")
        dip_res = client.get_dip_buying_stocks(count=args.top_n)
        dip_stocks = dip_res.get("symbols", [])

    logger.info("Fetching Finbox TradingBox base recommendations (/kn/all)...")
    tb_data = client.get_trading_box_recommendations()
    trading_box_recs = tb_data.get("active_positions", []) if isinstance(tb_data, dict) else (tb_data if isinstance(tb_data, list) else [])

    # 6. Nếu có yêu cầu phân tích chuyên sâu 1 mã cổ phiếu (--ticker)
    ticker_detail = None
    ticker_history = None
    target_symbol = None
    target_symbol_row = None
    if args.ticker:
        target_symbol = args.ticker.strip().upper()
        logger.info(f"Fetching 360-degree deep analysis for {target_symbol}...")
        for item in all_tickers:
            if str(item.get("ticker", "")).upper() == target_symbol:
                target_symbol_row = item
                break
        ticker_detail = client.get_ticker_detail(target_symbol)
        ticker_history = client.get_symbol_signals_history(target_symbol)

    # 7. Nếu có danh mục đầu tư / Watchlist cần theo dõi
    portfolio_eval = None
    if args.watchlist:
        positions = []
        wl_str = args.watchlist.strip()
        if os.path.exists(wl_str):
            with open(wl_str, "r", encoding="utf-8") as f:
                positions = json.load(f)
        else:
            try:
                positions = json.loads(wl_str)
            except json.JSONDecodeError:
                for part in wl_str.split(","):
                    if ":" in part:
                        s, p = part.split(":", 1)
                        positions.append({"symbol": s.strip().upper(), "buy_price": float(p.strip()), "quantity": 100})

        if positions:
            price_map = {str(item.get("ticker", "")).upper(): item for item in all_tickers if item.get("ticker")}
            tracker = PortfolioTracker(positions)
            portfolio_eval = tracker.evaluate_portfolio(price_map)

    # 8. Tổng hợp báo cáo Markdown và in trực tiếp ra stdout
    markdown_content = generate_markdown_report(
        overview=overview,
        indices=indices,
        confluence_picks=confluence_picks,
        smart_money_radar=smart_money_radar,
        market_regime=market_regime,
        sector_rankings=sector_rankings,
        sector_benchmarks=sector_benchmarks,
        daily_signals=daily_signals,
        macro_data=macro_data,
        portfolio_eval=portfolio_eval,
        ticker_detail=ticker_detail,
        ticker_history=ticker_history,
        target_symbol=target_symbol,
        nl_query_result=nl_query_result,
        dip_stocks=dip_stocks,
        trading_box_recs=trading_box_recs,
        target_symbol_row=target_symbol_row,
    )

    print(markdown_content)


if __name__ == "__main__":
    main()

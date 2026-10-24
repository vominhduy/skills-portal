"""
Signal Calculation, Valuation (Simplize-style), Smart Money Radar (TopInvest-style)
& 4-Layer High-Conviction Confluence Engine for VN Stock Advisor.
"""

import statistics
from typing import Any, Dict, List, Optional, Tuple


class SignalEngine:
    """
    Hệ thống Định lượng Đa tầng (4-Pillar Quantitative Engine):
    1. Kỹ thuật & Quản trị rủi ro 3 nấc (Finbox DCS + Breakeven Stop +5%):
       - Điểm Hòa Vốn Bảo Vệ (Breakeven Trigger): Chạm +5.0% -> nâng chặn lỗ về giá mua (100% không thua lỗ).
       - Mục tiêu 1 (Target 1): +8.5% (Chốt lời chủ động 40-50% vị thế).
       - Mục tiêu 2 (Target 2): +18.0% (Chốt lời theo sóng ngành).
       - Cắt lỗ tiêu chuẩn (Stop Loss): -5.5% đến -6.5% từ điểm vào lệnh.
    2. Dòng tiền Thông minh & Tâm lý Đám đông (TopInvest "Follow the Bigboys" Style):
       - Bóc tách dấu chân Cá mập: Gom hàng bùng nổ, Gom ngầm nền giá, Cầu bắt đáy, Kéo xả/Phân phối đỉnh.
       - Chỉ số Tâm lý Đám đông (Crowd Sentiment 0-100): Hoảng loạn vùng đáy <-> Hưng phấn vùng đỉnh.
       - Radar Luân chuyển Dòng tiền Ngành (Sector Money Flow Rotation).
    3. Định giá Cơ bản & Sức khỏe Tài chính 5 Trụ cột (Simplize Snowflake Style):
       - Định giá P/E, P/B so với Trung vị Ngành -> Giá trị hợp lý (Fair Value) & Biên an toàn (Margin of Safety %).
       - Chấm điểm 5 Trụ cột (Snowflake /25) & Cảnh báo rủi ro tài chính (Nợ/VCSH cao, P/E ảo, ROE yếu).
    4. Ma trận Siêu Hội Tụ 4 Lớp (Confluence Score 0-100 điểm):
       - Chọn lọc các cổ phiếu hội tụ đồng thời: Kỹ thuật mạnh + Cá mập gom + Định giá rẻ/hợp lý + Ngành dẫn dắt.
    """

    RATING_SCORES = {
        "A+": 10,
        "A": 9,
        "A-": 8,
        "B+": 7,
        "B": 6,
        "B-": 5,
        "C+": 4,
        "C": 3,
        "C-": 2,
        "D+": 1,
        "D": 0,
        "D-": -1
    }

    @classmethod
    def evaluate_entry_points(
        cls,
        price: float,
        signal_type: str = "BIG BUY",
        support_price: Optional[float] = None,
        resistance_price: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Tính toán vùng mua, điểm kích hoạt hòa vốn (+5%), cắt lỗ và chốt lời 3 nấc.
        """
        if price <= 0:
            return {}

        entry_low = round(price * 0.985, 2)
        entry_high = round(price * 1.015, 2)

        sig_upper = (signal_type or "").upper()
        if "PULLBACK" in sig_upper or "SMALL" in sig_upper or "DIP" in sig_upper:
            sl_pct = 0.055  # -5.5%
            tp1_pct = 0.08
            tp2_pct = 0.16
        else:
            sl_pct = 0.065  # -6.5%
            tp1_pct = 0.09
            tp2_pct = 0.20

        stop_loss = round(support_price * 0.99, 2) if (support_price and support_price < price) else round(price * (1.0 - sl_pct), 2)
        breakeven_trigger = round(price * 1.05, 2)  # Điểm kích hoạt nâng SL về hòa vốn (+5%)
        target_1 = round(price * (1.0 + tp1_pct), 2)
        target_2 = round(resistance_price, 2) if (resistance_price and resistance_price > target_1) else round(price * (1.0 + tp2_pct), 2)

        risk = max(price - stop_loss, 0.01)
        reward_1 = max(target_1 - price, 0.0)
        reward_2 = max(target_2 - price, 0.0)

        rr_1 = round(reward_1 / risk, 2)
        rr_2 = round(reward_2 / risk, 2)

        actual_sl_pct = round(((stop_loss - price) / price) * 100, 2)
        actual_tp1_pct = round(((target_1 - price) / price) * 100, 2)
        actual_tp2_pct = round(((target_2 - price) / price) * 100, 2)

        return {
            "current_price": price,
            "entry_zone": f"{entry_low} - {entry_high}",
            "entry_low": entry_low,
            "entry_high": entry_high,
            "breakeven_trigger": breakeven_trigger,
            "breakeven_pct": 5.0,
            "stop_loss": stop_loss,
            "stop_loss_pct": actual_sl_pct,
            "target_1": target_1,
            "target_1_pct": actual_tp1_pct,
            "target_2": target_2,
            "target_2_pct": actual_tp2_pct,
            "rr_ratio_1": rr_1,
            "rr_ratio_2": rr_2,
            "is_favorable_rr": rr_2 >= 2.0
        }

    # =========================================================================
    # 1. TOPINVEST CROWD SENTIMENT & SIMPLIZE MARKET VALUATION CYCLE
    # =========================================================================
    @classmethod
    def analyze_market_regime_and_crowd(
        cls,
        overview: Dict[str, Any],
        all_tickers: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Đo lường Chỉ số Tâm lý Đám đông (TopInvest Crowd Sentiment 0-100)
        và Chu kỳ Định giá Thị trường Chung (Simplize Market P/E & P/B).
        """
        pos_pct = cls._safe_float(overview.get("pos_pct", 50.0))
        buy_sell_ratio = cls._safe_float(overview.get("ratio", 1.0))
        foreign_net = cls._safe_float(overview.get("foreign_net", 0.0))

        liquid_stocks = [s for s in all_tickers if cls._safe_float(s.get("tbgtdd", 0)) >= 1.5]
        total_liquid = max(len(liquid_stocks), 1)

        uptrend_count = sum(1 for s in liquid_stocks if str(s.get("trend", "")).upper() == "TĂNG")
        vol_surge_up = sum(
            1 for s in liquid_stocks
            if cls._safe_float(s.get("volumePercent", 0)) >= 120.0 and cls._safe_float(s.get("pricePercent", 0)) > 0.5
        )
        vol_surge_down = sum(
            1 for s in liquid_stocks
            if cls._safe_float(s.get("volumePercent", 0)) >= 120.0 and cls._safe_float(s.get("pricePercent", 0)) < -1.0
        )

        uptrend_pct = (uptrend_count / total_liquid) * 100.0
        surge_up_pct = (vol_surge_up / total_liquid) * 100.0
        surge_down_pct = (vol_surge_down / total_liquid) * 100.0

        # Tính điểm Tâm lý Đám đông (0 - 100)
        # 40% từ Độ rộng thị trường + 25% từ Tỷ lệ Mua/Bán + 20% từ Tỷ lệ mã Uptrend + 15% từ Đột biến dòng tiền
        ratio_norm = min(max(buy_sell_ratio / 2.5, 0.0), 1.0) * 100.0
        flow_diff_norm = min(max(50.0 + (surge_up_pct - surge_down_pct) * 2.5, 0.0), 100.0)
        crowd_score = round(
            pos_pct * 0.40 + ratio_norm * 0.25 + uptrend_pct * 0.20 + flow_diff_norm * 0.15,
            1
        )
        crowd_score = max(5.0, min(98.0, crowd_score))

        if crowd_score <= 22:
            crowd_state = "🥶 HOẢNG LOẠN CỰC ĐỘ (Extreme Panic - Vùng Đáy Tiềm Năng)"
            allocation = "Giải ngân gom dần 40% - 60% cổ phiếu cơ bản Hạng A chiết khấu sâu"
            action_advice = "Đám đông đang bán tháo quá đà. Tuyệt đối không bán đuổi giá sàn; ưu tiên săn cổ phiếu có Cầu bắt đáy lớn (DIP BUY)."
        elif crowd_score <= 40:
            crowd_state = "😰 THẬN TRỌNG / PHÒNG THỦ (Fear & Accumulation)"
            allocation = "30% - 50% Cổ phiếu / 50% - 70% Tiền mặt"
            action_advice = "Dòng tiền chung còn dè dặt. Chỉ giải ngân thăm dò ở các cổ phiếu có Cá mập gom ngầm nền giá và định giá rẻ."
        elif crowd_score <= 68:
            crowd_state = "⚖️ CÂN BẰNG CUNG - CẦU / ĐỒNG THUẬN (Constructive Equilibrium)"
            allocation = "60% - 80% Cổ phiếu / 20% - 40% Tiền mặt"
            action_advice = "Trạng thái lý tưởng nhất để Mua theo dòng tiền lớn (Follow the Bigboys) tại các nhóm ngành dẫn dắt."
        elif crowd_score <= 82:
            crowd_state = "🔥 HƯNG PHẤN TÍCH CỰC (Greed / Strong Bull)"
            allocation = "70% Cổ phiếu (Ưu tiên gồng lãi) / 30% Tiền mặt"
            action_advice = "Sóng tăng lan tỏa mạnh nhưng hạn chế FOMO mua đuổi các mã đã tăng quá +7% từ nền. Chủ động nâng chặn lãi."
        else:
            crowd_state = "🚨 HƯNG PHẤN QUÁ ĐÀ (Extreme Euphoria - Cảnh Báo Đỉnh Ngắn Hạn)"
            allocation = "Hạ tỷ trọng về 40% - 50% Cổ phiếu, thu hồi toàn bộ Margin"
            action_advice = "Đám đông đang hưng phấn cực điểm, rủi ro Big Boys kéo xả cao. Chủ động chốt lời 50% danh mục và tuyệt đối không mua đuổi."

        # Định giá P/E, P/B, ROE trung vị toàn thị trường (Simplize Market Cycle)
        valid_pes = [cls._safe_float(s.get("pe", 0)) for s in liquid_stocks if 2.0 < cls._safe_float(s.get("pe", 0)) < 60.0]
        valid_pbs = [cls._safe_float(s.get("pb", 0)) for s in liquid_stocks if 0.2 < cls._safe_float(s.get("pb", 0)) < 10.0]
        valid_roes = [cls._safe_float(s.get("roe", 0)) for s in liquid_stocks if -20.0 < cls._safe_float(s.get("roe", 0)) < 60.0]

        market_pe = round(statistics.median(valid_pes), 2) if valid_pes else 13.5
        market_pb = round(statistics.median(valid_pbs), 2) if valid_pbs else 1.6
        market_roe = round(statistics.median(valid_roes), 2) if valid_roes else 13.0

        if market_pe < 11.5:
            valuation_zone = "💎 VÙNG ĐỊNH GIÁ RẺ (Undervalued - Cơ hội tích sản dài hạn)"
        elif market_pe <= 14.8:
            valuation_zone = "🟢 VÙNG ĐỊNH GIÁ HỢP LÝ (Fair Value - Đầu tư theo tăng trưởng & dòng tiền)"
        elif market_pe <= 17.0:
            valuation_zone = "🟡 VÙNG ĐỊNH GIÁ KHÁ CAO (Slightly Expensive - Chọn lọc khắt khe)"
        else:
            valuation_zone = "🔴 VÙNG ĐỊNH GIÁ ĐẮT (Overvalued - Cảnh giác bong bóng định giá)"

        return {
            "crowd_score": crowd_score,
            "crowd_state": crowd_state,
            "recommended_allocation": allocation,
            "action_advice": action_advice,
            "uptrend_pct": round(uptrend_pct, 1),
            "vol_surge_up_count": vol_surge_up,
            "vol_surge_down_count": vol_surge_down,
            "market_pe": market_pe,
            "market_pb": market_pb,
            "market_roe": market_roe,
            "valuation_zone": valuation_zone,
            "foreign_net": foreign_net,
        }

    # =========================================================================
    # 2. SECTOR MONEY FLOW ROTATION & BENCHMARKS (TOPINVEST + SIMPLIZE)
    # =========================================================================
    @classmethod
    def analyze_sector_rotation(
        cls,
        all_tickers: List[Dict[str, Any]]
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Dict[str, float]]]:
        """
        Xếp hạng dòng tiền luân chuyển giữa các Nhóm ngành (Sector Rotation)
        và tính bộ chỉ số Định giá Trung vị Ngành (P/E, P/B, ROE) làm chuẩn tham chiếu Simplize.
        """
        sectors: Dict[str, List[Dict[str, Any]]] = {}
        for s in all_tickers:
            ind = (s.get("industry") or "").strip()
            if not ind or ind in ("0", "None", "Khác"):
                continue
            tbgtdd = cls._safe_float(s.get("tbgtdd", 0))
            if tbgtdd < 0.5:
                continue
            sectors.setdefault(ind, []).append(s)

        sector_rankings: List[Dict[str, Any]] = []
        sector_benchmarks: Dict[str, Dict[str, float]] = {}

        for ind, stocks in sectors.items():
            if len(stocks) < 2:
                continue

            total_liq = sum(cls._safe_float(x.get("tbgtdd", 0)) for x in stocks)
            avg_vol_pct = statistics.mean([cls._safe_float(x.get("volumePercent", 0)) for x in stocks])
            avg_price_pct = statistics.mean([cls._safe_float(x.get("pricePercent", 0)) for x in stocks])
            up_count = sum(1 for x in stocks if cls._safe_float(x.get("pricePercent", 0)) > 0)
            uptrend_count = sum(1 for x in stocks if str(x.get("trend", "")).upper() == "TĂNG")
            buy_sigs = sum(
                1 for x in stocks
                if any(k in str(x.get("signal", "")).upper() for k in ["BUY", "MUA", "PULLBACK"])
                or str(x.get("dip_signal", "")).upper() not in ("", "0", "NONE")
            )
            sell_sigs = sum(
                1 for x in stocks
                if any(k in str(x.get("signal", "")).upper() for k in ["SELL", "BÁN", "BAN"])
            )

            pes = [cls._safe_float(x.get("pe", 0)) for x in stocks if 2.0 < cls._safe_float(x.get("pe", 0)) < 65.0]
            pbs = [cls._safe_float(x.get("pb", 0)) for x in stocks if 0.2 < cls._safe_float(x.get("pb", 0)) < 10.0]
            roes = [cls._safe_float(x.get("roe", 0)) for x in stocks if -15.0 < cls._safe_float(x.get("roe", 0)) < 60.0]

            med_pe = round(statistics.median(pes), 2) if pes else 13.5
            med_pb = round(statistics.median(pbs), 2) if pbs else 1.6
            med_roe = round(statistics.median(roes), 2) if roes else 13.0

            sector_benchmarks[ind] = {
                "pe": med_pe,
                "pb": med_pb,
                "roe": med_roe,
            }

            up_ratio = (up_count / len(stocks)) * 100.0
            uptrend_ratio = (uptrend_count / len(stocks)) * 100.0

            # Điểm sức mạnh dòng tiền ngành (0 - 100)
            flow_score = (
                min(avg_vol_pct, 200.0) * 0.25
                + max(min((avg_price_pct + 3.0) * 10.0, 60.0), 0.0) * 0.30
                + up_ratio * 0.25
                + uptrend_ratio * 0.20
                + (buy_sigs - sell_sigs) * 2.0
            )
            flow_score = round(max(5.0, min(99.0, flow_score)), 1)

            if flow_score >= 62 and avg_price_pct >= 0.4 and avg_vol_pct >= 90:
                flow_status = "🔥 DẪN DẮT SÓNG (Big Boys Inflow)"
            elif flow_score >= 50 and up_ratio >= 45:
                flow_status = "🟢 TÍCH LŨY / HÚT TIỀN (Accumulating)"
            elif avg_price_pct <= -0.8 and avg_vol_pct >= 110:
                flow_status = "🔴 ÁP LỰC PHÂN PHỐI / RÚT TIỀN (Outflow)"
            else:
                flow_status = "🟡 PHÂN HÓA (Selective)"

            # Chọn Top 3 cổ phiếu dẫn dắt trong ngành
            sorted_members = sorted(
                stocks,
                key=lambda item: (
                    cls.RATING_SCORES.get(str(item.get("rating", "C")), 0),
                    cls._safe_float(item.get("volumePercent", 0)),
                    cls._safe_float(item.get("tbgtdd", 0))
                ),
                reverse=True
            )
            leaders = [str(m.get("ticker", "")) for m in sorted_members[:3] if m.get("ticker")]

            sector_rankings.append({
                "industry": ind,
                "stock_count": len(stocks),
                "total_liquidity": round(total_liq, 1),
                "avg_vol_pct": round(avg_vol_pct, 1),
                "avg_price_pct": round(avg_price_pct, 2),
                "up_ratio": round(up_ratio, 1),
                "uptrend_ratio": round(uptrend_ratio, 1),
                "buy_signals": buy_sigs,
                "sell_signals": sell_sigs,
                "median_pe": med_pe,
                "median_pb": med_pb,
                "median_roe": med_roe,
                "flow_score": flow_score,
                "flow_status": flow_status,
                "leaders": ", ".join(leaders),
            })

        sector_rankings.sort(key=lambda x: (x["flow_score"], x["total_liquidity"]), reverse=True)
        return sector_rankings, sector_benchmarks

    # =========================================================================
    # 3. TOPINVEST SMART MONEY / BIG BOYS FOOTPRINT RADAR
    # =========================================================================
    @classmethod
    def detect_smart_money_footprint(cls, stock_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Bóc tách dấu chân Dòng tiền lớn (Big Boys / Cá mập) dựa trên tương quan Giá - Khối lượng - Thanh khoản - Xu hướng.
        Trả về điểm Smart Money (0 - 30 điểm) cho Ma trận Hội tụ.
        """
        price_pct = cls._safe_float(stock_data.get("pricePercent", 0))
        vol_pct = cls._safe_float(stock_data.get("volumePercent", 0))
        tbgtdd = cls._safe_float(stock_data.get("tbgtdd", 0))
        trend = str(stock_data.get("trend", "")).upper()
        signal = str(stock_data.get("signal", "")).upper()
        dip_signal = str(stock_data.get("dip_signal", "")).upper()
        rating = str(stock_data.get("rating", "C")).upper()
        rating_val = cls.RATING_SCORES.get(rating, 3)

        is_sell_sig = any(k in signal for k in ["SELL", "BÁN", "BAN"])
        is_buy_sig = any(k in signal for k in ["BUY", "MUA", "PULLBACK"])
        is_dip_sig = dip_signal not in ("", "0", "NONE")

        # Trường hợp 1: Cảnh báo Kéo xả / Phân phối đỉnh (Big Boys Distribution)
        if (vol_pct >= 135.0 and price_pct <= -1.5) or (is_sell_sig and vol_pct >= 115.0):
            return {
                "code": "DISTRIBUTION",
                "label": "⚠️ KÉO XẢ / PHÂN PHỐI (Distribution)",
                "score": 0,
                "is_distributing": True,
                "note": f"Khối lượng bung mạnh ({vol_pct:.0f}% TB 20N) kèm áp lực bán giá đỏ ({price_pct:+.2f}%). Dấu hiệu tay to thoát hàng, tuyệt đối không mua đuổi."
            }

        # Trường hợp 2: Cá mập Gom hàng Bùng nổ (Big Boys Breakout Inflow)
        if vol_pct >= 125.0 and price_pct >= 1.5 and tbgtdd >= 8.0 and not is_sell_sig:
            liq_bonus = 4 if tbgtdd >= 30.0 else (2 if tbgtdd >= 15.0 else 0)
            raw_score = min(30, 24 + liq_bonus + (2 if is_buy_sig else 0))
            return {
                "code": "BIG_BOYS_BREAKOUT",
                "label": "🐳 CÁ MẬP GOM MẠNH (Big Boys Breakout)",
                "score": raw_score,
                "is_distributing": False,
                "note": f"Dòng tiền tổ chức nhập cuộc quyết liệt (Vol đạt {vol_pct:.0f}% TB 20N, GTGD {tbgtdd:,.1f} tỷ/phiên, giá tăng {price_pct:+.2f}%)."
            }

        # Trường hợp 3: Cá mập Gom ngầm nền giá (Stealth Accumulation)
        if 95.0 <= vol_pct <= 165.0 and -0.6 <= price_pct <= 1.8 and rating_val >= 7 and trend in ("TĂNG", "TRUNG LẬP") and not is_sell_sig:
            raw_score = 22 if (tbgtdd >= 15.0 and trend == "TĂNG") else 19
            return {
                "code": "STEALTH_ACCUMULATION",
                "label": "🕵️ GOM NGẦM NỀN GIÁ (Stealth Accumulation)",
                "score": raw_score,
                "is_distributing": False,
                "note": f"Dòng tiền lớn hấp thụ cung lặng lẽ tại nền giá chặt ({price_pct:+.2f}%, Vol {vol_pct:.0f}% TB 20N). Điểm mua sớm an toàn trước khi nổ sóng."
            }

        # Trường hợp 4: Cầu Bắt đáy Lớn hấp thụ (Bottom Fishing Absorption)
        if (is_dip_sig or price_pct >= 0.5) and vol_pct >= 115.0 and tbgtdd >= 5.0 and not is_sell_sig:
            return {
                "code": "BOTTOM_ABSORPTION",
                "label": "🛟 CẦU BẮT ĐÁY LỚN (Smart Money Absorption)",
                "score": 20,
                "is_distributing": False,
                "note": f"Lực cầu lớn vào bắt đáy hấp thụ lực cung bán tháo (Vol {vol_pct:.0f}% TB 20N)."
            }

        # Trường hợp 5: Dòng tiền đồng thuận xu hướng tăng
        if trend == "TĂNG" and price_pct > 0 and vol_pct >= 85.0 and not is_sell_sig:
            return {
                "code": "HEALTHY_TREND",
                "label": "🟢 DÒNG TIỀN ĐỒNG THUẬN (Healthy Uptrend)",
                "score": 16,
                "is_distributing": False,
                "note": f"Giữ vững cấu trúc xu hướng tăng với dòng tiền duy trì ổn định ({vol_pct:.0f}% TB 20N)."
            }

        # Trường hợp 6: Cạn cung test nền hoặc dòng tiền yếu
        if abs(price_pct) <= 1.0 and vol_pct < 85.0 and trend == "TĂNG" and rating_val >= 7:
            return {
                "code": "LOW_SUPPLY_TEST",
                "label": "💎 TEST CUNG CẠN KIỆT (No-Supply Test)",
                "score": 15,
                "is_distributing": False,
                "note": f"Biên độ hẹp ({price_pct:+.2f}%) kèm Vol cạn ({vol_pct:.0f}% TB 20N) trong xu hướng tăng -> Áp lực bán đã cạn."
            }

        return {
            "code": "WEAK_FLOW",
            "label": "💤 DÒNG TIỀN YẾU / CHờ XÁC NHẬN",
            "score": 6 if not is_sell_sig else 2,
            "is_distributing": False,
            "note": f"Dòng tiền chưa có sự đột biến rõ rệt (Vol {vol_pct:.0f}% TB 20N, Giá {price_pct:+.2f}%)."
        }

    # =========================================================================
    # 4. SIMPLIZE 5-PILLAR FUNDAMENTAL VALUATION & SNOWFLAKE ENGINE
    # =========================================================================
    @classmethod
    def evaluate_simplize_fundamental(
        cls,
        stock_data: Dict[str, Any],
        sector_benchmarks: Optional[Dict[str, Dict[str, float]]] = None,
        detail_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Đánh giá Cơ bản & Định giá theo triết lý 5 Trụ cột của Simplize (Snowflake Model):
        - Ước tính Giá trị hợp lý (Fair Value) & Biên an toàn (Margin of Safety %) so với chuẩn Ngành.
        - Chấm điểm Cơ bản 0 - 25 điểm cho Ma trận Hội tụ.
        - Phát hiện Cảnh báo Sức khỏe Tài chính (Nợ/VCSH cao, P/E ảo, ROE kém).
        """
        d_data = (detail_data or {}).get("data", detail_data or {}) if isinstance(detail_data, dict) else {}

        price = cls._safe_float(stock_data.get("priceFlat") or d_data.get("close") or 0)
        pe = cls._safe_float(stock_data.get("pe") or d_data.get("pe") or 0)
        pb = cls._safe_float(stock_data.get("pb") or d_data.get("pb") or 0)
        roe = cls._safe_float(stock_data.get("roe") or d_data.get("roe") or 0)
        roa = cls._safe_float(stock_data.get("roa") or d_data.get("roa") or 0)
        eps = cls._safe_float(stock_data.get("eps") or d_data.get("eps") or 0)
        vonhoa = cls._safe_float(stock_data.get("vonhoa") or d_data.get("vonHoa") or 0)
        no_vcsh = cls._safe_float(d_data.get("noVCSH") or 0)
        rev_growth = cls._safe_float(d_data.get("doanhThuQuyGanNhat") or 0)
        profit_growth = cls._safe_float(d_data.get("loiNhuanQuyGanNhat") or 0)

        industry = (stock_data.get("industry") or "").strip()
        bench = (sector_benchmarks or {}).get(industry, {"pe": 13.5, "pb": 1.6, "roe": 13.0})
        sector_pe = bench.get("pe", 13.5)
        sector_pb = bench.get("pb", 1.6)

        # 1. Tính Giá trị hợp lý (Fair Value) & Biên an toàn (Margin of Safety %)
        fair_value = price
        mos_pct = 0.0
        valuation_label = "⚪ Chưa đủ dữ liệu P/E"

        if price > 0 and 1.5 < pe < 80.0:
            # Điều chỉnh P/E mục tiêu theo chất lượng ROE của doanh nghiệp (Simplize Quality-Adjusted P/E)
            if roe >= 20.0:
                target_pe = min(sector_pe * 1.22, 19.5)
            elif roe >= 15.0:
                target_pe = min(sector_pe * 1.12, 17.5)
            elif roe >= 10.0:
                target_pe = sector_pe
            else:
                target_pe = max(sector_pe * 0.82, 8.5)

            pe_implied_price = price * (target_pe / pe)

            if 0.2 < pb < 10.0:
                target_pb = sector_pb * (1.2 if roe >= 18.0 else (1.05 if roe >= 13.0 else 0.85))
                pb_implied_price = price * (target_pb / pb)
                raw_fair = pe_implied_price * 0.65 + pb_implied_price * 0.35
            else:
                raw_fair = pe_implied_price

            # Giới hạn biên độ hợp lý tránh nhiễu số liệu đột biến 1 quý
            fair_value = round(max(price * 0.60, min(price * 1.65, raw_fair)), 2)
            mos_pct = round(((fair_value - price) / price) * 100.0, 1)

            if mos_pct >= 15.0:
                valuation_label = f"💎 ĐỊNH GIÁ RẺ (Biên an toàn +{mos_pct:.1f}%)"
            elif mos_pct >= 0.0:
                valuation_label = f"🟢 HỢP LÝ (Upside định giá +{mos_pct:.1f}%)"
            elif mos_pct >= -12.0:
                valuation_label = f"🟡 TIỆM CẬN GIÁ TRỊ THỰC ({mos_pct:+.1f}%)"
            else:
                valuation_label = f"🔴 ĐỊNH GIÁ CAO ({mos_pct:+.1f}%)"

        # 2. Chấm điểm 5 Trụ cột Simplize (Mỗi trụ 0 - 5 điểm -> Tổng 0 - 25 điểm)
        # Trụ 1: Định giá (Valuation: 0 - 7 điểm)
        if 2.0 < pe <= 10.5 or mos_pct >= 18.0:
            val_pts = 7
        elif (10.5 < pe <= 14.5) or mos_pct >= 8.0:
            val_pts = 6
        elif (14.5 < pe <= 18.5) or mos_pct >= 0.0:
            val_pts = 4
        elif pe > 30.0 or pe <= 0:
            val_pts = 1
        else:
            val_pts = 3

        # Trụ 2: Hiệu quả Sinh lời (ROE / ROA: 0 - 8 điểm)
        if roe >= 20.0:
            prof_pts = 8
        elif roe >= 15.0:
            prof_pts = 7
        elif roe >= 11.0:
            prof_pts = 5
        elif roe >= 6.0:
            prof_pts = 3
        else:
            prof_pts = 1

        # Trụ 3: Sức khỏe Tài chính & Quy mô Vốn hóa (0 - 5 điểm)
        health_pts = 3
        if vonhoa >= 10000:
            health_pts += 2
        elif vonhoa >= 2000:
            health_pts += 1

        is_bank_or_sec = any(k in industry.lower() for k in ["ngân hàng", "chứng khoán", "bảo hiểm", "tài chính"])
        if no_vcsh > 0 and not is_bank_or_sec:
            if no_vcsh > 2.5:
                health_pts = max(1, health_pts - 2)
            elif no_vcsh < 0.8:
                health_pts = min(5, health_pts + 1)

        # Trụ 4: Chất lượng EPS & Tăng trưởng (0 - 5 điểm)
        growth_pts = 3
        if eps >= 3000 or profit_growth > 20:
            growth_pts = 5
        elif eps >= 1500:
            growth_pts = 4
        elif eps < 500 and eps != 0:
            growth_pts = 1

        fundamental_score = min(25, val_pts + prof_pts + health_pts + growth_pts)

        # 3. Cảnh báo chất lượng tài chính (Simplize Financial Red Flags)
        warnings = []
        if pe > 35.0:
            warnings.append(f"P/E cao ({pe:.1f}x vs Ngành {sector_pe:.1f}x) - Giá đã phản ánh kỳ vọng xa")
        elif pe < 0:
            warnings.append("EPS/P/E âm - Doanh nghiệp đang báo lỗ")
        if 0 < roe < 6.0:
            warnings.append(f"Hiệu quả sinh lời ROE thấp ({roe:.1f}%)")
        if no_vcsh > 2.5 and not is_bank_or_sec:
            warnings.append(f"Đòn bẩy Nợ/VCSH cao ({no_vcsh:.2f} lần)")

        return {
            "pe": round(pe, 2),
            "pb": round(pb, 2),
            "roe": round(roe, 2),
            "roa": round(roa, 2),
            "eps": round(eps, 0),
            "vonhoa": round(vonhoa, 1),
            "no_vcsh": round(no_vcsh, 2),
            "sector_pe": sector_pe,
            "sector_pb": sector_pb,
            "fair_value": fair_value,
            "margin_of_safety_pct": mos_pct,
            "valuation_label": valuation_label,
            "fundamental_score": fundamental_score,
            "pillars": {
                "valuation": f"{val_pts}/7",
                "profitability": f"{prof_pts}/8",
                "financial_health": f"{health_pts}/5",
                "growth_eps": f"{growth_pts}/5",
            },
            "warnings": warnings,
            "rev_growth": rev_growth,
            "profit_growth": profit_growth,
        }

    # =========================================================================
    # 5. 4-LAYER HIGH-CONVICTION CONFLUENCE ENGINE (0 - 100 POINTS)
    # =========================================================================
    @classmethod
    def calculate_confluence_score(
        cls,
        stock_data: Dict[str, Any],
        sector_benchmarks: Optional[Dict[str, Dict[str, float]]] = None,
        leading_sectors: Optional[List[str]] = None,
        detail_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Chấm điểm "Siêu Hội Tụ 4 Lớp" (Thang 100 điểm):
        - Lớp 1: Kỹ thuật & Xếp hạng Finbox (Tối đa 30 điểm)
        - Lớp 2: Dòng tiền Thông minh Big Boys TopInvest (Tối đa 30 điểm)
        - Lớp 3: Định giá & Sức khỏe Tài chính Simplize (Tối đa 25 điểm)
        - Lớp 4: Sức mạnh Ngành & Vĩ mô ủng hộ (Tối đa 15 điểm)
        """
        rating = str(stock_data.get("rating", "C")).upper()
        trend = str(stock_data.get("trend", "")).upper()
        signal = str(stock_data.get("signal", "")).upper()
        dip_signal = str(stock_data.get("dip_signal", "")).upper()
        industry = (stock_data.get("industry") or "Khác").strip()

        # --- LỚP 1: KỸ THUẬT & TÍN HIỆU FINBOX (0 - 30 điểm) ---
        rating_map_30 = {
            "A+": 17, "A": 15, "A-": 13, "B+": 11, "B": 8, "B-": 6, "C+": 4, "C": 2
        }
        ta_score = rating_map_30.get(rating, 2)
        if trend == "TĂNG":
            ta_score += 5
        elif trend == "TRUNG LẬP":
            ta_score += 2

        if "BIG BUY" in signal:
            ta_score += 8
        elif "BUY" in signal or "MUA" in signal or "PULLBACK" in signal:
            ta_score += 6
        elif dip_signal not in ("", "0", "NONE"):
            ta_score += 5
        elif any(k in signal for k in ["SELL", "BÁN", "BAN"]):
            ta_score = max(0, ta_score - 12)

        ta_score = min(30, ta_score)

        # --- LỚP 2: DÒNG TIỀN BIG BOYS TOPINVEST (0 - 30 điểm) ---
        smart_money = cls.detect_smart_money_footprint(stock_data)
        sm_score = smart_money["score"]

        # --- LỚP 3: ĐỊNH GIÁ & CƠ BẢN SIMPLIZE (0 - 25 điểm) ---
        simplize = cls.evaluate_simplize_fundamental(stock_data, sector_benchmarks, detail_data)
        fa_score = simplize["fundamental_score"]

        # --- LỚP 4: SỨC MẠNH NGÀNH & ĐỒNG THUẬN VĨ MÔ (0 - 15 điểm) ---
        leader_list = leading_sectors or []
        if industry in leader_list[:3]:
            sector_score = 15
        elif industry in leader_list[:6]:
            sector_score = 12
        elif industry and industry != "Khác":
            sector_score = 8
        else:
            sector_score = 5

        total_score = ta_score + sm_score + fa_score + sector_score
        if smart_money.get("is_distributing"):
            total_score = min(total_score, 42)

        total_score = max(5, min(100, int(round(total_score))))

        if total_score >= 82 and not smart_money.get("is_distributing"):
            conviction_tier = "🔥 SIÊU HỘI TỤ (Top Conviction - Ưu tiên Số 1)"
            action_verdict = "MUA MẠNH / GIẢI NGÂN TỰ TIN"
        elif total_score >= 70 and not smart_money.get("is_distributing"):
            conviction_tier = "⭐ CƠ HỘI CAO (High Probability)"
            action_verdict = "MUA THEO DÒNG TIỀN"
        elif total_score >= 56 and not smart_money.get("is_distributing"):
            conviction_tier = "👀 THEO DÕI / GOM THĂM DÒ (Watch / Accumulate)"
            action_verdict = "CHỜ ĐIỂM TEST NỀN / GIẢI NGÂN 30%"
        else:
            conviction_tier = "🛑 RỦI RO / TRÁNH MUA MỚI (Avoid)"
            action_verdict = "ĐỨNG NGOÀI / CƠ CẤU BÁN"

        return {
            "confluence_score": total_score,
            "conviction_tier": conviction_tier,
            "action_verdict": action_verdict,
            "breakdown": {
                "ta_finbox": f"{ta_score}/30",
                "smart_money_topinvest": f"{sm_score}/30",
                "fundamental_simplize": f"{fa_score}/25",
                "sector_macro": f"{sector_score}/15",
            },
            "smart_money": smart_money,
            "simplize": simplize,
        }

    @classmethod
    def filter_high_conviction_stocks(
        cls,
        all_tickers: List[Dict[str, Any]],
        sector_benchmarks: Optional[Dict[str, Dict[str, float]]] = None,
        leading_sectors: Optional[List[str]] = None,
        min_liquidity: float = 5.0,
        top_n: int = 12
    ) -> List[Dict[str, Any]]:
        """
        Sàng lọc Bảng Xếp Hạng Cổ Phiếu "Siêu Hội Tụ 4 Lớp" (Finbox + TopInvest Big Boys + Simplize Valuation + Sóng Ngành).
        Chỉ chọn các cổ phiếu có thanh khoản tốt, không có lệnh bán, không bị phân phối, và hội tụ cả FA lẫn Dòng tiền.
        """
        candidates = []
        for item in all_tickers:
            ticker = str(item.get("ticker", ""))
            if not ticker or len(ticker) > 4:
                continue

            price = cls._safe_float(item.get("priceFlat", 0))
            tbgtdd = cls._safe_float(item.get("tbgtdd", 0))
            if price <= 0 or tbgtdd < min_liquidity:
                continue

            signal = str(item.get("signal", "")).upper()
            if any(k in signal for k in ["SELL", "BÁN", "BAN"]):
                continue

            confluence = cls.calculate_confluence_score(
                item,
                sector_benchmarks=sector_benchmarks,
                leading_sectors=leading_sectors
            )
            if confluence["smart_money"].get("is_distributing"):
                continue

            trade_plan = cls.evaluate_entry_points(price, signal or "BIG BUY")

            candidates.append({
                "ticker": ticker,
                "floor": item.get("floor", "HOSE"),
                "industry": item.get("industry") or "Khác",
                "price": price,
                "price_pct": cls._safe_float(item.get("pricePercent", 0)),
                "rating": str(item.get("rating", "N/A")),
                "trend": str(item.get("trend", "N/A")),
                "vol_pct": cls._safe_float(item.get("volumePercent", 0)),
                "signal": str(item.get("signal") or item.get("dip_signal") or "TÍCH LŨY"),
                "tbgtdd": tbgtdd,
                "vonhoa": cls._safe_float(item.get("vonhoa", 0)),
                "roe": cls._safe_float(item.get("roe", 0)),
                "pe": cls._safe_float(item.get("pe", 0)),
                "pb": cls._safe_float(item.get("pb", 0)),
                "confluence_score": confluence["confluence_score"],
                "conviction_tier": confluence["conviction_tier"],
                "action_verdict": confluence["action_verdict"],
                "breakdown": confluence["breakdown"],
                "smart_money_label": confluence["smart_money"]["label"],
                "smart_money_note": confluence["smart_money"]["note"],
                "fair_value": confluence["simplize"]["fair_value"],
                "mos_pct": confluence["simplize"]["margin_of_safety_pct"],
                "valuation_label": confluence["simplize"]["valuation_label"],
                "trade_plan": trade_plan,
            })

        candidates.sort(
            key=lambda x: (x["confluence_score"], x["vol_pct"], x["tbgtdd"]),
            reverse=True
        )
        return candidates[:top_n]

    @classmethod
    def filter_smart_money_radar(
        cls,
        all_tickers: List[Dict[str, Any]],
        min_liquidity: float = 8.0,
        top_n: int = 8
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Tạo Radar Dòng Tiền Lớn TopInvest ("Follow the Bigboys"):
        - Danh sách cổ phiếu Cá mập đang Gom mạnh / Gom ngầm.
        - Danh sách cổ phiếu cảnh báo Kéo xả / Phân phối đỉnh để tránh bẫy.
        """
        accumulating = []
        distributing = []

        for item in all_tickers:
            ticker = str(item.get("ticker", ""))
            if not ticker or len(ticker) > 4:
                continue
            price = cls._safe_float(item.get("priceFlat", 0))
            tbgtdd = cls._safe_float(item.get("tbgtdd", 0))
            if price <= 0 or tbgtdd < min_liquidity:
                continue

            sm = cls.detect_smart_money_footprint(item)
            row = {
                "ticker": ticker,
                "industry": item.get("industry") or "Khác",
                "price": price,
                "price_pct": cls._safe_float(item.get("pricePercent", 0)),
                "vol_pct": cls._safe_float(item.get("volumePercent", 0)),
                "tbgtdd": tbgtdd,
                "rating": str(item.get("rating", "N/A")),
                "trend": str(item.get("trend", "N/A")),
                "signal": str(item.get("signal") or ""),
                "footprint_label": sm["label"],
                "footprint_note": sm["note"],
                "sm_score": sm["score"],
            }

            if sm["code"] in ("BIG_BOYS_BREAKOUT", "STEALTH_ACCUMULATION", "BOTTOM_ABSORPTION"):
                accumulating.append(row)
            elif sm["code"] == "DISTRIBUTION":
                distributing.append(row)

        accumulating.sort(key=lambda x: (x["sm_score"], x["vol_pct"], x["tbgtdd"]), reverse=True)
        distributing.sort(key=lambda x: (x["vol_pct"], x["tbgtdd"]), reverse=True)

        return {
            "accumulating": accumulating[:top_n],
            "distributing": distributing[:5],
        }

    @classmethod
    def filter_promising_stocks(
        cls,
        all_tickers: List[Dict[str, Any]],
        min_rating: str = "B+",
        min_liquidity: float = 3.0,
        only_buy_signals: bool = False,
        top_n: int = 15
    ) -> List[Dict[str, Any]]:
        """
        Lọc danh sách cổ phiếu tiềm năng nhất từ bảng tổng hợp `/data/filter` của Finbox.
        """
        min_score = cls.RATING_SCORES.get(min_rating, 7)
        candidates = []

        for item in all_tickers:
            ticker = item.get("ticker", "")
            if not ticker or len(str(ticker)) > 4:
                continue

            rating = str(item.get("rating", "D"))
            score = cls.RATING_SCORES.get(rating, 0)
            if score < min_score:
                continue

            tbgtdd = cls._safe_float(item.get("tbgtdd", 0))
            if tbgtdd < min_liquidity:
                continue

            signal = str(item.get("signal", "")).strip()
            price = cls._safe_float(item.get("priceFlat", 0))
            price_pct = cls._safe_float(item.get("pricePercent", 0))
            vol_pct = cls._safe_float(item.get("volumePercent", 0))
            vonhoa = cls._safe_float(item.get("vonhoa", 0))
            roe = cls._safe_float(item.get("roe", 0))
            pe = cls._safe_float(item.get("pe", 0))

            is_buy_signal = any(k in signal.upper() for k in ["BUY", "MUA", "PULLBACK"])
            is_sell_signal = any(k in signal.upper() for k in ["SELL", "BÁN", "BAN"])

            if is_sell_signal:
                continue

            if only_buy_signals and not is_buy_signal and vol_pct < 120:
                continue

            priority_score = (
                score * 10
                + (30 if "BIG BUY" in signal.upper() else (20 if is_buy_signal else 0))
                + min(vol_pct / 10.0, 25.0)
                + (10 if price_pct > 1.0 else 0)
                + (5 if roe >= 15 else 0)
            )

            trade_plan = cls.evaluate_entry_points(price, signal or "BIG BUY")

            candidates.append({
                "ticker": ticker,
                "price": price,
                "price_pct": price_pct,
                "rating": rating,
                "vol_pct": vol_pct,
                "signal": signal if signal else ("DÒNG TIỀN MẠNH" if vol_pct >= 120 else "TÍCH LŨY TỐT"),
                "tbgtdd": tbgtdd,
                "vonhoa": vonhoa,
                "roe": roe,
                "pe": pe,
                "priority_score": round(priority_score, 2),
                "trade_plan": trade_plan
            })

        candidates.sort(key=lambda x: x["priority_score"], reverse=True)
        return candidates[:top_n]

    @classmethod
    def extract_daily_signals(cls, all_tickers: List[Dict[str, Any]], min_liquidity: float = 2.0) -> Dict[str, List[Dict[str, Any]]]:
        """
        Tách danh sách các mã có tín hiệu MUA / BÁN trực tiếp trong phiên.
        """
        buy_signals = []
        sell_signals = []

        for item in all_tickers:
            ticker = item.get("ticker", "")
            signal = str(item.get("signal", "")).strip()
            tbgtdd = cls._safe_float(item.get("tbgtdd", 0))
            if not signal or tbgtdd < min_liquidity:
                continue

            price = cls._safe_float(item.get("priceFlat", 0))
            entry = {
                "ticker": ticker,
                "price": price,
                "price_pct": cls._safe_float(item.get("pricePercent", 0)),
                "rating": str(item.get("rating", "N/A")),
                "vol_pct": cls._safe_float(item.get("volumePercent", 0)),
                "signal": signal,
                "tbgtdd": tbgtdd,
                "roe": cls._safe_float(item.get("roe", 0)),
                "pe": cls._safe_float(item.get("pe", 0)),
                "trade_plan": cls.evaluate_entry_points(price, signal)
            }

            sig_upper = signal.upper()
            if any(k in sig_upper for k in ["BUY", "MUA", "PULLBACK"]):
                buy_signals.append(entry)
            elif any(k in sig_upper for k in ["SELL", "BÁN", "BAN"]):
                sell_signals.append(entry)

        buy_signals.sort(key=lambda x: (cls.RATING_SCORES.get(x["rating"], 0), x["vol_pct"]), reverse=True)
        sell_signals.sort(key=lambda x: x["vol_pct"], reverse=True)

        return {
            "buy_signals": buy_signals,
            "sell_signals": sell_signals
        }

    @staticmethod
    def _safe_float(val: Any) -> float:
        try:
            if val is None or val == "":
                return 0.0
            return float(val)
        except (ValueError, TypeError):
            return 0.0

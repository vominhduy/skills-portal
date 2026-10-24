"""
Portfolio & Watchlist Tracker.
Tracks positions, unrealized PnL, stop-loss triggers, breakeven stops (+5%), target hits,
and Smart Money distribution alerts based on real-time prices.
"""

from typing import Any, Dict, List, Optional


class PortfolioTracker:
    def __init__(self, positions: Optional[List[Dict[str, Any]]] = None):
        """
        positions schema:
        [
          {
            "symbol": "FPT",
            "buy_price": 135.0,
            "buy_date": "2026-08-15",
            "quantity": 1000,
            "target": 155.0,
            "stop_loss": 126.0,
            "note": "Mua nền tích lũy"
          }
        ]
        """
        self.positions = positions or []

    def evaluate_portfolio(self, current_prices: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Đánh giá danh mục đầu tư hiện tại so với giá thị trường thực tế,
        tích hợp Quy tắc Chặn Hòa Vốn (+5%) và Cảnh báo Cá mập Phân phối (TopInvest style).
        """
        evaluated_positions = []
        total_cost = 0.0
        total_market_value = 0.0
        alerts = []

        for pos in self.positions:
            sym = str(pos.get("symbol", "")).upper().strip()
            if not sym:
                continue

            buy_price = float(pos.get("buy_price", 0.0))
            quantity = int(pos.get("quantity", 0))
            buy_date = pos.get("buy_date", "N/A")

            mkt = current_prices.get(sym, {})
            cur_price = float(mkt.get("priceFlat", buy_price))
            price_pct_today = float(mkt.get("pricePercent", 0.0))
            vol_pct = float(mkt.get("volumePercent", 0.0))
            rating = str(mkt.get("rating", "N/A"))
            signal = str(mkt.get("signal", "")).strip()

            stop_loss = float(pos.get("stop_loss", round(buy_price * 0.935, 2)))
            breakeven_trigger = round(buy_price * 1.05, 2)
            target_1 = float(pos.get("target_1", round(buy_price * 1.085, 2)))
            target_2 = float(pos.get("target", round(buy_price * 1.18, 2)))

            pnl_pct = round(((cur_price - buy_price) / buy_price) * 100, 2) if buy_price > 0 else 0.0
            cost_val = buy_price * quantity
            mkt_val = cur_price * quantity
            pnl_val = round(mkt_val - cost_val, 2)

            total_cost += cost_val
            total_market_value += mkt_val

            is_distributing = (vol_pct >= 135.0 and price_pct_today <= -1.5) or (
                any(k in signal.upper() for k in ["SELL", "BÁN", "BAN"]) and vol_pct >= 115.0
            )

            status = "NẮM GIỮ (HOLD)"
            action = "Tiếp tục nắm giữ theo xu hướng"

            if cur_price <= stop_loss:
                status = "🚨 VI PHẠM CẮT LỖ (STOP LOSS)"
                action = f"BÁN CẮT LỖ NGAY (Giá {cur_price} <= SL {stop_loss}) để bảo toàn vốn"
                alerts.append(f"🚨 **{sym}**: Đã chạm/thủng ngưỡng cắt lỗ ({cur_price} <= {stop_loss}, {pnl_pct:+.2f}%). Khuyến nghị hạ tỷ trọng/bán dứt khoát!")
            elif is_distributing and pnl_pct > 0:
                status = "⚠️ CẢNH BÁO KÉO XẢ (BIG BOYS EXIT)"
                action = f"CHỐT LỜI BẢO VỆ NGAY 50-70% (Vol đột biến {vol_pct:.0f}% kèm giá giảm {price_pct_today:+.2f}%)"
                alerts.append(f"⚠️ **{sym}**: Xuất hiện dấu hiệu Cá mập phân phối (Vol {vol_pct:.0f}% TB 20N, giá {price_pct_today:+.2f}%). Chủ động chốt lời bảo vệ thành quả!")
            elif "SELL" in signal.upper() or "BÁN" in signal.upper():
                status = "⚠️ TÍN HIỆU BÁN (SELL SIGNAL)"
                action = f"Cơ cấu hạ tỷ trọng do xuất hiện tín hiệu {signal}"
                alerts.append(f"⚠️ **{sym}**: Xuất hiện tín hiệu `{signal}` trong phiên. Cân nhắc chốt lời hoặc thu hẹp vị thế.")
            elif cur_price >= target_2:
                status = "🎯 ĐẠT MỤC TIÊU 2 (TARGET 2 HIT)"
                action = f"Chốt lời 70-100% vị thế hoặc nâng chặn lãi lên {round(cur_price * 0.96, 2)}"
                alerts.append(f"🎯 **{sym}**: Đã vượt Target 2 ({cur_price} >= {target_2}, +{pnl_pct}%). Chủ động chốt lời hiện thực hóa lợi nhuận!")
            elif cur_price >= target_1:
                status = "✅ ĐẠT MỤC TIÊU 1 (TARGET 1 HIT)"
                action = f"Chốt lời 40-50% vị thế, nâng điểm chặn lãi lên {breakeven_trigger} (+5%)"
                alerts.append(f"✅ **{sym}**: Đạt Target 1 (+{pnl_pct}%). Nên chốt lời 1/2 và nâng Stop Loss lên {breakeven_trigger} (bảo toàn lãi).")
            elif cur_price >= breakeven_trigger:
                status = "🛡️ KÍCH HOẠT CHẶN HÒA VỐN (+5%)"
                action = f"Nâng Stop Loss từ {stop_loss} lên Giá mua ({buy_price}) -> Vị thế 100% Bất Bại"
                alerts.append(f"🛡️ **{sym}**: Đã lãi +{pnl_pct}% (vượt mốc +5%). Hãy dời Stop Loss về giá vốn `{buy_price}` để đảm bảo thương vụ 100% không thể lỗ!")
            elif pnl_pct <= -4.0:
                status = "⚡ CẢNH BÁO RỦI RO"
                action = f"Theo dõi sát mốc cắt lỗ {stop_loss} (Đang lỗ {pnl_pct}%)"

            evaluated_positions.append({
                "symbol": sym,
                "buy_date": buy_date,
                "buy_price": buy_price,
                "current_price": cur_price,
                "price_pct_today": price_pct_today,
                "vol_pct": vol_pct,
                "quantity": quantity,
                "pnl_pct": pnl_pct,
                "pnl_value": pnl_val,
                "stop_loss": stop_loss,
                "breakeven_trigger": breakeven_trigger,
                "target_1": target_1,
                "target_2": target_2,
                "rating": rating,
                "signal": signal or "NONE",
                "status": status,
                "action": action
            })

        total_pnl = round(total_market_value - total_cost, 2)
        total_pnl_pct = round((total_pnl / total_cost) * 100, 2) if total_cost > 0 else 0.0

        return {
            "positions": evaluated_positions,
            "total_cost": round(total_cost, 2),
            "total_market_value": round(total_market_value, 2),
            "total_pnl": total_pnl,
            "total_pnl_pct": total_pnl_pct,
            "alerts": alerts
        }

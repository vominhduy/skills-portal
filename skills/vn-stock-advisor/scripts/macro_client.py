"""
Macroeconomic, Intermarket & Financial News Client for VN Stock Advisor.
Collects real-time intermarket indicators (DXY, US10Y, USD/VND, Brent Oil, Gold, S&P 500, Nikkei 225, Shanghai)
and Vietnamese macroeconomic / stock-specific news from reputable financial RSS feeds.
"""

import json
import logging
import os
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Any, Dict, List, Optional

from finbox_client import _ensure_proxy_configured

logger = logging.getLogger(__name__)

USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
)


class MacroClient:
    """
    Thu thập dữ liệu Vĩ mô Liên thị trường (Intermarket) và Tin tức Kinh tế / Cổ phiếu thời gian thực.
    """

    INTERMARKET_SYMBOLS = [
        {"key": "DXY", "symbol": "DX-Y.NYB", "name": "Chỉ số Dollar (DXY)", "category": "Tiền tệ & Lãi suất", "unit": "điểm"},
        {"key": "US10Y", "symbol": "^TNX", "name": "Lợi suất TP Mỹ 10Y", "category": "Tiền tệ & Lãi suất", "unit": "%"},
        {"key": "USDVND", "symbol": "VND=X", "name": "Tỷ giá USD/VND", "category": "Tiền tệ & Lãi suất", "unit": "VNĐ"},
        {"key": "BRENT", "symbol": "BZ=F", "name": "Dầu Brent", "category": "Hàng hóa", "unit": "USD/thùng"},
        {"key": "GOLD", "symbol": "GC=F", "name": "Giá Vàng Thế giới", "category": "Hàng hóa", "unit": "USD/oz"},
        {"key": "SP500", "symbol": "^GSPC", "name": "S&P 500 (Mỹ)", "category": "Chứng khoán Quốc tế", "unit": "điểm"},
        {"key": "DJI", "symbol": "^DJI", "name": "Dow Jones (Mỹ)", "category": "Chứng khoán Quốc tế", "unit": "điểm"},
        {"key": "N225", "symbol": "^N225", "name": "Nikkei 225 (Nhật)", "category": "Chứng khoán Quốc tế", "unit": "điểm"},
    ]

    POSITIVE_KEYWORDS = [
        "tăng trưởng", "kỷ lục", "vượt kế hoạch", "lãi lớn", "khởi sắc", "bứt phá",
        "hạ lãi suất", "nới room", "đầu tư công", "giải ngân", "mua ròng", "nâng hạng",
        "hồi phục", "tích cực", "trúng thầu", "chia cổ tức", "hưởng lợi", "xuất khẩu tăng",
        "fdi tăng", "thặng dư", "vượt đỉnh"
    ]

    NEGATIVE_KEYWORDS = [
        "bán tháo", "thua lỗ", "sụt giảm", "áp lực tỷ giá", "tăng lãi suất", "lạm phát",
        "bán ròng", "căng thẳng", "rủi ro", "vi phạm", "xử phạt", "nợ xấu", "trái phiếu chậm trả",
        "suy thoái", "thuế quan", "phá đáy", "giải chấp", "call margin", "lao dốc"
    ]

    def __init__(self, timeout: int = 5):
        _ensure_proxy_configured()
        self.timeout = timeout

    def _fetch_url_bytes(self, url: str) -> Optional[bytes]:
        try:
            req = urllib.request.Request(
                url,
                headers={
                    "User-Agent": USER_AGENT,
                    "Accept": "application/json, application/xml, text/xml, */*",
                    "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8",
                },
                method="GET",
            )
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                return resp.read()
        except Exception as e:
            logger.debug(f"MacroClient fetch skip ({url}): {e}")
            return None

    def fetch_yahoo_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Lấy giá hiện tại và % thay đổi từ Yahoo Finance v8 chart endpoint.
        """
        encoded = urllib.parse.quote(symbol)
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{encoded}?interval=1d&range=5d"
        raw = self._fetch_url_bytes(url)
        if not raw:
            return None
        try:
            data = json.loads(raw.decode("utf-8", errors="ignore"))
            result = (data.get("chart") or {}).get("result")
            if not result or not isinstance(result, list):
                return None
            meta = result[0].get("meta") or {}
            price = meta.get("regularMarketPrice")
            prev_close = meta.get("chartPreviousClose") or meta.get("previousClose")

            # Fallback lấy từ mảng close nếu meta thiếu
            if price is None:
                quotes = (((result[0].get("indicators") or {}).get("quote") or [{}])[0]).get("close") or []
                valid_closes = [c for c in quotes if c is not None]
                if valid_closes:
                    price = valid_closes[-1]
                    if prev_close is None and len(valid_closes) >= 2:
                        prev_close = valid_closes[-2]

            if price is None:
                return None

            price = float(price)
            change = 0.0
            change_pct = 0.0
            if prev_close and float(prev_close) > 0:
                prev_val = float(prev_close)
                change = price - prev_val
                change_pct = (change / prev_val) * 100.0

            return {
                "price": round(price, 2),
                "change": round(change, 2),
                "change_pct": round(change_pct, 2),
            }
        except Exception as e:
            logger.debug(f"Yahoo parse error for {symbol}: {e}")
            return None

    def fetch_intermarket_indicators(self) -> List[Dict[str, Any]]:
        """
        Thu thập bảng chỉ số liên thị trường (DXY, US10Y, USD/VND, Brent, Gold, S&P500, Dow Jones, Nikkei).
        """
        results = []
        for item in self.INTERMARKET_SYMBOLS:
            quote = self.fetch_yahoo_quote(item["symbol"])
            if quote:
                results.append({
                    "key": item["key"],
                    "name": item["name"],
                    "category": item["category"],
                    "unit": item["unit"],
                    "price": quote["price"],
                    "change": quote["change"],
                    "change_pct": quote["change_pct"],
                    "impact_note": self._interpret_single_indicator(item["key"], quote["price"], quote["change_pct"]),
                })
        return results

    @staticmethod
    def _interpret_single_indicator(key: str, price: float, change_pct: float) -> str:
        if key == "DXY":
            if price >= 105.0 or change_pct >= 0.4:
                return "⚠️ DXY cao/tăng -> Áp lực tỷ giá & khối ngoại"
            if price <= 102.0 or change_pct <= -0.3:
                return "🟢 DXY hạ nhiệt -> Hỗ trợ tỷ giá & dòng vốn ngoại"
            return "🟡 DXY ổn định -> Tác động trung lập"
        if key == "US10Y":
            if price >= 4.4 or change_pct >= 1.5:
                return "⚠️ Lợi suất TP Mỹ căng -> Áp lực định giá cổ phiếu"
            if change_pct <= -1.0 or price < 4.0:
                return "🟢 Lợi suất hạ -> Thuận lợi cho tài sản rủi ro"
            return "🟡 Đi ngang vùng cân bằng"
        if key == "USDVND":
            if change_pct >= 0.25:
                return "⚠️ Tỷ giá tăng -> Theo dõi động thái hút ròng/SBV"
            return "🟢 Tỷ giá trong biên độ kiểm soát"
        if key == "BRENT":
            if change_pct >= 1.5:
                return "🔥 Dầu tăng mạnh -> Tích cực cho nhóm Dầu khí (PVD, PVS, BSR)"
            if change_pct <= -2.0:
                return "🟢 Dầu giảm -> Giảm áp lực chi phí vận tải/lạm phát"
            return "🟡 Giá dầu ổn định"
        if key == "GOLD":
            if change_pct >= 1.2:
                return "⚠️ Vàng tăng mạnh -> Dòng tiền phòng thủ địa chính trị"
            return "🟡 Tâm lý trú ẩn bình thường"
        if key in ("SP500", "DJI", "N225"):
            if change_pct >= 0.6:
                return "🟢 Tâm lý chứng khoán quốc tế hưng phấn"
            if change_pct <= -0.8:
                return "🔴 Chứng khoán quốc tế điều chỉnh giảm"
            return "🟡 Biến động nhẹ"
        return ""

    @classmethod
    def classify_headline_sentiment(cls, title: str) -> str:
        t = (title or "").lower()
        pos = sum(1 for k in cls.POSITIVE_KEYWORDS if k in t)
        neg = sum(1 for k in cls.NEGATIVE_KEYWORDS if k in t)
        if pos > neg:
            return "🟢 Tích cực"
        if neg > pos:
            return "🔴 Thận trọng"
        return "⚪ Thông tin"

    def _parse_rss_items(self, xml_bytes: bytes, source_label: str, max_items: int = 6) -> List[Dict[str, str]]:
        items_out = []
        try:
            root = ET.fromstring(xml_bytes)
            for item in root.findall(".//item"):
                title_el = item.find("title")
                pub_el = item.find("pubDate")
                source_el = item.find("source")
                if title_el is None or not title_el.text:
                    continue
                raw_title = html_unescape(title_el.text.strip())
                # Làm sạch đuôi "- Tên báo" của Google News nếu đã có source
                src_name = source_el.text.strip() if (source_el is not None and source_el.text) else source_label
                pub_str = pub_el.text.strip() if (pub_el is not None and pub_el.text) else ""
                if pub_str:
                    # Rút gọn ngày tháng từ chuẩn RFC822
                    pub_str = re.sub(r"\s+\d{2}:\d{2}:\d{2}.*$", "", pub_str)

                items_out.append({
                    "title": raw_title,
                    "source": src_name,
                    "published": pub_str,
                    "sentiment": self.classify_headline_sentiment(raw_title),
                })
                if len(items_out) >= max_items:
                    break
        except Exception as e:
            logger.debug(f"RSS parse error ({source_label}): {e}")
        return items_out

    def fetch_news_by_query(self, query_text: str, max_items: int = 5) -> List[Dict[str, str]]:
        """
        Tìm tin tức tài chính/vĩ mô/cổ phiếu qua Google News RSS Vietnam.
        """
        q_encoded = urllib.parse.quote(query_text)
        url = f"https://news.google.com/rss/search?q={q_encoded}&hl=vi&gl=VN&ceid=VN:vi"
        raw = self._fetch_url_bytes(url)
        if not raw:
            return []
        return self._parse_rss_items(raw, "Google News VN", max_items=max_items)

    def fetch_macro_and_stock_news(
        self,
        ticker: Optional[str] = None,
        custom_query: Optional[str] = None,
        max_macro: int = 6,
        max_specific: int = 5
    ) -> Dict[str, Any]:
        """
        Lấy tin tức Vĩ mô Kinh tế Việt Nam + Tin chuyên biệt cho Mã CP hoặc Ngành nghề được hỏi.
        """
        macro_headlines = self.fetch_news_by_query(
            "kinh tế vĩ mô Việt Nam OR Ngân hàng Nhà nước lãi suất tỷ giá OR chứng khoán VN-Index",
            max_items=max_macro
        )

        # Fallback sang CafeF RSS nếu Google News bị chặn
        if not macro_headlines:
            cafef_raw = self._fetch_url_bytes("https://cafef.vn/thi-truong-chung-khoan.rss")
            if cafef_raw:
                macro_headlines = self._parse_rss_items(cafef_raw, "CafeF", max_items=max_macro)

        specific_headlines = []
        specific_topic = None
        if ticker:
            specific_topic = f"Cổ phiếu {ticker.upper()}"
            specific_headlines = self.fetch_news_by_query(
                f"cổ phiếu {ticker.upper()} doanh thu lợi nhuận chứng khoán",
                max_items=max_specific
            )
        elif custom_query:
            specific_topic = custom_query
            specific_headlines = self.fetch_news_by_query(
                f"chứng khoán {custom_query}",
                max_items=max_specific
            )

        return {
            "macro_headlines": macro_headlines,
            "specific_topic": specific_topic,
            "specific_headlines": specific_headlines,
        }

    @classmethod
    def evaluate_macro_synthesis(
        cls,
        intermarket: List[Dict[str, Any]],
        news_data: Dict[str, Any],
        foreign_net_value: float = 0.0
    ) -> Dict[str, Any]:
        """
        Tổng hợp điểm số Vĩ mô & Liên thị trường (Macro Regime Score) và gợi ý nhóm ngành hưởng lợi.
        """
        score = 50  # Điểm trung lập
        drivers = []
        favored_sectors = []
        caution_sectors = []

        idx_map = {item["key"]: item for item in intermarket}

        # 1. Đánh giá DXY & Tỷ giá
        dxy = idx_map.get("DXY")
        if dxy:
            if dxy["price"] < 103.0 or dxy["change_pct"] <= -0.3:
                score += 10
                drivers.append(f"Chỉ số DXY ở mức thuận lợi ({dxy['price']}, {dxy['change_pct']:+.2f}%), giảm áp lực tỷ giá USD/VND.")
                favored_sectors.extend(["Chứng khoán", "Ngân hàng", "Bất động sản", "Thép"])
            elif dxy["price"] >= 105.0 or dxy["change_pct"] >= 0.45:
                score -= 10
                drivers.append(f"DXY tăng cao ({dxy['price']}, {dxy['change_pct']:+.2f}%), cần lưu ý áp lực tỷ giá ngắn hạn.")
                favored_sectors.extend(["Dệt may", "Thủy sản", "Phần mềm & DV máy tính"])  # Nhóm xuất khẩu thu USD
                caution_sectors.append("Nhóm vay nợ USD cao")

        # 2. Đánh giá Giá Dầu Brent
        brent = idx_map.get("BRENT")
        if brent:
            if brent["change_pct"] >= 1.2:
                favored_sectors.append("Dầu khí")
                drivers.append(f"Giá dầu Brent tăng tích cực ({brent['price']} USD, {brent['change_pct']:+.2f}%), hỗ trợ nhóm thượng nguồn/trung nguồn Dầu khí.")
            elif brent["change_pct"] <= -1.5:
                favored_sectors.extend(["Vận tải", "Hóa chất", "Bán lẻ"])

        # 3. Đánh giá Chứng khoán Mỹ / Quốc tế
        sp500 = idx_map.get("SP500")
        n225 = idx_map.get("N225")
        global_changes = [x["change_pct"] for x in (sp500, n225) if x is not None]
        if global_changes:
            avg_global = sum(global_changes) / len(global_changes)
            if avg_global >= 0.5:
                score += 8
                drivers.append(f"Chứng khoán quốc tế khởi sắc (TB {avg_global:+.2f}%), hỗ trợ tâm lý đầu phiên.")
            elif avg_global <= -0.8:
                score -= 8
                drivers.append(f"Chứng khoán quốc tế điều chỉnh (TB {avg_global:+.2f}%), tâm lý đầu phiên có thể thận trọng.")

        # 4. Đánh giá dòng vốn Khối ngoại trên VN-Index
        if foreign_net_value > 100:
            score += 10
            drivers.append(f"Khối ngoại mua ròng mạnh (+{foreign_net_value:,.1f} tỷ VNĐ), nâng đỡ nhóm Bluechip/VN30.")
        elif foreign_net_value < -300:
            score -= 8
            drivers.append(f"Khối ngoại bán ròng ({foreign_net_value:,.1f} tỷ VNĐ), ưu tiên các mã nội lực dòng tiền trong nước khỏe.")

        # 5. Đánh giá cảm xúc tin tức vĩ mô
        headlines = news_data.get("macro_headlines", [])
        pos_news = sum(1 for h in headlines if "Tích cực" in h.get("sentiment", ""))
        neg_news = sum(1 for h in headlines if "Thận trọng" in h.get("sentiment", ""))
        if pos_news > neg_news:
            score += 7
        elif neg_news > pos_news:
            score -= 7

        score = max(10, min(95, score))
        if score >= 65:
            regime = "🟢 VĨ MÔ THUẬN LỢI (SUPPORTIVE MACRO)"
        elif score <= 40:
            regime = "🔴 VĨ MÔ THẬN TRỌNG / ÁP LỰC LIÊN THỊ TRƯỜNG"
        else:
            regime = "🟡 VĨ MÔ TRUNG LẬP / PHÂN HÓA THEO NGÀNH"

        # Khử trùng lặp danh sách ngành
        favored_unique = list(dict.fromkeys(favored_sectors))
        if not favored_unique:
            favored_unique = ["Ngân hàng", "Công nghệ (FPT)", "Đầu tư công / Xây dựng", "BĐS Khu công nghiệp"]

        return {
            "macro_score": score,
            "macro_regime": regime,
            "drivers": drivers,
            "favored_sectors": favored_unique,
            "caution_sectors": list(dict.fromkeys(caution_sectors)),
        }


def html_unescape(text: str) -> str:
    import html
    return html.unescape(text)

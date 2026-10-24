"""
Finbox Data Client Module.
Reverse-engineered direct API client for https://dcs.finbox.vn.
No credentials or session cookies required for core market endpoints.
"""

import json
import logging
import os
import time
import urllib.request
import urllib.error
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

BASE_DCS_URL = "https://dcs.finbox.vn"
DEFAULT_TIMEOUT = int(os.environ.get("FINBOX_TIMEOUT", "15"))
HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
    "Origin": "https://www.finbox.vn",
    "Referer": "https://www.finbox.vn/",
    "Content-Type": "application/json"
}


def _ensure_proxy_configured():
    """
    Ensure corporate proxy is active if running in an intranet / corporate firewall environment (e.g. FPT)
    where direct outbound connections to port 443 are blocked and proxy env vars may have been stripped.
    """
    if any(os.getenv(k) for k in ("http_proxy", "https_proxy", "HTTP_PROXY", "HTTPS_PROXY")):
        return
    default_proxy = os.getenv("FINBOX_PROXY", "http://proxy.hcm.fpt.vn:80")
    try:
        import socket
        host = default_proxy.split("://")[-1].split(":")[0]
        port = int(default_proxy.split(":")[-1].rstrip("/"))
        with socket.create_connection((host, port), timeout=0.5):
            for var in ("http_proxy", "https_proxy", "HTTP_PROXY", "HTTPS_PROXY"):
                os.environ[var] = default_proxy
            opener = urllib.request.build_opener(
                urllib.request.ProxyHandler({"http": default_proxy, "https": default_proxy})
            )
            urllib.request.install_opener(opener)
            logger.info("Auto-configured corporate proxy for Finbox: %s", default_proxy)
    except Exception:
        pass


class FinboxClient:
    def __init__(
        self,
        base_url: str = BASE_DCS_URL,
        timeout: int = DEFAULT_TIMEOUT,
        max_retries: int = 2
    ):
        _ensure_proxy_configured()
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries

    def _execute_request(self, req: urllib.request.Request, method: str, path: str) -> Any:
        last_error = None
        for attempt in range(self.max_retries + 1):
            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as response:
                    return json.loads(response.read().decode("utf-8"))
            except Exception as e:
                last_error = e
                if attempt < self.max_retries:
                    wait_time = 1.0 * (attempt + 1)
                    logger.warning(
                        f"Finbox {method} {path} error: {e}. Retrying ({attempt + 1}/{self.max_retries}) in {wait_time}s..."
                    )
                    time.sleep(wait_time)
        logger.warning(f"Error calling Finbox {method} {path} after {self.max_retries + 1} attempts: {last_error}")
        return None

    def _post(self, path: str, payload: Dict[str, Any]) -> Any:
        url = f"{self.base_url}{path}"
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers=HEADERS, method="POST")
        return self._execute_request(req, "POST", path)

    def _get(self, path: str) -> Any:
        url = f"{self.base_url}{path}"
        req = urllib.request.Request(url, headers=HEADERS, method="GET")
        return self._execute_request(req, "GET", path)

    def get_market_overview(self) -> Dict[str, Any]:
        """
        Lấy thông tin tổng quan thị trường: xu hướng (positive, neutral, negative),
        tín hiệu mua/bán (buy, sell, ratio), khối ngoại mua ròng/bán ròng.
        """
        data = self._get("/dashboard/overview")
        return data or {}

    def get_market_indices(self) -> List[Dict[str, Any]]:
        """
        Lấy chỉ số các sàn (VNINDEX, VN30, HNX, UPCOM) kèm giá, biến động điểm, % và xu hướng.
        """
        data = self._get("/dashboard/index")
        return data if isinstance(data, list) else []

    def get_all_tickers_filter(self, date_str: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Lấy toàn bộ danh sách cổ phiếu kèm giá, khối lượng, % thay đổi, rating (A+, A, B+...) và tín hiệu Finbox.
        date_str định dạng YYYYMMDD (ví dụ 20260924). Nếu None, dùng ngày hiện tại.
        """
        if not date_str:
            date_str = datetime.now().strftime("%Y%m%d")

        payload = {
            "date": date_str,
            "values": [{"header": "category", "values": ["Cổ phiếu"]}],
            "conditions": [],
            "sort": [],
            "offset": 0,
            "count": 2000,
            "returns": [
                "ticker",
                "priceFlat",
                "pricePercent",
                "rating",
                "score",
                "trend",
                "volumeFlat",
                "volumePercent",
                "signal",
                "dip_signal",
                "dip_price",
                "tbgtdd",
                "vonhoa",
                "roe",
                "roa",
                "pe",
                "pb",
                "eps",
                "industry",
                "floor"
            ]
        }
        res = self._post("/data/filter", payload)
        if isinstance(res, dict):
            # API Finbox trả về key "symbols"
            if "symbols" in res:
                return res["symbols"]
            elif "data" in res:
                return res["data"]
        return []

    def get_ticker_detail(self, ticker: str, day: int = 0) -> Dict[str, Any]:
        """
        Lấy chi tiết cơ bản của 1 mã cổ phiếu: EPS, ROE, ROA, Nợ/VCSH, doanh thu, lợi nhuận quý, ngành.
        """
        payload = {"day": day, "ticker": ticker.upper()}
        data = self._post("/v1/getTickerDetail", payload)
        if isinstance(data, dict) and "tickerData" in data:
            raw = data["tickerData"]
            if isinstance(raw, str):
                try:
                    return json.loads(raw)
                except Exception:
                    pass
        return data or {}

    def get_symbol_signals_history(self, symbol: str) -> List[Dict[str, Any]]:
        """
        Lấy lịch sử các lệnh mua/bán gần nhất của mã từ Finbox (/kn/symbol/{symbol}/buys).
        """
        data = self._get(f"/kn/symbol/{symbol.upper()}/buys")
        return data if isinstance(data, list) else []

    def get_highlight_signals(self) -> List[Dict[str, Any]]:
        """
        Lấy danh sách các lệnh lãi cao / tín hiệu nổi bật từ Finbox (/kn/highlight).
        """
        data = self._get("/kn/highlight")
        return data if isinstance(data, list) else []

    def get_top_success_tickers(self) -> List[Dict[str, Any]]:
        """
        Lấy top cổ phiếu thành công nhất từ điểm khuyến nghị (/dashboard/success).
        """
        data = self._get("/dashboard/success")
        return data if isinstance(data, list) else []

    def filter_stocks_advanced(
        self,
        date_str: Optional[str] = None,
        ratings: Optional[List[str]] = None,
        industries: Optional[List[str]] = None,
        floors: Optional[List[str]] = None,
        trends: Optional[List[str]] = None,
        signals: Optional[List[str]] = None,
        dip_signals: Optional[List[str]] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        min_price_pct: Optional[float] = None,
        max_price_pct: Optional[float] = None,
        min_vol: Optional[float] = None,
        max_vol: Optional[float] = None,
        min_vol_pct: Optional[float] = None,
        max_vol_pct: Optional[float] = None,
        min_tbgtdd: Optional[float] = None,
        max_tbgtdd: Optional[float] = None,
        min_market_cap: Optional[float] = None,
        max_market_cap: Optional[float] = None,
        min_pe: Optional[float] = None,
        max_pe: Optional[float] = None,
        min_pb: Optional[float] = None,
        max_pb: Optional[float] = None,
        min_roe: Optional[float] = None,
        max_roe: Optional[float] = None,
        min_rsi: Optional[float] = None,
        max_rsi: Optional[float] = None,
        sort: Optional[List[Dict[str, Any]]] = None,
        offset: int = 0,
        count: int = 50,
        returns: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Bộ lọc cổ phiếu đa tiêu chí chuẩn xác theo API https://dcs.finbox.vn/data/filter.
        Hỗ trợ toàn bộ select box và tiêu chí trên màn hình signals-list.
        """
        if not date_str:
            date_str = datetime.now().strftime("%Y%m%d")

        # 1. Discrete values filter
        values = [{"header": "category", "values": ["Cổ phiếu"]}]
        if ratings:
            values.append({"header": "rating", "values": ratings})
        if industries:
            values.append({"header": "industry", "values": industries})
        if floors:
            values.append({"header": "floor", "values": floors})
        if trends:
            values.append({"header": "trend", "values": trends})
        if signals:
            values.append({"header": "signal", "values": signals})
        if dip_signals:
            values.append({"header": "dip_signal", "values": dip_signals})

        # 2. Numeric range & threshold conditions
        # Operator mapping: id=9 (range min-max), id=7 (>= singleValue), id=8 (<= singleValue)
        conditions = []

        def add_num_condition(header: str, min_val: Optional[float], max_val: Optional[float]):
            if min_val is not None and max_val is not None:
                conditions.append({
                    "header": header,
                    "id": 9,
                    "value": {"minValue": float(min_val), "maxValue": float(max_val)}
                })
            elif min_val is not None:
                conditions.append({
                    "header": header,
                    "id": 7,
                    "value": {"singleValue": float(min_val)}
                })
            elif max_val is not None:
                conditions.append({
                    "header": header,
                    "id": 8,
                    "value": {"singleValue": float(max_val)}
                })

        add_num_condition("priceFlat", min_price, max_price)
        add_num_condition("pricePercent", min_price_pct, max_price_pct)
        add_num_condition("volumeFlat", min_vol, max_vol)
        add_num_condition("volumePercent", min_vol_pct, max_vol_pct)
        add_num_condition("tbgtdd", min_tbgtdd, max_tbgtdd)
        add_num_condition("vonhoa", min_market_cap, max_market_cap)
        add_num_condition("pe", min_pe, max_pe)
        add_num_condition("pb", min_pb, max_pb)
        add_num_condition("roe", min_roe, max_roe)
        add_num_condition("rsi", min_rsi, max_rsi)

        # 3. Sort configuration
        sort_config = sort if sort is not None else [{"volumePercent": "desc"}]

        # 4. Return fields
        default_returns = [
            "ticker", "priceFlat", "pricePercent", "rating", "score", "trend",
            "volumeFlat", "volumePercent", "signal", "dip_signal", "dip_price",
            "tbgtdd", "vonhoa", "roe", "roa", "pe", "pb", "eps", "industry", "floor"
        ]
        ret_fields = returns if returns is not None else default_returns

        payload = {
            "date": date_str,
            "values": values,
            "conditions": conditions,
            "sort": sort_config,
            "offset": offset,
            "count": count,
            "returns": ret_fields
        }

        res = self._post("/data/filter", payload)
        if isinstance(res, dict):
            return {
                "total": res.get("total", 0),
                "symbols": res.get("symbols", []),
                "query_applied": {
                    "values": values,
                    "conditions": conditions,
                    "sort": sort_config
                }
            }
        return {"total": 0, "symbols": [], "query_applied": {}}

    def get_dip_buying_stocks(
        self,
        date_str: Optional[str] = None,
        only_active_signals: bool = True,
        ratings: Optional[List[str]] = None,
        industries: Optional[List[str]] = None,
        floors: Optional[List[str]] = None,
        max_rsi: Optional[float] = None,
        count: int = 50
    ) -> Dict[str, Any]:
        """
        Lấy danh sách cổ phiếu Bắt đáy từ endpoint chuyên biệt /data/dip của Finbox.
        Bao gồm các chỉ số độc quyền: RSI vùng đáy (low_rsi), RSI hiện tại, mức chiết khấu
        giá so với đỉnh 5, 10, 20, 60 phiên (discount_5, discount_10, discount_20, discount_60)
        và tín hiệu bắt đáy (SMALL DIP, BIG DIP).
        """
        if not date_str:
            date_str = datetime.now().strftime("%Y%m%d")

        values = [{"header": "category", "values": ["Cổ phiếu"]}]
        if only_active_signals:
            values.append({"header": "dip_signal", "values": ["SMALL DIP", "BIG DIP"]})
        if ratings:
            values.append({"header": "rating", "values": ratings})
        if industries:
            values.append({"header": "industry", "values": industries})
        if floors:
            values.append({"header": "floor", "values": floors})

        conditions = []
        if max_rsi is not None:
            conditions.append({
                "header": "rsi",
                "id": 8,
                "value": {"singleValue": float(max_rsi)}
            })

        returns = [
            "ticker", "priceFlat", "pricePercent", "rating", "rsi", "low_rsi",
            "dip_signal", "dip_price", "discount_5", "discount_10", "discount_20", "discount_60",
            "industry", "floor", "volumeFlat", "volumePercent", "vonhoa"
        ]

        payload = {
            "date": date_str,
            "values": values,
            "conditions": conditions,
            "sort": [{"volumePercent": "desc"}],
            "offset": 0,
            "count": count,
            "returns": returns
        }

        res = self._post("/data/dip", payload)
        if isinstance(res, dict):
            return {
                "total": res.get("total", 0),
                "symbols": res.get("symbols", []),
                "query_applied": payload
            }
        return {"total": 0, "symbols": [], "query_applied": {}}

    def get_trading_box_recommendations(self, category: str = "top") -> Dict[str, Any]:
        """
        Lấy danh mục khuyến nghị cơ sở TradingBox từ Finbox (/kn/all).
        Hỗ trợ 3 nhóm chiến lược:
        - 'top': Top Khuyến nghị (chiến lược hiệu suất cao nhất)
        - 'tc': Danh mục Tiêu chuẩn
        - 'pt': Danh mục Phổ thông
        """
        payload = {"category": category}
        res = self._post("/kn/all", payload)
        if isinstance(res, dict):
            month_data = res.get("monthData", [])
            # Lọc danh sách mã đang nắm giữ (chưa bán hoặc mới khuyến nghị)
            active_positions = []
            for m in month_data:
                td = m.get("tickerData", {})
                for sym, info_raw in td.items():
                    if isinstance(info_raw, str):
                        try:
                            info = json.loads(info_raw)
                        except Exception:
                            info = {}
                    else:
                        info = info_raw

                    # Mã chưa đóng vị thế (chưa có sellDate hoặc closed != True)
                    if not info.get("closed") and not info.get("sellDate"):
                        active_positions.append(info)

            return {
                "category": category,
                "total_months": len(month_data),
                "active_positions": active_positions,
                "latest_month_summary": month_data[0] if month_data else {}
            }
        return {"category": category, "active_positions": [], "latest_month_summary": {}}

    @staticmethod
    def parse_natural_language_query(query: str) -> Dict[str, Any]:
        """
        Trích xuất các tiêu chí kỹ thuật và cơ bản từ câu lệnh ngôn ngữ tự nhiên của người dùng.
        """
        import re
        q = query.lower()
        extracted: Dict[str, Any] = {
            "ratings": None,
            "industries": None,
            "floors": None,
            "trends": None,
            "signals": None,
            "dip_signals": None,
            "min_price": None,
            "max_price": None,
            "min_price_pct": None,
            "max_price_pct": None,
            "min_vol": None,
            "max_vol": None,
            "min_vol_pct": None,
            "max_vol_pct": None,
            "min_tbgtdd": None,
            "max_tbgtdd": None,
            "min_market_cap": None,
            "max_market_cap": None,
            "min_pe": None,
            "max_pe": None,
            "min_pb": None,
            "max_pb": None,
            "min_roe": None,
            "max_roe": None,
            "min_rsi": None,
            "max_rsi": None,
            "sort": None
        }

        # 1. Sàn giao dịch
        floors = []
        if re.search(r"\b(hose|hsx)\b", q):
            floors.append("HOSE")
        if re.search(r"\bhnx\b", q):
            floors.append("HNX")
        if re.search(r"\bupcom\b", q):
            floors.append("UPCOM")
        if floors:
            extracted["floors"] = floors

        # 2. Ngành nghề
        industries = []
        if re.search(r"ngân hàng|bank", q):
            industries.append("Ngân hàng")
        if re.search(r"bất động sản công nghiệp|bđs kcn|khu công nghiệp", q):
            industries.append("Bất động sản công nghiệp")
        elif re.search(r"bất động sản|bđs|địa ốc", q):
            industries.append("Bất động sản")
        if re.search(r"\bthép\b|kim loại", q):
            industries.append("Thép")
        if re.search(r"chứng khoán|ctck", q):
            industries.append("Chứng khoán")
        if re.search(r"dầu khí|xăng dầu", q):
            industries.append("Dầu khí")
        if re.search(r"bán lẻ|retail", q):
            industries.append("Bán lẻ")
        if re.search(r"công nghệ|cntt|phần mềm", q):
            industries.append("Phần mềm & DV máy tính")
        if re.search(r"hóa chất", q):
            industries.append("Hóa chất")
        if re.search(r"phân bón|đạm", q):
            industries.append("Phân bón")
        if re.search(r"thủy sản|tôm|cá tra", q):
            industries.append("Thủy sản")
        if re.search(r"dệt may|may mặc", q):
            industries.append("Dệt may")
        if re.search(r"vận tải|cảng biển|logistics|kho bãi", q):
            industries.append("Vận tải")
        if re.search(r"xây dựng", q):
            industries.append("Xây dựng")
        if re.search(r"vật liệu xây dựng", q):
            industries.append("Vật liệu xây dựng")
        if re.search(r"điện|năng lượng", q):
            industries.append("Điện")
        if re.search(r"dược phẩm|y tế|thuốc", q):
            industries.append("Dược phẩm")
        if industries:
            extracted["industries"] = industries

        # 3. Rating
        if re.search(r"rating\s*a\b|nhóm a|hạng a|xếp hạng a", q):
            extracted["ratings"] = ["A+", "A", "A-"]
        elif re.search(r"rating\s*a\+|hạng a\+", q):
            extracted["ratings"] = ["A+"]
        elif re.search(r"rating\s*b|nhóm b|hạng b", q):
            extracted["ratings"] = ["B+", "B", "B-"]
        elif re.search(r"tất cả rating|mọi rating", q):
            extracted["ratings"] = None

        # 4. Xu hướng
        if re.search(r"xu hướng tăng|uptrend|đang tăng", q):
            extracted["trends"] = ["TĂNG"]
        elif re.search(r"xu hướng giảm|downtrend|đang giảm", q):
            extracted["trends"] = ["GIẢM"]

        # 5. Tín hiệu Mua/Bán & Bắt đáy
        if re.search(r"bắt đáy|chiết khấu sâu|quá bán", q):
            extracted["dip_signals"] = ["SMALL DIP", "BIG DIP", "DIP"]
        elif re.search(r"tín hiệu mua|lệnh mua|\bbuy\b|mua chuẩn", q):
            extracted["signals"] = ["BUY", "BIG BUY", "SMALL BUY", "CONFIRM BUY"]
        elif re.search(r"tín hiệu bán|lệnh bán|\bsell\b", q):
            extracted["signals"] = ["BIG SELL", "SMALL SELL", "SELL"]

        # 6. Giá (priceFlat - đơn vị nghìn đồng)
        m_price_range = re.search(r"giá\s*(?:từ|trong khoảng)?\s*(\d+(?:\.\d+)?)\s*(?:đến|-|tới)\s*(\d+(?:\.\d+)?)", q)
        if m_price_range:
            extracted["min_price"] = float(m_price_range.group(1))
            extracted["max_price"] = float(m_price_range.group(2))
        else:
            m_min_p = re.search(r"giá\s*(?:trên|>|>=|tối thiểu|từ)\s*(\d+(?:\.\d+)?)", q)
            if m_min_p:
                extracted["min_price"] = float(m_min_p.group(1))
            m_max_p = re.search(r"giá\s*(?:dưới|<|<=|nhỏ hơn|tối đa)\s*(\d+(?:\.\d+)?)", q)
            if m_max_p:
                extracted["max_price"] = float(m_max_p.group(1))

        # 7. Thanh khoản / Giá trị giao dịch trung bình (tbgtdd - đơn vị tỷ VNĐ)
        m_tb = re.search(r"(?:thanh khoản|gtgd|giá trị giao dịch|giá trị)\s*(?:trên|>|>=|tối thiểu)\s*(\d+(?:\.\d+)?)\s*(?:tỷ|ty)?", q)
        if m_tb:
            extracted["min_tbgtdd"] = float(m_tb.group(1))

        # 8. Khối lượng đột biến (%Vol)
        m_vol_pct = re.search(r"(?:%vol|khối lượng|volume)\s*(?:đột biến|gấp|tăng|trên|>|>=)\s*(\d+(?:\.\d+)?)\s*(?:%|lần)?", q)
        if m_vol_pct:
            val = float(m_vol_pct.group(1))
            extracted["min_vol_pct"] = val / 100.0 if val > 20 else val
        elif re.search(r"khối lượng đột biến|vol nổ|volume nổ|đột biến khối lượng", q):
            extracted["min_vol_pct"] = 1.3  # Gấp 1.3 lần TB 20 phiên

        # 9. Định giá P/E, P/B, ROE
        m_pe = re.search(r"pe\s*(?:dưới|<|<=)\s*(\d+(?:\.\d+)?)", q)
        if m_pe:
            extracted["max_pe"] = float(m_pe.group(1))
        m_roe = re.search(r"roe\s*(?:trên|>|>=)\s*(\d+(?:\.\d+)?)\s*%?", q)
        if m_roe:
            val = float(m_roe.group(1))
            extracted["min_roe"] = val / 100.0 if val > 1 else val

        # 10. Vốn hóa (vonhoa - đơn vị tỷ VNĐ)
        m_cap = re.search(r"(?:vốn hóa|market cap)\s*(?:trên|>|>=)\s*(\d+(?:\.\d+)?)\s*(?:tỷ|ty)?", q)
        if m_cap:
            extracted["min_market_cap"] = float(m_cap.group(1))
        elif re.search(r"bluechip|vn30", q):
            extracted["min_market_cap"] = 20000.0
        elif re.search(r"midcap", q):
            extracted["min_market_cap"] = 3000.0
            extracted["max_market_cap"] = 25000.0
        elif re.search(r"penny", q):
            extracted["max_market_cap"] = 2000.0

        # 11. Sắp xếp (Sort)
        if re.search(r"thanh khoản cao nhất|gtgd cao nhất", q):
            extracted["sort"] = [{"tbgtdd": "desc"}]
        elif re.search(r"tăng mạnh nhất|tăng cao nhất|tăng tốt nhất", q):
            extracted["sort"] = [{"pricePercent": "desc"}]
        elif re.search(r"khối lượng cao nhất|vol cao nhất|vol đột biến nhất", q):
            extracted["sort"] = [{"volumePercent": "desc"}]

        return extracted

    def query_by_natural_language(
        self,
        query: str,
        date_str: Optional[str] = None,
        limit: int = 20
    ) -> Dict[str, Any]:
        """
        Nhận câu hỏi/yêu cầu bằng ngôn ngữ tự nhiên từ người dùng, tự động phân tích tiêu chí
        và gọi trực tiếp API Finbox để trả về kết quả chính xác nhất.
        """
        params = self.parse_natural_language_query(query)
        # Nếu câu hỏi về bắt đáy/chiết khấu/dip, gọi endpoint chuyên biệt /data/dip
        if params.get("dip_signals") or "bắt đáy" in query.lower() or "dip" in query.lower():
            result = self.get_dip_buying_stocks(
                date_str=date_str,
                only_active_signals=True,
                ratings=params.get("ratings"),
                industries=params.get("industries"),
                floors=params.get("floors"),
                max_rsi=params.get("max_rsi"),
                count=limit
            )
            result["is_dip_endpoint"] = True
        else:
            result = self.filter_stocks_advanced(
                date_str=date_str,
                ratings=params.get("ratings"),
                industries=params.get("industries"),
                floors=params.get("floors"),
                trends=params.get("trends"),
                signals=params.get("signals"),
                dip_signals=params.get("dip_signals"),
                min_price=params.get("min_price"),
                max_price=params.get("max_price"),
                min_price_pct=params.get("min_price_pct"),
                max_price_pct=params.get("max_price_pct"),
                min_vol=params.get("min_vol"),
                max_vol=params.get("max_vol"),
                min_vol_pct=params.get("min_vol_pct"),
                max_vol_pct=params.get("max_vol_pct"),
                min_tbgtdd=params.get("min_tbgtdd"),
                max_tbgtdd=params.get("max_tbgtdd"),
                min_market_cap=params.get("min_market_cap"),
                max_market_cap=params.get("max_market_cap"),
                min_pe=params.get("min_pe"),
                max_pe=params.get("max_pe"),
                min_pb=params.get("min_pb"),
                max_pb=params.get("max_pb"),
                min_roe=params.get("min_roe"),
                max_roe=params.get("max_roe"),
                min_rsi=params.get("min_rsi"),
                max_rsi=params.get("max_rsi"),
                sort=params.get("sort"),
                count=limit
            )
        result["natural_language_extracted"] = params
        return result

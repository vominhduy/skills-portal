---
name: vn-stock-advisor
description: "Phân tích đa tầng chứng khoán Việt Nam (4-Pillar Pro): Vĩ mô Liên thị trường (Yahoo Finance/News RSS) + Định giá Giá trị thực & 5 Trụ cột (Simplize) + Dòng tiền Cá mập Big Boys & Tâm lý Đám đông (TopInvest) + Tín hiệu Kỹ thuật Finbox DCS & Ma trận Siêu Hội Tụ 100 điểm với Kỷ luật Chặn Hòa Vốn (+5%)."
version: "2.0.0"
author: "AI Assistant"
triggers:
  - "chứng khoán"
  - "thị trường chứng khoán"
  - "cổ phiếu"
  - "phân tích cổ phiếu"
  - "điểm mua"
  - "điểm bán"
  - "cắt lỗ"
  - "chốt lời"
  - "finbox"
  - "watchlist cổ phiếu"
  - "danh mục cổ phiếu"
  - "khuyến nghị cổ phiếu"
  - "vĩ mô"
  - "simplize"
  - "topinvest"
  - "dòng tiền lớn"
  - "cá mập"
---

# Kỹ năng Phân tích Thị trường Chứng khoán Việt Nam Đa Tầng (4-Pillar Pro Edition)

Kỹ năng chuyên sâu hỗ trợ Nhà đầu tư và Chuyên viên phân tích thị trường chứng khoán Việt Nam (HOSE, HNX, UPCOM). Kỹ năng kết hợp sức mạnh từ 4 trụ cột định lượng độc lập:
1. **Toàn cảnh Vĩ mô Liên thị trường & Tin tức**: DXY, Lợi suất US10Y, Tỷ giá USD/VND, Dầu Brent, Vàng, Chứng khoán Quốc tế (Yahoo Finance) và Điểm tin tài chính (Google News VN / CafeF).
2. **Định giá Giá trị Thực & Sức khỏe Tài chính 5 Trụ cột (Mô hình Simplize Snowflake)**: P/E, P/B điều chỉnh theo ROE so với Trung vị Ngành, ước tính Fair Value và Biên an toàn (Margin of Safety %).
3. **Dòng tiền Thông minh & Tâm lý Đám đông (Triết lý TopInvest 'Follow the Bigboys')**: Bóc tách dấu chân Cá mập gom hàng / gom ngầm nền giá / kéo xả phân phối đỉnh, Chỉ số Tâm lý Đám đông (Crowd Sentiment 0-100), Radar Luân chuyển Dòng tiền Ngành.
4. **Hệ thống Tín hiệu Finbox DCS & Ma trận Siêu Hội Tụ 4 Lớp (Confluence Score 0-100 điểm)**: Kỷ luật quản trị rủi ro bất bại với Quy tắc Chặn Hòa Vốn (+5% Breakeven Trigger) và Chốt lời 3 nấc.

---

## 1. Năng Lực Cốt Lõi

1. **Tổng quan thị trường & Độ rộng dòng tiền**:
   - Thống kê tỷ lệ mã Tăng / Giảm / Tham chiếu toàn thị trường.
   - Thống kê cán cân dòng tiền Khối Ngoại (Mua ròng / Bán ròng).
   - Tỷ lệ tín hiệu Mua / Bán của hệ thống Finbox (`ratio`).
   - Diễn biến các chỉ số sàn (`VNINDEX`, `VN30`, `HNX`, `UPCOM`).

2. **Khuyến nghị Điểm Mua / Điểm Bán chuẩn xác**:
   - **Vùng mua (Entry Zone)**: Quanh giá hiện tại hoặc điểm breakout/pullback (-1.5% đến +1.5%).
   - **Cắt lỗ (Stop Loss)**: Ngưỡng rủi ro nghiêm ngặt -5% đến -7% (hoặc dưới hỗ trợ cứng).
   - **Mục tiêu 1 (Target 1)**: +8% đến +10% (Chốt lời chủ động 50% để bảo toàn vốn).
   - **Mục tiêu 2 (Target 2)**: +18% đến +25% (Sóng tăng trung hạn).
   - **Tỷ lệ R:R (Risk/Reward)**: Tối thiểu 1.5:1 đến 2:1 mới kích hoạt khuyến nghị Mua mới.

3. **Lọc cổ phiếu tiềm năng (Top Picks)**:
   - Sàng lọc theo tiêu chuẩn Finbox Rating cao (`A+`, `A`, `B+`).
   - Lọc thanh khoản an toàn: Giá trị giao dịch trung bình 20 phiên (`tbgtdd`) $\ge$ 3 tỷ VNĐ/phiên.
   - Bắt tín hiệu bùng nổ khối lượng (`%Vol vs 20N` $\ge 120\%$) hoặc tín hiệu `BIG BUY`, `PULLBACK`.

4. **Theo dõi Danh mục Đầu tư (Portfolio / Watchlist)**:
   - Tính toán lãi/lỗ theo thời gian thực (Unrealized PnL).
   - Cảnh báo tức thì khi cổ phiếu vi phạm ngưỡng cắt lỗ (Stop Loss Triggered) hoặc chạm mục tiêu (Target Hit).
   - Đưa ra lời khuyên cụ thể cho từng vị thế: Nắm giữ (Hold), Nâng trailing stop, Chốt lời từng phần, hoặc Cắt lỗ khẩn cấp.

---

## 2. Hướng Dẫn Sử Dụng

### 2.1. Chạy CLI Runner

Script runner chính nằm tại: `skills/vn-stock-advisor/scripts/run_stock_advisor.py`

#### A. Phân tích tổng quan thị trường & Top cổ phiếu tiềm năng:
```bash
python3 skills/vn-stock-advisor/scripts/run_stock_advisor.py
```

#### B. Phân tích chuyên sâu 1 mã cổ phiếu (Kèm điểm mua/bán, EPS, ROE, Nợ/VCSH, lịch sử lệnh):
```bash
python3 skills/vn-stock-advisor/scripts/run_stock_advisor.py --ticker FPT
```

#### C. Lọc cổ phiếu chỉ có tín hiệu Mua hoặc Vol bùng nổ:
```bash
python3 skills/vn-stock-advisor/scripts/run_stock_advisor.py --only-signals --min-rating A
```

#### D. Theo dõi danh mục đầu tư thực tế:
```bash
python3 skills/vn-stock-advisor/scripts/run_stock_advisor.py --watchlist '[{"symbol":"FPT","buy_price":64.0,"quantity":1000,"buy_date":"2026-09-01"},{"symbol":"SSI","buy_price":32.5,"quantity":2000,"buy_date":"2026-09-10"}]'
```

#### E. Lọc cổ phiếu theo Ngôn Ngữ Tự Nhiên (Natural Language Query):
```bash
# Lọc ngành, sàn, rating, thanh khoản và giá:
python3 skills/vn-stock-advisor/scripts/run_stock_advisor.py --query "tìm cổ phiếu ngân hàng sàn HOSE rating A giá trên 20 thanh khoản trên 10 tỷ"

# Lọc cổ phiếu bắt đáy hoặc tích lũy:
python3 skills/vn-stock-advisor/scripts/run_stock_advisor.py --query "các mã thép đang có tín hiệu bắt đáy dip mua"

# Lọc định giá cơ bản (P/E, ROE):
python3 skills/vn-stock-advisor/scripts/run_stock_advisor.py --query "cổ phiếu bluechip ROE trên 15% PE dưới 15"
```

---

## 3. Đặc Tả Toàn Diện API Bộ Lọc Finbox (DCS Filter API Specification)

Toàn bộ các select box và thanh trượt trên màn hình `https://www.finbox.vn/signals-list` được ánh xạ về endpoint:
- **URL**: `POST https://dcs.finbox.vn/data/filter`
- **Headers**: `Content-Type: application/json` (Không cần Token/Auth)

### 3.1. Cấu trúc Payload

```json
{
  "date": "20260408",
  "values": [
    {"header": "category", "value": ["Cổ phiếu"]},
    {"header": "industry", "value": ["Ngân hàng", "Thép", "Bất động sản"]},
    {"header": "rating", "value": ["A+", "A", "A-", "B+"]},
    {"header": "floor", "value": ["HOSE", "HNX", "UPCOM"]},
    {"header": "trend", "value": ["TĂNG", "GIẢM", "TRUNG LẬP"]},
    {"header": "signal", "value": ["BUY", "BIG BUY", "SMALL BUY", "BIG SELL", "SMALL SELL"]},
    {"header": "dip_signal", "value": ["SMALL DIP", "BIG DIP", "DIP"]}
  ],
  "conditions": [
    {
      "header": "priceFlat",
      "id": 9,
      "value": {"minValue": 20.0, "maxValue": 50.0}
    },
    {
      "header": "tbgtdd",
      "id": 7,
      "value": {"singleValue": 10.0}
    },
    {
      "header": "pe",
      "id": 8,
      "value": {"singleValue": 15.0}
    }
  ],
  "sort": [{"volumePercent": "desc"}, {"tbgtdd": "desc"}],
  "returns": ["ticker", "priceFlat", "pricePercent", "rating", "score", "trend", "volumeFlat", "volumePercent", "signal", "dip_signal", "dip_price", "tbgtdd", "vonhoa", "roe", "roa", "pe", "pb", "eps", "industry", "floor"],
  "limit": 50
}
```

### 3.2. Bảng Mã Operator IDs cho `conditions` (Numeric Filters)
- **`id = 9` (Range/Between)**: Yêu cầu object `value: {"minValue": X, "maxValue": Y}`
- **`id = 7` (Greater than or equal $\ge$)**: Yêu cầu object `value: {"singleValue": X}`
- **`id = 8` (Less than or equal $\le$)**: Yêu cầu object `value: {"singleValue": X}`

Các trường số học hỗ trợ: `priceFlat`, `pricePercent`, `volumeFlat`, `volumePercent`, `tbgtdd` (tỷ VNĐ), `vonhoa` (tỷ VNĐ), `pe`, `pb`, `roe`, `roa`, `eps`.

### 3.3. Endpoint Chuyên Biệt Bắt Đáy (Dip Buying API)
- **URL**: `POST https://dcs.finbox.vn/data/dip`
- **Mục đích**: Lọc các cổ phiếu rơi vào trạng thái quá bán, chiết khấu sâu từ đỉnh và có tín hiệu tạo đáy kỹ thuật.
- **Trường dữ liệu độc quyền**:
  - `low_rsi`: Chỉ số RSI thấp nhất ghi nhận tại vùng đáy.
  - `rsi`: Chỉ số RSI hiện tại.
  - `dip_signal`: Tín hiệu bắt đáy (`SMALL DIP`, `BIG DIP`).
  - `dip_price`: Mức giá xuất hiện tín hiệu bắt đáy.
  - `discount_5`, `discount_10`, `discount_20`, `discount_60`: Mức chiết khấu giá (%) so với mức đỉnh 5, 10, 20 và 60 phiên gần nhất.
- **Cách gọi qua CLI**:
  ```bash
  python3 skills/vn-stock-advisor/scripts/run_stock_advisor.py --dip
  # hoặc qua ngôn ngữ tự nhiên:
  python3 skills/vn-stock-advisor/scripts/run_stock_advisor.py --query "các mã có tín hiệu bắt đáy hôm nay"
  ```

### 3.4. Cơ Chế Tín Hiệu Sớm: Pre-Buy & Pre-Sell (Chờ Mua / Chờ Bán)
- **Bản chất**:
  - `CHỜ MUA` (`PRE BUY`) và `CHỜ BÁN` (`PRE SELL`) là các **tín hiệu cảnh báo sớm trong phiên (Intraday Realtime Early Signals)**.
  - Được kích hoạt khi giá tiệm cận ngưỡng Breakout mua hoặc gãy hỗ trợ bán trước khi phiên đóng cửa hoặc trước khi đạt đủ khối lượng xác nhận.
- **Vòng đời tín hiệu (Lifecycle)**:
  - Trong phiên: Hiển thị `CHỜ MUA` / `CHỜ BÁN` trong tab Tín hiệu cơ sở (TradingBox) và thông báo đẩy Realtime (`/notifications/list` trên `api2.finbox.vn`).
  - Hết phiên (EOD): Khi điều kiện khối lượng & giá đóng cửa được xác nhận đầy đủ, hệ thống chuyển thành tín hiệu chính thức: `BUY`, `BIG BUY`, `SMALL BUY` hoặc `SELL`, `BIG SELL`, `SMALL SELL`. Nếu không đạt, tín hiệu tự hủy.
- **Danh mục khuyến nghị cơ sở TradingBox (`/kn/all`)**:
  - `top`: Top Khuyến nghị (chiến lược tỷ suất sinh lời tối ưu nhất).
  - `tc`: Danh mục Tiêu chuẩn.
  - `pt`: Danh mục Phổ thông.

---

## 4. Đầu Ra & Phản Hồi Tin Nhắn (Output Contract)

- **KHÔNG tạo hay xuất file `.md`** (không ghi file báo cáo ra đĩa và không gọi tool `Write` tạo file `.md`).
- Script `run_stock_advisor.py` in trực tiếp toàn bộ dữ liệu phân tích và bảng chỉ số ra `stdout`.
- Sau khi chạy script, AI tổng hợp và trình bày trực tiếp báo cáo phân tích rõ ràng, đầy đủ ngay trong tin nhắn chat phản hồi cho người dùng.

---

## 5. Cấu Trúc Mã Nguồn

- `finbox_client.py`: API Client kết nối trực tiếp `https://dcs.finbox.vn` (Dashboard, Index, Ticker Detail, History, Highlighting).
- `signal_engine.py`: Động cơ tính toán điểm mua, điểm bán, vùng dừng lỗ, mục tiêu chốt lời và tỷ lệ R:R.
- `portfolio_tracker.py`: Quản lý danh mục, tính PnL và phát hiện cảnh báo rủi ro vị thế.
- `run_stock_advisor.py`: Script điều phối chính, nhận CLI arguments và in kết quả phân tích ra `stdout` để tổng hợp trực tiếp trong tin nhắn chat.

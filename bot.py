import requests
import time

# ================= CONFIG =================
BOT_TOKEN = "8741088698:AAEBTaXYMVGevB7tLz4oTaCKpPXAoe9E7j4"
CHAT_ID = "1674106249"
BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

CHECK_INTERVAL = 60
REQUEST_DELAY = 1
OI_REFRESH_INTERVAL = 300  # 5 min

# ================= SYMBOLS =================
INDEX_SYMBOLS = {
    "NIFTY": "%5ENSEI",
    "BANK": "%5ENSEBANK",
    "IT": "%5ECNXIT",
    "PHARMA": "%5ECNXPHARMA",
    "AUTO": "%5ECNXAUTO"
}

SECTOR_STOCKS = {
    "IT": ["INFY.NS", "TCS.NS", "WIPRO.NS"],
    "BANK": ["ICICIBANK.NS", "HDFCBANK.NS", "SBIN.NS"],
    "AUTO": ["TATAMOTORS.NS", "M&M.NS", "MARUTI.NS"],
    "PHARMA": ["SUNPHARMA.NS", "DRREDDY.NS", "CIPLA.NS"]
}

# ================= STATE =================
price_history = {}
STARTED = False
cached_oi_bias = None
last_oi_fetch = 0

# ================= TELEGRAM =================
def send_alert(msg):
    try:
        requests.post(f"{BASE_URL}/sendMessage", json={
            "chat_id": CHAT_ID,
            "text": msg
        })
    except:
        pass

# ================= PRICE FETCH =================
def get_price(symbol):
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
        response = requests.get(url, timeout=5)

        if response.status_code != 200 or not response.text.strip():
            return None, None

        data = response.json()
        result = data.get('chart', {}).get('result')
        if not result:
            return None, None

        meta = result[0]['meta']
        price = meta.get('regularMarketPrice') or meta.get('chartPreviousClose')
        prev = meta.get('previousClose')

        if price is None or prev is None:
            return None, None

        change = ((price - prev) / prev) * 100
        return price, round(change, 2)

    except:
        return None, None

# ================= NSE OI =================
def fetch_nse_oi():
    try:
        session = requests.Session()

        headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept-Language": "en-US,en;q=0.9",
        }

        session.get("https://www.nseindia.com", headers=headers)

        url = "https://www.nseindia.com/api/option-chain-indices?symbol=NIFTY"
        res = session.get(url, headers=headers).json()

        data = res.get("records", {}).get("data", [])

        total_call_oi = 0
        total_put_oi = 0

        for strike in data:
            ce = strike.get("CE")
            pe = strike.get("PE")

            if ce:
                total_call_oi += ce.get("openInterest", 0)
            if pe:
                total_put_oi += pe.get("openInterest", 0)

        if total_put_oi > total_call_oi:
            return "BULLISH"
        elif total_call_oi > total_put_oi:
            return "BEARISH"

        return "NEUTRAL"

    except Exception as e:
        print("OI Error:", e)
        return None

# ================= LOGIC =================
def classify(diff):
    if diff > 0.5:
        return "STRONG"
    elif diff < -0.5:
        return "WEAK"
    return "NEUTRAL"

def market_trend(nifty):
    if nifty > 0.3:
        return "BULLISH"
    elif nifty < -0.3:
        return "BEARISH"
    return "SIDEWAYS"

def momentum(name, price):
    if name not in price_history:
        price_history[name] = []

    price_history[name].append(price)

    if len(price_history[name]) > 5:
        price_history[name].pop(0)

    if len(price_history[name]) < 5:
        return None

    r = price_history[name]

    if r[-1] > max(r[:-1]):
        return "UP"
    elif r[-1] < min(r[:-1]):
        return "DOWN"

    return "SIDEWAYS"

# ================= MAIN =================
def run():
    global STARTED, cached_oi_bias, last_oi_fetch

    if not STARTED:
        send_alert("🧠 ELITE + OI Trading System Started")
        STARTED = True

    while True:
        try:
            data = {}
            prices = {}

            # ===== FETCH INDEX =====
            for name, symbol in INDEX_SYMBOLS.items():
                price, change = get_price(symbol)
                time.sleep(REQUEST_DELAY)

                if price is not None:
                    data[name] = change
                    prices[name] = price

            if not data or "NIFTY" not in data:
                time.sleep(10)
                continue

            nifty = data["NIFTY"]
            trend = market_trend(nifty)

            # ===== FETCH OI (cached) =====
            if time.time() - last_oi_fetch > OI_REFRESH_INTERVAL:
                cached_oi_bias = fetch_nse_oi()
                last_oi_fetch = time.time()
                print("OI Bias:", cached_oi_bias)

            # ===== FIND BEST SECTOR =====
            best_sector = None
            best_diff = -999

            for sector in data:
                if sector == "NIFTY":
                    continue

                diff = data[sector] - nifty

                if diff > best_diff:
                    best_diff = diff
                    best_sector = sector

            if best_sector not in SECTOR_STOCKS:
                time.sleep(CHECK_INTERVAL)
                continue

            # ===== SCAN STOCKS =====
            best_stock = None
            best_score = -999

            for stock in SECTOR_STOCKS[best_sector]:
                price, change = get_price(stock)
                time.sleep(REQUEST_DELAY)

                if price is None:
                    continue

                m = momentum(stock, price)

                score = 0
                if change > 0.5:
                    score += 1
                if m == "UP":
                    score += 1

                if score > best_score:
                    best_score = score
                    best_stock = (stock, price, change, m)

            if not best_stock:
                time.sleep(CHECK_INTERVAL)
                continue

            stock, price, change, m = best_stock

            # ===== FINAL FILTER (WITH OI) =====
            if (
                best_diff > 0.5 and
                m == "UP" and
                trend != "BEARISH" and
                cached_oi_bias != "BEARISH"
            ):

                msg = f"""
🔥 ELITE TRADE

Sector: {best_sector}
Stock: {stock}
Signal: BUY

Market: {trend}
OI Bias: {cached_oi_bias}

Price: {price}

Reason:
- Sector leader
- Momentum breakout
- OI support

Confidence: HIGH
"""
                send_alert(msg)

            time.sleep(CHECK_INTERVAL)

        except Exception as e:
            print("ERROR:", e)
            time.sleep(10)

# ================= RUN =================
if __name__ == "__main__":
    run()

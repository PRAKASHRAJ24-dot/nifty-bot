import requests
import time

# ================= CONFIG =================
BOT_TOKEN = "8741088698:AAEBTaXYMVGevB7tLz4oTaCKpPXAoe9E7j4"
CHAT_ID = "1674106249"
BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

CHECK_INTERVAL = 60
REQUEST_DELAY = 1  # prevent rate limit

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

price_history = {}
STARTED = False

# ================= TELEGRAM =================
def send_alert(msg):
    try:
        requests.post(f"{BASE_URL}/sendMessage", json={
            "chat_id": CHAT_ID,
            "text": msg
        })
    except Exception as e:
        print("Telegram Error:", e)

# ================= SAFE FETCH =================
def get_price(symbol):
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
        response = requests.get(url, timeout=5)

        # check response validity
        if response.status_code != 200 or not response.text.strip():
            print(f"⚠️ Empty response for {symbol}")
            return None, None

        data = response.json()

        result = data.get('chart', {}).get('result')
        if not result:
            print(f"⚠️ No result for {symbol}")
            return None, None

        meta = result[0].get('meta', {})

        price = meta.get('regularMarketPrice')
        prev = meta.get('previousClose')

        if price is None:
            price = meta.get('chartPreviousClose')

        if price is None or prev is None:
            print(f"⚠️ Missing data for {symbol}")
            return None, None

        change = ((price - prev) / prev) * 100
        return price, round(change, 2)

    except Exception as e:
        print(f"🔥 Data Error ({symbol}):", e)
        return None, None

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
    global STARTED

    if not STARTED:
        send_alert("🧠 ELITE Trading System Started")
        STARTED = True

    while True:
        try:
            data = {}
            prices = {}

            # ===== FETCH INDEX DATA =====
            for name, symbol in INDEX_SYMBOLS.items():
                price, change = get_price(symbol)
                time.sleep(REQUEST_DELAY)

                if price is not None:
                    data[name] = change
                    prices[name] = price

            print("DEBUG:", data)

            # ===== SAFETY CHECK =====
            if not data:
                print("⚠️ No data fetched, retrying...")
                time.sleep(10)
                continue

            if "NIFTY" not in data:
                time.sleep(10)
                continue

            nifty = data["NIFTY"]
            trend = market_trend(nifty)

            # ===== MARKET CLOSED =====
            if all(v == 0 for v in data.values()):
                send_alert("⏸️ Market closed / no movement")
                time.sleep(300)
                continue

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

            # ===== FINAL FILTER =====
            if best_diff > 0.5 and m == "UP" and trend != "BEARISH":

                msg = f"""
🔥 ELITE TRADE

Sector: {best_sector}
Stock: {stock}
Signal: BUY

Market: {trend}

Price: {price}

Reason:
- Sector leader
- Strong momentum
- Market aligned

Confidence: HIGH
"""

                send_alert(msg)

            time.sleep(CHECK_INTERVAL)

        except Exception as e:
            print("🔥 MAIN ERROR:", e)
            time.sleep(10)

# ================= RUN =================
if __name__ == "__main__":
    run()

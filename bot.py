import requests
import time

# ================= CONFIG =================
BOT_TOKEN = "8741088698:AAEBTaXYMVGevB7tLz4oTaCKpPXAoe9E7j4"
CHAT_ID = "1674106249"
BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

CHECK_INTERVAL = 60

# ================= SYMBOLS =================
SYMBOLS = {
    "NIFTY": "%5ENSEI",
    "BANK": "%5ENSEBANK",
    "IT": "%5ECNXIT",
    "PHARMA": "%5ECNXPHARMA",
    "FMCG": "%5ECNXFMCG",
    "AUTO": "%5ECNXAUTO"
}

# ================= STATE =================
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

# ================= DATA =================
def get_price(symbol):
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
        res = requests.get(url, timeout=5).json()

        result = res.get('chart', {}).get('result')
        if not result:
            return None, None

        meta = result[0].get('meta', {})
        price = meta.get('regularMarketPrice')
        prev = meta.get('previousClose')

        if price is None:
            price = meta.get('chartPreviousClose')

        if price is None or prev is None:
            return None, None

        change = ((price - prev) / prev) * 100
        return price, round(change, 2)

    except Exception as e:
        print("Data Error:", e)
        return None, None

# ================= MARKET TREND =================
def get_market_trend(nifty_change):
    if nifty_change > 0.3:
        return "BULLISH"
    elif nifty_change < -0.3:
        return "BEARISH"
    return "SIDEWAYS"

# ================= CLASSIFY =================
def classify(diff):
    if diff > 0.5:
        return "STRONG"
    elif diff < -0.5:
        return "WEAK"
    return "NEUTRAL"

# ================= MOMENTUM =================
def detect_momentum(name, price):
    if name not in price_history:
        price_history[name] = []

    price_history[name].append(price)

    if len(price_history[name]) > 5:
        price_history[name].pop(0)

    if len(price_history[name]) < 5:
        return None

    recent = price_history[name]

    if recent[-1] > max(recent[:-1]):
        return "UP"
    elif recent[-1] < min(recent[:-1]):
        return "DOWN"

    return "SIDEWAYS"

# ================= MAIN =================
def run():
    global STARTED

    if not STARTED:
        send_alert("🧠 PRO Trading Brain Started")
        STARTED = True

    while True:
        try:
            data = {}
            prices = {}

            # ===== Fetch Data =====
            for name, symbol in SYMBOLS.items():
                price, change = get_price(symbol)

                if price is not None:
                    data[name] = change
                    prices[name] = price

            print("DEBUG:", data)

            if "NIFTY" not in data:
                time.sleep(10)
                continue

            nifty = data["NIFTY"]
            market_trend = get_market_trend(nifty)

            # ===== Market Closed Detection =====
            if all(v == 0 for v in data.values()):
                send_alert("⏸️ Market closed / no movement")
                time.sleep(300)
                continue

            signals = []

            # ===== SIGNAL ENGINE =====
            for sector in data:
                if sector == "NIFTY":
                    continue

                diff = data[sector] - nifty
                state = classify(diff)

                momentum = detect_momentum(sector, prices[sector])

                # ===== BUY CONDITION =====
                if (
                    state == "STRONG" and
                    momentum == "UP" and
                    market_trend != "BEARISH"
                ):
                    signals.append((sector, "BUY", prices[sector], state, momentum))

                # ===== SELL CONDITION =====
                elif (
                    state == "WEAK" and
                    momentum == "DOWN" and
                    market_trend != "BULLISH"
                ):
                    signals.append((sector, "SELL", prices[sector], state, momentum))

            # ===== SEND SIGNALS =====
            for s in signals:
                sector, signal, price, state, momentum = s

                msg = f"""
🚀 TRADE SETUP

Sector: {sector}
Signal: {signal}
Market: {market_trend}

Price: {price}

Analysis:
- Sector: {state}
- Momentum: {momentum}

Target: {round(price * 1.01, 2)}
SL: {round(price * 0.995, 2)}
"""

                send_alert(msg)

            time.sleep(CHECK_INTERVAL)

        except Exception as e:
            print("🔥 MAIN ERROR:", e)
            time.sleep(10)

# ================= RUN =================
if __name__ == "__main__":
    run()

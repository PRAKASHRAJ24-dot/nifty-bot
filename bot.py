import requests
import time

# ================= CONFIG =================
BOT_TOKEN = "8741088698:AAEBTaXYMVGevB7tLz4oTaCKpPXAoe9E7j4"
CHAT_ID = "1674106249"
BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

CHECK_INTERVAL = 60

SYMBOLS = {
    "NIFTY": "%5ENSEI",
    "BANK": "%5ENSEBANK",
    "IT": "%5ECNXIT",
    "PHARMA": "%5ECNXPHARMA",
    "FMCG": "%5ECNXFMCG",
    "AUTO": "%5ECNXAUTO"
}

previous_states = {}
price_history = {}

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
            return None

        meta = result[0]['meta']

        price = meta.get('regularMarketPrice')
        prev = meta.get('previousClose')

        if price is None:
            price = meta.get('chartPreviousClose')

        if price is None or prev is None:
            return None

        change = ((price - prev) / prev) * 100
        return price, round(change, 2)

    except:
        return None, None

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
    send_alert("🔥 Smart Trading Bot Started")

    while True:
        try:
            data = {}
            prices = {}

            # ===== Fetch =====
            for name, symbol in SYMBOLS.items():
                price, change = get_price(symbol)

                if price is not None:
                    data[name] = change
                    prices[name] = price

            if "NIFTY" not in data:
                time.sleep(10)
                continue

            nifty = data["NIFTY"]

            signals = []

            for sector in data:
                if sector == "NIFTY":
                    continue

                diff = data[sector] - nifty
                state = classify(diff)

                momentum = detect_momentum(sector, prices[sector])

                # ================= SIGNAL =================
                if state == "STRONG" and momentum == "UP":
                    signals.append((sector, "BUY", prices[sector]))

                elif state == "WEAK" and momentum == "DOWN":
                    signals.append((sector, "SELL", prices[sector]))

            # ===== Send signals =====
            for s in signals:
                sector, signal, price = s

                msg = f"""
🚀 TRADE SETUP

Sector: {sector}
Signal: {signal}

Price: {price}

Reason:
- Sector {('outperforming' if signal=='BUY' else 'underperforming')} NIFTY
- Momentum confirmed

Target: {round(price * 1.01, 2)}
SL: {round(price * 0.995, 2)}
"""

                send_alert(msg)

            time.sleep(CHECK_INTERVAL)

        except Exception as e:
            print("Error:", e)
            time.sleep(10)

# ================= RUN =================
if __name__ == "__main__":
    run()

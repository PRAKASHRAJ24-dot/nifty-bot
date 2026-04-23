import requests
import time
from datetime import datetime

# ================== CONFIG ==================
BOT_TOKEN = "8741088698:AAEBTaXYMVGevB7tLz4oTaCKpPXAoe9E7j4"
CHAT_ID = "1674106249"

BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

last_signal = None


# ================== TELEGRAM ==================
def send_alert(msg):
    try:
        requests.post(f"{BASE_URL}/sendMessage", json={
            "chat_id": CHAT_ID,
            "text": msg
        })
    except Exception as e:
        print("Telegram error:", e)


# ================== FETCH CANDLES ==================
def fetch_candles():
    url = "https://query1.finance.yahoo.com/v8/finance/chart/%5ENSEI?interval=5m&range=1d"
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        res = requests.get(url, headers=headers, timeout=10)
        data = res.json()["chart"]["result"][0]

        close = data["indicators"]["quote"][0]["close"]
        high = data["indicators"]["quote"][0]["high"]
        low = data["indicators"]["quote"][0]["low"]

        # clean None
        candles = []
        for i in range(len(close)):
            if close[i] and high[i] and low[i]:
                candles.append({
                    "close": close[i],
                    "high": high[i],
                    "low": low[i]
                })

        return candles[-10:]  # last 10 candles

    except Exception as e:
        print("Fetch error:", e)
        return []


# ================== STRIKE ==================
def get_atm(price):
    return round(price / 50) * 50


# ================== VWAP STYLE BIAS ==================
def get_bias(candles):
    closes = [c["close"] for c in candles]
    avg = sum(closes) / len(closes)

    current = closes[-1]

    if current > avg:
        return "BULLISH"
    else:
        return "BEARISH"


# ================== SIGNAL ENGINE ==================
def generate_signal():
    global last_signal

    candles = fetch_candles()

    if len(candles) < 6:
        return

    last = candles[-1]
    prev = candles[-2]
    prev2 = candles[-3]

    highs = [c["high"] for c in candles[:-1]]
    lows = [c["low"] for c in candles[:-1]]

    current_price = last["close"]
    atm = get_atm(current_price)

    bias = get_bias(candles)

    # ================== BREAKOUT ==================

    # 📈 Bullish breakout
    if last["high"] > max(highs) and bias == "BULLISH" and last_signal != "CALL":
        last_signal = "CALL"

        msg = f"""🚀 CALL BREAKOUT

Index: {current_price}
Strike: {atm} CE

Bias: {bias}

Entry: {round(current_price,1)}
SL: {round(current_price - 40,1)}
Target: {round(current_price + 100,1)}

Reason: High breakout + trend support
Time: {datetime.now().strftime('%H:%M:%S')}
"""
        send_alert(msg)

    # 📉 Bearish breakdown
    elif last["low"] < min(lows) and bias == "BEARISH" and last_signal != "PUT":
        last_signal = "PUT"

        msg = f"""🔻 PUT BREAKDOWN

Index: {current_price}
Strike: {atm} PE

Bias: {bias}

Entry: {round(current_price,1)}
SL: {round(current_price + 40,1)}
Target: {round(current_price - 100,1)}

Reason: Low breakdown + trend support
Time: {datetime.now().strftime('%H:%M:%S')}
"""
        send_alert(msg)

    # ================== MOMENTUM ==================

    # 📈 Uptrend continuation
    elif prev2["close"] < prev["close"] < last["close"] and bias == "BULLISH" and last_signal != "CALL":
        last_signal = "CALL"

        msg = f"""📈 CALL MOMENTUM

Index: {current_price}
Strike: {atm} CE

Entry: {round(current_price,1)}
SL: {round(current_price - 30,1)}
Target: {round(current_price + 80,1)}

Reason: 3 candle bullish momentum
Time: {datetime.now().strftime('%H:%M:%S')}
"""
        send_alert(msg)

    # 📉 Downtrend continuation
    elif prev2["close"] > prev["close"] > last["close"] and bias == "BEARISH" and last_signal != "PUT":
        last_signal = "PUT"

        msg = f"""📉 PUT MOMENTUM

Index: {current_price}
Strike: {atm} PE

Entry: {round(current_price,1)}
SL: {round(current_price + 30,1)}
Target: {round(current_price - 80,1)}

Reason: 3 candle bearish momentum
Time: {datetime.now().strftime('%H:%M:%S')}
"""
        send_alert(msg)


# ================== MAIN ==================
if __name__ == "__main__":
    send_alert("🔥 ULTIMATE BOT STARTED")

    while True:
        try:
            generate_signal()
            time.sleep(60)

        except Exception as e:
            print("Loop error:", e)
            time.sleep(10)

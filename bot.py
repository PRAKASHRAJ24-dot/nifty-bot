import requests
import time
from datetime import datetime
import os

# ================= ENV VARIABLES =================
BOT_TOKEN = os.getenv("8741088698:AAEBTaXYMVGevB7tLz4oTaCKpPXAoe9E7j4")
CHAT_ID = os.getenv("1674106249")

BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

# ================= SEND ALERT =================
def send_alert(msg):
    url = f"{BASE_URL}/sendMessage"
    requests.post(url, json={
        "chat_id": CHAT_ID,
        "text": msg
    })

# ================= FETCH DATA =================
def fetch_data():
    url = "https://corsproxy.io/?https://www.nseindia.com/api/option-chain-indices?symbol=NIFTY"
    headers = {"User-Agent": "Mozilla/5.0"}
    return requests.get(url, headers=headers).json()

# ================= ANALYSIS =================
def analyze():
    data = fetch_data()
    records = data["records"]["data"]
    spot = data["records"]["underlyingValue"]

    atm = round(spot / 50) * 50

    call_chg = 0
    put_chg = 0

    for r in records:
        if "CE" in r and "PE" in r:
            strike = r["strikePrice"]

            # Focus ATM ± 2 strikes
            if abs(strike - atm) <= 100:
                call_chg += r["CE"]["changeinOpenInterest"]
                put_chg += r["PE"]["changeinOpenInterest"]

    return spot, call_chg, put_chg, atm

# ================= TREND =================
def get_trend(call_chg, put_chg):
    if call_chg > 5000 and put_chg < -2000:
        return "BEARISH"
    elif put_chg > 5000 and call_chg < -2000:
        return "BULLISH"
    else:
        return "SIDEWAYS"

# ================= MAIN LOOP =================
last_price = None
last_signal = None

while True:
    try:
        now = datetime.now()
        current_time = now.strftime("%H:%M")

        # ⛔ TIME FILTER
        if current_time < "09:20" or current_time > "15:10":
            time.sleep(30)
            continue

        spot, call_chg, put_chg, atm = analyze()
        trend = get_trend(call_chg, put_chg)

        signal = None

        # ⛔ SIDEWAYS FILTER
        if trend == "SIDEWAYS":
            print("No trade zone")
            time.sleep(20)
            continue

        if last_price:
            move = spot - last_price

            # 🔴 BREAKDOWN
            if trend == "BEARISH" and move < -15:
                signal = f"""🔴 BREAKDOWN SELL

Spot: {spot}
Trend: Bearish

👉 BUY {atm} PE
"""

            # 🟢 BREAKOUT
            elif trend == "BULLISH" and move > 15:
                signal = f"""🟢 BREAKOUT BUY

Spot: {spot}
Trend: Bullish

👉 BUY {atm} CE
"""

            # ⚡ PULLBACK
            elif abs(move) < 5:
                if trend == "BULLISH":
                    signal = f"""🟢 PULLBACK BUY

Spot: {spot}

👉 BUY {atm} CE
"""
                elif trend == "BEARISH":
                    signal = f"""🔴 PULLBACK SELL

Spot: {spot}

👉 BUY {atm} PE
"""

        # 🚀 SEND ALERT
        if signal and signal != last_signal:
            send_alert(signal)
            last_signal = signal

        last_price = spot

        time.sleep(20)

    except Exception as e:
        print("Error:", e)
        time.sleep(10)
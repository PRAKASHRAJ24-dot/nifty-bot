import requests
import time
from datetime import datetime

# ================== TELEGRAM CONFIG ==================
BOT_TOKEN = "8741088698:AAEBTaXYMVGevB7tLz4oTaCKpPXAoe9E7j4"
CHAT_ID = "1674106249"

BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

def send_alert(msg):
    try:
        url = f"{BASE_URL}/sendMessage"
        requests.post(url, json={
            "chat_id": CHAT_ID,
            "text": msg
        }, timeout=5)
    except Exception as e:
        print("Telegram error:", e)


# ================== FETCH NIFTY (YAHOO SAFE) ==================
def fetch_price():
    try:
        url = "https://query1.finance.yahoo.com/v8/finance/chart/%5ENSEI"

        headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json"
        }

        res = requests.get(url, headers=headers, timeout=5)

        # ✅ check empty response (fix your error)
        if not res.text:
            print("Empty response from Yahoo")
            return None

        data = res.json()

        # ✅ safe parsing
        if "chart" not in data or data["chart"]["result"] is None:
            print("Invalid Yahoo response:", data)
            return None

        price = data["chart"]["result"][0]["meta"]["regularMarketPrice"]
        return float(price)

    except Exception as e:
        print("Fetch error:", e)
        return None


# ================== SIGNAL LOGIC ==================
prices = []
last_signal = None

def check_signal(price):
    global last_signal

    prices.append(price)

    # keep only last 3
    if len(prices) > 3:
        prices.pop(0)

    if len(prices) < 3:
        return

    p1, p2, p3 = prices

    # 📈 CALL
    if p1 < p2 < p3 and last_signal != "CALL":
        strike = round(p3 / 50) * 50

        msg = f"""📈 CALL SIGNAL
Strike: {strike} CE
Entry: {p3}
SL: {p3 - 20}
Target: {p3 + 40}"""

        send_alert(msg)
        last_signal = "CALL"

    # 📉 PUT
    elif p1 > p2 > p3 and last_signal != "PUT":
        strike = round(p3 / 50) * 50

        msg = f"""📉 PUT SIGNAL
Strike: {strike} PE
Entry: {p3}
SL: {p3 + 20}
Target: {p3 - 40}"""

        send_alert(msg)
        last_signal = "PUT"


# ================== MAIN LOOP ==================
last_price = None

send_alert("🔥 ULTIMATE BOT STARTED")

while True:
    try:
        price = fetch_price()

        if price is None:
            time.sleep(15)
            continue

        # avoid duplicate spam
        if price == last_price:
            time.sleep(15)
            continue

        last_price = price

        print("NIFTY:", price)

        now = datetime.now().strftime("%H:%M:%S")

        send_alert(f"""📊 NIFTY LIVE
LTP: {price}
Time: {now}""")

        check_signal(price)

        time.sleep(20)  # ✅ safer delay for Yahoo

    except Exception as e:
        print("Main loop error:", e)
        time.sleep(10)

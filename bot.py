import requests
import time
from datetime import datetime

# ================== TELEGRAM CONFIG ==================
BOT_TOKEN = "8741088698:AAEBTaXYMVGevB7tLz4oTaCKpPXAoe9E7j4"
CHAT_ID = "1674106249"

BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

def send_alert(msg):
    url = f"{BASE_URL}/sendMessage"
    requests.post(url, json={
        "chat_id": CHAT_ID,
        "text": msg
    })

# ================== FETCH NIFTY (YAHOO) ==================
def fetch_price():
    try:
        url = "https://query1.finance.yahoo.com/v8/finance/chart/%5ENSEI"
        res = requests.get(url, timeout=5)
        data = res.json()

        price = data["chart"]["result"][0]["meta"]["regularMarketPrice"]
        return float(price)

    except Exception as e:
        print("Fetch error:", e)
        return None

# ================== SIGNAL LOGIC ==================
prices = []
last_signal = None  # prevent duplicate signals

def check_signal(price):
    global last_signal

    prices.append(price)

    # keep only last 3 prices
    if len(prices) > 3:
        prices.pop(0)

    if len(prices) < 3:
        return

    p1, p2, p3 = prices

    # 📈 CALL (Bullish momentum)
    if p1 < p2 < p3 and last_signal != "CALL":
        strike = round(p3 / 50) * 50

        msg = f"""📈 CALL SIGNAL
Strike: {strike} CE
Entry: {p3}
SL: {p3 - 20}
Target: {p3 + 40}"""

        send_alert(msg)
        last_signal = "CALL"

    # 📉 PUT (Bearish momentum)
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
            time.sleep(10)
            continue

        # avoid duplicate same price spam
        if price == last_price:
            time.sleep(10)
            continue

        last_price = price

        print("NIFTY:", price)

        # send live update
        now = datetime.now().strftime("%H:%M:%S")
        send_alert(f"📊 NIFTY LIVE\nLTP: {price}\nTime: {now}")

        # check signal
        check_signal(price)

        time.sleep(15)

    except Exception as e:
        print("Error:", e)
        time.sleep(10)

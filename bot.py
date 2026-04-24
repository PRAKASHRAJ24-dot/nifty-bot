import requests
import time

BOT_TOKEN = "8741088698:AAEBTaXYMVGevB7tLz4oTaCKpPXAoe9E7j4"
CHAT_ID = "1674106249"
BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

last_signal = None
last_time = 0

def send_alert(msg):
    requests.post(f"{BASE_URL}/sendMessage", json={
        "chat_id": CHAT_ID,
        "text": msg
    })

def get_price():
    try:
        url = "https://query1.finance.yahoo.com/v8/finance/chart/%5ENSEI"
        return requests.get(url).json()['chart']['result'][0]['meta']['regularMarketPrice']
    except:
        return None

# 🔴 MOCK (replace with API later)
def get_oi():
    return {
        "put_oi_change": 5000,
        "call_oi_change": 2000,
        "put_price_change": 10,
        "price_up": False
    }

def detect_trend(price, prev):
    if prev is None:
        return None
    return "UP" if price > prev else "DOWN"

def check_signal(price, prev_price):
    global last_signal, last_time

    if prev_price is None:
        return

    trend = detect_trend(price, prev_price)
    oi = get_oi()

    RESISTANCE = 23960
    SUPPORT = 23920

    now = time.time()
    if now - last_time < 300:
        return

    # 📉 PUT
    if (
        trend == "DOWN"
        and price < RESISTANCE
        and oi["put_oi_change"] > 0
        and oi["put_price_change"] > 0
    ):
        signal = "PUT"

        if signal != last_signal:
            msg = f"""📉 PUT SIGNAL
Strike: 23900 PE
Entry: {price}
SL: {price + 40}
Target: {price - 80}"""

            send_alert(msg)
            last_signal = signal
            last_time = now

    # 📈 CALL
    elif (
        trend == "UP"
        and price > RESISTANCE
        and oi["call_oi_change"] < 0
    ):
        signal = "CALL"

        if signal != last_signal:
            msg = f"""📈 CALL SIGNAL
Strike: 24000 CE
Entry: {price}
SL: {price - 40}
Target: {price + 80}"""

            send_alert(msg)
            last_signal = signal
            last_time = now


send_alert("🔥 PRO BOT STARTED")

prev_price = None

while True:
    price = get_price()

    if price:
        check_signal(price, prev_price)
        prev_price = price

    time.sleep(10)

import requests
import time
from datetime import datetime

# ================= CONFIG =================
BOT_TOKEN = "8741088698:AAEBTaXYMVGevB7tLz4oTaCKpPXAoe9E7j4"
CHAT_ID = "1674106249"

BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

# ================= SEND ALERT =================
def send_alert(msg):
    url = f"{BASE_URL}/sendMessage"
    requests.post(url, json={
        "chat_id": CHAT_ID,
        "text": msg
    })

# ================= FETCH PRICE =================
def get_price():
    try:
        url = "https://query1.finance.yahoo.com/v8/finance/chart/%5ENSEI"
        res = requests.get(url, timeout=5).json()
        return res['chart']['result'][0]['meta']['regularMarketPrice']
    except Exception as e:
        print("Fetch error:", e)
        return None

# ================= GLOBAL =================
last_signal = None
last_signal_time = 0
COOLDOWN = 300  # 5 minutes

# ================= SIGNAL LOGIC =================
def check_signal(price, prev_price):
    global last_signal, last_signal_time

    if prev_price is None:
        return

    now = time.time()

    # cooldown protection
    if now - last_signal_time < COOLDOWN:
        return

    # ================= LEVELS =================
    RESISTANCE = 23960
    SUPPORT = 23920

    # ================= BREAKOUT CALL =================
    if price > RESISTANCE and prev_price <= RESISTANCE:
        signal = "CALL_BREAKOUT"

        if signal != last_signal:
            msg = f"""📈 CALL SIGNAL
Strike: 24000 CE
Entry: {price}
SL: {price - 40}
Target: {price + 80}"""

            send_alert(msg)
            last_signal = signal
            last_signal_time = now

    # ================= REJECTION PUT =================
    elif price < RESISTANCE and prev_price > RESISTANCE:
        signal = "PUT_REJECTION"

        if signal != last_signal:
            msg = f"""📉 PUT SIGNAL
Strike: 23900 PE
Entry: {price}
SL: {price + 40}
Target: {price - 80}"""

            send_alert(msg)
            last_signal = signal
            last_signal_time = now


# ================= MAIN LOOP =================
send_alert("🔥 BOT STARTED (SMART MODE)")

prev_price = None

while True:
    price = get_price()

    if price:
        check_signal(price, prev_price)
        prev_price = price

    time.sleep(10)

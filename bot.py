import requests
import time

# ================= CONFIG =================
BOT_TOKEN = "8741088698:AAEBTaXYMVGevB7tLz4oTaCKpPXAoe9E7j4"
CHAT_ID = "1674106249"
BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

# ================= GLOBAL =================
last_signal = None
last_signal_time = 0
COOLDOWN = 300  # 5 min

# ================= TELEGRAM =================
def send_alert(msg):
    requests.post(f"{BASE_URL}/sendMessage", json={
        "chat_id": CHAT_ID,
        "text": msg
    })

# ================= PRICE =================
def get_price():
    try:
        url = "https://query1.finance.yahoo.com/v8/finance/chart/%5ENSEI"
        res = requests.get(url).json()
        return res['chart']['result'][0]['meta']['regularMarketPrice']
    except:
        return None

# ================= MOCK OI (REPLACE LATER) =================
def get_oi_data():
    return {
        "price_change": -10,
        "oi_change": 5000
    }

# ================= OI TYPE =================
def detect_oi_type(data):
    price_change = data["price_change"]
    oi_change = data["oi_change"]

    if price_change > 0 and oi_change > 0:
        return "LONG_BUILDUP"

    elif price_change < 0 and oi_change > 0:
        return "SHORT_BUILDUP"

    elif price_change > 0 and oi_change < 0:
        return "SHORT_COVERING"

    elif price_change < 0 and oi_change < 0:
        return "LONG_UNWINDING"

    return None

# ================= SIGNAL LOGIC =================
def check_signal(price, prev_price):
    global last_signal, last_signal_time

    if prev_price is None:
        return

    now = time.time()
    if now - last_signal_time < COOLDOWN:
        return

    # Levels (adjust as per market)
    RESISTANCE = 23960
    SUPPORT = 23920

    # OI type
    oi_data = get_oi_data()
    oi_type = detect_oi_type(oi_data)

    # ================= PUT LOGIC =================
    if (
        oi_type == "SHORT_BUILDUP"
        and price < RESISTANCE
        and prev_price > price
    ):
        signal = "PUT"

        if signal != last_signal:
            msg = f"""📉 PUT SIGNAL
OI: SHORT BUILDUP
Entry: {price}
SL: {price + 40}
Target: {price - 80}"""

            send_alert(msg)
            last_signal = signal
            last_signal_time = now

    # ================= CALL LOGIC =================
    elif (
        oi_type == "LONG_BUILDUP"
        and price > RESISTANCE
        and prev_price < price
    ):
        signal = "CALL"

        if signal != last_signal:
            msg = f"""📈 CALL SIGNAL
OI: LONG BUILDUP
Entry: {price}
SL: {price - 40}
Target: {price + 80}"""

            send_alert(msg)
            last_signal = signal
            last_signal_time = now

# ================= MAIN =================
send_alert("🔥 OI BOT STARTED")

prev_price = None

while True:
    price = get_price()

    if price:
        check_signal(price, prev_price)
        prev_price = price

    time.sleep(10)

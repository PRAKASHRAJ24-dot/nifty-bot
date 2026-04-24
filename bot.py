import requests
import time

# ================= CONFIG =================
BOT_TOKEN = "8741088698:AAEBTaXYMVGevB7tLz4oTaCKpPXAoe9E7j4"
CHAT_ID = "1674106249"
BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

# ================= GLOBAL =================
price_history = []
MAX_HISTORY = 30

last_signal = None
last_signal_time = 0
COOLDOWN = 300

swing_high = None
swing_low = None

trend = None  # UP / DOWN

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

# ================= MOCK OI =================
def get_oi_data():
    return {
        "price_change": -10,
        "oi_change": 5000
    }

def detect_oi_type(data):
    pc = data["price_change"]
    oi = data["oi_change"]

    if pc > 0 and oi > 0:
        return "LONG_BUILDUP"
    elif pc < 0 and oi > 0:
        return "SHORT_BUILDUP"
    elif pc > 0 and oi < 0:
        return "SHORT_COVERING"
    elif pc < 0 and oi < 0:
        return "LONG_UNWINDING"
    return None

# ================= SWING DETECTION =================
def detect_swings():
    global swing_high, swing_low

    if len(price_history) < 5:
        return

    for i in range(2, len(price_history) - 2):
        p = price_history[i]

        if p > price_history[i-1] and p > price_history[i+1]:
            swing_high = p

        if p < price_history[i-1] and p < price_history[i+1]:
            swing_low = p

# ================= UPDATE =================
def update_price(price):
    price_history.append(price)

    if len(price_history) > MAX_HISTORY:
        price_history.pop(0)

    detect_swings()

# ================= SIGNAL =================
def check_signal(price):
    global last_signal, last_signal_time, trend

    if swing_high is None or swing_low is None:
        return

    now = time.time()
    if now - last_signal_time < COOLDOWN:
        return

    oi_type = detect_oi_type(get_oi_data())

    # ================= CHOCH DETECTION =================

    # Bullish CHOCH (trend reversal)
    if trend == "DOWN" and price > swing_high:
        trend = "UP"

        send_alert(f"""🔄 CHOCH (BULLISH)
Trend Change Detected

Price: {price}""")

    # Bearish CHOCH
    elif trend == "UP" and price < swing_low:
        trend = "DOWN"

        send_alert(f"""🔄 CHOCH (BEARISH)
Trend Change Detected

Price: {price}""")

    # ================= BOS =================

    # 📈 Bullish BOS
    elif price > swing_high and oi_type == "LONG_BUILDUP":
        trend = "UP"
        signal = "CALL"

        if signal != last_signal:
            msg = f"""📈 CALL SIGNAL (BOS)
Trend: UP

Entry: {price}
SL: {swing_low}
Target: {price + 80}"""

            send_alert(msg)
            last_signal = signal
            last_signal_time = now

    # 📉 Bearish BOS
    elif price < swing_low and oi_type == "SHORT_BUILDUP":
        trend = "DOWN"
        signal = "PUT"

        if signal != last_signal:
            msg = f"""📉 PUT SIGNAL (BOS)
Trend: DOWN

Entry: {price}
SL: {swing_high}
Target: {price - 80}"""

            send_alert(msg)
            last_signal = signal
            last_signal_time = now

# ================= MAIN =================
send_alert("🔥 BOS + CHOCH BOT STARTED")

while True:
    price = get_price()

    if price:
        update_price(price)
        check_signal(price)

    time.sleep(10)

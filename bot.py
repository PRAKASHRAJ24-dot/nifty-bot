import requests
import time

# ================= CONFIG =================
BOT_TOKEN = "8741088698:AAEBTaXYMVGevB7tLz4oTaCKpPXAoe9E7j4"
CHAT_ID = "1674106249"
BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

# ================= GLOBAL =================
price_history = []
MAX_HISTORY = 30

last_signal_time = 0
COOLDOWN = 300

swing_high = None
swing_low = None
trend = None

# ================= LEVELS =================
SUPPORT = 24060
RESISTANCE = 24150

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

# ================= OI MOCK =================
def get_oi_data():
    return {
        "price_change": 10,
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

# ================= PRICE UPDATE =================
def update_price(price):
    price_history.append(price)
    if len(price_history) > MAX_HISTORY:
        price_history.pop(0)

# ================= SWING DETECTION =================
def detect_swings():
    global swing_high, swing_low

    if len(price_history) < 5:
        return

    for i in range(2, len(price_history)-2):
        p = price_history[i]

        if p > price_history[i-1] and p > price_history[i+1]:
            swing_high = p

        if p < price_history[i-1] and p < price_history[i+1]:
            swing_low = p

# ================= STRUCTURE =================
def detect_structure(price):
    global trend

    if swing_high is None or swing_low is None:
        return None

    # CHOCH
    if trend == "DOWN" and price > swing_high:
        trend = "UP"
        return "CHOCH_BULLISH"

    elif trend == "UP" and price < swing_low:
        trend = "DOWN"
        return "CHOCH_BEARISH"

    # BOS
    if price > swing_high:
        trend = "UP"
        return "BOS_BULLISH"

    elif price < swing_low:
        trend = "DOWN"
        return "BOS_BEARISH"

    return None

# ================= SIGNAL =================
def check_signal(price):
    global last_signal_time

    now = time.time()
    if now - last_signal_time < COOLDOWN:
        return

    detect_swings()
    structure = detect_structure(price)
    oi_type = detect_oi_type(get_oi_data())

    # ❌ Avoid sideways
    if SUPPORT < price < RESISTANCE:
        return

    # ================= CALL =================
    if (
        structure in ["BOS_BULLISH", "CHOCH_BULLISH"] and
        oi_type in ["LONG_BUILDUP", "SHORT_COVERING"] and
        price > RESISTANCE
    ):
        msg = f"""📈 CALL SIGNAL

Structure: {structure}
OI: {oi_type}

Entry: {price}
SL: {SUPPORT}
Target: {price + 100}"""

        send_alert(msg)
        last_signal_time = now

    # ================= PUT =================
    elif (
        structure in ["BOS_BEARISH", "CHOCH_BEARISH"] and
        oi_type in ["SHORT_BUILDUP", "LONG_UNWINDING"] and
        price < SUPPORT
    ):
        msg = f"""📉 PUT SIGNAL

Structure: {structure}
OI: {oi_type}

Entry: {price}
SL: {RESISTANCE}
Target: {price - 100}"""

        send_alert(msg)
        last_signal_time = now

# ================= MAIN =================
send_alert("🔥 ULTIMATE BOT STARTED")

while True:
    price = get_price()

    if price:
        update_price(price)
        check_signal(price)

    time.sleep(10)

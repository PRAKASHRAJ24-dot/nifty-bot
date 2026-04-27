import requests
import time

# ================= CONFIG =================
BOT_TOKEN = "8741088698:AAEBTaXYMVGevB7tLz4oTaCKpPXAoe9E7j4"
CHAT_ID = "1674106249"
BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

CHECK_INTERVAL = 60
OI_REFRESH = 120
COOLDOWN = 300

last_signal_time = 0

# ================= TELEGRAM =================
def send_alert(msg):
    try:
        requests.post(f"{BASE_URL}/sendMessage", json={
            "chat_id": CHAT_ID,
            "text": msg
        })
    except:
        pass

# ================= PRICE =================
def get_price():
    try:
        url = "https://query1.finance.yahoo.com/v8/finance/chart/%5ENSEI"
        res = requests.get(url, timeout=5).json()
        meta = res['chart']['result'][0]['meta']
        return meta.get('regularMarketPrice') or meta.get('chartPreviousClose')
    except:
        return None

# ================= NSE OI =================
session = requests.Session()
headers = {"User-Agent": "Mozilla/5.0"}

def get_oi():
    try:
        session.get("https://www.nseindia.com", headers=headers)
        url = "https://www.nseindia.com/api/option-chain-indices?symbol=NIFTY"
        res = session.get(url, headers=headers).json()
        return res["records"]["data"]
    except:
        return None

# ================= GLOBAL =================
price_history = []
prev_strike_oi = {}

# ================= EXTRACT =================
def extract_strikes(data):
    strikes = []

    for d in data:
        strike = d.get("strikePrice")
        ce = d.get("CE", {})
        pe = d.get("PE", {})

        strikes.append({
            "strike": strike,
            "call_oi": ce.get("openInterest", 0),
            "put_oi": pe.get("openInterest", 0)
        })

    return strikes

# ================= FIND LEVELS =================
def find_levels(strikes):
    max_call = max(strikes, key=lambda x: x["call_oi"])
    max_put = max(strikes, key=lambda x: x["put_oi"])

    return max_call["strike"], max_put["strike"]

# ================= OI SHIFT =================
def oi_shift(strikes):
    global prev_strike_oi

    shift_signal = []

    for s in strikes:
        strike = s["strike"]
        call = s["call_oi"]
        put = s["put_oi"]

        prev = prev_strike_oi.get(strike, {"call": call, "put": put})

        call_change = call - prev["call"]
        put_change = put - prev["put"]

        if call_change > 0:
            shift_signal.append(("CALL_BUILD", strike))

        if put_change > 0:
            shift_signal.append(("PUT_BUILD", strike))

        prev_strike_oi[strike] = {"call": call, "put": put}

    return shift_signal

# ================= BREAKOUT =================
def detect_breakout(price):
    price_history.append(price)

    if len(price_history) > 15:
        price_history.pop(0)

    if len(price_history) < 6:
        return None

    high = max(price_history[:-1])
    low = min(price_history[:-1])

    if price > high:
        return "UP"
    elif price < low:
        return "DOWN"

    return None

# ================= MAIN =================
def run():
    global last_signal_time

    send_alert("🚀 STRIKE-LEVEL OI SYSTEM STARTED")

    last_oi_time = 0
    resistance = None
    support = None

    while True:
        try:
            price = get_price()

            if not price:
                time.sleep(10)
                continue

            breakout = detect_breakout(price)

            # ===== FETCH OI =====
            if time.time() - last_oi_time > OI_REFRESH:
                raw = get_oi()
                if raw:
                    strikes = extract_strikes(raw)

                    resistance, support = find_levels(strikes)
                    shifts = oi_shift(strikes)

                    print("Resistance:", resistance, "Support:", support)
                    print("OI Shifts:", shifts)

                    last_oi_time = time.time()

            print(f"Price: {price} | Breakout: {breakout}")

            now = time.time()
            if now - last_signal_time < COOLDOWN:
                time.sleep(CHECK_INTERVAL)
                continue

            # ===== BUY =====
            if breakout == "UP" and price > resistance:
                send_alert(f"""
🚀 BUY BREAKOUT

Price: {price}
Resistance: {resistance}
Support: {support}

Reason:
- Resistance broken
- Call wall cleared
- Upside open
""")
                last_signal_time = now

            # ===== SELL =====
            elif breakout == "DOWN" and price < support:
                send_alert(f"""
📉 SELL BREAKDOWN

Price: {price}
Resistance: {resistance}
Support: {support}

Reason:
- Support broken
- Put wall failed
- Downside open
""")
                last_signal_time = now

            time.sleep(CHECK_INTERVAL)

        except Exception as e:
            print("ERROR:", e)
            time.sleep(10)

# ================= RUN =================
if __name__ == "__main__":
    run()

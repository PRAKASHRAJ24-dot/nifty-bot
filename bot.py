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
        res = requests.get(url).json()
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
confirm_buffer = []

# ================= STRIKE LEVELS =================
def get_levels(data):
    strikes = []

    for d in data:
        ce = d.get("CE", {})
        pe = d.get("PE", {})

        strikes.append({
            "strike": d["strikePrice"],
            "call": ce.get("openInterest", 0),
            "put": pe.get("openInterest", 0)
        })

    resistance = max(strikes, key=lambda x: x["call"])["strike"]
    support = max(strikes, key=lambda x: x["put"])["strike"]

    return resistance, support

# ================= BREAKOUT =================
def breakout(price):
    price_history.append(price)

    if len(price_history) > 10:
        price_history.pop(0)

    if len(price_history) < 5:
        return None

    high = max(price_history[:-1])
    low = min(price_history[:-1])

    if price > high:
        return "UP"
    elif price < low:
        return "DOWN"

    return None

# ================= CONFIRMATION =================
def confirm_breakout(price, level, direction):
    confirm_buffer.append(price)

    if len(confirm_buffer) > 3:
        confirm_buffer.pop(0)

    if len(confirm_buffer) < 3:
        return False

    if direction == "UP":
        return all(p > level for p in confirm_buffer)

    if direction == "DOWN":
        return all(p < level for p in confirm_buffer)

    return False

# ================= MAIN =================
def run():
    global last_signal_time

    send_alert("🔥 FINAL PRO TRADING SYSTEM STARTED")

    last_oi_time = 0
    resistance = None
    support = None

    while True:
        try:
            price = get_price()

            if not price:
                time.sleep(10)
                continue

            move = breakout(price)

            # ===== FETCH OI =====
            if time.time() - last_oi_time > OI_REFRESH:
                raw = get_oi()
                if raw:
                    resistance, support = get_levels(raw)
                    print("R:", resistance, "S:", support)
                    last_oi_time = time.time()

            print(f"Price: {price} | Move: {move}")

            now = time.time()
            if now - last_signal_time < COOLDOWN:
                time.sleep(CHECK_INTERVAL)
                continue

            # ===== BUY =====
            if move == "UP" and resistance:
                if confirm_breakout(price, resistance, "UP"):

                    entry = price
                    sl = resistance - 20
                    target = entry + 60

                    send_alert(f"""
🚀 CONFIRMED BUY

Entry: {entry}
SL: {sl}
Target: {target}

Reason:
- Resistance broken
- Sustained above level
- Real breakout (not trap)
""")

                    last_signal_time = now

            # ===== SELL =====
            if move == "DOWN" and support:
                if confirm_breakout(price, support, "DOWN"):

                    entry = price
                    sl = support + 20
                    target = entry - 60

                    send_alert(f"""
📉 CONFIRMED SELL

Entry: {entry}
SL: {sl}
Target: {target}

Reason:
- Support broken
- Sustained below level
- Real breakdown
""")

                    last_signal_time = now

            time.sleep(CHECK_INTERVAL)

        except Exception as e:
            print("ERROR:", e)
            time.sleep(10)

# ================= RUN =================
if __name__ == "__main__":
    run()

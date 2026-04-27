import requests
import time

# ================= CONFIG =================
BOT_TOKEN = "8741088698:AAEBTaXYMVGevB7tLz4oTaCKpPXAoe9E7j4"
CHAT_ID = "1674106249"
BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

CHECK_INTERVAL = 60  # seconds

# ================= SYMBOLS =================
SYMBOLS = {
    "NIFTY": "%5ENSEI",
    "BANK": "%5ENSEBANK",
    "IT": "%5ECNXIT",
    "PHARMA": "%5ECNXPHARMA",
    "FMCG": "%5ECNXFMCG",
    "AUTO": "%5ECNXAUTO"
}

# ================= STATE =================
previous_states = {}

# ================= TELEGRAM =================
def send_alert(msg):
    try:
        requests.post(f"{BASE_URL}/sendMessage", json={
            "chat_id": CHAT_ID,
            "text": msg
        })
    except Exception as e:
        print("Telegram Error:", e)

# ================= FETCH =================
def get_data(symbol):
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
        res = requests.get(url).json()
        meta = res['chart']['result'][0]['meta']

        price = meta['regularMarketPrice']
        prev = meta['previousClose']

        return round(((price - prev) / prev) * 100, 2)

    except:
        return None

# ================= CLASSIFY =================
def classify(diff):
    if diff > 0.5:
        return "STRONG"
    elif diff < -0.5:
        return "WEAK"
    else:
        return "NEUTRAL"

# ================= MAIN =================
def run():
    print("🚀 Smart Sector Scanner Started")
    send_alert("🔥 Smart Sector Scanner Started")

    while True:
        data = {}

        for name, symbol in SYMBOLS.items():
            val = get_data(symbol)
            if val is not None:
                data[name] = val

        if "NIFTY" not in data:
            time.sleep(10)
            continue

        nifty = data["NIFTY"]

        sector_scores = []

        for sector in data:
            if sector == "NIFTY":
                continue

            diff = data[sector] - nifty
            state = classify(diff)

            sector_scores.append((sector, data[sector], diff, state))

        # ================= SORT (Ranking) =================
        sector_scores.sort(key=lambda x: x[2], reverse=True)

        # ================= BUILD MESSAGE =================
        msg = f"📊 Sector Rotation (Ranked)\nNIFTY: {nifty}%\n\n"

        for s in sector_scores:
            msg += f"{s[0]}: {s[1]}% ({s[3]})\n"

        print(msg)

        # ================= ALERT ONLY ON CHANGE =================
        alerts = []

        for sector, change, diff, state in sector_scores:
            prev = previous_states.get(sector)

            if prev and prev != state:
                alerts.append(f"{sector}: {prev} → {state}")

            previous_states[sector] = state

        # ================= SEND ALERT =================
        if alerts:
            alert_msg = "🚨 Rotation Shift Detected\n\n" + "\n".join(alerts)
            send_alert(alert_msg)

        time.sleep(CHECK_INTERVAL)

# ================= RUN =================
if __name__ == "__main__":
    run()

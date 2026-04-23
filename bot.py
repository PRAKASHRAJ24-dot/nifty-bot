import requests
import time
from datetime import datetime

# ================== CONFIG ==================
BOT_TOKEN = "8741088698:AAEBTaXYMVGevB7tLz4oTaCKpPXAoe9E7j4"
CHAT_ID = "1674106249"

BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

# ================== SEND ALERT ==================
def send_alert(msg):
    url = f"{BASE_URL}/sendMessage"
    try:
        res = requests.post(url, json={
            "chat_id": CHAT_ID,
            "text": msg
        })
        print("Telegram:", res.text)
    except Exception as e:
        print("Send error:", e)

# ================== FETCH DATA (FIXED NSE) ==================
def fetch_data():
    url = "https://www.nseindia.com/api/option-chain-indices?symbol=NIFTY"

    session = requests.Session()

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br"
    }

    try:
        # Step 1: get cookies (IMPORTANT)
        session.get("https://www.nseindia.com", headers=headers)

        # Step 2: fetch actual data
        response = session.get(url, headers=headers)

        return response.json()

    except Exception as e:
        print("Fetch error:", e)
        return {}

# ================== LOGIC ==================
def check_signal():
    data = fetch_data()

    # SAFE CHECK (prevents crash)
    if "records" not in data:
        print("❌ Invalid NSE response:", data)
        return

    underlying = data["records"]["underlyingValue"]

    msg = f"📊 NIFTY Update\nLTP: {underlying}\nTime: {datetime.now().strftime('%H:%M:%S')}"
    send_alert(msg)

# ================== MAIN ==================
if __name__ == "__main__":
    send_alert("🔥 BOT STARTED SUCCESSFULLY")

    while True:
        try:
            check_signal()
            time.sleep(60)  # every 1 minute

        except Exception as e:
            print("Loop error:", e)
            send_alert(f"⚠️ ERROR: {e}")
            time.sleep(10)

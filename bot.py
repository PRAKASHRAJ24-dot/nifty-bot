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

# ================== FETCH DATA (PROXY FIX) ==================
def fetch_data():
    url = "https://api.allorigins.win/raw?url=https://www.nseindia.com/api/option-chain-indices?symbol=NIFTY"

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        return response.json()
    except Exception as e:
        print("Fetch error:", e)
        return {}

# ================== LOGIC ==================
def check_signal():
    data = fetch_data()

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
            time.sleep(60)

        except Exception as e:
            print("Loop error:", e)
            send_alert(f"⚠️ ERROR: {e}")
            time.sleep(10)

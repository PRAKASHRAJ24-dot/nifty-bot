import requests
import time
from datetime import datetime

# ================== CONFIG ==================
BOT_TOKEN = "8741088698:AAEBTaXYMVGevB7tLz4oTaCKpPXAoe9E7j4"
CHAT_ID = "1674106249"

BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

# ================== TELEGRAM ==================
def send_alert(msg):
    try:
        url = f"{BASE_URL}/sendMessage"
        res = requests.post(url, json={
            "chat_id": CHAT_ID,
            "text": msg
        })
        print("Telegram:", res.text)
    except Exception as e:
        print("Telegram Error:", e)


# ================== FETCH DATA ==================
def fetch_data():
    url = "https://query1.finance.yahoo.com/v8/finance/chart/%5ENSEI"

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    try:
        res = requests.get(url, headers=headers, timeout=10)

        if res.status_code != 200:
            print("Bad status:", res.status_code)
            return None

        data = res.json()

        result = data.get("chart", {}).get("result")

        if not result:
            print("No result in response")
            return None

        price = result[0]["meta"]["regularMarketPrice"]

        return price

    except Exception as e:
        print("Fetch error:", e)
        return None


# ================== LOGIC ==================
def check_signal():
    price = fetch_data()

    if price is None:
        print("⚠️ Skipping this cycle")
        return

    msg = f"""📊 NIFTY LIVE
LTP: {price}
Time: {datetime.now().strftime('%H:%M:%S')}
"""
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
            time.sleep(10)

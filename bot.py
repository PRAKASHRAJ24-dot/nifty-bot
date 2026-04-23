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
        response = requests.post(url, json={
            "chat_id": CHAT_ID,
            "text": msg
        })
        print("Telegram:", response.json())
    except Exception as e:
        print("Telegram Error:", e)


# ================== FETCH DATA ==================
def fetch_data():
    url = "https://query1.finance.yahoo.com/v8/finance/chart/%5ENSEI"

    try:
        response = requests.get(url, timeout=10)
        data = response.json()

        price = data["chart"]["result"][0]["meta"]["regularMarketPrice"]

        return {"price": price}

    except Exception as e:
        print("Fetch error:", e)
        return {}


# ================== LOGIC ==================
def check_signal():
    data = fetch_data()

    if "price" not in data:
        print("❌ Invalid response:", data)
        return

    price = data["price"]

    msg = f"""📊 NIFTY LIVE
LTP: {price}
Time: {datetime.now().strftime('%H:%M:%S')}
"""
    send_alert(msg)


# ================== MAIN LOOP ==================
if __name__ == "__main__":
    send_alert("🔥 BOT STARTED SUCCESSFULLY")

    while True:
        try:
            check_signal()
            time.sleep(60)  # every 1 min

        except Exception as e:
            print("Error:", e)
            time.sleep(10)

import requests
import time
from datetime import datetime

# ================= CONFIG =================
BOT_TOKEN = "8741088698:AAEBTaXYMVGevB7tLz4oTaCKpPXAoe9E7j4"
CHAT_ID = "1674106249"

BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

last_signal = None
last_price = None
prices = []


# ================= TELEGRAM =================
def send_alert(msg):
    try:
        requests.post(f"{BASE_URL}/sendMessage", json={
            "chat_id": CHAT_ID,
            "text": msg
        })
    except Exception as e:
        print("Telegram error:", e)


# ================= FETCH PRICE =================
def fetch_price():
    url = "https://query1.finance.yahoo.com/v8/finance/chart/%5ENSEI"
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        res = requests.get(url, headers=headers, timeout=10)

        if res.status_code != 200:
            return None

        data = res.json()

        result = data.get("chart", {}).get("result")
        if not result:
            return None

        return result[0]["meta"]["regularMarketPrice"]

    except Exception as e:
        print("Fetch error:", e)
        return None


# ================= STRIKE =================
def get_atm(price):
    return round(price / 50) * 50


# ================= SIGNAL LOGIC =================
def check_signal(price):
    global prices, last_signal

    prices.append(price)

    # keep last 3 prices
    if len(prices) > 3:
        prices.pop(0)

    if len(prices) < 3:
        return

    c1, c2, c3 = prices
    atm = get_atm(price)

    # 📈 CALL (up momentum)
    if c1 < c2 < c3 and last_signal != "CALL":
        last_signal = "CALL"

        send_alert(f"""📈 CALL SIGNAL

Index: {price}
Strike: {atm} CE

Entry: {price}
SL: {price - 40}
Target: {price + 80}

Time: {datetime.now().strftime('%H:%M:%S')}
""")

    # 📉 PUT (down momentum)
    elif c1 > c2 > c3 and last_signal != "PUT":
        last_signal = "PUT"

        send_alert(f"""📉 PUT SIGNAL

Index: {price}
Strike: {atm} PE

Entry: {price}
SL: {price + 40}
Target: {price - 80}

Time: {datetime.now().strftime('%H:%M:%S')}
""")


# ================= MAIN =================
if __name__ == "__main__":
    send_alert("🔥 YAHOO BOT STARTED")

    while True:
        try:
            price = fetch_price()

            if price is None:
                time.sleep(10)
                continue

            # 🔥 skip duplicate price
            global last_price
            if price == last_price:
                time.sleep(10)
                continue

            last_price = price

            print("New price:", price)

            check_signal(price)

            time.sleep(15)

        except Exception as e:
            print("Error:", e)
            time.sleep(10)

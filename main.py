import os
import requests
from datetime import datetime

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

API_URL = "http://et.tala.ir/webservice/haghanigold.com/6397dbw8333f095bb55cd539f865a994"


def to_persian_number(text):
    return str(text).translate(str.maketrans(
        "0123456789",
        "۰۱۲۳۴۵۶۷۸۹"
    ))


def safe_request(url):
    try:
        r = requests.get(url, timeout=10)
        return r.json()
    except Exception as e:
        print("API ERROR:", e)
        return None


data = safe_request(API_URL)

if not data:
    print("No data from API")
    exit()


price = data.get("geram18", {}).get("value", 0) // 10
server_time = data.get("serverTime", "")

if not price:
    print("Price not found")
    exit()


dt = datetime.strptime(server_time, "%Y-%m-%d %H:%M:%S")

date_text = dt.strftime("%Y/%m/%d")
tfrom datetime import timezone, timedelta

iran_time = dt.replace(tzinfo=timezone.utc) + timedelta(hours=3, minutes=30)
time_text = iran_time.strftime("%H:%M")

price_text = f"{price:,}"


# جلوگیری از ارسال تکراری
try:
    with open("last_price.txt", "r") as f:
        last_price = f.read().strip()
except:
    last_price = ""

if last_price == str(price):
    print("No change")
    exit()


with open("last_price.txt", "w") as f:
    f.write(str(price))


message = f"""💎 نرخ لحظه‌ای طلای ۱۸ عیار

🗓 {to_persian_number(date_text)}
🕒 بروزرسانی: {to_persian_number(time_text)}

💰 هر گرم: {to_persian_number(price_text)} تومان

━━━━━━━━━━━━━━━
طلای ماهان (اسکندری گلد)💎
"""


res = requests.post(
    f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
    data={
        "chat_id": CHAT_ID,
        "text": message
    }
)

print("STATUS:", res.status_code)
print("RESPONSE:", res.text)
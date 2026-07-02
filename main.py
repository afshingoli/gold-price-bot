import os
import requests
from datetime import datetime
from zoneinfo import ZoneInfo

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

API_URL = "http://et.tala.ir/webservice/haghanigold.com/6397dbw8333f095bb55cd539f865a994"


def to_persian_number(text):
    return str(text).translate(str.maketrans(
        "0123456789",
        "۰۱۲۳۴۵۶۷۸۹"
    ))


# گرفتن قیمت
try:
    data = requests.get(API_URL, timeout=10).json()
except:
    print("API ERROR")
    exit()

price = data["geram18"]["value"] // 10
price_text = f"{price:,}"


# ⭐ ساعت دقیق ایران (راه حل قطعی)
now = datetime.now(ZoneInfo("Asia/Tehran"))

weekdays = [
    "دوشنبه","سه‌شنبه","چهارشنبه","پنجشنبه","جمعه","شنبه","یکشنبه"
]

weekday = weekdays[now.weekday()]
time_text = now.strftime("%H:%M")


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


# پیام نهایی
message = f"""💎 نرخ لحظه‌ای طلای ۱۸ عیار

🗓 {weekday}
🕒 بروزرسانی: {to_persian_number(time_text)}

💰 هر گرم: {to_persian_number(price_text)} تومان

━━━━━━━━━━━━━━━
طلای ماهان (اسکندری گلد)💎
"""


# ارسال به تلگرام
res = requests.post(
    f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
    data={
        "chat_id": CHAT_ID,
        "text": message
    }
)

print("STATUS:", res.status_code)
print(res.text)
import os
import requests
from datetime import datetime

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

API_URL = "http://et.tala.ir/webservice/haghanigold.com/6397dbw8333f095bb55cd539f865a994"

def to_persian_number(text):
    return str(text).translate(str.maketrans(
        "0123456789",
        "۰۱۲۳۴۵۶۷۸۹"
    ))

# ماه‌ها و روزها (ثابت و بدون کتابخانه)
months = [
    "فروردین","اردیبهشت","خرداد","تیر","مرداد","شهریور",
    "مهر","آبان","آذر","دی","بهمن","اسفند"
]

weekdays = [
    "دوشنبه","سه‌شنبه","چهارشنبه","پنجشنبه","جمعه","شنبه","یکشنبه"
]

# گرفتن قیمت
data = requests.get(API_URL).json()

price = data["geram18"]["value"] // 10
server_time = data["serverTime"]

# تبدیل زمان API به datetime
dt = datetime.strptime(server_time, "%Y-%m-%d %H:%M:%S")

# ساخت تاریخ ساده (بدون jdatetime)
date_text = f"{dt.day} {months[(dt.month-1) % 12]} {dt.year}"
weekday = weekdays[dt.weekday()]
time_text = dt.strftime("%H:%M")

price_text = f"{price:,}"

# چک قیمت قبلی
try:
    with open("last_price.txt", "r") as f:
        last_price = f.read().strip()
except:
    last_price = ""

if last_price == str(price):
    print("Price not changed.")
    exit()

with open("last_price.txt", "w") as f:
    f.write(str(price))

message = f"""💎 نرخ لحظه‌ای طلای ۱۸ عیار

🗓 {to_persian_number(date_text)} | {weekday}
🕒 بروزرسانی: {to_persian_number(time_text)}

💰 هر گرم: {to_persian_number(price_text)} تومان

━━━━━━━━━━━━━━━
طلای ماهان (اسکندری گلد)💎
"""

requests.post(
    f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
    data={"chat_id": CHAT_ID, "text": message}
)

print("Message sent!")
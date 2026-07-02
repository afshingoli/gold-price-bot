import os
import requests
from datetime import datetime
import jdatetime

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

API_URL = "http://et.tala.ir/webservice/haghanigold.com/6397dbw8333f095bb55cd539f865a994"


# تبدیل عدد به فارسی
def to_persian_number(text):
    return str(text).translate(str.maketrans(
        "0123456789",
        "۰۱۲۳۴۵۶۷۸۹"
    ))


# ماه‌ها
months = [
    "فروردین","اردیبهشت","خرداد","تیر","مرداد","شهریور",
    "مهر","آبان","آذر","دی","بهمن","اسفند"
]

# روزهای هفته (درست)
weekdays = [
    "دوشنبه","سه‌شنبه","چهارشنبه","پنجشنبه","جمعه","شنبه","یکشنبه"
]


# گرفتن قیمت
data = requests.get(API_URL).json()

price = data["geram18"]["value"] // 10
price_text = f"{price:,}"


# زمان دقیق ایران (بدون API و بدون خطا)
now = jdatetime.datetime.now()

date_text = f"{now.day} {months[now.month-1]} {now.year}"
weekday = weekdays[now.weekday()]
time_text = now.strftime("%H:%M")


# چک قیمت قبلی
try:
    with open("last_price.txt", "r") as f:
        last_price = f.read().strip()
except:
    last_price = ""


if last_price == str(price):
    print("Price not changed.")
    exit()


# ذخیره قیمت جدید
with open("last_price.txt", "w") as f:
    f.write(str(price))


# پیام نهایی
message = f"""💎 نرخ لحظه‌ای طلای ۱۸ عیار

🗓 {to_persian_number(date_text)} | {weekday}
🕒 بروزرسانی: {to_persian_number(time_text)}

💰 هر گرم: {to_persian_number(price_text)} تومان

━━━━━━━━━━━━━━━
طلای ماهان (اسکندری گلد)💎
"""


# ارسال به تلگرام
requests.post(
    f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
    data={
        "chat_id": CHAT_ID,
        "text": message
    }
)

print("Done")
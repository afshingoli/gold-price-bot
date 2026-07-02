import os
import requests
from datetime import datetime, timedelta, timezone

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

API_URL = "http://et.tala.ir/webservice/haghanigold.com/6397dbw8333f095bb55cd539f865a994"


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

# روزهای هفته (ثابت درست)
weekdays = [
    "دوشنبه","سه‌شنبه","چهارشنبه","پنجشنبه","جمعه","شنبه","یکشنبه"
]


# گرفتن دیتا
data = requests.get(API_URL, timeout=10).json()

price = data["geram18"]["value"] // 10
price_text = f"{price:,}"

server_time = data["serverTime"]


# تبدیل زمان API به UTC
dt_utc = datetime.strptime(server_time, "%Y-%m-%d %H:%M:%S").replace(
    tzinfo=timezone.utc
)

# تبدیل به ساعت ایران (UTC+3:30)
iran_time = dt_utc + timedelta(hours=3, minutes=30)

# تاریخ شمسی واقعی با جلالی بر اساس زمان ایران
import jdatetime
jdt = jdatetime.datetime.fromgregorian(datetime=iran_time)


date_text = f"{jdt.day} {months[jdt.month-1]} {jdt.year}"
weekday = weekdays[iran_time.weekday()]
time_text = iran_time.strftime("%H:%M")


# کنترل تغییر قیمت
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

🗓 {to_persian_number(date_text)} | {weekday}
🕒 بروزرسانی: {to_persian_number(time_text)}

💰 هر گرم: {to_persian_number(price_text)} تومان

━━━━━━━━━━━━━━━
طلای ماهان (اسکندری گلد)💎
"""


res = requests.post(
    f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
    data={"chat_id": CHAT_ID, "text": message}
)

print("STATUS:", res.status_code)
print(res.text)
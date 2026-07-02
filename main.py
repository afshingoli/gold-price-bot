import os
import requests
import jdatetime
from datetime import datetime

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]
API_URL = "http://et.tala.ir/webservice/haghanigold.com/6397dbw8333f095bb55cd539f865a994"


def to_persian_number(text):
    return str(text).translate(str.maketrans(
        "0123456789",
        "۰۱۲۳۴۵۶۷۸۹"
    ))


weekdays_fa = {
    "Saturday": "شنبه",
    "Sunday": "یکشنبه",
    "Monday": "دوشنبه",
    "Tuesday": "سه‌شنبه",
    "Wednesday": "چهارشنبه",
    "Thursday": "پنجشنبه",
    "Friday": "جمعه",
}

months_fa = [
    "فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور",
    "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند"
]

# گرفتن قیمت
try:
    data = requests.get(API_URL, timeout=10).json()
except Exception as e:
    print("API ERROR:", e)
    exit()

price = data["geram18"]["value"] // 10
price_text = f"{price:,}"

# تاریخ و ساعت (به وقت ایران)
now_utc = datetime.utcnow()
now_iran = now_utc.timestamp() + 3.5 * 3600  # UTC+3:30
now_iran = datetime.fromtimestamp(now_iran)

jnow = jdatetime.date.fromgregorian(date=now_iran.date())
weekday_en = now_iran.strftime("%A")
weekday = weekdays_fa[weekday_en]

date_text = f"{jnow.day} {months_fa[jnow.month - 1]} {jnow.year}"
time_text = now_iran.strftime("%H:%M")

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

lines = [
    "💎 نرخ لحظه‌ای طلای ۱۸ عیار",
    "🗓 " + to_persian_number(date_text) + " | " + weekday,
    "🕒 بروزرسانی: " + to_persian_number(time_text),
    "💰 هر گرم: " + to_persian_number(price_text) + " تومان",
    "━━━━━━━━━━━━━━━",
    "طلای ماهان (اسکندری گلد)💎",
]
message = "\n".join(lines)

requests.post(
    f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
    data={"chat_id": CHAT_ID, "text": message}
)

print("Done")
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


months = [
    "فروردین","اردیبهشت","خرداد","تیر","مرداد","شهریور",
    "مهر","آبان","آذر","دی","بهمن","اسفند"
]

weekdays = [
    "دوشنبه","سه‌شنبه","چهارشنبه","پنجشنبه","جمعه","شنبه","یکشنبه"
]


try:
    data = requests.get(API_URL, timeout=10).json()
except Exception as e:
    print("API ERROR:", e)
    exit()


price = data["geram18"]["value"] // 10
server_time = data["serverTime"]

dt = datetime.strptime(server_time, "%Y-%m-%d %H:%M:%S")


# فقط برای ایران (بدون timezone دردسر)
iran_dt = dt  # چون serverTime تقریباً ایرانیه در این API

date_text = f"{iran_dt.day} {months[iran_dt.month-1]} {iran_dt.year}"
weekday = weekdays[iran_dt.weekday()]
time_text = iran_dt.strftime("%H:%M")

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
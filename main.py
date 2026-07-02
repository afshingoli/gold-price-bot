import os
import requests

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

PRICE_API = "http://et.tala.ir/webservice/haghanigold.com/6397dbw8333f095bb55cd539f865a994"
TIME_API = "https://api.keybit.ir/time/"


def to_persian_number(text):
    return str(text).translate(str.maketrans(
        "0123456789",
        "۰۱۲۳۴۵۶۷۸۹"
    ))


# گرفتن قیمت
data = requests.get(PRICE_API).json()
price = data["geram18"]["value"] // 10
price_text = f"{price:,}"


# گرفتن تاریخ دقیق شمسی (کاملاً درست)
tdata = requests.get(TIME_API).json()["date"]

date_text = tdata["full"]["official"]["iso"]["date"]["persian"]
weekday = tdata["week_day"]["name"]
time_text = tdata["time24"]["full"][:5]


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

print("Done")
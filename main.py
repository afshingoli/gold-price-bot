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


# ۱. گرفتن قیمت طلا
try:
    price_data = requests.get(PRICE_API).json()
    price = price_data["geram18"]["value"] // 10
    price_text = f"{price:,}"
except Exception as e:
    print(f"Error fetching price: {e}")
    exit()


# ۲. گرفتن تاریخ و زمان (اصلاح ساختار API)
try:
    time_response = requests.get(TIME_API).json()
    date_text = time_response["date"]["full"]["official"]["iso"]["date"]["persian"]
    weekday = time_response["week_day"]["name"]
    time_text = time_response["time24"]["full"][:5]
except Exception as e:
    print(f"Error fetching time: {e}")
    exit()


# ۳. بررسی تغییر قیمت
try:
    with open("last_price.txt", "r") as f:
        last_price = f.read().strip()
except:
    last_price = ""

# نکته: اگر می‌خواهی در هر شرایطی پیام ارسال شود، ۳ خط زیر را کامنت یا حذف کن:
if last_price == str(price):
    print("Price not changed. No message sent.")
    exit()


# بروزرسانی فایل قیمت قبلی
with open("last_price.txt", "w") as f:
    f.write(str(price))


# ۴. ساخت قالب پیام
message = f"""💎 نرخ لحظه‌ای طلای ۱۸ عیار

🗓 {to_persian_number(date_text)} | {weekday}
🕒 بروزرسانی: {to_persian_number(time_text)}

💰 هر گرم: {to_persian_number(price_text)} تومان

━━━━━━━━━━━━━━━
طلای ماهان (اسکندری گلد)💎
"""


# ۵. ارسال به تلگرام
try:
    response = requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        data={"chat_id": CHAT_ID, "text": message}
    )
    if response.status_code == 200:
        print("Message sent successfully.")
    else:
        print(f"Telegram API Error: {response.text}")
except Exception as e:
    print(f"Network Error: {e}")
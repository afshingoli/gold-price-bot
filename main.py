import os
import requests
import jdatetime
from zoneinfo import ZoneInfo

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

API_URL = "http://et.tala.ir/webservice/haghanigold.com/6397dbw8333f095bb55cd539f865a994"

def to_persian_number(text):
    return str(text).translate(str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹"))

# ۱. گرفتن قیمت
try:
    headers = {'User-Agent': 'Mozilla/5.0'} # برای جلوگیری از بلاک شدن توسط سرورهای ایرانی
    data = requests.get(API_URL, headers=headers, timeout=15).json()
    price = data["geram18"]["value"] // 10
    price_text = f"{price:,}"
except Exception as e:
    print(f"❌ خطا در دریافت قیمت: {e}")
    exit()

# ۲. گرفتن تاریخ و ساعت دقیق ایران (بسیار دقیق با jdatetime)
ir_tz = ZoneInfo("Asia/Tehran")
now = jdatetime.datetime.now(ir_tz)

date_str = now.strftime("%Y/%m/%d") # فرمت: 1403/04/11
time_str = now.strftime("%H:%M:%S") # فرمت: 17:05:22

weekdays = ["شنبه", "یکشنبه", "دوشنبه", "سه‌شنبه", "چهارشنبه", "پنجشنبه", "جمعه"]
weekday = weekdays[now.weekday()]

# ۳. بررسی قیمت قبلی
try:
    with open("last_price.txt", "r") as f:
        last_price = f.read().strip()
except FileNotFoundError:
    last_price = ""


# if last_price == str(price):
#     print("✅ ربات اجرا شد ولی چون قیمت طلا تغییری نکرده، پیامی ارسال نشد.")
#     exit()

# بروزرسانی فایل قیمت
with open("last_price.txt", "w") as f:
    f.write(str(price))

# ۴. ساخت متن پیام
message = f"""💎 نرخ لحظه‌ای طلای ۱۸ عیار

🗓 {weekday} | {to_persian_number(date_str)}
🕒 بروزرسانی: {to_persian_number(time_str)}

💰 هر گرم: {to_persian_number(price_text)} تومان

━━━━━━━━━━━━━━━
طلای ماهان (اسکندری گلد)💎
"""

# ۵. ارسال به تلگرام
try:
    res = requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        data={"chat_id": CHAT_ID, "text": message},
        timeout=10
    )
    if res.status_code == 200:
        print("🚀 پیام با موفقیت به تلگرام ارسال شد!")
    else:
        print(f"❌ خطا از سمت تلگرام: {res.text}")
except Exception as e:
    print(f"❌ خطای ارسال: {e}")
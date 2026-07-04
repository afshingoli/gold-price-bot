import os
import requests
import datetime

# تنظیمات اصلی
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
PRICE_API = "http://et.tala.ir/webservice/haghanigold.com/6397dbw8333f095bb55cd539f865a994"

def to_persian_number(text):
    # این تابع کاملاً اصلاح شد و دیگه ارور نمیده
    return str(text).translate(str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹"))

# ۱. دریافت قیمت جدید
try:
    data = requests.get(PRICE_API, timeout=10).json()
    price = data["geram18"]["value"] // 10
    price_text = f"{price:,}"
except Exception as e:
    print(f"خطا در دریافت قیمت: {e}")
    exit()

# ۲. دریافت ساعت و تاریخ دقیق ایران (بدون نیاز به هیچ API خارجی)
now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=3, minutes=30)))
weekdays = ["دوشنبه", "سه‌شنبه", "چهارشنبه", "پنجشنبه", "جمعه", "شنبه", "یکشنبه"]
weekday = weekdays[now.weekday()]
time_text = now.strftime("%H:%M")
# تاریخ رو به صورت ساده میذاریم چون API زمان قطع بود
date_text = now.strftime("%Y/%m/%d") 

# ۳. خواندن ایمن قیمت قبلی (ضد ارور Unicode)
last_price = "0"
try:
    with open("last_price.txt", "r", encoding="utf-8", errors="ignore") as f:
        content = f.read().strip()
        if content.isdigit():
            last_price = content
except Exception:
    last_price = "0"

# ۴. چک کردن تغییر قیمت
if str(price) == str(last_price):
    print("قیمت تغییری نکرده است.")
    exit()

# ۵. ارسال به تلگرام
message = f"""💎 نرخ لحظه‌ای طلای ۱۸ عیار
🗓 {to_persian_number(date_text)} | {weekday}
🕒 بروزرسانی: {to_persian_number(time_text)}

💰 هر گرم: {to_persian_number(price_text)} تومان
"""

try:
    tg_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    response = requests.post(tg_url, data={"chat_id": CHAT_ID, "text": message})
    if response.status_code == 200:
        with open("last_price.txt", "w", encoding="utf-8") as f:
            f.write(str(price))
        print("قیمت با موفقیت ارسال و ذخیره شد.")
    else:
        print(f"خطای تلگرام: {response.text}")
except Exception as e:
    print(f"خطا در ارسال پیام: {e}")
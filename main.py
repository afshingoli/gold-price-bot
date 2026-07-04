import os
import requests

# دریافت توکن‌ها از محیط گیت‌هاب
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

# آدرس API قیمت
PRICE_API = "http://et.tala.ir/webservice/haghanigold.com/6397dbw8333f095bb55cd539f865a994"
# آدرس API زمان
TIME_API = "https://api.keybit.ir/time/"

def to_persian_number(text):
    return str(text).translate(str.maketrans("0123456789", "۰۱۲۳۴۵۶ exorbitant۹"))

# ۱. دریافت قیمت جدید
try:
    data = requests.get(PRICE_API).json()
    price = data["geram18"]["value"] // 10
    price_text = f"{price:,}"
except Exception as e:
    print(f"خطا در دریافت قیمت: {e}")
    exit()

# ۲. دریافت زمان دقیق
try:
    tdata = requests.get(TIME_API).json()["date"]
    date_text = tdata["full"]["official"]["iso"]["date"]["persian"]
    weekday = tdata["week_day"]["name"]
    time_text = tdata["time24"]["full"][:5]
except Exception as e:
    print(f"خطا در دریافت زمان: {e}")
    date_text = "نامشخص"
    weekday = ""
    time_text = ""

# ۳. خواندن ایمن قیمت قبلی (نسخه ضد-خطا)
last_price = "0"
try:
    # پارامتر errors='ignore' جلوی ارور UnicodeDecodeError را می‌گیرد
    with open("last_price.txt", "r", encoding="utf-8", errors="ignore") as f:
        content = f.read().strip()
        if content.isdigit():
            last_price = content
except FileNotFoundError:
    last_price = "0"
except Exception:
    last_price = "0"

# ۴. چک کردن تغییر قیمت
if str(price) == str(last_price):
    print("قیمت تغییر نکرده است.")
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
        # ۶. ذخیره قیمت جدید فقط در صورت موفقیت
        with open("last_price.txt", "w", encoding="utf-8") as f:
            f.write(str(price))
        print("قیمت با موفقیت ارسال و ذخیره شد.")
    else:
        print(f"خطای تلگرام: {response.text}")
except Exception as e:
    print(f"خطا در ارسال پیام: {e}")
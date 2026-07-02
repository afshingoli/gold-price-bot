import os
import requests
from datetime import datetime
from zoneinfo import ZoneInfo

# تنظیمات توکن و چت‌آیدی از محیط گیت‌هاب
BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

API_URL = "http://et.tala.ir/webservice/haghanigold.com/6397dbw8333f095bb55cd539f865a994"


def to_persian_number(text):
    """تبدیل اعداد انگلیسی به فارسی برای زیبایی پیام"""
    return str(text).translate(str.maketrans(
        "0123456789",
        "۰۱۲۳۴۵۶۷۸۹"
    ))


# ۱. گرفتن قیمت طلا از API
try:
    data = requests.get(API_URL, timeout=10).json()
    price = data["geram18"]["value"] // 10
    price_text = f"{price:,}"
except Exception as e:
    print(f"API ERROR: {e}")
    exit()


# ۲. محاسبه ساعت دقیق تهران
now = datetime.now(ZoneInfo("Asia/Tehran"))

weekdays = [
    "دوشنبه", "سه‌شنبه", "چهارشنبه", "پنجشنبه", "جمعه", "شنبه", "یکشنبه"
]
weekday = weekdays[now.weekday()]
time_text = now.strftime("%H:%M")


# ۳. جلوگیری از ارسال پیام تکراری (منطق قیمت قبلی)
try:
    with open("last_price.txt", "r") as f:
        last_price = f.read().strip()
except:
    last_price = ""

# اگر قیمت تغییر نکرده باشد، کد اینجا متوقف می‌شود
if last_price == str(price):
    print(f"No change in price ({price} Tomans). Script stopped.")
    exit()

# اگر قیمت جدید بود، آن را در فایل ذخیره می‌کند
with open("last_price.txt", "w") as f:
    f.write(str(price))


# ۴. ساخت متن پیام نهایی
message = f"""💎 نرخ لحظه‌ای طلای ۱۸ عیار

🗓 {weekday}
🕒 بروزرسانی: {to_persian_number(time_text)}

💰 هر گرم: {to_persian_number(price_text)} تومان

━━━━━━━━━━━━━━━
طلای ماهان (اس
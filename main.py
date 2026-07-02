import os
import requests
import jdatetime
from zoneinfo import ZoneInfo

# ۱. تنظیمات توکن و چت‌آیدی از محیط گیت‌هاب
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

API_URL = "http://et.tala.ir/webservice/haghanigold.com/6397dbw8333f095bb55cd539f865a994"


def to_persian_number(text):
    """تبدیل اعداد انگلیسی به فارسی برای زیبایی متن پیام"""
    return str(text).translate(str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹"))


# ۲. دریافت قیمت طلا از API
try:
    headers = {'User-Agent': 'Mozilla/5.0'}
    data = requests.get(API_URL, headers=headers, timeout=15).json()
    price = data["geram18"]["value"] // 10
    price_text = f"{price:,}"
except Exception as e:
    print(f"❌ خطا در دریافت قیمت: {e}")
    exit()


# ۳. محاسبه تاریخ شمسی و ساعت دقیق تهران
ir_tz = ZoneInfo("Asia/Tehran")
now = jdatetime.datetime.now(ir_tz)

date_str = now.strftime("%Y/%m/%d")  # خروجی مثل: ۱۴۰۵/۰۴/۱۱
time_str = now.strftime("%H:%M:%S")  # خروجی مثل: ۱۷:۰۵:۲۲

weekdays = ["شنبه", "یکشنبه", "دوشنبه", "سه‌شنبه", "چهارشنبه", "پنجشنبه", "جمعه"]
weekday = weekdays[now.weekday()]


# ۴. بررسی قیمت قبلی (جلوگیری از ارسال پیام تکراری)
try:
    with open("last_price.txt", "r") as f:
        last_price = f.read().strip()
except FileNotFoundError:
    last_price = ""

# 🔒 اگر نرخ طلا تغییر نکرده باشد، ربات همین‌جا متوقف می‌شود و پیام نمی‌فرستد
if last_price == str(price):
    print(f"✅ نرخ طلا تغییری نکرده ({price} تومان). پیامی ارسال نشد.")
    exit()

# اگر نرخ جدید بود، آن را برای دفعات بعدی ذخیره می‌کند
with open("last_price.txt", "w") as f:
    f.write(str(price))


# ۵. ساخت متن پیام نهایی
message = f"""💎 نرخ لحظه‌ای طلای ۱۸ عیار

🗓 {weekday} | {to_persian_number(date_str)}
🕒 بروزرسانی: {to_persian_number(time_str)}

💰 هر گرم: {to_persian_number(price_text)} تومان

━━━━━━━━━━━━━━━
طلای ماهان (اسکندری گلد)💎
"""


# ۶. ارسال پیام به تلگرام
try:
    res = requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        data={"chat_id": CHAT_ID, "text": message},
        timeout=10
    )
    if res.status_code == 200:
        print("🚀 نرخ جدید بود و پیام با موفقیت به تلگرام ارسال شد!")
    else:
        print(f"❌ خطا از سمت تلگرام: {res.text}")
except Exception as e:
    print(f"❌ خطای شبکه در ارسال به تلگرام: {e}")
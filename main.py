import os
import re
import requests
import jdatetime
from bs4 import BeautifulSoup
from zoneinfo import ZoneInfo

# ۱. تنظیمات توکن و چت‌آیدی از محیط گیت‌هاب
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

# کانال منبع: اتحادیه طلا و جواهر مشهد
SOURCE_CHANNEL = "etjmir" 


def to_persian_number(text):
    """تبدیل اعداد انگلیسی به فارسی برای زیبایی متن پیام"""
    return str(text).translate(str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹"))

def fa_to_en_number(text):
    """تبدیل اعداد فارسی به انگلیسی برای پردازش محاسباتی"""
    return str(text).translate(str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789"))


# ۲. خواندن آخرین پیام از کانال منبع (تلگرام وب)
try:
    url = f"https://t.me/s/{SOURCE_CHANNEL}"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    res = requests.get(url, headers=headers, timeout=15)
    soup = BeautifulSoup(res.text, "html.parser")
    
    # پیدا کردن باکس‌های پیام کانال
    messages = soup.find_all("div", class_="tgme_widget_message_text js-message_text")
    if not messages:
        print("❌ پیامی در کانال پیدا نشد یا ساختار صفحه وب تلگرام تغییر کرده است.")
        exit()
        
    # گرفتن متن آخرین پیام ارسال شده در کانال
    latest_message = messages[-1].get_text()
    print("📰 متن آخرین پیام کانال منبع:\n", latest_message)
except Exception as e:
    print(f"❌ خطا در خواندن کانال تلگرام: {e}")
    exit()


# ۳. استخراج هوشمند قیمت طلای ۱۸ عیار از بین متن پیام
price = None
cleaned_text = fa_to_en_number(latest_message) # یکدست‌سازی اعداد

for line in cleaned_text.split("\n"):
    # جستجو در خطوطی که مربوط به طلای ۱۸ عیار یا هر گرم طلا هستند
    if "18" in line or "۱۸" in line or "گرم" in line:
        # حذف کاما، ویرگول و فاصله‌ها برای استخراج خالص عدد قیمت
        line_cleaned = line.replace(",", "").replace("،", "").replace(" ", "")
        # پیدا کردن اعداد ۶ تا ۸ رقمی (قیمت طلا به ریال یا تومان)
        numbers = re.findall(r'\d{6,8}', line_cleaned)
        if numbers:
            price = int(numbers[0])
            # اگر قیمت به ریال بود (مثلاً بالای ۱۰ میلیون بود)، تبدیلش میکنه به تومان
            if price > 10000000:
                price = price // 10
            break

if not price:
    print("❌ فرمول نتوانست قیمت ۱۸ عیار را از متن پیام استخراج کند.")
    print("💡 نکته: اگر پیام آخر کانال متنی غیر از قیمت (مثل اطلاعیه) باشد، این خطا طبیعی است.")
    exit()

price_text = f"{price:,}"


# ۴. محاسبه تاریخ شمسی و ساعت دقیق تهران
ir_tz = ZoneInfo("Asia/Tehran")
now = jdatetime.datetime.now(ir_tz)
date_str = now.strftime("%Y/%m/%d")
time_str = now.strftime("%H:%M:%S")

weekdays = ["شنبه", "یکشنبه", "دوشنبه", "سه‌شنبه", "چهارشنبه", "پنجشنبه", "جمعه"]
weekday = weekdays[now.weekday()]


# ۵. بررسی تکراری نبودن قیمت (ترمز هوشمند)
try:
    with open("last_price.txt", "r") as f:
        last_price = f.read().strip()
except FileNotFoundError:
    last_price = ""

if last_price == str(price):
    print(f"✅ نرخ طلا تغییری نکرده ({price} تومان). پیامی ارسال نشد.")
    exit()

with open("last_price.txt", "w") as f:
    f.write(str(price))


# ۶. ساخت متن پیام برای کانال شما
message = f"""💎 نرخ لحظه‌ای طلای ۱۸ عیار

🗓 {weekday} | {to_persian_number(date_str)}
🕒 بروزرسانی: {to_persian_number(time_str)}

💰 هر گرم: {to_persian_number(price_text)} تومان

━━━━━━━━━━━━━━━
طلای ماهان (اسکندری گلد)💎
"""


# ۷. ارسال به کانال خودت
try:
    res = requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        data={"chat_id": CHAT_ID, "text": message},
        timeout=10
    )
    if res.status_code == 200:
        print("🚀 قیمت از کانال اتحادیه مشهد گرفته شد و با موفقیت به کانال شما ارسال شد!")
    else:
        print(f"❌ خطا از سمت تلگرام: {res.text}")
except Exception as e:
    print(f"❌ خطای شبکه: {e}")
import os
import re
import requests
import jdatetime
from bs4 import BeautifulSoup
from zoneinfo import ZoneInfo

# ۱. تنظیمات توکن‌ها از محیط گیت‌هاب
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
EITAA_TOKEN = os.environ.get("EITAA_TOKEN")
EITAA_CHAT_ID = os.environ.get("EITAA_CHAT_ID")

# کانال منبع: اتحادیه طلا و جواهر مشهد
SOURCE_CHANNEL = "etjmir" 


def to_persian_number(text):
    return str(text).translate(str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹"))

def fa_to_en_number(text):
    return str(text).translate(str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789"))


# ۲. خواندن پیام‌ها از کانال منبع (تلگرام وب)
try:
    url = f"https://t.me/s/{SOURCE_CHANNEL}"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    res = requests.get(url, headers=headers, timeout=15)
    soup = BeautifulSoup(res.text, "html.parser")
    messages = soup.find_all("div", class_="tgme_widget_message_text js-message_text")
    if not messages:
        print("❌ پیامی در کانال پیدا نشد.")
        exit()
except Exception as e:
    print(f"❌ خطا در خواندن کانال تلگرام: {e}")
    exit()


# ۳. اسکن معکوس پیام‌ها برای پیدا کردن آخرین نرخ طلای ۱۸ عیار
price = None
for msg in reversed(messages):
    text = msg.get_text()
    cleaned_text = fa_to_en_number(text)
    
    if "18" in cleaned_text or "۱۸" in text or "گرم" in text:
        for line in cleaned_text.split("\n"):
            if "18" in line or "۱۸" in line or "گرم" in line:
                line_cleaned = line.replace(",", "").replace("،", "").replace(" ", "")
                numbers = re.findall(r'\d{5,8}', line_cleaned)
                if numbers:
                    price = int(numbers[0])
                    break
        if price:
            break

if not price:
    print("❌ فرمول نتوانست قیمت ۱۸ عیار را استخراج کند.")
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


# 🚀 ۷. ارسال پیام به تلگرام
try:
    res_tg = requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        data={"chat_id": CHAT_ID, "text": message},
        timeout=10
    )
    if res_tg.status_code == 200:
        print("🚀 پیام با موفقیت به تلگرام ارسال شد!")
    else:
        print(f"❌ خطا از سمت تلگرام: {res_tg.text}")
except Exception as e:
    print(f"❌ خطای شبکه تلگرام: {e}")


# 🚀 ۸. ارسال پیام به ایتا (ایتایار)
if EITAA_TOKEN and EITAA_CHAT_ID:
    try:
        res_eitaa = requests.post(
            f"https://eitaayar.ir/api/{EITAA_TOKEN}/sendMessage",
            data={"chat_id": EITAA_CHAT_ID, "text": message},
            timeout=15
        )
        if res_eitaa.json().get("ok") == True:
            print("🚀 پیام با موفقیت به ایتا ارسال شد!")
        else:
            print(f"❌ خطا از سمت ایتا: {res_eitaa.text}")
    except Exception as e:
        print(f"❌ خطای شبکه ایتا: {e}")
else:
    print("⚠️ تنظیمات سکرت‌های ایتا در گیت‌هاب انجام نشده است.")
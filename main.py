import os
import re
import datetime
import requests
from bs4 import BeautifulSoup

# تنظیمات توکن‌ها و آیدی‌ها از سکرت‌های گیت‌هاب
BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]
EITAA_TOKEN = os.environ.get("EITAA_TOKEN")
EITAA_CHAT_ID = os.environ.get("EITAA_CHAT_ID")

# آیدی کانال تلگرام اتحادیه
CHANNEL_USERNAME = "etjmir" 

def to_persian_number(text):
    return str(text).translate(str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹"))

def fa_to_en_number(text):
    return str(text).translate(str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789"))

def gregorian_to_jalali(gy, gm, gd):
    g_d_m = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 335]
    gy = gy - 1600 if gy > 1600 else gy - 621
    days = (365 * gy) + int((gy + 3) / 4) - int((gy + 99) / 100) + int((gy + 399) / 400) - 80 + gd + g_d_m[gm - 1]
    jy = 979 + 33 * int(days / 12053)
    days %= 12053
    jy += 4 * int(days / 1461)
    days %= 1461
    if days > 365:
        jy += int((days - 1) / 365)
        days = (days - 1) % 365
    jm = 1 + int(days / 31) if days < 186 else 7 + int((days - 186) / 30)
    jd = 1 + (days % 31) if days < 186 else 1 + ((days - 186) % 30)
    return f"{jy}/{jm:02d}/{jd:02d}"

# دریافت قیمت از کانال تلگرام اتحادیه
try:
    url = f"https://t.me/s/{CHANNEL_USERNAME}"
    response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    messages = soup.find_all('div', class_='tgme_widget_message_text')
    if not messages:
        print("خطا: پیامی پیدا نشد!")
        exit()
        
    price = None
    
    # گشتن بین آخرین پیام‌ها برای پیدا کردن نرخ طلای ۱۸ عیار
    for msg in reversed(messages):
        text = msg.get_text()
        clean_text = fa_to_en_number(text).replace(",", "").replace("،", "")
        
        for line in clean_text.split('\n'):
            if "18" in line or "۱۸" in line or "عیار" in line or "گرم" in line:
                numbers = re.findall(r'\d{7,8}', line)
                if numbers:
                    price = int(numbers[0])
                    break
        if price:
            break

    if not price:
        last_message = messages[-1].get_text()
        clean_text = fa_to_en_number(last_message).replace(",", "").replace("،", "")
        all_numbers = re.findall(r'\d{7,8}', clean_text)
        if all_numbers:
            price = int(all_numbers[0])

    if price:
        price_text = f"{price:,}"
    else:
        print("خطا: قیمت پیدا نشد.")
        exit()
        
except Exception as e:
    print("خطا در سیستم:", e)
    exit()

# محاسبات تاریخ و زمان تهران
tz_iran = datetime.timezone(datetime.timedelta(hours=3, minutes=30))
now_iran = datetime.datetime.now(tz_iran)
date_text = gregorian_to_jalali(now_iran.year, now_iran.month, now_iran.day)
weekdays = ["دوشنبه", "سه‌شنبه", "چهارشنبه", "پنج‌شنبه", "جمعه", "شنبه", "یکشنبه"]
weekday = weekdays[now_iran.weekday()]
time_text = now_iran.strftime("%H:%M")

# ذخیره برای آمار روزانه
try:
    with open("daily_prices.txt", "a") as f: f.write(f"{price}\n")
except: pass

# جلوگیری از ارسال پیام تکراری
try:
    with open("last_price.txt", "r") as f: last_price = f.read().strip()
except: last_price = ""

if str(last_price) == str(price):
    print("قیمت تغییر نکرده؛ خروج از برنامه.")
    exit()

try:
    with open("last_price.txt", "w") as f: f.write(str(price))
except: pass

# ساخت پیام نهایی
message = f"""💎 نرخ لحظه‌ای طلای ۱۸ عیار
🗓 {to_persian_number(date_text)} | {weekday}
🕒 بروزرسانی: {to_persian_number(time_text)}
💰 هر گرم: {to_persian_number(price_text)} تومان
━━━━━━━━━━━━━━━
طلای ماهان (اسکندری گلد)💎"""

# ارسال به تلگرام و ایتا
requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": message})
if EITAA_TOKEN and EITAA_CHAT_ID:
    requests.post(f"https://eitaayar.ir/api/{EITAA_TOKEN}/sendMessage", data={"chat_id": EITAA_CHAT_ID, "text": message})

print("✅ پیام با موفقیت ارسال شد.")
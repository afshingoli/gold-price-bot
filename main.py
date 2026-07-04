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
MODE = os.environ.get("MODE", "price")  # میتونه price باشه یا summary

# آیدی کانال تلگرام اتحادیه مشهد
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

# محاسبه تاریخ و زمان تهران
tz_iran = datetime.timezone(datetime.timedelta(hours=3, minutes=30))
now_iran = datetime.datetime.now(tz_iran)
date_text = gregorian_to_jalali(now_iran.year, now_iran.month, now_iran.day)
weekdays = ["دوشنبه", "سه‌شنبه", "چهارشنبه", "پنج‌شنبه", "جمعه", "شنبه", "یکشنبه"]
weekday = weekdays[now_iran.weekday()]
time_text = now_iran.strftime("%H:%M")

# 📊 بخش اول: پردازش گزارش روزانه (خلاصه بازار)
if MODE == "summary":
    if not os.path.exists("daily_prices.txt"):
        print("فایل آمار روزانه پیدا نشد.")
        exit()
        
    with open("daily_prices.txt", "r") as f:
        lines = [int(line.strip()) for line in f.readlines() if line.strip().isdigit()]
        
    if not lines:
        print("آماری برای امروز ثبت نشده است.")
        exit()
        
    open_price = lines[0]
    close_price = lines[-1]
    high_price = max(lines)
    low_price = min(lines)
    diff = close_price - open_price
    
    if diff > 0:
        diff_sign = "🔺 +"
    elif diff < 0:
        diff_sign = "🔻 "
    else:
        diff_sign = "🔹 "
        
    pct = (diff / open_price) * 100 if open_price else 0
    
    summary_message = f"""📊 گزارش و خلاصه بازار امروز
🗓 {to_persian_number(date_text)} | {weekday}
━━━━━━━━━━━━━━━
🔓 نرخ بازگشایی: {to_persian_number(f"{open_price:,}")} تومان
🔒 نرخ پایانی: {to_persian_number(f"{close_price:,}")} تومان
🔺 بالاترین نرخ: {to_persian_number(f"{high_price:,}")} تومان
🔻 پایین‌ترین نرخ: {to_persian_number(f"{low_price:,}")} تومان
📈 میزان تغییر: {diff_sign}{to_persian_number(f"{abs(diff):,}")} تومان ({to_persian_number(f"{pct:.2f}")}٪)
━━━━━━━━━━━━━━━
طلای ماهان (اسکندری گلد)💎"""

    # ارسال خلاصه به تلگرام
    tg_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(tg_url, data={"chat_id": CHAT_ID, "text": summary_message})
    
    # ارسال خلاصه به ایتا
    if EITAA_TOKEN and EITAA_CHAT_ID:
        eitaa_url = f"https://eitaayar.ir/api/{EITAA_TOKEN}/sendMessage"
        requests.post(eitaa_url, data={"chat_id": EITAA_CHAT_ID, "text": summary_message})
        
    # پاک کردن فایل برای روز بعد
    with open("daily_prices.txt", "w") as f:
        f.write("")
        
    print("✅ گزارش روزانه ارسال شد و لیست قیمت‌ها ریست شد.")
    exit()

# 💰 بخش دوم: دریافت و ارسال قیمت لحظه‌ای (روال عادی ربات)
try:
    url = f"https://t.me/s/{CHANNEL_USERNAME}"
    response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    messages = soup.find_all('div', class_='tgme_widget_message_text')
    if not messages:
        print("خطا: پیامی پیدا نشد!")
        exit()
        
    price = None
    for msg in reversed(messages):
        text = msg.get_text()
        if "18" in text or "۱۸" in text:
            for line in text.split('\n'):
                if ("18" in line or "۱۸" in line) and ("گرم" in line or "عیار" in line):
                    clean_line = fa_to_en_number(line).replace(",", "").replace("،", "")
                    clean_line = clean_line.replace("18", "")
                    numbers = re.findall(r'\d{6,9}', clean_line)
                    if numbers:
                        price = int(numbers[0])
                        break
        if price:
            break

    if not price:
        print("خطا: قیمت واقعی پیدا نشد.")
        exit()
        
    price_text = f"{price:,}"
        
except Exception as e:
    print("خطا در سیستم:", e)
    exit()

# ذخیره برای آمار روزانه
try:
    with open("daily_prices.txt", "a") as f: 
        f.write(f"{price}\n")
except: pass

# جلوگیری از ارسال پیام تکراری
try:
    with open("last_price.txt", "r") as f: 
        last_price = f.read().strip()
except: 
    last_price = ""

if str(last_price) == str(price):
    print("قیمت تغییر نکرده؛ خروج از برنامه.")
    exit()

try:
    with open("last_price.txt", "w") as f: 
        f.write(str(price))
except: pass

# ساخت پیام نرخ لحظه‌ای
message = f"""💎 نرخ لحظه‌ای طلای ۱۸ عیار
🗓 {to_persian_number(date_text)} | {weekday}
🕒 بروزرسانی: {to_persian_number(time_text)}
💰 هر گرم: {to_persian_number(price_text)} تومان
━━━━━━━━━━━━━━━
طلای ماهان (اسکندری گلد)💎"""

# ارسال پیام لحظه ای به تلگرام
tg_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
requests.post(tg_url, data={"chat_id": CHAT_ID, "text": message})

# ارسال پیام لحظه ای به ایتا
if EITAA_TOKEN and EITAA_CHAT_ID:
    eitaa_url = f"https://eitaayar.ir/api/{EITAA_TOKEN}/sendMessage"
    requests.post(eitaa_url, data={"chat_id": EITAA_CHAT_ID, "text": message})

print("✅ پیام لحظه‌ای با موفقیت ارسال شد.")
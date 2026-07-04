import os
import requests
import datetime
import re
from bs4 import BeautifulSoup

# تنظیم توکن‌ها و آیدی‌ها از سکرت‌های گیت‌هاب
BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

# متغیرهای ایتا
EITAA_TOKEN = os.environ.get("EITAA_TOKEN")
EITAA_CHAT_ID = os.environ.get("EITAA_CHAT_ID")

# 📢 آیدی کانال تلگرامی که می‌خواهی قیمت را از آن بگیری (بدون @)
# مثلاً اگر آیدی کانال tg_gold_union است، همان را بنویس
CHANNEL_USERNAME = "آیدی_کانال_اتحادیه_را_اینجا_بنویس" 

def to_persian_number(text):
    return str(text).translate(str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹"))

def fa_to_en_number(text):
    return str(text).translate(str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789"))

# تابع داخلی برای تبدیل تاریخ میلادی به شمسی بدون نیاز به اینترنت
def gregorian_to_jalali(gy, gm, gd):
    g_d_m = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 335]
    if gy > 1600:
        jy = 979
        gy -= 1600
    else:
        jy = 0
        gy -= 621
    gy2 = gy + 1 if gm > 2 else gy
    days = (365 * gy) + int((gy + 3) / 4) - int((gy + 99) / 100) + int((gy + 399) / 400) - 80 + gd + g_d_m[gm - 1]
    jy += 33 * int(days / 12053)
    days %= 12053
    jy += 4 * int(days / 1461)
    days %= 1461
    if days > 365:
        jy += int((days - 1) / 365)
        days = (days - 1) % 365
    if days < 186:
        jm = 1 + int(days / 31)
        jd = 1 + (days % 31)
    else:
        jm = 7 + int((days - 186) / 30)
        jd = 1 + ((days - 186) % 30)
    return f"{jy}/{jm:02d}/{jd:02d}"

# ۱. دریافت قیمت از آخرین پیام کانال تلگرام (اسکرپ کردن نسخه وب)
try:
    url = f"https://t.me/s/{CHANNEL_USERNAME}"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    response = requests.get(url, headers=headers, timeout=15)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # پیدا کردن تگ‌های حاوی متن پیام‌ها
    messages = soup.find_all('div', class_='tgme_widget_message_text')
    
    if not messages:
        print("خطا: هیچ پیامی در کانال پیدا نشد یا آیدی کانال اشتباه است/خصوصی است.")
        exit()
        
    # گرفتن متن آخرین پیام کانال
    last_message = messages[-1].get_text()
    print("متن آخرین پیام دریافت شده:\n", last_message)
    
    # تبدیل اعداد فارسی پیام به انگلیسی و حذف کاماها برای استخراج راحت‌تر
    clean_text = fa_to_en_number(last_message).replace(",", "").replace("،", "")
    
    # پیدا کردن اعداد ۷ یا ۸ رقمی (مثلاً عددی بین ۱ تا ۲۰ میلیون برای قیمت طلا)
    all_numbers = re.findall(r'\d{7,8}', clean_text)
    
    if all_numbers:
        # فرض بر این است که اولین عدد بزرگ پیدا
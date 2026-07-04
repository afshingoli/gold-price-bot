import os
import re
import datetime
import requests
from bs4 import BeautifulSoup

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]
EITAA_TOKEN = os.environ.get("EITAA_TOKEN")
EITAA_CHAT_ID = os.environ.get("EITAA_CHAT_ID")
MODE = os.environ.get("MODE", "price")

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

# تنظیم دقیق ساعت بر اساس زمان رسمی ایران
tz_iran = datetime.timezone(datetime.timedelta(hours=3, minutes=30))
now_iran = datetime.datetime.now(tz_iran)
date_text = gregorian_to_jalali(now_iran.year, now_iran.month, now_iran.day)
weekdays = ["دوشنبه", "سه‌شنبه", "چهارشنبه", "پنج‌شنبه", "جمعه", "شنبه", "یکشنبه"]
weekday = weekdays[now_iran.weekday()]
time_text = now_iran.strftime("%H:%M")

if MODE == "summary":
    if not os.path.exists("daily_prices.txt"):
        print("فایل آمار روزانه پیدا نشد.")
        exit()
        
    # 🔑 حل مشکل انکودینگ با استفاده از errors='ignore' یا utf-16 در صورت نیاز
    lines = []
    try:
        with open("daily_prices.txt", "r", encoding="utf-8", errors="ignore") as f:
            raw_lines = f.readlines()
    except Exception as e:
        print("خطا در خواندن فایل با utf-8، تلاش مجدد...", e)
        raw_lines = []

    for line in raw_lines:
        clean = line.strip().replace('\x00', '') # حذف کاراکترهای پوچ احتمالی
        if clean.isdigit() and int(clean) > 2000000:
            lines.append(int(clean))
        
    if not lines:
        print("آماری برای امروز ثبت نشده یا فایل خراب بوده است.")
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
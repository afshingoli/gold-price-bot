import os
import re
import datetime
import requests
from bs4 import BeautifulSoup

# تنظیمات اصلی
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
EITAA_TOKEN = os.environ.get("EITAA_TOKEN")
EITAA_CHAT_ID = os.environ.get("EITAA_CHAT_ID")
CHANNEL_USERNAME = "etjmir"

def to_persian_number(text):
    return str(text).translate(str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹"))

def fa_to_en_number(text):
    return str(text).translate(str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789"))

# فرمول آفلاین تبدیل تاریخ میلادی به شمسی
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

# محاسبه تاریخ و ساعت داخلی
tz_iran = datetime.timezone(datetime.timedelta(hours=3, minutes=30))
now = datetime.datetime.now(tz_iran)
weekdays = ["دوشنبه", "سه‌شنبه", "چهارشنبه", "پنجشنبه", "جمعه", "شنبه", "یکشنبه"]
weekday = weekdays[now.weekday()]
time_text = now.strftime("%H:%M")
date_text = gregorian_to_jalali(now.year, now.month, now.day)
hour_now = now.hour

# ==========================================
# بخش اول: استخراج قیمت از کانال اتحادیه (etjmir)
# ==========================================
try
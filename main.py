import requests
import os
import jdatetime
from datetime import datetime

# تنظیمات اصلی
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
API_URL = "http://et.tala.ir/webservice/haghanigold.com/6397dbw8333f095bb55cd539f865a994"

def get_persian_date():
    return jdatetime.date.today().strftime('%Y/%m/%d')

def send_message(text):
    try:
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": text})
    except Exception as e:
        print(f"Error sending message: {e}")

# 1. گرفتن نرخ
try:
    data = requests.get(API_URL, timeout=10).json()
    price_18 = data["geram18"]["value"] // 10
    
    # ذخیره در فایل
    with open("daily_prices.txt", "a", encoding="utf-8") as f:
        f.write(f"{price_18}\n")
except Exception as e:
    print(f"API Error: {e}")
    exit()

# 2. ارسال پیام لحظه‌ای (با شرط تغییر قیمت)
last_price_file = "last_price.txt"
if os.path.exists(last_price_file):
    with open(last_price_file, "r", encoding="utf-8") as f:
        last_price = f.read().strip()
else:
    last_price = "0"

if str(price_18) != last_price:
    msg = f"💎 نرخ لحظه‌ای: {price_18:,} تومان\nتاریخ: {get_persian_date()}"
    send_message(msg)
    with open(last_price_file, "w", encoding="utf-8") as f:
        f.write(str(price_18))

# 3. گزارش شبانه (ساعت 20:00)
now = datetime.now()
if now.hour == 20: 
    if os.path.exists("daily_prices.txt"):
        with open("daily_prices.txt", "r", encoding="utf-8") as f:
            lines = [int(line.strip()) for line in f if line.strip().isdigit()]
        
        if lines:
            report = f"📊 گزارش پایان روز {get_persian_date()}\n"
            report += f"🔓 نرخ بازگشایی: {lines[0]:,}\n"
            report += f"🔒 نرخ پایانی: {lines[-1]:,}\n"
            report += f"🔺 بالاترین نرخ: {max(lines):,}\n"
            report += f"🔻 پایین‌ترین نرخ: {min(lines):,}"
            send_message(report)
            os.remove("daily_prices.txt") # ریست برای فردا
import requests
import os
import jdatetime
from datetime import datetime

# تنظیمات اصلی
BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]
EITAA_TOKEN = os.environ.get("EITAA_TOKEN")
EITAA_CHAT_ID = os.environ.get("EITAA_CHAT_ID")
API_URL = "http://et.tala.ir/webservice/haghanigold.com/6397dbw8333f095bb55cd539f865a994"

def get_persian_date():
    return jdatetime.date.today().strftime('%Y/%m/%d')

def send_message(text):
    requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": text})
    if EITAA_TOKEN and EITAA_CHAT_ID:
        requests.post(f"https://eitaayar.ir/api/{EITAA_TOKEN}/sendMessage", data={"chat_id": EITAA_CHAT_ID, "text": text})

# 1. گرفتن نرخ لحظه‌ای از API
try:
    data = requests.get(API_URL, timeout=10).json()
    price_18 = data["geram18"]["value"] // 10
    # ذخیره در فایل برای گزارش شبانه
    with open("daily_prices.txt", "a") as f:
        f.write(f"{price_18}\n")
except Exception as e:
    print(f"Error: {e}")
    exit()

# 2. چک کردن برای ارسال پیام لحظه‌ای (با شرط تغییر قیمت)
try:
    with open("last_price.txt", "r") as f:
        last_price = f.read().strip()
except:
    last_price = "0"

if str(price_18) != last_price:
    msg = f"💎 نرخ لحظه‌ای: {price_18:,} تومان\nتاریخ: {get_persian_date()}"
    send_message(msg)
    with open("last_price.txt", "w") as f:
        f.write(str(price_18))

# 3. گزارش شبانه راس ساعت 20:00
now = datetime.now()
if now.hour == 20 and now.minute < 15:
    try:
        with open("daily_prices.txt", "r") as f:
            prices = [int(line.strip()) for line in f if line.strip().isdigit()]
        if prices:
            report = f"📊 گزارش پایان روز {get_persian_date()}\n"
            report += f"🔓 نرخ بازگشایی: {prices[0]:,}\n"
            report += f"🔒 نرخ پایانی: {prices[-1]:,}\n"
            report += f"🔺 بالاترین نرخ: {max(prices):,}\n"
            report += f"🔻 پایین‌ترین نرخ: {min(prices):,}"
            send_message(report)
            open("daily_prices.txt", "w").close() # خالی کردن فایل برای فردا
    except:
        pass
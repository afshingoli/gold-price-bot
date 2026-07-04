import requests
import os
import jdatetime
from bs4 import BeautifulSoup
from datetime import datetime

# تنظیمات اصلی
BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]
EITAA_TOKEN = os.environ.get("EITAA_TOKEN")
EITAA_CHAT_ID = os.environ.get("EITAA_CHAT_ID")
CHANNEL_USERNAME = "etjmir"

def send_message(text):
    try:
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": text})
        if EITAA_TOKEN and EITAA_CHAT_ID:
            requests.post(f"https://eitaayar.ir/api/{EITAA_TOKEN}/sendMessage", data={"chat_id": EITAA_CHAT_ID, "text": text})
    except Exception as e:
        print(f"Error: {e}")

# استخراج نرخ از کانال
try:
    url = f"https://t.me/s/{CHANNEL_USERNAME}"
    response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # هم پیام‌های متنی و هم کپشن عکس‌ها در این کلاس قرار دارند
    messages = soup.find_all('div', class_='tgme_widget_message_text')
    
    price = None
    for msg in reversed(messages):
        text = msg.get_text()
        # جستجو برای "18" و اعداد
        if "18" in text or "عیار" in text:
            # جدا کردن اعداد با ریجکس هوشمندتر
            import re
            numbers = re.findall(r'[\d,]{6,9}', text.replace("،", ","))
            for n in numbers:
                clean_n = int(n.replace(",", ""))
                if clean_n > 2000000: # فیلتر شماره موبایل
                    price = clean_n
                    break
        if price: break

    if not price: exit("نرخ پیدا نشد")
    
    # چک کردن تغییر قیمت
    last_price_file = "last_price.txt"
    last_price = "0"
    if os.path.exists(last_price_file):
        with open(last_price_file, "r", encoding="utf-8") as f:
            last_price = f.read().strip()
    
    if str(price) == last_price:
        exit("No change")

    # ارسال پیام
    msg = f"💎 نرخ لحظه‌ای طلای ۱۸ عیار\n🗓 {jdatetime.date.today().strftime('%Y/%m/%d')}\n💰 هر گرم: {price:,} تومان\n━━━━━━━━━━━━━━━\nطلای ماهان (اسکندری گلد)💎"
    send_message(msg)
    
    with open(last_price_file, "w", encoding="utf-8") as f:
        f.write(str(price))
        
except Exception as e:
    print(f"Error: {e}")
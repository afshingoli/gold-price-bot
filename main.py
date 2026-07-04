import requests
import os
import re
from bs4 import BeautifulSoup
import jdatetime
from datetime import datetime

# تنظیمات اصلی
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
CHANNEL_USERNAME = "etjmir"

def send_message(text):
    try:
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": text})
    except Exception as e:
        print(f"Error: {e}")

try:
    # 1. گرفتن صفحه کانال
    url = f"https://t.me/s/{CHANNEL_USERNAME}"
    response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
    soup = BeautifulSoup(response.text, 'html.parser')
    messages = soup.find_all('div', class_='tgme_widget_message_text')
    
    if not messages:
        send_message("❌ ارور: پیامی در کانال پیدا نشد!")
        exit()

    # 2. جستجوی قیمت در پیام‌ها
    price = None
    for msg in reversed(messages):
        text = msg.get_text()
        # جستجوی اعداد 7 تا 9 رقمی که قیمت طلا هستند
        pattern = r'\d{1,3}[,٫]?\d{3}[,٫]?\d{3}'
        matches = re.findall(pattern, text.replace("،", ","))
        candidates = [int(m.replace(",", "").replace("٫", "")) for m in matches if 2000000 < int(m.replace(",", "").replace("٫", "")) < 100000000]
        if candidates:
            price = max(candidates)
            break
            
    if not price:
        send_message("❌ ارور: نرخ طلا در پیام‌های اخیر پیدا نشد!")
        exit()

    # 3. ارسال نرخ (بدون شرط تکراری بودن برای تست)
    msg = f"💎 نرخ لحظه‌ای طلای ۱۸ عیار\n🗓 {jdatetime.date.today().strftime('%Y/%m/%d')}\n🕒 بروزرسانی: {datetime.now().strftime('%H:%M')}\n\n💰 هر گرم: {price:,} تومان\n━━━━━━━━━━━━━━━\nطلای ماهان (اسکندری گلد)💎"
    
    send_message(msg)
    print(f"Success: Sent {price}")

except Exception as e:
    send_message(f"❌ ارور سیستم: {str(e)}")
    print(f"Error: {e}")
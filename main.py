import requests
import os
import re
from bs4 import BeautifulSoup
import jdatetime
from datetime import datetime
from zoneinfo import ZoneInfo

# تنظیمات اصلی
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
EITAA_TOKEN = os.environ.get("EITAA_TOKEN")
EITAA_CHAT_ID = os.environ.get("EITAA_CHAT_ID")
CHANNEL_USERNAME = "etjmir"

def to_persian_number(text):
    return str(text).translate(str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹"))

def send_message(text):
    # ارسال تلگرام
    if BOT_TOKEN:
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": text})
    # ارسال ایتا
    if EITAA_TOKEN:
        requests.post(f"https://eitaayar.ir/api/{EITAA_TOKEN}/sendMessage", data={"chat_id": EITAA_CHAT_ID, "text": text})

try:
    url = f"https://t.me/s/{CHANNEL_USERNAME}"
    response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
    soup = BeautifulSoup(response.text, 'html.parser')
    messages = soup.find_all('div', class_='tgme_widget_message_text')
    
    if messages:
        last_message = messages[-1].get_text()
        # شکار قیمت (اعداد ۷ تا ۹ رقمی)
        pattern = r'\d{1,3}[,٫]?\d{3}[,٫]?\d{3}'
        matches = re.findall(pattern, last_message.replace("،", ","))
        prices = [int(m.replace(",", "").replace("٫", "")) for m in matches if 2000000 < int(m.replace(",", "").replace("٫", "")) < 100000000]
        
        if prices:
            current_price = max(prices)
            # بدون هیچ شرطی، تاریخ رو می‌سازیم و می‌فرستیم
            now = datetime.now(ZoneInfo("Asia/Tehran"))
            j_date = jdatetime.date.fromgregorian(date=now.date())
            weekdays = ["دوشنبه", "سه‌شنبه", "چهارشنبه", "پنجشنبه", "جمعه", "شنبه", "یکشنبه"]
            weekday = weekdays[now.weekday()]
            
            msg = f"""💎 نرخ لحظه‌ای طلای ۱۸ عیار
🗓 {to_persian_number(j_date.strftime('%Y/%m/%d'))} | {weekday}
🕒 بروزرسانی: {to_persian_number(now.strftime('%H:%M'))}

💰 هر گرم: {to_persian_number(f'{current_price:,}')} تومان
━━━━━━━━━━━━━━━
طلای ماهان (اسکندری گلد)💎"""
            
            send_message(msg)
            # دیگه هیچ فایلی (last_price) رو چک نمی‌کنیم!
                    
except Exception as e:
    print(f"Error: {e}")
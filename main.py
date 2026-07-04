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
CHANNEL_USERNAME = "etjmir"

def to_persian_number(text):
    # تبدیل اعداد انگلیسی به فارسی
    return str(text).translate(str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹"))

def send_message(text):
    try:
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": text})
    except Exception as e:
        print(f"Telegram Error: {e}")

try:
    # گرفتن قیمت از کانال
    url = f"https://t.me/s/{CHANNEL_USERNAME}"
    response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
    soup = BeautifulSoup(response.text, 'html.parser')
    messages = soup.find_all('div', class_='tgme_widget_message_text')
    
    if messages:
        last_message = messages[-1].get_text()
        
        # شکار اعداد 7 تا 9 رقمی (قیمت‌های طلا)
        pattern = r'\d{1,3}[,٫]?\d{3}[,٫]?\d{3}'
        matches = re.findall(pattern, last_message.replace("،", ","))
        prices = [int(m.replace(",", "").replace("٫", "")) for m in matches if 2000000 < int(m.replace(",", "").replace("٫", "")) < 100000000]
        
        if prices:
            current_price = max(prices)
            
            # بررسی تغییر قیمت
            last_price_file = "last_price.txt"
            last_price = "0"
            if os.path.exists(last_price_file):
                with open(last_price_file, "r", encoding="utf-8") as f:
                    last_price = f.read().strip()
            
            if str(current_price) != last_price:
                # محاسبه زمان و تاریخ به وقت ایران
                now = datetime.now(ZoneInfo("Asia/Tehran"))
                j_date = jdatetime.date.fromgregorian(date=now.date())
                weekdays = ["دوشنبه", "سه‌شنبه", "چهارشنبه", "پنجشنبه", "جمعه", "شنبه", "یکشنبه"]
                weekday = weekdays[now.weekday()]
                
                # قالبِ شیک و رسمیِ موردنظر تو
                msg = f"""💎 نرخ لحظه‌ای طلای ۱۸ عیار
🗓 {to_persian_number(j_date.strftime('%Y/%m/%d'))} | {weekday}
🕒 بروزرسانی: {to_persian_number(now.strftime('%H:%M'))}

💰 هر گرم: {to_persian_number(f'{current_price:,}')} تومان
━━━━━━━━━━━━━━━
طلای ماهان (اسکندری گلد)💎"""
                
                send_message(msg)
                
                # ذخیره قیمت جدید
                with open(last_price_file, "w", encoding="utf-8") as f:
                    f.write(str(current_price))
                    
except Exception as e:
    print(f"Error: {e}")
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
    if BOT_TOKEN and CHAT_ID:
        try:
            requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": text})
        except:
            pass
    # ارسال ایتا
    if EITAA_TOKEN and EITAA_CHAT_ID:
        try:
            requests.post(f"https://eitaayar.ir/api/{EITAA_TOKEN}/sendMessage", data={"chat_id": EITAA_CHAT_ID, "text": text})
        except:
            pass

try:
    url = f"https://t.me/s/{CHANNEL_USERNAME}"
    response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # گرفتن کلِ باکسِ پیام‌ها برای پیدا کردن ID پست
    message_containers = soup.find_all('div', class_='tgme_widget_message')
    
    if message_containers:
        # استخراج آخرین پست
        last_container = message_containers[-1]
        msg_id = last_container.get('data-post', 'unknown')
        
        text_div = last_container.find('div', class_='tgme_widget_message_text')
        if text_div:
            last_message = text_div.get_text()
            
            # شکارچی اعداد
            pattern = r'\d{1,3}[,٫]?\d{3}[,٫]?\d{3}'
            matches = re.findall(pattern, last_message.replace("،", ","))
            
            prices = []
            for m in matches:
                clean_num = int(m.replace(",", "").replace("٫", ""))
                # 🛑 فیلترِ طلایی: فقط اعدادی که بین ۵ میلیون تا ۵۰ میلیون تومان هستند رو قبول کن
                # با این کار اعدادی مثل ۹۳ میلیون یا شماره تلفن‌ها کلاً نادیده گرفته میشن
                if 5000000 < clean_num < 50000000:
                    prices.append(clean_num)
            
            if prices:
                current_price = max(prices)
                
                # چک کردن آیدی پستِ اتحادیه (به جای چک کردن قیمت)
                last_id_file = "last_msg_id.txt"
                last_id = ""
                if os.path.exists(last_id_file):
                    with open(last_id_file, "r", encoding="utf-8") as f:
                        last_id = f.read().strip()
                
                # اگر اتحادیه یک پستِ کاملاً جدید گذاشته بود (حتی با قیمتِ قبلی)
                if msg_id != last_id:
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
                    
                    # ذخیره آیدی پیام برای جلوگیری از اسپم هر ۵ دقیقه
                    with open(last_id_file, "w", encoding="utf-8") as f:
                        f.write(msg_id)
                    print(f"✅ Success! Sent Price: {current_price} from Msg ID: {msg_id}")
                else:
                    print("💤 No new post from the union yet.")
            else:
                print("❌ No valid gold price (between 5m and 50m) found in the last post.")
except Exception as e:
    print(f"Error: {e}")
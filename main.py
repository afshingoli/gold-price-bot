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

def clean_text_for_check(text):
    # حذف فاصله‌ها، نیم‌فاصله‌ها و کشیدگی حروف (ـ) برای مقایسه دقیق و بدون خطا
    return text.replace(" ", "").replace("‌", "").replace("ـ", "").replace("\u200c", "")

try:
    url = f"https://t.me/s/{CHANNEL_USERNAME}"
    response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    message_containers = soup.find_all('div', class_='tgme_widget_message')
    
    current_price = None
    msg_id = None
    
    # 🎯 هشتگ اختصاصی شما
    target_hashtag = "#نرخ‌روزطــلانقــره‌وسکــه‌مشـهدمقــدس"
    cleaned_target = clean_text_for_check(target_hashtag)
    
    # گشتن در پیام‌ها از جدیدترین به قدیمی‌ترین
    if message_containers:
        for container in reversed(message_containers):
            text_div = container.find('div', class_='tgme_widget_message_text')
            if text_div:
                text = text_div.get_text()
                
                # بررسی وجود هشتگ در متن (با حذف خطاهای نگارشی احتمالی تلگرام)
                if cleaned_target in clean_text_for_check(text):
                    # شکارچی قیمت: فقط اعدادی که کاما دارن
                    pattern = r'\d{1,3}[,٫]\d{3}[,٫]\d{3}'
                    matches = re.findall(pattern, text)
                    
                    prices = []
                    for m in matches:
                        clean_num = int(m.replace(",", "").replace("٫", ""))
                        # فیلتر قیمت: فقط بین ۵ تا ۵۰ میلیون تومان
                        if 5000000 < clean_num < 50000000:
                            prices.append(clean_num)
                    
                    if prices:
                        current_price = max(prices)
                        msg_id = container.get('data-post', 'unknown')
                        break # پیدا شد! توقف جستجو
        
        # اگر قیمت و آیدی پیام پیدا شد
        if current_price and msg_id:
            last_id_file = "last_msg_id.txt"
            last_id = ""
            if os.path.exists(last_id_file):
                with open(last_id_file, "r", encoding="utf-8") as f:
                    last_id = f.read().strip()
            
            # ارسال پیام فقط در صورتی که این آیدی جدید باشه
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
                
                with open(last_id_file, "w", encoding="utf-8") as f:
                    f.write(msg_id)
except Exception as e:
    print(f"Error: {e}")
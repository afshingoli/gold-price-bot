import requests
import os
import re
from bs4 import BeautifulSoup

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

def send_message(text):
    try:
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": text})
    except: pass

try:
    url = f"https://t.me/s/etjmir"
    response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
    soup = BeautifulSoup(response.text, 'html.parser')
    messages = soup.find_all('div', class_='tgme_widget_message_text')
    
    if messages:
        last_message = messages[-1].get_text()
        
        # الگوی جدید: شکار هر عددی که بیش از 6 رقم داشته باشه و احتمالا قیمت باشه
        # این الگو اعداد 6 تا 9 رقمی رو پیدا میکنه
        pattern = r'\d{1,3}[,٫]?\d{3}[,٫]?\d{3}'
        matches = re.findall(pattern, last_message.replace("،", ","))
        
        # تبدیل اعداد پیدا شده به عدد خالص
        prices = []
        for m in matches:
            clean_price = int(m.replace(",", "").replace("٫", ""))
            # فیلتر: قیمت باید بین 2 میلیون تا 100 میلیون باشه (طلا و سکه)
            if 2000000 < clean_price < 100000000:
                prices.append(clean_price)
        
        if prices:
            # بزرگترین عدد رو به عنوان نرخ طلای 18 عیار در نظر میگیریم
            current_price = max(prices)
            
            # چک کردن تغییر قیمت
            last_price_file = "last_price.txt"
            last_price = "0"
            if os.path.exists(last_price_file):
                with open(last_price_file, "r", encoding="utf-8") as f:
                    last_price = f.read().strip()
            
            if str(current_price) != last_price:
                message = f"💎 نرخ لحظه‌ای شکار شده از بازار:\n💰 قیمت: {current_price:,} تومان\n━━━━━━━━━━━━━━━\nطلای ماهان (اسکندری گلد)💎"
                send_message(message)
                with open(last_price_file, "w", encoding="utf-8") as f:
                    f.write(str(current_price))
                    
except Exception as e:
    print(f"Error: {e}")
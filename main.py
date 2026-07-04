import requests
import os
import jdatetime
from bs4 import BeautifulSoup
from datetime import datetime

# تنظیمات اصلی
BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]
CHANNEL_ID = "etjmir"

def send_message(text):
    try:
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": text})
    except Exception as e:
        print(f"Telegram Error: {e}")

# گرفتن نرخ از تلگرام
try:
    url = f"https://t.me/s/{CHANNEL_ID}"
    response = requests.get(url, timeout=15)
    soup = BeautifulSoup(response.text, 'html.parser')
    messages = soup.find_all('div', class_='tgme_widget_message_text')
    
    if messages:
        last_message = messages[-1].get_text(separator="\n")
        
        def get_price(keyword):
            for line in last_message.split('\n'):
                if keyword in line:
                    price = ''.join(filter(str.isdigit, line))
                    return price if len(price) > 5 else None
            return None

        price_18 = get_price("گرم‌طلای18عیار") or get_price("18عیار")
        price_emami = get_price("سکهامامی") or get_price("سکه")
        
        # چک کردن تغییرات
        if price_18:
            last_price_file = "last_price.txt"
            last_price = ""
            if os.path.exists(last_price_file):
                with open(last_price_file, "r", encoding="utf-8") as f:
                    last_price = f.read().strip()
            
            if price_18 != last_price:
                message = f"""💎 نرخ‌های لحظه‌ای بازار مشهد
🗓 {jdatetime.date.today().strftime('%Y/%m/%d')}

💰 طلا ۱۸ عیار: {price_18:,} تومان
🥇 سکه امامی: {price_emami:,} تومان
━━━━━━━━━━━━━━━
طلای ماهان"""
                send_message(message)
                with open(last_price_file, "w", encoding="utf-8") as f:
                    f.write(price_18)
except Exception as e:
    print(f"Error: {e}")
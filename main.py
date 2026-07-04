import requests
import os
import re
from bs4 import BeautifulSoup
import jdatetime

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
EITAA_TOKEN = os.environ.get("EITAA_TOKEN")
EITAA_CHAT_ID = os.environ.get("EITAA_CHAT_ID")

def send_message(text):
    # ارسال به تلگرام
    try:
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": text})
    except Exception as e:
        print(f"Telegram Error: {e}")
    # ارسال به ایتا
    if EITAA_TOKEN and EITAA_CHAT_ID:
        try:
            requests.post(f"https://eitaayar.ir/api/{EITAA_TOKEN}/sendMessage", data={"chat_id": EITAA_CHAT_ID, "text": text})
        except Exception as e:
            print(f"Eitaa Error: {e}")

try:
    url = "https://t.me/s/etjmir"
    response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
    soup = BeautifulSoup(response.text, 'html.parser')
    messages = soup.find_all('div', class_='tgme_widget_message_text')
    
    if messages:
        last_message = messages[-1].get_text()
        pattern = r'\d{1,3}[,٫]?\d{3}[,٫]?\d{3}'
        matches = re.findall(pattern, last_message.replace("،", ","))
        prices = [int(m.replace(",", "").replace("٫", "")) for m in matches if 2000000 < int(m.replace(",", "").replace("٫", "")) < 100000000]
        
        if prices:
            current_price = max(prices)
            last_price_file = "last_price.txt"
            last_price = ""
            if os.path.exists(last_price_file):
                with open(last_price_file, "r", encoding="utf-8") as f:
                    last_price = f.read().strip()
            
            if str(current_price) != last_price:
                # فرمت شیک پیام
                msg = f"""💎 نرخ لحظه‌ای طلای ماهان
🗓 {jdatetime.date.today().strftime('%Y/%m/%d')}
🕒 بروزرسانی: {jdatetime.datetime.now().strftime('%H:%M')}

💰 قیمت هر گرم طلا: {current_price:,} تومان

━━━━━━━━━━━━━━━
طلای ماهان (اسکندری گلد)💎"""
                send_message(msg)
                with open(last_price_file, "w", encoding="utf-8") as f:
                    f.write(str(current_price))
except Exception as e:
    print(f"Error: {e}")
import requests
import os
import jdatetime
from bs4 import BeautifulSoup

# تنظیمات اصلی
BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]
# آیدی کانال اتحادیه مشهد
CHANNEL_ID = "etjmir"

def send_message(text):
    try:
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": text})
    except Exception as e:
        print(f"Error: {e}")

# 1. گرفتن نرخ از تلگرام
url = f"https://t.me/s/{CHANNEL_ID}"
try:
    response = requests.get(url, timeout=15)
    soup = BeautifulSoup(response.text, 'html.parser')
    # گرفتن آخرین پیام کانال
    messages = soup.find_all('div', class_='tgme_widget_message_text')
    if messages:
        last_message = messages[-1].get_text(separator="\n")
        
        # استخراج نرخ‌ها با پیدا کردن کلمات کلیدی
        def get_price(keyword):
            for line in last_message.split('\n'):
                if keyword in line:
                    # حذف کاراکترهای غیر عددی
                    price = ''.join(filter(str.isdigit, line))
                    if price: return price
            return "---"

        price_18 = get_price("گرم‌طلای18عیار") or get_price("18عیار")
        price_emami = get_price("سکهامامی") or get_price("سکه")
        
        message = f"""💎 نرخ‌های لحظه‌ای بازار مشهد
🗓 {jdatetime.date.today().strftime('%Y/%m/%d')}

💰 طلا ۱۸ عیار: {price_18} تومان
🥇 سکه امامی: {price_emami} تومان
━━━━━━━━━━━━━━━
طلای ماهان"""
        
        # ارسال فقط در صورت تغییر قیمت (با استفاده از last_price.txt)
        if os.path.exists("last_price.txt"):
            with open("last_price.txt", "r", encoding="utf-8") as f:
                if f.read().strip() == price_18:
                    exit()
        
        send_message(message)
        with open("last_price.txt", "w", encoding="utf-8") as f:
            f.write(price_18)
            
except Exception as e:
    print(f"Error: {e}")
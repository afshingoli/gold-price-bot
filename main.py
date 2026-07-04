import os
import re
import datetime
import requests
from bs4 import BeautifulSoup

# دریافت تنظیمات از گیت‌هاب
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
CHANNEL_USERNAME = "etjmir" 

def to_persian_number(text):
    return str(text).translate(str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹"))

def fa_to_en_number(text):
    return str(text).translate(str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789"))

# تنظیم زمان ایران
tz_iran = datetime.timezone(datetime.timedelta(hours=3, minutes=30))
now_iran = datetime.datetime.now(tz_iran)
time_text = now_iran.strftime("%H:%M")

# تابع ایمن برای خواندن فایل (بدون ایجاد ارور Unicode)
def get_safe_data(filename):
    if not os.path.exists(filename): return None
    try:
        with open(filename, "r", encoding="utf-8", errors="ignore") as f:
            return f.read().strip()
    except: return None

# ۱. دریافت نرخ از کانال اتحادیه
try:
    url = f"https://t.me/s/{CHANNEL_USERNAME}"
    response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
    soup = BeautifulSoup(response.text, 'html.parser')
    messages = soup.find_all('div', class_='tgme_widget_message_text')
    
    price = None
    for msg in reversed(messages):
        text = fa_to_en_number(msg.get_text())
        if any(x in text for x in ["18", "گرم", "عیار"]):
            numbers = re.findall(r'\d{6,9}', text.replace(",", ""))
            for n in numbers:
                if int(n) > 2000000:
                    price = int(n)
                    break
        if price: break
    
    if not price: exit("قیمت پیدا نشد")
except Exception as e:
    exit(f"خطای شبکه: {e}")

# ۲. جلوگیری از ارسال پیام تکراری
last_price = get_safe_data("last_price.txt")
if str(price) == str(last_price):
    print("قیمت تغییری نکرده است.")
    exit()

# ۳. ارسال به تلگرام
message = f"""💎 نرخ لحظه‌ای طلای ۱۸ عیار
🕒 بروزرسانی: {to_persian_number(time_text)}
💰 هر گرم: {to_persian_number(f"{price:,}")} تومان
━━━━━━━━━━━━━━━
طلای ماهان"""

requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", 
              data={"chat_id": CHAT_ID, "text": message})

# ۴. ذخیره قیمت جدید با انکودینگ ایمن
with open("last_price.txt", "w", encoding="utf-8") as f:
    f.write(str(price))

print(f"✅ نرخ {price} با موفقیت ارسال شد.")
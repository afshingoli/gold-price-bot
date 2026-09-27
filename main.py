import os
import json
import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from zoneinfo import ZoneInfo
import jdatetime

# =========================
# CONFIG & SETUP
# =========================
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
EITAA_TOKEN = os.environ.get("EITAA_TOKEN")
EITAA_CHAT_ID = os.environ.get("EITAA_CHAT_ID")
CHANNEL_USERNAME = "etjmir"
STATE_FILE = "bot_state.json"

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
})

# =========================
# HELPERS
# =========================
def to_persian_number(text):
    return str(text).translate(str.maketrans("0123456789.", "۰۱۲۳۴۵۶۷۸۹٫"))

def fa_to_en_number(text):
    return str(text).translate(str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789"))

# =========================
# MAIN LOGIC
# =========================
def main():
    # بارگذاری حافظه ربات
    state = {"last_price": 0, "last_msg_id": ""}
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                state = json.load(f)
        except:
            pass

    try:
        # استخراج دیتای کانال اتحادیه
        url = f"https://t.me/s/{CHANNEL_USERNAME}"
        res = session.get(url, timeout=15)
        soup = BeautifulSoup(res.text, 'html.parser')
        messages = soup.find_all('div', class_='tgme_widget_message')

        current_price = None
        current_msg_id = ""

        # جستجوی نقطه‌زن از جدیدترین پیام به سمت عقب
        for msg in reversed(messages):
            text_div = msg.find('div', class_='tgme_widget_message_text')
            if not text_div: 
                continue
                
            text = fa_to_en_number(text_div.get_text())
            clean_text = text.replace("ـ", "").replace(" ", "").replace("‌", "")

            # فیلتر کلمات کلیدی طلا
            if "عیار" in clean_text or "نرخروزطلانقره" in clean_text:
                numbers = re.findall(r'\d{1,3}(?:[,٫،]\d{3}){1,3}', text)
                if not numbers:
                    numbers = re.findall(r'\d{7,9}', text.replace(",", "").replace("،", ""))
                    
                for n in numbers:
                    clean_num = int(n.replace(",", "").replace("،", ""))
                    # فیلتر رنج دقیق قیمت طلا (حذف اعداد پرت مثل شماره تلفن یا بازدید)
                    if 5000000 < clean_num < 50000000:
                        current_price = clean_num
                        current_msg_id = msg.get('data-post', '')
                        break
                        
            if current_price:
                break

        if not current_price:
            print("⚠️ نرخ معتبری در کانال یافت نشد.")
            return

        # ماشه دوگانه: ارسال در صورت تغییر قیمت یا پست جدید
        if current_price != state["last_price"] or current_msg_id != state["last_msg_id"]:
            now = datetime.now(ZoneInfo("Asia/Tehran"))
            jdate = jdatetime.date.fromgregorian(date=now.date())
            date_text = jdate.strftime("%Y/%m/%d")
            time_text = now.strftime("%H:%M")
            weekdays = ["دوشنبه", "سه‌شنبه", "چهارشنبه", "پنجشنبه", "جمعه", "شنبه", "یکشنبه"]
            weekday = weekdays[now.weekday()]

            message = f"💎 نرخ لحظه‌ای طلای ۱۸ عیار\n🗓 {to_persian_number(date_text)} | {weekday}\n🕒 بروزرسانی: {to_persian_number(time_text)}\n\n💰 هر گرم: {to_persian_number(f'{current_price:,}')} تومان\n━━━━━━━━━━━━━━━\nطلای ماهان (اسکندری گلد)💎"

            # ارسال به تلگرام
            if BOT_TOKEN and CHAT_ID:
                try:
                    session.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": message}, timeout=10)
                    print("✅ تلگرام آپدیت شد.")
                except Exception as e:
                    print(f"❌ خطا در تلگرام: {e}")
                    
            # ارسال به ایتا
            if EITAA_TOKEN and EITAA_CHAT_ID:
                try:
                    res_eitaa = session.post(f"https://eitaayar.ir/api/{EITAA_TOKEN}/sendMessage", data={"chat_id": EITAA_CHAT_ID, "text": message}, timeout=10)
                    print(f"✅ ایتا آپدیت شد. وضعیت: {res_eitaa.status_code}")
                except Exception as e:
                    print(f"❌ خطا در ایتا: {e}")

            # ذخیره وضعیت جدید
            state["last_price"] = current_price
            state["last_msg_id"] = current_msg_id
            with open(STATE_FILE, "w", encoding="utf-8") as f:
                json.dump(state, f)
                
        else:
            print("✅ نرخ تکراری است و تغییری نکرده است.")

    except Exception as e:
        print(f"❌ خطای کلی سیستم: {e}")

if __name__ == "__main__":
    main()
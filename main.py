import os
import re
import json
import logging
from bs4 import BeautifulSoup
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import jdatetime
from datetime import datetime
from zoneinfo import ZoneInfo

# تنظیمات لاگر برای عیب‌یابی دقیق‌تر
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# تنظیمات اصلی
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
EITAA_TOKEN = os.environ.get("EITAA_TOKEN")
EITAA_CHAT_ID = os.environ.get("EITAA_CHAT_ID")
CHANNEL_USERNAME = "etjmir"
STATE_FILE = "bot_state.json"

# تنظیم سشن (Session) با قابلیت تلاش مجدد (Retry) در صورت قطعی شبکه
session = requests.Session()
retry = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
adapter = HTTPAdapter(max_retries=retry)
session.mount('http://', adapter)
session.mount('https://', adapter)
session.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"})

def to_persian_number(text):
    return str(text).translate(str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹"))

def clean_text_for_check(text):
    return text.replace(" ", "").replace("‌", "").replace("ـ", "").replace("\u200c", "")

def send_message(text):
    if BOT_TOKEN and CHAT_ID:
        try:
            session.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": text}, timeout=10)
        except Exception as e:
            logger.error(f"Telegram Send Error: {e}")
    if EITAA_TOKEN and EITAA_CHAT_ID:
        try:
            session.post(f"https://eitaayar.ir/api/{EITAA_TOKEN}/sendMessage", data={"chat_id": EITAA_CHAT_ID, "text": text}, timeout=10)
        except Exception as e:
            logger.error(f"Eitaa Send Error: {e}")

def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error reading state file: {e}")
    return {"id": "", "price": 0, "time": ""}

def save_state(msg_id, price):
    state_data = {
        "id": msg_id,
        "price": price,
        "time": datetime.now(ZoneInfo("Asia/Tehran")).isoformat()
    }
    tmp_file = STATE_FILE + ".tmp"
    try:
        # Atomic write: اول در یک فایل موقت می‌نویسیم، بعد جایگزین می‌کنیم تا فایل خراب نشود
        with open(tmp_file, "w", encoding="utf-8") as f:
            json.dump(state_data, f, indent=4)
        os.replace(tmp_file, STATE_FILE)
    except Exception as e:
        logger.error(f"Error saving state: {e}")

def extract_price_from_text(full_text):
    # فقط خطی که کلمه "عیار" دارد را جدا می‌کنیم تا با قیمت سکه قاطی نشود
    lines = full_text.split('\n')
    for line in lines:
        if "عیار" in line:
            # رگکس پیشرفته برای گرفتن اعداد فارسی و انگلیسی با کاما یا نقطه
            pattern = r'[\d۰-۹]{1,3}[,٫.][\d۰-۹]{3}[,٫.][\d۰-۹]{3}'
            matches = re.findall(pattern, line)
            for m in matches:
                # تبدیل اعداد فارسی به انگلیسی و حذف جداکننده‌ها
                m_eng = m.translate(str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789"))
                clean_num = int(m_eng.replace(",", "").replace("٫", "").replace(".", ""))
                # محکم‌کاریِ نهایی: قیمت طلای 18 عیار در این محدوده است
                if 5000000 < clean_num < 50000000:
                    return clean_num
    return None

try:
    url = f"https://t.me/s/{CHANNEL_USERNAME}"
    response = session.get(url, timeout=15)
    response.raise_for_status() # توقف برنامه در صورت ارور گرفتن از تلگرام
    soup = BeautifulSoup(response.text, 'html.parser')
    
    message_containers = soup.find_all('div', class_='tgme_widget_message')
    
    current_price = None
    msg_id = None
    
    target_hashtag = "#نرخ‌روزطــلانقــره‌وسکــه‌مشـهدمقــدس"
    cleaned_target = clean_text_for_check(target_hashtag)
    
    if message_containers:
        for container in reversed(message_containers):
            text_div = container.find('div', class_='tgme_widget_message_text')
            if text_div:
                # جایگزین کردن تگ‌های br با \n برای جدا کردن دقیق خطوط
                for br in text_div.find_all("br"):
                    br.replace_with("\n")
                
                text = text_div.get_text()
                
                if cleaned_target in clean_text_for_check(text):
                    extracted_price = extract_price_from_text(text)
                    if extracted_price:
                        current_price = extracted_price
                        msg_id = container.get('data-post', 'unknown')
                        break
        
        if current_price and msg_id:
            last_state = load_state()
            
            # اگر آیدی پست عوض شده بود، یا قیمت تغییر کرده بود
            if str(msg_id) != str(last_state.get("id")) or current_price != last_state.get("price"):
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
                save_state(msg_id, current_price)
                logger.info(f"✅ Updated! Sent ID: {msg_id}, Price: {current_price}")
            else:
                logger.info("💤 No new post and no price changes.")
        else:
            logger.warning("❌ Target hashtag found, but no valid price extracted from the 'عیار' line.")
except Exception as e:
    logger.error(f"Critical System Error: {e}")
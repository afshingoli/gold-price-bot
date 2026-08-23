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
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
EITAA_TOKEN = os.getenv("EITAA_TOKEN")
EITAA_CHAT_ID = os.getenv("EITAA_CHAT_ID")
ABSHODE_CHAT_ID = "@AbshodeEskandariGold"

UNION_CHANNEL_URL = "https://t.me/s/etjmir"
TSDAYAN_CHANNEL_URL = "https://t.me/s/TSdayan"
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

def format_price(price):
    return to_persian_number(f"{price:,}")

def normalize_number(text):
    return text.replace(",", "").replace("٫", "").replace(".", "").replace(" ", "").translate(str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789"))

def extract_price(text):
    patterns = [
        r"\d{1,3}(?:[,٫،]\d{3}){1,3}",
        r"\d{7,9}"
    ]
    for p in patterns:
        m = re.search(p, text)
        if m:
            return int(normalize_number(m.group()))
    return None

# =========================
# NETWORK
# =========================
def send_to_api(url, data, name):
    try:
        res = session.post(url, data=data, timeout=15)
        res.raise_for_status()
        print(f"✅ Sent successfully to {name}")
    except Exception as e:
        print(f"❌ Error sending to {name}: {e}")

# =========================
# SCRAPER 1: ETJMIR (ضد ویرایش)
# =========================
def get_etjmir_data():
    try:
        r = session.get(UNION_CHANNEL_URL, timeout=15)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        
        posts = soup.find_all("div", class_="tgme_widget_message")
        for post in reversed(posts[-10:]):
            text_div = post.find("div", class_="tgme_widget_message_text")
            if not text_div:
                continue
            text = text_div.get_text("\n")
            
            clean_text = text.replace("ـ", "").replace(" ", "").replace("‌", "")
            if "نرخروزطلانقره" in clean_text or "عیار" in text:
                price = extract_price(text)
                if price and 5_000_000 < price < 50_000_000:
                    msg_id = post.get("data-post", "")
                    return {"price": price, "msg_id": msg_id}
    except Exception as e:
        print(f"❌ Scraper Error (etjmir): {e}")
    return None

# =========================
# SCRAPER 2: TSDAYAN (+10 و قالب جدید)
# =========================
def get_tsdayan_data():
    try:
        r = session.get(TSDAYAN_CHANNEL_URL, timeout=15)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        posts = soup.find_all("div", class_="tgme_widget_message")
        
        for post in reversed(posts[-3:]):
            text_div = post.find("div", class_="tgme_widget_message_text")
            if not text_div:
                continue
            text = text_div.get_text("\n")
            msg_id = post.get("data-post", "")
            
            if "نقد فردا" in text and "🔴" in text:
                
                # استخراج‌کننده هوشمند اعداد با قابلیت افزودن 10 واحد
                def extract_nums(pattern, input_text):
                    m = re.search(pattern, input_text, re.DOTALL)
                    if m:
                        def clean_and_add(s):
                            s = s.replace(",", "").replace("،", "").translate(str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789"))
                            new_num = int(s) + 10
                            return f"{new_num:,}"
                        try:
                            return clean_and_add(m.group(1)), clean_and_add(m.group(2))
                        except:
                            pass
                    return None, None

                # گرفتن اعداد نقد فردا
                f_red, f_blue = extract_nums(r'نقد\s*فردا.*?🔴\s*([\d,،۰-۹]+).*?🔵\s*([\d,،۰-۹]+)', text)
                # گرفتن اعداد نقد پس‌فردا
                p_red, p_blue = extract_nums(r'نقد\s*پس.*?فردا.*?🔴\s*([\d,،۰-۹]+).*?🔵\s*([\d,،۰-۹]+)', text)
                
                # اگر هر ۴ عدد با موفقیت استخراج و +10 شدند
                if f_red and f_blue and p_red and p_blue:
                    # قالب‌بندی جدید دقیقاً مشابه درخواست کاربر
                    formatted_msg = f"""💰 نرخ نقدی طلای آبشده اسکندری
🔴 نقد فردا: {f_red}
🔵 نقد فردا: {f_blue}
━━━━━━━━━━━━
🔴 نقد پس‌فردا: {p_red}
🔵 نقد پس‌فردا: {p_blue}
@AbshodeEskandariGold"""
                    return {"text": formatted_msg, "msg_id": msg_id}
    except Exception as e:
        print(f"❌ Scraper Error (TSdayan): {e}")
    return None

# =========================
# STATE MANAGEMENT
# =========================
def load_state():
    default_state = {
        "last_price": 0,
        "last_msg_id": "",
        "last_tsdayan_text": "",
        "last_tsdayan_msg_id": ""
    }
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                for key in default_state:
                    if key not in data:
                        data[key] = default_state[key]
                return data
        except:
            pass
    return default_state

def save_state(state):
    tmp = STATE_FILE + ".tmp"
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=4)
        os.replace(tmp, STATE_FILE)
    except Exception as e:
        print(f"❌ State Save Error: {e}")

# =========================
# MAIN LOGIC
# =========================
def main():
    state = load_state()
    now = datetime.now(ZoneInfo("Asia/Tehran"))
    jdate = jdatetime.date.fromgregorian(date=now.date())
    date_text = jdate.strftime("%Y/%m/%d")
    time_text = now.strftime("%H:%M")
    weekdays = ["دوشنبه","سه‌شنبه","چهارشنبه","پنجشنبه","جمعه","شنبه","یکشنبه"]
    weekday = weekdays[now.weekday()]

    # ------------------------------------------------
    # شاخه اول: کانال اصلی
    # ------------------------------------------------
    etjmir_data = get_etjmir_data()
    if etjmir_data:
        current_price = etjmir_data["price"]
        current_msg_id = etjmir_data["msg_id"]
        
        # ماشه دوگانه برای کانال اول (جلوگیری از خطای ویرایش پست)
        if (current_msg_id != state.get("last_msg_id")) or (current_price != state.get("last_price")):
            
            msg_main = f"💎 نرخ لحظه‌ای طلای ۱۸ عیار\n🗓 {to_persian_number(date_text)} | {weekday}\n🕒 بروزرسانی: {to_persian_number(time_text)}\n\n💰 هر گرم: {format_price(current_price)} تومان\n━━━━━━━━━━━━━━━\nطلای ماهان (اسکندری گلد)💎"
            
            if BOT_TOKEN and CHAT_ID:
                url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
                send_to_api(url, {"chat_id": CHAT_ID, "text": msg_main}, "Telegram (Main)")
                
            if EITAA_TOKEN and EITAA_CHAT_ID:
                url = f"https://eitaayar.ir/api/{EITAA_TOKEN}/sendMessage"
                send_to_api(url, {"chat_id": EITAA_CHAT_ID, "text": msg_main}, "Eitaa (Main)")
                
            state["last_msg_id"] = current_msg_id
            state["last_price"] = current_price
        else:
            print("✅ Etjmir: No new post and no price change.")
    else:
        print("⚠️ Etjmir: Could not find valid price or post.")

    # ------------------------------------------------
    # شاخه دوم: کانال آبشده (+10 و قالب جدید)
    # ------------------------------------------------
    tsdayan_data = get_tsdayan_data()
    if tsdayan_data:
        current_text = tsdayan_data["text"]
        current_msg_id = tsdayan_data["msg_id"]
        
        # ماشه دوگانه برای کانال دوم
        if (current_msg_id != state.get("last_tsdayan_msg_id")) or (current_text != state.get("last_tsdayan_text")):
            
            if BOT_TOKEN and ABSHODE_CHAT_ID:
                url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
                send_to_api(url, {"chat_id": ABSHODE_CHAT_ID, "text": current_text}, "Telegram (Abshode)")
                
            state["last_tsdayan_msg_id"] = current_msg_id
            state["last_tsdayan_text"] = current_text
        else:
            print("✅ TSdayan: No new changes.")
    else:
        print("⚠️ TSdayan: Could not find target pattern in recent posts.")

    save_state(state)

if __name__ == "__main__":
    main()
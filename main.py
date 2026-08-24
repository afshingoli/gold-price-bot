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
DAILY_PRICES_FILE = "daily_prices.txt"

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

def send_to_api(url, data, name):
    try:
        res = session.post(url, data=data, timeout=15)
        res.raise_for_status()
        print(f"✅ Sent successfully to {name}")
    except Exception as e:
        print(f"❌ Error sending to {name}: {e}")

# =========================
# SCRAPERS
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

                f_red, f_blue = extract_nums(r'نقد\s*فردا.*?🔴\s*([\d,،۰-۹]+).*?🔵\s*([\d,،۰-۹]+)', text)
                p_red, p_blue = extract_nums(r'نقد\s*پس.*?فردا.*?🔴\s*([\d,،۰-۹]+).*?🔵\s*([\d,،۰-۹]+)', text)
                
                if f_red and f_blue and p_red and p_blue:
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
        "last_tsdayan_msg_id": "",
        "date": "",
        "eitaa_930": False,
        "eitaa_1400": False,
        "eitaa_1700": False,
        "summary_2100": False
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

def save_daily_price(price):
    try:
        with open(DAILY_PRICES_FILE, "a", encoding="utf-8") as f:
            f.write(f"{price}\n")
    except Exception:
        pass

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
    
    current_date_str = now.strftime("%Y-%m-%d")
    
    # ------------------------------------------------
    # ریست کردن حافظه برای روز جدید
    # ------------------------------------------------
    if state["date"] != current_date_str:
        state["date"] = current_date_str
        state["eitaa_930"] = False
        state["eitaa_1400"] = False
        state["eitaa_1700"] = False
        state["summary_2100"] = False
        # پاک کردن قیمت‌های روز گذشته
        try:
            with open(DAILY_PRICES_FILE, "w", encoding="utf-8") as f:
                f.write("")
        except Exception:
            pass

    # ------------------------------------------------
    # ۱. کانال اصلی طلا (اسکن اتحادیه)
    # ------------------------------------------------
    etjmir_data = get_etjmir_data()
    if etjmir_data:
        current_price = etjmir_data["price"]
        current_msg_id = etjmir_data["msg_id"]
        
        # ذخیره قیمت برای محاسبه خلاصه شبانه
        save_daily_price(current_price)
        
        msg_main = f"💎 نرخ لحظه‌ای طلای ۱۸ عیار\n🗓 {to_persian_number(date_text)} | {weekday}\n🕒 بروزرسانی: {to_persian_number(time_text)}\n\n💰 هر گرم: {format_price(current_price)} تومان\n━━━━━━━━━━━━━━━\nطلای ماهان (اسکندری گلد)💎"
        
        # الف) ارسال به تلگرام (در لحظه و سریع)
        if (current_msg_id != state.get("last_msg_id")) or (current_price != state.get("last_price")):
            if BOT_TOKEN and CHAT_ID:
                url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
                send_to_api(url, {"chat_id": CHAT_ID, "text": msg_main}, "Telegram (Main)")
            state["last_msg_id"] = current_msg_id
            state["last_price"] = current_price

        # ب) ارسال به ایتا (فقط راس ساعت‌های مقرر)
        h = now.hour
        m = now.minute
        
        # پیام ساعت ۹:۳۰ صبح ایتا
        if h == 9 and m >= 30 and not state["eitaa_930"]:
            if EITAA_TOKEN and EITAA_CHAT_ID:
                url = f"https://eitaayar.ir/api/{EITAA_TOKEN}/sendMessage"
                send_to_api(url, {"chat_id": EITAA_CHAT_ID, "text": msg_main}, "Eitaa (09:30)")
            state["eitaa_930"] = True

        # پیام ساعت ۲:۰۰ ظهر ایتا
        if h == 14 and m >= 0 and not state["eitaa_1400"]:
            if EITAA_TOKEN and EITAA_CHAT_ID:
                url = f"https://eitaayar.ir/api/{EITAA_TOKEN}/sendMessage"
                send_to_api(url, {"chat_id": EITAA_CHAT_ID, "text": msg_main}, "Eitaa (14:00)")
            state["eitaa_1400"] = True

        # پیام ساعت ۵:۰۰ عصر ایتا
        if h == 17 and m >= 0 and not state["eitaa_1700"]:
            if EITAA_TOKEN and EITAA_CHAT_ID:
                url = f"https://eitaayar.ir/api/{EITAA_TOKEN}/sendMessage"
                send_to_api(url, {"chat_id": EITAA_CHAT_ID, "text": msg_main}, "Eitaa (17:00)")
            state["eitaa_1700"] = True

    # ------------------------------------------------
    # ۲. کانال آبشده (در لحظه و سریع برای تلگرام)
    # ------------------------------------------------
    tsdayan_data = get_tsdayan_data()
    if tsdayan_data:
        current_text = tsdayan_data["text"]
        current_msg_id = tsdayan_data["msg_id"]
        
        if (current_msg_id != state.get("last_tsdayan_msg_id")) or (current_text != state.get("last_tsdayan_text")):
            if BOT_TOKEN and ABSHODE_CHAT_ID:
                url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
                send_to_api(url, {"chat_id": ABSHODE_CHAT_ID, "text": current_text}, "Telegram (Abshode)")
            state["last_tsdayan_msg_id"] = current_msg_id
            state["last_tsdayan_text"] = current_text

    # ------------------------------------------------
    # ۳. گزارش خلاصه بازار (رأس ساعت ۹ شب / ۲۱:۰۰)
    # ------------------------------------------------
    if now.hour >= 21 and not state["summary_2100"]:
        try:
            if os.path.exists(DAILY_PRICES_FILE):
                with open(DAILY_PRICES_FILE, "r", encoding="utf-8") as f:
                    lines = [int(line.strip()) for line in f.readlines() if line.strip().isdigit()]
                
                if lines:
                    open_price = lines[0]
                    close_price = lines[-1]
                    high_price = max(lines)
                    low_price = min(lines)
                    
                    diff = close_price - open_price
                    diff_sign = "🔺 +" if diff > 0 else ("🔻 " if diff < 0 else "🔹 ")
                    
                    summary_msg = f"""📊 پرونده بازار امروز بسته شد!
🗓 {weekday} | {to_persian_number(date_text)}
🕒 ساعت گزارش: {to_persian_number(time_text)}

🔸 بازگشایی صبح: {format_price(open_price)} تومان
📈 بالاترین نرخ: {format_price(high_price)} تومان
📉 پایین‌ترین نرخ: {format_price(low_price)} تومان
💰 آخرین نرخ: {format_price(close_price)} تومان

برآیند امروز:
{diff_sign}{format_price(abs(diff))} تومان

━━━━━━━━━━━━━━━
#گزارش_روزانه #تحلیل_بازار 
طلای ماهان (اسکندری گلد)💎"""
                    
                    # ارسال گزارش شبانه به تلگرام و ایتا
                    if BOT_TOKEN and CHAT_ID:
                        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
                        send_to_api(url, {"chat_id": CHAT_ID, "text": summary_msg}, "Telegram (Summary)")
                    if EITAA_TOKEN and EITAA_CHAT_ID:
                        url = f"https://eitaayar.ir/api/{EITAA_TOKEN}/sendMessage"
                        send_to_api(url, {"chat_id": EITAA_CHAT_ID, "text": summary_msg}, "Eitaa (Summary)")
                        
            state["summary_2100"] = True
        except Exception as e:
            print(f"❌ Summary Error: {e}")

    save_state(state)

if __name__ == "__main__":
    main()
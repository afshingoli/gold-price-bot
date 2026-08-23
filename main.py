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

CHANNEL_URL = "https://t.me/s/etjmir"
TSDAYAN_URL = "https://t.me/s/TSdayan"
ABSHODE_CHAT_ID = "@AbshodeEskandariGold"

STATE_FILE = "bot_state.json"

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
})

# =========================
# HELPERS (FORMATTING & MATH)
# =========================
def to_persian_number(text):
    return str(text).translate(str.maketrans("0123456789.", "۰۱۲۳۴۵۶۷۸۹٫"))

def format_price(price):
    return to_persian_number(f"{price:,}")

def normalize_number(text):
    return text.replace(",", "").replace("٫", "").replace(".", "").replace(" ", "")

def extract_price(text):
    patterns = [
        r"\d{1,3}(?:[,٫]\d{3}){1,3}",
        r"\d{7,9}"
    ]
    for p in patterns:
        m = re.search(p, text)
        if m:
            return int(normalize_number(m.group()))
    return None

def calculate_percent_change(old, new):
    if old == 0:
        return 0
    change = ((new - old) / old) * 100
    return round(change, 2)

# =========================
# NETWORK & MESSAGING
# =========================
def send_to_api(url, data, name):
    try:
        res = session.post(url, data=data, timeout=15)
        res.raise_for_status() 
        print(f"✅ Sent successfully to {name}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Error sending to {name}:\nUrl: {url}\nDetails: {e}")
        if hasattr(e, 'response') and e.response is not None:
             print(f"❌ Server Response: {e.response.text}")

def send_message(text):
    # ارسال به تلگرام (شاخه اصلی)
    if BOT_TOKEN and CHAT_ID:
        tg_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        send_to_api(tg_url, {"chat_id": CHAT_ID, "text": text}, "Telegram")
    else:
        print("⚠️ Telegram token or chat_id is missing.")
        
    # ارسال به ایتا
    if EITAA_TOKEN and EITAA_CHAT_ID:
        eitaa_url = f"https://eitaayar.ir/api/{EITAA_TOKEN}/sendMessage"
        send_to_api(eitaa_url, {"chat_id": EITAA_CHAT_ID, "text": text}, "Eitaa")
    else:
        print("⚠️ Eitaa token or chat_id is missing.")

# =========================
# SCRAPERS
# =========================
def get_price():
    try:
        r = session.get(CHANNEL_URL, timeout=15)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        
        posts = soup.find_all("div", class_="tgme_widget_message_text")
        for post in reversed(posts[-5:]):
            lines = post.get_text("\n").split("\n")
            for line in lines:
                if "۱۸" in line or "18" in line or "عیار" in line:
                    price = extract_price(line)
                    if price and 3_000_000 < price < 20_000_000:
                        return price
        return None
    except Exception as e:
        print(f"❌ Scraper Error: {e}")
        return None

def get_and_modify_tsdayan():
    try:
        r = session.get(TSDAYAN_URL, timeout=15)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        
        posts = soup.find_all("div", class_="tgme_widget_message_text")
        for post in reversed(posts[-3:]):
            text = post.get_text("\n")
            if "نقد فردا" in text and ("🔴" in text or "🔵" in text):
                
                # تابع هوشمند برای استخراج، جمع با ۱۰ و فرمت دوباره
                def add_10(match):
                    symbol = match.group(1)
                    num_str = match.group(2).replace(",", "").replace("،", "")
                    num_str = num_str.translate(str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789"))
                    try:
                        new_num = int(num_str) + 10
                        return f"{symbol} {new_num:,}"
                    except:
                        return match.group(0)

                # جایگزینی الگوها تو کل متن
                modified_text = re.sub(r'(🔴|🔵)\s*([0-9۰-۹,،]+)', add_10, text)
                return modified_text
        return None
    except Exception as e:
        print(f"❌ Scraper Error (TSdayan): {e}")
        return None

# =========================
# STATE MANAGEMENT
# =========================
def load_state():
    default_state = {
        "date": "",
        "day_start_price": 0,
        "last_price": 0,
        "high": 0,
        "low": float('inf'),
        "summary_sent": False,
        "week_start_price": 0,
        "weekly_summary_sent": False,
        "last_tsdayan_text": ""  # حافظه جدید برای کانال آبشده
    }
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                for key in default_state:
                    if key not in data:
                        data[key] = default_state[key]
                
                if data.get("high", 0) > 20_000_000 or data.get("day_start_price", 0) > 20_000_000:
                    print("⚠️ Auto-Heal: دیتابیس خراب بود (اعداد نجومی یافت شد). حافظه ریست شد.")
                    return default_state
                    
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
    # شاخه اول: کانال اصلی طلا (بدون هیچ تغییری)
    # ------------------------------------------------
    current_price = get_price()
    if current_price:
        current_date_str = now.strftime("%Y-%m-%d")

        if state["date"] != current_date_str:
            state["date"] = current_date_str
            state["day_start_price"] = current_price
            state["high"] = current_price
            state["low"] = current_price
            state["summary_sent"] = False
            
            if now.weekday() == 5: 
                state["week_start_price"] = current_price
                state["weekly_summary_sent"] = False

        if state["week_start_price"] == 0:
            state["week_start_price"] = current_price

        if current_price > state["high"]: state["high"] = current_price
        if current_price < state["low"]: state["low"] = current_price

        if current_price != state["last_price"] and state["last_price"] != 0:
            diff = current_price - state["last_price"]
            
            if diff > 0:
                trend = f"🔺 افزایش نسبت به قبل: {format_price(diff)} تومان"
                hashtag = "#صعودی 🚀" if diff >= 50_000 else "#افزایش_قیمت 📈"
            else:
                trend = f"🔻 کاهش نسبت به قبل: {format_price(abs(diff))} تومان"
                hashtag = "#سقوط_قیمت 📉" if abs(diff) >= 50_000 else "#کاهش_قیمت 🔻"

            msg = f"""💎 نرخ لحظه‌ای طلای ۱۸ عیار
🗓 {weekday} | {to_persian_number(date_text)}
🕒 بروزرسانی: {to_persian_number(time_text)}

💰 هر گرم: {format_price(current_price)} تومان
{trend}

━━━━━━━━━━━━━━━
{hashtag} #طلا 
طلای ماهان (اسکندری گلد)💎"""
            send_message(msg)

        state["last_price"] = current_price

        is_evening = (now.hour > 20) or (now.hour == 20 and now.minute >= 30)
        
        if is_evening and not state["summary_sent"]:
            daily_diff = current_price - state["day_start_price"]
            daily_percent = calculate_percent_change(state["day_start_price"], current_price)
            
            if daily_diff > 0:
                daily_trend = f"🔺 رشد {to_persian_number(abs(daily_percent))}٪ ({format_price(abs(daily_diff))} تومان سود)"
            elif daily_diff < 0:
                daily_trend = f"🔻 افت {to_persian_number(abs(daily_percent))}٪ ({format_price(abs(daily_diff))} تومان افت)"
            else:
                daily_trend = "➖ بدون تغییر نسبت به صبح"

            daily_msg = f"""📊 پرونده بازار امروز بسته شد!
🗓 {weekday} | {to_persian_number(date_text)}

🔸 بازگشایی صبح: {format_price(state["day_start_price"])}
📈 بالاترین نرخ: {format_price(state["high"])}
📉 پایین‌ترین نرخ: {format_price(state["low"])}
💰 آخرین نرخ: {format_price(current_price)}

برآیند امروز:
{daily_trend}

━━━━━━━━━━━━━━━
#گزارش_روزانه #تحلیل_بازار 
طلای ماهان (اسکندری گلد)💎"""
            send_message(daily_msg)
            state["summary_sent"] = True

        if now.weekday() == 3 and is_evening and not state["weekly_summary_sent"]:
            weekly_diff = current_price - state["week_start_price"]
            weekly_percent = calculate_percent_change(state["week_start_price"], current_price)
            
            if weekly_diff > 0:
                weekly_status = f"🟢 بازار صعودی بود و {to_persian_number(abs(weekly_percent))}٪ رشد کرد."
            elif weekly_diff < 0:
                weekly_status = f"🔴 بازار نزولی بود و {to_persian_number(abs(weekly_percent))}٪ افت کرد."
            else:
                weekly_status = "⚪️ بازار این هفته تقریباً ثابت بود."

            weekly_msg = f"""🗓 پرونده ویژه آخر هفته!
از شنبه تا پنجشنبه چه گذشت؟ 

شروع هفته (شنبه): {format_price(state["week_start_price"])}
پایان هفته (پنجشنبه): {format_price(current_price)}
اختلاف: {format_price(abs(weekly_diff))} تومان

وضعیت کلی:
{weekly_status}

━━━━━━━━━━━━━━━
#پرونده_هفته #طلا_اقتصادی
طلای ماهان (اسکندری گلد)💎"""
            send_message(weekly_msg)
            state["weekly_summary_sent"] = True
    else:
        print("⚠️ No valid price found in the main channel.")

    # ------------------------------------------------
    # شاخه دوم: کانال آبشده (TSdayan)
    # ------------------------------------------------
    tsdayan_text = get_and_modify_tsdayan()
    
    # مقایسه با دیتابیس تا متن تکراری نفرستیم
    if tsdayan_text and tsdayan_text != state.get("last_tsdayan_text", ""):
        msg_abshode = f"""📊 بروزرسانی نرخ آبشده
🕒 {to_persian_number(time_text)}

{to_persian_number(tsdayan_text)}

━━━━━━━━━━━━━━━
طلای ماهان (اسکندری گلد)💎"""
        
        # ارسال مستقیم به کانال آبشده
        if BOT_TOKEN:
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
            send_to_api(url, {"chat_id": ABSHODE_CHAT_ID, "text": msg_abshode}, "Telegram (Abshode)")
            
        state["last_tsdayan_text"] = tsdayan_text

    # ذخیره نهایی
    save_state(state)

if __name__ == "__main__":
    main()
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
    except Exception as e:
        print(f"❌ Error sending to {name}: {e}")

def send_message(text):
    if BOT_TOKEN and CHAT_ID:
        tg_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        send_to_api(tg_url, {"chat_id": CHAT_ID, "text": text}, "Telegram")
        
    if EITAA_TOKEN and EITAA_CHAT_ID:
        eitaa_url = f"https://eitaayar.ir/api/{EITAA_TOKEN}/sendMessage"
        send_to_api(eitaa_url, {"chat_id": EITAA_CHAT_ID, "text": text}, "Eitaa")

# =========================
# SCRAPER (ROBUST)
# =========================
def get_price():
    try:
        r = session.get(CHANNEL_URL, timeout=15)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        
        # بررسی ۵ پیام آخر کانال برای جلوگیری از گم شدن قیمت بین پیام‌های متفرقه
        posts = soup.find_all("div", class_="tgme_widget_message_text")
        for post in reversed(posts[-5:]):
            text = post.get_text("\n")
            if "۱۸" in text or "18" in text or "عیار" in text:
                price = extract_price(text)
                # فیلتر منطقی قیمت (بین ۵ تا ۱۰۰ میلیون تومان)
                if price and 5_000_000 < price < 100_000_000:
                    return price
        return None
    except Exception as e:
        print(f"❌ Scraper Error: {e}")
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
        "weekly_summary_sent": False
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
    current_price = get_price()
    if not current_price:
        print("⚠️ No valid price found.")
        return

    now = datetime.now(ZoneInfo("Asia/Tehran"))
    current_date_str = now.strftime("%Y-%m-%d")
    state = load_state()

    jdate = jdatetime.date.fromgregorian(date=now.date())
    date_text = jdate.strftime("%Y/%m/%d")
    time_text = now.strftime("%H:%M")
    
    weekdays = ["دوشنبه","سه‌شنبه","چهارشنبه","پنجشنبه","جمعه","شنبه","یکشنبه"]
    weekday = weekdays[now.weekday()]

    # ۱. مدیریت تغییر روز و هفته
    if state["date"] != current_date_str:
        state["date"] = current_date_str
        state["day_start_price"] = current_price
        state["high"] = current_price
        state["low"] = current_price
        state["summary_sent"] = False
        
        # اگر شنبه است، هفته جدید رو استارت بزن
        if now.weekday() == 5: 
            state["week_start_price"] = current_price
            state["weekly_summary_sent"] = False

    # مقداردهی اولیه هفته (برای اولین اجرای ربات)
    if state["week_start_price"] == 0:
        state["week_start_price"] = current_price

    # آپدیت بالاترین و پایین‌ترین نرخ امروز
    if current_price > state["high"]: state["high"] = current_price
    if current_price < state["low"]: state["low"] = current_price

    # ۲. ارسال پیام لحظه‌ای (در صورت تغییر قیمت)
    if current_price != state["last_price"] and state["last_price"] != 0:
        diff = current_price - state["last_price"]
        
        # فلش‌ها و هشتگ‌های هوشمند
        if diff > 0:
            trend = f"🔺 افزایش نسبت به قبل: {format_price(diff)} تومان"
            hashtag = "#صعودی 🚀" if diff >= 50000 else "#افزایش_قیمت 📈"
        else:
            trend = f"🔻 کاهش نسبت به قبل: {format_price(abs(diff))} تومان"
            hashtag = "#سقوط_قیمت 📉" if abs(diff) >= 50000 else "#کاهش_قیمت 🔻"

        msg = f"""💎 نرخ لحظه‌ای طلای ۱۸ عیار
🗓 {weekday} | {to_persian_number(date_text)}
🕒 بروزرسانی: {to_persian_number(time_text)}

💰 هر گرم: {format_price(current_price)} تومان
{trend}

━━━━━━━━━━━━━━━
{hashtag} #طلا 
طلای ماهان (اسکندری گلد)💎"""
        
        send_message(msg)

    # ذخیره قیمت فعلی برای مقایسه بعدی
    state["last_price"] = current_price

    # ۳. گزارش پایانی روز (رأس ساعت ۲۰:۳۰ به بعد)
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

    # ۴. گزارش ویژه آخر هفته (پنجشنبه‌ها ساعت ۲۰:۳۰)
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

    # ذخیره نهایی
    save_state(state)

if __name__ == "__main__":
    main()
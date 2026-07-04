import os
import requests
from datetime import datetime
from zoneinfo import ZoneInfo

# تنظیم توکن‌ها و آیدی‌ها از سکرت‌های گیت‌هاب
BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

# متغیرهای ایتا (اگر در گیت‌هاب ست کرده باشی خودکار کار می‌کنند)
EITAA_TOKEN = os.environ.get("EITAA_TOKEN")
EITAA_CHAT_ID = os.environ.get("EITAA_CHAT_ID")

API_URL = "http://et.tala.ir/webservice/haghanigold.com/6397dbw8333f095bb55cd539f865a994"

def to_persian_number(text):
    return str(text).translate(str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹"))

# ۱. گرفتن قیمت لحظه‌ای از API
try:
    data = requests.get(API_URL, timeout=10).json()
except Exception as e:
    print("API ERROR:", e)
    exit()

price = data["geram18"]["value"] // 10
price_text = f"{price:,}"

# محاسبه زمان و تاریخ دقیق تهران
now = datetime.now(ZoneInfo("Asia/Tehran"))
weekdays = ["دوشنبه", "سه‌شنبه", "چهارشنبه", "پنجشنبه", "جمعه", "شنبه", "یکشنبه"]
weekday = weekdays[now.weekday()]
time_text = now.strftime("%H:%M")
today_str = now.strftime("%Y-%m-%d")

# 📊 ۲. ذخیره قیمت در آرشیو روزانه (برای محاسبه سوابق امروز)
try:
    with open("daily_prices.txt", "a") as f:
        f.write(f"{price}\n")
except Exception as e:
    print("Error saving daily price:", e)

# 📈 ۳. منطق ارسال گزارش خلاصه وضعیت پایان روز (ساعت ۸ شب به بعد)
try:
    with open("last_summary_date.txt", "r") as f:
        last_summary = f.read().strip()
except:
    last_summary = ""

# اگر ساعت از ۲۰ (۸ شب) گذشته بود و امروز هنوز گزارش پایانی نفرستاده بودیم
if now.hour >= 20 and last_summary != today_str:
    try:
        with open("daily_prices.txt", "r") as f:
            lines = f.readlines()
        
        # تبدیل خطوط فایل به اعداد صحیح
        prices = [int(line.strip()) for line in lines if line.strip().isdigit()]
        
        if prices:
            open_p = prices[0]       # اولین قیمت ثبت شده در روز
            high_p = max(prices)     # بالاترین قیمت روز
            low_p = min(prices)      # پایین‌ترین قیمت روز
            close_p = prices[-1]     # آخرین قیمت روز (قیمت پایانی)
            
            summary_message = f"""📊 گزارش خلاصه وضعیت بازار امروز
🗓 {weekday} | {to_persian_number(now.strftime("%Y/%m/%d"))}
🕒 ساعت انتشار: {to_persian_number(time_text)}

🔹 نرخ شروع بازار: {to_persian_number(f"{open_p:,}")} تومان
🔺 بالاترین نرخ امروز: {to_persian_number(f"{high_p:,}")} تومان
🔻 پایین‌ترین نرخ امروز: {to_persian_number(f"{low_p:,}")} تومان
🏁 نرخ پایانی بازار: {to_persian_number(f"{close_p:,}")} تومان

━━━━━━━━━━━━━━━
طلای ماهان (اسکندری گلد)💎"""
            
            # ارسال گزارش به تلگرام
            requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": summary_message})
            
            # ارسال گزارش به ایتا
            if EITAA_TOKEN and EITAA_CHAT_ID:
                requests.post(f"https://eitaayar.ir/api/{EITAA_TOKEN}/sendMessage", data={"chat_id": EITAA_CHAT_ID, "text": summary_message})
                
            print("✅ گزارش خلاصه وضعیت روزانه با موفقیت ارسال شد.")
            
            # خالی کردن فایل قیمت‌های روزانه برای شروع دیتای فردا
            with open("daily_prices.txt", "w") as f:
                f.write("")
                
            # ثبت تاریخ امروز برای اینکه دوباره ارسال نشود
            with open("last_summary_date.txt", "w") as f:
                f.write(today_str)
                
    except Exception as e:
        print("Error in generating summary:", e)

# 🛑 ۴. منطق جلوگیری از ارسال قیمت تکراری (برای پیام‌های ۵ دقیقه‌ای معمولی)
try:
    with open("last_price.txt", "r") as f:
        last_price = f.read().strip()
except:
    last_price = ""

# اگر قیمت تغییری نکرده باشد، اسکریپت در این مرحله متوقف می‌شود
if last_price == str(price):
    print("No price change for regular update.")
    exit()

# ذخیره قیمت جدید برای مقایسه در ۵ دقیقه بعدی
with open("last_price.txt", "w") as f:
    f.write(str(price))

# متن پیام نرخ لحظه‌ای معمولی
message = f"""💎 نرخ لحظه‌ای طلای ۱۸ عیار
🗓 {weekday}
🕒 بروزرسانی: {to_persian_number(time_text)}
💰 هر گرم: {to_persian_number(price_text)} تومان
━━━━━━━━━━━━━━━
طلای ماهان (اسکندری گلد)💎"""

# ارسال پیام معمولی به تلگرام
requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": message})

# ارسال پیام معمولی به ایتا
if EITAA_TOKEN and EITAA_CHAT_ID:
    requests.post(f"https://eitaayar.ir/api/{EITAA_TOKEN}/sendMessage", data={"chat_id": EITAA_CHAT_ID, "text": message})

print("✅ پیام نرخ لحظه‌ای ارسال شد.")
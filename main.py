import os
import requests

# تنظیم توکن‌ها و آیدی‌ها از سکرت‌های گیت‌هاب
BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

# متغیرهای ایتا (اگر در گیت‌هاب ست شده باشند خودکار کار می‌کنند)
EITAA_TOKEN = os.environ.get("EITAA_TOKEN")
EITAA_CHAT_ID = os.environ.get("EITAA_CHAT_ID")

PRICE_API = "http://et.tala.ir/webservice/haghanigold.com/6397dbw8333f095bb55cd539f865a994"
TIME_API = "https://api.keybit.ir/time/"

def to_persian_number(text):
    return str(text).translate(str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹"))

# ۱. دریافت قیمت لحظه‌ای از API
try:
    data = requests.get(PRICE_API, timeout=10).json()
    price = data["geram18"]["value"] // 10
    price_text = f"{price:,}"
except Exception as e:
    print("API PRICE ERROR:", e)
    exit()

# ۲. دریافت تاریخ و زمان شمسی دقیق از API زمان
try:
    time_response = requests.get(TIME_API, timeout=10).json()
    date_text = time_response["date"]["full"]["official"]["iso"]["date"]["persian"]  # مثل: 1402/08/25
    weekday = time_response["week_day"]["name"]  # مثل: پنجشنبه
    time_text = time_response["time24"]["full"][:5]  # مثل: 23:30
    hour_now = int(time_response["time24"]["hour"])  # ساعت فعلی ایران
    minute_now = int(time_response["time24"]["minute"])  # دقیقه فعلی ایران
except Exception as e:
    print("API TIME ERROR:", e)
    exit()

# ۳. ذخیره قیمت لحظه‌ای در آرشیو روزانه (برای محاسبه سوابق)
try:
    with open("daily_prices.txt", "a") as f:
        f.write(f"{price}\n")
except Exception as e:
    print("Error saving daily price:", e)

# خواندن تاریخ آخرین گزارش ارسال شده
try:
    with open("last_summary_date.txt", "r") as f:
        last_summary = f.read().strip()
except:
    last_summary = ""

# 📊 ۴. منطق ارسال گزارش خلاصه وضعیت پایان روز (راس ساعت ۱۱:۳۰ شب)
if hour_now == 23 and minute_now >= 30 and last_summary != date_text:
    try:
        with open("daily_prices.txt", "r") as f:
            lines = f.readlines()
        
        prices = [int(line.strip()) for line in lines if line.strip().isdigit()]
        
        if prices:
            open_p = prices[0]       # نرخ شروع بازار
            high_p = max(prices)     # بالاترین نرخ روز
            low_p = min(prices)      # پایین‌ترین نرخ روز
            close_p = prices[-1]     # نرخ پایانی بازار
            
            summary_message = f"""📊 گزارش خلاصه وضعیت بازار امروز
🗓 {to_persian_number(date_text)} | {weekday}
🕒 ساعت انتشار: {to_persian_number(time_text)}

🔹 نرخ شروع بازار: {to_persian_number(f"{open_p:,}")} تومان
🔺 بالاترین نرخ امروز: {to_persian_number(f"{high_p:,}")} تومان
🔻 پایین‌ترین نرخ امروز: {to_persian_number(f"{low_p:,}")} تومان
🏁 نرخ پایانی بازار: {to_persian_number(f"{close_p:,}")} تومان

━━━━━━━━━━━━━━━
طلای ماهان (اسکندری گلد)💎"""
            
            # ارسال گزارش پایانی به تلگرام
            requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": summary_message})
            
            # ارسال گزارش پایانی به ایتا
            if EITAA_TOKEN and EITAA_CHAT_ID:
                requests.post(f"https://eitaayar.ir/api/{EITAA_TOKEN}/sendMessage", data={"chat_id": EITAA_CHAT_ID, "text": summary_message})
                
            print("✅ گزارش خلاصه وضعیت روزانه با موفقیت ارسال شد.")
            
            # خالی کردن فایل قیمت‌ها برای شروع دیتای فردا
            with open("daily_prices.txt", "w") as f:
                f.write("")
            # ثبت تاریخ امروز برای جلوگیری از ارسال مجدد در همان شب
            with open("last_summary_date.txt", "w") as f:
                f.write(date_text)
                
    except Exception as e:
        print("Error in generating summary:", e)

# 🛑 ۵. منطق جلوگیری از ارسال قیمت تکراری (برای پیام‌های معمولی طول روز)
try:
    with open("last_price.txt", "r") as f:
        last_price = f.read().strip()
except:
    last_price = ""

# اگر قیمت تغییر نکرده باشد، اسکریپت پیام معمولی نمی‌فرستد و خارج می‌شود
if last_price == str(price):
    print("قیمت تغییر نکرده است. خروج از برنامه.")
    exit()

# ذخیره قیمت جدید برای مقایسه بعدی
with open("last_price.txt", "w") as f:
    f.write(str(price))

# 💎 ساختار پیام معمولی لحظه‌ای (همراه با تاریخ شمسی دقیق)
message = f"""💎 نرخ لحظه‌ای طلای ۱۸ عیار
🗓 {to_persian_number(date_text)} | {weekday}
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
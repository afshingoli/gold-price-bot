import os
import requests

# تنظیم توکن‌ها و آیدی‌ها از سکرت‌های گیت‌هاب
BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

# متغیرهای ایتا (اگر ست کرده باشی خودکار ارسال می‌شود)
EITAA_TOKEN = os.environ.get("EITAA_TOKEN")
EITAA_CHAT_ID = os.environ.get("EITAA_CHAT_ID")

PRICE_API = "http://et.tala.ir/webservice/haghanigold.com/6397dbw8333f095bb55cd539f865a994"
TIME_API = "https://api.keybit.ir/time/"

def to_persian_number(text):
    return str(text).translate(str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹"))

# ۱. گرفتن قیمت لحظه‌ای از API
try:
    data = requests.get(PRICE_API, timeout=10).json()
    price = data["geram18"]["value"] // 10
    price_text = f"{price:,}"
except Exception as e:
    print("API PRICE ERROR:", e)
    exit()

# ۲. گرفتن تاریخ و زمان شمسی دقیق (اصلاح شده و بدون کرش)
try:
    time_response = requests.get(TIME_API, timeout=10).json()
    date_text = time_response["date"]["full"]["official"]["iso"]["date"]["persian"]  # مثل: 1402/08/25
    weekday = time_response["week_day"]["name"]  # مثل: پنجشنبه
    time_text = time_response["time24"]["full"][:5]  # مثل: 20:15
    hour_now = int(time_response["time24"]["hour"])  # ساعت فعلی ایران برای گزارش شبانه
except Exception as e:
    print("API TIME ERROR:", e)
    exit()

# ۳. ذخیره قیمت در آرشیو روزانه برای خلاصه وضعیت
try:
    with open("daily_prices.txt", "a") as f:
        f.write(f"{price}\n")
except Exception as e:
    print("Error saving daily price:", e)

try:
    with open("last_summary_date.txt", "r") as f:
        last_summary = f.read().strip()
except:
    last_summary = ""

# 📊 ۴. منطق ارسال گزارش خلاصه وضعیت پایان روز (ساعت ۸ شب به بعد)
# نکته: برای تست فوری می‌توانید موقتاً عدد 20 را به 0 تغییر دهید
if hour_now >= 20 and last_summary != date_text:
    try:
        with open("daily_prices.txt", "r") as f:
            lines = f.readlines()
        
        prices = [int(line.strip()) for line in lines if line.strip().isdigit()]
        
        if prices:
            open_p = prices[0]       # نرخ شروع
            high_p = max(prices)     # بالاترین نرخ
            low_p = min(prices)      # پایین‌ترین نرخ
            close_p = prices[-1]     # نرخ پایانی
            
            summary_message = f"""📊 گزارش خلاصه وضعیت بازار امروز
🗓 {to_persian_number(date_text)} | {weekday}
🕒 ساعت انتشار: {to_persian_number(time_text)}

🔹 نرخ شروع بازار: {to_persian_number(f"{open_p:,}")} تومان
🔺 بالاترین نرخ امروز: {to_persian_number(f"{high_p:,}")} تومان
🔻 پایین‌ترین نرخ امروز: {to_persian_number(f"{low_p:,}")} تومان
🏁 نرخ پایانی بازار: {to_persian_number(f"{close_p:,}")} تومان

━━━━━━━━━━━━━━━
طلای ماهان (اسکندری گلد)💎"""
            
            # ارسال خلاصه به تلگرام
            requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": summary_message})
            
            # ارسال خلاصه به ایتا
            if EITAA_TOKEN and EITAA_CHAT_ID:
                requests.post(f"https://eitaayar.ir/api/{EITAA_TOKEN}/sendMessage", data={"chat_id": EITAA_CHAT_ID, "text": summary_message})
                
            print("✅ گزارش خلاصه وضعیت روزانه با موفقیت ارسال شد.")
            
            # خالی کردن فایل قیمت‌ها برای فردا و ثبت تاریخ امروز
            with open("daily_prices.txt", "w") as f:
                f.write("")
            with open("last
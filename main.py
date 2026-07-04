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
    date_text = time_response["date"]["full"]["official"]["iso"]["date"]["persian"]
    weekday = time_response["week_day"]["name"]
    time_text = time_response["time24"]["full"][:5]
    hour_now = int(time_response["time24"]["hour"])
    minute_now = int(time_response["time24"]["minute"])
except Exception as e:
    print("API TIME ERROR:", e)
    exit()

# ۳. ذخیره قیمت لحظه‌ای در آرشیو روزانه
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

# 📊 ۴. منطق ارسال گزارش خلاصه وضعیت پایان روز (ساعت ۲۳:۳۰ شب)
if hour_now == 23 and minute_now >= 30 and last_summary != date_text:
    try:
        prices = []
        try:
            with open("daily_prices.txt", "r") as f:
                lines = f.readlines()
            prices = [int(line.strip()) for line in lines if line.strip().isdigit()]
        except Exception as e:
            print("Error reading daily_prices.txt:", e)
        
        if prices:
            open_p = prices[0]
            high_p = max(prices)
            low_p = min(prices)
            close_p = prices[-1]
            
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
            
            # خالی کردن فایل قیمت‌ها و ثبت تاریخ
            try:
                with open("daily_prices.txt", "w") as f:
                    f.write("")
                with open("last_summary_date.txt", "w") as f:
                    f.write(date_text)
            except Exception as e:
                print("Error clearing files after summary:", e)
                
    except Exception as e:
        print("Error in generating summary:", e)

# 🛑 ۵. منطق جلوگیری از ارسال قیمت تکراری
try:
    with open("last_price.txt", "r") as f:
        last_price = f.read().strip()
except:
    last_price = ""

# اگر قیمت تغییر نکرده باشد، اسکریپت خارج می‌شود
if last_price == str(price):
    print("قیمت تغییر نکرده است. خروج از برنامه.")
    exit()

# ذخیره قیمت جدید برای مقایسه بعدی (این بار کاملاً ایمن و داخل try-except)
try:
    with open("last_price.txt", "w") as f:
        f.write(str(price))
except Exception as e:
    print("Error saving last price to file:", e)

# 💎 ساختار پیام معمولی لحظه‌ای
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
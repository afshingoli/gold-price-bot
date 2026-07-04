import os
import requests
import datetime

# تنظیمات اصلی
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
EITAA_TOKEN = os.environ.get("EITAA_TOKEN")
EITAA_CHAT_ID = os.environ.get("EITAA_CHAT_ID")
PRICE_API = "http://et.tala.ir/webservice/haghanigold.com/6397dbw8333f095bb55cd539f865a994"

def to_persian_number(text):
    return str(text).translate(str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹"))

# فرمول تبدیل تاریخ میلادی به شمسی (بدون نیاز به اینترنت و سایت خارجی)
def gregorian_to_jalali(gy, gm, gd):
    g_d_m = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 335]
    gy = gy - 1600 if gy > 1600 else gy - 621
    days = (365 * gy) + int((gy + 3) / 4) - int((gy + 99) / 100) + int((gy + 399) / 400) - 80 + gd + g_d_m[gm - 1]
    jy = 979 + 33 * int(days / 12053)
    days %= 12053
    jy += 4 * int(days / 1461)
    days %= 1461
    if days > 365:
        jy += int((days - 1) / 365)
        days = (days - 1) % 365
    jm = 1 + int(days / 31) if days < 186 else 7 + int((days - 186) / 30)
    jd = 1 + (days % 31) if days < 186 else 1 + ((days - 186) % 30)
    return f"{jy}/{jm:02d}/{jd:02d}"

# محاسبه تاریخ و ساعت داخلی (ضد تحریم)
tz_iran = datetime.timezone(datetime.timedelta(hours=3, minutes=30))
now = datetime.datetime.now(tz_iran)
weekdays = ["دوشنبه", "سه‌شنبه", "چهارشنبه", "پنجشنبه", "جمعه", "شنبه", "یکشنبه"]
weekday = weekdays[now.weekday()]
time_text = now.strftime("%H:%M")
# استخراج تاریخ شمسی دقیق
date_text = gregorian_to_jalali(now.year, now.month, now.day)
hour_now = now.hour

# ==========================================
# بخش اول: دریافت قیمت فعلی از API
# ==========================================
try:
    data = requests.get(PRICE_API, timeout=10).json()
    price = data["geram18"]["value"] // 10
    price_text = f"{price:,}"
except Exception as e:
    print(f"خطا در دریافت قیمت: {e}")
    exit()

# ذخیره قیمت در لیست روزانه (برای خلاصه ۸ شب)
try:
    with open("daily_prices.txt", "a", encoding="utf-8") as f:
        f.write(f"{price}\n")
except: pass

# ==========================================
# بخش دوم: گزارش خلاصه وضعیت راس ساعت ۸ شب
# ==========================================
last_summary_date = ""
try:
    with open("last_summary.txt", "r", encoding="utf-8", errors="ignore") as f:
        last_summary_date = f.read().strip()
except: pass

# اگر ساعت 20 (۸ شب) یا بیشتر است و امروز هنوز گزارش ندادیم
if hour_now >= 20 and last_summary_date != date_text:
    try:
        with open("daily_prices.txt", "r", encoding="utf-8", errors="ignore") as f:
            raw_lines = f.readlines()
        
        lines = [int(line.strip()) for line in raw_lines if line.strip().isdigit() and int(line.strip()) > 0]
        
        if lines:
            open_price = lines[0]
            close_price = lines[-1]
            high_price = max(lines)
            low_price = min(lines)
            diff = close_price - open_price
            
            diff_sign = "🔺 +" if diff > 0 else ("🔻 " if diff < 0 else "🔹 ")
            pct = (diff / open_price) * 100 if open_price else 0
            
            summary_message = f"""📊 گزارش و خلاصه بازار امروز
🗓 تاریخ: {to_persian_number(date_text)} | {weekday}
🕒 ساعت گزارش: {to_persian_number(time_text)}
━━━━━━━━━━━━━━━
🔓 بازگشایی: {to_persian_number(f"{open_price:,}")} تومان
🔒 پایانی: {to_persian_number(f"{close_price:,}")} تومان
🔺 بالاترین: {to_persian_number(f"{high_price:,}")} تومان
🔻 پایین‌ترین: {to_persian_number(f"{low_price:,}")} تومان
📈 تغییر: {diff_sign}{to_persian_number(f"{abs(diff):,}")} تومان ({to_persian_number(f"{pct:.2f}")}٪)
━━━━━━━━━━━━━━━
طلای ماهان (اسکندری گلد)💎"""
            
            # ارسال به تلگرام و ایتا
            requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": summary_message})
            if EITAA_TOKEN and EITAA_CHAT_ID:
                requests.post(f"https://eitaayar.ir/api/{EITAA_TOKEN}/sendMessage", data={"chat_id": EITAA_CHAT_ID, "text": summary_message})
            
            print("✅ گزارش روزانه ارسال شد.")
            
            # ثبت تاریخ امروز برای جلوگیری از تکرار گزارش
            with open("last_summary.txt", "w", encoding="utf-8") as f:
                f.write(date_text)
            
            # پاکسازی فایل قیمت ها برای روز بعد
            with open("daily_prices.txt", "w", encoding="utf-8") as f:
                f.write("")
    except Exception as e:
        print(f"خطا در ارسال گزارش روزانه: {e}")

# ==========================================
# بخش سوم: ارسال قیمت لحظه ای (در صورت تغییر)
# ==========================================
last_price = "0"
try:
    with open("last_price.txt", "r", encoding="utf-8", errors="ignore") as f:
        content = f.read().strip()
        if content.isdigit():
            last_price = content
except Exception: pass

if str(price) == str(last_price):
    print("قیمت تغییری نکرده است.")
    exit()

message = f"""💎 نرخ لحظه‌ای طلای ۱۸ عیار
🗓 {to_persian_number(date_text)} | {weekday}
🕒 بروزرسانی: {to_persian_number(time_text)}

💰 هر گرم: {to_persian_number(price_text)} تومان
━━━━━━━━━━━━━━━
طلای ماهان (اسکندری گلد)💎"""

try:
    response = requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": message})
    if EITAA_TOKEN and EITAA_CHAT_ID:
        requests.post(f"https://eitaayar.ir/api/{EITAA_TOKEN}/sendMessage", data={"chat_id": EITAA_CHAT_ID, "text": message})
    
    if response.status_code == 200:
        with open("last_price.txt", "w", encoding="utf-8") as f:
            f.write(str(price))
        print("قیمت با موفقیت ارسال و ذخیره شد.")
except Exception as e:
    print(f"خطا در ارسال پیام لحظه ای: {e}")
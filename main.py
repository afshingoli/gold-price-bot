import os
import requests
import jdatetime
from datetime import datetime

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

API_URL = "http://et.tala.ir/webservice/haghanigold.com/6397dbw8333f095bb55cd539f865a994"


# تبدیل اعداد انگلیسی به فارسی
def to_persian_number(text):
    english = "0123456789"
    persian = "۰۱۲۳۴۵۶۷۸۹"
    return str(text).translate(str.maketrans(english, persian))


# دریافت اطلاعات
data = requests.get(API_URL).json()

price = data["geram18"]["value"] // 10
server_time = data["serverTime"]

# تبدیل زمان API به شمسی
dt = datetime.strptime(server_time, "%Y-%m-%d %H:%M:%S")
jdt = jdatetime.datetime.fromgregorian(datetime=dt)

date_text = jdt.strftime("%d %B %Y")
weekday = jdt.strftime("%A")
time_text = jdt.strftime("%H:%M")

price_text = f"{price:,}"

# خواندن آخرین قیمت
try:
    with open("last_price.txt", "r") as f:
        last_price = f.read().strip()
except:
    last_price = ""

# اگر قیمت تغییر نکرد، پیام ارسال نکن
if last_price == str(price):
    print("Price not changed.")
    exit()

# ذخیره قیمت جدید
with open("last_price.txt", "w") as f:
    f.write(str(price))

message = f"""💎 نرخ لحظه‌ای طلای ۱۸ عیار

🗓 {to_persian_number(date_text)} | {weekday}
🕒 بروزرسانی: {to_persian_number(time_text)}

💰 هر گرم: {to_persian_number(price_text)} تومان

━━━━━━━━━━━━━━━
طلای ماهان (اسکندری گلد)💎
"""

response = requests.post(
    f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
    data={
        "chat_id": CHAT_ID,
        "text": message
    }
)

if response.status_code == 200:
    print("Message sent!")
else:
    print("Telegram Error:", response.text)
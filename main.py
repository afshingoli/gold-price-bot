import os
import requests

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

API_URL = "http://et.tala.ir/webservice/haghanigold.com/6397dbw8333f095bb55cd539f865a994"

# دریافت اطلاعات از API
data = requests.get(API_URL).json()

price = data["geram18"]["value"]      # ریال
server_time = data["serverTime"]      # مثال: 2026-07-02 16:30:03

# تبدیل به تومان
price_toman = price // 10
price_text = f"{price_toman:,}"

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

message = f"""💰 نرخ لحظه‌ای طلای ۱۸ عیار

💵 {price_text} تومان

📅 تاریخ و ساعت:
{server_time}

💎 طلای ماهان (اسکندری گلد)
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
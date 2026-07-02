import os
import requests

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

API_URL = "http://et.tala.ir/webservice/haghanigold.com/6397dbw8333f095bb55cd539f865a994"

# دریافت اطلاعات
data = requests.get(API_URL).json()

price = data["geram18"]["value"]
time = data["serverTime"]

# خواندن آخرین قیمت
try:
    with open("last_price.txt", "r") as f:
        last_price = f.read().strip()
except:
    last_price = ""

# اگر قیمت تغییر نکرد، هیچ کاری نکن
if last_price == str(price):
    print("Price not changed.")
    exit()

# ذخیره قیمت جدید
with open("last_price.txt", "w") as f:
    f.write(str(price))

price_text = f"{price:,}"

message = f"""💰 قیمت طلای ۱۸ عیار

💵 {price_text} ریال

🕒 {time}
"""

requests.post(
    f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
    data={
        "chat_id": CHAT_ID,
        "text": message
    }
)

print("Message sent!")
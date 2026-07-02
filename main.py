import os
import requests

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

url = "http://et.tala.ir/webservice/haghanigold.com/6397dbw8333f095bb55cd539f865a994"

data = requests.get(url).json()

price = data["geram18"]["value"]
time = data["serverTime"]

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
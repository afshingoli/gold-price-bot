import os
import requests

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

PRICE_API = "http://et.tala.ir/webservice/haghanigold.com/6397dbw8333f095bb55cd539f865a994"
TIME_API = "https://api.keybit.ir/time/"


def to_persian_number(text):
    return str(text).translate(str.maketrans(
        "0123456789",
        "۰۱۲۳۴۵۶۷۸۹"
    ))


# گرفتن قیمت
price_resp = requests.get(PRICE_API, timeout=10)
price_resp.raise_for_status()
data = price_resp.json()
price = data["geram18"]["value"] // 10
price_text = f"{price:,}"

# گرفتن تاریخ و ساعت دقیق شمسی
time_resp = requests.get(TIME_API, timeout=10)
time_resp.raise_for_status()
tdata = time_resp.json()["date"]

date_text = tdata["full"]["official"]["iso"]["date"]["persian"]
weekday = tdata["week_day"]["name"]
time_text = tdata["time24"]["full"][:5]

print("DEBUG price:", price)
print("DEBUG date:", date_text, weekday, time_text)

# چک قیمت قبلی
try:
    with open("last_price.txt", "r") as f:
        last_price = f.read().strip()
except FileNotFoundError:
    last_price = ""

print("DEBUG last_price:", repr(last_price))

if last_price == str(price):
    print("Price not changed. Exiting without sending.")
    exit()

with open("last_price.txt", "w") as f:
    f.write(str(price))

message = f"""💎 نرخ لحظه‌ای طلای ۱۸ عیار
🗓 {to_persian
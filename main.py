import requests
from bs4 import BeautifulSoup

url = "https://www.tala.ir/price/18k"

headers = {
    "User-Agent": "Mozilla/5.0"
}

response = requests.get(url, headers=headers)

print("Status:", response.status_code)

soup = BeautifulSoup(response.text, "lxml")

print(soup.title)

print("=" * 50)

print(soup.get_text()[:3000])

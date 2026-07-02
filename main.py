import requests
from bs4 import BeautifulSoup

url = "https://www.tala.ir/price/18k"

headers = {
    "User-Agent": "Mozilla/5.0"
}

response = requests.get(url, headers=headers)

soup = BeautifulSoup(response.text, "lxml")

text = soup.get_text()

index = text.find("آخرین قیمت")

print(text[index:index+1000])

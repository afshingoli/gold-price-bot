import requests

url = "https://www.tala.ir/price/18k"

headers = {
    "User-Agent": "Mozilla/5.0"
}

response = requests.get(url, headers=headers)

print("Status Code:", response.status_code)
print(response.text[:1000])

import requests
from bs4 import BeautifulSoup

# این آدرس صفحه اصلی نرخ‌های طلا و سکه در شبکه اطلاع‌رسانی است
url = "https://www.tgju.org/currency"

try:
    # یک درخواست ساده بدون نیاز به هیچ کوکی یا یوزر-آجنت خاصی
    response = requests.get(url, timeout=10)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # پیدا کردن جدول قیمت‌ها
    # این کد نرخ طلای 18 عیار و سکه امامی رو از جدول استخراج میکنه
    print("نرخ‌های استخراج شده:")
    
    # مثال: پیدا کردن نرخ طلای 18 عیار
    gold_18 = soup.find('tr', {'data-market-row': 'geram18'})
    if gold_18:
        price = gold_18.find('td', class_='nf').text.strip()
        print(f"طلای 18 عیار: {price} تومان")
        
    # مثال: پیدا کردن نرخ سکه امامی
    sekeh = soup.find('tr', {'data-market-row': 'sekeh'})
    if sekeh:
        price = sekeh.find('td', class_='nf').text.strip()
        print(f"سکه امامی: {price} تومان")

except Exception as e:
    print("خطا در دریافت نرخ:", e)
import requests
from bs4 import BeautifulSoup
import urllib.parse
from datetime import datetime
import pytz

# --- KONFIGURĀCIJA ---
TOKEN = "7949226714:AAGqh8FySc76-zYVBMAN3rjYJUuNxgef9do"
CHAT_ID = "7957861677" 
SCRAPING_ANT_KEY = "b53e4174e68e442bb5a039fe4bf95b6a"

# URL ar visiem filtriem: BMW 3, 2011+, <7000€, Dīzelis, Automāts
TARGET_URL = "https://lv.autoplius.lt/sludinajumi/lietotas-automasinas?make_date_from=2011&make_date_to=&sell_price_from=&sell_price_to=7000&engine_capacity_from=&engine_capacity_to=&power_from=&power_to=&kilometrage_from=&kilometrage_to=&qt=&category_id=2&fuel_id%5B32%5D=32&gearbox_id=38&make_id=97&model_id=1319&slist=2826739261"

def send_telegram(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    params = {"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}
    try:
        requests.get(url, params=params, timeout=15)
    except:
        print("Telegram timeout")

def is_work_time():
    tz = pytz.timezone('Europe/Riga')
    now = datetime.now(tz)
    # Tagad strādās līdz 23:59:59
    return 9 <= now.hour <= 23

def check_autoplius():
    if not is_work_time():
        return

    encoded_url = urllib.parse.quote_plus(TARGET_URL)
    api_url = f"https://api.scrapingant.com/v2/general?url={encoded_url}&x-api-key={SCRAPING_ANT_KEY}&browser=true"

    try:
        response = requests.get(api_url, timeout=120)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            ads = soup.find_all('a', class_='announcement-item')
            
            if not ads:
                return

            try:
                with open("seen_bmw.txt", "r") as f:
                    seen_ads = set(f.read().splitlines())
            except FileNotFoundError:
                seen_ads = set()

            found_new = 0
            for ad in ads:
                ad_url = ad.get('href', '')
                if not ad_url: continue
                ad_id = ad_url.split("-")[-1].replace(".html", "")

                if ad_id not in seen_ads:
                    title = ad.find('div', class_='announcement-title').get_text(strip=True)
                    price = ad.find('div', class_='announcement-pricing-info').get_text(strip=True)
                    
                    msg = f"🌟 <b>JAUNS BMW SLUDINĀJUMS!</b>\n🚗 {title}\n💰 Cena: {price}\n🔗 {ad_url}"
                    send_telegram(msg)
                    
                    seen_ads.add(ad_id)
                    found_new += 1

            with open("seen_bmw.txt", "w") as f:
                f.write("\n".join(seen_ads))
            
    except Exception as e:
        print(f"Kļūda: {e}")

if __name__ == "__main__":
    check_autoplius()

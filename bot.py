import requests
from bs4 import BeautifulSoup
import urllib.parse
from datetime import datetime
import pytz
import time

# --- KONFIGURĀCIJA ---
TOKEN = "8353649009:AAHZA_uGUHSxmhzCgOkeoPpyAzBH4smYU-o"
CHAT_ID = "1034267908"
SCRAPING_ANT_KEY = "b53e4174e68e442bb5a039fe4bf95b6a"

# TAVS JAUNAIS URL (ar gadu un cenu filtru)
TARGET_URL = "https://lv.autoplius.lt/sludinajumi/lietotas-automasinas?make_date_from=2011&make_date_to=&sell_price_from=&sell_price_to=7000&engine_capacity_from=&engine_capacity_to=&power_from=&power_to=&kilometrage_from=&kilometrage_to=&qt=&category_id=2&make_id=97&model_id=1319&slist=2826874171&order_by=2&order_direction=DESC"

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
    return 9 <= now.hour < 23

def check_autoplius():
    if not is_work_time():
        print("Bots atpūšas.")
        return

    encoded_url = urllib.parse.quote_plus(TARGET_URL)
    api_url = f"https://api.scrapingant.com/v2/general?url={encoded_url}&x-api-key={SCRAPING_ANT_KEY}&browser=true"

    for attempt in range(3):
        try:
            print(f"Mēģinājums #{attempt + 1}...")
            response = requests.get(api_url, timeout=120)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                ads = soup.find_all('a', class_='announcement-item')
                
                if not ads:
                    # Ja saraksts tukšs, varbūt lapa vēl lādējas, mēģinām nākamo piegājienu
                    if attempt < 2: continue
                    send_telegram("🔎 Pārbaude pabeigta. Pašlaik sarakstā nav neviena BMW, kas atbilstu taviem kritērijiem.")
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
                        try:
                            # Tā kā gads un cena jau ir filtrā, pārbaudām tikai kārbu un degvielu
                            full_text = ad.get_text(" ", strip=True).lower()
                            
                            # Atslēgvārdi kārba/degviela (LV un LT valodās)
                            is_diesel = any(x in full_text for x in ["dīz", "dyzel"])
                            is_auto = any(x in full_text for x in ["auto", "autom"])

                            if is_diesel and is_auto:
                                title = ad.find('div', class_='announcement-title').get_text(strip=True)
                                price_raw = ad.find('div', class_='announcement-pricing-info').get_text(strip=True)
                                
                                msg = f"🚀 <b>JAUNS ATRASTIE BMW!</b>\n🚗 {title}\n💰 Cena: {price_raw}\n🔗 {ad_url}"
                                send_telegram(msg)
                                found_new += 1
                        except:
                            continue
                        seen_ads.add(ad_id)

                with open("seen_bmw.txt", "w") as f:
                    f.write("\n".join(seen_ads))
                
                if found_new == 0:
                    print("Jaunu sludinājumu nav.")
                return 

            else:
                if attempt == 2:
                    send_telegram(f"❌ Proxy kļūda (Status {response.status_code}).")
                time.sleep(10)

        except Exception as e:
            if attempt == 2:
                send_telegram(f"🚨 Kļūda: {str(e)}")
            time.sleep(10)

if __name__ == "__main__":
    check_autoplius()

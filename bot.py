import requests
from bs4 import BeautifulSoup
import urllib.parse
from datetime import datetime
import pytz

# --- KONFIGURĀCIJA ---
TOKEN = "8353649009:AAHZA_uGUHSxmhzCgOkeoPpyAzBH4smYU-o"
CHAT_ID = "1034267908"
SCRAPING_ANT_KEY = "b53e4174e68e442bb5a039fe4bf95b6a"
TARGET_URL = "https://lv.autoplius.lt/sludinajumi/lietotas-automasinas?make_id=97&model_id=1319&slist=2826775433&order_by=2&order_direction=DESC"

def is_work_time():
    # Pārbaudām laiku Rīgas laika zonā
    tz = pytz.timezone('Europe/Riga')
    now = datetime.now(tz)
    return 9 <= now.hour < 23

def check_autoplius():
    if not is_work_time():
        print("Pašlaik ir nakts miers. Bots atpūšas.")
        return

    encoded_url = urllib.parse.quote_plus(TARGET_URL)
    api_url = f"https://api.scrapingant.com/v2/general?url={encoded_url}&x-api-key={SCRAPING_ANT_KEY}&browser=true"

    try:
        print("Mēģinu pieslēgties caur ScrapingAnt...")
        response = requests.get(api_url, timeout=60)
        
        if response.status_code != 200:
            print(f"Kļūda! Statuss: {response.status_code}")
            return

        soup = BeautifulSoup(response.text, 'html.parser')
        # Atrodam tikai galvenos sludinājumu blokus (pirmā lapa)
        ads = soup.find_all('a', class_='announcement-item')

        try:
            with open("seen_bmw.txt", "r") as f:
                seen_ads = set(f.read().splitlines())
        except FileNotFoundError:
            seen_ads = set()

        new_count = 0
        for ad in ads:
            ad_url = ad.get('href', '')
            if not ad_url: continue
            ad_id = ad_url.split("-")[-1].replace(".html", "")

            if ad_id not in seen_ads:
                try:
                    # Datu ieguve no saraksta skata
                    price_raw = ad.find('div', class_='announcement-pricing-info').get_text(strip=True)
                    price = int(''.join(filter(str.isdigit, price_raw)))
                    
                    params_div = ad.find('div', class_='announcement-parameters')
                    params = params_div.get_text(strip=True).lower() if params_div else ""

                    # Filtra loģika (pēc tavas bildes parauga)
                    is_diesel = "dīzelis" in params or "dyzelinas" in params
                    is_auto = "automātiskā" in params or "automatinė" in params

                    if price <= 7000 and is_diesel and is_auto:
                        title = ad.find('div', class_='announcement-title').get_text(strip=True)
                        msg = f"✨ **ATRĀDĪTS BMW 3**\n🚗 {title}\n💰 Cena: {price}€\n⚙️ {params}\n🔗 {ad_url}"
                        
                        requests.get(f"https://api.telegram.org/bot{TOKEN}/sendMessage", 
                                     params={"chat_id": CHAT_ID, "text": msg})
                        new_count += 1
                except Exception as e:
                    print(f"Kļūda apstrādē: {e}")
                    continue
                
                seen_ads.add(ad_id)

        with open("seen_bmw.txt", "w") as f:
            f.write("\n".join(seen_ads))
        
        print(f"Pabeigts. Nosūtīti {new_count} jauni sludinājumi.")

    except Exception as e:
        print(f"Sistēmas kļūda: {e}")

if __name__ == "__main__":
    check_autoplius()

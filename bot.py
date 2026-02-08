import requests
from bs4 import BeautifulSoup
import urllib.parse
from datetime import datetime
import pytz
import re

# --- KONFIGURĀCIJA ---
TOKEN = "8353649009:AAHZA_uGUHSxmhzCgOkeoPpyAzBH4smYU-o"
CHAT_ID = "1034267908"
SCRAPING_ANT_KEY = "b53e4174e68e442bb5a039fe4bf95b6a"
TARGET_URL = "https://lv.autoplius.lt/sludinajumi/lietotas-automasinas?make_id=97&model_id=1319&slist=2826775433&order_by=2&order_direction=DESC"

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

    try:
        print("Mēģinu ielādēt datus...")
        response = requests.get(api_url, timeout=60)
        
        soup = BeautifulSoup(response.text, 'html.parser')
        ads = soup.find_all('a', class_='announcement-item')
        
        print(f"Atrasto sludinājumu skaits lapā: {len(ads)}")

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
                    # Nolasām visu tekstu no sludinājuma rāmja
                    full_text = ad.get_text(" ", strip=True).lower()
                    
                    # Cena
                    price_raw = ad.find('div', class_='announcement-pricing-info').get_text(strip=True)
                    price = int(''.join(filter(str.isdigit, price_raw)))
                    
                    # Meklējam atslēgvārdus visā sludinājuma tekstā
                    is_diesel = any(x in full_text for x in ["dīz", "dyzel"])
                    is_auto = any(x in full_text for x in ["auto", "autom"])
                    
                    # FILTRS (Vienkāršots uz brīdi, lai notestētu)
                    if price <= 7000 and is_diesel and is_auto:
                        msg = f"✅ **Atrasts BMW 3**\n💰 Cena: {price}€\n🔗 {ad_url}"
                        requests.get(f"https://api.telegram.org/bot{TOKEN}/sendMessage", 
                                     params={"chat_id": CHAT_ID, "text": msg})
                        new_count += 1
                        seen_ads.add(ad_id)
                except Exception as e:
                    print(f"Kļūda pie sludinājuma {ad_id}: {e}")
                    continue

        with open("seen_bmw.txt", "w") as f:
            f.write("\n".join(seen_ads))
        
        # Ja nekas netika atrasts, aizsūtam testa ziņu uz Telegram
        if new_count == 0:
            test_msg = f"Bots pārbaudīja lapu, atrada {len(ads)} sludinājumus, bet neviens neatbilda filtram."
            requests.get(f"https://api.telegram.org/bot{TOKEN}/sendMessage", 
                         params={"chat_id": CHAT_ID, "text": test_msg})

    except Exception as e:
        print(f"Sistēmas kļūda: {e}")

if __name__ == "__main__":
    check_autoplius()

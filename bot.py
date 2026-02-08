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

def send_telegram(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    params = {"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}
    try:
        requests.get(url, params=params, timeout=10)
    except:
        print("Neizdevās aizsūtīt ziņu uz Telegram")

def is_work_time():
    tz = pytz.timezone('Europe/Riga')
    now = datetime.now(tz)
    return 9 <= now.hour < 23

def check_autoplius():
    # Uzreiz pasakām Telegramam, ka esam dzīvi
    send_telegram("🚀 <b>Bots sāk meklēšanu!</b>")

    if not is_work_time():
        send_telegram("😴 Pašlaik ir nakts miers (9:00-23:00). Bots atpūšas.")
        return

    encoded_url = urllib.parse.quote_plus(TARGET_URL)
    api_url = f"https://api.scrapingant.com/v2/general?url={encoded_url}&x-api-key={SCRAPING_ANT_KEY}&browser=true"

    try:
        response = requests.get(api_url, timeout=60)
        if response.status_code != 200:
            send_telegram(f"❌ Kļūda savienojumā ar proxy. Statuss: {response.status_code}")
            return

        soup = BeautifulSoup(response.text, 'html.parser')
        ads = soup.find_all('a', class_='announcement-item')
        
        if not ads:
            send_telegram("⚠️ Lapā netika atrasts neviens sludinājums. Pārbaudi URL.")
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
                    # Nolasām visu tekstu no sludinājuma rāmja (Dīzelis, Automātiskā utt.)
                    item_text = ad.get_text(" ", strip=True).lower()
                    
                    # 1. Cena
                    price_raw = ad.find('div', class_='announcement-pricing-info').get_text(strip=True)
                    price = int(''.join(filter(str.isdigit, price_raw)))
                    
                    # 2. Gads (Meklējam 4 ciparus pēc kārtas)
                    year_match = re.search(r'(\d{4})', item_text)
                    year = int(year_match.group(1)) if year_match else 0

                    # FILTRI: Cena līdz 7000, Gads no 2011, Dīzelis un Automāts
                    if price <= 7000 and year >= 2011:
                        # Pārbaudām atslēgvārdus (arī Lietuviešu valodā, ja nu kas)
                        is_diesel = any(x in item_text for x in ["dīz", "dyzel"])
                        is_auto = any(x in item_text for x in ["auto", "autom"])

                        if is_diesel and is_auto:
                            msg = f"✅ <b>ATRĀDĪTS BMW 3</b>\n📅 Gads: {year}\n💰 Cena: {price}€\n🔗 <a href='{ad_url}'>Atvērt sludinājumu</a>"
                            send_telegram(msg)
                            found_new += 1
                except:
                    continue
                
                seen_ads.add(ad_id)

        with open("seen_bmw.txt", "w") as f:
            f.write("\n".join(seen_ads))
        
        if found_new == 0:
            send_telegram(f"🔎 Pārbaude pabeigta. Jaunu variantu (BMW 3, >2011, dīzelis, automāts, <7000€) nav.")

    except Exception as e:
        send_telegram(f"🚨 Kļūda: {str(e)}")

if __name__ == "__main__":
    check_autoplius()

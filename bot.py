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

def send_telegram(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    params = {"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}
    requests.get(url, params=params)

def check_autoplius():
    # Ignorējam darba laiku uz šo vienu testu, lai redzētu rezultātu tūlīt
    encoded_url = urllib.parse.quote_plus(TARGET_URL)
    api_url = f"https://api.scrapingant.com/v2/general?url={encoded_url}&x-api-key={SCRAPING_ANT_KEY}&browser=true"

    try:
        send_telegram("🔄 Bots sāk darbu un pieslēdzas proxy...")
        
        response = requests.get(api_url, timeout=60)
        
        if response.status_code != 200:
            send_telegram(f"❌ Proxy kļūda! Statuss: {response.status_code}")
            return

        html_content = response.text
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Meklējam jebkuru sludinājumu elementu (pamēģināsim plašāku klasi)
        ads = soup.find_all('a', class_='announcement-item')
        
        if not ads:
            # Ja neatrod, varbūt klases nosaukums ir cits? Pārbaudām virsrakstus.
            titles = soup.find_all('div', class_='announcement-title')
            send_telegram(f"⚠️ Sludinājumi netika atrasti. Atrasti {len(titles)} virsraksti. HTML garums: {len(html_content)}")
        else:
            send_telegram(f"✅ Veiksme! Lapā atrasti {len(ads)} sludinājumi. Sāku filtrēšanu...")

        # --- FILTRĒŠANAS DAĻA ---
        try:
            with open("seen_bmw.txt", "r") as f:
                seen_ads = set(f.read().splitlines())
        except FileNotFoundError:
            seen_ads = set()

        found_count = 0
        for ad in ads:
            ad_url = ad.get('href', '')
            ad_id = ad_url.split("-")[-1].replace(".html", "") if ad_url else "unknown"

            # Ļoti vienkāršots filtrs testam: tikai cena
            price_elem = ad.find('div', class_='announcement-pricing-info')
            if price_elem:
                price_text = price_elem.get_text(strip=True)
                price = int(''.join(filter(str.isdigit, price_text)))
                
                if price <= 7000 and ad_id not in seen_ads:
                    send_telegram(f"🚗 <b>Atrasts variants!</b>\nCena: {price}€\n{ad_url}")
                    seen_ads.add(ad_id)
                    found_count += 1

        with open("seen_bmw.txt", "w") as f:
            f.write("\n".join(seen_ads))

    except Exception as e:
        send_telegram(f"🚨 Kritiska kļūda: {str(e)}")

if __name__ == "__main__":
    check_autoplius()

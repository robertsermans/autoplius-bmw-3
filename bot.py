import requests
from bs4 import BeautifulSoup
import os

# TAVI DATI
TOKEN = "8353649009:AAHZA_uGUHSxmhzCgOkeoPpyAzBH4smYU-o"
CHAT_ID = "1034267908"
URL = "https://lv.autoplius.lt/sludinajumi/lietotas-automasinas?make_id=97&model_id=1319&slist=2826775433&order_by=2&order_direction=DESC"

def check_autoplius():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Accept-Language": "lv-LV,lv;q=0.9"
    }
    
    try:
        response = requests.get(URL, headers=headers, timeout=15)
        if response.status_code != 200:
            print(f"Kļūda! Statusa kods: {response.status_code}")
            return

        soup = BeautifulSoup(response.text, 'html.parser')
        # Atrodam visus sludinājumus sarakstā
        ads = soup.find_all('a', class_='announcement-item')

        try:
            with open("seen_bmw.txt", "r") as f:
                seen_ads = set(f.read().splitlines())
        except FileNotFoundError:
            seen_ads = set()

        new_ads_count = 0

        for ad in ads:
            ad_url = ad.get('href')
            if not ad_url: continue
            
            # Izvelkam unikālo ID no linka
            ad_id = ad_url.split("-")[-1].replace(".html", "")
            
            if ad_id not in seen_ads:
                # Datu izvilkšana no galvenā saraksta (bez atvēršanas)
                title = ad.find('div', class_='announcement-title').get_text(strip=True)
                
                # Cenas pārbaude
                price_raw = ad.find('div', class_='announcement-pricing-info').get_text(strip=True)
                price = int(''.join(filter(str.isdigit, price_raw)))
                
                # Parametru pārbaude (Dīzelis / Automātiskā)
                params = ad.find('div', class_='announcement-parameters').get_text(strip=True).lower()
                
                # Filtri: Cena līdz 7000, satur "dīzelis" un "automātiskā"
                if price <= 7000 and "dīzelis" in params and "automātiskā" in params:
                    msg = f"🔥 **JAUNS BMW 3**\n🚗 {title}\n💰 {price} €\n⚙️ {params}\n🔗 {ad_url}"
                    
                    # Sūtām uz Telegram
                    requests.get(f"https://api.telegram.org/bot{TOKEN}/sendMessage", 
                                 params={"chat_id": CHAT_ID, "text": msg})
                    new_ads_count += 1
                
                seen_ads.add(ad_id)

        # Saglabājam redzētos, lai nākamreiz nesūtītu tos pašus
        with open("seen_bmw.txt", "w") as f:
            f.write("\n".join(seen_ads))
            
        print(f"Pārbaude pabeigta. Atrasti {new_ads_count} jauni sludinājumi.")

    except Exception as e:
        print(f"Notikusi kļūda: {e}")

if __name__ == "__main__":
    check_autoplius()

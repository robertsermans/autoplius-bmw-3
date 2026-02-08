import cloudscraper
from bs4 import BeautifulSoup
import requests
import time
import random

TOKEN = "8353649009:AAHZA_uGUHSxmhzCgOkeoPpyAzBH4smYU-o"
CHAT_ID = "1034267908"
URL = "https://lv.autoplius.lt/sludinajumi/lietotas-automasinas?make_id=97&model_id=1319&slist=2826775433&order_by=2&order_direction=DESC"

def check_autoplius():
    # Izveidojam scraperi, kas mēģina vēl labāk imitēt pārlūku
    scraper = cloudscraper.create_scraper(
        browser={
            'browser': 'chrome',
            'platform': 'windows',
            'desktop': True
        }
    )
    
    # Pievienojam papildu galvenes, ko parasti sūta pārlūki
    scraper.headers.update({
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'lv-LV,lv;q=0.9,en-US;q=0.8,en;q=0.7',
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache',
        'Referer': 'https://www.google.com/',
        'Sec-Ch-Ua': '"Not A(Brand";v="99", "Google Chrome";v="121", "Chromium";v="121"',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'cross-site',
        'Upgrade-Insecure-Requests': '1'
    })

    try:
        # Pievienojam nejaušu pauzi pirms pieprasījuma (0.5 līdz 3 sekundes)
        time.sleep(random.uniform(0.5, 3.0))
        
        print(f"Mēģinu pieslēgties ar uzlabotu imitāciju...")
        response = scraper.get(URL, timeout=30)
        
        print(f"Servera atbilde: {response.status_code}")
        
        if response.status_code != 200:
            return

        soup = BeautifulSoup(response.text, 'html.parser')
        ads = soup.find_all('a', class_='announcement-item')

        try:
            with open("seen_bmw.txt", "r") as f:
                seen_ads = set(f.read().splitlines())
        except FileNotFoundError:
            seen_ads = set()

        for ad in ads:
            ad_url = ad.get('href')
            if not ad_url: continue
            ad_id = ad_url.split("-")[-1].replace(".html", "")

            if ad_id not in seen_ads:
                # Šoreiz izmantojam try/except katram elementam, lai skripts neapstātos
                try:
                    title = ad.find('div', class_='announcement-title').get_text(strip=True)
                    price_raw = ad.find('div', class_='announcement-pricing-info').get_text(strip=True)
                    price = int(''.join(filter(str.isdigit, price_raw)))
                    params = ad.find('div', class_='announcement-parameters').get_text(strip=True).lower()

                    if price <= 7000 and "dīzelis" in params and "automātiskā" in params:
                        msg = f"🔍 **Jauns atradums!**\n🚗 {title}\n💰 {price}€\n⚙️ {params}\n🔗 {ad_url}"
                        requests.get(f"https://api.telegram.org/bot{TOKEN}/sendMessage", 
                                     params={"chat_id": CHAT_ID, "text": msg})
                except:
                    continue
                
                seen_ads.add(ad_id)

        with open("seen_bmw.txt", "w") as f:
            f.write("\n".join(seen_ads))

    except Exception as e:
        print(f"Kļūda: {e}")

if __name__ == "__main__":
    check_autoplius()

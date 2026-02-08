import cloudscraper
from bs4 import BeautifulSoup
import requests

TOKEN = "8353649009:AAHZA_uGUHSxmhzCgOkeoPpyAzBH4smYU-o"
CHAT_ID = "1034267908"
URL = "https://lv.autoplius.lt/sludinajumi/lietotas-automasinas?make_id=97&model_id=1319&slist=2826775433&order_by=2&order_direction=DESC"

def check_autoplius():
    # Cloudscraper ir gudrāks par parasto requests - tas mēģina atrisināt aizsardzības testus
    scraper = cloudscraper.create_scraper(
        browser={
            'browser': 'chrome',
            'platform': 'windows',
            'desktop': True
        }
    )
    
    try:
        print(f"Mēģinu apiet aizsardzību...")
        response = scraper.get(URL, timeout=20)
        
        if response.status_code != 200:
            print(f"Pat ar viltību neizdevās. Statuss: {response.status_code}")
            return

        print("✅ Aizsardzība apieta!")
        soup = BeautifulSoup(response.text, 'html.parser')
        ads = soup.find_all('a', class_='announcement-item')

        # Ielādējam iepriekš redzētos
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
                title_elem = ad.find('div', class_='announcement-title')
                price_elem = ad.find('div', class_='announcement-pricing-info')
                param_elem = ad.find('div', class_='announcement-parameters')
                
                if title_elem and price_elem and param_elem:
                    title = title_elem.get_text(strip=True)
                    price_raw = price_elem.get_text(strip=True)
                    price = int(''.join(filter(str.isdigit, price_raw)))
                    params = param_elem.get_text(strip=True).lower()

                    # Tavs filtrs: BMW 3, Automāts, Dīzelis, Cena līdz 7000
                    if price <= 7000 and "dīzelis" in params and "automātiskā" in params:
                        msg = f"🚀 **Atrasts BMW!**\n{title}\nCena: {price}€\n{params}\n{ad_url}"
                        requests.get(f"https://api.telegram.org/bot{TOKEN}/sendMessage", 
                                     params={"chat_id": CHAT_ID, "text": msg})
                
                seen_ads.add(ad_id)

        with open("seen_bmw.txt", "w") as f:
            f.write("\n".join(seen_ads))

    except Exception as e:
        print(f"Kļūda: {e}")

if __name__ == "__main__":
    check_autoplius()

import requests
from bs4 import BeautifulSoup
import urllib.parse

# --- KONFIGURĀCIJA ---
TOKEN = "8353649009:AAHZA_uGUHSxmhzCgOkeoPpyAzBH4smYU-o"
CHAT_ID = "1034267908"
SCRAPING_ANT_KEY = "b53e4174e68e442bb5a039fe4bf95b6a"

TARGET_URL = "https://lv.autoplius.lt/sludinajumi/lietotas-automasinas?make_id=97&model_id=1319&slist=2826775433&order_by=2&order_direction=DESC"

def check_autoplius():
    # Sagatavojam saiti caur ScrapingAnt proxy, izmantojot pārlūka simulāciju
    encoded_url = urllib.parse.quote_plus(TARGET_URL)
    api_url = f"https://api.scrapingant.com/v2/general?url={encoded_url}&x-api-key={SCRAPING_ANT_KEY}&browser=true"

    try:
        print("Mēģinu pieslēgties Autoplius caur ScrapingAnt proxy...")
        response = requests.get(api_url, timeout=60)
        
        if response.status_code != 200:
            print(f"Pat proxy nepalīdzēja. Statuss: {response.status_code}")
            print(f"Atbilde no servera: {response.text[:200]}")
            return

        print("✅ Veiksmīgi ielādēta lapa!")
        soup = BeautifulSoup(response.text, 'html.parser')
        ads = soup.find_all('a', class_='announcement-item')

        # Ielādējam iepriekš redzētos sludinājumus
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
                    # Izvelkam datus no saraksta
                    price_raw = ad.find('div', class_='announcement-pricing-info').get_text(strip=True)
                    price = int(''.join(filter(str.isdigit, price_raw)))
                    params = ad.find('div', class_='announcement-parameters').get_text(strip=True).lower()

                    # Tavs filtrs: BMW 3, līdz 7000€, dīzelis un automātiskā
                    if price <= 7000 and "dīzelis" in params and "automātiskā" in params:
                        msg = f"🚀 **JAUNS BMW 3**\n💰 Cena: {price}€\n⚙️ {params}\n🔗 {ad_url}"
                        requests.get(f"https://api.telegram.org/bot{TOKEN}/sendMessage", 
                                     params={"chat_id": CHAT_ID, "text": msg})
                        new_count += 1
                except Exception as e:
                    continue
                
                seen_ads.add(ad_id)

        # Saglabājam redzētos sludinājumus
        with open("seen_bmw.txt", "w") as f:
            f.write("\n".join(seen_ads))
        
        print(f"Pārbaude pabeigta. Atrasti {new_count} jauni auto.")

    except Exception as e:
        print(f"Sistēmas kļūda: {e}")

if __name__ == "__main__":
    check_autoplius()

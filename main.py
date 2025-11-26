import requests
from bs4 import BeautifulSoup
import os
import time

TELEGRAM_TOKEN = os.environ['TELEGRAM_TOKEN']
CHAT_ID = os.environ['CHAT_ID']
ISIN = "DE000TUAG505"

# URL pro data (seznam obchodů - odtud bereme cenu, je to přesné)
URL_DATA = f"https://www.tradegate.de/orderbuch_umsaetze.php?lang=en&isin={ISIN}"

# URL pro graf (Intraday - dnešní vývoj)
# Přidáváme parametr času, aby se obrázek vždy načetl znovu a nebyl z cache
timestamp = int(time.time())
URL_CHART = f"https://www.tradegate.de/images/charts/intraday/{ISIN}.png?t={timestamp}"

def send_telegram_photo(photo_url, caption):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
    payload = {
        "chat_id": CHAT_ID,
        "photo": photo_url,
        "caption": caption,
        "parse_mode": "HTML"  # Umožní tučné písmo
    }
    # Odeslání požadavku
    requests.post(url, data=payload)

def get_tui_price():
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(URL_DATA, headers=headers)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            rows = soup.find_all('tr')
            
            for row in rows:
                cols = row.find_all('td')
                # Hledáme řádek s daty (5 sloupců)
                if len(cols) >= 5:
                    # Cena je v posledním sloupci
                    price_text = cols[-1].text.strip()
                    if len(price_text) > 0 and any(c.isdigit() for c in price_text):
                        return price_text
            
            return "N/A"
        else:
            return f"Err {response.status_code}"
    except Exception as e:
        return f"Err"

if __name__ == "__main__":
    cena = get_tui_price()
    
    # Vytvoření textu zprávy (HTML formátování)
    zprava = (
        f"<b>TUI AG</b>\n"
        f"💰 Cena: <b>{cena} EUR</b>\n"
        f"📊 <a href='https://www.tradegate.de/orderbuch.php?lang=en&isin={ISIN}'>Otevřít Tradegate</a>"
    )
    
    # Odeslání fotky s textem
    send_telegram_photo(URL_CHART, zprava)
    print("Obrázek s cenou odeslán")

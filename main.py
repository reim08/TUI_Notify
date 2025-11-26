import requests
from bs4 import BeautifulSoup
import os
import time

TELEGRAM_TOKEN = os.environ['TELEGRAM_TOKEN']
CHAT_ID = os.environ['CHAT_ID']
ISIN = "DE000TUAG505"

# Použijeme hlavní stránku (orderbuch.php), kde je Cena i Změna pohromadě
URL_PAGE = f"https://www.tradegate.de/orderbuch.php?lang=en&isin={ISIN}"

# URL pro graf (zůstává stejné)
timestamp = int(time.time())
URL_CHART = f"https://www.tradegate.de/images/charts/intraday/{ISIN}.png?t={timestamp}"

def send_telegram_photo(photo_url, caption):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
    payload = {
        "chat_id": CHAT_ID,
        "photo": photo_url,
        "caption": caption,
        "parse_mode": "HTML" # Důležité pro tučné písmo
    }
    requests.post(url, data=payload)

def get_tui_data():
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(URL_PAGE, headers=headers)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Najdeme všechny buňky tabulek na stránce
            tds = soup.find_all('td')
            
            price = "N/A"
            change = "?"
            
            # Procházíme buňky a hledáme popisky "Last" a "Change"
            # Hodnota je vždy v buňce hned vedle (i+1)
            for i, td in enumerate(tds):
                text = td.text.strip().lower()
                
                # Hledáme cenu (Last)
                if text == "last" and i + 1 < len(tds):
                    price = tds[i+1].text.strip()
                
                # Hledáme změnu (Change)
                if text == "change" and i + 1 < len(tds):
                    change = tds[i+1].text.strip()

            return price, change
        else:
            return "Err", "Err"
    except Exception as e:
        return "Err", str(e)

if __name__ == "__main__":
    cena, zmena = get_tui_data()
    
    # Vybereme emoji podle toho, zda je změna plusová nebo mínusová
    emoji = "📉"
    if "+" in zmena:
        emoji = "📈"
    elif "0.00" in zmena:
        emoji = "😐"
    
    # Sestavení zprávy (HTML tag <b> dělá tučné písmo)

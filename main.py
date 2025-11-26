import requests
from bs4 import BeautifulSoup
import os

# Načtení hesel z GitHubu
TELEGRAM_TOKEN = os.environ['TELEGRAM_TOKEN']
CHAT_ID = os.environ['CHAT_ID']
# Vaše URL s tabulkou
URL = "https://www.tradegate.de/orderbuch_umsaetze.php?lang=en&isin=DE000TUAG505"

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message
    }
    requests.post(url, json=payload)

def get_tui_price():
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(URL, headers=headers)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # NOVÁ LOGIKA PRO TABULKU:
            # Najdeme všechny buňky tabulky (tag 'td')
            cells = soup.find_all('td')
            
            # Projdeme prvních 10 buněk (první řádek tabulky je hned na začátku)
            found_prices = []
            for cell in cells[:15]:
                text = cell.text.strip()
                # Hledáme text, který:
                # 1. Obsahuje číslice
                # 2. Obsahuje čárku (německý formát ceny 7,15)
                # 3. Neobsahuje dvojtečku (to by byl čas 14:05)
                if any(char.isdigit() for char in text) and ',' in text and ':' not in text:
                    found_prices.append(text)

            if found_prices:
                # Obvykle je cena první nebo druhá hodnota (Volume | Price)
                # Vrátíme první nalezenou hodnotu, která vypadá jako cena
                return found_prices[0]
            else:
                return "Cena nenalezena v tabulce (zkontroluj HTML)"
        else:
            return f"Chyba připojení: {response.status_code}"
    except Exception as e:
        return f"Chyba skriptu: {str(e)}"

if __name__ == "__main__":
    cena = get_tui_price()
    zprava = f"📈 TUI Aktuální cena (Tradegate):\n\n{cena} EUR\n\n{URL}"
    send_telegram_message(zprava)
    print("Zpráva odeslána")

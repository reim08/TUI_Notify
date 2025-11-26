import requests
from bs4 import BeautifulSoup
import os
import re

TELEGRAM_TOKEN = os.environ['TELEGRAM_TOKEN']
CHAT_ID = os.environ['CHAT_ID']
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
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(URL, headers=headers)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Hledáme všechny řádky tabulky
            rows = soup.find_all('tr')
            
            # Procházíme řádky a hledáme první, který obsahuje data
            for row in rows:
                cols = row.find_all('td')
                # Očekáváme řádek, který má alespoň 3 sloupce (Čas | Cena | Objem)
                if len(cols) >= 3:
                    # Tradegate formát: 1. sloupec=Čas, 2. sloupec=Cena, 3. sloupec=Objem
                    price_text = cols[1].text.strip()
                    
                    # Kontrola, zda to vypadá jako cena (obsahuje číslice a tečku nebo čárku)
                    if any(c.isdigit() for c in price_text) and ('.' in price_text or ',' in price_text):
                        return price_text
            
            return "Cena nenalezena (Tabulka má jiný formát?)"
        else:
            return f"Chyba připojení: {response.status_code}"
    except Exception as e:
        return f"Chyba skriptu: {str(e)}"

if __name__ == "__main__":
    cena = get_tui_price()
    zprava = f"📈 TUI Aktuální cena (Tradegate):\n\n{cena} EUR\n\n{URL}"
    send_telegram_message(zprava)
    print("Zpráva odeslána")

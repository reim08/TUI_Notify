import requests
from bs4 import BeautifulSoup
import os

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
            
            # Najdeme všechny řádky tabulky
            rows = soup.find_all('tr')
            
            for row in rows:
                cols = row.find_all('td')
                # Podle screenshotu má tabulka 5 sloupců: Date | Time | Volume | Order Vol | PRICE
                # Hledáme řádek, který má data (není to záhlaví)
                if len(cols) >= 5:
                    # Vezmeme ÚPLNĚ POSLEDNÍ sloupec (v Pythonu index -1 znamená poslední)
                    price_text = cols[-1].text.strip()
                    
                    # Rychlá kontrola, zda to není prázdné a vypadá to jako číslo
                    # (ignorujeme řádky, kde by cena chyběla)
                    if len(price_text) > 0 and any(c.isdigit() for c in price_text):
                        return price_text
            
            return "Cena nenalezena (Tabulka je prázdná?)"
        else:
            return f"Chyba připojení: {response.status_code}"
    except Exception as e:
        return f"Chyba skriptu: {str(e)}"

if __name__ == "__main__":
    cena = get_tui_price()
    # Přidáme formátování, aby to vypadalo hezky
    zprava = f"📈 TUI: {cena} EUR"
    send_telegram_message(zprava)
    print("Zpráva odeslána")

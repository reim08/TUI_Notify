import requests
from bs4 import BeautifulSoup
import os

# Konfigurace (Tyto hodnoty si načteme z nastavení GitHubu)
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
        # Stáhneme stránku (tváříme se jako prohlížeč, aby nás neblokovali)
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(URL, headers=headers)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            # Tradegate má cenu obvykle v ID "last" nebo "bid"/"ask"
            # Zde hledáme element s ID 'last'
            price_tag = soup.find(id="last")
            
            if price_tag:
                price = price_tag.text.strip()
                return price
            else:
                return "Cena nenalezena (změna struktury webu?)"
        else:
            return f"Chyba připojení: {response.status_code}"
    except Exception as e:
        return f"Chyba skriptu: {str(e)}"

if __name__ == "__main__":
    cena = get_tui_price()
    zprava = f"📈 TUI Aktuální cena (Tradegate):\n\n{cena}\n\n{URL}"
    send_telegram_message(zprava)
    print("Zpráva odeslána")

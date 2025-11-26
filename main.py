import requests
from bs4 import BeautifulSoup
import os
import time

TELEGRAM_TOKEN = os.environ['TELEGRAM_TOKEN']
CHAT_ID = os.environ['CHAT_ID']
ISIN = "DE000TUAG505"

# URL stránky a grafu
URL_PAGE = f"https://www.tradegate.de/orderbuch.php?lang=en&isin={ISIN}"
timestamp = int(time.time())
URL_CHART = f"https://www.tradegate.de/images/charts/intraday/{ISIN}.png?t={timestamp}"

def send_telegram(text, photo_url=None):
    """Univerzální funkce: zkusí poslat fotku, když to nejde, pošle text."""
    try:
        if photo_url:
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
            payload = {
                "chat_id": CHAT_ID,
                "photo": photo_url,
                "caption": text,
                "parse_mode": "HTML"
            }
            r = requests.post(url, data=payload)
            # Pokud API vrátí chybu (např. špatný formát obrázku), vyvoláme výjimku
            r.raise_for_status()
        else:
            # Pouze text
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
            payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}
            requests.post(url, json=payload)
            
    except Exception as e:
        print(f"Chyba při odesílání fotky: {e}")
        # Záložní plán: Poslat jen text, pokud fotka selhala
        if photo_url:
            send_telegram(text + "\n(Obrázek se nepodařilo načíst)", photo_url=None)

def get_data_safe():
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(URL_PAGE, headers=headers)
        
        if response.status_code != 200:
            return None, None, f"Chyba webu: {response.status_code}"

        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Zkusíme najít ID, které Tradegate často používá
        price_tag = soup.find(id="last")
        delta_tag = soup.find(id="delta")
        
        price = None
        change = None

        # 1. Pokus přes ID (nejpřesnější)
        if price_tag: price = price_tag.text.strip()
        if delta_tag: change = delta_tag.text.strip()

        # 2. Pokus přes textové popisky (pokud ID selže)
        if not price or not change:
            tds = soup.find_all('td')
            for i, td in enumerate(tds):
                txt = td.text.strip().lower()
                # Hledáme buňku s nápisem "Last" a vezmeme tu vedle
                if not price and "last" == txt and i+1 < len(tds):
                    price = tds[i+1].text.strip()
                # Hledáme buňku s nápisem "Change" a vezmeme tu vedle
                if not change and "change" in txt and i+1 < len(tds):
                    change = tds[i+1].text.strip()

        if price:
            return price, change, None
        else:
            return None, None, "Nenašel jsem cenu v HTML kódu."

    except Exception as e:
        return None, None, f"Chyba skriptu: {str(e)}"

if __name__ == "__main__":
    print("Spouštím skript...")
    cena, zmena, chyba = get_data_safe()

    if chyba:
        # Pokud nastala chyba, pošleme o tom zprávu (aby uživatel věděl)
        print(f"Chyba: {chyba}")
        send_telegram(f"⚠️ <b>Chyba bota:</b>\n{chyba}")
    else:
        # Pokud je vše OK
        if zmena is None: zmena = "?"
        
        emoji = "😐"
        if "+" in zmena: emoji = "📈"
        elif "-" in zmena: emoji = "📉"

        zprava = (
            f"<b>TUI AG</b>\n"
            f"💰 Cena: <b>{cena} EUR</b>\n"
            f"{emoji} Změna: <b>{zmena}</b>\n\n"
            f"<a href='{URL_PAGE}'>Web Tradegate</a>"
        )
        
        print(f"Odesílám: {cena} / {zmena}")
        send_telegram(zprava, URL_CHART)

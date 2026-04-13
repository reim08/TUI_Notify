import requests
from bs4 import BeautifulSoup
import os
import time

TELEGRAM_TOKEN = os.environ['TELEGRAM_TOKEN']
CHAT_ID = os.environ['CHAT_ID']

# ─── Konfigurace ETF ──────────────────────────────────────────────────────────
# Formát: "TICKER": ("Zobrazovaný název", "ISIN")
# ISINy ověř na Tradegate, pokud by scraping nefungoval.
ETFS = {
    "SXR8": ("S&P 500",            "IE00B5BMR087"),
    "SXR7": ("Nasdaq 100",         "IE00B53SZB19"),
    "AMEA": ("Asie",               "IE00B5L8K969"),
    "SXRV": ("Evropa",             "IE00B4K48X80"),
    "ZPRS": ("Malé společnosti",   "IE00BCBJG560"),
}

# Graf se pošle vždy pro tento ticker (SP500)
CHART_TICKER = "SXR8"
# ─────────────────────────────────────────────────────────────────────────────


def tradegate_url(isin):
    return f"https://www.tradegate.de/orderbuch.php?lang=en&isin={isin}"


def chart_url(isin):
    return f"https://www.tradegate.de/images/charts/intraday/{isin}.png?t={int(time.time())}"


def get_data(isin):
    """Stáhne cenu a změnu z Tradegate. Vrací (price, change, error)."""
    try:
        r = requests.get(tradegate_url(isin), headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        if r.status_code != 200:
            return None, None, f"HTTP {r.status_code}"

        soup = BeautifulSoup(r.text, 'html.parser')

        price = soup.find(id="last")
        change = soup.find(id="delta")
        price = price.text.strip() if price else None
        change = change.text.strip() if change else None

        # Záložní metoda přes TD tabulku
        if not price or not change:
            tds = soup.find_all('td')
            for i, td in enumerate(tds):
                txt = td.text.strip().lower()
                if not price and txt == "last" and i + 1 < len(tds):
                    price = tds[i + 1].text.strip()
                if not change and "change" in txt and i + 1 < len(tds):
                    change = tds[i + 1].text.strip()

        if price:
            return price, change, None
        return None, None, "Cena nenalezena v HTML"

    except Exception as e:
        return None, None, str(e)


def format_line(name, price, change):
    """Formátuje jeden řádek zprávy."""
    change = change or "?"
    if "+" in change:
        emoji = "📈"
    elif "-" in change:
        emoji = "📉"
    else:
        emoji = "😐"
    return f"{emoji} <b>{name}:</b> {price} EUR  <i>({change})</i>"


def send_telegram(text, photo_url=None):
    """Pošle zprávu (s fotkou nebo bez). Při selhání fotky zkusí jen text."""
    try:
        if photo_url:
            r = requests.post(
                f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto",
                data={"chat_id": CHAT_ID, "photo": photo_url,
                      "caption": text, "parse_mode": "HTML"},
                timeout=15
            )
            r.raise_for_status()
            return
    except Exception as e:
        print(f"Graf se nepodařilo odeslat: {e}")
        text += "\n⚠️ (Graf nedostupný)"

    # Fallback – jen text
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            json={"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"},
            timeout=15
        )
    except Exception as e:
        print(f"Chyba při odesílání textu: {e}")


# ─── Hlavní logika ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("Spouštím skript...")

    lines = ["<b>📊 Přehled ETF</b>\n"]

    for ticker, (name, isin) in ETFS.items():
        price, change, error = get_data(isin)
        if error:
            print(f"  ⚠️  {ticker}: {error}")
            lines.append(f"⚠️ <b>{name}:</b> chyba načítání")
        else:
            print(f"  ✅ {ticker}: {price} ({change})")
            lines.append(format_line(name, price, change))
        time.sleep(0.5)  # Slušné chování vůči serveru

    sp500_isin = ETFS[CHART_TICKER][1]
    lines.append(f"\n<a href='{tradegate_url(sp500_isin)}'>Tradegate – {CHART_TICKER}</a>")

    zprava = "\n".join(lines)
    print("\nOdesílám zprávu do Telegramu...")
    send_telegram(zprava, chart_url(sp500_isin))
    print("Hotovo!")

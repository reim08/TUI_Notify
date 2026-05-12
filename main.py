import requests
from bs4 import BeautifulSoup
import os
import time

TELEGRAM_TOKEN = os.environ[“TELEGRAM_TOKEN”]
CHAT_ID = os.environ[“CHAT_ID”]

# Konfigurace ETF

ETFS = {
“CSG”: (“CSG”, “NL0015073TS8”),
“SXR8”: (“S&P 500”, “IE00B5BMR087”),
“SXR7”: (“Nasdaq 100”, “IE00B53SZB19”),
“AMEA”: (“Asie”, “IE00B5L8K969”),
“SXRV”: (“Evropa”, “IE00B4K48X80”),
“ZPRS”: (“Male spolecnosti”, “IE00BCBJG560”),
}

CHART_TICKER = “SXR8”

def tradegate_url(isin):
return f”https://www.tradegate.de/orderbuch.php?lang=en&isin={isin}”

def chart_url(isin):
return f”https://www.tradegate.de/images/charts/intraday/{isin}.png?t={int(time.time())}”

def get_data(isin):
“”“Stahne cenu a zmenu z Tradegate.”””
try:
r = requests.get(tradegate_url(isin), headers={“User-Agent”: “Mozilla/5.0”}, timeout=10)
if r.status_code != 200:
return None, None, f”HTTP {r.status_code}”

```
    soup = BeautifulSoup(r.text, "html.parser")

    price = soup.find(id="last")
    change = soup.find(id="delta")
    price = price.text.strip() if price else None
    change = change.text.strip() if change else None

    # Zalozni metoda pres TD tabulku
    if not price or not change:
        tds = soup.find_all("td")
        for i, td in enumerate(tds):
            txt = td.text.strip().lower()
            if not price and txt == "last" and i + 1 < len(tds):
                price = tds[i + 1].text.strip()
            if not change and "change" in txt and i + 1 < len(tds):
                change = tds[i + 1].text.strip()

    if price:
        return price, change, None
    return None, None, "Cena nenalezena"

except Exception as e:
    return None, None, str(e)
```

def format_line(name, price, change):
“”“Formatuje jeden radek zpravy.”””
change = change or “?”
if “+” in change:
emoji = “^”
elif “-” in change:
emoji = “v”
else:
emoji = “-”
return f”{emoji} {name}: {price} EUR ({change})”

def send_telegram(text, photo_url=None):
“”“Posle zpravu do Telegramu.”””
try:
if photo_url:
r = requests.post(
f”https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto”,
data={“chat_id”: CHAT_ID, “photo”: photo_url, “caption”: text, “parse_mode”: “HTML”},
timeout=15,
)
r.raise_for_status()
return
except Exception as e:
print(f”Graf se nepodarilo odeslat: {e}”)
text += “\n(Graf nedostupny)”

```
try:
    requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
        json={"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"},
        timeout=15,
    )
except Exception as e:
    print(f"Chyba pri odesílani textu: {e}")
```

if **name** == “**main**”:
print(“Spoustim skript…”)

```
lines = ["PREHLED ETF\n"]

for ticker, (name, isin) in ETFS.items():
    price, change, error = get_data(isin)
    if error:
        print(f"  ! {ticker}: {error}")
        lines.append(f"! {name}: chyba nacitani")
    else:
        print(f"  OK {ticker}: {price} ({change})")
        lines.append(format_line(name, price, change))
    time.sleep(0.5)

sp500_isin = ETFS[CHART_TICKER][1]
lines.append(f"\nTradegate: {tradegate_url(sp500_isin)}")

zprava = "\n".join(lines)
print("\nOdesílam zpravu do Telegramu...")
send_telegram(zprava, chart_url(sp500_isin))
print("Hotovo!")
```

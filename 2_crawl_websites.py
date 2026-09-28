"""
SCHRITT 2: Websites crawlen und anreichern
--------------------------------------------
Fragen: 
Was ist mit den Leads, die zwar keine Website haben, aber z.b. im Google eintrag, eine
Email gelistet haben? 
Crawlt NUR die Leads, die in Schritt 1 als "echte_website" eingestuft
wurden. Prüft Startseite + Kontakt-/Impressum-Unterseiten auf:
  - E-Mail-Adresse (per Regex)
  - Ladezeit (Sekunden)
  - Mobile-Tauglichkeit (Viewport-Meta-Tag vorhanden?)
  - HTTPS vorhanden?

Ausgabe: leads_angereichert.csv (Basis für Schritt 3)

"""

import pandas as pd
import requests
from bs4 import BeautifulSoup
import re
import time

INPUT_FILE = "leads_klassifiziert.csv"
OUTPUT_FILE = "leads_angereichert.csv"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/(KHTML, like Gecko) "
    )
}

# Diese Unterseiten werden zusätzlich zur Startseite geprüft,
# da E-Mails oft nicht auf der Startseite stehen
UNTERSEITEN = ["/kontakt", "/impressum", "/contact", "/about"]

EMAIL_REGEX = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"


def hole_seite(url, timeout=8):
    """Ruft eine URL ab, gibt (html, ladezeit) oder (None, None) zurück."""
    try:
        start = time.time()
        resp = requests.get(url, headers=HEADERS, timeout=timeout)
        ladezeit = round(time.time() - start, 2)
        if resp.status_code == 200:
            return resp.text, ladezeit
        return None, None
    except requests.RequestException:
        return None, None


def finde_email(html):
    treffer = re.findall(EMAIL_REGEX, html)
    # Typische Spam-Schutz-Fake-Adressen und Bild-Domains rausfiltern
    treffer = [t for t in treffer if not any(
        x in t.lower() for x in ["example.com", "sentry.io", ".png", ".jpg"]
    )]
    return treffer[0] if treffer else None


def hat_mobile_viewport(html):
    soup = BeautifulSoup(html, "html.parser")
    tag = soup.find("meta", attrs={"name": "viewport"})
    return tag is not None


def analysiere_website(url):
    """Crawlt Startseite + Unterseiten, gibt ein Dict mit Ergebnissen zurück."""
    ergebnis = {
        "email_gefunden": None,
        "ladezeit_sek": None,
        "mobile_optimiert": None,
        "https": None,
        "erreichbar": False,
    }

    if not url.startswith("http"):
        url = "https://" + url

    ergebnis["https"] = url.startswith("https://")

    html, ladezeit = hole_seite(url)
    if html is None:
        return ergebnis  # Website nicht erreichbar -> bleibt bei Defaults

    ergebnis["erreichbar"] = True
    ergebnis["ladezeit_sek"] = ladezeit
    ergebnis["mobile_optimiert"] = hat_mobile_viewport(html)
    email = finde_email(html)

    # Falls auf der Startseite keine E-Mail steht, Unterseiten prüfen
    if email is None:
        basis_url = url.rstrip("/")
        for pfad in UNTERSEITEN:
            time.sleep(1.5)  # Server nicht überlasten
            sub_html, _ = hole_seite(basis_url + pfad)
            if sub_html:
                email = finde_email(sub_html)
                if email:
                    break

    ergebnis["email_gefunden"] = email
    return ergebnis


def main():
    print(f"Lese {INPUT_FILE} ein...")
    df = pd.read_csv(INPUT_FILE)

    nur_echte_websites = df[df["lead_kategorie"] == "echte_website"].copy()
    print(f"{len(nur_echte_websites)} Websites werden gecrawlt (das kann dauern)...")

    ergebnisse = []
    website_spalte = "website" if "website" in df.columns else "url"

    for i, row in nur_echte_websites.iterrows():
        url = row[website_spalte]
        print(f"  [{i+1}/{len(df)}] Crawle: {url}")
        ergebnis = analysiere_website(url)
        ergebnisse.append(ergebnis)
        time.sleep(1.5)  # Server nicht überlasten

    ergebnis_df = pd.DataFrame(ergebnisse, index=nur_echte_websites.index)
    df = df.join(ergebnis_df)

    df.to_csv(OUTPUT_FILE, index=False)
    print(f"\nFertig! Ergebnis gespeichert in: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()

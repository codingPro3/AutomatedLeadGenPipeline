"""
SCHRITT 1: Leads klassifizieren
--------------------------------
Liest den CSV-Export von Apify ein und ordnet jeden Lead einer von
drei Kategorien zu:
  - "keine_website"     -> kein Website-Feld vorhanden
  - "social_media"       -> Website-Feld verweist auf Instagram/Facebook/etc.
  - "echte_website"      -> eigene Domain vorhanden
 

"""
 
import pandas as pd
import re
from branchen_konfig import erkenne_branche
 
INPUT_FILE = "apify_export.csv"
OUTPUT_FILE = "leads_klassifiziert.csv"
 
# Diese Domains gelten als "nur Social Media", keine echte eigene Website
SOCIAL_MEDIA_DOMAINS = [
    "instagram.com",
    "facebook.com",
    "linktr.ee",
    "wa.me",
    "wa.link",
    "tiktok.com",
    "linktree.com",
    "beacons.ai",
]
 
# Nur diese Spalten werden in der Ausgabe behalten (Google Maps liefert oft
# 20-50 zusätzliche "Amenity"-Spalten wie "Dusche", "Kostenloses WLAN" etc.,
# die für die Lead-Bewertung nicht gebraucht werden). Jede Zeile ist eine
# Gruppe möglicher Spaltennamen - die erste vorhandene wird übernommen.
RELEVANTE_SPALTEN_GRUPPEN = [
    ["title", "name"],
    ["address", "Address"],
    ["phone", "phoneNumber", "phone_number"],
    ["website", "Website", "url", "site"],
    ["totalScore", "rating", "Rating"],
    ["reviewsCount", "reviews"],
    ["category", "categoryName"],
    ["placeId", "place_id"],
]
 
 
def klassifiziere_website(url):
    """Gibt die Kategorie für eine gegebene Website-URL zurück."""
    if pd.isna(url) or str(url).strip() == "":
        return "keine_website"
 
    url_lower = str(url).lower()
    for domain in SOCIAL_MEDIA_DOMAINS:
        if domain in url_lower:
            return "social_media"
 
    return "echte_website"
 
 
def main():
    print(f"Lese {INPUT_FILE} ein...")
    df = pd.read_csv(INPUT_FILE)
 
    # Apify nennt die Spalte je nach Actor unterschiedlich - wir versuchen
    # die gängigsten Varianten automatisch zu erkennen
    website_spalte = None
    for kandidat in ["website", "Website", "url", "site"]:
        if kandidat in df.columns:
            website_spalte = kandidat
            break
 
    if website_spalte is None:
        print("WARNUNG: Konnte keine Website-Spalte finden.")
        print(f"Verfügbare Spalten: {list(df.columns)}")
        print("Bitte passe 'website_spalte' im Skript manuell an.")
        return
 
    df["lead_kategorie"] = df[website_spalte].apply(klassifiziere_website)
 
    # Branche automatisch aus der Google-Maps-Kategorie erkennen (Nagelstudio,
    # Friseur, Kosmetikstudio, ...) - steuert spaeter Texte/Bilder der Vorschau-Website
    kategorie_spalte = None
    for kandidat in ["category", "categoryName"]:
        if kandidat in df.columns:
            kategorie_spalte = kandidat
            break
    df["branche"] = df[kategorie_spalte].apply(erkenne_branche) if kategorie_spalte else "beauty_allgemein"
 
    # Nur relevante Spalten behalten (Amenity-Spalten wie "Dusche" etc. rausfiltern)
    behaltene_spalten = []
    for gruppe in RELEVANTE_SPALTEN_GRUPPEN:
        for kandidat in gruppe:
            if kandidat in df.columns and kandidat not in behaltene_spalten:
                behaltene_spalten.append(kandidat)
                break
    behaltene_spalten.append("lead_kategorie")
    behaltene_spalten.append("branche")
 
    anzahl_vorher = len(df.columns)
    df = df[behaltene_spalten]
    print(f"\nSpalten reduziert: {anzahl_vorher} -> {len(df.columns)}")
 
    # Duplikate entfernen: Google Maps liefert denselben Betrieb manchmal
    # mehrfach, wenn er bei mehreren Suchbegriffen auftaucht. Bevorzugt wird
    # nach placeId/place_id dedupliziert (eindeutigste ID), sonst nach Telefonnummer.
    dedupe_spalte = None
    for kandidat in ["placeId", "place_id", "phone", "phoneNumber", "phone_number"]:
        if kandidat in df.columns:
            dedupe_spalte = kandidat
            break
 
    anzahl_vor_dedupe = len(df)
    if dedupe_spalte:
        df = df.drop_duplicates(subset=[dedupe_spalte], keep="first")
        entfernt = anzahl_vor_dedupe - len(df)
        print(f"Duplikate entfernt (nach '{dedupe_spalte}'): {entfernt}")
    else:
        print("WARNUNG: Keine geeignete Spalte für Duplikat-Prüfung gefunden - "
              "es wurde nicht dedupliziert.")
 
    # Kurze Zusammenfassung ausgeben
    print("\n--- Zusammenfassung ---")
    print(df["lead_kategorie"].value_counts())
    print("\n--- Branchen-Verteilung ---")
    print(df["branche"].value_counts())
    print(f"\nGesamt: {len(df)} Leads")
 
    df.to_csv(OUTPUT_FILE, index=False)
    print(f"\nFertig! Ergebnis gespeichert in: {OUTPUT_FILE}")
 
 
if __name__ == "__main__":
    main()
 
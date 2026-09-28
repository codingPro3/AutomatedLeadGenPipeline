"""
SCHRITT 3: Leads bewerten und final sortieren
-------------------------------------------------
Vergibt Punkte nach der Scoring-Tabelle und erstellt die finale,
sortierte Leadliste als Excel-Datei (leichter lesbar als CSV).

Ausgabe: finale_leadliste.xlsx

"""

import pandas as pd

INPUT_FILE = "leads_angereichert.csv"
OUTPUT_FILE = "finale_leadliste.xlsx"


def berechne_score(row):
    score = 0
    gruende = []

    # Kein Website / nur Social Media = leichtester Abschluss
    if row.get("lead_kategorie") == "keine_website":
        score += 30
        gruende.append("Keine Website")
    elif row.get("lead_kategorie") == "social_media":
        score += 20
        gruende.append("Nur Social Media")

    # Schlechte Ladezeit bei vorhandener Website
    if row.get("ladezeit_sek") and row["ladezeit_sek"] > 3:
        score += 15
        gruende.append("Langsame Website")

    # Nicht mobile-optimiert
    if row.get("mobile_optimiert") is False:
        score += 15
        gruende.append("Nicht mobiltauglich")

    # Kein HTTPS = unseriös wirkend, gutes Argument
    if row.get("https") is False:
        score += 10
        gruende.append("Kein HTTPS")

    # Keine E-Mail auffindbar -> schwerer erreichbar, aber trotzdem Potenzial
    if pd.isna(row.get("email_gefunden")):
        score += 5
        gruende.append("Keine E-Mail auffindbar")

    # Gute Bewertungen = zahlungsfähigerer, seriöser Betrieb
    rating_spalte = row.get("totalScore") or row.get("rating") or row.get("Rating")
    reviews_spalte = row.get("reviewsCount") or row.get("reviews")
    try:
        if rating_spalte and float(rating_spalte) >= 4.5:
            score += 10
            gruende.append("Sehr gute Bewertungen")
        if reviews_spalte and float(reviews_spalte) >= 50:
            score += 5
            gruende.append("Viele Reviews (etabliert)")
    except (ValueError, TypeError):
        pass

    return pd.Series({"score": score, "score_begruendung": ", ".join(gruende)})


def main():
    print(f"Lese {INPUT_FILE} ein...")
    df = pd.read_csv(INPUT_FILE)

    score_ergebnisse = df.apply(berechne_score, axis=1)
    df = pd.concat([df, score_ergebnisse], axis=1)

    df = df.sort_values("score", ascending=False)

    df.to_excel(OUTPUT_FILE, index=False)
    print(f"\nFertig! Sortierte Leadliste gespeichert in: {OUTPUT_FILE}")
    print("\nTop 5 Leads:")
    anzeige_spalten = [c for c in ["title", "name", "score", "score_begruendung"] if c in df.columns]
    print(df[anzeige_spalten].head(5).to_string(index=False))


if __name__ == "__main__":
    main()

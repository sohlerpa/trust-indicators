"""
sourcetype.py

Einfacher Source-Type-Classifier.

- nutzt (falls vorhanden) die Datei 'sources_de.json'
- ergänzt manuell wichtige Quellen wie tagesschau.de
- normalisiert URLs so, dass es egal ist, ob:
  - mit/ohne https
  - mit/ohne www
  - mit/ohne Pfad (z.B. /impressum)

Kategorien:
- public_service  -> öffentlich-rechtlich
- state           -> staatlich
- private         -> privat (Fallback)
"""

import json
from pathlib import Path
from urllib.parse import urlparse

# Pfad zur JSON-Datei mit Wikidata-Daten (falls vorhanden)
DATA_FILE = Path(__file__).with_name("sources_de.json")

# Basis-Datenstruktur
SOURCES = {}

# 1) Versuche, sources_de.json zu laden (falls du das Wikidata-Skript schon ausgeführt hast)
try:
    with DATA_FILE.open(encoding="utf-8") as f:
        SOURCES = json.load(f)
except Exception as e:
    # Kein Abbruch, wir arbeiten einfach nur mit manuellen Quellen
    print("Hinweis: Konnte sources_de.json nicht laden:", e)
    SOURCES = {}

# 2) Manuelle Ergänzungen / Overrides
MANUAL_SOURCES_DE = {
    "tagesschau.de": {
        "source_type": "public_service",
        "org_name": "Tagesschau (ARD-aktuell)",
        "country": "DE",
    },
    # Hier kannst du später mehr hinzufügen, z.B.:
    # "heute.de": {...}
}

# Manuelle Quellen überschreiben ggf. Wikidata-Daten
for domain, info in MANUAL_SOURCES_DE.items():
    SOURCES[domain] = info


def normalize_host(url_or_host):
    """
    Normalisiert alles auf eine Domain wie 'tagesschau.de'.

    Beispiele:
      'tagesschau.de'                         -> 'tagesschau.de'
      'www.tagesschau.de'                     -> 'tagesschau.de'
      'https://www.tagesschau.de'             -> 'tagesschau.de'
      'https://www.tagesschau.de/impressum'   -> 'tagesschau.de'
    """
    text = url_or_host.strip()

    # Wenn kein Schema drin ist, eins ergänzen, damit urlparse sauber funktioniert
    if "://" not in text:
        text = "http://" + text

    parsed = urlparse(text)

    host = parsed.netloc or parsed.path   # falls jemand nur 'tagesschau.de' eingibt
    host = host.lower()

    # Port entfernen (z.B. example.com:8080)
    if ":" in host:
        host = host.split(":", 1)[0]

    # www. entfernen
    if host.startswith("www."):
        host = host[4:]

    return host


def classify_source(url_or_host):
    """
    Liefert 'public_service', 'state' oder 'private'.

    Logik:
    - Host normalisieren (siehe normalize_host)
    - In SOURCES nachschlagen
    - Falls gefunden -> type zurückgeben
    - Falls nicht -> 'private'
    """
    host = normalize_host(url_or_host)
    info = SOURCES.get(host)
    if info is not None:
        return info.get("source_type", "private")
    return "private"


if __name__ == "__main__":
    # Kleine Tests direkt beim Ausführen von 'python sourcetype.py'
    test_inputs = [
        "tagesschau.de",
        "www.tagesschau.de",
        "https://www.tagesschau.de",
        "https://www.tagesschau.de/impressum",
        "https://www.bundesregierung.de/breg-de",
        "https://www.spiegel.de",
    ]

    print("Test der Source-Type-Klassifikation:\n")
    for item in test_inputs:
        print(f"{item:45s} -> {classify_source(item)}")

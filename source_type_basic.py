"""
source_type_basic.py

Minimaler Source-Type-Classifier zum Testen.

- Erkennt tagesschau.de sicher als 'public_service'
- Erkennt bundesregierung.de als 'state'
- Alles andere -> 'private'

Egal ob:
- mit/ohne https
- mit/ohne www
- mit Pfad (z.B. /impressum)
"""

from urllib.parse import urlparse


# 🔹 Kleine Test-Datenbank
SOURCE_MAP = {
    "tagesschau.de": "public_service",
    "bundesregierung.de": "state",
    "bundestag.de": "state",
    "spiegel.de": "private",   # explizit privat
}


def normalize_host(url_or_host: str) -> str:
    """
    Normalisiert alles auf eine Domain wie 'tagesschau.de'.

    Beispiele:
      'tagesschau.de'                         -> 'tagesschau.de'
      'www.tagesschau.de'                     -> 'tagesschau.de'
      'https://www.tagesschau.de'             -> 'tagesschau.de'
      'https://www.tagesschau.de/impressum'   -> 'tagesschau.de'
    """
    text = url_or_host.strip()

    # Wenn kein Schema drin ist, eins ergänzen, damit urlparse funktioniert
    if "://" not in text:
        text = "http://" + text

    parsed = urlparse(text)

    host = parsed.netloc or parsed.path
    host = host.lower()

    # Port entfernen, falls vorhanden
    if ":" in host:
        host = host.split(":", 1)[0]

    # www. entfernen
    if host.startswith("www."):
        host = host[4:]

    return host


def classify_source(url_or_host: str) -> str:
    """
    Liefert 'public_service', 'state' oder 'private'.
    """
    host = normalize_host(url_or_host)
    return SOURCE_MAP.get(host, "private")


if __name__ == "__main__":
    # Tests, damit du direkt siehst, was passiert
    test_inputs = [
        "tagesschau.de",
        "www.tagesschau.de",
        "https://www.tagesschau.de",
        "https://www.tagesschau.de/impressum",
        "bundesregierung.de",
        "https://www.bundesregierung.de/breg-de",
        "https://www.spiegel.de/politik/deutschland",
        "example.com",
    ]

    print("Test der Source-Type-Klassifikation:\n")
    for item in test_inputs:
        print(f"{item:55s} -> {classify_source(item)}")

from typing import Optional
import requests
import trafilatura

USER_AGENT = "TrustIndicators-FactCheck/0.1 (contact: your-email@example.com)"

def fetch_url_text(url: str) -> Optional[str]:
    """
    Holt HTML von einer URL und extrahiert den Hauptartikeltext.
    """
    try:
        r = requests.get(url, timeout=20, headers={"User-Agent": USER_AGENT})
    except requests.RequestException as e:
        print("⚠️ Netzwerkfehler:", e)
        return None

    if r.status_code != 200:
        print(f"⚠️ HTTP {r.status_code} beim Laden der URL")
        return None

    downloaded = trafilatura.extract(r.text, include_comments=False, include_tables=False)
    if not downloaded or len(downloaded.strip()) < 200:
        # 200 Zeichen ist nur ein grober Filter
        print("⚠️ Konnte keinen sinnvollen Artikeltext extrahieren.")
        return None

    return downloaded.strip()

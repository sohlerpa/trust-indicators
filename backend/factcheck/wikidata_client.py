from typing import Optional, Dict, Any
import requests

# Basis-URLs für Wikidata
WIKIDATA_SEARCH_URL = "https://www.wikidata.org/w/api.php"
WIKIDATA_SPARQL_URL = "https://query.wikidata.org/sparql"

# Bitte anpassen (eine echte Kontaktinfo hilft, nicht geblockt zu werden)
USER_AGENT = "TrustIndicators-FactCheck/0.1 (contact: your-email@example.com)"


def _request_get(url: str, **kwargs) -> Optional[requests.Response]:
    """
    Helper: führt einen GET-Request aus, setzt User-Agent
    und fängt Netzwerkfehler ab.
    """
    headers = kwargs.pop("headers", {})
    headers.setdefault("User-Agent", USER_AGENT)

    try:
        response = requests.get(url, headers=headers, timeout=15, **kwargs)
    except requests.RequestException as e:
        print(f"⚠️ Netzwerkfehler bei Anfrage an {url}: {e}")
        return None

    # Kein raise_for_status, damit wir Statuscode selbst ausgeben können
    if response.status_code != 200:
        print(f"⚠️ HTTP-Fehler {response.status_code} bei {url}")
        try:
            print("Antwort (gekürzt):", response.text[:300])
        except Exception:
            pass
        return None

    return response


def search_entity(name: str, language: str = "de") -> Optional[str]:
    """
    Suche eine Entität in Wikidata und gib die erste Q-ID zurück.
    Beispiel: 'Deutschland' -> 'Q183'
    Gibt None zurück, wenn nichts gefunden wird oder ein Fehler auftritt.
    """
    params = {
        "action": "wbsearchentities",
        "search": name,
        "language": language,
        "format": "json",
        "limit": 1,
    }

    resp = _request_get(WIKIDATA_SEARCH_URL, params=params)
    if resp is None:
        print(f"⚠️ Konnte keine Antwort von Wikidata für Suche nach '{name}' bekommen.")
        return None

    try:
        data = resp.json()
    except ValueError as e:
        print("⚠️ Konnte JSON der Wikidata-Suche nicht parsen:", e)
        print("Antwort (gekürzt):", resp.text[:300])
        return None

    if not data.get("search"):
        print(f"ℹ️ Keine Suchergebnisse in Wikidata für: {name}")
        return None

    # Erste gefundene Entität verwenden
    return data["search"][0].get("id")


def run_sparql(query: str) -> Dict[str, Any]:
    """
    Führt eine SPARQL-Query gegen den Wikidata-Endpoint aus.
    Gibt immer ein Dict zurück (zur Not ein leeres Ergebnis),
    damit der Rest des Codes nicht abstürzt.
    """
    params = {
        "query": query,
        "format": "json",
    }
    headers = {
        "Accept": "application/sparql-results+json",
    }

    resp = _request_get(WIKIDATA_SPARQL_URL, params=params, headers=headers)
    if resp is None:
        print("⚠️ SPARQL-Request fehlgeschlagen.")
        return {"results": {"bindings": []}}

    try:
        data = resp.json()
    except ValueError as e:
        print("⚠️ Konnte SPARQL-JSON nicht parsen:", e)
        print("Antwort (gekürzt):", resp.text[:300])
        return {"results": {"bindings": []}}

    return data


def get_population(qid: str) -> Optional[int]:
    """
    Holt die neueste bekannte Bevölkerungszahl (P1082) für eine Wikidata-Entität.
    Beispiel: qid='Q183' (Deutschland)
    Gibt None zurück, wenn nichts gefunden oder Fehler.
    """
    query = f"""
    SELECT ?population ?date WHERE {{
      wd:{qid} p:P1082 ?popStatement .
      ?popStatement ps:P1082 ?population .
      OPTIONAL {{ ?popStatement pq:P585 ?date }}
    }}
    ORDER BY DESC(?date)
    LIMIT 1
    """

    data = run_sparql(query)
    results = data.get("results", {}).get("bindings", [])
    if not results:
        print(f"ℹ️ Keine Populationsdaten in Wikidata für {qid} gefunden.")
        return None

    pop_value = results[0].get("population", {}).get("value")
    if pop_value is None:
        print(f"⚠️ Unerwartetes SPARQL-Ergebnis für Population von {qid}: {results[0]}")
        return None

    try:
        return int(float(pop_value))
    except (ValueError, TypeError) as e:
        print(f"⚠️ Konnte Population '{pop_value}' nicht in int konvertieren:", e)
        return None

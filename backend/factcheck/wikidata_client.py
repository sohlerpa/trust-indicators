from typing import Optional
import requests

WIKIDATA_SEARCH_URL = "https://www.wikidata.org/w/api.php"
WIKIDATA_SPARQL_URL = "https://query.wikidata.org/sparql"

# Bitte irgendwann anpassen
USER_AGENT = "TrustIndicatorsDemo/1.0 (contact@example.com)"


def search_entity(name: str, language: str = "de") -> Optional[str]:
    """
    Suche eine Entität (z. B. Deutschland) und gib die Q-ID zurück (z. B. Q183).
    """
    params = {
        "action": "wbsearchentities",
        "search": name,
        "language": language,
        "format": "json",
        "limit": 1,
    }
    response = requests.get(WIKIDATA_SEARCH_URL, params=params, timeout=10)
    response.raise_for_status()

    data = response.json()

    if not data.get("search"):
        return None

    return data["search"][0]["id"]


def run_sparql(query: str) -> dict:
    headers = {
        "Accept": "application/sparql-results+json",
        "User-Agent": USER_AGENT,
    }
    response = requests.get(
        WIKIDATA_SPARQL_URL,
        params={"query": query, "format": "json"},
        headers=headers,
        timeout=20,
    )
    response.raise_for_status()
    return response.json()


def get_population(qid: str) -> Optional[int]:
    """
    Holt die neueste bekannte Bevölkerungszahl (P1082) aus Wikidata.
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
        return None

    value = results[0]["population"]["value"]

    try:
        return int(float(value))
    except ValueError:
        return None

"""
build_sources_from_wikidata.py

Baut aus Wikidata + manuellen Ergänzungen eine Mapping-Datei:

    domain -> { source_type, org_name, org_wikidata_id, ... }

Kategorien:
- public_service  = öffentlich-rechtliche Sender in DE
- state           = staatliche Organisationen in DE (Ministerien, Behörden, Parlamente)
"""

import json
from urllib.parse import urlparse

import requests  # pip install requests


WIKIDATA_ENDPOINT = "https://query.wikidata.org/sparql"
HEADERS = {
    "User-Agent": "trust-indicators-student-project/0.1 (your-email@example.com)"
}

# 🔹 Manuelle Ergänzungen für Quellen, die in den SPARQL-Queries fehlen
MANUAL_SOURCES_DE = {
    "tagesschau.de": {
        "source_type": "public_service",
        "org_name": "Tagesschau (ARD-aktuell)",
        "org_wikidata_id": "Q157273",
        "country": "DE",
    },
    # hier kannst du später weitere ergänzen
    # "heute.de": {...}
}


def normalize_domain(url_or_host: str) -> str:
    """
    Normalisiert URL oder Host auf reine Domain:
    - entfernt Protokoll (http/https)
    - entfernt Pfad, Query, Fragment
    - entfernt führendes 'www.'
    """
    text = url_or_host.strip()

    # Falls kein Schema drin ist, eins ergänzen, damit urlparse sauber arbeitet
    if "://" not in text:
        text = "http://" + text

    parsed = urlparse(text)

    host = parsed.netloc or parsed.path  # falls jemand nur 'tagesschau.de' ohne Schema angibt

    host = host.lower()

    # Port entfernen
    if ":" in host:
        host = host.split(":", 1)[0]

    # www. entfernen
    if host.startswith("www."):
        host = host[4:]

    return host


def run_sparql(query: str) -> list[dict]:
    response = requests.get(
        WIKIDATA_ENDPOINT,
        params={"query": query, "format": "json"},
        headers=HEADERS,
        timeout=30,
    )
    response.raise_for_status()
    data = response.json()
    return data["results"]["bindings"]


def fetch_public_service_de() -> dict:
    query = """
    SELECT ?org ?orgLabel ?website WHERE {
      ?org wdt:P31 wd:Q15265344 .   # public broadcaster
      ?org wdt:P17 wd:Q183 .        # Germany
      ?org wdt:P856 ?website .      # official website
      SERVICE wikibase:label { bd:serviceParam wikibase:language "de,en". }
    }
    """
    rows = run_sparql(query)
    result: dict[str, dict] = {}
    for row in rows:
        url = row["website"]["value"]
        domain = normalize_domain(url)
        result[domain] = {
            "source_type": "public_service",
            "org_name": row["orgLabel"]["value"],
            "org_wikidata_id": row["org"]["value"].split("/")[-1],
            "country": "DE",
        }
    return result


def fetch_state_orgs_de() -> dict:
    query = """
    SELECT ?org ?orgLabel ?website ?type ?typeLabel WHERE {
      VALUES ?type {
        wd:Q327333     # government agency
        wd:Q1792450    # ministry
        wd:Q35749      # parliament
      }
      ?org wdt:P31 ?type .
      ?org wdt:P17 wd:Q183 .      # Germany
      ?org wdt:P856 ?website .
      SERVICE wikibase:label { bd:serviceParam wikibase:language "de,en". }
    }
    """
    rows = run_sparql(query)
    result: dict[str, dict] = {}
    for row in rows:
        url = row["website"]["value"]
        domain = normalize_domain(url)
        result[domain] = {
            "source_type": "state",
            "org_name": row["orgLabel"]["value"],
            "org_wikidata_id": row["org"]["value"].split("/")[-1],
            "org_type": row["typeLabel"]["value"],
            "country": "DE",
        }
    return result


def build_source_mapping_de() -> dict:
    mapping: dict[str, dict] = {}

    print("Hole öffentlich-rechtliche Sender…")
    mapping.update(fetch_public_service_de())
    print(f"{len(mapping)} Domains nach public_service-Abfrage.")

    print("Hole staatliche Organisationen…")
    state_mapping = fetch_state_orgs_de()
    mapping.update(state_mapping)
    print(f"{len(mapping)} Domains insgesamt nach state-Abfrage.")

    print("Füge manuelle Quellen hinzu…")
    mapping.update(MANUAL_SOURCES_DE)
    print(f"{len(mapping)} Domains insgesamt nach manuellen Ergänzungen.")

    return mapping


def main():
    mapping = build_source_mapping_de()
    out_path = "sources_de.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(mapping, f, ensure_ascii=False, indent=2)

    print(f"✅ Saved {len(mapping)} domains to {out_path}")


if __name__ == "__main__":
    main()

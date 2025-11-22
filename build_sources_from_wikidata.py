"""
build_sources_from_wikidata.py

Dieses Skript fragt Wikidata per SPARQL ab und baut eine Mapping-Datei:

    domain -> { source_type, org_name, org_wikidata_id, ... }

Aktuell:
- public_service  = öffentlich-rechtliche Sender in DE
- state           = staatliche Organisationen in DE (Ministerien, Behörden, Parlamente)

Ergebnis wird als 'sources_de.json' im Repo gespeichert.
"""

import json
from urllib.parse import urlparse

import requests  # Stelle sicher, dass 'requests' installiert ist


WIKIDATA_ENDPOINT = "https://query.wikidata.org/sparql"
HEADERS = {
    # Bitte mit deiner Mail / Projektbeschreibung anpassen – Wikidata mag „echte“ User-Agents
    "User-Agent": "trust-indicators-student-project/0.1 (your-email@example.com)"
}


def run_sparql(query: str) -> list[dict]:
    """SPARQL-Query an Wikidata schicken und JSON-Bindings zurückgeben."""
    response = requests.get(
        WIKIDATA_ENDPOINT,
        params={"query": query, "format": "json"},
        headers=HEADERS,
        timeout=30,
    )
    response.raise_for_status()
    data = response.json()
    return data["results"]["bindings"]


def extract_domain(url: str) -> str:
    """Aus einer URL die Domain extrahieren, z.B. https://www.tagesschau.de -> tagesschau.de"""
    parsed = urlparse(url)
    host = parsed.netloc.lower()
    if host.startswith("www."):
        host = host[4:]
    return host


def fetch_public_service_de() -> dict:
    """
    Öffentlich-rechtliche Medien in Deutschland (public broadcaster, country = Germany).
    Nutzt:
      - instance of (P31) = public broadcaster (Q15265344)
      - country (P17)      = Germany (Q183)
      - official website (P856)
    """
    query = """
    SELECT ?org ?orgLabel ?website WHERE {
      ?org wdt:P31 wd:Q15265344 .   # public broadcaster
      ?org wdt:P17 wd:Q183 .        # country = Germany
      ?org wdt:P856 ?website .      # official website
      SERVICE wikibase:label { bd:serviceParam wikibase:language "de,en". }
    }
    """
    rows = run_sparql(query)
    result = {}
    for row in rows:
        url = row["website"]["value"]
        domain = extract_domain(url)
        result[domain] = {
            "source_type": "public_service",
            "org_name": row["orgLabel"]["value"],
            "org_wikidata_id": row["org"]["value"].split("/")[-1],
            "country": "DE",
        }
    return result


def fetch_state_orgs_de() -> dict:
    """
    Staatliche Organisationen in Deutschland (Behörden, Ministerien, Parlamente).

    Typen (instance of / P31):
      - government agency (Q327333)
      - ministry (Q1792450)
      - parliament (Q35749)
    """
    query = """
    SELECT ?org ?orgLabel ?website ?type ?typeLabel WHERE {
      VALUES ?type {
        wd:Q327333     # government agency
        wd:Q1792450    # ministry
        wd:Q35749      # parliament
      }
      ?org wdt:P31 ?type .
      ?org wdt:P17 wd:Q183 .      # country = Germany
      ?org wdt:P856 ?website .    # official website
      SERVICE wikibase:label { bd:serviceParam wikibase:language "de,en". }
    }
    """
    rows = run_sparql(query)
    result = {}
    for row in rows:
        url = row["website"]["value"]
        domain = extract_domain(url)
        result[domain] = {
            "source_type": "state",
            "org_name": row["orgLabel"]["value"],
            "org_wikidata_id": row["org"]["value"].split("/")[-1],
            "org_type": row["typeLabel"]["value"],
            "country": "DE",
        }
    return result


def build_source_mapping_de() -> dict:
    """
    Kombiniert öffentlich-rechtliche + staatliche Quellen in eine Domain-Mapping-Struktur.
    """
    mapping: dict[str, dict] = {}

    print("Hole öffentlich-rechtliche Sender…")
    mapping.update(fetch_public_service_de())
    print(f"{len(mapping)} Domains nach public_service-Abfrage.")

    print("Hole staatliche Organisationen…")
    state_mapping = fetch_state_orgs_de()
    mapping.update(state_mapping)
    print(f"{len(mapping)} Domains insgesamt nach state-Abfrage.")

    return mapping


def main():
    mapping = build_source_mapping_de()

    out_path = "sources_de.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(mapping, f, ensure_ascii=False, indent=2)

    print(f"✅ Saved {len(mapping)} domains to {out_path}")


if __name__ == "__main__":
    main()


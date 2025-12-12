import re
from typing import List

def split_sentences(text: str) -> List[str]:
    """
    Einfacher Satzsplit (MVP). Für DE/EN ok als Start.
    """
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return []
    # Split bei . ! ? (naiv)
    parts = re.split(r"(?<=[.!?])\s+", text)
    return [p.strip() for p in parts if len(p.strip()) > 0]

def is_fact_like(sentence: str) -> bool:
    s = sentence.strip()
    low = s.lower()

    # Noise-Filter: typische UI-/Navigationsphrasen raus
    blacklist = [
        "interaktive", "karte", "open data", "hier stellen wir", "mehr information",
        "bitte beachten", "methoden", "dokumentation", "regionalatlas",
        "tabelle", "publikation", "jahrgänge", "finden sie", "wie funktioniert",
    ]
    if any(b in low for b in blacklist):
        return False

    # sehr kurze / fragmentierte Sätze raus
    if len(s) < 40:
        return False

    has_number = bool(re.search(r"\d", low))
    has_fact_verbs = any(x in low for x in [" ist ", " hat ", " beträgt", " entspricht", " beläuft", " liegt bei "])

    # Wir wollen lieber “harte” Fakten: Zahl + Faktwort
    return has_number and has_fact_verbs


def extract_claims(text: str, max_claims: int = 25) -> List[str]:
    """
    Extrahiert die Top-N faktverdächtigen Sätze.
    """
    sentences = split_sentences(text)
    candidates = [s for s in sentences if is_fact_like(s)]
    return candidates[:max_claims]

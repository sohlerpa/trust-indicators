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

    # harte Ausschlüsse: extrem kurz oder reine UI-Fragmente
    if len(s) < 25:
        return False

    # Wenn eine Zahl drin ist, ist es oft fakt-nah (für MVP)
    has_number = bool(re.search(r"\d", low))

    # oder klassische Fakt-Formulierungen
    has_fact_verbs = any(x in low for x in [
        " ist ", " hat ", " beträgt", " betrug ", " liegt bei ", " entspricht",
        " was ", " is ", " has ", " are "
    ])

    return has_number or has_fact_verbs



def extract_claims(text: str, max_claims: int = 25) -> List[str]:
    """
    Extrahiert die Top-N faktverdächtigen Sätze.
    """
    sentences = split_sentences(text)
    candidates = [s for s in sentences if is_fact_like(s)]
    return candidates[:max_claims]

import re
from typing import Dict, Any, Optional
from .base import FactChecker
from .wikidata_client import search_entity, get_area_km2
from .scoring import compute_numeric_score


class AreaChecker(FactChecker):
    """
    Erkennt Claims mit Fläche, z.B.:
    - "Deutschland ... Fläche von 357.588 Quadratkilometern ..."
    - "Deutschland hat eine Fläche von 357588 km²"
    """

    def supports(self, claim: str) -> bool:
        t = claim.lower()
        # sehr grob: "fläche" oder km² / quadratkilometer
        return ("fläche" in t) and (("km" in t) or ("quadratkilometer" in t) or re.search(r"\d", t))

    def check(self, claim: str) -> Dict[str, Any]:
        entity, area = self._extract_entity_and_area(claim)
        if not entity or area is None:
            return {"score": 0.0, "type": "area", "error": "Claim konnte nicht geparst werden (Entity/Zahl)."}
        
        qid = search_entity(entity, language="de")
        if not qid:
            return {"score": 0.0, "type": "area", "error": f"Keine Wikidata-Entität für: {entity}"}

        true_area = get_area_km2(qid)
        if true_area is None:
            return {"score": 0.0, "type": "area", "error": f"Keine Flächen-Daten für {qid} gefunden."}

        score = compute_numeric_score(area, true_area)

        return {
            "score": score,
            "type": "area",
            "entity": entity,
            "wikidata_id": qid,
            "claim_value": float(area),
            "true_value": float(true_area),
            "relative_error": abs(area - true_area) / true_area if true_area else None,
        }

    def _extract_entity_and_area(self, claim: str) -> tuple[Optional[str], Optional[float]]:
        text = claim.strip()

        # Entity: wir nehmen erstmal den ersten Token-Block bis "hat" oder bis Satzanfang
        # MVP: Wenn "Deutschland" im Satz steht, reicht das oft.
        # Später: NER
        entity = None
        if "Deutschland" in text:
            entity = "Deutschland"
        else:
            # fallback: nimm erstes Wort (nicht perfekt)
            entity = text.split(" ")[0].strip()

        # Area finden: z.B. "357.588 Quadratkilometern" oder "357588 km²"
        # Wir suchen die erste Zahl nach dem Wort "Fläche"
        low = text.lower()
        idx = low.find("fläche")
        slice_text = text[idx:idx+200] if idx != -1 else text

        m = re.search(r"(\d{1,3}(?:[.\s]\d{3})*(?:,\d+)?)", slice_text)
        if not m:
            return entity, None

        num_str = m.group(1).replace(" ", "").replace(".", "").replace(",", ".")
        try:
            value = float(num_str)
        except Exception:
            return entity, None

        return entity, value

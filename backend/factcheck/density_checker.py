import re
from typing import Dict, Any, Optional
from .base import FactChecker
from .wikidata_client import search_entity, get_population, get_area_km2
from .scoring import compute_numeric_score


class DensityChecker(FactChecker):
    """
    Erkennt Bevölkerungsdichte, z.B.:
    - "durchschnittlich 234 Einwohnern pro Quadratkilometer"
    - "234 Einwohner pro km²"
    """

    def supports(self, claim: str) -> bool:
        t = claim.lower()
        return ("einwohner pro" in t or "einwohnern pro" in t) and ("kilometer" in t or "km" in t)

    def check(self, claim: str) -> Dict[str, Any]:
        entity, density = self._extract_entity_and_density(claim)
        if not entity or density is None:
            return {"score": 0.0, "type": "density", "error": "Claim konnte nicht geparst werden (Entity/Zahl)."}
        
        qid = search_entity(entity, language="de")
        if not qid:
            return {"score": 0.0, "type": "density", "error": f"Keine Wikidata-Entität für: {entity}"}

        pop = get_population(qid)
        area = get_area_km2(qid)
        if pop is None or area is None or area == 0:
            return {"score": 0.0, "type": "density", "error": f"Population/Fläche fehlt für {qid}."}

        true_density = pop / area  # Einwohner pro km²
        score = compute_numeric_score(density, true_density)

        return {
            "score": score,
            "type": "density",
            "entity": entity,
            "wikidata_id": qid,
            "claim_value": float(density),
            "true_value": float(true_density),
            "population_used": int(pop),
            "area_km2_used": float(area),
        }

    def _extract_entity_and_density(self, claim: str) -> tuple[Optional[str], Optional[float]]:
        text = claim.strip()

        # Entity MVP: Deutschland hardcoded wenn vorkommt
        entity = "Deutschland" if "Deutschland" in text else text.split(" ")[0].strip()

        # Suche Zahl vor "Einwohner"
        m = re.search(r"(\d+(?:[.,]\d+)?)\s+einwohner", text.lower())
        if not m:
            return entity, None

        num_str = m.group(1).replace(",", ".")
        try:
            value = float(num_str)
        except Exception:
            return entity, None

        return entity, value

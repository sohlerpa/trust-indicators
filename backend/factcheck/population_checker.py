import re
from typing import Dict, Any, Optional
from .base import FactChecker
from .wikidata_client import search_entity, get_population
from .scoring import compute_numeric_score


class PopulationChecker(FactChecker):

    def supports(self, claim: str) -> bool:
        text = claim.lower()
        return ("einwohner" in text or "inhabitants" in text) and bool(re.search(r"\d", text))

    def check(self, claim: str) -> Dict[str, Any]:
        country, claim_pop = self._extract_country_and_population(claim)

        if not country or claim_pop is None:
            return {
                "score": 0.0,
                "type": "population",
                "error": "Claim konnte nicht geparst werden (Land oder Zahl fehlt)."
            }

        qid = search_entity(country, language="de")
        if not qid:
            return {
                "score": 0.0,
                "type": "population",
                "error": f"Keine Wikidata-Entität für: {country}"
            }

        true_pop = get_population(qid)
        if not true_pop:
            return {
                "score": 0.0,
                "type": "population",
                "error": f"Keine Populationsdaten für {qid} gefunden."
            }

        score = compute_numeric_score(claim_pop, true_pop)

        return {
            "score": score,
            "type": "population",
            "entity": country,
            "wikidata_id": qid,
            "claim_value": claim_pop,
            "true_value": true_pop,
            "relative_error": abs(claim_pop - true_pop) / true_pop,
        }

    def _extract_country_and_population(self, claim: str):
        text = claim.strip()

        country: Optional[str] = None

        if " hat " in text:
            country = text.split(" hat ")[0].strip()
        elif " has " in text:
            country = text.split(" has ")[0].strip()

        num_match = re.search(r"(\d+[.,]?\d*)", text)
        if not num_match:
            return None, None

        number_str = num_match.group(1)
        number_str = number_str.replace(".", "").replace(",", ".")

        try:
            number = float(number_str)
        except ValueError:
            return country, None

        lower = text.lower()

        multiplier = 1
        if "million" in lower:
            multiplier = 1_000_000
        elif "milliarde" in lower or "billion" in lower:
            multiplier = 1_000_000_000

        claim_pop = int(number * multiplier)

        return country, claim_pop

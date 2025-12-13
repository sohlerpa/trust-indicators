from typing import Dict, Any, List
from .base import FactChecker
from .population_checker import PopulationChecker
from .area_checker import AreaChecker
from .density_checker import DensityChecker


class FactCheckManager:
    def __init__(self):
        self.checkers: List[FactChecker] = [
            PopulationChecker(),
            AreaChecker(),
            DensityChecker(),
        ]

    def factcheck(self, claim: str) -> Dict[str, Any]:
        results = []

        for checker in self.checkers:
            if checker.supports(claim):
                res = checker.check(claim)
                res["checker"] = checker.__class__.__name__
                results.append(res)

        if not results:
            return {
                "type": "unknown",
                "score": 0.0,
                "error": "Kein passender Checker gefunden."
            }

        # Nur erfolgreiche Checks für Aggregation
        valid = [r for r in results if "error" not in r]

        # Sentence-Score = Durchschnitt der gültigen Scores
        sentence_score = (
            sum(r["score"] for r in valid) / len(valid)
            if valid else 0.0
        )

        return {
            "type": "multi",
            "score": sentence_score,
            "checks": results
        }

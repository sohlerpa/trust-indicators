from typing import Dict, Any, List
from .population_checker import PopulationChecker
from .base import FactChecker


class FactCheckManager:

    def __init__(self):
        self.checkers: List[FactChecker] = [
            PopulationChecker(),
        ]

    def factcheck(self, claim: str) -> Dict[str, Any]:
        candidates = [c for c in self.checkers if c.supports(claim)]

        if not candidates:
            return {
                "score": 0.0,
                "type": "unknown",
                "error": "Kein passender Checker gefunden."
            }

        checker = candidates[0]
        return checker.check(claim)

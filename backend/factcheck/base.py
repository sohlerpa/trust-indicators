from abc import ABC, abstractmethod
from typing import Dict, Any


class FactChecker(ABC):
    @abstractmethod
    def supports(self, claim: str) -> bool:
        """
        Gibt True zurück, wenn dieser Checker den Claim verstehen
        und prüfen kann.
        """
        pass

    @abstractmethod
    def check(self, claim: str) -> Dict[str, Any]:
        """
        Führt den Fact-Check aus und gibt strukturierte Daten zurück.
        """
        pass

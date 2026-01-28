from typing import Literal, Optional

from src.modules.fact_checking.fact_checking import FactCheckTrustDTO

Badge = Literal["green", "orange", "red", "grey"]

def compute_badge(
        has_false_facts: Optional[bool],
        author_label: Optional[str],
        c2pa_present: Optional[bool],
        publisher_type: Optional[str],
        x_mode: bool = False,
        fact_dto: FactCheckTrustDTO = None,
) -> Badge:
    # hard fail
    if has_false_facts is True:
        return "red"

    # fail is not enough data is present
    if not has_false_facts and not author_label and not c2pa_present and not x_mode:
        return "grey"

    if x_mode and not fact_dto:
        return "grey"

    score = 0

    # fact-check evidence
    if has_false_facts is False:
        score += 2

    # author expertise
    if author_label == "field_expert":
        score += 1
    elif author_label == "not_field_expert":
        score -= 1

    # c2pa: only positive signal
    if c2pa_present is True:
        score += 1

    # publisher type
    if publisher_type == "unknown":
        score -= 1

    if score >= 2:
        return "green"
    if score == 1:
        return "orange"
    return "red"
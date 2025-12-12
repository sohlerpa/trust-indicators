def compute_numeric_score(claim_value: float, true_value: float) -> float:
    """
    Berechnet einen Score zwischen 0 und 1.
    1 bedeutet: Claim stimmt exakt.
    0 bedeutet: Claim ist komplett falsch.
    """
    if true_value == 0:
        return 0.0

    rel_error = abs(claim_value - true_value) / abs(true_value)
    score = 1.0 - rel_error

    if score < 0.0:
        return 0.0
    if score > 1.0:
        return 1.0

    return score

from __future__ import annotations


def compute_coding_confidence(code_ratio: float, total_chars: int, threshold: float) -> float:
    if total_chars <= 0:
        return 0.0

    distance = abs(float(code_ratio) - float(threshold))
    distance_component = min(0.24, distance * 1.6)

    if total_chars < 120:
        evidence_component = 0.16
    elif total_chars < 800:
        evidence_component = 0.30
    elif total_chars < 4000:
        evidence_component = 0.42
    else:
        evidence_component = 0.55

    confidence = 0.26 + evidence_component + distance_component
    if confidence > 0.99:
        return 0.99
    if confidence < 0.0:
        return 0.0
    return confidence

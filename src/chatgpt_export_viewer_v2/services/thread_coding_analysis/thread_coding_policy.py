from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ThreadCodingPolicy:
    primary_threshold: float = 0.50
    min_line_len_for_symbol_detection: int = 8
    min_symbol_density: float = 0.14
    low_evidence_chars: int = 120
    medium_evidence_chars: int = 800
    high_evidence_chars: int = 4000

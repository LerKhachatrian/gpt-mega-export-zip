from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ThreadCodingSignals:
    fenced_blocks: int = 0
    inline_code_spans: int = 0
    indented_code_lines: int = 0
    command_lines: int = 0
    syntax_code_lines: int = 0
    stacktrace_lines: int = 0
    prose_lines: int = 0
    code_chars: int = 0
    non_code_chars: int = 0

    @property
    def total_chars(self) -> int:
        return int(self.code_chars + self.non_code_chars)

    @property
    def code_ratio(self) -> float:
        total = self.total_chars
        if total <= 0:
            return 0.0
        return float(self.code_chars) / float(total)


@dataclass
class ThreadCodingClassification:
    code_chars: int
    non_code_chars: int
    code_ratio: float
    confidence: float
    is_primary_coding: bool
    signal_summary: str

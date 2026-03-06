from __future__ import annotations

from .thread_coding_models import ThreadCodingSignals


def build_signal_summary(signals: ThreadCodingSignals) -> str:
    parts = [
        f"fenced={signals.fenced_blocks}",
        f"inline={signals.inline_code_spans}",
        f"indented={signals.indented_code_lines}",
        f"command={signals.command_lines}",
        f"syntax={signals.syntax_code_lines}",
        f"stacktrace={signals.stacktrace_lines}",
    ]
    return "; ".join(parts)

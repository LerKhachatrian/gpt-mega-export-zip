from __future__ import annotations

from dataclasses import dataclass

from ..domain.enums import LoadState, SortMode, ThreadTypeFilter


@dataclass
class RuntimeState:
    source_path: str = ""
    theme: str = "dark"
    number_format_mode: str = "compact"
    query: str = ""
    shared_only: bool = False
    parse_health: str = "all"
    sort_mode: SortMode = SortMode.UPDATED
    thread_type_filter: ThreadTypeFilter = ThreadTypeFilter.ALL
    coding_threshold_pct: int = 50
    min_coding_confidence_pct: int = 0
    load_state: LoadState = LoadState.IDLE

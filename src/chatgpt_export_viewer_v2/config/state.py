from __future__ import annotations

from dataclasses import dataclass

from ..domain.enums import LoadState, SortMode


@dataclass
class RuntimeState:
    source_path: str = ""
    theme: str = "dark"
    query: str = ""
    shared_only: bool = False
    parse_health: str = "all"
    sort_mode: SortMode = SortMode.UPDATED
    load_state: LoadState = LoadState.IDLE

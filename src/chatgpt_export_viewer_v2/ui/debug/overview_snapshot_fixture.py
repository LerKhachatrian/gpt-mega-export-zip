from __future__ import annotations

from PySide6.QtWidgets import QApplication

from ...config.defaults import THEME_DARK_PATH
from ...domain.models import GlobalStats


def apply_snapshot_theme(app: QApplication) -> None:
    if THEME_DARK_PATH.exists():
        app.setStyleSheet(THEME_DARK_PATH.read_text(encoding="utf-8", errors="ignore"))


def seed_overview_page(widget) -> None:
    widget.set_source("February 2026 Export Archive")

    widget.update_stats(
        GlobalStats(
            total_threads=18426,
            classification_ready_threads=17311,
            classification_pending_threads=1115,
            shared_threads=1384,
            total_messages=512903,
            total_words=13872944,
            total_tokens_o200k=18234711,
            coding_threads=6842,
            non_coding_threads=10469,
            coding_messages=218640,
            coding_words=6482140,
            coding_tokens_o200k=9421630,
            non_coding_messages=256870,
            non_coding_words=6210487,
            non_coding_tokens_o200k=7362048,
            pending_messages=37393,
            pending_words=1180317,
            pending_tokens_o200k=1451033,
            coding_share_pct=0.395,
            avg_messages=27.8,
            avg_words=752.8,
            avg_tokens_o200k=989.6,
            avg_code_ratio=0.366,
            avg_coding_messages=32.0,
            avg_coding_words=947.4,
            avg_coding_tokens_o200k=1377.1,
            avg_non_coding_messages=24.5,
            avg_non_coding_words=593.2,
            avg_non_coding_tokens_o200k=703.2,
            coding_threshold_pct=50.0,
            parse_ok=17984,
            parse_partial=442,
            health_events=327,
        )
    )

from __future__ import annotations

from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from ...domain.models import GlobalStats
from ...services.number_format_service import NUMBER_FORMAT_COMPACT, format_quantity, normalize_number_format_mode


class _MetricCard(QWidget):
    def __init__(self, title: str, hint: str = "", parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("overviewMetricCard")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(6)

        self.title_label = QLabel(title, self)
        self.title_label.setObjectName("overviewMetricTitle")

        self.value_label = QLabel("0", self)
        self.value_label.setObjectName("overviewMetricValue")

        self.hint_label = QLabel(hint, self)
        self.hint_label.setObjectName("overviewMetricHint")

        layout.addWidget(self.title_label)
        layout.addWidget(self.value_label)
        layout.addWidget(self.hint_label)
        layout.addStretch(1)

    def set_value(self, value: str) -> None:
        self.value_label.setText(value)

    def set_hint(self, hint: str) -> None:
        self.hint_label.setText(hint)


class OverviewPage(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._number_format_mode = NUMBER_FORMAT_COMPACT

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll_host = QWidget(scroll)
        scroll_host.setObjectName("overviewScrollHost")
        scroll.setWidget(scroll_host)
        root.addWidget(scroll)

        layout = QVBoxLayout(scroll_host)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(12)

        self.header_panel = QWidget(scroll_host)
        self.header_panel.setObjectName("overviewHeaderPanel")
        header_layout = QVBoxLayout(self.header_panel)
        header_layout.setContentsMargins(16, 14, 16, 14)
        header_layout.setSpacing(8)

        header_top = QHBoxLayout()
        self.title_label = QLabel("Dataset Overview", self.header_panel)
        self.title_label.setObjectName("overviewTitle")
        self.status_badge = QLabel("No data", self.header_panel)
        self.status_badge.setObjectName("overviewBadge")
        header_top.addWidget(self.title_label)
        header_top.addStretch(1)
        header_top.addWidget(self.status_badge)

        self.source_label = QLabel("Source: none", self.header_panel)
        self.source_label.setObjectName("overviewSourceLabel")

        self.note = QLabel("Load a source to start exploring.", self.header_panel)
        self.note.setObjectName("mutedLabel")

        header_layout.addLayout(header_top)
        header_layout.addWidget(self.source_label)
        header_layout.addWidget(self.note)

        layout.addWidget(self.header_panel)

        self.cards: dict[str, _MetricCard] = {}

        volume_section, volume_grid = self._build_section(
            parent=scroll_host,
            title="Core Volume",
            subtitle="Scale metrics for threads, messages, words, and tokens",
        )
        self._add_card(volume_grid, 0, 0, "Total Threads", "Thread count in current source")
        self._add_card(volume_grid, 0, 1, "Shared Threads", "Threads from shared conversations")
        self._add_card(volume_grid, 0, 2, "Total Messages", "All visible user/assistant/system messages")
        self._add_card(volume_grid, 0, 3, "Total Words", "Word count across indexed thread content")
        self._add_card(volume_grid, 1, 0, "Total Tokens (o200k)", "o200k_base token estimate across indexed messages")
        self._add_card(volume_grid, 1, 1, "Avg Messages", "Average messages per thread")
        self._add_card(volume_grid, 1, 2, "Avg Words", "Average words per thread")
        self._add_card(volume_grid, 1, 3, "Avg Tokens (o200k)", "Average o200k tokens per thread")
        layout.addWidget(volume_section)

        analysis_section, analysis_grid = self._build_section(
            parent=scroll_host,
            title="Coding Analysis",
            subtitle="Classification coverage and coding vs non-coding distribution",
        )
        self._add_card(analysis_grid, 0, 0, "Classified Threads", "Threads with completed coding analysis")
        self._add_card(analysis_grid, 0, 1, "Pending Classification", "Threads waiting for background analysis")
        self._add_card(analysis_grid, 0, 2, "Coding Threads", "Threads at or above coding threshold")
        self._add_card(analysis_grid, 0, 3, "Non-Coding Threads", "Threads below coding threshold")
        self._add_card(analysis_grid, 1, 0, "Coding Share", "Share among classified threads")
        self._add_card(analysis_grid, 1, 1, "Avg Code Ratio", "Average estimated code-content ratio")
        self._add_card(analysis_grid, 1, 2, "Healthy Threads", "Threads parsed without partial status")
        self._add_card(analysis_grid, 1, 3, "Health Events", "Warnings or errors captured during load")
        layout.addWidget(analysis_section)

        split_section, split_grid = self._build_section(
            parent=scroll_host,
            title="Coding Volume Split",
            subtitle="Classified-thread volume split by coding threshold; pending rows are tracked separately.",
        )
        self._add_card(split_grid, 0, 0, "Coding Messages", "Total messages in coding-classified threads")
        self._add_card(split_grid, 0, 1, "Coding Words", "Total words in coding-classified threads")
        self._add_card(split_grid, 0, 2, "Coding Tokens (o200k)", "Total o200k tokens in coding-classified threads")
        self._add_card(split_grid, 0, 3, "Coding Threads Volume", "Thread count contributing to coding-classified volume")

        self._add_card(split_grid, 1, 0, "Non-Coding Messages", "Total messages in non-coding-classified threads")
        self._add_card(split_grid, 1, 1, "Non-Coding Words", "Total words in non-coding-classified threads")
        self._add_card(split_grid, 1, 2, "Non-Coding Tokens (o200k)", "Total o200k tokens in non-coding-classified threads")
        self._add_card(split_grid, 1, 3, "Non-Coding Threads Volume", "Thread count contributing to non-coding volume")

        self._add_card(split_grid, 2, 0, "Avg Msg / Coding Thread", "Average messages across coding-classified threads")
        self._add_card(split_grid, 2, 1, "Avg Words / Coding Thread", "Average words across coding-classified threads")
        self._add_card(split_grid, 2, 2, "Avg Tokens / Coding Thread", "Average tokens across coding-classified threads")
        self._add_card(split_grid, 2, 3, "Avg Msg / Non-Coding Thread", "Average messages across non-coding-classified threads")

        self._add_card(split_grid, 3, 0, "Avg Words / Non-Coding Thread", "Average words across non-coding-classified threads")
        self._add_card(split_grid, 3, 1, "Avg Tokens / Non-Coding Thread", "Average tokens across non-coding-classified threads")
        self._add_card(split_grid, 3, 2, "Pending Tokens (o200k)", "Token volume in threads still pending classification")
        self._add_card(split_grid, 3, 3, "Pending Threads Volume", "Threads still pending coding/non-coding split")
        layout.addWidget(split_section)

        progress_section, progress_grid = self._build_section(
            parent=scroll_host,
            title="Progress Snapshot",
            subtitle="Live processing health and coverage indicators",
        )

        self.classification_progress_label = QLabel("Classification Coverage", progress_section)
        self.classification_progress_label.setObjectName("overviewProgressLabel")
        self.classification_progress = QProgressBar(progress_section)
        self.classification_progress.setObjectName("overviewProgressBar")
        self.classification_progress.setRange(0, 100)

        self.coding_progress_label = QLabel("Coding Share", progress_section)
        self.coding_progress_label.setObjectName("overviewProgressLabel")
        self.coding_progress = QProgressBar(progress_section)
        self.coding_progress.setObjectName("overviewProgressBar")
        self.coding_progress.setRange(0, 100)

        self.parse_health_progress_label = QLabel("Parse Health", progress_section)
        self.parse_health_progress_label.setObjectName("overviewProgressLabel")
        self.parse_health_progress = QProgressBar(progress_section)
        self.parse_health_progress.setObjectName("overviewProgressBar")
        self.parse_health_progress.setRange(0, 100)

        progress_grid.addWidget(self.classification_progress_label, 0, 0)
        progress_grid.addWidget(self.classification_progress, 0, 1)
        progress_grid.addWidget(self.coding_progress_label, 1, 0)
        progress_grid.addWidget(self.coding_progress, 1, 1)
        progress_grid.addWidget(self.parse_health_progress_label, 2, 0)
        progress_grid.addWidget(self.parse_health_progress, 2, 1)
        layout.addWidget(progress_section)

        layout.addStretch(1)

    def _build_section(self, parent: QWidget, title: str, subtitle: str) -> tuple[QWidget, QGridLayout]:
        section = QWidget(parent)
        section.setObjectName("overviewSection")
        section_layout = QVBoxLayout(section)
        section_layout.setContentsMargins(14, 14, 14, 14)
        section_layout.setSpacing(10)

        title_label = QLabel(title, section)
        title_label.setObjectName("overviewSectionTitle")
        subtitle_label = QLabel(subtitle, section)
        subtitle_label.setObjectName("overviewSectionSubtitle")

        grid = QGridLayout()
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(10)

        section_layout.addWidget(title_label)
        section_layout.addWidget(subtitle_label)
        section_layout.addLayout(grid)
        return section, grid

    def _add_card(self, grid: QGridLayout, row: int, col: int, key: str, hint: str) -> None:
        card = _MetricCard(title=key, hint=hint, parent=self)
        grid.addWidget(card, row, col)
        self.cards[key] = card

    def set_source(self, source: str) -> None:
        self.source_label.setText(f"Source: {source}")

    def set_loading(self) -> None:
        self.status_badge.setText("Loading")
        self.note.setText("Building index and background analysis...")
        self.classification_progress.setValue(0)
        self.coding_progress.setValue(0)
        self.parse_health_progress.setValue(0)

    def set_number_format_mode(self, mode: str) -> None:
        self._number_format_mode = normalize_number_format_mode(mode)

    def update_stats(self, stats: GlobalStats) -> None:
        mode = self._number_format_mode

        self.cards["Total Threads"].set_value(format_quantity(stats.total_threads, mode=mode))
        self.cards["Shared Threads"].set_value(format_quantity(stats.shared_threads, mode=mode))
        self.cards["Total Messages"].set_value(format_quantity(stats.total_messages, mode=mode))
        self.cards["Total Words"].set_value(format_quantity(stats.total_words, mode=mode))
        self.cards["Total Tokens (o200k)"].set_value(format_quantity(stats.total_tokens_o200k, mode=mode))
        self.cards["Avg Messages"].set_value(format_quantity(stats.avg_messages, mode=mode, decimals=1))
        self.cards["Avg Words"].set_value(format_quantity(stats.avg_words, mode=mode, decimals=1))
        self.cards["Avg Tokens (o200k)"].set_value(format_quantity(stats.avg_tokens_o200k, mode=mode, decimals=1))

        self.cards["Classified Threads"].set_value(format_quantity(stats.classification_ready_threads, mode=mode))
        self.cards["Pending Classification"].set_value(format_quantity(stats.classification_pending_threads, mode=mode))
        self.cards["Coding Threads"].set_value(format_quantity(stats.coding_threads, mode=mode))
        self.cards["Non-Coding Threads"].set_value(format_quantity(stats.non_coding_threads, mode=mode))
        self.cards["Coding Share"].set_value(f"{stats.coding_share_pct * 100:,.1f}%")
        self.cards["Avg Code Ratio"].set_value(f"{stats.avg_code_ratio * 100:,.1f}%")
        self.cards["Healthy Threads"].set_value(format_quantity(stats.parse_ok, mode=mode))
        self.cards["Health Events"].set_value(format_quantity(stats.health_events, mode=mode))

        self.cards["Coding Messages"].set_value(format_quantity(stats.coding_messages, mode=mode))
        self.cards["Coding Words"].set_value(format_quantity(stats.coding_words, mode=mode))
        self.cards["Coding Tokens (o200k)"].set_value(format_quantity(stats.coding_tokens_o200k, mode=mode))
        self.cards["Coding Threads Volume"].set_value(format_quantity(stats.coding_threads, mode=mode))

        self.cards["Non-Coding Messages"].set_value(format_quantity(stats.non_coding_messages, mode=mode))
        self.cards["Non-Coding Words"].set_value(format_quantity(stats.non_coding_words, mode=mode))
        self.cards["Non-Coding Tokens (o200k)"].set_value(format_quantity(stats.non_coding_tokens_o200k, mode=mode))
        self.cards["Non-Coding Threads Volume"].set_value(format_quantity(stats.non_coding_threads, mode=mode))

        self.cards["Avg Msg / Coding Thread"].set_value(format_quantity(stats.avg_coding_messages, mode=mode, decimals=1))
        self.cards["Avg Words / Coding Thread"].set_value(format_quantity(stats.avg_coding_words, mode=mode, decimals=1))
        self.cards["Avg Tokens / Coding Thread"].set_value(
            format_quantity(stats.avg_coding_tokens_o200k, mode=mode, decimals=1)
        )
        self.cards["Avg Msg / Non-Coding Thread"].set_value(
            format_quantity(stats.avg_non_coding_messages, mode=mode, decimals=1)
        )
        self.cards["Avg Words / Non-Coding Thread"].set_value(
            format_quantity(stats.avg_non_coding_words, mode=mode, decimals=1)
        )
        self.cards["Avg Tokens / Non-Coding Thread"].set_value(
            format_quantity(stats.avg_non_coding_tokens_o200k, mode=mode, decimals=1)
        )
        self.cards["Pending Tokens (o200k)"].set_value(format_quantity(stats.pending_tokens_o200k, mode=mode))
        self.cards["Pending Threads Volume"].set_value(format_quantity(stats.classification_pending_threads, mode=mode))

        pending = stats.classification_pending_threads
        total = stats.total_threads
        if total <= 0:
            self.status_badge.setText("No data")
        elif pending > 0:
            self.status_badge.setText(
                f"Analyzing {format_quantity(pending, mode=mode)} pending"
            )
        else:
            self.status_badge.setText("Analysis complete")

        self.cards["Pending Classification"].set_hint(
            "Background analysis still running" if pending > 0 else "All threads analyzed"
        )
        self.cards["Pending Tokens (o200k)"].set_hint(
            "Unclassified token volume still pending analysis" if pending > 0 else "No unclassified token volume"
        )
        self.cards["Pending Threads Volume"].set_hint(
            "Threads still awaiting coding split" if pending > 0 else "No pending threads"
        )

        classified_pct = int(round((stats.classification_ready_threads / total) * 100)) if total else 0
        coding_pct = int(round(stats.coding_share_pct * 100))
        parse_ok_pct = int(round((stats.parse_ok / total) * 100)) if total else 0

        self.classification_progress_label.setText(f"Classification Coverage  {classified_pct}%")
        self.classification_progress.setValue(classified_pct)
        self.coding_progress_label.setText(f"Coding Share  {coding_pct}%")
        self.coding_progress.setValue(coding_pct)
        self.parse_health_progress_label.setText(f"Parse Health  {parse_ok_pct}%")
        self.parse_health_progress.setValue(parse_ok_pct)

        self.note.setText(
            f"Classified {format_quantity(stats.classification_ready_threads, mode=mode)}/"
            f"{format_quantity(total, mode=mode)} threads. "
            f"Coding threshold: {stats.coding_threshold_pct:.0f}%. "
            f"Coding tokens: {format_quantity(stats.coding_tokens_o200k, mode=mode)} | "
            f"Non-coding tokens: {format_quantity(stats.non_coding_tokens_o200k, mode=mode)}."
        )

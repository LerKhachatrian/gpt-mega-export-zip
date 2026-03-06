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
    def __init__(self, title: str, hint: str = "", variant: str = "secondary", parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("overviewMetricCard")
        self.setProperty("variant", variant)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(6)

        self.title_label = QLabel(title, self)
        self.title_label.setObjectName("overviewMetricTitle")

        self.value_label = QLabel("0", self)
        self.value_label.setObjectName("overviewMetricValue")

        self.hint_label = QLabel(hint, self)
        self.hint_label.setObjectName("overviewMetricHint")
        self.hint_label.setWordWrap(True)

        layout.addWidget(self.title_label)
        layout.addWidget(self.value_label)
        layout.addWidget(self.hint_label)
        layout.addStretch(1)

    def set_value(self, value: str) -> None:
        self.value_label.setText(value)

    def set_hint(self, hint: str) -> None:
        self.hint_label.setText(hint)


class _ResponsiveCardGrid(QWidget):
    def __init__(self, min_item_width: int, max_columns: int, parent=None) -> None:
        super().__init__(parent)
        self._min_item_width = min_item_width
        self._max_columns = max(1, max_columns)
        self._current_columns = 0
        self._cards: list[QWidget] = []

        self._layout = QGridLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setHorizontalSpacing(12)
        self._layout.setVerticalSpacing(12)

    def add_card(self, card: QWidget) -> None:
        self._cards.append(card)
        self._relayout(force=True)

    def resizeEvent(self, event) -> None:  # pragma: no cover
        super().resizeEvent(event)
        self._relayout()

    def _relayout(self, force: bool = False) -> None:
        if not self._cards:
            return

        margins = self._layout.contentsMargins()
        spacing = max(0, self._layout.horizontalSpacing())
        available_width = max(1, self.width() - margins.left() - margins.right())
        columns = max(1, min(self._max_columns, (available_width + spacing) // (self._min_item_width + spacing)))
        if not force and columns == self._current_columns:
            return

        self._current_columns = columns

        while self._layout.count():
            item = self._layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(self)

        for index, card in enumerate(self._cards):
            row = index // columns
            col = index % columns
            self._layout.addWidget(card, row, col)

        for col in range(self._max_columns):
            self._layout.setColumnStretch(col, 0)
        for col in range(columns):
            self._layout.setColumnStretch(col, 1)


class _ProgressCard(QWidget):
    def __init__(self, title: str, hint: str, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("overviewProgressCard")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(8)

        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        header.setSpacing(8)

        self.title_label = QLabel(title, self)
        self.title_label.setObjectName("overviewProgressTitle")

        self.percent_label = QLabel("0%", self)
        self.percent_label.setObjectName("overviewProgressPercent")

        header.addWidget(self.title_label)
        header.addStretch(1)
        header.addWidget(self.percent_label)

        self.progress = QProgressBar(self)
        self.progress.setObjectName("overviewProgressBar")
        self.progress.setRange(0, 100)
        self.progress.setTextVisible(False)

        self.hint_label = QLabel(hint, self)
        self.hint_label.setObjectName("overviewProgressHint")
        self.hint_label.setWordWrap(True)

        layout.addLayout(header)
        layout.addWidget(self.progress)
        layout.addWidget(self.hint_label)

    def set_progress(self, value: int, hint: str | None = None) -> None:
        value = max(0, min(100, int(value)))
        self.percent_label.setText(f"{value}%")
        self.progress.setValue(value)
        if hint is not None:
            self.hint_label.setText(hint)


class _StatRow(QWidget):
    def __init__(self, label: str, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("overviewStatRow")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        self.label = QLabel(label, self)
        self.label.setObjectName("overviewStatRowLabel")

        self.value = QLabel("0", self)
        self.value.setObjectName("overviewStatRowValue")

        layout.addWidget(self.label, 1)
        layout.addWidget(self.value, 0)

    def set_value(self, value: str) -> None:
        self.value.setText(value)


class _StatGroupCard(QWidget):
    def __init__(self, title: str, subtitle: str, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("overviewGroupCard")
        self.rows: dict[str, _StatRow] = {}

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(10)

        self.title_label = QLabel(title, self)
        self.title_label.setObjectName("overviewGroupTitle")

        self.subtitle_label = QLabel(subtitle, self)
        self.subtitle_label.setObjectName("overviewGroupSubtitle")
        self.subtitle_label.setWordWrap(True)

        self.rows_host = QVBoxLayout()
        self.rows_host.setContentsMargins(0, 6, 0, 0)
        self.rows_host.setSpacing(8)

        layout.addWidget(self.title_label)
        layout.addWidget(self.subtitle_label)
        layout.addLayout(self.rows_host)
        layout.addStretch(1)

    def add_row(self, key: str, label: str) -> None:
        row = _StatRow(label, self)
        self.rows[key] = row
        self.rows_host.addWidget(row)

    def set_value(self, key: str, value: str) -> None:
        self.rows[key].set_value(value)


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
        layout.setContentsMargins(16, 16, 16, 20)
        layout.setSpacing(14)

        self.header_panel = QWidget(scroll_host)
        self.header_panel.setObjectName("overviewHeaderPanel")
        header_layout = QVBoxLayout(self.header_panel)
        header_layout.setContentsMargins(18, 16, 18, 16)
        header_layout.setSpacing(8)

        header_top = QHBoxLayout()
        header_top.setContentsMargins(0, 0, 0, 0)
        header_top.setSpacing(10)

        self.title_label = QLabel("Dataset Overview", self.header_panel)
        self.title_label.setObjectName("overviewTitle")

        self.status_badge = QLabel("No data", self.header_panel)
        self.status_badge.setObjectName("overviewBadge")

        header_top.addWidget(self.title_label)
        header_top.addStretch(1)
        header_top.addWidget(self.status_badge)

        self.source_label = QLabel("Source: none", self.header_panel)
        self.source_label.setObjectName("overviewSourceLabel")
        self.source_label.setWordWrap(True)

        self.note = QLabel("Point the app at a ChatGPT export folder or zip to build a readable dataset summary.", self.header_panel)
        self.note.setObjectName("overviewLead")
        self.note.setWordWrap(True)

        header_layout.addLayout(header_top)
        header_layout.addWidget(self.source_label)
        header_layout.addWidget(self.note)
        layout.addWidget(self.header_panel)

        self.empty_state = QWidget(scroll_host)
        self.empty_state.setObjectName("overviewEmptyState")
        empty_layout = QVBoxLayout(self.empty_state)
        empty_layout.setContentsMargins(18, 18, 18, 18)
        empty_layout.setSpacing(10)

        self.empty_title = QLabel("Nothing is loaded yet", self.empty_state)
        self.empty_title.setObjectName("overviewEmptyTitle")
        self.empty_copy = QLabel(
            "Choose an export source, let the cache build once, then use this page to scan dataset size, coding mix, and parse health before diving into threads.",
            self.empty_state,
        )
        self.empty_copy.setObjectName("overviewEmptyCopy")
        self.empty_copy.setWordWrap(True)

        self.empty_steps = QLabel(
            "1. Select an export folder or zip.\n"
            "2. Load it once to build cache and analysis coverage.\n"
            "3. Return here for the top-line picture before filtering threads.",
            self.empty_state,
        )
        self.empty_steps.setObjectName("overviewEmptySteps")
        self.empty_steps.setWordWrap(True)

        empty_layout.addWidget(self.empty_title)
        empty_layout.addWidget(self.empty_copy)
        empty_layout.addWidget(self.empty_steps)
        layout.addWidget(self.empty_state)

        self.summary_section = self._build_section(
            parent=scroll_host,
            title="At a Glance",
            subtitle="The four numbers you usually need first before drilling into thread details.",
        )
        self.summary_grid = _ResponsiveCardGrid(min_item_width=220, max_columns=4, parent=self.summary_section)
        self.summary_cards: dict[str, _MetricCard] = {}
        self._add_summary_card("Threads", "Indexed conversation threads", "primary")
        self._add_summary_card("Messages", "Messages across the current source", "primary")
        self._add_summary_card("Words", "Visible text volume", "primary")
        self._add_summary_card("Tokens (o200k)", "Estimated token footprint", "primary")
        self.summary_section.layout().addWidget(self.summary_grid)
        layout.addWidget(self.summary_section)

        self.signals_section = self._build_section(
            parent=scroll_host,
            title="Processing Signals",
            subtitle="Coverage, coding mix, and health indicators kept separate from the raw volume numbers.",
        )
        self.progress_grid = _ResponsiveCardGrid(min_item_width=250, max_columns=3, parent=self.signals_section)
        self.progress_cards: dict[str, _ProgressCard] = {}
        self._add_progress_card("Classification Coverage", "How much of the dataset has finished coding analysis.")
        self._add_progress_card("Coding Share", "Share of classified threads that clear the coding threshold.")
        self._add_progress_card("Parse Health", "Threads parsed cleanly without landing in a partial state.")
        self.signals_section.layout().addWidget(self.progress_grid)

        self.signal_cards_grid = _ResponsiveCardGrid(min_item_width=220, max_columns=3, parent=self.signals_section)
        self.signal_cards: dict[str, _MetricCard] = {}
        self._add_signal_card("Classified", "Threads with completed coding analysis")
        self._add_signal_card("Pending", "Threads still waiting on background analysis")
        self._add_signal_card("Coding", "Threads at or above the coding threshold")
        self._add_signal_card("Non-Coding", "Threads below the coding threshold")
        self._add_signal_card("Shared", "Threads sourced from shared conversations")
        self._add_signal_card("Health Events", "Warnings and errors captured during load")
        self.signals_section.layout().addWidget(self.signal_cards_grid)
        layout.addWidget(self.signals_section)

        self.breakdown_section = self._build_section(
            parent=scroll_host,
            title="Breakdowns",
            subtitle="Grouped volume cards keep the detailed split visible without turning the page into a wall of identical KPI tiles.",
        )
        self.breakdown_grid = _ResponsiveCardGrid(min_item_width=320, max_columns=3, parent=self.breakdown_section)

        self.coding_group = _StatGroupCard(
            "Coding footprint",
            "Volume and per-thread averages for threads classified as coding-heavy.",
            self.breakdown_section,
        )
        self._add_group_rows(
            self.coding_group,
            [
                ("threads", "Threads"),
                ("messages", "Messages"),
                ("words", "Words"),
                ("tokens", "Tokens (o200k)"),
                ("avg_messages", "Avg Messages / Thread"),
                ("avg_words", "Avg Words / Thread"),
                ("avg_tokens", "Avg Tokens / Thread"),
            ],
        )
        self.breakdown_grid.add_card(self.coding_group)

        self.non_coding_group = _StatGroupCard(
            "Non-coding footprint",
            "The same split for advisory, planning, and non-code-heavy conversations.",
            self.breakdown_section,
        )
        self._add_group_rows(
            self.non_coding_group,
            [
                ("threads", "Threads"),
                ("messages", "Messages"),
                ("words", "Words"),
                ("tokens", "Tokens (o200k)"),
                ("avg_messages", "Avg Messages / Thread"),
                ("avg_words", "Avg Words / Thread"),
                ("avg_tokens", "Avg Tokens / Thread"),
            ],
        )
        self.breakdown_grid.add_card(self.non_coding_group)

        self.processing_group = _StatGroupCard(
            "Pipeline details",
            "Secondary counters that explain what is still pending and how clean the dataset import was.",
            self.breakdown_section,
        )
        self._add_group_rows(
            self.processing_group,
            [
                ("ready_threads", "Classification Ready"),
                ("pending_threads", "Pending Threads"),
                ("pending_tokens", "Pending Tokens (o200k)"),
                ("parse_ok", "Healthy Threads"),
                ("parse_partial", "Partial Threads"),
                ("shared_threads", "Shared Threads"),
                ("avg_code_ratio", "Avg Code Ratio"),
                ("health_events", "Health Events"),
            ],
        )
        self.breakdown_grid.add_card(self.processing_group)

        self.breakdown_section.layout().addWidget(self.breakdown_grid)
        layout.addWidget(self.breakdown_section)
        layout.addStretch(1)

        self._content_sections = [self.summary_section, self.signals_section, self.breakdown_section]
        self._set_content_visibility(has_data=False, loading=False)

    def _build_section(self, parent: QWidget, title: str, subtitle: str) -> QWidget:
        section = QWidget(parent)
        section.setObjectName("overviewSection")
        section_layout = QVBoxLayout(section)
        section_layout.setContentsMargins(16, 16, 16, 16)
        section_layout.setSpacing(12)

        title_label = QLabel(title, section)
        title_label.setObjectName("overviewSectionTitle")
        subtitle_label = QLabel(subtitle, section)
        subtitle_label.setObjectName("overviewSectionSubtitle")
        subtitle_label.setWordWrap(True)

        section_layout.addWidget(title_label)
        section_layout.addWidget(subtitle_label)
        return section

    def _add_summary_card(self, key: str, hint: str, variant: str) -> None:
        card = _MetricCard(title=key, hint=hint, variant=variant, parent=self.summary_grid)
        self.summary_cards[key] = card
        self.summary_grid.add_card(card)

    def _add_signal_card(self, key: str, hint: str) -> None:
        card = _MetricCard(title=key, hint=hint, variant="secondary", parent=self.signal_cards_grid)
        self.signal_cards[key] = card
        self.signal_cards_grid.add_card(card)

    def _add_progress_card(self, key: str, hint: str) -> None:
        card = _ProgressCard(title=key, hint=hint, parent=self.progress_grid)
        self.progress_cards[key] = card
        self.progress_grid.add_card(card)

    def _add_group_rows(self, group: _StatGroupCard, rows: list[tuple[str, str]]) -> None:
        for key, label in rows:
            group.add_row(key, label)

    def _set_content_visibility(self, has_data: bool, loading: bool) -> None:
        show_sections = has_data or loading
        self.empty_state.setVisible(not show_sections)
        for section in self._content_sections:
            section.setVisible(show_sections)

    def set_source(self, source: str) -> None:
        self.source_label.setText(f"Source: {source or 'none'}")

    def set_loading(self) -> None:
        self.status_badge.setText("Loading")
        self.note.setText("Scanning the source, building cache, and queuing coding analysis.")
        self.progress_cards["Classification Coverage"].set_progress(0)
        self.progress_cards["Coding Share"].set_progress(0)
        self.progress_cards["Parse Health"].set_progress(0)
        self._set_content_visibility(has_data=False, loading=True)

    def set_number_format_mode(self, mode: str) -> None:
        self._number_format_mode = normalize_number_format_mode(mode)

    def update_stats(self, stats: GlobalStats) -> None:
        mode = self._number_format_mode
        total = max(0, int(stats.total_threads))
        pending = max(0, int(stats.classification_pending_threads))

        if total <= 0:
            self.status_badge.setText("No data")
            self.note.setText("Point the app at a ChatGPT export folder or zip to build a readable dataset summary.")
            self._set_content_visibility(has_data=False, loading=False)
            return

        self._set_content_visibility(has_data=True, loading=False)

        if pending > 0:
            self.status_badge.setText(f"Analyzing {format_quantity(pending, mode=mode)} pending")
        else:
            self.status_badge.setText("Analysis complete")

        ready_threads = format_quantity(stats.classification_ready_threads, mode=mode)
        total_threads = format_quantity(total, mode=mode)
        coding_threads = format_quantity(stats.coding_threads, mode=mode)
        non_coding_threads = format_quantity(stats.non_coding_threads, mode=mode)
        health_events = format_quantity(stats.health_events, mode=mode)
        shared_threads = format_quantity(stats.shared_threads, mode=mode)

        coding_pct = int(round(stats.coding_share_pct * 100))
        classified_pct = int(round((stats.classification_ready_threads / total) * 100)) if total else 0
        parse_ok_pct = int(round((stats.parse_ok / total) * 100)) if total else 0

        self.note.setText(
            f"{ready_threads}/{total_threads} threads classified at a {stats.coding_threshold_pct:.0f}% coding threshold. "
            f"{coding_threads} coding, {non_coding_threads} non-coding, {shared_threads} shared, {health_events} health events."
        )

        self.summary_cards["Threads"].set_value(total_threads)
        self.summary_cards["Messages"].set_value(format_quantity(stats.total_messages, mode=mode))
        self.summary_cards["Words"].set_value(format_quantity(stats.total_words, mode=mode))
        self.summary_cards["Tokens (o200k)"].set_value(format_quantity(stats.total_tokens_o200k, mode=mode))

        pending_hint = "Background analysis still running" if pending > 0 else "Analysis queue is clear"
        self.signal_cards["Classified"].set_value(ready_threads)
        self.signal_cards["Pending"].set_value(format_quantity(stats.classification_pending_threads, mode=mode))
        self.signal_cards["Pending"].set_hint(pending_hint)
        self.signal_cards["Coding"].set_value(coding_threads)
        self.signal_cards["Non-Coding"].set_value(non_coding_threads)
        self.signal_cards["Shared"].set_value(shared_threads)
        self.signal_cards["Health Events"].set_value(health_events)
        self.signal_cards["Health Events"].set_hint(
            "Warnings and errors recorded during import" if stats.health_events else "No health events recorded"
        )

        self.progress_cards["Classification Coverage"].set_progress(
            classified_pct,
            hint=f"{ready_threads} of {total_threads} threads have completed coding analysis.",
        )
        self.progress_cards["Coding Share"].set_progress(
            coding_pct,
            hint=f"{coding_threads} coding threads out of the classified pool.",
        )
        self.progress_cards["Parse Health"].set_progress(
            parse_ok_pct,
            hint=f"{format_quantity(stats.parse_ok, mode=mode)} healthy vs {format_quantity(stats.parse_partial, mode=mode)} partial threads.",
        )

        self.coding_group.set_value("threads", format_quantity(stats.coding_threads, mode=mode))
        self.coding_group.set_value("messages", format_quantity(stats.coding_messages, mode=mode))
        self.coding_group.set_value("words", format_quantity(stats.coding_words, mode=mode))
        self.coding_group.set_value("tokens", format_quantity(stats.coding_tokens_o200k, mode=mode))
        self.coding_group.set_value("avg_messages", format_quantity(stats.avg_coding_messages, mode=mode, decimals=1))
        self.coding_group.set_value("avg_words", format_quantity(stats.avg_coding_words, mode=mode, decimals=1))
        self.coding_group.set_value("avg_tokens", format_quantity(stats.avg_coding_tokens_o200k, mode=mode, decimals=1))

        self.non_coding_group.set_value("threads", format_quantity(stats.non_coding_threads, mode=mode))
        self.non_coding_group.set_value("messages", format_quantity(stats.non_coding_messages, mode=mode))
        self.non_coding_group.set_value("words", format_quantity(stats.non_coding_words, mode=mode))
        self.non_coding_group.set_value("tokens", format_quantity(stats.non_coding_tokens_o200k, mode=mode))
        self.non_coding_group.set_value("avg_messages", format_quantity(stats.avg_non_coding_messages, mode=mode, decimals=1))
        self.non_coding_group.set_value("avg_words", format_quantity(stats.avg_non_coding_words, mode=mode, decimals=1))
        self.non_coding_group.set_value(
            "avg_tokens",
            format_quantity(stats.avg_non_coding_tokens_o200k, mode=mode, decimals=1),
        )

        self.processing_group.set_value("ready_threads", ready_threads)
        self.processing_group.set_value("pending_threads", format_quantity(stats.classification_pending_threads, mode=mode))
        self.processing_group.set_value("pending_tokens", format_quantity(stats.pending_tokens_o200k, mode=mode))
        self.processing_group.set_value("parse_ok", format_quantity(stats.parse_ok, mode=mode))
        self.processing_group.set_value("parse_partial", format_quantity(stats.parse_partial, mode=mode))
        self.processing_group.set_value("shared_threads", shared_threads)
        self.processing_group.set_value("avg_code_ratio", f"{stats.avg_code_ratio * 100:,.1f}%")
        self.processing_group.set_value("health_events", health_events)

from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QGridLayout,
    QHeaderView,
    QHBoxLayout,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ...domain.models import GlobalStats, ThreadSummary
from ...services.number_format_service import NUMBER_FORMAT_COMPACT, format_quantity, normalize_number_format_mode


class _StatsMetricCard(QWidget):
    def __init__(self, title: str, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("statsMetricCard")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(4)

        self.title_label = QLabel(title, self)
        self.title_label.setObjectName("statsMetricTitle")

        self.value_label = QLabel("0", self)
        self.value_label.setObjectName("statsMetricValue")

        layout.addWidget(self.title_label)
        layout.addWidget(self.value_label)
        layout.addStretch(1)

    def set_value(self, value: str) -> None:
        self.value_label.setText(value)


class StatsPage(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._number_format_mode = NUMBER_FORMAT_COMPACT

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(12)

        self.header_panel = QWidget(self)
        self.header_panel.setObjectName("statsHeaderPanel")
        header_layout = QVBoxLayout(self.header_panel)
        header_layout.setContentsMargins(16, 14, 16, 14)
        header_layout.setSpacing(8)

        header_top = QHBoxLayout()
        self.title_label = QLabel("Thread Stats", self.header_panel)
        self.title_label.setObjectName("statsTitle")
        self.status_badge = QLabel("No data", self.header_panel)
        self.status_badge.setObjectName("statsBadge")
        header_top.addWidget(self.title_label)
        header_top.addStretch(1)
        header_top.addWidget(self.status_badge)

        self.subtitle_label = QLabel(
            "Top threads by message volume with coding and token context.",
            self.header_panel,
        )
        self.subtitle_label.setObjectName("statsSubtitle")
        self.subtitle_label.setWordWrap(True)

        header_layout.addLayout(header_top)
        header_layout.addWidget(self.subtitle_label)
        layout.addWidget(self.header_panel)

        summary_section = QWidget(self)
        summary_section.setObjectName("statsSummarySection")
        summary_layout = QVBoxLayout(summary_section)
        summary_layout.setContentsMargins(14, 14, 14, 14)
        summary_layout.setSpacing(10)

        summary_title = QLabel("Dataset Summary", summary_section)
        summary_title.setObjectName("statsSectionTitle")
        self.summary_note = QLabel("No data loaded yet.", summary_section)
        self.summary_note.setObjectName("statsSectionSubtitle")
        self.summary_note.setWordWrap(True)

        summary_grid = QGridLayout()
        summary_grid.setHorizontalSpacing(10)
        summary_grid.setVerticalSpacing(10)

        self.cards: dict[str, _StatsMetricCard] = {}
        self._add_card(summary_grid, 0, 0, "Threads")
        self._add_card(summary_grid, 0, 1, "Shared")
        self._add_card(summary_grid, 0, 2, "Messages")
        self._add_card(summary_grid, 1, 0, "Words")
        self._add_card(summary_grid, 1, 1, "Tokens (o200k)")
        self._add_card(summary_grid, 1, 2, "Coding Share")

        summary_layout.addWidget(summary_title)
        summary_layout.addWidget(self.summary_note)
        summary_layout.addLayout(summary_grid)
        layout.addWidget(summary_section)

        table_section = QWidget(self)
        table_section.setObjectName("statsTableSection")
        table_section_layout = QVBoxLayout(table_section)
        table_section_layout.setContentsMargins(14, 14, 14, 14)
        table_section_layout.setSpacing(10)

        table_title = QLabel("Top Threads", table_section)
        table_title.setObjectName("statsSectionTitle")
        self.table_summary = QLabel("No rows", table_section)
        self.table_summary.setObjectName("statsSectionSubtitle")
        self.table_summary.setWordWrap(True)

        self.table = QTableWidget(self)
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(
            ["Thread", "Messages", "Words", "Tokens (o200k)", "Code Ratio", "Confidence", "Updated"]
        )
        self.table.setObjectName("statsTable")
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setShowGrid(False)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(28)
        self.table.horizontalHeader().setStretchLastSection(False)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)

        table_section_layout.addWidget(table_title)
        table_section_layout.addWidget(self.table_summary)
        table_section_layout.addWidget(self.table, 1)

        layout.addWidget(table_section, 1)

    def _add_card(self, grid: QGridLayout, row: int, col: int, key: str) -> None:
        card = _StatsMetricCard(key, self)
        grid.addWidget(card, row, col)
        self.cards[key] = card

    def set_loading(self) -> None:
        self.status_badge.setText("Loading")
        self.summary_note.setText("Computing aggregate metrics...")
        self.table_summary.setText("Building top-thread leaderboard...")
        self.table.setRowCount(0)

    def set_number_format_mode(self, mode: str) -> None:
        self._number_format_mode = normalize_number_format_mode(mode)

    def update_stats(self, stats: GlobalStats, top_threads: list[ThreadSummary]) -> None:
        mode = self._number_format_mode

        total_threads = max(0, int(stats.total_threads))
        pending = max(0, int(stats.classification_pending_threads))

        if total_threads <= 0:
            self.status_badge.setText("No data")
        elif pending > 0:
            self.status_badge.setText(f"Analyzing {format_quantity(pending, mode=mode)} pending")
        else:
            self.status_badge.setText("Analysis complete")

        self.cards["Threads"].set_value(format_quantity(stats.total_threads, mode=mode))
        self.cards["Shared"].set_value(format_quantity(stats.shared_threads, mode=mode))
        self.cards["Messages"].set_value(format_quantity(stats.total_messages, mode=mode))
        self.cards["Words"].set_value(format_quantity(stats.total_words, mode=mode))
        self.cards["Tokens (o200k)"].set_value(format_quantity(stats.total_tokens_o200k, mode=mode))
        self.cards["Coding Share"].set_value(f"{stats.coding_share_pct * 100:.1f}%")

        self.summary_note.setText(
            f"Classified {format_quantity(stats.classification_ready_threads, mode=mode)}/"
            f"{format_quantity(total_threads, mode=mode)} threads @ {stats.coding_threshold_pct:.0f}% threshold. "
            f"Coding volume: {format_quantity(stats.coding_threads, mode=mode)} threads | "
            f"{format_quantity(stats.coding_messages, mode=mode)} msgs | "
            f"{format_quantity(stats.coding_words, mode=mode)} words | "
            f"{format_quantity(stats.coding_tokens_o200k, mode=mode)} tok. "
            f"Non-coding volume: {format_quantity(stats.non_coding_threads, mode=mode)} threads | "
            f"{format_quantity(stats.non_coding_messages, mode=mode)} msgs | "
            f"{format_quantity(stats.non_coding_words, mode=mode)} words | "
            f"{format_quantity(stats.non_coding_tokens_o200k, mode=mode)} tok. "
            f"Pending: {format_quantity(stats.classification_pending_threads, mode=mode)} threads | "
            f"{format_quantity(stats.pending_tokens_o200k, mode=mode)} tok."
        )
        self.table_summary.setText(
            f"Showing {format_quantity(len(top_threads), mode=mode)} top threads by message count."
        )

        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(top_threads))
        for row_index, row in enumerate(top_threads):
            title_item = QTableWidgetItem(row.title)
            title_item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(row_index, 0, title_item)

            self._set_numeric_item(row_index, 1, format_quantity(row.total_messages, mode=mode))
            self._set_numeric_item(row_index, 2, format_quantity(row.words, mode=mode))
            self._set_numeric_item(row_index, 3, format_quantity(row.tokens_o200k, mode=mode))
            self._set_numeric_item(row_index, 4, f"{row.code_ratio * 100:.1f}%")
            self._set_numeric_item(row_index, 5, f"{row.coding_confidence * 100:.1f}%")

            updated_item = QTableWidgetItem(self._format_updated(row.updated_at))
            updated_item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(row_index, 6, updated_item)

        self.table.setSortingEnabled(False)

    def _set_numeric_item(self, row: int, col: int, value: str) -> None:
        item = QTableWidgetItem(value)
        item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.table.setItem(row, col, item)

    def _format_updated(self, value) -> str:
        if value is None:
            return "n/a"

        if isinstance(value, (int, float)):
            timestamp = float(value)
            if timestamp <= 0:
                return "n/a"
            if timestamp > 1_000_000_000_000:
                timestamp /= 1000.0
            try:
                return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M")
            except Exception:
                return "n/a"

        text = str(value).strip()
        if not text:
            return "n/a"

        try:
            timestamp = float(text)
            if timestamp > 0:
                if timestamp > 1_000_000_000_000:
                    timestamp /= 1000.0
                return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M")
        except ValueError:
            pass

        if "T" in text and len(text) >= 16:
            return text.replace("T", " ")[:16]
        return text

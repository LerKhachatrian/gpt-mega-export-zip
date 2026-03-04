from __future__ import annotations

from PySide6.QtWidgets import QLabel, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget

from ...domain.models import GlobalStats, ThreadSummary


class StatsPage(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        self.summary = QLabel("No data", self)
        self.summary.setObjectName("mutedLabel")

        self.table = QTableWidget(self)
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Title", "Messages", "Words", "Updated"])
        self.table.verticalHeader().setVisible(False)

        layout.addWidget(self.summary)
        layout.addWidget(self.table, 1)

    def set_loading(self) -> None:
        self.summary.setText("Computing stats...")

    def update_stats(self, stats: GlobalStats, top_threads: list[ThreadSummary]) -> None:
        self.summary.setText(
            f"Threads={stats.total_threads:,} | Shared={stats.shared_threads:,} | "
            f"Messages={stats.total_messages:,} | Words={stats.total_words:,}"
        )

        self.table.setRowCount(len(top_threads))
        for row_index, row in enumerate(top_threads):
            self.table.setItem(row_index, 0, QTableWidgetItem(row.title))
            self.table.setItem(row_index, 1, QTableWidgetItem(f"{row.total_messages:,}"))
            self.table.setItem(row_index, 2, QTableWidgetItem(f"{row.words:,}"))
            self.table.setItem(row_index, 3, QTableWidgetItem(str(row.updated_at or "n/a")))

        self.table.resizeColumnsToContents()

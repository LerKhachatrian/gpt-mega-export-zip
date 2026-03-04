from __future__ import annotations

from PySide6.QtWidgets import QGridLayout, QLabel, QVBoxLayout, QWidget

from ...domain.models import GlobalStats


class OverviewPage(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(12)

        self.source_label = QLabel("Source: none", self)
        self.source_label.setObjectName("mutedLabel")

        grid = QGridLayout()
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(12)

        self.cards: dict[str, QLabel] = {}
        for idx, key in enumerate(
            [
                "Total Threads",
                "Shared Threads",
                "Total Messages",
                "Total Words",
                "Avg Messages",
                "Avg Words",
                "Healthy Threads",
                "Health Events",
            ]
        ):
            title = QLabel(key, self)
            title.setObjectName("mutedLabel")
            value = QLabel("0", self)
            value.setObjectName("kpiValue")
            box = QWidget(self)
            box_layout = QVBoxLayout(box)
            box_layout.setContentsMargins(12, 10, 12, 10)
            box_layout.addWidget(title)
            box_layout.addWidget(value)
            row = idx // 4
            col = idx % 4
            grid.addWidget(box, row, col)
            self.cards[key] = value

        self.note = QLabel("Load a source to start exploring.", self)
        self.note.setObjectName("mutedLabel")

        layout.addWidget(self.source_label)
        layout.addLayout(grid)
        layout.addWidget(self.note)
        layout.addStretch(1)

    def set_source(self, source: str) -> None:
        self.source_label.setText(f"Source: {source}")

    def set_loading(self) -> None:
        self.note.setText("Loading and indexing export in background...")

    def update_stats(self, stats: GlobalStats) -> None:
        self.cards["Total Threads"].setText(f"{stats.total_threads:,}")
        self.cards["Shared Threads"].setText(f"{stats.shared_threads:,}")
        self.cards["Total Messages"].setText(f"{stats.total_messages:,}")
        self.cards["Total Words"].setText(f"{stats.total_words:,}")
        self.cards["Avg Messages"].setText(f"{stats.avg_messages:,.1f}")
        self.cards["Avg Words"].setText(f"{stats.avg_words:,.1f}")
        self.cards["Healthy Threads"].setText(f"{stats.parse_ok:,}")
        self.cards["Health Events"].setText(f"{stats.health_events:,}")
        self.note.setText("Live stats update as parse batches stream in.")

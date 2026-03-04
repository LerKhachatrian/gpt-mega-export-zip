from __future__ import annotations

from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTabWidget,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from ...domain.models import ThreadDetails
from ...services.markdown_service import MarkdownService


class ThreadInspector(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        self._current_markdown = ""

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        head = QWidget(self)
        head_layout = QHBoxLayout(head)
        head_layout.setContentsMargins(0, 0, 0, 0)
        self.title_label = QLabel("No thread selected", head)
        self.title_label.setObjectName("sectionTitle")
        self.thread_id_label = QLabel("", head)
        self.thread_id_label.setObjectName("mutedLabel")
        self.copy_btn = QPushButton("Copy markdown", head)
        self.copy_btn.clicked.connect(self._copy_markdown)

        head_layout.addWidget(self.title_label)
        head_layout.addStretch(1)
        head_layout.addWidget(self.thread_id_label)
        head_layout.addWidget(self.copy_btn)

        self.tabs = QTabWidget(self)
        self.markdown_view = QTextBrowser(self.tabs)
        self.timeline_view = QTextBrowser(self.tabs)
        self.metadata_view = QTextBrowser(self.tabs)
        self.raw_view = QTextBrowser(self.tabs)

        self.tabs.addTab(self.markdown_view, "Markdown")
        self.tabs.addTab(self.timeline_view, "Timeline")
        self.tabs.addTab(self.metadata_view, "Metadata")
        self.tabs.addTab(self.raw_view, "Raw")

        layout.addWidget(head)
        layout.addWidget(self.tabs, 1)

        self.set_placeholder("Select a thread to inspect")

    def set_placeholder(self, message: str) -> None:
        self.title_label.setText(message)
        self.thread_id_label.setText("")
        self._current_markdown = ""
        self.markdown_view.setMarkdown(f"# {message}\n")
        self.timeline_view.setMarkdown("# Timeline\n")
        self.metadata_view.setMarkdown("# Metadata\n")
        self.raw_view.setMarkdown("# Raw\n")

    def set_loading(self, thread_id: str) -> None:
        self.title_label.setText("Loading thread")
        self.thread_id_label.setText(thread_id)
        self._current_markdown = ""
        self.markdown_view.setMarkdown("# Loading...\n\nFetching thread details.")

    def set_details(self, details: ThreadDetails, renderer: MarkdownService) -> None:
        self.title_label.setText(details.summary.title)
        self.thread_id_label.setText(details.summary.thread_id)

        conversation_md = renderer.render_conversation(details)
        self._current_markdown = conversation_md

        self.markdown_view.setMarkdown(conversation_md)
        self.timeline_view.setMarkdown(renderer.render_timeline(details))
        self.metadata_view.setMarkdown(renderer.render_metadata(details))
        self.raw_view.setMarkdown(renderer.render_raw(details))

    def set_error(self, message: str) -> None:
        self.title_label.setText("Thread load failed")
        self.markdown_view.setMarkdown(f"# Error\n\n{message}")

    def _copy_markdown(self) -> None:
        if not self._current_markdown:
            return
        clipboard = QApplication.clipboard()
        clipboard.setText(self._current_markdown)

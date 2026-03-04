import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from PySide6.QtWidgets import QApplication

from chatgpt_export_viewer_v2.app_shell import create_window


def main() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName("GPT Mega Export (.zip)")
    app.setApplicationDisplayName("GPT Mega Export (.zip)")
    window = create_window(app)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

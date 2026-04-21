"""Entry point for the Todo List application."""

import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFont

from database import init_db
from main_window import MainWindow


def main():
    init_db()

    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    # Set default font
    font = QFont("Segoe UI", 13)
    app.setFont(font)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()

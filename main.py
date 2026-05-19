"""Entry point for the Todo List application."""

import sys
from PyQt6.QtWidgets import QApplication, QDialog
from PyQt6.QtGui import QFont

from database import init_db, get_api_token
from main_window import MainWindow
from dialogs import LoginDialog


def main():
    init_db()

    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    # Set default font
    font = QFont("Segoe UI", 13)
    app.setFont(font)

    if not get_api_token():
        login_dialog = LoginDialog()
        if login_dialog.exec() != QDialog.DialogCode.Accepted:
            return

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()

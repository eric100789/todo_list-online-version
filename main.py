"""Entry point for the Todo List application."""

import sys
from PyQt6.QtWidgets import QApplication, QDialog
from PyQt6.QtGui import QFont

from database import init_db, get_api_token, validate_api_token
from main_window import MainWindow
from dialogs import LoginDialog


def main():
    init_db()

    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    # Set default font
    font = QFont("Segoe UI", 13)
    app.setFont(font)

    token_valid = validate_api_token()
    if not token_valid:
        login_dialog = LoginDialog()
        if get_api_token():
            login_dialog.status_label.setText("Saved token expired or was revoked. Please login again.")
        else:
            login_dialog.status_label.setText("Backend unavailable or not authenticated. Please login when ready.")
        if login_dialog.exec() != QDialog.DialogCode.Accepted:
            return

    try:
        window = MainWindow()
        window.show()
    except Exception:
        login_dialog = LoginDialog()
        login_dialog.status_label.setText("Backend unavailable or app initialization failed. Please login again.")
        if login_dialog.exec() != QDialog.DialogCode.Accepted:
            return
        window = MainWindow()
        window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()

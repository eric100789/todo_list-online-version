"""Notes view – simple note-taking panel (not shown in mini mode)."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QScrollArea, QFrame, QMessageBox, QSizePolicy,
    QApplication
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QCursor

from styles import COLORS
from database import add_note, get_all_notes, update_note, delete_note
from date_utils import format_datetime
from i18n import t


class NoteCard(QFrame):
    """A single note card with edit / copy / delete actions."""

    def __init__(self, note: dict, parent=None):
        super().__init__(parent)
        self.note = note
        self.note_id = note["id"]
        self._editing = False
        self.setObjectName("noteCard")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self._apply_style()
        self._build_ui()

    def _apply_style(self):
        self.setStyleSheet(f"""
            QFrame#noteCard {{
                background-color: {COLORS['surface']};
                border: 1px solid {COLORS['border']};
                border-radius: 10px;
            }}
        """)

    def _build_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(14, 10, 14, 10)
        self.main_layout.setSpacing(6)

        # Content display
        self.content_label = QLabel(self.note["content"])
        self.content_label.setFont(QFont("Segoe UI", 12))
        self.content_label.setWordWrap(True)
        self.content_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        self.main_layout.addWidget(self.content_label)

        # Content editor (hidden initially)
        self.content_edit = QTextEdit()
        self.content_edit.setFont(QFont("Segoe UI", 12))
        self.content_edit.setPlaceholderText(t("note_placeholder"))
        self.content_edit.setMaximumHeight(120)
        self.content_edit.setVisible(False)
        self.main_layout.addWidget(self.content_edit)

        # Footer row: timestamp + action buttons
        footer = QHBoxLayout()
        footer.setSpacing(8)

        ts = format_datetime(self.note.get("updated_at") or self.note.get("created_at"))
        self.time_label = QLabel(ts)
        self.time_label.setFont(QFont("Segoe UI", 10))
        self.time_label.setStyleSheet(f"color: {COLORS['text_muted']};")
        footer.addWidget(self.time_label)

        footer.addStretch()

        # Edit / Save button
        self.edit_btn = QPushButton(t("edit_note"))
        self.edit_btn.setObjectName("ghostBtn")
        self.edit_btn.setFont(QFont("Segoe UI", 11))
        self.edit_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.edit_btn.clicked.connect(self._toggle_edit)
        footer.addWidget(self.edit_btn)

        # Copy button
        self.copy_btn = QPushButton(t("copy_note"))
        self.copy_btn.setObjectName("ghostBtn")
        self.copy_btn.setFont(QFont("Segoe UI", 11))
        self.copy_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.copy_btn.clicked.connect(self._copy)
        footer.addWidget(self.copy_btn)

        # Delete button
        self.del_btn = QPushButton("✕")
        self.del_btn.setFixedSize(28, 28)
        self.del_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.del_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {COLORS['text_muted']};
                border: none;
                border-radius: 14px;
                font-size: 13px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {COLORS['danger']};
                color: white;
            }}
        """)
        self.del_btn.clicked.connect(self._delete)
        footer.addWidget(self.del_btn)

        self.main_layout.addLayout(footer)

    # ── actions ──

    def _toggle_edit(self):
        if self._editing:
            # Save
            new_content = self.content_edit.toPlainText().strip()
            if new_content:
                update_note(self.note_id, new_content)
                self.content_label.setText(new_content)
            self._editing = False
            self.content_edit.setVisible(False)
            self.content_label.setVisible(True)
            self.edit_btn.setText(t("edit_note"))
        else:
            # Enter edit mode
            self.content_edit.setPlainText(self.content_label.text())
            self._editing = True
            self.content_edit.setVisible(True)
            self.content_label.setVisible(False)
            self.content_edit.setFocus()
            self.edit_btn.setText(t("save"))

    def _copy(self):
        clipboard = QApplication.clipboard()
        if clipboard:
            clipboard.setText(self.note["content"])

    def _delete(self):
        reply = QMessageBox.question(
            self, t("delete_note_title"),
            t("delete_note_confirm"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            delete_note(self.note_id)
            # Find the parent NotesView and refresh
            parent = self.parent()
            while parent and not isinstance(parent, NotesView):
                parent = parent.parent()
            if parent:
                parent.refresh()


class NotesView(QWidget):
    """Panel for simple notes: text input + add button, scrollable list."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Header
        header = QHBoxLayout()
        self.title_label = QLabel(t("notes_title"))
        self.title_label.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        header.addWidget(self.title_label)
        header.addStretch()
        layout.addLayout(header)

        # New note area
        self.new_note_edit = QTextEdit()
        self.new_note_edit.setPlaceholderText(t("note_placeholder"))
        self.new_note_edit.setFont(QFont("Segoe UI", 12))
        self.new_note_edit.setMaximumHeight(100)
        layout.addWidget(self.new_note_edit)

        self.add_btn = QPushButton(t("add_note"))
        self.add_btn.setFont(QFont("Segoe UI", 12, QFont.Weight.DemiBold))
        self.add_btn.setMinimumHeight(38)
        self.add_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.add_btn.clicked.connect(self._add_note)
        layout.addWidget(self.add_btn)

        # Scrollable notes list
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.container = QWidget()
        self.container_layout = QVBoxLayout(self.container)
        self.container_layout.setContentsMargins(0, 0, 0, 0)
        self.container_layout.setSpacing(8)
        self.container_layout.addStretch()

        self.scroll.setWidget(self.container)
        layout.addWidget(self.scroll)

    def _add_note(self):
        content = self.new_note_edit.toPlainText().strip()
        if not content:
            return
        add_note(content)
        self.new_note_edit.clear()
        self.refresh()

    def refresh(self):
        """Reload notes from database."""
        while self.container_layout.count() > 1:
            item = self.container_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        notes = get_all_notes()

        if not notes:
            empty = QLabel(t("no_notes"))
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty.setFont(QFont("Segoe UI", 14))
            empty.setStyleSheet(f"color: {COLORS['text_muted']}; padding: 40px;")
            self.container_layout.insertWidget(0, empty)
            return

        for note in notes:
            card = NoteCard(note)
            self.container_layout.insertWidget(self.container_layout.count() - 1, card)

    def retranslate(self):
        """Update labels after language change."""
        self.title_label.setText(t("notes_title"))
        self.new_note_edit.setPlaceholderText(t("note_placeholder"))
        self.add_btn.setText(t("add_note"))
        self.refresh()

"""Quick sticky-note view for sudden tasks."""

from PyQt6.QtCore import QPoint, Qt, pyqtSignal
from PyQt6.QtGui import QCursor, QFont, QMouseEvent
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from date_utils import format_due_date, is_overdue
from i18n import t
from styles import COLORS


DEFAULT_STICKY_COLOR = "#FDE68A"
CARD_W = 220
CARD_H = 160
MARGIN = 20


class QuickStickyCard(QFrame):
    """Draggable sticky card used in quick view."""

    completed = pyqtSignal(int)
    deleted = pyqtSignal(int)
    edit_requested = pyqtSignal(int)
    moved = pyqtSignal(int, int, int)

    def __init__(self, task: dict, parent_canvas: QWidget):
        super().__init__(parent_canvas)
        self.task = task
        self.task_id = int(task["id"])
        self._dragging = False
        self._drag_offset = QPoint()
        self._build_ui()

    def _build_ui(self):
        bg = self.task.get("color") or DEFAULT_STICKY_COLOR
        self.setObjectName("quickStickyCard")
        self.setCursor(QCursor(Qt.CursorShape.OpenHandCursor))
        self.setFixedSize(CARD_W, CARD_H)
        self.setStyleSheet(
            f"""
            QFrame#quickStickyCard {{
                background: {bg};
                border: 1px solid rgba(0, 0, 0, 0.16);
                border-radius: 8px;
            }}
            QLabel {{
                color: #1F2937;
                background: transparent;
            }}
            QPushButton {{
                background: rgba(255, 255, 255, 0.45);
                color: #1F2937;
                border: none;
                border-radius: 10px;
                padding: 0;
                font-weight: 700;
            }}
            QPushButton:hover {{
                background: rgba(255, 255, 255, 0.72);
            }}
            """
        )

        root = QVBoxLayout(self)
        root.setContentsMargins(10, 8, 10, 8)
        root.setSpacing(6)

        top = QHBoxLayout()
        top.setSpacing(4)

        title = QLabel(self.task.get("title", ""))
        title.setWordWrap(True)
        title.setFont(QFont("Segoe UI", 11, QFont.Weight.DemiBold))
        top.addWidget(title, 1)

        done_btn = QPushButton("✓")
        done_btn.setFixedSize(20, 20)
        done_btn.setToolTip(t("kanban_mark_done"))
        done_btn.clicked.connect(lambda: self.completed.emit(self.task_id))
        top.addWidget(done_btn)

        del_btn = QPushButton("✕")
        del_btn.setFixedSize(20, 20)
        del_btn.setToolTip(t("delete_title"))
        del_btn.clicked.connect(lambda: self.deleted.emit(self.task_id))
        top.addWidget(del_btn)

        root.addLayout(top)

        due = QLabel(format_due_date(self.task.get("due_date")))
        due.setFont(QFont("Segoe UI", 9))
        if is_overdue(self.task.get("due_date")):
            due.setStyleSheet(f"color: {COLORS['overdue']};")
        else:
            due.setStyleSheet("color: #374151;")
        root.addWidget(due)

        desc = QLabel((self.task.get("description") or "").strip())
        desc.setWordWrap(True)
        desc.setFont(QFont("Segoe UI", 9))
        desc.setStyleSheet("color: #374151;")
        root.addWidget(desc, 1)

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        self.edit_requested.emit(self.task_id)
        super().mouseDoubleClickEvent(event)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self._dragging = True
            self._drag_offset = event.pos()
            self.setCursor(QCursor(Qt.CursorShape.ClosedHandCursor))
            self.raise_()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        if not (self._dragging and (event.buttons() & Qt.MouseButton.LeftButton)):
            return

        parent = self.parentWidget()
        if not parent:
            return

        target = self.mapToParent(event.pos() - self._drag_offset)
        max_x = max(MARGIN, parent.width() - self.width() - MARGIN)
        max_y = max(MARGIN, parent.height() - self.height() - MARGIN)
        nx = max(MARGIN, min(target.x(), max_x))
        ny = max(MARGIN, min(target.y(), max_y))
        self.move(nx, ny)

    def mouseReleaseEvent(self, event: QMouseEvent):
        if self._dragging and event.button() == Qt.MouseButton.LeftButton:
            self._dragging = False
            self.setCursor(QCursor(Qt.CursorShape.OpenHandCursor))
            self.moved.emit(self.task_id, self.x(), self.y())
        super().mouseReleaseEvent(event)


class QuickView(QWidget):
    """Canvas-like board for quick sticky tasks."""

    add_quick_requested = pyqtSignal()
    task_completed = pyqtSignal(int)
    task_deleted = pyqtSignal(int)
    task_edit_requested = pyqtSignal(int)
    task_moved = pyqtSignal(int, int, int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(10)

        head = QHBoxLayout()
        self.title = QLabel(t("quick_title"))
        self.title.setFont(QFont("Segoe UI", 17, QFont.Weight.Bold))
        head.addWidget(self.title)

        head.addStretch()

        self.count_label = QLabel(t("task_count", n=0, s="s"))
        self.count_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        head.addWidget(self.count_label)

        self.add_btn = QPushButton(t("add_quick"))
        self.add_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.add_btn.clicked.connect(self.add_quick_requested.emit)
        head.addWidget(self.add_btn)

        self.reflow_btn = QPushButton(t("quick_reflow"))
        self.reflow_btn.setObjectName("ghostBtn")
        self.reflow_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.reflow_btn.clicked.connect(self.reflow_cards)
        head.addWidget(self.reflow_btn)

        root.addLayout(head)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        self.canvas = QWidget()
        self.canvas.setMinimumSize(980, 680)
        self.canvas.setStyleSheet(
            """
            QWidget {
                background-color: #ECEFF3;
                border-radius: 10px;
            }
            """
        )

        self.scroll.setWidget(self.canvas)
        root.addWidget(self.scroll)

    def retranslate(self):
        self.title.setText(t("quick_title"))
        self.add_btn.setText(t("add_quick"))
        self.reflow_btn.setText(t("quick_reflow"))

    def refresh(self, tasks: list[dict]):
        for child in self.canvas.findChildren(QuickStickyCard):
            child.deleteLater()

        old_empty = self.canvas.findChild(QLabel, "quickEmpty")
        if old_empty:
            old_empty.deleteLater()

        count = len(tasks)
        self.count_label.setText(t("task_count", n=count, s="" if count == 1 else "s"))

        if not tasks:
            empty = QLabel(t("quick_empty"), self.canvas)
            empty.setObjectName("quickEmpty")
            empty.setFont(QFont("Segoe UI", 13))
            empty.setStyleSheet("color: #6B7280; background: transparent;")
            empty.adjustSize()
            empty.move(24, 24)
            empty.show()
            return

        max_right = self.canvas.minimumWidth()
        max_bottom = self.canvas.minimumHeight()

        for idx, task in enumerate(tasks):
            card = QuickStickyCard(task, self.canvas)
            card.completed.connect(self.task_completed.emit)
            card.deleted.connect(self.task_deleted.emit)
            card.edit_requested.connect(self.task_edit_requested.emit)
            card.moved.connect(self.task_moved.emit)

            x = int(task.get("pos_x") or 0)
            y = int(task.get("pos_y") or 0)
            if x <= 0 and y <= 0:
                x = MARGIN + (idx % 4) * (CARD_W + 20)
                y = MARGIN + (idx // 4) * (CARD_H + 20)

            card.move(max(MARGIN, x), max(MARGIN, y))
            card.show()

            max_right = max(max_right, card.x() + card.width() + MARGIN)
            max_bottom = max(max_bottom, card.y() + card.height() + MARGIN)

        self.canvas.setMinimumSize(max(980, max_right), max(680, max_bottom))

    def reflow_cards(self):
        """Re-layout sticky cards to fit current viewport without overflowing canvas bounds."""
        cards = self.canvas.findChildren(QuickStickyCard)
        if not cards:
            return

        view_w = max(self.scroll.viewport().width(), CARD_W + 2 * MARGIN)
        cols = max(1, (view_w - MARGIN) // (CARD_W + 20))

        max_right = view_w
        max_bottom = self.scroll.viewport().height()

        for idx, card in enumerate(cards):
            col = idx % cols
            row = idx // cols
            x = MARGIN + col * (CARD_W + 20)
            y = MARGIN + row * (CARD_H + 20)
            card.move(x, y)
            card.moved.emit(card.task_id, x, y)
            max_right = max(max_right, x + CARD_W + MARGIN)
            max_bottom = max(max_bottom, y + CARD_H + MARGIN)

        self.canvas.setMinimumSize(max(980, max_right), max(680, max_bottom))

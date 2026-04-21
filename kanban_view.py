"""Kanban board view widgets."""

from typing import Optional

from PyQt6.QtCore import QPoint, QSize, Qt, QMimeData, pyqtSignal
from PyQt6.QtGui import QCursor, QDrag, QFont, QMouseEvent
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QColorDialog,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from date_utils import format_due_date, is_overdue
from i18n import t
from styles import COLORS


CATEGORY_PRESET_COLORS = [
    "#0EA5E9", "#10B981", "#F59E0B", "#F97316", "#EF4444", "#8B5CF6", "#EC4899", "#64748B"
]
MIME_CATEGORY_ID = "application/x-kanban-category-id"


class CategoryDialog(QDialog):
    """Dialog for creating/editing a board category."""

    def __init__(self, parent=None, category: Optional[dict] = None):
        super().__init__(parent)
        self.category = category or {}
        self.result_data = None
        self._selected_color = self.category.get("color", "")
        self.setWindowTitle(t("kanban_edit_category") if category else t("kanban_new_category"))
        self.setFixedSize(420, 250)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        title = QLabel(t("kanban_category_name"))
        title.setFont(QFont("Segoe UI", 11, QFont.Weight.DemiBold))
        layout.addWidget(title)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText(t("kanban_category_name_placeholder"))
        self.name_input.setMinimumHeight(36)
        self.name_input.setText(self.category.get("name", ""))
        layout.addWidget(self.name_input)

        color_title = QLabel(t("task_color"))
        color_title.setFont(QFont("Segoe UI", 11, QFont.Weight.DemiBold))
        layout.addWidget(color_title)

        chips = QHBoxLayout()
        chips.setSpacing(8)
        self._chip_buttons = []
        for color in CATEGORY_PRESET_COLORS:
            btn = QPushButton()
            btn.setCheckable(True)
            btn.setFixedSize(22, 22)
            btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: {color};
                    border: 2px solid transparent;
                    border-radius: 11px;
                }}
                QPushButton:checked {{
                    border-color: {COLORS['text']};
                }}
            """)
            btn.clicked.connect(lambda checked=False, c=color: self._select_color(c))
            chips.addWidget(btn)
            self._chip_buttons.append((btn, color))

        custom_btn = QPushButton(t("task_color_custom"))
        custom_btn.setObjectName("ghostBtn")
        custom_btn.clicked.connect(self._pick_custom_color)
        chips.addWidget(custom_btn)

        clear_btn = QPushButton(t("task_color_none"))
        clear_btn.setObjectName("ghostBtn")
        clear_btn.clicked.connect(lambda: self._select_color(""))
        chips.addWidget(clear_btn)

        chips.addStretch()
        layout.addLayout(chips)

        self.preview = QLabel()
        self.preview.setFixedHeight(24)
        layout.addWidget(self.preview)
        self._refresh_preview()

        btn_row = QHBoxLayout()
        cancel = QPushButton(t("cancel"))
        cancel.setObjectName("ghostBtn")
        cancel.clicked.connect(self.reject)
        btn_row.addWidget(cancel)

        save = QPushButton(t("save"))
        save.clicked.connect(self._on_save)
        btn_row.addWidget(save)

        layout.addStretch()
        layout.addLayout(btn_row)

        self._sync_chip_checks()

    def _pick_custom_color(self):
        color = QColorDialog.getColor(parent=self)
        if color.isValid():
            self._select_color(color.name())

    def _select_color(self, color: str):
        self._selected_color = color
        self._sync_chip_checks()
        self._refresh_preview()

    def _sync_chip_checks(self):
        for btn, color in self._chip_buttons:
            btn.blockSignals(True)
            btn.setChecked(self._selected_color.lower() == color.lower())
            btn.blockSignals(False)

    def _refresh_preview(self):
        color = self._selected_color or COLORS['border']
        text = self._selected_color or t("task_color_none")
        self.preview.setText(t("kanban_color_preview", c=text))
        self.preview.setStyleSheet(
            f"border-left: 8px solid {color}; padding-left: 8px; color: {COLORS['text_secondary']};"
        )

    def _on_save(self):
        name = self.name_input.text().strip()
        if not name:
            self.name_input.setFocus()
            return
        self.result_data = {"name": name, "color": self._selected_color or ""}
        self.accept()


class KanbanTaskList(QListWidget):
    """Task list in a single Kanban column."""

    task_dropped = pyqtSignal(int, object)
    task_complete_requested = pyqtSignal(int)
    task_delete_requested = pyqtSignal(int)
    task_edit_requested = pyqtSignal(int)

    def __init__(self, category_id, parent=None):
        super().__init__(parent)
        self.category_id = category_id
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setDragDropMode(QAbstractItemView.DragDropMode.DragDrop)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setAlternatingRowColors(False)
        self.setSpacing(6)
        self.setStyleSheet(f"QListWidget {{ background: transparent; border: none; }}")
        self.itemDoubleClicked.connect(self._on_item_double_clicked)

    _drag_task_id: Optional[int] = None

    def add_task(self, task: dict):
        item = QListWidgetItem()
        item.setData(Qt.ItemDataRole.UserRole, int(task["id"]))
        widget = KanbanTaskItem(task)
        widget.complete_requested.connect(self.task_complete_requested.emit)
        widget.delete_requested.connect(self.task_delete_requested.emit)
        item.setSizeHint(QSize(max(120, self.viewport().width() - 8), widget.sizeHint().height()))
        self.addItem(item)
        self.setItemWidget(item, widget)
        self._sync_item_widths()

    def add_section_header(self, text: str):
        item = QListWidgetItem(text)
        item.setData(Qt.ItemDataRole.UserRole, None)
        item.setFlags(Qt.ItemFlag.ItemIsEnabled)
        item.setForeground(self.palette().mid())
        item.setSizeHint(QSize(max(120, self.viewport().width() - 8), 24))
        self.addItem(item)

    def startDrag(self, supportedActions):
        item = self.currentItem()
        KanbanTaskList._drag_task_id = int(item.data(Qt.ItemDataRole.UserRole)) if item else None
        super().startDrag(supportedActions)

    def dropEvent(self, event):
        super().dropEvent(event)
        if KanbanTaskList._drag_task_id is not None:
            self.task_dropped.emit(int(KanbanTaskList._drag_task_id), self.category_id)
        KanbanTaskList._drag_task_id = None
        self._sync_item_widths()

    def _on_item_double_clicked(self, item: QListWidgetItem):
        task_id = item.data(Qt.ItemDataRole.UserRole)
        if task_id is not None:
            self.task_edit_requested.emit(int(task_id))

    def _sync_item_widths(self):
        width = max(120, self.viewport().width() - 8)
        for i in range(self.count()):
            item = self.item(i)
            widget = self.itemWidget(item)
            h = widget.sizeHint().height() if widget else 24
            item.setSizeHint(QSize(width, h))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._sync_item_widths()


class KanbanTaskItem(QFrame):
    """Compact task row used in Kanban columns."""

    complete_requested = pyqtSignal(int)
    delete_requested = pyqtSignal(int)

    def __init__(self, task: dict, parent=None):
        super().__init__(parent)
        self.task = task
        self.task_id = int(task["id"])
        self._build_ui()

    def _build_ui(self):
        accent = self.task.get("color") or COLORS['primary']
        self.setStyleSheet(f"""
            QFrame {{
                background: {COLORS['surface']};
                border: 1px solid {COLORS['border']};
                border-left: 4px solid {accent};
                border-radius: 8px;
            }}
            QLabel {{
                background: transparent;
            }}
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 8, 8)
        layout.setSpacing(6)

        row = QHBoxLayout()
        row.setSpacing(6)

        title = QLabel(self.task.get("title", ""))
        title.setWordWrap(True)
        title.setFont(QFont("Segoe UI", 11, QFont.Weight.DemiBold))
        row.addWidget(title, 1)

        done_btn = QPushButton("✓")
        done_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        done_btn.setFixedSize(24, 24)
        done_btn.setToolTip(t("kanban_mark_done"))
        done_btn.setStyleSheet(f"""
            QPushButton {{
                background: {COLORS['success']};
                color: white;
                border: none;
                border-radius: 12px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background: #059669;
            }}
        """)
        done_btn.clicked.connect(lambda: self.complete_requested.emit(self.task_id))
        row.addWidget(done_btn)

        del_btn = QPushButton("✕")
        del_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        del_btn.setFixedSize(24, 24)
        del_btn.setToolTip(t("delete_title"))
        del_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {COLORS['text_muted']};
                border: none;
                border-radius: 12px;
            }}
            QPushButton:hover {{
                background: {COLORS['danger']};
                color: white;
            }}
        """)
        del_btn.clicked.connect(lambda: self.delete_requested.emit(self.task_id))
        row.addWidget(del_btn)

        layout.addLayout(row)

        due = format_due_date(self.task.get("due_date"))
        due_label = QLabel(due)
        due_label.setFont(QFont("Segoe UI", 9))
        if is_overdue(self.task.get("due_date")):
            due_label.setStyleSheet(f"color: {COLORS['overdue']};")
        elif self.task.get("due_date"):
            due_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        else:
            due_label.setStyleSheet(f"color: {COLORS['text_muted']};")
        layout.addWidget(due_label)


class CategoryDragHandle(QLabel):
    """Drag handle for reordering Kanban categories."""

    def __init__(self, category_id: int, parent=None):
        super().__init__(parent)
        self.category_id = category_id
        self._drag_start = QPoint()
        self.setText("↕")
        self.setCursor(QCursor(Qt.CursorShape.SizeAllCursor))
        self.setToolTip(t("kanban_reorder_category"))
        self.setStyleSheet(f"color: {COLORS['text_muted']}; padding: 0 4px;")

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_start = event.pos()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        if not (event.buttons() & Qt.MouseButton.LeftButton):
            return
        if (event.pos() - self._drag_start).manhattanLength() < 6:
            return

        drag = QDrag(self)
        mime = QMimeData()
        mime.setData(MIME_CATEGORY_ID, str(self.category_id).encode("utf-8"))
        drag.setMimeData(mime)
        drag.exec(Qt.DropAction.MoveAction)


class KanbanColumn(QFrame):
    """A single Kanban category column."""

    add_task_requested = pyqtSignal(object)
    edit_category_requested = pyqtSignal(int)
    delete_category_requested = pyqtSignal(int)
    category_drop_requested = pyqtSignal(int, int)

    def __init__(self, category_id, name: str, color: str, editable: bool, reorderable: bool, allow_add: bool, parent=None):
        super().__init__(parent)
        self.category_id = category_id
        self._editable = editable
        self._reorderable = reorderable
        self._allow_add = allow_add
        self.setObjectName("kanbanColumn")
        self.setMinimumWidth(220)
        self.setMaximumWidth(520)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        border_color = color or COLORS['border']
        self.setStyleSheet(f"""
            QFrame#kanbanColumn {{
                background: {COLORS['surface']};
                border: 1px solid {COLORS['border']};
                border-top: 4px solid {border_color};
                border-radius: 10px;
            }}
        """)
        self.setAcceptDrops(self._reorderable)

        root = QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(8)

        header = QHBoxLayout()
        header.setSpacing(6)

        self.title_label = QLabel(name)
        self.title_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        header.addWidget(self.title_label, 1)

        if self._reorderable and isinstance(self.category_id, int):
            header.addWidget(CategoryDragHandle(self.category_id))

        if self._allow_add:
            add_btn = QPushButton("+")
            add_btn.setToolTip(t("kanban_add_to_category"))
            add_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            add_btn.setFixedSize(24, 24)
            add_btn.clicked.connect(lambda: self.add_task_requested.emit(self.category_id))
            header.addWidget(add_btn)

        if self._editable:
            edit_btn = QPushButton("✎")
            edit_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            edit_btn.setFixedSize(24, 24)
            edit_btn.setToolTip(t("kanban_edit_category"))
            edit_btn.setObjectName("ghostBtn")
            edit_btn.clicked.connect(lambda: self.edit_category_requested.emit(int(self.category_id)))
            header.addWidget(edit_btn)

            del_btn = QPushButton("🗑")
            del_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            del_btn.setFixedSize(24, 24)
            del_btn.setToolTip(t("kanban_delete_category"))
            del_btn.setObjectName("ghostBtn")
            del_btn.clicked.connect(lambda: self.delete_category_requested.emit(int(self.category_id)))
            header.addWidget(del_btn)

        root.addLayout(header)

        self.list_widget = KanbanTaskList(self.category_id)
        root.addWidget(self.list_widget)

    def set_column_width(self, width: int):
        self.setMinimumWidth(width)
        self.setMaximumWidth(width)
        self.list_widget._sync_item_widths()

    def dragEnterEvent(self, event):
        if not self._reorderable:
            event.ignore()
            return
        if event.mimeData().hasFormat(MIME_CATEGORY_ID):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if self._reorderable and event.mimeData().hasFormat(MIME_CATEGORY_ID):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        if not (self._reorderable and event.mimeData().hasFormat(MIME_CATEGORY_ID)):
            event.ignore()
            return
        dragged_raw = bytes(event.mimeData().data(MIME_CATEGORY_ID)).decode("utf-8")
        try:
            dragged_id = int(dragged_raw)
            target_id = int(self.category_id)
        except (TypeError, ValueError):
            event.ignore()
            return
        if dragged_id != target_id:
            self.category_drop_requested.emit(dragged_id, target_id)
        event.acceptProposedAction()


class KanbanView(QWidget):
    """Full Kanban board view."""

    add_category_requested = pyqtSignal()
    add_task_requested = pyqtSignal(object)
    edit_category_requested = pyqtSignal(int)
    delete_category_requested = pyqtSignal(int)
    task_moved = pyqtSignal(int, object)
    task_completed = pyqtSignal(int)
    task_deleted = pyqtSignal(int)
    task_edit_requested = pyqtSignal(int)
    categories_reordered = pyqtSignal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.min_column_width = 260
        self._category_order_ids: list[int] = []
        self._columns: list[KanbanColumn] = []
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(10)

        top = QHBoxLayout()
        self.title = QLabel(t("nav_kanban"))
        self.title.setFont(QFont("Segoe UI", 15, QFont.Weight.Bold))
        top.addWidget(self.title)

        top.addStretch()

        self.count_label = QLabel(t("task_count", n=0, s="s"))
        self.count_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        top.addWidget(self.count_label)

        self.add_col_btn = QPushButton(t("kanban_add_category"))
        self.add_col_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.add_col_btn.clicked.connect(self.add_category_requested.emit)
        top.addWidget(self.add_col_btn)

        root.addLayout(top)

        self.scroll = QScrollArea()
        self.scroll.setObjectName("kanbanScroll")
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll.setStyleSheet(f"""
            QScrollArea#kanbanScroll {{
                border: none;
            }}
            QScrollArea#kanbanScroll QScrollBar:horizontal {{
                background: {COLORS['bg']};
                height: 10px;
                border-radius: 5px;
            }}
            QScrollArea#kanbanScroll QScrollBar::handle:horizontal {{
                background: {COLORS['border']};
                border-radius: 5px;
                min-width: 30px;
            }}
            QScrollArea#kanbanScroll QScrollBar::handle:horizontal:hover {{
                background: {COLORS['text_muted']};
            }}
            QScrollArea#kanbanScroll QScrollBar::add-line:horizontal,
            QScrollArea#kanbanScroll QScrollBar::sub-line:horizontal {{
                width: 0px;
            }}
        """)

        self.board = QWidget()
        self.board_layout = QHBoxLayout(self.board)
        self.board_layout.setContentsMargins(0, 0, 0, 0)
        self.board_layout.setSpacing(10)
        self.board_layout.addStretch()

        self.scroll.setWidget(self.board)
        root.addWidget(self.scroll)

    def retranslate(self):
        self.title.setText(t("nav_kanban"))
        self.add_col_btn.setText(t("kanban_add_category"))

    def set_layout_preferences(self, min_column_width: int):
        self.min_column_width = max(180, int(min_column_width))
        self._apply_column_sizing()

    def refresh(self, tasks: list[dict], categories: list[dict]):
        while self.board_layout.count() > 1:
            item = self.board_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._columns.clear()
        self._category_order_ids = [int(c["id"]) for c in categories]

        self.count_label.setText(t("task_count", n=len(tasks), s="" if len(tasks) == 1 else "s"))

        grouped: dict[object, list[dict]] = {None: []}
        for cat in categories:
            grouped[cat["id"]] = []

        for task in tasks:
            cat_id = task.get("category_id")
            if cat_id not in grouped:
                cat_id = None
            grouped[cat_id].append(task)

        # Default uncategorized column
        self._add_column(None, t("kanban_uncategorized"), "", False, False, True, grouped.get(None, []))

        for cat in categories:
            self._add_column(
                cat["id"],
                cat.get("name", ""),
                cat.get("color", ""),
                True,
                True,
                True,
                grouped.get(cat["id"], []),
            )

        self._apply_column_sizing()

    def _add_column(self, category_id, name: str, color: str, editable: bool, reorderable: bool, allow_add: bool, tasks: list[dict]):
        column = KanbanColumn(category_id, name, color, editable, reorderable, allow_add)
        column.add_task_requested.connect(self.add_task_requested.emit)
        column.edit_category_requested.connect(self.edit_category_requested.emit)
        column.delete_category_requested.connect(self.delete_category_requested.emit)
        column.category_drop_requested.connect(self._on_category_drop)

        column.list_widget.task_dropped.connect(self.task_moved.emit)
        column.list_widget.task_complete_requested.connect(self.task_completed.emit)
        column.list_widget.task_delete_requested.connect(self.task_deleted.emit)
        column.list_widget.task_edit_requested.connect(self.task_edit_requested.emit)

        for task in tasks:
            column.list_widget.add_task(task)

        self._columns.append(column)
        self.board_layout.insertWidget(self.board_layout.count() - 1, column)

    def _on_category_drop(self, dragged_id: int, target_id: int):
        if dragged_id not in self._category_order_ids or target_id not in self._category_order_ids:
            return
        if dragged_id == target_id:
            return

        ordered = self._category_order_ids[:]
        ordered.remove(dragged_id)
        target_idx = ordered.index(target_id)
        ordered.insert(target_idx, dragged_id)
        self._category_order_ids = ordered
        self.categories_reordered.emit(ordered)

    def _apply_column_sizing(self):
        if not self._columns:
            return
        spacing = self.board_layout.spacing()
        total_width = len(self._columns) * self.min_column_width + max(0, len(self._columns) - 1) * spacing
        self.board.setMinimumWidth(total_width)
        for col in self._columns:
            col.set_column_width(self.min_column_width)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._apply_column_sizing()

    def confirm_delete_category(self) -> bool:
        reply = QMessageBox.question(
            self,
            t("delete_title"),
            t("kanban_delete_category_confirm"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        return reply == QMessageBox.StandardButton.Yes
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Add Flight Dialog — premium dark themed search dialog with background threading.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QListWidget, QListWidgetItem,
    QFrame, QSizePolicy, QGraphicsOpacityEffect, QButtonGroup,
    QWidget
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QFont, QColor

from typing import Any, cast

from .translations import Translator
from .flight_tracker import FlightTracker


# ======================================================================
# Background search worker
# ======================================================================

class SearchWorker(QThread):
    """Run API search in background thread to keep UI responsive."""
    results_ready = pyqtSignal(list)
    error_occurred = pyqtSignal(str)

    def __init__(self, tracker: FlightTracker, query: str):
        super().__init__()
        self.tracker = tracker
        self.query = query

    def run(self):
        try:
            results = self.tracker.search_flight(self.query)
            self.results_ready.emit(results)
        except Exception as e:
            self.error_occurred.emit(str(e))


# ======================================================================
# Dialog
# ======================================================================

DIALOG_STYLE = """
QDialog {
    background-color: #0f1923;
    color: #e8eaf0;
    border-radius: 12px;
}

QLabel {
    color: #a8b4c0;
    font-size: 13px;
}

QLabel#title_label {
    color: #ffffff;
    font-size: 18px;
    font-weight: bold;
}

QLabel#hint_label {
    color: #5a6a7a;
    font-size: 11px;
}

QLineEdit {
    background-color: #1a2535;
    border: 2px solid #2a3a4a;
    border-radius: 8px;
    color: #e8eaf0;
    font-size: 14px;
    padding: 10px 14px;
    selection-background-color: #1e6fbf;
}

QLineEdit:focus {
    border-color: #1e90ff;
}

QPushButton {
    border-radius: 8px;
    font-size: 13px;
    font-weight: 600;
    padding: 10px 22px;
    border: none;
}

QPushButton#btn_search {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
        stop:0 #1e6fbf, stop:1 #0da5e8);
    color: #ffffff;
}

QPushButton#btn_search:hover {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
        stop:0 #2585d9, stop:1 #18b5f5);
}

QPushButton#btn_search:pressed {
    background: #1558a0;
}

QPushButton#btn_add {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
        stop:0 #0f9960, stop:1 #16c47a);
    color: #ffffff;
}

QPushButton#btn_add:hover {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
        stop:0 #14b070, stop:1 #1dd88a);
}

QPushButton#btn_add:disabled {
    background-color: #1e2d3a;
    color: #3a4a5a;
}

QPushButton#btn_cancel {
    background-color: #1a2535;
    color: #8090a0;
    border: 1px solid #2a3a4a;
}

QPushButton#btn_cancel:hover {
    background-color: #243040;
    color: #b0c0d0;
}

QListWidget {
    background-color: #111d2a;
    border: 2px solid #1e2e3e;
    border-radius: 8px;
    color: #d0dce8;
    font-size: 13px;
    outline: none;
}

QListWidget::item {
    padding: 10px 14px;
    border-bottom: 1px solid #1a2a3a;
    border-radius: 0px;
}

QListWidget::item:selected {
    background-color: #1e3a5a;
    color: #4db8ff;
    border-left: 3px solid #1e90ff;
}

QListWidget::item:hover:!selected {
    background-color: #172230;
}

QFrame#separator {
    background-color: #1e2e3e;
    max-height: 1px;
}

QLabel#status_label {
    color: #5a7a9a;
    font-size: 12px;
    font-style: italic;
}
"""


class AddFlightDialog(QDialog):
    """Premium dark themed dialog for searching and adding flights."""

    def __init__(self, tracker: FlightTracker, translator: Translator, parent=None):
        super().__init__(parent)
        self.tracker = tracker
        self.translator = translator
        self.selected_flight_id: str = ""
        self.selected_flight_result: dict[str, Any] = {}
        self._search_results_data: list[dict[str, Any]] = []
        self._worker: SearchWorker | None = None
        self._filter_mode: str = "all"  # all, live, schedule

        self.setStyleSheet(DIALOG_STYLE)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setModal(True)
        self.resize(580, 520)
        self._init_ui()
        self._center_on_parent()
        
        # Install event filter to prevent Enter from closing dialog
        self.installEventFilter(self)

    # ------------------------------------------------------------------
    # UI Construction
    # ------------------------------------------------------------------

    def _init_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(16)

        # ── Title bar ──────────────────────────────────────────────────
        title_bar = QHBoxLayout()
        title = QLabel(self.translator.tr("dlg_add_title"))
        title.setObjectName("title_label")
        fnt = title.font()
        fnt.setPointSize(16)
        fnt.setBold(True)
        title.setFont(fnt)

        btn_close_x = QPushButton("✕")
        btn_close_x.setFixedSize(32, 32)
        btn_close_x.setStyleSheet("""
            QPushButton {
                background: transparent; color: #4a5a6a;
                border: none; font-size: 16px; border-radius: 16px;
            }
            QPushButton:hover { background: #1e2e3e; color: #e05050; }
        """)
        btn_close_x.clicked.connect(self.reject)

        title_bar.addWidget(title)
        title_bar.addStretch()
        title_bar.addWidget(btn_close_x)
        root.addLayout(title_bar)

        # ── Separator ─────────────────────────────────────────────────
        sep = QFrame()
        sep.setObjectName("separator")
        sep.setFrameShape(QFrame.Shape.HLine)
        root.addWidget(sep)

        # ── Search row ────────────────────────────────────────────────
        root.addWidget(QLabel(self.translator.tr("label_flight_number")))

        search_row = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(self.translator.tr("search_placeholder"))
        self.search_input.returnPressed.connect(self._do_search)
        self.search_input.installEventFilter(self)

        self.btn_search = QPushButton(self.translator.tr("btn_search"))
        self.btn_search.setObjectName("btn_search")
        self.btn_search.setFixedWidth(110)
        self.btn_search.setAutoDefault(False)
        self.btn_search.setDefault(False)
        self.btn_search.clicked.connect(self._do_search)

        search_row.addWidget(self.search_input)
        search_row.addWidget(self.btn_search)
        root.addLayout(search_row)

        # ── Filter tabs ───────────────────────────────────────────────
        filter_row = QHBoxLayout()
        filter_row.setSpacing(4)
        self._filter_group = QButtonGroup(self)
        for mode, key in [("all", "search_all"), ("live", "search_live_only"), ("schedule", "search_scheduled_only")]:
            btn = QPushButton(self.translator.tr(key))
            btn.setCheckable(True)
            btn.setFixedHeight(28)
            btn.setStyleSheet("""
                QPushButton {
                    background: #1a2535; color: #7c9dbd; border: 1px solid #2a3a4a;
                    border-radius: 6px; font-size: 12px; padding: 4px 14px;
                }
                QPushButton:checked {
                    background: #1e3a5a; color: #4db8ff; border-color: #1e90ff;
                }
                QPushButton:hover:!checked {
                    background: #243040; color: #b0c0d0;
                }
            """)
            btn.clicked.connect(lambda checked, m=mode: self._set_filter(m))
            self._filter_group.addButton(btn)
            filter_row.addWidget(btn)
            if mode == "all":
                btn.setChecked(True)
        filter_row.addStretch()
        root.addLayout(filter_row)

        # ── Status label ──────────────────────────────────────────────
        self.status_label = QLabel("")
        self.status_label.setObjectName("status_label")
        root.addWidget(self.status_label)

        # ── Results list ──────────────────────────────────────────────
        root.addWidget(QLabel(self.translator.tr("label_search_result")))
        self.results_list = QListWidget()
        self.results_list.setMinimumHeight(220)
        self.results_list.itemSelectionChanged.connect(self._on_selection)
        self.results_list.itemDoubleClicked.connect(self._on_double_click)
        root.addWidget(self.results_list)

        # ── Bottom buttons ────────────────────────────────────────────
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        self.btn_add = QPushButton(self.translator.tr("btn_add"))
        self.btn_add.setObjectName("btn_add")
        self.btn_add.setEnabled(False)
        self.btn_add.setFixedWidth(150)
        self.btn_add.setAutoDefault(False)  # Prevent Enter from triggering this button
        self.btn_add.setDefault(False)
        self.btn_add.clicked.connect(self._accept_selected)

        btn_cancel = QPushButton(self.translator.tr("btn_cancel"))
        btn_cancel.setObjectName("btn_cancel")
        btn_cancel.setFixedWidth(100)
        btn_cancel.setAutoDefault(False)  # Prevent Enter from triggering this button
        btn_cancel.setDefault(False)
        btn_cancel.clicked.connect(self.reject)

        btn_row.addWidget(self.btn_add)
        btn_row.addWidget(btn_cancel)
        root.addLayout(btn_row)

    def _center_on_parent(self):
        p = self.parent()
        if p is not None:
            pw = cast(QWidget, p)
            pg = pw.geometry()
            self.move(
                pg.x() + (pg.width() - self.width()) // 2,
                pg.y() + (pg.height() - self.height()) // 2,
            )

    # ------------------------------------------------------------------
    # Drag support for frameless dialog
    # ------------------------------------------------------------------

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and hasattr(self, "_drag_pos"):
            self.move(event.globalPosition().toPoint() - self._drag_pos)

    def eventFilter(self, obj, event):
        """Prevent Enter/Return key from closing dialog."""
        if event.type() == event.Type.KeyPress:
            if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                # Only allow Enter to trigger search in search input
                if obj == self.search_input:
                    self._do_search()
                    return True
                # Block Enter for all other widgets
                return True
        return super().eventFilter(obj, event)

    # ------------------------------------------------------------------
    # Search logic
    # ------------------------------------------------------------------

    def _do_search(self):
        query = self.search_input.text().strip()
        if not query:
            self.status_label.setText(self.translator.tr("msg_enter_flight"))
            return

        self.results_list.clear()
        self._search_results_data = []
        self.selected_flight_id = ""
        self.selected_flight_result = {}
        self.btn_add.setEnabled(False)
        self.btn_search.setEnabled(False)
        self.status_label.setText(self.translator.tr("msg_searching", query))

        # Kill previous worker if any
        if self._worker and self._worker.isRunning():
            self._worker.quit()

        self._worker = SearchWorker(self.tracker, query)
        self._worker.results_ready.connect(self._on_results)
        self._worker.error_occurred.connect(self._on_error)
        self._worker.start()

    def _on_results(self, results: list[dict[str, Any]]):
        self.btn_search.setEnabled(True)

        if not results:
            self.status_label.setText(self.translator.tr("msg_flight_not_found"))
            return

        # Store all results and apply filter
        self._search_results_data = results
        self._apply_filter()

    def _set_filter(self, mode: str):
        """Set filter mode and re-render results."""
        self._filter_mode = mode
        self._apply_filter()

    def _apply_filter(self):
        """Re-render results list respecting current filter."""
        self.results_list.clear()
        self.btn_add.setEnabled(False)
        added = 0
        for flight in self._search_results_data:
            ftype = flight.get("type", "")
            if self._filter_mode == "live" and ftype != "live":
                continue
            if self._filter_mode == "schedule" and ftype not in ("schedule", "scheduled"):
                continue
            added += self._render_flight_item(flight)
        if added == 0 and self._search_results_data:
            self.status_label.setText(self.translator.tr("msg_flight_not_found"))
        elif self._search_results_data:
            self.status_label.setText(f"{'✓'} {added} result{'s' if added != 1 else ''} found")

    def _render_flight_item(self, flight: dict[str, Any]) -> int:
        """Render a single flight into the list widget. Returns 1 if added."""
        try:
            fid   = flight.get("id", "")
            label = flight.get("label", "")
            detail = flight.get("detail") or {}
            if not fid:
                return 0
            if isinstance(detail, dict):
                callsign = detail.get("callsign") or detail.get("flight") or "N/A"
                origin   = detail.get("dep") or detail.get("origin") or "?"
                dest     = detail.get("arr") or detail.get("destination") or "?"
            else:
                callsign, origin, dest = "N/A", "?", "?"
            if not label:
                label = flight.get("name") or callsign
            ftype = flight.get("type", "")
            if ftype == "live":
                badge = self.translator.tr("search_live")
            elif ftype in ("schedule", "scheduled"):
                badge = self.translator.tr("search_scheduled")
            else:
                badge = ""
            display = f"{badge}  {label}  ·  {callsign}  ·  {origin} → {dest}".strip()
            item = QListWidgetItem(display)
            item.setData(Qt.ItemDataRole.UserRole, self._search_results_data.index(flight))
            self.results_list.addItem(item)
            return 1
        except Exception:
            return 0

    def _on_error(self, msg: str):
        self.btn_search.setEnabled(True)
        self.status_label.setText(self.translator.tr("msg_api_error", msg))

    # ------------------------------------------------------------------
    # Selection & accept
    # ------------------------------------------------------------------

    def _on_selection(self):
        items = self.results_list.selectedItems()
        self.btn_add.setEnabled(bool(items))
        if items:
            idx = items[0].data(Qt.ItemDataRole.UserRole)
            self.selected_flight_result = self._search_results_data[idx]
            self.selected_flight_id = self.selected_flight_result.get("id", "")

    def _on_double_click(self, item: QListWidgetItem):
        idx = item.data(Qt.ItemDataRole.UserRole)
        self.selected_flight_result = self._search_results_data[idx]
        self.selected_flight_id = self.selected_flight_result.get("id", "")
        if self.selected_flight_id:
            self.accept()

    def _accept_selected(self):
        if self.selected_flight_id:
            self.accept()

    # ------------------------------------------------------------------
    # Public accessor
    # ------------------------------------------------------------------

    def get_selected_flight_data(self):
        """Return (flight_id, search_result_dict)."""
        return self.selected_flight_id, self.selected_flight_result

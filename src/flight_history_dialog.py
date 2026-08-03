#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Flight History Dialog — "Flight history for <number>" style view.

Shows recent (past/live) and upcoming (scheduled) operations of a flight
number, mirroring FlightRadar24's own flight-history table:
DATE | FROM | TO | AIRCRAFT | FLIGHT TIME | STD | ATD | STA | STATUS

A future scheduled flight (e.g. one departing tomorrow) can be added to the
tracking list ahead of time; MyRadar24 will keep polling it and will
automatically switch to full live tracking (position, ETA, sounds) as soon
as FlightRadar24 assigns it a live flight id.
"""

from datetime import datetime
from typing import Any, List, Optional, cast

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QFrame, QButtonGroup, QWidget, QHeaderView, QAbstractItemView,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QColor, QBrush

from .translations import Translator
from .flight_tracker import FlightTracker
from .flight_history import FlightHistoryEntry


# ======================================================================
# Background history-fetch worker
# ======================================================================

class HistoryWorker(QThread):
    """Fetch flight-number history in a background thread."""
    results_ready = pyqtSignal(list, int)
    error_occurred = pyqtSignal(str)

    def __init__(self, tracker: FlightTracker, query: str, page: int = 1, limit: int = 100):
        super().__init__()
        self.tracker = tracker
        self.query = query
        self.page = page
        self.limit = limit

    def run(self):
        try:
            entries = self.tracker.get_flight_history(self.query, page=self.page, limit=self.limit)
            self.results_ready.emit(entries, self.page)
        except Exception as e:
            self.error_occurred.emit(str(e))


# ======================================================================
# Column layout
# ======================================================================

COL_DATE        = 0
COL_FROM        = 1
COL_TO          = 2
COL_AIRCRAFT    = 3
COL_FLIGHT_TIME = 4
COL_STD         = 5
COL_ATD         = 6
COL_STA         = 7
COL_STATUS      = 8
NUM_H_COLS      = 9


# ======================================================================
# Styling
# ======================================================================

DIALOG_STYLE = """
QDialog {
    background-color: #0f1923;
    color: #e8eaf0;
    border-radius: 12px;
}

QLabel { color: #a8b4c0; font-size: 13px; }
QLabel#title_label { color: #ffffff; font-size: 18px; font-weight: bold; }
QLabel#hint_label { color: #5a6a7a; font-size: 11px; }
QLabel#status_label { color: #5a7a9a; font-size: 12px; font-style: italic; }

QLineEdit {
    background-color: #1a2535;
    border: 2px solid #2a3a4a;
    border-radius: 8px;
    color: #e8eaf0;
    font-size: 14px;
    padding: 10px 14px;
    selection-background-color: #1e6fbf;
}
QLineEdit:focus { border-color: #1e90ff; }

QPushButton {
    border-radius: 8px;
    font-size: 13px;
    font-weight: 600;
    padding: 10px 22px;
    border: none;
}
QPushButton#btn_search {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #1e6fbf, stop:1 #0da5e8);
    color: #ffffff;
}
QPushButton#btn_search:hover {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #2585d9, stop:1 #18b5f5);
}
QPushButton#btn_add {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #0f9960, stop:1 #16c47a);
    color: #ffffff;
}
QPushButton#btn_add:hover {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #14b070, stop:1 #1dd88a);
}
QPushButton#btn_add:disabled { background-color: #1e2d3a; color: #3a4a5a; }
QPushButton#btn_cancel {
    background-color: #1a2535; color: #8090a0; border: 1px solid #2a3a4a;
}
QPushButton#btn_cancel:hover { background-color: #243040; color: #b0c0d0; }
QPushButton#btn_more {
    background-color: #172230; color: #7c9dbd; border: 1px solid #2a3a4a;
    font-weight: 500; padding: 6px 16px;
}
QPushButton#btn_more:hover { background-color: #1e2e3e; color: #b0c0d0; }

QPushButton#filter_btn {
    background: #1a2535; color: #7c9dbd; border: 1px solid #2a3a4a;
    border-radius: 6px; font-size: 12px; padding: 4px 14px;
}
QPushButton#filter_btn:checked {
    background: #1e3a5a; color: #4db8ff; border-color: #1e90ff;
}
QPushButton#filter_btn:hover:!checked { background: #243040; color: #b0c0d0; }

QTableWidget {
    background-color: #111d2a;
    alternate-background-color: #0d1620;
    border: 2px solid #1e2e3e;
    border-radius: 8px;
    color: #d0dce8;
    font-size: 12px;
    gridline-color: #1a2a3a;
    outline: none;
}
QTableWidget::item { padding: 6px; }
QTableWidget::item:selected { background-color: #1e3a5a; color: #4db8ff; }
QHeaderView::section {
    background-color: #16222f;
    color: #7c9dbd;
    padding: 8px 6px;
    border: none;
    border-bottom: 2px solid #243040;
    font-weight: 600;
    font-size: 11px;
}

QFrame#separator { background-color: #1e2e3e; max-height: 1px; }
"""


class FlightHistoryDialog(QDialog):
    """Dialog showing recent + upcoming flights for a flight number."""

    def __init__(
        self,
        tracker: FlightTracker,
        translator: Translator,
        parent=None,
        initial_query: str = "",
    ):
        super().__init__(parent)
        self.tracker = tracker
        self.translator = translator
        self._entries: List[FlightHistoryEntry] = []
        self._filter_mode: str = "all"  # all, upcoming, past
        self._worker: Optional[HistoryWorker] = None
        self._current_page = 1
        self._current_query = ""
        self.selected_entry: Optional[FlightHistoryEntry] = None

        self.setStyleSheet(DIALOG_STYLE)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setModal(True)
        self.resize(920, 620)
        self._init_ui()
        self._center_on_parent()
        self.installEventFilter(self)

        if initial_query:
            self.search_input.setText(initial_query)
            self._do_search()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _init_ui(self):
        t = self.translator
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(14)

        # ── Title bar ────────────────────────────────────────────────
        title_bar = QHBoxLayout()
        title = QLabel(t.tr("dlg_history_title"))
        title.setObjectName("title_label")
        fnt = title.font()
        fnt.setPointSize(16)
        fnt.setBold(True)
        title.setFont(fnt)

        btn_close_x = QPushButton("✕")
        btn_close_x.setFixedSize(32, 32)
        btn_close_x.setStyleSheet("""
            QPushButton { background: transparent; color: #4a5a6a; border: none;
                          font-size: 16px; border-radius: 16px; }
            QPushButton:hover { background: #1e2e3e; color: #e05050; }
        """)
        btn_close_x.clicked.connect(self.reject)

        title_bar.addWidget(title)
        title_bar.addStretch()
        title_bar.addWidget(btn_close_x)
        root.addLayout(title_bar)

        sep = QFrame()
        sep.setObjectName("separator")
        sep.setFrameShape(QFrame.Shape.HLine)
        root.addWidget(sep)

        hint = QLabel(t.tr("history_hint"))
        hint.setObjectName("hint_label")
        hint.setWordWrap(True)
        root.addWidget(hint)

        # ── Search row ───────────────────────────────────────────────
        root.addWidget(QLabel(t.tr("label_flight_number")))
        search_row = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(t.tr("search_placeholder"))
        self.search_input.returnPressed.connect(self._do_search)
        self.search_input.installEventFilter(self)

        self.btn_search = QPushButton(t.tr("btn_search"))
        self.btn_search.setObjectName("btn_search")
        self.btn_search.setFixedWidth(110)
        self.btn_search.setAutoDefault(False)
        self.btn_search.clicked.connect(self._do_search)

        search_row.addWidget(self.search_input)
        search_row.addWidget(self.btn_search)
        root.addLayout(search_row)

        # ── Filter tabs ──────────────────────────────────────────────
        filter_row = QHBoxLayout()
        filter_row.setSpacing(4)
        self._filter_group = QButtonGroup(self)
        for mode, key in [
            ("all", "history_filter_all"),
            ("upcoming", "history_filter_upcoming"),
            ("past", "history_filter_past"),
        ]:
            btn = QPushButton(t.tr(key))
            btn.setObjectName("filter_btn")
            btn.setCheckable(True)
            btn.setFixedHeight(28)
            btn.clicked.connect(lambda checked, m=mode: self._set_filter(m))
            self._filter_group.addButton(btn)
            filter_row.addWidget(btn)
            if mode == "all":
                btn.setChecked(True)
        filter_row.addStretch()
        root.addLayout(filter_row)

        # ── Status label ─────────────────────────────────────────────
        self.status_label = QLabel("")
        self.status_label.setObjectName("status_label")
        root.addWidget(self.status_label)

        # ── Results table ────────────────────────────────────────────
        self.table = QTableWidget(0, NUM_H_COLS)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.setMinimumHeight(300)
        self.table.itemSelectionChanged.connect(self._on_selection)
        self.table.itemDoubleClicked.connect(self._on_double_click)

        headers = [
            t.tr("header_date"), t.tr("header_from"), t.tr("header_to"),
            t.tr("header_aircraft"), t.tr("header_flight_time"),
            t.tr("header_std"), t.tr("header_atd"), t.tr("header_sta"),
            t.tr("header_status"),
        ]
        self.table.setHorizontalHeaderLabels(headers)

        hdr = self.table.horizontalHeader()
        hdr.setStretchLastSection(False)
        col_widths = [130, 65, 65, 130, 90, 70, 70, 70, 160]
        for i, w in enumerate(col_widths):
            self.table.setColumnWidth(i, w)
        hdr.setSectionResizeMode(COL_AIRCRAFT, QHeaderView.ResizeMode.Interactive)
        hdr.setSectionResizeMode(COL_STATUS, QHeaderView.ResizeMode.Stretch)

        root.addWidget(self.table)

        # ── Load more ────────────────────────────────────────────────
        more_row = QHBoxLayout()
        more_row.addStretch()
        self.btn_more = QPushButton(f"⋯  {t.tr('history_filter_past')} +100")
        self.btn_more.setObjectName("btn_more")
        self.btn_more.setAutoDefault(False)
        self.btn_more.setVisible(False)
        self.btn_more.clicked.connect(self._load_more)
        more_row.addWidget(self.btn_more)
        more_row.addStretch()
        root.addLayout(more_row)

        # ── Bottom buttons ───────────────────────────────────────────
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        self.btn_add = QPushButton(t.tr("btn_add_to_tracking"))
        self.btn_add.setObjectName("btn_add")
        self.btn_add.setEnabled(False)
        self.btn_add.setFixedWidth(170)
        self.btn_add.setAutoDefault(False)
        self.btn_add.clicked.connect(self._accept_selected)

        btn_cancel = QPushButton(t.tr("btn_close"))
        btn_cancel.setObjectName("btn_cancel")
        btn_cancel.setFixedWidth(100)
        btn_cancel.setAutoDefault(False)
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
    # Drag support / Enter-key handling for frameless dialog
    # ------------------------------------------------------------------

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and hasattr(self, "_drag_pos"):
            self.move(event.globalPosition().toPoint() - self._drag_pos)

    def eventFilter(self, obj, event):
        if event.type() == event.Type.KeyPress:
            if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                if obj == self.search_input:
                    self._do_search()
                    return True
                return True
        return super().eventFilter(obj, event)

    # ------------------------------------------------------------------
    # Search logic
    # ------------------------------------------------------------------

    def _do_search(self):
        query = self.search_input.text().strip()
        if not query:
            self.status_label.setText(self.translator.tr("msg_enter_flight_number"))
            return

        self._current_query = query
        self._current_page = 1
        self._entries = []
        self.table.setRowCount(0)
        self.selected_entry = None
        self.btn_add.setEnabled(False)
        self.btn_more.setVisible(False)
        self.btn_search.setEnabled(False)
        self.status_label.setText(self.translator.tr("msg_history_searching", query))

        self._start_worker(query, page=1)

    def _load_more(self):
        if not self._current_query:
            return
        self.btn_more.setEnabled(False)
        self._current_page += 1
        self._start_worker(self._current_query, page=self._current_page)

    def _start_worker(self, query: str, page: int):
        if self._worker and self._worker.isRunning():
            self._worker.quit()
        self._worker = HistoryWorker(self.tracker, query, page=page, limit=100)
        self._worker.results_ready.connect(self._on_results)
        self._worker.error_occurred.connect(self._on_error)
        self._worker.start()

    def _on_results(self, entries: List[FlightHistoryEntry], page: int):
        self.btn_search.setEnabled(True)
        self.btn_more.setEnabled(True)

        if page == 1 and not entries:
            self.status_label.setText(self.translator.tr("msg_history_not_found"))
            self.btn_more.setVisible(False)
            return

        self._entries.extend(entries)
        self.btn_more.setVisible(len(entries) >= 100)
        self.status_label.setText(
            self.translator.tr("label_flight_history_for", self._current_query)
            + f"  ·  {len(self._entries)} " + self.translator.tr("history_filter_all").lower()
        )
        self._apply_filter()

    def _on_error(self, msg: str):
        self.btn_search.setEnabled(True)
        self.btn_more.setEnabled(True)
        self.status_label.setText(self.translator.tr("msg_history_error", msg))

    def _set_filter(self, mode: str):
        self._filter_mode = mode
        self._apply_filter()

    # ------------------------------------------------------------------
    # Table rendering
    # ------------------------------------------------------------------

    def _apply_filter(self):
        now = datetime.now().timestamp()
        rows: List[FlightHistoryEntry] = []
        for e in self._entries:
            if self._filter_mode == "upcoming":
                ts = e.scheduled_departure or 0
                if not (ts > now and not e.is_departed()):
                    continue
            elif self._filter_mode == "past":
                if not (e.is_departed() or e.is_landed()):
                    continue
            rows.append(e)

        self.table.setRowCount(len(rows))
        for row, entry in enumerate(rows):
            self._render_row(row, entry)

    def _render_row(self, row: int, entry: FlightHistoryEntry):
        if entry.is_cancelled():
            fg = QColor("#e85959")
        elif entry.is_landed():
            fg = QColor("#7ec98f")
        elif entry.is_live():
            fg = QColor("#4db8ff")
        elif entry.is_pending_schedule():
            fg = QColor("#b790f5")
        else:
            fg = QColor("#c7d3de")

        cells = [
            entry.get_date_display(),
            entry.origin_iata,
            entry.destination_iata,
            entry.get_aircraft_display(),
            entry.get_flight_time_display(),
            entry.get_std_display(),
            entry.get_atd_display() if entry.get_atd_display() != "—" else entry.get_etd_display(),
            entry.get_sta_display(),
            entry.status_text or "—",
        ]
        for col, text in enumerate(cells):
            item = QTableWidgetItem(str(text))
            item.setForeground(QBrush(fg))
            if col in (COL_FROM, COL_TO, COL_FLIGHT_TIME, COL_STD, COL_ATD, COL_STA):
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
            item.setData(Qt.ItemDataRole.UserRole, entry)
            self.table.setItem(row, col, item)

    # ------------------------------------------------------------------
    # Selection & accept
    # ------------------------------------------------------------------

    def _on_selection(self):
        items = self.table.selectedItems()
        if items:
            entry = items[0].data(Qt.ItemDataRole.UserRole)
            self.selected_entry = entry
            self.btn_add.setEnabled(True)
        else:
            self.selected_entry = None
            self.btn_add.setEnabled(False)

    def _on_double_click(self, item: QTableWidgetItem):
        entry = item.data(Qt.ItemDataRole.UserRole)
        if entry:
            self.selected_entry = entry
            self.accept()

    def _accept_selected(self):
        if self.selected_entry:
            self.accept()

    # ------------------------------------------------------------------
    # Public accessor
    # ------------------------------------------------------------------

    def get_selected_entry(self) -> Optional[FlightHistoryEntry]:
        return self.selected_entry

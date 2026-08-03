#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MyRadar24 — Main Window
Premium dark-themed PyQt6 flight tracking application.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QLabel, QStatusBar, QDialog,
    QCheckBox, QComboBox, QFrame, QFileDialog, QSystemTrayIcon,
    QMenu, QAbstractItemView, QToolBar
)
from PyQt6.QtCore import QTimer, Qt, QSize, QThread, pyqtSignal
from PyQt6.QtGui import (
    QAction, QColor, QFont, QIcon, QPixmap, QBrush, QPainter,
    QLinearGradient, QCloseEvent
)
from PyQt6.QtWidgets import QApplication

from .translations import Translator
from .flight_tracker import FlightTracker, TrackedFlight
from .flight_history import FlightHistoryEntry
from .sound_manager import SoundManager
from .add_flight_dialog import AddFlightDialog
from .flight_history_dialog import FlightHistoryDialog
from .toast_notification import ToastManager


# ======================================================================
# Colour palette
# ======================================================================

C = {
    "bg":           "#0a1626",
    "surface":      "#0e1f33",
    "card":         "#132842",
    "border":       "#1b314a",
    "border_light": "#243d5a",
    "accent":       "#228be6",
    "accent2":      "#15aabf",
    "green":        "#20c05c",
    "green_dim":    "#0d7a3a",
    "amber":        "#f59f00",
    "amber_dim":    "#9c6700",
    "red":          "#e85959",
    "text":         "#e3edf6",
    "text_dim":     "#7c9dbd",
    "text_muted":   "#3b5270",
    "row_even":     "#0e1f33",
    "row_odd":      "#0a1726",
    "row_inflight": "#0a1e36",
    "row_landed":   "#051e10",
    "row_hover":    "#162e48",
    "selected":     "#1b3f66",
    "purple":       "#9775fa",
    "row_scheduled": "#140f26",
}


# ======================================================================
# Background update worker
# ======================================================================

class UpdateWorker(QThread):
    """Run flight updates in background; emit results when done."""
    updates_ready: pyqtSignal = pyqtSignal(dict)
    tracker: FlightTracker
    mode: str

    def __init__(self, tracker: FlightTracker, mode: str = "all") -> None:
        super().__init__()
        self.tracker = tracker
        self.mode = mode

    def run(self) -> None:  # type: ignore[override]
        if self.mode == "not_departed":
            changes = self.tracker.update_not_departed()
        else:
            changes = self.tracker.update_all()
        self.updates_ready.emit(changes)


# ======================================================================
# Settings Dialog
# ======================================================================

class SettingsDialog(QDialog):
    translator: Translator
    sound_manager: SoundManager
    _refresh_interval: int
    chk_sound: QCheckBox
    cmb_refresh: QComboBox

    def __init__(self, translator: Translator, sound_manager: SoundManager,
                 refresh_interval: int, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.translator = translator
        self.sound_manager = sound_manager
        self._refresh_interval = refresh_interval

        self.setWindowTitle(self.translator.tr("dlg_settings_title"))
        self.setFixedSize(380, 280)
        self.setStyleSheet(f"""
            QDialog {{ background:{C['surface']}; color:{C['text']}; border-radius:10px; }}
            QLabel  {{ color:{C['text']}; font-size:13px; }}
            QLabel#section {{ color:{C['accent']}; font-size:11px; font-weight:bold;
                              text-transform:uppercase; letter-spacing:1px; margin-top:8px; }}
            QCheckBox {{ color:{C['text']}; font-size:13px; spacing:8px; }}
            QCheckBox::indicator {{
                width:18px; height:18px; border-radius:4px;
                border:2px solid {C['border_light']};
                background:{C['card']};
            }}
            QCheckBox::indicator:checked {{
                background:{C['accent']};
                border-color:{C['accent']};
            }}
            QComboBox {{
                background:{C['card']}; color:{C['text']}; border:2px solid {C['border']};
                border-radius:6px; padding:6px 10px; font-size:13px;
            }}
            QComboBox::drop-down {{ border:none; width:24px; }}
            QComboBox QAbstractItemView {{
                background:{C['surface']}; color:{C['text']}; border:1px solid {C['border']};
                selection-background-color:{C['selected']};
            }}
            QPushButton {{
                background:{C['accent']}; color:#fff; border:none;
                border-radius:7px; padding:8px 20px; font-size:13px; font-weight:600;
            }}
            QPushButton:hover {{ background:{C['accent2']}; }}
            QPushButton#cancel {{
                background:{C['card']}; color:{C['text_dim']}; border:1px solid {C['border']};
            }}
            QPushButton#cancel:hover {{ background:{C['border']}; }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)

        title = QLabel(self.translator.tr("dlg_settings_title"))
        title.setFont(QFont("", 15, QFont.Weight.Bold))
        layout.addWidget(title)

        sep = QFrame(); sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"background:{C['border']}; max-height:1px;")
        layout.addWidget(sep)

        # Sound
        sound_sec = QLabel(self.translator.tr("label_sound"))
        sound_sec.setObjectName("section")
        layout.addWidget(sound_sec)

        self.chk_sound = QCheckBox(self.translator.tr("settings_sound_enabled"))
        self.chk_sound.setChecked(sound_manager.enabled)
        layout.addWidget(self.chk_sound)

        # Refresh
        refresh_sec = QLabel(self.translator.tr("label_refresh_interval"))
        refresh_sec.setObjectName("section")
        layout.addWidget(refresh_sec)

        self.cmb_refresh = QComboBox()
        self.cmb_refresh.addItem(self.translator.tr("settings_refresh_5"),   5)
        self.cmb_refresh.addItem(self.translator.tr("settings_refresh_30"),  30)
        self.cmb_refresh.addItem(self.translator.tr("settings_refresh_60"),  60)
        self.cmb_refresh.addItem(self.translator.tr("settings_refresh_120"), 120)
        # Select current
        idx = self.cmb_refresh.findData(refresh_interval)
        if idx >= 0:
            self.cmb_refresh.setCurrentIndex(idx)
        else:
            # Fallback: if saved interval not in list, select 5 second default
            self.cmb_refresh.setCurrentIndex(0)
        layout.addWidget(self.cmb_refresh)

        layout.addStretch()

        # Buttons
        btns = QHBoxLayout()
        btns.addStretch()
        btn_ok = QPushButton(self.translator.tr("btn_save"))
        btn_ok.clicked.connect(self.accept)
        btn_cancel = QPushButton(self.translator.tr("btn_cancel"))
        btn_cancel.setObjectName("cancel")
        btn_cancel.clicked.connect(self.reject)
        btns.addWidget(btn_ok)
        btns.addWidget(btn_cancel)
        layout.addLayout(btns)

    @property
    def sound_enabled(self) -> bool:
        return self.chk_sound.isChecked()

    @property
    def refresh_interval(self) -> int:
        return int(self.cmb_refresh.currentData())


# ======================================================================
# Main Window stylesheet
# ======================================================================

MAIN_STYLE = f"""
QMainWindow, QWidget {{
    background-color: {C['bg']};
    color: {C['text']};
    font-family: 'Segoe UI', 'Arial', sans-serif;
    font-size: 12px;
}}

/* ── Toolbar ── */
QToolBar {{
    background-color: {C['surface']};
    border-bottom: 2px solid {C['accent']};
    spacing: 4px;
    padding: 4px 10px;
}}

QToolBar QToolButton {{
    background: transparent;
    color: {C['text_dim']};
    border: 1px solid transparent;
    border-radius: 6px;
    padding: 6px 12px;
    font-size: 13px;
    font-weight: 500;
}}

QToolBar QToolButton:hover {{
    background-color: {C['card']};
    color: {C['text']};
    border-color: {C['border_light']};
}}

QToolBar QToolButton:pressed {{
    background-color: {C['border']};
}}

QToolBar::separator {{
    background: {C['border']};
    width: 1px;
    margin: 8px 6px;
}}

/* ── Menu bar ── */
QMenuBar {{
    background-color: {C['surface']};
    color: {C['text']};
    border-bottom: 1px solid {C['border']};
    padding: 2px 6px;
    font-size: 13px;
}}

QMenuBar::item:selected {{
    background-color: {C['card']};
    border-radius: 5px;
    color: {C['accent']};
}}

QMenu {{
    background-color: {C['card']};
    color: {C['text']};
    border: 1px solid {C['border_light']};
    border-radius: 8px;
    padding: 6px 4px;
}}

QMenu::item {{
    padding: 8px 24px 8px 14px;
    border-radius: 5px;
    font-size: 13px;
}}

QMenu::item:selected {{
    background-color: {C['selected']};
    color: {C['accent']};
}}

QMenu::separator {{
    background: {C['border']};
    height: 1px;
    margin: 4px 8px;
}}

/* ── Status bar ── */
QStatusBar {{
    background-color: {C['surface']};
    color: {C['text_dim']};
    border-top: 1px solid {C['border']};
    font-size: 12px;
    padding: 4px 12px;
}}

QStatusBar QLabel {{
    padding: 2px 8px;
    color: {C['text_dim']};
}}

/* ── Table ── */
QTableWidget {{
    background-color: {C['bg']};
    alternate-background-color: {C['row_odd']};
    gridline-color: {C['border']};
    border: none;
    color: {C['text']};
    selection-background-color: {C['selected']};
    selection-color: #ffffff;
    outline: none;
}}

QTableWidget::item {{
    padding: 4px 10px;
    border-bottom: 1px solid {C['border']};
}}

QTableWidget::item:selected {{
    background-color: {C['selected']};
    color: #ffffff;
}}

QHeaderView::section {{
    background-color: {C['card']};
    color: {C['text']};
    border: none;
    border-bottom: 2px solid {C['accent']};
    border-right: 1px solid {C['border']};
    padding: 8px 8px;
    font-size: 11px;
    font-weight: 600;
}}

QHeaderView::section:last {{
    border-right: none;
}}

QScrollBar:vertical {{
    background: {C['surface']};
    width: 10px;
    border-radius: 5px;
}}

QScrollBar::handle:vertical {{
    background: {C['border_light']};
    border-radius: 5px;
    min-height: 30px;
}}

QScrollBar::handle:vertical:hover {{
    background: {C['accent']};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}

QScrollBar:horizontal {{
    background: {C['surface']};
    height: 10px;
    border-radius: 5px;
}}

QScrollBar::handle:horizontal {{
    background: {C['border_light']};
    border-radius: 5px;
    min-width: 30px;
}}

QScrollBar::handle:horizontal:hover {{
    background: {C['accent']};
}}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0px;
}}

/* ── Buttons ── */
QPushButton {{
    border-radius: 7px;
    font-size: 13px;
    font-weight: 600;
    padding: 9px 20px;
    border: none;
}}

QPushButton#btn_add_flight {{
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
        stop:0 {C['accent']}, stop:1 {C['accent2']});
    color: #ffffff;
}}

QPushButton#btn_add_flight:hover {{
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
        stop:0 #339af0, stop:1 #1dc8d9);
}}

QPushButton#btn_remove {{
    background-color: #2a1520;
    color: {C['red']};
    border: 1px solid #3a2030;
}}

QPushButton#btn_remove:hover {{
    background-color: #3a2030;
    border-color: {C['red']};
}}

QPushButton#btn_refresh {{
    background-color: {C['card']};
    color: {C['text_dim']};
    border: 1px solid {C['border']};
}}

QPushButton#btn_refresh:hover {{
    background-color: {C['border']};
    color: {C['text']};
}}

/* ── Empty state label ── */
QLabel#empty_label {{
    color: {C['text_muted']};
    font-size: 16px;
}}
"""


# ======================================================================
# Column indices
# ======================================================================

COL_FLIGHT   = 0
COL_NOTE     = 1
COL_FROM     = 2
COL_TO       = 3
COL_AIRCRAFT = 4
COL_DEP      = 5
COL_DEP_DATE = 6
COL_ARR      = 7
COL_ARR_DATE = 8
COL_STATUS   = 9
COL_ETA      = 10
COL_REAL_LANDED = 11
COL_LANDED_SINCE = 12
COL_ALT      = 13
COL_SPEED    = 14
NUM_COLS     = 15


# ======================================================================
# Main Window
# ======================================================================

class MainWindow(QMainWindow):
    """MyRadar24 premium main window."""

    # Settings persistence file
    _SETTINGS_FILE: Path = Path(__file__).parent.parent / "myradar24_settings.json"

    # ── Core components ──────────────────────────────────────────────
    translator: Translator
    flight_tracker: FlightTracker
    sound_manager: SoundManager

    # ── Runtime state ────────────────────────────────────────────────
    _refresh_interval: int
    _update_worker: UpdateWorker | None
    _nd_worker: UpdateWorker | None
    _is_editing: bool
    _update_pending: bool

    # ── Timers ───────────────────────────────────────────────
    _timer_all: QTimer
    _timer_nd: QTimer
    _timer_display: QTimer
    _blink_timer: QTimer
    _blink_on: bool
    _toast_manager: ToastManager

    # ── Menu bar widgets ─────────────────────────────────────────────
    _menu_file: QMenu | None
    _act_exit: QAction
    _menu_flight: QMenu | None
    _act_menu_add: QAction
    _act_menu_history: QAction
    _lang_menu: QMenu | None
    _menu_settings: QMenu | None
    _act_settings: QAction
    _menu_help: QMenu | None
    _act_github: QAction
    _act_copy_url: QAction
    _act_about: QAction
    _act_import_lang: QAction

    # ── Toolbar widgets ──────────────────────────────────────────────
    _toolbar: QToolBar
    _act_tb_add: QAction
    _act_tb_history: QAction
    _act_tb_remove: QAction
    _act_tb_remove_all: QAction
    _act_tb_move_up: QAction
    _act_tb_move_down: QAction
    _act_tb_refresh: QAction
    _act_tb_settings: QAction

    # ── Central widgets ──────────────────────────────────────────────
    _empty_label: QLabel
    table: QTableWidget

    # ── Status bar widgets ───────────────────────────────────────────
    _lbl_count: QLabel
    _lbl_update: QLabel

    # ── System tray ──────────────────────────────────────────────────
    _tray: QSystemTrayIcon | None

    def __init__(self) -> None:
        super().__init__()

        # Core components
        self.translator    = Translator("en")
        self.flight_tracker = FlightTracker()
        self.sound_manager  = SoundManager()

        # Runtime state
        self._refresh_interval = 5   # seconds - Update ALL flights every 5 seconds
        self._update_worker = None
        self._nd_worker = None   # not-departed worker
        self._is_editing = False  # Track if user is currently editing a cell
        self._update_pending = False  # True if a timer fired while worker was busy
        self._blink_on = False  # Toggle state for delay-alert row blinking

        # Load persisted settings
        self._load_settings()

        # Build UI
        self._init_ui()
        self._apply_language_to_ui()

        # Compact in-app notifications (bottom-right corner, non-blocking)
        self._toast_manager = ToastManager(self)

        # Timers
        self._timer_all = QTimer(self)
        self._timer_all.timeout.connect(self._trigger_update_all)
        self._timer_all.start(self._refresh_interval * 1000)

        self._timer_nd = QTimer(self)
        self._timer_nd.timeout.connect(self._trigger_update_not_departed)
        # Offset by 2.5s so it doesn't fire simultaneously with _timer_all
        self._timer_nd.start(int(self._refresh_interval * 1000 / 2))   # half interval offset

        self._timer_display = QTimer(self)
        self._timer_display.timeout.connect(self._refresh_eta_display)
        self._timer_display.start(1_000)  # every second

        self._blink_timer = QTimer(self)
        self._blink_timer.timeout.connect(self._apply_blink_highlights)
        self._blink_timer.start(500)  # early/late alert row blinking

        # System tray
        self._init_tray()

    # ==================================================================
    # UI construction
    # ==================================================================

    def _init_ui(self):
        self.setMinimumSize(1200, 600)
        self.resize(1800, 800)
        self.setStyleSheet(MAIN_STYLE)
        
        # Set window icon
        logo_path = Path(__file__).parent.parent / "logo.png"
        if logo_path.exists():
            self.setWindowIcon(QIcon(str(logo_path)))
        
        self._build_menubar()
        self._build_toolbar()
        self._build_central()
        self._build_statusbar()

    def _build_menubar(self):
        mb = self.menuBar()
        t = self.translator

        # ── File ──────────────────────────────────────────────────────
        file_menu = mb.addMenu(t.tr("menu_file"))
        assert file_menu is not None
        self._menu_file = file_menu

        act_exit = QAction(t.tr("menu_exit"), self)
        act_exit.setShortcut("Ctrl+Q")
        act_exit.triggered.connect(self.close)
        file_menu.addAction(act_exit)
        self._act_exit = act_exit

        # ── Flight ──────────────────────────────────────────────
        flight_menu = mb.addMenu(t.tr("menu_flight"))
        assert flight_menu is not None
        self._menu_flight = flight_menu

        act_add = QAction(t.tr("toolbar_add"), self)
        act_add.setShortcut("Ctrl+N")
        act_add.triggered.connect(self._show_add_dialog)
        flight_menu.addAction(act_add)
        self._act_menu_add = act_add

        act_history = QAction(t.tr("toolbar_history"), self)
        act_history.setShortcut("Ctrl+H")
        act_history.triggered.connect(lambda: self._show_history_dialog())
        flight_menu.addAction(act_history)
        self._act_menu_history = act_history

        # ── Language ──────────────────────────────────────────────────
        self._lang_menu = mb.addMenu(t.tr("menu_language"))
        assert self._lang_menu is not None
        self._rebuild_language_menu()

        # ── Settings ──────────────────────────────────────────────────
        settings_menu = mb.addMenu(t.tr("menu_settings"))
        assert settings_menu is not None
        self._menu_settings = settings_menu

        act_settings = QAction(t.tr("menu_settings") + "\u2026", self)
        act_settings.triggered.connect(self._show_settings)
        settings_menu.addAction(act_settings)
        self._act_settings = act_settings

        # ── Help ──────────────────────────────────────────────────────
        help_menu = mb.addMenu(t.tr("menu_help"))
        assert help_menu is not None
        self._menu_help = help_menu

        act_github = QAction(t.tr("menu_github"), self)
        act_github.triggered.connect(self._open_github)
        help_menu.addAction(act_github)
        self._act_github = act_github

        act_copy_url = QAction(t.tr("menu_copy_url"), self)
        act_copy_url.triggered.connect(self._copy_github_url)
        help_menu.addAction(act_copy_url)
        self._act_copy_url = act_copy_url

        help_menu.addSeparator()

        act_about = QAction(t.tr("menu_about"), self)
        act_about.triggered.connect(self._show_about)
        help_menu.addAction(act_about)
        self._act_about = act_about

    def _rebuild_language_menu(self):
        """Populate language menu from locales/ directory + import option."""
        self._lang_menu.clear()

        languages = self.translator.get_available_languages()
        for code, name in languages.items():
            act = QAction(name, self)
            act.setData(code)
            act.triggered.connect(lambda checked, c=code: self._change_language(c))
            if code == self.translator.get_current_language():
                act.setCheckable(True)
                act.setChecked(True)
            self._lang_menu.addAction(act)

        self._lang_menu.addSeparator()

        act_import = QAction(self.translator.tr("menu_import_language"), self)
        act_import.triggered.connect(self._import_language)
        self._lang_menu.addAction(act_import)
        self._act_import_lang = act_import

    def _build_toolbar(self):
        tb = QToolBar("Main Toolbar")
        tb.setMovable(False)
        tb.setIconSize(QSize(20, 20))
        tb.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.addToolBar(tb)
        self._toolbar = tb

        # ── Add flight ────────────────────────────────────────────────
        self._act_tb_add = QAction("✈  Add Flight", self)
        self._act_tb_add.triggered.connect(self._show_add_dialog)
        tb.addAction(self._act_tb_add)

        # ── Flight history ────────────────────────────────────────────
        self._act_tb_history = QAction("🕓  Flight History", self)
        self._act_tb_history.triggered.connect(self._show_history_dialog)
        tb.addAction(self._act_tb_history)

        # ── Remove ────────────────────────────────────────────────────
        self._act_tb_remove = QAction("✕  Remove", self)
        self._act_tb_remove.triggered.connect(self._remove_selected)
        tb.addAction(self._act_tb_remove)

        # ── Remove All ────────────────────────────────────────────────
        self._act_tb_remove_all = QAction("🗑  Remove All", self)
        self._act_tb_remove_all.triggered.connect(self._remove_all_flights)
        tb.addAction(self._act_tb_remove_all)

        tb.addSeparator()

        # ── Move Up ───────────────────────────────────────────────────
        self._act_tb_move_up = QAction("↑  Move Up", self)
        self._act_tb_move_up.triggered.connect(self._move_row_up)
        tb.addAction(self._act_tb_move_up)

        # ── Move Down ─────────────────────────────────────────────────
        self._act_tb_move_down = QAction("↓  Move Down", self)
        self._act_tb_move_down.triggered.connect(self._move_row_down)
        tb.addAction(self._act_tb_move_down)

        tb.addSeparator()

        # ── Refresh ───────────────────────────────────────────────────
        self._act_tb_refresh = QAction("⟳  Refresh All", self)
        self._act_tb_refresh.triggered.connect(self._trigger_update_all)
        tb.addAction(self._act_tb_refresh)

        tb.addSeparator()

        # ── Settings ──────────────────────────────────────────────────
        self._act_tb_settings = QAction("⚙  Settings", self)
        self._act_tb_settings.triggered.connect(self._show_settings)
        tb.addAction(self._act_tb_settings)

    def _build_central(self):
        central = QWidget()
        self.setCentralWidget(central)
        vlay = QVBoxLayout(central)
        vlay.setContentsMargins(0, 0, 0, 0)
        vlay.setSpacing(0)

        # ── Empty state overlay ───────────────────────────────────────
        self._empty_label = QLabel(self.translator.tr("label_no_flights"))
        self._empty_label.setObjectName("empty_label")
        self._empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_label.setVisible(True)
        vlay.addWidget(self._empty_label)

        # ── Table ─────────────────────────────────────────────────────
        self.table = QTableWidget(0, NUM_COLS)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.DoubleClicked | QAbstractItemView.EditTrigger.EditKeyPressed)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(True)
        self.table.setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(60)

        # Enable scroll bars
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.table.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.table.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)

        # Right-click context menu
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._on_context_menu)

        # Connect signals
        self.table.itemChanged.connect(self._on_table_item_changed)
        self.table.itemDoubleClicked.connect(self._on_item_double_clicked)
        self.table.itemClicked.connect(self._on_item_clicked)

        hdr = self.table.horizontalHeader()
        hdr.setStretchLastSection(False)
        hdr.setMinimumSectionSize(60)
        # Column widths — calibrated for 1800px window, no truncation
        col_widths = [130, 115, 85, 85, 170, 70, 155, 70, 155, 125, 175, 110, 120, 80, 75]
        for i, w in enumerate(col_widths):
            self.table.setColumnWidth(i, w)
        # Fixed-size columns
        hdr.setSectionResizeMode(COL_FROM, QHeaderView.ResizeMode.Fixed)
        hdr.setSectionResizeMode(COL_TO,   QHeaderView.ResizeMode.Fixed)
        hdr.setSectionResizeMode(COL_DEP,  QHeaderView.ResizeMode.Fixed)
        hdr.setSectionResizeMode(COL_ARR,  QHeaderView.ResizeMode.Fixed)
        hdr.setSectionResizeMode(COL_ALT,  QHeaderView.ResizeMode.Fixed)
        hdr.setSectionResizeMode(COL_SPEED,QHeaderView.ResizeMode.Fixed)
        # Interactive columns (user can resize)
        hdr.setSectionResizeMode(COL_FLIGHT, QHeaderView.ResizeMode.Interactive)
        hdr.setSectionResizeMode(COL_AIRCRAFT, QHeaderView.ResizeMode.Interactive)
        hdr.setSectionResizeMode(COL_DEP_DATE, QHeaderView.ResizeMode.Interactive)
        hdr.setSectionResizeMode(COL_ARR_DATE, QHeaderView.ResizeMode.Interactive)
        hdr.setSectionResizeMode(COL_REAL_LANDED, QHeaderView.ResizeMode.Interactive)
        hdr.setSectionResizeMode(COL_LANDED_SINCE, QHeaderView.ResizeMode.Interactive)
        # Stretch columns (fill remaining space)
        hdr.setSectionResizeMode(COL_STATUS,   QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(COL_NOTE,     QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(COL_ETA,      QHeaderView.ResizeMode.Stretch)

        self._set_table_headers()
        vlay.addWidget(self.table)

    def _set_table_headers(self):
        t = self.translator
        headers = [
            t.tr("header_flight"),
            t.tr("header_note"),
            t.tr("header_from"),
            t.tr("header_to"),
            t.tr("header_aircraft"),
            t.tr("header_departure"),
            t.tr("header_dep_date"),
            t.tr("header_arrival"),
            t.tr("header_arr_date"),
            t.tr("header_status"),
            t.tr("header_eta"),
            t.tr("header_real_landed"),
            t.tr("header_landed_since"),
            t.tr("header_altitude"),
            t.tr("header_speed"),
        ]
        self.table.setHorizontalHeaderLabels(headers)

    def _build_statusbar(self):
        sb = QStatusBar()
        self.setStatusBar(sb)
        self._lbl_count = QLabel(self.translator.tr("label_tracking", 0))
        self._lbl_update = QLabel(self.translator.tr("label_last_update", "—"))
        sb.addWidget(self._lbl_count)
        sb.addPermanentWidget(self._lbl_update)

    def _init_tray(self):
        """Create system tray icon (best-effort)."""
        try:
            if not QSystemTrayIcon.isSystemTrayAvailable():
                return

            # Use app logo if available, otherwise create a simple icon
            logo_path = Path(__file__).parent.parent / "logo.png"
            if logo_path.exists():
                icon = QIcon(str(logo_path))
            else:
                # Create a simple coloured icon programmatically
                pix = QPixmap(32, 32)
                pix.fill(QColor("transparent"))
                p = QPainter(pix)
                p.setRenderHint(QPainter.RenderHint.Antialiasing)
                grad = QLinearGradient(0, 0, 32, 32)
                grad.setColorAt(0, QColor(C["accent"]))
                grad.setColorAt(1, QColor(C["green"]))
                p.setBrush(grad)
                p.setPen(Qt.PenStyle.NoPen)
                p.drawEllipse(2, 2, 28, 28)
                p.setPen(QColor("white"))
                p.setFont(QFont("Arial", 14, QFont.Weight.Bold))
                p.drawText(pix.rect(), Qt.AlignmentFlag.AlignCenter, "✈")
                p.end()
                icon = QIcon(pix)

            self._tray = QSystemTrayIcon(icon, self)
            tray_menu = QMenu()
            act_show = QAction(self.translator.tr("tray_show"), self)
            act_show.triggered.connect(self.show)
            act_exit = QAction(self.translator.tr("tray_exit"), self)
            act_exit.triggered.connect(self.close)
            tray_menu.addAction(act_show)
            tray_menu.addSeparator()
            tray_menu.addAction(act_exit)
            self._tray.setContextMenu(tray_menu)
            self._tray.setToolTip("MyRadar24")
            self._tray.activated.connect(
                lambda reason: self.show() if reason == QSystemTrayIcon.ActivationReason.Trigger else None
            )
            self._tray.show()
        except Exception:
            pass

    # ==================================================================
    # Language
    # ==================================================================

    def _change_language(self, code: str):
        self.translator.set_language(code)
        self._apply_language_to_ui()
        self._rebuild_language_menu()
        self._save_settings()

    def _apply_language_to_ui(self):
        t = self.translator
        self.setWindowTitle(t.tr("app_title"))

        # Menubar text
        self._menu_file.setTitle(t.tr("menu_file"))
        self._act_exit.setText(t.tr("menu_exit"))
        self._menu_flight.setTitle(t.tr("menu_flight"))
        self._act_menu_add.setText(t.tr("toolbar_add"))
        self._act_menu_history.setText(t.tr("toolbar_history"))
        self._lang_menu.setTitle(t.tr("menu_language"))
        self._menu_settings.setTitle(t.tr("menu_settings"))
        self._act_settings.setText(t.tr("menu_settings") + "…")
        self._menu_help.setTitle(t.tr("menu_help"))
        self._act_github.setText(t.tr("menu_github"))
        self._act_copy_url.setText(t.tr("menu_copy_url"))
        self._act_about.setText(t.tr("menu_about"))

        # Toolbar actions
        self._act_tb_add.setText(f"✈  {t.tr('toolbar_add')}")
        self._act_tb_history.setText(f"🕓  {t.tr('toolbar_history')}")
        self._act_tb_remove.setText(f"✕  {t.tr('toolbar_remove')}")
        self._act_tb_remove_all.setText(f"🗑  {t.tr('toolbar_remove_all')}")
        self._act_tb_move_up.setText(f"↑  {t.tr('toolbar_move_up')}")
        self._act_tb_move_down.setText(f"↓  {t.tr('toolbar_move_down')}")
        self._act_tb_refresh.setText(f"⟳  {t.tr('toolbar_refresh')}")
        self._act_tb_settings.setText(f"⚙  {t.tr('toolbar_settings')}")

        # Table headers
        self._set_table_headers()

        # Empty label
        self._empty_label.setText(t.tr("label_no_flights"))

        # Status bar
        n = len(self.flight_tracker.get_all_tracked())
        self._lbl_count.setText(t.tr("label_tracking", n))

        # Full table repaint
        self._repopulate_table()

    def _import_language(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            self.translator.tr("dlg_import_lang_title"),
            "",
            self.translator.tr("dlg_import_lang_filter"),
        )
        if not path:
            return

        ok, result = self.translator.import_language(path)
        if ok:
            QMessageBox.information(
                self,
                self.translator.tr("info_title"),
                self.translator.tr("msg_language_imported", result),
            )
            self._rebuild_language_menu()
        else:
            QMessageBox.warning(
                self,
                self.translator.tr("warning_title"),
                self.translator.tr("msg_language_import_error", result),
            )

    # ==================================================================
    # Add / Remove flights
    # ==================================================================

    def _show_add_dialog(self):
        self.sound_manager.play_button()
        dlg = AddFlightDialog(self.flight_tracker, self.translator, self)
        if dlg.exec():
            fid, result = dlg.get_selected_flight_data()
            if fid:
                self._add_flight(fid, result)

    def _show_history_dialog(self, initial_query: str = ""):
        """Open the Flight History dialog (recent + upcoming/scheduled flights)."""
        self.sound_manager.play_button()
        dlg = FlightHistoryDialog(self.flight_tracker, self.translator, self, initial_query=initial_query)
        if dlg.exec():
            entry = dlg.get_selected_entry()
            if entry:
                self._add_flight_from_history(entry)

    def _add_flight_from_history(self, entry: FlightHistoryEntry):
        """Add a flight-history entry (past, live, or future scheduled) to tracking."""
        t = self.translator

        # Duplicate check — works for both resolved and pending-schedule ids.
        if entry.flight_id and entry.flight_id in self.flight_tracker.tracked_flights:
            tracked = self.flight_tracker.tracked_flights[entry.flight_id]
            QMessageBox.information(self, t.tr("info_title"), t.tr("msg_flight_exists", tracked.display_name()))
            return
        if not entry.flight_id:
            tracking_id = self.flight_tracker.make_schedule_tracking_id(entry.flight_number, entry.row_id)
            if tracking_id in self.flight_tracker.tracked_flights:
                tracked = self.flight_tracker.tracked_flights[tracking_id]
                QMessageBox.information(self, t.tr("info_title"), t.tr("msg_flight_exists", tracked.display_name()))
                return

        tracked = self.flight_tracker.add_scheduled_flight(entry)
        if tracked:
            self.sound_manager.play_add()
            if tracked.is_pending_schedule:
                QMessageBox.information(self, t.tr("info_title"), t.tr("msg_schedule_flight_added", tracked.display_name()))
            else:
                QMessageBox.information(self, t.tr("info_title"), t.tr("msg_flight_added", tracked.display_name()))
            self._repopulate_table()
            self._update_status()
            self._save_settings()
        else:
            QMessageBox.warning(self, t.tr("warning_title"), t.tr("msg_flight_not_found"))

    def _add_flight(self, fid: str, search_result: dict[str, Any] | None = None):
        t = self.translator

        # Duplicate check
        if fid in self.flight_tracker.tracked_flights:
            tracked = self.flight_tracker.tracked_flights[fid]
            QMessageBox.information(
                self,
                t.tr("info_title"),
                t.tr("msg_flight_exists", tracked.display_name()),
            )
            return

        tracked = self.flight_tracker.add_flight(fid, search_result)
        if tracked:
            self.sound_manager.play_add()
            QMessageBox.information(
                self,
                t.tr("info_title"),
                t.tr("msg_flight_added", tracked.display_name()),
            )
            self._repopulate_table()
            self._update_status()
        else:
            QMessageBox.warning(
                self,
                t.tr("warning_title"),
                t.tr("msg_flight_not_found"),
            )

    def _remove_selected(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(
                self,
                self.translator.tr("warning_title"),
                self.translator.tr("msg_no_flight_selected"),
            )
            return

        fids = list(self.flight_tracker.get_all_tracked().keys())
        if row < len(fids):
            fid = fids[row]
            tracked = self.flight_tracker.tracked_flights[fid]
            name = tracked.display_name()
            reply = QMessageBox.question(
                self,
                self.translator.tr("confirm_title"),
                self.translator.tr("msg_remove_confirm", name),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.sound_manager.play_remove()
                self.flight_tracker.remove_flight(fid)
                self._repopulate_table()
                self._update_status()
                self._save_settings()
    
    def _remove_all_flights(self):
        """Remove all tracked flights with double confirmation."""
        flights = self.flight_tracker.get_all_tracked()
        if not flights:
            QMessageBox.information(
                self,
                self.translator.tr("info_title"),
                self.translator.tr("msg_no_flights_to_remove"),
            )
            return
        
        # First confirmation
        reply1 = QMessageBox.question(
            self,
            self.translator.tr("confirm_title"),
            self.translator.tr("msg_remove_all_confirm_1", len(flights)),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        
        if reply1 != QMessageBox.StandardButton.Yes:
            return
        
        # Second confirmation (Are you sure?)
        reply2 = QMessageBox.warning(
            self,
            self.translator.tr("confirm_title"),
            self.translator.tr("msg_remove_all_confirm_2"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        
        if reply2 == QMessageBox.StandardButton.Yes:
            # Remove all flights
            for fid in list(flights.keys()):
                self.flight_tracker.remove_flight(fid)
            
            self.sound_manager.play_remove()
            self._repopulate_table()
            self._update_status()
            self._save_settings()
            
            QMessageBox.information(
                self,
                self.translator.tr("info_title"),
                self.translator.tr("msg_all_flights_removed"),
            )

    # ==================================================================
    # Update workers
    # ==================================================================

    def _trigger_update_all(self):
        """Start background worker to update all flights."""
        if self._update_worker and self._update_worker.isRunning():
            self._update_pending = True  # Remember to update after this one finishes
            return
        self._update_pending = False
        self._update_worker = UpdateWorker(self.flight_tracker, "all")
        self._update_worker.updates_ready.connect(self._on_updates_all)
        self._update_worker.finished.connect(self._on_worker_all_finished)
        self._update_worker.start()

    def _on_updates_all(self, changes: dict[str, Any]):
        """Process results from all-update worker."""
        self._process_updates(changes)

    def _on_worker_all_finished(self):
        """If a timer tick was skipped, trigger a fresh update now."""
        if self._update_pending and not (self._update_worker and self._update_worker.isRunning()):
            self._trigger_update_all()

    def _trigger_update_not_departed(self):
        """Start background worker to update only not-departed flights."""
        # Don't start if all-update worker is already running (covers same flights)
        if self._update_worker and self._update_worker.isRunning():
            return
        if self._nd_worker and self._nd_worker.isRunning():
            return
        # Only bother if there are not-departed flights
        has_nd = any(
            not t.has_departed
            for t in self.flight_tracker.get_all_tracked().values()
        )
        if not has_nd:
            return
        self._nd_worker = UpdateWorker(self.flight_tracker, "not_departed")
        self._nd_worker.updates_ready.connect(self._on_updates_nd)
        self._nd_worker.start()

    def _on_updates_nd(self, changes: dict[str, Any]):
        """Process results from not-departed worker."""
        self._process_updates(changes)

    def _process_updates(self, changes: dict[str, Any]):
        """Process state-change results from UpdateWorker — shared by both workers."""
        for fid, state in changes.items():
            self._handle_state_change(fid, state)

        self._repopulate_table()
        self._update_status()

    def _handle_state_change(self, fid: str, state: dict[str, Any]):
        """Fire sounds and notifications for departure / landing events."""
        tracked = self.flight_tracker.tracked_flights.get(fid)
        if not tracked:
            return

        name = tracked.display_name()

        # Just departed → play takeoff sound + compact notification
        if state.get("just_departed") and not tracked.notified_departure:
            tracked.notified_departure = True
            self.sound_manager.play_takeoff()
            eta = tracked.get_eta_text()
            self._toast_manager.show_toast(
                self.translator.tr("notif_takeoff_title"),
                self.translator.tr("msg_flight_departed", name, eta),
                kind="takeoff",
            )

        # Just landed → play landing sound + compact notification
        if state.get("just_landed") and not tracked.notified_landing:
            tracked.notified_landing = True
            self.sound_manager.play_landing()
            self._toast_manager.show_toast(
                self.translator.tr("notif_landing_title"),
                self.translator.tr("msg_flight_landed", name),
                kind="landing",
            )

        # ETA hit 00:00 while in-flight → also trigger landing sound if not already
        if (tracked.has_departed and not tracked.has_landed
                and not tracked.notified_landing):
            secs = tracked.get_eta_seconds()
            if secs is not None and secs == 0:
                tracked.notified_landing = True
                self.sound_manager.play_landing()

    # ==================================================================
    # Display refresh (every second for live countdown)
    # ==================================================================

    def _refresh_eta_display(self):
        """Update ETA (countdown) and Landed Since every second — no API call."""
        # Don't refresh if user is editing a cell
        if self._is_editing:
            return
        
        flights = self.flight_tracker.get_all_tracked()
        
        # Temporarily disconnect itemChanged to prevent edit triggers during refresh
        try:
            self.table.itemChanged.disconnect(self._on_table_item_changed)
        except TypeError:
            pass  # Signal wasn't connected, that's fine
        
        for row, (fid, tracked) in enumerate(flights.items()):
            if row >= self.table.rowCount():
                break

            # Update ETA for in-flight planes (COUNTDOWN!)
            if tracked.has_departed and not tracked.has_landed:
                self._set_cell(row, COL_ETA, tracked.get_eta_text(), align_center=True)
                
                # Check ETA → 00:00 for landing
                secs = tracked.get_eta_seconds()
                if secs is not None and secs == 0 and not tracked.notified_landing:
                    tracked.notified_landing = True
                    tracked.has_landed = True
                    
                    # Update Real Landed column with STATIC time
                    self._set_cell(row, COL_REAL_LANDED, tracked.get_landed_time_static(), align_center=True)
                    
                    # Play sound
                    self.sound_manager.play_landing()
                    
                    # Show compact notification (bottom-right, non-blocking)
                    self._toast_manager.show_toast(
                        self.translator.tr("notif_landing_title"),
                        self.translator.tr("msg_flight_landed", tracked.display_name()),
                        kind="landing",
                    )
            
            # Update Landed Since for landed planes (COUNTDOWN!)
            if tracked.has_landed:
                self._set_cell(row, COL_LANDED_SINCE, tracked.get_landed_text(), align_center=True)

            # Re-evaluate early/late arrival alert. Blinking persists until
            # the row is clicked, but the caution sound fires only once per
            # new alert episode.
            tracked.refresh_delay_state()
            if tracked.should_play_delay_sound():
                tracked.mark_delay_sound_played()
                self.sound_manager.play_caution()
        
        # Reconnect itemChanged signal
        try:
            self.table.itemChanged.connect(self._on_table_item_changed)
        except Exception:
            pass  # Already connected, that's fine

    # ==================================================================
    # Table rendering
    # ==================================================================

    def _repopulate_table(self):
        """Full table rebuild from current flight data."""
        # Don't refresh if user is editing a cell
        if self._is_editing:
            return
        
        flights = self.flight_tracker.get_all_tracked()
        t = self.translator

        has_flights = bool(flights)
        self._empty_label.setVisible(not has_flights)
        self.table.setVisible(has_flights)

        # Disconnect itemChanged signal to prevent triggering during repopulation
        try:
            self.table.itemChanged.disconnect(self._on_table_item_changed)
        except TypeError:
            pass  # Signal wasn't connected, that's fine
        
        self.table.setRowCount(len(flights))

        for row, (fid, tracked) in enumerate(flights.items()):
            self._render_row(row, tracked)
        
        # Reconnect itemChanged signal
        try:
            self.table.itemChanged.connect(self._on_table_item_changed)
        except Exception:
            pass  # Already connected, that's fine

    def _get_status_style(self, tracked: TrackedFlight) -> tuple[str, QColor, QColor]:
        """Return (status_text, status_color, row_bg) for a tracked flight's
        normal (non-blinking) appearance."""
        t = self.translator
        if tracked.has_landed:
            return t.tr("status_landed"), QColor(C["green"]), QColor(C["row_landed"])
        if tracked.has_departed:
            return t.tr("status_in_flight"), QColor(C["accent"]), QColor(C["row_inflight"])
        if tracked.is_pending_schedule:
            return t.tr("status_scheduled"), QColor(C["purple"]), QColor(C["row_scheduled"])
        return t.tr("status_not_departed"), QColor(C["amber"]), QColor(C["row_even"])

    def _get_delay_minutes(self, tracked: TrackedFlight) -> int:
        """Deviation (whole minutes) between estimated and scheduled arrival."""
        if tracked.scheduled_arrival and tracked.estimated_arrival:
            return max(1, abs(tracked.scheduled_arrival - tracked.estimated_arrival) // 60)
        return 0

    def _get_row_paint(self, tracked: TrackedFlight) -> tuple[str, QColor, QColor]:
        """Return (status_text, status_color, row_bg) including the early/late
        arrival alert override: the STATUS text always shows a clear
        ⚠ EARLY/LATE label (so it's obvious *which* flight is affected even
        without watching the blink), while the row background alternates
        between the alert colour and its normal colour on every blink tick."""
        status_text, status_color, row_bg = self._get_status_style(tracked)

        if tracked.has_active_delay_alert():
            t = self.translator
            mins = self._get_delay_minutes(tracked)
            if tracked.delay_kind == "early":
                alert_color = QColor(C["red"])
                status_text = f"{status_text}  {t.tr('status_suffix_early', mins)}"
            else:
                alert_color = QColor(C["green"])
                status_text = f"{status_text}  {t.tr('status_suffix_late', mins)}"
            status_color = alert_color
            if self._blink_on:
                row_bg = alert_color

        return status_text, status_color, row_bg

    def _render_row(self, row: int, tracked: TrackedFlight):
        """Render / refresh one complete table row."""
        status_text, status_color, row_bg = self._get_row_paint(tracked)

        # ── Cell data ────────────────────────────────────────
        # For NOTE column, preserve existing cell value to prevent overwriting user edits
        existing_note = ""
        note_item = self.table.item(row, COL_NOTE)
        if note_item:
            existing_note = note_item.text()
        else:
            existing_note = tracked.note or ""
        
        cells = {
            COL_FLIGHT:   (tracked.display_name(), False, status_color if tracked.has_landed or tracked.has_departed else QColor(C["text"])),
            COL_NOTE:     (existing_note, False, QColor(C["text_dim"])),
            COL_FROM:     (tracked.origin, True, None),
            COL_TO:       (tracked.destination, True, None),
            COL_AIRCRAFT: (f"{tracked.aircraft_code}  {tracked.registration}", False, None),
            COL_DEP:      (tracked.get_departure_display(), True, None),
            COL_DEP_DATE: (tracked.get_departure_date_display(), True, QColor(C["text_dim"])),
            COL_ARR:      (tracked.get_arrival_display(), True, None),
            COL_ARR_DATE: (tracked.get_arrival_date_display(), True, QColor(C["text_dim"])),
            COL_STATUS:   (status_text, True, status_color),
            COL_ETA:      (tracked.get_eta_text(), True, None),
            COL_REAL_LANDED: (tracked.get_landed_time_static() if tracked.has_landed else "—", True, QColor(C["green"]) if tracked.has_landed else None),
            COL_LANDED_SINCE: (tracked.get_landed_text() if tracked.has_landed else "—", True, QColor(C["amber"]) if tracked.has_landed else None),
            COL_ALT:      (f"{tracked.altitude:,}" if tracked.altitude else "—", True, None),
            COL_SPEED:    (str(tracked.ground_speed) if tracked.ground_speed else "—", True, None),
        }

        for col, (text, center, color) in cells.items():
            item = QTableWidgetItem(str(text))
            item.setBackground(QBrush(row_bg))
            if center:
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
            else:
                item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            if color:
                item.setForeground(QBrush(color))
            self.table.setItem(row, col, item)

    def _set_cell(self, row: int, col: int, text: str, align_center: bool = False):
        """Update a single cell without rebuilding the full row."""
        item = self.table.item(row, col)
        if item:
            item.setText(text)
        else:
            item = QTableWidgetItem(text)
            if align_center:
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(row, col, item)

    # ==================================================================
    # Early / late arrival alert (blinking rows + looping caution sound)
    # ==================================================================

    def _apply_blink_highlights(self):
        """Toggle blinking backgrounds for flights with an active, unacknowledged
        early/late arrival alert. Red = arriving 2+ min early, green = 2+ min late.

        Re-renders the whole row (via _render_row) on every tick so the
        blink state can never be silently overwritten/undone by a periodic
        full table repaint (_repopulate_table) happening in between ticks."""
        self._blink_on = not self._blink_on
        flights = list(self.flight_tracker.get_all_tracked().items())

        for row, (_fid, tracked) in enumerate(flights):
            if row >= self.table.rowCount():
                break
            if tracked.has_active_delay_alert():
                self._render_row(row, tracked)

    def _on_item_clicked(self, item: QTableWidgetItem):
        """A single click on a flight's row acknowledges (silences) its
        early/late arrival alert, if any — stopping the row from blinking."""
        row = item.row()
        flights = list(self.flight_tracker.get_all_tracked().items())
        if row >= len(flights):
            return
        _fid, tracked = flights[row]
        if tracked.has_active_delay_alert():
            tracked.acknowledge_delay_alert()
            self._render_row(row, tracked)

    # ==================================================================
    # Right-click context menu
    # ==================================================================

    def _on_context_menu(self, pos):
        """Show right-click context menu on table row."""
        row = self.table.rowAt(pos.y())
        if row < 0:
            return

        flights = list(self.flight_tracker.get_all_tracked().values())
        if row >= len(flights):
            return
        tracked = flights[row]

        t = self.translator
        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{ background:{C['card']}; color:{C['text']}; border:1px solid {C['border_light']};
                    border-radius:8px; padding:6px 4px; }}
            QMenu::item {{ padding:8px 24px 8px 14px; border-radius:5px; font-size:13px; }}
            QMenu::item:selected {{ background:{C['selected']}; color:{C['accent']}; }}
            QMenu::separator {{ background:{C['border']}; height:1px; margin:4px 8px; }}
        """)

        # Flight info header (non-clickable)
        header = QAction(f"✈  {tracked.display_name()}", menu)
        header.setEnabled(False)
        menu.addAction(header)
        menu.addSeparator()

        # Open on FR24
        act_open = menu.addAction(f"🌐  {t.tr('ctx_open_fr24')}")
        act_open.triggered.connect(lambda: self._open_fr24_flight(tracked.get_fr24_url_slug()))

        # Flight history / schedule
        act_history = menu.addAction(f"🕓  {t.tr('ctx_view_history')}")
        act_history.triggered.connect(lambda: self._show_history_dialog(tracked.flight_number or tracked.callsign))

        menu.addSeparator()

        # Copy actions
        act_copy_flight = menu.addAction(f"📋  {t.tr('ctx_copy_flight')}")
        act_copy_flight.triggered.connect(lambda: self._copy_to_clipboard(tracked.display_name()))

        act_copy_callsign = menu.addAction(f"📋  {t.tr('ctx_copy_callsign')}")
        act_copy_callsign.triggered.connect(lambda: self._copy_to_clipboard(tracked.callsign or tracked.flight_number))

        act_copy_url = menu.addAction(f"🔗  {t.tr('ctx_copy_fr24_url')}")
        act_copy_url.triggered.connect(lambda: self._copy_fr24_url(tracked.get_fr24_url_slug()))

        menu.addSeparator()

        # Note actions
        act_edit_note = menu.addAction(f"✏️  {t.tr('ctx_edit_note')}")
        act_edit_note.triggered.connect(lambda: self._edit_note_dialog(row, tracked))

        act_clear_note = menu.addAction(f"🗑  {t.tr('ctx_clear_note')}")
        act_clear_note.triggered.connect(lambda: self._clear_note(row, tracked))

        menu.addSeparator()

        # Move actions
        act_up = menu.addAction(f"↑  {t.tr('ctx_move_up')}")
        act_up.triggered.connect(self._move_row_up)
        act_up.setEnabled(row > 0)

        act_down = menu.addAction(f"↓  {t.tr('ctx_move_down')}")
        act_down.triggered.connect(self._move_row_down)
        act_down.setEnabled(row < self.table.rowCount() - 1)

        menu.addSeparator()

        # View details
        act_details = menu.addAction(f"ℹ️  {t.tr('ctx_view_details')}")
        act_details.triggered.connect(lambda: self._show_flight_details(tracked))

        menu.addSeparator()

        # Remove
        act_remove = menu.addAction(f"✕  {t.tr('ctx_remove_flight')}")
        act_remove.triggered.connect(lambda: self._remove_flight_by_row(row))

        menu.exec(self.table.viewport().mapToGlobal(pos))

    def _open_fr24_flight(self, flight_id: str):
        """Open flight on FlightRadar24.com."""
        import webbrowser
        webbrowser.open(f"https://www.flightradar24.com/data/flights/{flight_id}")

    def _copy_to_clipboard(self, text: str):
        """Copy text to clipboard."""
        QApplication.clipboard().setText(text)

    def _copy_fr24_url(self, flight_id: str):
        """Copy FR24 flight URL to clipboard."""
        QApplication.clipboard().setText(
            f"https://www.flightradar24.com/data/flights/{flight_id}"
        )

    def _edit_note_dialog(self, row: int, tracked: TrackedFlight):
        """Show dialog to edit flight note."""
        from PyQt6.QtWidgets import QInputDialog
        text, ok = QInputDialog.getText(
            self, self.translator.tr("ctx_edit_note"),
            f"{tracked.display_name()}:",
            text=tracked.note,
        )
        if ok:
            tracked.note = text.strip()
            self._repopulate_table()
            self._save_settings()

    def _clear_note(self, row: int, tracked: TrackedFlight):
        """Clear the note for a tracked flight."""
        tracked.note = ""
        self._repopulate_table()
        self._save_settings()

    def _show_flight_details(self, tracked: TrackedFlight):
        """Show detailed flight information dialog."""
        t = self.translator
        details = (
            f"<b>{tracked.display_name()}</b><br><br>"
            f"<b>{t.tr('header_flight')}:</b> {tracked.flight_number or tracked.callsign}<br>"
            f"<b>{t.tr('header_from')}:</b> {tracked.origin_name or tracked.origin}<br>"
            f"<b>{t.tr('header_to')}:</b> {tracked.destination_name or tracked.destination}<br>"
            f"<b>{t.tr('header_aircraft')}:</b> {tracked.aircraft_code} ({tracked.registration})<br>"
            f"<b>{t.tr('header_departure')}:</b> {tracked.get_departure_date_display().replace(chr(10), ' ')} {tracked.get_departure_display()}<br>"
            f"<b>{t.tr('header_arrival')}:</b> {tracked.get_arrival_date_display().replace(chr(10), ' ')} {tracked.get_arrival_display()}<br>"
            f"<b>{t.tr('header_status')}:</b> {tracked.status_text or 'N/A'}<br>"
            f"<b>{t.tr('header_altitude')}:</b> {f'{tracked.altitude:,} ft' if tracked.altitude else 'N/A'}<br>"
            f"<b>{t.tr('header_speed')}:</b> {f'{tracked.ground_speed} kts' if tracked.ground_speed else 'N/A'}<br>"
            f"<b>Note:</b> {tracked.note or '—'}"
        )
        msg = QMessageBox(self)
        msg.setWindowTitle(tracked.display_name())
        msg.setTextFormat(Qt.TextFormat.RichText)
        msg.setText(details)
        msg.exec()

    def _remove_flight_by_row(self, row: int):
        """Remove a flight by table row index."""
        flights = list(self.flight_tracker.get_all_tracked().items())
        if row >= len(flights):
            return
        fid, tracked = flights[row]
        reply = QMessageBox.question(
            self,
            self.translator.tr("confirm_title"),
            self.translator.tr("msg_remove_confirm", tracked.display_name()),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.flight_tracker.remove_flight(fid)
            self.sound_manager.play_remove()
            self._repopulate_table()
            self._update_status()
            self._save_settings()

    # ==================================================================
    # Table editing
    # ==================================================================

    def _on_item_double_clicked(self, item: QTableWidgetItem):
        """User started editing - pause auto-refresh."""
        self._is_editing = True
    
    def _move_row_up(self):
        """Move selected row up."""
        row = self.table.currentRow()
        if row <= 0:
            return  # Already at top
        
        self._swap_rows(row, row - 1)
        self.table.setCurrentCell(row - 1, 0)
        self._save_settings()
    
    def _move_row_down(self):
        """Move selected row down."""
        row = self.table.currentRow()
        if row < 0 or row >= self.table.rowCount() - 1:
            return  # Already at bottom
        
        self._swap_rows(row, row + 1)
        self.table.setCurrentCell(row + 1, 0)
        self._save_settings()
    
    def _swap_rows(self, row1: int, row2: int):
        """Swap two table rows and update flight_tracker order."""
        # Disconnect signal during swap
        try:
            self.table.itemChanged.disconnect(self._on_table_item_changed)
        except TypeError:
            pass
        
        # Get flight IDs for both rows
        flights = list(self.flight_tracker.get_all_tracked().items())
        if row1 >= len(flights) or row2 >= len(flights):
            try:
                self.table.itemChanged.connect(self._on_table_item_changed)
            except Exception:
                pass
            return
        
        fid1, flight1 = flights[row1]
        fid2, flight2 = flights[row2]
        
        # Swap in flight_tracker dict (preserve order)
        flight_list = list(self.flight_tracker.tracked_flights.items())
        flight_list[row1], flight_list[row2] = flight_list[row2], flight_list[row1]
        self.flight_tracker.tracked_flights = dict(flight_list)
        
        # Swap table rows visually
        for col in range(self.table.columnCount()):
            item1 = self.table.takeItem(row1, col)
            item2 = self.table.takeItem(row2, col)
            if item1:
                self.table.setItem(row2, col, item1)
            if item2:
                self.table.setItem(row1, col, item2)
        
        # Reconnect signal
        try:
            self.table.itemChanged.connect(self._on_table_item_changed)
        except Exception:
            pass
    
    def _on_table_item_changed(self, item: QTableWidgetItem):
        """Handle table cell edits - save changes to TrackedFlight objects."""
        if not item:
            return
        
        # User finished editing
        self._is_editing = False
        
        row = item.row()
        col = item.column()
        new_text = item.text().strip()
        
        # Get the flight for this row
        flights = list(self.flight_tracker.get_all_tracked().values())
        if row >= len(flights):
            return
        
        tracked = flights[row]
        
        # Map column to TrackedFlight attribute
        # Allow editing of all user-visible fields
        if col == COL_FLIGHT:
            # Split into callsign / flight_number
            if new_text:
                tracked.callsign = new_text
                tracked.flight_number = new_text
        elif col == COL_NOTE:
            tracked.note = new_text
        elif col == COL_FROM:
            tracked.origin = new_text
        elif col == COL_TO:
            tracked.destination = new_text
        elif col == COL_AIRCRAFT:
            # Try to split aircraft code and registration
            parts = new_text.split()
            if len(parts) >= 2:
                tracked.aircraft_code = parts[0]
                tracked.registration = parts[1]
            elif len(parts) == 1:
                tracked.aircraft_code = parts[0]
        elif col == COL_DEP:
            # Parse departure time (HH:MM format expected)
            try:
                time_obj = datetime.strptime(new_text, "%H:%M")
                # Convert to timestamp (use today's date)
                dt = datetime.now().replace(
                    hour=time_obj.hour,
                    minute=time_obj.minute,
                    second=0,
                    microsecond=0
                )
                tracked.actual_departure = int(dt.timestamp())
            except:
                pass
        elif col == COL_ARR:
            # Parse arrival time (HH:MM format expected)
            try:
                time_obj = datetime.strptime(new_text, "%H:%M")
                dt = datetime.now().replace(
                    hour=time_obj.hour,
                    minute=time_obj.minute,
                    second=0,
                    microsecond=0
                )
                tracked.actual_arrival = int(dt.timestamp())
            except:
                pass
        elif col == COL_STATUS:
            tracked.status_text = new_text
        elif col == COL_ALT:
            # Parse altitude (remove commas)
            try:
                tracked.altitude = int(new_text.replace(",", "").replace(" ", ""))
            except:
                pass
        elif col == COL_SPEED:
            # Parse speed
            try:
                tracked.ground_speed = int(new_text)
            except:
                pass
        # COL_DEP_DATE, COL_ARR_DATE, COL_ETA, COL_REAL_LANDED, COL_LANDED_SINCE are read-only
        
        # Save settings after edit
        self._save_settings()

    # ==================================================================
    # Status bar
    # ==================================================================

    def _update_status(self):
        n = len(self.flight_tracker.get_all_tracked())
        self._lbl_count.setText(self.translator.tr("label_tracking", n))
        now = datetime.now().strftime("%H:%M:%S")
        self._lbl_update.setText(self.translator.tr("label_last_update", now))

    # ==================================================================
    # Settings dialog
    # ==================================================================

    def _show_settings(self):
        dlg = SettingsDialog(
            self.translator,
            self.sound_manager,
            self._refresh_interval,
            self,
        )
        if dlg.exec():
            self.sound_manager.set_enabled(dlg.sound_enabled)
            new_interval = dlg.refresh_interval
            if new_interval != self._refresh_interval:
                self._refresh_interval = new_interval
                self._timer_all.setInterval(new_interval * 1000)
                # Also re-offset the not-departed timer
                self._timer_nd.setInterval(int(new_interval * 1000 / 2))
            self._save_settings()

    def _show_about(self):
        QMessageBox.about(
            self,
            self.translator.tr("dlg_about_title"),
            self.translator.tr("dlg_about_text"),
        )
    
    def _open_github(self):
        """Open GitHub repository in browser."""
        import webbrowser
        webbrowser.open("https://github.com/JustLachin/MyRadar24")
    
    def _copy_github_url(self):
        """Copy GitHub URL to clipboard."""
        from PyQt6.QtWidgets import QApplication
        clipboard = QApplication.clipboard()
        clipboard.setText("https://github.com/JustLachin/MyRadar24")
        QMessageBox.information(
            self,
            self.translator.tr("info_title"),
            self.translator.tr("msg_url_copied"),
        )

    # ==================================================================
    # Settings persistence
    # ==================================================================

    def _save_flight_order(self):
        """Save current table row order to tracked flights."""
        # Read current table order and update flight_tracker order
        new_order = []
        for row in range(self.table.rowCount()):
            item = self.table.item(row, COL_FLIGHT)
            if item:
                flight_name = item.text()
                # Find matching flight
                for fid, tracked in self.flight_tracker.get_all_tracked().items():
                    if tracked.display_name() == flight_name:
                        new_order.append(fid)
                        break
        
        # Update flight_tracker with new order
        if new_order:
            # Reorder the tracked_flights dict
            old_flights = self.flight_tracker.tracked_flights.copy()
            self.flight_tracker.tracked_flights.clear()
            for fid in new_order:
                if fid in old_flights:
                    self.flight_tracker.tracked_flights[fid] = old_flights[fid]

    def _save_settings(self):
        try:
            # Save current table order
            self._save_flight_order()
            
            # Save UI preferences
            data: dict[str, Any] = {
                "language":         self.translator.get_current_language(),
                "sound_enabled":    self.sound_manager.enabled,
                "refresh_interval": self._refresh_interval,
            }
            
            # Save tracked flights (including notes and order)
            flights_data = []
            for fid, tracked in self.flight_tracker.get_all_tracked().items():
                flights_data.append({
                    "flight_id": fid,
                    "note": tracked.note,
                    "callsign": tracked.callsign,
                    "flight_number": tracked.flight_number,
                    "is_pending_schedule": tracked.is_pending_schedule,
                    "schedule_number": tracked.schedule_number,
                    "schedule_row_id": tracked.schedule_row_id,
                    "resolved_flight_id": tracked.resolved_flight_id,
                })
            data["tracked_flights"] = flights_data
            
            with open(self._SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[MainWindow] save_settings error: {e}")

    def _load_settings(self):
        try:
            if self._SETTINGS_FILE.exists():
                with open(self._SETTINGS_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.translator.set_language(data.get("language", "en"))
                self.sound_manager.set_enabled(data.get("sound_enabled", True))
                # NOTE: refresh_interval is hardcoded to 5 seconds.
                # User can temporarily change it via Settings, but on restart
                # it always resets to 5s for reliable real-time tracking.
                
                # Load tracked flights with notes
                tracked_flights = data.get("tracked_flights", [])
                for flight_data in tracked_flights:
                    fid = flight_data.get("flight_id")
                    note = flight_data.get("note", "")
                    if not fid:
                        continue

                    if flight_data.get("is_pending_schedule"):
                        tracked = self.flight_tracker.restore_scheduled_flight(
                            fid,
                            flight_data.get("schedule_number") or flight_data.get("flight_number") or "",
                            flight_data.get("schedule_row_id"),
                            flight_data.get("resolved_flight_id"),
                        )
                    else:
                        tracked = self.flight_tracker.add_flight(fid)

                    if tracked and note:
                        tracked.note = note
        except Exception as e:
            print(f"[MainWindow] load_settings error: {e}")

    # ==================================================================
    # Window close
    # ==================================================================

    def closeEvent(self, event: QCloseEvent) -> None:
        self._save_settings()
        # Stop workers gracefully
        for w in (self._update_worker, self._nd_worker):
            if w and w.isRunning():
                w.quit()
                w.wait(2000)
        event.accept()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        if hasattr(self, "_toast_manager"):
            self._toast_manager.reposition()

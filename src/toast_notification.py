#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Toast notification widget — compact, non-blocking, bottom-right corner
notifications shown *inside* the application window (not OS/system-tray
popups). Unlike QMessageBox, these never steal focus or require an "OK"
click to dismiss, so the user can keep working while they're visible.
"""

from typing import List, Optional

from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QPropertyAnimation, QEasingCurve
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QGraphicsOpacityEffect, QWidget

# Accent colour + icon per notification kind
_KIND_STYLE = {
    "takeoff": ("#20c05c", "✈"),
    "landing": ("#228be6", "🛬"),
    "info":    ("#228be6", "ℹ"),
}


class ToastWidget(QFrame):
    """A single compact notification card."""

    closed = pyqtSignal(object)  # emits self

    def __init__(self, parent: QWidget, title: str, message: str, kind: str = "info", duration_ms: int = 6000):
        super().__init__(parent)
        self._duration_ms = duration_ms
        accent, icon = _KIND_STYLE.get(kind, _KIND_STYLE["info"])

        self.setObjectName("toast")
        self.setFixedWidth(320)
        self.setStyleSheet(f"""
            QFrame#toast {{
                background-color: #132842;
                border: 1px solid {accent};
                border-left: 4px solid {accent};
                border-radius: 10px;
            }}
            QLabel#toast_icon {{ font-size: 20px; }}
            QLabel#toast_title {{ color: #e3edf6; font-size: 13px; font-weight: 700; }}
            QLabel#toast_msg {{ color: #a8c0d8; font-size: 12px; }}
            QPushButton#toast_close {{
                background: transparent; color: #5a7a9a; border: none;
                font-size: 13px; font-weight: bold; border-radius: 10px;
            }}
            QPushButton#toast_close:hover {{ background: #1e3a5a; color: #e85959; }}
        """)

        outer = QHBoxLayout(self)
        outer.setContentsMargins(12, 10, 8, 10)
        outer.setSpacing(10)

        icon_lbl = QLabel(icon)
        icon_lbl.setObjectName("toast_icon")
        outer.addWidget(icon_lbl, 0, Qt.AlignmentFlag.AlignTop)

        text_col = QVBoxLayout()
        text_col.setSpacing(2)
        title_lbl = QLabel(title)
        title_lbl.setObjectName("toast_title")
        title_lbl.setWordWrap(True)
        msg_lbl = QLabel(message)
        msg_lbl.setObjectName("toast_msg")
        msg_lbl.setWordWrap(True)
        text_col.addWidget(title_lbl)
        text_col.addWidget(msg_lbl)
        outer.addLayout(text_col, 1)

        btn_close = QPushButton("✕")
        btn_close.setObjectName("toast_close")
        btn_close.setFixedSize(22, 22)
        btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_close.clicked.connect(self.dismiss)
        outer.addWidget(btn_close, 0, Qt.AlignmentFlag.AlignTop)

        # Fade-in
        self._opacity = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self._opacity)
        self._fade_in = QPropertyAnimation(self._opacity, b"opacity", self)
        self._fade_in.setDuration(180)
        self._fade_in.setStartValue(0.0)
        self._fade_in.setEndValue(1.0)
        self._fade_in.setEasingCurve(QEasingCurve.Type.OutCubic)

        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self.dismiss)

    def show_animated(self):
        self.show()
        self.adjustSize()
        self._fade_in.start()
        self._timer.start(self._duration_ms)

    def enterEvent(self, event):
        self._timer.stop()  # pause auto-dismiss while the user is reading it
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._timer.start(2000)
        super().leaveEvent(event)

    def dismiss(self):
        self._timer.stop()
        self.closed.emit(self)
        self.hide()
        self.deleteLater()


class ToastManager:
    """Owns and stacks ToastWidgets in the bottom-right corner of a window."""

    MARGIN = 16
    SPACING = 10

    def __init__(self, host: QWidget):
        self.host = host
        self._toasts: List[ToastWidget] = []

    def show_toast(self, title: str, message: str, kind: str = "info", duration_ms: int = 6000) -> ToastWidget:
        toast = ToastWidget(self.host, title, message, kind, duration_ms)
        toast.closed.connect(self._on_closed)
        self._toasts.append(toast)
        toast.show_animated()
        self.reposition()
        return toast

    def _on_closed(self, toast: ToastWidget):
        if toast in self._toasts:
            self._toasts.remove(toast)
        self.reposition()

    def reposition(self):
        """Stack toasts bottom-up in the host widget's bottom-right corner."""
        rect = self.host.rect()
        y = rect.height() - self.MARGIN
        for toast in reversed(self._toasts):
            toast.adjustSize()
            x = rect.width() - toast.width() - self.MARGIN
            y -= toast.height()
            toast.move(max(0, x), max(0, y))
            toast.raise_()
            y -= self.SPACING

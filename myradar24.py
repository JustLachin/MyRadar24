#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MyRadar24 - Entry Point
FlightRadar24 Desktop Client | Premium PyQt6 Application
"""
import io
import sys
# Force UTF-8 output on Windows terminals that default to cp1252
if sys.stdout and hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if sys.stderr and hasattr(sys.stderr, 'buffer'):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import os
import logging
import traceback
from pathlib import Path

# ── Silence noisy SDK/brotli warnings ─────────────────────────────────
logging.basicConfig(level=logging.ERROR,
                    format="%(levelname)s %(name)s: %(message)s")
for noisy in ("FlightRadarAPI.request", "FlightRadarAPI", "urllib3"):
    logging.getLogger(noisy).setLevel(logging.CRITICAL)

# ── Qt imports ────────────────────────────────────────────────────────
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import Qt, QLocale
from PyQt6.QtGui import QPalette, QColor, QFont

from src.main_window import MainWindow


# ======================================================================
# Dark palette
# ======================================================================

def _build_dark_palette() -> QPalette:
    p = QPalette()
    c = {
        "window":        QColor("#0b1520"),
        "window_text":   QColor("#dce8f4"),
        "base":          QColor("#0f1e2e"),
        "alt_base":      QColor("#0d1a28"),
        "tooltip_base":  QColor("#13243a"),
        "tooltip_text":  QColor("#dce8f4"),
        "text":          QColor("#dce8f4"),
        "button":        QColor("#13243a"),
        "button_text":   QColor("#dce8f4"),
        "bright_text":   QColor("#ffffff"),
        "link":          QColor("#1e90ff"),
        "highlight":     QColor("#1a3c60"),
        "highlight_text":QColor("#4db8ff"),
        "mid":           QColor("#1e3048"),
        "shadow":        QColor("#000a14"),
        "dark":          QColor("#060f18"),
        "light":         QColor("#1e3048"),
    }
    p.setColor(QPalette.ColorRole.Window,          c["window"])
    p.setColor(QPalette.ColorRole.WindowText,      c["window_text"])
    p.setColor(QPalette.ColorRole.Base,            c["base"])
    p.setColor(QPalette.ColorRole.AlternateBase,   c["alt_base"])
    p.setColor(QPalette.ColorRole.ToolTipBase,     c["tooltip_base"])
    p.setColor(QPalette.ColorRole.ToolTipText,     c["tooltip_text"])
    p.setColor(QPalette.ColorRole.Text,            c["text"])
    p.setColor(QPalette.ColorRole.Button,          c["button"])
    p.setColor(QPalette.ColorRole.ButtonText,      c["button_text"])
    p.setColor(QPalette.ColorRole.BrightText,      c["bright_text"])
    p.setColor(QPalette.ColorRole.Link,            c["link"])
    p.setColor(QPalette.ColorRole.Highlight,       c["highlight"])
    p.setColor(QPalette.ColorRole.HighlightedText, c["highlight_text"])
    p.setColor(QPalette.ColorRole.Mid,             c["mid"])
    p.setColor(QPalette.ColorRole.Shadow,          c["shadow"])
    p.setColor(QPalette.ColorRole.Dark,            c["dark"])
    p.setColor(QPalette.ColorRole.Light,           c["light"])
    return p


# ======================================================================
# Exception hook
# ======================================================================

def _exception_hook(exc_type, exc_value, exc_tb):
    """Global exception handler — shows an error dialog instead of silent crash."""
    msg = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    print(msg, file=sys.stderr)
    try:
        box = QMessageBox()
        box.setIcon(QMessageBox.Icon.Critical)
        box.setWindowTitle("MyRadar24 — Unexpected Error")
        box.setText(f"An unexpected error occurred:\n\n{exc_value}")
        box.setDetailedText(msg)
        box.exec()
    except Exception:
        pass


# ======================================================================
# Main
# ======================================================================

def main():
    # High-DPI support
    os.environ.setdefault("QT_ENABLE_HIGHDPI_SCALING", "1")

    app = QApplication(sys.argv)
    app.setApplicationName("MyRadar24")
    app.setOrganizationName("MyRadar24")
    app.setApplicationVersion("2.0.0")
    app.setStyle("Fusion")   # Fusion style works best with custom palettes

    # Apply dark palette globally
    app.setPalette(_build_dark_palette())

    # Default font
    font = QFont("Segoe UI", 10)
    app.setFont(font)

    # Global exception hook
    sys.excepthook = _exception_hook

    print("=" * 60)
    print("  MyRadar24 v2.0 - Flight Tracking Application")
    print("  Powered by FlightRadar24 API")
    print("=" * 60)

    window = MainWindow()
    window.show()

    print("  [OK] Application started. Ready to track flights.")
    print("=" * 60)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()

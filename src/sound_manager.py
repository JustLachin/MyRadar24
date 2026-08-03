#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Sound manager for MyRadar24 — uses PyQt6 QSoundEffect for async playback.
Maps events to specific sound files from the SND01-sine-sound-pack.
"""

from pathlib import Path
from typing import Any

try:
    from PyQt6.QtMultimedia import QSoundEffect
    from PyQt6.QtCore import QUrl
    _has_multimedia = True
except ImportError:
    _has_multimedia: bool = False
    QSoundEffect: Any = None  # type: ignore[no-redef]
    QUrl: Any = None  # type: ignore[no-redef]

# Fallback: winsound for Windows if multimedia unavailable
try:
    import winsound
    _has_winsound = True
except ImportError:
    _has_winsound: bool = False
    winsound: Any = None  # type: ignore[no-redef]


SOUND_DIR = Path(__file__).parent.parent / "sound" / "SND01-sine-sound-pack"

# Sound event → filename mapping
SOUND_MAP = {
    "takeoff":      "ringtone_loop.wav",  # Flight departed & ETA shown
    "landing":      "ringtone_loop.wav",  # Flight landed (ETA = 00:00)
    "button":       "button.wav",         # UI button click
    "add":          "transition_up.wav",  # Flight added to list
    "remove":       "transition_down.wav",# Flight removed from list
    "select":       "select.wav",         # Item selected
    "notification": "notification.wav",   # Generic notification
    "caution":      "caution.wav",        # Early/late (2min+) delay alert
}


class SoundManager:
    """
    Manages sound effects for flight event notifications.
    Supports enable/disable, volume control, and multiple sound events.
    """

    def __init__(self):
        self.enabled: bool = True
        self._effects: dict[str, Any] = {}

        if _has_multimedia:
            self._load_qt_sounds()
        # winsound fallback requires no preloading

    # ------------------------------------------------------------------
    # Loading
    # ------------------------------------------------------------------

    def _load_qt_sounds(self):
        """Pre-load QSoundEffect objects for each mapped sound."""
        for event, filename in SOUND_MAP.items():
            path = SOUND_DIR / filename
            if path.exists():
                fx = QSoundEffect()
                fx.setSource(QUrl.fromLocalFile(str(path)))
                fx.setVolume(0.85)
                self._effects[event] = fx

    # ------------------------------------------------------------------
    # Playback helpers
    # ------------------------------------------------------------------

    def _play(self, event: str):
        """Play a sound event if enabled."""
        if not self.enabled:
            return

        if _has_multimedia and event in self._effects:
            try:
                self._effects[event].play()
                return
            except Exception as e:
                print(f"[SoundManager] QSoundEffect error ({event}): {e}")

        # winsound fallback (Windows only, blocking — but we pass SND_ASYNC)
        if _has_winsound:
            filename = SOUND_MAP.get(event)
            if filename:
                path = SOUND_DIR / filename
                if path.exists():
                    try:
                        winsound.PlaySound(
                            str(path),
                            winsound.SND_FILENAME | winsound.SND_ASYNC
                        )
                    except Exception as e:
                        print(f"[SoundManager] winsound error ({event}): {e}")

    # ------------------------------------------------------------------
    # Public event methods
    # ------------------------------------------------------------------

    def play_takeoff(self):
        """Play when a tracked flight departs and ETA becomes available."""
        self._play("takeoff")

    def play_landing(self):
        """Play when ETA reaches 00:00 (flight has landed)."""
        self._play("landing")

    def play_button(self):
        """Play on general button clicks."""
        self._play("button")

    def play_add(self):
        """Play when a flight is added to the tracking list."""
        self._play("add")

    def play_remove(self):
        """Play when a flight is removed from the tracking list."""
        self._play("remove")

    def play_select(self):
        """Play when a list item is selected."""
        self._play("select")

    def play_notification(self):
        """Play a generic notification sound."""
        self._play("notification")

    def play_caution(self):
        """Play once when a flight starts arriving 2+ minutes early/late.
        Fires a single time per alert episode (not looped)."""
        self._play("caution")

    # ------------------------------------------------------------------
    # Settings
    # ------------------------------------------------------------------

    def set_enabled(self, enabled: bool):
        self.enabled = enabled

    def set_volume(self, volume: float):
        """Set volume for all QSoundEffect objects (0.0 – 1.0)."""
        for fx in self._effects.values():
            fx.setVolume(max(0.0, min(1.0, volume)))

    def is_available(self) -> bool:
        """Return True if at least one sound backend is available."""
        return _has_multimedia or _has_winsound

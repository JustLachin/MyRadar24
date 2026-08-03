#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Translation module for MyRadar24
JSON-based multi-language system with import support
"""

import json
import shutil
from pathlib import Path
from typing import Any

# Base required keys (subset that must exist for a valid language file)
REQUIRED_KEYS = [
    "app_title", "menu_file", "menu_exit", "menu_language",
    "btn_add_flight", "btn_cancel", "btn_search",
    "header_flight", "header_status", "header_eta",
    "status_not_departed", "status_in_flight", "status_landed",
]

# Locales directory (next to this file's parent)
LOCALES_DIR = Path(__file__).parent.parent / "locales"


class Translator:
    """
    JSON-based translation manager.
    Loads language files from locales/ directory.
    Supports runtime language import.
    """

    def __init__(self, language: str = "en"):
        self._data: dict[str, str] = {}
        self._fallback: dict[str, str] = {}
        self._current_language: str = "en"

        # Ensure locales dir exists
        LOCALES_DIR.mkdir(parents=True, exist_ok=True)

        # Load English as fallback first
        self._fallback = self._load_file("en") or {}

        # Load requested language
        self.set_language(language)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_language(self, language: str) -> bool:
        """
        Switch to a different language.
        Returns True on success, False if language file not found.
        """
        data = self._load_file(language)
        if data is not None:
            self._data = data
            self._current_language = language
            return True

        # Fallback to English
        self._data = self._fallback.copy()
        self._current_language = "en"
        return False

    def tr(self, key: str, *args: Any) -> str:
        """
        Translate a key.
        Optional positional args are used for .format() substitution.
        Falls back to English, then to the key itself.
        """
        text = (
            self._data.get(key)
            or self._fallback.get(key)
            or key
        )
        if args:
            try:
                text = text.format(*args)
            except (IndexError, KeyError):
                pass
        return text

    def get_current_language(self) -> str:
        return self._current_language

    def get_available_languages(self) -> dict[str, str]:
        """
        Scan locales/ directory and return {code: display_name} dict.
        Reads _meta.language from each JSON file.
        """
        languages: dict[str, str] = {}
        if not LOCALES_DIR.exists():
            return languages

        for json_file in sorted(LOCALES_DIR.glob("*.json")):
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                code = json_file.stem
                name = data.get("_meta", {}).get("language", code.upper())
                languages[code] = name
            except Exception:
                continue
        return languages

    def import_language(self, source_path: str) -> tuple[bool, str]:
        """
        Import an external JSON language file into locales/.
        Returns (True, language_name) on success, (False, error_msg) on failure.
        """
        src = Path(source_path)

        if not src.exists():
            return False, f"File not found: {source_path}"

        try:
            with open(src, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            return False, f"JSON parse error: {e}"

        # Validate required keys
        missing = [k for k in REQUIRED_KEYS if k not in data]
        if missing:
            return False, f"Missing required keys: {', '.join(missing[:5])}"

        # Determine language code
        meta = data.get("_meta", {})
        code = meta.get("code", src.stem).lower()
        name = meta.get("language", code.upper())

        # Copy to locales dir
        dest = LOCALES_DIR / f"{code}.json"
        shutil.copy2(src, dest)

        return True, name

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _load_file(self, language: str) -> dict[str, str] | None:
        """Load and return a language dict, or None if not found."""
        path = LOCALES_DIR / f"{language}.json"
        if not path.exists():
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            # Strip _meta key
            return {k: v for k, v in data.items() if k != "_meta"}
        except Exception as e:
            print(f"[Translator] Failed to load {language}.json: {e}")
            return None

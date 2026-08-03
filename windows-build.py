#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MyRadar24 - Windows Build Script
=================================
Builds a standalone Windows distribution using PyInstaller in
**--onedir** mode (NOT --onefile). The result is a plain, inspectable
folder containing:

    dist/MyRadar24/
        MyRadar24.exe
        logo.png
        sound/SND01-sine-sound-pack/*.wav
        locales/*.json
        SDK/...              (bundled automatically via analysis)
        <Qt / Python runtime DLLs, all visible, nothing hidden>

Everything (sounds, icons, translations, DLLs) is placed as loose,
openly-browsable files right next to the executable -- nothing is
packed into a single opaque binary blob.

Usage:
    python windows-build.py
"""

import importlib
import os
import shutil
import subprocess
import sys
from pathlib import Path

# ======================================================================
# Configuration
# ======================================================================

APP_NAME = "MyRadar24"
ENTRY_POINT = "myradar24.py"
ICON_SOURCE = "logo.png"       # PyInstaller + Pillow convert PNG -> ICO
WINDOWED = True                 # True = no console window (GUI app)

ROOT = Path(__file__).resolve().parent

# Folders copied as loose, visible files next to the .exe
DATA_DIRS = [
    ("sound", "sound"),
    ("locales", "locales"),
]

# Single files copied as loose, visible files next to the .exe
DATA_FILES = [
    ("logo.png", "."),
]

# Extra locations PyInstaller's analysis should search for imports
# (needed because src/flight_tracker.py adds SDK/python to sys.path
# manually at runtime, so PyInstaller must be told about it too)
EXTRA_ANALYSIS_PATHS = [
    ROOT / "SDK" / "python",
]

# Packages that ship compiled extensions / runtime data that static
# analysis alone might miss
COLLECT_ALL = ["curl_cffi", "brotli"]

HIDDEN_IMPORTS = [
    "PyQt6.QtMultimedia",
]

# Build artifacts to wipe before each build
CLEAN_PATHS = ["build", "dist", f"{APP_NAME}.spec"]


# ======================================================================
# Helpers
# ======================================================================

def run(cmd: list[str]) -> None:
    print("+ " + " ".join(str(c) for c in cmd))
    subprocess.run(cmd, check=True, cwd=ROOT)


def ensure_package(pip_name: str, import_name: str | None = None) -> None:
    """Install a build-time dependency if it isn't already available."""
    import_name = import_name or pip_name
    try:
        importlib.import_module(import_name)
        return
    except ImportError:
        pass
    print(f"[build] Installing missing build dependency: {pip_name}")
    run([sys.executable, "-m", "pip", "install", pip_name])


def clean(paths: list[str]) -> None:
    for rel in paths:
        p = ROOT / rel
        if p.is_dir():
            print(f"[build] Removing old {p}")
            shutil.rmtree(p, ignore_errors=True)
        elif p.is_file():
            print(f"[build] Removing old {p}")
            p.unlink()


# ======================================================================
# Build
# ======================================================================

def build() -> None:
    if os.name != "nt":
        print("[build] WARNING: this script is meant to run on Windows. "
              "Continuing anyway, but the result may not be a valid .exe.")

    ensure_package("pyinstaller", "PyInstaller")
    ensure_package("pillow", "PIL")  # lets PyInstaller convert logo.png -> .ico

    clean(CLEAN_PATHS)

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", APP_NAME,
        "--noconfirm",
        "--clean",
        "--onedir",                 # <-- explicit: one folder, NEVER --onefile
        "--contents-directory", ".",  # flatten: no hidden "_internal" folder,
                                       # everything sits openly next to the .exe
    ]

    cmd.append("--windowed" if WINDOWED else "--console")

    icon_path = ROOT / ICON_SOURCE
    if icon_path.exists():
        cmd += ["--icon", str(icon_path)]
    else:
        print(f"[build] NOTE: icon file not found ({icon_path}), skipping --icon")

    for extra in EXTRA_ANALYSIS_PATHS:
        if extra.exists():
            cmd += ["--paths", str(extra)]
        else:
            print(f"[build] WARNING: analysis path not found: {extra}")

    for src, dest in DATA_DIRS:
        src_path = ROOT / src
        if src_path.exists():
            cmd += ["--add-data", f"{src_path};{dest}"]
        else:
            print(f"[build] WARNING: data directory not found, skipping: {src_path}")

    for src, dest in DATA_FILES:
        src_path = ROOT / src
        if src_path.exists():
            cmd += ["--add-data", f"{src_path};{dest}"]
        else:
            print(f"[build] WARNING: data file not found, skipping: {src_path}")

    for pkg in COLLECT_ALL:
        cmd += ["--collect-all", pkg]

    for hidden in HIDDEN_IMPORTS:
        cmd += ["--hidden-import", hidden]

    cmd.append(ENTRY_POINT)

    run(cmd)

    dist_dir = ROOT / "dist" / APP_NAME
    exe_path = dist_dir / f"{APP_NAME}.exe"

    print()
    print("=" * 60)
    print("  BUILD COMPLETE")
    print(f"  Folder : {dist_dir}")
    print(f"  Run    : {exe_path}")
    print("=" * 60)


if __name__ == "__main__":
    try:
        build()
    except subprocess.CalledProcessError as exc:
        print(f"[build] PyInstaller failed with exit code {exc.returncode}")
        sys.exit(exc.returncode)

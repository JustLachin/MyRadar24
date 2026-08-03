# MyRadar24

DOWNLOAD LINK HERE: https://github.com/JustLachin/MyRadar24/releases/download/v1.0/MyRadar24.zip (JUST OPEN MyRadar42.exe file)


A desktop application for tracking flights in real time, built with **PyQt6** and powered by the **FlightRadar24 API**.

![MyRadar24](logo.png)

## Overview

MyRadar24 lets you keep a personal watchlist of flights — by flight number, callsign, or a scheduled (not-yet-departed) service — and automatically follows them from gate to landing. It polls live data, detects takeoff/landing events, plays sound and on-screen notifications, and keeps your list persisted across restarts.

## Features

### Flight Tracking
- Track an unlimited number of flights at the same time
- Search by flight number or callsign (e.g. `THY123`, `TK1983`)
- **Flight History** view — see a flight number's recent and upcoming operations, and add a future scheduled flight ahead of time; MyRadar24 automatically switches it to full live tracking as soon as FlightRadar24 assigns it a live ID
- Per-flight personal notes
- Reorder tracked flights (move up/down) and remove one or all at once
- Smart, tiered refresh: flights that haven't departed yet are polled faster than airborne/landed flights, so you get near real-time takeoff detection without hammering the API

### Flight Information
Displayed per flight: flight number, note, origin/destination (IATA), aircraft type & registration, scheduled/actual departure and arrival dates & times, live status (Not Departed / In Flight / Landed), ETA countdown, and time elapsed since landing.

### Notifications
- **Sound alerts** for takeoff, landing, early/late arrival warnings, and general UI actions (add, remove, select, buttons) — fully toggleable
- **In-app toast notifications** (bottom-right, non-blocking, no click-to-dismiss required)
- **System tray icon** with show/hide and quick exit
- Blinking row highlight when a flight is running notably early or late

### Customization
- **Multi-language UI**: English, Turkish, and Russian included, with the ability to **import your own JSON language file** at runtime
- Configurable refresh interval (5 / 30 / 120 seconds) and sound on/off via the Settings dialog
- Dark, modern Fusion-based theme throughout

### Persistence
- Tracked flights, notes, language, and sound preference are saved to `myradar24_settings.json` and restored automatically on the next launch

## Requirements

- Python 3.10+ (developed/tested on 3.10)
- Windows (uses `winsound` as a sound fallback; PyQt6's `QSoundEffect` is used as the primary audio backend)
- Dependencies listed in [`requirements.txt`](requirements.txt):
  - `PyQt6`, `PyQt6-Qt6`
  - `requests`, `curl-cffi`, `brotli`
- The [FlightRadar24 SDK](SDK) (bundled in this repository under `SDK/python`)

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/JustLachin/MyRadar24.git
cd MyRadar24
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

Or on Windows, just run `setup.bat`.

### 3. Run the application

```bash
python myradar24.py
```

Or on Windows, double-click `start.bat`.

## Building a Standalone Windows Executable

A ready-to-use build script is included: [`windows-build.py`](windows-build.py). It uses **PyInstaller** in **`--onedir`** mode (never `--onefile`), so the result is a plain, inspectable folder — the executable sits next to loose, visible resource files (sounds, locale JSON files, icon) and runtime DLLs, with nothing hidden away in a single opaque binary.

```bash
python windows-build.py
```

This will produce:

```
dist/MyRadar24/
├── MyRadar24.exe
├── logo.png
├── sound/SND01-sine-sound-pack/*.wav
├── locales/*.json
└── ... (Qt & Python runtime files)
```

The script automatically installs `pyinstaller` and `pillow` (used to convert the `.png` icon) if they're missing, and cleans previous `build/`/`dist/` output before each run.

## Usage

### Adding a flight
1. Click **Add Flight** (toolbar) or **Flight → Add Flight** (`Ctrl+N`)
2. Enter a flight number or callsign and search
3. Double-click a result, or select it and click **Add**

### Viewing flight history / adding a scheduled flight
1. Click **Flight History** (toolbar) or **Flight → Flight History** (`Ctrl+H`)
2. Browse past and upcoming operations for a flight number
3. Add an upcoming scheduled flight to start tracking it before it even departs

### Managing tracked flights
- Select a row and click **Remove** to untrack it, or **Remove All** to clear the whole list
- Use **Move Up** / **Move Down** to reorder rows
- Double-click the **Note** cell to attach a personal note to a flight
- Click **Refresh All** to force an immediate update

### Settings
Open **Settings** (menu or toolbar) to toggle sound notifications and change the refresh interval (5s / 30s / 120s).

### Changing language
Use the **Language** menu to switch between English, Türkçe, and Русский, or import a custom language file via **Language → Import Language…**.

### System tray
Closing/minimizing keeps MyRadar24 available from the system tray icon, from which you can restore the window or exit.

## Sound Pack

Notification sounds are provided by the bundled `SND01-sine-sound-pack` (see [`sound/`](sound)), mapped to events such as takeoff, landing, early/late caution, add/remove, and general UI interactions.

## Project Structure

See [`PROJECT_STRUCTURE.md`](PROJECT_STRUCTURE.md) for a full breakdown of the source layout, and [`FEATURES.md`](FEATURES.md) for a more detailed feature-by-feature overview.

```
MyRadar24/
├── myradar24.py            # Application entry point
├── windows-build.py        # PyInstaller (--onedir) build script
├── src/                    # Application source code
├── SDK/python/             # Bundled FlightRadar24 SDK
├── sound/                  # Notification sound effects
├── locales/                # UI translation files (en, ru, tr)
└── myradar24_settings.json # Persisted user settings (auto-created)
```

## Disclaimer & License

This project uses the community [FlightRadar24 SDK](SDK) to access flight data and is intended for personal, non-commercial, educational use. Please review FlightRadar24's terms of service before relying on this data for any other purpose. Refer to the SDK's own [LICENSE](SDK/LICENSE) for terms governing that component.

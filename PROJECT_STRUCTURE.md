# MyRadar24 - Project Structure

## Directory Layout

```
MyRadar24/
│
├── myradar24.py              # Main application entry point
├── test_app.py               # Module testing script
├── requirements.txt          # Python dependencies
├── setup.bat                 # Windows setup script
├── start.bat                 # Windows start script
│
├── README.md                 # English documentation
├── README.tr.md              # Turkish documentation
├── FEATURES.md               # Feature overview
├── USAGE_GUIDE.md           # User guide (EN/TR)
├── PROJECT_STRUCTURE.md     # This file
│
├── src/                      # Application source code
│   ├── __init__.py
│   ├── main_window.py        # Main application window
│   ├── add_flight_dialog.py  # Flight search and add dialog
│   ├── flight_tracker.py     # Flight tracking logic
│   ├── sound_manager.py      # Sound notification manager
│   └── translations.py       # Multi-language support
│
├── SDK/                      # FlightRadar24 SDK
│   └── python/
│       └── FlightRadarAPI/   # FlightRadar24 Python API
│           ├── __init__.py
│           ├── api.py        # Main API class
│           ├── core.py       # Core functionality
│           ├── entities/     # Data models
│           │   ├── airport.py
│           │   ├── entity.py
│           │   └── flight.py
│           ├── errors.py     # Error classes
│           ├── parsers.py    # HTML parsers
│           ├── request.py    # HTTP client
│           └── zones.py      # Geographic zones
│
└── sound/                    # Sound effects
    └── SND01-sine-sound-pack/
        ├── celebration.wav   # Takeoff notification
        ├── notification.wav  # Landing notification
        └── ... (other sounds)
```

## Module Descriptions

### Core Application Files

#### `myradar24.py`
- Application entry point
- Initializes QApplication
- Creates and displays MainWindow
- Sets application metadata

#### `src/main_window.py`
- Main application window (QMainWindow)
- Flight table display
- Menu bar (File, Language)
- Button controls (Add, Remove, Refresh)
- Update timers (5s for not departed, 30s for all)
- Flight state change handling
- Sound notification triggering

#### `src/add_flight_dialog.py`
- Flight search dialog (QDialog)
- Search input field
- Results list display
- Flight selection and addition
- Double-click quick add

#### `src/flight_tracker.py`
- FlightRadar24 API wrapper
- Flight tracking logic
- TrackedFlight class for state management
- Flight search functionality
- Flight update and state detection
- Time calculations (ETA, landed time)

#### `src/sound_manager.py`
- Sound effect management
- Windows winsound integration
- Takeoff sound playback
- Landing sound playback
- Error handling for missing files

#### `src/translations.py`
- Multi-language support
- Translation dictionary (EN/TR)
- Translator class
- Language switching
- Format string support

### Helper Files

#### `test_app.py`
- Module import testing
- Dependency verification
- Translation testing
- Pre-flight check

#### `setup.bat`
- Windows installation script
- Pip upgrade
- Dependency installation
- User instructions

#### `start.bat`
- Windows quick start script
- Launches application
- Pause after exit

## Data Flow

```
┌─────────────────────────────────────────────────────────────┐
│                        User Interface                        │
│                      (main_window.py)                        │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ├─> Add Flight Dialog
                   │   (add_flight_dialog.py)
                   │
                   ├─> Flight Tracker
                   │   (flight_tracker.py)
                   │   │
                   │   └─> FlightRadar24 API
                   │       (SDK/python/FlightRadarAPI/)
                   │
                   ├─> Sound Manager
                   │   (sound_manager.py)
                   │   │
                   │   └─> Sound Files
                   │       (sound/SND01-sine-sound-pack/)
                   │
                   └─> Translator
                       (translations.py)
```

## Update Flow

```
Timer Tick (5s or 30s)
    │
    ├─> Update Flight Data
    │   └─> API Request to FlightRadar24
    │       └─> Parse Response
    │           └─> Update TrackedFlight Object
    │
    ├─> Detect State Changes
    │   ├─> Just Departed?
    │   │   └─> Play Takeoff Sound
    │   │       └─> Show Notification
    │   │
    │   └─> Just Landed?
    │       └─> Play Landing Sound
    │           └─> Show Notification
    │
    └─> Update Table Display
        └─> Refresh All Cells
```

## Flight State Machine

```
┌──────────────┐
│ Not Departed │ (on_ground=1, altitude=0)
└──────┬───────┘
       │ Takeoff Event
       │ (altitude > 100, on_ground=0)
       │ → Play Takeoff Sound 🔊
       │
       ▼
┌──────────────┐
│   In Flight  │ (altitude > 0, on_ground=0)
└──────┬───────┘
       │ Landing Event
       │ (on_ground=1, has_departed=true)
       │ → Play Landing Sound 🔊
       │
       ▼
┌──────────────┐
│    Landed    │ (on_ground=1)
└──────────────┘
```

## Key Classes

### TrackedFlight
```python
Attributes:
- flight_id: str
- callsign: str
- flight_number: str
- origin: str
- destination: str
- aircraft_code: str
- registration: str
- has_departed: bool
- has_landed: bool
- scheduled_departure: timestamp
- actual_departure: timestamp
- scheduled_arrival: timestamp
- actual_arrival: timestamp
- estimated_arrival: timestamp

Methods:
- update_from_details(details: dict) -> dict
- get_eta_minutes() -> Optional[int]
- get_landed_minutes() -> Optional[int]
```

### FlightTracker
```python
Attributes:
- api: FlightRadar24API
- tracked_flights: Dict[str, TrackedFlight]

Methods:
- search_flight(query: str) -> list
- add_flight(flight_id: str) -> Optional[TrackedFlight]
- remove_flight(flight_id: str)
- update_flight(flight_id: str) -> Optional[dict]
- get_all_tracked_flights() -> Dict
```

### MainWindow
```python
Attributes:
- translator: Translator
- flight_tracker: FlightTracker
- sound_manager: SoundManager
- update_timer: QTimer (30s)
- not_departed_timer: QTimer (5s)
- table: QTableWidget

Methods:
- show_add_flight_dialog()
- add_flight_to_tracking(flight_id: str)
- remove_selected_flight()
- update_all_flights()
- update_not_departed_flights()
- handle_state_changes(flight_id: str, changes: dict)
- update_table_display()
```

## Configuration

### Update Intervals
- Not departed flights: 5000ms (5 seconds)
- All flights: 30000ms (30 seconds)

### Sound Files
- Takeoff: `sound/SND01-sine-sound-pack/celebration.wav`
- Landing: `sound/SND01-sine-sound-pack/notification.wav`

### Languages
- English (en)
- Turkish (tr)

## Dependencies

### Required Python Packages
- PyQt6 >= 6.4.0 (GUI framework)
- requests >= 2.28.0 (HTTP requests)
- curl-cffi >= 0.5.0 (Cloudflare bypass)
- brotli >= 1.0.0 (Compression)

### System Requirements
- Python 3.8 or higher
- Windows OS (for winsound)
- Internet connection (for API)

## API Integration

### FlightRadar24 SDK
- Location: `SDK/python/FlightRadarAPI/`
- Version: 1.5.1
- Methods Used:
  - `search(query, limit)` - Search flights
  - `get_flights()` - Get all live flights
  - `get_flight_details(flight)` - Get detailed info

### API Endpoints
- Real-time flight data
- Flight search
- Detailed flight information
- Time details (departure, arrival, ETA)

## Error Handling

### Network Errors
- Handled silently in flight_tracker.py
- Print to console for debugging
- Continue operation without crash

### Sound Errors
- Try/except in sound_manager.py
- Print error message
- Continue without sound

### Missing Data
- Display as "N/A" or "Unknown"
- Graceful degradation
- No application crash

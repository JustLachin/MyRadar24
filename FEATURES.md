# MyRadar24 - Feature Overview

## 🎯 Main Features

### 1. Live Flight Tracking
- Track unlimited number of flights simultaneously
- Real-time data updates from FlightRadar24
- Automatic refresh for all tracked flights every 30 seconds
- Enhanced refresh for not-departed flights every 5 seconds

### 2. Flight Information Display
| Column | Description |
|--------|-------------|
| Flight | Flight number or callsign (e.g., THY123, TK1983) |
| From | Origin airport IATA code |
| To | Destination airport IATA code |
| Aircraft | Aircraft type and registration number |
| Departure Time | Actual or scheduled departure time (HH:MM format) |
| Arrival Time | Actual or scheduled arrival time (HH:MM format) |
| Status | Current flight status (Not Departed / In Flight / Landed) |
| ETA | Estimated time to arrival (countdown timer) |
| Landed Since | Time elapsed since landing |

### 3. Flight Status Tracking

#### Not Departed
- Shows scheduled departure time
- Updates every 5 seconds
- Status changes automatically when flight takes off

#### In Flight
- Shows actual departure time
- Displays estimated time to arrival (ETA) in countdown format
- Examples: "45 min", "2h 15m"
- Updates every 30 seconds

#### Landed
- Shows actual arrival time
- Displays time elapsed since landing
- Examples: "Just now", "15 min", "1h 30m"
- ETA shows "00:00" when landed

### 4. Sound Notifications

#### Takeoff Alert
- Triggers when a tracked flight departs
- Sound: celebration.wav
- Shows popup notification with flight number

#### Landing Alert
- Triggers when a tracked flight lands (ETA reaches 00:00)
- Sound: notification.wav
- Shows popup notification with flight number

### 5. Multi-Language Support
- **English**: Full UI translation
- **Türkçe**: Full UI translation
- Switch language on-the-fly via menu
- All text updates immediately

### 6. Flight Search & Add
- Search by flight number (e.g., THY123)
- Search by callsign (e.g., TK1983)
- Shows live search results with:
  - Flight number
  - Callsign
  - Origin and destination
- Double-click or click "Add" to track

### 7. Flight Management
- Add flights to tracking list
- Remove selected flight
- Refresh all flights manually
- No limit on number of tracked flights

## 🎨 User Interface

### Main Window
- Clean, modern PyQt6 interface
- Sortable table with all flight information
- Resizable columns
- Single row selection

### Menu Bar
- **File Menu**
  - Exit application
- **Language Menu**
  - English
  - Türkçe

### Buttons
- **Add Flight**: Opens search dialog
- **Remove Flight**: Removes selected flight
- **Refresh All**: Manually refresh all flights

### Add Flight Dialog
- Search input field
- Search results list
- Add and Cancel buttons
- Double-click to add quickly

## 🔄 Update Intervals

| Condition | Update Frequency |
|-----------|------------------|
| Not departed flights | Every 5 seconds |
| All tracked flights | Every 30 seconds |
| Manual refresh | On button click |

## 🔊 Sound Pack

Uses SND01-sine-sound-pack:
- `celebration.wav` - Takeoff notification
- `notification.wav` - Landing notification

## 💡 Smart Features

1. **Automatic State Detection**
   - Detects when flight departs (altitude > 100ft and not on ground)
   - Detects when flight lands (on ground and has departed)
   - Prevents duplicate notifications

2. **Time Formatting**
   - Smart time display based on duration
   - Minutes only: "45 min"
   - Hours and minutes: "2h 15m"
   - Just landed: "Just now"

3. **Graceful Error Handling**
   - API errors handled silently
   - Sound errors don't crash app
   - Missing data shown as "Unknown" or "N/A"

## 🚀 Technical Details

- **Framework**: PyQt6 6.4.0+
- **API**: FlightRadar24 SDK (Python)
- **Sound**: Windows winsound (cross-platform compatible)
- **Language**: Python 3.8+

## 📋 Future Enhancement Ideas

- [ ] Airport information display
- [ ] Flight path visualization
- [ ] Historical flight data
- [ ] Export tracked flights to CSV
- [ ] Custom notification sounds
- [ ] Dark/Light theme toggle
- [ ] Save/Load tracking lists
- [ ] Push notifications to system tray
- [ ] Multiple airline filtering
- [ ] Aircraft type filtering

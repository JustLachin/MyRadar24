#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Flight tracker module — manages flight data and FlightRadar24 API communication.
"""

import sys
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List
from urllib.parse import quote

# Add SDK to path
sdk_path = Path(__file__).parent.parent / "SDK" / "python"
sys.path.insert(0, str(sdk_path))

from FlightRadarAPI import FlightRadar24API

from .flight_history import FlightHistoryEntry, parse_history_entry

# Constants extracted from FlightRadarAPI.core.Core to avoid a static-analysis
# import error (Core itself is only used for its string/dict constants below).
_FLIGHT_DATA_URL = "https://data-live.flightradar24.com/clickhandler/?flight={}"
_FLIGHT_LIST_URL = "https://api.flightradar24.com/common/v1/flight/list.json?query={}&fetchBy=flight&page={}&limit={}"
_JSON_HEADERS: Dict[str, str] = {
    "accept-encoding": "gzip, br",
    "accept-language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
    "cache-control": "max-age=0",
    "origin": "https://www.flightradar24.com",
    "referer": "https://www.flightradar24.com/",
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-site",
    "user-agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.86 Safari/537.36",
    "accept": "application/json",
}


class TrackedFlight:
    """Represents a single tracked flight and its current state."""

    # Minimum deviation (seconds) between estimated and scheduled arrival
    # before a flight is flagged as arriving noticeably early/late.
    DELAY_THRESHOLD_SECONDS = 120

    def __init__(self, flight_id: str, flight_data: Dict[str, Any]):
        self.flight_id = flight_id

        # Identification
        self.callsign: str = flight_data.get("callsign") or ""
        self.flight_number: str = flight_data.get("number") or ""

        # Route
        self.origin: str = flight_data.get("origin_airport_iata") or "N/A"
        self.destination: str = flight_data.get("destination_airport_iata") or "N/A"
        self.origin_name: Optional[str] = None
        self.destination_name: Optional[str] = None

        # Aircraft
        self.aircraft_code: str = flight_data.get("aircraft_code") or "N/A"
        self.registration: str = flight_data.get("registration") or "N/A"
        self.airline_iata: str = flight_data.get("airline_iata") or ""
        self.airline_icao: str = flight_data.get("airline_icao") or ""

        # Position
        self.altitude: int = int(flight_data.get("altitude") or 0)
        self.ground_speed: int = int(flight_data.get("ground_speed") or 0)
        self.on_ground: int = int(flight_data.get("on_ground") or 0)
        self.latitude: float = float(flight_data.get("latitude") or 0.0)
        self.longitude: float = float(flight_data.get("longitude") or 0.0)

        # Times (Unix timestamps)
        self.scheduled_departure: Optional[int] = None
        self.scheduled_arrival: Optional[int] = None
        self.actual_departure: Optional[int] = None
        self.actual_arrival: Optional[int] = None
        self.estimated_arrival: Optional[int] = None
        self.real_landing_time: Optional[datetime] = None  # When ETA reached 00:00

        # State
        self.has_departed: bool = False
        self.has_landed: bool = False
        self.status_text: str = ""
        self.last_update: datetime = datetime.now()
        
        # User note
        self.note: str = ""

        # Sound notification flags (fire once)
        self.notified_departure: bool = False
        self.notified_landing: bool = False

        # Scheduled-flight tracking (added ahead of departure, before FR24
        # has assigned it a live flight id).
        self.is_pending_schedule: bool = False
        self.schedule_number: str = ""
        self.schedule_row_id: Optional[int] = None
        self.resolved_flight_id: Optional[str] = None

        # Early/late arrival alert (ETA vs scheduled arrival deviation).
        # 'early' | 'late' | None. Blinking persists until acknowledged by
        # clicking the flight's row; the caution sound fires only once per
        # alert episode (not looped).
        self.delay_kind: Optional[str] = None
        self.delay_acknowledged_kind: Optional[str] = None
        self.delay_sound_played_kind: Optional[str] = None

    # ------------------------------------------------------------------
    # Update from API details
    # ------------------------------------------------------------------

    def update_from_details(self, details: Dict[str, Any]) -> Dict[str, bool]:
        """
        Update flight state from a detailed API response dict.
        Returns dict with 'just_departed' and 'just_landed' booleans.
        """
        old_departed = self.has_departed
        old_landed = self.has_landed

        try:
            # --- Identification ---
            ident = details.get("identification", {})
            if ident.get("callsign"):
                self.callsign = ident["callsign"]
            num = ident.get("number", {})
            if isinstance(num, dict) and num.get("default"):
                self.flight_number = num["default"]

            # --- Airline ---
            airline = details.get("airline", {})
            if airline.get("code", {}).get("iata"):
                self.airline_iata = airline["code"]["iata"]
            if airline.get("code", {}).get("icao"):
                self.airline_icao = airline["code"]["icao"]

            # --- Airport ---
            airport = details.get("airport", {})
            origin = airport.get("origin") or {}
            dest = airport.get("destination") or {}

            if origin.get("code", {}).get("iata"):
                self.origin = origin["code"]["iata"]
            if origin.get("name"):
                self.origin_name = origin["name"]
            if dest.get("code", {}).get("iata"):
                self.destination = dest["code"]["iata"]
            if dest.get("name"):
                self.destination_name = dest["name"]

            # --- Aircraft ---
            aircraft = details.get("aircraft") or {}
            if aircraft.get("model", {}).get("code"):
                self.aircraft_code = aircraft["model"]["code"]
            if aircraft.get("registration"):
                self.registration = aircraft["registration"]

            # --- Times ---
            time_info = details.get("time") or {}
            scheduled = time_info.get("scheduled") or {}
            real = time_info.get("real") or {}
            estimated = time_info.get("estimated") or {}
            other = time_info.get("other") or {}

            self.scheduled_departure = scheduled.get("departure") or self.scheduled_departure
            self.scheduled_arrival   = scheduled.get("arrival")   or self.scheduled_arrival
            self.actual_departure    = real.get("departure")       or self.actual_departure
            self.actual_arrival      = real.get("arrival")         or self.actual_arrival

            # ETA priority: estimated.arrival > other.eta > scheduled.arrival (if not landed)
            if estimated.get("arrival"):
                self.estimated_arrival = estimated["arrival"]
            elif other.get("eta"):
                self.estimated_arrival = other["eta"]
            elif self.scheduled_arrival and not self.actual_arrival:
                self.estimated_arrival = self.scheduled_arrival

            # --- Status text ---
            status = details.get("status") or {}
            self.status_text = (status.get("text") or "").lower()

            # --- Trail (latest position) ---
            trail = details.get("trail") or []
            if trail:
                latest = trail[-1]
                if latest.get("alt") is not None:
                    self.altitude = int(latest["alt"])
                if latest.get("spd") is not None:
                    self.ground_speed = int(latest["spd"])
                if latest.get("lat") is not None:
                    self.latitude = float(latest["lat"])
                if latest.get("lng") is not None:
                    self.longitude = float(latest["lng"])

            # --- Derive state ---
            is_landed_by_status = any(w in self.status_text for w in ("landed", "arrived"))
            is_flying_by_status = any(w in self.status_text for w in ("airborne", "en route", "cruising", "flight"))

            if is_landed_by_status or self.actual_arrival:
                self.on_ground = 1
            elif is_flying_by_status and self.altitude > 100:
                self.on_ground = 0

            self.has_departed = bool(
                self.actual_departure
                or (self.on_ground == 0 and self.altitude > 100)
                or is_flying_by_status
                or (self.estimated_arrival and "estimated" in self.status_text)
            )

            self.has_landed = bool(
                self.actual_arrival
                or is_landed_by_status
            )

            self.last_update = datetime.now()

        except Exception as e:
            print(f"[TrackedFlight] update_from_details error: {e}")
            import traceback
            traceback.print_exc()

        self.refresh_delay_state()

        return {
            "just_departed": self.has_departed and not old_departed,
            "just_landed":   self.has_landed   and not old_landed,
        }

    # ------------------------------------------------------------------
    # Update from flight-history / schedule entry
    # ------------------------------------------------------------------

    def update_from_history_entry(self, entry: "FlightHistoryEntry") -> Dict[str, bool]:
        """
        Update flight state from a FlightHistoryEntry (recent/scheduled flight
        list). Used for flights added ahead of departure that don't have a
        live FR24 flight id yet. Once the entry resolves a real flight id,
        this flight is promoted to full live tracking automatically.
        Returns dict with 'just_departed' and 'just_landed' booleans.
        """
        old_departed = self.has_departed
        old_landed = self.has_landed

        try:
            if entry.callsign:
                self.callsign = entry.callsign
            if entry.flight_number:
                self.flight_number = entry.flight_number

            if entry.origin_iata and entry.origin_iata != "N/A":
                self.origin = entry.origin_iata
            if entry.origin_name:
                self.origin_name = entry.origin_name
            if entry.destination_iata and entry.destination_iata != "N/A":
                self.destination = entry.destination_iata
            if entry.destination_name:
                self.destination_name = entry.destination_name

            if entry.aircraft_code and entry.aircraft_code != "N/A":
                self.aircraft_code = entry.aircraft_code
            if entry.registration and entry.registration != "N/A":
                self.registration = entry.registration
            if entry.airline_iata:
                self.airline_iata = entry.airline_iata
            if entry.airline_icao:
                self.airline_icao = entry.airline_icao

            self.scheduled_departure = entry.scheduled_departure or self.scheduled_departure
            self.scheduled_arrival   = entry.scheduled_arrival   or self.scheduled_arrival
            self.actual_departure    = entry.actual_departure    or self.actual_departure
            self.actual_arrival      = entry.actual_arrival      or self.actual_arrival

            if entry.estimated_arrival:
                self.estimated_arrival = entry.estimated_arrival
            elif self.scheduled_arrival and not self.actual_arrival:
                self.estimated_arrival = self.scheduled_arrival

            self.status_text = (entry.status_text or self.status_text or "").lower()

            # Promote to live tracking once FR24 assigns a real flight id.
            if entry.flight_id:
                self.resolved_flight_id = entry.flight_id
                self.is_pending_schedule = False

            self.has_departed = bool(entry.is_departed() or self.actual_departure)
            self.has_landed = bool(entry.is_landed() or self.actual_arrival)

            self.last_update = datetime.now()

        except Exception as e:
            print(f"[TrackedFlight] update_from_history_entry error: {e}")

        self.refresh_delay_state()

        return {
            "just_departed": self.has_departed and not old_departed,
            "just_landed":   self.has_landed   and not old_landed,
        }

    # ------------------------------------------------------------------
    # ETA helpers
    # ------------------------------------------------------------------

    def get_eta_seconds(self) -> Optional[int]:
        """Return seconds until arrival, or None if unknown, or 0 if landed."""
        if self.has_landed:
            return 0
        if not self.has_departed:
            return None
        if self.estimated_arrival:
            try:
                delta = datetime.fromtimestamp(self.estimated_arrival) - datetime.now()
                remaining = max(0, int(delta.total_seconds()))
                
                # IMPORTANT: If ETA reaches 0, mark as landed and record time!
                if remaining == 0 and not self.has_landed:
                    self.has_landed = True
                    if not self.real_landing_time:
                        self.real_landing_time = datetime.now()
                        print(f"✈️ REAL LANDING TIME RECORDED: {self.real_landing_time.strftime('%H:%M:%S')}")
                
                return remaining
            except Exception:
                pass
        return None

    def get_eta_text(self) -> str:
        """Live ETA countdown string with estimated landing time (HH:MM:SS (HH:MM))."""
        secs = self.get_eta_seconds()
        if secs is None:
            return "—"
        if secs == 0:
            return "00:00"
        
        # Calculate countdown
        h = secs // 3600
        m = (secs % 3600) // 60
        s = secs % 60
        
        # Calculate estimated landing time
        landing_time = ""
        if self.estimated_arrival:
            try:
                dt = datetime.fromtimestamp(self.estimated_arrival)
                landing_time = f" ({dt.strftime('%H:%M')})"
            except:
                pass
        
        if h > 0:
            return f"{h}:{m:02d}:{s:02d}{landing_time}"
        return f"{m:02d}:{s:02d}{landing_time}"

    # ------------------------------------------------------------------
    # Early / late arrival alert
    # ------------------------------------------------------------------

    def compute_delay_kind(self) -> Optional[str]:
        """
        Classify the current ETA vs scheduled-arrival deviation.
        Returns 'early' if the flight is estimated to land 2+ minutes ahead
        of schedule, 'late' if 2+ minutes behind, otherwise None.
        Only meaningful while airborne (departed, not yet landed).
        """
        if not self.has_departed or self.has_landed:
            return None
        if not self.estimated_arrival or not self.scheduled_arrival:
            return None

        diff = self.scheduled_arrival - self.estimated_arrival  # >0 early, <0 late
        if diff >= self.DELAY_THRESHOLD_SECONDS:
            return "early"
        if diff <= -self.DELAY_THRESHOLD_SECONDS:
            return "late"
        return None

    def refresh_delay_state(self) -> None:
        """Recompute delay_kind. Clears acknowledgement + played-sound flags
        once back on time / landed, so a future deviation triggers a fresh
        alert (blink + a new one-shot caution sound)."""
        self.delay_kind = self.compute_delay_kind()
        if self.delay_kind is None:
            self.delay_acknowledged_kind = None
            self.delay_sound_played_kind = None

    def has_active_delay_alert(self) -> bool:
        """True while there's an unacknowledged early/late deviation
        (controls row blinking)."""
        return self.delay_kind is not None and self.delay_kind != self.delay_acknowledged_kind

    def acknowledge_delay_alert(self) -> None:
        """Silence the current alert (called when the user clicks the row)."""
        self.delay_acknowledged_kind = self.delay_kind

    def should_play_delay_sound(self) -> bool:
        """True exactly once per new alert episode — used to fire the
        caution sound a single time (not looped) even though blinking
        continues until acknowledged."""
        return self.delay_kind is not None and self.delay_kind != self.delay_sound_played_kind

    def mark_delay_sound_played(self) -> None:
        """Record that the caution sound has already fired for this episode."""
        self.delay_sound_played_kind = self.delay_kind

    # ------------------------------------------------------------------
    # Landed-since helpers
    # ------------------------------------------------------------------

    def get_landed_seconds(self) -> Optional[int]:
        """Return seconds since landing, or None if not yet landed."""
        if not self.has_landed:
            return None
        
        # Priority 1: Use real_landing_time (when ETA reached 00:00)
        if self.real_landing_time:
            try:
                delta = datetime.now() - self.real_landing_time
                return max(0, int(delta.total_seconds()))
            except Exception:
                pass
        
        # Priority 2: Use actual_arrival from API
        if self.actual_arrival:
            try:
                delta = datetime.now() - datetime.fromtimestamp(self.actual_arrival)
                return max(0, int(delta.total_seconds()))
            except Exception:
                pass
        
        return 0

    def get_landed_text(self) -> str:
        """Human-readable string of how long since landing."""
        secs = self.get_landed_seconds()
        if secs is None:
            return "—"
        if secs < 60:
            return f"{secs}s"
        h = secs // 3600
        m = (secs % 3600) // 60
        s = secs % 60
        if h > 0:
            return f"{h}h {m:02d}m {s:02d}s"
        return f"{m:02d}m {s:02d}s"
    
    def get_landed_time_static(self) -> str:
        """
        Return STATIC landing time (HH:MM:SS format).
        Priority: real_landing_time > actual_arrival
        This is NOT a countdown - it's the actual time the plane landed!
        """
        if not self.has_landed:
            return "—"
        
        # Priority 1: Use real_landing_time (when ETA reached 00:00)
        if self.real_landing_time:
            return self.real_landing_time.strftime("%H:%M:%S")
        
        # Priority 2: Use actual_arrival from API
        if self.actual_arrival:
            try:
                dt = datetime.fromtimestamp(self.actual_arrival)
                return dt.strftime("%H:%M:%S")
            except Exception:
                pass
        
        return "—"

    # ------------------------------------------------------------------
    # Time formatting helpers
    # ------------------------------------------------------------------

    def format_time(self, timestamp: Optional[int], fmt: str = "%H:%M") -> str:
        if not timestamp:
            return "—"
        try:
            return datetime.fromtimestamp(timestamp).strftime(fmt)
        except Exception:
            return "—"

    def get_departure_display(self) -> str:
        ts = self.actual_departure or self.scheduled_departure
        return self.format_time(ts)

    def get_arrival_display(self) -> str:
        ts = self.actual_arrival or self.scheduled_arrival
        return self.format_time(ts)

    def get_date_display(self, timestamp: int | None) -> str:
        """Return dual-format date: DD/MM/YYYY\nDayName / DD / MonthName"""
        if not timestamp:
            return "—"
        try:
            dt = datetime.fromtimestamp(timestamp)
            day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            month_names = ["January", "February", "March", "April", "May", "June",
                          "July", "August", "September", "October", "November", "December"]
            numeric = dt.strftime("%d/%m/%Y")
            text = f"{day_names[dt.weekday()]} / {dt.day:02d} / {month_names[dt.month - 1]}"
            return f"{numeric}\n{text}"
        except Exception:
            return "—"

    def get_departure_date_display(self) -> str:
        ts = self.actual_departure or self.scheduled_departure
        return self.get_date_display(ts)

    def get_arrival_date_display(self) -> str:
        ts = self.actual_arrival or self.scheduled_arrival
        return self.get_date_display(ts)

    # ------------------------------------------------------------------
    # Display name
    # ------------------------------------------------------------------

    def display_name(self) -> str:
        return self.callsign or self.flight_number or self.flight_id

    def get_fr24_url_slug(self) -> str:
        """Return the best identifier to build a flightradar24.com/data/flights/ URL.
        Falls back to the flight number for flights that don't have a
        resolved live flight id yet (pending scheduled flights).
        """
        return self.resolved_flight_id or (self.flight_id if not self.is_pending_schedule else None) or self.flight_number or self.flight_id


# ======================================================================
# FlightTracker
# ======================================================================

class FlightTracker:
    """Main class: manages API access and collection of tracked flights."""

    def __init__(self):
        self.api = FlightRadar24API()
        self.tracked_flights: Dict[str, TrackedFlight] = {}

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    def search_flight(self, query: str) -> list[Dict[str, Any]]:
        """Search FlightRadar24 for flights matching query."""
        try:
            results = self.api.search(query, limit=30)
            flights = []
            if isinstance(results, dict):
                flights.extend(results.get("live", []))
                flights.extend(results.get("schedule", []))
                flights.extend(results.get("stats", []))
            return flights
        except Exception as e:
            print(f"[FlightTracker] search error: {e}")
            return []

    # ------------------------------------------------------------------
    # Add / Remove
    # ------------------------------------------------------------------

    def add_flight(self, flight_id: str, search_result: Optional[Dict[str, Any]] = None) -> Optional[TrackedFlight]:
        """Add a flight to the tracked list. Returns the TrackedFlight or None."""
        if flight_id in self.tracked_flights:
            return self.tracked_flights[flight_id]

        # Build initial data from search result or minimal placeholder
        if search_result:
            detail = search_result.get("detail") or {}
            flight_data = {
                "id": flight_id,
                "callsign": detail.get("callsign") or flight_id,
                "number":   detail.get("flight")   or flight_id,
                "origin_airport_iata":      detail.get("dep") or detail.get("origin") or "N/A",
                "destination_airport_iata": detail.get("arr") or detail.get("destination") or "N/A",
                "aircraft_code": "N/A",
                "registration":  "N/A",
                "altitude": 0, "ground_speed": 0, "on_ground": 1,
            }
        else:
            flight_data = self._fetch_basic_data(flight_id)
            if not flight_data:
                return None

        tracked = TrackedFlight(flight_id, flight_data)

        # Fetch full details immediately
        details = self._fetch_details(flight_id)
        if details:
            tracked.update_from_details(details)

        self.tracked_flights[flight_id] = tracked
        return tracked

    def remove_flight(self, flight_id: str):
        self.tracked_flights.pop(flight_id, None)

    # ------------------------------------------------------------------
    # Flight history / scheduled flights
    # ------------------------------------------------------------------

    def get_flight_history(self, flight_number: str, page: int = 1, limit: int = 100) -> List[FlightHistoryEntry]:
        """
        Fetch recent + scheduled/upcoming operations for a flight number
        (e.g. 'TK1983'). Mirrors the data shown on FlightRadar24's
        "Flight history for <number>" page: date, route, aircraft,
        STD/ATD/STA and status — for both past and future dates.
        """
        query = (flight_number or "").strip().upper()
        if not query:
            return []
        try:
            url = _FLIGHT_LIST_URL.format(quote(query), page, limit)
            client: Any = getattr(self.api, '_FlightRadar24API__client', None)  # type: ignore[arg-type]
            if client is None:
                return []
            response = client.request(url, headers=_JSON_HEADERS, timeout=self.api.timeout)
            data = response.get_json_content()
            items = (((data.get("result") or {}).get("response") or {}).get("data")) or []
            entries: List[FlightHistoryEntry] = []
            for raw in items:
                try:
                    entries.append(parse_history_entry(raw))
                except Exception:
                    continue
            return entries
        except Exception as e:
            print(f"[FlightTracker] get_flight_history error: {e}")
            return []

    @staticmethod
    def make_schedule_tracking_id(flight_number: str, row_id: Optional[int]) -> str:
        return f"sched:{flight_number.upper()}:{row_id}"

    def add_scheduled_flight(self, entry: FlightHistoryEntry) -> Optional[TrackedFlight]:
        """
        Add a flight-history entry to tracking. Works for any row returned by
        get_flight_history(): a future scheduled operation (no live id yet —
        will auto-upgrade to live tracking once FR24 assigns one), a
        currently live flight, or a past/landed one.
        """
        if entry.flight_id:
            # Already resolvable — behaves just like a normal add_flight().
            return self.add_flight(entry.flight_id)

        if not entry.flight_number:
            return None

        tracking_id = self.make_schedule_tracking_id(entry.flight_number, entry.row_id)
        if tracking_id in self.tracked_flights:
            return self.tracked_flights[tracking_id]

        flight_data = {
            "id": tracking_id,
            "callsign": entry.callsign or entry.flight_number,
            "number": entry.flight_number,
            "origin_airport_iata": entry.origin_iata or "N/A",
            "destination_airport_iata": entry.destination_iata or "N/A",
            "aircraft_code": entry.aircraft_code or "N/A",
            "registration": entry.registration or "N/A",
            "altitude": 0, "ground_speed": 0, "on_ground": 1,
        }
        tracked = TrackedFlight(tracking_id, flight_data)
        tracked.is_pending_schedule = True
        tracked.schedule_number = entry.flight_number
        tracked.schedule_row_id = entry.row_id
        tracked.update_from_history_entry(entry)

        self.tracked_flights[tracking_id] = tracked
        return tracked

    def restore_scheduled_flight(
        self,
        tracking_id: str,
        schedule_number: str,
        schedule_row_id: Optional[int],
        resolved_flight_id: Optional[str] = None,
    ) -> Optional[TrackedFlight]:
        """Recreate a pending-schedule TrackedFlight from persisted settings."""
        if tracking_id in self.tracked_flights:
            return self.tracked_flights[tracking_id]

        flight_data = {
            "id": tracking_id,
            "callsign": schedule_number,
            "number": schedule_number,
            "origin_airport_iata": "N/A",
            "destination_airport_iata": "N/A",
            "aircraft_code": "N/A",
            "registration": "N/A",
            "altitude": 0, "ground_speed": 0, "on_ground": 1,
        }
        tracked = TrackedFlight(tracking_id, flight_data)
        tracked.schedule_number = schedule_number
        tracked.schedule_row_id = schedule_row_id
        tracked.resolved_flight_id = resolved_flight_id
        tracked.is_pending_schedule = resolved_flight_id is None
        self.tracked_flights[tracking_id] = tracked

        # Immediately refresh so the row has real data on first paint.
        self.update_flight(tracking_id)
        return tracked

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def update_flight(self, flight_id: str) -> Optional[Dict[str, bool]]:
        """
        Refresh data for one tracked flight.
        Returns state-change dict {'just_departed', 'just_landed'} or None.
        """
        tracked = self.tracked_flights.get(flight_id)
        if not tracked:
            return None

        # Resolved (or normal) flight: use the real FR24 id for live details.
        real_id = tracked.resolved_flight_id or (None if tracked.is_pending_schedule else flight_id)
        if real_id:
            details = self._fetch_details(real_id)
            if details:
                return tracked.update_from_details(details)
            return {"just_departed": False, "just_landed": False}

        # Still pending schedule: poll the flight-number history list to see
        # if a live flight id has been assigned yet, and refresh schedule data.
        if tracked.is_pending_schedule and tracked.schedule_number:
            entries = self.get_flight_history(tracked.schedule_number, limit=30)
            match = None
            if tracked.schedule_row_id is not None:
                match = next((e for e in entries if e.row_id == tracked.schedule_row_id), None)
            if match:
                return tracked.update_from_history_entry(match)

        return {"just_departed": False, "just_landed": False}

    def update_all(self) -> Dict[str, Dict[str, bool]]:
        """Update every tracked flight. Returns {flight_id: state_changes}."""
        changes = {}
        for fid in list(self.tracked_flights.keys()):
            result = self.update_flight(fid)
            if result:
                changes[fid] = result
        return changes

    def update_not_departed(self) -> Dict[str, Dict[str, bool]]:
        """Update only flights that haven't departed yet."""
        changes = {}
        for fid, tracked in list(self.tracked_flights.items()):
            if not tracked.has_departed:
                result = self.update_flight(fid)
                if result:
                    changes[fid] = result
        return changes

    def get_all_tracked(self) -> Dict[str, TrackedFlight]:
        return self.tracked_flights

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _fetch_details(self, flight_id: str) -> Optional[Dict[str, Any]]:
        """Call the click-handler endpoint for a specific flight ID."""
        try:
            url = _FLIGHT_DATA_URL.format(flight_id)
            client: Any = getattr(self.api, '_FlightRadar24API__client', None)  # type: ignore[arg-type]
            if client is None:
                return None
            response = client.request(
                url,
                headers=_JSON_HEADERS,
                timeout=self.api.timeout,
            )
            data = response.get_json_content()
            if data and len(data) > 0:
                return data
        except Exception:
            # Silently ignore update errors (network, rate-limit, etc.)
            pass
        return None

    def _fetch_basic_data(self, flight_id: str) -> Optional[Dict[str, Any]]:
        """Try to build basic flight_data dict via details or live list."""
        details = self._fetch_details(flight_id)
        if details:
            airport = details.get("airport") or {}
            origin  = airport.get("origin") or {}
            dest    = airport.get("destination") or {}
            aircraft = details.get("aircraft") or {}
            ident    = details.get("identification") or {}
            number   = ident.get("number") or {}
            return {
                "id": flight_id,
                "callsign": ident.get("callsign") or flight_id,
                "number":   number.get("default") or flight_id,
                "origin_airport_iata":      (origin.get("code") or {}).get("iata") or "N/A",
                "destination_airport_iata": (dest.get("code") or {}).get("iata") or "N/A",
                "aircraft_code": (aircraft.get("model") or {}).get("code") or "N/A",
                "registration":  aircraft.get("registration") or "N/A",
                "altitude": 0, "ground_speed": 0, "on_ground": 1,
            }

        # Minimal placeholder so we can still track it
        return {
            "id": flight_id, "callsign": flight_id, "number": flight_id,
            "origin_airport_iata": "N/A", "destination_airport_iata": "N/A",
            "aircraft_code": "N/A", "registration": "N/A",
            "altitude": 0, "ground_speed": 0, "on_ground": 1,
        }

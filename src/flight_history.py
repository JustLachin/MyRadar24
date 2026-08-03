#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Flight history module — models and parsing for the FlightRadar24
"Flight history for <number>" data (recent + scheduled/upcoming flights
for a given flight number).
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional


@dataclass
class FlightHistoryEntry:
    """A single row of flight-number history: one specific date's operation
    of a flight number. May represent a past (landed), live (airborne), or
    future (scheduled, not yet assigned a live flight id) operation.
    """

    flight_number: str = ""
    row_id: Optional[int] = None          # Stable identifier for this specific
                                           # scheduled operation (persists even
                                           # before a live flight id exists).
    flight_id: Optional[str] = None       # FR24 hex flight id, only present
                                           # once the flight is trackable live.
    callsign: str = ""

    airline_name: str = ""
    airline_iata: str = ""
    airline_icao: str = ""

    origin_iata: str = "N/A"
    origin_name: str = ""
    origin_tz_offset: Optional[int] = None   # seconds from UTC

    destination_iata: str = "N/A"
    destination_name: str = ""
    destination_tz_offset: Optional[int] = None  # seconds from UTC

    aircraft_code: str = "N/A"
    aircraft_text: str = ""
    registration: str = "N/A"

    scheduled_departure: Optional[int] = None
    scheduled_arrival: Optional[int] = None
    actual_departure: Optional[int] = None
    actual_arrival: Optional[int] = None
    estimated_departure: Optional[int] = None
    estimated_arrival: Optional[int] = None
    duration_seconds: Optional[int] = None

    status_text: str = ""          # Human readable, e.g. "Landed 17:28"
    status_type: str = ""          # "departure" | "arrival" | ""
    status_generic: str = ""       # "scheduled" | "estimated" | "landed" | "canceled" | ...
    live: bool = False

    # ------------------------------------------------------------------
    # State helpers
    # ------------------------------------------------------------------

    def is_pending_schedule(self) -> bool:
        """True if this operation has no live flight id yet (purely scheduled)."""
        return not self.flight_id

    def is_cancelled(self) -> bool:
        return self.status_generic in ("canceled", "cancelled")

    def is_departed(self) -> bool:
        return bool(self.actual_departure) or self.status_type == "arrival"

    def is_landed(self) -> bool:
        return self.status_generic == "landed" or bool(self.actual_arrival)

    def is_live(self) -> bool:
        return self.live or (self.is_departed() and not self.is_landed())

    # ------------------------------------------------------------------
    # Formatting helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _fmt(ts: Optional[int], tz_offset: Optional[int], fmt: str) -> str:
        if not ts:
            return "—"
        try:
            if tz_offset is not None:
                dt = datetime.fromtimestamp(ts, tz=timezone(timedelta(seconds=tz_offset)))
            else:
                dt = datetime.fromtimestamp(ts)
            return dt.strftime(fmt)
        except Exception:
            return "—"

    def get_date_display(self) -> str:
        """Date of the (origin-local) scheduled departure, e.g. '03/08/2026 (Mon)'."""
        ts = self.scheduled_departure or self.actual_departure
        if not ts:
            return "—"
        try:
            if self.origin_tz_offset is not None:
                dt = datetime.fromtimestamp(ts, tz=timezone(timedelta(seconds=self.origin_tz_offset)))
            else:
                dt = datetime.fromtimestamp(ts)
            days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
            return f"{dt.strftime('%d/%m/%Y')} ({days[dt.weekday()]})"
        except Exception:
            return "—"

    def get_std_display(self) -> str:
        """Scheduled Time of Departure (origin-local)."""
        return self._fmt(self.scheduled_departure, self.origin_tz_offset, "%H:%M")

    def get_atd_display(self) -> str:
        """Actual Time of Departure (origin-local)."""
        return self._fmt(self.actual_departure, self.origin_tz_offset, "%H:%M")

    def get_etd_display(self) -> str:
        """Estimated Time of Departure (origin-local)."""
        return self._fmt(self.estimated_departure, self.origin_tz_offset, "%H:%M")

    def get_sta_display(self) -> str:
        """Scheduled Time of Arrival (destination-local)."""
        return self._fmt(self.scheduled_arrival, self.destination_tz_offset, "%H:%M")

    def get_ata_display(self) -> str:
        """Actual Time of Arrival (destination-local)."""
        return self._fmt(self.actual_arrival, self.destination_tz_offset, "%H:%M")

    def get_eta_display(self) -> str:
        """Estimated Time of Arrival (destination-local)."""
        return self._fmt(self.estimated_arrival, self.destination_tz_offset, "%H:%M")

    def get_flight_time_display(self) -> str:
        """Total flight duration, e.g. '9h 42m'."""
        secs = self.duration_seconds
        if secs is None:
            if self.actual_departure and self.actual_arrival:
                secs = self.actual_arrival - self.actual_departure
            elif self.scheduled_departure and self.scheduled_arrival:
                secs = self.scheduled_arrival - self.scheduled_departure
        if not secs or secs <= 0:
            return "—"
        h = secs // 3600
        m = (secs % 3600) // 60
        if h > 0:
            return f"{h}h {m:02d}m"
        return f"{m}m"

    def get_aircraft_display(self) -> str:
        code = self.aircraft_code or "N/A"
        if self.registration and self.registration != "N/A":
            return f"{code}  ({self.registration})"
        return code

    def get_route_display(self) -> str:
        return f"{self.origin_iata} → {self.destination_iata}"


def parse_history_entry(raw: Dict[str, Any]) -> FlightHistoryEntry:
    """Parse one raw item from the FR24 flight/list.json 'data' array."""
    ident = raw.get("identification") or {}
    number = ident.get("number") or {}

    status = raw.get("status") or {}
    generic = status.get("generic") or {}
    generic_status = generic.get("status") or {}

    aircraft = raw.get("aircraft") or {}
    model = aircraft.get("model") or {}

    airline = raw.get("airline") or raw.get("owner") or {}
    airline_code = airline.get("code") or {} if isinstance(airline, dict) else {}

    airport = raw.get("airport") or {}
    origin = airport.get("origin") or {}
    destination = airport.get("destination") or {}
    origin_code = origin.get("code") or {}
    dest_code = destination.get("code") or {}
    origin_tz = origin.get("timezone") or {}
    dest_tz = destination.get("timezone") or {}

    time_info = raw.get("time") or {}
    scheduled = time_info.get("scheduled") or {}
    real = time_info.get("real") or {}
    estimated = time_info.get("estimated") or {}
    other = time_info.get("other") or {}

    return FlightHistoryEntry(
        flight_number=number.get("default") or "",
        row_id=ident.get("row"),
        flight_id=ident.get("id"),
        callsign=ident.get("callsign") or "",

        airline_name=airline.get("name") or "" if isinstance(airline, dict) else "",
        airline_iata=airline_code.get("iata") or "",
        airline_icao=airline_code.get("icao") or "",

        origin_iata=origin_code.get("iata") or "N/A",
        origin_name=origin.get("name") or "",
        origin_tz_offset=origin_tz.get("offset"),

        destination_iata=dest_code.get("iata") or "N/A",
        destination_name=destination.get("name") or "",
        destination_tz_offset=dest_tz.get("offset"),

        aircraft_code=model.get("code") or "N/A",
        aircraft_text=model.get("text") or "",
        registration=aircraft.get("registration") or "N/A",

        scheduled_departure=scheduled.get("departure"),
        scheduled_arrival=scheduled.get("arrival"),
        actual_departure=real.get("departure"),
        actual_arrival=real.get("arrival"),
        estimated_departure=estimated.get("departure"),
        estimated_arrival=estimated.get("arrival"),
        duration_seconds=other.get("duration"),

        status_text=status.get("text") or "",
        status_type=generic_status.get("type") or "",
        status_generic=(generic_status.get("text") or "").lower(),
        live=bool(status.get("live")),
    )

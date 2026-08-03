#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test FlightRadar24 API responses - Check ETA data for commercial flights
"""

import sys
from pathlib import Path

# Add SDK to path
sdk_path = Path(__file__).parent / "SDK" / "python"
sys.path.insert(0, str(sdk_path))

from FlightRadarAPI import FlightRadar24API
from FlightRadarAPI.core import Core
import json
from datetime import datetime

print("="*60)
print("Testing FlightRadar24 ETA Data - Commercial Flights")
print("="*60)

api = FlightRadar24API()

# Test 1: Get live flights with valid origin/destination (commercial flights)
print("\n1. Getting commercial flights...")
flights = api.get_flights()
print(f"Found {len(flights)} total flights")

# Filter for commercial flights (has origin and destination)
commercial_flights = [
    f for f in flights 
    if f.altitude > 5000 
    and f.on_ground == 0 
    and f.origin_airport_iata 
    and f.destination_airport_iata
    and f.origin_airport_iata != 'N/A'
    and f.destination_airport_iata != 'N/A'
]
print(f"Found {len(commercial_flights)} commercial flights")

# Try first 3 flights
for i, test_flight in enumerate(commercial_flights[:3]):
    flight_id = test_flight.id
    
    print(f"\n{'='*60}")
    print(f"Flight {i+1}: {flight_id}")
    print(f"Callsign: {test_flight.callsign}")
    print(f"Number: {test_flight.number}")
    print(f"Route: {test_flight.origin_airport_iata} → {test_flight.destination_airport_iata}")
    print(f"Altitude: {test_flight.altitude} ft")
    print(f"Ground speed: {test_flight.ground_speed} kt")
    
    # Get details
    try:
        details = api.get_flight_details(test_flight)
        
        # Check time field
        if 'time' in details:
            time_data = details['time']
            
            # Check all ETA sources
            eta_found = False
            
            # Source 1: estimated.arrival
            if time_data.get('estimated', {}).get('arrival'):
                eta_timestamp = time_data['estimated']['arrival']
                print(f"✓ ETA found in estimated.arrival: {eta_timestamp}")
                eta_time = datetime.fromtimestamp(eta_timestamp)
                now = datetime.now()
                remaining = eta_time - now
                total_seconds = int(remaining.total_seconds())
                hours = total_seconds // 3600
                minutes = (total_seconds % 3600) // 60
                seconds = total_seconds % 60
                print(f"  Arrival time: {eta_time.strftime('%H:%M:%S')}")
                print(f"  Time remaining: {hours}h {minutes}m {seconds}s")
                eta_found = True
            
            # Source 2: other.eta
            if time_data.get('other', {}).get('eta'):
                other_eta = time_data['other']['eta']
                print(f"✓ ETA found in other.eta: {other_eta}")
                eta_time = datetime.fromtimestamp(other_eta)
                now = datetime.now()
                remaining = eta_time - now
                total_seconds = int(remaining.total_seconds())
                hours = total_seconds // 3600
                minutes = (total_seconds % 3600) // 60
                seconds = total_seconds % 60
                print(f"  Arrival time: {eta_time.strftime('%H:%M:%S')}")
                print(f"  Time remaining: {hours}h {minutes}m {seconds}s")
                eta_found = True
            
            # Source 3: scheduled.arrival
            if time_data.get('scheduled', {}).get('arrival'):
                sched_arrival = time_data['scheduled']['arrival']
                print(f"✓ Scheduled arrival: {sched_arrival}")
                sched_time = datetime.fromtimestamp(sched_arrival)
                print(f"  Scheduled time: {sched_time.strftime('%H:%M:%S')}")
                if not eta_found:
                    print(f"  (Using scheduled as ETA)")
            
            if not eta_found:
                print(f"✗ No ETA found for this flight")
                print(f"Time data: {json.dumps(time_data, indent=2)}")
        
        # Check status
        if 'status' in details:
            status = details['status']
            print(f"Status: {status.get('text')} (Live: {status.get('live')})")
        
        if eta_found:
            print(f"\n✓✓✓ SUCCESS! Found flight with ETA data ✓✓✓")
            break
            
    except Exception as e:
        print(f"Error getting details: {e}")

print("\n" + "="*60)
print("Test complete!")




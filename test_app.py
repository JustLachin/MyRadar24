#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Simple test script to check if all modules load correctly
"""

import sys
from pathlib import Path

# Add SDK to path
sdk_path = Path(__file__).parent / "SDK" / "python"
sys.path.insert(0, str(sdk_path))

print("Testing imports...")

try:
    from src.translations import Translator
    print("✓ Translations module loaded")
    
    from src.sound_manager import SoundManager
    print("✓ Sound manager loaded")
    
    from src.flight_tracker import FlightTracker
    print("✓ Flight tracker loaded")
    
    from src.add_flight_dialog import AddFlightDialog
    print("✓ Add flight dialog loaded")
    
    from src.main_window import MainWindow
    print("✓ Main window loaded")
    
    from FlightRadarAPI import FlightRadar24API
    print("✓ FlightRadar24 API loaded")
    
    print("\n✓ All modules loaded successfully!")
    print("\nTesting translator...")
    translator = Translator('en')
    print(f"  English: {translator.tr('app_title')}")
    translator.set_language('tr')
    print(f"  Turkish: {translator.tr('app_title')}")
    
    print("\n✓ Everything looks good! You can now run: python myradar24.py")
    
except Exception as e:
    print(f"\n✗ Error: {e}")
    import traceback
    traceback.print_exc()

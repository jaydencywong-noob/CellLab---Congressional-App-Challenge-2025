#!/usr/bin/env python3
"""
Simple test to verify main.py functionality
"""
import sys
import os

# Add the current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    print("Testing main.py imports...")
    
    # Test basic imports
    import pygame
    print("✓ pygame imported")
    
    from config import SCREEN_WIDTH, SCREEN_HEIGHT
    print("✓ config imported")
    
    from game_state import GameStateManager, GameState
    print("✓ game_state imported")
    
    from ui import MainMenuUI
    print("✓ ui imported")
    
    print("\nTesting main.py execution...")
    import main
    print("✓ main.py imported successfully")
    
    # Test basic functionality
    game_state_manager = main.game_state_manager
    print(f"✓ Game state manager initialized: {game_state_manager.current_state}")
    
    main_menu_ui = main.main_menu_ui
    print(f"✓ Main menu UI initialized: {type(main_menu_ui)}")
    
    print("\n✅ All tests passed! main.py appears to be working correctly.")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
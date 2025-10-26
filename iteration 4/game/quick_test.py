#!/usr/bin/env python3
"""
Quick test of the main menu functionality
"""
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    import pygame
    from config import SCREEN_WIDTH, SCREEN_HEIGHT, FPS
    from ui import MainMenuUI
    from game_state import GameStateManager, GameState
    
    print("Starting main menu test...")
    
    # Initialize pygame
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("CellLab - Main Menu Test")
    clock = pygame.time.Clock()
    
    # Create game state manager and main menu
    game_state_manager = GameStateManager()
    main_menu_ui = MainMenuUI(screen)
    
    print("Main menu initialized successfully!")
    print(f"Current state: {game_state_manager.get_state()}")
    
    # Run for a few frames to test
    running = True
    frames = 0
    max_frames = 60  # Run for 1 second at 60 FPS
    
    while running and frames < max_frames:
        delta_time = clock.tick(FPS) / 1000.0
        events = pygame.event.get()
        
        for event in events:
            if event.type == pygame.QUIT:
                running = False
        
        # Test main menu drawing
        main_menu_ui.draw(delta_time)
        pygame.display.flip()
        
        frames += 1
    
    print(f"✅ Main menu test completed successfully! Ran {frames} frames.")
    pygame.quit()
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    if 'pygame' in locals():
        pygame.quit()
    sys.exit(1)
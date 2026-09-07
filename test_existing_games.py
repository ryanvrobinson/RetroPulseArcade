#!/usr/bin/env python3
"""
Test that existing games still work after our changes to main.py
"""
import os
os.environ["SDL_VIDEODRIVER"] = "dummy"  # Use dummy video driver

import sys
import pygame
sys.path.insert(0, '.')

def test_existing_games():
    print("Testing existing games still work...")

    # Import and initialize
    import main
    pygame.init()

    # Create app
    app = main.RetroPulseApp()

    # Get neutral key state
    neutral_keys = pygame.key.get_pressed()

    # List of game keys to test (from the original 10 games)
    game_keys = ["flash", "dodge", "spot_it", "archery", "traffic",
                 "memory", "block_drop", "sky_dash", "find_secret", "color_chaos"]

    for game_key in game_keys:
        try:
            print(f"  Testing {game_key}...")
            app.start_game(game_key)
            assert app.state == game_key.upper(), f"Expected state {game_key.upper()}, got {app.state}"
            assert app.game is not None, f"Game object not created for {game_key}"

            # Update the game a few times with neutral keys
            for _ in range(10):
                if game_key in ["dodge", "traffic", "sky_dash"]:  # These take keys
                    app.game.update(0.016, neutral_keys)
                else:  # These take only dt
                    app.game.update(0.016)

            # If we get here, the game didn't crash
            print(f"    [OK] {game_key} updated 10 frames without crashing")

        except Exception as e:
            print(f"    [FAIL] {game_key} failed: {e}")
            return False

    print("\n[SUCCESS] All existing games still work!")
    return True

if __name__ == '__main__':
    success = test_existing_games()
    sys.exit(0 if success else 1)
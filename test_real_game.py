#!/usr/bin/env python3
"""
Test script to verify the jump fix for NEON RUSH with longer simulation
"""
import os
os.environ["SDL_VIDEODRIVER"] = "dummy"  # Use dummy video driver

import sys
import pygame
sys.path.insert(0, '.')

def test_jump_physics():
    print("Testing NEON RUSH jump physics with extended simulation...")

    # Import and initialize
    import main
    pygame.init()

    # Create app and start NEON RUSH
    app = main.RetroPulseApp()
    app.start_game('neon_rush')
    game = app.game

    print(f"[INFO] Initial state: y={game.y}, vy={game.vy}, is_jumping={game.is_jumping}")
    print(f"[INFO] Physics values: jump_power={game.jump_power}, gravity={game.gravity}, max_fall_speed={game.max_fall_speed}")

    # Test jump initiation
    game._start_jump()
    print(f"[INFO] After jump: y={game.y}, vy={game.vy}, is_jumping={game.is_jumping}")

    # Simulate jump over extended time to see the full trajectory
    neutral_keys = [False] * 512
    max_height_reached = game.y
    apex_frame = 0
    ground_launch_y = SCREEN_HEIGHT - 100  # 540

    # Simulate 5 seconds (300 frames at 60 FPS)
    for i in range(300):
        game.update(0.016, neutral_keys)

        # Track highest point (lowest y)
        if game.y < max_height_reached:
            max_height_reached = game.y
            apex_frame = i

        # Break if we've landed and stayed on ground for a while
        if i > 50 and game.y >= ground_launch_y - 2 and game.vy >= 0:
            print(f"[INFO] Landed at frame {i}")
            break

        # Print progress every 50 frames
        if i % 50 == 0:
            print(f"[INFO] Frame {i}: y={game.y:.2f}, vy={game.vy:.2f}")

    print(f"\\n[RESULTS] Jump analysis:")
    print(f"  Launch y: {ground_launch_y}")
    print(f"  Max height (lowest y): {max_height_reached:.2f}")
    print(f"  Jump height achieved: {ground_launch_y - max_height_reached:.2f} pixels")
    print(f"  Time to apex: {apex_frame * 0.016:.2f} seconds ({apex_frame} frames)")
    print(f"  Final state: y={game.y:.2f}, vy={game.vy:.2f}, is_jumping={game.is_jumping}")

    # With current values (jump_power=18.0, gravity=0.8):
    # Expected time to apex: jump_power / gravity = 18.0 / 0.8 = 22.5 seconds
    # Expected height: 0.5 * gravity * t² = 0.5 * 0.8 * (22.5)² = 202.5 pixels
    expected_time_to_apex = game.jump_power / game.gravity
    expected_height = 0.5 * game.gravity * (expected_time_to_apex ** 2)

    print(f"\\n[EXPECTED with current values]:")
    print(f"  Time to apex: {expected_time_to_apex:.2f} seconds")
    print(f"  Jump height: {expected_height:.2f} pixels")

    # The jump is extremely slow and high - not suitable for a game
    # Let's test what values would be more reasonable
    print(f"\\n[REASONABLE VALUES for arcade game]:")
    print(f"  For 80px jump in 0.6s to apex:")
    print(f"    gravity = 2 * height / t² = 2 * 80 / 0.6² = {2 * 80 / 0.36:.1f}")
    print(f"    jump_power = gravity * t = {(2 * 80 / 0.36) * 0.6:.1f}")

    print(f"\\n[RECOMMENDATION: Increase jump_power and gravity]")
    return True

if __name__ == '__main__':
    from constants import SCREEN_HEIGHT
    success = test_jump_physics()
    sys.exit(0 if success else 1)
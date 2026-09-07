#!/usr/bin/env python3
"""
Test the new jump physics values for NEON RUSH
"""
import os
os.environ["SDL_VIDEODRIVER"] = "dummy"  # Use dummy video driver

import sys
import pygame
sys.path.insert(0, '.')

def test_new_physics():
    print("Testing NEW jump physics values...")

    # Import and initialize
    import main
    pygame.init()

    # Get neutral key state (no keys pressed)
    neutral_keys = pygame.key.get_pressed()

    # Create app and start NEON RUSH
    app = main.RetroPulseApp()
    app.start_game('neon_rush')
    game = app.game

    print(f"[INFO] New physics values: jump_power={game.jump_power}, gravity={game.gravity}, max_fall_speed={game.max_fall_speed}")

    # Test jump initiation
    game._start_jump()
    print(f"[INFO] After jump: y={game.y}, vy={game.vy}, is_jumping={game.is_jumping}")

    # Simulate jump over time to see the trajectory
    max_height_reached = game.y
    apex_frame = 0
    ground_launch_y = SCREEN_HEIGHT - 100  # 540

    # Simulate 2 seconds (120 frames at 60 FPS)
    for i in range(120):
        game.update(0.016, neutral_keys)

        # Track highest point (lowest y)
        if game.y < max_height_reached:
            max_height_reached = game.y
            apex_frame = i

        # Break if we've landed and stayed on ground for a while
        if i > 20 and game.y >= ground_launch_y - 2 and game.vy >= 0:
            print(f"[INFO] Landed at frame {i}")
            break

        # Print progress every 20 frames
        if i % 20 == 0:
            print(f"[INFO] Frame {i}: y={game.y:.2f}, vy={game.vy:.2f}")

    print(f"\n[RESULTS] Jump analysis with new values:")
    print(f"  Launch y: {ground_launch_y}")
    print(f"  Max height (lowest y): {max_height_reached:.2f}")
    print(f"  Jump height achieved: {ground_launch_y - max_height_reached:.2f} pixels")
    print(f"  Time to apex: {apex_frame * 0.016:.2f} seconds ({apex_frame} frames)")
    print(f"  Final state: y={game.y:.2f}, vy={game.vy:.2f}, is_jumping={game.is_jumping}")

    # Calculate expected values
    # With jump_power=500, gravity=1250:
    # Expected time to apex: jump_power / gravity = 500 / 1250 = 0.4 seconds
    # Expected height: 0.5 * gravity * t² = 0.5 * 1250 * (0.4)² = 0.5 * 1250 * 0.16 = 100 pixels
    expected_time_to_apex = game.jump_power / game.gravity
    expected_height = 0.5 * game.gravity * (expected_time_to_apex ** 2)

    print(f"\n[EXPECTED with new values]:")
    print(f"  Time to apex: {expected_time_to_apex:.2f} seconds")
    print(f"  Jump height: {expected_height:.2f} pixels")

    # Check if results are reasonable
    height_achieved = ground_launch_y - max_height_reached
    time_to_apex_sec = apex_frame * 0.016

    # Allow 20% tolerance
    assert abs(height_achieved - expected_height) / expected_height < 0.2, \
        f"Height mismatch: got {height_achieved}, expected {expected_height}"
    assert abs(time_to_apex_sec - expected_time_to_apex) / expected_time_to_apex < 0.2, \
        f"Time mismatch: got {time_to_apex_sec}, expected {expected_time_to_apex}"

    print(f"\n[OK] Jump physics matches expected values within 20% tolerance")

    # Test that we don't exceed max fall speed
    # Let's test a long fall
    app.start_game('neon_rush')
    game = app.game
    # Make them jump high
    game._start_jump()
    # Let them reach apex and start falling
    for i in range(30):  # About 0.5 seconds
        game.update(0.016, neutral_keys)

    # Now let them fall for a while and check velocity
    max_vy_during_fall = game.vy
    for i in range(100):  # About 1.6 seconds more
        game.update(0.016, neutral_keys)
        if game.vy > max_vy_during_fall:
            max_vy_during_fall = game.vy
        # Should not exceed max_fall_speed
        assert game.vy <= game.max_fall_speed + 1e-3, \
            f"Exceeded max fall speed: vy={game.vy}, max={game.max_fall_speed}"

    print(f"[OK] Maximum fall speed respected: max vy during fall = {max_vy_during_fall:.2f}")

    print("\n[SUCCESS] New physics values work correctly!")
    return True

if __name__ == '__main__':
    from constants import SCREEN_HEIGHT
    success = test_new_physics()
    sys.exit(0 if success else 1)
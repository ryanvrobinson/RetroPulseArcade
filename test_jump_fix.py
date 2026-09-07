#!/usr/bin/env python3
"""
Test script to verify the jump fix for NEON RUSH
"""
import os
os.environ["SDL_VIDEODRIVER"] = "dummy"  # Use dummy video driver

import sys
import pygame
sys.path.insert(0, '.')

def test_jump_physics():
    print("Testing NEON RUSH jump physics fix...")

    # Import and initialize
    import main
    pygame.init()

    # Create app and start NEON RUSH
    app = main.RetroPulseApp()
    app.start_game('neon_rush')
    game = app.game

    print(f"[INFO] Initial state: y={game.y}, vy={game.vy}, is_jumping={game.is_jumping}")

    # Test 1: Jump initiation
    keys = pygame.key.get_pressed()
    # Test that we can access the key constants without error
    try:
        _ = keys[pygame.K_UP]
        _ = keys[pygame.K_SPACE]
        print("[OK] Can access key constants")
    except IndexError as e:
        print(f"[FAIL] Cannot access key constants: {e}")
        return False

    # Test jump with UP arrow
    test_keys = [False] * 512
    # Manually set the UP key - we can't actually modify the returned keys,
    # but we can test the logic by checking what happens in the game's update method
    # when it receives a key array where the UP position would be True if it were accessible

    # Instead, let's directly test the _start_jump method and physics
    game._start_jump()
    print(f"[INFO] After _start_jump: y={game.y}, vy={game.vy}, is_jumping={game.is_jumping}")

    assert game.is_jumping, "Player should be jumping after _start_jump"
    assert game.vy < 0, "Player should have negative (upward) velocity after jump"
    assert game.vy == -game.jump_power, f"Jump velocity should be -{game.jump_power}, got {game.vy}"
    print("[OK] Jump initiation works correctly")

    # Test 2: Jump trajectory - should go up then come down
    launch_y = game.y  # Starting jump position
    max_height_reached = game.y
    frames_above_ground = 0
    frames_below_launch = 0

    # Simulate about 2 seconds of gameplay with no keys
    neutral_keys = [False] * 512
    for i in range(120):  # 120 frames at 60 FPS = 2 seconds
        game.update(0.016, neutral_keys)

        # Track highest point (lowest y value since y increases downward)
        if game.y < max_height_reached:
            max_height_reached = game.y

        # Once we start going down past launch point, count those frames
        if game.y > launch_y + 5:  # Significantly below launch point
            frames_below_launch += 1

        # Stop testing when we land
        if game.y >= launch_y - 1 and game.vy >= 0:  # On or near ground and not moving up
            break

    print(f"[INFO] Jump stats: max_height_reached={max_height_reached:.2f}, launch_y={launch_y:.2f}")
    print(f"[INFO] Frames below launch: {frames_below_launch}")

    # The player should reach a reasonable height and come back down
    height_achieved = launch_y - max_height_reached
    print(f"[INFO] Jump height achieved: {height_achieved:.1f} pixels")

    # Should achieve reasonable jump height (with our fixed physics)
    # Original jump_power=18, gravity=0.8, no erroneous *60 multiplier
    # With correct physics: vy starts at -18, increases by 0.8 per frame
    # Time to apex: 18/0.8 = 22.5 frames
    # Distance: integral of (-18 + 0.8*t) dt from 0 to 22.5 = -18*22.5 + 0.4*22.5^2 = -405 + 202.5 = -202.5 pixels
    # So we expect about 200 pixels height
    assert height_achieved > 150, f"Jump too low: {height_achieved} pixels (expected >150)"
    assert height_achieved < 250, f"Jump too high: {height_achieved} pixels (expected <250)"
    assert frames_below_launch > 10, "Player should spend multiple frames coming down"
    print("[OK] Jump trajectory is reasonable and bounded")

    # Test 3: Multiple jumps should work
    # Let player land first
    while not (game.y >= launch_y - 1 and game.vy >= 0):  # Until landed
        game.update(0.016, neutral_keys)

    # Now jump again
    game._start_jump()
    assert game.is_jumping, "Second jump should work"
    assert game.vy < 0, "Second jump should have upward velocity"
    assert game.vy == -game.jump_power, f"Second jump velocity should be -{game.jump_power}, got {game.vy}"
    print("[OK] Multiple jumps work")

    # Test 4: Ensure player doesn't fly off screen permanently
    # Reset and test a longer sequence
    app.start_game('neon_rush')
    game = app.game
    launch_y = game.y

    # Jump and hold up for a while (simulate holding jump key)
    for i in range(180):  # 3 seconds
        game.update(0.016, neutral_keys)  # No keys after initial jump

        # Player should never go too far above the screen
        # With our physics, maximum negative y should be around launch_y - 200
        if game.y < launch_y - 300:  # More than 300 pixels above launch point
            print(f"[FAIL] Player flew too far off screen: y={game.y}, launch_y={launch_y}")
            return False

        # Stop if we've landed and stayed landed for a bit
        if i > 60 and game.y >= launch_y - 1 and game.vy >= 0:
            break

    print("[OK] Player does not fly off screen permanently")

    # Test 5: Check that we never exceed max fall speed
    # Create a scenario where we fall for a long time
    app.start_game('neon_rush')
    game = app.game
    # Make them jump high
    game._start_jump()
    # Let them reach apex and start falling
    for i in range(30):
        game.update(0.016, neutral_keys)

    # Now let them fall for a while and check velocity
    for i in range(100):
        game.update(0.016, neutral_keys)
        if game.vy > game.max_fall_speed:
            print(f"[FAIL] Exceeded max fall speed: vy={game.vy}, max={game.max_fall_speed}")
            return False

    print("[OK] Maximum fall speed is respected")

    print("\n[SUCCESS] All jump physics tests passed!")
    return True

if __name__ == '__main__':
    success = test_jump_physics()
    sys.exit(0 if success else 1)
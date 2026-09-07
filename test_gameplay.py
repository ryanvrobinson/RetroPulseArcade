#!/usr/bin/env python3
"""
Test NEON RUSH gameplay for a few seconds to ensure no crashes
"""
import os
os.environ["SDL_VIDEODRIVER"] = "dummy"  # Use dummy video driver

import sys
import pygame
import time
sys.path.insert(0, '.')

def test_gameplay():
    print("Testing NEON RUSH gameplay for 5 seconds...")

    # Import and initialize
    import main
    pygame.init()

    # Create app and start NEON RUSH
    app = main.RetroPulseApp()
    app.start_game('neon_rush')
    game = app.game

    print(f"[INFO] Game started: {type(game).__name__}")
    print(f"[INFO] Initial state: lane={game.lane}, score={game.score}")

    # Run game loop for 5 seconds with some random input
    start_time = time.time()
    frame_count = 0
    last_second = start_time

    try:
        while time.time() - start_time < 5.0 and not game.game_over:
            dt = 1.0/60.0

            # Get the real key state
            keys = pygame.key.get_pressed()

            # We'll simulate some periodic input by modifying a copy
            # But since we can't modify the returned array, we'll just test with no keys for now
            # The key handling was already tested separately
            game.update(dt, keys)

            frame_count += 1

            # Print status every second
            if time.time() - last_second >= 1.0:
                print(f"[INFO] Time: {time.time() - start_time:.1f}s, Frame: {frame_count}, "
                      f"Lane: {game.lane}, Score: {game.score}, "
                      f"Jumping: {game.is_jumping}, Sliding: {game.is_sliding}")
                last_second = time.time()

    except Exception as e:
        print(f"[ERROR] Gameplay test failed at frame {frame_count}: {e}")
        import traceback
        traceback.print_exc()
        return False

    print(f"[INFO] Gameplay test completed:")
    print(f"  Total frames: {frame_count}")
    print(f"  Final time: {time.time() - start_time:.2f} seconds")
    print(f"  Game over: {game.game_over}")
    print(f"  Final lane: {game.lane}")
    print(f"  Final score: {game.score}")
    print(f"  Distance: {getattr(game, 'distance', 0):.1f}")
    print(f"  Combo: {game.combo}")

    if game.game_over:
        print(f"  Result data: {game.result_data is not None}")
        if game.result_data:
            print(f"  Tournament points added: {game.result_data.get('added_pts', 0)}")

    print("[SUCCESS] Gameplay test completed without crashing!")
    return True

if __name__ == '__main__':
    success = test_gameplay()
    sys.exit(0 if success else 1)
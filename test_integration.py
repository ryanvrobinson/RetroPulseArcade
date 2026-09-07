#!/usr/bin/env python3
"""
Test NEON RUSH integration: start from game select and play for a few seconds
"""
import os
os.environ["SDL_VIDEODRIVER"] = "dummy"  # Use dummy video driver

import sys
import pygame
import time
sys.path.insert(0, '.')

def test_integration():
    print("Testing NEON RUSH integration from game select...")

    # Import and initialize
    import main
    pygame.init()

    # Create app
    app = main.RetroPulseApp()
    print("[OK] App created")

    # Set state to GAME_SELECT and active page to 1 (where NEON RUSH is)
    app.state = "GAME_SELECT"
    app.active_page = 1  # Page index 1 (0-based) -> second page
    print(f"[INFO] State: {app.state}, Active page: {app.active_page}")

    # Simulate clicking on NEON RUSH
    # NEON RUSH is the 5th game on page 1 (index 4 in page_keys)
    # Page 1 keys: ALL_GAME_KEYS[6:] = ['block_drop', 'sky_dash', 'find_secret', 'color_chaos', 'neon_rush']
    # So index 4 in page_keys is 'neon_rush'
    # Position: col = 4 % 3 = 1, row = 4 // 3 = 1
    # cx = 55 + col * 295 = 55 + 1*295 = 350
    # cy = 88 + row * 240 = 88 + 1*240 = 328
    # Center of rect: (cx + 130, cy + 110) = (350+130, 328+110) = (480, 438)
    click_pos = (480, 438)
    print(f"[INFO] Simulating click at {click_pos} to start NEON RUSH")
    app.handle_click(click_pos)

    # Check that the game started
    assert app.state == "NEON_RUSH", f"Expected state NEON_RUSH, got {app.state}"
    assert app.game is not None, "Game object not created"
    assert isinstance(app.game, main.GameNeonRush), f"Expected GameNeonRush, got {type(app.game)}"
    print(f"[OK] NEON RUSH game started: {type(app.game).__name__}")

    # Get the game object
    game = app.game
    # PLAYER_BASE_Y is defined in neon_rush.py, not constants.py
    PLAYER_BASE_Y = 520
    print(f"[INFO] Initial game state: lane={game.current_lane}, score={game.score}, x={game.player_x}, y={int(PLAYER_BASE_Y + game.jump_y)}")

    # Run the game for 5 seconds with some input
    start_time = time.time()
    frame_count = 0
    last_second = start_time

    try:
        while time.time() - start_time < 5.0 and not game.game_over:
            dt = 1.0/60.0

            # Get the real key state
            keys = pygame.key.get_pressed()

            # We'll add some periodic input to test controls by modifying a copy
            elapsed = time.time() - start_time
            test_keys = list(keys)  # Create a mutable copy

            # Every 3 seconds, press left for 0.2 seconds
            if (elapsed % 6.0) < 0.2:
                test_keys[pygame.K_LEFT] = True
                test_keys[pygame.K_a] = True
            # Every 4 seconds, press right for 0.2 seconds
            elif (elapsed % 8.0) < 0.2:
                test_keys[pygame.K_RIGHT] = True
                test_keys[pygame.K_d] = True
            # Every 2 seconds, press jump for 0.1 seconds
            elif (elapsed % 4.0) < 0.1:
                test_keys[pygame.K_SPACE] = True
                test_keys[pygame.K_UP] = True
                test_keys[pygame.K_w] = True
            # Every 5 seconds, press slide for 0.1 seconds
            elif (elapsed % 10.0) < 0.1:
                test_keys[pygame.K_DOWN] = True
                test_keys[pygame.K_s] = True

            game.update(dt, test_keys)

            frame_count += 1

            # Print status every second
            if time.time() - last_second >= 1.0:
                print(f"[INFO] Time: {elapsed:.1f}s, Frame: {frame_count}, "
                      f"Lane: {game.current_lane}, Score: {game.score}, "
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
            print(f"  Final score recorded: {game.result_data.get('score', 0)}")

    # Also test that we can restart
    if game.game_over:
        print("[INFO] Testing restart...")
        # Simulate pressing SPACE to restart
        keys = pygame.key.get_pressed()
        test_keys = [False] * 512
        test_keys[pygame.K_SPACE] = True
        app.handle_click((0, 0))  # Dummy click to make sure we are in game over state? Actually, we need to be in the game over state and press SPACE.
        # But note: in main.py, the game over restart is handled in the event loop for KEYDOWN.
        # We are not simulating the event loop, we are directly updating the game.
        # Instead, we can call the game's jump method? But restart is done by starting a new game.
        # Let's just start a new game via the app's start_game method (which is what happens when you press SPACE in game over).
        # We'll do that by setting the state back to GAME_SELECT and then clicking again?
        # Actually, in main.py, when in game over state and SPACE is pressed, it calls:
        #   self.start_game(self.state.lower())
        # Since self.state is "NEON_RUSH", self.state.lower() is "neon_rush"
        # So we can do:
        app.start_game("neon_rush")
        assert app.state == "NEON_RUSH", "Should be back to NEON_RUSH state after restart"
        assert app.game is not None, "New game object not created"
        print(f"[OK] Restarted NEON RUSH: score reset to {app.game.score}")

    print("[SUCCESS] Integration test completed without crashing!")
    return True

if __name__ == '__main__':
    success = test_integration()
    sys.exit(0 if success else 1)
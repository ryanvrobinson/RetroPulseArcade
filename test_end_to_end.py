#!/usr/bin/env python3
"""
End-to-end test of NEON RUSH integration
"""
import os
os.environ["SDL_VIDEODRIVER"] = "dummy"  # Use dummy video driver

import sys
import pygame
import time
sys.path.insert(0, '.')

def test_end_to_end():
    print("Testing NEON RUSH end-to-end integration...")

    # Import and initialize
    import main
    pygame.init()

    # Create app
    app = main.RetroPulseApp()
    print("[OK] App created")

    # Test 1: Start NEON RUSH from game select
    print("\n[TEST 1] Starting NEON RUSH from game select")
    app.state = "GAME_SELECT"
    app.active_page = 1  # Page with NEON RUSH

    # Simulate clicking on NEON RUSH (position calculated earlier)
    click_pos = (480, 438)  # Center of NEON RUSH button on page 1
    app.handle_click(click_pos)

    assert app.state == "NEON_RUSH", f"Expected state NEON_RUSH, got {app.state}"
    assert app.game is not None, "Game object not created"
    print(f"[OK] NEON RUSH game started: {type(app.game).__name__}")

    # Test 2: Play the game for 3 seconds
    print("\n[TEST 2] Playing game for 3 seconds")
    game = app.game
    # First, we need to start the game (transition from START to PLAYING)
    game.jump()  # This should transition from START to PLAYING
    assert game.game_state == "PLAYING", "Should be in PLAYING state after first jump"
    start_time = time.time()
    frame_count = 0

    while time.time() - start_time < 3.0 and not game.game_over:
        dt = 1.0/60.0
        keys = pygame.key.get_pressed()
        game.update(dt, keys)
        frame_count += 1

        if frame_count % 180 == 0:  # Every 3 seconds at 60 FPS
            elapsed = time.time() - start_time
            print(f"  [INFO] {elapsed:.1f}s: lane={game.current_lane}, score={game.score}, jumping={game.is_jumping}")

    print(f"[INFO] Gameplay session ended after {frame_count} frames ({time.time() - start_time:.2f}s)")
    print(f"       Final state: game_over={game.game_over}, score={game.score}")

    # Test 3: Test game over and restart
    print("\n[TEST 3] Testing game over and restart")
    if not game.game_over:
        # Force a game over by placing an obstacle in the player's lane
        game.obstacles.append({
            'lane': game.current_lane,
            'x': float(game.player_x),
            'y': -50.0,
            'type': 'GROUND_BARRIER',
            'w': 52,
            'h': 32,
            'move_dir': 1,
            'alive': True
        })
        # Update a few times to ensure collision
        for i in range(20):
            game.update(0.016, pygame.key.get_pressed())

    assert game.game_over, "Should be game over after forced collision"
    assert game.result_data is not None, "Should have result data"
    print(f"[OK] Game over triggered: score={game.score}, points added={game.result_data.get('added_pts', 0)}")

    # Test restart by starting a new game
    app.start_game('neon_rush')
    assert app.state == "NEON_RUSH", "Should be back to NEON_RUSH state"
    assert app.game is not None, "New game object not created"
    new_game = app.game
    assert new_game.score == 0, "Score should be reset to 0"
    assert new_game.game_state == "START", "Should be in START state"
    print(f"[OK] Restart successful: score reset to {new_game.score}")

    # Test 4: Verify existing games still work
    print("\n[TEST 4] Verifying existing games still work")
    for game_key in ['flash', 'dodge', 'archery'][:3]:
        try:
            app.start_game(game_key)
            assert app.state == game_key.upper(), f"Expected state {game_key.upper()}"
            assert app.game is not None, f"Game object not created for {game_key}"
            # Quick update
            if app.game:
                if game_key in ['dodge']:
                    keys = pygame.key.get_pressed()
                    app.game.update(0.016, keys)
                else:
                    app.game.update(0.016)
            print(f"  [OK] {game_key} still works")
        except Exception as e:
            print(f"  [FAIL] {game_key} failed: {e}")
            return False

    print("\n[SUCCESS] All end-to-end tests passed!")
    return True

if __name__ == '__main__':
    success = test_end_to_end()
    sys.exit(0 if success else 1)
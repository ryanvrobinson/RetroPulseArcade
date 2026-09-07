#!/usr/bin/env python3
"""
Final test of NEON RUSH gameplay mechanics
"""
import os
os.environ["SDL_VIDEODRIVER"] = "dummy"  # Use dummy video driver

import sys
import pygame
import time
sys.path.insert(0, '.')

def test_mechanics():
    print("Testing NEON RUSH mechanics...")

    # Import and initialize
    import main
    pygame.init()

    # Create app and start NEON RUSH
    app = main.RetroPulseApp()
    app.start_game('neon_rush')
    game = app.game

    print(f"[INFO] Game started: {type(game).__name__}")
    print(f"[INFO] Initial state: current_lane={game.current_lane}, score={game.score}, player_x={game.player_x}")

    # Get the real key state (no keys pressed)
    neutral_keys = pygame.key.get_pressed()

    # Test 1: Jump mechanics (via the jump() method which is called by main.py)
    print("\n[TEST 1] Jump mechanics")
    # First, we need to start the game (transition from START to PLAYING)
    game.jump()  # This should transition from START to PLAYING
    assert game.game_state == "PLAYING", "Should be in PLAYING state after first jump"
    print("  OK: Game started (transitioned to PLAYING)")

    # Now we can initiate a jump
    game.start_jump()
    assert game.is_jumping, "Should be jumping after start_jump"
    assert game.jump_vy < 0, "Should have upward velocity"
    start_y = game.jump_y
    # Update a few frames to see movement
    for i in range(10):
        game.update(0.016, neutral_keys)
    assert game.jump_y < start_y, "Should have moved up (jump_y more negative)"
    print(f"  OK: Jump initiated, moved up from {start_y:.2f} to {game.jump_y:.2f}")

    # Test 2: Lane change
    print("\n[TEST 2] Lane change")
    # Reset jump state
    game.is_jumping = False
    game.jump_vy = 0.0
    game.jump_y = 0.0
    start_lane = game.current_lane
    start_x = game.player_x
    # Change lane to left via _process_inputs (we need to simulate key presses)
    # Since we can't easily modify the key array, let's test the lane change logic directly
    # by calling _change_lane equivalent - but looking at the code, lane changes happen
    # through target_lane in _process_inputs

    # Instead, let's test the lane system by directly manipulating target_lane
    # and see if player_x moves toward it
    game.target_lane = 0  # left lane
    # Update several frames to see movement
    for i in range(20):
        game.update(0.016, neutral_keys)
    # Player should have moved left
    assert game.player_x < start_x, "Should have moved left"
    print(f"  OK: Moved left from {start_x:.2f} to {game.player_x:.2f}")
    # Change to right lane
    game.target_lane = 2
    for i in range(20):
        game.update(0.016, neutral_keys)
    assert game.player_x > start_x, "Should have moved right"
    print(f"  OK: Moved right to {game.player_x:.2f}")
    # Back to center
    game.target_lane = 1
    for i in range(20):
        game.update(0.016, neutral_keys)
    assert abs(game.player_x - 480.0) < 10, f"Should be back to center: {game.player_x}"
    print(f"  OK: Back to center lane: {game.player_x:.2f}")

    # Test 3: Slide
    print("\n[TEST 3] Slide")
    game.start_slide()
    assert game.is_sliding, "Should be sliding after start_slide"
    start_slide_time = game.slide_timer
    # Update a few frames
    for i in range(10):
        game.update(0.016, neutral_keys)
    assert game.slide_timer < start_slide_time, "Slide timer should decrease"
    assert game.is_sliding, "Should still be sliding"
    print(f"  OK: Slide active, timer: {game.slide_timer:.2f} (started {start_slide_time:.2f})")
    # Wait for slide to end
    while game.is_sliding:
        game.update(0.016, neutral_keys)
    assert not game.is_sliding, "Should not be sliding after timer expires"
    print(f"  OK: Slide ended after {start_slide_time - game.slide_timer:.2f} seconds")

    # Test 4: Obstacle collision (simplified)
    print("\n[TEST 4] Obstacle collision")
    # Reset game state
    app.start_game('neon_rush')
    game = app.game
    game.jump()  # Start the game
    # Place an obstacle in the current lane, close to the player
    game.obstacles.append({
        'lane': game.current_lane,
        'x': float(game.player_x),
        'y': -50.0,  # Above the player, moving down
        'type': 'GROUND_BARRIER',
        'w': 52,
        'h': 32,
        'move_dir': 1,
        'alive': True
    })
    # Update should cause collision and game over
    # We need to update enough times for the obstacle to reach the player
    for i in range(50):
        game.update(0.016, neutral_keys)
        if game.game_over:
            break
    assert game.game_over, "Should be game over after hitting obstacle"
    assert game.result_data is not None, "Should have result data"
    print(f"  OK: Game over triggered, score: {game.score}, points added: {game.result_data.get('added_pts', 0)}")

    # Test 5: Collectible collection
    print("\n[TEST 5] Collectible collection")
    app.start_game('neon_rush')
    game = app.game
    game.jump()  # Start the game
    # Place a collectible in the current lane, close to the player
    game.collectibles.append({
        'lane': game.current_lane,
        'x': float(game.player_x),
        'y': -50.0,  # Above the player
        'type': 'ORB',
        'high': False,
        'alive': True
    })
    initial_score = game.score
    initial_combo = game.combo
    # Update should collect it
    for i in range(50):
        game.update(0.016, neutral_keys)
        if not game.collectibles[0]['alive']:  # If collected
            break
    assert game.score > initial_score, "Score should increase after collecting orb"
    assert game.combo > initial_combo, "Combo should increase after collecting orb"
    assert not game.collectibles[0]['alive'], "Collectible should be removed"
    print(f"  OK: Collected orb, score: {initial_score} -> {game.score}, combo: {initial_combo} -> {game.combo}")

    # Test 6: Multiple jumps and landing
    print("\n[TEST 6] Multiple jumps")
    app.start_game('neon_rush')
    game = app.game
    game.jump()  # Start the game
    # Jump, wait to land, jump again
    game.start_jump()
    # Wait for apex and start falling
    for i in range(30):
        game.update(0.016, neutral_keys)
    # Continue to land
    while not (game.jump_y >= -1.0 and game.jump_vy >= 0):
        game.update(0.016, neutral_keys)
    assert not game.is_jumping, "Should have landed"
    # Jump again
    game.start_jump()
    assert game.is_jumping, "Second jump should work"
    # Wait to land again
    while not (game.jump_y >= -1.0 and game.jump_vy >= 0):
        game.update(0.016, neutral_keys)
    assert not game.is_jumping, "Should have landed after second jump"
    print(f"  OK: Two jumps completed")

    print("\n[SUCCESS] All mechanics tests passed!")
    return True

if __name__ == '__main__':
    from constants import SCREEN_HEIGHT
    success = test_mechanics()
    sys.exit(0 if success else 1)
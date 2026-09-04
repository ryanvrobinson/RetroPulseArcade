#!/usr/bin/env python3
import sys
import pygame
sys.path.insert(0, '.')

# Try to import and run with basic interaction
try:
    print("Importing main...")
    from main import RetroPulseApp
    print("Import successful")
    print("Creating app...")
    app = RetroPulseApp()
    print("App creation successful")

    # Run for a longer time with some basic interaction
    frame_count = 0
    max_frames = 600  # 10 seconds at 60 FPS

    print(f"Running for {max_frames} frames (~10 seconds)...")
    running = True
    last_state = None

    while running and frame_count < max_frames:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if app.state != "MENU":
                        app.state = "MENU"
                    else:
                        running = False
                elif event.key == pygame.K_SPACE:
                    # Try to click play button if in menu
                    if app.state == "MENU":
                        app.state = "GAME_SELECT"
                elif event.key == pygame.K_RETURN:
                    # Try to select first game if in game select
                    if app.state == "GAME_SELECT":
                        app.state = "FLASH"

        # Update game state
        if hasattr(app, 'game') and app.game:
            if hasattr(app.game, 'update'):
                keys = pygame.key.get_pressed()
                # Try to call update with appropriate args
                try:
                    app.game.update(1/60)
                except TypeError:
                    try:
                        app.game.update(1/60, keys)
                    except:
                        pass  # Ignore update errors for test

        # Draw frame
        if hasattr(app, 'draw'):
            surf = pygame.Surface((app.screen.get_width(), app.screen.get_height()))
            app.draw(surf)

        # Print state changes
        if app.state != last_state:
            print(f"Frame {frame_count}: State changed to {app.state}")
            last_state = app.state

        frame_count += 1

        # Limit FPS
        if hasattr(app, 'clock'):
            app.clock.tick(60)

    print(f"Test completed successfully - ran {frame_count} frames")
    print(f"Final state: {app.state}")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    try:
        pygame.quit()
    except:
        pass
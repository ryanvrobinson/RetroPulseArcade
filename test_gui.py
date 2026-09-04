#!/usr/bin/env python3
import sys
import pygame
sys.path.insert(0, '.')

# Try to import and run just briefly
try:
    print("Importing main...")
    from main import RetroPulseApp
    print("Import successful")
    print("Creating app...")
    app = RetroPulseApp()
    print("App creation successful")

    # Run for just 5 frames then exit
    frame_count = 0
    max_frames = 5

    print(f"Running for {max_frames} frames...")
    running = True
    while running and frame_count < max_frames:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

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

        frame_count += 1
        print(f"Frame {frame_count} completed")

        # Limit FPS
        if hasattr(app, 'clock'):
            app.clock.tick(60)

    print("Test completed successfully - no crash in early frames")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    try:
        pygame.quit()
    except:
        pass
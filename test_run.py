#!/usr/bin/env python3
import sys
import pygame
sys.path.insert(0, '.')

# Try to import and run just briefly
try:
    from main import RetroPulseApp
    print("Import successful")
    app = RetroPulseApp()
    print("App creation successful")
    # Run for just 2 frames
    app.clock = pygame.time.Clock()
    running = True
    frame_count = 0
    while running and frame_count < 2:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        dt = min(app.clock.tick(60) / 1000.0, 0.1)
        frame_count += 1
        print(f"Frame {frame_count} completed")
    print("Test completed successfully")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
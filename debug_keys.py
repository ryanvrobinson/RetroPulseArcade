#!/usr/bin/env python3
import os
os.environ["SDL_VIDEODRIVER"] = "dummy"

import pygame
pygame.init()

# Test what pygame.key.get_pressed() returns
keys = pygame.key.get_pressed()
print(f"Type: {type(keys)}")
print(f"Length: {len(keys)}")
print(f"K_LEFT: {pygame.K_LEFT}")
print(f"K_RIGHT: {pygame.K_RIGHT}")
print(f"K_UP: {pygame.K_UP}")
print(f"K_DOWN: {pygame.K_DOWN}")
print(f"K_SPACE: {pygame.K_SPACE}")
print(f"K_a: {pygame.K_a}")
print(f"K_d: {pygame.K_d}")
print(f"K_s: {pygame.K_s}")
print(f"K_w: {pygame.K_w}")

# Test accessing by index
print(f"keys[0]: {keys[0]}")
print(f"keys[1]: {keys[1]}")
print(f"keys[2]: {keys[2]}")

# Test accessing by pygame constants (this is what fails)
try:
    val = keys[pygame.K_LEFT]
    print(f"keys[pygame.K_LEFT]: {val} - SUCCESS")
except Exception as e:
    print(f"keys[pygame.K_LEFT]: FAILED - {e}")

try:
    val = keys[pygame.K_a]
    print(f"keys[pygame.K_a]: {val} - SUCCESS")
except Exception as e:
    print(f"keys[pygame.K_a]: FAILED - {e}")

# Let's see what the maximum valid index is
print(f"Maximum index should be: {len(keys) - 1}")
print(f"K_LEFT is: {pygame.K_LEFT}")
print(f"K_LEFT < len(keys)? {pygame.K_LEFT < len(keys)}")

# Let's test creating a proper list and see if that works
test_list = [False] * len(keys)
print(f"Test list length: {len(test_list)}")
print(f"K_LEFT < len(test_list)? {pygame.K_LEFT < len(test_list)}")

try:
    val = test_list[pygame.K_LEFT]
    print(f"test_list[pygame.K_LEFT]: {val} - SUCCESS")
except Exception as e:
    print(f"test_list[pygame.K_LEFT]: FAILED - {e}")
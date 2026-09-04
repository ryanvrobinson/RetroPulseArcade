"""
Unified input abstraction for handling mouse, keys, and button states.
"""
import pygame

class InputHandler:
    def __init__(self):
        self.mouse_pos = (0, 0)
        self.mouse_clicked = False
        self.mouse_down = False
        self.keys_pressed = set()
        self.keys_down = set()
        self.keys_up = set()

    def process_events(self, events):
        self.mouse_clicked = False
        self.mouse_pos = pygame.mouse.get_pos()
        self.keys_down.clear()
        self.keys_up.clear()

        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    self.mouse_clicked = True
                    self.mouse_down = True
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    self.mouse_down = False
            elif event.type == pygame.KEYDOWN:
                self.keys_pressed.add(event.key)
                self.keys_down.add(event.key)
            elif event.type == pygame.KEYUP:
                self.keys_pressed.discard(event.key)
                self.keys_up.add(event.key)

    def is_key_down(self, key):
        return key in self.keys_down

    def is_key_pressed(self, key):
        return key in self.keys_pressed
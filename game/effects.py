"""
Screen shake and visual juicing effects.
"""
import random

class ScreenShake:
    def __init__(self):
        self.duration = 0.0
        self.intensity = 0.0
        self.offset_x = 0
        self.offset_y = 0

    def add_shake(self, intensity=8.0, duration=0.25):
        self.intensity = max(self.intensity, intensity)
        self.duration = max(self.duration, duration)

    def update(self, dt):
        if self.duration > 0:
            self.duration -= dt
            decay = self.intensity * (self.duration / max(0.001, self.duration + dt))
            self.offset_x = int(random.uniform(-decay, decay))
            self.offset_y = int(random.uniform(-decay, decay))
        else:
            self.offset_x = 0
            self.offset_y = 0

    def get_offset(self):
        return self.offset_x, self.offset_y
import math
import random
import pygame
from constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT, C_SKY_DEEP, C_SKY_LIGHT,
    C_WHITE, C_SLATE_DARK, C_MINT
)

class EnvironmentEngine:
    def __init__(self):
        self.clouds = [
            {"x": 60,  "y": 60,  "spd": 0.35, "scale": 1.2},
            {"x": 380, "y": 120, "spd": 0.22, "scale": 0.9},
            {"x": 720, "y": 70,  "spd": 0.40, "scale": 1.3},
            {"x": 880, "y": 140, "spd": 0.28, "scale": 1.0}
        ]
        self.birds = [
            {"x": 120, "y": 110, "spd": 1.2, "wing": 0.0},
            {"x": 560, "y": 90,  "spd": 1.5, "wing": 1.5}
        ]

    def update(self, dt):
        for c in self.clouds:
            c["x"] += c["spd"] * dt * 40
            if c["x"] > SCREEN_WIDTH + 100:
                c["x"] = -120
                c["y"] = random.uniform(30, 180)
        for b in self.birds:
            b["x"] += b["spd"] * dt * 50
            b["wing"] += dt * 8.0
            if b["x"] > SCREEN_WIDTH + 60:
                b["x"] = -40
                b["y"] = random.uniform(60, 160)

    def draw_clouds(self, surf):
        for c in self.clouds:
            cx, cy, s = c["x"], c["y"], c["scale"]
            pygame.draw.rect(surf, C_WHITE, (cx - 24 * s, cy - 10 * s, 48 * s, 20 * s), border_radius=6)
            pygame.draw.rect(surf, C_WHITE, (cx - 14 * s, cy - 18 * s, 28 * s, 12 * s), border_radius=4)

    def draw_birds(self, surf):
        for b in self.birds:
            bx, by = int(b["x"]), int(b["y"])
            wing_y = math.sin(b["wing"]) * 3
            pygame.draw.line(surf, C_SLATE_DARK, (bx - 6, by + wing_y), (bx, by), 2)
            pygame.draw.line(surf, C_SLATE_DARK, (bx, by), (bx + 6, by + wing_y), 2)

    def draw_base_countryside(self, surf, ground_y=540):
        for y in range(0, ground_y, 6):
            t = y / ground_y
            r = int(C_SKY_DEEP[0] * (1 - t) + C_SKY_LIGHT[0] * t)
            g = int(C_SKY_DEEP[1] * (1 - t) + C_SKY_LIGHT[1] * t)
            b = int(C_SKY_DEEP[2] * (1 - t) + C_SKY_LIGHT[2] * t)
            pygame.draw.rect(surf, (r, g, b), (0, y, SCREEN_WIDTH, 6))

        self.draw_clouds(surf)
        self.draw_birds(surf)

        m_pts = [(0, ground_y - 90), (140, ground_y - 200), (320, ground_y - 120), (520, ground_y - 220), (740, ground_y - 130), (960, ground_y - 180), (960, ground_y), (0, ground_y)]
        pygame.draw.polygon(surf, (147, 197, 253), m_pts)
        pygame.draw.polygon(surf, C_WHITE, [(140, ground_y - 200), (115, ground_y - 165), (165, ground_y - 165)])
        pygame.draw.polygon(surf, C_WHITE, [(520, ground_y - 220), (490, ground_y - 180), (550, ground_y - 180)])

        pygame.draw.ellipse(surf, (134, 239, 172), (-80, ground_y - 130, 480, 200))
        pygame.draw.ellipse(surf, (110, 231, 183), (300, ground_y - 160, 520, 220))
        pygame.draw.ellipse(surf, (167, 243, 208), (680, ground_y - 110, 360, 160))

        pygame.draw.rect(surf, C_MINT, (0, ground_y, SCREEN_WIDTH, SCREEN_HEIGHT - ground_y))
        pygame.draw.rect(surf, (34, 197, 94), (0, ground_y + 10, SCREEN_WIDTH, 6))
        pygame.draw.rect(surf, (22, 101, 52), (0, ground_y + 16, SCREEN_WIDTH, SCREEN_HEIGHT - ground_y - 16))

env_engine = EnvironmentEngine()
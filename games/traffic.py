import random
import pygame
from constants import (
    SCREEN_HEIGHT, C_SLATE_DEEP, C_ROAD, C_ROAD_LINE,
    C_CORAL, C_PINK, C_PURPLE, C_YELLOW, draw_hud
)
from audio import play_sound
from effects import spawn_burst
from tournament import tournament_manager

class GameTrafficRider:
    def __init__(self):
        self.score, self.distance, self.speed = 0, 0.0, 360.0
        self.lanes = [310, 480, 650]
        self.player_x, self.target_x = float(self.lanes[1]), float(self.lanes[1])
        self.traffic, self.coins = [], []
        self.spawn_timer = 0.0
        self.road_scroll = 0.0
        self.game_over = False
        self.combo = 0
        self.result_data = None

    def update(self, dt, keys):
        if self.game_over: return
        self.speed = min(620.0, 360.0 + (self.distance / 120.0))
        self.distance += (self.speed * dt) * 0.1
        self.score = int(self.distance * 10) + (self.combo * 50)
        self.road_scroll = (self.road_scroll + self.speed * dt) % 60
        if keys[pygame.K_LEFT] or keys[pygame.K_a]: self.target_x = max(self.lanes[0], self.target_x - 480 * dt)
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: self.target_x = min(self.lanes[2], self.target_x + 480 * dt)
        self.player_x += (self.target_x - self.player_x) * 12.0 * dt

        self.spawn_timer += dt
        if self.spawn_timer >= 1.1:
            self.spawn_timer = 0.0
            lane = random.choice([0, 1, 2])
            self.traffic.append({"x": self.lanes[lane], "y": -120, "color": random.choice([C_CORAL, C_PINK, C_PURPLE, C_YELLOW])})

        for v in self.traffic:
            v["y"] += (self.speed - 180.0) * dt
            if abs(self.player_x - v["x"]) < 42 and abs(520 - v["y"]) < 54:
                self.game_over = True
                play_sound("hit")
                spawn_burst(self.player_x, 520, C_CORAL, 24)
                self.result_data = tournament_manager.record_game("traffic", self.score)
                break
        self.traffic = [v for v in self.traffic if v["y"] < SCREEN_HEIGHT + 140]

    def draw(self, surf):
        surf.fill(C_SLATE_DEEP)
        pygame.draw.rect(surf, C_ROAD, (210, 0, 540, SCREEN_HEIGHT))
        for lx in [395, 565]:
            for y in range(-60, SCREEN_HEIGHT + 60, 60):
                pygame.draw.line(surf, C_ROAD_LINE, (lx, y + int(self.road_scroll)), (lx, y + int(self.road_scroll) + 34), 4)
        for v in self.traffic:
            pygame.draw.rect(surf, v["color"], (v["x"] - 22, v["y"] - 35, 44, 70), border_radius=6)
        pygame.draw.rect(surf, C_YELLOW, (int(self.player_x) - 22, 490, 44, 64), border_radius=8)
        draw_hud(surf, self.score, combo=self.combo)
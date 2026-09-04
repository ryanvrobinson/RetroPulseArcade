import math
import random
import pygame
from constants import (
    SCREEN_WIDTH, C_YELLOW, C_PINK, C_CORAL, C_PURPLE, C_MINT,
    C_WHITE, draw_hud
)
from audio import play_sound
from effects import spawn_burst, score_popups, ScorePopup
from environment import env_engine
from tournament import tournament_manager

class GameSpotIt:
    def __init__(self):
        self.round_num, self.score, self.lives = 1, 0, 3
        self.state, self.state_timer = "MEMORIZE", 2.4
        self.items, self.changed_index = [], -1
        self.game_over = False
        self.result_data = None
        self.setup_round()

    def setup_round(self):
        self.items = []
        item_types = ["STAR", "FLOWER", "GEM", "SHIELD", "MUSHROOM"]
        colors = [C_YELLOW, C_PINK, C_CORAL, C_PURPLE, C_MINT]
        num_items = min(6, 3 + self.round_num // 2)
        start_x = (SCREEN_WIDTH - (num_items * 110)) // 2 + 55
        for i in range(num_items):
            self.items.append({
                "type": random.choice(item_types),
                "color": random.choice(colors),
                "x": start_x + i * 110, "y": 320, "radius": 36
            })
        self.state = "MEMORIZE"
        self.state_timer = max(1.5, 2.8 - (self.round_num * 0.15))
        self.changed_index = random.randint(0, num_items - 1)

    def apply_change(self):
        target = self.items[self.changed_index]
        if random.random() < 0.5:
            new_cols = [c for c in [C_YELLOW, C_PINK, C_CORAL, C_PURPLE, C_MINT] if c != target["color"]]
            target["color"] = random.choice(new_cols)
        else:
            new_types = [t for t in ["STAR", "FLOWER", "GEM", "SHIELD", "MUSHROOM"] if t != target["type"]]
            target["type"] = random.choice(new_types)

    def handle_click(self, mx, my):
        if self.game_over or self.state != "GUESS": return
        for idx, item in enumerate(self.items):
            if math.hypot(mx - item["x"], my - item["y"]) <= item["radius"] + 8:
                if idx == self.changed_index:
                    play_sound("celebrate")
                    self.score += 250 * self.round_num
                    spawn_burst(item["x"], item["y"], C_YELLOW, 20, shape="star")
                    score_popups.append(ScorePopup("+CORRECT!", item["x"], item["y"] - 30, C_MINT))
                    self.round_num += 1
                    self.setup_round()
                else:
                    play_sound("wrong")
                    self.lives -= 1
                    if self.lives <= 0:
                        self.game_over = True
                        self.result_data = tournament_manager.record_game("spot_it", self.score)
                break

    def update(self, dt):
        if self.game_over: return
        if self.state == "MEMORIZE":
            self.state_timer -= dt
            if self.state_timer <= 0:
                self.apply_change()
                self.state = "GUESS"
                play_sound("pop")

    def draw(self, surf):
        env_engine.draw_base_countryside(surf)
        for item in self.items:
            ix, iy, r = item["x"], item["y"], item["radius"]
            pygame.draw.circle(surf, C_WHITE, (ix, iy), r)
            pygame.draw.circle(surf, item["color"], (ix, iy), r - 6)
        draw_hud(surf, self.score, lives=self.lives, round_num=self.round_num)
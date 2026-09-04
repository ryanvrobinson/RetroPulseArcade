import random
import pygame
from constants import (
    SCREEN_WIDTH, C_MINT, C_GOLD, C_CORAL, C_PINK, C_PURPLE,
    C_BLUE_CARD, C_YELLOW, C_SLATE_DARK, draw_pixel_box, draw_hud
)
from audio import play_sound
from effects import spawn_burst, score_popups, ScorePopup
from environment import env_engine
from tournament import tournament_manager

class GameBlockDrop:
    def __init__(self):
        self.score, self.combo, self.height = 0, 0, 0
        self.block_w, self.block_h = 220, 28
        self.tower = [{"x": SCREEN_WIDTH // 2 - 110, "w": 220, "y": 560, "color": C_MINT}]
        self.cur_x, self.cur_vx = 100.0, 320.0
        self.game_over = False
        self.result_data = None
        self.cam_y, self.target_cam_y = 0.0, 0.0

    def update(self, dt):
        if self.game_over: return
        self.cur_x += self.cur_vx * dt
        top_w = self.tower[-1]["w"]
        if self.cur_x < 120: self.cur_x = 120; self.cur_vx = abs(self.cur_vx)
        elif self.cur_x + top_w > SCREEN_WIDTH - 120: self.cur_x = SCREEN_WIDTH - 120 - top_w; self.cur_vx = -abs(self.cur_vx)
        self.cam_y += (self.target_cam_y - self.cam_y) * 8.0 * dt

    def drop_block(self):
        if self.game_over: return
        prev = self.tower[-1]
        cur_w = prev["w"]
        overlap_left = max(prev["x"], self.cur_x)
        overlap_right = min(prev["x"] + cur_w, self.cur_x + cur_w)

        if overlap_right > overlap_left:
            new_w = overlap_right - overlap_left
            diff = abs(prev["x"] - self.cur_x)
            if diff <= 4:
                new_w = cur_w
                overlap_left = prev["x"]
                self.combo += 1
                self.score += 250 * self.combo
                play_sound("coin")
                score_popups.append(ScorePopup("PERFECT ALIGN!", SCREEN_WIDTH // 2, 220, C_GOLD))
                spawn_burst(overlap_left + new_w // 2, prev["y"] - self.block_h, C_GOLD, 24, shape="star")
            else:
                self.combo = 1
                self.score += 100
                play_sound("pop")
                spawn_burst(overlap_left + new_w // 2, prev["y"] - self.block_h, C_CORAL, 12)

            self.tower.append({"x": overlap_left, "w": new_w, "y": prev["y"] - self.block_h, "color": random.choice([C_CORAL, C_PINK, C_PURPLE, C_BLUE_CARD, C_YELLOW])})
            self.height += 1
            self.cur_vx = (abs(self.cur_vx) + 12.0) * (1 if self.cur_vx > 0 else -1)
            if self.height > 6:
                self.target_cam_y = (self.height - 6) * self.block_h
        else:
            self.game_over = True
            play_sound("hit")
            self.result_data = tournament_manager.record_game("block_drop", self.score)

    def handle_click(self, mx, my):
        self.drop_block()

    def draw(self, surf):
        env_engine.draw_base_countryside(surf)
        oy = int(self.cam_y)
        for b in self.tower:
            draw_pixel_box(surf, pygame.Rect(b["x"], b["y"] + oy, b["w"], self.block_h), b["color"], border_color=C_SLATE_DARK, elevation=2)
        if not self.game_over:
            draw_pixel_box(surf, pygame.Rect(self.cur_x, self.tower[-1]["y"] - self.block_h + oy, self.tower[-1]["w"], self.block_h), C_YELLOW, border_color=C_SLATE_DARK, elevation=2)
        draw_hud(surf, self.score, combo=self.combo, round_num=self.height)
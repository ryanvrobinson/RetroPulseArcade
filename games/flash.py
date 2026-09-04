import math
import random
import pygame
from constants import SCREEN_WIDTH, SCREEN_HEIGHT, C_SLATE_DARK, C_YELLOW, C_CORAL, C_WHITE, C_PINK, draw_hud
from audio import play_sound
from effects import spawn_burst, score_popups, ScorePopup
from mascot import draw_pulse_character
from environment import env_engine
from tournament import tournament_manager

class GameFlash:
    def __init__(self):
        self.score, self.combo, self.time_left = 0, 0, 30.0
        self.target_x, self.target_y = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2
        self.target_radius, self.target_timer, self.target_lifespan = 48, 0.0, 1.3
        self.pulse_phase = 0.0
        self.game_over = False
        self.result_data = None
        self.spawn_target()

    def spawn_target(self):
        self.target_x = random.randint(140, SCREEN_WIDTH - 140)
        self.target_y = random.randint(110, SCREEN_HEIGHT - 130)
        self.target_lifespan = max(0.65, 1.3 - (self.score / 2500) * 0.45)
        self.target_timer = self.target_lifespan
        self.target_radius = random.randint(38, 50)
        self.pulse_phase = 0.0

    def update(self, dt):
        if self.game_over: return
        self.time_left -= dt
        self.pulse_phase += dt * 8.0
        self.target_timer -= dt
        if self.target_timer <= 0:
            self.combo = 0
            self.spawn_target()
        if self.time_left <= 0:
            self.time_left = 0
            self.game_over = True
            self.result_data = tournament_manager.record_game("flash", self.score)
            play_sound("celebrate")

    def handle_click(self, mx, my):
        if self.game_over: return
        if math.hypot(mx - self.target_x, my - self.target_y) <= self.target_radius + 6:
            self.combo += 1
            pts = 100 * self.combo
            self.score += pts
            play_sound("pop")
            spawn_burst(self.target_x, self.target_y, C_YELLOW, 16, shape="star")
            score_popups.append(ScorePopup(f"+{pts}", self.target_x, self.target_y - 20, C_YELLOW))
            self.spawn_target()
        else:
            self.combo = 0
            play_sound("wrong")

    def draw(self, surf):
        env_engine.draw_base_countryside(surf)
        if not self.game_over:
            r = self.target_radius + math.sin(self.pulse_phase) * 4.0
            pygame.draw.circle(surf, C_SLATE_DARK, (int(self.target_x), int(self.target_y)), int(r + 4))
            pygame.draw.circle(surf, C_YELLOW, (int(self.target_x), int(self.target_y)), int(r))
            pygame.draw.circle(surf, C_CORAL, (int(self.target_x), int(self.target_y)), int(r * 0.72))
            pygame.draw.circle(surf, C_WHITE, (int(self.target_x), int(self.target_y)), int(r * 0.44))
            pygame.draw.circle(surf, C_PINK, (int(self.target_x), int(self.target_y)), int(r * 0.22))
            draw_pulse_character(surf, 90, SCREEN_HEIGHT - 65, scale=1.1, state="HAPPY", anim_time=self.pulse_phase * 0.5)
        draw_hud(surf, self.score, time_left=self.time_left, combo=self.combo)
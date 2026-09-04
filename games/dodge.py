import math
import random
import pygame
from constants import SCREEN_WIDTH, SCREEN_HEIGHT, C_CORAL, C_YELLOW, C_SLATE_DARK, C_WHITE, draw_hud
from audio import play_sound
from effects import spawn_burst, score_popups, ScorePopup
from mascot import draw_pulse_character
from environment import env_engine
from tournament import tournament_manager

class Obstacle:
    def __init__(self, x, y, vx, vy, radius, color):
        self.x, self.y, self.vx, self.vy = x, y, vx, vy
        self.radius, self.color = radius, color
        self.alive = True

    def update(self, dt):
        self.x += self.vx * dt * 60
        self.y += self.vy * dt * 60
        if self.x < -60 or self.x > SCREEN_WIDTH + 60 or self.y < -60 or self.y > SCREEN_HEIGHT + 60:
            self.alive = False

    def draw(self, surf):
        ix, iy, r = int(self.x), int(self.y), int(self.radius)
        pygame.draw.circle(surf, C_SLATE_DARK, (ix, iy), r + 2)
        pygame.draw.circle(surf, self.color, (ix, iy), r)
        pygame.draw.circle(surf, C_WHITE, (ix - 3, iy - 3), int(r * 0.38))

class GameDodge:
    def __init__(self):
        self.px, self.py = SCREEN_WIDTH // 2, 480
        self.speed = 360.0
        self.obstacles, self.stars = [], []
        self.score, self.survival_time = 0, 0.0
        self.spawn_timer, self.star_timer = 0.0, 0.0
        self.game_over = False
        self.facing_right = True
        self.anim_time = 0.0
        self.result_data = None

    def update(self, dt, keys):
        if self.game_over: return
        self.anim_time += dt
        self.survival_time += dt
        self.score = int(self.survival_time * 50)
        dx, dy = 0, 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]: dx -= 1; self.facing_right = False
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: dx += 1; self.facing_right = True
        if keys[pygame.K_UP] or keys[pygame.K_w]: dy -= 1
        if keys[pygame.K_DOWN] or keys[pygame.K_s]: dy += 1
        if dx != 0 and dy != 0: dx *= 0.7071; dy *= 0.7071

        self.px = max(40, min(SCREEN_WIDTH - 40, self.px + dx * self.speed * dt))
        self.py = max(80, min(SCREEN_HEIGHT - 60, self.py + dy * self.speed * dt))

        self.spawn_timer += dt
        if self.spawn_timer >= max(0.35, 1.1 - (self.survival_time / 45.0) * 0.65):
            self.spawn_timer = 0.0
            ox = random.randint(50, SCREEN_WIDTH - 50)
            self.obstacles.append(Obstacle(ox, -30, random.uniform(-1.5, 1.5), random.uniform(3.5, 6.0), random.randint(14, 22), C_CORAL))

        self.star_timer += dt
        if self.star_timer >= 3.0:
            self.star_timer = 0.0
            self.stars.append({"x": random.randint(80, SCREEN_WIDTH - 80), "y": random.randint(100, SCREEN_HEIGHT - 100), "life": 6.0})

        for obs in self.obstacles:
            obs.update(dt)
            if math.hypot(self.px - obs.x, (self.py - 10) - obs.y) < obs.radius + 16:
                self.game_over = True
                play_sound("hit")
                spawn_burst(self.px, self.py, (239, 68, 68), 24, shape="square")
                self.result_data = tournament_manager.record_game("dodge", self.score)
                break

        self.obstacles = [o for o in self.obstacles if o.alive]
        for st in self.stars:
            st["life"] -= dt
            if math.hypot(self.px - st["x"], (self.py - 10) - st["y"]) < 26:
                play_sound("coin")
                self.score += 150
                score_popups.append(ScorePopup("+150 STAR!", st["x"], st["y"], C_YELLOW))
                spawn_burst(st["x"], st["y"], C_YELLOW, 12, shape="star")
                st["life"] = -1
        self.stars = [s for s in self.stars if s["life"] > 0]

    def draw(self, surf):
        env_engine.draw_base_countryside(surf, ground_y=520)
        for st in self.stars:
            pygame.draw.circle(surf, C_YELLOW, (int(st["x"]), int(st["y"])), 12)
        for obs in self.obstacles:
            obs.draw(surf)
        state = "HIT" if self.game_over else "RUN"
        draw_pulse_character(surf, self.px, self.py, scale=1.1, state=state, anim_time=self.anim_time, facing_right=self.facing_right)
        draw_hud(surf, self.score)
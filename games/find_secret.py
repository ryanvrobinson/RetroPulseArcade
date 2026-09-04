import math
import random
import pygame
from constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT, C_CORAL, C_BLUE_CARD, C_PINK, C_PURPLE,
    C_YELLOW, C_GOLD, C_SLATE_DARK, C_WHITE, C_MINT, FONT_CARD,
    draw_pixel_box, draw_hud
)
from audio import play_sound
from effects import spawn_burst, score_popups, ScorePopup
from environment import env_engine
from tournament import tournament_manager

class GameFindSecret:
    def __init__(self):
        self.round_num = 1
        self.score = 0
        self.streak = 0
        self.time_left = 10.0
        self.items = []
        self.secret_idx = -1
        self.clue_type = "ANOMALY"
        self.clue_timer = 0.8
        self.game_over = False
        self.result_data = None
        self.anim_time = 0.0
        self.setup_round()

    def setup_round(self):
        self.items = []
        self.anim_time = 0.0
        count = min(10, 6 + (self.round_num // 2) * 2)

        modes = ["ANOMALY", "TELL", "RUNE", "PULSE"]
        self.clue_type = modes[(self.round_num - 1) % len(modes)]
        self.clue_timer = 0.75

        base_color = random.choice([C_CORAL, C_BLUE_CARD, C_PINK, C_PURPLE, C_MINT])
        cols = 4 if count >= 8 else 3
        rows = math.ceil(count / cols)

        start_x = (SCREEN_WIDTH - (cols * 130 - 30)) // 2 + 50
        start_y = 170 + (320 - (rows * 120 - 20)) // 2

        for i in range(count):
            c = i % cols
            r = i // cols
            self.items.append({
                "x": start_x + c * 130,
                "y": start_y + r * 120,
                "color": base_color,
                "radius": 34,
                "is_secret": False
            })

        self.secret_idx = random.randint(0, count - 1)
        self.items[self.secret_idx]["is_secret"] = True
        self.time_left = max(5.0, 11.0 - (self.round_num * 0.45))

    def update(self, dt):
        if self.game_over:
            return

        self.anim_time += dt
        if self.clue_timer > 0:
            self.clue_timer -= dt

        self.time_left -= dt
        if self.time_left <= 0:
            self.time_left = 0
            self.game_over = True
            play_sound("wrong")
            self.result_data = tournament_manager.record_game("find_secret", self.score)

    def handle_click(self, mx, my):
        if self.game_over:
            return

        for idx, item in enumerate(self.items):
            if math.hypot(mx - item["x"], my - item["y"]) <= item["radius"] + 6:
                if item["is_secret"]:
                    play_sound("celebrate")
                    self.streak += 1
                    pts = 350 + (self.streak * 50)
                    self.score += pts
                    spawn_burst(item["x"], item["y"], C_GOLD, 24, shape="star")
                    score_popups.append(ScorePopup(f"+{pts} SECRET FOUND!", item["x"], item["y"] - 30, C_GOLD))
                    self.round_num += 1
                    self.setup_round()
                else:
                    play_sound("wrong")
                    self.streak = 0
                    self.time_left = max(0.0, self.time_left - 1.5)
                    spawn_burst(item["x"], item["y"], (148, 163, 184), 8)
                    score_popups.append(ScorePopup("-1.5s DECOY!", mx, my - 20, (239, 68, 68)))
                break

    def draw(self, surf):
        env_engine.draw_base_countryside(surf)

        clue_desc = {
            "ANOMALY": "ANOMALY: One relic has a mismatched inner core!",
            "TELL": "WATCH THE TELL: One relic shivered at round start!",
            "RUNE": "INSCRIPTION: Find the relic marked with a golden rune!",
            "PULSE": "AURA: Spot the relic pulsing with magic!"
        }
        top_box = pygame.Rect(SCREEN_WIDTH // 2 - 210, 70, 420, 42)
        draw_pixel_box(surf, top_box, C_WHITE, border_color=C_GOLD, elevation=3)
        ctxt = FONT_CARD.render(clue_desc[self.clue_type], True, C_SLATE_DARK)
        surf.blit(ctxt, (top_box.centerx - ctxt.get_width() // 2, top_box.centery - ctxt.get_height() // 2))

        for idx, it in enumerate(self.items):
            ix, iy, ir = it["x"], it["y"], it["radius"]
            ox, oy = 0, 0
            if it["is_secret"] and self.clue_type == "TELL" and self.clue_timer > 0:
                ox = math.sin(self.anim_time * 40.0) * 4

            pygame.draw.ellipse(surf, (148, 163, 184), (ix + ox - ir - 4, iy + oy + ir - 12, (ir + 4) * 2, 20))
            draw_pixel_box(surf, pygame.Rect(ix + ox - ir, iy + oy - ir, ir * 2, ir * 2), it["color"], border_color=C_SLATE_DARK, elevation=3)

            if it["is_secret"]:
                if self.clue_type == "ANOMALY":
                    pygame.draw.circle(surf, C_GOLD, (int(ix + ox), int(iy + oy)), 12)
                    pygame.draw.circle(surf, C_WHITE, (int(ix + ox), int(iy + oy)), 5)
                elif self.clue_type == "RUNE":
                    pts = [
                        (ix + ox, iy + oy - 11), (ix + ox + 4, iy + oy - 3),
                        (ix + ox + 11, iy + oy), (ix + ox + 4, iy + oy + 4),
                        (ix + ox, iy + oy + 11), (ix + ox - 4, iy + oy + 4),
                        (ix + ox - 11, iy + oy), (ix + ox - 4, iy + oy - 3)
                    ]
                    pygame.draw.polygon(surf, C_GOLD, pts)
                elif self.clue_type == "PULSE":
                    glow_r = 10 + int(math.sin(self.anim_time * 8.0) * 4)
                    pygame.draw.circle(surf, C_GOLD, (int(ix + ox), int(iy + oy)), glow_r)
                    pygame.draw.circle(surf, C_WHITE, (int(ix + ox), int(iy + oy)), 4)
                else:
                    pygame.draw.circle(surf, C_WHITE, (int(ix + ox), int(iy + oy)), 8)
            else:
                pygame.draw.circle(surf, C_WHITE, (int(ix + ox), int(iy + oy)), 8)
                pygame.draw.circle(surf, C_SLATE_DARK, (int(ix + ox), int(iy + oy)), 3)

        draw_hud(surf, self.score, time_left=self.time_left, round_num=self.round_num)
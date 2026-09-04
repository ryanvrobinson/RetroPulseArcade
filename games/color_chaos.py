import math
import random
import pygame
from constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT, C_BLUE_CARD, C_YELLOW, C_MINT,
    C_SLATE_DEEP, C_WHITE, C_SLATE_DARK, C_CORAL, C_PURPLE, C_GOLD,
    FONT_CARD, draw_pixel_box, draw_hud
)
from audio import play_sound
from effects import spawn_burst, score_popups, ScorePopup
from tournament import tournament_manager

class GameColorChaos:
    def __init__(self):
        self.score, self.combo, self.time_left = 0, 0, 30.0
        self.target_color_name = "BLUE"
        self.target_color = C_BLUE_CARD
        self.bubbles = []
        self.rule_timer = 5.5
        self.spawn_timer = 0.0
        self.game_over = False
        self.result_data = None
        self.streak = 0
        self.palette = [
            ("BLUE", C_BLUE_CARD),
            ("RED", (239, 68, 68)),
            ("YELLOW", C_YELLOW),
            ("MINT", C_MINT),
            ("PURPLE", C_PURPLE)
        ]
        self.pick_new_rule()

    def pick_new_rule(self):
        valid_opts = [opt for opt in self.palette if opt[0] != self.target_color_name]
        self.target_color_name, self.target_color = random.choice(valid_opts)
        self.rule_timer = 5.5
        play_sound("pop")
        score_popups.append(ScorePopup(f"RULE: POP {self.target_color_name}!", SCREEN_WIDTH // 2, 220, self.target_color))

    def update(self, dt):
        if self.game_over:
            return

        self.time_left -= dt
        if self.time_left <= 0:
            self.time_left = 0
            self.game_over = True
            play_sound("celebrate")
            self.result_data = tournament_manager.record_game("color_chaos", self.score)
            return

        self.rule_timer -= dt
        if self.rule_timer <= 0:
            self.pick_new_rule()

        self.spawn_timer += dt
        spawn_rate = max(0.38, 0.7 - (self.score / 3500.0))
        if self.spawn_timer >= spawn_rate:
            self.spawn_timer = 0.0
            is_bomb = (random.random() < 0.22)
            chosen = random.choice(self.palette)
            self.bubbles.append({
                "x": random.randint(100, SCREEN_WIDTH - 100),
                "y": SCREEN_HEIGHT + 35,
                "color_name": chosen[0],
                "color": chosen[1],
                "is_bomb": is_bomb,
                "radius": 28,
                "vy": random.uniform(3.0, 5.2),
                "wobble": random.uniform(0, 6.28)
            })

        for b in self.bubbles:
            b["y"] -= b["vy"] * dt * 60
            b["wobble"] += dt * 4.0
            b["x"] += math.sin(b["wobble"]) * 1.2

        self.bubbles = [b for b in self.bubbles if b["y"] > -50]

    def handle_click(self, mx, my):
        if self.game_over:
            return

        clicked_idx = -1
        for idx, b in enumerate(self.bubbles):
            if math.hypot(mx - b["x"], my - b["y"]) <= b["radius"] + 6:
                clicked_idx = idx
                break

        if clicked_idx != -1:
            b = self.bubbles.pop(clicked_idx)
            if b["is_bomb"]:
                play_sound("hit")
                self.combo = 0
                self.streak = 0
                self.time_left = max(0.0, self.time_left - 2.5)
                spawn_burst(b["x"], b["y"], (239, 68, 68), 20, shape="square")
                score_popups.append(ScorePopup("HAZARD! -2.5s", b["x"], b["y"] - 20, (239, 68, 68)))
            elif b["color_name"] == self.target_color_name:
                play_sound("pop")
                self.combo += 1
                self.streak += 1
                pts = 100 * self.combo
                self.score += pts
                spawn_burst(b["x"], b["y"], b["color"], 16, shape="star")
                score_popups.append(ScorePopup(f"+{pts}", b["x"], b["y"] - 20, C_GOLD))

                if self.streak % 5 == 0:
                    self.time_left = min(45.0, self.time_left + 1.5)
                    play_sound("coin")
                    score_popups.append(ScorePopup("+1.5s TIME BONUS!", SCREEN_WIDTH // 2, 280, C_MINT))
            else:
                play_sound("wrong")
                self.combo = 0
                self.streak = 0
                spawn_burst(b["x"], b["y"], (148, 163, 184), 8)
                score_popups.append(ScorePopup("MISS!", b["x"], b["y"] - 20, (239, 68, 68)))

    def draw(self, surf):
        surf.fill(C_SLATE_DEEP)

        rule_box = pygame.Rect(SCREEN_WIDTH // 2 - 180, 68, 360, 44)
        draw_pixel_box(surf, rule_box, self.target_color, border_color=C_WHITE, elevation=3)
        rtxt = FONT_CARD.render(f"DIRECTIVE: POP {self.target_color_name}!", True, C_SLATE_DARK)
        surf.blit(rtxt, (rule_box.centerx - rtxt.get_width() // 2, rule_box.centery - rtxt.get_height() // 2))

        for b in self.bubbles:
            bx, by, br = int(b["x"]), int(b["y"]), b["radius"]
            if b["is_bomb"]:
                pygame.draw.circle(surf, C_SLATE_DARK, (bx, by), br + 2)
                pygame.draw.circle(surf, (239, 68, 68), (bx, by), br)
                pygame.draw.line(surf, C_WHITE, (bx - 7, by - 7), (bx + 7, by + 7), 3)
                pygame.draw.line(surf, C_WHITE, (bx - 7, by + 7), (bx + 7, by - 7), 3)
            else:
                pygame.draw.circle(surf, C_SLATE_DARK, (bx, by), br + 2)
                pygame.draw.circle(surf, b["color"], (bx, by), br)
                pygame.draw.circle(surf, C_WHITE, (bx - 8, by - 8), 6)

        draw_hud(surf, self.score, time_left=self.time_left, combo=self.combo)
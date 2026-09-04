import math
import random
import pygame
from constants import (
    SCREEN_WIDTH, C_CREAM, C_WHITE, C_BLUE_CARD,
    C_SLATE_DARK, FONT_CARD, draw_pixel_box, draw_hud
)
from audio import play_sound
from tournament import tournament_manager

class GameMemoryPuzzle:
    def __init__(self):
        self.round_num, self.score, self.combo = 1, 0, 0
        self.cards, self.flipped = [], []
        self.preview_timer, self.in_preview = 1.8, True
        self.mismatch_timer = 0.0
        self.time_left = 45.0
        self.game_over = False
        self.result_data = None
        self.setup_grid()

    def setup_grid(self):
        self.cards, self.flipped, self.mismatch_timer = [], [], 0.0
        deck = (["STAR", "HEART", "GEM", "MOON", "BOLT", "CLOVER"][:min(6, 3 + self.round_num)]) * 2
        random.shuffle(deck)
        cols = 3 if len(deck) == 6 else 4
        rows = math.ceil(len(deck) / cols)
        start_x = (SCREEN_WIDTH - (cols * 108 - 18)) // 2
        start_y = 120 + (380 - (rows * 128 - 18)) // 2
        for i, sym in enumerate(deck):
            c, r = i % cols, i // cols
            self.cards.append({
                "symbol": sym, "rect": pygame.Rect(start_x + c * 108, start_y + r * 128, 90, 110),
                "matched": False, "face_up": True
            })
        self.in_preview = True
        self.preview_timer = 1.6

    def update(self, dt):
        if self.game_over: return
        self.time_left -= dt
        if self.time_left <= 0:
            self.time_left = 0; self.game_over = True
            self.result_data = tournament_manager.record_game("memory", self.score)
            return
        if self.in_preview:
            self.preview_timer -= dt
            if self.preview_timer <= 0:
                self.in_preview = False
                for c in self.cards: c["face_up"] = False
        if self.mismatch_timer > 0:
            self.mismatch_timer -= dt
            if self.mismatch_timer <= 0:
                for c in self.flipped: c["face_up"] = False
                self.flipped = []

    def handle_click(self, mx, my):
        if self.game_over or self.in_preview or self.mismatch_timer > 0 or len(self.flipped) >= 2: return
        for card in self.cards:
            if card["rect"].collidepoint(mx, my) and not card["face_up"] and not card["matched"]:
                card["face_up"] = True
                self.flipped.append(card)
                if len(self.flipped) == 2:
                    if self.flipped[0]["symbol"] == self.flipped[1]["symbol"]:
                        self.flipped[0]["matched"] = self.flipped[1]["matched"] = True
                        self.combo += 1; self.score += 200 * self.combo
                        play_sound("coin")
                        self.flipped = []
                        if all(c["matched"] for c in self.cards):
                            self.score += 500; self.time_left += 8.0
                            self.round_num += 1; self.setup_grid()
                    else:
                        play_sound("wrong")
                        self.combo = 0; self.mismatch_timer = 0.5
                break

    def draw(self, surf):
        surf.fill(C_CREAM)
        for card in self.cards:
            col = C_WHITE if card["face_up"] or card["matched"] else C_BLUE_CARD
            draw_pixel_box(surf, card["rect"], col, border_color=C_SLATE_DARK, elevation=4)
            if card["face_up"] or card["matched"]:
                txt = FONT_CARD.render(card["symbol"][:3], True, C_SLATE_DARK)
                surf.blit(txt, (card["rect"].centerx - txt.get_width() // 2, card["rect"].centery - txt.get_height() // 2))
        draw_hud(surf, self.score, time_left=self.time_left, combo=self.combo, round_num=self.round_num)
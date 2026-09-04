"""
MINI GAME 3: SPOT IT
Visual observation and memory game where players discover which shape subtly morphed or shifted.
"""
import pygame
import random
from game.states import State
from game.utils import draw_rounded_rect, draw_text, draw_radial_glow
from game.animation import FloatingText
from game.settings import (
    COLOR_BG_CARD, COLOR_ACCENT_CYAN, COLOR_ACCENT_PINK,
    COLOR_ACCENT_YELLOW, COLOR_ACCENT_GREEN, COLOR_WHITE, COLOR_GRAY, COLOR_DANGER
)

SHAPE_COLORS = [
    (0, 240, 255),   # Cyan
    (255, 0, 128),   # Pink
    (255, 215, 0),   # Gold
    (0, 255, 136),   # Emerald
    (157, 78, 221),  # Purple
    (255, 102, 0)    # Orange
]

SHAPE_TYPES = ["circle", "rect", "triangle"]

class SceneObject:
    def __init__(self, obj_id, x, y, size, shape_type, color):
        self.id = obj_id
        self.x = float(x)
        self.y = float(y)
        self.size = float(size)
        self.shape_type = shape_type
        self.color = color

    def copy(self):
        return SceneObject(self.id, self.x, self.y, self.size, self.shape_type, self.color)

    def draw(self, surface, highlight=False):
        center = (int(self.x), int(self.y))
        r = int(self.size // 2)

        if highlight:
            draw_radial_glow(surface, center, r + 15, COLOR_ACCENT_YELLOW, max_alpha=120)

        if self.shape_type == "circle":
            pygame.draw.circle(surface, self.color, center, r)
        elif self.shape_type == "rect":
            rect = pygame.Rect(self.x - r, self.y - r, self.size, self.size)
            draw_rounded_rect(surface, self.color, rect, radius=8)
        elif self.shape_type == "triangle":
            points = [
                (self.x, self.y - r),
                (self.x - r, self.y + r),
                (self.x + r, self.y + r)
            ]
            pygame.draw.polygon(surface, self.color, points)

    def contains_point(self, px, py):
        r = self.size // 2
        return abs(px - self.x) <= r and abs(py - self.y) <= r


class ObservationGame(State):
    def enter(self, **kwargs):
        self.play_rect = pygame.Rect(40, 80, self.game.width - 80, self.game.height - 110)
        self.score = 0
        self.streak = 0
        self.best_streak = 0
        self.round_num = 1
        self.lives = 3
        self.game_over = False

        self.phase = "observe"  # "observe", "transition", "guess"
        self.phase_timer = 3.0
        self.objects = []
        self.changed_obj_id = None
        self.floating_texts = []

        self.start_new_round()

    def start_new_round(self):
        num_items = min(12, 4 + (self.round_num // 2))
        self.objects.clear()

        pad = 50
        cols = 4
        rows = 3
        cell_w = self.play_rect.width // cols
        cell_h = self.play_rect.height // rows

        positions = []
        for c in range(cols):
            for r in range(rows):
                cx = self.play_rect.left + c * cell_w + cell_w // 2 + random.randint(-20, 20)
                cy = self.play_rect.top + r * cell_h + cell_h // 2 + random.randint(-20, 20)
                positions.append((cx, cy))

        random.shuffle(positions)

        for i in range(num_items):
            x, y = positions[i]
            size = random.choice([44, 56, 68])
            stype = random.choice(SHAPE_TYPES)
            color = random.choice(SHAPE_COLORS)
            self.objects.append(SceneObject(i, x, y, size, stype, color))

        # Pick one object to morph
        target = random.choice(self.objects)
        self.changed_obj_id = target.id

        self.mutation_type = random.choice(["color", "shape", "size"])
        self.mutated_target = target.copy()

        if self.mutation_type == "color":
            other_colors = [c for c in SHAPE_COLORS if c != target.color]
            self.mutated_target.color = random.choice(other_colors)
        elif self.mutation_type == "shape":
            other_shapes = [s for s in SHAPE_TYPES if s != target.shape_type]
            self.mutated_target.shape_type = random.choice(other_shapes)
        elif self.mutation_type == "size":
            self.mutated_target.size = 28 if target.size >= 56 else 76

        self.phase = "observe"
        self.phase_timer = max(1.5, 3.2 - (self.round_num * 0.15))

    def handle_input(self, input_handler):
        if self.game_over:
            if input_handler.is_key_down(pygame.K_SPACE) or input_handler.is_key_down(pygame.K_RETURN):
                self.enter()
            elif input_handler.is_key_down(pygame.K_ESCAPE):
                self.game.set_state("menu")
            elif input_handler.mouse_clicked:
                mx, my = input_handler.mouse_pos
                if pygame.Rect(self.game.width // 2 - 160, 460, 140, 48).collidepoint(mx, my):
                    self.game.audio.play("click")
                    self.enter()
                elif pygame.Rect(self.game.width // 2 + 20, 460, 140, 48).collidepoint(mx, my):
                    self.game.audio.play("click")
                    self.game.set_state("menu")
            return

        if input_handler.is_key_down(pygame.K_ESCAPE):
            self.game.set_state("menu")
            return

        if self.phase == "guess" and input_handler.mouse_clicked:
            mx, my = input_handler.mouse_pos
            if not self.play_rect.collidepoint(mx, my):
                return

            clicked_obj = None
            for obj in self.objects:
                if obj.contains_point(mx, my):
                    clicked_obj = obj
                    break

            if clicked_obj:
                if clicked_obj.id == self.changed_obj_id:
                    # Correct!
                    self.game.audio.play("success")
                    self.streak += 1
                    if self.streak > self.best_streak:
                        self.best_streak = self.streak

                    time_bonus = int(self.phase_timer * 100)
                    gained = 300 + (self.streak * 50) + time_bonus
                    self.score += gained
                    self.round_num += 1

                    self.game.particles.emit_burst(clicked_obj.x, clicked_obj.y, count=24, colors=[COLOR_ACCENT_GREEN, COLOR_WHITE, COLOR_ACCENT_YELLOW])
                    self.floating_texts.append(FloatingText(f"CORRECT! +{gained}", clicked_obj.x, clicked_obj.y - 30, color=COLOR_ACCENT_GREEN, size=22))
                    self.start_new_round()
                else:
                    # Wrong!
                    self.game.audio.play("error")
                    self.streak = 0
                    self.lives -= 1
                    self.game.shake.add_shake(intensity=8.0, duration=0.25)
                    self.floating_texts.append(FloatingText("WRONG!", clicked_obj.x, clicked_obj.y - 20, color=COLOR_DANGER, size=20))
                    
                    if self.lives <= 0:
                        self.game_over = True
                        self.game.audio.play("gameover")
                        self.game.save_high_score("observation", self.score, self.best_streak)

    def update(self, dt):
        for ft in self.floating_texts:
            ft.update(dt)
        self.floating_texts = [ft for ft in self.floating_texts if not ft.dead]

        if self.game_over:
            return

        self.phase_timer -= dt
        if self.phase == "observe" and self.phase_timer <= 0:
            # Transition to guess phase by swapping mutated object
            self.phase = "guess"
            self.phase_timer = 5.0
            for idx, obj in enumerate(self.objects):
                if obj.id == self.changed_obj_id:
                    self.objects[idx] = self.mutated_target
                    break
        elif self.phase == "guess" and self.phase_timer <= 0:
            # Timeout counts as a lost life
            self.game.audio.play("error")
            self.streak = 0
            self.lives -= 1
            if self.lives <= 0:
                self.game_over = True
                self.game.audio.play("gameover")
                self.game.save_high_score("observation", self.score, self.best_streak)
            else:
                self.start_new_round()

    def draw(self, surface):
        # Header
        draw_text(surface, "SPOT IT!", 40, 45, font_size=28, color=COLOR_ACCENT_YELLOW, align="left", bold=True)
        draw_text(surface, f"SCORE: {self.score}", self.game.width // 2 - 120, 45, font_size=24, color=COLOR_WHITE, bold=True)
        draw_text(surface, f"STREAK: x{self.streak}", self.game.width // 2 + 40, 45, font_size=24, color=COLOR_ACCENT_CYAN, bold=True)

        # Lives indicators
        hearts = "♥ " * self.lives
        draw_text(surface, hearts.strip(), self.game.width - 50, 45, font_size=24, color=COLOR_DANGER, align="right", bold=True)

        # Arena
        draw_rounded_rect(surface, COLOR_BG_CARD, self.play_rect, radius=16, border_width=2, border_color=(60, 68, 95))

        # Instructions / Prompt bar
        status_bar = pygame.Rect(self.play_rect.left, self.play_rect.top, self.play_rect.width, 36)
        draw_rounded_rect(surface, (28, 32, 48), status_bar, radius=8)
        if self.phase == "observe":
            draw_text(surface, f"MEMORIZE THE SCENE ({self.phase_timer:.1f}s)", status_bar.centerx, status_bar.centery, font_size=18, color=COLOR_ACCENT_CYAN, bold=True)
        else:
            draw_text(surface, f"WHICH SHAPE CHANGED? ({self.phase_timer:.1f}s)", status_bar.centerx, status_bar.centery, font_size=18, color=COLOR_ACCENT_YELLOW, bold=True)

        # Render Objects
        for obj in self.objects:
            obj.draw(surface)

        for ft in self.floating_texts:
            ft.draw(surface)

        # Game Over Screen
        if self.game_over:
            overlay = pygame.Surface((self.game.width, self.game.height), pygame.SRCALPHA)
            overlay.fill((16, 18, 27, 210))
            surface.blit(overlay, (0, 0))

            card_rect = pygame.Rect(self.game.width // 2 - 220, 130, 440, 400)
            draw_rounded_rect(surface, COLOR_BG_CARD, card_rect, radius=18, border_width=2, border_color=COLOR_ACCENT_YELLOW)

            draw_text(surface, "ROUND OVER", self.game.width // 2, 180, font_size=36, color=COLOR_DANGER, bold=True)
            draw_text(surface, f"FINAL SCORE: {self.score}", self.game.width // 2, 245, font_size=28, color=COLOR_WHITE, bold=True)
            draw_text(surface, f"BEST STREAK: {self.best_streak}", self.game.width // 2, 295, font_size=22, color=COLOR_ACCENT_YELLOW)

            high = self.game.scores.get("observation", {}).get("high_score", 0)
            if self.score >= high and self.score > 0:
                draw_text(surface, "★ NEW HIGH SCORE! ★", self.game.width // 2, 350, font_size=24, color=COLOR_ACCENT_GREEN, bold=True)

            btn_replay = pygame.Rect(self.game.width // 2 - 160, 415, 140, 48)
            btn_menu = pygame.Rect(self.game.width // 2 + 20, 415, 140, 48)
            
            draw_rounded_rect(surface, COLOR_ACCENT_YELLOW, btn_replay, radius=10)
            draw_text(surface, "AGAIN (Space)", btn_replay.centerx, btn_replay.centery, font_size=18, color=COLOR_BG_CARD, bold=True)
            
            draw_rounded_rect(surface, (50, 56, 78), btn_menu, radius=10)
            draw_text(surface, "MENU (Esc)", btn_menu.centerx, btn_menu.centery, font_size=18, color=COLOR_WHITE, bold=True)
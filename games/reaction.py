"""
MINI GAME 1: FLASH!
High-speed reflex and target tracking with satisfying combo multipliers.
"""
import pygame
import random
import math
from game.states import State
from game.utils import draw_rounded_rect, draw_text, draw_radial_glow, get_font
from game.animation import FloatingText, Tween
from game.settings import (
    COLOR_BG_CARD, COLOR_ACCENT_CYAN, COLOR_ACCENT_PINK,
    COLOR_ACCENT_YELLOW, COLOR_ACCENT_GREEN, COLOR_WHITE, COLOR_GRAY, COLOR_DANGER
)

class ReactionGame(State):
    def enter(self, **kwargs):
        self.total_time = 30.0
        self.time_left = self.total_time
        self.score = 0
        self.combo = 0
        self.best_combo = 0
        self.hits = 0
        self.clicks = 0
        self.game_over = False

        self.play_rect = pygame.Rect(40, 90, self.game.width - 80, self.game.height - 150)
        self.target_x = 0
        self.target_y = 0
        self.base_radius = 45.0
        self.radius = self.base_radius
        self.spawn_timer = 0.0
        self.pulse = 0.0

        self.floating_texts = []
        self.target_tween = Tween(0.0, 1.0, 0.25, easing="elastic")
        self.spawn_target()

    def spawn_target(self):
        # Progressively shrink radius based on score
        self.radius = max(20.0, self.base_radius - (self.score / 250.0))
        pad = int(self.radius + 15)
        self.target_x = random.randint(self.play_rect.left + pad, self.play_rect.right - pad)
        self.target_y = random.randint(self.play_rect.top + pad, self.play_rect.bottom - pad)
        self.target_tween.reset(0.0, 1.0)
        self.pulse = 0.0

    def handle_input(self, input_handler):
        if self.game_over:
            if input_handler.is_key_down(pygame.K_SPACE) or input_handler.is_key_down(pygame.K_RETURN):
                self.enter()
            elif input_handler.is_key_down(pygame.K_ESCAPE):
                self.game.set_state("menu")
            elif input_handler.mouse_clicked:
                mx, my = input_handler.mouse_pos
                # Replay Button
                if pygame.Rect(self.game.width // 2 - 160, 480, 140, 48).collidepoint(mx, my):
                    self.game.audio.play("click")
                    self.enter()
                # Menu Button
                elif pygame.Rect(self.game.width // 2 + 20, 480, 140, 48).collidepoint(mx, my):
                    self.game.audio.play("click")
                    self.game.set_state("menu")
            return

        if input_handler.is_key_down(pygame.K_ESCAPE):
            self.game.set_state("menu")
            return

        if input_handler.mouse_clicked:
            mx, my = input_handler.mouse_pos
            self.clicks += 1

            if not self.play_rect.collidepoint(mx, my):
                return

            dist = math.hypot(mx - self.target_x, my - self.target_y)
            cur_r = self.radius * self.target_tween.current

            if dist <= cur_r:
                # HIT!
                self.hits += 1
                self.combo += 1
                if self.combo > self.best_combo:
                    self.best_combo = self.combo

                base_points = int(100 * (1.0 + (cur_r / self.base_radius)))
                multiplier = min(5.0, 1.0 + (self.combo - 1) * 0.25)
                points_awarded = int(base_points * multiplier)
                self.score += points_awarded

                # Visual Juice
                self.game.audio.play("hit" if self.combo < 5 else "combo")
                self.game.particles.emit_burst(self.target_x, self.target_y, count=16, colors=[COLOR_ACCENT_CYAN, COLOR_ACCENT_PINK, COLOR_WHITE])
                self.game.shake.add_shake(intensity=min(6.0, 2.0 + self.combo * 0.4), duration=0.15)
                
                txt_col = COLOR_ACCENT_YELLOW if self.combo > 4 else COLOR_ACCENT_CYAN
                combo_str = f"+{points_awarded} (x{self.combo})" if self.combo > 1 else f"+{points_awarded}"
                self.floating_texts.append(FloatingText(combo_str, self.target_x, self.target_y - 20, color=txt_col, size=22))

                self.spawn_target()
            else:
                # MISS!
                if self.combo > 0:
                    self.combo = 0
                    self.game.audio.play("error")
                    self.floating_texts.append(FloatingText("COMBO LOST", mx, my, color=COLOR_DANGER, size=18))

    def update(self, dt):
        for ft in self.floating_texts:
            ft.update(dt)
        self.floating_texts = [ft for ft in self.floating_texts if not ft.dead]

        if self.game_over:
            return

        self.target_tween.update(dt)
        self.pulse += dt * 6.0
        self.time_left -= dt

        if self.time_left <= 0:
            self.time_left = 0
            self.game_over = True
            self.game.audio.play("gameover")
            self.game.save_high_score("reaction", self.score, self.best_combo)

    def draw(self, surface):
        # Header / Status bar
        draw_text(surface, "FLASH! - REACTION", 40, 45, font_size=28, color=COLOR_ACCENT_CYAN, align="left", bold=True)
        draw_text(surface, f"SCORE: {self.score}", self.game.width // 2 - 80, 45, font_size=24, color=COLOR_WHITE, bold=True)
        
        # Combo Indicator with dynamic pulse
        combo_col = COLOR_ACCENT_YELLOW if self.combo >= 5 else COLOR_ACCENT_PINK
        combo_scale = f"COMBO: x{self.combo}" if self.combo > 0 else "COMBO: -"
        draw_text(surface, combo_scale, self.game.width // 2 + 100, 45, font_size=24, color=combo_col, bold=True)

        # Time Bar
        bar_w = 160
        bar_h = 16
        bar_x = self.game.width - 200
        bar_y = 37
        ratio = max(0.0, self.time_left / self.total_time)
        draw_rounded_rect(surface, (40, 44, 60), (bar_x, bar_y, bar_w, bar_h), radius=6)
        bar_color = COLOR_ACCENT_GREEN if ratio > 0.3 else COLOR_DANGER
        if ratio > 0:
            draw_rounded_rect(surface, bar_color, (bar_x, bar_y, int(bar_w * ratio), bar_h), radius=6)
        draw_text(surface, f"{self.time_left:.1f}s", bar_x + bar_w // 2, bar_y + 8, font_size=14, color=COLOR_WHITE, bold=True)

        # Arena Boundary
        draw_rounded_rect(surface, COLOR_BG_CARD, self.play_rect, radius=16, border_width=2, border_color=(60, 68, 95))

        # Render Active Target
        if not self.game_over:
            scale = self.target_tween.current
            current_r = max(2.0, self.radius * scale)
            
            # Subtle radial breathing
            pulse_offset = math.sin(self.pulse) * 3.0
            draw_radial_glow(surface, (int(self.target_x), int(self.target_y)), int(current_r + 18 + pulse_offset), COLOR_ACCENT_CYAN, max_alpha=90)
            
            # Target Rings
            pygame.draw.circle(surface, COLOR_ACCENT_PINK, (int(self.target_x), int(self.target_y)), int(current_r))
            pygame.draw.circle(surface, COLOR_BG_CARD, (int(self.target_x), int(self.target_y)), int(current_r * 0.65))
            pygame.draw.circle(surface, COLOR_ACCENT_YELLOW, (int(self.target_x), int(self.target_y)), int(current_r * 0.3))

        # Floating Popups
        for ft in self.floating_texts:
            ft.draw(surface)

        # Game Over Overlay
        if self.game_over:
            overlay = pygame.Surface((self.game.width, self.game.height), pygame.SRCALPHA)
            overlay.fill((16, 18, 27, 210))
            surface.blit(overlay, (0, 0))

            card_rect = pygame.Rect(self.game.width // 2 - 220, 110, 440, 430)
            draw_rounded_rect(surface, COLOR_BG_CARD, card_rect, radius=18, border_width=2, border_color=COLOR_ACCENT_CYAN)

            draw_text(surface, "TIME'S UP!", self.game.width // 2, 160, font_size=36, color=COLOR_ACCENT_PINK, bold=True)
            draw_text(surface, f"FINAL SCORE: {self.score}", self.game.width // 2, 230, font_size=28, color=COLOR_WHITE, bold=True)
            draw_text(surface, f"BEST COMBO: x{self.best_combo}", self.game.width // 2, 280, font_size=22, color=COLOR_ACCENT_YELLOW)
            
            acc = int((self.hits / self.clicks) * 100) if self.clicks > 0 else 0
            draw_text(surface, f"ACCURACY: {acc}% ({self.hits}/{self.clicks})", self.game.width // 2, 325, font_size=20, color=COLOR_GRAY)

            high = self.game.scores.get("reaction", {}).get("high_score", 0)
            if self.score >= high and self.score > 0:
                draw_text(surface, "★ NEW HIGH SCORE! ★", self.game.width // 2, 375, font_size=24, color=COLOR_ACCENT_GREEN, bold=True)

            # Action Buttons
            btn_replay = pygame.Rect(self.game.width // 2 - 160, 435, 140, 48)
            btn_menu = pygame.Rect(self.game.width // 2 + 20, 435, 140, 48)
            
            draw_rounded_rect(surface, COLOR_ACCENT_CYAN, btn_replay, radius=10)
            draw_text(surface, "AGAIN (Space)", btn_replay.centerx, btn_replay.centery, font_size=18, color=COLOR_BG_CARD, bold=True)
            
            draw_rounded_rect(surface, (50, 56, 78), btn_menu, radius=10)
            draw_text(surface, "MENU (Esc)", btn_menu.centerx, btn_menu.centery, font_size=18, color=COLOR_WHITE, bold=True)
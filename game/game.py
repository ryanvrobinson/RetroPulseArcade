"""
Core Engine orchestrating states, window transitions, UI menus, and the 60 FPS loop.
"""
import pygame
import sys
import math
import random
from datetime import datetime
from game.settings import (
    DEFAULT_WIDTH, DEFAULT_HEIGHT, FPS, TITLE,
    COLOR_BG, COLOR_BG_SURFACE, COLOR_BG_CARD, COLOR_ACCENT_CYAN, COLOR_ACCENT_PINK,
    COLOR_ACCENT_YELLOW, COLOR_ACCENT_GREEN, COLOR_ACCENT_PURPLE, COLOR_WHITE, COLOR_GRAY, COLOR_DARK_GRAY,
    load_settings, save_settings, load_scores, save_scores
)
from game.audio import AudioManager
from game.particles import ParticleSystem
from game.effects import ScreenShake
from game.input import InputHandler
from game.utils import draw_rounded_rect, draw_text, draw_radial_glow
from games.reaction import ReactionGame
from games.dodge import DodgeGame
from games.observation import ObservationGame

class ArcadeHub:
    def __init__(self):
        pygame.init()
        self.settings = load_settings()
        self.scores = load_scores()

        self.width = self.settings.get("width", DEFAULT_WIDTH)
        self.height = self.settings.get("height", DEFAULT_HEIGHT)
        self.fullscreen = self.settings.get("fullscreen", False)

        flags = pygame.DOUBLEBUF | (pygame.FULLSCREEN if self.fullscreen else 0)
        self.screen = pygame.display.set_mode((self.width, self.height), flags)
        pygame.display.set_caption(TITLE)

        self.clock = pygame.time.Clock()
        self.running = True

        self.audio = AudioManager()
        self.audio.set_sound_enabled(self.settings.get("sound_on", True))
        self.audio.set_music_enabled(self.settings.get("music_on", True))

        self.particles = ParticleSystem()
        self.shake = ScreenShake()
        self.input = InputHandler()

        # States registry
        self.states = {
            "reaction": ReactionGame(self),
            "dodge": DodgeGame(self),
            "observation": ObservationGame(self)
        }
        self.current_state_name = "menu"
        self.menu_tab = "main" # "main", "games", "scores", "settings"
        self.ui_anim_time = 0.0

        # Precompute stars for background aesthetics
        self.stars = [
            (random.randint(0, self.width), random.randint(0, self.height), random.uniform(0.5, 2.0))
            for _ in range(70)
        ]

    def toggle_fullscreen(self):
        self.fullscreen = not self.fullscreen
        self.settings["fullscreen"] = self.fullscreen
        save_settings(self.settings)
        flags = pygame.DOUBLEBUF | (pygame.FULLSCREEN if self.fullscreen else 0)
        self.screen = pygame.display.set_mode((self.width, self.height), flags)

    def set_state(self, state_name):
        self.particles.clear()
        if state_name in self.states:
            self.current_state_name = state_name
            self.states[state_name].enter()
        else:
            self.current_state_name = "menu"

    def save_high_score(self, game_key, score, combo):
        entry = self.scores.get(game_key, {"high_score": 0, "best_combo": 0, "last_played": "Never"})
        updated = False
        if score > entry.get("high_score", 0):
            entry["high_score"] = score
            updated = True
        if combo > entry.get("best_combo", 0):
            entry["best_combo"] = combo
            updated = True
        entry["last_played"] = datetime.now().strftime("%Y-%m-%d %H:%M")
        self.scores[game_key] = entry
        save_scores(self.scores)
        return updated

    def run(self):
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            dt = min(dt, 0.05) # Cap delta time to prevent spiraling
            self.ui_anim_time += dt

            # Global Events
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_F11:
                    self.toggle_fullscreen()

            self.input.process_events(events)

            # Update Active Mode
            if self.current_state_name == "menu":
                self._update_menu(dt)
            else:
                active_game = self.states[self.current_state_name]
                active_game.handle_input(self.input)
                active_game.update(dt)

            self.particles.update(dt)
            self.shake.update(dt)

            # Render
            render_surface = pygame.Surface((self.width, self.height))
            render_surface.fill(COLOR_BG)

            # Ambient Background Nebula
            self._draw_background(render_surface)

            if self.current_state_name == "menu":
                self._draw_menu(render_surface)
            else:
                self.states[self.current_state_name].draw(render_surface)

            self.particles.draw(render_surface)

            # Apply Screen Shake offset
            ox, oy = self.shake.get_offset()
            self.screen.blit(render_surface, (ox, oy))
            pygame.display.flip()

        pygame.quit()
        sys.exit()

    def _draw_background(self, surface):
        for x, y, speed in self.stars:
            twinkle = (math.sin(self.ui_anim_time * speed * 2.0) + 1.0) * 0.5
            col = int(90 + twinkle * 100)
            surface.set_at((int(x), int(y)), (col, col, int(col * 1.2)))

    def _update_menu(self, dt):
        mx, my = self.input.mouse_pos
        clicked = self.input.mouse_clicked

        if self.menu_tab == "main":
            # Main menu with PLAY button as primary focus
            play_button_rect = pygame.Rect(self.width // 2 - 180, self.height // 2 + 50, 360, 80)
            if play_button_rect.collidepoint(mx, my) and clicked:
                self.audio.play("click")
                self.set_state("reaction")  # Directly launch FLASH! game
                return

            # Secondary buttons below
            secondary_buttons = [
                ("MINI GAMES", self.height // 2 + 150, lambda: setattr(self, "menu_tab", "games")),
                ("HIGH SCORES", self.height // 2 + 210, lambda: setattr(self, "menu_tab", "scores")),
                ("SETTINGS", self.height // 2 + 270, lambda: setattr(self, "menu_tab", "settings")),
                ("QUIT", self.height // 2 + 330, lambda: setattr(self, "running", False))
            ]

            for label, y, action in secondary_buttons:
                rect = pygame.Rect(self.width // 2 - 120, y, 240, 50)
                if rect.collidepoint(mx, my) and clicked:
                    self.audio.play("click")
                    action()

        elif self.menu_tab == "games":
            cards = [
                ("reaction", self.width // 2 - 260, 180),
                ("dodge", self.width // 2, 180),
                ("observation", self.width // 2 + 260, 180),
            ]
            for g_id, x, y in cards:
                card_rect = pygame.Rect(x, y, 200, 260)
                if card_rect.collidepoint(mx, my) and clicked:
                    self.audio.play("click")
                    self.set_state(g_id)

            back_btn = pygame.Rect(self.width // 2 - 80, 480, 160, 44)
            if back_btn.collidepoint(mx, my) and clicked:
                self.audio.play("click")
                self.menu_tab = "main"

        elif self.menu_tab == "scores":
            back_btn = pygame.Rect(self.width // 2 - 80, 480, 160, 44)
            if back_btn.collidepoint(mx, my) and clicked:
                self.audio.play("click")
                self.menu_tab = "main"

        elif self.menu_tab == "settings":
            # Toggles
            sound_btn = pygame.Rect(self.width // 2 + 60, 200, 80, 36)
            music_btn = pygame.Rect(self.width // 2 + 60, 260, 80, 36)
            screen_btn = pygame.Rect(self.width // 2 + 60, 320, 80, 36)
            back_btn = pygame.Rect(self.width // 2 - 80, 440, 160, 44)

            if clicked:
                if sound_btn.collidepoint(mx, my):
                    self.audio.play("click")
                    self.settings["sound_on"] = not self.settings["sound_on"]
                    self.audio.set_sound_enabled(self.settings["sound_on"])
                    save_settings(self.settings)
                elif music_btn.collidepoint(mx, my):
                    self.audio.play("click")
                    self.settings["music_on"] = not self.settings["music_on"]
                    self.audio.set_music_enabled(self.settings["music_on"])
                    save_settings(self.settings)
                elif screen_btn.collidepoint(mx, my):
                    self.audio.play("click")
                    self.toggle_fullscreen()
                elif back_btn.collidepoint(mx, my):
                    self.audio.play("click")
                    self.menu_tab = "main"

    def _draw_menu(self, surface):
        mx, my = self.input.mouse_pos
        clicked = self.input.mouse_clicked

        # Header Title - RETRO PULSE with playful subtitle
        title_pulse = math.sin(self.ui_anim_time * 2.0) * 3.0
        draw_radial_glow(surface, (self.width // 2, 100), 100, COLOR_ACCENT_CYAN, max_alpha=40)
        draw_text(surface, "RETRO PULSE", self.width // 2, 80 + int(title_pulse * 0.5), font_size=48, color=COLOR_ACCENT_CYAN, bold=True, shadow=False)
        draw_text(surface, "A Bright Arcade Adventure", self.width // 2, 130, font_size=20, color=COLOR_ACCENT_YELLOW, bold=False)

        if self.menu_tab == "main":
            # Main PLAY button - large and prominent
            play_button_rect = pygame.Rect(self.width // 2 - 180, self.height // 2 + 50, 360, 80)
            hovered = play_button_rect.collidepoint(mx, my)

            # Button hover animation - slight scale and color shift
            scale_factor = 1.05 if hovered else 1.0
            button_width = int(360 * scale_factor)
            button_height = int(80 * scale_factor)
            button_x = self.width // 2 - button_width // 2
            button_y = self.height // 2 + 50 - (button_height - 80) // 2

            # Button background with subtle shadow effect
            shadow_rect = pygame.Rect(button_x + 3, button_y + 3, button_width, button_height)
            draw_rounded_rect(surface, (200, 220, 240, 100), shadow_rect, radius=15)  # Semi-transparent shadow

            # Main button
            button_color = COLOR_ACCENT_YELLOW if hovered else COLOR_ACCENT_CYAN
            draw_rounded_rect(surface, COLOR_WHITE, pygame.Rect(button_x, button_y, button_width, button_height), radius=15)
            draw_rounded_rect(surface, button_color, pygame.Rect(button_x, button_y, button_width, button_height), radius=15, border_width=3, border_color=button_color)

            # Button text with pulse animation
            text_pulse = math.sin(self.ui_anim_time * 4.0) * 2.0 if hovered else 0
            draw_text(surface, "PLAY", button_x + button_width // 2, button_y + button_height // 2 + int(text_pulse), font_size=32, color=COLOR_BG, bold=True)

            # Particle feedback for button hover
            if hovered and clicked and self.ui_anim_time % 0.5 < 0.1:  # Emit particles occasionally when hovering
                for _ in range(3):
                    particle_x = button_x + random.randint(20, button_width - 20)
                    particle_y = button_y + random.randint(10, button_height - 10)
                    self.particles.emit_burst(particle_x, particle_y, count=2, colors=[COLOR_ACCENT_YELLOW, COLOR_WHITE], speed_range=(10, 30), size_range=(2, 4), life_range=(0.3, 0.6))

            # Handle play button click
            if hovered and clicked:
                self.audio.play("click")
                self.set_state("reaction")  # Directly launch FLASH! game

            # Secondary buttons below
            secondary_buttons = [
                ("MINI GAMES", self.height // 2 + 150, lambda: setattr(self, "menu_tab", "games")),
                ("HIGH SCORES", self.height // 2 + 210, lambda: setattr(self, "menu_tab", "scores")),
                ("SETTINGS", self.height // 2 + 270, lambda: setattr(self, "menu_tab", "settings")),
                ("QUIT", self.height // 2 + 330, lambda: setattr(self, "running", False))
            ]

            for label, y, action in secondary_buttons:
                rect = pygame.Rect(self.width // 2 - 120, y, 240, 50)
                hovered = rect.collidepoint(mx, my)
                clicked = self.input.mouse_clicked
                bg_color = COLOR_WHITE if hovered else COLOR_BG_SURFACE
                border_color = COLOR_ACCENT_YELLOW if hovered else COLOR_ACCENT_CYAN
                text_color = COLOR_BG if hovered else COLOR_DARK_GRAY

                # Subtle hover lift effect
                lift = -3 if hovered else 0
                draw_rounded_rect(surface, bg_color, pygame.Rect(rect.x, rect.y + lift, rect.width, rect.height), radius=12, border_width=2, border_color=border_color)
                draw_text(surface, label, rect.centerx, rect.centery + lift, font_size=20, color=text_color, bold=True)

                # Handle secondary button clicks
                if hovered and clicked:
                    self.audio.play("click")
                    action()

        elif self.menu_tab == "games":
            # Game selection screen with three large cards
            games = [
                ("FLASH!", "Reaction", "Click spawning targets\nbefore they vanish!", COLOR_ACCENT_CYAN, self.width // 2 - 260, 180),
                ("DON'T GET HIT", "Survival", "Maneuver past raining\nhazards and survive!", COLOR_ACCENT_PINK, self.width // 2, 180),
                ("SPOT IT!", "Observation", "Spot what subtle\ndetail morphed!", COLOR_ACCENT_YELLOW, self.width // 2 + 260, 180),
            ]
            clicked = self.input.mouse_clicked  # Define clicked variable

            for title, category, desc, color, x, y in games:
                card_rect = pygame.Rect(x, y, 220, 280)  # Slightly larger cards
                hovered = card_rect.collidepoint(mx, my)

                # Card hover animation - slight lift and scale
                lift = -8 if hovered else 0
                scale_factor = 1.03 if hovered else 1.0
                card_width = int(220 * scale_factor)
                card_height = int(280 * scale_factor)
                card_x = x - (card_width - 220) // 2
                card_y = y + lift - (card_height - 280) // 2

                # Card shadow
                shadow_rect = pygame.Rect(card_x + 2, card_y + 2, card_width, card_height)
                draw_rounded_rect(surface, (200, 220, 240, 80), shadow_rect, radius=18)

                # Card background
                bg_color = COLOR_WHITE if hovered else COLOR_BG_SURFACE
                draw_rounded_rect(surface, bg_color, pygame.Rect(card_x, card_y, card_width, card_height), radius=18)

                # Card border with color
                draw_rounded_rect(surface, color, pygame.Rect(card_x, card_y, card_width, card_height), radius=18, border_width=3 if hovered else 2, border_color=color)

                # Animated icon preview based on game type
                icon_x = card_x + card_width // 2
                icon_y = card_y + 60

                if title == "FLASH!":
                    # Animated target with pulse
                    pulse = math.sin(self.ui_anim_time * 3.0) * 0.3 + 0.7
                    base_size = 20
                    size = int(base_size * pulse)
                    # Target rings
                    pygame.draw.circle(surface, COLOR_WHITE, (icon_x, icon_y), size + 8)
                    pygame.draw.circle(surface, color, (icon_x, icon_y), size + 4)
                    pygame.draw.circle(surface, COLOR_WHITE, (icon_x, icon_y), size)
                    # Center spark
                    spark_size = int(3 + math.sin(self.ui_anim_time * 5.0) * 2)
                    pygame.draw.circle(surface, COLOR_ACCENT_YELLOW, (icon_x, icon_y), spark_size)

                elif title == "DON'T GET HIT":
                    # Player shape with moving obstacles
                    player_size = 18
                    pygame.draw.circle(surface, COLOR_ACCENT_CYAN, (icon_x, icon_y), player_size)
                    pygame.draw.circle(surface, COLOR_WHITE, (icon_x, icon_y), player_size // 2)
                    # Moving obstacle indicators
                    obstacle_offset = math.sin(self.ui_anim_time * 2.0) * 15
                    for i in range(3):
                        angle = self.ui_anim_time * 0.5 + i * 2.09  # Spread them out
                        ox = icon_x + math.cos(angle) * (obstacle_offset + 25)
                        oy = icon_y + math.sin(angle) * (obstacle_offset + 25)
                        pygame.draw.circle(surface, COLOR_ACCENT_PINK, (int(ox), int(oy)), 6)

                elif title == "SPOT IT!":
                    # Shapes with one different
                    shape_size = 14
                    colors = [COLOR_ACCENT_CYAN, COLOR_ACCENT_PINK, COLOR_ACCENT_YELLOW, COLOR_ACCENT_GREEN, COLOR_ACCENT_PURPLE]
                    # Draw 4 shapes in a 2x2 grid
                    positions = [
                        (icon_x - 18, icon_y - 18),
                        (icon_x + 18, icon_y - 18),
                        (icon_x - 18, icon_y + 18),
                        (icon_x + 18, icon_y + 18)
                    ]
                    # Make one shape pulse/pulsate differently
                    pulse_shape = int(self.ui_anim_time * 2) % 4
                    for i, pos in enumerate(positions):
                        shape_color = colors[i % len(colors)]
                        if i == pulse_shape:
                            # Pulse this shape
                            pulse = math.sin(self.ui_anim_time * 4.0) * 0.3 + 0.7
                            draw_size = int(shape_size * pulse)
                        else:
                            draw_size = shape_size

                        # Alternate between circle and rect
                        if i % 2 == 0:
                            pygame.draw.circle(surface, shape_color, pos, draw_size)
                        else:
                            rect = pygame.Rect(pos[0] - draw_size, pos[1] - draw_size, draw_size * 2, draw_size * 2)
                            draw_rounded_rect(surface, shape_color, rect, radius=5)

                # Game title
                draw_text(surface, title, icon_x, icon_y + 50, font_size=24, color=COLOR_DARK_GRAY, bold=True)

                # Category badge
                badge_width = 80
                badge_height = 22
                badge_x = icon_x - badge_width // 2
                badge_y = icon_y + 80
                draw_rounded_rect(surface, COLOR_BG_CARD, pygame.Rect(badge_x, badge_y, badge_width, badge_height), radius=8)
                draw_rounded_rect(surface, color, pygame.Rect(badge_x, badge_y, badge_width, badge_height), radius=8, border_width=1, border_color=color)
                draw_text(surface, category, badge_x + badge_width // 2, badge_y + badge_height // 2, font_size=14, color=COLOR_WHITE, bold=True)

                # Description
                lines = desc.split("\n")
                for i, line in enumerate(lines):
                    draw_text(surface, line, icon_x, icon_y + 120 + i * 18, font_size=14, color=COLOR_GRAY)

                # Best score display
                game_key = title.lower().replace("!", "").replace(" ", "_")
                best_score = self.scores.get(game_key, {}).get("high_score", 0)
                score_bg = pygame.Rect(icon_x - 40, icon_y + 180, 80, 25)
                draw_rounded_rect(surface, COLOR_BG_CARD, score_bg, radius=8)
                draw_rounded_rect(surface, color, score_bg, radius=8, border_width=1, border_color=color)
                draw_text(surface, f"BEST: {best_score}", icon_x, icon_y + 192, font_size=16, color=COLOR_DARK_GRAY, bold=True)

                # Play button on card
                play_btn_rect = pygame.Rect(icon_x - 50, icon_y + 220, 100, 30)
                btn_hovered = play_btn_rect.collidepoint(mx, my)
                btn_color = color if btn_hovered else COLOR_BG_CARD
                text_btn_color = COLOR_WHITE if btn_hovered else color
                draw_rounded_rect(surface, btn_color, play_btn_rect, radius=8)
                draw_text(surface, "PLAY", play_btn_rect.centerx, play_btn_rect.centery, font_size=16, color=text_btn_color, bold=True)

                # Handle card click
                if card_rect.collidepoint(mx, my) and clicked:
                    self.audio.play("click")
                    if title == "FLASH!":
                        self.set_state("reaction")
                    elif title == "DON'T GET HIT":
                        self.set_state("dodge")
                    elif title == "SPOT IT!":
                        self.set_state("observation")

            # Back button
            back_btn = pygame.Rect(self.width // 2 - 80, 480, 160, 44)
            hovered = back_btn.collidepoint(mx, my)
            bg_color = COLOR_WHITE if hovered else COLOR_BG_SURFACE
            border_color = COLOR_ACCENT_CYAN if hovered else COLOR_GRAY
            text_color = COLOR_BG if hovered else COLOR_DARK_GRAY
            draw_rounded_rect(surface, bg_color, back_btn, radius=12, border_width=2, border_color=border_color)
            draw_text(surface, "BACK", back_btn.centerx, back_btn.centery, font_size=18, color=text_color, bold=True)

        elif self.menu_tab == "scores":
            # High scores screen
            board_rect = pygame.Rect(self.width // 2 - 300, 160, 600, 300)
            draw_rounded_rect(surface, COLOR_BG_SURFACE, board_rect, radius=18, border_width=2, border_color=COLOR_ACCENT_CYAN)

            # Header
            draw_text(surface, "HIGH SCORES", board_rect.centerx, board_rect.top + 25, font_size=28, color=COLOR_ACCENT_CYAN, bold=True)

            # Column headers
            draw_text(surface, "GAME", board_rect.left + 80, board_rect.top + 60, font_size=18, color=COLOR_DARK_GRAY, bold=True)
            draw_text(surface, "BEST SCORE", board_rect.centerx, board_rect.top + 60, font_size=18, color=COLOR_DARK_GRAY, bold=True)
            draw_text(surface, "RECORD COMBO/TIME", board_rect.right - 80, board_rect.top + 60, font_size=18, color=COLOR_DARK_GRAY, bold=True, align="right")

            # Score entries
            games_data = [
                ("FLASH!", "reaction", COLOR_ACCENT_CYAN),
                ("DON'T GET HIT", "dodge", COLOR_ACCENT_PINK),
                ("SPOT IT!", "observation", COLOR_ACCENT_YELLOW)
            ]

            for i, (display_name, key, color) in enumerate(games_data):
                y_pos = board_rect.top + 100 + i * 50
                score_data = self.scores.get(key, {"high_score": 0, "best_combo": 0, "last_played": "Never"})

                # Game name
                draw_text(surface, display_name, board_rect.left + 80, y_pos, font_size=20, color=color, bold=True)

                # Best score
                draw_text(surface, str(score_data.get("high_score", 0)), board_rect.centerx, y_pos, font_size=22, color=COLOR_WHITE, bold=True)

                # Combo/time
                if key == "dodge":
                    combo_text = f"{score_data.get('best_combo', 0):.1f}s"
                else:
                    combo_text = f"x{score_data.get('best_combo', 0)}"
                draw_text(surface, combo_text, board_rect.right - 80, y_pos, font_size=22, color=COLOR_WHITE, bold=True, align="right")

                # Subtle separator line
                if i < len(games_data) - 1:
                    pygame.draw.line(surface, (*COLOR_GRAY, 50),
                                   (board_rect.left + 40, y_pos + 25),
                                   (board_rect.right - 40, y_pos + 25), 1)

            # Back button
            back_btn = pygame.Rect(self.width // 2 - 80, 480, 160, 44)
            hovered = back_btn.collidepoint(mx, my)
            bg_color = COLOR_WHITE if hovered else COLOR_BG_SURFACE
            border_color = COLOR_ACCENT_CYAN if hovered else COLOR_GRAY
            text_color = COLOR_BG if hovered else COLOR_DARK_GRAY
            draw_rounded_rect(surface, bg_color, back_btn, radius=12, border_width=2, border_color=border_color)
            draw_text(surface, "BACK", back_btn.centerx, back_btn.centery, font_size=18, color=text_color, bold=True)

        elif self.menu_tab == "settings":
            # Settings screen
            card = pygame.Rect(self.width // 2 - 220, 150, 440, 300)
            draw_rounded_rect(surface, COLOR_BG_SURFACE, card, radius=18, border_width=2, border_color=COLOR_ACCENT_CYAN)

            # Header
            draw_text(surface, "SETTINGS", card.centerx, card.top + 25, font_size=24, color=COLOR_ACCENT_CYAN, bold=True)

            # Settings items with larger touch targets
            items = [
                ("Sound Effects", 90, self.settings.get("sound_on", True), "Toggle game sound effects"),
                ("Music Audio", 140, self.settings.get("music_on", True), "Toggle background music"),
                ("Fullscreen Display", 190, self.fullscreen, "Toggle fullscreen mode")
            ]
            clicked = self.input.mouse_clicked  # Define clicked variable

            for label, y, val, description in items:
                # Label
                draw_text(surface, label, card.left + 40, y, font_size=20, color=COLOR_DARK_GRAY, align="left", bold=True)

                # Description (smaller text)
                draw_text(surface, description, card.left + 40, y + 20, font_size=14, color=COLOR_GRAY, align="left")

                # Toggle button
                btn_width = 80
                btn_height = 36
                btn_x = card.right - btn_width - 40
                btn_y = y - 10
                btn_rect = pygame.Rect(btn_x, btn_y, btn_width, btn_height)
                btn_hovered = btn_rect.collidepoint(mx, my)

                bg_color = COLOR_ACCENT_GREEN if val else COLOR_BG_CARD
                if btn_hovered:
                    # Lighter shade when hovered
                    bg_color = tuple(min(255, c + 20) for c in bg_color)

                draw_rounded_rect(surface, bg_color, btn_rect, radius=10)
                draw_text(surface, "ON" if val else "OFF", btn_rect.centerx, btn_rect.centery, font_size=16, color=COLOR_WHITE if val else COLOR_BG, bold=True)

                # Handle click
                if clicked and btn_hovered:
                    self.audio.play("click")
                    if label == "Sound Effects":
                        self.settings["sound_on"] = not self.settings["sound_on"]
                        self.audio.set_sound_enabled(self.settings["sound_on"])
                        save_settings(self.settings)
                    elif label == "Music Audio":
                        self.settings["music_on"] = not self.settings["music_on"]
                        self.audio.set_music_enabled(self.settings["music_on"])
                        save_settings(self.settings)
                    elif label == "Fullscreen Display":
                        self.audio.play("click")
                        self.toggle_fullscreen()

            # Back button
            back_btn = pygame.Rect(self.width // 2 - 80, 480, 160, 44)
            hovered = back_btn.collidepoint(mx, my)
            bg_color = COLOR_WHITE if hovered else COLOR_BG_SURFACE
            border_color = COLOR_ACCENT_CYAN if hovered else COLOR_GRAY
            text_color = COLOR_BG if hovered else COLOR_DARK_GRAY
            draw_rounded_rect(surface, bg_color, back_btn, radius=12, border_width=2, border_color=border_color)
            draw_text(surface, "BACK", back_btn.centerx, back_btn.centery, font_size=18, color=text_color, bold=True)
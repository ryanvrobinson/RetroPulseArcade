"""
RETROPULSE ARCADE — FINAL 10-GAME MASTER CONTROLLER
10 Games: FLASH!, DON'T GET HIT!, SPOT IT!, ARCHERY, TRAFFIC RIDER,
          MEMORY PUZZLE, BLOCK DROP, SKY DASH, FIND THE SECRET, COLOR CHAOS
"""

import math
import pygame
from constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT, FPS, ALL_GAME_KEYS, GAME_TITLES,
    C_SLATE_DARK, C_CORAL, C_YELLOW, C_CREAM, C_WHITE, C_GOLD, C_MINT,
    C_BLUE_CARD, C_ROAD, C_ROAD_LINE, C_PURPLE, C_BROWN, C_DANGER, C_LIGHT_GRAY, C_SUN,
    FONT_HUGE, FONT_TITLE, FONT_CARD, FONT_BODY, draw_pixel_box
)
from audio import play_sound
from effects import particles, score_popups
from mascot import draw_pulse_character
from environment import env_engine
from tournament import tournament_manager, settings_manager

# Exact 10 Games exported from games package
from games import (
    GameFlash, GameDodge, GameSpotIt, GameArchery, GameTrafficRider,
    GameMemoryPuzzle, GameBlockDrop, GameSkyDash, GameFindSecret, GameColorChaos, GameNeonRush
)

class RetroPulseApp:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("RetroPulse Arcade — 10-Game Tournament")
        # Flush initial window manager events to prevent false immediate quits
        pygame.event.clear()
        self.clock = pygame.time.Clock()
        self.canvas = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.state = "MENU"
        self.game = None
        self.anim_time = 0.0
        self.active_page = 0
        self.name_buffer = tournament_manager.player_name
        self.leaderboard_tab = "OVERALL"

    def start_game(self, game_key):
        mapping = {
            "flash": GameFlash, "dodge": GameDodge, "spot_it": GameSpotIt,
            "archery": GameArchery, "traffic": GameTrafficRider, "memory": GameMemoryPuzzle,
            "block_drop": GameBlockDrop, "sky_dash": GameSkyDash,
            "find_secret": GameFindSecret, "color_chaos": GameColorChaos, "neon_rush": GameNeonRush
        }
        if game_key in mapping:
            self.game = mapping[game_key]()
            self.state = game_key.upper()
            play_sound("pop")

    def run(self):
        running = True
        try:
            while running:
                dt = min(self.clock.tick(FPS) / 1000.0, 0.1)
                self.anim_time += dt
                env_engine.update(dt)

                for p in particles: p.update(dt)
                particles[:] = [p for p in particles if p.life > 0]
                for pop in score_popups: pop.update(dt)
                score_popups[:] = [pop for pop in score_popups if pop.life > 0]

                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                    elif event.type == pygame.KEYDOWN:
                        if self.state == "TOURNAMENT_ENTRY":
                            if event.key == pygame.K_RETURN:
                                if self.name_buffer.strip():
                                    tournament_manager.player_name = self.name_buffer.strip()
                                    tournament_manager.save()
                                    self.state = "GAME_SELECT"
                            elif event.key == pygame.K_BACKSPACE:
                                self.name_buffer = self.name_buffer[:-1]
                            elif len(self.name_buffer) < 12 and event.unicode.isprintable():
                                self.name_buffer += event.unicode
                        elif event.key == pygame.K_ESCAPE:
                            if self.state in [k.upper() for k in ALL_GAME_KEYS]:
                                self.state = "GAME_SELECT"
                            elif self.state in ("GAME_SELECT", "LEADERBOARD", "SETTINGS", "TOURNAMENT_ENTRY"):
                                self.state = "MENU"
                        # Keyboard restart on Game Over
                        elif self.game and getattr(self.game, "game_over", False):
                            if event.key in (pygame.K_SPACE, pygame.K_UP, pygame.K_RETURN):
                                self.start_game(self.state.lower())
                        # Active game keyboard inputs
                        elif event.key == pygame.K_SPACE or event.key == pygame.K_UP:
                            if self.state == "BLOCK_DROP" and self.game:
                                self.game.drop_block()
                            elif self.state == "SKY_DASH" and self.game:
                                self.game.jump()
                        # Catalog pagination via arrow keys
                        elif self.state == "GAME_SELECT" and event.key in (pygame.K_LEFT, pygame.K_RIGHT):
                            self.active_page = 1 if self.active_page == 0 else 0
                            play_sound("pop")
                    elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        self.handle_click(event.pos)

                # Continuous keyboard polling
                keys = pygame.key.get_pressed()
                if self.state in ["DODGE", "TRAFFIC", "SKY_DASH", "NEON_RUSH"] and self.game:
                    self.game.update(dt, keys)
                elif self.game and self.state in [k.upper() for k in ALL_GAME_KEYS]:
                    self.game.update(dt)

                self.draw(self.canvas)

                for p in particles: p.draw(self.canvas)
                for pop in score_popups: pop.draw(self.canvas)

                self.screen.blit(self.canvas, (0, 0))
                pygame.display.flip()
        except KeyboardInterrupt:
            pass
        finally:
            pygame.quit()

    def handle_click(self, pos):
        mx, my = pos
        if self.state == "MENU":
            play_btn = pygame.Rect(SCREEN_WIDTH // 2 - 130, 300, 260, 56)
            tourney_btn = pygame.Rect(SCREEN_WIDTH // 2 - 130, 368, 260, 48)
            board_btn = pygame.Rect(SCREEN_WIDTH // 2 - 130, 426, 260, 48)
            settings_btn = pygame.Rect(SCREEN_WIDTH // 2 - 130, 484, 260, 48)
            quit_btn = pygame.Rect(SCREEN_WIDTH // 2 - 130, 542, 260, 44)

            if play_btn.collidepoint(pos):
                play_sound("jump"); self.state = "GAME_SELECT"
            elif tourney_btn.collidepoint(pos):
                play_sound("pop"); self.state = "TOURNAMENT_ENTRY"
            elif board_btn.collidepoint(pos):
                play_sound("pop"); self.state = "LEADERBOARD"
            elif settings_btn.collidepoint(pos):
                play_sound("pop"); self.state = "SETTINGS"
            elif quit_btn.collidepoint(pos):
                pygame.event.post(pygame.event.Event(pygame.QUIT))

        elif self.state == "TOURNAMENT_ENTRY":
            join_btn = pygame.Rect(SCREEN_WIDTH // 2 - 100, 380, 200, 50)
            if join_btn.collidepoint(pos):
                if self.name_buffer.strip():
                    tournament_manager.player_name = self.name_buffer.strip()
                    tournament_manager.save()
                    play_sound("celebrate")
                    self.state = "GAME_SELECT"

        elif self.state == "GAME_SELECT":
            # 10 Games: Page 0 has 6 games, Page 1 has 4 games
            page_keys = ALL_GAME_KEYS[:6] if self.active_page == 0 else ALL_GAME_KEYS[6:]
            for i, key in enumerate(page_keys):
                col, row = i % 3, i // 3
                cx = 55 + col * 295
                cy = 88 + row * 240
                if pygame.Rect(cx, cy, 260, 220).collidepoint(pos):
                    self.start_game(key)
                    return

            btn_prev = pygame.Rect(SCREEN_WIDTH // 2 - 160, 585, 140, 38)
            btn_next = pygame.Rect(SCREEN_WIDTH // 2 + 20, 585, 140, 38)
            back_btn = pygame.Rect(30, 25, 100, 40)
            if btn_prev.collidepoint(pos) or btn_next.collidepoint(pos):
                self.active_page = 1 if self.active_page == 0 else 0
                play_sound("pop")
            elif back_btn.collidepoint(pos):
                play_sound("pop"); self.state = "MENU"

        elif self.state == "LEADERBOARD":
            back_btn = pygame.Rect(SCREEN_WIDTH // 2 - 70, 545, 140, 46)
            tab_o = pygame.Rect(SCREEN_WIDTH // 2 - 160, 134, 150, 32)
            tab_g = pygame.Rect(SCREEN_WIDTH // 2 + 10, 134, 150, 32)
            if back_btn.collidepoint(pos):
                play_sound("pop"); self.state = "MENU"
            elif tab_o.collidepoint(pos):
                self.leaderboard_tab = "OVERALL"; play_sound("pop")
            elif tab_g.collidepoint(pos):
                self.leaderboard_tab = "flash"; play_sound("pop")

        elif self.state == "SETTINGS":
            back_btn = pygame.Rect(SCREEN_WIDTH // 2 - 70, 520, 140, 46)
            t_snd = pygame.Rect(SCREEN_WIDTH // 2 + 40, 240, 80, 36)
            t_shk = pygame.Rect(SCREEN_WIDTH // 2 + 40, 310, 80, 36)
            if back_btn.collidepoint(pos):
                play_sound("pop"); self.state = "MENU"
            elif t_snd.collidepoint(pos):
                settings_manager.toggle("sound"); play_sound("pop")
            elif t_shk.collidepoint(pos):
                settings_manager.toggle("shake"); play_sound("pop")

        elif self.game and self.state in [k.upper() for k in ALL_GAME_KEYS]:
            if self.game.game_over:
                btn_again = pygame.Rect(SCREEN_WIDTH // 2 - 120, 380, 240, 46)
                btn_menu = pygame.Rect(SCREEN_WIDTH // 2 - 120, 438, 240, 44)
                if btn_again.collidepoint(pos):
                    self.start_game(self.state.lower())
                elif btn_menu.collidepoint(pos):
                    play_sound("pop"); self.state = "GAME_SELECT"
            else:
                if hasattr(self.game, "handle_click"):
                    self.game.handle_click(mx, my)

    def draw(self, surf):
        if self.state == "MENU": self.draw_menu(surf)
        elif self.state == "TOURNAMENT_ENTRY": self.draw_tournament_entry(surf)
        elif self.state == "GAME_SELECT": self.draw_game_select(surf)
        elif self.state == "LEADERBOARD": self.draw_leaderboard(surf)
        elif self.state == "SETTINGS": self.draw_settings(surf)
        elif self.game and self.state in [k.upper() for k in ALL_GAME_KEYS]:
            self.game.draw(surf)
            if self.game.game_over and getattr(self.game, "result_data", None):
                self.draw_result_modal(surf, self.game.result_data)

    def draw_menu(self, surf):
        env_engine.draw_base_countryside(surf)
        t_sh = FONT_HUGE.render("RETRO PULSE", True, C_SLATE_DARK)
        t_mn = FONT_HUGE.render("RETRO PULSE", True, C_CORAL)
        surf.blit(t_sh, (SCREEN_WIDTH // 2 - t_mn.get_width() // 2 + 3, 103))
        surf.blit(t_mn, (SCREEN_WIDTH // 2 - t_mn.get_width() // 2, 100))
        sub = FONT_CARD.render("10-Game Pixel Arcade Tournament", True, C_SLATE_DARK)
        surf.blit(sub, (SCREEN_WIDTH // 2 - sub.get_width() // 2, 168))

        draw_pulse_character(surf, SCREEN_WIDTH // 2 - 210, 360, scale=1.6, state="HAPPY", anim_time=self.anim_time)
        m_pos = pygame.mouse.get_pos()

        p_btn = pygame.Rect(SCREEN_WIDTH // 2 - 130, 300, 260, 56)
        draw_pixel_box(surf, p_btn, C_YELLOW if not p_btn.collidepoint(m_pos) else C_SUN, border_color=C_SLATE_DARK, elevation=5)
        pt = FONT_CARD.render("PLAY ARCADE!", True, C_SLATE_DARK)
        surf.blit(pt, (p_btn.centerx - pt.get_width() // 2, p_btn.centery - pt.get_height() // 2))

        for label, y in [("TOURNAMENT ENTRY", 368), ("LEADERBOARDS", 426), ("SETTINGS", 484), ("QUIT", 542)]:
            b = pygame.Rect(SCREEN_WIDTH // 2 - 130, y, 260, 48 if y != 542 else 44)
            draw_pixel_box(surf, b, C_CREAM if not b.collidepoint(m_pos) else C_WHITE, border_color=C_SLATE_DARK, elevation=3)
            bt = FONT_BODY.render(label, True, C_SLATE_DARK)
            surf.blit(bt, (b.centerx - bt.get_width() // 2, b.centery - bt.get_height() // 2))

    def draw_tournament_entry(self, surf):
        env_engine.draw_base_countryside(surf)
        box = pygame.Rect(SCREEN_WIDTH // 2 - 220, 150, 440, 320)
        draw_pixel_box(surf, box, C_WHITE, border_color=C_GOLD, elevation=6)

        title = FONT_TITLE.render("PLAYER ENTRY", True, C_CORAL)
        surf.blit(title, (box.centerx - title.get_width() // 2, box.y + 26))

        sub = FONT_BODY.render("Enter your arcade nickname:", True, C_SLATE_DARK)
        surf.blit(sub, (box.centerx - sub.get_width() // 2, box.y + 88))

        input_box = pygame.Rect(box.centerx - 140, box.y + 124, 280, 50)
        draw_pixel_box(surf, input_box, C_CREAM, border_color=C_SLATE_DARK, elevation=2)
        ntxt = FONT_CARD.render(self.name_buffer + ("_" if int(self.anim_time * 2) % 2 == 0 else ""), True, C_SLATE_DARK)
        surf.blit(ntxt, (input_box.centerx - ntxt.get_width() // 2, input_box.centery - ntxt.get_height() // 2))

        join_btn = pygame.Rect(box.centerx - 100, box.y + 210, 200, 50)
        draw_pixel_box(surf, join_btn, C_MINT, border_color=C_SLATE_DARK, elevation=4)
        jtxt = FONT_CARD.render("ENTER & PLAY", True, C_SLATE_DARK)
        surf.blit(jtxt, (join_btn.centerx - jtxt.get_width() // 2, join_btn.centery - jtxt.get_height() // 2))

    def draw_game_select(self, surf):
        env_engine.draw_base_countryside(surf)
        title = FONT_TITLE.render("TOURNAMENT CATALOG", True, C_SLATE_DARK)
        surf.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 28))

        back_btn = pygame.Rect(30, 25, 100, 40)
        draw_pixel_box(surf, back_btn, C_CREAM, border_color=C_SLATE_DARK, elevation=3)
        btxt = FONT_BODY.render("< BACK", True, C_SLATE_DARK)
        surf.blit(btxt, (back_btn.centerx - btxt.get_width() // 2, back_btn.centery - btxt.get_height() // 2))

        page_keys = ALL_GAME_KEYS[:6] if self.active_page == 0 else ALL_GAME_KEYS[6:]
        m_pos = pygame.mouse.get_pos()

        for i, key in enumerate(page_keys):
            col, row = i % 3, i // 3
            cx = 55 + col * 295
            cy = 88 + row * 240
            rect = pygame.Rect(cx, cy, 260, 220)
            lift = 4 if rect.collidepoint(m_pos) else 0
            draw_rect = pygame.Rect(rect.x, rect.y - lift, rect.width, rect.height)
            draw_pixel_box(surf, draw_rect, C_WHITE, border_color=C_SLATE_DARK, elevation=4)

            prev_rect = pygame.Rect(draw_rect.x + 14, draw_rect.y + 12, draw_rect.width - 28, 80)
            pygame.draw.rect(surf, C_CREAM, prev_rect, border_radius=8)

            # Previews for the 10 games
            if key == "flash":
                pr = 16 + math.sin(self.anim_time * 6) * 3
                pygame.draw.circle(surf, C_CORAL, (prev_rect.centerx, prev_rect.centery), int(pr))
                pygame.draw.circle(surf, C_YELLOW, (prev_rect.centerx, prev_rect.centery), int(pr * 0.5))
            elif key == "dodge":
                draw_pulse_character(surf, prev_rect.centerx - 18, prev_rect.centery + 10, scale=0.6, state="RUN", anim_time=self.anim_time)
                pygame.draw.circle(surf, C_CORAL, (prev_rect.centerx + 28, prev_rect.centery), 8)
            elif key == "spot_it":
                pygame.draw.circle(surf, C_PURPLE, (prev_rect.centerx - 16, prev_rect.centery), 12)
                pygame.draw.circle(surf, C_YELLOW, (prev_rect.centerx + 16, prev_rect.centery), 12)
            elif key == "archery":
                pygame.draw.circle(surf, C_WHITE, (prev_rect.centerx + 20, prev_rect.centery), 16)
                pygame.draw.circle(surf, C_CORAL, (prev_rect.centerx + 20, prev_rect.centery), 8)
                pygame.draw.line(surf, C_BROWN, (prev_rect.centerx - 24, prev_rect.centery), (prev_rect.centerx + 12, prev_rect.centery), 3)
            elif key == "traffic":
                pygame.draw.rect(surf, C_ROAD, (prev_rect.centerx - 28, prev_rect.y + 4, 56, prev_rect.height - 8), border_radius=4)
                pygame.draw.rect(surf, C_YELLOW, (prev_rect.centerx - 8, prev_rect.centery - 8, 16, 20), border_radius=3)
            elif key == "memory":
                pygame.draw.rect(surf, C_BLUE_CARD, (prev_rect.centerx - 22, prev_rect.centery - 14, 18, 28), border_radius=3)
                pygame.draw.rect(surf, C_WHITE, (prev_rect.centerx + 4, prev_rect.centery - 14, 18, 28), border_radius=3)
            elif key == "block_drop":
                pygame.draw.rect(surf, C_MINT, (prev_rect.centerx - 25, prev_rect.centery + 6, 50, 12), border_radius=3)
                pygame.draw.rect(surf, C_YELLOW, (prev_rect.centerx - 18, prev_rect.centery - 8, 36, 12), border_radius=3)
            elif key == "sky_dash":
                pygame.draw.rect(surf, C_MINT, (prev_rect.centerx - 35, prev_rect.centery + 12, 70, 8), border_radius=3)
                draw_pulse_character(surf, prev_rect.centerx, prev_rect.centery + 2, scale=0.55, state="JUMP", anim_time=self.anim_time)
            elif key == "find_secret":
                for ox in [-24, 0, 24]: pygame.draw.circle(surf, C_CORAL if ox != 0 else C_GOLD, (prev_rect.centerx + ox, prev_rect.centery), 8)
            elif key == "color_chaos":
                pygame.draw.circle(surf, C_BLUE_CARD, (prev_rect.centerx - 20, prev_rect.centery), 12)
                pygame.draw.circle(surf, C_DANGER, (prev_rect.centerx + 20, prev_rect.centery), 12)
            elif key == "neon_rush":
                # Draw a simple neon road with three lanes
                road_width = 180
                road_height = 60
                road_x = prev_rect.centerx - road_width // 2
                road_y = prev_rect.centery - road_height // 2
                # Road base
                pygame.draw.rect(surf, C_ROAD, (road_x, road_y, road_width, road_height), border_radius=4)
                # Lane markers
                for i in range(1, 3):
                    lane_x = road_x + i * road_width // 3
                    pygame.draw.line(surf, C_ROAD_LINE, (lane_x, road_y), (lane_x, road_y + road_height), 2)
                # Draw Pulse character in middle lane (lane 1)
                draw_pulse_character(surf, prev_rect.centerx, prev_rect.centery + 10, scale=0.5, state="RUN", anim_time=self.anim_time, facing_right=True)
                # Draw an obstacle (barrier) in left lane
                barrier_x = road_x + road_width // 6 - 10
                barrier_y = road_y + road_height - 20
                pygame.draw.rect(surf, C_CORAL, (barrier_x, barrier_y, 20, 20))
                pygame.draw.rect(surf, C_WHITE, (barrier_x, barrier_y, 20, 20), 2)
                # Draw an energy orb in right lane
                orb_x = road_x + road_width * 5 // 6 - 10
                orb_y = road_y + 20
                pygame.draw.circle(surf, C_YELLOW, (orb_x, orb_y), 12)
                pygame.draw.circle(surf, C_WHITE, (orb_x, orb_y), 12, 2)

            t_txt = FONT_CARD.render(GAME_TITLES[key], True, C_SLATE_DARK)
            surf.blit(t_txt, (draw_rect.centerx - t_txt.get_width() // 2, draw_rect.y + 104))

            best = tournament_manager.get_score(key)
            b_txt = FONT_BODY.render(f"BEST: {best}", True, C_CORAL)
            surf.blit(b_txt, (draw_rect.centerx - b_txt.get_width() // 2, draw_rect.y + 140))

            p_btn = pygame.Rect(draw_rect.centerx - 45, draw_rect.y + 175, 90, 26)
            draw_pixel_box(surf, p_btn, C_MINT, border_color=C_SLATE_DARK, elevation=2)
            pt = FONT_BODY.render("PLAY", True, C_WHITE)
            surf.blit(pt, (p_btn.centerx - pt.get_width() // 2, p_btn.centery - pt.get_height() // 2))

        p_bg = pygame.Rect(SCREEN_WIDTH // 2 - 180, 580, 360, 44)
        draw_pixel_box(surf, p_bg, C_WHITE, border_color=C_SLATE_DARK, elevation=3)
        lbl = f"PAGE {self.active_page + 1} OF 2 — " + ("CLASSICS (1-6)" if self.active_page == 0 else "ACTION & PUZZLE (7-10)")
        ltxt = FONT_BODY.render(lbl, True, C_SLATE_DARK)
        surf.blit(ltxt, (p_bg.centerx - ltxt.get_width() // 2, p_bg.centery - ltxt.get_height() // 2))

    def draw_leaderboard(self, surf):
        env_engine.draw_base_countryside(surf)
        box = pygame.Rect(SCREEN_WIDTH // 2 - 270, 70, 540, 460)
        draw_pixel_box(surf, box, C_WHITE, border_color=C_GOLD, elevation=6)

        title = FONT_TITLE.render("TOURNAMENT STANDINGS", True, C_SLATE_DARK)
        surf.blit(title, (box.centerx - title.get_width() // 2, box.y + 16))

        tab_o = pygame.Rect(box.centerx - 160, box.y + 64, 150, 32)
        tab_g = pygame.Rect(box.centerx + 10, box.y + 64, 150, 32)
        draw_pixel_box(surf, tab_o, C_YELLOW if self.leaderboard_tab == "OVERALL" else C_CREAM, border_color=C_SLATE_DARK, elevation=2)
        draw_pixel_box(surf, tab_g, C_YELLOW if self.leaderboard_tab != "OVERALL" else C_CREAM, border_color=C_SLATE_DARK, elevation=2)
        otxt = FONT_BODY.render("OVERALL", True, C_SLATE_DARK)
        gtxt = FONT_BODY.render("GAME BESTS", True, C_SLATE_DARK)
        surf.blit(otxt, (tab_o.centerx - otxt.get_width() // 2, tab_o.centery - otxt.get_height() // 2))
        surf.blit(gtxt, (tab_g.centerx - gtxt.get_width() // 2, tab_g.centery - gtxt.get_height() // 2))

        standings = tournament_manager.get_overall_standings() if self.leaderboard_tab == "OVERALL" else tournament_manager.get_game_standings("flash")
        for i, row in enumerate(standings[:8]):
            ry = box.y + 115 + i * 38
            is_p = row.get("is_player", False) or row["name"] == tournament_manager.player_name
            rcol = C_SUN if is_p else (C_CREAM if i % 2 == 0 else C_WHITE)
            r_box = pygame.Rect(box.x + 30, ry, box.width - 60, 34)
            pygame.draw.rect(surf, rcol, r_box, border_radius=6)
            pygame.draw.rect(surf, C_SLATE_DARK, r_box, width=1, border_radius=6)

            rank_txt = FONT_CARD.render(f"#{i+1}", True, C_CORAL if i < 3 else C_SLATE_DARK)
            name_txt = FONT_CARD.render(row["name"], True, C_SLATE_DARK)
            val = row.get("points", row.get("score", 0))
            score_txt = FONT_CARD.render(f"{val} PTS", True, C_SLATE_DARK)

            surf.blit(rank_txt, (r_box.x + 14, r_box.y + 5))
            surf.blit(name_txt, (r_box.x + 70, r_box.y + 5))
            surf.blit(score_txt, (r_box.right - score_txt.get_width() - 14, r_box.y + 5))

        back_btn = pygame.Rect(SCREEN_WIDTH // 2 - 70, 545, 140, 46)
        draw_pixel_box(surf, back_btn, C_CREAM, border_color=C_SLATE_DARK, elevation=3)
        bt = FONT_BODY.render("< BACK", True, C_SLATE_DARK)
        surf.blit(bt, (back_btn.centerx - bt.get_width() // 2, back_btn.centery - bt.get_height() // 2))

    def draw_settings(self, surf):
        env_engine.draw_base_countryside(surf)
        box = pygame.Rect(SCREEN_WIDTH // 2 - 200, 130, 400, 350)
        draw_pixel_box(surf, box, C_WHITE, border_color=C_SLATE_DARK, elevation=5)
        title = FONT_TITLE.render("SETTINGS", True, C_SLATE_DARK)
        surf.blit(title, (box.centerx - title.get_width() // 2, box.y + 25))

        s_lbl = FONT_CARD.render("Sound FX", True, C_SLATE_DARK)
        surf.blit(s_lbl, (box.x + 50, 245))
        s_btn = pygame.Rect(SCREEN_WIDTH // 2 + 40, 240, 80, 36)
        draw_pixel_box(surf, s_btn, C_MINT if settings_manager.get("sound") else C_LIGHT_GRAY, border_color=C_SLATE_DARK, elevation=2)
        st_txt = FONT_BODY.render("ON" if settings_manager.get("sound") else "OFF", True, C_SLATE_DARK)
        surf.blit(st_txt, (s_btn.centerx - st_txt.get_width() // 2, s_btn.centery - st_txt.get_height() // 2))

        k_lbl = FONT_CARD.render("Screen Shake", True, C_SLATE_DARK)
        surf.blit(k_lbl, (box.x + 50, 315))
        k_btn = pygame.Rect(SCREEN_WIDTH // 2 + 40, 310, 80, 36)
        draw_pixel_box(surf, k_btn, C_MINT if settings_manager.get("shake") else C_LIGHT_GRAY, border_color=C_SLATE_DARK, elevation=2)
        kt_txt = FONT_BODY.render("ON" if settings_manager.get("shake") else "OFF", True, C_SLATE_DARK)
        surf.blit(kt_txt, (k_btn.centerx - kt_txt.get_width() // 2, k_btn.centery - kt_txt.get_height() // 2))

        back_btn = pygame.Rect(SCREEN_WIDTH // 2 - 70, 520, 140, 46)
        draw_pixel_box(surf, back_btn, C_CREAM, border_color=C_SLATE_DARK, elevation=3)
        bt = FONT_BODY.render("< BACK", True, C_SLATE_DARK)
        surf.blit(bt, (back_btn.centerx - bt.get_width() // 2, back_btn.centery - bt.get_height() // 2))

    def draw_result_modal(self, surf, res):
        dim = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        dim.fill((15, 23, 42, 140))
        surf.blit(dim, (0, 0))

        box = pygame.Rect(SCREEN_WIDTH // 2 - 180, 130, 360, 380)
        draw_pixel_box(surf, box, C_WHITE, border_color=C_GOLD, elevation=6)

        title = FONT_TITLE.render("GAME OVER", True, C_CORAL)
        surf.blit(title, (box.centerx - title.get_width() // 2, box.y + 24))

        stxt = FONT_CARD.render(f"Score: {res['score']}", True, C_SLATE_DARK)
        surf.blit(stxt, (box.centerx - stxt.get_width() // 2, box.y + 86))

        ptxt = FONT_CARD.render(f"+{res['added_pts']} TOURNAMENT PTS", True, C_GOLD)
        surf.blit(ptxt, (box.centerx - ptxt.get_width() // 2, box.y + 124))

        if res["rank_climbed"]:
            rtxt = FONT_CARD.render(f"RANK CLIMB: #{res['prev_rank']} -> #{res['new_rank']}!", True, C_MINT)
        else:
            rtxt = FONT_BODY.render(f"Current Tournament Rank: #{res['new_rank']}", True, C_SLATE_DARK)
        surf.blit(rtxt, (box.centerx - rtxt.get_width() // 2, box.y + 168))

        if res["is_best"]:
            btxt = FONT_BODY.render("★ NEW PERSONAL BEST! ★", True, C_CORAL)
            surf.blit(btxt, (box.centerx - btxt.get_width() // 2, box.y + 204))

        btn_again = pygame.Rect(box.centerx - 120, box.y + 250, 240, 46)
        draw_pixel_box(surf, btn_again, C_MINT, border_color=C_SLATE_DARK, elevation=3)
        atxt = FONT_CARD.render("PLAY AGAIN (SPACE)", True, C_SLATE_DARK)
        surf.blit(atxt, (btn_again.centerx - atxt.get_width() // 2, btn_again.centery - atxt.get_height() // 2))

        btn_menu = pygame.Rect(box.centerx - 120, box.y + 308, 240, 44)
        draw_pixel_box(surf, btn_menu, C_CREAM, border_color=C_SLATE_DARK, elevation=2)
        mtxt = FONT_BODY.render("GAME SELECT (ESC)", True, C_SLATE_DARK)
        surf.blit(mtxt, (btn_menu.centerx - mtxt.get_width() // 2, btn_menu.centery - mtxt.get_height() // 2))

if __name__ == "__main__":
    app = RetroPulseApp()
    app.run()
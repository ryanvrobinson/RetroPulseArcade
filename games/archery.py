import math
import pygame
from constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT, C_WHITE, C_BLUE_CARD,
    C_CORAL, C_YELLOW, C_GOLD, C_MINT, C_GREEN_DARK,
    C_SLATE_DARK, draw_hud
)
from audio import play_sound
from effects import spawn_burst, score_popups, ScorePopup
from environment import env_engine
from tournament import tournament_manager

class Arrow:
    def __init__(self, x, y, vx, vy):
        self.x, self.y = float(x), float(y)
        self.vx, self.vy = float(vx), float(vy)
        self.alive = True
        self.checked_hit = False

    def update(self, dt):
        self.x += self.vx * dt * 60
        self.y += self.vy * dt * 60
        self.vy += 0.08 * dt * 60

        if (self.x > SCREEN_WIDTH + 60 or
            self.y > SCREEN_HEIGHT + 60 or
            self.y < -60):
            self.alive = False

    def draw(self, surf):
        angle = math.atan2(self.vy, self.vx)
        length = 38
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)

        tail_x = self.x - length * cos_a
        tail_y = self.y - length * sin_a

        pygame.draw.line(surf, (146, 64, 14), (tail_x, tail_y), (self.x, self.y), 4)
        pygame.draw.line(surf, (217, 119, 6), (tail_x, tail_y), (self.x, self.y), 2)

        head_len = 10
        barb_w = 5
        base_x = self.x - head_len * cos_a
        base_y = self.y - head_len * sin_a

        p_tip = (self.x + 2 * cos_a, self.y + 2 * sin_a)
        p_left = (base_x - barb_w * sin_a, base_y + barb_w * cos_a)
        p_right = (base_x + barb_w * sin_a, base_y - barb_w * cos_a)

        pygame.draw.polygon(surf, (203, 213, 225), [p_tip, p_left, p_right])
        pygame.draw.polygon(surf, C_SLATE_DARK, [p_tip, p_left, p_right], 1)

        f_len = 9
        f_w = 4
        f_base_x = tail_x + f_len * cos_a
        f_base_y = tail_y + f_len * sin_a

        f1_tip = (tail_x - f_w * sin_a, tail_y + f_w * cos_a)
        f1_base = (f_base_x - f_w * sin_a, f_base_y + f_w * cos_a)
        f2_tip = (tail_x + f_w * sin_a, tail_y - f_w * cos_a)
        f2_base = (f_base_x + f_w * sin_a, f_base_y - f_w * cos_a)

        pygame.draw.line(surf, C_CORAL, f1_tip, f1_base, 3)
        pygame.draw.line(surf, C_WHITE, f2_tip, f2_base, 3)

class GameArchery:
    def __init__(self):
        self.score = 0
        self.combo = 0
        self.arrows_left = 10
        self.target_x = 800
        self.target_y = SCREEN_HEIGHT // 2
        self.target_vy = 2.4
        self.active_arrow = None
        self.game_over = False
        self.result_data = None
        self.bow_x = 110
        self.bow_y = SCREEN_HEIGHT // 2 + 10
        self.target_recoil = 0.0

    def update(self, dt):
        if self.game_over:
            return

        self.target_y += self.target_vy * dt * 60
        if self.target_y < 130 or self.target_y > SCREEN_HEIGHT - 130:
            self.target_vy = -self.target_vy

        if self.target_recoil > 0:
            self.target_recoil = max(0.0, self.target_recoil - dt * 25.0)

        if self.active_arrow:
            self.active_arrow.update(dt)

            if (self.target_x - 14 <= self.active_arrow.x <= self.target_x + 22) and not self.active_arrow.checked_hit:
                dy = abs(self.active_arrow.y - self.target_y)
                if dy <= 54:
                    self.active_arrow.checked_hit = True
                    hit_y = self.active_arrow.y

                    if dy <= 14:
                        pts = 300
                        popup_txt = "BULLSEYE! +300"
                        burst_color = C_GOLD
                        play_sound("celebrate")
                    elif dy <= 30:
                        pts = 150
                        popup_txt = f"+{pts}"
                        burst_color = C_CORAL
                        play_sound("coin")
                    else:
                        pts = 75
                        popup_txt = f"+{pts}"
                        burst_color = C_MINT
                        play_sound("pop")

                    self.combo += 1
                    total_pts = pts * self.combo
                    self.score += total_pts
                    self.target_recoil = 10.0

                    spawn_burst(self.target_x, hit_y, burst_color, 22, shape="star")
                    score_popups.append(ScorePopup(popup_txt, self.target_x - 50, hit_y - 20, burst_color))
                    self.active_arrow = None

            if self.active_arrow:
                if self.active_arrow.x > self.target_x + 25 and not getattr(self.active_arrow, "passed_target", False):
                    self.active_arrow.passed_target = True
                    self.combo = 0

                if not self.active_arrow.alive or self.active_arrow.x > SCREEN_WIDTH + 40 or self.active_arrow.y > SCREEN_HEIGHT + 60 or self.active_arrow.y < -60:
                    self.combo = 0
                    self.active_arrow = None

            if self.arrows_left <= 0 and self.active_arrow is None:
                self.game_over = True
                self.result_data = tournament_manager.record_game("archery", self.score)
                play_sound("celebrate")

    def handle_click(self, mx, my):
        if self.game_over or self.active_arrow or self.arrows_left <= 0:
            return

        dx = mx - self.bow_x
        dy = my - self.bow_y
        angle = math.atan2(dy, max(1.0, dx))
        angle = max(math.radians(-48), min(math.radians(48), angle))

        spd = 19.5
        vx = math.cos(angle) * spd
        vy = math.sin(angle) * spd

        launch_x = self.bow_x + math.cos(angle) * 14
        launch_y = self.bow_y + math.sin(angle) * 14

        self.active_arrow = Arrow(launch_x, launch_y, vx, vy)
        self.arrows_left -= 1
        play_sound("shoot")

    def draw_archer(self, surf, aim_angle):
        bow_x = self.bow_x
        bow_y = self.bow_y
        platform_top = bow_y + 45
        arch_x = 76

        pygame.draw.rect(surf, (146, 64, 14), (28, platform_top, 95, 12), border_radius=3)
        pygame.draw.rect(surf, (180, 83, 9), (30, platform_top + 2, 91, 4))
        pygame.draw.rect(surf, (120, 53, 15), (38, platform_top + 12, 10, 160))
        pygame.draw.rect(surf, (120, 53, 15), (105, platform_top + 12, 10, 160))
        pygame.draw.line(surf, (120, 53, 15), (38, platform_top + 20), (115, platform_top + 90), 3)
        pygame.draw.line(surf, (120, 53, 15), (38, platform_top + 90), (115, platform_top + 20), 3)

        pygame.draw.rect(surf, (146, 64, 14), (44, platform_top - 20, 15, 20), border_radius=2)
        pygame.draw.rect(surf, C_SLATE_DARK, (44, platform_top - 20, 15, 20), 1, border_radius=2)
        visible_spares = min(5, max(0, self.arrows_left - (1 if self.active_arrow else 0)))
        for i in range(visible_spares):
            qx = 46 + i * 3
            qy = platform_top - 26 - (i % 2) * 3
            pygame.draw.line(surf, (180, 83, 9), (qx, platform_top - 20), (qx, qy), 2)
            pygame.draw.line(surf, C_CORAL if i % 2 == 0 else C_WHITE, (qx - 1, qy), (qx + 1, qy), 2)

        tunic_y = platform_top - 48
        pygame.draw.rect(surf, C_SLATE_DARK, (arch_x - 14, platform_top - 8, 12, 8), border_radius=2)
        pygame.draw.rect(surf, C_SLATE_DARK, (arch_x + 2, platform_top - 8, 14, 8), border_radius=2)
        pygame.draw.rect(surf, C_BLUE_CARD, (arch_x - 12, platform_top - 24, 9, 18), border_radius=2)
        pygame.draw.rect(surf, C_BLUE_CARD, (arch_x + 3, platform_top - 24, 9, 18), border_radius=2)

        pygame.draw.rect(surf, C_MINT, (arch_x - 11, tunic_y, 22, 25), border_radius=4)
        pygame.draw.rect(surf, C_GREEN_DARK, (arch_x - 11, tunic_y, 22, 25), 2, border_radius=4)
        pygame.draw.rect(surf, (146, 64, 14), (arch_x - 11, tunic_y + 15, 22, 5))
        pygame.draw.rect(surf, C_GOLD, (arch_x - 2, tunic_y + 14, 5, 7))

        head_x = arch_x + 2
        head_y = tunic_y - 12
        pygame.draw.circle(surf, C_SLATE_DARK, (head_x, head_y), 13)
        pygame.draw.circle(surf, (254, 240, 199), (head_x, head_y), 12)

        pygame.draw.polygon(surf, C_GREEN_DARK, [
            (head_x - 13, head_y - 2),
            (head_x + 12, head_y - 2),
            (head_x + 3, head_y - 16),
            (head_x - 10, head_y - 14)
        ])
        pygame.draw.polygon(surf, C_CORAL, [
            (head_x - 6, head_y - 12),
            (head_x - 16, head_y - 24),
            (head_x - 4, head_y - 16)
        ])

        eye_x = head_x + 4
        eye_y = head_y - 1
        pygame.draw.circle(surf, C_WHITE, (eye_x, eye_y), 4)
        pygame.draw.circle(surf, C_SLATE_DARK, (eye_x + 1, eye_y), 2)
        pygame.draw.line(surf, C_SLATE_DARK, (eye_x - 3, eye_y - 4), (eye_x + 4, eye_y - 3), 2)

        fx = math.cos(aim_angle)
        fy = math.sin(aim_angle)
        nx = -fy
        ny = fx

        pygame.draw.line(surf, C_SLATE_DARK, (arch_x + 6, tunic_y + 6), (bow_x - 2, bow_y), 6)
        pygame.draw.line(surf, C_MINT, (arch_x + 6, tunic_y + 6), (bow_x - 2, bow_y), 4)
        pygame.draw.circle(surf, (254, 240, 199), (int(bow_x - 2), int(bow_y)), 4)

        tip_top = (bow_x + 6 * fx + 28 * nx, bow_y + 6 * fy + 28 * ny)
        mid_top = (bow_x + 14 * fx + 14 * nx, bow_y + 14 * fy + 14 * ny)
        grip = (bow_x, bow_y)
        mid_bot = (bow_x + 14 * fx - 14 * nx, bow_y + 14 * fy - 14 * ny)
        tip_bot = (bow_x + 6 * fx - 28 * nx, bow_y + 6 * fy - 28 * ny)

        bow_pts = [tip_top, mid_top, grip, mid_bot, tip_bot]
        pygame.draw.lines(surf, C_SLATE_DARK, False, bow_pts, 6)
        pygame.draw.lines(surf, (180, 83, 9), False, bow_pts, 4)
        pygame.draw.lines(surf, (217, 119, 6), False, [mid_top, grip, mid_bot], 2)

        is_nocked = (self.active_arrow is None and self.arrows_left > 0 and not self.game_over)
        if is_nocked:
            pull_x = bow_x - 18 * fx
            pull_y = bow_y - 18 * fy

            rear_shoulder = (arch_x - 4, tunic_y + 8)
            elbow = (arch_x - 12, tunic_y + 12)
            pygame.draw.line(surf, C_MINT, rear_shoulder, elbow, 4)
            pygame.draw.line(surf, C_MINT, elbow, (pull_x, pull_y), 4)
            pygame.draw.circle(surf, (254, 240, 199), (int(pull_x), int(pull_y)), 3)

            pygame.draw.line(surf, C_WHITE, tip_top, (pull_x, pull_y), 2)
            pygame.draw.line(surf, C_WHITE, (pull_x, pull_y), tip_bot, 2)

            nocked_tip_x = bow_x + 14 * fx
            nocked_tip_y = bow_y + 14 * fy
            pygame.draw.line(surf, (146, 64, 14), (pull_x, pull_y), (nocked_tip_x, nocked_tip_y), 3)
            pygame.draw.circle(surf, (203, 213, 225), (int(nocked_tip_x), int(nocked_tip_y)), 3)
            pygame.draw.line(surf, C_CORAL, (pull_x - 3 * fx, pull_y - 3 * fy), (pull_x, pull_y), 4)
        else:
            pygame.draw.line(surf, C_WHITE, tip_top, tip_bot, 2)
            rear_shoulder = (arch_x - 4, tunic_y + 8)
            hand_rest = (arch_x - 6, tunic_y + 20)
            pygame.draw.line(surf, C_MINT, rear_shoulder, hand_rest, 4)
            pygame.draw.circle(surf, (254, 240, 199), hand_rest, 3)

    def draw(self, surf):
        env_engine.draw_base_countryside(surf)

        tx = int(self.target_x + (self.target_recoil * 0.6))
        ty = int(self.target_y)

        pygame.draw.rect(surf, (120, 53, 15), (tx - 6, ty - 68, 12, 136), border_radius=3)
        pygame.draw.rect(surf, (180, 83, 9), (tx - 4, ty - 66, 8, 132))

        pygame.draw.circle(surf, C_SLATE_DARK, (tx, ty), 56)
        pygame.draw.circle(surf, C_WHITE, (tx, ty), 54)
        pygame.draw.circle(surf, C_BLUE_CARD, (tx, ty), 40)
        pygame.draw.circle(surf, C_CORAL, (tx, ty), 26)
        pygame.draw.circle(surf, C_YELLOW, (tx, ty), 12)
        pygame.draw.circle(surf, (239, 68, 68), (tx, ty), 4)

        mx, my = pygame.mouse.get_pos()
        dx = mx - self.bow_x
        dy = my - self.bow_y
        aim_angle = math.atan2(dy, max(1.0, dx))
        aim_angle = max(math.radians(-48), min(math.radians(48), aim_angle))

        if self.active_arrow is None and self.arrows_left > 0 and not self.game_over:
            for i in range(1, 6):
                dot_dist = i * 36
                dot_x = self.bow_x + math.cos(aim_angle) * dot_dist
                dot_y = self.bow_y + math.sin(aim_angle) * dot_dist + (i * i * 0.7)
                pygame.draw.circle(surf, (255, 255, 255, 150), (int(dot_x), int(dot_y)), 3)

        self.draw_archer(surf, aim_angle)

        if self.active_arrow:
            self.active_arrow.draw(surf)

        draw_hud(surf, self.score, ammo=self.arrows_left, combo=self.combo)
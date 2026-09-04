import math
import random
import pygame

from constants import (
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    C_MINT,
    C_GREEN_DARK,
    C_GOLD,
    C_YELLOW,
    C_SLATE_DARK,
    C_CORAL,
    C_WHITE,
    C_PURPLE,
    draw_pixel_box,
    draw_hud,
)

from audio import play_sound
from effects import spawn_burst, score_popups, ScorePopup
from mascot import draw_pulse_character
from environment import env_engine
from tournament import tournament_manager


class GameSkyDash:
    """
    RetroPulse Arcade — Sky Dash

    Controls:
        SPACE      -> Jump
        UP ARROW   -> Jump
        LEFT CLICK -> Jump

    Gameplay:
        - Automatic forward movement
        - Double jump
        - Platform landing
        - Star collectibles
        - Spike hazards
        - Near-miss bonus
        - Increasing game speed
        - Tournament score recording
    """

    # ---------------------------------------------------------
    # PHYSICS TUNING
    # ---------------------------------------------------------

    GRAVITY = 900.0
    JUMP_POWER = -520.0
    DOUBLE_JUMP_POWER = -500.0

    MAX_FALL_SPEED = 700.0

    # Player collision size
    PLAYER_WIDTH = 28
    PLAYER_HEIGHT = 48

    # ---------------------------------------------------------
    # GAME SETTINGS
    # ---------------------------------------------------------

    START_SPEED = 360.0
    MAX_SPEED = 580.0

    PLATFORM_HEIGHT = 24

    # ---------------------------------------------------------
    # INITIALIZATION
    # ---------------------------------------------------------

    def __init__(self):
        self.px = 180.0
        self.py = 420.0

        self.p_vy = 0.0

        self.on_ground = False
        self.jumps_left = 2

        self.score = 0
        self.speed = self.START_SPEED

        self.platforms = [
            {
                "x": 80.0,
                "y": 480.0,
                "w": 420.0,
            },
            {
                "x": 560.0,
                "y": 450.0,
                "w": 380.0,
            },
        ]

        self.collectibles = []
        self.hazards = []

        self.spawn_timer = 0.0

        self.game_over = False
        self.result_data = None

        self.anim_time = 0.0

    # ---------------------------------------------------------
    # UPDATE
    # ---------------------------------------------------------

    def update(self, dt, keys):
        if self.game_over:
            return

        # Prevent unusual physics spikes.
        dt = min(dt, 0.05)

        self.anim_time += dt

        # -----------------------------------------------------
        # SCORE + SPEED
        # -----------------------------------------------------

        self.speed = min(
            self.MAX_SPEED,
            self.START_SPEED + (self.score / 45.0),
        )

        self.score += int(dt * 38)

        # -----------------------------------------------------
        # PLAYER PHYSICS
        # -----------------------------------------------------

        self.p_vy += self.GRAVITY * dt

        # Prevent unlimited falling speed.
        self.p_vy = min(
            self.p_vy,
            self.MAX_FALL_SPEED,
        )

        self.py += self.p_vy * dt

        # -----------------------------------------------------
        # SPAWN NEW CONTENT
        # -----------------------------------------------------

        self.spawn_timer += dt

        if self.spawn_timer >= 1.05:
            self.spawn_timer = 0.0

            last_platform = self.platforms[-1]

            platform_width = random.randint(200, 360)
            platform_y = random.randint(380, 500)

            platform_x = (
                last_platform["x"]
                + last_platform["w"]
                + random.randint(90, 170)
            )

            new_platform = {
                "x": float(platform_x),
                "y": float(platform_y),
                "w": float(platform_width),
            }

            self.platforms.append(new_platform)

            # -------------------------------------------------
            # STAR COLLECTIBLE
            # -------------------------------------------------

            if random.random() < 0.65:
                self.collectibles.append(
                    {
                        "x": platform_x + platform_width // 2,
                        "y": platform_y - 40,
                        "alive": True,
                    }
                )

            # -------------------------------------------------
            # SPIKE HAZARD
            # -------------------------------------------------

            if random.random() < 0.4:
                hazard_x = platform_x + random.randint(
                    60,
                    max(60, platform_width - 60),
                )

                self.hazards.append(
                    {
                        "x": float(hazard_x),
                        "y": float(platform_y),
                        "w": 22,
                        "h": 24,
                        "near_scored": False,
                    }
                )

        # -----------------------------------------------------
        # PLATFORM MOVEMENT + LANDING
        # -----------------------------------------------------

        self.on_ground = False

        previous_bottom = self.py + self.PLAYER_HEIGHT // 2

        for platform in self.platforms:

            platform["x"] -= self.speed * dt

            platform_left = platform["x"] - 14
            platform_right = platform["x"] + platform["w"] + 14

            player_over_platform = (
                platform_left <= self.px <= platform_right
            )

            if not player_over_platform:
                continue

            platform_y = platform["y"]

            player_bottom = self.py + self.PLAYER_HEIGHT // 2

            # Only land while falling.
            if self.p_vy >= 0:

                crossed_platform = (
                    previous_bottom <= platform_y
                    and player_bottom >= platform_y
                )

                close_to_platform = (
                    0 <= player_bottom - platform_y <= 20
                )

                if crossed_platform or close_to_platform:
                    self.py = (
                        platform_y
                        - self.PLAYER_HEIGHT // 2
                    )

                    self.p_vy = 0.0

                    self.on_ground = True
                    self.jumps_left = 2

        # -----------------------------------------------------
        # HAZARDS
        # -----------------------------------------------------

        player_rect = pygame.Rect(
            int(self.px - self.PLAYER_WIDTH // 2),
            int(self.py - self.PLAYER_HEIGHT // 2),
            self.PLAYER_WIDTH,
            self.PLAYER_HEIGHT,
        )

        for hazard in self.hazards:

            hazard["x"] -= self.speed * dt

            hazard_rect = pygame.Rect(
                int(hazard["x"] - hazard["w"] // 2),
                int(hazard["y"] - hazard["h"]),
                int(hazard["w"]),
                int(hazard["h"]),
            )

            # -------------------------------------------------
            # DIRECT COLLISION
            # -------------------------------------------------

            if player_rect.colliderect(hazard_rect):

                self.game_over = True

                play_sound("hit")

                spawn_burst(
                    self.px,
                    self.py,
                    C_CORAL,
                    24,
                    shape="square",
                )

                self.result_data = (
                    tournament_manager.record_game(
                        "sky_dash",
                        self.score,
                    )
                )

                break

            # -------------------------------------------------
            # NEAR MISS
            # -------------------------------------------------

            if (
                abs(self.px - hazard["x"]) < 42
                and abs(self.py - hazard["y"]) < 48
                and not hazard["near_scored"]
            ):

                hazard["near_scored"] = True

                self.score += 50

                score_popups.append(
                    ScorePopup(
                        "+50 NEAR MISS!",
                        self.px,
                        self.py - 30,
                        C_GOLD,
                    )
                )

                spawn_burst(
                    self.px,
                    self.py,
                    C_WHITE,
                    4,
                    shape="star",
                )

        # -----------------------------------------------------
        # COLLECTIBLES
        # -----------------------------------------------------

        for collectible in self.collectibles:

            collectible["x"] -= self.speed * dt

            if not collectible["alive"]:
                continue

            distance = math.hypot(
                self.px - collectible["x"],
                self.py - collectible["y"],
            )

            if distance < 30:

                collectible["alive"] = False

                self.score += 150

                play_sound("coin")

                spawn_burst(
                    collectible["x"],
                    collectible["y"],
                    C_GOLD,
                    12,
                    shape="star",
                )

                score_popups.append(
                    ScorePopup(
                        "+150 STAR!",
                        collectible["x"],
                        collectible["y"] - 20,
                        C_GOLD,
                    )
                )

        # -----------------------------------------------------
        # REMOVE OLD OBJECTS
        # -----------------------------------------------------

        self.platforms = [
            platform
            for platform in self.platforms
            if platform["x"] + platform["w"] > -60
        ]

        self.hazards = [
            hazard
            for hazard in self.hazards
            if hazard["x"] > -60
        ]

        self.collectibles = [
            collectible
            for collectible in self.collectibles
            if (
                collectible["alive"]
                and collectible["x"] > -60
            )
        ]

        # -----------------------------------------------------
        # FALLING INTO A GAP
        # -----------------------------------------------------

        if self.py > SCREEN_HEIGHT + 70:

            self.game_over = True

            play_sound("hit")

            self.result_data = (
                tournament_manager.record_game(
                    "sky_dash",
                    self.score,
                )
            )

    # ---------------------------------------------------------
    # JUMP
    # ---------------------------------------------------------

    def jump(self):
        """
        Perform a normal jump or double jump.

        First jump:
            -520 velocity

        Second jump:
            -500 velocity
        """

        if self.game_over:
            return

        if self.jumps_left <= 0:
            return

        # First jump
        if self.on_ground:

            self.p_vy = self.JUMP_POWER

            self.on_ground = False
            self.jumps_left = 1

            play_sound("jump")

            return

        # Double jump
        self.p_vy = self.DOUBLE_JUMP_POWER

        self.jumps_left = 0

        play_sound("jump")

        spawn_burst(
            self.px,
            self.py + 20,
            (254, 240, 138),
            8,
            shape="star",
        )

    # ---------------------------------------------------------
    # MOUSE CONTROL
    # ---------------------------------------------------------

    def handle_click(self, mx, my):
        self.jump()

    # ---------------------------------------------------------
    # DRAW
    # ---------------------------------------------------------

    def draw(self, surf):

        # -----------------------------------------------------
        # BACKGROUND
        # -----------------------------------------------------

        env_engine.draw_base_countryside(
            surf,
            ground_y=580,
        )

        # -----------------------------------------------------
        # PLATFORMS
        # -----------------------------------------------------

        for platform in self.platforms:

            rect = pygame.Rect(
                int(platform["x"]),
                int(platform["y"]),
                int(platform["w"]),
                self.PLATFORM_HEIGHT,
            )

            draw_pixel_box(
                surf,
                rect,
                C_MINT,
                border_color=C_GREEN_DARK,
                elevation=4,
            )

            # Platform highlight
            pygame.draw.rect(
                surf,
                (34, 197, 94),
                (
                    int(platform["x"] + 2),
                    int(platform["y"] + 2),
                    int(platform["w"] - 4),
                    5,
                ),
            )

        # -----------------------------------------------------
        # SPIKE HAZARDS
        # -----------------------------------------------------

        for hazard in self.hazards:

            hx = int(hazard["x"])
            hy = int(hazard["y"])
            hw = int(hazard["w"])
            hh = int(hazard["h"])

            # Dark outline
            pygame.draw.polygon(
                surf,
                C_SLATE_DARK,
                [
                    (hx - hw // 2 - 2, hy),
                    (hx, hy - hh - 2),
                    (hx + hw // 2 + 2, hy),
                ],
            )

            # Main spike
            pygame.draw.polygon(
                surf,
                C_PURPLE,
                [
                    (hx - hw // 2, hy),
                    (hx, hy - hh),
                    (hx + hw // 2, hy),
                ],
            )

            # Highlight
            pygame.draw.line(
                surf,
                C_WHITE,
                (hx - 2, hy),
                (hx, hy - hh + 4),
                2,
            )

        # -----------------------------------------------------
        # STAR COLLECTIBLES
        # -----------------------------------------------------

        for collectible in self.collectibles:

            if not collectible["alive"]:
                continue

            cx = int(collectible["x"])
            cy = int(collectible["y"])

            # Outer coin
            pygame.draw.circle(
                surf,
                C_GOLD,
                (cx, cy),
                13,
            )

            # Inner coin
            pygame.draw.circle(
                surf,
                C_YELLOW,
                (cx, cy),
                9,
            )

            # Shine
            pygame.draw.circle(
                surf,
                C_WHITE,
                (cx - 3, cy - 3),
                3,
            )

        # -----------------------------------------------------
        # PLAYER
        # -----------------------------------------------------

        state = (
            "JUMP"
            if not self.on_ground
            else "RUN"
        )

        draw_pulse_character(
            surf,
            self.px,
            self.py,
            scale=1.0,
            state=state,
            anim_time=self.anim_time,
        )

        # -----------------------------------------------------
        # HUD
        # -----------------------------------------------------

        draw_hud(
            surf,
            self.score,
        )
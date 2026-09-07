"""
RETROPULSE ARCADE — NEON RUSH
A 3-lane cyberpunk endless runner with procedural neon visuals,
dt-based jump and slide physics, multi-type obstacles, and fair gameplay.
"""

import math
import random
import pygame

from constants import (
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    C_SLATE_DARK,
    C_SLATE_DEEP,
    C_WHITE,
    C_GOLD,
    C_YELLOW,
    C_CORAL,
    C_MINT,
    C_BLUE_CARD,
    C_PURPLE,
    C_DANGER,
    C_ROAD,
    FONT_HUGE,
    FONT_TITLE,
    FONT_CARD,
    FONT_BODY,
    FONT_HUD,
    draw_pixel_box,
    draw_hud,
)
from audio import play_sound
from effects import spawn_burst, score_popups, ScorePopup
from mascot import draw_pulse_character
from tournament import tournament_manager


# Lane coordinates (Centered across 960 width)
LANE_X = [310, 480, 650]
ROAD_LEFT = 210
ROAD_RIGHT = 750
ROAD_WIDTH = ROAD_RIGHT - ROAD_LEFT
PLAYER_BASE_Y = 520

# Physics constants (clean dt-based pixel/second kinematics)
GRAVITY = 1750.0
JUMP_IMPULSE = -590.0
MAX_JUMP_HEIGHT = -140.0
SLIDE_DURATION = 0.65


class GameNeonRush:
    def __init__(self):
        # Game states: "START", "PLAYING", "GAME_OVER"
        self.game_state = "START"
        self.game_over = False
        self.result_data = None

        # Scoring & progression
        self.score = 0
        self.distance = 0.0
        self.combo = 0
        self.base_speed = 370.0
        self.speed = 370.0
        self.speed_boost_timer = 0.0

        # Lane system
        self.current_lane = 1
        self.target_lane = 1
        self.player_x = float(LANE_X[1])

        # Jump physics
        self.jump_y = 0.0
        self.jump_vy = 0.0
        self.is_jumping = False

        # Slide system
        self.is_sliding = False
        self.slide_timer = 0.0

        # Input edge-detection / debouncing
        self.prev_left_key = False
        self.prev_right_key = False
        self.prev_jump_key = False
        self.prev_slide_key = False

        # Entities
        self.obstacles = []
        self.collectibles = []
        self.spawn_timer = 0.0
        self.next_spawn_interval = 1.3
        self.last_pattern_type = None

        # Environment & Animation
        self.anim_time = 0.0
        self.road_scroll = 0.0
        self.loading_timer = 0.0
        self.loading_duration = 1.5  # seconds of loading screen
        self.show_start_screen = False  # becomes True after loading

        # Deterministic background skyline (Fixes any random flickering)
        self.city_buildings = []
        rng = random.Random(777)
        for i in range(24):  # More buildings for denser city
            bx = i * 42 - 60
            bw = rng.randint(38, 50)
            bh = rng.randint(180, 300)
            # Brighter building colors for vibrant cyberpunk feel
            b_color = rng.choice([
                (10, 30, 60),   # Deep blue
                (20, 10, 40),   # Purple
                (0, 20, 30),    # Teal
                (30, 0, 30),    # Dark magenta
                (10, 10, 30),   # Very dark blue
            ])
            # Brighter window colors
            win_color = rng.choice([
                C_BLUE_CARD,
                (100, 200, 255),  # Light blue
                (255, 100, 180),  # Pink
                (100, 255, 180),  # Mint
                (255, 255, 100),  # Yellow
                (255, 100, 100),  # Coral
            ])
            windows = []
            for wy in range(16, bh - 20, 18):
                for wx in range(4, bw - 6, 10):
                    if rng.random() < 0.5:  # Slightly fewer windows for performance
                        windows.append((wx, wy))
            self.city_buildings.append({
                "x": bx, "w": bw, "h": bh,
                "color": b_color, "win_color": win_color,
                "windows": windows
            })

        # Neon signs on buildings (deterministic)
        self.neon_signs = []
        rng2 = random.Random(888)
        for i in range(8):
            building_idx = rng2.randint(0, len(self.city_buildings) - 1)
            b = self.city_buildings[building_idx]
            sign_x = b["x"] + rng2.randint(5, b["w"] - 20)
            sign_y = 160 - (b["h"] - 140) + rng2.randint(10, b["h"] - 30)
            sign_width = rng2.randint(18, 35)
            sign_height = rng2.randint(8, 15)
            sign_color = rng2.choice([
                (255, 0, 100),   # Pink
                (0, 255, 255),   # Cyan
                (255, 255, 0),   # Yellow
                (0, 255, 0),     # Green
                (255, 0, 255),   # Magenta
                (0, 150, 255),   # Blue
            ])
            self.neon_signs.append({
                "x": sign_x, "y": sign_y,
                "w": sign_width, "h": sign_height,
                "color": sign_color,
                "pulse": rng2.random() * 6.28,  # Random pulse offset
                "pulse_speed": rng2.uniform(1.0, 3.0),
            })

    def start_jump(self):
        """Initiates a crisp, height-clamped jump."""
        if not self.is_jumping and not self.is_sliding and self.jump_y == 0.0:
            self.is_jumping = True
            self.jump_vy = JUMP_IMPULSE
            play_sound("jump")
            spawn_burst(int(self.player_x), PLAYER_BASE_Y, C_BLUE_CARD, 8, shape="star")

    def start_slide(self):
        """Initiates a temporary low-profile slide."""
        if not self.is_sliding:
            # If in air, perform a fast-fall to return quickly
            if self.is_jumping:
                self.jump_vy = max(self.jump_vy, 350.0)
            else:
                self.is_sliding = True
                self.slide_timer = SLIDE_DURATION
                play_sound("pop")
                spawn_burst(int(self.player_x), PLAYER_BASE_Y - 4, C_MINT, 6, shape="square")

    def jump(self):
        """Public method called directly by main.py."""
        if self.game_state == "START":
            self.game_state = "PLAYING"
            play_sound("jump")
            return
        if self.game_state == "PLAYING" and not self.game_over:
            self.start_jump()

    def slide(self):
        """Public method for sliding."""
        if self.game_state == "PLAYING" and not self.game_over:
            self.start_slide()

    def handle_click(self, *args):
        """Public method called on mouse click."""
        if self.game_state == "START":
            self.game_state = "PLAYING"
            play_sound("jump")
            return
        if self.game_state == "PLAYING" and not self.game_over:
            self.start_jump()

    def _process_inputs(self, keys):
        """Processes continuous and edge-triggered keyboard input."""
        left_pressed = keys[pygame.K_LEFT] or keys[pygame.K_a]
        right_pressed = keys[pygame.K_RIGHT] or keys[pygame.K_d]
        jump_pressed = keys[pygame.K_SPACE] or keys[pygame.K_UP] or keys[pygame.K_w]
        slide_pressed = keys[pygame.K_DOWN] or keys[pygame.K_s]

        # Start game from start screen
        if self.game_state == "START":
            if (jump_pressed and not self.prev_jump_key) or (slide_pressed and not self.prev_slide_key):
                self.game_state = "PLAYING"
                play_sound("jump")
            self.prev_jump_key = jump_pressed
            self.prev_slide_key = slide_pressed
            return

        if self.game_state != "PLAYING" or self.game_over:
            return

        # Lane shift left (Edge-detected)
        if left_pressed and not self.prev_left_key:
            if self.target_lane > 0:
                self.target_lane -= 1
                play_sound("pop")
                spawn_burst(int(self.player_x) - 10, PLAYER_BASE_Y - 14, C_BLUE_CARD, 4, shape="square")

        # Lane shift right (Edge-detected)
        if right_pressed and not self.prev_right_key:
            if self.target_lane < 2:
                self.target_lane += 1
                play_sound("pop")
                spawn_burst(int(self.player_x) + 10, PLAYER_BASE_Y - 14, C_BLUE_CARD, 4, shape="square")

        # Jump (Edge-detected)
        if jump_pressed and not self.prev_jump_key:
            self.start_jump()

        # Slide (Continuous or edge-detected)
        if slide_pressed and not self.prev_slide_key:
            self.start_slide()
        elif slide_pressed and self.is_jumping:
            # Fast fall mechanic
            self.jump_vy = max(self.jump_vy, 650.0)

        # Store edge states
        self.prev_left_key = left_pressed
        self.prev_right_key = right_pressed
        self.prev_jump_key = jump_pressed
        self.prev_slide_key = slide_pressed

    def _spawn_wave(self):
        """Spawns fair, guaranteed-avoidable obstacle and collectible waves."""
        spawn_y = -80.0
        speed_factor = min(1.0, self.score / 3500.0)

        # Guarantee at least one lane is completely clear or cleanly bypassable
        safe_lane = random.randint(0, 2)
        other_lanes = [l for l in [0, 1, 2] if l != safe_lane]

        pattern_roll = random.random()

        if pattern_roll < 0.40:
            # Single obstacle in one lane
            obs_lane = random.choice(other_lanes)
            obs_type = random.choice(["GROUND_BARRIER", "HIGH_LASER", "NEON_BLOCK"])
            self.obstacles.append(self._create_obstacle(obs_lane, spawn_y, obs_type))

        elif pattern_roll < 0.72:
            # Two lanes blocked, but with varied mechanics
            type_a = random.choice(["GROUND_BARRIER", "NEON_BLOCK"])
            type_b = random.choice(["HIGH_LASER", "GROUND_BARRIER"])
            self.obstacles.append(self._create_obstacle(other_lanes[0], spawn_y, type_a))
            self.obstacles.append(self._create_obstacle(other_lanes[1], spawn_y, type_b))

        elif pattern_roll < 0.88:
            # Moving drone in one lane, leaves two open
            self.obstacles.append(self._create_obstacle(other_lanes[0], spawn_y, "MOVING_DRONE"))

        else:
            # Double high laser (requires slide in two lanes or safe lane)
            self.obstacles.append(self._create_obstacle(other_lanes[0], spawn_y, "HIGH_LASER"))
            self.obstacles.append(self._create_obstacle(other_lanes[1], spawn_y, "HIGH_LASER"))

        # Spawn collectibles in the safe lane or reward jump
        if random.random() < 0.75:
            # Energy orbs or special pickups
            if random.random() < 0.12 and self.score > 200:
                item_type = "BOOST"
            elif random.random() < 0.28:
                item_type = "PRISM"
            else:
                item_type = "ORB"

            # Occasionally place collectible high to reward jumping over ground barrier
            high_pickup = False
            for obs in self.obstacles:
                if obs["lane"] == safe_lane and obs["type"] == "GROUND_BARRIER":
                    high_pickup = True

            self.collectibles.append({
                "lane": safe_lane,
                "x": float(LANE_X[safe_lane]),
                "y": spawn_y - (50.0 if not high_pickup else 80.0),
                "type": item_type,
                "high": high_pickup,
                "alive": True
            })

    def _create_obstacle(self, lane, y, obs_type):
        """Creates an obstacle data dictionary with guaranteed valid keys."""
        return {
            "lane": lane,
            "x": float(LANE_X[lane]),
            "y": y,
            "type": obs_type,
            "w": 52,
            "h": 32 if obs_type == "GROUND_BARRIER" else (36 if obs_type == "HIGH_LASER" else 68),
            "move_dir": 1 if lane == 0 else -1,
            "alive": True
        }

    def update(self, dt, keys=None):
        """Frame update with delta-time physics and collision detection."""
        # Fallback to direct key polling if keys not passed
        if keys is None:
            keys = pygame.key.get_pressed()

        self.anim_time += dt
        self._process_inputs(keys)

        if self.game_state != "PLAYING" or self.game_over:
            return

        # Boost timer & speed calculation
        if self.speed_boost_timer > 0:
            self.speed_boost_timer -= dt
            self.speed = self.base_speed * 1.35
        else:
            self.speed = min(620.0, self.base_speed + (self.distance / 45.0))

        # Scoring & road scroll
        self.distance += (self.speed * dt) * 0.1
        self.score = int(self.distance * 8) + (self.combo * 45)
        self.road_scroll = (self.road_scroll + self.speed * dt) % 64.0

        # Smooth lane transition
        target_x = float(LANE_X[self.target_lane])
        self.player_x += (target_x - self.player_x) * min(1.0, 19.0 * dt)

        # Delta-time based Jump Physics (Strictly clamped, guaranteed landing)
        if self.is_jumping:
            self.jump_vy += GRAVITY * dt
            self.jump_y += self.jump_vy * dt

            # Ceiling clamp: prevent flying upward indefinitely
            if self.jump_y < MAX_JUMP_HEIGHT:
                self.jump_y = MAX_JUMP_HEIGHT
                if self.jump_vy < 0:
                    self.jump_vy = 0.0

            # Ground clamp: guaranteed landing
            if self.jump_y >= 0.0:
                self.jump_y = 0.0
                self.jump_vy = 0.0
                self.is_jumping = False
                spawn_burst(int(self.player_x), PLAYER_BASE_Y, (148, 163, 184), 5, shape="square")
        else:
            self.jump_y = 0.0
            self.jump_vy = 0.0

        # Slide countdown
        if self.is_sliding:
            self.slide_timer -= dt
            if self.slide_timer <= 0:
                self.is_sliding = False

        # Obstacle wave spawner
        self.spawn_timer += dt
        spawn_rate = max(0.85, 1.45 - (self.speed / 1100.0))
        if self.spawn_timer >= spawn_rate:
            self.spawn_timer = 0.0
            self._spawn_wave()

        # Update and collide obstacles
        player_hitbox = self._get_player_hitbox()

        for obs in self.obstacles:
            obs["y"] += self.speed * dt

            # Update moving drone horizontal sweep
            if obs["type"] == "MOVING_DRONE":
                obs["x"] += obs["move_dir"] * 130.0 * dt
                # Bounce between road bounds
                if obs["x"] <= LANE_X[0] - 15:
                    obs["move_dir"] = 1
                elif obs["x"] >= LANE_X[2] + 15:
                    obs["move_dir"] = -1

            # Check collision when obstacle enters player's depth
            obs_rect = self._get_obstacle_hitbox(obs)
            if obs_rect and player_hitbox.colliderect(obs_rect):
                # Check specific bypass conditions
                bypassed = False

                if obs["type"] == "GROUND_BARRIER":
                    # Clearable only by jumping high
                    if self.is_jumping and self.jump_y < -42.0:
                        bypassed = True

                elif obs["type"] == "HIGH_LASER":
                    # Clearable by sliding cleanly underneath
                    if self.is_sliding and not self.is_jumping:
                        bypassed = True

                if not bypassed:
                    self._trigger_game_over()
                    break

        # Remove passed obstacles safely
        self.obstacles = [o for o in self.obstacles if o["y"] < SCREEN_HEIGHT + 100]

        # Update and collect pickups
        for c in self.collectibles:
            c["y"] += self.speed * dt
            c_rect = pygame.Rect(int(c["x"] - 14), int(c["y"] - 14), 28, 28)

            if c["alive"] and player_hitbox.colliderect(c_rect):
                c["alive"] = False
                self.combo += 1

                if c["type"] == "ORB":
                    self.score += 100 * min(5, self.combo)
                    play_sound("pop")
                    spawn_burst(int(c["x"]), int(c["y"]), C_BLUE_CARD, 12, shape="star")
                    score_popups.append(ScorePopup(f"+{100 * min(5, self.combo)}", c["x"], c["y"] - 20, C_BLUE_CARD))

                elif c["type"] == "PRISM":
                    self.score += 250 * min(5, self.combo)
                    play_sound("coin")
                    spawn_burst(int(c["x"]), int(c["y"]), C_GOLD, 16, shape="star")
                    score_popups.append(ScorePopup("PRISM +250!", c["x"], c["y"] - 20, C_GOLD))

                elif c["type"] == "BOOST":
                    self.score += 150
                    self.speed_boost_timer = 4.0
                    play_sound("celebrate")
                    spawn_burst(int(c["x"]), int(c["y"]), C_YELLOW, 20, shape="star")
                    score_popups.append(ScorePopup("CYBER BOOST!", c["x"], c["y"] - 20, C_YELLOW))

        self.collectibles = [c for c in self.collectibles if c["alive"] and c["y"] < SCREEN_HEIGHT + 60]

    def _get_player_hitbox(self):
        """Constructs accurate pygame.Rect for player accounting for jump and slide."""
        px = int(self.player_x)
        if self.is_sliding:
            # Low, wide slide hitbox
            return pygame.Rect(px - 18, PLAYER_BASE_Y - 22, 36, 20)
        else:
            # Standing or jumping hitbox
            py = int(PLAYER_BASE_Y + self.jump_y)
            return pygame.Rect(px - 16, py - 46, 32, 44)

    def _get_obstacle_hitbox(self, obs):
        """Constructs accurate vertical collision rect based on obstacle type."""
        ox = int(obs["x"])
        oy = int(obs["y"])

        if obs["type"] == "GROUND_BARRIER":
            # Sits on ground (Requires jumping over)
            return pygame.Rect(ox - 24, oy - 28, 48, 26)

        elif obs["type"] == "HIGH_LASER":
            # Overhead beam (Requires sliding underneath)
            return pygame.Rect(ox - 26, oy - 56, 52, 28)

        elif obs["type"] == "NEON_BLOCK":
            # Tall monolith (Requires lane switch)
            return pygame.Rect(ox - 22, oy - 66, 44, 64)

        elif obs["type"] == "MOVING_DRONE":
            # Sweeping aerial obstacle
            return pygame.Rect(ox - 20, oy - 48, 40, 42)

        return None

    def _trigger_game_over(self):
        """Handles game over exactly once and records tournament data."""
        if not self.game_over:
            self.game_over = True
            play_sound("hit")
            spawn_burst(int(self.player_x), int(PLAYER_BASE_Y + self.jump_y), C_CORAL, 28, shape="square")
            score_popups.append(ScorePopup("SYSTEM CRASH!", self.player_x, PLAYER_BASE_Y - 40, C_DANGER))
            self.result_data = tournament_manager.record_game("neon_rush", self.score)

    def draw_background(self, surf):
        """Draws a stable, deterministic cyberpunk neon skyline."""
        surf.fill(C_SLATE_DEEP)

        # Distant static neon skyline
        for b in self.city_buildings:
            bx, by = b["x"], 160 - (b["h"] - 140)
            pygame.draw.rect(surf, b["color"], (bx, by, b["w"], b["h"]))
            # Deterministic windows
            for wx, wy in b["windows"]:
                pygame.draw.rect(surf, b["win_color"], (bx + wx, by + wy, 4, 6))

        # Neon signs on buildings (with pulsing animation)
        for sign in self.neon_signs:
            # Pulsing brightness
            pulse = (math.sin(sign["pulse"]) + 1) * 0.5  # 0 to 1
            sign["pulse"] += sign["pulse_speed"] * 0.016  # Approx 60 FPS
            # Brighten the sign color based on pulse
            r = min(255, int(sign["color"][0] * (0.5 + pulse * 0.5)))
            g = min(255, int(sign["color"][1] * (0.5 + pulse * 0.5)))
            b = min(255, int(sign["color"][2] * (0.5 + pulse * 0.5)))
            pulse_color = (r, g, b)
            # Draw neon sign with glow effect (simple layered rectangles)
            glow_size = 2
            pygame.draw.rect(surf, (0, 0, 0), (sign["x"] - glow_size, sign["y"] - glow_size, sign["w"] + glow_size*2, sign["h"] + glow_size*2))
            pygame.draw.rect(surf, pulse_color, (sign["x"], sign["y"], sign["w"], sign["h"]))
            # Inner brighter core
            inner_w = max(2, sign["w"] - 4)
            inner_h = max(2, sign["h"] - 4)
            pygame.draw.rect(surf, (min(255, r+50), min(255, g+50), min(255, b+50)),
                           (sign["x"]+2, sign["y"]+2, inner_w, inner_h))

        # Neon horizon glow line
        pygame.draw.line(surf, (56, 189, 248), (0, 160), (SCREEN_WIDTH, 160), 3)
        pygame.draw.line(surf, (244, 114, 182), (0, 162), (SCREEN_WIDTH, 162), 1)

        # Cyber Asphalt Road
        pygame.draw.rect(surf, C_ROAD, (ROAD_LEFT, 160, ROAD_WIDTH, SCREEN_HEIGHT - 160))

        # Glowing neon road guardrails
        pygame.draw.line(surf, (244, 114, 182), (ROAD_LEFT, 160), (ROAD_LEFT, SCREEN_HEIGHT), 5)
        pygame.draw.line(surf, C_WHITE, (ROAD_LEFT + 2, 160), (ROAD_LEFT + 2, SCREEN_HEIGHT), 2)
        pygame.draw.line(surf, (56, 189, 248), (ROAD_RIGHT, 160), (ROAD_RIGHT, SCREEN_HEIGHT), 5)
        pygame.draw.line(surf, C_WHITE, (ROAD_RIGHT - 2, 160), (ROAD_RIGHT - 2, SCREEN_HEIGHT), 2)

        # Scrolling neon lane divider dashes
        dash_len = 36.0
        dash_gap = 28.0
        total_dash = dash_len + dash_gap

        for divider_x in [395, 565]:
            offset_y = self.road_scroll % total_dash
            for y in range(-int(total_dash), SCREEN_HEIGHT + int(total_dash), int(total_dash)):
                dy = y + int(offset_y)
                if dy >= 160:
                    pygame.draw.line(surf, (148, 163, 184), (divider_x, dy), (divider_x, min(SCREEN_HEIGHT, dy + int(dash_len))), 3)

    def draw_entities(self, surf):
        """Draws collectibles and obstacles with distinct neon styling."""
        # Collectibles
        for c in self.collectibles:
            cx = int(c["x"])
            cy = int(c["y"])

            if c["type"] == "ORB":
                # Glowing blue energy orb with pulse
                pulse = (math.sin(self.anim_time * 5.0) + 1) * 0.3 + 0.7  # 0.7 to 1.0
                radius = int(11 * pulse)
                # Outer glow
                pygame.draw.circle(surf, (30, 30, 60), (cx, cy), radius + 4)
                # Mid layer
                pygame.draw.circle(surf, C_SLATE_DARK, (cx, cy), radius + 2)
                # Core
                pygame.draw.circle(surf, C_BLUE_CARD, (cx, cy), radius)
                # Sparkle
                pygame.draw.circle(surf, C_WHITE, (cx - 2, cy - 2), 2)

            elif c["type"] == "PRISM":
                # Glowing gold prism gem with pulse
                pulse = (math.sin(self.anim_time * 4.0) + 1) * 0.2 + 0.8  # 0.8 to 1.0
                size = int(14 * pulse)
                pts = [(cx, cy - size), (cx + size, cy), (cx, cy + size), (cx - size, cy)]
                # Outer glow
                glow_pts = [(p[0] + 2, p[1] + 2) for p in pts]
                pygame.draw.polygon(surf, (30, 30, 60), glow_pts)
                # Mid layer
                mid_pts = [(p[0] + 1, p[1] + 1) for p in pts]
                pygame.draw.polygon(surf, C_SLATE_DARK, mid_pts)
                # Core
                pygame.draw.polygon(surf, C_GOLD, pts)
                # Inner sparkle
                inner_pts = [(cx, cy - size//2), (cx + size//2, cy), (cx, cy + size//2), (cx - size//2, cy)]
                pygame.draw.polygon(surf, C_YELLOW, inner_pts)
                pygame.draw.circle(surf, C_WHITE, (cx - 1, cy - 1), 1)

            elif c["type"] == "BOOST":
                # Neon lightning cell with pulse
                pulse = (math.sin(self.anim_time * 6.0) + 1) * 0.2 + 0.8  # 0.8 to 1.0
                radius = int(12 * pulse)
                # Outer glow
                pygame.draw.circle(surf, (30, 30, 60), (cx, cy), radius + 3)
                # Mid layer
                pygame.draw.circle(surf, C_SLATE_DARK, (cx, cy), radius + 1)
                # Core
                pygame.draw.circle(surf, C_YELLOW, (cx, cy), radius)
                # Lightning bolt icon (scaled)
                bolt_size = 0.5 * pulse
                bolt = [(cx - 2*bolt_size, cy - 9*bolt_size),
                       (cx + 5*bolt_size, cy - 1*bolt_size),
                       (cx, cy),
                       (cx + 4*bolt_size, cy + 9*bolt_size),
                       (cx - 5*bolt_size, cy + 1*bolt_size),
                       (cx - 1*bolt_size, cy)]
                pygame.draw.polygon(surf, C_CORAL, bolt)

        # Obstacles
        for obs in self.obstacles:
            ox = int(obs["x"])
            oy = int(obs["y"])
            ow = obs["w"]
            oh = obs["h"]

            if obs["type"] == "GROUND_BARRIER":
                # Low neon hurdle (jump required) - brighter colors
                r = pygame.Rect(ox - ow // 2, oy - oh, ow, oh)
                # Outer glow
                pygame.draw.rect(surf, (30, 0, 0), (r.x - 3, r.y - 3, r.width + 6, r.height + 6))
                # Main barrier
                draw_pixel_box(surf, r, C_CORAL, border_color=C_SLATE_DARK, elevation=2)
                # Warning stripes - brighter yellow
                for s in range(r.left + 6, r.right - 6, 12):
                    pygame.draw.line(surf, C_YELLOW, (s, r.bottom - 4), (s + 6, r.top + 4), 3)
                # Neon edge
                pygame.draw.line(surf, (255, 100, 100), (r.left, r.top), (r.right, r.top), 2)

            elif obs["type"] == "HIGH_LASER":
                # Overhead beam with side emitter posts (slide required) - brighter
                top_y = oy - oh
                # Left emitter
                pygame.draw.rect(surf, (30, 30, 60), (ox - ow // 2, top_y, 8, oh + 24), border_radius=2)
                pygame.draw.rect(surf, C_MINT, (ox - ow // 2 + 1, top_y + 1, 6, oh + 22))
                # Right emitter
                pygame.draw.rect(surf, (30, 30, 60), (ox + ow // 2 - 8, top_y, 8, oh + 24), border_radius=2)
                pygame.draw.rect(surf, C_MINT, (ox + ow // 2 - 7, top_y + 1, 6, oh + 22))
                # Glowing high laser beam - brighter pink
                beam_rect = pygame.Rect(ox - ow // 2 + 4, top_y + 6, ow - 8, 12)
                pygame.draw.rect(surf, (255, 100, 200), beam_rect, border_radius=3)
                pygame.draw.rect(surf, C_WHITE, (beam_rect.x, beam_rect.y + 3, beam_rect.w, 5))
                # Neon pulse on beam
                pulse = (math.sin(self.anim_time * 3.0) + 1) * 0.3
                pulse_width = int(ow * 0.1 * pulse)
                pygame.draw.rect(surf, (255, 180, 220),
                               (beam_rect.x + (ow//2 - pulse_width//2), beam_rect.y, pulse_width, beam_rect.h))

            elif obs["type"] == "NEON_BLOCK":
                # Impassable monolith (lane change required) - brighter purple
                r = pygame.Rect(ox - ow // 2, oy - oh, ow, oh)
                # Outer glow
                pygame.draw.rect(surf, (30, 0, 30), (r.x - 3, r.y - 3, r.width + 6, r.height + 6))
                # Main block
                draw_pixel_box(surf, r, C_PURPLE, border_color=C_SLATE_DARK, elevation=4)
                # Inner glow
                pygame.draw.rect(surf, (192, 132, 252), (r.left + 4, r.top + 4, r.width - 8, r.height - 8), 2)
                # Center core
                pygame.draw.circle(surf, C_BLUE_CARD, (r.centerx, r.centery), 8)
                # Pulsing core
                pulse = (math.sin(self.anim_time * 4.0) + 1) * 0.3
                pulse_radius = int(4 * pulse)
                pygame.draw.circle(surf, (200, 180, 255), (r.centerx, r.centery), pulse_radius)

            elif obs["type"] == "MOVING_DRONE":
                # Sweeping drone - brighter colors
                drone_y = oy - oh // 2
                # Outer glow
                pygame.draw.circle(surf, (30, 30, 60), (ox, drone_y), 20)
                # Main body
                pygame.draw.circle(surf, C_SLATE_DARK, (ox, drone_y), 17)
                pygame.draw.circle(surf, C_YELLOW, (ox, drone_y), 14)
                pygame.draw.circle(surf, C_DANGER, (ox, drone_y), 7)
                # Core glow
                pygame.draw.circle(surf, (255, 180, 100), (ox, drone_y), 4)
                # Wing blades
                pygame.draw.line(surf, C_BLUE_CARD, (ox - 22, drone_y - 8), (ox + 22, drone_y - 8), 3)
                # Engine glow
                pygame.draw.circle(surf, (100, 200, 255), (ox - 18, drone_y - 12), 3)
                pygame.draw.circle(surf, (100, 200, 255), (ox + 18, drone_y - 12), 3)

    def draw_player(self, surf):
        """Renders the mascot character in run, jump, or slide posture."""
        px = int(self.player_x)

        # Ground drop shadow (anchors character in lane)
        shadow_w = 34 if not self.is_sliding else 42
        shadow_h = 10 if not self.is_sliding else 8
        pygame.draw.ellipse(surf, (10, 10, 20), (px - shadow_w // 2, PLAYER_BASE_Y - 4, shadow_w, shadow_h))

        if self.is_sliding:
            # Slide posture: squashed lower profile with speed spark trails
            slide_y = PLAYER_BASE_Y - 14
            # Draw mascot with scaled squat state
            draw_pulse_character(surf, px, slide_y, scale=0.75, state="RUN", anim_time=self.anim_time, facing_right=True)
            # Cyber sliding sparks - more numerous and brighter
            for i in range(5):
                spk_x = px - 20 - (i * 6)
                spk_y = PLAYER_BASE_Y - 2 + (i * 2)
                size = 4 - i
                if size > 0:
                    pygame.draw.circle(surf, C_BLUE_CARD, (spk_x, spk_y), size)
                    # Outer glow
                    pygame.draw.circle(surf, (100, 200, 255), (spk_x, spk_y), size + 1, 1)

        elif self.is_jumping:
            # Jump posture: elevated with vertical stretch
            py = int(PLAYER_BASE_Y + self.jump_y)
            # Draw mascot with jump state
            draw_pulse_character(surf, px, py, scale=1.05, state="JUMP", anim_time=self.anim_time, facing_right=True)
            # Jetpack effect below feet
            jet_y = py + 20
            jet_w = 8
            jet_h = 12
            pygame.draw.rect(surf, (30, 30, 60), (px - jet_w//2, jet_y, jet_w, jet_h))
            pygame.draw.rect(surf, C_MINT, (px - jet_w//2 + 1, jet_y + 1, jet_w - 2, jet_h - 2))
            # Jet flame
            flame_height = 6 + int(3 * math.sin(self.anim_time * 10.0))
            pygame.draw.polygon(surf, C_YELLOW, [
                (px, jet_y + jet_h),
                (px - 4, jet_y + jet_h + flame_height),
                (px + 4, jet_y + jet_h + flame_height)
            ])

        else:
            # Standard run cycle
            draw_pulse_character(surf, px, PLAYER_BASE_Y, scale=1.0, state="RUN", anim_time=self.anim_time, facing_right=True)
            # Speed lines when running fast
            if self.speed > 450:
                for i in range(3):
                    line_x = px - 20 - i*15
                    line_y = PLAYER_BASE_Y - 10 + i*5
                    length = 10 + int(5 * math.sin(self.anim_time * 5.0 + i))
                    pygame.draw.line(surf, C_MINT, (line_x, line_y), (line_x + length, line_y), 2)

    def draw_loading_screen(self, surf):
        """Draws a polished loading interface for Neon Rush."""
        # Dark background with vibrant gradient
        surf.fill(C_SLATE_DEEP)

        # Animated background elements
        # Moving grid lines
        grid_offset = (self.anim_time * 50) % 40
        for x in range(-20, SCREEN_WIDTH + 20, 40):
            pygame.draw.line(surf, (30, 30, 60), (x + grid_offset, 0), (x + grid_offset, SCREEN_HEIGHT), 1)
            pygame.draw.line(surf, (30, 30, 60), (0, x + grid_offset), (SCREEN_WIDTH, x + grid_offset), 1)

        # Floating geometric shapes
        for i in range(5):
            x = (SCREEN_WIDTH // 5) * (i + 1) + math.sin(self.anim_time * 0.5 + i) * 20
            y = 200 + math.cos(self.anim_time * 0.7 + i * 0.5) * 30
            size = 15 + math.sin(self.anim_time * 0.3 + i) * 5
            color = [
                (100, 200, 255),  # Blue
                (200, 100, 255),  # Purple
                (100, 255, 150),  # Mint
                (255, 200, 100),  # Orange
                (255, 100, 200),  # Pink
            ][i]
            alpha = int(100 + 100 * math.sin(self.anim_time * 0.2 + i))
            s = pygame.Surface((size*2, size*2), pygame.SRCALPHA)
            pygame.draw.polygon(s, (*color, alpha), [
                (size, 0), (size*2, size), (size, size*2), (0, size)
            ])
            surf.blit(s, (x - size, y - size))

        # Main loading box
        box_width = 500
        box_height = 300
        box_x = (SCREEN_WIDTH - box_width) // 2
        box_y = (SCREEN_HEIGHT - box_height) // 2

        # Outer glow
        glow_surf = pygame.Surface((box_width + 20, box_height + 20), pygame.SRCALPHA)
        pygame.draw.rect(glow_surf, (0, 0, 0, 100), (0, 0, box_width + 20, box_height + 20), border_radius=10)
        surf.blit(glow_surf, (box_x - 10, box_y - 10))

        # Main box
        draw_pixel_box(surf, pygame.Rect(box_x, box_y, box_width, box_height),
                      C_WHITE, border_color=C_BLUE_CARD, elevation=6)

        # Title
        title_txt = FONT_HUGE.render("RETROPULSE ARCADE", True, (244, 114, 182))
        surf.blit(title_txt, (box_x + box_width//2 - title_txt.get_width()//2, box_y + 30))

        # Game title
        game_title_txt = FONT_TITLE.render("NEON RUSH", True, C_MINT)
        surf.blit(game_title_txt, (box_x + box_width//2 - game_title_txt.get_width()//2, box_y + 100))

        # Subtitle
        sub_txt = FONT_CARD.render("RUN THE NEON GRID", True, C_SLATE_DARK)
        surf.blit(sub_txt, (box_x + box_width//2 - sub_txt.get_width()//2, box_y + 140))

        # Animated progress bar
        progress = min(1.0, self.loading_timer / self.loading_duration)
        bar_width = 300
        bar_height = 20
        bar_x = box_x + (box_width - bar_width) // 2
        bar_y = box_y + 180

        # Background bar
        pygame.draw.rect(surf, (30, 30, 60), (bar_x, bar_y, bar_width, bar_height), border_radius=10)
        # Progress fill
        if progress > 0:
            fill_width = int(bar_width * progress)
            # Gradient effect
            for i in range(fill_width):
                ratio = i / bar_width
                r = int(100 + 155 * ratio)
                g = int(100 + 155 * ratio)
                b = 255
                pygame.draw.line(surf, (r, g, b),
                               (bar_x + i, bar_y),
                               (bar_x + i, bar_y + bar_height))
        # Bar outline
        pygame.draw.rect(surf, C_WHITE, (bar_x, bar_y, bar_width, bar_height), 2, border_radius=10)

        # Progress percentage
        percent_txt = FONT_BODY.render(f"{int(progress * 100)}%", True, C_WHITE)
        surf.blit(percent_txt, (bar_x + bar_width//2 - percent_txt.get_width()//2, bar_y + bar_height + 10))

        # Status messages
        status_messages = [
            "INITIALIZING NEON GRID...",
            "LOADING CITY...",
            "CALIBRATING LANES...",
            "CHARGING PULSE...",
            "SYNCING WITH RETROPULSE...",
            "READY!"
        ]
        msg_index = min(len(status_messages) - 1, int(progress * len(status_messages)))
        status_txt = FONT_BODY.render(status_messages[msg_index], True, C_SLATE_DARK)
        surf.blit(status_txt, (box_x + box_width//2 - status_txt.get_width()//2, box_y + 220))

        # Animated neon particles
        for i in range(8):
            x = box_x + 50 + i * 50 + math.sin(self.anim_time * 2 + i) * 10
            y = box_y + box_height - 30 + math.cos(self.anim_time * 1.5 + i) * 10
            size = 3 + math.sin(self.anim_time * 3 + i) * 2
            color = [
                C_MINT, C_BLUE_CARD, C_YELLOW, C_CORAL,
                (255, 100, 200), (100, 200, 255), (200, 100, 255), (100, 255, 150)
            ][i % 8]
            pygame.draw.circle(surf, color, (int(x), int(y)), int(size))
            # Glow
            pygame.draw.circle(surf, (*color, 100), (int(x), int(y)), int(size) + 2, 1)

    def draw_start_overlay(self, surf):
        """Draws an arcade cyberpunk intro card."""
        dim_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        dim_surf.fill((15, 23, 42, 160))
        surf.blit(dim_surf, (0, 0))

        box = pygame.Rect(SCREEN_WIDTH // 2 - 220, 140, 440, 340)
        draw_pixel_box(surf, box, C_WHITE, border_color=C_BLUE_CARD, elevation=6)

        title_txt = FONT_HUGE.render("NEON RUSH", True, (244, 114, 182))
        surf.blit(title_txt, (box.centerx - title_txt.get_width() // 2, box.y + 24))

        sub_txt = FONT_CARD.render("High-Speed 3-Lane Cyber Run", True, C_SLATE_DARK)
        surf.blit(sub_txt, (box.centerx - sub_txt.get_width() // 2, box.y + 86))

        # Instructions list
        lines = [
            ("A / D or LEFT / RIGHT", "Switch Lanes"),
            ("W / UP or SPACE", "Jump Over Low Barriers"),
            ("S / DOWN", "Slide Under High Lasers")
        ]
        for idx, (ctrl, desc) in enumerate(lines):
            cy = box.y + 130 + (idx * 38)
            draw_pixel_box(surf, pygame.Rect(box.x + 24, cy, 170, 30), C_SLATE_DEEP, border_color=C_SLATE_DARK, elevation=2)
            c_s = FONT_BODY.render(ctrl, True, C_YELLOW)
            d_s = FONT_BODY.render(desc, True, C_SLATE_DARK)
            surf.blit(c_s, (box.x + 30, cy + 6))
            surf.blit(d_s, (box.x + 205, cy + 6))

        # Start CTA Pill
        prompt_box = pygame.Rect(box.centerx - 130, box.bottom - 54, 260, 42)
        pulse_col = C_MINT if int(self.anim_time * 4.0) % 2 == 0 else (110, 231, 183)
        draw_pixel_box(surf, prompt_box, pulse_col, border_color=C_SLATE_DARK, elevation=3)
        cta_txt = FONT_CARD.render("PRESS SPACE TO START", True, C_SLATE_DARK)
        surf.blit(cta_txt, (prompt_box.centerx - cta_txt.get_width() // 2, prompt_box.centery - cta_txt.get_height() // 2))

    def draw_game_over_overlay(self, surf):
        """Draws stylish game over screen with stats and restart hints."""
        dim_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        dim_surf.fill((15, 23, 42, 170))
        surf.blit(dim_surf, (0, 0))

        box = pygame.Rect(SCREEN_WIDTH // 2 - 180, 160, 360, 310)
        draw_pixel_box(surf, box, C_WHITE, border_color=C_CORAL, elevation=6)

        t_txt = FONT_TITLE.render("GAME OVER", True, C_DANGER)
        surf.blit(t_txt, (box.centerx - t_txt.get_width() // 2, box.y + 24))

        s_txt = FONT_CARD.render(f"Final Score: {self.score}", True, C_SLATE_DARK)
        surf.blit(s_txt, (box.centerx - s_txt.get_width() // 2, box.y + 90))

        d_txt = FONT_BODY.render(f"Distance Traveled: {int(self.distance)}m", True, (100, 116, 139))
        surf.blit(d_txt, (box.centerx - d_txt.get_width() // 2, box.y + 128))

        c_txt = FONT_BODY.render(f"Max Combo: x{self.combo}", True, C_GOLD)
        surf.blit(c_txt, (box.centerx - c_txt.get_width() // 2, box.y + 154))

        # Tip based on gameplay
        tip_txt = FONT_BODY.render("Tip: Slide (S/DOWN) under high pink lasers!", True, C_SLATE_DARK)
        surf.blit(tip_txt, (box.centerx - tip_txt.get_width() // 2, box.y + 200))

        # Restart hint
        hint_box = pygame.Rect(box.centerx - 110, box.y + 244, 220, 42)
        draw_pixel_box(surf, hint_box, C_MINT, border_color=C_SLATE_DARK, elevation=2)
        h_txt = FONT_CARD.render("PLAY AGAIN (SPACE)", True, C_SLATE_DARK)
        surf.blit(h_txt, (hint_box.centerx - h_txt.get_width() // 2, hint_box.centery - h_txt.get_height() // 2))

    def draw(self, surf):
        """Renders the complete game scene."""
        # Handle loading screen transition
        if self.game_state == "START":
            if not self.show_start_screen:
                # Still in loading phase
                self.loading_timer += 1/60.0  # Approximate dt, we'll use fixed 60 FPS for loading timer
                if self.loading_timer >= self.loading_duration:
                    self.show_start_screen = True
                self.draw_loading_screen(surf)
                return
            else:
                # Show start screen after loading
                self.draw_start_overlay(surf)
                return

        # 1. Background & Skyline
        self.draw_background(surf)

        # 2. Obstacles & Collectibles
        self.draw_entities(surf)

        # 3. Mascot Player Character
        self.draw_player(surf)

        # 4. Standard Minimal HUD
        draw_hud(surf, self.score, combo=self.combo)

        # 5. Boost indicator banner if active
        if self.speed_boost_timer > 0:
            b_box = pygame.Rect(SCREEN_WIDTH // 2 - 80, 18, 160, 32)
            draw_pixel_box(surf, b_box, C_YELLOW, border_color=C_SLATE_DARK, elevation=2)
            bt = FONT_HUD.render("TURBO BOOST!", True, C_SLATE_DARK)
            surf.blit(bt, (b_box.centerx - bt.get_width() // 2, b_box.centery - bt.get_height() // 2))

        # 6. State Overlays
        if self.game_over:
            self.draw_game_over_overlay(surf)
import pygame

SCREEN_WIDTH = 960
SCREEN_HEIGHT = 640
FPS = 60

# Palette
C_SKY_DEEP    = (79, 172, 254)
C_SKY_LIGHT   = (194, 233, 251)
C_CREAM       = (254, 252, 232)
C_YELLOW      = (253, 224, 71)
C_CORAL       = (249, 115, 22)
C_CORAL_DARK  = (194, 65, 12)
C_PINK        = (244, 114, 182)
C_MINT        = (74, 222, 128)
C_GREEN_DARK  = (22, 101, 52)
C_PURPLE      = (168, 85, 247)
C_BLUE_CARD   = (56, 189, 248)
C_SLATE_DARK  = (30, 41, 59)
C_SLATE_DEEP  = (15, 23, 42)
C_WHITE       = (255, 255, 255)
C_ROAD        = (51, 65, 85)
C_ROAD_LINE   = (241, 245, 249)
C_GOLD        = (245, 158, 11)
C_BROWN       = (180, 83, 9)
C_GRAY        = (120, 113, 108)
C_LIGHT_GRAY  = (203, 213, 225)
C_DANGER      = (239, 68, 68)
C_SUN         = (254, 240, 138)

# Exact 10 Games
ALL_GAME_KEYS = [
    "flash", "dodge", "spot_it", "archery", "traffic",
    "memory", "block_drop", "sky_dash", "find_secret", "color_chaos"
]

GAME_TITLES = {
    "flash": "FLASH!",
    "dodge": "DON'T GET HIT!",
    "spot_it": "SPOT IT!",
    "archery": "ARCHERY",
    "traffic": "TRAFFIC RIDER",
    "memory": "MEMORY PUZZLE",
    "block_drop": "BLOCK DROP",
    "sky_dash": "SKY DASH",
    "find_secret": "FIND THE SECRET",
    "color_chaos": "COLOR CHAOS"
}

pygame.font.init()

def get_font(size, bold=True):
    for name in ["Arial Rounded MT Bold", "Trebuchet MS", "DejaVu Sans", "Arial"]:
        try:
            f = pygame.font.SysFont(name, size, bold=bold)
            if f:
                return f
        except Exception:
            continue
    return pygame.font.Font(None, size)

FONT_TITLE = get_font(42, bold=True)
FONT_CARD  = get_font(20, bold=True)
FONT_BODY  = get_font(16, bold=False)
FONT_HUD   = get_font(20, bold=True)
FONT_HUGE  = get_font(58, bold=True)

def draw_pixel_box(surf, rect, bg_color, border_color=C_SLATE_DARK, shadow_color=(148, 163, 184), border_w=3, elevation=4):
    x, y, w, h = rect.x, rect.y, rect.width, rect.height
    if elevation > 0:
        pygame.draw.rect(surf, shadow_color, (x, y + elevation, w, h), border_radius=12)
    pygame.draw.rect(surf, bg_color, (x, y, w, h), border_radius=12)
    h_surf = pygame.Surface((max(1, w - border_w * 2), 4), pygame.SRCALPHA)
    h_surf.fill((255, 255, 255, 80))
    surf.blit(h_surf, (x + border_w, y + border_w))
    if border_color and border_w > 0:
        pygame.draw.rect(surf, border_color, (x, y, w, h), width=border_w, border_radius=12)

def draw_hud(surf, score, time_left=None, combo=None, lives=None, ammo=None, round_num=None):
    hud_bg = pygame.Rect(18, 14, 180, 42)
    draw_pixel_box(surf, hud_bg, C_WHITE, border_color=C_SLATE_DARK, elevation=3)
    s_txt = FONT_HUD.render(f"SCORE: {score}", True, C_SLATE_DARK)
    surf.blit(s_txt, (hud_bg.x + 16, hud_bg.y + 10))

    if combo is not None and combo > 1:
        c_bg = pygame.Rect(208, 14, 140, 42)
        draw_pixel_box(surf, c_bg, C_YELLOW, border_color=C_CORAL_DARK, elevation=3)
        c_txt = FONT_HUD.render(f"x{combo} COMBO!", True, C_SLATE_DARK)
        surf.blit(c_txt, (c_bg.x + 12, c_bg.y + 10))

    if round_num is not None:
        r_bg = pygame.Rect(358, 14, 130, 42)
        draw_pixel_box(surf, r_bg, C_MINT, border_color=C_GREEN_DARK, elevation=3)
        r_txt = FONT_HUD.render(f"STAGE {round_num}", True, C_SLATE_DARK)
        surf.blit(r_txt, (r_bg.x + 12, r_bg.y + 10))

    if time_left is not None:
        t_bg = pygame.Rect(SCREEN_WIDTH - 180, 14, 162, 42)
        t_col = (254, 202, 202) if time_left <= 5 else C_CREAM
        draw_pixel_box(surf, t_bg, t_col, border_color=C_SLATE_DARK, elevation=3)
        t_txt = FONT_HUD.render(f"TIME: {int(time_left)}s", True, C_SLATE_DARK)
        surf.blit(t_txt, (t_bg.x + 22, t_bg.y + 10))

    if ammo is not None:
        a_bg = pygame.Rect(SCREEN_WIDTH - 180, 14, 162, 42)
        draw_pixel_box(surf, a_bg, C_CREAM, border_color=C_SLATE_DARK, elevation=3)
        a_txt = FONT_HUD.render(f"ARROWS: {ammo}", True, C_SLATE_DARK)
        surf.blit(a_txt, (a_bg.x + 16, a_bg.y + 10))

    if lives is not None:
        l_bg = pygame.Rect(SCREEN_WIDTH - 180, 14, 162, 42)
        draw_pixel_box(surf, l_bg, C_CREAM, border_color=C_SLATE_DARK, elevation=3)
        for i in range(3):
            lx = l_bg.x + 26 + i * 40
            ly = l_bg.y + 20
            col = (239, 68, 68) if i < lives else (203, 213, 225)
            pygame.draw.circle(surf, col, (lx - 5, ly - 4), 6)
            pygame.draw.circle(surf, col, (lx + 5, ly - 4), 6)
            pygame.draw.polygon(surf, col, [(lx - 10, ly - 3), (lx + 10, ly - 3), (lx, ly + 8)])
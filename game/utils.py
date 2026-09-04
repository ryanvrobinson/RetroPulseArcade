"""
Geometry, procedural UI drawing, and text rendering helpers.
"""
import pygame
import math

_font_cache = {}

def get_font(size, bold=False):
    key = (size, bold)
    if key not in _font_cache:
        # Fallback to system font safely
        _font_cache[key] = pygame.font.SysFont("Trebuchet MS", size, bold=bold)
    return _font_cache[key]

def draw_rounded_rect(surface, color, rect, radius=12, border_width=0, border_color=None):
    rect = pygame.Rect(rect)
    radius = min(radius, rect.width // 2, rect.height // 2)
    pygame.draw.rect(surface, color, rect, border_radius=radius)
    if border_width > 0 and border_color:
        pygame.draw.rect(surface, border_color, rect, width=border_width, border_radius=radius)

def draw_text(surface, text, x, y, font_size=24, color=(255, 255, 255), align="center", bold=False, shadow=False):
    font = get_font(font_size, bold=bold)
    text_surf = font.render(str(text), True, color)
    rect = text_surf.get_rect()

    if align == "center":
        rect.center = (x, y)
    elif align == "left":
        rect.midleft = (x, y)
    elif align == "right":
        rect.midright = (x, y)
    elif align == "topleft":
        rect.topleft = (x, y)

    if shadow:
        shadow_surf = font.render(str(text), True, (10, 10, 15))
        shadow_rect = rect.copy()
        shadow_rect.x += 2
        shadow_rect.y += 2
        surface.blit(shadow_surf, shadow_rect)

    surface.blit(text_surf, rect)
    return rect

def draw_radial_glow(surface, center, radius, color, max_alpha=120):
    glow_surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
    for r in range(radius, 0, -max(1, radius // 8)):
        alpha = int(max_alpha * (1.0 - (r / radius)))
        c = (color[0], color[1], color[2], alpha)
        pygame.draw.circle(glow_surf, c, (radius, radius), r)
    surface.blit(glow_surf, (center[0] - radius, center[1] - radius), special_flags=pygame.BLEND_ALPHA_SDL2)

def lerp(start, end, factor):
    return start + (end - start) * factor

def ease_out_cubic(t):
    t = max(0.0, min(1.0, t))
    return 1.0 - math.pow(1.0 - t, 3)

def ease_out_elastic(t):
    if t <= 0: return 0.0
    if t >= 1: return 1.0
    p = 0.3
    return math.pow(2, -10 * t) * math.sin((t - p / 4.0) * (2.0 * math.pi) / p) + 1.0
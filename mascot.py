import math
import pygame
from constants import (
    C_SLATE_DARK, C_CORAL, C_CORAL_DARK, C_WHITE,
    C_BLUE_CARD, C_YELLOW, C_CREAM
)

def draw_pulse_character(surf, cx, cy, scale=1.0, state="IDLE", anim_time=0.0, facing_right=True):
    bob = math.sin(anim_time * 6.0) * 3.0 * scale
    squash_x, squash_y = 1.0, 1.0

    if state in ("WALK", "RUN"):
        bob = abs(math.sin(anim_time * 10.0)) * 5.0 * scale
        squash_x = 1.0 + math.sin(anim_time * 10.0) * 0.08
        squash_y = 1.0 - math.sin(anim_time * 10.0) * 0.08
    elif state == "JUMP":
        squash_x, squash_y = 0.85, 1.15
        bob = -10 * scale
    elif state == "HIT":
        squash_x, squash_y = 1.25, 0.75
        bob = 6 * scale

    center_y = cy - bob
    leg_offset = math.sin(anim_time * 10.0) * 8.0 * scale if state in ("WALK", "RUN") else 0
    shoe_l_x = cx - 11 * scale - leg_offset
    shoe_r_x = cx + 11 * scale + leg_offset
    shoe_y = center_y + 24 * scale

    for sx in (shoe_l_x, shoe_r_x):
        pygame.draw.rect(surf, C_SLATE_DARK, (sx - 7 * scale, shoe_y, 14 * scale, 10 * scale), border_radius=3)
        pygame.draw.rect(surf, C_CORAL, (sx - 6 * scale, shoe_y + 1 * scale, 12 * scale, 6 * scale), border_radius=2)
        pygame.draw.rect(surf, C_WHITE, (sx - 6 * scale, shoe_y + 7 * scale, 12 * scale, 2 * scale))

    body_w = 28 * scale * squash_x
    body_h = 24 * scale * squash_y
    body_rect = pygame.Rect(cx - body_w / 2, center_y + 3 * scale, body_w, body_h)
    pygame.draw.rect(surf, C_SLATE_DARK, body_rect, border_radius=int(6 * scale))
    pygame.draw.rect(surf, C_BLUE_CARD, (body_rect.x + 2, body_rect.y + 2, body_rect.w - 4, body_rect.h - 4), border_radius=int(5 * scale))
    pygame.draw.rect(surf, C_YELLOW, (cx - 7 * scale, center_y + 8 * scale, 3 * scale, 3 * scale))
    pygame.draw.rect(surf, C_YELLOW, (cx + 4 * scale, center_y + 8 * scale, 3 * scale, 3 * scale))

    arm_swing = math.cos(anim_time * 10.0) * 7.0 * scale if state in ("WALK", "RUN") else 0
    if state == "VICTORY":
        pygame.draw.circle(surf, C_CREAM, (int(cx - 16 * scale), int(center_y - 6 * scale)), int(4.5 * scale))
        pygame.draw.circle(surf, C_CREAM, (int(cx + 16 * scale), int(center_y - 6 * scale)), int(4.5 * scale))
    else:
        pygame.draw.circle(surf, C_CREAM, (int(cx - 16 * scale), int(center_y + 13 * scale - arm_swing)), int(4.5 * scale))
        pygame.draw.circle(surf, C_CREAM, (int(cx + 16 * scale), int(center_y + 13 * scale + arm_swing)), int(4.5 * scale))

    head_r = 17 * scale
    head_center = (int(cx), int(center_y - 12 * scale))
    pygame.draw.circle(surf, C_SLATE_DARK, head_center, int(head_r + 1))
    pygame.draw.circle(surf, (254, 240, 199), head_center, int(head_r))

    cap_rect = pygame.Rect(cx - 17 * scale, center_y - 27 * scale, 34 * scale, 12 * scale)
    pygame.draw.rect(surf, C_CORAL_DARK, cap_rect, border_radius=3)
    pygame.draw.rect(surf, C_CORAL, (cap_rect.x + 2, cap_rect.y + 2, cap_rect.w - 4, cap_rect.h - 4), border_radius=2)
    brim_x = cx - 12 * scale if not facing_right else cx - 4 * scale
    pygame.draw.rect(surf, C_SLATE_DARK, (brim_x, center_y - 18 * scale, 18 * scale, 5 * scale), border_radius=2)
    pygame.draw.rect(surf, C_CORAL, (brim_x + 1, center_y - 17 * scale, 16 * scale, 3 * scale))

    blink = (math.sin(anim_time * 2.5) > 0.94) and (state != "SURPRISED")
    eye_offset = 2 * scale if facing_right else -2 * scale
    if state == "HIT":
        for ex in [cx - 6 * scale, cx + 6 * scale]:
            pygame.draw.line(surf, C_SLATE_DARK, (ex - 3, head_center[1] - 3), (ex + 3, head_center[1] + 3), 2)
            pygame.draw.line(surf, C_SLATE_DARK, (ex - 3, head_center[1] + 3), (ex + 3, head_center[1] - 3), 2)
    elif blink:
        pygame.draw.line(surf, C_SLATE_DARK, (cx - 8 * scale, head_center[1]), (cx - 3 * scale, head_center[1]), 2)
        pygame.draw.line(surf, C_SLATE_DARK, (cx + 3 * scale, head_center[1]), (cx + 8 * scale, head_center[1]), 2)
    else:
        er = 4.5 * scale if state != "SURPRISED" else 6.0 * scale
        for ex in [cx - 6 * scale + eye_offset, cx + 6 * scale + eye_offset]:
            pygame.draw.circle(surf, C_WHITE, (int(ex), head_center[1] - 1), int(er))
            px = 1 * scale if facing_right else -1 * scale
            pygame.draw.circle(surf, C_SLATE_DARK, (int(ex + px), head_center[1] - 1), int(2.2 * scale))
            pygame.draw.rect(surf, C_WHITE, (int(ex + px - 1), head_center[1] - 3, 2, 2))

    if state in ("HAPPY", "VICTORY"):
        pygame.draw.arc(surf, C_SLATE_DARK, (cx - 5 * scale, head_center[1] + 2 * scale, 10 * scale, 6 * scale), 3.14, 0, 2)
    elif state == "SURPRISED":
        pygame.draw.circle(surf, C_SLATE_DARK, (int(cx), int(head_center[1] + 5 * scale)), int(3 * scale))
    elif state == "WORRIED":
        pygame.draw.arc(surf, C_SLATE_DARK, (cx - 5 * scale, head_center[1] + 5 * scale, 10 * scale, 5 * scale), 0, 3.14, 2)
    else:
        pygame.draw.arc(surf, C_SLATE_DARK, (cx - 4 * scale, head_center[1] + 3 * scale, 8 * scale, 5 * scale), 3.14, 0, 2)
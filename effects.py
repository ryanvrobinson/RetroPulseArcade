import math
import random
import pygame
from constants import C_YELLOW, FONT_CARD

particles = []
score_popups = []

class PixelParticle:
    def __init__(self, x, y, color, size, vx, vy, life, shape="square"):
        self.x, self.y = x, y
        self.color, self.size, self.max_size = color, size, size
        self.vx, self.vy = vx, vy
        self.life, self.max_life = life, life
        self.shape = shape

    def update(self, dt):
        self.x += self.vx * dt * 60
        self.y += self.vy * dt * 60
        self.vy += 0.1 * dt * 60
        self.life -= dt
        self.size = max(0, self.max_size * (self.life / self.max_life))

    def draw(self, surf):
        if self.size <= 0: return
        s = int(self.size)
        if self.shape == "square":
            pygame.draw.rect(surf, self.color, (int(self.x), int(self.y), s, s))
        elif self.shape == "star":
            pts = [
                (self.x, self.y - s), (self.x + s * 0.35, self.y - s * 0.35),
                (self.x + s, self.y), (self.x + s * 0.35, self.y + s * 0.35),
                (self.x, self.y + s), (self.x - s * 0.35, self.y + s * 0.35),
                (self.x - s, self.y), (self.x - s * 0.35, self.y - s * 0.35)
            ]
            pygame.draw.polygon(surf, self.color, pts)
        else:
            pygame.draw.circle(surf, self.color, (int(self.x), int(self.y)), s)

def spawn_burst(x, y, color, count=12, shape="square"):
    for _ in range(count):
        speed = random.uniform(2.0, 5.0)
        angle = random.uniform(0, 2 * math.pi)
        vx = math.cos(angle) * speed
        vy = math.sin(angle) * speed - 1.2
        life = random.uniform(0.35, 0.65)
        size = random.uniform(3, 7)
        particles.append(PixelParticle(x, y, color, size, vx, vy, life, shape))

class ScorePopup:
    def __init__(self, text, x, y, color=C_YELLOW):
        self.text = text
        self.x, self.y = x, y
        self.color = color
        self.life = self.max_life = 0.8

    def update(self, dt):
        self.life -= dt
        self.y -= 35 * dt

    def draw(self, surf):
        if self.life <= 0: return
        alpha = int(255 * (self.life / self.max_life))
        font_s = FONT_CARD.render(self.text, True, self.color)
        font_s.set_alpha(alpha)
        surf.blit(font_s, (self.x - font_s.get_width() // 2, self.y))
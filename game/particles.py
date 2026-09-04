"""
High-performance particle burst and ambient dust system.
"""
import pygame
import random
import math

class Particle:
    __slots__ = ('x', 'y', 'vx', 'vy', 'color', 'size', 'original_size', 'life', 'max_life')

    def __init__(self, x, y, vx, vy, color, size, life):
        self.x = float(x)
        self.y = float(y)
        self.vx = float(vx)
        self.vy = float(vy)
        self.color = color
        self.size = float(size)
        self.original_size = float(size)
        self.life = float(life)
        self.max_life = float(life)

    def update(self, dt):
        self.life -= dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vx *= (1.0 - 1.5 * dt)
        self.vy *= (1.0 - 1.5 * dt)
        ratio = max(0.0, self.life / self.max_life)
        self.size = self.original_size * ratio
        return self.life > 0

    def draw(self, surface):
        if self.size < 0.8:
            return
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), int(self.size))


class ParticleSystem:
    def __init__(self):
        self.particles = []

    def emit_burst(self, x, y, count=20, colors=None, speed_range=(40, 220), size_range=(2, 6), life_range=(0.3, 0.7)):
        if colors is None:
            colors = [(0, 240, 255), (255, 0, 128), (255, 255, 255)]
        for _ in range(count):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(*speed_range)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            col = random.choice(colors)
            size = random.uniform(*size_range)
            life = random.uniform(*life_range)
            self.particles.append(Particle(x, y, vx, vy, col, size, life))

    def emit_ring(self, x, y, count=16, color=(255, 255, 255), speed=140, size=3, life=0.4):
        for i in range(count):
            angle = (2 * math.pi / count) * i
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            self.particles.append(Particle(x, y, vx, vy, color, size, life))

    def update(self, dt):
        self.particles = [p for p in self.particles if p.update(dt)]

    def draw(self, surface):
        for p in self.particles:
            p.draw(surface)

    def clear(self):
        self.particles.clear()
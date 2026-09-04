"""
Frame-rate independent tweening and animated value tracking.
"""
from game.utils import lerp, ease_out_cubic, ease_out_elastic

class Tween:
    def __init__(self, start, target, duration, easing="cubic"):
        self.start = float(start)
        self.target = float(target)
        self.current = float(start)
        self.duration = max(0.001, float(duration))
        self.elapsed = 0.0
        self.finished = False
        self.easing = easing

    def update(self, dt):
        if self.finished:
            return self.target
        self.elapsed += dt
        t = min(1.0, self.elapsed / self.duration)
        
        if self.easing == "elastic":
            factor = ease_out_elastic(t)
        elif self.easing == "cubic":
            factor = ease_out_cubic(t)
        else:
            factor = t
            
        self.current = lerp(self.start, self.target, factor)
        if t >= 1.0:
            self.current = self.target
            self.finished = True
        return self.current

    def reset(self, start=None, target=None):
        if start is not None:
            self.start = float(start)
            self.current = float(start)
        if target is not None:
            self.target = float(target)
        self.elapsed = 0.0
        self.finished = False


class FloatingText:
    def __init__(self, text, x, y, color=(255, 255, 255), size=24, duration=0.8, vy=-60):
        self.text = text
        self.x = float(x)
        self.y = float(y)
        self.color = color
        self.size = size
        self.duration = duration
        self.lifetime = 0.0
        self.vy = vy
        self.dead = False

    def update(self, dt):
        self.lifetime += dt
        self.y += self.vy * dt
        if self.lifetime >= self.duration:
            self.dead = True

    def draw(self, surface):
        from game.utils import get_font
        progress = self.lifetime / self.duration
        alpha = int(255 * (1.0 - progress))
        if alpha <= 0:
            return
            
        font = get_font(self.size, bold=True)
        txt = font.render(self.text, True, self.color)
        txt.set_alpha(alpha)
        r = txt.get_rect(center=(int(self.x), int(self.y)))
        surface.blit(txt, r)
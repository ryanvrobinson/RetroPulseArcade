import math
import random
import array
import pygame
from tournament import settings_manager

AUDIO_ENABLED = False
try:
    pygame.mixer.pre_init(44100, -16, 2, 512)
    pygame.mixer.init()
    AUDIO_ENABLED = True
except Exception as e:
    print(f"[Audio] Running in fallback silent mode: {e}")

SOUNDS = {}
if AUDIO_ENABLED:
    def make_sound(freq=440.0, duration=0.1, wave="sine", decay=True):
        sample_rate = 44100
        n_samples = int(sample_rate * duration)
        buf = array.array('h')
        for i in range(n_samples):
            t = float(i) / sample_rate
            env = (1.0 - (i / n_samples)) if decay else 1.0
            if wave == "sine":
                val = math.sin(2.0 * math.pi * freq * t)
            elif wave == "square":
                val = 1.0 if math.sin(2.0 * math.pi * freq * t) > 0 else -1.0
            else:
                val = (random.random() * 2.0 - 1.0)
            sample = int(val * env * 14000)
            buf.append(sample)
            buf.append(sample)
        return pygame.mixer.Sound(buffer=buf)

    try:
        SOUNDS["pop"] = make_sound(660, 0.08, "sine")
        SOUNDS["coin"] = make_sound(880, 0.12, "sine")
        SOUNDS["hit"] = make_sound(140, 0.22, "noise")
        SOUNDS["jump"] = make_sound(540, 0.15, "square")
        SOUNDS["celebrate"] = make_sound(784, 0.25, "sine")
        SOUNDS["wrong"] = make_sound(180, 0.22, "square")
        SOUNDS["shoot"] = make_sound(720, 0.1, "sine")
        SOUNDS["flap"] = make_sound(480, 0.09, "sine")
    except Exception:
        pass

def play_sound(name):
    if AUDIO_ENABLED and settings_manager.get("sound") and name in SOUNDS:
        try:
            SOUNDS[name].play()
        except Exception:
            pass
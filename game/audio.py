"""
Audio manager with automatic procedural fallback synthesizer so no sound file ever crashes the engine.
"""
import pygame
import math
import struct
import array

class AudioManager:
    def __init__(self):
        self.sound_enabled = True
        self.music_enabled = True
        self.sounds = {}
        self.initialized = False

        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
            self.initialized = True
            self._synthesize_soundtrack_effects()
        except Exception as e:
            print(f"[Audio] Audio device failed to initialize: {e}. Running silently.")
            self.initialized = False

    def _generate_tone(self, freq=440, duration=0.1, wave_type="sine", volume=0.5):
        if not self.initialized:
            return None
        sample_rate = 44100
        num_samples = int(sample_rate * duration)
        raw_data = array.array("h")
        for i in range(num_samples):
            t = float(i) / sample_rate
            env = 1.0 - (float(i) / num_samples) # envelope linear fade
            if wave_type == "sine":
                val = math.sin(2.0 * math.pi * freq * t)
            elif wave_type == "square":
                val = 1.0 if math.sin(2.0 * math.pi * freq * t) > 0 else -1.0
            elif wave_type == "saw":
                val = 2.0 * (t * freq - math.floor(0.5 + t * freq))
            else:
                val = 0.0
            sample = int(val * env * volume * 32767)
            raw_data.append(sample) # Left channel
            raw_data.append(sample) # Right channel
        return pygame.mixer.Sound(buffer=raw_data.tobytes())

    def _synthesize_soundtrack_effects(self):
        try:
            self.sounds["click"] = self._generate_tone(freq=880, duration=0.04, wave_type="sine", volume=0.3)
            self.sounds["hit"] = self._generate_tone(freq=620, duration=0.08, wave_type="square", volume=0.35)
            self.sounds["combo"] = self._generate_tone(freq=980, duration=0.12, wave_type="sine", volume=0.4)
            self.sounds["success"] = self._generate_tone(freq=1200, duration=0.18, wave_type="sine", volume=0.45)
            self.sounds["error"] = self._generate_tone(freq=180, duration=0.22, wave_type="square", volume=0.4)
            self.sounds["gameover"] = self._generate_tone(freq=140, duration=0.4, wave_type="saw", volume=0.5)
            self.sounds["powerup"] = self._generate_tone(freq=1320, duration=0.15, wave_type="sine", volume=0.45)
        except Exception as e:
            print(f"[Audio] Synthesizer warning: {e}")

    def play(self, sound_name):
        if not self.sound_enabled or not self.initialized:
            return
        snd = self.sounds.get(sound_name)
        if snd:
            try:
                snd.play()
            except Exception:
                pass

    def set_sound_enabled(self, enabled):
        self.sound_enabled = enabled

    def set_music_enabled(self, enabled):
        self.music_enabled = enabled
"""
Global settings, color palettes, and persistent configuration management.
"""
import json
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
CONFIG_FILE = os.path.join(DATA_DIR, "settings.json")
SCORES_FILE = os.path.join(DATA_DIR, "high_scores.json")

# Display
DEFAULT_WIDTH = 960
DEFAULT_HEIGHT = 600
FPS = 60
TITLE = "RETRO PULSE ARCADE HUB"

# Bright, Cheerful Arcade Palette - Redesigned Visual Identity
COLOR_BG = (240, 248, 255)      # Light sky blue/alice blue - bright background
COLOR_BG_SURFACE = (220, 235, 250)  # Slightly darker surface for cards
COLOR_BG_CARD = (255, 255, 255)     # Pure white for cards/containers
COLOR_ACCENT_CYAN = (64, 224, 255)   # Bright turquoise/aqua
COLOR_ACCENT_PINK = (255, 182, 193)  # Light coral/pink
COLOR_ACCENT_YELLOW = (255, 239, 166) # Warm cream/yellow
COLOR_ACCENT_GREEN = (152, 251, 152) # Mint green
COLOR_ACCENT_ORANGE = (255, 165, 0)   # Sunny orange
COLOR_ACCENT_PURPLE = (221, 160, 221) # Plum/light purple
COLOR_WHITE = (255, 255, 255)       # Pure white
COLOR_GRAY = (136, 136, 136)        # Medium gray
COLOR_DARK_GRAY = (105, 105, 105)   # Darker gray for text
COLOR_DANGER = (255, 99, 71)        # Tomato red (softer than bright red)

DEFAULT_SETTINGS = {
    "sound_on": True,
    "music_on": True,
    "effects_on": True,
    "fullscreen": False,
    "width": DEFAULT_WIDTH,
    "height": DEFAULT_HEIGHT
}

def load_settings():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR, exist_ok=True)
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                data = json.load(f)
                config = DEFAULT_SETTINGS.copy()
                config.update(data)
                return config
        except Exception:
            return DEFAULT_SETTINGS.copy()
    save_settings(DEFAULT_SETTINGS)
    return DEFAULT_SETTINGS.copy()

def save_settings(settings_dict):
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR, exist_ok=True)
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(settings_dict, f, indent=2)
    except Exception as e:
        print(f"[Settings] Failed to save settings: {e}")

def load_scores():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR, exist_ok=True)
    default_scores = {
        "reaction": {"high_score": 0, "best_combo": 0, "last_played": "Never"},
        "dodge": {"high_score": 0, "best_combo": 0, "last_played": "Never"},
        "observation": {"high_score": 0, "best_combo": 0, "last_played": "Never"}
    }
    if os.path.exists(SCORES_FILE):
        try:
            with open(SCORES_FILE, "r") as f:
                data = json.load(f)
                for k, v in default_scores.items():
                    if k not in data:
                        data[k] = v
                return data
        except Exception:
            return default_scores
    save_scores(default_scores)
    return default_scores

def save_scores(scores_dict):
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR, exist_ok=True)
    try:
        with open(SCORES_FILE, "w") as f:
            json.dump(scores_dict, f, indent=2)
    except Exception as e:
        print(f"[Scores] Failed to save scores: {e}")
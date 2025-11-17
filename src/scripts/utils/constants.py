# scripts/utils/constants.py
"""
Defines global constants, file paths, default settings, achievement definitions, and theme data.
"""

# Standard library imports
import os
import sys
from pathlib import Path

# --- VERSION ---
LAUNCHER_VERSION = "v0.3.1-alpha"

# ------------------- PATHS / CONFIG -------------------
if os.name == 'nt':
    USER_DIR = os.path.expandvars(r"%userprofile%")
else:
    USER_DIR = os.path.expanduser("~")

MGAIO_DIR = os.path.join(USER_DIR, "Documents", ".mgaio")
SAVE_PATH = os.path.join(MGAIO_DIR, "Saves")
SETTINGS_PATH = os.path.join(MGAIO_DIR, "settingsave.json")
CACHE_PATH = os.path.join(MGAIO_DIR, "game_meta_cache.json")
RECENTLY_PLAYED_PATH = os.path.join(MGAIO_DIR, "recently_played.json")

# Ensure necessary directories exist
os.makedirs(SAVE_PATH, exist_ok=True)

if getattr(sys, 'frozen', False):
    MINIGAMES_DIR = os.path.join(MGAIO_DIR, "minigames")
else:
    # Assuming 'scripts' is a subfolder of the project root
    _base_dir = Path(__file__).resolve().parent.parent
    MINIGAMES_DIR = os.path.join(_base_dir, "minigames")

os.makedirs(MINIGAMES_DIR, exist_ok=True)

REQUIRED_LIBS = ["pyinstaller"]  # Add more if needed


# ------------------- DEFAULT SETTINGS -------------------
DEFAULT_SETTINGS = {
    "theme": "light",
    "lock_password": "",
    "last_window_geometry": None,
    "recently_played": {},
    "show_tips": True,
    # gamification
    "coins": 0,
    "favorites": [],  # list of folder names
    "play_counts": {},  # folder_name -> count
    "achievements": {},  # id -> unlocked timestamp
    # feature toggles
    "mini_rewards": True,
    "achievements_panel": True,
    "favorites_only": False,
    "view_mode": "Grid",
    "grid_columns": 3,
    "card_size": "Normal",
    "daily_challenges": True,
    "easter_eggs": True,
    "particles": True,
    "sound_effects": True,
    "notifications": True,
    "font": {"family": "Segoe UI", "size": 11},  # default font
    "theme_colors": {"bg": "#FFFFFF", "fg": "#000000", "accent": "#0078D7"},  # light theme default
    "startup_script": "",  # path to optional custom startup script
    "auto_sort": "Alphabetical",  # default sorting method
    "compact_mode": False,  # default compact mode off
    "lock_on_startup": False,  # default no lock on startup
    "use_pin": False,  # default password over pin
    "auto_lock": 0,  # minutes before auto-lock
    "failed_attempts": 0,
    "lockout_until": 0,  # Unix timestamp until which login is blocked
    "max_attempts": 5,   # optional, max allowed attempts
    "lockout_duration": 60  # seconds to lock after max failed attempts
}

# Achievements definitions
ACHIEVEMENTS_DEF = {
    "first_play": {"name": "First Play", "desc": "Play any game for the first time", "coins": 5},
    "five_plays": {"name": "5 Plays", "desc": "Play games 5 times total", "coins": 10},
    "ten_plays": {"name": "10 Plays", "desc": "Play games 10 times total", "coins": 25},
    "favorite_creator": {"name": "Favorite Creator", "desc": "Mark a game as favorite", "coins": 7},
}

# THEMES
_base_dir = Path(__file__).resolve().parent.parent.parent
_theme_data_path = _base_dir / "data" / "themes"

THEMES = {
    "default": {"qss": str(_theme_data_path / "default.qss"), "bg": "#1e1e2f", "fg": "#ffffff"},
    "light":   {"qss": str(_theme_data_path / "light.qss"), "bg": "#f0f0f0", "fg": "#222222"},
    "dark":    {"qss": str(_theme_data_path / "dark.qss"), "bg": "#121212", "fg": "#ffffff"},
}
"""
Defines global constants, file paths, default settings, achievement definitions, and theme data.
"""

# Standard library imports
import os
import sys
import platform
from pathlib import Path
import psutil

# --- VERSION ---
LAUNCHER_VERSION = "v0.3.1-alpha"


# ------------------------------------------------------------
# DEVICE DETECTION
# ------------------------------------------------------------
def is_android_device() -> bool:
    """
    Detect Android (Pydroid 3) reliably using environment + psutil.
    """
    try:
        # Pydroid 3 signature
        if "PYDROID3" in os.environ.get("PATH", ""):
            return True

        # CPU architecture check
        cpu_arch = platform.machine().lower()
        if "arm" in cpu_arch or "aarch64" in cpu_arch:
            # Android usually has a battery
            battery = psutil.sensors_battery()
            if battery is not None:
                return True

        # Check process paths for /data or /storage
        for proc in psutil.process_iter(['exe']):
            try:
                exe = proc.info.get("exe") or ""
                if exe.startswith("/data") or exe.startswith("/storage"):
                    return True
            except Exception:
                pass
    except Exception:
        pass

    return False


# ------------------------------------------------------------
# PATHS / CONFIG
# ------------------------------------------------------------
if is_android_device():
    # Android user directory is usually /storage/emulated/0/Documents
    USER_DIR = "/storage/emulated/0/Documents"
else:
    # Windows or other OS
    USER_DIR = os.path.expandvars(r"%userprofile%") if os.name == 'nt' else os.path.expanduser("~")

# Core MGAIO directories
MGAIO_DIR = os.path.join(USER_DIR, "Documents", ".mgaio") if not is_android_device() else os.path.join(USER_DIR, ".mgaio")
SAVE_PATH = os.path.join(MGAIO_DIR, "Saves")
SETTINGS_PATH = os.path.join(MGAIO_DIR, "settingsave.json")
CACHE_PATH = os.path.join(MGAIO_DIR, "game_meta_cache.json")
RECENTLY_PLAYED_PATH = os.path.join(MGAIO_DIR, "recently_played.json")

# Ensure necessary directories exist
os.makedirs(SAVE_PATH, exist_ok=True)

# Minigames folder
if getattr(sys, 'frozen', False):
    MINIGAMES_DIR = os.path.join(MGAIO_DIR, "minigames")
else:
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
    "coins": 0,
    "favorites": [],
    "play_counts": {},
    "achievements": {},
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
    "font": {"family": "Segoe UI", "size": 11},
    "theme_colors": {"bg": "#FFFFFF", "fg": "#000000", "accent": "#0078D7"},
    "startup_script": "",
    "auto_sort": "Alphabetical",
    "compact_mode": False,
    "lock_on_startup": False,
    "use_pin": False,
    "auto_lock": 0,
    "failed_attempts": 0,
    "lockout_until": 0,
    "max_attempts": 5,
    "lockout_duration": 60
}

# ------------------- ACHIEVEMENTS -------------------
ACHIEVEMENTS_DEF = {
    "first_play": {"name": "First Play", "desc": "Play any game for the first time", "coins": 5},
    "five_plays": {"name": "5 Plays", "desc": "Play games 5 times total", "coins": 10},
    "ten_plays": {"name": "10 Plays", "desc": "Play games 10 times total", "coins": 25},
    "favorite_creator": {"name": "Favorite Creator", "desc": "Mark a game as favorite", "coins": 7},
}

# ------------------- THEMES -------------------
_base_dir = Path(__file__).resolve().parent.parent.parent
_theme_data_path = _base_dir / "data" / "themes"

THEMES = {
    "default": {"qss": str(_theme_data_path / "default.qss"), "bg": "#1e1e2f", "fg": "#ffffff"},
    "light":   {"qss": str(_theme_data_path / "light.qss"), "bg": "#f0f0f0", "fg": "#222222"},
    "dark":    {"qss": str(_theme_data_path / "dark.qss"), "bg": "#121212", "fg": "#ffffff"},
}

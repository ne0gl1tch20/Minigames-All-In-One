# scripts/managers/settings_manager.py
"""
Handles the global settings dictionary, loading from and saving to disk, 
and provides the current theme data.
"""

import os
import json
from ..utils.constants import SETTINGS_PATH, DEFAULT_SETTINGS, THEMES
from ..utils.file_io import safe_load_json

# Global variable to hold all application settings
settings = {}

# --- Initialization ---
try:
    if os.path.exists(SETTINGS_PATH):
        settings.update(safe_load_json(SETTINGS_PATH) or {})
        for k, v in DEFAULT_SETTINGS.items():
            settings.setdefault(k, v)
    else:
        settings.update(DEFAULT_SETTINGS.copy())
        os.makedirs(os.path.dirname(SETTINGS_PATH), exist_ok=True)
        with open(SETTINGS_PATH, 'w', encoding='utf-8') as f:
            json.dump(settings, f, indent=2)
except Exception as e:
    print(f"Error loading settings, using defaults: {e}")
    settings.update(DEFAULT_SETTINGS.copy())


# --- Theme Management ---
def get_current_theme():
    """Returns the current theme dictionary based on settings."""
    theme_name = settings.get('theme', 'default')
    return THEMES.get(theme_name, THEMES['default'])

# Initialize the theme variable based on loaded settings
theme = get_current_theme()


# --- Save Function ---
def save_settings():
    """Saves the current global settings dictionary to SETTINGS_PATH."""
    global theme
    try:
        os.makedirs(os.path.dirname(SETTINGS_PATH), exist_ok=True)
        theme = get_current_theme()
        settings['theme_colors'] = theme # Save theme colors for persistence/export
        with open(SETTINGS_PATH, 'w', encoding='utf-8') as f:
            json.dump(settings, f, indent=2)
    except Exception as e:
        print(f'Failed to save settings: {e}')

# Set theme based on loaded/default settings one last time
theme = get_current_theme()
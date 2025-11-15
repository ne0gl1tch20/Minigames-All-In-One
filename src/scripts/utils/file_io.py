# scripts/utils/file_io.py
"""
Utility functions for safe JSON loading/saving and managing 'recently played' data.
"""

import json
import os
from .constants import RECENTLY_PLAYED_PATH

def load_recently_played():
    """Loads recently played data from RECENTLY_PLAYED_PATH."""
    if os.path.exists(RECENTLY_PLAYED_PATH):
        try:
            with open(RECENTLY_PLAYED_PATH, "r") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_recently_played(data):
    """Saves recently played data to RECENTLY_PLAYED_PATH."""
    try:
        with open(RECENTLY_PLAYED_PATH, "w") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"Failed to save recently played data: {e}")


def safe_load_json(path):
    """Safely attempts to load and return a JSON file."""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return None
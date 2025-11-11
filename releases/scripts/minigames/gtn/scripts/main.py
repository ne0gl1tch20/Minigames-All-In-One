
#   ________                              ___________.__              _______               ___.                 
#  /  _____/ __ __   ____   ______ ______ \__    ___/|  |__   ____    \      \  __ __  _____\_ |__   ___________ 
# /   \  ___|  |  \_/ __ \ /  ___//  ___/   |    |   |  |  \_/ __ \   /   |   \|  |  \/     \| __ \_/ __ \_  __ \
# \    \_\  \  |  /\  ___/ \___ \ \___ \    |    |   |   Y  \  ___/  /    |    \  |  /  Y Y  \ \_\ \  ___/|  | \/
#  \______  /____/  \___  >____  >____  >   |____|   |___|  /\___  > \____|__  /____/|__|_|  /___  /\___  >__|   
#         \/            \/     \/     \/                  \/     \/          \/            \/    \/     \/       
#
# -------------------------------------------------------
# This is a number guessing game where the player tries 
# to guess a randomly chosen number within a certain 
# range. The game tracks the number of guesses, supports 
# different difficulty levels, has optional time-trial mode, 
# power-ups (like extra hints, retries, or revealing digits),
# and maintains save data for statistics, achievements, and
# leaderboard scores. It also features recovery for corrupted 
# save files and a GUI built with PySide6.
# -------------------------------------------------------

# --- Standard Library Imports ---
import sys                # System-specific parameters and functions
import base64             # Encode/decode data (e.g., settings or save files)
import random             # Random number generation for game logic
import json               # Reading/writing save files and configurations
import os                 # File system operations
import subprocess         # Running external processes or recovery scripts
import traceback          # Debugging: getting error stack traces
import time               # Timing operations, delays, or countdowns
import re                 # Regular expressions for text validation
import datetime           # Date and time handling
import threading          # Running background tasks (e.g., AI hint simulation)
from pathlib import Path  # File system paths management

import matplotlib
matplotlib.use('QtAgg')  # MUST be before QApplication

# --- PySide6 GUI Components ---
from PySide6.QtWidgets import (
    QApplication,        # Main application object
    QWidget,             # Base window/dialog class
    QLabel,              # Display text or images
    QPushButton,         # Clickable button
    QLineEdit,           # Single-line text input
    QVBoxLayout,         # Vertical layout manager
    QHBoxLayout,         # Horizontal layout manager
    QMessageBox,         # Pop-up dialogs for info/warnings/errors
    QComboBox,           # Drop-down selection box
    QCheckBox,           # Toggleable checkbox
    QDialog,             # Modal/non-modal dialog window
    QSpinBox,            # Number input with arrows
    QStackedWidget,      # Stack of widgets (like pages)
    QTableWidget,        # Table display widget
    QTableWidgetItem,    # Item inside a QTableWidget
    QHeaderView,         # Table header customization
    QGroupBox,           # Group of widgets with a title border
    QSlider,             # Slider for numeric input
    QFrame,              # Basic container widget with optional borders
    QColorDialog,        # Color selection dialog
    QScrollArea,         # Scrollable container
    QSizePolicy,         # Widget sizing behavior
    QGridLayout,         # Grid layout manager
    QMenuBar,            # Menu bar
    QInputDialog         # Simple input dialog (text/number)
)

from PySide6.QtGui import (
    QColor,              # Color representation
    QPalette,            # Color scheme for widgets
    QFont,               # Font object
    QFontDatabase,       # Access system fonts
    QIcon,               # Icons for buttons/windows
    QMovie,              # Animated GIFs
    QAction,             # Actions for menus/buttons
    QGuiApplication,     # Application-wide GUI control
    QFontDatabase,       # Font Database
    QIcon                # App icon
)

from PySide6.QtCore import (
    Qt,                  # Alignment, orientation, and other constants
    QTimer,              # Timer for periodic updates
    Signal,              # Custom signals for events
    QObject,             # Base class for PyQt/PySide objects
    QUrl,                # URL representation
    QPropertyAnimation,  # Animations for widget properties
    QEasingCurve,        # Smooth animation curves
    QSize,               # Size object for width/height
    QFileSystemWatcher   # Watch filesystem changes
)

from PySide6.QtMultimedia import (
    QMediaPlayer,        # Music or media player
    QAudioOutput,        # Audio output device
    QSoundEffect         # Short sound effects playback
)

# --- Matplotlib for charts and statistics ---
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas  
# Canvas widget for embedding matplotlib charts in PySide6 GUI

from matplotlib.figure import Figure  
# Figure object to create plots, subplots, and graphs

import matplotlib.animation as animation  
# For animating charts or updating plots in real-time

import numpy as np  
# Numerical computations, array handling, and data manipulation for charts

from rich.traceback import install # Enhanced tracebacks for debugging
install(show_locals=True)

try:
    import inspect
    # code that uses inspect
except Exception:
    pass  # skip in compiled exe

# --- Constants and Configuration ---

# User directory
USER_DIR = os.path.expandvars(r"%userprofile%")

# Base MGAIO save directory
MG_SAVE_DIR = Path(USER_DIR) / "Documents" / ".mgaio"

# App-specific save folder
APP_NAME = "GuessTheNumber"
SAVE_FOLDER = MG_SAVE_DIR / "Saves" / APP_NAME
SAVE_FOLDER.mkdir(parents=True, exist_ok=True)  # Ensure folder exists

# File paths
SETTINGS_FILE = SAVE_FOLDER / "settings.json"
LEADERBOARD_FILE = SAVE_FOLDER / "leaderboard.json"
GAME_STATE_FILE = SAVE_FOLDER / "game_state.json"
ACHIEVEMENTS_FILE = SAVE_FOLDER / "achievements.json"
STATISTICS_FILE = SAVE_FOLDER / "statistics.json"

ALL_FILES = {
    "leaderboard": LEADERBOARD_FILE,
    "settings": SETTINGS_FILE,
    "game_state": GAME_STATE_FILE,
    "achievements": ACHIEVEMENTS_FILE,
    "statistics": STATISTICS_FILE
}

# --- Message Templates ---
WIN_MESSAGES = [
    "🎉 Correct! You got it!", "👍 Nice! You found it!", "😎 Amazing!", "🥳 You're a genius!",
    "💯 Perfect!", "🎯 Bullseye!", "✨ Wow, spot on!", "🏆 You're a champ!", "🚀 Nailed it!",
    "🔥 On fire!", "😇 Legendary move!", "🌟 Superstar!", "🎵 Music to my ears!", "🍀 Lucky guess!",
    "🕺 Dance time! You got it!", "🥂 Cheers to that!", "🏅 Medal-worthy!", "🎬 Movie star move!",
    "🎡 Fun fact: You're awesome!", "🌈 Rainbow of correctness!", "🦄 Magical answer!",
    "💥 Boom! Right on!", "⚡ Lightning fast brain!", "🥇 Gold medal answer!", "🌊 Wave of genius!",
    "🎲 Lucky roll!", "🎨 Masterpiece guess!", "🍩 Sweet success!", "🎈 Up, up and correct!", "🪄 Abracadabra, right!",
    "🌞 Bright idea!", "🌻 Bloomed perfectly!", "🎯 Target achieved!", "🪂 Smooth landing!", "🎉 Party time!",
    "🏖️ Chill victory!", "🍹 Cheers!", "🌟 Star player!", "💫 Cosmic hit!", "🦚 Showstopper!", 
    "🥳 Celebration time!", "🏔️ Peak performance!", "🏎️ Fastest brain!", "🎷 Jazz hands!", "🪁 Soaring high!",
    "🎮 Game master!", "🍕 Slice of success!", "📚 Brainiac move!", "🏹 Sharp shot!", "🛡️ Defender of correctness!",
    "💌 Heartfelt win!", "🕹️ Level up!", "🏓 Ping pong precision!", "🎤 Mic drop!", "🥁 Drumroll please!", 
    "💎 Gem of an answer!", "🎨 Picasso move!", "🧩 Puzzle solved!", "🌊 Surfer's ride!", "🚁 Helicopter brain!",
    "🦄 Unicorn vibes!", "🎇 Fireworks!", "🏆 Trophy earned!"
]

LOSE_MESSAGES = [
    "Better luck next time!", "Game Over!", "Time's up!", "😢 Almost had it!", "💔 Not this time!",
    "😞 Oops, try again!", "⏰ Ran out of time!", "😟 Keep practicing!", "⚡ Don’t give up!", "🙁 So close!",
    "🍂 Missed it!", "🌪️ Swept away by time!", "🛑 Stop! Not yet!", "💨 Too fast, too slow!", "🚪 Door closed!",
    "🕳️ Fell short!", "🌑 Dark miss!", "🧩 Piece missing!", "🧊 Cold guess!", "🐢 Slow and missed!",
    "🥀 Oops, almost bloomed!", "💤 Snoozed too long!", "⚖️ Not balanced!", "🌀 Twisted answer!", "🕷️ Caught in error!",
    "🔥 Burned out!", "💣 Boom! Wrong!", "🏚️ House of mistakes!", "🎭 Wrong act!", "💧 Slipped away!",
    "🌧️ Rainy day guess!", "🌊 Drowned in error!", "🧨 Explosion of wrong!", "🛶 Capsized!", "🦦 Slipped past!",
    "🕰️ Out of time!", "💨 Fast fail!", "🥺 Close but no cigar!", "🪨 Rock bottom!", "🐌 Slowpoke mistake!",
    "🩹 Ouch, that hurts!", "🪤 Caught in the trap!", "🪁 Drifted away!", "🚫 Blocked!", "🔒 Locked out!",
    "🪣 Bucket missed!", "⚡ Shocked by error!", "🏔️ Fell from the peak!", "🎢 Rollercoaster fail!", "🪄 Magic fizzled!",
    "🌪️ Tornado of wrong!", "🛸 UFO missed!", "🐉 Dragon burned!", "💨 Air slip!", "🕷️ Webbed in mistake!",
    "💀 Skull crash!", "🩸 Blew it!", "🦹 Villain won!", "🎃 Spooky fail!", "🦨 Stinky mistake!"
]

INCORRECT_MESSAGES = [
    "❌ Incorrect, try again!", "😅 Nope, try another one!", "😬 Not quite!", "🤔 Hmm, not quite!",
    "🙃 Almost, but nope!", "😮 Try thinking differently!", "💡 Nope, keep guessing!", "😓 Wrong, try once more!",
    "🧐 Not the answer!", "😖 Keep going, you got this!", "🍎 Not the right fruit!", "🏀 Missed the hoop!",
    "🎯 Aim better!", "🚀 Not launched correctly!", "🧩 Wrong puzzle piece!", "💎 Not sparkling yet!", 
    "🪁 Flying off course!", "🌪️ Twisted wrong!", "🎢 Up and down, but nope!", "🛸 Not landed yet!",
    "🦋 Fluttered away!", "🥨 Twisted pretzel guess!", "🧸 Cute but wrong!", "🎃 Spooky miss!", "🪐 Wrong orbit!",
    "🎹 Off-key!", "🕰️ Time's off!", "🏔️ Almost there, but no peak!", "🌊 Wave crashed!", "🛶 Capsized!",
    "🍌 Slipped on banana!", "🪄 Magic misfire!", "🎈 Balloon popped!", "🏹 Missed the target!", "🦖 Dino stomped it!",
    "🪐 Wrong planet!", "🧟 Zombie missed!", "🎭 Acting wrong!", "🪶 Feathered fail!", "🦢 Swan dive miss!",
    "🪤 Caught in the trap!", "🥶 Ice cold guess!", "🦀 Pinched by wrong!", "🧊 Frozen error!", "🎤 Off-key singing!",
    "🪁 Drifted off!", "🥨 Twisted!", "🛷 Slid off track!", "🚂 Off the rails!", "🪂 Parachute fail!",
    "🌋 Erupted wrong!", "⚡ Zapped!", "🛸 Flying too far!", "🦖 Roar failed!", "🧙‍♂️ Wizard miscast!",
    "🎮 Game over!", "🏓 Missed the bounce!", "🎯 Close but not!", "🕹️ Try again!", "🪃 Boomerang missed!"
]


# Default theme colors
DEFAULT_THEMES = {
    "Default Light": {
        "bg": "background-color: #f0f0f0; color: #333333;",
        "window_bg": QColor(240, 240, 240), "window_text": QColor(51, 51, 51),
        "base": QColor(255, 255, 255), "text": QColor(51, 51, 51),
        "button": QColor(200, 200, 200), "button_text": QColor(51, 51, 51),
        "highlight": QColor(70, 130, 180), "chart_bars": ["#66c2a5", "#fc8d62", "#8da0cb"] # Teal, Orange, Purple
    },
    "Default Dark": {
        "bg": "background-color: #333333; color: #f0f0f0;",
        "window_bg": QColor(53, 53, 53), "window_text": QColor(255, 255, 255),
        "base": QColor(25, 25, 25), "text": QColor(255, 255, 255),
        "button": QColor(70, 70, 70), "button_text": QColor(255, 255, 255),
        "highlight": QColor(100, 149, 237), "chart_bars": ["#8dd3c7", "#ffffb3", "#bebada"] # Mint, Yellow, Lavender
    },
    "Ocean Blue": {
        "bg": "background-color: #2196F3; color: #FFFFFF;",
        "window_bg": QColor(33, 150, 243), "window_text": QColor(255, 255, 255),
        "base": QColor(68, 138, 255), "text": QColor(255, 255, 255),
        "button": QColor(25, 118, 210), "button_text": QColor(255, 255, 255),
        "highlight": QColor(90, 180, 255), "chart_bars": ["#42a5f5", "#2196f3", "#1976d2"] # Light Blue, Blue, Dark Blue
    },
    "Forest Green": {
        "bg": "background-color: #388E3C; color: #FFFFFF;",
        "window_bg": QColor(56, 142, 60), "window_text": QColor(255, 255, 255),
        "base": QColor(76, 175, 80), "text": QColor(255, 255, 255),
        "button": QColor(27, 94, 32), "button_text": QColor(255, 255, 255),
        "highlight": QColor(102, 187, 106), "chart_bars": ["#66bb6a", "#43a047", "#2e7d32"] # Light Green, Green, Dark Green
    }
}

# --- Utility Functions ---
def load_json(file_path, default=None): # type: ignore
    if not file_path.exists():
        return default or {}
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return default or {}

# Utility function to save JSON safely
def save_json(file_path, data): # type: ignore
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

# --- Services (Modular Components) ---

class SoundManager:
    """Flexible sound manager for SFX (WAV/MP3) and BGM (WAV/MP3), PyInstaller-compatible."""

    def __init__(self, parent, sfx_folder="sound", music_folder="music"):
        self.parent = parent  # parent should have parent.data_path
        self.sfx = {}  # name -> (QMediaPlayer, QAudioOutput)
        self._temp_sfx = []  # temporary one-shot sounds
        self.music_player = QMediaPlayer()
        self.music_output = QAudioOutput()
        self.music_player.setAudioOutput(self.music_output)
        self.music_output.setVolume(0.5)  # default BGM volume

        # Paths relative to parent.data_path
        self.sfx_folder = self._resource_path(os.path.join(self.parent.data_path, sfx_folder))
        self.music_folder = self._resource_path(os.path.join(self.parent.data_path, music_folder))
        os.makedirs(self.sfx_folder, exist_ok=True)
        os.makedirs(self.music_folder, exist_ok=True)

        # Preload all WAV/MP3 files in SFX folder
        self._load_sfx_from_folder(self.sfx_folder)

    def _resource_path(self, relative_path):
        """Return absolute path for development or PyInstaller executable."""
        return os.path.abspath(os.path.join(os.path.dirname(sys.argv[0]), "..", "data", relative_path))

    def _load_sfx_from_folder(self, folder):
        """Preload WAV and MP3 files as SFX."""
        for file in os.listdir(folder):
            if file.lower().endswith((".wav", ".mp3")):
                name = os.path.splitext(file)[0]
                path = os.path.join(folder, file)
                player = QMediaPlayer()
                audio_output = QAudioOutput()
                player.setAudioOutput(audio_output)
                player.setSource(QUrl.fromLocalFile(path))
                audio_output.setVolume(0.7)
                self.sfx[name] = (player, audio_output)

    # -------------------------
    # SFX
    # -------------------------
    def play_sfx(self, name=None, file_path=None, volume=0.7):
        if file_path:
            path = self._resource_path(file_path)
            if os.path.exists(path):
                temp_player = QMediaPlayer()
                temp_output = QAudioOutput()
                temp_player.setAudioOutput(temp_output)
                temp_player.setSource(QUrl.fromLocalFile(path))
                temp_output.setVolume(volume)
                temp_player.play()
                self._temp_sfx.append((temp_player, temp_output))
                # clean finished sounds
                self._temp_sfx = [(p, o) for p, o in self._temp_sfx if p.playbackState() == QMediaPlayer.PlayingState]  # type: ignore
                return

        if name in self.sfx:
            player, output = self.sfx[name]
            output.setVolume(volume)
            player.play()
        else:
            print(f"Warning: SFX '{name}' not found in {self.sfx_folder}.")

    def set_sfx_volume(self, volume):
        for player, output in self.sfx.values():
            output.setVolume(volume)

    # -------------------------
    # BGM
    # -------------------------
    def play_music(self, filename=None, file_path=None, volume=0.5, loop=True):
        path = None
        if file_path:
            path = self._resource_path(file_path)
        elif filename:
            path = self._resource_path(os.path.join(self.music_folder, filename))

        if path and os.path.exists(path):
            self.music_player.setSource(QUrl.fromLocalFile(path))
            self.music_output.setVolume(volume)
            self.music_player.setLoops(QMediaPlayer.Infinite if loop else 1)  # type: ignore
            self.music_player.play()
        else:
            print(f"Warning: Music file '{filename or file_path}' not found.")

    def stop_music(self):
        self.music_player.stop()

    def set_music_volume(self, volume):
        self.music_output.setVolume(volume)

class SettingsService:
    """Manages application settings and full JSON export/import."""

    def __init__(self, sound_manager):
        self.sound_manager = sound_manager
        self.settings = load_json(SETTINGS_FILE, self._default_settings())
        self.apply_initial_settings()

    def _default_settings(self):
        return {
            "hints_enabled": True,
            "dark_mode": False,
            "color_theme": "Default Light",
            "min_val": 1,
            "max_val": 10,
            "sfx_volume": 0.7,
            "music_volume": 0.5,
            "confetti_on_win": True,
            "current_font": QApplication.font().family(),
            "selected_bg_color": "#f0f0f0",
            "chart_bar_colors": ["#66c2a5", "#fc8d62", "#8da0cb"]
        }

    # --- Basic Settings Access ---
    def get_setting(self, key):
        return self.settings.get(key)

    def set_setting(self, key, value):
        self.settings[key] = value
        self.save_settings()
        if key == "sfx_volume":
            self.sound_manager.set_sfx_volume(value)
        elif key == "music_volume":
            self.sound_manager.set_music_volume(value)

    def save_settings(self):
        save_json(SETTINGS_FILE, self.settings)

    def reset_settings(self):
        self.settings = self._default_settings()
        self.save_settings()
        self.apply_initial_settings()

    def apply_initial_settings(self):
        self.sound_manager.set_sfx_volume(self.settings.get("sfx_volume", 0.7))
        self.sound_manager.set_music_volume(self.settings.get("music_volume", 0.5))

    # --- Full JSON Export/Import ---
    def export_settings(self):
        """Returns Base64 string of all JSON files."""
        combined_data = {}
        for key, file_path in ALL_FILES.items():
            combined_data[key] = load_json(file_path, {})
        json_str = json.dumps(combined_data)
        encoded = base64.b64encode(json_str.encode('utf-8')).decode('utf-8')
        return encoded

    def import_settings(self, encoded_str):
        """Imports all JSONs from a Base64 string. Requires restart."""
        try:
            # 1️⃣ Validate that the input looks like Base64 (only A-Z, a-z, 0-9, +, /, =)
            if not re.fullmatch(r'[A-Za-z0-9+/=\s]+', encoded_str.strip()):
                return False, "Invalid data: input is not Base64-encoded."

            # 2️⃣ Strict Base64 decode
            decoded_bytes = base64.b64decode(encoded_str.strip(), validate=True)
            decoded = decoded_bytes.decode('utf-8')

            # 3️⃣ Parse JSON
            combined_data = json.loads(decoded)
            for key, file_path in ALL_FILES.items():
                data = combined_data.get(key, {})
                save_json(file_path, data)

            return True, "All data imported successfully! Restart required."

        except (base64.binascii.Error, json.JSONDecodeError) as e:
            return False, f"Invalid import data: {e}"
        except Exception as e:
            return False, f"Unexpected error: {e}"

class LeaderboardService:
    """Handles all leaderboard data safely, ensuring consistent dictionary entries."""

    def __init__(self):
        # Load existing leaderboard or use default structure
        self.leaderboard = load_json(LEADERBOARD_FILE, default={
            "Easy": [],
            "Medium": [],
            "Hard": [],
            "Time Trial": []
        })

    def add_score(self, difficulty, name, guesses=None, time=None, date=None):
        """Adds a new score to the leaderboard."""
        if date is None:
            date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        entry = {
            "name": name,
            "guesses": guesses if guesses is not None else 0,
            "time": time if time is not None else 0,
            "date": date
        }
        self.leaderboard.setdefault(difficulty, []).append(entry)

        # Sort based on difficulty type
        if difficulty == "Time Trial":
            self.leaderboard[difficulty].sort(key=lambda x: x["time"])  # lower time is better
        else:
            self.leaderboard[difficulty].sort(key=lambda x: x["guesses"])  # fewer guesses is better

        # Save immediately after adding a score
        save_json(LEADERBOARD_FILE, self.leaderboard)

    def get_top_scores(self, difficulty, limit=10):
        """Returns a list of top scores, normalized as dictionaries."""
        scores = self.leaderboard.get(difficulty, [])

        normalized_scores = []
        for s in scores:
            if isinstance(s, int):  # legacy integer entry
                normalized_scores.append({"name": "Unknown", "guesses": s, "time": s, "date": "N/A"})
            elif isinstance(s, dict):
                normalized_scores.append(s)
            else:
                continue

        return normalized_scores[:limit]

    def reset_leaderboard(self):
        """Resets all leaderboard data."""
        for key in self.leaderboard:
            self.leaderboard[key] = []

        # Save immediately after reset
        save_json(LEADERBOARD_FILE, self.leaderboard)

    def get_all_scores(self, difficulty):
        """Returns all scores for a difficulty (normalized)."""
        return self.get_top_scores(difficulty, limit=len(self.leaderboard.get(difficulty, [])))

class AchievementService(QObject):
    achievement_unlocked = Signal(str, str, str)  # title, description, badge

    ACHIEVEMENTS_DEFINITION = {
        "First Win!": {"description": "Win your very first game.", "unlocked": False, "badge": "⭐"},
        "Easy Mode Master": {"description": "Win 5 games on Easy difficulty.", "unlocked": False, "badge": "🟢"},
        "Medium Challenger": {"description": "Win 5 games on Medium difficulty.", "unlocked": False, "badge": "🟠"},
        "Hardcore Guesser": {"description": "Win 3 games on Hard difficulty.", "unlocked": False, "badge": "🔴"},
        "Guessing Streak (3)": {"description": "Win 3 games in a row.", "unlocked": False, "badge": "🔥"},
        "Guessing Streak (5)": {"description": "Win 5 games in a row.", "unlocked": False, "badge": "🔥🔥"},
        "Quick Thinker": {"description": "Win a Time Trial game.", "unlocked": False, "badge": "⏱️"},
        "Power User": {"description": "Use a power-up for the first time.", "unlocked": False, "badge": "⚡"},
        "AI Apprentice": {"description": "Use an AI hint for the first time.", "unlocked": False, "badge": "🤖"},
        "Ultimate Guesser": {"description": "Win a game on Hard difficulty in 5 guesses or less.", "unlocked": False, "badge": "👑"},
        # Daily streak achievements
        "Daily Streak (3)": {"description": "Win games 3 consecutive days!", "unlocked": False, "badge": "🔥"},
        "Daily Streak (7)": {"description": "Win games 7 consecutive days!", "unlocked": False, "badge": "🔥🔥"},
        "Daily Streak (30)": {"description": "Win games 30 consecutive days!", "unlocked": False, "badge": "💎"},
    }

    DAILY_STREAK_MILESTONES = [3, 7, 30]  # milestones for achievement

    def __init__(self, sound_manager):
        super().__init__()
        self.sound_manager = sound_manager
        self.achievements = load_json(ACHIEVEMENTS_FILE, self.ACHIEVEMENTS_DEFINITION)

        # Ensure all definitions exist
        for key, value in self.ACHIEVEMENTS_DEFINITION.items():
            if key not in self.achievements:
                self.achievements[key] = value

        # --- Watch statistics file for changes ---
        self.stats_watcher = QFileSystemWatcher([STATISTICS_FILE]) # type: ignore
        self.stats_watcher.fileChanged.connect(self._on_statistics_changed)

        # Initial check
        self.update_from_statistics()
        
    def evaluate_achievements(self, stats):
        """Force-check all achievements based on current stats."""
        self.update_from_statistics()

    def _on_statistics_changed(self, path):
        # Delay slightly in case file is still writing
        QTimer.singleShot(100, self.update_from_statistics)

    def get_all_achievements(self):
        """Returns the full achievements dictionary."""
        return self.achievements

    def save_achievements(self):
        save_json(ACHIEVEMENTS_FILE, self.achievements)

    def check_and_unlock(self, achievement_key, condition_met):
        if achievement_key in self.achievements and not self.achievements[achievement_key]["unlocked"]:
            if condition_met:
                self.achievements[achievement_key]["unlocked"] = True
                self.save_achievements()
                if self.sound_manager:
                    self.sound_manager.play_sfx("achievement_unlock")
                self.achievement_unlocked.emit(
                    achievement_key,
                    self.achievements[achievement_key]["description"],
                    self.achievements[achievement_key]["badge"]
                )
                return True
        return False

    def start_daily_streak_timer(self):
        """
        Starts a QTimer that refreshes the daily streak at midnight every day.
        Call this once when your app/game starts.
        """
        now = time.localtime()
        # Calculate seconds until next midnight
        seconds_until_midnight = (
            (24 - now.tm_hour - 1) * 3600 +  # hours left
            (60 - now.tm_min - 1) * 60 +     # minutes left
            (60 - now.tm_sec)                 # seconds left
        )

        # Create a single-shot timer for midnight
        self._midnight_timer = QTimer(self)
        self._midnight_timer.setSingleShot(True)
        self._midnight_timer.timeout.connect(self._on_midnight)
        self._midnight_timer.start(seconds_until_midnight * 1000)  # QTimer uses milliseconds

    def _on_midnight(self):
        """
        Called at midnight to refresh the daily streak.
        Resets streak if no win today and schedules next midnight.
        """
        self.refresh_daily_streak()

        # Reschedule timer for next midnight (24h)
        self._midnight_timer.start(24 * 3600 * 1000)

    # --- New: Check stats and unlock relevant achievements ---
    def update_from_statistics(self):
        stats = load_json(STATISTICS_FILE, default={})
        
        # Example: wins per difficulty
        wins_easy = stats.get("wins_easy", 0)
        wins_medium = stats.get("wins_medium", 0)
        wins_hard = stats.get("wins_hard", 0)
        current_streak = stats.get("current_streak", 0)
        time_trial_wins = stats.get("time_trial_wins", 0)
        powerups_used = stats.get("powerups_used", 0)
        ai_hints_used = stats.get("ai_hints_used", 0)
        hard_five_guess_wins = stats.get("hard_five_guess_wins", 0)
        total_wins = wins_easy + wins_medium + wins_hard

        self.check_and_unlock("First Win!", total_wins >= 1)
        self.check_and_unlock("Easy Mode Master", wins_easy >= 5)
        self.check_and_unlock("Medium Challenger", wins_medium >= 5)
        self.check_and_unlock("Hardcore Guesser", wins_hard >= 3)
        self.check_and_unlock("Guessing Streak (3)", current_streak >= 3)
        self.check_and_unlock("Guessing Streak (5)", current_streak >= 5)
        self.check_and_unlock("Quick Thinker", time_trial_wins >= 1)
        self.check_and_unlock("Power User", powerups_used >= 1)
        self.check_and_unlock("AI Apprentice", ai_hints_used >= 1)
        self.check_and_unlock("Ultimate Guesser", hard_five_guess_wins >= 1)

        # --- Daily streak achievements ---
        daily_streak = stats.get("daily_streak", 0)
        for milestone in self.DAILY_STREAK_MILESTONES:
            key = f"Daily Streak ({milestone})"
            self.check_and_unlock(key, daily_streak >= milestone)
            
    def reset_achievements(self):
        """Reset all achievements to locked state."""
        for key in self.achievements:
            self.achievements[key]["unlocked"] = False
        self.save_achievements()  # save immediately

class StatisticsService:
    """Tracks various in-game statistics."""
    def __init__(self):
        self.stats = load_json(STATISTICS_FILE, self._default_stats())
        
    def _default_stats(self):
        return {
            "total_games": 0,
            "total_wins": 0,
            "total_losses": 0,
            "easy_wins": 0,
            "medium_wins": 0,
            "hard_wins": 0,
            "time_trial_wins": 0,
            "current_streak": 0,
            "longest_streak": 0,
            "daily_streak": 0,
            "last_played_date": 0,  # epoch timestamp of last game played
            "total_guesses_all_games": 0,
            "games_with_guesses": 0,
            "power_ups_used": 0,
            "ai_hints_used": 0
        }
        
    def refresh_daily_streak(self):
        """
        Checks the last played date and updates/resets the daily streak automatically.
        Call this at app startup or whenever stats are loaded.
        """
        now = int(time.time())
        last_played = self.stats.get("last_played_date", 0)

        now_struct = time.localtime(now)
        today_day = now_struct.tm_yday
        today_year = now_struct.tm_year

        if last_played:
            last_struct = time.localtime(last_played)
            last_day = last_struct.tm_yday
            last_year = last_struct.tm_year
        else:
            # First game ever
            self.stats["daily_streak"] = 0
            self.stats["last_played_date"] = now
            self.save_stats()
            return

        # Determine if streak should continue or reset
        if today_year == last_year and today_day == last_day:
            # Already played today, streak stays the same
            pass
        elif (
            (today_year == last_year and today_day == last_day + 1) or
            (today_year == last_year + 1 and last_day == 365 and today_day == 1)  # handle year rollover
        ):
            # Consecutive day, streak continues
            pass
        else:
            # Missed one or more days, reset streak
            self.stats["daily_streak"] = 0  # reset to 0 until next win

        # Always update last_played_date so we know when the streak was last checked
        self.stats["last_played_date"] = now
        self.save_stats()

    def update_daily_streak(self, won):
        """Increment daily streak if the player won today."""
        if not won:
            return

        # Ensure the streak is refreshed first (resets after missed days)
        self.refresh_daily_streak()

        # Increment streak
        self.stats["daily_streak"] = self.stats.get("daily_streak", 0) + 1

        # Update last_played_date
        self.stats["last_played_date"] = int(time.time())
        self.save_stats()


    def save_stats(self):
        """Saves current statistics to file."""
        save_json(STATISTICS_FILE, self.stats)

    def increment(self, key, value=1):
        """Increments a statistic by a given value."""
        self.stats[key] = self.stats.get(key, 0) + value
        self.save_stats()

    def update_streak(self, won):
        """Updates the win streak."""
        if won:
            self.stats["current_streak"] = self.stats.get("current_streak", 0) + 1
            if self.stats["current_streak"] > self.stats["longest_streak"]:
                self.stats["longest_streak"] = self.stats["current_streak"]
        else:
            self.stats["current_streak"] = 0
        self.save_stats()

    def add_guesses(self, guesses):
        """Adds guesses to the total and increments game count for average."""
        self.stats["total_guesses_all_games"] += guesses
        self.stats["games_with_guesses"] += 1
        self.save_stats()

    def get_average_guesses(self):
        """Calculates the average guesses per game."""
        if self.stats.get("games_with_guesses", 0) > 0:
            return self.stats["total_guesses_all_games"] / self.stats["games_with_guesses"]
        return 0

    def get_stats(self):
        """Returns the full statistics dictionary."""
        return self.stats

    def reset_stats(self):
        """Resets all statistics to default."""
        self.stats = self._default_stats()
        self.save_stats()
    
    def set_stats(self, stats_dict):
        """Replaces current stats with the given dictionary and saves."""
        self.stats = stats_dict
        self.save_stats()

class AIService:
    """Provides human-like AI hints based on game state, aware of target, guesses, and range."""
    def __init__(self):
        self.past_hints = []

    def get_hint(self, target_number, guesses_made, min_val, max_val, previous_guesses):
        import time, random
        time.sleep(0.5)  # simulate thinking

        remaining_range = [n for n in range(min_val, max_val + 1) if n not in previous_guesses]
        if not remaining_range:
            return "Hmm, it seems like we've explored all possible numbers… maybe check the range?"

        hints = []

        # Early game: gentle guidance
        if guesses_made < 2:
            mid = (min_val + max_val) // 2
            hints.append(f"Let's start around the middle, maybe somewhere near {mid}.")
        else:
            # Smart narrowing
            mid = (min_val + max_val) // 2
            if target_number <= mid:
                hints.append(f"I think the number is in the lower half ({min_val}-{mid}).")
            else:
                hints.append(f"I'm leaning towards the upper half ({mid+1}-{max_val}).")

            # Proximity hint based on last guess
            if previous_guesses:
                last_guess = previous_guesses[-1]
                diff = target_number - last_guess
                if diff == 0:
                    hints.append("You just guessed it! Well done… but let’s pretend you didn’t for this hint 😉")
                elif abs(diff) <= max(1, (max_val - min_val)//10):
                    if diff > 0:
                        hints.append(f"You're slightly low. Try a bit higher than {last_guess}.")
                    else:
                        hints.append(f"You're slightly high. Try a bit lower than {last_guess}.")
                else:
                    if diff > 0:
                        hints.append(f"You're way too low. Aim higher than {last_guess}.")
                    else:
                        hints.append(f"You're way too high. Aim lower than {last_guess}.")

            # Even/Odd reasoning
            if target_number % 2 == 0:
                hints.append("I'd bet the number is even. Numbers like 2,4,6… might work.")
            else:
                hints.append("Seems odd to me! Odd numbers could be your friends here.")

            # Fun reasoning about multiples and prime
            multiples = []
            if target_number % 3 == 0: multiples.append(3)
            if target_number % 5 == 0: multiples.append(5)
            if multiples:
                hints.append(f"Interesting… it's divisible by {', '.join(map(str, multiples))}.")

            is_prime = target_number > 1 and all(target_number % i != 0 for i in range(2, int(target_number**0.5)+1))
            if is_prime:
                hints.append("Fun fact: it's a prime number. That might help you narrow it down.")

        # Avoid repeating hints until all are used
        unused_hints = [h for h in hints if h not in self.past_hints]
        if not unused_hints:
            self.past_hints = []
            unused_hints = hints

        hint = random.choice(unused_hints)
        self.past_hints.append(hint)
        return hint
    
class GameService(QObject):
    """Manages all game logic, states, and interactions with other services."""

    # Signals
    game_over = Signal(bool, int, float)  # won, guesses, time_taken
    timer_update = Signal(int)  # remaining time
    ai_hint_ready = Signal(str)  # hint text
    ai_hint_loading = Signal(bool)  # True if AI hint is processing
    game_state_changed = Signal()  # UI update triggers

    def __init__(self, settings_service, leaderboard_service, achievement_service, statistics_service, sound_manager):
        super().__init__()  # MUST call QObject init

        # Services
        self.settings = settings_service
        self.leaderboard = leaderboard_service
        self.achievements = achievement_service
        self.stats = statistics_service
        self.sound_manager = sound_manager

        # Game state variables
        self.target_number = 0
        self.guesses_made = 0
        self.previous_guesses = []

        self.min_val = 1
        self.max_val = 10
        self.difficulty = "Easy"
        self.time_trial_mode = False
        self.time_limit = 60
        self.time_remaining = self.time_limit
        self.start_time = 0

        self.power_ups = {"extra_hint": 0, "retry": 0, "reveal_digit": 0}

        # Timer setup
        self.game_timer = QTimer()
        self.game_timer.timeout.connect(self._tick_timer)

        # Initialize AI Service
        self.ai_service = AIService()


        # Initialize
        self._reset_game_state()
        self.load_game_state()

    # -------------------------------
    # Game state management
    # -------------------------------
    def _reset_game_state(self):
        """Reset game variables to defaults."""
        self.target_number = 0
        self.guesses_made = 0
        self.previous_guesses = []
        self.game_timer.stop()
        self.time_remaining = self.time_limit
        self.start_time = 0
        self.power_ups = {
            "extra_hint": self.stats.get_stats().get("power_ups_inventory_extra_hint", 0),
            "retry": self.stats.get_stats().get("power_ups_inventory_retry", 0),
            "reveal_digit": self.stats.get_stats().get("power_ups_inventory_reveal_digit", 0)
        }
        self.game_state_changed.emit()

    # -------------------------------
    # Game logic
    # -------------------------------
    def start_new_game(self, difficulty, min_val=None, max_val=None, time_trial=False):
        self._reset_game_state()
        self.difficulty = difficulty
        self.time_trial_mode = time_trial

        # Set range
        if min_val is not None and max_val is not None:
            self.min_val = min_val
            self.max_val = max_val
        else:
            default_ranges = {"Easy": (1, 10), "Medium": (1, 100), "Hard": (1, 1000)}
            self.min_val, self.max_val = default_ranges.get(difficulty, (1, 10))

        if self.min_val > self.max_val:
            self.min_val, self.max_val = self.max_val, self.min_val

        if self.min_val == self.max_val:
            self.max_val += 1

        self.target_number = random.randint(self.min_val, self.max_val)
        self.stats.increment("total_games")

        # Timer
        if self.time_trial_mode:
            self.time_remaining = self.time_limit
            self.start_time = time.time()
            self.game_timer.start(1000)
        else:
            self.start_time = 0
            self.game_timer.stop()

        self.game_state_changed.emit()
        self.save_game_state()

    def check_guess(self, guess):
        """Check player's guess against target."""
        self.guesses_made += 1
        self.previous_guesses.append(guess)
        self.game_state_changed.emit()

        if guess == self.target_number:
            self.sound_manager.play_sfx("win")
            time_taken = time.time() - self.start_time if self.time_trial_mode else 0
            self.leaderboard.add_score(self.difficulty, "Player", self.guesses_made, time_taken)
            self.stats.increment("total_wins")
            self.game_over.emit(True, self.guesses_made, time_taken)
            self.save_game_state()
            return "correct"
        else:
            self.sound_manager.play_sfx("incorrect_guess")
            return "too_low" if guess < self.target_number else "too_high"

    # -------------------------------
    # Timer
    # -------------------------------
    def _tick_timer(self):
        self.time_remaining -= 1
        self.timer_update.emit(self.time_remaining)
        self.sound_manager.play_sfx("tick")
        if self.time_remaining <= 0:
            self.game_timer.stop()
            self.stats.increment("total_losses")
            self.game_over.emit(False, self.guesses_made, self.time_limit)
            self.save_game_state()

    # -------------------------------
    # AI hints
    # -------------------------------
    def request_ai_hint(self):
        if not self.settings.get_setting("hints_enabled"):
            QMessageBox.warning(None, "Hints Disabled", "AI Hints are disabled.")
            return

        self.ai_hint_loading.emit(True)
        threading.Thread(target=self._generate_ai_hint_thread, daemon=True).start()

        # Update stats
        self.stats.increment("ai_hints_used")
        self.stats.save_stats()  # make sure stats persist

        # Force achievement check
        current_stats = self.stats.get_stats()
        self.achievements.update_from_statistics()

    def _generate_ai_hint_thread(self):
        if self.ai_service is None:
            hint = "AI service unavailable."
        else:
            hint = self.ai_service.get_hint(
                self.target_number,
                self.guesses_made,
                self.min_val,
                self.max_val,
                self.previous_guesses
            )
        self.ai_hint_ready.emit(hint)
        self.ai_hint_loading.emit(False)

    # -------------------------------
    # Power-ups
    # -------------------------------
    def use_power_up(self, power_up_type):
        if self.power_ups.get(power_up_type, 0) <= 0:
            QMessageBox.warning(None, "No Power-Ups", f"No '{power_up_type}' left!")
            return False

        # Consume the power-up
        self.power_ups[power_up_type] -= 1

        # Update stats
        self.stats.increment("power_ups_used")
        self.stats.save_stats()  # ensure persistence

        # Force achievement check
        current_stats = self.stats.get_stats()
        self.achievements.update_from_statistics()

        # Play sound & notify UI
        self.sound_manager.play_sfx("powerup_activate")
        self.game_state_changed.emit()

        # Apply specific power-up effect
        if power_up_type == "extra_hint":
            self.request_ai_hint()
            return True
        elif power_up_type == "retry":
            if self.previous_guesses:
                self.guesses_made -= 1
                self.previous_guesses.pop()
            return True
        elif power_up_type == "reveal_digit":
            str_num = str(self.target_number)
            digit_to_reveal = random.choice(str_num)
            QMessageBox.information(None, "Power-Up", f"One digit: {digit_to_reveal}")
            return True

        return False


    def add_power_up(self, power_up_type, count=1):
        self.power_ups[power_up_type] = self.power_ups.get(power_up_type, 0) + count
        self.stats.get_stats()[f"power_ups_inventory_{power_up_type}"] = self.power_ups[power_up_type]
        self.stats.save_stats()
        self.game_state_changed.emit()

    # -------------------------------
    # Save/load
    # -------------------------------
    def save_game_state(self):
        game_state = {
            "target_number": self.target_number,
            "guesses_made": self.guesses_made,
            "min_val": self.min_val,
            "max_val": self.max_val,
            "difficulty": self.difficulty,
            "time_trial_mode": self.time_trial_mode,
            "time_remaining": self.time_remaining,
            "start_time": self.start_time,
            "previous_guesses": self.previous_guesses,
            "power_ups": self.power_ups
        }
        save_json(GAME_STATE_FILE, game_state)

    def load_game_state(self):
        """Load the game state. Returns True if genuinely first-time launch."""
        if not GAME_STATE_FILE.exists() or os.path.getsize(GAME_STATE_FILE) == 0:
            # Truly first-time
            return True

        try:
            game_state = load_json(GAME_STATE_FILE)
            if not game_state:
                return True  # Empty or invalid JSON = first-time

            # --- Corruption checks ---
            target_number = game_state.get("target_number", 0)
            min_val = game_state.get("min_val", 1)
            max_val = game_state.get("max_val", 10)
            previous_guesses = game_state.get("previous_guesses", [])
            power_ups = game_state.get("power_ups", {})

            corruption_detected = False
            if target_number == 0 or not (min_val <= target_number <= max_val):
                corruption_detected = True
            if not all(isinstance(g, int) and min_val <= g <= max_val for g in previous_guesses):
                corruption_detected = True
            if any(not isinstance(v, int) or v < 0 for v in power_ups.values()):
                corruption_detected = True

            if corruption_detected:
                msg_box = QMessageBox()
                msg_box.setIcon(QMessageBox.Icon.Critical)
                msg_box.setWindowTitle("Save Data Corrupted")
                msg_box.setText("Your save data appears corrupted.\nDo you want to run recovery now?")
                response = msg_box.exec()
                if response == QMessageBox.StandardButton.Yes:
                    self.run_recovery()
                sys.exit(1)  # stop game if user cancels

            # --- Load valid game state ---
            self.target_number = target_number
            self.guesses_made = game_state.get("guesses_made", 0)
            self.min_val = min_val
            self.max_val = max_val
            self.difficulty = game_state.get("difficulty", "Easy")
            self.time_trial_mode = game_state.get("time_trial_mode", False)
            self.time_remaining = game_state.get("time_remaining", 60)
            self.start_time = game_state.get("start_time", 0)
            self.previous_guesses = previous_guesses
            self.power_ups = power_ups

            if self.time_trial_mode and self.time_remaining > 0:
                self.start_time = time.time() - (self.time_limit - self.time_remaining)
                self.game_timer.start(1000)
                self.timer_update.emit(self.time_remaining)

            self.game_state_changed.emit()
            return False  # Successfully loaded

        except Exception as e:
            QMessageBox.critical(None, "Load Error", f"Failed to load game state:\n{e}")
            sys.exit(1)


    def run_recovery():
        """Run recovery tool from the same folder, PyInstaller-compatible."""
        try:
            # Determine folder where main.exe or main.py resides
            if getattr(sys, 'frozen', False):
                # PyInstaller: folder where main.exe exists
                base_path = os.path.dirname(sys.executable)
            else:
                # Development: folder of this script
                base_path = os.path.dirname(os.path.abspath(__file__))

            # Paths to recovery targets
            recovery_exe = os.path.join(base_path, "recovery.exe")
            recovery_py = os.path.join(base_path, "recovery.py")

            if os.path.exists(recovery_exe):
                subprocess.Popen([recovery_exe])
            elif os.path.exists(recovery_py):
                subprocess.Popen([sys.executable, recovery_py])
            else:
                # Neither recovery.exe nor recovery.py found
                msg_box = QMessageBox()
                msg_box.setIcon(QMessageBox.Critical)
                msg_box.setWindowTitle("Recovery Failed")
                msg_box.setText(f"Recovery tool not found in:\n{base_path}")
                msg_box.exec()
                return

            # Optionally close main window if needed
            try:
                # assuming self is MainWindow instance
                self.close()
            except NameError:
                pass  # not called from a window instance

            sys.exit(0)

        except Exception as e:
            tb = traceback.format_exc()
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Critical)
            msg_box.setWindowTitle("Recovery Failed")
            msg_box.setText(f"Failed to run recovery tool:\n{e}")
            msg_box.setDetailedText(tb)
            msg_box.exec()


    def clear_saved_game_state(self):
        if os.path.exists(GAME_STATE_FILE):
            os.remove(GAME_STATE_FILE)
        self._reset_game_state()
        QMessageBox.information(
            None,
            "Cleared",
            "Saved game reset!\n\nIf you want to set a new minimum-maximum or adjust other settings,\njust click \"New Game\"."
        )


class ThemedButton(QPushButton):
    """A custom button that reacts to theme changes and provides animations."""

    def __init__(self, text, parent=None):
        super().__init__(text, parent)  # FIX: __init__, not .init
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet(self._get_default_style())

        # Animation for hover effect MUST be inside __init__
        self.animation = QPropertyAnimation(self, b"pos")
        self.animation.setDuration(100)
        self.animation.setEasingCurve(QEasingCurve.OutBack)

        self.original_style = ""  # Store original stylesheet for theme updates

    def _get_default_style(self):
        return """
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 10px 20px;
                border-radius: 5px;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #367c39;
            }
        """

    def apply_theme_style(self, style_sheet):
        self.original_style = style_sheet
        self.setStyleSheet(style_sheet)

    def enterEvent(self, event):
        self.animation.setStartValue(self.pos())
        self.animation.setEndValue(self.pos() + QPoint(0, -3))  # move slightly up
        self.animation.start()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.animation.setStartValue(self.pos())
        self.animation.setEndValue(self.pos())  # back to original
        self.animation.start()
        super().leaveEvent(event)

class QPoint:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __add__(self, other):
        return QPoint(self.x + other.x, self.y + other.y)

    def __sub__(self, other):
        return QPoint(self.x - other.x, self.y - other.y)

    def to_qt_point(self):
        # Convert to actual QPoint if needed in some contexts
        from PySide6.QtCore import QPoint as QtQPoint
        return QtQPoint(self.x, self.y)

    def __repr__(self):
        return f"QPoint({self.x}, {self.y})"

class ConfettiEffect(QWidget):
    """A widget that displays a confetti GIF animation."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowTransparentForInput)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.hide()

        confetti_path = "confetti.gif"
        if not os.path.exists(confetti_path):
            try:
                from PIL import Image
                img = Image.new('RGB', (1, 1), color='red')
                img.save(confetti_path, format="GIF")
            except ImportError:
                with open(confetti_path, "wb") as f:  # binary mode!
                    f.write(b"GIF89a\x01\x00\x01\x00\x00\xff\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;")
                print("Warning: Pillow not found, created a minimal static GIF placeholder.")

        self.movie = QMovie(confetti_path)
        self.label = QLabel(self)
        layout = QVBoxLayout(self)
        layout.addWidget(self.label)

        if self.movie.isValid():
            self.label.setMovie(self.movie)
            self.movie.setSpeed(150)
            self.movie.frameChanged.connect(self._check_movie_finished)
            self.is_gif_valid = True
        else:
            self.label.setText("✨🎉 Confetti! 🎉✨")
            self.label.setAlignment(Qt.AlignCenter)
            self.label.setStyleSheet("color: gold; font-size: 30px; font-weight: bold;")
            self.is_gif_valid = False

        self.adjustSize()

    def showEvent(self, event):
        """Ensure the confetti fills the parent when shown."""
        if self.parent():
            self.setFixedSize(self.parent().size())
            if self.is_gif_valid:
                self.movie.setScaledSize(self.size())
        super().showEvent(event)

    def _check_movie_finished(self, frame_number):
        if self.is_gif_valid and self.movie.currentFrameNumber() == self.movie.frameCount() - 1:
            self.hide_confetti()

    def show_confetti(self):
        if self.is_gif_valid:
            self.movie.start()
        self.show()
        QTimer.singleShot(2000, self.hide_confetti)

    def hide_confetti(self):
        if self.is_gif_valid:
            self.movie.stop()
        self.hide()


class AchievementPopup(QDialog):
    """A transient popup for displaying achievement unlocks."""
    def __init__(self, title, description, badge, dark_mode=False, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.SplashScreen | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setModal(False)
        self.setFixedSize(300, 100)

        self.dark_mode = dark_mode  # True for dark mode, False for light mode

        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(15)

        # Badge emoji
        badge_label = QLabel(badge)
        badge_label.setFont(QFont("Segoe UI Emoji", 30))
        layout.addWidget(badge_label, alignment=Qt.AlignCenter)

        # Text layout
        text_layout = QVBoxLayout()
        title_label = QLabel("Achievement Unlocked!")
        title_label.setFont(QFont("Arial", 12, QFont.Bold))
        title_label.setStyleSheet("color: gold;")

        achievement_title_label = QLabel(title)
        achievement_title_label.setFont(QFont("Arial", 10, QFont.Bold))
        achievement_title_label.setStyleSheet(
            f"color: {'white' if self.dark_mode else 'black'};"
        )

        description_label = QLabel(description)
        description_label.setFont(QFont("Arial", 8))
        description_label.setWordWrap(True)
        description_label.setStyleSheet(
            f"color: {'lightgray' if self.dark_mode else 'gray'};"
        )

        text_layout.addWidget(title_label)
        text_layout.addWidget(achievement_title_label)
        text_layout.addWidget(description_label)
        layout.addLayout(text_layout)

        # Background & border
        bg_color = "rgba(0,0,0,180)" if self.dark_mode else "rgba(255,255,255,230)"
        border_color = "gold"
        self.setStyleSheet(f"""
            AchievementPopup {{
                background-color: {bg_color};
                border: 2px solid {border_color};
                border-radius: 15px;
            }}
        """)

        # Fade in/out animation
        self.animation = QPropertyAnimation(self, b"windowOpacity")
        self.animation.setDuration(500)
        self.animation.setStartValue(0.0)
        self.animation.setEndValue(1.0)
        self.animation.setEasingCurve(QEasingCurve.OutCubic)

        # Auto close timer
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self._fade_out)

    def showEvent(self, event):
        """Position the popup in top-right corner and start animations."""
        if self.parentWidget():
            parent_rect = self.parentWidget().geometry()
            x = parent_rect.right() - self.width() - 20
            y = parent_rect.top() + 20
            self.move(x, y)
        else:
            screen_geometry = QGuiApplication.primaryScreen().availableGeometry()
            x = screen_geometry.right() - self.width() - 20
            y = screen_geometry.top() + 20
            self.move(x, y)

        self.setWindowOpacity(0.0)
        self.show()
        self.animation.start()
        self.timer.start(3000)  # Show for 3 seconds

    def _fade_out(self):
        """Fade out then close."""
        self.animation.setDirection(QPropertyAnimation.Backward)
        self.animation.finished.connect(self.close)
        self.animation.start()

class ThemeManager:
    """Manages applying themes (stylesheets and palettes) to the entire application."""
    def __init__(self, settings_service):
        self.settings = settings_service
        self.current_theme_name = self.settings.get_setting("color_theme")
        self.dark_mode_enabled = self.settings.get_setting("dark_mode")

    def get_current_theme_data(self):
        """Returns the data for the currently active theme."""
        theme_name = self.current_theme_name if not self.dark_mode_enabled else "Default Dark" # Dark mode overrides custom themes for overall palette
        if self.current_theme_name in DEFAULT_THEMES:
            return DEFAULT_THEMES[self.current_theme_name]
        return DEFAULT_THEMES["Default Light"] # Fallback

    def apply_theme_to_app(self, app):
        """Applies the current theme to the QApplication."""
        theme_data = DEFAULT_THEMES["Default Dark"] if self.dark_mode_enabled else DEFAULT_THEMES["Default Light"]
        if self.current_theme_name in DEFAULT_THEMES: # If a custom non-dark theme is selected
            if not self.dark_mode_enabled: # Only apply custom light theme if dark mode is off
                theme_data = DEFAULT_THEMES[self.current_theme_name]
            else: # If dark mode is on, use the dark theme's palette but potentially custom chart colors
                theme_data = DEFAULT_THEMES["Default Dark"]

        palette = QPalette()
        palette.setColor(QPalette.Window, theme_data["window_bg"])
        palette.setColor(QPalette.WindowText, theme_data["window_text"])
        palette.setColor(QPalette.Base, theme_data["base"])
        palette.setColor(QPalette.Text, theme_data["text"])
        palette.setColor(QPalette.Button, theme_data["button"])
        palette.setColor(QPalette.ButtonText, theme_data["button_text"])
        palette.setColor(QPalette.Highlight, theme_data["highlight"])
        palette.setColor(QPalette.HighlightedText, QColor(255, 255, 255))
        app.setPalette(palette)

        # Apply global stylesheet for background and text colors.
        # Specific widget styles can be handled individually or with more specific QSS rules.
        bg_color = self.settings.get_setting("selected_bg_color")
        main_text_color = theme_data["window_text"].name()
        
        # Override with custom background color if set
        if self.settings.get_setting("selected_bg_color"):
            app.setStyleSheet(f"QWidget {{ background-color: {self.settings.get_setting('selected_bg_color')}; color: {main_text_color}; }}")
        else:
            app.setStyleSheet(theme_data["bg"])

        # Set font
        font = QFont(self.settings.get_setting("current_font"))
        app.setFont(font)

    def get_button_stylesheet(self):
        """Generates a dynamic stylesheet for buttons based on current theme settings."""
        theme_data = DEFAULT_THEMES["Default Dark"] if self.dark_mode_enabled else DEFAULT_THEMES["Default Light"]
        if self.current_theme_name in DEFAULT_THEMES and not self.dark_mode_enabled:
            theme_data = DEFAULT_THEMES[self.current_theme_name]

        btn_bg = theme_data["button"].name()
        btn_text = theme_data["button_text"].name()
        btn_highlight = theme_data["highlight"].name()

        # Generate a slightly darker/lighter hover color
        hover_color = QColor(btn_bg).lighter(120).name() if not self.dark_mode_enabled else QColor(btn_bg).darker(120).name()
        pressed_color = QColor(btn_bg).darker(150).name() if not self.dark_mode_enabled else QColor(btn_bg).lighter(150).name()

        return f"""
            QPushButton {{
                background-color: {btn_bg};
                color: {btn_text};
                padding: 12px 25px;
                border-radius: 8px;
                font-size: 16px;
                font-weight: bold;
                border: none;
                min-width: 100px;
            }}
            QPushButton:hover {{
                background-color: {hover_color};
            }}
            QPushButton:pressed {{
                background-color: {pressed_color};
            }}
            QComboBox {{
                padding: 5px;
                border-radius: 5px;
                border: 1px solid {btn_bg};
                background-color: {theme_data["base"].name()};
                color: {theme_data["text"].name()};
            }}
            QComboBox::drop-down {{
                border-left: 1px solid {btn_bg};
                width: 20px;
            }}
            QComboBox::down-arrow {{
                image: url(arrow_down.png); /* Placeholder, in real app provide icon */
            }}
            QLineEdit {{
                padding: 8px;
                border-radius: 5px;
                border: 1px solid {btn_highlight};
                background-color: {theme_data["base"].name()};
                color: {theme_data["text"].name()};
            }}
            QSpinBox {{
                padding: 5px;
                border-radius: 5px;
                border: 1px solid {btn_highlight};
                background-color: {theme_data["base"].name()};
                color: {theme_data["text"].name()};
            }}
            QCheckBox::indicator {{
                width: 20px;
                height: 20px;
            }}
        """

    def update_widgets_style(self, widgets):
        """Applies the current button stylesheet to a list of widgets."""
        style = self.get_button_stylesheet()
        for widget in widgets:
            if isinstance(widget, QPushButton) or isinstance(widget, QComboBox) or isinstance(widget, QLineEdit) or isinstance(widget, QSpinBox) or isinstance(widget, QCheckBox):
                widget.setStyleSheet(style)
            elif isinstance(widget, QLabel):
                widget.setStyleSheet(f"color: {DEFAULT_THEMES['Default Dark']['window_text'].name() if self.dark_mode_enabled else DEFAULT_THEMES['Default Light']['window_text'].name()};")

class GameView(QWidget):
    """The main game interface for guessing numbers."""
    def __init__(self, game_service, settings_service, sound_manager, theme_manager, achievement_popup_signal, stats_service, parent=None):
        super().__init__(parent)
        
        # --- Services ---
        self.stats = stats_service
        self.game = game_service
        self.settings = settings_service
        self.sound_manager = sound_manager
        self.theme_manager = theme_manager
        self.achievement_popup_signal = achievement_popup_signal  # Signal to main window for popup

        # --- Connect signals ---
        self.game.game_over.connect(self._handle_game_over)
        self.game.timer_update.connect(self._update_timer_display)
        self.game.ai_hint_ready.connect(self._display_ai_hint)
        self.game.ai_hint_loading.connect(self._toggle_ai_hint_loading_state)
        self.game.game_state_changed.connect(self._update_game_info_labels)

        # --- Initialize UI ---
        self.init_ui()
        self._update_game_info_labels()  # Initial state update

        # --- Check game state file to determine first-time launch ---
        if GAME_STATE_FILE.exists():
            try:
                success = self.game.load_game_state()
            except Exception as e:
                print(f"Failed to load game state: {e}")
                success = False

            if not success:
                # Either file corrupted or loading failed → first-time launch
                self._start_new_game_dialog(first_time=True)
            else:
                # Successfully loaded → normal flow
                self._update_game_info_labels()
        else:
            # File missing → first-time launch
            self._start_new_game_dialog(first_time=True)



    def init_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(15)
        self.layout.setAlignment(Qt.AlignCenter)

        # Title and Game Info
        self.title_label = QLabel("Guess The Number Game!")
        self.title_label.setObjectName("titleLabel")
        self.title_label.setStyleSheet("font-size: 28px; font-weight: bold;")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.title_label)

        self.info_layout = QHBoxLayout()
        self.difficulty_label = QLabel("Difficulty: Easy")
        self.guesses_label = QLabel("Guesses: 0")
        self.time_label = QLabel("Time: N/A")
        self.info_layout.addWidget(self.difficulty_label)
        self.info_layout.addWidget(self.guesses_label)
        self.info_layout.addWidget(self.time_label)
        self.layout.addLayout(self.info_layout)

        # Guess Input and Button
        input_button_layout = QHBoxLayout()
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText(f"Enter number ({self.game.min_val}-{self.game.max_val})")
        self.input_field.returnPressed.connect(self.check_guess) # Allow Enter key to submit
        self.input_field.setFixedWidth(200)
        self.input_field.setAlignment(Qt.AlignCenter) # type: ignore
        input_button_layout.addWidget(self.input_field)

        self.guess_button = QPushButton("Guess!")
        self.guess_button.clicked.connect(self.check_guess)
        input_button_layout.addWidget(self.guess_button)
        self.layout.addLayout(input_button_layout)

        # Game Controls (Start New Game, Time Trial, Save/Load)
        game_control_layout = QHBoxLayout()
        self.new_game_button = QPushButton("New Game")
        self.new_game_button.clicked.connect(self._start_new_game_dialog)
        game_control_layout.addWidget(self.new_game_button)

        self.time_trial_button = QPushButton("Time Trial")
        self.time_trial_button.clicked.connect(self._start_time_trial_game)
        game_control_layout.addWidget(self.time_trial_button)
        self.layout.addLayout(game_control_layout)

        # Hints and Power-ups
        hints_powerups_group = QGroupBox("Hints & Power-Ups")
        hints_powerups_layout = QVBoxLayout(hints_powerups_group)

        self.ai_hint_label = QLabel("AI Hint: (Request a hint)")
        self.ai_hint_label.setWordWrap(True)
        hints_powerups_layout.addWidget(self.ai_hint_label)

        hint_button_layout = QHBoxLayout()
        self.get_ai_hint_button = QPushButton("Get AI Hint")
        self.get_ai_hint_button.clicked.connect(self.game.request_ai_hint)
        self.get_ai_hint_button.setCheckable(False) # Not checkable
        hint_button_layout.addWidget(self.get_ai_hint_button)
        hints_powerups_layout.addLayout(hint_button_layout)

        self.powerup_layout = QHBoxLayout()
        self.extra_hint_powerup_button = QPushButton("Extra Hint (0)")
        self.extra_hint_powerup_button.clicked.connect(lambda: self.game.use_power_up("extra_hint"))
        self.powerup_layout.addWidget(self.extra_hint_powerup_button)

        self.retry_powerup_button = QPushButton("Retry (0)")
        self.retry_powerup_button.clicked.connect(lambda: self.game.use_power_up("retry"))
        self.powerup_layout.addWidget(self.retry_powerup_button)

        self.reveal_digit_powerup_button = QPushButton("Reveal Digit (0)")
        self.reveal_digit_powerup_button.clicked.connect(lambda: self.game.use_power_up("reveal_digit"))
        self.powerup_layout.addWidget(self.reveal_digit_powerup_button)
        
        hints_powerups_layout.addLayout(self.powerup_layout)
        self.layout.addWidget(hints_powerups_group)

        # Confetti overlay
        self.confetti_effect = ConfettiEffect(self.parentWidget()) # Parent it to the main window
        self.confetti_effect.hide() # Start hidden

        self.update_styles()

    def update_styles(self):
        """Applies current theme styles to all relevant widgets in this view."""
        button_style = self.theme_manager.get_button_stylesheet()
        self.title_label.setStyleSheet(self.theme_manager.get_button_stylesheet().split('QPushButton')[0] + "font-size: 28px; font-weight: bold;") # Reuse some general styling
        
        # Apply style to all buttons and inputs
        for btn in [self.guess_button, self.new_game_button, self.time_trial_button, self.get_ai_hint_button, self.extra_hint_powerup_button,
                    self.retry_powerup_button, self.reveal_digit_powerup_button]:
            btn.setStyleSheet(button_style)
        
        for input_widget in [self.input_field]:
            input_widget.setStyleSheet(button_style) # QLineEdit styling is part of button_style for consistency
        
        # Update text labels
        text_color = DEFAULT_THEMES["Default Dark"]["window_text"].name() if self.settings.get_setting("dark_mode") else DEFAULT_THEMES["Default Light"]["window_text"].name()
        self.difficulty_label.setStyleSheet(f"color: {text_color};")
        self.guesses_label.setStyleSheet(f"color: {text_color};")
        self.time_label.setStyleSheet(f"color: {text_color};")
        self.ai_hint_label.setStyleSheet(f"color: {text_color};")
        self.findChild(QGroupBox).setStyleSheet(f"QGroupBox {{ color: {text_color}; font-weight: bold; }}")

    def _start_new_game_dialog(self, first_time=False):
        """Opens a dialog to select difficulty for a new game.
        If first_time=True, shows a welcome message after creating a new game."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Start New Game")
        layout = QVBoxLayout(dialog)

        layout.addWidget(QLabel("Select Difficulty:"))
        difficulty_selector = QComboBox()
        difficulty_selector.addItems(["Easy", "Medium", "Hard", "Adaptive"])
        difficulty_selector.setCurrentText(self.game.difficulty)
        layout.addWidget(difficulty_selector)

        # Min/Max inputs, pre-filled from current settings, but allow override
        layout.addWidget(QLabel("Custom Range (Optional):"))
        range_layout = QHBoxLayout()
        min_label = QLabel("Min:")
        min_spin = QSpinBox()
        min_spin.setRange(-99999, 99999)
        min_spin.setValue(self.settings.get_setting("min_val"))
        range_layout.addWidget(min_label)
        range_layout.addWidget(min_spin)

        max_label = QLabel("Max:")
        max_spin = QSpinBox()
        max_spin.setRange(-99999, 99999)
        max_spin.setValue(self.settings.get_setting("max_val"))
        range_layout.addWidget(max_label)
        range_layout.addWidget(max_spin)
        layout.addLayout(range_layout)
        
        start_button = QPushButton("Start Game")
        start_button.clicked.connect(dialog.accept)
        layout.addWidget(start_button)
        
        # Apply theme
        dialog.setStyleSheet(self.theme_manager.get_button_stylesheet())
        dialog.findChild(QComboBox).setStyleSheet(self.theme_manager.get_button_stylesheet())
        for spin in dialog.findChildren(QSpinBox):
            spin.setStyleSheet(self.theme_manager.get_button_stylesheet())
        for i, label in enumerate(dialog.findChildren(QLabel)):
            label.setStyleSheet(
                f"color: {DEFAULT_THEMES['Default Dark']['window_text'].name() if self.settings.get_setting('dark_mode') else DEFAULT_THEMES['Default Light']['window_text'].name()};"
            )

        if dialog.exec() == QDialog.Accepted:
            selected_difficulty = difficulty_selector.currentText()
            custom_min = min_spin.value()
            custom_max = max_spin.value()
            self.game.start_new_game(selected_difficulty, custom_min, custom_max)
            self._update_game_info_labels()
            self.input_field.setPlaceholderText(f"Enter number ({self.game.min_val}-{self.game.max_val})")

            # Show welcome if first-time launch
            if first_time:
                QMessageBox.information(self, "Welcome!", "🎉 Welcome to The Guessing Game! 🎉\nSetting things up for you…")

    def _start_time_trial_game(self):
        """Starts a new game in Time Trial mode."""
        self.game.start_new_game("Time Trial", time_trial=True)
        self._update_game_info_labels()
        self.input_field.setPlaceholderText(f"Enter number ({self.game.min_val}-{self.game.max_val})")
        QMessageBox.information(self, "Time Trial Started!", f"Guess the number between {self.game.min_val}-{self.game.max_val} before time runs out!")


    def _update_game_info_labels(self):
        """Updates labels showing current difficulty, guesses, power-ups, and AI hint state."""
        # Update basic game info
        self.difficulty_label.setText(
            f"Difficulty: {self.game.difficulty}{' (Time Trial)' if self.game.time_trial_mode else ''}"
        )
        self.guesses_label.setText(f"Guesses: {self.game.guesses_made}")
        self.input_field.setPlaceholderText(f"Enter number ({self.game.min_val}-{self.game.max_val})")

        # Update power-up buttons
        self.extra_hint_powerup_button.setText(f"Extra Hint ({self.game.power_ups['extra_hint']})")
        self.retry_powerup_button.setText(f"Retry ({self.game.power_ups['retry']})")
        self.reveal_digit_powerup_button.setText(f"Reveal Digit ({self.game.power_ups['reveal_digit']})")

        # Enable/disable power-ups based on availability
        self.extra_hint_powerup_button.setEnabled(self.game.power_ups['extra_hint'] > 0)
        self.retry_powerup_button.setEnabled(self.game.power_ups['retry'] > 0)
        self.reveal_digit_powerup_button.setEnabled(self.game.power_ups['reveal_digit'] > 0)

        # AI Hint: Update label only if not currently loading
        if not getattr(self, 'ai_hint_request_in_progress', False):
            self.ai_hint_label.setText("AI Hint: (Request a hint)")


    def _update_timer_display(self, time_remaining):
        """Updates the timer display for Time Trial mode."""
        if time_remaining >= 0:
            self.time_label.setText(f"Time: {time_remaining}s")
            self.sound_manager.play_sfx("tick")
        else:
            self.time_label.setText("Time: 0s - Ended!")

    def _handle_game_over(self, won, guesses, time_taken):
        """Handles game over logic (win/lose) and triggers stats & achievements."""
        
        # Load current stats
        stats = self.game.stats.get_stats()
        
        if won:
            message = random.choice(WIN_MESSAGES) + f"\nYou guessed it in {guesses} tries!"
            if self.game.time_trial_mode:
                message += f" Time: {time_taken:.2f}s."
            QMessageBox.information(self, "You Won!", message)
            
            if self.settings.get_setting("confetti_on_win"):
                self.confetti_effect.show_confetti()
            
            # Update stats
            stats["total_wins"] = stats.get("total_wins", 0) + 1
            stats[f"wins_{self.game.difficulty.lower()}"] = stats.get(f"wins_{self.game.difficulty.lower()}", 0) + 1
            stats["current_streak"] = stats.get("current_streak", 0) + 1
            stats["max_streak"] = max(stats.get("max_streak", 0), stats["current_streak"])
            if self.game.difficulty == "Hard" and guesses <= 5:
                stats["hard_five_guess_wins"] = stats.get("hard_five_guess_wins", 0) + 1

            # Save updated stats
            self.game.stats.set_stats(stats)
            self.game.stats.save_stats()
            
            # Check & unlock achievements
            self._check_and_unlock_achievements(stats)
            
            # Update total wins, streaks, difficulty stats
            self.stats.increment("total_wins")
            self.stats.update_streak(True)
            # Daily streak tracking
            self.stats.update_daily_streak(True)
            
            # Offer a power-up reward for winning
            reward_powerup = random.choice(["extra_hint", "retry", "reveal_digit"])
            self.game.add_power_up(reward_powerup)
            QMessageBox.information(self, "Reward!", f"You won a {reward_powerup.replace('_', ' ').title()} power-up!")
            
            daily_streak = self.stats.get_stats().get("daily_streak", 0)
            QMessageBox.information(None, "Daily Streak", f"Your current daily streak: {daily_streak} 🔥")

        else:
            message = random.choice(LOSE_MESSAGES) + f"\nThe number was {self.game.target_number}."
            QMessageBox.warning(self, "Game Over", message)
            
            # Update stats
            stats["total_losses"] = stats.get("total_losses", 0) + 1
            stats["current_streak"] = 0  # reset streak
            self.game.stats.set_stats(stats)
            self.game.stats.save_stats()
            
            # Check & unlock achievements
            self._check_and_unlock_achievements(stats)
            self.stats.increment("total_losses")
            self.stats.update_streak(False)
        
        # Reset and start new game
        self.game.clear_saved_game_state()
        self.game.start_new_game(self.game.difficulty)
        self._update_game_info_labels()


    def _check_and_unlock_achievements(self, stats):
        """Use stats to unlock achievements immediately."""
        achievements = self.game.achievements.get_all_achievements()
        
        # Mapping achievements to conditions
        conditions = {
            "First Win!": stats.get("total_wins", 0) >= 1,
            "Easy Mode Master": stats.get("wins_easy", 0) >= 5,
            "Medium Challenger": stats.get("wins_medium", 0) >= 5,
            "Hardcore Guesser": stats.get("wins_hard", 0) >= 3,
            "Guessing Streak (3)": stats.get("current_streak", 0) >= 3,
            "Guessing Streak (5)": stats.get("current_streak", 0) >= 5,
            "Quick Thinker": stats.get("time_trial_wins", 0) >= 1,
            "Power User": stats.get("powerups_used", 0) >= 1,
            "AI Apprentice": stats.get("ai_hints_used", 0) >= 1,
            "Ultimate Guesser": stats.get("hard_five_guess_wins", 0) >= 1
        }
        
        # Unlock achievements
        for key, condition_met in conditions.items():
            if key in achievements and not achievements[key]["unlocked"] and condition_met:
                achievements[key]["unlocked"] = True
                self.game.achievements.save_achievements()
                # Play sound & emit signal
                if self.game.sound_manager:
                    self.game.sound_manager.play_sfx("achievement_unlock")
                self.game.achievements.achievement_unlocked.emit(
                    key,
                    achievements[key]["description"],
                    achievements[key]["badge"]
                )

    def check_guess(self):
        """Processes a player's guess."""
        self.sound_manager.play_sfx("button_click")
        try:
            guess = int(self.input_field.text())
            if not (self.game.min_val <= guess <= self.game.max_val):
                QMessageBox.warning(self, "Invalid Guess", f"Please enter a number between {self.game.min_val} and {self.game.max_val}!")
                self.input_field.clear()
                return

            result = self.game.check_guess(guess)
            if result == "correct":
                # Message box handled by _handle_game_over
                pass
            else:
                msg = random.choice(INCORRECT_MESSAGES)
                if self.settings.get_setting("hints_enabled"):
                    msg += " 🔺 Too low!" if result == "too_low" else " 🔻 Too high!"
                QMessageBox.warning(self, "Try Again", msg)
            self.input_field.clear()
            self.input_field.setFocus() # Keep focus on input field

        except ValueError:
            self.sound_manager.play_sfx("incorrect_guess")
            # Shake animation for invalid input
            self._shake_widget(self.input_field)
            QMessageBox.warning(self, "Invalid Input", "Please enter a valid number! ⚠️")
            self.input_field.clear()
            self.input_field.setFocus()

    def _shake_widget(self, widget):
        """Applies a shake animation to a widget."""
        shake_animation = QPropertyAnimation(widget, b"pos")
        shake_animation.setDuration(200)
        shake_animation.setLoopCount(3)
        shake_animation.setKeyValueAt(0, widget.pos())
        shake_animation.setKeyValueAt(0.1, widget.pos() + QPoint(5, 0).to_qt_point())
        shake_animation.setKeyValueAt(0.2, widget.pos() - QPoint(5, 0).to_qt_point())
        shake_animation.setKeyValueAt(0.3, widget.pos() + QPoint(5, 0).to_qt_point())
        shake_animation.setKeyValueAt(0.4, widget.pos() - QPoint(5, 0).to_qt_point())
        shake_animation.setKeyValueAt(0.5, widget.pos() + QPoint(5, 0).to_qt_point())
        shake_animation.setKeyValueAt(1, widget.pos())
        shake_animation.start()

    def _display_ai_hint(self, hint):
        """Displays the AI-generated hint."""
        self.ai_hint_label.setText(f"AI Hint: {hint}")

    def _toggle_ai_hint_loading_state(self, is_loading):
        """Toggles the state of the AI hint button and label during loading."""
        if is_loading:
            self.get_ai_hint_button.setText("AI Thinking...")
            self.get_ai_hint_button.setEnabled(False)
            self.ai_hint_label.setText("AI Hint: AI is thinking...")
        else:
            self.get_ai_hint_button.setText("Get AI Hint")
            self.get_ai_hint_button.setEnabled(True)

class LeaderboardView(QWidget):
    """Displays the interactive and animated leaderboard."""
    def __init__(self, leaderboard_service, settings_service, theme_manager, parent=None):
        super().__init__(parent)
        self.leaderboard = leaderboard_service
        self.settings = settings_service
        self.theme_manager = theme_manager


        self.animation_running = False # Flag to prevent multiple animations simultaneously
        self.anim = None # Store Matplotlib animation object

        self.init_ui()
        self.update_leaderboard_chart() # Initial chart draw
        self.update_table()

    def init_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(15)
        self.layout.setAlignment(Qt.AlignCenter)

        title_label = QLabel("🏆 Global Leaderboard 🏆")
        title_label.setObjectName("titleLabel")
        title_label.setStyleSheet("font-size: 28px; font-weight: bold;")
        title_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(title_label)

        # Difficulty filter
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Filter by Difficulty:"))
        self.difficulty_filter = QComboBox()
        self.difficulty_filter.addItems(["Easy", "Medium", "Hard", "Time Trial"])
        self.difficulty_filter.currentTextChanged.connect(self.update_leaderboard_display)
        filter_layout.addWidget(self.difficulty_filter)
        self.layout.addLayout(filter_layout)

        # Matplotlib Chart
        self.figure = Figure(figsize=(8, 4))
        self.canvas = FigureCanvas(self.figure)
        self.layout.addWidget(self.canvas)

        # Table View for detailed scores
        self.leaderboard_table = QTableWidget()
        self.leaderboard_table.setColumnCount(4)
        self.leaderboard_table.setHorizontalHeaderLabels(["Rank", "Name", "Score", "Date/Time"])
        self.leaderboard_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.leaderboard_table.setEditTriggers(QTableWidget.NoEditTriggers) # Make table read-only
        self.layout.addWidget(self.leaderboard_table)
        
        # Reset Button
        self.reset_leaderboard_button = QPushButton("Reset Leaderboard")
        self.reset_leaderboard_button.clicked.connect(self._reset_leaderboard_confirm)
        self.layout.addWidget(self.reset_leaderboard_button)
        
        self.update_styles()

    def update_styles(self):
        """Applies current theme styles to all relevant widgets in this view."""
        button_style = self.theme_manager.get_button_stylesheet()
        text_color = (DEFAULT_THEMES["Default Dark"]["window_text"].name() 
                    if self.settings.get_setting("dark_mode") 
                    else DEFAULT_THEMES["Default Light"]["window_text"].name())

        # Title label
        if hasattr(self, "title_label"):
            self.title_label.setStyleSheet(
                self.theme_manager.get_button_stylesheet().split('QPushButton')[0] +
                "font-size: 28px; font-weight: bold;"
            )

        # Filter label
        if hasattr(self, "filter_label"):
            self.filter_label.setStyleSheet(f"color: {text_color};")

        # Buttons
        if hasattr(self, "difficulty_filter"):
            self.difficulty_filter.setStyleSheet(button_style)
        if hasattr(self, "reset_leaderboard_button"):
            self.reset_leaderboard_button.setStyleSheet(button_style)

        # Leaderboard table
        if hasattr(self, "leaderboard_table"):
            self.leaderboard_table.setStyleSheet(f"""
                QTableWidget {{
                    background-color: {DEFAULT_THEMES['Default Dark']['base'].name() if self.settings.get_setting('dark_mode') else DEFAULT_THEMES['Default Light']['base'].name()};
                    color: {text_color};
                    border: 1px solid {text_color};
                    selection-background-color: {DEFAULT_THEMES['Default Dark']['highlight'].name() if self.settings.get_setting('dark_mode') else DEFAULT_THEMES['Default Light']['highlight'].name()};
                    gridline-color: {QColor(text_color).darker(150).name()};
                }}
                QHeaderView::section {{
                    background-color: {DEFAULT_THEMES['Default Dark']['button'].name() if self.settings.get_setting('dark_mode') else DEFAULT_THEMES['Default Light']['button'].name()};
                    color: {DEFAULT_THEMES['Default Dark']['button_text'].name() if self.settings.get_setting('dark_mode') else DEFAULT_THEMES['Default Light']['button_text'].name()};
                    padding: 5px;
                    border: 1px solid {QColor(text_color).darker(150).name()};
                }}
            """)

    def _reset_leaderboard_confirm(self):
        """Confirms and resets the leaderboard."""
        reply = QMessageBox.question(self, "Reset Leaderboard",
                                    "Are you sure you want to reset ALL leaderboard data? This cannot be undone.",
                                    QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.leaderboard.reset_leaderboard()
            self.update_leaderboard_display()
            QMessageBox.information(self, "Leaderboard Reset", "Leaderboard has been successfully reset!")

    def update_leaderboard_display(self):
        """Updates both chart and table based on current filter."""
        self.update_leaderboard_chart()
        self.update_table()

    def update_leaderboard_chart(self):
        """
        Updates the Matplotlib bar chart with animated transitions.
        This uses Matplotlib's FuncAnimation for smooth transitions.
        """
        if self.anim: # Stop previous animation if running
            self.anim.event_source.stop()

        self.figure.clear()
        ax = self.figure.add_subplot(111)
        
        current_difficulty = self.difficulty_filter.currentText()
        top_scores = self.leaderboard.get_top_scores(current_difficulty, limit=5) # Show top 5 in chart
        
        names = [score["name"] for score in top_scores]
        scores = [score["guesses"] if current_difficulty != "Time Trial" else score["time"] for score in top_scores]
        
        # If no scores, display placeholder
        if not scores:
            names = ["No Scores Yet"]
            scores = [0]
            ax.text(0.5, 0.5, "No scores recorded for this difficulty.", horizontalalignment='center', verticalalignment='center', transform=ax.transAxes, color='gray', fontsize=12)
            
        x_pos = np.arange(len(names))
        
        # Get chart bar colors from settings, default if not set
        chart_colors = self.settings.get_setting("chart_bar_colors")
        if not chart_colors or not isinstance(chart_colors, list) or len(chart_colors) < len(x_pos):
            chart_colors = self.theme_manager.get_current_theme_data()["chart_bars"]
        
        # Create initial bars with zero height for animation start
        bars = ax.bar(x_pos, np.zeros_like(scores), color=chart_colors[:len(x_pos)]) # Use numpy zeros for initial animation
        
        ax.set_xticks(x_pos)
        ax.set_xticklabels(names, rotation=45, ha="right")
        ax.set_ylabel("Fewest Guesses" if current_difficulty != "Time Trial" else "Fastest Time (s)")
        ax.set_title(f"Top 5 Scores - {current_difficulty}")
        ax.set_ylim(0, max(scores + [1]) * 1.2) # Ensure Y-axis is scaled correctly

        # Set chart background and text colors based on theme
        bg_color = DEFAULT_THEMES["Default Dark"]["window_bg"] if self.settings.get_setting("dark_mode") else DEFAULT_THEMES["Default Light"]["window_bg"]
        text_color = DEFAULT_THEMES["Default Dark"]["window_text"] if self.settings.get_setting("dark_mode") else DEFAULT_THEMES["Default Light"]["window_text"]
        ax.set_facecolor(bg_color.name())
        self.figure.set_facecolor(bg_color.name())
        ax.tick_params(axis='x', colors=text_color.name())
        ax.tick_params(axis='y', colors=text_color.name())
        ax.xaxis.label.set_color(text_color.name())
        ax.yaxis.label.set_color(text_color.name())
        ax.title.set_color(text_color.name())

        # Animation function
        def animate(i):
            if i >= len(scores):
                # Ensure all bars have reached their final height
                for bar_idx, bar in enumerate(bars):
                    if bar_idx < len(scores):
                        bar.set_height(scores[bar_idx])
                return bars # return bars for all frames
            
            # Gradually increase height up to the final score
            for bar_idx, bar in enumerate(bars):
                if bar_idx < len(scores):
                    target_height = scores[bar_idx]
                    current_height = bar.get_height()
                    # Linear interpolation for smooth growth
                    new_height = current_height + (target_height - current_height) * 0.1
                    bar.set_height(new_height)
            return bars

        # Start animation only if scores are present and non-zero
        if any(s > 0 for s in scores):
            self.anim = animation.FuncAnimation(self.figure, animate, frames=20, interval=50, blit=True) # 1 second animation (20 frames * 50ms)
        else:
            self.canvas.draw() # Just draw static chart if no animation needed

        self.canvas.draw()


    def update_table(self):
        """Populates the QTableWidget with leaderboard data."""
        current_difficulty = self.difficulty_filter.currentText()
        top_scores = self.leaderboard.get_top_scores(current_difficulty, limit=50) # Show more in table

        self.leaderboard_table.setRowCount(len(top_scores))
        
        # Adjust header labels for Time Trial
        if current_difficulty == "Time Trial":
            self.leaderboard_table.setHorizontalHeaderLabels(["Rank", "Name", "Time (s)", "Date/Time"])
        else:
            self.leaderboard_table.setHorizontalHeaderLabels(["Rank", "Name", "Guesses", "Date/Time"])


        for row, score in enumerate(top_scores):
            self.leaderboard_table.setItem(row, 0, QTableWidgetItem(str(row + 1)))
            self.leaderboard_table.setItem(row, 1, QTableWidgetItem(score["name"]))
            
            score_value = f"{score['time']:.2f}" if current_difficulty == "Time Trial" else str(score["guesses"])
            self.leaderboard_table.setItem(row, 2, QTableWidgetItem(score_value))
            self.leaderboard_table.setItem(row, 3, QTableWidgetItem(score["date"]))

        self.leaderboard_table.resizeRowsToContents()

class AchievementsView(QWidget):
    """Displays the player's achievements and their status."""
    def __init__(self, achievement_service, settings_service, theme_manager, parent=None):
        super().__init__(parent)
        self.achievements = achievement_service
        self.settings = settings_service
        self.theme_manager = theme_manager
        self.init_ui()
        self.update_achievements_display()

    def init_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(15)
        self.layout.setAlignment(Qt.AlignTop | Qt.AlignCenter)

        title_label = QLabel("🌟 Achievements 🌟")
        title_label.setObjectName("titleLabel")
        title_label.setStyleSheet("font-size: 28px; font-weight: bold;")
        title_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(title_label)
        
        # Scroll area for achievements
        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        self.achievement_list_widget = QWidget()
        self.achievement_list_layout = QVBoxLayout(self.achievement_list_widget)
        self.achievement_list_layout.setAlignment(Qt.AlignTop)
        scroll_area.setWidget(self.achievement_list_widget)
        self.layout.addWidget(scroll_area)

        self.reset_achievements_button = QPushButton("Reset All Achievements")
        self.reset_achievements_button.clicked.connect(self._reset_achievements_confirm)
        self.layout.addWidget(self.reset_achievements_button)
        
        self.update_styles()

    def update_styles(self):
        """Applies current theme styles to all relevant widgets in this view."""
        button_style = self.theme_manager.get_button_stylesheet()
        text_color = DEFAULT_THEMES["Default Dark"]["window_text"].name() if self.settings.get_setting("dark_mode") else DEFAULT_THEMES["Default Light"]["window_text"].name()
        
        self.findChild(QLabel, "titleLabel").setStyleSheet(self.theme_manager.get_button_stylesheet().split('QPushButton')[0] + "font-size: 28px; font-weight: bold;")
        self.reset_achievements_button.setStyleSheet(button_style)
        
        self.achievement_list_widget.setStyleSheet(f"background-color: transparent; color: {text_color};")
        self.findChild(QScrollArea).setStyleSheet(f"QScrollArea {{ border: none; }}")


    def update_achievements_display(self):
        """Populates the achievements list."""
        # Clear existing widgets
        for i in reversed(range(self.achievement_list_layout.count())):
            widget = self.achievement_list_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()

        all_achievements = self.achievements.get_all_achievements()
        text_color = DEFAULT_THEMES["Default Dark"]["window_text"].name() if self.settings.get_setting("dark_mode") else DEFAULT_THEMES["Default Light"]["window_text"].name()

        for title, data in all_achievements.items():
            frame = QFrame(self)
            frame_layout = QHBoxLayout(frame)
            
            badge_label = QLabel(data["badge"])
            badge_label.setFont(QFont("Segoe UI Emoji", 24))
            frame_layout.addWidget(badge_label)

            text_layout = QVBoxLayout()
            title_label = QLabel(title)
            title_label.setFont(QFont("Arial", 14, QFont.Bold))
            title_label.setStyleSheet(f"color: {text_color};")
            
            desc_label = QLabel(data["description"])
            desc_label.setWordWrap(True)
            desc_label.setStyleSheet(f"color: {QColor(text_color).darker(150).name() if data['unlocked'] else QColor(text_color).lighter(150).name()};")
            
            text_layout.addWidget(title_label)
            text_layout.addWidget(desc_label)
            frame_layout.addLayout(text_layout)
            
            status_label = QLabel("Unlocked" if data["unlocked"] else "Locked")
            status_label.setFont(QFont("Arial", 12, QFont.Bold))
            status_label.setStyleSheet(f"color: {'gold' if data['unlocked'] else 'grey'};")
            frame_layout.addWidget(status_label, alignment=Qt.AlignRight)

            frame.setFrameShape(QFrame.StyledPanel)
            frame.setFrameShadow(QFrame.Raised)
            frame.setStyleSheet(f"""
                QFrame {{
                    background-color: {DEFAULT_THEMES["Default Dark"]["button"].name() if self.settings.get_setting("dark_mode") else DEFAULT_THEMES["Default Light"]["button"].name()};
                    border-radius: 10px;
                    padding: 10px;
                    border: 1px solid {'gold' if data['unlocked'] else 'gray'};
                }}
            """)
            self.achievement_list_layout.addWidget(frame)

    def _reset_achievements_confirm(self):
        """Confirms and resets all achievements."""
        self.sound_manager.play_sfx("button_click")
        reply = QMessageBox.question(self, "Reset Achievements",
                                    "Are you sure you want to reset ALL achievement progress? This cannot be undone.",
                                    QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.achievements.reset_achievements()
            self.update_achievements_display()
            QMessageBox.information(self, "Achievements Reset", "All achievements have been reset to locked state!")

class StatsView(QWidget):
    """Displays player statistics."""
    def __init__(self, stats_service, settings_service, theme_manager, sound_manager=None, achievement_service=None, parent=None):
        super().__init__(parent)
        self.stats = stats_service
        self.settings = settings_service
        self.theme_manager = theme_manager
        self.sound_manager = sound_manager  # Optional
        self.achievement_service = achievement_service  # NEW
        self.init_ui()
        self.update_stats_display()

    def update_achievements_from_stats(self):
        if not self.achievement_service:
            return

        stats = self.stats.get_stats()
        current_streak = stats.get("current_streak", 0)
        easy_wins = stats.get("easy_wins", 0)
        medium_wins = stats.get("medium_wins", 0)
        hard_wins = stats.get("hard_wins", 0)
        ai_hints_used = stats.get("ai_hints_used", 0)
        powerups_used = stats.get("powerups_used", 0)
        average_guesses = self.stats.get_average_guesses()

        # Unlock achievements
        self.achievement_service.check_and_unlock("First Win!", stats.get("total_wins", 0) >= 1)
        self.achievement_service.check_and_unlock("Easy Mode Master", easy_wins >= 5)
        self.achievement_service.check_and_unlock("Medium Challenger", medium_wins >= 5)
        self.achievement_service.check_and_unlock("Hardcore Guesser", hard_wins >= 3)
        self.achievement_service.check_and_unlock("Guessing Streak (3)", current_streak >= 3)
        self.achievement_service.check_and_unlock("Guessing Streak (5)", current_streak >= 5)
        self.achievement_service.check_and_unlock("Quick Thinker", stats.get("time_trial_wins", 0) >= 1)
        self.achievement_service.check_and_unlock("Power User", powerups_used >= 1)
        self.achievement_service.check_and_unlock("AI Apprentice", ai_hints_used >= 1)
        self.achievement_service.check_and_unlock("Ultimate Guesser",
                                                hard_wins >= 1 and average_guesses <= 5)


    def init_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(15)
        self.layout.setAlignment(Qt.AlignTop | Qt.AlignCenter)

        # Title
        self.title_label = QLabel("📊 Player Statistics 📊")
        self.title_label.setObjectName("titleLabel")
        self.title_label.setStyleSheet("font-size: 28px; font-weight: bold;")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.title_label)
        
        # Stats grid
        self.stats_grid = QGridLayout()
        self.stats_grid.setSpacing(10)
        self.stat_labels = {}  # Store labels for easy updates

        stats_data = self.stats.get_stats()
        text_color = self._get_text_color()

        row = 0
        for key, value in stats_data.items():
            formatted_key = key.replace('_', ' ').title()
            label_key = QLabel(f"{formatted_key}:")
            label_key.setStyleSheet(f"font-weight: bold; color: {text_color};")
            self.stats_grid.addWidget(label_key, row, 0)

            label_value = QLabel(str(value))
            label_value.setStyleSheet(f"color: {text_color};")
            self.stats_grid.addWidget(label_value, row, 1)
            self.stat_labels[key] = label_value
            row += 1

        # Add average guesses
        avg_label_key = QLabel("Average Guesses:")
        avg_label_key.setStyleSheet(f"font-weight: bold; color: {text_color};")
        self.stats_grid.addWidget(avg_label_key, row, 0)

        avg_label_value = QLabel(f"{self.stats.get_average_guesses():.2f}")
        avg_label_value.setStyleSheet(f"color: {text_color};")
        self.stats_grid.addWidget(avg_label_value, row, 1)
        self.stat_labels["average_guesses"] = avg_label_value

        self.layout.addLayout(self.stats_grid)

        # Reset button
        self.reset_stats_button = QPushButton("Reset All Statistics")
        self.reset_stats_button.clicked.connect(self._reset_stats_confirm)
        self.layout.addWidget(self.reset_stats_button)

        self.update_styles()

    def _get_text_color(self):
        return (DEFAULT_THEMES["Default Dark"]["window_text"].name()
                if self.settings.get_setting("dark_mode")
                else DEFAULT_THEMES["Default Light"]["window_text"].name())

    def update_styles(self):
        """Applies current theme styles to all relevant widgets."""
        button_style = self.theme_manager.get_button_stylesheet()
        text_color = self._get_text_color()

        self.title_label.setStyleSheet(
            self.theme_manager.get_button_stylesheet().split('QPushButton')[0] +
            "font-size: 28px; font-weight: bold;"
        )

        self.reset_stats_button.setStyleSheet(button_style)

        # Update labels
        for key, label in self.stat_labels.items():
            label.setStyleSheet(f"color: {text_color};")
        # Bold for key labels
        for i in range(self.stats_grid.count()):
            widget = self.stats_grid.itemAt(i).widget()
            if isinstance(widget, QLabel) and ":" in widget.text():
                widget.setStyleSheet(f"font-weight: bold; color: {text_color};")

    def update_stats_display(self):
        """Updates the displayed statistics."""
        current_stats = self.stats.get_stats()
        for key, label in self.stat_labels.items():
            if key == "average_guesses":
                label.setText(f"{self.stats.get_average_guesses():.2f}")
            else:
                label.setText(str(current_stats.get(key, 0)))

        # Update achievements automatically
        self.update_achievements_from_stats()


    def _reset_stats_confirm(self):
        """Confirms and resets all statistics."""
        if self.sound_manager:
            self.sound_manager.play_sfx("button_click")
        reply = QMessageBox.question(self, "Reset Statistics",
                                     "Are you sure you want to reset ALL game statistics? This cannot be undone.",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.stats.reset_stats()
            self.update_stats_display()
            QMessageBox.information(self, "Statistics Reset", "All game statistics have been reset!")

class SettingsWindow(QDialog):
    """
    A comprehensive settings window that allows live customization of various game aspects.
    It applies changes immediately to the main window without closing.
    """
    settings_changed = Signal()  # Signal to notify MainWindow that settings have changed

    def __init__(self, settings_service, leaderboard_service, achievement_service,
                 statistics_service, sound_service, theme_manager, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings ⚙️")
        self.setMinimumSize(400, 600)

        # Store services
        self.settings = settings_service
        self.leaderboard = leaderboard_service
        self.achievements = achievement_service
        self.statistics = statistics_service
        self.sound_service = sound_service
        self.theme_manager = theme_manager

        # Modal so other windows don’t respond while open
        self.setModal(True)

        self.init_ui()
        self.apply_current_settings_to_ui()
        self.update_styles()  # Apply theme to itself

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)

        title_label = QLabel("⚙️ Game Settings ⚙️")
        title_label.setObjectName("titleLabel")
        title_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)

        # Scroll area for settings to handle many options
        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        settings_content_widget = QWidget()
        settings_layout = QVBoxLayout(settings_content_widget)
        settings_layout.setSpacing(10)
        settings_layout.setAlignment(Qt.AlignTop)
        

        # --- General Game Settings ---
        game_settings_group = QGroupBox("Gameplay Settings")
        game_settings_layout = QVBoxLayout(game_settings_group)

        self.hints_checkbox = QCheckBox("Enable Hints (Higher/Lower)")
        self.hints_checkbox.stateChanged.connect(lambda: self._setting_changed("hints_enabled", self.hints_checkbox.isChecked()))
        game_settings_layout.addWidget(self.hints_checkbox)

        self.confetti_checkbox = QCheckBox("Show Confetti on Win")
        self.confetti_checkbox.stateChanged.connect(lambda: self._setting_changed("confetti_on_win", self.confetti_checkbox.isChecked()))
        game_settings_layout.addWidget(self.confetti_checkbox)

        game_settings_layout.addWidget(QLabel("Set Custom Min and Max Numbers (for Easy/Medium/Hard)"))
        min_layout = QHBoxLayout()
        min_layout.addWidget(QLabel("Min:"))
        self.min_spin = QSpinBox()
        self.min_spin.setMinimum(-100000)
        self.min_spin.setMaximum(100000)
        self.min_spin.valueChanged.connect(lambda: self._setting_changed("min_val", self.min_spin.value()))
        min_layout.addWidget(self.min_spin)
        game_settings_layout.addLayout(min_layout)

        max_layout = QHBoxLayout()
        max_layout.addWidget(QLabel("Max:"))
        self.max_spin = QSpinBox()
        self.max_spin.setMinimum(-100000)
        self.max_spin.setMaximum(100000)
        self.max_spin.valueChanged.connect(lambda: self._setting_changed("max_val", self.max_spin.value()))
        max_layout.addWidget(self.max_spin)
        game_settings_layout.addLayout(max_layout)
        
        settings_layout.addWidget(game_settings_group)

        # --- Audio Settings ---
        audio_settings_group = QGroupBox("Audio Settings")
        audio_settings_layout = QVBoxLayout(audio_settings_group)

        # --- Music Volume ---
        audio_settings_layout.addWidget(QLabel("Music Volume:"))
        self.music_volume_slider = QSlider(Qt.Horizontal)
        self.music_volume_slider.setRange(0, 100)
        self.music_volume_slider.setValue(int(self.settings.get_setting("music_volume") * 100))

        # Live feedback: adjust volume instantly without saving
        self.music_volume_slider.valueChanged.connect(
            lambda val: self.sound_service.set_music_volume(val / 100.0)
        )

        # Save settings only when slider is released
        self.music_volume_slider.sliderReleased.connect(
            lambda: self._setting_changed("music_volume", self.music_volume_slider.value() / 100.0)
        )

        audio_settings_layout.addWidget(self.music_volume_slider)

        # --- SFX Volume ---
        audio_settings_layout.addWidget(QLabel("SFX Volume:"))
        self.sfx_volume_slider = QSlider(Qt.Horizontal)
        self.sfx_volume_slider.setRange(0, 100)
        self.sfx_volume_slider.setValue(int(self.settings.get_setting("sfx_volume") * 100))

        # Live feedback for SFX
        self.sfx_volume_slider.valueChanged.connect(
            lambda val: self.sound_service.set_sfx_volume(val / 100.0)
        )

        # Save SFX setting on release
        self.sfx_volume_slider.sliderReleased.connect(
            lambda: self._setting_changed("sfx_volume", self.sfx_volume_slider.value() / 100.0)
        )

        audio_settings_layout.addWidget(self.sfx_volume_slider)

        # Add the audio group to main settings layout
        settings_layout.addWidget(audio_settings_group)

        
        # --- Export/Import Settings ---
        export_import_group = QGroupBox("Export / Import Settings")
        export_import_layout = QVBoxLayout(export_import_group)

        self.export_button = QPushButton("Export Settings (Copy Encoded)")
        self.export_button.clicked.connect(self._export_settings)
        export_import_layout.addWidget(self.export_button)

        self.import_button = QPushButton("Import Settings (Paste Encoded)")
        self.import_button.clicked.connect(self._import_settings)
        export_import_layout.addWidget(self.import_button)

        settings_layout.addWidget(export_import_group)

        # --- Theme & Visual Settings (Live Editor) ---
        theme_settings_group = QGroupBox("Theme & Visual Settings (Live Editor)")
        theme_settings_layout = QVBoxLayout(theme_settings_group)

        self.darkmode_checkbox = QCheckBox("Enable Dark Mode")
        self.darkmode_checkbox.stateChanged.connect(self._toggle_dark_mode)
        theme_settings_layout.addWidget(self.darkmode_checkbox)

        theme_settings_layout.addWidget(QLabel("Color Theme:"))
        self.theme_select = QComboBox()
        self.theme_select.addItems(list(DEFAULT_THEMES.keys()))
        self.theme_select.currentTextChanged.connect(self._change_color_theme)
        theme_settings_layout.addWidget(self.theme_select)
        
        # Custom background color picker
        self.bg_color_picker_button = QPushButton("Choose Background Color")
        self.bg_color_picker_button.clicked.connect(self._pick_background_color)
        theme_settings_layout.addWidget(self.bg_color_picker_button)
        
        # Custom chart bar colors (example for 3 bars)
        theme_settings_layout.addWidget(QLabel("Chart Bar Colors (Leaderboard):"))
        self.chart_color_buttons = []
        chart_color_layout = QHBoxLayout()
        for i in range(3):
            btn = QPushButton(f"Bar {i+1}")
            btn.setFixedSize(60, 30)
            btn.clicked.connect(lambda checked, idx=i: self._pick_chart_bar_color(idx))
            self.chart_color_buttons.append(btn)
            chart_color_layout.addWidget(btn)
        theme_settings_layout.addLayout(chart_color_layout)

        # Font selection
        theme_settings_layout.addWidget(QLabel("App Font:"))
        self.font_select = QComboBox()
        # Get system fonts
        self.font_select.addItems(QFontDatabase.families())
        self.font_select.currentTextChanged.connect(lambda font_name: self._setting_changed("current_font", font_name))
        theme_settings_layout.addWidget(self.font_select)

        settings_layout.addWidget(theme_settings_group)
        scroll_area.setWidget(settings_content_widget)
        main_layout.addWidget(scroll_area)

        # --- Reset Options ---
        reset_group = QGroupBox("Reset Options")
        reset_layout = QVBoxLayout(reset_group)
        
        self.reset_leaderboard_button = QPushButton("Reset Leaderboard")
        self.reset_leaderboard_button.clicked.connect(self._reset_leaderboard)
        reset_layout.addWidget(self.reset_leaderboard_button)

        self.reset_achievements_button = QPushButton("Reset Achievements")
        self.reset_achievements_button.clicked.connect(self._reset_achievements)
        reset_layout.addWidget(self.reset_achievements_button)

        self.reset_stats_button = QPushButton("Reset All Statistics")
        self.reset_stats_button.clicked.connect(self._reset_statistics)
        reset_layout.addWidget(self.reset_stats_button)
        
        self.clear_save_game_button = QPushButton("Clear Saved Game")
        self.clear_save_game_button.clicked.connect(lambda: self.parent().game_service.clear_saved_game_state())
        reset_layout.addWidget(self.clear_save_game_button)

        self.reset_all_settings_button = QPushButton("Reset ALL Settings to Default")
        self.reset_all_settings_button.clicked.connect(self._reset_all_settings)
        reset_layout.addWidget(self.reset_all_settings_button)

        settings_layout.addWidget(reset_group)
        main_layout.addWidget(reset_group)

        # Save & Close button
        save_close_button = QPushButton("Save and Close Settings")
        save_close_button.clicked.connect(self.accept)
        main_layout.addWidget(save_close_button)

        self.setStyleSheet(self.theme_manager.get_button_stylesheet()) # Apply default style to all children
        
        # Apply initial styling to newly created QGroupBoxes within the settings_layout (nested)
        for group_box in [game_settings_group, audio_settings_group, theme_settings_group, reset_group]:
            group_box.setStyleSheet(f"""
                QGroupBox {{
                    font-weight: bold;
                    color: {DEFAULT_THEMES["Default Dark"]["window_text"].name() if self.settings.get_setting("dark_mode") else DEFAULT_THEMES["Default Light"]["window_text"].name()};
                    border: 1px solid {DEFAULT_THEMES["Default Dark"]["button"].name() if self.settings.get_setting("dark_mode") else DEFAULT_THEMES["Default Light"]["button"].name()};
                    border-radius: 5px;
                    margin-top: 1ex; /* leave space for title */
                }}
                QGroupBox::title {{
                    subcontrol-origin: margin;
                    subcontrol-position: top center; /* position at top center */
                    padding: 0 5px;
                    background-color: transparent;
                }}
                QLabel {{ color: {DEFAULT_THEMES["Default Dark"]["window_text"].name() if self.settings.get_setting("dark_mode") else DEFAULT_THEMES["Default Light"]["window_text"].name()}; }}
                QCheckBox {{ color: {DEFAULT_THEMES["Default Dark"]["window_text"].name() if self.settings.get_setting("dark_mode") else DEFAULT_THEMES["Default Light"]["window_text"].name()}; }}
            """)
        
        # Manually apply button stylesheet to specific buttons
        for btn in [self.bg_color_picker_button, save_close_button, self.reset_leaderboard_button,
                    self.reset_achievements_button, self.reset_stats_button, self.clear_save_game_button,
                    self.reset_all_settings_button] + self.chart_color_buttons:
            btn.setStyleSheet(self.theme_manager.get_button_stylesheet())
        
        # ComboBoxes, SpinBoxes also get their style from the general button_stylesheet if defined there
        self.theme_select.setStyleSheet(self.theme_manager.get_button_stylesheet())
        self.font_select.setStyleSheet(self.theme_manager.get_button_stylesheet())
        self.min_spin.setStyleSheet(self.theme_manager.get_button_stylesheet())
        self.max_spin.setStyleSheet(self.theme_manager.get_button_stylesheet())


    def apply_current_settings_to_ui(self):
        """Populates the settings UI elements with current settings values."""
        self.hints_checkbox.setChecked(self.settings.get_setting("hints_enabled"))
        self.darkmode_checkbox.setChecked(self.settings.get_setting("dark_mode"))
        self.theme_select.setCurrentText(self.settings.get_setting("color_theme"))
        self.min_spin.setValue(self.settings.get_setting("min_val"))
        self.max_spin.setValue(self.settings.get_setting("max_val"))
        self.music_volume_slider.setValue(int(self.settings.get_setting("music_volume") * 100))
        self.sfx_volume_slider.setValue(int(self.settings.get_setting("sfx_volume") * 100))
        self.confetti_checkbox.setChecked(self.settings.get_setting("confetti_on_win"))
        self.font_select.setCurrentText(self.settings.get_setting("current_font"))
        
        # Update chart color buttons with current colors
        current_chart_colors = self.settings.get_setting("chart_bar_colors")
        for i, btn in enumerate(self.chart_color_buttons):
            color = current_chart_colors[i] if i < len(current_chart_colors) else "#cccccc"
            btn.setStyleSheet(f"background-color: {color}; border: 1px solid gray; border-radius: 5px;")
        
        # Update background color button with current color
        current_bg_color = self.settings.get_setting("selected_bg_color")
        if current_bg_color:
            self.bg_color_picker_button.setStyleSheet(f"background-color: {current_bg_color}; color: {QColor(current_bg_color).lighter(150).name() if QColor(current_bg_color).lightness() < 128 else QColor(current_bg_color).darker(150).name()};")
        else:
            self.bg_color_picker_button.setStyleSheet(self.theme_manager.get_button_stylesheet()) # Reset to default button style

    def update_styles(self):
        """Applies theme manager styles to itself and its children."""
        self.theme_manager.current_theme_name = self.settings.get_setting("color_theme")
        self.theme_manager.dark_mode_enabled = self.settings.get_setting("dark_mode")
        self.theme_manager.apply_theme_to_app(QApplication.instance()) # Apply to entire app

        # Reapply styles to this window's widgets
        button_style = self.theme_manager.get_button_stylesheet()
        
        for widget in self.findChildren(QWidget): # Iterate all children to apply styles
            if isinstance(widget, (QPushButton, QComboBox, QLineEdit, QSpinBox, QCheckBox)):
                widget.setStyleSheet(button_style)
            elif isinstance(widget, QLabel):
                text_color = DEFAULT_THEMES["Default Dark"]["window_text"].name() if self.settings.get_setting("dark_mode") else DEFAULT_THEMES["Default Light"]["window_text"].name()
                widget.setStyleSheet(f"color: {text_color};")
            elif isinstance(widget, QGroupBox):
                text_color = DEFAULT_THEMES["Default Dark"]["window_text"].name() if self.settings.get_setting("dark_mode") else DEFAULT_THEMES["Default Light"]["window_text"].name()
                border_color = DEFAULT_THEMES["Default Dark"]["button"].name() if self.settings.get_setting("dark_mode") else DEFAULT_THEMES["Default Light"]["button"].name()
                widget.setStyleSheet(f"""
                    QGroupBox {{
                        font-weight: bold;
                        color: {text_color};
                        border: 1px solid {border_color};
                        border-radius: 5px;
                        margin-top: 1ex;
                    }}
                    QGroupBox::title {{
                        subcontrol-origin: margin;
                        subcontrol-position: top center;
                        padding: 0 5px;
                        background-color: transparent;
                    }}
                    QLabel {{ color: {text_color}; }} /* Labels inside groupbox */
                    QCheckBox {{ color: {text_color}; }} /* Checkboxes inside groupbox */
                    QSlider::groove:horizontal {{
                        border: 1px solid #999999;
                        height: 8px; /* the groove height */
                        background: {DEFAULT_THEMES["Default Dark"]["base"].name() if self.settings.get_setting("dark_mode") else DEFAULT_THEMES["Default Light"]["base"].name()};
                        margin: 2px 0;
                        border-radius: 4px;
                    }}
                    QSlider::handle:horizontal {{
                        background: {DEFAULT_THEMES["Default Dark"]["highlight"].name() if self.settings.get_setting("dark_mode") else DEFAULT_THEMES["Default Light"]["highlight"].name()};
                        border: 1px solid #5c5c5c;
                        width: 18px;
                        margin: -5px 0; /* handle is 16px wide, make it overlap with groove */
                        border-radius: 9px;
                    }}
                """)
            
            # Special case for the title label
            if widget.objectName() == "titleLabel":
                widget.setStyleSheet(self.theme_manager.get_button_stylesheet().split('QPushButton')[0] + "font-size: 24px; font-weight: bold;")
        
        # Re-update chart color buttons and background color button
        self.apply_current_settings_to_ui()

        # Notify other views to update
        self.settings_changed.emit()
        
    def _export_settings(self):
        """Copy current settings as Base64 encoded string to clipboard."""
        try:
            encoded = self.settings.export_settings()  # call SettingsService
            clipboard = QApplication.clipboard()
            clipboard.setText(encoded)
            self.sound_manager.play_sfx("button_click")
            QMessageBox.information(self, "Export Settings", "Settings copied to clipboard (encoded)!")
        except Exception as e:
            # Create a warning message box with selectable text
            msg_box = QMessageBox(self)
            msg_box.setIcon(QMessageBox.Icon.Warning)
            msg_box.setWindowTitle("Export Settings Failed")
            msg_box.setText("Failed to export settings:")
            msg_box.setDetailedText(str(e))  # Show error details in expandable area
            msg_box.exec()

    def _import_settings(self):
        """Paste Base64 string from user input and import settings."""
        text, ok = QInputDialog.getMultiLineText(
            self, "Import Settings", "Paste encoded settings:"
        )
        if not ok or not text.strip():
            return

        text_lower = text.strip().lower()

        # 🛠️ Special dev menu Easter egg
        if text_lower == "devmenu":
            import time
            uptime_seconds = int(time.time() - getattr(self.parent(), "start_time", time.time()))
            days, rem = divmod(uptime_seconds, 86400)
            hours, rem = divmod(rem, 3600)
            minutes, seconds = divmod(rem, 60)
            uptime_str = f"{days}d:{hours:02}h:{minutes:02}m:{seconds:02}s"

            QMessageBox.information(
                self,
                "Developer Menu",
                f"App Uptime: {uptime_str}\nBwahahahaha! You found a secret!!!!!"
            )
            return
        if text_lower == "starlight":
            QMessageBox.information(self, "So...", "i loved to but i liked starlight compiler or starlight glimmer or starlight zones\nbut ok, i promise.")
            return

        if text_lower == "guessit":
            QMessageBox.information(self, "Bruh...", "i thought you scramble it, but ok,\ni can do that.")
            return

        if text_lower == "erika":
            QMessageBox.information(self, "Uhh...", "Que sera sera...")
            return

        if text_lower == "template":
            QMessageBox.information(self, "Template Found", "This is a template message.")
            return

        if text_lower == "unicorn":
            QMessageBox.information(self, "✨ Magical!", "You summoned the legendary unicorn! 🦄")
            return

        if text_lower == "420":
            QMessageBox.information(self, "Haha...", "Time flies, but remember, keep it responsible! 🍃")
            return

        if text_lower == "rickroll":
            QMessageBox.information(self, "Never Gonna...", "You just got Rickrolled! 🎵")
            return

        if text_lower == "debugmode":
            QMessageBox.information(self, "Sneaky!", "Developer mode activated! Shh... 🤫")
            return

        if text_lower == "pizza":
            QMessageBox.information(self, "🍕 Yum!", "Pizza is life! Don’t forget extra cheese.")
            return

        if text_lower == "pogchamp":
            QMessageBox.information(self, "Pog!", "You found the ultimate hype! PogChamp! 😎")
            return

        if text_lower == "cookie":
            QMessageBox.information(self, "🍪 Sweet!", "Here’s a cookie for you! But don’t eat your screen.")
            return

        if text_lower == "brainpower":
            QMessageBox.information(self, "🧠 Genius!", "Your brain is on overdrive. Keep thinking big!")
            return

        if text_lower == "oops":
            QMessageBox.information(self, "Oopsie!", "Nothing happened… or did it? 🤔")
            return
        # 🚀 Special case: launch recovery tool
        if text_lower == "recovery":
            reply = QMessageBox.question(
                self,
                "Run Recovery Mode?",
                "Do you want to launch the Recovery Tool to repair your data?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                import subprocess, sys, os, traceback

                try:
                    # Determine base folder (works with PyInstaller)
                    if getattr(sys, 'frozen', False):
                        # PyInstaller: scripts folder is __file__'s parent
                        base_path = os.path.dirname(sys.executable)
                    else:
                        # Development
                        base_path = os.path.dirname(os.path.abspath(__file__))

                    # Recovery targets
                    recovery_exe = os.path.join(base_path, "recovery.exe")
                    recovery_py = os.path.join(base_path, "recovery.py")

                    if os.path.exists(recovery_exe):
                        subprocess.Popen([recovery_exe])
                    elif os.path.exists(recovery_py):
                        subprocess.Popen([sys.executable, recovery_py])
                    else:
                        raise FileNotFoundError(f"Recovery tool not found in {base_path}")

                    # Close main window and exit
                    self.close()
                    sys.exit(0)

                except Exception as e:
                    tb = traceback.format_exc()
                    msg_box = QMessageBox()
                    msg_box.setIcon(QMessageBox.Critical)
                    msg_box.setWindowTitle("Recovery Failed")
                    msg_box.setText(f"Failed to launch recovery:\n{e}")
                    msg_box.setDetailedText(tb)
                    msg_box.exec()


                except Exception as e:
                    tb = traceback.format_exc()
                    msg_box = QMessageBox()
                    msg_box.setIcon(QMessageBox.Critical)
                    msg_box.setWindowTitle("Recovery Failed")
                    msg_box.setText(f"Failed to launch Recovery Tool:\n{e}")
                    msg_box.setDetailedText(tb)
                    msg_box.exec()

        # ✅ Normal import flow
        success, msg = self.settings.import_settings(text)
        if success:
            self.sound_manager.play_sfx("button_click")
            QMessageBox.information(self, "Import Settings", msg)
        else:
            msg_box = QMessageBox(self)
            msg_box.setIcon(QMessageBox.Icon.Warning)
            msg_box.setWindowTitle("Import Settings Failed")
            msg_box.setText("Failed to import settings.")
            msg_box.setDetailedText(msg)
            msg_box.exec()

    def _setting_changed(self, key, value):
        """Generic handler for settings changes."""
        self.settings.set_setting(key, value)
        self.update_styles() # Reapply all styles immediately

    def _toggle_dark_mode(self, state):
        """Handles dark mode toggle."""
        self.settings.set_setting("dark_mode", state)
        if state: # When dark mode is enabled, force theme selection to "Default Dark"
            self.theme_select.setCurrentText("Default Dark")
            self.settings.set_setting("color_theme", "Default Dark")
        self.update_styles()

    def _change_color_theme(self, theme_name):
        """Handles color theme selection."""
        self.settings.set_setting("color_theme", theme_name)
        # If selecting a custom theme, ensure dark mode is off (unless "Default Dark" is selected)
        if theme_name != "Default Dark":
            self.darkmode_checkbox.setChecked(False)
            self.settings.set_setting("dark_mode", False)
        
        # Reset custom background color if a named theme is chosen
        self.settings.set_setting("selected_bg_color", DEFAULT_THEMES[theme_name]["bg"].split(': ')[1].replace(';', ''))
        self.settings.set_setting("chart_bar_colors", DEFAULT_THEMES[theme_name]["chart_bars"])

        self.update_styles()

    def _pick_background_color(self):
        """Opens a color dialog to pick a custom background color."""
        self.sound_service.play_sfx("button_click")
        initial_color = QColor(self.settings.get_setting("selected_bg_color"))
        color = QColorDialog.getColor(initial_color, self, "Choose Background Color")
        if color.isValid():
            self.settings.set_setting("selected_bg_color", color.name())
            self.update_styles()

    def _pick_chart_bar_color(self, bar_index):
        """Opens a color dialog to pick a custom color for a chart bar."""
        self.sound_service.play_sfx("button_click")
        current_colors = self.settings.get_setting("chart_bar_colors")
        initial_color = QColor(current_colors[bar_index] if bar_index < len(current_colors) else "#cccccc")
        color = QColorDialog.getColor(initial_color, self, f"Choose Color for Chart Bar {bar_index + 1}")
        if color.isValid():
            current_colors[bar_index] = color.name()
            self.settings.set_setting("chart_bar_colors", current_colors)
            self.update_styles()

    def _reset_leaderboard(self):
        """Resets the leaderboard."""
        self.sound_service.play_sfx("button_click")
        self.leaderboard.reset_leaderboard()
        QMessageBox.information(self, "Leaderboard Reset", "Leaderboard has been reset!")
        self.settings_changed.emit() # Update main window LeaderboardView

    def _reset_achievements(self):
        """Resets all achievements."""
        self.sound_service.play_sfx("button_click")
        self.achievements.reset_achievements()
        QMessageBox.information(self, "Achievements Reset", "All achievements have been reset!")
        self.settings_changed.emit() # Update main window AchievementsView

    def _reset_statistics(self):
        """Resets all statistics."""
        self.sound_service.play_sfx("button_click")
        self.statistics.reset_stats()
        QMessageBox.information(self, "Statistics Reset", "All statistics have been reset!")
        self.settings_changed.emit() # Update main window StatsView

    def _reset_all_settings(self):
        """Resets all settings to factory defaults."""
        self.sound_service.play_sfx("button_click")
        reply = QMessageBox.question(self, "Reset All Settings",
                                    "Are you sure you want to reset ALL application settings to default?",
                                    QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.settings.reset_settings()
            self.apply_current_settings_to_ui() # Update UI elements
            self.update_styles() # Apply the default theme
            QMessageBox.information(self, "Settings Reset", "All settings have been reset to default!")

class MainWindow(QWidget):
    """The main window orchestrating all views and services."""
    achievement_popup_signal = Signal(str, str, str) # title, description, badge

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Supercharged Number Guessing Game")
        self.setMinimumSize(800, 700)

        # --- Determine the correct path for the icon ---
        if getattr(sys, 'frozen', False):
            # Running as a PyInstaller bundle
            base_path = sys._MEIPASS  # PyInstaller extracts files here
        else:
            # Running in development
            base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data'))

        icon_path = os.path.join(base_path, 'icon.ico')

        # --- Set the window icon ---
        self.setWindowIcon(QIcon(icon_path))
        self.start_time = time.time()

        icon_path = "icon.png"

        # --- DATA PATH ---
        self.data_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")

        # --- Service Initialization ---
        self.sound_service = SoundManager(self)
        self.settings_service = SettingsService(self.sound_service)
        self.leaderboard_service = LeaderboardService()
        self.stats_service = StatisticsService()  # Only one instance
        self.achievement_service = AchievementService(self.sound_service)
        self.game_service = GameService(
            self.settings_service,
            self.leaderboard_service,
            self.achievement_service,
            self.stats_service,  # pass the single instance
            self.sound_service
        )
        self.theme_manager = ThemeManager(self.settings_service)

        # --- Daily Streak Refresh ---
        self.stats_service.refresh_daily_streak()  # reset streak if missed days

        # --- Connect achievement signals ---
        self.achievement_popup_signal.connect(self._show_achievement_popup)
        self.achievement_service.achievement_unlocked.connect(self._show_achievement_popup)
        self.achievement_service.start_daily_streak_timer()

        self.init_ui()
        self._apply_theme()  # Apply initial theme to main window

        

    def init_ui(self):
        main_layout = QHBoxLayout(self)
        
        # --- Side Navigation Menu ---
        nav_menu_layout = QVBoxLayout()
        nav_menu_layout.setAlignment(Qt.AlignTop | Qt.AlignLeft) # type: ignore
        nav_menu_layout.setSpacing(10)
        nav_menu_layout.setContentsMargins(10, 10, 10, 10)
        
        # --- Top Menu Bar ---
        menu_bar = QMenuBar(self)

        # About action
        about_action = QAction("About", self)
        about_action.triggered.connect(self._show_about)
        menu_bar.addAction(about_action)

        # Help action
        help_action = QAction("Help", self)
        help_action.triggered.connect(self._show_help)
        menu_bar.addAction(help_action)
                
        self.game_button = QPushButton("🎮 Game")
        self.leaderboard_button = QPushButton("🏆 Leaderboard")
        self.achievements_button = QPushButton("🌟 Achievements")
        self.stats_button = QPushButton("📊 Statistics")
        self.settings_button = QPushButton("⚙️ Settings")

        self.nav_buttons = [
            self.game_button, self.leaderboard_button, self.achievements_button,
            self.stats_button, self.settings_button
        ]

        # Apply basic style and connect to view switching
        for btn in self.nav_buttons:
            btn.setFixedSize(150, 45)
            btn.clicked.connect(self._switch_view)
            nav_menu_layout.addWidget(btn)
        
        main_layout.addLayout(nav_menu_layout)

        # --- Main Content Area (Stacked Widget for Views) ---
        self.stacked_widget = QStackedWidget(self)
        main_layout.addWidget(self.stacked_widget)
        
        # --- Wrap main_layout with vertical layout to include menu bar ---
        vertical_layout = QVBoxLayout()
        vertical_layout.setContentsMargins(0, 0, 0, 0)
        vertical_layout.setSpacing(0)
        vertical_layout.addWidget(menu_bar)   # <-- your menu bar
        vertical_layout.addLayout(main_layout)  # <-- your existing main_layout
        self.setLayout(vertical_layout)       # <-- set the window layout

        self.game_view = GameView(self.game_service, self.settings_service, self.sound_service, self.theme_manager, self.achievement_popup_signal, self.stats_service)
        self.leaderboard_view = LeaderboardView(self.leaderboard_service, self.settings_service, self.theme_manager)
        self.achievements_view = AchievementsView(self.achievement_service, self.settings_service, self.theme_manager)
        self.stats_view = StatsView(self.stats_service, self.settings_service, self.theme_manager)
        self.settings_dialog = SettingsWindow(
            self.settings_service,
            self.leaderboard_service,
            self.achievement_service,
            self.stats_service,
            self.sound_service,  # only this one now
            self.theme_manager,
            self
        )


        self.stacked_widget.addWidget(self.game_view)
        self.stacked_widget.addWidget(self.leaderboard_view)
        self.stacked_widget.addWidget(self.achievements_view)
        self.stacked_widget.addWidget(self.stats_view)
        # Settings view is a dialog, not part of stacked widget for now, but will be shown via its own button click

        # Connect settings_dialog's settings_changed signal to a method in MainWindow
        # that updates all views
        self.settings_dialog.settings_changed.connect(self._apply_theme)

        # Set initial view
        self.stacked_widget.setCurrentWidget(self.game_view)
        self.game_button.setChecked(True) # Highlight initial button

        self._apply_theme() # Initial theme application

    def _switch_view(self):
        """Switches the displayed view in the stacked widget."""
        self.sound_service.play_sfx("button_click")
        sender_button = self.sender()
        if sender_button == self.game_button:
            self.stacked_widget.setCurrentWidget(self.game_view)
        elif sender_button == self.leaderboard_button:
            self.leaderboard_view.update_leaderboard_display() # Ensure up-to-date
            self.stacked_widget.setCurrentWidget(self.leaderboard_view)
        elif sender_button == self.achievements_button:
            self.achievements_view.update_achievements_display() # Ensure up-to-date
            self.stacked_widget.setCurrentWidget(self.achievements_view)
        elif sender_button == self.stats_button:
            self.stats_view.update_stats_display() # Ensure up-to-date
            self.stacked_widget.setCurrentWidget(self.stats_view)
        elif sender_button == self.settings_button:
            # Settings is a dialog, not part of the stacked widget
            self.settings_dialog.apply_current_settings_to_ui() # Refresh UI
            self.settings_dialog.exec() # Show modal dialog
        
        # Uncheck all buttons and check the current one (except settings)
        for btn in self.nav_buttons:
            if btn != self.settings_button:
                btn.setChecked(False)
        if sender_button != self.settings_button:
            sender_button.setChecked(True) # type: ignore # type: ignore

    def _apply_theme(self):
        """Applies the current theme to the entire application and all views."""
        self.theme_manager.apply_theme_to_app(QApplication.instance())
        
        # Apply button specific styles to navigation buttons
        button_style = self.theme_manager.get_button_stylesheet()
        for btn in self.nav_buttons:
            btn.setStyleSheet(button_style + """
                QPushButton { border: none; }
                QPushButton:checked {
                    background-color: %s; /* Highlight color for checked button */
                    color: white;
                    border-bottom: 3px solid white;
                }
            """ % (self.theme_manager.get_current_theme_data()["highlight"].name()))
        
        # Ensure the selected nav button stays highlighted
        for btn in self.nav_buttons:
            if self.stacked_widget.currentWidget() == self.game_view and btn == self.game_button: btn.setChecked(True)
            elif self.stacked_widget.currentWidget() == self.leaderboard_view and btn == self.leaderboard_button: btn.setChecked(True)
            elif self.stacked_widget.currentWidget() == self.achievements_view and btn == self.achievements_button: btn.setChecked(True)
            elif self.stacked_widget.currentWidget() == self.stats_view and btn == self.stats_button: btn.setChecked(True)

        # Trigger updates in all active views
        self.game_view.update_styles()
        self.leaderboard_view.update_styles()
        self.achievements_view.update_styles()
        self.stats_view.update_styles()
        # The settings_dialog updates itself when opened or when its internal settings_changed signal fires.
        
    def _show_about(self):
        """Displays a detailed About dialog for the Guessing Game."""
        about_text = (
            "<h2>Supercharged Number Guessing Game</h2>"
            "<p><b>Main Version:</b> 0.1.8-prerelease<br>"
            "<b>Recovery Version:</b> 0.1.0-prerelease<br>"
            "<b>Developer:</b> G0ld Ne0</p>"
            "<hr>"
            "<p>This is a fun and interactive number guessing game designed to challenge "
            "your logic and speed. Features include:</p>"
            "<ul>"
            "<li>Multiple game modes (Classic, Time Trial)</li>"
            "<li>Achievements and unlockable bonuses</li>"
            "<li>Leaderboards to track your high scores</li>"
            "<li>Detailed stats and performance tracking</li>"
            "</ul>"
            "<p>Enjoy the game and try to beat your personal best!</p>"
        )

        QMessageBox.information(
            self,
            "About Guessing Game",
            about_text,
            QMessageBox.Ok
        )

    def _show_help(self):
        """Displays a detailed Help/Instructions dialog for the Guessing Game."""
        help_text = (
            "<h2>How to Play</h2>"
            "<p>Follow these steps to enjoy the Supercharged Number Guessing Game:</p>"
            "<ol>"
            "<li>Navigate to the <b>'Game'</b> tab.</li>"
            "<li>Enter your guess for the secret number in the input field.</li>"
            "<li>Click the <b>'Guess!'</b> button to check your guess.</li>"
            "<li>Use power-ups and hints wisely to improve your chances.</li>"
            "<li>Unlock achievements and climb the leaderboard!</li>"
            "</ol>"
            "<p>Remember: the goal is to guess the number as efficiently as possible. "
            "Have fun and challenge yourself! 🎮</p>"
        )

        QMessageBox.information(
            self,
            "How to Play",
            help_text,
            QMessageBox.Ok
        )


    def _show_achievement_popup(self, title, description, badge):
        """Displays a transient popup for a newly unlocked achievement."""
        popup = AchievementPopup(title, description, badge, self) # type: ignore
        popup.show()

if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())

#   ________                              ___________.__              _______               ___.                 
#  /  _____/ __ __   ____   ______ ______ \__    ___/|  |__   ____    \      \  __ __  _____\_ |__   ___________ 
# /   \  ___|  |  \_/ __ \ /  ___//  ___/   |    |   |  |  \_/ __ \   /   |   \|  |  \/     \| __ \_/ __ \_  __ \
# \    \_\  \  |  /\  ___/ \___ \ \___ \    |    |   |   Y  \  ___/  /    |    \  |  /  Y Y  \ \_\ \  ___/|  | \/
#  \______  /____/  \___  >____  >____  >   |____|   |___|  /\___  > \____|__  /____/|__|_|  /___  /\___  >__|   
#         \/            \/     \/     \/                  \/     \/          \/            \/    \/     \/       

# -------------------------------------------------------
# Save Data Recovery System
# -------------------------------------------------------
# This system checks the game's save files (game state, statistics,
# achievements, leaderboard) for corruption, invalid JSON, missing files,
# or inconsistent data. 
#
# If problems are detected, it can:
# - Warn the player about corrupted or missing data
# - Offer to run a recovery/reset process
# - Restore default save files to allow the game to start safely
#
# Purpose: Prevent the game from crashing due to corrupted or missing save
# data, ensuring a smooth and safe player experience.
# -------------------------------------------------------

import json                 # For reading/writing save files in JSON format
from pathlib import Path    # For cross-platform file path handling

# PySide6 Widgets for GUI
from PySide6.QtWidgets import (
    QApplication,            # Main application object
    QWidget,                 # Base class for windows and dialogs
    QVBoxLayout,             # Vertical layout for arranging widgets
    QLabel,                  # For displaying text or images
    QPushButton,             # For clickable buttons
    QProgressBar,            # For showing progress (e.g., checking files)
    QMessageBox              # For dialogs: info, warning, error messages
)

# PySide6 Core for timers and alignment
from PySide6.QtCore import (
    QTimer,                  # For periodic updates (like progress bars)
    Qt                       # For alignment flags and other constants
)
import sys                   # For system-specific parameters and functions

# Base MGAIO user directory
USER_DIR = os.path.expandvars(r"%userprofile%")
MG_SAVE_DIR = Path(USER_DIR) / "Documents" / ".mgaio"

# App-specific folder (change name per minigame)
APP_NAME = "GuessTheNumber"
SAVE_FOLDER = MG_SAVE_DIR / "Saves" / APP_NAME
SAVE_FOLDER.mkdir(parents=True, exist_ok=True)  # Make sure it exists

# --- Save Files ---
LEADERBOARD_FILE = SAVE_FOLDER / "leaderboard.json"
SETTINGS_FILE = SAVE_FOLDER / "settings.json"
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

# --- Default Data ---
DEFAULT_GAME_STATE = {
    "target_number": 9,
    "guesses_made": 0,
    "min_val": 1,
    "max_val": 10,
    "difficulty": "Easy",
    "time_trial_mode": False,
    "time_remaining": 60,
    "start_time": 0,
    "previous_guesses": [],
    "power_ups": {"extra_hint": 0, "retry": 0, "reveal_digit": 0}
}

DEFAULT_SETTINGS = {
    "hints_enabled": True,
    "dark_mode": False,
    "color_theme": "Default Light",
    "min_val": 1,
    "max_val": 10,
    "sfx_volume": 0.7,
    "music_volume": 0.5,
    "confetti_on_win": True,
    "current_font": "Segoe UI",
    "selected_bg_color": "#f0f0f0",
    "chart_bar_colors": ["#66c2a5", "#fc8d62", "#8da0cb"]
}

DEFAULT_STATISTICS = {
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
    "last_played_date": 0,
    "total_guesses_all_games": 0,
    "games_with_guesses": 0,
    "power_ups_used": 0,
    "ai_hints_used": 0
}

DEFAULT_ACHIEVEMENTS = {
    "First Win!": {"description": "Win your very first game.", "unlocked": False, "badge": "⭐"},
    "Easy Mode Master": {"description": "Win 5 games on Easy difficulty.", "unlocked": False, "badge": "🟢"},
    "Medium Challenger": {"description": "Win 5 games on Medium difficulty.", "unlocked": False, "badge": "🟠"},
    "Hardcore Guesser": {"description": "Win 3 games on Hard difficulty.", "unlocked": False, "badge": "🔴"},
}

DEFAULT_LEADERBOARD = {"scores": []}


def load_json(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def write_json(file_path, data):
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


def validate_json(data, default, path=""):
    errors = []
    if not isinstance(data, dict):
        errors.append(f"{path} is not a dict")
        return errors
    for key, val in default.items():
        if key not in data:
            errors.append(f"Missing key: {path + key}")
        else:
            if isinstance(val, dict):
                if not isinstance(data[key], dict):
                    errors.append(f"Key {path + key} should be a dict")
                else:
                    errors.extend(validate_json(data[key], val, path + key + "."))
            elif isinstance(val, list):
                if not isinstance(data[key], list):
                    errors.append(f"Key {path + key} should be a list")
            else:
                if not isinstance(data[key], type(val)):
                    errors.append(f"Key {path + key} should be {type(val).__name__}")
    return errors


def advanced_checks(name, data):
    errors = []
    if name == "game_state":
        tn = data.get("target_number", 0)
        min_val, max_val = data.get("min_val", 1), data.get("max_val", 10)
        if tn == 0:
            errors.append("target_number is 0 (corrupted) [ERROR_CODE: 004]")
        if not (min_val <= tn <= max_val):
            errors.append(f"target_number {tn} out of range {min_val}-{max_val} [ERROR_CODE: 005]")
        if data.get("guesses_made", 0) < 0:
            errors.append("guesses_made is negative [ERROR_CODE: 006]")
        prev_guesses = data.get("previous_guesses", [])
        if not all(isinstance(g, int) and min_val <= g <= max_val for g in prev_guesses):
            errors.append("previous_guesses contain invalid values [ERROR_CODE: 007]")
        for pu_name, pu_val in data.get("power_ups", {}).items():
            if not isinstance(pu_val, int) or pu_val < 0:
                errors.append(f"Power-up {pu_name} has invalid value {pu_val} [ERROR_CODE: 008]")

    elif name == "settings":
        sfx = data.get("sfx_volume", 0.7)
        music = data.get("music_volume", 0.5)
        if not (0 <= sfx <= 1):
            errors.append(f"sfx_volume {sfx} out of range 0-1 [ERROR_CODE: 009]")
        if not (0 <= music <= 1):
            errors.append(f"music_volume {music} out of range 0-1 [ERROR_CODE: 010]")

    elif name == "statistics":
        numeric_fields = ["total_games", "total_wins", "total_losses", "easy_wins",
                          "medium_wins", "hard_wins", "time_trial_wins",
                          "current_streak", "longest_streak", "daily_streak",
                          "total_guesses_all_games", "games_with_guesses",
                          "power_ups_used", "ai_hints_used"]
        for field in numeric_fields:
            val = data.get(field, 0)
            if not isinstance(val, int) or val < 0:
                errors.append(f"{field} invalid or negative: {val} [ERROR_CODE: 011]")

    elif name == "leaderboard":
        scores = data.get("scores", [])
        for i, entry in enumerate(scores):
            if not isinstance(entry, dict) or "name" not in entry or "score" not in entry:
                errors.append(f"Leaderboard entry {i} invalid [ERROR_CODE: 012]")
            elif not isinstance(entry["score"], int) or entry["score"] < 0:
                errors.append(f"Leaderboard entry {i} score invalid [ERROR_CODE: 013]")

    return errors


class RecoveryApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Guess The Number Recovery")
        self.setFixedSize(550, 350)
        layout = QVBoxLayout(self)

        self.label = QLabel("Welcome to recovery!\nPlease choose an option below:", self)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.label)

        self.check_button = QPushButton("Check and Fix Save Files", self)
        self.check_button.clicked.connect(self.start_check)
        layout.addWidget(self.check_button)

        self.progress = QProgressBar(self)
        self.progress.setRange(0, 100)
        layout.addWidget(self.progress)

        self.status_label = QLabel("", self)
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_progress)
        self.progress_value = 0
        self.malformed_files = {}

    def start_check(self):
        self.check_button.setEnabled(False)
        self.status_label.setText("Diagnosing files...")
        self.progress_value = 0
        self.malformed_files.clear()
        self.timer.start(50)

    def update_progress(self):
        self.progress_value += 2
        self.progress.setValue(self.progress_value)
        if self.progress_value >= 100:
            self.timer.stop()
            self.check_files()

    def check_files(self):
        self.status_label.setText("Checking files for errors...")
        self.malformed_files.clear()
        major_errors = []

        for name, path in ALL_FILES.items():
            if name == "game_state" and (not path.exists() or path.stat().st_size == 0):
                major_errors.append(f"{name.upper()} is blank! [ERROR_CODE: 001]")
                continue

            if not path.exists() or path.stat().st_size == 0:
                self.malformed_files[name] = ["Cannot scan, file missing or empty"]
                continue

            data = load_json(path)
            default = {
                "leaderboard": DEFAULT_LEADERBOARD,
                "settings": DEFAULT_SETTINGS,
                "game_state": DEFAULT_GAME_STATE,
                "achievements": DEFAULT_ACHIEVEMENTS,
                "statistics": DEFAULT_STATISTICS
            }[name]

            if data is None:
                self.malformed_files[name] = ["Cannot read file or invalid JSON [ERROR_CODE: 002]"]
            else:
                errors = validate_json(data, default)
                errors += advanced_checks(name, data)
                if errors:
                    self.malformed_files[name] = errors

        if major_errors:
            QMessageBox.critical(self, "MAJOR ERROR", "\n".join(major_errors))
            sys.exit(1)

        if self.malformed_files:
            msg = "\n".join([f"{file}: {', '.join(errs)}" for file, errs in self.malformed_files.items()])
            
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Icon.Critical)
            msg_box.setWindowTitle("Malformed Data Found")
            msg_box.setText("Malformed or broken data detected.\nDo you want to reset all files?")
            msg_box.setDetailedText(msg)  # full error is copyable
            msg_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            msg_box.setDefaultButton(QMessageBox.StandardButton.Yes)
            
            reply = msg_box.exec()
            
            if reply == QMessageBox.StandardButton.Yes:
                self.start_reset()
            else:
                QMessageBox.warning(self, "Recovery Aborted", "No changes were made. Exiting.")
                sys.exit(0)
        else:
            QMessageBox.information(self, "All Good", "Save data has no errors! You're good to go!")
            sys.exit(0)

    def start_reset(self):
        self.status_label.setText("Resetting save files...")
        self.progress.setValue(0)
        self.progress_value = 0
        self.reset_timer = QTimer()
        self.reset_timer.timeout.connect(self.perform_reset_step)
        self.reset_timer.start(15)

    def perform_reset_step(self):
        self.progress_value += 2
        self.progress.setValue(self.progress_value)
        self.status_label.setText(f"Resetting... {self.progress_value}%")
        if self.progress_value >= 100:
            self.reset_timer.stop()
            for name, path in ALL_FILES.items():
                default_data = {
                    "leaderboard": DEFAULT_LEADERBOARD,
                    "settings": DEFAULT_SETTINGS,
                    "game_state": DEFAULT_GAME_STATE,
                    "achievements": DEFAULT_ACHIEVEMENTS,
                    "statistics": DEFAULT_STATISTICS
                }[name]
                write_json(path, default_data)
            QMessageBox.information(self, "Recovery Complete", "All save files have been reset successfully!")
            sys.exit(0)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = RecoveryApp()
    window.show()
    sys.exit(app.exec())

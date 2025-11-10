import sys
import os
import json
from pathlib import Path
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QCheckBox, QSpinBox
)
from PySide6.QtCore import Qt, QTimer, QUrl
from PySide6.QtMultimedia import QSoundEffect

# ------------------- CONFIG / SAVE PATH -------------------
USER_DIR = os.path.expandvars(r"%userprofile%")
MG_SAVE_DIR = Path(USER_DIR) / "Documents" / ".mgaio"
APP_NAME = "Pomodoro Timer"
SAVE_FOLDER = MG_SAVE_DIR / "Saves" / APP_NAME
SAVE_FOLDER.mkdir(parents=True, exist_ok=True)

SETTINGS_FILE = SAVE_FOLDER / "settings.json"
STATS_FILE = SAVE_FOLDER / "stats.json"  # local stats
SHARED_STATS = MG_SAVE_DIR / "Saves" / "Shared" / "stats.json"  # shared coins file
SHARED_STATS.parent.mkdir(parents=True, exist_ok=True)

# ------------------- DEFAULT SETTINGS -------------------
default_settings = {
    "focus_duration_minutes": 25,
    "short_break_minutes": 5,
    "long_break_minutes": 15,
    "sessions_before_long_break": 4,
    "auto_start_next_session": False,
    "sound_alerts": True
}

# ------------------- LOAD OR CREATE SETTINGS -------------------
if SETTINGS_FILE.exists():
    with open(SETTINGS_FILE, "r") as f:
        settings = json.load(f)
else:
    settings = default_settings
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=4)

# ------------------- SHARED STATS -------------------
def load_shared_stats():
    if SHARED_STATS.exists():
        with open(SHARED_STATS, "r") as f:
            return json.load(f)
    else:
        data = {"coins": 0, "tasks_completed": 0}
        with open(SHARED_STATS, "w") as f:
            json.dump(data, f, indent=4)
        return data

def save_shared_stats(data):
    with open(SHARED_STATS, "w") as f:
        json.dump(data, f, indent=4)

# ------------------- MAIN APP -------------------
class PomodoroApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pomodoro Timer")
        self.setFixedSize(360, 260)

        # State
        self.is_running = False
        self.current_session = 0
        self.on_break = False
        self.remaining_seconds = settings["focus_duration_minutes"] * 60
        self.shared_stats = load_shared_stats()

        # Timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_timer)

        # Layout
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        # Timer display
        self.label = QLabel(self.format_time(self.remaining_seconds))
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet("font-size: 38px;")
        self.layout.addWidget(self.label)

        # Coins display
        self.coins_label = QLabel(f"🪙 Coins: {self.shared_stats['coins']}")
        self.coins_label.setAlignment(Qt.AlignCenter)
        self.coins_label.setStyleSheet("font-size: 16px; color: gold;")
        self.layout.addWidget(self.coins_label)

        # Buttons
        self.buttons_layout = QHBoxLayout()
        self.start_btn = QPushButton("Start")
        self.pause_btn = QPushButton("Pause")
        self.reset_btn = QPushButton("Reset")
        self.skip_btn = QPushButton("Skip")

        self.start_btn.clicked.connect(self.start_timer)
        self.pause_btn.clicked.connect(self.pause_timer)
        self.reset_btn.clicked.connect(self.reset_timer)
        self.skip_btn.clicked.connect(self.skip_session)

        for btn in [self.start_btn, self.pause_btn, self.reset_btn, self.skip_btn]:
            self.buttons_layout.addWidget(btn)
        self.layout.addLayout(self.buttons_layout)

        # Sound toggle
        self.sound_checkbox = QCheckBox("Sound Alerts")
        self.sound_checkbox.setChecked(settings.get("sound_alerts", True))
        self.sound_checkbox.stateChanged.connect(self.toggle_sound)
        self.layout.addWidget(self.sound_checkbox)

        # Settings layout
        self.settings_layout = QHBoxLayout()
        self.focus_spin = QSpinBox()
        self.focus_spin.setRange(1, 180)
        self.focus_spin.setValue(settings["focus_duration_minutes"])
        self.focus_spin.setSuffix(" min")
        self.focus_spin.valueChanged.connect(self.update_focus)

        self.short_break_spin = QSpinBox()
        self.short_break_spin.setRange(1, 60)
        self.short_break_spin.setValue(settings["short_break_minutes"])
        self.short_break_spin.setSuffix(" min")
        self.short_break_spin.valueChanged.connect(self.update_short_break)

        self.long_break_spin = QSpinBox()
        self.long_break_spin.setRange(1, 120)
        self.long_break_spin.setValue(settings["long_break_minutes"])
        self.long_break_spin.setSuffix(" min")
        self.long_break_spin.valueChanged.connect(self.update_long_break)

        self.settings_layout.addWidget(self.focus_spin)
        self.settings_layout.addWidget(self.short_break_spin)
        self.settings_layout.addWidget(self.long_break_spin)
        self.layout.addLayout(self.settings_layout)

        # Sound setup
        self.sound_effect = QSoundEffect()
        sound_path = Path(__file__).parent / "alert.wav"
        if sound_path.exists():
            self.sound_effect.setSource(QUrl.fromLocalFile(str(sound_path)))
        self.sound_effect.setVolume(0.5)

    # ----------------- Timer Logic -----------------
    def start_timer(self):
        if not self.is_running:
            self.timer.start(1000)
            self.is_running = True

    def pause_timer(self):
        if self.is_running:
            self.timer.stop()
            self.is_running = False

    def reset_timer(self):
        self.timer.stop()
        self.is_running = False
        self.remaining_seconds = (
            self.get_current_break_seconds() if self.on_break else settings["focus_duration_minutes"] * 60
        )
        self.label.setText(self.format_time(self.remaining_seconds))

    def skip_session(self):
        self.end_session()

    def update_timer(self):
        self.remaining_seconds -= 1
        self.label.setText(self.format_time(self.remaining_seconds))
        if self.remaining_seconds <= 0:
            self.end_session()

    def end_session(self):
        self.timer.stop()
        self.is_running = False
        self.on_break = not self.on_break

        if self.sound_checkbox.isChecked() and self.sound_effect.source():
            self.sound_effect.play()

        if self.on_break:
            # Earn coins after a focus session only
            self.shared_stats["coins"] += 1
            save_shared_stats(self.shared_stats)
            self.coins_label.setText(f"🪙 Coins: {self.shared_stats['coins']}")

            self.remaining_seconds = self.get_current_break_seconds()
        else:
            self.current_session += 1
            self.remaining_seconds = settings["focus_duration_minutes"] * 60

        self.label.setText(self.format_time(self.remaining_seconds))
        if settings.get("auto_start_next_session", False):
            self.start_timer()

    def get_current_break_seconds(self):
        if self.current_session % settings["sessions_before_long_break"] == 0:
            return settings["long_break_minutes"] * 60
        return settings["short_break_minutes"] * 60

    @staticmethod
    def format_time(seconds):
        mins = seconds // 60
        secs = seconds % 60
        return f"{mins:02d}:{secs:02d}"

    # ----------------- Settings Updates -----------------
    def toggle_sound(self, state):
        settings["sound_alerts"] = bool(state)
        save_settings()

    def update_focus(self, value):
        settings["focus_duration_minutes"] = value
        save_settings()
        if not self.on_break:
            self.remaining_seconds = value * 60
            self.label.setText(self.format_time(self.remaining_seconds))

    def update_short_break(self, value):
        settings["short_break_minutes"] = value
        save_settings()
        if self.on_break:
            self.remaining_seconds = self.get_current_break_seconds()
            self.label.setText(self.format_time(self.remaining_seconds))

    def update_long_break(self, value):
        settings["long_break_minutes"] = value
        save_settings()
        if self.on_break:
            self.remaining_seconds = self.get_current_break_seconds()
            self.label.setText(self.format_time(self.remaining_seconds))


# ----------------- RUN APP -----------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PomodoroApp()
    window.show()
    sys.exit(app.exec())

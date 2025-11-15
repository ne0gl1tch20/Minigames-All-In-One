import sys
import os, json
from pathlib import Path
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QSpinBox, QCheckBox
)
from PySide6.QtCore import Qt, QTimer, QTime
from PySide6.QtMultimedia import QSoundEffect
from PySide6.QtGui import QFont

# ------------------- CONFIG / SAVE PATH -------------------
USER_DIR = os.path.expandvars(r"%userprofile%")
MG_SAVE_DIR = Path(USER_DIR) / "Documents" / ".mgaio"
APP_NAME = "Quick Stretch"
SAVE_FOLDER = MG_SAVE_DIR / "Saves" / APP_NAME
SAVE_FOLDER.mkdir(parents=True, exist_ok=True)

SETTINGS_FILE = SAVE_FOLDER / "settings.json"

# ------------------- DEFAULT SETTINGS -------------------
default_settings = {
    "reminder_interval_minutes": 60,
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

# ------------------- MAIN APP -------------------
class StretchReminder(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Quick Stretch Reminder 🏃‍♂️")
        self.setFixedSize(300, 200)

        self.timer = QTimer()
        self.timer.timeout.connect(self.show_stretch_notification)
        self.remaining_seconds = settings["reminder_interval_minutes"] * 60

        # Layout
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        # Countdown display
        self.label = QLabel(self.format_time(self.remaining_seconds))
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setFont(QFont("Arial", 28))
        self.layout.addWidget(self.label)

        # Interval settings
        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(5, 180)
        self.interval_spin.setValue(settings["reminder_interval_minutes"])
        self.interval_spin.setSuffix(" min")
        self.interval_spin.valueChanged.connect(self.update_interval)
        self.layout.addWidget(self.interval_spin)

        # Sound toggle
        self.sound_checkbox = QCheckBox("Sound Alerts")
        self.sound_checkbox.setChecked(settings.get("sound_alerts", True))
        self.sound_checkbox.stateChanged.connect(self.toggle_sound)
        self.layout.addWidget(self.sound_checkbox)

        # Start/Stop buttons
        self.start_btn = QPushButton("Start")
        self.stop_btn = QPushButton("Stop")
        self.start_btn.clicked.connect(self.start_timer)
        self.stop_btn.clicked.connect(self.stop_timer)
        self.layout.addWidget(self.start_btn)
        self.layout.addWidget(self.stop_btn)

        # Sound setup
        self.sound_effect = QSoundEffect()
        sound_path = Path(__file__).parent / "alert.wav"
        if sound_path.exists():
            self.sound_effect.setSource(sound_path.as_uri())
        self.sound_effect.setVolume(0.5)

        # Timer tick
        self.tick_timer = QTimer()
        self.tick_timer.timeout.connect(self.update_countdown)
        self.tick_timer.start(1000)

    def start_timer(self):
        self.remaining_seconds = settings["reminder_interval_minutes"] * 60

    def stop_timer(self):
        self.remaining_seconds = 0
        self.label.setText("Stopped")

    def update_countdown(self):
        if self.remaining_seconds > 0:
            self.remaining_seconds -= 1
            self.label.setText(self.format_time(self.remaining_seconds))
        else:
            self.show_stretch_notification()
            self.remaining_seconds = settings["reminder_interval_minutes"] * 60

    def show_stretch_notification(self):
        self.label.setText("Stretch Time! 🏃‍♂️")
        if self.sound_checkbox.isChecked() and self.sound_effect.source():
            self.sound_effect.play()

    def update_interval(self, value):
        settings["reminder_interval_minutes"] = value
        self.remaining_seconds = value * 60
        self.save_settings()

    def toggle_sound(self, state):
        settings["sound_alerts"] = bool(state)
        self.save_settings()

    def save_settings(self):
        with open(SETTINGS_FILE, "w") as f:
            json.dump(settings, f, indent=4)

    @staticmethod
    def format_time(seconds):
        mins = seconds // 60
        secs = seconds % 60
        return f"{mins:02d}:{secs:02d}"

# ----------------- RUN APP -----------------
if __name__ == "__main__":
    import json
    app = QApplication(sys.argv)
    window = StretchReminder()
    window.show()
    sys.exit(app.exec())

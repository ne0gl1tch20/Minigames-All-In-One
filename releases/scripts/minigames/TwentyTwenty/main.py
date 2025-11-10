import sys
from pathlib import Path
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QSpinBox, QCheckBox, QHBoxLayout
)
from PySide6.QtCore import Qt, QTimer, QTime
from PySide6.QtMultimedia import QSoundEffect
from PySide6.QtCore import QUrl

# ---------------- CONFIG ----------------
APP_NAME = "Eye Strain Reminder"
SAVE_DIR = Path.home() / "Documents" / ".mgaio" / "Saves" / APP_NAME
SAVE_DIR.mkdir(parents=True, exist_ok=True)
SETTINGS_FILE = SAVE_DIR / "settings.json"

default_settings = {
    "work_interval_minutes": 20,
    "break_seconds": 20,
    "sound_alerts": True
}

# Load or create settings
import json
if SETTINGS_FILE.exists():
    with open(SETTINGS_FILE, "r") as f:
        settings = json.load(f)
else:
    settings = default_settings
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=4)

# ---------------- APP ----------------
class EyeStrainReminder(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.setFixedSize(300, 200)

        self.is_working = True
        self.remaining_seconds = settings["work_interval_minutes"] * 60

        self.timer = QTimer()
        self.timer.timeout.connect(self.tick)

        layout = QVBoxLayout()
        self.setLayout(layout)

        self.label = QLabel(self.format_time(self.remaining_seconds))
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet("font-size: 32px;")
        layout.addWidget(self.label)

        # Sound
        self.sound_effect = QSoundEffect()
        sound_path = Path(__file__).parent / "alert.wav"
        if sound_path.exists():
            self.sound_effect.setSource(QUrl.fromLocalFile(str(sound_path)))
        self.sound_effect.setVolume(0.5)

        # Buttons
        btn_layout = QHBoxLayout()
        self.start_btn = QPushButton("Start")
        self.pause_btn = QPushButton("Pause")
        self.reset_btn = QPushButton("Reset")
        btn_layout.addWidget(self.start_btn)
        btn_layout.addWidget(self.pause_btn)
        btn_layout.addWidget(self.reset_btn)
        layout.addLayout(btn_layout)

        self.start_btn.clicked.connect(self.start)
        self.pause_btn.clicked.connect(self.pause)
        self.reset_btn.clicked.connect(self.reset)

        # Settings
        settings_layout = QVBoxLayout()
        self.work_spin = QSpinBox()
        self.work_spin.setRange(1, 180)
        self.work_spin.setValue(settings["work_interval_minutes"])
        self.work_spin.setSuffix(" min")
        self.work_spin.valueChanged.connect(self.update_work_interval)

        self.break_spin = QSpinBox()
        self.break_spin.setRange(5, 300)
        self.break_spin.setValue(settings["break_seconds"])
        self.break_spin.setSuffix(" sec")
        self.break_spin.valueChanged.connect(self.update_break_seconds)

        self.sound_checkbox = QCheckBox("Sound Alerts")
        self.sound_checkbox.setChecked(settings.get("sound_alerts", True))
        self.sound_checkbox.stateChanged.connect(self.update_sound)

        settings_layout.addWidget(QLabel("Work Interval:"))
        settings_layout.addWidget(self.work_spin)
        settings_layout.addWidget(QLabel("Break Duration:"))
        settings_layout.addWidget(self.break_spin)
        settings_layout.addWidget(self.sound_checkbox)
        layout.addLayout(settings_layout)

    # ---------------- Timer Logic ----------------
    def start(self):
        if not self.timer.isActive():
            self.timer.start(1000)

    def pause(self):
        if self.timer.isActive():
            self.timer.stop()

    def reset(self):
        self.timer.stop()
        self.is_working = True
        self.remaining_seconds = settings["work_interval_minutes"] * 60
        self.label.setText(self.format_time(self.remaining_seconds))

    def tick(self):
        self.remaining_seconds -= 1
        self.label.setText(self.format_time(self.remaining_seconds))
        if self.remaining_seconds <= 0:
            self.end_interval()

    def end_interval(self):
        self.timer.stop()
        if settings["sound_alerts"] and self.sound_effect.source():
            self.sound_effect.play()
        if self.is_working:
            # Start break
            self.is_working = False
            self.remaining_seconds = settings["break_seconds"]
            self.label.setText(f"Look away! {self.format_time(self.remaining_seconds)}")
        else:
            # Start next work session
            self.is_working = True
            self.remaining_seconds = settings["work_interval_minutes"] * 60
            self.label.setText(self.format_time(self.remaining_seconds))
        self.timer.start(1000)

    # ---------------- Settings ----------------
    def update_work_interval(self, value):
        settings["work_interval_minutes"] = value
        with open(SETTINGS_FILE, "w") as f:
            json.dump(settings, f, indent=4)
        if self.is_working:
            self.remaining_seconds = value * 60
            self.label.setText(self.format_time(self.remaining_seconds))

    def update_break_seconds(self, value):
        settings["break_seconds"] = value
        with open(SETTINGS_FILE, "w") as f:
            json.dump(settings, f, indent=4)
        if not self.is_working:
            self.remaining_seconds = value
            self.label.setText(f"Look away! {self.format_time(self.remaining_seconds)}")

    def update_sound(self, state):
        settings["sound_alerts"] = bool(state)
        with open(SETTINGS_FILE, "w") as f:
            json.dump(settings, f, indent=4)

    @staticmethod
    def format_time(seconds):
        mins = seconds // 60
        secs = seconds % 60
        return f"{mins:02d}:{secs:02d}"

# ---------------- Run ----------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = EyeStrainReminder()
    window.show()
    sys.exit(app.exec())

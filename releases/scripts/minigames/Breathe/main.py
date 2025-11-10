import sys
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QSpinBox, QCheckBox
from PySide6.QtCore import Qt, QTimer
from PySide6.QtMultimedia import QSoundEffect
from pathlib import Path

# ----------------- CONFIG / SAVE PATH -----------------
import os, json
USER_DIR = os.path.expandvars(r"%userprofile%")
MG_SAVE_DIR = Path(USER_DIR) / "Documents" / ".mgaio"
APP_NAME = "Breathe"
SAVE_FOLDER = MG_SAVE_DIR / "Saves" / APP_NAME
SAVE_FOLDER.mkdir(parents=True, exist_ok=True)
SETTINGS_FILE = SAVE_FOLDER / "settings.json"

# ----------------- DEFAULT SETTINGS -----------------
default_settings = {
    "session_minutes": 1,  # default 1-minute micro breathing
    "sound_alerts": True
}

# Load settings
if SETTINGS_FILE.exists():
    with open(SETTINGS_FILE, "r") as f:
        settings = json.load(f)
else:
    settings = default_settings
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=4)

# ----------------- MAIN APP -----------------
class BreatheApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("💨 Micro Breathe")
        self.setFixedSize(300, 200)

        self.total_seconds = settings["session_minutes"] * 60
        self.remaining_seconds = self.total_seconds
        self.cycle_phase = 0  # 0=Inhale,1=Hold,2=Exhale

        # Timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_breath)

        # Layout
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        # Countdown / Phase label
        self.label = QLabel(self.format_time(self.remaining_seconds))
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet("font-size: 28px;")
        self.layout.addWidget(self.label)

        self.phase_label = QLabel("Ready")
        self.phase_label.setAlignment(Qt.AlignCenter)
        self.phase_label.setStyleSheet("font-size: 20px; color: teal;")
        self.layout.addWidget(self.phase_label)

        # Buttons
        self.start_btn = QPushButton("Start")
        self.stop_btn = QPushButton("Stop")
        self.start_btn.clicked.connect(self.start_session)
        self.stop_btn.clicked.connect(self.stop_session)
        self.layout.addWidget(self.start_btn)
        self.layout.addWidget(self.stop_btn)

        # Session length
        self.session_spin = QSpinBox()
        self.session_spin.setRange(1, 10)
        self.session_spin.setValue(settings["session_minutes"])
        self.session_spin.setSuffix(" min")
        self.session_spin.valueChanged.connect(self.update_session_length)
        self.layout.addWidget(self.session_spin)

        # Sound toggle
        self.sound_checkbox = QCheckBox("Sound Alert")
        self.sound_checkbox.setChecked(settings.get("sound_alerts", True))
        self.sound_checkbox.stateChanged.connect(self.toggle_sound)
        self.layout.addWidget(self.sound_checkbox)

        # Sound setup
        self.sound_effect = QSoundEffect()
        sound_path = Path(__file__).parent / "bell.wav"
        if sound_path.exists():
            self.sound_effect.setSource(sound_path.as_uri())
        self.sound_effect.setVolume(0.5)

    # ----------------- Timer Logic -----------------
    def start_session(self):
        self.remaining_seconds = self.total_seconds
        self.cycle_phase = 0
        self.timer.start(1000)

    def stop_session(self):
        self.timer.stop()
        self.phase_label.setText("Stopped")
        self.label.setText(self.format_time(self.remaining_seconds))

    def update_breath(self):
        if self.remaining_seconds > 0:
            self.remaining_seconds -= 1
            self.label.setText(self.format_time(self.remaining_seconds))

            # Breathing cycle (inhale 4s, hold 4s, exhale 4s)
            cycle_time = 12  # total seconds per breath cycle
            phase_time = self.remaining_seconds % cycle_time
            if phase_time < 4:
                self.phase_label.setText("Inhale")
            elif phase_time < 8:
                self.phase_label.setText("Hold")
            else:
                self.phase_label.setText("Exhale")

        else:
            self.timer.stop()
            self.phase_label.setText("Done!")
            self.label.setText("✨")
            if self.sound_checkbox.isChecked() and self.sound_effect.source():
                self.sound_effect.play()

    # ----------------- Settings -----------------
    def update_session_length(self, value):
        settings["session_minutes"] = value
        self.total_seconds = value * 60
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
    app = QApplication(sys.argv)
    window = BreatheApp()
    window.show()
    sys.exit(app.exec())

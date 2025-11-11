import sys
import uuid
from pathlib import Path
import json

from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QPushButton,
    QHBoxLayout, QSlider, QFileDialog, QCheckBox, QInputDialog,
    QMessageBox, QGridLayout, QFrame, QSizePolicy
)
from PySide6.QtCore import Qt, QUrl, Slot
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput

# ---------------- CONFIG ----------------
APP_NAME = "Custom Soundboard"
SAVE_DIR = Path.home() / "Documents" / ".mgaio" / "Saves" / APP_NAME
SAVE_DIR.mkdir(parents=True, exist_ok=True)
SETTINGS_FILE = SAVE_DIR / "settings.json"

default_settings = {
    # sounds: { id: {"name": str, "path": str} }
    "sounds": {},
    "volume": 50,
    "loop_sounds": False
}

# Load or create settings (backwards compatibility handled below)
if SETTINGS_FILE.exists():
    with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
        settings = json.load(f)
else:
    settings = default_settings
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=4)

# Backwards-compat: if old format (name -> path), convert to id-based
if isinstance(settings.get("sounds"), dict) and any(not isinstance(v, dict) for v in settings["sounds"].values()):
    old = settings["sounds"]
    new_sounds = {}
    for name, path in old.items():
        sid = str(uuid.uuid4())
        new_sounds[sid] = {"name": name, "path": path}
    settings["sounds"] = new_sounds
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=4)


# ---------------- APP ----------------
class SoundWidget(QFrame):
    def __init__(self, parent, sid: str, name: str, path: str, play_callback, edit_callback, delete_callback, stop_callback):
        super().__init__(parent)
        self.sid = sid
        self.sound_name = name
        self.sound_path = Path(path)
        self.play_callback = play_callback
        self.edit_callback = edit_callback
        self.delete_callback = delete_callback
        self.stop_callback = stop_callback

        self.setFrameShape(QFrame.StyledPanel)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self.setStyleSheet("border-radius:10px; padding:6px;")

        layout = QVBoxLayout()
        layout.setSpacing(6)
        layout.setContentsMargins(6, 6, 6, 6)

        # Big play button showing name
        self.play_btn = QPushButton(self.sound_name)
        self.play_btn.setMinimumHeight(64)
        self.play_btn.clicked.connect(self.on_play)
        layout.addWidget(self.play_btn)

        # small controls: Stop, Edit, Delete
        ctrl_layout = QHBoxLayout()
        self.stop_btn = QPushButton("■ Stop")
        self.stop_btn.setFixedWidth(70)
        self.stop_btn.clicked.connect(self.on_stop)
        ctrl_layout.addWidget(self.stop_btn)

        self.edit_btn = QPushButton("✎ Edit")
        self.edit_btn.setFixedWidth(70)
        self.edit_btn.clicked.connect(self.on_edit)
        ctrl_layout.addWidget(self.edit_btn)

        self.del_btn = QPushButton("🗑 Delete")
        self.del_btn.setFixedWidth(70)
        self.del_btn.clicked.connect(self.on_delete)
        ctrl_layout.addWidget(self.del_btn)

        layout.addLayout(ctrl_layout)
        self.setLayout(layout)

    def on_play(self):
        self.play_callback(self.sid)

    def on_stop(self):
        self.stop_callback(self.sid)

    def on_edit(self):
        self.edit_callback(self.sid)

    def on_delete(self):
        self.delete_callback(self.sid)


class SoundboardApp(QWidget):
    def __init__(self, cols: int = 3):
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.setMinimumSize(520, 420)
        self.cols = cols

        # players: sid -> {"player": QMediaPlayer, "audio": QAudioOutput}
        self.players = {}

        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        title = QLabel("🎧 Custom Soundboard")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 22px; font-weight: bold;")
        main_layout.addWidget(title)

        # Grid area for sound widgets
        self.grid_container = QWidget()
        self.grid_layout = QGridLayout()
        self.grid_layout.setSpacing(10)
        self.grid_container.setLayout(self.grid_layout)
        main_layout.addWidget(self.grid_container)

        # controls row
        ctrl_row = QHBoxLayout()

        self.add_btn = QPushButton("➕ Add New Sound")
        self.add_btn.clicked.connect(self.add_new_sound)
        ctrl_row.addWidget(self.add_btn)

        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(settings.get("volume", 50))
        self.volume_slider.valueChanged.connect(self.update_volume)
        ctrl_row.addWidget(QLabel("Volume:"))
        ctrl_row.addWidget(self.volume_slider)

        self.loop_checkbox = QCheckBox("Loop Sounds")
        self.loop_checkbox.setChecked(settings.get("loop_sounds", False))
        self.loop_checkbox.stateChanged.connect(self.update_loop)
        ctrl_row.addWidget(self.loop_checkbox)

        main_layout.addLayout(ctrl_row)

        # load existing sounds into grid
        self.widgets = {}  # sid -> SoundWidget
        self.reload_grid()

    def reload_grid(self):
        # clear layout widgets
        for i in reversed(range(self.grid_layout.count())):
            w = self.grid_layout.itemAt(i).widget()
            if w:
                w.setParent(None)

        self.widgets.clear()

        items = list(settings.get("sounds", {}).items())  # [(sid, {name,path}), ...]
        for idx, (sid, meta) in enumerate(items):
            r = idx // self.cols
            c = idx % self.cols
            name = meta.get("name", f"Sound-{idx}")
            path = meta.get("path", "")
            w = SoundWidget(self, sid, name, path,
                            play_callback=self.play_sound,
                            edit_callback=self.edit_sound,
                            delete_callback=self.delete_sound,
                            stop_callback=self.stop_sound)
            self.grid_layout.addWidget(w, r, c)
            self.widgets[sid] = w

            # prepare player for this sound (but don't start)
            self._ensure_player_for(sid, path)

    def _ensure_player_for(self, sid: str, path: str):
        # if player exists, update source; otherwise create
        if sid in self.players:
            player_info = self.players[sid]
            try:
                player_info["player"].stop()
            except Exception:
                pass
            player_info["player"].setSource(QUrl.fromLocalFile(path))
            player_info["audio"].setVolume(self.volume_slider.value() / 100)
            return

        player = QMediaPlayer(self)
        audio_out = QAudioOutput(self)
        audio_out.setVolume(self.volume_slider.value() / 100)
        player.setAudioOutput(audio_out)
        player.setSource(QUrl.fromLocalFile(path))

        # handle end-of-media for loop support
        def handle_media_status(status, pl=player, sid_local=sid):
            # constant names differ, so use numeric checks or strings; safe approach:
            try:
                # QMediaPlayer.MediaStatus.EndOfMedia is available in newer PySide6
                from PySide6.QtMultimedia import QMediaPlayer as QMP
                if status == QMP.MediaStatus.EndOfMedia:
                    if self.loop_checkbox.isChecked():
                        pl.setPosition(0)
                        pl.play()
            except Exception:
                # fallback: if playbackState becomes Stopped and loop is requested, replay
                if not pl.isPlaying() and self.loop_checkbox.isChecked():
                    pl.setPosition(0)
                    pl.play()

        try:
            player.mediaStatusChanged.connect(handle_media_status)
        except Exception:
            pass

        self.players[sid] = {"player": player, "audio": audio_out}

    def add_new_sound(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Sound File", "", "Audio Files (*.wav *.mp3 *.ogg)")
        if not file_path:
            return
        # ask for button name
        name, ok = QInputDialog.getText(self, "Enter Button Name", "Button Name:")
        if not ok or not name.strip():
            name = Path(file_path).stem
        name = name.strip()

        sid = str(uuid.uuid4())
        settings.setdefault("sounds", {})[sid] = {"name": name, "path": file_path}
        self.save_settings()
        self.reload_grid()

    def play_sound(self, sid: str):
        meta = settings.get("sounds", {}).get(sid)
        if not meta:
            return
        path = meta.get("path", "")
        if not Path(path).exists():
            QMessageBox.warning(self, "File missing", f"Sound file not found:\n{path}")
            return

        self._ensure_player_for(sid, path)
        player_info = self.players.get(sid)
        if not player_info:
            return
        player = player_info["player"]
        # ensure volume set
        player_info["audio"].setVolume(self.volume_slider.value() / 100)
        # start playback
        try:
            # If already playing, restart from beginning
            player.stop()
            player.setPosition(0)
            player.play()
        except Exception as e:
            QMessageBox.critical(self, "Playback Error", f"Unable to play sound:\n{e}")

    def stop_sound(self, sid: str):
        info = self.players.get(sid)
        if info:
            try:
                info["player"].stop()
            except Exception:
                pass

    def edit_sound(self, sid: str):
        meta = settings.get("sounds", {}).get(sid)
        if not meta:
            return
        # Option to change name
        new_name, ok = QInputDialog.getText(self, "Edit Button Name", "Button Name:", text=meta.get("name", ""))
        if ok and new_name.strip():
            meta["name"] = new_name.strip()

        # Option to change file (ask yes/no)
        change_file = QMessageBox.question(self, "Replace File?", "Do you want to replace the audio file?", QMessageBox.Yes | QMessageBox.No)
        if change_file == QMessageBox.Yes:
            file_path, _ = QFileDialog.getOpenFileName(self, "Select Sound File", "", "Audio Files (*.wav *.mp3 *.ogg)")
            if file_path:
                meta["path"] = file_path
                # reset player for sid
                if sid in self.players:
                    try:
                        self.players[sid]["player"].stop()
                    except Exception:
                        pass
                    del self.players[sid]

        settings["sounds"][sid] = meta
        self.save_settings()
        self.reload_grid()

    def delete_sound(self, sid: str):
        confirm = QMessageBox.question(self, "Delete Sound", "Are you sure you want to delete this sound?", QMessageBox.Yes | QMessageBox.No)
        if confirm != QMessageBox.Yes:
            return
        # stop and cleanup player
        if sid in self.players:
            try:
                self.players[sid]["player"].stop()
            except Exception:
                pass
            del self.players[sid]
        # remove widget and setting
        if sid in settings.get("sounds", {}):
            del settings["sounds"][sid]
        self.save_settings()
        self.reload_grid()

    def update_volume(self, value):
        settings["volume"] = value
        # update live audio volumes
        for info in self.players.values():
            try:
                info["audio"].setVolume(value / 100)
            except Exception:
                pass
        self.save_settings()

    def update_loop(self, state):
        settings["loop_sounds"] = bool(state)
        self.save_settings()

    def save_settings(self):
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=4)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SoundboardApp(cols=3)  # set columns for grid here
    window.show()
    sys.exit(app.exec())

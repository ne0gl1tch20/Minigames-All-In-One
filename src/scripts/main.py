import sys
import os
import json
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QScrollArea,
    QFrame, QFileDialog, QLineEdit, QDialog, QMessageBox
)
from PySide6.QtGui import QIcon, QPixmap, QFont, QColor
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve
from PySide6.QtWidgets import QGraphicsDropShadowEffect, QInputDialog

# Base user folder for saves/settings (same for dev & PyInstaller)
USER_DIR = os.path.expandvars(r"%userprofile%")
MGAIO_DIR = os.path.join(USER_DIR, "Documents", ".mgaio")
SAVE_PATH = os.path.join(MGAIO_DIR, "Saves")
SETTINGS_PATH = os.path.join(MGAIO_DIR, "settingsave.json")
THEME_PATH = os.path.join(MGAIO_DIR, "themesave.json")

os.makedirs(SAVE_PATH, exist_ok=True)

# Detect minigames path
if getattr(sys, 'frozen', False):
    # PyInstaller frozen build
    MINIGAMES_DIR = os.path.join(MGAIO_DIR, "minigames")
else:
    # Development mode (relative to main.py)
    MINIGAMES_DIR = os.path.join(os.path.dirname(__file__), "minigames")

os.makedirs(MINIGAMES_DIR, exist_ok=True)

print("Minigames loaded from:", MINIGAMES_DIR)

# === Default Settings ===
default_settings = {"theme": "default", "lock_password": ""}
if os.path.exists(SETTINGS_PATH):
    with open(SETTINGS_PATH, "r") as f:
        settings = json.load(f)
else:
    settings = default_settings.copy()
    with open(SETTINGS_PATH, "w") as f:
        json.dump(settings, f, indent=4)

# === Theme Presets ===
themes = {
    "default": {"bg": "#1e1e2f", "fg": "#ffffff", "accent": "#ffcc00"},
    "light": {"bg": "#f0f0f0", "fg": "#222222", "accent": "#ff8800"},
    "dark": {"bg": "#121212", "fg": "#ffffff", "accent": "#00ffcc"},
}
theme = themes.get(settings.get("theme", "default"), themes["default"])

# === Animated Game Card ===
class GameCard(QFrame):
    def __init__(self, game_name, game_path, icon_path=None, game_desc="", how_to_play=""):
        super().__init__()
        self.game_path = game_path
        self.how_to_play_text = how_to_play
        self.setFrameShape(QFrame.StyledPanel)
        self.setFixedHeight(120)  # taller to fit description & buttons
        self.setStyleSheet(f"background-color: {theme['bg']}; border-radius: 10px;")
        self.setGraphicsEffect(QGraphicsDropShadowEffect(blurRadius=15, xOffset=0, yOffset=5, color=QColor(0,0,0,160)))

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10,5,10,5)
        main_layout.setSpacing(5)

        # Top: Icon + Title
        top_layout = QHBoxLayout()
        self.icon_label = QLabel()
        if icon_path and os.path.exists(icon_path):
            pixmap = QPixmap(icon_path).scaled(48,48, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.icon_label.setPixmap(pixmap)
        top_layout.addWidget(self.icon_label)

        self.name_label = QLabel(game_name)
        self.name_label.setFont(QFont("Segoe UI", 14, QFont.Bold))
        self.name_label.setStyleSheet(f"color: {theme['fg']}")
        top_layout.addWidget(self.name_label, alignment=Qt.AlignVCenter)

        main_layout.addLayout(top_layout)

        # Description
        if game_desc:
            self.desc_label = QLabel(game_desc)
            self.desc_label.setFont(QFont("Segoe UI", 10))
            self.desc_label.setStyleSheet(f"color: {theme['fg']}")
            self.desc_label.setWordWrap(True)
            main_layout.addWidget(self.desc_label)

        # Buttons
        btn_layout = QHBoxLayout()
        self.launch_btn = QPushButton("▶ Play")
        self.launch_btn.setFixedSize(80,30)
        self.launch_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {theme['accent']};
                color: #000;
                border-radius: 15px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #ffffff;
                color: {theme['accent']};
            }}
        """)
        self.launch_btn.clicked.connect(self.launch_game)
        btn_layout.addWidget(self.launch_btn)

        self.howto_btn = QPushButton("❓ How to Play")
        self.howto_btn.setFixedSize(120,30)
        self.howto_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {theme['fg']};
                color: {theme['bg']};
                border-radius: 15px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #cccccc;
                color: {theme['bg']};
            }}
        """)
        self.howto_btn.clicked.connect(self.show_how_to_play)
        btn_layout.addWidget(self.howto_btn)

        btn_layout.addStretch()
        main_layout.addLayout(btn_layout)

        self.setLayout(main_layout)

        # Hover animation
        self.anim = QPropertyAnimation(self, b"geometry")
        self.anim.setDuration(200)
        self.anim.setEasingCurve(QEasingCurve.OutCubic)

    def enterEvent(self, event):
        geom = self.geometry()
        self.anim.stop()
        self.anim.setStartValue(geom)
        self.anim.setEndValue(geom.adjusted(-5,-5,5,5))
        self.anim.start()
        super().enterEvent(event)

    def leaveEvent(self, event):
        geom = self.geometry()
        self.anim.stop()
        self.anim.setStartValue(geom)
        self.anim.setEndValue(geom.adjusted(5,5,-5,-5))
        self.anim.start()
        super().leaveEvent(event)

    def launch_game(self):
        game_main = os.path.join(self.game_path, "main.py")
        if os.path.exists(game_main):
            os.system(f'python "{game_main}"')
        else:
            QMessageBox.warning(self, "Error", f"No main.py found in {self.game_path}")

    def show_how_to_play(self):
        if not self.how_to_play_text:
            QMessageBox.information(self, "How to Play", "No instructions available.")
            return
        dlg = QDialog(self)
        dlg.setWindowTitle(f"How to Play: {self.name_label.text()}")
        dlg.resize(500,400)
        dlg.setStyleSheet(f"background-color: {theme['bg']}; color:{theme['fg']}")

        layout = QVBoxLayout()
        text_label = QLabel(self.how_to_play_text)
        text_label.setWordWrap(True)
        text_label.setFont(QFont("Segoe UI", 11))
        layout.addWidget(text_label)

        dlg.setLayout(layout)
        dlg.exec()



# === Settings Dialog ===
class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setMinimumWidth(350)
        self.setStyleSheet(f"background-color: {theme['bg']}; color:{theme['fg']}")
        layout = QVBoxLayout()

        # App Lock
        layout.addWidget(QLabel("Set App Lock Password:"))
        self.pwd_input = QLineEdit()
        self.pwd_input.setEchoMode(QLineEdit.Password)
        self.pwd_input.setText(settings.get("lock_password",""))
        layout.addWidget(self.pwd_input)

        # Backup/Restore
        backup_btn = QPushButton("Backup Settings")
        backup_btn.clicked.connect(self.backup_settings)
        restore_btn = QPushButton("Restore Settings")
        restore_btn.clicked.connect(self.restore_settings)
        layout.addWidget(backup_btn)
        layout.addWidget(restore_btn)

        # Theme Presets
        layout.addWidget(QLabel("Theme Presets:"))
        for name in themes.keys():
            btn = QPushButton(name.capitalize())
            btn.clicked.connect(lambda _, n=name: self.apply_theme(n))
            layout.addWidget(btn)

        self.setLayout(layout)

    def backup_settings(self):
        path,_ = QFileDialog.getSaveFileName(self,"Backup Settings","","JSON Files (*.json)")
        if path:
            with open(path,"w") as f:
                json.dump(settings,f,indent=4)
            QMessageBox.information(self,"Backup","Settings backed up successfully!")

    def restore_settings(self):
        path,_ = QFileDialog.getOpenFileName(self,"Restore Settings","","JSON Files (*.json)")
        if path:
            with open(path,"r") as f:
                restored = json.load(f)
            settings.update(restored)
            with open(SETTINGS_PATH,"w") as f:
                json.dump(settings,f,indent=4)
            QMessageBox.information(self,"Restore","Settings restored successfully!")

    def apply_theme(self, name):
        global theme
        theme = themes[name]
        settings["theme"] = name
        with open(SETTINGS_PATH,"w") as f:
            json.dump(settings,f,indent=4)
        QMessageBox.information(self,"Theme","Applied theme: "+name)
        self.close()


# === Main Launcher ===
class Launcher(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MGAIO Launcher")
        self.setMinimumSize(700,500)
        self.setStyleSheet(f"background-color: {theme['bg']};")

        layout = QVBoxLayout()
        layout.setContentsMargins(15,15,15,15)

        # Settings button
        top_bar = QHBoxLayout()
        settings_btn = QPushButton("⚙ Settings")
        settings_btn.clicked.connect(self.open_settings)
        settings_btn.setFixedHeight(40)
        top_bar.addStretch()
        top_bar.addWidget(settings_btn)
        layout.addLayout(top_bar)

        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        self.game_layout = QVBoxLayout()
        self.game_layout.setSpacing(10)
        container.setLayout(self.game_layout)
        scroll.setWidget(container)
        layout.addWidget(scroll)

        self.setLayout(layout)
        self.load_games()

    def load_games(self):
        if not os.path.exists(MINIGAMES_DIR):
            return
        for game in os.listdir(MINIGAMES_DIR):
            game_path = os.path.join(MINIGAMES_DIR, game)
            if os.path.isdir(game_path):
                icon_path = os.path.join(game_path,"icon.ico")
                config_path = os.path.join(game_path, "config.json")

                game_title, game_desc, how_to_play = game, "", ""
                if os.path.exists(config_path):
                    try:
                        with open(config_path, "r") as f:
                            config = json.load(f)
                        game_title = config.get("title", game)
                        game_desc = config.get("description", "")
                        how_to_play = config.get("how_to_play","")
                    except:
                        pass

                card = GameCard(game_title, game_path, icon_path, game_desc, how_to_play)
                self.game_layout.addWidget(card)



    def open_settings(self):
        dlg = SettingsDialog(self)
        dlg.exec()
        self.reload_theme()

    def reload_theme(self):
        self.setStyleSheet(f"background-color: {theme['bg']};")
        for i in range(self.game_layout.count()):
            widget = self.game_layout.itemAt(i).widget()
            widget.setStyleSheet(f"background-color: {theme['bg']};")
            widget.name_label.setStyleSheet(f"color:{theme['fg']}")
            widget.launch_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {theme['accent']};
                    color: #000;
                    border-radius: 20px;
                    font-weight: bold;
                    font-size: 16px;
                }}
                QPushButton:hover {{
                    background-color: #ffffff;
                    color: {theme['accent']};
                }}
            """)

# === App Lock ===
def app_lock():
    if settings.get("lock_password"):
        pwd, ok = QInputDialog.getText(None,"App Lock","Enter Password:", QLineEdit.Password)
        if not ok or pwd != settings["lock_password"]:
            QMessageBox.critical(None,"Access Denied","Wrong password!")
            sys.exit()

# === Main ===
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app_lock()
    launcher = Launcher()
    launcher.show()
    sys.exit(app.exec())

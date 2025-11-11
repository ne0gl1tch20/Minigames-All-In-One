#    _____    ________    _____  .___________    .____                               .__                  
#   /     \  /  _____/   /  _  \ |   \_____  \   |    |   _____   __ __  ____   ____ |  |__   ___________ 
#  /  \ /  \/   \  ___  /  /_\  \|   |/   |   \  |    |   \__  \ |  |  \/    \_/ ___\|  |  \_/ __ \_  __ \
# /    Y    \    \_\  \/    |    \   /    |    \ |    |___ / __ \|  |  /   |  \  \___|   Y  \  ___/|  | \/
# \____|__  /\______  /\____|__  /___\_______  / |_______ (____  /____/|___|  /\___  >___|  /\___  >__|   
#         \/        \/         \/            \/          \/    \/           \/     \/     \/     \/       
#                                           Made by G0ldNe0!

LAUNCHER_VERSION = "v0.2.6-prerelease"

# Standard library imports
import sys                 # Access to system-specific parameters and functions
import os, subprocess, tempfile  # os: file system operations, subprocess: run external programs, tempfile: temp files
import json, random        # json: read/write JSON files, random: random numbers/selections
import time                # Time-related functions (timestamps, sleep)
import traceback, shutil   # traceback: exception details, shutil: file operations like copy/move
from pathlib import Path   # Object-oriented filesystem paths
from typing import List, Dict  # Type hints for lists and dictionaries
from zipfile import ZipFile, ZIP_DEFLATED  # Handle ZIP archives
import importlib.util       # Dynamic import of modules by file path
import hashlib  # provides secure hashing functions (we use PBKDF2 for passwords)
import binascii  # for converting binary data to hex strings and back
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
import base64, re # encode and decode text, regular expressions

# PySide6 imports for GUI
from PySide6.QtWidgets import (  
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QScrollArea,  # Core widgets and layouts
    QFrame, QFileDialog, QLineEdit, QDialog, QMessageBox, QComboBox, QInputDialog, QSizePolicy,  # Dialogs, input widgets, and sizing
    QCheckBox, QSpinBox, QColorDialog, QFontDialog, QListWidget, QListWidgetItem, QTextEdit,  # Additional widgets
    QGridLayout  # Grid layout manager
)
from PySide6.QtGui import QIcon, QPixmap, QFont, QColor  # Icons, images, fonts, colors
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QSize  # Core functionality, animation, constants
from PySide6.QtWidgets import QGraphicsDropShadowEffect  # Shadow effect for widgets

# ------------------- PATHS / CONFIG -------------------
if os.name == 'nt':
    USER_DIR = os.path.expandvars(r"%userprofile%")
else:
    USER_DIR = os.path.expanduser("~")

MGAIO_DIR = os.path.join(USER_DIR, "Documents", ".mgaio")
SAVE_PATH = os.path.join(MGAIO_DIR, "Saves")
SETTINGS_PATH = os.path.join(MGAIO_DIR, "settingsave.json")
CACHE_PATH = os.path.join(MGAIO_DIR, "game_meta_cache.json")
RECENTLY_PLAYED_PATH = os.path.join(MGAIO_DIR, "recently_played.json")


os.makedirs(SAVE_PATH, exist_ok=True)

if getattr(sys, 'frozen', False):
    MINIGAMES_DIR = os.path.join(MGAIO_DIR, "minigames")
else:
    MINIGAMES_DIR = os.path.join(os.path.dirname(__file__), "minigames")

os.makedirs(MINIGAMES_DIR, exist_ok=True)

print("Minigames loaded from:", MINIGAMES_DIR)

REQUIRED_LIBS = ["pyinstaller"]  # Add more if needed


# ------------------- DEFAULT SETTINGS -------------------
DEFAULT_SETTINGS = {
    "theme": "light",
    "lock_password": "",
    "last_window_geometry": None,
    "recently_played": {},
    "show_tips": True,
    # gamification
    "coins": 0,
    "favorites": [],  # list of folder names
    "play_counts": {},  # folder_name -> count
    "achievements": {},  # id -> unlocked timestamp
    # feature toggles
    "mini_rewards": True,
    "achievements_panel": True,
    "favorites_only": False,
    "view_mode": "Grid",
    "grid_columns": 3,
    "card_size": "Normal",
    "daily_challenges": True,
    "easter_eggs": True,
    "particles": True,
    "sound_effects": True,
    "notifications": True,
    "font": {"family": "Segoe UI", "size": 11},  # default font
    "theme_colors": {"bg": "#FFFFFF", "fg": "#000000", "accent": "#0078D7"},  # light theme default
    "startup_script": "",  # path to optional custom startup script
    "auto_sort": "Alphabetical",  # default sorting method
    "compact_mode": False,  # default compact mode off
    "lock_on_startup": False,  # default no lock on startup
    "use_pin": False,  # default password over pin
    "auto_lock": 0,  # minutes before auto-lock
    "failed_attempts": 0,
    "lockout_until": 0,  # Unix timestamp until which login is blocked
    "max_attempts": 5,   # optional, max allowed attempts
    "lockout_duration": 60  # seconds to lock after max failed attempts
}



def load_recently_played():
    if os.path.exists(RECENTLY_PLAYED_PATH):
        try:
            with open(RECENTLY_PLAYED_PATH, "r") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_recently_played(data):
    with open(RECENTLY_PLAYED_PATH, "w") as f:
        json.dump(data, f, indent=2)

# load settings safely
try:
    if os.path.exists(SETTINGS_PATH):
        with open(SETTINGS_PATH, 'r', encoding='utf-8') as f:
            settings = json.load(f)
            # ensure defaults exist for new keys
            for k, v in DEFAULT_SETTINGS.items():
                settings.setdefault(k, v)
    else:
        settings = DEFAULT_SETTINGS.copy()
        with open(SETTINGS_PATH, 'w', encoding='utf-8') as f:
            json.dump(settings, f, indent=2)
except Exception:
    settings = DEFAULT_SETTINGS.copy()

# THEMES
themes = {
    "default": {"bg": "#1e1e2f", "fg": "#ffffff", "accent": "#ffcc00"},
    "light": {"bg": "#f0f0f0", "fg": "#222222", "accent": "#ff8800"},
    "dark": {"bg": "#121212", "fg": "#ffffff", "accent": "#00ffcc"},
}

theme = themes.get(settings.get('theme', 'default'), themes['default'])

# ------------------- UTILITIES -------------------

def password_strength(pwd: str):
    if not pwd:
        return "Empty", 0
    score = 0
    # PIN detection (only digits, length 4–6)
    if pwd.isdigit():
        if len(pwd) == 4:
            return "Fair (PIN)", 2
        elif len(pwd) >= 6:
            return "Good (PIN)", 3

    # Regular password rules
    if len(pwd) >= 4:
        score += 1
    if re.search(r'\d', pwd):
        score += 1
    if re.search(r'[!@#$%^&*(),.?":{}|<>]', pwd):
        score += 1
    sequences = ['0123','1234','2345','3456','4567','5678','6789','7890',
                 '9876','8765','7654','6543','5432','4321','3210','0987']
    if any(seq in pwd for seq in sequences):
        return "Weak", score
    if score <= 1:
        return "Weak", score
    elif score == 2:
        return "Fair", score
    elif score == 3:
        return "Good", score
    elif score == 4:
        return "Strong", score
    else:
        return "Stronger", score


def encrypt_json(data: dict, password: str) -> str:
    """Encrypt JSON dict using AES with password."""
    raw = json.dumps(data).encode('utf-8')
    key = password.encode('utf-8').ljust(32, b'\0')[:32]  # 32-byte key
    cipher = AES.new(key, AES.MODE_EAX)
    ciphertext, tag = cipher.encrypt_and_digest(raw)
    return base64.b64encode(cipher.nonce + tag + ciphertext).decode('utf-8')

def decrypt_json(enc_text: str, password: str) -> dict:
    """Decrypt AES-encrypted JSON string."""
    data = base64.b64decode(enc_text)
    key = password.encode('utf-8').ljust(32, b'\0')[:32]
    nonce, tag, ciphertext = data[:16], data[16:32], data[32:]
    cipher = AES.new(key, AES.MODE_EAX, nonce=nonce)
    raw = cipher.decrypt_and_verify(ciphertext, tag)
    return json.loads(raw)

def save_settings():
    try:
        os.makedirs(os.path.dirname(SETTINGS_PATH), exist_ok=True)
        with open(SETTINGS_PATH, 'w', encoding='utf-8') as f:
            json.dump(settings, f, indent=2)
    except Exception as e:
        print('Failed to save settings:', e)

def safe_load_json(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return None

# Achievements definitions
ACHIEVEMENTS_DEF = {
    "first_play": {"name": "First Play", "desc": "Play any game for the first time", "coins": 5},
    "five_plays": {"name": "5 Plays", "desc": "Play games 5 times total", "coins": 10},
    "ten_plays": {"name": "10 Plays", "desc": "Play games 10 times total", "coins": 25},
    "favorite_creator": {"name": "Favorite Creator", "desc": "Mark a game as favorite", "coins": 7},
}

# ------------------- UI COMPONENTS -------------------
class GameCard(QFrame):
    """Represents a single minigame card with launch, instructions, reorder buttons, favorite toggle."""

    def __init__(self, meta: dict, parent=None):
        super().__init__(parent)
        self.meta = meta
        self.setObjectName('game_card')
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.setMinimumHeight(120)
        self.setFrameShape(QFrame.StyledPanel)
        self.setStyleSheet('border-radius:12px;')

        # Shadow effect
        shadow = QGraphicsDropShadowEffect(blurRadius=18, xOffset=0, yOffset=6)
        shadow.setColor(QColor(0, 0, 0, 160))
        self.setGraphicsEffect(shadow)

        # Build UI
        self._build_ui()
        self.apply_theme()

        # Hover animation
        self.anim = QPropertyAnimation(self, b'geometry')
        self.anim.setDuration(180)
        self.anim.setEasingCurve(QEasingCurve.OutCubic)

    def _build_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(6)

        # Main info area
        top_layout = QHBoxLayout()
        self._add_icon(top_layout)
        self._add_text_column(top_layout)
        self._add_buttons_column(top_layout)

        layout.addLayout(top_layout)

        # Extra metadata info (Author, Version, Release Date)
        self._add_meta_info(layout)

        # Tags
        self._add_tags(layout)

        self.setLayout(layout)

    def update_layout_view(self, view_mode: str):
        """Update card layout depending on Grid or List view."""
        self.current_view = view_mode
        compact = settings.get("compact_mode", False)

        if view_mode == "Grid":
            # Smaller, stacked layout
            self.setMaximumHeight(180 if not compact else 100)
            self.desc_label.setVisible(not compact)
            self.howto_btn.setVisible(not compact)
            self.title_label.setAlignment(Qt.AlignCenter)
        else:
            # List mode: horizontal full info
            self.setMaximumHeight(220 if not compact else 120)
            self.desc_label.setVisible(True)
            self.howto_btn.setVisible(True)
            self.title_label.setAlignment(Qt.AlignLeft)
        
        self.update()

    def _add_icon(self, parent_layout):
        self.icon_label = QLabel()
        self.icon_label.setFixedSize(56, 56)
        icon_path = os.path.join(self.meta.get('path', ''), 'icon.ico')
        if os.path.exists(icon_path):
            try:
                pixmap = QPixmap(icon_path).scaled(56, 56, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.icon_label.setPixmap(pixmap)
            except Exception:
                pass
        parent_layout.addWidget(self.icon_label)

    def _add_text_column(self, parent_layout):
        text_layout = QVBoxLayout()
        self.title_label = QLabel(self.meta.get('title', 'Unknown'))
        self.title_label.setFont(QFont('Segoe UI', 13, QFont.Bold))
        self.title_label.setWordWrap(False)
        text_layout.addWidget(self.title_label)

        self.desc_label = QLabel(self.meta.get('description', ''))
        self.desc_label.setFont(QFont('Segoe UI', 10))
        self.desc_label.setWordWrap(True)
        self.desc_label.setMaximumHeight(38)
        text_layout.addWidget(self.desc_label)

        parent_layout.addLayout(text_layout, stretch=1)

    def update_ui(self):
        """Update card according to current launcher settings."""
        # Theme
        self.apply_theme()
        
        # Favorites filter
        folder = self.meta.get("folder_name")
        if settings.get("favorites_only", False) and folder not in settings.get("favorites", []):
            self.hide()
        else:
            self.show()
        
        # Compact mode
        compact = settings.get("compact_mode", False)
        self.setMaximumHeight(100 if compact else 200)
        self.desc_label.setVisible(not compact)
        self.howto_btn.setVisible(not compact)
        
        # Card size
        size = settings.get("card_size", "Normal")
        if size == "Mini":
            self.setFixedHeight(100)
        elif size == "Normal":
            self.setFixedHeight(140)
        else:  # Large
            self.setFixedHeight(180)

    def _add_meta_info(self, parent_layout):
        """Shows author, version, and release date below the description."""
        # Pull directly from meta; fallback only if missing
        author = self.meta.get("author", "—")           # Shows "—" if no author
        version = self.meta.get("version", "1.0.0")    # Default to 1.0.0 if missing
        release_date = self.meta.get("release_date", "—")  # Shows "—" if no date

        info_label = QLabel(f"👤 {author}  •  🕓 {release_date}  •  🧩 v{version}")
        info_label.setFont(QFont("Segoe UI", 9))
        info_label.setStyleSheet("color: gray;")
        parent_layout.addWidget(info_label)


    def _add_buttons_column(self, parent_layout):
        btn_layout = QVBoxLayout()
        btn_layout.setSpacing(6)

        self.play_btn = QPushButton('▶ Play')
        self.play_btn.setFixedHeight(30)
        self.play_btn.clicked.connect(self.launch_game)
        btn_layout.addWidget(self.play_btn)

        self.howto_btn = QPushButton('❓ How to Play')
        self.howto_btn.setFixedHeight(30)
        self.howto_btn.clicked.connect(self.show_howto)
        btn_layout.addWidget(self.howto_btn)

        self.favorite_btn = QPushButton('⭐ Favorite')
        self.favorite_btn.setCheckable(True)
        folder_name = self.meta.get('folder_name')
        fav_list = settings.get('favorites', [])
        self.favorite_btn.setChecked(folder_name in fav_list)
        self.favorite_btn.clicked.connect(self.toggle_favorite)
        btn_layout.addWidget(self.favorite_btn)

        reorder_layout = QHBoxLayout()
        self.up_btn = QPushButton('▲')
        self.up_btn.setFixedSize(30, 28)
        self.down_btn = QPushButton('▼')
        self.down_btn.setFixedSize(30, 28)
        reorder_layout.addWidget(self.up_btn)
        reorder_layout.addWidget(self.down_btn)
        btn_layout.addLayout(reorder_layout)

        parent_layout.addLayout(btn_layout)
        
    def toggle_favorite(self):
        folder = self.meta.get('folder_name')
        favs = settings.setdefault('favorites', [])
        if self.favorite_btn.isChecked():
            if folder not in favs:
                favs.append(folder)
                # achievement for marking favorite
                check_unlock_achievement('favorite_creator')
        else:
            if folder in favs:
                favs.remove(folder)
        settings['favorites'] = favs
        save_settings()

    def _add_tags(self, parent_layout):
        tags = self.meta.get('tags', [])
        if not tags:
            return
        tags_layout = QHBoxLayout()
        for t in tags[:5]:
            chip = QLabel(t)
            chip.setStyleSheet('padding:4px 8px; border-radius:8px; background-color:#2c2c2c; color:white;')
            chip.setFont(QFont('Segoe UI', 9))
            tags_layout.addWidget(chip)
        tags_layout.addStretch()
        parent_layout.addLayout(tags_layout)

    def apply_theme(self):
        self.setStyleSheet(f"background-color: {theme['bg']}; border-radius:12px;")
        self.title_label.setStyleSheet(f"color: {theme['accent']};")
        self.desc_label.setStyleSheet(f"color: {theme['fg']};")

        primary_btn_style = f"""
            QPushButton {{
                background-color: {theme['accent']};
                color: #000;
                border-radius: 8px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #ffffff;
                color: {theme['accent']};
            }}
        """
        secondary_btn_style = f"""
            QPushButton {{
                background-color: {theme['fg']};
                color: {theme['bg']};
                border-radius: 6px;
            }}
        """

        self.play_btn.setStyleSheet(primary_btn_style)
        self.howto_btn.setStyleSheet(secondary_btn_style)
        self.up_btn.setStyleSheet(secondary_btn_style)
        self.down_btn.setStyleSheet(secondary_btn_style)
        self.favorite_btn.setStyleSheet(secondary_btn_style)

    def launch_game(self):
        import PySide6.QtWidgets as QtWidgets
        import subprocess
        import os
        import sys
        import time

        entry_file = self.meta.get('entry', 'main.py')  # fallback to 'main.py'
        main_py = os.path.join(self.meta.get('path', ''), entry_file)
        if not os.path.exists(main_py):
            QtWidgets.QMessageBox.warning(self, 'Launch Error',
                                        f"No main.py found in {self.meta.get('path')}")
            return

        folder_name = self.meta.get('folder_name') or os.path.basename(self.meta.get('path', ''))

        # ------------------- Update recently played -------------------
        # 1. Update settings
        settings.setdefault('recently_played', {})[folder_name] = int(time.time())
        pc = settings.setdefault('play_counts', {})
        pc[folder_name] = pc.get(folder_name, 0) + 1
        settings['play_counts'] = pc
        if settings.get('mini_rewards', True):
            settings['coins'] = settings.get('coins', 0) + 1
        save_settings()

        # 2. Update dedicated recently_played.json
        try:
            RECENTLY_PLAYED_PATH = os.path.join(MGAIO_DIR, "recently_played.json")
            if os.path.exists(RECENTLY_PLAYED_PATH):
                with open(RECENTLY_PLAYED_PATH, "r") as f:
                    recent = json.load(f)
            else:
                recent = {}

            recent[folder_name] = int(time.time())
            with open(RECENTLY_PLAYED_PATH, "w") as f:
                json.dump(recent, f, indent=2)
        except Exception as e:
            print("Failed to update recently_played.json:", e)

        # ------------------- Achievements -------------------
        total_plays = sum(settings.get('play_counts', {}).values())
        if total_plays >= 1: check_unlock_achievement('first_play')
        if total_plays >= 5: check_unlock_achievement('five_plays')
        if total_plays >= 10: check_unlock_achievement('ten_plays')

        # ------------------- Launch game -------------------
        try:
            subprocess.Popen([sys.executable, main_py])
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, 'Launch Failed',
                                        f'Failed to launch game: {e}')




    def show_howto(self):
        txt = self.meta.get('how_to_play') or 'No instructions available.'
        dlg = QDialog(self)
        dlg.setWindowTitle(f"How to Play — {self.meta.get('title', 'Game')}")
        dlg.resize(520, 420)
        dlg.setStyleSheet(f"background-color: {theme['bg']}; color: {theme['fg']};")
        layout = QVBoxLayout()
        label = QLabel(txt)
        label.setWordWrap(True)
        label.setFont(QFont('Segoe UI', 11))
        layout.addWidget(label)
        dlg.setLayout(layout)
        dlg.exec()

# ------------------- Achievements UI & Logic -------------------

def check_unlock_achievement(aid: str):
    if aid not in ACHIEVEMENTS_DEF:
        return
    ach = settings.setdefault('achievements', {})
    if aid in ach:
        return  # already unlocked
    # unlock
    ach[aid] = int(time.time())
    settings['achievements'] = ach
    # award coins if defined
    coin_award = ACHIEVEMENTS_DEF.get(aid, {}).get('coins', 0)
    if coin_award and settings.get('mini_rewards', True):
        settings['coins'] = settings.get('coins', 0) + coin_award
    save_settings()
    # notify user
    try:
        QMessageBox.information(None, 'Achievement Unlocked!',
                                f"{ACHIEVEMENTS_DEF[aid]['name']}\n{ACHIEVEMENTS_DEF[aid]['desc']}\n+{coin_award} coins")
    except Exception:
        print('Achievement unlocked:', aid)


class AchievementsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Achievements")
        self.resize(480, 420)
        self.setStyleSheet(f"background-color: {theme['bg']}; color: {theme['fg']};")
        layout = QVBoxLayout()

        self.list_widget = QListWidget()
        layout.addWidget(self.list_widget)

        self.desc = QTextEdit()
        self.desc.setReadOnly(True)
        self.desc.setFixedHeight(120)
        layout.addWidget(self.desc)

        close_btn = QPushButton('Close')
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

        self.setLayout(layout)
        self.populate()

    def populate(self):
        self.list_widget.clear()
        ach_state = settings.get('achievements', {})
        for aid, info in ACHIEVEMENTS_DEF.items():
            unlocked = aid in ach_state
            text = f"{info['name']} {'(Unlocked)' if unlocked else '(Locked)'}"
            item = QListWidgetItem(text)
            item.setData(Qt.UserRole, aid)
            self.list_widget.addItem(item)
        self.list_widget.currentItemChanged.connect(self.on_select)

    def on_select(self, cur: QListWidgetItem, prev: QListWidgetItem):
        if not cur:
            self.desc.setPlainText('')
            return
        aid = cur.data(Qt.UserRole)
        info = ACHIEVEMENTS_DEF.get(aid, {})
        unlocked = aid in settings.get('achievements', {})
        ts = settings.get('achievements', {}).get(aid)
        ts_text = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(ts)) if ts else '—'
        self.desc.setPlainText(f"{info.get('desc','')}\n\nUnlocked: {unlocked}\nWhen: {ts_text}\nReward coins: {info.get('coins',0)}")

# ------------------- SETTINGS DIALOG -------------------
class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Launcher Settings")
        self.resize(420, 620)
        self.setStyleSheet(f"background-color: {theme['bg']}; color:{theme['fg']}")

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        self.layout = QVBoxLayout(content)
        scroll.setWidget(content)

        main_layout = QVBoxLayout(self)
        main_layout.addWidget(scroll)

        # Sections
        self._app_lock_section()
        self._theme_section()
        self._launcher_layout_section()
        self._game_management_section()
        self._backup_restore_section()
        self._advanced_features_section()
        self._fun_section()

        save_btn = QPushButton("Save Settings")
        save_btn.clicked.connect(self.save_all)
        self.layout.addWidget(save_btn)

    def _theme_section(self):
        self.add_section_label("--- 🎨 Theme & UI Customization ---")
        self.layout.addWidget(QLabel("Theme Presets:"))
        for key in themes.keys():
            btn = QPushButton(key.capitalize())
            btn.clicked.connect(lambda _, k=key: self.apply_theme(k))
            self.layout.addWidget(btn)

        for label, key in [("Background", "bg"), ("Foreground", "fg"), ("Accent", "accent")]:
            btn = QPushButton(f"Pick {label} Color")
            btn.clicked.connect(lambda _, k=key: self.pick_color(k))
            self.layout.addWidget(btn)

        self.font_btn = QPushButton("Pick Font")
        self.font_btn.clicked.connect(self.pick_font)
        self.layout.addWidget(self.font_btn)
        
        
        # Import / Export theme buttons
        self.import_theme_btn = QPushButton("Import Theme")
        self.import_theme_btn.clicked.connect(self.import_theme)
        self.layout.addWidget(self.import_theme_btn)

        self.export_theme_btn = QPushButton("Export Theme")
        self.export_theme_btn.clicked.connect(self.export_theme)
        self.layout.addWidget(self.export_theme_btn)

    def import_theme(self):
        path, _ = QFileDialog.getOpenFileName(self, "Import Theme JSON", "", "JSON Files (*.json)")
        if not path:
            return

        password, ok = QInputDialog.getText(self, "Password (optional)", "Enter password if encrypted:", QLineEdit.Normal)
        try:
            with open(path, 'r', encoding='utf-8') as f:
                text = f.read()
                if ok and password:
                    data = decrypt_json(text, password)
                else:
                    data = json.loads(text)

            if 'name' in data and 'bg' in data and 'fg' in data:
                themes[data['name']] = data
                QMessageBox.information(self, "Theme Imported", f"Theme '{data['name']}' added!")
            else:
                QMessageBox.warning(self, "Error", "Invalid theme file!")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to import theme:\n{e}")

    def export_theme(self):
        current_theme_name = settings.get("theme", "default")
        if current_theme_name not in themes:
            QMessageBox.warning(self, "Export Theme", "Current theme not found!")
            return

        path, _ = QFileDialog.getSaveFileName(self, "Export Theme JSON", "", "JSON Files (*.json)")
        if not path:
            return

        password, ok = QInputDialog.getText(self, "Password (optional)", "Enter password to encrypt (leave blank for none):", QLineEdit.Normal)
        try:
            data = themes[current_theme_name]
            if ok and password:
                out_text = encrypt_json(data, password)
            else:
                out_text = json.dumps(data, indent=2)

            with open(path, 'w', encoding='utf-8') as f:
                f.write(out_text)

            QMessageBox.information(self, "Theme Exported", f"Theme '{current_theme_name}' exported successfully!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to export theme:\n{e}")


    def _launcher_layout_section(self):
        self.add_section_label("--- 🖥️ Launcher Layout & Behavior ---")

        self.a_toggle = QCheckBox("OMG THERES NOTHING HEREE")
        self.layout.addWidget(self.a_toggle)

    def _game_management_section(self):
        self.add_section_label("--- 🎮 Game Management ---")
        self.favorites_toggle = QCheckBox("Show Favorites Only")
        self.favorites_toggle.setChecked(settings.get("favorites_only", False))
        self.layout.addWidget(self.favorites_toggle)

        self.auto_sort_combo = QComboBox()
        self.auto_sort_combo.addItems(["Alphabetical", "Recently Played", "Favorites"])
        self.auto_sort_combo.setCurrentText(settings.get("auto_sort", "Alphabetical"))
        self.layout.addWidget(QLabel("Auto-Sort Games By:"))
        self.layout.addWidget(self.auto_sort_combo)

        self.bulk_backup_btn = QPushButton("Backup All Game Saves")
        self.bulk_backup_btn.clicked.connect(self.backup_saves)
        self.layout.addWidget(self.bulk_backup_btn)

        self.bulk_restore_btn = QPushButton("Restore All Game Saves")
        self.bulk_restore_btn.clicked.connect(self.restore_saves)
        self.layout.addWidget(self.bulk_restore_btn)

        # Clear cache button
        self.clear_cache_btn = QPushButton("Clear Game Cache")
        self.clear_cache_btn.clicked.connect(self.clear_cache)
        self.layout.addWidget(self.clear_cache_btn)

    def backup_saves(self):
        if not os.path.exists(SAVE_PATH):
            QMessageBox.warning(self, "Backup", "No saves found to backup!")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Backup Game Saves", "", "ZIP Files (*.zip)")
        if path:
            try:
                with ZipFile(path, "w", ZIP_DEFLATED) as zipf:
                    for root, dirs, files in os.walk(SAVE_PATH):
                        for file in files:
                            full_path = os.path.join(root, file)
                            arcname = os.path.relpath(full_path, SAVE_PATH)
                            zipf.write(full_path, arcname)
                QMessageBox.information(self, "Backup", "All game saves have been backed up!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to backup saves:\n{e}")

    def restore_saves(self):
        path, _ = QFileDialog.getOpenFileName(self, "Restore Game Saves", "", "ZIP Files (*.zip)")
        if path:
            reply = QMessageBox.question(
                self, "Restore Saves",
                "This will overwrite your current saves. Continue?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                try:
                    if os.path.exists(SAVE_PATH):
                        shutil.rmtree(SAVE_PATH)
                    os.makedirs(SAVE_PATH, exist_ok=True)
                    with ZipFile(path, "r") as zipf:
                        zipf.extractall(SAVE_PATH)
                    QMessageBox.information(self, "Restore", "All game saves have been restored!")
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to restore saves:\n{e}")

    def clear_cache(self):
        reply = QMessageBox.question(
            self, "Clear Cache?",
            "Only do this if a game isn't working properly.\n\nDo you want to clear the cache?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            try:
                if os.path.exists(CACHE_PATH):
                    os.remove(CACHE_PATH)
                QMessageBox.information(self, "Cache Cleared", "Game cache has been cleared.")
                # reload games after clearing cache
                if hasattr(self.parent(), "load_games"):
                    self.parent().load_games()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to clear cache:\n{e}")
                
    def _app_lock_section(self):
        self.add_section_label("--- 🔒 App Lock & Security ---")

        self.pwd_input = QLineEdit()
        self.pwd_input.setEchoMode(QLineEdit.Password)
        self.pwd_input.setText(settings.get("lock_password", ""))
        self.layout.addWidget(QLabel("Set App Lock Password or PIN:"))
        self.layout.addWidget(self.pwd_input)

        self.strength_label = QLabel("Strength: ")
        self.strength_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.layout.addWidget(self.strength_label)

        # Update strength dynamically
        self.pwd_input.textChanged.connect(lambda: self.strength_label.setText(
            "Strength: " + password_strength(self.pwd_input.text())[0]
        ))

        self.pin_checkbox = QCheckBox("Use 4-digit PIN instead of password")
        self.pin_checkbox.setChecked(settings.get("use_pin", False))
        self.layout.addWidget(self.pin_checkbox)

        self.lock_on_startup = QCheckBox("Lock on startup")
        self.lock_on_startup.setChecked(settings.get("lock_on_startup", False))
        self.layout.addWidget(self.lock_on_startup)

        self.auto_lock_spin = QSpinBox()
        self.auto_lock_spin.setRange(0, 120)
        self.auto_lock_spin.setSuffix(" min")
        self.auto_lock_spin.setValue(settings.get("auto_lock", 0))
        self.layout.addWidget(QLabel("Auto-lock timeout (0=disabled):"))
        self.layout.addWidget(self.auto_lock_spin)

    def _backup_restore_section(self):
        self.add_section_label("💾 Backup / Restore")
        for text, func in [("Backup Settings Now", self.backup),
                           ("Restore Settings Now", self.restore),
                           ("Reset to Default", self.reset_to_default)]:
            btn = QPushButton(text)
            btn.clicked.connect(func)
            self.layout.addWidget(btn)

    def _advanced_features_section(self):
        self.add_section_label("--- ⚙ Advanced Features ---")
        self.custom_script_btn = QPushButton("Select Startup Script")
        self.custom_script_btn.clicked.connect(self.select_script)
        self.layout.addWidget(self.custom_script_btn)

    def _fun_section(self):
        toggles = [
            ("Enable Daily Challenges", "daily_challenges"),
            ("Enable Mini Rewards", "mini_rewards"),
            ("Enable Particles", "particles"),
            ("Enable Sound Effects", "sound_effects"),
            ("Enable Notifications", "notifications"),
            ("Enable Achievements Panel", "achievements_panel"),
            ("Enable Easter Eggs", "easter_eggs")
        ]

        for text, key in toggles:
            cb = QCheckBox(text)
            cb.setChecked(settings.get(key, True))
            setattr(self, f"{key}_toggle", cb)
            self.layout.addWidget(cb)


        # Example: when user clicks the coin label in settings
        coins_label = QLabel(f"Coins: {settings.get('coins', 0)}")
        coins_label.mousePressEvent = lambda e: self.trigger_easter_egg()
        self.layout.addWidget(coins_label)


    def trigger_easter_egg(self):
        if not settings.get("easter_eggs", True):
            return  # Easter eggs are disabled

        # Fun popup with a random message or image
        messages = [
            "🎉 Surprise! You found an Easter Egg!",
            "🥚 Crack the code, win a cookie!",
            "🦎 Lizard is watching you...",
            "✨ Magic mode activated!"
        ]
        msg = random.choice(messages)
        QMessageBox.information(self, "Easter Egg", msg)


    def add_section_label(self, text):
        lbl = QLabel(text)
        lbl.setStyleSheet("font-weight:bold; margin-top:10px;")
        self.layout.addWidget(lbl)

    def apply_theme(self, name):
        global theme
        theme = themes[name]
        settings["theme"] = name
        save_settings()
        QMessageBox.information(self, "Theme", f"Applied theme: {name}")

    def pick_color(self, key):
        color = QColorDialog.getColor()
        if color.isValid():
            theme[key] = color.name()
            settings["theme_colors"] = theme
            save_settings()
            QMessageBox.information(self, "Color Picker", f"{key.capitalize()} set to {color.name()}")

    def pick_font(self):
        font, ok = QFontDialog.getFont(
            QFont(settings.get("font", {}).get("family", "Segoe UI"), settings.get("font", {}).get("size", 11)),
            self,
            "Select Font"
        )
        if ok:
            settings["font"] = {"family": font.family(), "size": font.pointSize()}
            save_settings()
            QMessageBox.information(self, "Font", f"Font set to {font.family()} {font.pointSize()}pt")

    def backup(self):
        path, _ = QFileDialog.getSaveFileName(self, "Backup Settings", "", "JSON Files (*.json)")
        if path:
            with open(path, "w") as f:
                json.dump(settings, f, indent=2)
            QMessageBox.information(self, "Backup", "Settings backed up.")

    def restore(self):
        path, _ = QFileDialog.getOpenFileName(self, "Restore Settings", "", "JSON Files (*.json)")
        if path:
            data = safe_load_json(path) or {}
            settings.update(data)
            save_settings()
            QMessageBox.information(self, "Restore", "Settings restored.")

    def reset_to_default(self):
        # First warning prompt
        reply = QMessageBox.warning(
            self,
            "⚠️ Reset to Default",
            "This will erase all your current settings and cannot be undone!\n\nDo you want to continue?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return

        # Second typed confirmation
        text, ok = QInputDialog.getText(
            self,
            "Confirm Reset",
            "Type 'RESET' to confirm:",
            QLineEdit.Normal
        )
        if not ok or text.strip().upper() != "RESET":
            QMessageBox.information(self, "Cancelled", "Reset cancelled.")
            return

        # Proceed with actual reset
        global theme
        settings.clear()
        settings.update(DEFAULT_SETTINGS.copy())
        theme = themes["default"]
        save_settings()
        QMessageBox.information(self, "Reset", "Settings have been reset to default.")
        sys.exit()


    def select_script(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Python Startup Script", "", "Python Files (*.py)")
        if path:
            settings["startup_script"] = path
            save_settings()
            QMessageBox.information(self, "Startup Script", f"Selected: {path}")

    def save_all(self):
        password = self.pwd_input.text().strip()
        use_pin = self.pin_checkbox.isChecked()

        # --- Password & PIN validation ---
        def password_strength(pwd):
            score = 0
            if len(pwd) >= 4:
                score += 1
            if re.search(r'\d', pwd):
                score += 1
            if re.search(r'[!@#$%^&*(),.?":{}|<>]', pwd):
                score += 1
            # Detect simple sequences
            sequences = ['0123','1234','2345','3456','4567','5678','6789','7890',
                        '9876','8765','7654','6543','5432','4321','3210','0987']
            if any(seq in pwd for seq in sequences):
                return "Weak (sequence)", score

            if score <= 1:
                return "Weak", score
            elif score == 2:
                return "Fair", score
            elif score == 3:
                return "Good", score
            elif score == 4:
                return "Strong", score
            else:
                return "Stronger", score

        # --- PIN mode ---
        if use_pin:
            if not password.isdigit() or len(password) != 4:
                QMessageBox.warning(
                    None, "Invalid PIN",
                    "Your PIN must be exactly 4 digits (0–9 only)."
                )
                return
            settings["lock_password"] = hash_password(password)
            settings["use_pin"] = True
        else:
            # --- Password mode ---
            if password:
                strength, _ = password_strength(password)
                if strength not in ["Strong", "Stronger"]:
                    QMessageBox.warning(
                        None, "Weak Password",
                        f"Your password is too weak: {strength}\n"
                        "Please use at least 4 characters, include 1 number and 1 symbol, and avoid simple sequences."
                    )
                    return
                settings["lock_password"] = hash_password(password)
            else:
                settings["lock_password"] = ""  # no password set
            settings["use_pin"] = False
        
        settings["lock_on_startup"] = self.lock_on_startup.isChecked()
        settings["auto_lock"] = self.auto_lock_spin.value()

        settings["favorites_only"] = self.favorites_toggle.isChecked()
        settings["auto_sort"] = self.auto_sort_combo.currentText()

        for key in ["particles", "sound_effects", "notifications", "achievements_panel",
                    "daily_challenges", "mini_rewards", "easter_eggs"]:
            settings[key] = getattr(self, f"{key}_toggle").isChecked()
        save_settings()
        QMessageBox.information(self, "Settings", "All settings saved!")
        # Reload games/cards in new view
        if hasattr(self.parent(), 'load_games'):
            self.parent().load_games()
        self.accept()

# ------------------- MAIN LAUNCHER -------------------
class Launcher(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowIcon(QIcon(self.resource_path("data/icon.ico")))
        self.setWindowTitle("Minigames All In One Launcher")
        self.setMinimumSize(760, 540)
        self.setStyleSheet(f"background-color: {theme['bg']};")

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(14, 14, 14, 14)
        main_layout.setSpacing(10)

        self._init_top_bar(main_layout)
        self._init_scroll_area(main_layout)

        self.setLayout(main_layout)

        self.cards: List[GameCard] = []
        self.game_meta: List[Dict] = []
        self.available_tags = set()

        self.load_games()
        self._restore_geometry()
        self._easter_code = [Qt.Key_Up, Qt.Key_Up, Qt.Key_Down, Qt.Key_Down,
                             Qt.Key_Left, Qt.Key_Right, Qt.Key_Left, Qt.Key_Right,
                             Qt.Key_B, Qt.Key_A]
        self._current_code = []

    def keyPressEvent(self, event):
        self._current_code.append(event.key())
        if self._current_code[-len(self._easter_code):] == self._easter_code:
            self.trigger_easter_egg()
            self._current_code.clear()
        elif len(self._current_code) > len(self._easter_code):
            self._current_code.pop(0)

    def trigger_easter_egg(self):
        QMessageBox.information(self, "🎉 Secret Unlocked!", "You found the hidden game! 🕹️")
        
    def validate_cache(self):
        cache = safe_load_json(CACHE_PATH) or {'handled': {}, 'meta': []}
        valid_folders = set(os.listdir(MINIGAMES_DIR))
        removed = []
        for folder in list(cache['handled'].keys()):
            if folder not in valid_folders:
                del cache['handled'][folder]
                removed.append(folder)
        if removed:
            with open(CACHE_PATH, 'w', encoding='utf-8') as f:
                json.dump(cache, f, indent=2)
        return removed
            

    def _init_top_bar(self, parent_layout):
        top_bar = QHBoxLayout()

        self.search = QLineEdit()
        self.search.setPlaceholderText("Search by title, description or tag...")
        self.search.textChanged.connect(self.filter_games)
        top_bar.addWidget(self.search, stretch=2)

        self.filter_combo = QComboBox()
        self.filter_combo.addItem("All")
        self.filter_combo.currentIndexChanged.connect(self.filter_games)
        self.filter_combo.setFixedHeight(34)
        top_bar.addWidget(self.filter_combo, stretch=0)

        for label, callback in [
            ("🔄 Refresh", self.load_games),
            ("⚙ Settings", self.open_settings),
            ("❔ Help", self.show_help),
            ("ℹ About", self.show_about),
            ("🏆 Achievements", self.open_achievements),
        ]:
            btn = QPushButton(label)
            btn.setFixedHeight(34)
            btn.clicked.connect(callback)
            top_bar.addWidget(btn)

        parent_layout.addLayout(top_bar)

    def _init_scroll_area(self, parent_layout):
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        container = QWidget()
        self.vbox = QVBoxLayout(container)
        self.vbox.setSpacing(10)
        self.scroll.setWidget(container)
        parent_layout.addWidget(self.scroll)

    @staticmethod
    def resource_path(relative_path):
        if hasattr(sys, "_MEIPASS"):
            return os.path.join(sys._MEIPASS, relative_path)
        return os.path.join(os.path.abspath("."), relative_path)

    def _restore_geometry(self):
        geom = settings.get('last_window_geometry')
        if geom:
            try:
                self.restoreGeometry(bytes.fromhex(geom))
            except Exception:
                pass

    def closeEvent(self, event):
        try:
            geom = self.saveGeometry().toHex().data().hex()
            settings['last_window_geometry'] = geom
        except Exception:
            pass
        save_settings()
        return super().closeEvent(event)

    def load_games(self):
        self._clear_cards()

        # --- validate cache first ---
        removed = self.validate_cache()
        if removed:
            print(f"Removed missing/deleted games from cache: {removed}")  # optional, for debug/log

        cache = safe_load_json(CACHE_PATH) or {'handled': {}, 'meta': []}
        cache_handled = cache.get('handled', {})
        fresh_meta = []

        for folder in sorted(os.listdir(MINIGAMES_DIR), key=str.lower):
            folder_path = os.path.join(MINIGAMES_DIR, folder)
            if not os.path.isdir(folder_path):
                continue
            meta = self._load_game_meta(folder, folder_path, cache_handled)
            meta['favorite'] = folder in settings.get('favorites', [])
            fresh_meta.append(meta)

        for card in self.cards:  # assuming you store references to your GameCard instances
            card.update_ui()

        try:
            with open(CACHE_PATH, 'w', encoding='utf-8') as f:
                json.dump({'handled': cache_handled}, f, indent=2)
        except Exception:
            pass

        # Filter favorites if needed
        if settings.get("favorites_only", False):
            fresh_meta = [m for m in fresh_meta if m.get('favorite', False)]

        # Load recently played
        recently_played = load_recently_played()

        # Sort games alphabetically for Recommended section later
        fresh_meta.sort(key=lambda m: m.get('title', '').lower())

        self._populate_cards(fresh_meta, recently_played)



    def _clear_cards(self):
        while self.vbox.count():
            w = self.vbox.takeAt(0).widget()
            if w:
                w.setParent(None)
        self.cards.clear()
        self.game_meta.clear()
        self.available_tags = set()
        self.filter_combo.clear()
        self.filter_combo.addItem('All')

    def _load_game_meta(self, folder, folder_path, cache_handled):
        try:
            mtime = int(os.path.getmtime(folder_path))
        except Exception:
            mtime = 0

        cached_entry = cache_handled.get(folder)
        if cached_entry and cached_entry.get('mtime') == mtime:
            meta = cached_entry.get('meta')
            if meta:
                meta['path'] = folder_path
                return meta

        # Defaults
        meta = {
            'title': folder,
            'description': '',
            'how_to_play': '',
            'tags': [],
            'path': folder_path,
            'folder_name': folder,
            'author': 'Unknown',
            'version': '1.0.0',
            'release_date': 'Unknown'
        }

        config_path = os.path.join(folder_path, 'config.json')
        if os.path.exists(config_path):
            try:
                data = safe_load_json(config_path)
                if isinstance(data, dict):
                    meta['title'] = data.get('title', meta['title'])
                    meta['description'] = data.get('description', meta['description'])
                    meta['how_to_play'] = data.get('how_to_play', meta['how_to_play'])
                    meta['tags'] = [str(t).strip() for t in (data.get('tags') or []) if t]
                    meta['author'] = data.get('author', meta.get('author', '—'))
                    meta['version'] = data.get('version', meta.get('version', '1.0.0'))
                    meta['release_date'] = data.get('release_date', meta.get('release_date', '—'))
                    meta['entry'] = data.get('entry', 'main.py')  # default to 'main.py' if missing

            except Exception:
                pass

        # Save to cache
        cache_handled[folder] = {'mtime': mtime, 'meta': {
            'title': meta['title'],
            'description': meta['description'],
            'how_to_play': meta['how_to_play'],
            'tags': meta['tags'],
            'folder_name': meta['folder_name'],
            'author': meta['author'],
            'version': meta['version'],
            'release_date': meta['release_date'],
            'entry': meta['entry'],  # <-- store entry path
        }}
        return meta


    def _sort_key(self, meta):
        recent_map = settings.get('recently_played', {})
        rp = recent_map.get(meta.get('folder_name'))
        if rp:
            return (0, -int(rp))
        return (1, meta.get('title', '').lower())

    def _populate_cards(self, fresh_meta, recently_played: dict):
        self.cards.clear()
        self.game_meta.clear()
        self.available_tags = set()
        self.filter_combo.clear()
        self.filter_combo.addItem('All')

        # Clear layout first
        while self.vbox.count():
            w = self.vbox.takeAt(0).widget()
            if w:
                w.setParent(None)

        # --- Recently Played Section ---
        if recently_played:
            rp_label = QLabel("Recently Played")
            rp_label.setFont(QFont("Segoe UI", 12, QFont.Bold))
            self.vbox.addWidget(rp_label)

            # Sort descending by timestamp
            sorted_rp = sorted(recently_played.items(), key=lambda x: x[1], reverse=True)
            for folder_name, _ts in sorted_rp:
                meta = next((m for m in fresh_meta if m['folder_name'] == folder_name), None)
                if meta:
                    card = GameCard(meta, self)
                    self._connect_card_buttons(card)
                    self.vbox.addWidget(card)
                    self._register_card_meta(card, meta)

        # --- Recommended Section (shuffle) ---
        rec_meta = [m for m in fresh_meta if m['folder_name'] not in recently_played]
        if rec_meta:
            rec_label = QLabel("Recommended")
            rec_label.setFont(QFont("Segoe UI", 12, QFont.Bold))
            self.vbox.addWidget(rec_label)

            random.shuffle(rec_meta)
            for meta in rec_meta:
                card = GameCard(meta, self)
                card.update_layout_view(settings.get("view_mode", "Grid"))

                self._connect_card_buttons(card)
                self.vbox.addWidget(card)
                self._register_card_meta(card, meta)

        # --- No games fallback ---
        if not fresh_meta:
            empty_label = QLabel("Games are not found!")
            empty_label.setFont(QFont("Segoe UI", 14, QFont.Bold))
            empty_label.setStyleSheet("color: red;")
            empty_label.setAlignment(Qt.AlignCenter)
            self.vbox.addWidget(empty_label)

        # Populate filter combo with tags
        for t in sorted(self.available_tags, key=str.lower):
            self.filter_combo.addItem(t)

        self.apply_theme_to_cards()
        
    def _connect_card_buttons(self, card):
        card.up_btn.clicked.connect(lambda _, c=card: self.move_card_up(c))
        card.down_btn.clicked.connect(lambda _, c=card: self.move_card_down(c))

    def _register_card_meta(self, card, meta):
        self.cards.append(card)
        self.game_meta.append({
            'title': meta.get('title', '').lower(),
            'desc': str(meta.get('description', '')).lower(),
            'tags': [t.lower() for t in meta.get('tags', [])],
            'card': card,
            'favorite': meta.get('favorite', False),
            'folder_name': meta.get('folder_name')
        })
        self.available_tags.update(meta.get('tags', []))

    def apply_current_theme(self):
        global theme
        theme = themes.get(settings.get('theme', 'default'), themes['default'])
        self.setStyleSheet(f"background-color: {theme['bg']};")
        self.apply_theme_to_cards()

    def apply_theme_to_cards(self):
        for c in self.cards:
            c.apply_theme()

    def move_card_up(self, card: 'GameCard'):
        idx = self.vbox.indexOf(card)
        if idx > 0:
            self.vbox.removeWidget(card)
            self.vbox.insertWidget(idx - 1, card)
            self._reorder_meta(card, idx - 1)

    def move_card_down(self, card: 'GameCard'):
        idx = self.vbox.indexOf(card)
        if idx < self.vbox.count() - 1:
            self.vbox.removeWidget(card)
            self.vbox.insertWidget(idx + 1, card)
            self._reorder_meta(card, idx + 1)

    def _reorder_meta(self, card, new_idx):
        for i, m in enumerate(self.game_meta):
            if m['card'] == card:
                self.game_meta.insert(new_idx, self.game_meta.pop(i))
                break

    def filter_games(self):
        q = self.search.text().strip().lower()
        tag = self.filter_combo.currentText().strip().lower()
        fav_only = settings.get('favorites_only', False)
        for m in self.game_meta:
            title_ok = q in m['title'] if q else True
            desc_ok = q in m['desc'] if q else True
            tag_ok = tag in m['tags'] if tag and tag != 'all' else True
            fav_ok = (not fav_only) or (m.get('folder_name') in settings.get('favorites', []))
            visible = (title_ok or desc_ok) and tag_ok and fav_ok
            m['card'].setVisible(visible)

    def show_help(self):
        self._show_dialog("MGAIO Launcher Help",
            "Welcome to MGAIO Launcher!\n\n"
            "• Use the search box to find games by title, description, or tags.\n"
            "• Filter games using the tag dropdown.\n"
            "• Click '▶ Play' to launch a game.\n"
            "• Click '❓ How to Play' to view game instructions.\n"
            "• Move games up/down to reorder them.\n"
            "• Settings allow theme changes, backups, and app lock.\n\n"
            "Enjoy your games! 🎮", 520, 420
        )

    def show_about(self):
        self._show_dialog(
            "About MGAIO Launcher",
            f"MGAIO Launcher {LAUNCHER_VERSION}\n"
            "Minigames All-In-One\n\n"
            "• Developed for offline minigame management\n"
            "• Features theming, search, filtering, and leaderboards\n"
            "• Saveable settings, app lock, and smooth UI\n\n"
            "© 2025 MGAIO Project",
            400, 280
        )

    def _show_dialog(self, title, text, width, height):
        dlg = QDialog(self)
        dlg.setWindowTitle(title)
        dlg.resize(width, height)
        dlg.setStyleSheet(f"background-color: {theme['bg']}; color: {theme['fg']};")
        layout = QVBoxLayout()
        label = QLabel(text)
        label.setWordWrap(True)
        label.setFont(QFont('Segoe UI', 11))
        layout.addWidget(label)
        dlg.setLayout(layout)
        dlg.exec()

    def open_settings(self):
        dlg = SettingsDialog(self)
        if dlg.exec():
            save_settings()
            self.apply_current_theme()

    def open_achievements(self):
        if not settings.get('achievements_panel', True):
            QMessageBox.information(self, 'Achievements', 'Achievements panel is disabled in settings.')
            return
        dlg = AchievementsDialog(self)
        dlg.exec()

# ------------------- APP LOCK -------------------
def hash_password(password, salt=None):
    """Hash password using PBKDF2 with SHA256"""
    if not salt:
        salt = os.urandom(16)  # generate 16-byte random salt
    pwdhash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100_000)
    return binascii.hexlify(salt).decode() + ":" + binascii.hexlify(pwdhash).decode()

def verify_password(stored_password, provided_password):
    """Verify a stored password against one provided"""
    salt_hex, pwdhash_hex = stored_password.split(":")
    salt = binascii.unhexlify(salt_hex)
    new_hash = hashlib.pbkdf2_hmac('sha256', provided_password.encode(), salt, 100_000)
    return binascii.hexlify(new_hash).decode() == pwdhash_hex

def app_lock():
    stored_hash = settings.get('lock_password')
    if not stored_hash:
        return  # no lock set

    max_attempts = 5
    lockout_duration = 60  # in seconds

    # Check if currently locked
    now = int(time.time())
    lock_until = settings.get('lockout_until', 0)
    if lock_until > now:
        remaining = lock_until - now
        QMessageBox.warning(None, "Locked Out", f"Too many wrong attempts! Try again in {remaining} seconds.")
        sys.exit(1)

    # Ask for password
    text, ok = QInputDialog.getText(None, 'App Lock', 'Enter password/pin:', QLineEdit.Password)
    if not ok:
        sys.exit(1)

    if verify_password(stored_hash, text):
        # Correct password: reset attempts
        settings['failed_attempts'] = 0
        settings['lockout_until'] = 0
        save_settings()
        return  # allow access

    # Wrong password
    settings['failed_attempts'] = settings.get('failed_attempts', 0) + 1
    remaining_tries = max_attempts - settings['failed_attempts']

    if remaining_tries <= 0:
        settings['lockout_until'] = now + lockout_duration
        QMessageBox.critical(None, 'Access Denied', f"Too many wrong attempts! Locked for {lockout_duration} seconds.")
    else:
        QMessageBox.critical(None, 'Access Denied', f"Wrong password! {remaining_tries} tries left.")

    save_settings()
    sys.exit(1)


# ------------------- RUN -------------------
if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setApplicationName('MGAIO Launcher')
    try:
        app_lock()
        launcher = Launcher()
        launcher.show()
        sys.exit(app.exec())
    except Exception as e:
        print('Fatal error:', e)
        traceback.print_exc()
        QMessageBox.critical(None, 'Fatal', f'Launcher crashed: {e}')
        sys.exit(1)

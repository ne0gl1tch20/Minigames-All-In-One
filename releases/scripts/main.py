"""
MGAIO Launcher v2 - Settings-driven, Achievements & Favorites
Updated features:
- Settings control most behavior (favorites-only view, mini rewards, achievements, daily challenges toggles)
- Favorites system saved in settings
- Reward (coins) system with mini_rewards toggle
- Achievements tracking & simple unlock rules (First Play, 5 Plays, 10 Plays, Favorite Creator)
- Achievements panel (view unlocked/locked achievements)
- Achievements pop-up on unlock
- Settings persistence and integration with UI actions

Usage: drop this alongside your minigames folder, ensure PySide6 installed
Run: python MGAIO_Launcher_v2_updated.py
"""

import sys
import os, subprocess, tempfile
import json
import time
import traceback, shutil
from pathlib import Path
from typing import List, Dict
import importlib.util

from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QScrollArea,
    QFrame, QFileDialog, QLineEdit, QDialog, QMessageBox, QComboBox, QInputDialog, QSizePolicy,
    QCheckBox, QSpinBox, QColorDialog, QFontDialog, QListWidget, QListWidgetItem, QTextEdit,
    QGridLayout
)
from PySide6.QtGui import QIcon, QPixmap, QFont, QColor
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QSize
from PySide6.QtWidgets import QGraphicsDropShadowEffect

# ------------------- PATHS / CONFIG -------------------
if os.name == 'nt':
    USER_DIR = os.path.expandvars(r"%userprofile%")
else:
    USER_DIR = os.path.expanduser("~")

MGAIO_DIR = os.path.join(USER_DIR, "Documents", ".mgaio")
SAVE_PATH = os.path.join(MGAIO_DIR, "Saves")
SETTINGS_PATH = os.path.join(MGAIO_DIR, "settingsave.json")
CACHE_PATH = os.path.join(MGAIO_DIR, "game_meta_cache.json")

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
    "theme": "default",
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
}

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
        self.setMinimumHeight(100)
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

        top_layout = QHBoxLayout()
        self._add_icon(top_layout)
        self._add_text_column(top_layout)
        self._add_buttons_column(top_layout)

        layout.addLayout(top_layout)
        self._add_tags(layout)
        self.setLayout(layout)

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

    def _add_buttons_column(self, parent_layout):
        btn_layout = QVBoxLayout()
        btn_layout.setSpacing(6)

        # Primary buttons
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
        # reflect settings favorites
        folder_name = self.meta.get('folder_name')
        fav_list = settings.get('favorites', [])
        self.favorite_btn.setChecked(folder_name in fav_list)
        self.favorite_btn.clicked.connect(self.toggle_favorite)
        btn_layout.addWidget(self.favorite_btn)

        # Reorder buttons
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
            chip.setStyleSheet('padding:4px 8px; border-radius:8px;')
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
        import shutil

        main_py = os.path.join(self.meta.get('path', ''), 'main.py')
        if not os.path.exists(main_py):
            QtWidgets.QMessageBox.warning(self, 'Launch Error', f"No main.py found in {self.meta.get('path')}")
            return

        folder_name = self.meta.get('folder_name') or os.path.basename(self.meta.get('path', ''))

        # Update settings
        settings.setdefault('recently_played', {})[folder_name] = int(time.time())
        pc = settings.setdefault('play_counts', {})
        pc[folder_name] = pc.get(folder_name, 0) + 1
        settings['play_counts'] = pc
        if settings.get('mini_rewards', True):
            settings['coins'] = settings.get('coins', 0) + 1
        save_settings()

        # Check achievements
        total_plays = sum(settings.get('play_counts', {}).values())
        if total_plays >= 1: check_unlock_achievement('first_play')
        if total_plays >= 5: check_unlock_achievement('five_plays')
        if total_plays >= 10: check_unlock_achievement('ten_plays')

        # Launch Python script directly
        try:
            subprocess.Popen([sys.executable, main_py])
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, 'Launch Failed', f'Failed to launch game: {e}')



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

    def _app_lock_section(self):
        self.add_section_label("🔒 App Lock & Security")
        self.pwd_input = QLineEdit()
        self.pwd_input.setEchoMode(QLineEdit.Password)
        self.pwd_input.setText(settings.get("lock_password", ""))
        self.layout.addWidget(QLabel("Set App Lock Password:"))
        self.layout.addWidget(self.pwd_input)

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

    def _theme_section(self):
        self.add_section_label("🎨 Theme & UI Customization")
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

        self.dark_mode_toggle = QCheckBox("Enable Dark Mode")
        self.dark_mode_toggle.setChecked(settings.get("dark_mode", False))
        self.layout.addWidget(self.dark_mode_toggle)

        self.animated_bg_toggle = QCheckBox("Enable Animated Background")
        self.animated_bg_toggle.setChecked(settings.get("animated_bg", False))
        self.layout.addWidget(self.animated_bg_toggle)

    def _launcher_layout_section(self):
        self.add_section_label("🖥️ Launcher Layout & Behavior")

        self.view_toggle = QComboBox()
        self.view_toggle.addItems(["Grid", "List"])
        self.view_toggle.setCurrentText(settings.get("view_mode", "Grid"))
        self.layout.addWidget(QLabel("Launcher View Mode:"))
        self.layout.addWidget(self.view_toggle)

        self.columns_spin = QSpinBox()
        self.columns_spin.setRange(1, 10)
        self.columns_spin.setValue(settings.get("grid_columns", 3))
        self.layout.addWidget(QLabel("Grid Columns:"))
        self.layout.addWidget(self.columns_spin)

        self.compact_mode_toggle = QCheckBox("Enable Compact Mode")
        self.compact_mode_toggle.setChecked(settings.get("compact_mode", False))
        self.layout.addWidget(self.compact_mode_toggle)

        self.card_size_combo = QComboBox()
        self.card_size_combo.addItems(["Mini", "Normal", "Large"])
        self.card_size_combo.setCurrentText(settings.get("card_size", "Normal"))
        self.layout.addWidget(QLabel("Card Size:"))
        self.layout.addWidget(self.card_size_combo)

    def _game_management_section(self):
        self.add_section_label("🎮 Game Management")
        self.favorites_toggle = QCheckBox("Show Favorites Only")
        self.favorites_toggle.setChecked(settings.get("favorites_only", False))
        self.layout.addWidget(self.favorites_toggle)

        self.hide_games_toggle = QCheckBox("Hide Selected Games")
        self.hide_games_toggle.setChecked(settings.get("hide_games", False))
        self.layout.addWidget(self.hide_games_toggle)

        self.auto_sort_combo = QComboBox()
        self.auto_sort_combo.addItems(["Alphabetical", "Recently Played", "Favorites"])
        self.auto_sort_combo.setCurrentText(settings.get("auto_sort", "Alphabetical"))
        self.layout.addWidget(QLabel("Auto-Sort Games By:"))
        self.layout.addWidget(self.auto_sort_combo)

        self.bulk_backup_btn = QPushButton("Backup All Game Saves")
        self.layout.addWidget(self.bulk_backup_btn)
        self.bulk_restore_btn = QPushButton("Restore All Game Saves")
        self.layout.addWidget(self.bulk_restore_btn)

    def _backup_restore_section(self):
        self.add_section_label("💾 Backup / Restore")
        for text, func in [("Backup Settings Now", self.backup),
                           ("Restore Settings Now", self.restore),
                           ("Reset to Default", self.reset_to_default)]:
            btn = QPushButton(text)
            btn.clicked.connect(func)
            self.layout.addWidget(btn)

    def _advanced_features_section(self):
        self.add_section_label("⚙️ Advanced Launcher Features")
        toggles = [("Enable Card Particles", "particles"),
                   ("Enable Sound Effects", "sound_effects"),
                   ("Show Notifications", "notifications"),
                   ("Show Achievements Panel", "achievements_panel")]
        for text, key in toggles:
            cb = QCheckBox(text)
            cb.setChecked(settings.get(key, True))
            setattr(self, f"{key}_toggle", cb)
            self.layout.addWidget(cb)

        self.custom_script_btn = QPushButton("Select Startup Script")
        self.custom_script_btn.clicked.connect(self.select_script)
        self.layout.addWidget(self.custom_script_btn)

    def _fun_section(self):
        self.add_section_label("🎉 Fun / Gamification")
        toggles = [("Enable Daily Challenges", "daily_challenges"),
                   ("Enable Mini Rewards", "mini_rewards"),
                   ("Enable Easter Eggs", "easter_eggs")]
        for text, key in toggles:
            cb = QCheckBox(text)
            cb.setChecked(settings.get(key, True))
            setattr(self, f"{key}_toggle", cb)
            self.layout.addWidget(cb)

        # show coin balance
        self.layout.addWidget(QLabel(f"Coins: {settings.get('coins',0)}"))

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
        global theme
        settings.clear()
        settings.update(DEFAULT_SETTINGS.copy())
        theme = themes["default"]
        save_settings()
        QMessageBox.information(self, "Reset", "Settings reset to default.")

    def select_script(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Python Startup Script", "", "Python Files (*.py)")
        if path:
            settings["startup_script"] = path
            save_settings()
            QMessageBox.information(self, "Startup Script", f"Selected: {path}")

    def save_all(self):
        settings["lock_password"] = self.pwd_input.text()
        settings["use_pin"] = self.pin_checkbox.isChecked()
        settings["lock_on_startup"] = self.lock_on_startup.isChecked()
        settings["auto_lock"] = self.auto_lock_spin.value()

        settings["dark_mode"] = self.dark_mode_toggle.isChecked()
        settings["animated_bg"] = self.animated_bg_toggle.isChecked()

        settings["view_mode"] = self.view_toggle.currentText()
        settings["grid_columns"] = self.columns_spin.value()
        settings["compact_mode"] = self.compact_mode_toggle.isChecked()
        settings["card_size"] = self.card_size_combo.currentText()

        settings["favorites_only"] = self.favorites_toggle.isChecked()
        settings["hide_games"] = self.hide_games_toggle.isChecked()
        settings["auto_sort"] = self.auto_sort_combo.currentText()

        for key in ["particles", "sound_effects", "notifications", "achievements_panel",
                    "daily_challenges", "mini_rewards", "easter_eggs"]:
            settings[key] = getattr(self, f"{key}_toggle").isChecked()

        save_settings()
        QMessageBox.information(self, "Settings", "All settings saved!")
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
        cache = safe_load_json(CACHE_PATH) or {'handled': {}, 'meta': []}
        cache_handled = cache.get('handled', {})
        fresh_meta = []

        for folder in sorted(os.listdir(MINIGAMES_DIR), key=str.lower):
            folder_path = os.path.join(MINIGAMES_DIR, folder)
            if not os.path.isdir(folder_path):
                continue
            meta = self._load_game_meta(folder, folder_path, cache_handled)
            # set favorite flag from settings
            meta['favorite'] = folder in settings.get('favorites', [])
            fresh_meta.append(meta)

        try:
            with open(CACHE_PATH, 'w', encoding='utf-8') as f:
                json.dump({'handled': cache_handled}, f, indent=2)
        except Exception:
            pass

        # Sort games (recent first or alphabetical)
        fresh_meta.sort(key=self._sort_key)

        self._populate_cards(fresh_meta)

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

        meta = {'title': folder, 'description': '', 'how_to_play': '', 'tags': [], 'path': folder_path, 'folder_name': folder}
        config_path = os.path.join(folder_path, 'config.json')
        if os.path.exists(config_path):
            try:
                data = safe_load_json(config_path)
                if isinstance(data, dict):
                    meta['title'] = data.get('title', meta['title'])
                    meta['description'] = data.get('description', '')
                    meta['how_to_play'] = data.get('how_to_play', '')
                    meta['tags'] = [str(t).strip() for t in (data.get('tags') or []) if t]
            except Exception:
                pass

        cache_handled[folder] = {'mtime': mtime, 'meta': {
            'title': meta['title'],
            'description': meta['description'],
            'how_to_play': meta['how_to_play'],
            'tags': meta['tags'],
            'folder_name': meta['folder_name']
        }}
        return meta

    def _sort_key(self, meta):
        recent_map = settings.get('recently_played', {})
        rp = recent_map.get(meta.get('folder_name'))
        if rp:
            return (0, -int(rp))
        return (1, meta.get('title', '').lower())

    def _populate_cards(self, fresh_meta):
        for meta in fresh_meta:
            card = GameCard(meta, self)
            card.up_btn.clicked.connect(lambda _, c=card: self.move_card_up(c))
            card.down_btn.clicked.connect(lambda _, c=card: self.move_card_down(c))
            self.vbox.addWidget(card)
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

        for t in sorted(self.available_tags, key=str.lower):
            self.filter_combo.addItem(t)

        self.apply_theme_to_cards()

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
        self._show_dialog("About MGAIO Launcher",
            "MGAIO Launcher v2\n"
            "Minigames All-In-One\n\n"
            "• Developed for offline minigame management\n"
            "• Features theming, search, filtering, and leaderboards\n"
            "• Saveable settings, app lock, and smooth UI\n\n"
            "© 2025 MGAIO Project", 400, 280
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

def app_lock():
    pwd = settings.get('lock_password')
    if pwd:
        text, ok = QInputDialog.getText(None, 'App Lock', 'Enter password:', QLineEdit.Password)
        if not ok or text != pwd:
            QMessageBox.critical(None, 'Access Denied', 'Wrong password')
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

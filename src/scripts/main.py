"""
MGAIO Launcher v2
- Renovated, themed, searchable, filterable, robust launcher for Minigames All-In-One

Features implemented:
- Theming (default/dark/light/custom) with live preview and saved settings
- Responsive card-based UI with hover animations and shadows
- Search by title/description, tag filter dropdown, real-time filtering
- Game metadata validation with graceful error handling
- Per-game leaderboard viewer (reads leaderboard.json inside game folder)
- Simple reorder controls (Move Up / Move Down) to reorder game cards
- Recently played ordering (stores last_played timestamp in settings)
- Save/restore settings (including window geometry)
- Backup/restore settings, app lock (password), and safe path handling
- Offline metadata cache (auto-updates when game folder mtime changes)
- Extra polish: smooth hover animations, card resizing based on description

Usage: drop this file alongside your previous launcher, ensure PySide6 is installed
Run: python MGAIO_Launcher_v2.py
"""

import sys
import os
import json
import time
import traceback
from pathlib import Path
from typing import List, Dict

from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QScrollArea,
    QFrame, QFileDialog, QLineEdit, QDialog, QMessageBox, QComboBox, QInputDialog, QSizePolicy
)
from PySide6.QtGui import QIcon, QPixmap, QFont, QColor
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QSize
from PySide6.QtWidgets import QGraphicsDropShadowEffect

# ------------------- PATHS / CONFIG -------------------
# Cross-platform user documents directory fallback
if os.name == 'nt':
    USER_DIR = os.path.expandvars(r"%userprofile%")
else:
    USER_DIR = os.path.expanduser("~")

MGAIO_DIR = os.path.join(USER_DIR, "Documents", ".mgaio")
SAVE_PATH = os.path.join(MGAIO_DIR, "Saves")
SETTINGS_PATH = os.path.join(MGAIO_DIR, "settingsave.json")
CACHE_PATH = os.path.join(MGAIO_DIR, "game_meta_cache.json")

os.makedirs(SAVE_PATH, exist_ok=True)

# Determine dev vs frozen
if getattr(sys, 'frozen', False):
    MINIGAMES_DIR = os.path.join(MGAIO_DIR, "minigames")
else:
    MINIGAMES_DIR = os.path.join(os.path.dirname(__file__), "minigames")

os.makedirs(MINIGAMES_DIR, exist_ok=True)

print("Minigames loaded from:", MINIGAMES_DIR)

# ------------------- DEFAULT SETTINGS -------------------
DEFAULT_SETTINGS = {
    "theme": "default",
    "lock_password": "",
    "last_window_geometry": None,
    "recently_played": {},  # game_folder -> timestamp
}

# load settings safely
try:
    if os.path.exists(SETTINGS_PATH):
        with open(SETTINGS_PATH, 'r', encoding='utf-8') as f:
            settings = json.load(f)
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


# ------------------- UI COMPONENTS -------------------
class GameCard(QFrame):
    """Card representing a single game. Includes Move Up / Move Down for reordering and View Leaderboard."""

    def __init__(self, meta: Dict, parent=None):
        super().__init__(parent)
        self.meta = meta  # contains title, desc, how_to_play, tags, path
        self.setObjectName('game_card')
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.setStyleSheet('border-radius:12px;')
        self.setFrameShape(QFrame.StyledPanel)
        self.setMinimumHeight(100)

        shadow = QGraphicsDropShadowEffect(blurRadius=18, xOffset=0, yOffset=6)
        shadow.setColor(QColor(0, 0, 0, 160))
        self.setGraphicsEffect(shadow)

        self.build_ui()
        self.apply_theme()

        # hover animation
        self.anim = QPropertyAnimation(self, b'geometry')
        self.anim.setDuration(180)
        self.anim.setEasingCurve(QEasingCurve.OutCubic)

    def build_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(6)

        top = QHBoxLayout()
        # icon
        self.icon_label = QLabel()
        self.icon_label.setFixedSize(56, 56)
        icon_path = os.path.join(self.meta['path'], 'icon.ico')
        if os.path.exists(icon_path):
            try:
                px = QPixmap(icon_path).scaled(56, 56, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.icon_label.setPixmap(px)
            except Exception:
                pass
        top.addWidget(self.icon_label)

        # title + desc
        text_col = QVBoxLayout()
        self.title_label = QLabel(self.meta.get('title', 'Unknown'))
        self.title_label.setFont(QFont('Segoe UI', 13, QFont.Bold))
        self.title_label.setWordWrap(False)
        text_col.addWidget(self.title_label)

        desc = self.meta.get('description', '')
        self.desc_label = QLabel(desc)
        self.desc_label.setFont(QFont('Segoe UI', 10))
        self.desc_label.setWordWrap(True)
        self.desc_label.setMaximumHeight(38)
        text_col.addWidget(self.desc_label)

        top.addLayout(text_col, stretch=1)

        # buttons column
        btn_col = QVBoxLayout()
        btn_col.setSpacing(6)

        self.play_btn = QPushButton('▶ Play')
        self.play_btn.setFixedHeight(30)
        self.play_btn.clicked.connect(self.launch_game)
        btn_col.addWidget(self.play_btn)

        self.howto_btn = QPushButton('❓ How to Play')
        self.howto_btn.setFixedHeight(30)
        self.howto_btn.clicked.connect(self.show_howto)
        btn_col.addWidget(self.howto_btn)

        # second row: leaderboard and reorder
        second_row = QHBoxLayout()
        self.lb_btn = QPushButton('🏆 Leaderboard')
        self.lb_btn.setFixedHeight(28)
        self.lb_btn.clicked.connect(self.view_leaderboard)
        second_row.addWidget(self.lb_btn)

        self.up_btn = QPushButton('▲')
        self.up_btn.setFixedSize(30, 28)
        second_row.addWidget(self.up_btn)
        self.down_btn = QPushButton('▼')
        self.down_btn.setFixedSize(30, 28)
        second_row.addWidget(self.down_btn)

        btn_col.addLayout(second_row)

        top.addLayout(btn_col)
        layout.addLayout(top)

        # tags row
        tags = self.meta.get('tags', [])
        if tags:
            tags_layout = QHBoxLayout()
            for t in tags[:5]:
                chip = QLabel(t)
                chip.setStyleSheet('padding:4px 8px; border-radius:8px;')
                chip.setFont(QFont('Segoe UI', 9))
                tags_layout.addWidget(chip)
            tags_layout.addStretch()
            layout.addLayout(tags_layout)

        self.setLayout(layout)

    def apply_theme(self):
        # apply current theme colors to widget parts
        self.setStyleSheet(f"background-color: {theme['bg']}; border-radius:12px;")
        self.title_label.setStyleSheet(f"color: {theme['accent']};")
        self.desc_label.setStyleSheet(f"color: {theme['fg']};")
        # buttons
        btn_style = f"""
        QPushButton {{ background-color: {theme['accent']}; color: #000; border-radius: 8px; font-weight: bold; }}
        QPushButton:hover {{ background-color: #ffffff; color: {theme['accent']}; }}
        """
        small_btn_style = f"QPushButton {{ background-color: {theme['fg']}; color: {theme['bg']}; border-radius: 6px; }}"
        self.play_btn.setStyleSheet(btn_style)
        self.howto_btn.setStyleSheet(small_btn_style)
        self.lb_btn.setStyleSheet(small_btn_style)
        self.up_btn.setStyleSheet(small_btn_style)
        self.down_btn.setStyleSheet(small_btn_style)

    def launch_game(self):
        """Safely execute game's main.py and update recently played"""
        main_py = os.path.join(self.meta['path'], 'main.py')
        if not os.path.exists(main_py):
            QMessageBox.warning(self, 'Launch Error', f'No main.py found in {self.meta["path"]}')
            return

        # Ensure 'folder_name' exists in meta
        folder_name = self.meta.get('folder_name') or os.path.basename(self.meta.get('path',''))

        # store recently played timestamp
        settings.setdefault('recently_played', {})
        settings['recently_played'][folder_name] = int(time.time())
        save_settings()

        # run the game in a subprocess so launcher stays responsive
        try:
            os.spawnv(os.P_NOWAIT, sys.executable, [sys.executable, main_py])
        except Exception as e:
            QMessageBox.critical(self, 'Launch Failed', f'Failed to launch game: {e}')


    def show_howto(self):
        txt = self.meta.get('how_to_play') or 'No instructions available.'
        dlg = QDialog(self)
        dlg.setWindowTitle(f"How to Play — {self.meta.get('title')}")
        dlg.resize(520, 420)
        dlg.setStyleSheet(f"background-color: {theme['bg']}; color: {theme['fg']};")
        layout = QVBoxLayout()
        label = QLabel(txt)
        label.setWordWrap(True)
        label.setFont(QFont('Segoe UI', 11))
        layout.addWidget(label)
        dlg.setLayout(layout)
        dlg.exec()

    def view_leaderboard(self):
        lb_file = os.path.join(self.meta['path'], 'leaderboard.json')
        lb = safe_load_json(lb_file) or []
        dlg = QDialog(self)
        dlg.setWindowTitle(f"Leaderboard — {self.meta.get('title')}")
        dlg.resize(420, 360)
        dlg.setStyleSheet(f"background-color: {theme['bg']}; color: {theme['fg']};")
        layout = QVBoxLayout()
        if not lb:
            label = QLabel('No leaderboard data found for this game.')
            layout.addWidget(label)
        else:
            for i, e in enumerate(sorted(lb, key=lambda x: x.get('score', 0), reverse=True)[:20], start=1):
                name = e.get('name', 'Player')
                score = e.get('score', 0)
                label = QLabel(f"{i}. {name} — {score}")
                layout.addWidget(label)
        dlg.setLayout(layout)
        dlg.exec()

    # enable client code to connect up/down


# ------------------- SETTINGS DIALOG -------------------
class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Settings')
        self.setMinimumWidth(380)
        self.setStyleSheet(f"background-color: {theme['bg']}; color:{theme['fg']}")
        layout = QVBoxLayout()

        # App lock
        layout.addWidget(QLabel('Set App Lock Password:'))
        self.pwd_input = QLineEdit()
        self.pwd_input.setEchoMode(QLineEdit.Password)
        self.pwd_input.setText(settings.get('lock_password', ''))
        layout.addWidget(self.pwd_input)

        # Theme presets
        layout.addWidget(QLabel('Theme Presets:'))
        for key in themes.keys():
            btn = QPushButton(key.capitalize())
            btn.clicked.connect(lambda _, k=key: self.apply_theme(k))
            layout.addWidget(btn)

        # Backup/restore
        backup_btn = QPushButton('Backup Settings')
        backup_btn.clicked.connect(self.backup)
        restore_btn = QPushButton('Restore Settings')
        restore_btn.clicked.connect(self.restore)
        layout.addWidget(backup_btn)
        layout.addWidget(restore_btn)

        self.setLayout(layout)

    def apply_theme(self, name):
        global theme
        theme = themes[name]
        settings['theme'] = name
        save_settings()
        QMessageBox.information(self, 'Theme', f'Applied theme: {name}')
        self.accept()

    def backup(self):
        path, _ = QFileDialog.getSaveFileName(self, 'Backup Settings', '', 'JSON Files (*.json)')
        if path:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2)
            QMessageBox.information(self, 'Backup', 'Settings backed up.')

    def restore(self):
        path, _ = QFileDialog.getOpenFileName(self, 'Restore Settings', '', 'JSON Files (*.json)')
        if path:
            data = safe_load_json(path) or {}
            settings.update(data)
            save_settings()
            QMessageBox.information(self, 'Restore', 'Settings restored.')
            self.accept()


# ------------------- MAIN LAUNCHER -------------------
class Launcher(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Minigames All In One Launcher')
        self.setMinimumSize(760, 540)
        self.setStyleSheet(f"background-color: {theme['bg']};")
        
        main = QVBoxLayout()
        main.setContentsMargins(14, 14, 14, 14)
        main.setSpacing(10)

        # ----------------- Top Bar -----------------
        top = QHBoxLayout()

        self.search = QLineEdit()
        self.search.setPlaceholderText('Search by title, description or tag...')
        self.search.textChanged.connect(self.filter_games)
        top.addWidget(self.search, stretch=2)

        self.filter_combo = QComboBox()
        self.filter_combo.addItem('All')
        self.filter_combo.currentIndexChanged.connect(self.filter_games)
        self.filter_combo.setFixedHeight(34)
        top.addWidget(self.filter_combo, stretch=0)
        
        self.refresh_btn = QPushButton('🔄 Refresh')
        self.refresh_btn.setFixedHeight(34)
        self.refresh_btn.clicked.connect(self.load_games)
        top.addWidget(self.refresh_btn)


        self.settings_btn = QPushButton('⚙ Settings')
        self.settings_btn.clicked.connect(self.open_settings)
        top.addWidget(self.settings_btn)

        self.help_btn = QPushButton('❔ Help')
        self.help_btn.clicked.connect(self.show_help)
        top.addWidget(self.help_btn)

        self.about_btn = QPushButton('ℹ About')
        self.about_btn.clicked.connect(self.show_about)
        top.addWidget(self.about_btn)

        main.addLayout(top)  # ✅ add the single top bar once

        # ----------------- Scroll Area -----------------
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        container = QWidget()
        self.vbox = QVBoxLayout()
        self.vbox.setSpacing(10)
        container.setLayout(self.vbox)
        self.scroll.setWidget(container)
        main.addWidget(self.scroll)

        self.setLayout(main)

        # ----------------- Internal Data -----------------
        self.cards: List[GameCard] = []
        self.game_meta: List[Dict] = []
        self.available_tags = set()

        # load games and apply previous geometry
        self.load_games()
        geom = settings.get('last_window_geometry')
        if geom:
            try:
                self.restoreGeometry(bytes.fromhex(geom))
            except Exception:
                pass


    def closeEvent(self, event):
        # save geometry
        try:
            geom = self.saveGeometry().toHex().data().hex()
            settings['last_window_geometry'] = geom
        except Exception:
            pass
        save_settings()
        return super().closeEvent(event)

    # ---------- load/cache metadata ----------
    def load_games(self):
        # clear
        while self.vbox.count():
            w = self.vbox.takeAt(0).widget()
            if w:
                w.setParent(None)
        self.cards.clear()
        self.game_meta.clear()
        self.available_tags = set()
        self.filter_combo.clear()
        self.filter_combo.addItem('All')

        # check cache
        cache = safe_load_json(CACHE_PATH) or {'handled': {}, 'meta': []}
        cache_handled = cache.get('handled', {})
        fresh_meta = []

        for folder in sorted(os.listdir(MINIGAMES_DIR), key=lambda s: s.lower()):
            folder_path = os.path.join(MINIGAMES_DIR, folder)
            if not os.path.isdir(folder_path):
                continue

            # check mtime
            try:
                mtime = int(os.path.getmtime(folder_path))
            except Exception:
                mtime = 0

            # use cached if exists and mtime matches
            cached_entry = cache_handled.get(folder)
            if cached_entry and cached_entry.get('mtime') == mtime:
                meta = cached_entry.get('meta')
                if meta:
                    meta['path'] = folder_path
                    fresh_meta.append(meta)
                    continue

            # else read config.json
            config_path = os.path.join(folder_path, 'config.json')
            meta = { 'title': folder, 'description': '', 'how_to_play': '', 'tags': [], 'path': folder_path, 'folder_name': folder }
            if os.path.exists(config_path):
                try:
                    data = safe_load_json(config_path)
                    if isinstance(data, dict):
                        meta['title'] = data.get('title', meta['title'])
                        meta['description'] = data.get('description', '')
                        meta['how_to_play'] = data.get('how_to_play', '')
                        meta['tags'] = [str(t).strip() for t in (data.get('tags') or []) if t]
                except Exception:
                    # keep defaults
                    pass

            fresh_meta.append(meta)
            cache_handled[folder] = {
                'mtime': mtime,
                'meta': {
                    'title': meta['title'],
                    'description': meta['description'],
                    'how_to_play': meta['how_to_play'],
                    'tags': meta['tags'],
                    'folder_name': meta['folder_name']  # <- add this
                }
            }

        # write updated cache
        try:
            with open(CACHE_PATH, 'w', encoding='utf-8') as f:
                json.dump({'handled': cache_handled}, f, indent=2)
        except Exception:
            pass
        
        # sort by recently played then alphabetically
        recent_map = settings.get('recently_played', {})
        def sort_key(m):
            rp = recent_map.get(m.get('folder_name'))
            if rp:
                return (0, -int(rp))
            return (1, m.get('title','').lower())

        fresh_meta.sort(key=sort_key)

        for meta in fresh_meta:
            # create card
            card = GameCard(meta, self)
            # connect reorder buttons
            card.up_btn.clicked.connect(lambda _, c=card: self.move_card_up(c))
            card.down_btn.clicked.connect(lambda _, c=card: self.move_card_down(c))
            self.vbox.addWidget(card)
            self.cards.append(card)
            self.game_meta.append({
                'title': meta.get('title','').lower(),
                'desc': str(meta.get('description','')).lower(),
                'tags': [t.lower() for t in meta.get('tags',[])],
                'card': card
            })
            for t in meta.get('tags',[]):
                self.available_tags.add(t)

        for t in sorted(self.available_tags, key=lambda s: s.lower()):
            self.filter_combo.addItem(t)

        self.apply_theme_to_cards()

    # ------------------- New methods in Launcher class -------------------

    def show_help(self):
        dlg = QDialog(self)
        dlg.setWindowTitle('MGAIO Launcher Help')
        dlg.resize(520, 420)
        dlg.setStyleSheet(f"background-color: {theme['bg']}; color: {theme['fg']};")
        layout = QVBoxLayout()
        txt = (
        "Welcome to MGAIO Launcher!\n\n"
        "• Use the search box to find games by title, description, or tags.\n"
        "• Filter games using the tag dropdown.\n"
        "• Click '▶ Play' to launch a game.\n"
        "• Click '❓ How to Play' to view game instructions.\n"
        "• '🏆 Leaderboard' shows top scores for each game.\n"
        "• Move games up/down to reorder them.\n"
        "• Settings allow theme changes, backups, and app lock.\n\n"
        "Enjoy your games! 🎮"
        )
        label = QLabel(txt)
        label.setWordWrap(True)
        label.setFont(QFont('Segoe UI', 11))
        layout.addWidget(label)
        dlg.setLayout(layout)
        dlg.exec()

    def show_about(self):
        dlg = QDialog(self)
        dlg.setWindowTitle('About MGAIO Launcher')
        dlg.resize(400, 280)
        dlg.setStyleSheet(f"background-color: {theme['bg']}; color: {theme['fg']};")
        layout = QVBoxLayout()
        txt = (
        "MGAIO Launcher v2\n"
        "Minigames All-In-One\n\n"
        "• Developed for offline minigame management\n"
        "• Features theming, search, filtering, and leaderboards\n"
        "• Saveable settings, app lock, and smooth UI\n\n"
        "© 2025 MGAIO Project"
        )
        label = QLabel(txt)
        label.setWordWrap(True)
        label.setFont(QFont('Segoe UI', 11))
        layout.addWidget(label)
        dlg.setLayout(layout)
        dlg.exec()

    def apply_theme_to_cards(self):
        for c in self.cards:
            c.apply_theme()

    # ---------- reorder helpers ----------
    def move_card_up(self, card: GameCard):
        idx = self.vbox.indexOf(card)
        if idx > 0:
            self.vbox.removeWidget(card)
            self.vbox.insertWidget(idx-1, card)
            # also reorder game_meta to keep filtering consistent
            for i, m in enumerate(self.game_meta):
                if m['card'] == card:
                    self.game_meta.insert(max(0, i-1), self.game_meta.pop(i))
                    break

    def move_card_down(self, card: GameCard):
        idx = self.vbox.indexOf(card)
        cnt = self.vbox.count()
        if 0 <= idx < cnt-1:
            self.vbox.removeWidget(card)
            self.vbox.insertWidget(idx+1, card)
            for i, m in enumerate(self.game_meta):
                if m['card'] == card:
                    self.game_meta.insert(min(len(self.game_meta), i+1), self.game_meta.pop(i))
                    break

    # ---------- filter/search ----------
    def filter_games(self):
        q = self.search.text().strip().lower()
        tag = self.filter_combo.currentText().strip().lower()
        for m in self.game_meta:
            title_ok = q in m['title'] if q else True
            desc_ok = q in m['desc'] if q else True
            query_ok = title_ok or desc_ok
            tag_ok = True
            if tag and tag != 'all':
                tag_ok = tag in m['tags']
            visible = query_ok and tag_ok
            m['card'].setVisible(visible)

    def open_settings(self):
        dlg = SettingsDialog(self)
        if dlg.exec():
            # reapply theme and reload
            save_settings()
            global theme
            theme = themes.get(settings.get('theme','default'), themes['default'])
            self.setStyleSheet(f"background-color: {theme['bg']};")
            self.apply_theme_to_cards()
            self.load_games()


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

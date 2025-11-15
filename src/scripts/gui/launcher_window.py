# scripts/gui/launcher_window.py
"""
The main application window (Launcher) responsible for structure,
game display/filtering, and interaction with other components/dialogs.
"""

import os
import sys
import json
import random
import traceback
from typing import List, Dict

# PySide6 imports
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea, QMenuBar,
    QComboBox, QLineEdit, QAction, QMessageBox, QDialog
)
from PySide6.QtGui import QIcon, QFont
from PySide6.QtCore import Qt

# Project imports
from ..managers.settings_manager import settings, save_settings, get_current_theme
from ..utils.constants import LAUNCHER_VERSION, MINIGAMES_DIR, CACHE_PATH
from ..utils.file_io import safe_load_json, load_recently_played
from .components import GameCard
from .dialogs import SettingsDialog, AchievementsDialog


class Launcher(QWidget):
    def __init__(self):
        super().__init__()

        print("Step 0: Starting Launcher init")

        # --- Basic Setup ---
        try:
            self.setWindowIcon(QIcon(self.resource_path("data/icon.ico")))
            self.setWindowTitle("Minigames All In One Launcher")
            self.setMinimumSize(760, 540)
            print("Minigames loaded from:", MINIGAMES_DIR)
        except Exception as e:
            print("Error setting window properties:", e)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(14, 14, 14, 14)
        main_layout.setSpacing(10)

        # --- UI Initialization ---
        self._init_top_bar(main_layout)
        self._init_scroll_area(main_layout)

        self.setLayout(main_layout)

        # --- State Variables ---
        self.cards: List[GameCard] = []
        self.game_meta: List[Dict] = []
        self.available_tags = set()
        self._easter_code = [Qt.Key_Up, Qt.Key_Up, Qt.Key_Down, Qt.Key_Down,
                             Qt.Key_Left, Qt.Key_Right, Qt.Key_Left, Qt.Key_Right,
                             Qt.Key_B, Qt.Key_A]
        self._current_code = []

        # --- Final Steps ---
        self.load_games()
        self._restore_geometry()
        self.apply_current_theme()
        self._run_startup_script()

        print("Launcher init finished successfully ✅")

    def _run_startup_script(self):
        script_path = settings.get("startup_script")
        if script_path and os.path.exists(script_path):
            try:
                import importlib.util
                spec = importlib.util.spec_from_file_location("custom_script", script_path)
                module = importlib.util.module_from_spec(spec)
                sys.modules["custom_script"] = module
                spec.loader.exec_module(module)
                print(f"Executed custom startup script: {os.path.basename(script_path)}")
            except Exception as e:
                print(f"Failed to run custom startup script: {e}")
                traceback.print_exc()
                
    @staticmethod
    def resource_path(relative_path):
        """Get absolute path to resource, works for dev and PyInstaller."""
        if hasattr(sys, "_MEIPASS"):
            return os.path.join(sys._MEIPASS, relative_path)
        return os.path.join(os.path.abspath(os.path.dirname(__file__)), "..", "..", relative_path)

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

    def _init_top_bar(self, parent_layout):
        menu_bar = QMenuBar()

        file_menu = menu_bar.addMenu("File")
        refresh_action = QAction("Refresh 🔄", self)
        refresh_action.triggered.connect(self.load_games)
        file_menu.addAction(refresh_action)

        stats_action = QAction("Stats 📊", self)
        stats_action.triggered.connect(self.open_stats)
        file_menu.addAction(stats_action)

        settings_menu = menu_bar.addMenu("Settings")
        settings_action = QAction("Open Settings ⚙", self)
        settings_action.triggered.connect(self.open_settings)
        settings_menu.addAction(settings_action)

        help_menu = menu_bar.addMenu("Help")
        help_action = QAction("Help ❔", self)
        help_action.triggered.connect(self.show_help)
        help_menu.addAction(help_action)

        about_action = QAction("About ℹ", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

        achievements_action = QAction("Achievements 🏆", self)
        achievements_action.triggered.connect(self.open_achievements)
        help_menu.addAction(achievements_action)

        parent_layout.addWidget(menu_bar)

        top_row = QHBoxLayout()

        self.filter_combo = QComboBox()
        self.filter_combo.addItem("All")
        self.filter_combo.currentIndexChanged.connect(self.filter_games)
        top_row.addWidget(self.filter_combo, stretch=0)

        self.search = QLineEdit()
        self.search.setPlaceholderText("Search...")
        self.search.textChanged.connect(self.filter_games)
        top_row.addWidget(self.search, stretch=2)

        parent_layout.addLayout(top_row)

    def _init_scroll_area(self, parent_layout):
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        container = QWidget()
        self.vbox = QVBoxLayout(container)
        self.vbox.setSpacing(10)
        self.scroll.setWidget(container)
        parent_layout.addWidget(self.scroll)

    def validate_cache(self):
        cache = safe_load_json(CACHE_PATH) or {'handled': {}, 'meta': []}
        valid_folders = set(os.listdir(MINIGAMES_DIR))
        removed = []
        for folder in list(cache['handled'].keys()):
            if folder not in valid_folders:
                del cache['handled'][folder]
                removed.append(folder)
        if removed:
            try:
                with open(CACHE_PATH, 'w', encoding='utf-8') as f:
                    json.dump(cache, f, indent=2)
            except Exception as e:
                print(f"Error saving updated cache: {e}")
        return removed

    def load_games(self):
        self._clear_cards()

        self.validate_cache()
        cache = safe_load_json(CACHE_PATH) or {'handled': {}, 'meta': []}
        cache_handled = cache.get('handled', {})
        fresh_meta: List[Dict] = []

        for folder in sorted(os.listdir(MINIGAMES_DIR), key=str.lower):
            folder_path = os.path.join(MINIGAMES_DIR, folder)
            if not os.path.isdir(folder_path):
                continue
            meta = self._load_game_meta(folder, folder_path, cache_handled)
            meta['favorite'] = folder in settings.get('favorites', [])
            fresh_meta.append(meta)

        try:
            with open(CACHE_PATH, 'w', encoding='utf-8') as f:
                json.dump({'handled': cache_handled}, f, indent=2)
        except Exception:
            pass
            
        if settings.get("favorites_only", False):
            fresh_meta = [m for m in fresh_meta if m.get('favorite', False)]

        recently_played = load_recently_played()
        
        # Sorting
        sort_key = settings.get("auto_sort", "Alphabetical")
        if sort_key == "Recently Played":
            fresh_meta.sort(key=lambda m: recently_played.get(m.get('folder_name', ''), 0), reverse=True)
        elif sort_key == "Favorites":
            fresh_meta.sort(key=lambda m: (0 if m.get('favorite') else 1, m.get('title', '').lower()))
        else:
            fresh_meta.sort(key=lambda m: m.get('title', '').lower())

        self._populate_cards(fresh_meta, recently_played)
        self.filter_games()

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
                meta['rating'] = settings.get('game_metadata', {}).get(folder, {}).get('rating', 0)
                return meta

        meta = {
            'title': folder, 'description': '', 'how_to_play': '', 'tags': [],
            'path': folder_path, 'folder_name': folder, 'author': 'Unknown',
            'version': '1.0.0', 'release_date': 'Unknown', 'entry': 'main.py'
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
                    meta['entry'] = data.get('entry', 'main.py')

            except Exception:
                pass

        cache_handled[folder] = {'mtime': mtime, 'meta': {k: v for k, v in meta.items() if k not in ('path', 'favorite', 'rating')}}
        meta['rating'] = settings.get('game_metadata', {}).get(folder, {}).get('rating', 0)
        return meta

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

    def _populate_cards(self, fresh_meta: List[Dict], recently_played: dict):
        self.available_tags = set()
        self.filter_combo.clear()
        self.filter_combo.addItem('All')
        while self.vbox.count():
            w = self.vbox.takeAt(0).widget()
            if w:
                w.setParent(None)

        recently_played_meta = []
        recommended_meta = []
        for meta in fresh_meta:
            if meta['folder_name'] in recently_played:
                recently_played_meta.append(meta)
            else:
                recommended_meta.append(meta)
                
        if recently_played_meta:
            rp_label = QLabel("Recently Played")
            rp_label.setFont(QFont("Segoe UI", 12, QFont.Bold))
            self.vbox.addWidget(rp_label)

            for meta in recently_played_meta:
                card = GameCard(meta, self)
                self._connect_card_buttons(card)
                self.vbox.addWidget(card)
                self._register_card_meta(card, meta)

        if recommended_meta:
            rec_label = QLabel("Recommended")
            rec_label.setFont(QFont("Segoe UI", 12, QFont.Bold))
            self.vbox.addWidget(rec_label)

            random.shuffle(recommended_meta)
            for meta in recommended_meta:
                    card = GameCard(meta, self)
                    self._connect_card_buttons(card)
                    self.vbox.addWidget(card)
                    self._register_card_meta(card, meta)

        if not fresh_meta:
            empty_label = QLabel("Games are not found!")
            empty_label.setFont(QFont("Segoe UI", 14, QFont.Bold))
            empty_label.setStyleSheet("color: red;")
            empty_label.setAlignment(Qt.AlignCenter)
            self.vbox.addWidget(empty_label)

        for t in sorted(self.available_tags, key=str.lower):
            self.filter_combo.addItem(t)

        self.apply_theme_to_cards()

    def _connect_card_buttons(self, card: GameCard):
        card.up_btn.clicked.connect(lambda _, c=card: self.move_card_up(c))
        card.down_btn.clicked.connect(lambda _, c=card: self.move_card_down(c))

    def _register_card_meta(self, card: GameCard, meta: Dict):
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
        current_theme_data = get_current_theme()
        qss_path = self.resource_path(current_theme_data.get('qss', 'data/themes/default.qss'))

        try:
            with open(qss_path, 'r', encoding='utf-8') as f:
                self.setStyleSheet(f.read())
        except Exception:
            self.setStyleSheet(f"background-color: {current_theme_data.get('bg', '#2B2B2B')}; color: {current_theme_data.get('fg', '#FFFFFF')};")

        self.apply_theme_to_cards()
        
    def apply_theme_to_cards(self):
        for c in self.cards:
            c.apply_theme()

    def move_card_up(self, card: GameCard):
        idx = self.vbox.indexOf(card)
        if idx > 0:
            self.vbox.removeWidget(card)
            self.vbox.insertWidget(idx - 1, card)

    def move_card_down(self, card: GameCard):
        idx = self.vbox.indexOf(card)
        if idx < self.vbox.count() - 1:
            self.vbox.removeWidget(card)
            self.vbox.insertWidget(idx + 1, card)

    def filter_games(self):
        query = self.search.text().strip().lower()
        selected_tag = self.filter_combo.currentText().strip().lower()
        favorites_only = settings.get('favorites_only', False)

        if query and query not in settings.get('search_history', []):
            history = settings.setdefault('search_history', [])
            history.insert(0, query)
            settings['search_history'] = history[:5]
            save_settings()

        for meta in self.game_meta:
            title_match = query in meta['title'] if query else True
            desc_match = query in meta['desc'] if query else True
            tag_match = (selected_tag in meta['tags']) if selected_tag and selected_tag != 'all' else True
            fav_match = (not favorites_only) or meta['favorite']

            meta['card'].setVisible((title_match or desc_match) and tag_match and fav_match)

    def open_stats(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("📊 Player Stats")
        dlg.setStyleSheet(f"background-color: {get_current_theme()['bg']}; color: {get_current_theme()['fg']};")
        layout = QVBoxLayout()
        
        total_hours = "N/A"
        total_games_played = len(settings.get('play_counts', {}))
        achievements_unlocked = len(settings.get('achievements', {}))
        total_coins = settings.get('coins', 0)

        layout.addWidget(QLabel(f"Total Coins: {total_coins}"))
        layout.addWidget(QLabel(f"Total Games Played (once or more): {total_games_played}"))
        layout.addWidget(QLabel(f"Achievements Unlocked: {achievements_unlocked}"))
        layout.addWidget(QLabel(f"Total Hours Played: {total_hours} (Feature not implemented)"))

        dlg.setLayout(layout)
        dlg.exec()

    def show_help(self):
        self._show_dialog("MGAIO Launcher Help",
            "Welcome to MGAIO Launcher!\n\n"
            "• Use the search box to find games by title, description, or tags.\n"
            "• Filter games using the tag dropdown.\n"
            "• Click '▶ Play' to launch a game.\n"
            "• Click '❓ How to Play' to view game instructions.\n"
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
        current_theme_data = get_current_theme()
        dlg.setStyleSheet(f"background-color: {current_theme_data.get('bg', '#FFFFFF')}; color: {current_theme_data.get('fg', '#222222')};")
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
            self.apply_current_theme()

    def open_achievements(self):
        if not settings.get('achievements_panel', True):
            QMessageBox.information(self, 'Achievements', 'Achievements panel is disabled in settings.')
            return
        dlg = AchievementsDialog(self)
        dlg.exec()
        
    def keyPressEvent(self, event):
        super().keyPressEvent(event)
        
        key_map = settings.get('hotkeys', {})
        folder = key_map.get(event.text())
        if folder:
            card = next((c['card'] for c in self.game_meta if c['folder_name'] == folder), None)
            if card:
                card.launch_game()
        
        if settings.get("easter_eggs", True):
            if event.key() == self._easter_code[len(self._current_code)]:
                self._current_code.append(event.key())
                if len(self._current_code) == len(self._easter_code):
                    self.trigger_easter_egg()
                    self._current_code = []
            elif event.key() == self._easter_code[0]:
                self._current_code = [event.key()]
            else:
                self._current_code = []

    def trigger_easter_egg(self):
        secret_meta = next((m for m in self.game_meta if m['folder_name'] == "secret_game"), None)
        
        if secret_meta:
            is_visible = any(m['card'].isVisible() and m['folder_name'] == "secret_game" for m in self.game_meta)
            
            if not is_visible:
                # To insert a new card, we need its meta. Since `secret_meta` is from `game_meta` dict:
                secret_card_meta = secret_meta['card'].meta # Use existing card's full meta
                card = GameCard(secret_card_meta, self)
                self.vbox.insertWidget(0, QLabel("🎉 SECRET GAME UNLOCKED! 🎉"))
                self.vbox.insertWidget(1, card)
                self._register_card_meta(card, secret_card_meta)
                QMessageBox.information(self, "🎉 Secret Unlocked!", "You unlocked a hidden game! 🕹️")
            else:
                QMessageBox.information(self, "Easter Egg", "Secret game already visible! 🥳")
        else:
             QMessageBox.information(self, "Easter Egg", "Konami code entered! But no secret game found. 😢")
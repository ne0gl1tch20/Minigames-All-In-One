# scripts/gui/launcher_windowMobile.py
"""
The main application window (Launcher) responsible for structure,
game display/filtering, and interaction with other components/dialogs.

REDESIGNED FOR MOBILE LAYOUT.
"""

import os
import sys
import json
import random
import traceback
from typing import List, Dict

# PySide6 imports
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea,
    QComboBox, QLineEdit, QMessageBox, QDialog, QPushButton, QToolButton, QSizePolicy
)
from PySide6.QtGui import QIcon, QFont, QAction
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

        # --- Basic Setup (Mobile Optimization) ---
        try:
            self.setWindowIcon(QIcon(self.resource_path("data/icon.ico")))
            self.setWindowTitle("Minigames All In One Launcher")
            # Set a fixed size for mobile simulation (9:16 aspect ratio)
            self.setFixedSize(400, 720) 
            print("Minigames loaded from:", MINIGAMES_DIR)
        except Exception as e:
            print("Error setting window properties:", e)

        # Main Layout (Column structure: Header -> Search/Filter -> Scroll Area -> Bottom Nav)
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0) # Use internal component margins
        main_layout.setSpacing(0)

        # --- UI Initialization (Mobile-style components) ---
        self._init_header(main_layout)
        self._init_search_filter(main_layout)
        self._init_scroll_area(main_layout)
        self._init_bottom_nav(main_layout)

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
        # Removed _restore_geometry as it interferes with fixed mobile size
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
        # Disabled for mobile layout
        pass

    def closeEvent(self, event):
        try:
            geom = self.saveGeometry().toHex().data().hex()
            settings['last_window_geometry'] = geom
        except Exception:
            pass
        save_settings()
        return super().closeEvent(event)

    def _init_header(self, parent_layout):
        """Initializes the mobile-style top header bar (Title and Actions)."""
        header_widget = QWidget()
        header_widget.setObjectName("HeaderContainer")
        header = QHBoxLayout(header_widget)
        header.setContentsMargins(15, 15, 15, 5)
        
        # Title/Logo
        title_label = QLabel("MGAIO Launcher")
        title_label.setObjectName("HeaderTitle")
        # Font will be scaled via QSS, but set a high-level one for fallbacks
        header.addWidget(title_label)
        
        header.addStretch()

        # Refresh button
        self.refresh_btn = QPushButton("🔄")
        self.refresh_btn.setObjectName("HeaderButton")
        self.refresh_btn.clicked.connect(self.load_games)
        header.addWidget(self.refresh_btn)
        
        # Help/About (using one button to show all extra dialogs)
        self.help_btn = QPushButton("❓")
        self.help_btn.setObjectName("HeaderButton")
        self.help_btn.clicked.connect(self.show_help)
        header.addWidget(self.help_btn)

        parent_layout.addWidget(header_widget)

    def _init_search_filter(self, parent_layout):
        """Initializes the search bar and filter dropdown."""
        top_row = QHBoxLayout()
        top_row.setContentsMargins(15, 5, 15, 15) # Clean spacing
        
        # Search Bar
        self.search = QLineEdit()
        self.search.setPlaceholderText("🔍 Search by title, tag, or desc...")
        self.search.setObjectName("SearchInput")
        self.search.textChanged.connect(self.filter_games)
        top_row.addWidget(self.search, stretch=2)

        # Filter Dropdown
        self.filter_combo = QComboBox()
        self.filter_combo.addItem("All")
        self.filter_combo.setObjectName("FilterDropdown")
        self.filter_combo.currentIndexChanged.connect(self.filter_games)
        top_row.addWidget(self.filter_combo, stretch=1)
        
        parent_layout.addLayout(top_row)

    def _init_scroll_area(self, parent_layout):
        """Initializes the mobile-optimized scrollable game list."""
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setObjectName("GameScrollArea")
        
        container = QWidget()
        self.vbox = QVBoxLayout(container)
        self.vbox.setSpacing(15) # Increased spacing for mobile scrolling
        self.vbox.setContentsMargins(15, 0, 15, 15) # Horizontal padding
        self.vbox.setAlignment(Qt.AlignmentFlag.AlignTop) # Stick content to the top
        self.scroll.setWidget(container)
        
        parent_layout.addWidget(self.scroll)

    def _init_bottom_nav(self, parent_layout):
        """Initializes the mobile-style bottom navigation bar."""
        nav_bar = QWidget()
        nav_bar.setObjectName("BottomNav")
        nav_layout = QHBoxLayout(nav_bar)
        nav_layout.setContentsMargins(0, 0, 0, 0)
        nav_layout.setSpacing(0)
        
        def create_nav_btn(text, icon_char, slot):
            btn = QToolButton()
            btn.setText(f"{icon_char}\n{text}")
            btn.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
            btn.setObjectName("NavButton")
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            btn.clicked.connect(slot)
            return btn

        # Navigation Buttons (replaces most QMenuBar items)
        nav_layout.addWidget(create_nav_btn("Home", "🏠", lambda: self.search.setText("")))
        nav_layout.addWidget(create_nav_btn("Stats", "📊", self.open_stats))
        nav_layout.addWidget(create_nav_btn("Achievements", "🏆", self.open_achievements))
        nav_layout.addWidget(create_nav_btn("Settings", "⚙", self.open_settings))

        parent_layout.addWidget(nav_bar)

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
        
        # Clear existing widgets efficiently
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
                
        # --- Mobile Section Headers ---
        if recently_played_meta:
            rp_label = QLabel("Recently Played")
            rp_label.setObjectName("SectionHeader")
            self.vbox.addWidget(rp_label)

            for meta in recently_played_meta:
                card = GameCard(meta, self)
                # Ensure the card is a good size for touch
                card.setFixedHeight(260)
                self._connect_card_buttons(card)
                self.vbox.addWidget(card)
                self._register_card_meta(card, meta)

        if recommended_meta:
            rec_label = QLabel("Recommended")
            rec_label.setObjectName("SectionHeader")
            self.vbox.addWidget(rec_label)

            random.shuffle(recommended_meta)
            for meta in recommended_meta:
                    card = GameCard(meta, self)
                    card.setFixedHeight(260)
                    self._connect_card_buttons(card)
                    self.vbox.addWidget(card)
                    self._register_card_meta(card, meta)

        if not fresh_meta:
            empty_label = QLabel("Games are not found!")
            empty_label.setFont(QFont("Segoe UI", 16, QFont.Bold))
            empty_label.setStyleSheet("color: red;")
            empty_label.setAlignment(Qt.AlignCenter)
            self.vbox.addWidget(empty_label)

        for t in sorted(self.available_tags, key=str.lower):
            self.filter_combo.addItem(t)

        self.apply_theme_to_cards()

    def _connect_card_buttons(self, card: GameCard):
        # Move buttons are for desktop organization, usually omitted on mobile, but kept for full functionality
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

        mobile_qss = f"""
        /* ---------------------------------------------------- */
        /* --- MOBILE LAYOUT OVERRIDES (Rounded, Large Touch) --- */
        /* ---------------------------------------------------- */
        
        /* Global Font Scaling */
        * {{
            font-size: 13pt; /* Base font size for mobile */
        }}

        /* Header Styling */
        #HeaderContainer {{
            background-color: {current_theme_data.get('bg', '#2B2B2B')};
            border-bottom: 1px solid #444444;
        }}
        #HeaderTitle {{
            font-size: 20pt;
            font-weight: bold;
            color: {current_theme_data.get('fg', '#FFFFFF')};
        }}
        
        /* Section Header (Recently Played/Recommended) */
        #SectionHeader {{
            font-size: 16pt;
            font-weight: bold;
            padding: 10px 0 5px 0;
            color: {current_theme_data.get('fg', '#FFFFFF')};
        }}

        /* Search & Filter Styling */
        #SearchInput, #FilterDropdown {{
            padding: 12px 10px; /* Bigger touch target */
            border-radius: 12px;
            border: 2px solid #555555;
            min-height: 48px;
            font-size: 14pt;
        }}
        
        /* General Buttons (Header) */
        QPushButton#HeaderButton {{
            min-height: 48px;
            min-width: 48px;
            border-radius: 12px;
            background-color: #555555;
            color: #FFFFFF;
            font-size: 18pt;
            border: none;
        }}
        
        /* Bottom Navigation Bar */
        #BottomNav {{
            background-color: #1E1E1E;
            border-top: 1px solid #333333;
            min-height: 60px; /* Large touch zone */
        }}
        #BottomNav QToolButton {{
            border: none;
            color: #AAAAAA; 
            font-size: 12pt;
            padding: 8px 0;
            margin: 0;
        }}
        #BottomNav QToolButton:hover, #BottomNav QToolButton:pressed {{
            color: #00A9FF; /* Active/Highlight color */
        }}
        
        /* Scroll Area */
        QScrollArea#GameScrollArea {{
            border: none;
        }}
        
        /* GameCard (assuming GameCard is a QWidget) */
        GameCard {{
            background-color: #3C3C3C;
            border-radius: 15px; 
            padding: 15px;
            min-height: 260px; /* Enforced touch-friendly height */
        }}
        """

        try:
            with open(qss_path, 'r', encoding='utf-8') as f:
                base_qss = f.read()
            self.setStyleSheet(base_qss + mobile_qss)
        except Exception:
            # Fallback + Mobile QSS
            self.setStyleSheet(f"background-color: {current_theme_data.get('bg', '#2B2B2B')}; color: {current_theme_data.get('fg', '#FFFFFF')};" + mobile_qss)

        self.apply_theme_to_cards()
        
    def apply_theme_to_cards(self):
        for c in self.cards:
            c.apply_theme()

    # (move_card_up/down methods remain unchanged)
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

    # (open_stats, show_help, show_about, _show_dialog methods remain unchanged, 
    # but their appearance will be governed by the QSS and base font scaling.)
    def open_stats(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("📊 Player Stats")
        # Added explicit size for mobile dialog consistency
        dlg.resize(380, 500) 
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
            "• Settings (bottom bar) allow theme changes, backups, and app lock.\n\n"
            "Enjoy your games! 🎮", 380, 420
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
            380, 280
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
        # Use a consistent font size that is scaled by QSS
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
        
    # (keyPressEvent and trigger_easter_egg methods remain unchanged)
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
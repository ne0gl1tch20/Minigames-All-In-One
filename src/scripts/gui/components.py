# scripts/gui/components.py
"""
Contains reusable GUI components, primarily the GameCard widget.
"""

import os
import sys
import time
import subprocess
from typing import Dict

# PySide6 imports
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFrame,
    QSizePolicy, QMessageBox, QDialog, QGraphicsDropShadowEffect, QSizePolicy
)
from PySide6.QtGui import QPixmap, QFont, QColor
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve

# Project imports
from ..managers.settings_manager import settings, save_settings, theme
from ..utils.file_io import load_recently_played, save_recently_played
from ..core.achievements import check_unlock_achievement


class GameCard(QFrame):
    """Represents a single minigame card with launch, instructions, reorder buttons, favorite toggle."""

    def __init__(self, meta: Dict, parent=None):
        super().__init__(parent)
        self.meta = meta
        self.rating = meta.get('rating', 0)
        self.play_streak = meta.get('streak', 0)
        self.achievements = meta.get('achievements', [])
        self.setObjectName('game_card')
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.setMinimumHeight(120)

        shadow = QGraphicsDropShadowEffect(blurRadius=18, xOffset=0, yOffset=6)
        shadow.setColor(QColor(0, 0, 0, 160))
        self.setGraphicsEffect(shadow)

        self._build_ui()
        self.apply_theme()

        self.anim = QPropertyAnimation(self, b'geometry')
        self.anim.setDuration(180)
        self.anim.setEasingCurve(QEasingCurve.OutCubic)

        self.current_view = settings.get("view_mode", "List")
        
        self._add_gameplay_widgets()
        self.update_layout_view(self.current_view)
        
        # Prevent vertical shrinking
        self.setMinimumHeight(100)  # tweak as needed
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    def _build_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(6)

        top_layout = QHBoxLayout()
        top_layout.setSpacing(12)
        top_layout.setContentsMargins(0, 0, 0, 0)

        self._add_icon(top_layout)
        self._add_text_column(top_layout)
        self._add_buttons_column(top_layout)

        layout.addLayout(top_layout)
        self._add_meta_info(layout)
        self._add_tags(layout)

        self.setLayout(layout)

    def _add_gameplay_widgets(self):
        self.gameplay_layout = QHBoxLayout()
        self.gameplay_layout.setSpacing(8)
        self.gameplay_layout.setContentsMargins(0, 0, 0, 0)

        self.star_labels = []
        for i in range(5):
            lbl = QLabel("☆")
            lbl.setFont(QFont('Segoe UI', 12))
            lbl.setStyleSheet("color: gold;")
            # Mouse event setup
            def create_mouse_handler(idx):
                def handler(event):
                    if event.button() == Qt.LeftButton:
                        self.set_rating(idx + 1)
                return handler
            lbl.mousePressEvent = create_mouse_handler(i)
            self.star_labels.append(lbl)
            self.gameplay_layout.addWidget(lbl)

        self.streak_label = QLabel(f"🔥 {self.play_streak} day streak!")
        self.streak_label.setFont(QFont("Segoe UI", 9))
        self.streak_label.setStyleSheet("color: orange;")
        self.gameplay_layout.addWidget(self.streak_label)

        self.layout().addLayout(self.gameplay_layout)
        self._update_star_display()

    def _update_star_display(self):
        for i, lbl in enumerate(self.star_labels):
            lbl.setText("★" if i < self.rating else "☆")

    def set_rating(self, stars: int):
        self.rating = stars
        # The rating needs to be saved to settings (game_metadata key not in original, assume it's saved somewhere)
        # We'll save to meta for now and rely on launcher to pull this if needed
        self.meta['rating'] = stars 
        self._update_star_display()
        save_settings()
        # The original code had 'rated_a_game' which is not in ACHIEVEMENTS_DEF, so we'll skip the check for now
        # check_unlock_achievement('rated_a_game')

    def update_layout_view(self, view_mode: str):
        compact = settings.get("compact_mode", False)
        if view_mode == "Grid":
            self.setFixedHeight(180 if not compact else 100)
            self.desc_label.setVisible(not compact)
            self.howto_btn.setVisible(not compact)
            self.title_label.setAlignment(Qt.AlignCenter)
        else:  # List view
            self.setFixedHeight(220 if not compact else 140)
            self.desc_label.setVisible(True)
            self.howto_btn.setVisible(True)
            self.title_label.setAlignment(Qt.AlignLeft)

        # Fix button column width
        if hasattr(self, "btn_container"):
            self.btn_container.setFixedWidth(140)
            self.btn_container.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Minimum)

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
        parent_layout.addWidget(self.icon_label, 0, Qt.AlignVCenter)

    def _add_text_column(self, parent_layout):
        text_layout = QVBoxLayout()
        text_layout.setSpacing(4)
        text_layout.setContentsMargins(0, 0, 0, 0)

        self.title_label = QLabel(self.meta.get('title', 'Unknown'))
        self.title_label.setFont(QFont('Segoe UI', 13, QFont.Bold))
        self.title_label.setWordWrap(False)
        self.title_label.setAlignment(Qt.AlignLeft)
        text_layout.addWidget(self.title_label, 0, Qt.AlignVCenter)

        self.desc_label = QLabel(self.meta.get('description', ''))
        self.desc_label.setFont(QFont('Segoe UI', 10))
        self.desc_label.setWordWrap(True)
        self.desc_label.setMaximumHeight(38)
        self.desc_label.setAlignment(Qt.AlignVCenter)
        text_layout.addWidget(self.desc_label, 0, Qt.AlignVCenter)

        parent_layout.addLayout(text_layout, stretch=1)

    def update_ui(self):
        self.apply_theme()

        folder = self.meta.get("folder_name")
        if settings.get("favorites_only", False) and folder not in settings.get("favorites", []):
            self.hide()
        else:
            self.show()

        compact = settings.get("compact_mode", False)
        # NEW: unified fixed height based on compact mode
        self.setFixedHeight(140 if not settings.get("compact_mode", False) else 100)
        self.desc_label.setVisible(not settings.get("compact_mode", False))
        self.howto_btn.setVisible(not settings.get("compact_mode", False))


    def _add_meta_info(self, parent_layout):
        author = self.meta.get("author", "—")
        version = self.meta.get("version", "1.0.0")
        release_date = self.meta.get("release_date", "—")

        info_label = QLabel(f"👤 {author}  •  🕓 {release_date}  •  🧩 v{version}")
        info_label.setFont(QFont("Segoe UI", 9))
        info_label.setStyleSheet("color: gray;")
        parent_layout.addWidget(info_label)

    def _add_buttons_column(self, parent_layout):
        self.btn_container = QWidget()
        btn_layout = QVBoxLayout(self.btn_container)
        btn_layout.setSpacing(8)
        btn_layout.setContentsMargins(0, 0, 0, 0)
        btn_layout.setAlignment(Qt.AlignTop)

        self.play_btn = QPushButton('▶ Play')
        self.play_btn.setObjectName("play_btn")
        self.play_btn.setFixedHeight(30)
        self.play_btn.setFixedWidth(120)
        self.play_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.play_btn.clicked.connect(self.launch_game)
        btn_layout.addWidget(self.play_btn, 0, Qt.AlignTop)

        self.howto_btn = QPushButton('❓ How to Play')
        self.howto_btn.setObjectName("howto_btn")
        self.howto_btn.setFixedHeight(30)
        self.howto_btn.setFixedWidth(120)
        self.howto_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.howto_btn.clicked.connect(self.show_howto)
        btn_layout.addWidget(self.howto_btn, 0, Qt.AlignTop)

        self.favorite_btn = QPushButton('⭐ Favorite')
        self.favorite_btn.setObjectName("favorite_btn")
        self.favorite_btn.setCheckable(True)
        folder_name = self.meta.get('folder_name')
        fav_list = settings.get('favorites', [])
        self.favorite_btn.setChecked(folder_name in fav_list)
        self.favorite_btn.clicked.connect(self.toggle_favorite)
        self.favorite_btn.setFixedHeight(30)
        self.favorite_btn.setFixedWidth(120)
        self.favorite_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        btn_layout.addWidget(self.favorite_btn, 0, Qt.AlignTop)

        reorder_widget = QWidget()
        reorder_layout = QHBoxLayout(reorder_widget)
        reorder_layout.setContentsMargins(0, 0, 0, 0)
        reorder_layout.setSpacing(6)
        self.up_btn = QPushButton('▲')
        self.up_btn.setFixedSize(30, 28)
        self.down_btn = QPushButton('▼')
        self.down_btn.setFixedSize(30, 28)
        reorder_layout.addWidget(self.up_btn)
        reorder_layout.addWidget(self.down_btn)
        btn_layout.addWidget(reorder_widget, 0, Qt.AlignTop)

        self.btn_container.setFixedWidth(140)
        self.btn_container.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Minimum)

        parent_layout.addWidget(self.btn_container, 0, Qt.AlignTop)

    def toggle_favorite(self):
        folder = self.meta.get('folder_name')
        favs = settings.setdefault('favorites', [])
        if self.favorite_btn.isChecked():
            if folder not in favs:
                favs.append(folder)
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
        tags_layout.setSpacing(6)
        for t in tags[:5]:
            chip = QLabel(t)
            chip.setObjectName("game_tag")
            chip.setFont(QFont('Segoe UI', 9))
            tags_layout.addWidget(chip)
        parent_layout.addLayout(tags_layout)

    def apply_theme(self):
        # Leave styling to QSS
        self.title_label.setStyleSheet(f"")
        self.desc_label.setStyleSheet(f"")

    def launch_game(self):
        try:
            entry_file = self.meta.get('entry', 'main.py')
            main_py = os.path.join(self.meta.get('path', ''), entry_file)
            if not os.path.exists(main_py):
                QMessageBox.warning(self, 'Launch Error', f"No {entry_file} found in {self.meta.get('path')}")
                return
            
            folder_name = self.meta.get('folder_name') or os.path.basename(self.meta.get('path', ''))
            
            settings.setdefault('recently_played', {})[folder_name] = int(time.time())
            settings['recently_played'] = dict(sorted(settings['recently_played'].items(), key=lambda x: x[1], reverse=True))
            
            pc = settings.setdefault('play_counts', {})
            pc[folder_name] = pc.get(folder_name, 0) + 1
            settings['play_counts'] = pc
            
            if settings.get('mini_rewards', True):
                settings['coins'] = settings.get('coins', 0) + 1
                
            save_settings()
            
            try:
                recent = load_recently_played()
                recent[folder_name] = int(time.time())
                save_recently_played(recent)
            except Exception as e:
                print("Failed to update recently_played.json:", e)
                
            total_plays = sum(settings.get('play_counts', {}).values())
            if total_plays >= 1: check_unlock_achievement('first_play')
            if total_plays >= 5: check_unlock_achievement('five_plays')
            if total_plays >= 10: check_unlock_achievement('ten_plays')
            
            subprocess.Popen([sys.executable, main_py])
            
        except Exception as e:
            try:
                QMessageBox.critical(self, 'Launch Failed', f'Failed to launch game: {e}')
            except Exception:
                print("Launch failed:", e)

    def show_howto(self):
        txt = self.meta.get('how_to_play') or 'No instructions available.'
        dlg = QDialog(self)
        dlg.setWindowTitle(f"How to Play — {self.meta.get('title', 'Game')}")
        dlg.resize(520, 420)
        dlg.setStyleSheet(f"background-color: {theme.get('bg', '#2B2B2B')}; color: {theme.get('fg', '#FFFFFF')};")
        layout = QVBoxLayout()
        label = QLabel(txt)
        label.setWordWrap(True)
        label.setFont(QFont('Segoe UI', 11))
        layout.addWidget(label)
        dlg.setLayout(layout)
        dlg.exec()
# scripts/gui/dialogs.py
"""
Contains various dialog windows for settings, achievements, and other modal interactions.
"""

import os
import json
import shutil
import time
import random
import sys
from zipfile import ZipFile, ZIP_DEFLATED

# PySide6 imports
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QScrollArea, QWidget, QFileDialog, QLineEdit, QMessageBox,
    QComboBox, QInputDialog, QCheckBox, QSpinBox, QColorDialog,
    QFontDialog, QListWidget, QListWidgetItem, QTextEdit
)
from PySide6.QtGui import QFont, QColor
from PySide6.QtCore import Qt

# Project imports
from ..managers.settings_manager import settings, save_settings, THEMES, DEFAULT_SETTINGS, theme
from ..utils.constants import SAVE_PATH, CACHE_PATH, ACHIEVEMENTS_DEF, MGAIO_DIR
from ..utils.file_io import safe_load_json
from ..utils.security import password_strength, encrypt_json, decrypt_json, hash_password


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
        sorted_aids = sorted(ACHIEVEMENTS_DEF.keys(), key=lambda k: 0 if k in ach_state else 1)

        for aid in sorted_aids:
            info = ACHIEVEMENTS_DEF[aid]
            unlocked = aid in ach_state
            text = f"{info['name']} {'(Unlocked)' if unlocked else '(Locked)'}"
            item = QListWidgetItem(text)
            item.setData(Qt.UserRole, aid)
            self.list_widget.addItem(item)
        self.list_widget.currentItemChanged.connect(self.on_select)
        if self.list_widget.count() > 0:
            self.list_widget.setCurrentRow(0)

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
        
        preset_layout = QHBoxLayout()
        for key in THEMES.keys():
            btn = QPushButton(key.capitalize())
            btn.clicked.connect(lambda _, k=key: self.apply_theme(k))
            preset_layout.addWidget(btn)
        self.layout.addLayout(preset_layout)

        for label, key in [("Background", "bg"), ("Foreground", "fg"), ("Accent", "accent")]:
            btn = QPushButton(f"Pick {label} Color")
            btn.clicked.connect(lambda _, k=key: self.pick_color(k))
            self.layout.addWidget(btn)

        self.font_btn = QPushButton("Pick Font")
        self.font_btn.clicked.connect(self.pick_font)
        self.layout.addWidget(self.font_btn)
        
        theme_io_layout = QHBoxLayout()
        self.import_theme_btn = QPushButton("Import Theme")
        self.import_theme_btn.clicked.connect(self.import_theme)
        theme_io_layout.addWidget(self.import_theme_btn)

        self.export_theme_btn = QPushButton("Export Theme")
        self.export_theme_btn.clicked.connect(self.export_theme)
        theme_io_layout.addWidget(self.export_theme_btn)
        self.layout.addLayout(theme_io_layout)
        
        self.load_qss_btn = QPushButton("Load Custom QSS")
        self.load_qss_btn.clicked.connect(self.load_custom_qss)
        self.layout.addWidget(self.load_qss_btn)


    def load_custom_qss(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select QSS File", "", "Stylesheets (*.qss)")
        if not path:
            return

        try:
            with open(path, 'r', encoding='utf-8') as f:
                qss = f.read()
                if hasattr(self.parent(), "setStyleSheet"):
                    self.parent().setStyleSheet(qss)
                settings["custom_qss_path"] = path
                save_settings()
            QMessageBox.information(self, "Custom QSS", f"Applied QSS from: {os.path.basename(path)}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load QSS:\n{e}")

    def import_theme(self):
        path, _ = QFileDialog.getOpenFileName(self, "Import Theme JSON", "", "JSON Files (*.json)")
        if not path:
            return

        password, ok = QInputDialog.getText(self, "Password (optional)", "Enter password if encrypted:", QLineEdit.Normal)
        try:
            with open(path, 'r', encoding='utf-8') as f:
                text = f.read()
                data = decrypt_json(text, password) if ok and password else json.loads(text)

            if 'name' in data and 'bg' in data and 'fg' in data:
                THEMES[data['name']] = data
                QMessageBox.information(self, "Theme Imported", f"Theme '{data['name']}' added!")
            else:
                QMessageBox.warning(self, "Error", "Invalid theme file (missing 'name', 'bg', or 'fg')!")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to import theme:\n{e}")

    def export_theme(self):
        current_theme_name = settings.get("theme", "default")
        if current_theme_name not in THEMES:
            QMessageBox.warning(self, "Export Theme", "Current theme not found!")
            return

        path, _ = QFileDialog.getSaveFileName(self, "Export Theme JSON", "", "JSON Files (*.json)")
        if not path:
            return

        password, ok = QInputDialog.getText(self, "Password (optional)", "Enter password to encrypt (leave blank for none):", QLineEdit.Normal)
        try:
            data = THEMES[current_theme_name].copy()
            data['name'] = current_theme_name
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

        self.compact_mode_toggle = QCheckBox("Enable Compact Mode")
        self.compact_mode_toggle.setChecked(settings.get("compact_mode", False))
        self.layout.addWidget(self.compact_mode_toggle)

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

        game_btn_layout = QHBoxLayout()
        self.bulk_backup_btn = QPushButton("Backup Saves")
        self.bulk_backup_btn.clicked.connect(self.backup_saves)
        game_btn_layout.addWidget(self.bulk_backup_btn)

        self.bulk_restore_btn = QPushButton("Restore Saves")
        self.bulk_restore_btn.clicked.connect(self.restore_saves)
        game_btn_layout.addWidget(self.bulk_restore_btn)
        self.layout.addLayout(game_btn_layout)

        self.clear_cache_btn = QPushButton("Clear Game Cache")
        self.clear_cache_btn.clicked.connect(self.clear_cache)
        self.layout.addWidget(self.clear_cache_btn)

    def backup_saves(self):
        if not os.path.exists(SAVE_PATH) or not os.listdir(SAVE_PATH):
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
                if hasattr(self.parent(), "load_games"):
                    self.parent().load_games()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to clear cache:\n{e}")

    def _app_lock_section(self):
        self.add_section_label("--- 🔒 App Lock & Security ---")

        self.pwd_input = QLineEdit()
        self.pwd_input.setEchoMode(QLineEdit.Password)
        self.pwd_input.setPlaceholderText("Enter new password/PIN or leave blank to disable")
        self.layout.addWidget(QLabel("Set App Lock Password or PIN:"))
        self.layout.addWidget(self.pwd_input)

        self.strength_label = QLabel("Strength: ")
        self.strength_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.layout.addWidget(self.strength_label)

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
        self.add_section_label("💾 Backup / Restore Settings")
        for text, func in [("Backup Settings Now", self.backup),
                           ("Restore Settings Now", self.restore),
                           ("Reset to Default (Warning)", self.reset_to_default)]:
            btn = QPushButton(text)
            btn.clicked.connect(func)
            self.layout.addWidget(btn)

    def _advanced_features_section(self):
        self.add_section_label("--- ⚙ Advanced Features ---")
        self.custom_script_btn = QPushButton("Select Startup Script")
        self.custom_script_btn.clicked.connect(self.select_script)
        self.layout.addWidget(self.custom_script_btn)

    def _fun_section(self):
        self.add_section_label("--- 🥳 Fun & Gamification ---")
        toggles = [
            ("Enable Daily Challenges", "daily_challenges"),
            ("Enable Mini Rewards (+1 coin per play)", "mini_rewards"),
            ("Enable Particles (on some events)", "particles"),
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

        self.coins_label = QLabel(f"Coins: {settings.get('coins', 0)}")
        self.coins_label.mousePressEvent = lambda e: self.trigger_easter_egg()
        self.layout.addWidget(self.coins_label)

    def trigger_easter_egg(self):
        if not settings.get("easter_eggs", True):
            return

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
        current_theme_colors = THEMES.get(name)
        if current_theme_colors:
            settings["theme"] = name
            settings["theme_colors"] = current_theme_colors
            save_settings()
            QMessageBox.information(self, "Theme", f"Applied theme: {name}. Restart recommended.")
            if hasattr(self.parent(), "apply_current_theme"):
                 self.parent().apply_current_theme()

    def pick_color(self, key):
        color = QColorDialog.getColor(QColor(settings.get("theme_colors", {}).get(key, "#FFFFFF")))
        if color.isValid():
            settings["theme_colors"][key] = color.name().upper()
            save_settings()
            QMessageBox.information(self, "Color Picker", f"{key.capitalize()} set to {color.name()}. Restart recommended.")
            if hasattr(self.parent(), "apply_current_theme"):
                 self.parent().apply_current_theme()

    def pick_font(self):
        font_data = settings.get("font", {"family": "Segoe UI", "size": 11})
        font, ok = QFontDialog.getFont(
            QFont(font_data.get("family"), font_data.get("size")),
            self,
            "Select Font"
        )
        if ok:
            settings["font"] = {"family": font.family(), "size": font.pointSize()}
            save_settings()
            QMessageBox.information(self, "Font", f"Font set to {font.family()} {font.pointSize()}pt. Restart recommended.")

    def backup(self):
        path, _ = QFileDialog.getSaveFileName(self, "Backup Settings", os.path.join(MGAIO_DIR, "settings_backup.json"), "JSON Files (*.json)")
        if path:
            with open(path, "w") as f:
                json.dump(settings, f, indent=2)
            QMessageBox.information(self, "Backup", "Settings backed up.")

    def restore(self):
        path, _ = QFileDialog.getOpenFileName(self, "Restore Settings", os.path.join(MGAIO_DIR, "settings_backup.json"), "JSON Files (*.json)")
        if path:
            data = safe_load_json(path) or {}
            settings.clear()
            settings.update(DEFAULT_SETTINGS.copy())
            settings.update(data)
            save_settings()
            QMessageBox.information(self, "Restore", "Settings restored. Please restart the launcher.")

    def reset_to_default(self):
        reply = QMessageBox.warning(
            self,
            "⚠️ Reset to Default",
            "This will erase all your current settings and plays and cannot be undone!\n\nDo you want to continue?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return

        text, ok = QInputDialog.getText(
            self,
            "Confirm Reset",
            "Type 'RESET' to confirm:",
            QLineEdit.Normal
        )
        if not ok or text.strip().upper() != "RESET":
            QMessageBox.information(self, "Cancelled", "Reset cancelled.")
            return

        settings.clear()
        settings.update(DEFAULT_SETTINGS.copy())
        save_settings()
        QMessageBox.information(self, "Reset", "Settings have been reset to default. Restarting...")
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
        
        new_password_set = False
        if password:
            strength, _ = password_strength(password)
            if use_pin:
                if not password.isdigit() or len(password) != 4:
                    QMessageBox.warning(None, "Invalid PIN", "Your PIN must be exactly 4 digits (0–9 only).")
                    return
            elif strength not in ["Strong", "Stronger"]:
                QMessageBox.warning(None, "Weak Password", f"Your password is too weak: {strength}\n"
                                                           "Please use at least 4 chars, include 1 number and 1 symbol, and avoid sequences.")
                return

            settings["lock_password"] = hash_password(password)
            new_password_set = True
        elif settings.get('lock_password') and not password:
            reply = QMessageBox.question(None, "Disable Lock", "Do you want to disable the App Lock?", QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                settings["lock_password"] = ""
        
        settings["use_pin"] = use_pin
        settings["lock_on_startup"] = self.lock_on_startup.isChecked()
        settings["auto_lock"] = self.auto_lock_spin.value()

        settings["favorites_only"] = self.favorites_toggle.isChecked()
        settings["auto_sort"] = self.auto_sort_combo.currentText()
        settings["compact_mode"] = self.compact_mode_toggle.isChecked()

        for key in ["particles", "sound_effects", "notifications", "achievements_panel",
                    "daily_challenges", "mini_rewards", "easter_eggs"]:
            settings[key] = getattr(self, f"{key}_toggle").isChecked()
            
        self.coins_label.setText(f"Coins: {settings.get('coins', 0)}")
        
        save_settings()
        QMessageBox.information(self, "Settings", "All settings saved!" + ("\nPlease restart for full theme/font effect." if new_password_set else ""))
        
        if hasattr(self.parent(), 'load_games'):
            self.parent().load_games()
            
        self.accept()
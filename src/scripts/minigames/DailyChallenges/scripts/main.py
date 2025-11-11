#!/usr/bin/env python3
# daily_challenges.py — Daily Challenges / Missions App (PySide6)

import sys
import json
import uuid
import random
from pathlib import Path
from datetime import date, timedelta

from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QInputDialog, QSpinBox, QMessageBox, QLineEdit
)
from PySide6.QtCore import Qt

# ---------------- CONFIG / SAVE PATH ----------------
APP_NAME = "Daily Challenges"
SAVE_DIR = Path.home() / "Documents" / ".mgaio" / "Saves" / APP_NAME
SAVE_DIR.mkdir(parents=True, exist_ok=True)
SETTINGS_FILE = SAVE_DIR / "settings.json"

DEFAULT_DATA = {
    "missions": {},   # id -> {"text": str, "reward": int, "completed": bool}
    "order": [],      # list of ids (order in UI)
    "coins": 0,
    "streak": 0,
    "last_reset": None,         # "YYYY-MM-DD"
    "last_all_complete": None   # "YYYY-MM-DD" when all missions were completed and rewarded
}

def load_data():
    if SETTINGS_FILE.exists():
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = DEFAULT_DATA.copy()
    else:
        data = DEFAULT_DATA.copy()
    # ensure keys
    for k, v in DEFAULT_DATA.items():
        if k not in data:
            data[k] = v
    return data

def save_data(d):
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(d, f, indent=2)
    except Exception as e:
        print("Failed to save settings:", e)

# ---------------- Helper date funcs ----------------
def today_iso():
    return date.today().isoformat()

def yesterday_iso():
    return (date.today() - timedelta(days=1)).isoformat()

# ---------------- App ----------------
class DailyChallengesApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Daily Challenges / Missions")
        self.setMinimumSize(520, 420)

        self.data = load_data()
        self._ensure_defaults()

        # reset daily if needed
        self._daily_reset_if_needed()

        # UI
        main = QVBoxLayout()
        self.setLayout(main)

        # header: coins + streak
        header = QHBoxLayout()
        self.coins_label = QLabel()
        self.streak_label = QLabel()
        header.addWidget(self.coins_label)
        header.addStretch()
        header.addWidget(self.streak_label)
        main.addLayout(header)
        self._update_status_labels()

        # mission list
        self.list_widget = QListWidget()
        self.list_widget.itemChanged.connect(self.on_item_changed)
        main.addWidget(self.list_widget, stretch=1)

        # action buttons
        row1 = QHBoxLayout()
        self.add_btn = QPushButton("➕ Add")
        self.edit_btn = QPushButton("✎ Edit")
        self.delete_btn = QPushButton("🗑 Delete")
        self.shuffle_btn = QPushButton("🔀 Shuffle")
        row1.addWidget(self.add_btn)
        row1.addWidget(self.edit_btn)
        row1.addWidget(self.delete_btn)
        row1.addWidget(self.shuffle_btn)
        main.addLayout(row1)

        # claim / reset row
        row2 = QHBoxLayout()
        self.claim_btn = QPushButton("🏆 Claim Reward (All Done)")
        self.reset_btn = QPushButton("🔁 Reset Today")
        self.refresh_btn = QPushButton("🔄 Refresh")
        row2.addWidget(self.claim_btn)
        row2.addWidget(self.reset_btn)
        row2.addWidget(self.refresh_btn)
        main.addLayout(row2)

        # Connect signals
        self.add_btn.clicked.connect(self.add_mission)
        self.edit_btn.clicked.connect(self.edit_selected)
        self.delete_btn.clicked.connect(self.delete_selected)
        self.shuffle_btn.clicked.connect(self.shuffle_missions)
        self.claim_btn.clicked.connect(self.claim_reward)
        self.reset_btn.clicked.connect(self.force_reset)
        self.refresh_btn.clicked.connect(self.reload_ui)

        # populate list
        self.reload_ui()

    def _ensure_defaults(self):
        # If no missions exist, create sample missions
        if not self.data.get("missions"):
            for t, r in [("Do 10 push-ups", 5), ("Drink a glass of water", 2), ("Read for 10 minutes", 5)]:
                sid = str(uuid.uuid4())
                self.data["missions"][sid] = {"text": t, "reward": r, "completed": False}
                self.data.setdefault("order", []).append(sid)
            save_data(self.data)

    def _daily_reset_if_needed(self):
        last = self.data.get("last_reset")
        today = today_iso()
        if last != today:
            # Reset completed flags
            for sid, m in self.data["missions"].items():
                m["completed"] = False
            self.data["last_reset"] = today
            save_data(self.data)

    def _update_status_labels(self):
        self.coins_label.setText(f"Coins: {self.data.get('coins',0)}")
        self.streak_label.setText(f"Streak: {self.data.get('streak',0)}  (last complete: {self.data.get('last_all_complete') or '—'})")

    def reload_ui(self):
        # avoid firing itemChanged while populating
        self.list_widget.blockSignals(True)
        self.list_widget.clear()
        order = self.data.get("order", [])
        # ensure order contains all ids
        ids = list(self.data["missions"].keys())
        for sid in ids:
            if sid not in order:
                order.append(sid)
        # show in order
        for sid in order:
            meta = self.data["missions"].get(sid)
            if not meta:
                continue
            text = meta.get("text","")
            reward = meta.get("reward", 0)
            item = QListWidgetItem(f"{text}  —  (+{reward} coins)")
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable | Qt.ItemIsSelectable | Qt.ItemIsEnabled)
            item.setCheckState(Qt.Checked if meta.get("completed", False) else Qt.Unchecked)
            item.setData(Qt.UserRole, sid)
            self.list_widget.addItem(item)
        self.list_widget.blockSignals(False)
        self._update_status_labels()
        self._update_claim_button_state()

    def on_item_changed(self, item: QListWidgetItem):
        sid = item.data(Qt.UserRole)
        checked = item.checkState() == Qt.Checked
        if sid in self.data["missions"]:
            self.data["missions"][sid]["completed"] = checked
            save_data(self.data)
        self._update_claim_button_state()

    def add_mission(self):
        text, ok = QInputDialog.getText(self, "New Mission", "Mission description:")
        if not ok or not text.strip():
            return
        reward, ok2 = QInputDialog.getInt(self, "Reward (coins)", "Coins reward:", 5, 0, 1000)
        if not ok2:
            reward = 5
        sid = str(uuid.uuid4())
        self.data["missions"][sid] = {"text": text.strip(), "reward": int(reward), "completed": False}
        self.data.setdefault("order", []).append(sid)
        save_data(self.data)
        self.reload_ui()

    def edit_selected(self):
        item = self.list_widget.currentItem()
        if not item:
            QMessageBox.information(self, "Edit", "Select a mission to edit.")
            return
        sid = item.data(Qt.UserRole)
        meta = self.data["missions"].get(sid)
        if not meta:
            return
        new_text, ok = QInputDialog.getText(self, "Edit Mission", "Mission description:", text=meta.get("text",""))
        if ok and new_text.strip():
            meta["text"] = new_text.strip()
        new_reward, ok2 = QInputDialog.getInt(self, "Edit Reward", "Coins reward:", meta.get("reward",5), 0, 10000)
        if ok2:
            meta["reward"] = int(new_reward)
        self.data["missions"][sid] = meta
        save_data(self.data)
        self.reload_ui()

    def delete_selected(self):
        item = self.list_widget.currentItem()
        if not item:
            QMessageBox.information(self, "Delete", "Select a mission to delete.")
            return
        sid = item.data(Qt.UserRole)
        confirm = QMessageBox.question(self, "Delete Mission", "Delete selected mission?", QMessageBox.Yes | QMessageBox.No)
        if confirm != QMessageBox.Yes:
            return
        if sid in self.data["missions"]:
            del self.data["missions"][sid]
        if sid in self.data.get("order", []):
            self.data["order"].remove(sid)
        save_data(self.data)
        self.reload_ui()

    def shuffle_missions(self):
        order = self.data.get("order", [])
        random.shuffle(order)
        self.data["order"] = order
        save_data(self.data)
        self.reload_ui()

    def _all_completed(self):
        if not self.data["missions"]:
            return False
        return all(m.get("completed", False) for m in self.data["missions"].values())

    def _update_claim_button_state(self):
        if self._all_completed():
            # disable claim if already claimed today
            last_complete = self.data.get("last_all_complete")
            if last_complete == today_iso():
                self.claim_btn.setEnabled(False)
                self.claim_btn.setText("🏆 Already claimed today")
            else:
                self.claim_btn.setEnabled(True)
                self.claim_btn.setText("🏆 Claim Reward (All Done)")
        else:
            self.claim_btn.setEnabled(False)
            self.claim_btn.setText("🏆 Claim Reward (All Done)")

    def claim_reward(self):
        if not self._all_completed():
            QMessageBox.information(self, "Not complete", "Complete all missions first to claim the reward.")
            return
        # prevent double-claim same day
        if self.data.get("last_all_complete") == today_iso():
            QMessageBox.information(self, "Already claimed", "You have already claimed today's reward.")
            return
        # sum rewards
        total = sum(m.get("reward",0) for m in self.data["missions"].values())
        # update coins
        self.data["coins"] = self.data.get("coins", 0) + total
        # update streak: if last_all_complete == yesterday -> +1 else reset to 1
        last = self.data.get("last_all_complete")
        if last == yesterday_iso():
            self.data["streak"] = self.data.get("streak", 0) + 1
        else:
            self.data["streak"] = 1
        self.data["last_all_complete"] = today_iso()
        save_data(self.data)
        QMessageBox.information(self, "Reward Claimed", f"You earned {total} coins!\nTotal coins: {self.data['coins']}")
        self.reload_ui()

    def force_reset(self):
        confirm = QMessageBox.question(self, "Reset Today", "Reset today's completion flags now?", QMessageBox.Yes | QMessageBox.No)
        if confirm != QMessageBox.Yes:
            return
        for sid in self.data["missions"].keys():
            self.data["missions"][sid]["completed"] = False
        self.data["last_reset"] = today_iso()
        save_data(self.data)
        self.reload_ui()

# ---------------- Run ----------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = DailyChallengesApp()
    w.show()
    sys.exit(app.exec())

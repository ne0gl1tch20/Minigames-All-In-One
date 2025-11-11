#!/usr/bin/env python3
# habit_tracker.py — Habit Tracker / Streaks App (PySide6)

import sys
import json
import uuid
from pathlib import Path
from datetime import date, timedelta, datetime

from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QInputDialog, QMessageBox
)
from PySide6.QtCore import Qt

# ---------------- CONFIG / SAVE PATH ----------------
APP_NAME = "Habit Tracker"
SAVE_DIR = Path.home() / "Documents" / ".mgaio" / "Saves" / APP_NAME
SAVE_DIR.mkdir(parents=True, exist_ok=True)
SETTINGS_FILE = SAVE_DIR / "settings.json"

DEFAULT_DATA = {
    "habits": {  # id -> { "name": str, "history": [ "YYYY-MM-DD", ... ], "longest": int }
    },
    "meta": {
        "created": date.today().isoformat()
    }
}

def load_data():
    if SETTINGS_FILE.exists():
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                d = json.load(f)
        except Exception:
            d = DEFAULT_DATA.copy()
    else:
        d = DEFAULT_DATA.copy()
    # ensure keys
    if "habits" not in d:
        d["habits"] = {}
    if "meta" not in d:
        d["meta"] = {"created": date.today().isoformat()}
    return d

def save_data(d):
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(d, f, indent=2)
    except Exception as e:
        print("Failed to save habit data:", e)

# ---------- Date helpers ----------
def today_iso():
    return date.today().isoformat()

def to_date(iso_str):
    return datetime.strptime(iso_str, "%Y-%m-%d").date()

def days_between(a_iso, b_iso):
    return (to_date(a_iso) - to_date(b_iso)).days

def yesterday_iso():
    return (date.today() - timedelta(days=1)).isoformat()

# ---------- Streak computation ----------
def compute_streak(history_iso_list):
    """
    Given a list of ISO date strings (history), compute current consecutive-day streak
    ending at the latest day in history (if that is today or earlier).
    Also returns the longest streak found.
    """
    if not history_iso_list:
        return 0, 0
    # unique and sort ascending
    dates = sorted({d for d in history_iso_list})
    # convert to date objects
    dt = [to_date(s) for s in dates]
    longest = 0
    current_longest = 1
    longest = 1
    for i in range(1, len(dt)):
        if (dt[i] - dt[i-1]).days == 1:
            current_longest += 1
            if current_longest > longest:
                longest = current_longest
        else:
            current_longest = 1
    # compute current streak ending at the last date
    last = dt[-1]
    streak = 1
    idx = len(dt) - 1
    while idx > 0:
        if (dt[idx] - dt[idx-1]).days == 1:
            streak += 1
            idx -= 1
        else:
            break
    # if the last recorded day isn't today, current streak should be 0 (not completed today)
    if last != date.today():
        # But if last == yesterday, we still let streak reflect consecutive run even if not yet completed today.
        # Usually user's "current streak" is only active if done today. We'll return actual consecutive run but caller can treat differently.
        # For UI, we'll show streak as the consecutive run including last_done; if user wants "active streak", check if today in history.
        pass
    return streak, longest

# ---------------- App ----------------
class HabitTrackerApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Habit Tracker / Streaks")
        self.setMinimumSize(520, 420)

        self.data = load_data()
        self._ensure_sample()

        main = QVBoxLayout()
        self.setLayout(main)

        header = QHBoxLayout()
        self.info_label = QLabel()
        header.addWidget(self.info_label)
        header.addStretch()
        main.addLayout(header)
        self._update_info()

        # list of habits
        self.list_widget = QListWidget()
        self.list_widget.itemChanged.connect(self.on_item_changed)
        main.addWidget(self.list_widget, stretch=1)

        row1 = QHBoxLayout()
        self.add_btn = QPushButton("➕ Add Habit")
        self.edit_btn = QPushButton("✎ Edit Habit")
        self.delete_btn = QPushButton("🗑 Delete Habit")
        self.view_history_btn = QPushButton("📜 View History")
        row1.addWidget(self.add_btn)
        row1.addWidget(self.edit_btn)
        row1.addWidget(self.delete_btn)
        row1.addWidget(self.view_history_btn)
        main.addLayout(row1)

        row2 = QHBoxLayout()
        self.mark_prev_btn = QPushButton("◀ Mark Yesterday Done")
        self.reset_streak_btn = QPushButton("♻ Reset Streak")
        self.refresh_btn = QPushButton("🔄 Refresh")
        row2.addWidget(self.mark_prev_btn)
        row2.addWidget(self.reset_streak_btn)
        row2.addWidget(self.refresh_btn)
        main.addLayout(row2)

        # Connect signals
        self.add_btn.clicked.connect(self.add_habit)
        self.edit_btn.clicked.connect(self.edit_selected)
        self.delete_btn.clicked.connect(self.delete_selected)
        self.view_history_btn.clicked.connect(self.view_history)
        self.mark_prev_btn.clicked.connect(self.mark_yesterday_for_selected)
        self.reset_streak_btn.clicked.connect(self.reset_streak_selected)
        self.refresh_btn.clicked.connect(self.reload_ui)

        self.reload_ui()

    def _ensure_sample(self):
        if not self.data.get("habits"):
            # sample habits
            for name in ["Drink water", "Read 10 min", "Stretch"]:
                sid = str(uuid.uuid4())
                self.data["habits"][sid] = {"name": name, "history": [], "longest": 0}
            save_data(self.data)

    def _update_info(self):
        total = len(self.data.get("habits", {}))
        active_streaks = sum(1 for h in self.data.get("habits", {}).values() if today_iso() in h.get("history", []))
        self.info_label.setText(f"Habits: {total}   •   Done today: {active_streaks}")

    def reload_ui(self):
        self.list_widget.blockSignals(True)
        self.list_widget.clear()
        # show habits sorted by name
        items = sorted(self.data.get("habits", {}).items(), key=lambda x: x[1].get("name","").lower())
        for sid, meta in items:
            name = meta.get("name", "Habit")
            hist = meta.get("history", [])
            streak, longest = compute_streak(hist)
            done_today = today_iso() in hist
            item_text = f"{name}  —  Streak: {streak}  •  Longest: {meta.get('longest', longest)}"
            item = QListWidgetItem(item_text)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable | Qt.ItemIsSelectable | Qt.ItemIsEnabled)
            item.setCheckState(Qt.Checked if done_today else Qt.Unchecked)
            item.setData(Qt.UserRole, sid)
            self.list_widget.addItem(item)
        self.list_widget.blockSignals(False)
        self._update_info()

    def on_item_changed(self, item: QListWidgetItem):
        sid = item.data(Qt.UserRole)
        if sid not in self.data["habits"]:
            return
        checked = item.checkState() == Qt.Checked
        hist = set(self.data["habits"][sid].get("history", []))
        today = today_iso()
        if checked:
            if today not in hist:
                hist.add(today)
        else:
            if today in hist:
                hist.remove(today)
        # store sorted unique history
        hist_list = sorted(hist)
        self.data["habits"][sid]["history"] = hist_list
        # recompute streak and longest
        streak, longest = compute_streak(hist_list)
        prev_longest = self.data["habits"][sid].get("longest", 0)
        if longest > prev_longest:
            self.data["habits"][sid]["longest"] = longest
        save_data(self.data)
        self.reload_ui()

    def add_habit(self):
        text, ok = QInputDialog.getText(self, "New Habit", "Habit name:")
        if not ok or not text.strip():
            return
        sid = str(uuid.uuid4())
        self.data["habits"][sid] = {"name": text.strip(), "history": [], "longest": 0}
        save_data(self.data)
        self.reload_ui()

    def edit_selected(self):
        item = self.list_widget.currentItem()
        if not item:
            QMessageBox.information(self, "Edit Habit", "Select a habit to edit.")
            return
        sid = item.data(Qt.UserRole)
        meta = self.data["habits"].get(sid, {})
        new_name, ok = QInputDialog.getText(self, "Edit Habit", "Habit name:", text=meta.get("name",""))
        if ok and new_name.strip():
            meta["name"] = new_name.strip()
            self.data["habits"][sid] = meta
            save_data(self.data)
            self.reload_ui()

    def delete_selected(self):
        item = self.list_widget.currentItem()
        if not item:
            QMessageBox.information(self, "Delete Habit", "Select a habit to delete.")
            return
        sid = item.data(Qt.UserRole)
        confirm = QMessageBox.question(self, "Delete Habit", "Delete selected habit?", QMessageBox.Yes | QMessageBox.No)
        if confirm != QMessageBox.Yes:
            return
        if sid in self.data["habits"]:
            del self.data["habits"][sid]
            save_data(self.data)
            self.reload_ui()

    def view_history(self):
        item = self.list_widget.currentItem()
        if not item:
            QMessageBox.information(self, "View History", "Select a habit first.")
            return
        sid = item.data(Qt.UserRole)
        meta = self.data["habits"].get(sid, {})
        hist = sorted(meta.get("history", []), reverse=True)
        if not hist:
            QMessageBox.information(self, "History", "No history yet for this habit.")
            return
        # show last 30 entries
        lines = hist[:30]
        QMessageBox.information(self, "History (latest first)", "\n".join(lines))

    def mark_yesterday_for_selected(self):
        item = self.list_widget.currentItem()
        if not item:
            QMessageBox.information(self, "Mark Yesterday", "Select a habit first.")
            return
        sid = item.data(Qt.UserRole)
        meta = self.data["habits"].get(sid, {})
        y = yesterday_iso()
        hist = set(meta.get("history", []))
        if y in hist:
            QMessageBox.information(self, "Already marked", "Yesterday is already marked done for this habit.")
            return
        hist.add(y)
        meta["history"] = sorted(hist)
        # recompute longest
        _, longest = compute_streak(meta["history"])
        if longest > meta.get("longest", 0):
            meta["longest"] = longest
        self.data["habits"][sid] = meta
        save_data(self.data)
        self.reload_ui()

    def reset_streak_selected(self):
        item = self.list_widget.currentItem()
        if not item:
            QMessageBox.information(self, "Reset Streak", "Select a habit first.")
            return
        sid = item.data(Qt.UserRole)
        confirm = QMessageBox.question(self, "Reset Streak", "Reset the streak and clear history for this habit?", QMessageBox.Yes | QMessageBox.No)
        if confirm != QMessageBox.Yes:
            return
        meta = self.data["habits"].get(sid, {})
        meta["history"] = []
        meta["longest"] = 0
        self.data["habits"][sid] = meta
        save_data(self.data)
        self.reload_ui()

# ---------------- Run ----------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = HabitTrackerApp()
    w.show()
    sys.exit(app.exec())

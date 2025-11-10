import sys
import os
import json
from pathlib import Path
from datetime import datetime
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout,
    QLineEdit, QListWidget, QListWidgetItem, QMessageBox, QComboBox
)
from PySide6.QtCore import Qt

# ------------------- CONFIG / SAVE PATH -------------------
USER_DIR = os.path.expandvars(r"%userprofile%")
MG_SAVE_DIR = Path(USER_DIR) / "Documents" / ".mgaio"
APP_NAME = "Task Manager"
SAVE_FOLDER = MG_SAVE_DIR / "Saves" / APP_NAME
SAVE_FOLDER.mkdir(parents=True, exist_ok=True)

TASKS_FILE = SAVE_FOLDER / "tasks.json"
STATS_FILE = SAVE_FOLDER / "stats.json"

# ------------------- LOAD / SAVE UTILS -------------------
def load_json(path, default):
    if path.exists():
        with open(path, "r") as f:
            return json.load(f)
    return default

def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=4)

# ------------------- INITIAL DATA -------------------
tasks_data = load_json(TASKS_FILE, {"tasks": []})
stats_data = load_json(STATS_FILE, {"completed_tasks": [], "coins": 0})
last_undo = None

# ------------------- MAIN APP -------------------
class TaskManager(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Task Manager / To-Do Board")
        self.setMinimumSize(400, 400)

        # --- Layouts ---
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        # --- Header ---
        self.header = QLabel("📝 Task Manager (Pomodoro Linked)")
        self.header.setAlignment(Qt.AlignCenter)
        self.header.setStyleSheet("font-size: 18px; font-weight: bold;")
        main_layout.addWidget(self.header)

        # --- Coin Counter ---
        self.coin_label = QLabel(f"Coins: {stats_data.get('coins', 0)} 🪙")
        self.coin_label.setAlignment(Qt.AlignCenter)
        self.coin_label.setStyleSheet("font-size: 14px; color: #ffaa00;")
        main_layout.addWidget(self.coin_label)

        # --- Task Entry ---
        entry_layout = QHBoxLayout()
        self.task_input = QLineEdit()
        self.task_input.setPlaceholderText("Enter a new task...")
        self.priority_combo = QComboBox()
        self.priority_combo.addItems(["Low", "Medium", "High"])
        self.add_btn = QPushButton("Add Task")
        self.add_btn.clicked.connect(self.add_task)
        entry_layout.addWidget(self.task_input)
        entry_layout.addWidget(self.priority_combo)
        entry_layout.addWidget(self.add_btn)
        main_layout.addLayout(entry_layout)

        # --- Task List ---
        self.task_list = QListWidget()
        main_layout.addWidget(self.task_list)

        # --- Buttons ---
        btn_layout = QHBoxLayout()
        self.complete_btn = QPushButton("Complete Task ✅")
        self.delete_btn = QPushButton("Delete Task ❌")
        self.undo_btn = QPushButton("Undo Last Complete ↩️")
        self.complete_btn.clicked.connect(self.complete_task)
        self.delete_btn.clicked.connect(self.delete_task)
        self.undo_btn.clicked.connect(self.undo_last)
        btn_layout.addWidget(self.complete_btn)
        btn_layout.addWidget(self.delete_btn)
        btn_layout.addWidget(self.undo_btn)
        main_layout.addLayout(btn_layout)

        # --- Load Tasks ---
        self.load_tasks()

    # ------------------- TASK MANAGEMENT -------------------
    def add_task(self):
        text = self.task_input.text().strip()
        if not text:
            return
        priority = self.priority_combo.currentText()
        task = {"text": text, "priority": priority, "created": datetime.now().isoformat()}
        tasks_data["tasks"].append(task)
        self.task_input.clear()
        self.save_all()
        self.load_tasks()

    def complete_task(self):
        global last_undo
        selected = self.task_list.currentItem()
        if not selected:
            return
        index = self.task_list.row(selected)
        task = tasks_data["tasks"].pop(index)
        stats_data["completed_tasks"].append({
            "text": task["text"],
            "priority": task["priority"],
            "completed_at": datetime.now().isoformat()
        })
        stats_data["coins"] = stats_data.get("coins", 0) + 1
        last_undo = task
        self.save_all()
        self.load_tasks()

    def delete_task(self):
        selected = self.task_list.currentItem()
        if not selected:
            return
        index = self.task_list.row(selected)
        tasks_data["tasks"].pop(index)
        self.save_all()
        self.load_tasks()

    def undo_last(self):
        global last_undo
        if not last_undo:
            QMessageBox.information(self, "Undo", "No recent completed task to undo.")
            return
        # Remove from completed and deduct coin
        if stats_data["completed_tasks"]:
            last_entry = stats_data["completed_tasks"][-1]
            if last_entry["text"] == last_undo["text"]:
                stats_data["completed_tasks"].pop(-1)
                stats_data["coins"] = max(0, stats_data["coins"] - 1)
        tasks_data["tasks"].append(last_undo)
        last_undo = None
        self.save_all()
        self.load_tasks()

    # ------------------- FILE MANAGEMENT -------------------
    def save_all(self):
        save_json(TASKS_FILE, tasks_data)
        save_json(STATS_FILE, stats_data)
        self.coin_label.setText(f"Coins: {stats_data.get('coins', 0)} 🪙")

    def load_tasks(self):
        self.task_list.clear()
        for task in tasks_data["tasks"]:
            priority_color = {
                "Low": "#88ff88",
                "Medium": "#ffff88",
                "High": "#ff8888"
            }[task["priority"]]
            item = QListWidgetItem(f"[{task['priority']}] {task['text']}")
            item.setBackground(Qt.white)
            item.setForeground(Qt.black)
            item.setToolTip(f"Created: {task['created']}")
            item.setBackground(Qt.GlobalColor.transparent)
            item.setBackground(Qt.white)
            item.setBackground(Qt.transparent)
            item.setForeground(Qt.black)
            item.setBackground(Qt.transparent)
            item.setBackground(Qt.transparent)
            item.setBackground(Qt.transparent)
            item.setForeground(Qt.black)
            item.setBackground(Qt.transparent)
            item.setForeground(Qt.black)
            item.setBackground(Qt.transparent)
            item.setForeground(Qt.black)
            item.setBackground(Qt.transparent)
            self.task_list.addItem(item)

# ------------------- RUN APP -------------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TaskManager()
    window.show()
    sys.exit(app.exec())

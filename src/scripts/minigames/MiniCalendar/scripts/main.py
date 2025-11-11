#!/usr/bin/env python3
"""
Mini Calendar / Event Planner (PySide6)
- Month calendar view (QCalendarWidget)
- Add/Edit/Delete events for dates
- Simple recurrence: none / daily / weekly / monthly
- Save/load events to Documents/.mgaio/Saves/Mini Calendar/events.json
- Export / Import JSON and Export CSV
"""

import sys
import json
import uuid
from pathlib import Path
from datetime import date, datetime, timedelta
import csv

from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QLineEdit, QTextEdit, QDialog, QFormLayout,
    QDateEdit, QTimeEdit, QComboBox, QMessageBox, QFileDialog, QCalendarWidget,
    QSplitter, QSizePolicy
)
from PySide6.QtCore import Qt, QDate, QTime

# ---------------- CONFIG / SAVE PATH ----------------
APP_NAME = "Mini Calendar"
SAVE_DIR = Path.home() / "Documents" / ".mgaio" / "Saves" / APP_NAME
SAVE_DIR.mkdir(parents=True, exist_ok=True)
EVENTS_FILE = SAVE_DIR / "events.json"

DEFAULT_DATA = {
    "events": {}  # date_iso -> [ {id, title, time, notes, recurrence} ]
}

# ---------------- Data helpers ----------------
def load_events():
    if EVENTS_FILE.exists():
        try:
            with open(EVENTS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            if "events" not in data:
                data = {"events": {}}
        except Exception:
            data = {"events": {}}
    else:
        data = {"events": {}}
    # ensure structure
    data.setdefault("events", {})
    return data

def save_events(data):
    try:
        with open(EVENTS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print("Failed to save events:", e)

def iso_from_qdate(qdate: QDate):
    return qdate.toString("yyyy-MM-dd")

def qdate_from_iso(iso: str):
    return QDate.fromString(iso, "yyyy-MM-dd")

def time_to_str(qtime: QTime):
    return qtime.toString("HH:mm")

def str_to_time(s: str):
    try:
        return datetime.strptime(s, "%H:%M").time()
    except Exception:
        return None

# Recurrence checker: returns True if an event (with recurrence) occurs on `target_date`
def occurs_on(event, target_date: date):
    """
    event: dict with keys 'date' (iso string), 'time' (HH:MM or ""), 'recurrence' in (None, "daily","weekly","monthly")
    target_date: datetime.date
    """
    try:
        start = datetime.strptime(event["date"], "%Y-%m-%d").date()
    except Exception:
        return False
    if target_date < start:
        return False
    rec = event.get("recurrence") or None
    if not rec:
        return target_date == start
    if rec == "daily":
        return True  # every day from start
    if rec == "weekly":
        # same weekday
        return target_date.weekday() == start.weekday()
    if rec == "monthly":
        # same day-of-month where possible
        return start.day == target_date.day
    return False

# Flatten events for a specific date, includes recurring matches
def events_for_date(data, target_date: date):
    hits = []
    for iso, items in data.get("events", {}).items():
        for ev in items:
            if occurs_on(ev, target_date):
                hits.append(ev)
    # sort by time if available, else by title
    def keyfn(e):
        t = e.get("time") or ""
        return (t, e.get("title","").lower())
    hits.sort(key=keyfn)
    return hits

# ---------------- Dialog for Add/Edit ----------------
class EventDialog(QDialog):
    def __init__(self, parent=None, event=None, default_date: QDate = None):
        super().__init__(parent)
        self.setWindowTitle("Event")
        self.resize(420, 320)
        self.event = event

        layout = QVBoxLayout()
        form = QFormLayout()

        self.title_edit = QLineEdit()
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.time_edit = QTimeEdit()
        self.time_edit.setDisplayFormat("HH:mm")
        self.notes_edit = QTextEdit()
        self.recur_combo = QComboBox()
        self.recur_combo.addItems(["None", "Daily", "Weekly", "Monthly"])

        form.addRow("Title:", self.title_edit)
        form.addRow("Date:", self.date_edit)
        form.addRow("Time (optional):", self.time_edit)
        form.addRow("Recurrence:", self.recur_combo)
        form.addRow("Notes:", self.notes_edit)

        layout.addLayout(form)

        btn_row = QHBoxLayout()
        self.save_btn = QPushButton("Save")
        self.cancel_btn = QPushButton("Cancel")
        btn_row.addStretch()
        btn_row.addWidget(self.save_btn)
        btn_row.addWidget(self.cancel_btn)

        layout.addLayout(btn_row)
        self.setLayout(layout)

        self.save_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)

        # initialize values
        if event:
            self.title_edit.setText(event.get("title",""))
            self.date_edit.setDate(qdate_from_iso(event.get("date")))
            if event.get("time"):
                t = str_to_time(event.get("time"))
                if t:
                    self.time_edit.setTime(QTime(t.hour, t.minute))
            recur = event.get("recurrence") or ""
            if recur == "daily":
                self.recur_combo.setCurrentText("Daily")
            elif recur == "weekly":
                self.recur_combo.setCurrentText("Weekly")
            elif recur == "monthly":
                self.recur_combo.setCurrentText("Monthly")
            else:
                self.recur_combo.setCurrentText("None")
            self.notes_edit.setPlainText(event.get("notes",""))
        else:
            # defaults
            if default_date:
                self.date_edit.setDate(default_date)
            else:
                self.date_edit.setDate(QDate.currentDate())

    def result(self):
        title = self.title_edit.text().strip()
        date_iso = iso_from_qdate(self.date_edit.date())
        time_str = time_to_str(self.time_edit.time()) if self.time_edit.time().isValid() else ""
        notes = self.notes_edit.toPlainText().strip()
        r = self.recur_combo.currentText()
        recurrence = None
        if r == "Daily":
            recurrence = "daily"
        elif r == "Weekly":
            recurrence = "weekly"
        elif r == "Monthly":
            recurrence = "monthly"
        return {"title": title, "date": date_iso, "time": time_str, "notes": notes, "recurrence": recurrence}

# ---------------- Main App ----------------
class MiniCalendarApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Mini Calendar / Event Planner")
        self.setMinimumSize(800, 500)

        self.data = load_events()

        root = QVBoxLayout()
        self.setLayout(root)

        header = QHBoxLayout()
        header.addWidget(QLabel("📅 Mini Calendar — Add events, plan your day"))
        header.addStretch()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search events by title...")
        self.search_input.returnPressed.connect(self.search_events)
        header.addWidget(self.search_input)
        root.addLayout(header)

        splitter = QSplitter(Qt.Horizontal)
        root.addWidget(splitter, stretch=1)

        # Left: Calendar
        left = QWidget()
        llay = QVBoxLayout()
        left.setLayout(llay)
        self.calendar = QCalendarWidget()
        self.calendar.setGridVisible(True)
        self.calendar.selectionChanged.connect(self.on_date_selected)
        llay.addWidget(self.calendar)
        left_buttons = QHBoxLayout()
        self.prev_btn = QPushButton("◀ Prev Month")
        self.next_btn = QPushButton("Next Month ▶")
        self.today_btn = QPushButton("Today")
        left_buttons.addWidget(self.prev_btn)
        left_buttons.addWidget(self.today_btn)
        left_buttons.addWidget(self.next_btn)
        llay.addLayout(left_buttons)
        self.prev_btn.clicked.connect(lambda: self.calendar.showPreviousMonth())
        self.next_btn.clicked.connect(lambda: self.calendar.showNextMonth())
        self.today_btn.clicked.connect(lambda: self.calendar.setSelectedDate(QDate.currentDate()))

        splitter.addWidget(left)

        # Right: events list and controls
        right = QWidget()
        rlay = QVBoxLayout()
        right.setLayout(rlay)

        self.date_label = QLabel()
        self.date_label.setStyleSheet("font-weight:bold;")
        rlay.addWidget(self.date_label)

        self.events_list = QListWidget()
        self.events_list.itemDoubleClicked.connect(self.on_edit_event)
        rlay.addWidget(self.events_list, stretch=1)

        btns = QHBoxLayout()
        self.add_btn = QPushButton("➕ Add Event")
        self.edit_btn = QPushButton("✎ Edit Event")
        self.del_btn = QPushButton("🗑 Delete Event")
        self.export_btn = QPushButton("Export CSV")
        self.import_btn = QPushButton("Import JSON")
        btns.addWidget(self.add_btn)
        btns.addWidget(self.edit_btn)
        btns.addWidget(self.del_btn)
        btns.addWidget(self.export_btn)
        btns.addWidget(self.import_btn)
        rlay.addLayout(btns)

        control_row = QHBoxLayout()
        self.show_recurring_checkbox = QPushButton("Toggle recurring display")
        # simple toggle button behavior
        self.show_recurring_checkbox.setCheckable(True)
        self.show_recurring_checkbox.setChecked(True)
        control_row.addWidget(self.show_recurring_checkbox)
        control_row.addStretch()
        rlay.addLayout(control_row)

        splitter.addWidget(right)
        splitter.setStretchFactor(0, 60)
        splitter.setStretchFactor(1, 40)

        # connect buttons
        self.add_btn.clicked.connect(self.on_add_event)
        self.edit_btn.clicked.connect(self.on_edit_event)
        self.del_btn.clicked.connect(self.on_delete_event)
        self.export_btn.clicked.connect(self.on_export_csv)
        self.import_btn.clicked.connect(self.on_import_json)

        self.show_recurring_checkbox.toggled.connect(lambda _: self.refresh_events())

        # initial populate
        self.refresh_events()

    def selected_date(self):
        qd = self.calendar.selectedDate()
        return date(qd.year(), qd.month(), qd.day())

    def on_date_selected(self):
        self.refresh_events()

    def refresh_events(self):
        target = self.selected_date()
        self.date_label.setText(f"Events for {target.isoformat()}")
        self.events_list.clear()

        # gather events for date, considering recurrence toggle
        items = []
        for iso, evs in self.data.get("events", {}).items():
            for ev in evs:
                if occurs_on(ev, target):
                    # if recurrence and toggle off, skip
                    if not self.show_recurring_checkbox.isChecked() and ev.get("recurrence"):
                        # only show non-recurring if unchecked
                        if ev.get("recurrence"):
                            continue
                    items.append(ev)

        # sort by time/title
        items.sort(key=lambda e: (e.get("time") or "", e.get("title","").lower()))
        for ev in items:
            title = ev.get("title","(no title)")
            t = ev.get("time") or ""
            rec = ev.get("recurrence") or ""
            label = f"{t}  —  {title}" + (f"  ({rec})" if rec else "")
            it = QListWidgetItem(label)
            it.setData(Qt.UserRole, ev.get("id"))
            self.events_list.addItem(it)

    def find_event_by_id(self, eid):
        for iso, evs in self.data.get("events", {}).items():
            for ev in evs:
                if ev.get("id") == eid:
                    return ev, iso
        return None, None

    def on_add_event(self):
        default_qdate = QDate(self.selected_date().year, self.selected_date().month, self.selected_date().day) \
            if False else QDate.currentDate()
        dlg = EventDialog(self, event=None, default_date=self.calendar.selectedDate())
        if dlg.exec() == QDialog.Accepted:
            ev = dlg.result()
            if not ev.get("title"):
                QMessageBox.warning(self, "Empty title", "Please provide a title for the event.")
                return
            ev_id = str(uuid.uuid4())
            ev["id"] = ev_id
            # store under its start date iso
            iso = ev["date"]
            self.data.setdefault("events", {}).setdefault(iso, []).append(ev)
            save_events(self.data)
            self.refresh_events()

    def on_edit_event(self, *args):
        # either called from button or double-click; get selected item
        item = None
        if isinstance(args[0], QListWidgetItem):
            item = args[0]
        else:
            item = self.events_list.currentItem()
        if not item:
            QMessageBox.information(self, "Edit", "Select an event to edit.")
            return
        eid = item.data(Qt.UserRole)
        ev, iso = self.find_event_by_id(eid)
        if not ev:
            QMessageBox.warning(self, "Not found", "Event not found.")
            return
        dlg = EventDialog(self, event=ev)
        if dlg.exec() == QDialog.Accepted:
            new = dlg.result()
            if not new.get("title"):
                QMessageBox.warning(self, "Empty title", "Please provide a title.")
                return
            # update fields; if date changed, move to new iso key
            ev.update(new)
            # if moved date
            if ev.get("date") != iso:
                # remove from old list and push to new date
                try:
                    self.data["events"][iso] = [e for e in self.data["events"].get(iso, []) if e.get("id") != eid]
                    if not self.data["events"][iso]:
                        del self.data["events"][iso]
                except Exception:
                    pass
                self.data.setdefault("events", {}).setdefault(ev.get("date"), []).append(ev)
            save_events(self.data)
            self.refresh_events()

    def on_delete_event(self):
        item = self.events_list.currentItem()
        if not item:
            QMessageBox.information(self, "Delete", "Select an event to delete.")
            return
        eid = item.data(Qt.UserRole)
        ev, iso = self.find_event_by_id(eid)
        if not ev:
            QMessageBox.warning(self, "Not found", "Event not found.")
            return
        confirm = QMessageBox.question(self, "Delete Event", f"Delete '{ev.get('title')}'?", QMessageBox.Yes | QMessageBox.No)
        if confirm != QMessageBox.Yes:
            return
        # remove
        try:
            self.data["events"][iso] = [e for e in self.data["events"].get(iso, []) if e.get("id") != eid]
            if not self.data["events"][iso]:
                del self.data["events"][iso]
        except Exception:
            pass
        save_events(self.data)
        self.refresh_events()

    def on_export_csv(self):
        path, _ = QFileDialog.getSaveFileName(self, "Export events to CSV", str(SAVE_DIR / "events.csv"), "CSV files (*.csv)")
        if not path:
            return
        try:
            rows = []
            for iso, evs in self.data.get("events", {}).items():
                for ev in evs:
                    rows.append({
                        "id": ev.get("id"),
                        "title": ev.get("title"),
                        "date": ev.get("date"),
                        "time": ev.get("time",""),
                        "recurrence": ev.get("recurrence") or "",
                        "notes": ev.get("notes","")
                    })
            with open(path, "w", encoding="utf-8", newline='') as csvf:
                writer = csv.DictWriter(csvf, fieldnames=["id","title","date","time","recurrence","notes"])
                writer.writeheader()
                for r in rows:
                    writer.writerow(r)
            QMessageBox.information(self, "Exported", f"Events exported to:\n{path}")
        except Exception as e:
            QMessageBox.warning(self, "Export Failed", f"Failed to export CSV:\n{e}")

    def on_import_json(self):
        path, _ = QFileDialog.getOpenFileName(self, "Import events (JSON)", str(SAVE_DIR), "JSON files (*.json)")
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                newdata = json.load(f)
            # crude merge: append events from newdata if they have id or create id
            imported = 0
            for iso, evs in (newdata.get("events") or {}).items():
                for ev in evs:
                    if "id" not in ev:
                        ev["id"] = str(uuid.uuid4())
                    # ensure date present
                    if "date" not in ev:
                        ev["date"] = iso
                    self.data.setdefault("events", {}).setdefault(ev["date"], []).append(ev)
                    imported += 1
            save_events(self.data)
            QMessageBox.information(self, "Imported", f"Imported {imported} events.")
            self.refresh_events()
        except Exception as e:
            QMessageBox.warning(self, "Import Failed", f"Failed to import JSON:\n{e}")

    def search_events(self):
        q = self.search_input.text().strip().lower()
        if not q:
            self.refresh_events()
            return
        results = []
        for iso, evs in self.data.get("events", {}).items():
            for ev in evs:
                if q in (ev.get("title","").lower() + " " + (ev.get("notes","") or "").lower()):
                    results.append(ev)
        if not results:
            QMessageBox.information(self, "Search", "No events found.")
            return
        # show results in a temporary dialog list
        dlg = QDialog(self)
        dlg.setWindowTitle(f"Search results for '{q}'")
        layout = QVBoxLayout()
        listw = QListWidget()
        for ev in sorted(results, key=lambda e: (e.get("date",""), e.get("time",""), e.get("title",""))):
            listw.addItem(f"{ev.get('date')} {ev.get('time','')} — {ev.get('title')}")
        layout.addWidget(listw)
        btn = QPushButton("Close")
        btn.clicked.connect(dlg.accept)
        layout.addWidget(btn)
        dlg.setLayout(layout)
        dlg.exec()

# ---------------- Run ----------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = MiniCalendarApp()
    w.show()
    sys.exit(app.exec())

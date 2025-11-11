#!/usr/bin/env python3
"""
Mini Drawing / Pixel Art App (PySide6)
- Pixel canvas stored as QImage
- Pen / Eraser / Fill / Color picker
- Zoom, grid, save/load/export
"""

import sys
from pathlib import Path
import json

from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QSpinBox, QColorDialog, QFileDialog, QSlider, QMessageBox, QFrame
)
from PySide6.QtGui import QPainter, QColor, QImage, QMouseEvent, QPixmap
from PySide6.QtCore import Qt, QPoint

# ---------------- CONFIG / SAVE PATH ----------------
APP_NAME = "Mini Drawing"
SAVE_DIR = Path.home() / "Documents" / ".mgaio" / "Saves" / APP_NAME
PROJECTS_DIR = SAVE_DIR / "projects"
SAVE_DIR.mkdir(parents=True, exist_ok=True)
PROJECTS_DIR.mkdir(parents=True, exist_ok=True)

SETTINGS_FILE = SAVE_DIR / "settings.json"
DEFAULT_SETTINGS = {
    "canvas_w": 32,
    "canvas_h": 32,
    "zoom": 12,
    "primary_color": "#000000",
    "bg_color": "#ffffff",
    "show_grid": True
}

def load_settings():
    if SETTINGS_FILE.exists():
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                s = json.load(f)
            DEFAULT_SETTINGS.update(s)
        except Exception:
            pass
    return DEFAULT_SETTINGS.copy()

def save_settings(s):
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(s, f, indent=2)
    except Exception:
        pass

settings = load_settings()

# ---------------- Pixel Canvas Widget ----------------
class PixelCanvas(QFrame):
    def __init__(self, width=32, height=32, bg_color="#ffffff", parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.StyledPanel)
        self.canvas_w = max(1, int(width))
        self.canvas_h = max(1, int(height))
        self.bg_color = QColor(bg_color)
        self._create_image()
        self.zoom = int(settings.get("zoom", 12))
        self.show_grid = bool(settings.get("show_grid", True))

        # Tool state
        self.tool = "pen"   # 'pen' | 'eraser' | 'fill' | 'picker'
        self.brush_color = QColor(settings.get("primary_color", "#000000"))
        self.mouse_down = False
        self.last_pos = None

        # Widget behavior
        self.setMinimumSize(200, 200)
        self.setMouseTracking(True)

    def _create_image(self):
        # RGBA image
        self.image = QImage(self.canvas_w, self.canvas_h, QImage.Format_RGBA8888)
        self.image.fill(self.bg_color)

    def resize_canvas(self, w, h):
        w = max(1, int(w))
        h = max(1, int(h))
        new_img = QImage(w, h, QImage.Format_RGBA8888)
        new_img.fill(self.bg_color)
        # copy existing content into new image
        min_w = min(w, self.image.width())
        min_h = min(h, self.image.height())
        for y in range(min_h):
            for x in range(min_w):
                new_img.setPixelColor(x, y, self.image.pixelColor(x, y))
        self.canvas_w, self.canvas_h = w, h
        self.image = new_img
        self.update()

    def set_zoom(self, z):
        self.zoom = max(1, int(z))
        self.updateGeometry()
        self.update()

    def set_tool(self, tool):
        self.tool = tool

    def set_brush_color(self, qcolor):
        self.brush_color = qcolor

    def set_bg_color(self, qcolor):
        self.bg_color = qcolor
        # replace fully-transparent or bg pixels? For simplicity, fill background-only pixels
        for y in range(self.image.height()):
            for x in range(self.image.width()):
                pc = self.image.pixelColor(x, y)
                # if pixel exactly equals previous bg, update it
                if pc == self.bg_color:  # if same, no change
                    continue
        self.update()

    def paintEvent(self, ev):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor("#fafafa"))

        # draw image scaled-up
        img = self.image
        z = self.zoom
        target_w = img.width() * z
        target_h = img.height() * z

        # center canvas
        cx = max((self.width() - target_w) // 2, 0)
        cy = max((self.height() - target_h) // 2, 0)

        # draw each pixel as rectangle for crisp pixel art (avoid smooth scaling)
        for y in range(img.height()):
            for x in range(img.width()):
                c = img.pixelColor(x, y)
                if c.alpha() == 0:
                    # treat transparent as bg
                    painter.fillRect(cx + x*z, cy + y*z, z, z, self.bg_color)
                else:
                    painter.fillRect(cx + x*z, cy + y*z, z, z, c)

        # grid overlay
        if self.show_grid and z >= 4:
            pen = painter.pen()
            pen.setColor(QColor(200,200,200,160))
            pen.setWidth(1)
            painter.setPen(pen)
            # vertical lines
            for gx in range(img.width()+1):
                painter.drawLine(cx + gx*z, cy, cx + gx*z, cy + target_h)
            # horizontal lines
            for gy in range(img.height()+1):
                painter.drawLine(cx, cy + gy*z, cx + target_w, cy + gy*z)

        painter.end()

    def _pos_to_cell(self, pos: QPoint):
        z = self.zoom
        img = self.image
        target_w = img.width() * z
        target_h = img.height() * z
        cx = max((self.width() - target_w) // 2, 0)
        cy = max((self.height() - target_h) // 2, 0)

        x = (pos.x() - cx) // z
        y = (pos.y() - cy) // z
        if x < 0 or y < 0 or x >= img.width() or y >= img.height():
            return None
        return int(x), int(y)

    def mousePressEvent(self, ev: QMouseEvent):
        cell = self._pos_to_cell(ev.position().toPoint())
        if not cell:
            return
        x, y = cell
        self.mouse_down = True
        self.last_pos = (x, y)
        if self.tool == "pen":
            self.image.setPixelColor(x, y, self.brush_color)
            self.update()
        elif self.tool == "eraser":
            self.image.setPixelColor(x, y, self.bg_color)
            self.update()
        elif self.tool == "fill":
            target = self.image.pixelColor(x, y)
            if target != self.brush_color:
                self._flood_fill(x, y, target, self.brush_color)
                self.update()
        elif self.tool == "picker":
            picked = self.image.pixelColor(x, y)
            self.parent().on_color_picked(picked)  # notify parent
        ev.accept()

    def mouseMoveEvent(self, ev: QMouseEvent):
        if not self.mouse_down:
            return
        cell = self._pos_to_cell(ev.position().toPoint())
        if not cell:
            return
        x, y = cell
        if (x, y) == self.last_pos:
            return
        self.last_pos = (x, y)
        if self.tool == "pen":
            self.image.setPixelColor(x, y, self.brush_color)
            self.update()
        elif self.tool == "eraser":
            self.image.setPixelColor(x, y, self.bg_color)
            self.update()
        ev.accept()

    def mouseReleaseEvent(self, ev: QMouseEvent):
        self.mouse_down = False
        self.last_pos = None
        ev.accept()

    def _flood_fill(self, x, y, target_color: QColor, replacement_color: QColor):
        # iterative stack fill to avoid recursion limits
        w = self.image.width()
        h = self.image.height()
        target_rgba = target_color.rgba()
        rep_rgba = replacement_color.rgba()
        if target_rgba == rep_rgba:
            return
        stack = [(x,y)]
        while stack:
            cx, cy = stack.pop()
            try:
                pc = self.image.pixelColor(cx, cy)
            except Exception:
                continue
            if pc.rgba() != target_rgba:
                continue
            self.image.setPixelColor(cx, cy, replacement_color)
            if cx > 0: stack.append((cx-1, cy))
            if cx < w-1: stack.append((cx+1, cy))
            if cy > 0: stack.append((cx, cy-1))
            if cy < h-1: stack.append((cx, cy+1))

    # image save/load helpers
    def export_png(self, dest: Path):
        # save scaled-up as an image (preserve pixel art by saving original QImage scaled)
        # We'll save the raw image as PNG (original pixel dimensions) for editing; to export scaled image, use scaled().save()
        try:
            self.image.save(str(dest), "PNG")
            return True
        except Exception:
            return False

    def load_png(self, src: Path):
        if not src.exists():
            return False
        img = QImage(str(src))
        if img.isNull():
            return False
        # convert to our format and replace
        new_img = img.convertToFormat(QImage.Format_RGBA8888)
        self.canvas_w = new_img.width()
        self.canvas_h = new_img.height()
        self.image = new_img
        self.update()
        return True

# ---------------- Main Window ----------------
class MiniDrawingApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Mini Drawing / Pixel Art")
        self.setMinimumSize(760, 520)

        self.canvas = PixelCanvas(width=settings["canvas_w"], height=settings["canvas_h"], bg_color=settings["bg_color"], parent=self)
        self._build_ui()

    def _build_ui(self):
        main = QVBoxLayout()
        self.setLayout(main)

        # top controls
        top = QHBoxLayout()
        main.addLayout(top)

        # tool selector
        self.tool_combo = QComboBox()
        self.tool_combo.addItems(["pen", "eraser", "fill", "picker"])
        self.tool_combo.setCurrentText("pen")
        self.tool_combo.currentTextChanged.connect(self.on_tool_changed)
        top.addWidget(QLabel("Tool:"))
        top.addWidget(self.tool_combo)

        # color button
        self.color_btn = QPushButton("Primary Color")
        self.color_btn.clicked.connect(self.pick_color)
        self.color_display = QLabel()
        self.color_display.setFixedSize(28,28)
        self._update_color_display(self.canvas.brush_color)
        top.addWidget(self.color_btn)
        top.addWidget(self.color_display)

        # canvas size controls
        top.addWidget(QLabel("Canvas W:"))
        self.w_spin = QSpinBox()
        self.w_spin.setRange(1, 256)
        self.w_spin.setValue(self.canvas.canvas_w)
        top.addWidget(self.w_spin)

        top.addWidget(QLabel("H:"))
        self.h_spin = QSpinBox()
        self.h_spin.setRange(1, 256)
        self.h_spin.setValue(self.canvas.canvas_h)
        top.addWidget(self.h_spin)

        self.resize_btn = QPushButton("Resize")
        self.resize_btn.clicked.connect(self.resize_canvas)
        top.addWidget(self.resize_btn)

        # zoom slider
        top.addWidget(QLabel("Zoom:"))
        self.zoom_slider = QSlider(Qt.Horizontal)
        self.zoom_slider.setRange(4, 24)
        self.zoom_slider.setValue(self.canvas.zoom)
        self.zoom_slider.setFixedWidth(140)
        self.zoom_slider.valueChanged.connect(self.on_zoom_changed)
        top.addWidget(self.zoom_slider)

        # grid toggle
        self.grid_btn = QPushButton("Toggle Grid")
        self.grid_btn.setCheckable(True)
        self.grid_btn.setChecked(self.canvas.show_grid)
        self.grid_btn.clicked.connect(self.toggle_grid)
        top.addWidget(self.grid_btn)

        main.addWidget(self.canvas, stretch=1)

        # bottom actions
        bottom = QHBoxLayout()
        main.addLayout(bottom)

        self.new_btn = QPushButton("New")
        self.new_btn.clicked.connect(self.new_canvas)
        bottom.addWidget(self.new_btn)

        self.open_btn = QPushButton("Open")
        self.open_btn.clicked.connect(self.open_image)
        bottom.addWidget(self.open_btn)

        self.save_btn = QPushButton("Save Project")
        self.save_btn.clicked.connect(self.save_project)
        bottom.addWidget(self.save_btn)

        self.export_btn = QPushButton("Export PNG")
        self.export_btn.clicked.connect(self.export_png)
        bottom.addWidget(self.export_btn)

        self.clear_btn = QPushButton("Clear")
        self.clear_btn.clicked.connect(self.clear_canvas)
        bottom.addWidget(self.clear_btn)

    # UI callbacks
    def on_tool_changed(self, t):
        self.canvas.set_tool(t)

    def pick_color(self):
        c = QColorDialog.getColor(self.canvas.brush_color, self, "Pick Color")
        if c.isValid():
            self.canvas.set_brush_color(c)
            self._update_color_display(c)

    def _update_color_display(self, qcolor):
        pix = QPixmap(28,28)
        pix.fill(qcolor)
        self.color_display.setPixmap(pix)

    def resize_canvas(self):
        w = self.w_spin.value()
        h = self.h_spin.value()
        confirm = QMessageBox.question(self, "Resize Canvas",
                                       "Resizing will preserve top-left content and crop or pad the rest. Continue?",
                                       QMessageBox.Yes | QMessageBox.No)
        if confirm == QMessageBox.Yes:
            self.canvas.resize_canvas(w, h)
            settings["canvas_w"] = w
            settings["canvas_h"] = h
            save_settings(settings)

    def on_zoom_changed(self, v):
        self.canvas.set_zoom(v)
        settings["zoom"] = v
        save_settings(settings)

    def toggle_grid(self, _):
        self.canvas.show_grid = self.grid_btn.isChecked()
        settings["show_grid"] = self.canvas.show_grid
        save_settings(settings)
        self.canvas.update()

    def new_canvas(self):
        w = self.w_spin.value()
        h = self.h_spin.value()
        confirm = QMessageBox.question(self, "New Canvas", "Create new canvas? Unsaved changes will be lost.", QMessageBox.Yes | QMessageBox.No)
        if confirm != QMessageBox.Yes:
            return
        self.canvas.canvas_w = w
        self.canvas.canvas_h = h
        self.canvas._create_image()
        settings["canvas_w"] = w
        settings["canvas_h"] = h
        save_settings(settings)
        self.canvas.update()

    def open_image(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open Image", str(PROJECTS_DIR), "Images (*.png *.jpg *.bmp)")
        if not path:
            return
        ok = self.canvas.load_png(Path(path))
        if not ok:
            QMessageBox.warning(self, "Open Failed", "Failed to load image.")
        else:
            # update spin boxes
            self.w_spin.setValue(self.canvas.canvas_w)
            self.h_spin.setValue(self.canvas.canvas_h)

    def save_project(self):
        # save to projects dir with name input
        name, ok = QFileDialog.getSaveFileName(self, "Save Project (PNG)", str(PROJECTS_DIR / "untitled.png"), "PNG Files (*.png)")
        if not ok or not name:
            return
        dest = Path(name)
        if not dest.parent.exists():
            dest = PROJECTS_DIR / dest.name
        ok = self.canvas.export_png(dest)
        if ok:
            QMessageBox.information(self, "Saved", f"Project saved to:\n{dest}")
        else:
            QMessageBox.warning(self, "Save Failed", "Could not save project.")

    def export_png(self):
        # export scaled-up image for sharing (choose scale)
        fname, ok = QFileDialog.getSaveFileName(self, "Export PNG (recommended scale x8)", str(PROJECTS_DIR / "export.png"), "PNG Files (*.png)")
        if not ok or not fname:
            return
        # export raw pixel PNG (same as save_project). If user wants scaled export, we can scale.
        dest = Path(fname)
        # ask for scale maybe:
        scale, ok2 = QInputDialog.getInt(self, "Export scale", "Scale factor (integer):", 8, 1, 64)
        if not ok2:
            scale = 8
        # create scaled QImage
        scaled = self.canvas.image.scaled(self.canvas.image.width()*scale, self.canvas.image.height()*scale, Qt.IgnoreAspectRatio, Qt.FastTransformation)
        try:
            scaled.save(str(dest), "PNG")
            QMessageBox.information(self, "Exported", f"Exported PNG to:\n{dest}")
        except Exception as e:
            QMessageBox.warning(self, "Export Failed", f"Failed to export PNG:\n{e}")

    def clear_canvas(self):
        confirm = QMessageBox.question(self, "Clear Canvas", "Clear entire canvas?", QMessageBox.Yes | QMessageBox.No)
        if confirm != QMessageBox.Yes:
            return
        self.canvas._create_image()
        self.canvas.update()

    # Color picker callback from canvas
    def on_color_picked(self, qcolor: QColor):
        if qcolor is None:
            return
        self.canvas.set_brush_color(qcolor)
        self._update_color_display(qcolor)

# ---------------- Run ----------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = MiniDrawingApp()
    w.show()
    sys.exit(app.exec())

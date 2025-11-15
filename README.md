# 🎮 Minigames All-In-One Launcher

![MGAIO Main Window](https://raw.githubusercontent.com/ne0gl1tch20/Minigames-All-In-One/main/screenshots/MainWindow.png)
![Settings Window](https://raw.githubusercontent.com/ne0gl1tch20/Minigames-All-In-One/main/screenshots/SettingsWindow.png)

---

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/Python-3.12-blue)](https://www.python.org/)

**Version:** v0.3.0-alpha 🚀
**Status:** Pre-release ⚠️ – Early version for testing new features. Some bugs may exist...

---

## 🔹 Overview

Minigames All-In-One Launcher (MGAIO) is an **offline launcher for Python-based mini-games**. Manage, play, and track your games easily with features like:

* Dynamic game cards with launch, instructions, favorite toggle, and up/down ordering
* Recently Played & Recommended sections
* Save/restore game files
* Theming and UI customization
* Achievements and mini-rewards
* Batch installer to automatically set up Python & dependencies

---

## 📑 Documentation Tabs

### 📘 SDK Guide

* [SDKGuide.md](docs/SDKGuide.md) – Instructions on integrating new minigames and configuring the launcher.

### 📝 Changelog

* [CHANGELOG.md](docs/CHANGELOG.md) – Track updates, bug fixes, and new features in each version.

---

## 🕹️ Games Included

* Number Chain
* Coin Collector
* Snack Stack
* Type Rush
* Lizard Defender
* Clean Your Room
* Pixel Racer
* Color Slider
* Flappy Bird Clone
* Bubble Pop
* Lalalala Game
* Number Slider
* Word Scramble
* Pizza Panic
* Dodge The Blocks
* Ice Bath

### 🛠 Extra Apps

* Pomodoro ⏱️
* Task Manager 📝
* Eye Strain / 20-20-20 Reminder 👀
* Stretch / Micro Stretch 🧘
* Micro Meditate 🧘‍♂️
* Hydrate 💧
* Breathe 💨

---

## 🚀 Planned Future Games & Apps

### 🧠 Brain / Puzzle Games

* Color Maze – navigate mazes by color rules
* Sudoku Challenge – classic sudoku with daily challenges

### 🎯 Arcade / Action Games

* Space Blaster – shoot incoming aliens/obstacles
* Jumping Jack – endless platform runner
* Speed Clicker – click as fast as possible under timer
* Dodgeball Dash – avoid falling objects

### 🥶 Funny / Weird Games

* Hot Potato – pass the bomb by pressing keys
* Cat Cafe Simulator – manage cats & orders
* Ice Cream Rush – stack cones without dropping
* Lizard Escape – save lizards from pests
* Toilet Paper Challenge – stack rolls as high as possible

### 🛠 Future Apps / Tools

* 📊 **Mood Tracker & Focus Timer**
* 🔊 **Soundboard / Audio FX Lab**
* 🎹 **Mini Music Studio**
* 🏆 **Daily Challenge Hub**
* 🐾 **Virtual Pet Companion App**
* 🗂️ **Game Asset Organizer / Previewer**
* 🎲 **Randomizer & Idea Generator**
* 📈 **Offline Stats & Tracker Hub**

---

## 💻 Installation

1. **Download the repo using releases**:

```bash
https://github.com/ne0gl1tch20/Minigames-All-In-One/releases
```

2. **Run the batch installer** (Windows) to install Python, dependencies, and setup:

```bash
runit.bat
```

3. **Launch MGAIO**:

```bash
cd src/scripts
python main.py
```

---

## 📂 Directory Structure

```text
MGAIO/
├─ src/
│  ├─ scripts/
│  │  ├─ main.py             # Launcher entry point
│  │  └─ minigames/
│  │     ├─ Minigame1/
│  │     │  ├─ main.py       # Minigame entry
│  │     │  ├─ data/         # All assets here
│  │     │  │  ├─ sprites/
│  │     │  │  ├─ images/
│  │     │  │  ├─ music/
│  │     │  │  ├─ sound/
│  │     │  │  ├─ json/
│  │     │  │  └─ icon.ico
│  │     │  └─ config.json
│  │     └─ Minigame2/
│  │        └─ ...
├─ Documents/ (UserProfile)
│  └─ .mgaio/
│     ├─ Saves/               # Game save files
│     ├─ settingsave.json     # Launcher settings
│     └─ themesave.json       # Selected theme
├─ docs/
│  ├─ SDKGuide.md             # SDK / Integration guide
│  └─ CHANGELOG.md            # Version changelog
```

---

## 📧 Feedback & Suggestions

Have a **game suggestion, question, or just want to say hi?**
Use our dedicated suggestions email: [`python709853@gmail.com`](mailto:python709853@gmail.com)

---

## 💡 Tips & Tricks

* **Game Cards:** Launch quickly, mark favorites ❤️, and reorder with up/down arrows.
* **Recently Played:** Track progress and relaunch quickly.
* **Recommended Games:** Discover new games randomly.
* **Themes & UI:** Switch light/dark themes and customize colors.
* **Save & Restore:** Saves stored in `Documents/.mgaio/Saves`. Backup by copying this folder.
* **Settings:** Adjust volume, themes, and launcher preferences via `settingsave.json`.
* **Achievements & Rewards:** Earn mini-rewards and track progress.

---

## 🎨 Theme Customization

MGAIO supports **custom themes using QSS**. You can load your own `.qss` file to completely change the look of the launcher.

### 1️⃣ Using Preset Themes

* Go to **Settings → Theme & UI Customization**.
* Click on a preset theme (e.g., Dark, Light).
* Click **Apply/Save Settings** for changes to take effect.

### 2️⃣ Loading Your Own QSS

* Go to **Settings → Theme & UI Customization → Load Custom QSS**.
* Select a `.qss` file from your computer.
* Click **Apply/Save Settings** to apply it.

### 3️⃣ QSS Example

```css
/* =========================================
   MGAIO Launcher Black Theme QSS - Unified Gray
   File: src/data/themes/black.qss
   ========================================= */

/* QWidget - base background and font */
QWidget {
    background-color: #121212; /* dark background */
    color: #EEEEEE;           /* light text */
    font-family: "Segoe UI";
    font-size: 11pt;
}

/* QLineEdit - search bar */
QLineEdit {
    background-color: #2C2C2C;
    border: 1px solid #333333;
    border-radius: 6px;
    padding: 6px;
    selection-background-color: #444444;
    color: #EEEEEE;
}

/* QPushButton - all main buttons */
QPushButton {
    background-color: #2C2C2C;
    border: 1px solid #444444;
    border-radius: 6px;
    padding: 6px 12px;
    color: #EEEEEE;
}
QPushButton:hover { background-color: #3C3C3C; }
QPushButton:pressed { background-color: #555555; }

/* Scrollbar style */
QScrollBar:vertical {
    background: #2C2C2C;
    width: 12px;
}
QScrollBar::handle:vertical { background: #555555; border-radius: 6px; }
QScrollBar::handle:vertical:hover { background: #777777; }

/* Play button - yellow */
QPushButton#play_btn {
    background-color: #FFCC00;
    color: #000000;
    border-radius: 8px;
    font-weight: bold;
}
QPushButton#play_btn:hover { background-color: #FFE066; }
QPushButton#play_btn:pressed { background-color: #E6B800; }
```

### 4️⃣ Notes

* QSS changes **only apply after clicking Apply/Save** in the settings.
* You can combine JSON themes with a custom `.qss` for advanced styling.
* Experiment safely—make a copy of your current theme first!

---

## ⚡ License

MIT License – See [LICENSE](LICENSE) for details.

---

**Enjoy your games! 🎮 Have fun with Minigames All-In-One Launcher!**

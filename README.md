# 🎮 Minigames All-In-One Launcher

![MGAIO Main Window](https://raw.githubusercontent.com/ne0gl1tch20/Minigames-All-In-One/main/screenshots/MainWindow.png)
![Settings Window](https://raw.githubusercontent.com/ne0gl1tch20/Minigames-All-In-One/main/screenshots/SettingsWindow.png)

---

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/Python-3.12-blue)](https://www.python.org/)

**Version:** v0.2.7-alpha 🚀
**Status:** Pre-release ⚠️ – Early version for testing new features. Some bugs may exist.

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

## ⚡ License

MIT License – See [LICENSE](LICENSE) for details.

---

**Enjoy your games! 🎮 Have fun with Minigames All-In-One Launcher!**

# 🎮 Minigames All-In-One Launcher

![MGAIO Main Window](https://raw.githubusercontent.com/ne0gl1tch20/Minigames-All-In-One/main/screenshots/MainWindow.png)  
![Settings Window](https://raw.githubusercontent.com/ne0gl1tch20/Minigames-All-In-One/main/screenshots/SettingsWindow.png)  

---

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)  
[![Python Version](https://img.shields.io/badge/Python-3.12-blue)](https://www.python.org/)  

**Version:** v0.2.0-prerelease 🚀  
**Status:** Pre-release ⚠️ – This is an early version for testing new features. Some bugs may exist.

---

## 🔹 Overview

Minigames All-In-One Launcher (MGAIO) is an **offline launcher for Python-based mini-games**. Manage, play, and track your games easily with features like:

- Dynamic game cards with launch, instructions, favorite toggle, and up/down ordering  
- Recently Played & Recommended sections  
- Save/restore game files  
- Theming and UI customization  
- Achievements and mini-rewards  
- Batch installer to automatically set up Python & dependencies  

---

## 🕹️ Games Included

- Number Chain  
- Coin Collector  
- Snack Stack  
- Type Rush  
- Lizard Defender  
- Clean Your Room  
- Pixel Racer  
- Color Slider  
- Flappy Bird Clone  
- Bubble Pop  
- Lalalala Game  
- Number Slider  
- Word Scramble  
- Pizza Panic  
- Dodge The Blocks  
- Ice Bath  

### 🛠 Extra Apps

- Pomodoro  
- Task Manager  

---

## 🚀 Planned Future Games & Apps

### 🧠 Brain / Puzzle Games
- Math Mania – timed math puzzles  
- Word Ladder – change one letter at a time  
- Color Maze – navigate mazes by color rules  
- Sudoku Challenge – classic sudoku with daily challenges  
- Memory Vault – advanced memory matching  

### 🎯 Arcade / Action Games
- Space Blaster – shoot incoming aliens/obstacles  
- Jumping Jack – endless platform runner  
- Target Panic – hit moving targets fast  
- Speed Clicker – click as fast as possible under timer  
- Dodgeball Dash – avoid falling objects  

### 🥶 Funny / Weird Games
- Hot Potato – pass the bomb by pressing keys  
- Cat Cafe Simulator – manage cats & orders  
- Ice Cream Rush – stack cones without dropping  
- Lizard Escape – save lizards from pests  
- Toilet Paper Challenge – stack rolls as high as possible  

### 🛠 Future Apps / Tools
- Mini Calendar / Event Planner  
- Habit Tracker / Streaks App  
- Daily Challenges / Missions App  
- Custom Soundboard App  
- Mini Drawing / Pixel Art App  

---

## 💻 Installation

1. **Download the repo** or clone it:

```bash
git clone https://github.com/ne0gl1tch20/Minigames-All-In-One.git
````

2. **Run the batch installer** (Windows) to install Python, dependencies, and setup:

```bash
runit.bat
```

* Dependencies installed automatically: `pygame`, `librosa`, `PySide6`, `numpy`
* Python 3.12 is recommended if not installed

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
│  │  ├─ main.py           # Launcher entry point
│  │  └─ minigames/        # All minigame folders live here
│  │     ├─ Game1/
│  │     │  ├─ main.py
│  │     │  ├─ config.json
│  │     │  └─ icon.ico
│  │     └─ ...
├─ Documents/ (UserProfile)
│  └─ .mgaio/
│     ├─ Saves/             # Game save files
│     ├─ settingsave.json   # Launcher settings
│     └─ themesave.json     # Selected theme
```

---

## 📧 Feedback & Suggestions

Have a **game suggestion, question, or just want to say hi?**
Use our dedicated suggestions email (keeps personal inbox untouched): [`python709853@gmail.com`](mailto:python709853@gmail.com)

---

## ⚡ License

MIT License – See [LICENSE](LICENSE) for details.

---

**Enjoy your games! 🎮 Have fun with Minigames All-In-One Launcher!**
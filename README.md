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

## 💡 Tips & Tricks

Make the most out of your Minigames All-In-One Launcher with these handy tips:

### 🎮 Game Cards
- **Launch Quickly:** Click the game icon or “Play” button to start instantly.  
- **Favorites:** Click the heart ❤️ on a game card to add it to your favorites section for quick access.  
- **Ordering:** Use the up/down arrows on the game cards to arrange them to your liking.

### 🕒 Recently Played
- **Track Your Progress:** The “Recently Played” section shows the last few games you opened. Perfect if you switch between multiple games.  
- **Quick Relaunch:** Click a game in this section to jump straight back into your last session.

### 🌟 Recommended Games
- **Discover New Fun:** This section shuffles your games randomly to suggest what to play next.  
- **Try Everything:** Keep the fun fresh by letting the launcher recommend games you haven’t played in a while.

### 🎨 Themes & UI
- **Customize Appearance:** Change themes and colors in the Settings window to suit your mood.  
- **Light & Dark Modes:** Switch between light and dark themes for day or night gaming.

### 💾 Save & Restore
- **Never Lose Progress:** Your game saves are stored in `Documents/.mgaio/Saves`. Each game’s progress is kept separately.  
- **Backup Your Saves:** Copy the Saves folder if you want to transfer your progress to another PC.

### ⚙️ Settings
- **Batch Installer:** Use `runit.bat` to quickly install Python & dependencies.  
- **Adjust Game Volume:** Individual minigames may have sound settings in the config.json file.  
- **Launcher Settings:** Modify themes, recent/recommended game display, and other launcher preferences via `settingsave.json`.

### 🏆 Achievements & Rewards
- **Earn Coins & Badges:** Many minigames have mini-rewards. Check each game’s instructions for ways to earn them.  
- **Track Your Progress:** Achievements may unlock special items or features in future updates.

---

**Pro Tip:** Combine “Favorites” with “Recently Played” to quickly access your top games without scrolling endlessly. 🎮

---

## ⚡ License

MIT License – See [LICENSE](LICENSE) for details.

---

**Enjoy your games! 🎮 Have fun with Minigames All-In-One Launcher!**
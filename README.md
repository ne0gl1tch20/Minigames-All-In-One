# MGAIO Launcher

**Minigames All-In-One Launcher** built with Python and PySide6. 🎮✨

Organize, launch, and manage all your minigames from a single interactive application. MGAIO supports themes, game descriptions, achievements, app lock, and a polished UI experience.

---

## Features

### 🎴 Dynamic Game Cards

Each minigame is displayed as an animated card with:

* Icon & title
* Short description
* "Play" button
* "How to Play" instructions
* Optional version info (`version` in `config.json`)

### 🎨 Theme Support

Switch between multiple themes:

* Default
* Light
* Dark

Themes are saved in your settings and applied automatically on next launch.

### 🔒 App Lock

Secure your launcher with a password to prevent unauthorized access.

### ⚙️ Settings Management

* Backup and restore settings via JSON
* Track recently played games
* Coin / mini reward system for game play

### 📜 Resizable & Scrollable UI

* Browse your games with smooth vertical scrolling
* Animated hover effects for an interactive feel
* Grid or list layout planned for future updates

### 🛠️ PyInstaller Ready

* Works both in development (Python) and packaged as an executable
* Game saves and settings stored in `Documents/.mgaio/` by default
* Auto-detects minigames folder and icons

### 🏆 Achievements & Rewards

* First play, 5 plays, 10 plays
* Mini reward system: earn coins per game
* Optional in-game achievement tracking

---

## 📦 Installation

1. Download through Releases page:
- After you download through Releases page, unzip it.

```link
https://github.com/ne0gl1tch20/Minigames-All-In-One
```

2. Download Python 3.10+:
- You can skip this step if you already installed it.

```link
https://www.python.org/downloads/
```

3. After you installed **Python**, Open **Command Prompt** and install dependencies:
- You can skip this step if you already installed the dependencies.

```bash
pip install PySide6 pygame librosa numpy
```

4. Run the launcher:
- This depends on where is the script.

```bash
python src/scripts/main.py
```

> The launcher automatically detects all minigames in the `minigames/` folder.

---

## 📂 Directory Structure

```
MGAIO/
├─ src/
│  ├─ scripts/
│  │  └─ main.py          # Launcher script
├─ minigames/             # Each minigame folder here
│  ├─ Game1/
│  │  ├─ main.py
│  │  ├─ config.json      # Optional: title, description, how_to_play
│  │  └─ icon.ico
│  └─ Game2/
├─ Documents/
   └─ .mgaio/
      ├─ Saves/           # Game save files
      ├─ settingsave.json # Launcher settings
      └─ themesave.json   # Selected theme
```

---

## 📝 Game Card Config (`config.json`)

Optional configuration file for each minigame:

```json
{
  "title": "Game Title",
  "description": "Short game description",
  "how_to_play": "Instructions for the player",
  "version": "1.0.0"
}
```

> If `config.json` is missing, the launcher uses the folder name as the game title and shows a default card.

---

## 🚀 Running Games

* The launcher will run games directly via Python.
* Example:

```bash
python minigames/Game1/main.py
```

* If a game doesn’t have `main.py`, the launcher will show a warning instead of crashing.

---

## 📌 Notes

* Compatible with **Python 3.10+**
* Saves and settings are stored under `Documents/.mgaio/`
* Supports hover animations, shadows, and interactive UI elements
* Automatically ensures required libraries (`librosa`, `pygame`, `PySide6`, `numpy`) are installed

---

## 🌟 Planned Future Features (if it's compatible)

* Search & filter games
* Favorites / pinned games
* Recently played section
* Grid/List view toggle
* Game stats & achievements
* Drag-and-drop game reordering
* Background music and UI sounds
* Error logging & crash recovery
* Optional EXE compilation for each game

---

## 📜 License

MIT License – free to modify and distribute.

---

**Enjoy your games!** 🎮🚀
MGAIO – your all-in-one Python minigame launcher.

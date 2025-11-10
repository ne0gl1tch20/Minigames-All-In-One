# MGAIO Launcher

**Minigames All-In-One Launcher** built with Python and PySide6. 🎮✨

Organize, launch, and manage all your minigames from a single interactive application. MGAIO now supports **full favorites filtering**, **game saves backup/restore**, **typed reset confirmations**, and a polished UI experience.

---

## Features

### 🎴 Dynamic Game Cards

Each minigame is displayed as an animated card with:

* Icon & title
* Short description
* "Play" button
* "How to Play" instructions
* Optional version info (`version` in `config.json`)
* ⭐ Mark/unmark as favorite, with full launcher-wide filtering

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
* Full **game saves backup & restore** for all minigames in `Documents/.mgaio/Saves/`
* Reset settings with **typed confirmation** to prevent accidental data loss
* Track recently played games
* Coin / mini reward system for gameplay

### 📜 Resizable & Scrollable UI

* Browse your games with smooth vertical scrolling
* Animated hover effects for an interactive feel
* Grid or list layout with adjustable columns
* Favorites filter toggle: show only favorited games

### 🛠️ PyInstaller Ready

* Works both in development (Python) and packaged as an executable
* Game saves and settings stored in `Documents/.mgaio/` by default
* Auto-detects minigames folder and icons

### 🏆 Achievements & Rewards

* First play, 5 plays, 10 plays
* Mini reward system: earn coins per game
* Optional in-game achievement tracking

### 💾 Backup / Restore

* **Backup all game saves** to a ZIP
* **Restore all game saves** from a ZIP
* Backup & restore launcher settings via JSON
* Clear game cache safely

### 📷 Screenshots

![Main Window](https://github.com/ne0gl1tch20/Minigames-All-In-One/tree/main/screenshots/MainWindow.png)

![Settings Window](https://github.com/ne0gl1tch20/Minigames-All-In-One/tree/main/screenshots/SettingsWindow.png)

---

## 📦 Installation

1. Download through Releases page:

```text
https://github.com/ne0gl1tch20/Minigames-All-In-One/Releases
```

2. Download Python 3.10+ if needed:

```text
https://www.python.org/downloads/
```

3. Run this file:
- The file will do it for you to launch the launcher.
```runit.bat``

> The launcher automatically detects all minigames in the `minigames/` folder.

---

## 📂 Directory Structure

```
MGAIO/
├─ src/
│  ├─ scripts/
│  │  ├─ main.py           # Launcher/game entry point
│  │  └─ minigames/        # All individual game folders live here
│  │     ├─ Game1/
│  │     │  ├─ main.py
│  │     │  ├─ config.json
│  │     │  └─ icon.ico
│  │     ├─ Game2/
│  │     │  ├─ main.py
│  │     │  ├─ config.json
│  │     │  └─ icon.ico
│  │     └─ ...            # Other games
└─ %USERPROFILE%/Documents/
   └─ .mgaio/
      ├─ Saves/             # Game save files (backed up/restored via launcher)
      ├─ settingsave.json   # Launcher settings
      ├─ recently_played.json  # Recently played games timestamps
      └─ game_meta_cache.json # Cached minigame metadata
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

* If a game doesn’t have `main.py`, the launcher shows a warning instead of crashing.

---

## ⚠️ Danger Features

* Reset to default **requires typing `RESET`** to confirm.
* Backup & restore all saves before performing destructive actions.
* Clear cache safely with confirmation prompts.

---

## 🌟 Planned Future Features

* Confidental!!

---

## 📜 License

MIT License – free to modify and distribute.

---

**Enjoy your games safely!** 🎮🚀
MGAIO – your all-in-one Python minigame launcher.


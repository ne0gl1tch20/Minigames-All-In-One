# MGAIO Launcher

**Minigames All-In-One Launcher** built with Python and PySide6. 🎮✨

This launcher allows you to organize, launch, and manage multiple minigames from a single application. It supports themes, app lock, game descriptions, and a visually interactive UI.

---

## Features

* **Dynamic Game Cards**
  Each minigame is displayed as an animated card with:

  * Icon & title
  * Game description
  * "Play" button
  * "How to Play" instructions

* **Theme Support**
  Switch between default, light, and dark themes. Themes are saved in your settings.

* **App Lock**
  Set a password to lock the launcher for privacy and security.

* **Settings Management**
  Backup and restore your launcher settings via JSON.

* **Resizable & Scrollable UI**
  Supports vertical scrolling to browse your games, with animated hover effects.

* **PyInstaller Ready**
  Works both in development and as a packaged executable. Saves are stored in the user's Documents folder.

---

## Installation

1. **Clone the repository:**

```bash
git clone https://github.com/ne0gl1tch20/Minigames-All-In-One.git
cd Minigames-All-In-One
```

2. **Install dependencies:**

```bash
pip install PySide6
```

3. **Run the launcher:**

```bash
python src/scripts/main.py
```

> If you plan to package it with PyInstaller, the launcher automatically detects the minigames folder and saves settings in the user’s Documents.

---

## Directory Structure

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

## Game Card Config (`config.json`)

Optional JSON file for each minigame:

```json
{
  "title": "Game Title",
  "description": "Short game description",
  "how_to_play": "Instructions for the player",
  "version": "1.0.0"
}
```

---

## Notes

* The launcher works in **dev mode** or as a **PyInstaller executable**.
* All saves and settings are stored under `Documents/.mgaio/`.
* Hover animations, shadows, and UI polish enhance the user experience.
* If `main.py` is missing from a minigame, the launcher shows a warning instead of crashing.

---

## Future Features (Planned)

* Search & filter games
* Favorites / pinned games
* Recently played section
* Grid/List view toggle
* Game stats & achievements
* Drag-and-drop reordering
* Background music and UI sounds
* Error logging & crash recovery

---

## License

MIT License – feel free to modify and distribute!

---

**Enjoy your games!** 🎮🚀

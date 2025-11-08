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

[Releases](<https://github.com/ne0gl1tch20/Minigames-All-In-One>)
# 🎮 Minigames All-In-One SDK Guide

Want to make your **own minigame** for the Minigames All-In-One Launcher? This guide will walk you through creating, configuring, and submitting your game.  

---

## 🔹 Step 0: Download Base Minigame Kit

Before creating your own game, make sure to download the **Base Minigame Kit** from this repository.  

- This kit contains a **template folder**, pre-configured `main.py`, `config.json`, and a sample `icon.ico`.  
- Using the kit ensures your game is **launcher-compatible** and helps you get started quickly.  

> 📥 **Download here:** [BaseMinigameKit.zip]()

---

## 🔹 Minigame Folder Structure

Every minigame lives in its own folder inside `src/scripts/minigames/`. The basic structure looks like this:

```text
MinigameName/
├─ main.py         # The main Python script that runs your game
├─ config.json     # Configuration and metadata for your game
└─ icon.ico        # Icon that appears in the launcher
````

> ✅ Tip: Keep the folder name unique and descriptive. This name will appear in the launcher unless overridden in `config.json`.

---

## 📝 Config.json

Your `config.json` defines how your game is displayed in MGAIO. Here’s an example:

```json
{
  "title": "Minigame SDK",
  "description": "A fun little game where you click as fast as possible to earn points.",
  "how_to_play": "1. Press Play to start the game.\n2. Click on targets as quickly as you can.\n3. Each hit gives points.\n4. Avoid missing targets.\n5. Try to beat your high score!\n\nTips:\n- Focus on the center of the screen.\n- Stay calm and do not rush.",
  "tags": ["Clicker","Arcade","Fast-Paced"],
  "author": "G0ldNe0",
  "version": "1.0.0",
  "release_date": "2025-11-10"
}
```

### 🔹 Fields Explained

| Field          | Description                                  |
| -------------- | -------------------------------------------- |
| `title`        | Name of your minigame as it appears in MGAIO |
| `description`  | Short summary of your game                   |
| `how_to_play`  | Instructions & tips for players              |
| `tags`         | Categories for search/filter in the launcher |
| `author`       | Your name or handle                          |
| `version`      | Game version                                 |
| `release_date` | YYYY-MM-DD format of release                 |

---

## 🕹 main.py

* This is where your game logic goes.
* Must be executable via `python main.py` in the game folder.
* Recommended: use `pygame` or other lightweight Python libraries compatible with MGAIO.
* Avoid heavy dependencies for smooth offline play.

> 💡 Tip: You can include sounds, images, and save files within your minigame folder. Keep all assets relative to `main.py` for portability.

---

## 🖼 icon.ico

* This icon represents your game in the launcher.
* Recommended size: **64x64** or **128x128 px**.
* Use `.ico` format for compatibility.

---

## 📂 MGAIO Directory Reference

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

## 📧 Submitting Your Game

We love community contributions! To submit your game:

1. Zip your minigame folder (include `main.py`, `config.json`, `icon.ico`, and any assets).
2. Email it to: [`python709853@gmail.com`](mailto:python709853@gmail.com)
3. Include a short description and your preferred author name.

> ✅ Make sure your game works offline and all paths are relative so it runs on any computer.

---

**Pro Tip:** Test your game locally by running `python main.py` inside the folder before submitting. This ensures the launcher can execute it without issues.

**Happy coding! 🎮 Bring your ideas to life in Minigames All-In-One!**
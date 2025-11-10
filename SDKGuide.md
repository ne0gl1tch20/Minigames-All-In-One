# 🎮 Minigames All-In-One SDK Guide

Want to make your **own minigame** for the Minigames All-In-One Launcher? This guide will walk you through creating, configuring, and submitting your game.  

---

## 🔹 Step 0: Download Base Minigame Kit

Before creating your own game, make sure to download the **Base Minigame Kit** from this repository.  

- This kit contains a **template folder**, pre-configured `main.py`, `config.json`, and a sample `icon.ico`.  
- Using the kit ensures your game is **launcher-compatible** and helps you get started quickly.  

> 📥 **Download here:** [BaseMinigameKit.zip](https://github.com/ne0gl1tch20/Minigames-All-In-One/tree/main/BaseMinigameKit/BaseMinigameKit.zip)

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

## 🎨 Designing Your Game

* **Keep it simple:** Short, focused gameplay works best in MGAIO.
* **Visual clarity:** Ensure buttons, sprites, and text are easy to see.
* **Consistent theme:** Colors, fonts, and UI elements should match your game style.
* **Accessible controls:** Use intuitive keyboard and/or mouse input.

---

## 🔊 Adding Sound & Music

* Place all sound effects and music **inside your minigame folder**.
* Load audio using **relative paths**, e.g.,

  ```python
  sound = pygame.mixer.Sound("click.wav")
  ```
* Keep sounds **short and non-intrusive**.
* Optional: implement a **toggle sound** feature in-game.

---

## 💾 Saving Progress

* Follow the launcher’s save structure:

  * **Local:** `Documents/.mgaio/Saves/GameName/`
  * **Shared:** `Documents/.mgaio/Saves/Shared/`
* Use **JSON** for storing player progress.
* Never write outside your minigame folder or the designated save paths.

---

## 🕹 Game Loop Tips

* Maintain a **stable frame rate** (30–60 FPS recommended).
* Avoid blocking calls; prefer **timers or events** to keep UI responsive.
* Use **event-driven logic** instead of infinite loops when possible.

---

## 🧪 Debugging & Testing

* Run `python main.py` multiple times to catch crashes.
* Test all features: gameplay, save/load, coins, sounds, and settings.
* Verify **path independence**: move the folder to another directory and ensure it still works.

---

## 🌐 Optional Features

* **Leaderboard support:** Store high scores or coins in the Shared stats JSON.
* **Achievements:** Implement unlockable milestones saved in JSON.
* **Settings menu:** Allow players to toggle sound, difficulty, or themes.

---

## 💡 Pro Tips

* Name sprites, sounds, and variables **clearly**.
* Comment your code for **future reference**.
* Design your game for **short sessions** (1–5 minutes) for quick play.
* Avoid hardcoding paths; always use:

  ```python
  Path(__file__).parent
  ```

  for assets and saves.

## 📏 Rules for Making a Minigame

To keep MGAIO smooth, fun, and consistent, all community games must follow these rules:

### 1️⃣ General Guidelines

* Your game **must run offline** without requiring internet access.
* All **assets must be included** in the game folder (images, sounds, etc.).
* Keep your **folder and file names simple and unique**. Avoid spaces; use underscores `_` instead.
* Avoid **external heavy dependencies**; use standard Python libraries or `pygame`/`PySide6`.

### 2️⃣ Code Rules

* `main.py` **must be executable** via `python main.py` inside the game folder.
* The script **cannot modify files outside its own folder** except for designated save paths (`Documents/.mgaio/Saves`).
* Avoid global modifications that affect the launcher or other games.
* Use **relative paths** for all assets and save files.

### 3️⃣ Launcher Integration

* Include a **valid `config.json`** describing the game (title, description, how_to_play, tags, author, version, release_date).
* Include a **launcher icon (`icon.ico`)** for easy recognition.
* Optional: Implement a **high score / coins system** using `Documents/.mgaio/Saves/Shared/`.

### 4️⃣ Content Rules

* Games must be **family-friendly**: no NSFW, violence beyond cartoon/funny levels, or offensive content.
* No malware, adware, or hidden scripts.
* Sound effects and visuals should **not be excessively loud or flashy** to avoid discomfort.

### 5️⃣ Testing

* Always **test your game locally** before submitting.
* Ensure that:

  * It starts correctly via `python main.py`.
  * All assets load properly.
  * Save files are created and read in the proper save folder.
  * Coins / scores work correctly if implemented.

### 6️⃣ Submission Rules

* Submit only **zipped folders** with `main.py`, `config.json`, `icon.ico`, and all assets.
* Include a **short author note** or description.
* Make sure your game is **compatible with Windows** (cross-platform optional, but test first).

> ⚡ Tip: Follow these rules strictly! Games that break rules may not be accepted into MGAIO.

## 📧 Submitting Your Game

We love community contributions! To submit your game:

1. Zip your minigame folder (include `main.py`, `config.json`, `icon.ico`, and any assets).
2. Email it to: [`python709853@gmail.com`](mailto:python709853@gmail.com)
3. Include a short description and your preferred author name.

> ✅ Make sure your game works offline and all paths are relative so it runs on any computer.

---

**Pro Tip:** Test your game locally by running `python main.py` inside the folder before submitting. This ensures the launcher can execute it without issues.

**Happy coding! 🎮 Bring your ideas to life in Minigames All-In-One!**
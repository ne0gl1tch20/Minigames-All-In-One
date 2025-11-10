"""
Number Chain Minigame (Pygame)
Title: Number Chain
Description: Click numbers in ascending order as fast as possible!
Features:
- Start Menu / Settings / Leaderboard (JSON)
- Saveable settings and leaderboard
- Keyboard + Joystick support
- Particle system (visual flair)
- Procedural sound effects (no external files)
Requirements:
pip install pygame
Run:
python number_chain.py
"""

import pygame
import sys
import json
import os
import math
import random
import time
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict

# ------------------- CONFIG / SAVE PATH -------------------
USER_DIR = os.path.expandvars(r"%userprofile%")
MG_SAVE_DIR = Path(USER_DIR) / "Documents" / ".mgaio"
APP_NAME = "Number Chain"
SAVE_FOLDER = MG_SAVE_DIR / "Saves" / APP_NAME
SAVE_FOLDER.mkdir(parents=True, exist_ok=True)

SETTINGS_FILE = SAVE_FOLDER / "settings.json"
LEADERBOARD_FILE = SAVE_FOLDER / "leaderboard.json"

DEFAULT_SETTINGS = {
    "volume": 100,
    "sound": True,
    "difficulty": "normal",  # "easy", "normal", "hard"
    "keymap": {"action": pygame.K_RETURN},
    "joymap": {"action": {"type": "button", "id": 0}},
}
DEFAULT_LEADERBOARD: List[Dict] = []

def load_json(path: Path, default):
    if path.exists():
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return default

def save_json(path: Path, data):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print("Save failed:", e)

# ------------------- PARTICLE / HELPER -------------------
@dataclass
class Particle:
    x: float
    y: float
    vx: float
    vy: float
    life: float
    size: float
    color: tuple

# ------------------- BASE MINIGAME (adapted) -------------------
class BaseMinigame:
    WIDTH, HEIGHT = 800, 600
    FPS = 60

    def __init__(self):
        pygame.init()
        # try init mixer
        self.mixer_available = True
        try:
            pygame.mixer.init()
        except Exception as e:
            print("Audio init failed:", e)
            self.mixer_available = False

        pygame.joystick.init()
        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT))
        pygame.display.set_caption(APP_NAME)
        self.clock = pygame.time.Clock()
        self.font_big = pygame.font.SysFont("arial", 48, bold=True)
        self.font_med = pygame.font.SysFont("arial", 24)
        self.font_sm = pygame.font.SysFont("arial", 18)

        # Load settings / leaderboard
        self.settings = load_json(SETTINGS_FILE, DEFAULT_SETTINGS.copy())
        for k, v in DEFAULT_SETTINGS.items():
            self.settings.setdefault(k, v)
        self.leaderboard = load_json(LEADERBOARD_FILE, DEFAULT_LEADERBOARD.copy())

        # Game state
        # states: "menu", "settings", "leaderboard", "playing", "gameover"
        self.state = "menu"
        self.running = True
        self.particles: List[Particle] = []
        self.score = 0
        self.player_name = "Player"

        # Joystick
        self.joystick = None
        self.detect_joystick()

        # create sounds
        self.sounds: Dict[str, pygame.mixer.Sound] = {}
        if self.mixer_available:
            self._create_sounds()
            self._apply_volume_to_sounds()

    # ---------- joystick ----------
    def detect_joystick(self):
        if pygame.joystick.get_count() > 0:
            js = pygame.joystick.Joystick(0)
            js.init()
            self.joystick = js
            print("Joystick detected:", js.get_name())

    # ---------- sound helpers ----------
    def _create_sounds(self):
        """Create small procedural sounds and store as pygame.mixer.Sound objects."""
        try:
            sample_rate = 22050
            defs = {
                "select": (660, 0.06),
                "start": (880, 0.12),
                "action": (1200, 0.05),
                "cancel": (220, 0.08),
                "error": (160, 0.12),
                "correct": (1000, 0.06),
                "complete": (1500, 0.16),
            }
            for name, (hz, dur) in defs.items():
                n_samples = int(sample_rate * dur)
                buf = bytearray()
                max_amp = 127
                for i in range(n_samples):
                    t = i / sample_rate
                    env = 1.0 - (i / n_samples)
                    v = int(max_amp * math.sin(2 * math.pi * hz * t) * env)
                    buf.append(v + 128)
                try:
                    snd = pygame.mixer.Sound(buffer=bytes(buf))
                    self.sounds[name] = snd
                except Exception as e:
                    print(f"Failed to create sound {name}:", e)
            for k in defs.keys():
                self.sounds.setdefault(k, None)
        except Exception as e:
            print("Error creating sounds:", e)
            self.sounds = {}

    def _apply_volume_to_sounds(self):
        vol = max(0.0, min(1.0, float(self.settings.get("volume", 100)) / 100.0))
        for s in self.sounds.values():
            if s:
                try:
                    s.set_volume(vol)
                except Exception:
                    pass

    def play_sound(self, name: str):
        if not self.mixer_available:
            return
        if not self.settings.get("sound", True):
            return
        s = self.sounds.get(name)
        if s:
            try:
                s.play()
            except Exception:
                pass

    # ---------- game logic hooks ----------
    def update_game(self, dt):
        pass

    def handle_input(self, key=None, joy_event=None):
        if key == self.settings["keymap"].get("action"):
            self.play_sound("action")

    def emit_particle(self, x, y, color=(255, 200, 60), amount=8):
        for _ in range(amount):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(40, 220)
            p = Particle(
                x=x,
                y=y,
                vx=math.cos(angle) * speed,
                vy=math.sin(angle) * speed,
                life=random.uniform(0.5, 1.2),
                size=random.uniform(2, 6),
                color=color
            )
            self.particles.append(p)

    # ---------- main loop ----------
    def run(self):
        # ensure leaderboard file exists on start
        if not Path(LEADERBOARD_FILE).exists():
            save_json(Path(LEADERBOARD_FILE), self.leaderboard)
        while self.running:
            dt = self.clock.tick(self.FPS) / 1000.0
            self.handle_events()
            if self.state == "playing":
                self.update_game(dt)
            self.update_particles(dt)
            self.render()
        pygame.quit()
        sys.exit()

    # ---------- event handling ----------
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            # Keyboard controls
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.state in ("settings", "leaderboard"):
                        self.state = "menu"
                        self.play_sound("cancel")
                    elif self.state == "playing":
                        self.state = "menu"
                        self.play_sound("cancel")
                    else:
                        if self.state == "menu":
                            self.play_sound("cancel")
                            self.running = False

                elif self.state == "menu":
                    if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                        self.play_sound("start")
                        self.start_play()
                    elif event.key == pygame.K_s:
                        self.play_sound("select")
                        self.state = "settings"
                    elif event.key == pygame.K_l:
                        self.play_sound("select")
                        self.state = "leaderboard"

                elif self.state == "settings":
                    if event.key == pygame.K_SPACE:
                        cur = self.settings.get("sound", True)
                        self.settings["sound"] = not cur
                        save_json(SETTINGS_FILE, self.settings)
                        self.play_sound("select" if self.settings["sound"] else "cancel")
                    elif event.key == pygame.K_UP:
                        self.settings["volume"] = min(100, self.settings.get("volume", 100) + 5)
                        self._apply_volume_to_sounds()
                        save_json(SETTINGS_FILE, self.settings)
                        self.play_sound("select")
                    elif event.key == pygame.K_DOWN:
                        self.settings["volume"] = max(0, self.settings.get("volume", 100) - 5)
                        self._apply_volume_to_sounds()
                        save_json(SETTINGS_FILE, self.settings)
                        self.play_sound("select")

                elif self.state == "playing":
                    self.handle_input(event.key)

            elif event.type in (pygame.JOYBUTTONDOWN, pygame.JOYAXISMOTION):
                if self.state == "playing":
                    self.handle_input(joy_event=event)

            elif event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos
                if self.state == "menu":
                    start_rect = pygame.Rect(self.WIDTH//2 - 140, 240, 280, 44)
                    settings_rect = pygame.Rect(self.WIDTH//2 - 140, 300, 280, 44)
                    leader_rect = pygame.Rect(self.WIDTH//2 - 140, 360, 280, 44)
                    if start_rect.collidepoint(mx, my):
                        self.play_sound("start")
                        self.start_play()
                    elif settings_rect.collidepoint(mx, my):
                        self.play_sound("select")
                        self.state = "settings"
                    elif leader_rect.collidepoint(mx, my):
                        self.play_sound("select")
                        self.state = "leaderboard"

    # ---------- particles ----------
    def update_particles(self, dt):
        for p in list(self.particles):
            p.x += p.vx * dt
            p.y += p.vy * dt
            p.vy += 300 * dt
            p.life -= dt
            if p.life <= 0:
                self.particles.remove(p)

    # ---------- rendering ----------
    def render_particles(self):
        for p in self.particles:
            alpha = max(0, min(255, int(255 * p.life)))
            surf = pygame.Surface((int(p.size*2), int(p.size*2)), pygame.SRCALPHA)
            pygame.draw.circle(surf, (*p.color, alpha), (int(p.size), int(p.size)), int(p.size))
            self.screen.blit(surf, (int(p.x - p.size), int(p.y - p.size)))

    def render(self):
        self.screen.fill((12, 12, 12))
        if self.state == "menu":
            self.draw_menu()
        elif self.state == "playing":
            self.draw_game()
        elif self.state == "settings":
            self.draw_settings()
        elif self.state == "leaderboard":
            self.draw_leaderboard()
        elif self.state == "gameover":
            self.draw_gameover()
        self.render_particles()
        pygame.display.flip()

    # ---------- menu / UI ----------
    def draw_menu(self):
        title = self.font_big.render(APP_NAME, True, (255, 200, 60))
        self.screen.blit(title, (self.WIDTH//2 - title.get_width()//2, 80))

        info = self.font_med.render("Enter = Start    S = Settings    L = Leaderboard", True, (200, 200, 200))
        self.screen.blit(info, (self.WIDTH//2 - info.get_width()//2, 170))

        start_rect = pygame.Rect(self.WIDTH//2 - 140, 240, 280, 44)
        settings_rect = pygame.Rect(self.WIDTH//2 - 140, 300, 280, 44)
        leader_rect = pygame.Rect(self.WIDTH//2 - 140, 360, 280, 44)

        pygame.draw.rect(self.screen, (40, 40, 40), start_rect, border_radius=8)
        pygame.draw.rect(self.screen, (40, 40, 40), settings_rect, border_radius=8)
        pygame.draw.rect(self.screen, (40, 40, 40), leader_rect, border_radius=8)

        start_txt = self.font_med.render("Press Enter to Start", True, (230,230,230))
        settings_txt = self.font_med.render("S — Settings", True, (230,230,230))
        leader_txt = self.font_med.render("L — Leaderboard", True, (230,230,230))

        self.screen.blit(start_txt, (start_rect.x + 18, start_rect.y + 8))
        self.screen.blit(settings_txt, (settings_rect.x + 18, settings_rect.y + 8))
        self.screen.blit(leader_txt, (leader_rect.x + 18, leader_rect.y + 8))

        foot = self.font_sm.render("Esc = Quit", True, (150,150,150))
        self.screen.blit(foot, (12, self.HEIGHT - 28))

    def draw_settings(self):
        title = self.font_big.render("Settings", True, (255, 200, 60))
        self.screen.blit(title, (48, 36))

        sound_state = self.settings.get("sound", True)
        vol = self.settings.get("volume", 100)
        txt1 = self.font_med.render(f"Sound: {'On' if sound_state else 'Off'} (Press SPACE to toggle)", True, (255,255,255))
        txt2 = self.font_med.render(f"Volume: {vol} (Press Up/Down to change)", True, (255,255,255))
        txt3 = self.font_sm.render("Press Esc to return to Menu", True, (180,180,180))

        self.screen.blit(txt1, (48, 140))
        self.screen.blit(txt2, (48, 190))
        self.screen.blit(txt3, (48, 260))

    def draw_leaderboard(self):
        title = self.font_big.render("Leaderboard", True, (255, 200, 60))
        self.screen.blit(title, (48, 36))

        if not isinstance(self.leaderboard, list):
            self.leaderboard = []

        y = 120
        for i, entry in enumerate(sorted(self.leaderboard, key=lambda x: x.get('score', 0), reverse=True)[:10], start=1):
            name = entry.get('name', 'Player')
            score = entry.get('score', 0)
            line = self.font_med.render(f"{i}. {name} — {score}", True, (230,230,230))
            self.screen.blit(line, (68, y))
            y += 36

        hint = self.font_sm.render("Press Esc to return to Menu", True, (180,180,180))
        self.screen.blit(hint, (48, self.HEIGHT - 48))

    def draw_game(self):
        score_text = self.font_med.render(f"Score: {self.score}", True, (255, 255, 255))
        self.screen.blit(score_text, (20, 20))

    def draw_gameover(self):
        title = self.font_big.render("Game Over", True, (255, 140, 120))
        self.screen.blit(title, (self.WIDTH//2 - title.get_width()//2, 80))
        stat = self.font_med.render(f"Score: {self.score}", True, (255,255,255))
        self.screen.blit(stat, (self.WIDTH//2 - stat.get_width()//2, 160))

        prompt = self.font_med.render("Type name and press Enter to save:", True, (220,220,220))
        self.screen.blit(prompt, (self.WIDTH//2 - prompt.get_width()//2, 220))

        name_txt = self.font_med.render(self.player_name, True, (255,255,255))
        self.screen.blit(name_txt, (self.WIDTH//2 - name_txt.get_width()//2, 260))

        hint = self.font_sm.render("Esc = Menu (without saving)", True, (180,180,180))
        self.screen.blit(hint, (48, self.HEIGHT - 48))

    def start_play(self):
        self.state = "playing"
        self.score = 0

    def save_score_and_return(self):
        entry = {"name": self.player_name.strip() or "Player", "score": int(self.score)}
        self.leaderboard.append(entry)
        self.leaderboard = sorted(self.leaderboard, key=lambda x: x.get('score', 0), reverse=True)[:100]
        save_json(LEADERBOARD_FILE, self.leaderboard)
        self.play_sound("select")
        self.state = "leaderboard"

# ------------------- NUMBER CHAIN GAME -------------------
class NumberChainGame(BaseMinigame):
    def __init__(self):
        super().__init__()
        # game-specific
        self.grid_cols = 4
        self.grid_rows = 4
        self.tiles = []  # list of dicts: {"num", "rect", "clicked"}
        self.next_num = 1
        self.start_time = 0.0
        self.end_time = 0.0
        self.selection = None  # idx of keyboard-selected tile
        self.tile_margin = 12
        self.cell_rect = pygame.Rect(80, 120, self.WIDTH - 160, self.HEIGHT - 240)
        self.difficulty_map = {
            "easy": (3, 3),
            "normal": (4, 4),
            "hard": (5, 5)
        }

    def start_play(self):
        super().start_play()
        # setup according to difficulty
        diff = self.settings.get("difficulty", "normal")
        cols, rows = self.difficulty_map.get(diff, (4,4))
        self.grid_cols, self.grid_rows = cols, rows
        self._generate_tiles(cols, rows)
        self.next_num = 1
        self.start_time = time.time()
        self.end_time = 0.0
        self.score = 0
        self.selection = None
        self.play_sound("start")

    def _generate_tiles(self, cols, rows):
        nums = list(range(1, cols*rows + 1))
        random.shuffle(nums)
        self.tiles = []
        cw = (self.cell_rect.width - (cols+1)*self.tile_margin) / cols
        ch = (self.cell_rect.height - (rows+1)*self.tile_margin) / rows
        for r in range(rows):
            for c in range(cols):
                x = self.cell_rect.x + self.tile_margin + c * (cw + self.tile_margin)
                y = self.cell_rect.y + self.tile_margin + r * (ch + self.tile_margin)
                idx = r*cols + c
                rect = pygame.Rect(int(x), int(y), int(cw), int(ch))
                self.tiles.append({
                    "num": nums[idx],
                    "rect": rect,
                    "clicked": False
                })

    def update_game(self, dt):
        # nothing heavy per-frame other than timer checks
        if self.next_num > (self.grid_cols * self.grid_rows):
            # finished
            if self.end_time == 0.0:
                self.end_time = time.time()
                elapsed = max(0.01, self.end_time - self.start_time)
                # scoring: faster = higher; scale by number of tiles
                n = self.grid_cols * self.grid_rows
                base = max(10, int((n * 1200) / elapsed))
                # difficulty multiplier
                mult = 1.0
                diff = self.settings.get("difficulty", "normal")
                if diff == "easy": mult = 0.9
                elif diff == "hard": mult = 1.15
                self.score = int(base * mult)
                self.play_sound("complete")
                # go to gameover state for name entry
                self.state = "gameover"
                self.player_name = "Player"

    def handle_input(self, key=None, joy_event=None):
        # keyboard navigation and selection
        if key:
            if self.state != "playing":
                return
            if key == pygame.K_LEFT:
                self._move_selection(-1, 0)
            elif key == pygame.K_RIGHT:
                self._move_selection(1, 0)
            elif key == pygame.K_UP:
                self._move_selection(0, -1)
            elif key == pygame.K_DOWN:
                self._move_selection(0, 1)
            elif key in (pygame.K_RETURN, pygame.K_SPACE):
                # attempt to click selected tile (or nearest)
                if self.selection is None:
                    # try pop at center
                    mx = self.WIDTH//2
                    my = self.HEIGHT//2
                    self._attempt_click_at(mx, my)
                else:
                    self._attempt_click_index(self.selection)
        if joy_event:
            if getattr(joy_event, "type", None) == pygame.JOYAXISMOTION:
                # ignore fine joystick for now
                pass
            elif getattr(joy_event, "type", None) == pygame.JOYBUTTONDOWN:
                self.handle_input(key=self.settings.get("keymap", {}).get("action"))

    def _move_selection(self, dx, dy):
        cols, rows = self.grid_cols, self.grid_rows
        if self.selection is None:
            # pick first tile (top-left)
            self.selection = 0
            return
        col = self.selection % cols
        row = self.selection // cols
        col = max(0, min(cols-1, col + dx))
        row = max(0, min(rows-1, row + dy))
        self.selection = row*cols + col

    def _attempt_click_at(self, mx, my):
        for idx, t in enumerate(self.tiles):
            if t["rect"].collidepoint(mx, my) and (not t["clicked"]):
                self._click_tile(idx)
                return True
        # miss -> penalty sound
        self.play_sound("error")
        return False

    def _attempt_click_index(self, idx):
        if idx < 0 or idx >= len(self.tiles): return False
        t = self.tiles[idx]
        if t["clicked"]:
            self.play_sound("error")
            return False
        self._click_tile(idx)
        return True

    def _click_tile(self, idx):
        t = self.tiles[idx]
        if t["num"] == self.next_num:
            t["clicked"] = True
            self.emit_particle(t["rect"].centerx, t["rect"].centery, color=(120, 230, 160), amount=12)
            self.play_sound("correct")
            self.next_num += 1
            # auto-advance selection to next nearest
            self._auto_select_next()
        else:
            # wrong click penalty (small time penalty)
            self.play_sound("error")
            # penalty: shuffle a tiny bit or mark shake — we'll just emit red particles
            self.emit_particle(t["rect"].centerx, t["rect"].centery, color=(220, 90, 90), amount=10)

    def _auto_select_next(self):
        # try to select tile with next_num if present
        for idx, t in enumerate(self.tiles):
            if (not t["clicked"]) and t["num"] == self.next_num:
                self.selection = idx
                return
        # fallback: pick first unclicked
        for idx, t in enumerate(self.tiles):
            if not t["clicked"]:
                self.selection = idx
                return
        self.selection = None

    # override events to catch mouse clicks on tiles
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.state in ("settings", "leaderboard"):
                        self.state = "menu"
                        self.play_sound("cancel")
                    elif self.state == "playing":
                        self.state = "menu"
                        self.play_sound("cancel")
                    elif self.state == "gameover":
                        self.state = "menu"
                        self.play_sound("cancel")
                    else:
                        if self.state == "menu":
                            self.play_sound("cancel")
                            self.running = False
                elif self.state == "menu":
                    if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                        self.play_sound("start")
                        self.start_play()
                    elif event.key == pygame.K_s:
                        self.play_sound("select")
                        self.state = "settings"
                    elif event.key == pygame.K_l:
                        self.play_sound("select")
                        self.state = "leaderboard"
                elif self.state == "settings":
                    if event.key == pygame.K_SPACE:
                        cur = self.settings.get("sound", True)
                        self.settings["sound"] = not cur
                        save_json(SETTINGS_FILE, self.settings)
                        self.play_sound("select" if self.settings["sound"] else "cancel")
                    elif event.key == pygame.K_UP:
                        # cycle difficulty up
                        opts = ["easy", "normal", "hard"]
                        cur = self.settings.get("difficulty", "normal")
                        i = (opts.index(cur) + 1) % len(opts)
                        self.settings["difficulty"] = opts[i]
                        save_json(SETTINGS_FILE, self.settings)
                        self.play_sound("select")
                    elif event.key == pygame.K_DOWN:
                        opts = ["easy", "normal", "hard"]
                        cur = self.settings.get("difficulty", "normal")
                        i = (opts.index(cur) - 1) % len(opts)
                        self.settings["difficulty"] = opts[i]
                        save_json(SETTINGS_FILE, self.settings)
                        self.play_sound("select")
                elif self.state == "playing":
                    self.handle_input(event.key)
                elif self.state == "gameover":
                    if event.key == pygame.K_BACKSPACE:
                        self.player_name = self.player_name[:-1]
                    elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                        self.save_score_and_return()
                    else:
                        if len(self.player_name) < 16:
                            ch = event.unicode
                            if ch.isprintable():
                                self.player_name += ch

            elif event.type in (pygame.JOYBUTTONDOWN, pygame.JOYAXISMOTION):
                if self.state == "playing":
                    self.handle_input(joy_event=event)

            elif event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos
                if self.state == "menu":
                    start_rect = pygame.Rect(self.WIDTH//2 - 140, 240, 280, 44)
                    settings_rect = pygame.Rect(self.WIDTH//2 - 140, 300, 280, 44)
                    leader_rect = pygame.Rect(self.WIDTH//2 - 140, 360, 280, 44)
                    if start_rect.collidepoint(mx, my):
                        self.play_sound("start")
                        self.start_play()
                    elif settings_rect.collidepoint(mx, my):
                        self.play_sound("select")
                        self.state = "settings"
                    elif leader_rect.collidepoint(mx, my):
                        self.play_sound("select")
                        self.state = "leaderboard"
                elif self.state == "playing":
                    # check tiles
                    clicked = False
                    for idx, t in enumerate(self.tiles):
                        if t["rect"].collidepoint(mx, my):
                            self._attempt_click_index(idx)
                            clicked = True
                            break
                    if not clicked:
                        self.play_sound("error")

    def draw_game(self):
        # background & header
        self.screen.fill((18, 22, 30))
        title = self.font_med.render(f"Number Chain — Find {self.next_num}", True, (240,240,240))
        self.screen.blit(title, (20, 18))
        # timer
        if self.start_time > 0 and self.end_time == 0:
            elapsed = time.time() - self.start_time
        elif self.end_time > 0:
            elapsed = self.end_time - self.start_time
        else:
            elapsed = 0.0
        timer_txt = self.font_med.render(f"Time: {elapsed:.2f}s", True, (220,220,220))
        self.screen.blit(timer_txt, (20, 50))
        # draw grid tiles
        for idx, t in enumerate(self.tiles):
            rect = t["rect"]
            # fill color depending on state
            if t["clicked"]:
                col = (60, 140, 80)
            else:
                col = (40, 60, 90)
            pygame.draw.rect(self.screen, col, rect, border_radius=8)
            # border highlight if selected
            if self.selection == idx and not t["clicked"]:
                pygame.draw.rect(self.screen, (255, 220, 120), rect, 4, border_radius=8)
            # number text (centered)
            num_txt = self.font_big.render(str(t["num"]), True, (240,240,240) if not t["clicked"] else (230, 250, 230))
            self.screen.blit(num_txt, (rect.centerx - num_txt.get_width()/2, rect.centery - num_txt.get_height()/2))
        # footer
        footer = self.font_sm.render("Click numbers in ascending order • Arrow keys to navigate • Enter/Space to select", True, (180,180,200))
        self.screen.blit(footer, (self.WIDTH//2 - footer.get_width()//2, self.HEIGHT - 30))

# ------------------- RUN -------------------
if __name__ == "__main__":
    game = NumberChainGame()
    # ensure leaderboard exists
    if not Path(LEADERBOARD_FILE).exists():
        save_json(Path(LEADERBOARD_FILE), [])
    game.run()

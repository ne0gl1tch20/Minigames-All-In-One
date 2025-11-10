"""
Type Rush Minigame (Pygame)
Title: Type Rush
Description: Type random words quickly to stay alive. Words fall from the top — type them before they hit the ground!
Features:
- Start Menu / Settings / Leaderboard (JSON)
- Saveable settings and leaderboard
- Keyboard + Joystick support
- Particle system (visual flair)
- Procedural sound effects (no external files)
Requirements:
pip install pygame
Run:
python type_rush.py
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
APP_NAME = "Type Rush"
SAVE_FOLDER = MG_SAVE_DIR / "Saves" / APP_NAME
SAVE_FOLDER.mkdir(parents=True, exist_ok=True)

SETTINGS_FILE = SAVE_FOLDER / "settings.json"
LEADERBOARD_FILE = SAVE_FOLDER / "leaderboard.json"

DEFAULT_SETTINGS = {
    "volume": 90,
    "sound": True,
    "difficulty": "normal",  # easy / normal / hard
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
    WIDTH, HEIGHT = 900, 640
    FPS = 60

    def __init__(self):
        pygame.init()
        # audio
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
        self.font_med = pygame.font.SysFont("arial", 22)
        self.font_sm = pygame.font.SysFont("arial", 16)

        # Load settings / leaderboard
        self.settings = load_json(SETTINGS_FILE, DEFAULT_SETTINGS.copy())
        for k, v in DEFAULT_SETTINGS.items():
            self.settings.setdefault(k, v)
        self.leaderboard = load_json(LEADERBOARD_FILE, DEFAULT_LEADERBOARD.copy())

        self.state = "menu"
        self.running = True
        self.particles: List[Particle] = []
        self.score = 0
        self.player_name = "Player"

        self.joystick = None
        self.detect_joystick()

        self.sounds: Dict[str, pygame.mixer.Sound] = {}
        if self.mixer_available:
            self._create_sounds()
            self._apply_volume_to_sounds()

    def detect_joystick(self):
        if pygame.joystick.get_count() > 0:
            js = pygame.joystick.Joystick(0)
            js.init()
            self.joystick = js
            print("Joystick detected:", js.get_name())

    def _create_sounds(self):
        try:
            sample_rate = 22050
            defs = {
                "select": (660, 0.06),
                "start": (880, 0.12),
                "type": (1200, 0.02),
                "correct": (1400, 0.08),
                "wrong": (220, 0.10),
                "gameover": (160, 0.18),
            }
            for name, (hz, dur) in defs.items():
                n_samples = int(sample_rate * dur)
                buf = bytearray()
                max_amp = 127
                for i in range(n_samples):
                    t = i / sample_rate
                    env = 1.0 - (i / n_samples)
                    v = int(max_amp * math.sin(2 * math.pi * hz * t) * env)
                    buf.append((v + 128) & 0xFF)
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
        vol = max(0.0, min(1.0, float(self.settings.get("volume", 90)) / 100.0))
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

    def update_game(self, dt):
        pass

    def handle_input(self, key=None, joy_event=None):
        if key == self.settings.get("keymap", {}).get("action"):
            self.play_sound("type")

    def emit_particle(self, x, y, color=(255, 200, 60), amount=6):
        for _ in range(amount):
            angle = random.uniform(-math.pi, 0)
            speed = random.uniform(20, 180)
            p = Particle(
                x=x + random.uniform(-6, 6),
                y=y + random.uniform(-6, 6),
                vx=math.cos(angle) * speed,
                vy=math.sin(angle) * speed,
                life=random.uniform(0.5, 1.4),
                size=random.uniform(2, 6),
                color=color
            )
            self.particles.append(p)

    def run(self):
        if not Path(LEADERBOARD_FILE).exists():
            save_json(Path(LEADERBOARD_FILE), [])
        while self.running:
            dt = self.clock.tick(self.FPS) / 1000.0
            self.handle_events()
            if self.state == "playing":
                self.update_game(dt)
            self.update_particles(dt)
            self.render()
        pygame.quit()
        sys.exit()

    def handle_events(self):
        # Basic handling: override in subclass for more behavior
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.state in ("settings", "leaderboard"):
                        self.state = "menu"
                        self.play_sound("select")
                    elif self.state == "playing":
                        self.state = "menu"
                        self.play_sound("select")
                    elif self.state == "gameover":
                        self.state = "menu"
                        self.play_sound("select")
                    else:
                        if self.state == "menu":
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
                        self._apply_volume_to_sounds()
                        self.play_sound("select" if self.settings["sound"] else "wrong")
                    elif event.key == pygame.K_UP:
                        self.settings["volume"] = min(100, self.settings.get("volume", 90) + 5)
                        self._apply_volume_to_sounds()
                        save_json(SETTINGS_FILE, self.settings)
                        self.play_sound("select")
                    elif event.key == pygame.K_DOWN:
                        self.settings["volume"] = max(0, self.settings.get("volume", 90) - 5)
                        self._apply_volume_to_sounds()
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
                    start_rect = pygame.Rect(self.WIDTH//2 - 160, 240, 320, 48)
                    settings_rect = pygame.Rect(self.WIDTH//2 - 160, 310, 320, 48)
                    leader_rect = pygame.Rect(self.WIDTH//2 - 160, 380, 320, 48)
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
                    # clicking acts as typing the action (for mobile)
                    self.handle_input(key=self.settings.get("keymap", {}).get("action"))

    def update_particles(self, dt):
        for p in list(self.particles):
            p.x += p.vx * dt
            p.y += p.vy * dt
            p.vy += 200 * dt
            p.life -= dt
            if p.life <= 0:
                self.particles.remove(p)

    def render_particles(self):
        for p in self.particles:
            alpha = max(0, min(255, int(255 * p.life)))
            surf = pygame.Surface((int(p.size*2), int(p.size*2)), pygame.SRCALPHA)
            pygame.draw.circle(surf, (*p.color, alpha), (int(p.size), int(p.size)), int(p.size))
            self.screen.blit(surf, (int(p.x - p.size), int(p.y - p.size)))

    def render(self):
        self.screen.fill((18, 18, 22))
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

    def draw_menu(self):
        title = self.font_big.render(APP_NAME, True, (220, 220, 245))
        self.screen.blit(title, (self.WIDTH//2 - title.get_width()//2, 60))
        info = self.font_med.render("Enter = Start    S = Settings    L = Leaderboard", True, (200,200,200))
        self.screen.blit(info, (self.WIDTH//2 - info.get_width()//2, 140))
        start_rect = pygame.Rect(self.WIDTH//2 - 160, 240, 320, 48)
        settings_rect = pygame.Rect(self.WIDTH//2 - 160, 310, 320, 48)
        leader_rect = pygame.Rect(self.WIDTH//2 - 160, 380, 320, 48)
        pygame.draw.rect(self.screen, (36,36,40), start_rect, border_radius=8)
        pygame.draw.rect(self.screen, (36,36,40), settings_rect, border_radius=8)
        pygame.draw.rect(self.screen, (36,36,40), leader_rect, border_radius=8)
        self.screen.blit(self.font_med.render("Start", True, (240,240,240)), (start_rect.x + 20, start_rect.y + 12))
        self.screen.blit(self.font_med.render("Settings", True, (240,240,240)), (settings_rect.x + 20, settings_rect.y + 12))
        self.screen.blit(self.font_med.render("Leaderboard", True, (240,240,240)), (leader_rect.x + 20, leader_rect.y + 12))
        foot = self.font_sm.render("Esc = Quit", True, (160,160,160))
        self.screen.blit(foot, (12, self.HEIGHT - 28))

    def draw_settings(self):
        title = self.font_big.render("Settings", True, (220,220,245))
        self.screen.blit(title, (48, 36))
        sound_state = self.settings.get("sound", True)
        vol = self.settings.get("volume", 90)
        diff = self.settings.get("difficulty", "normal")
        txt1 = self.font_med.render(f"Sound: {'On' if sound_state else 'Off'} (Press SPACE)", True, (240,240,240))
        txt2 = self.font_med.render(f"Volume: {vol} (Up/Down)", True, (240,240,240))
        txt3 = self.font_med.render(f"Difficulty: {diff} (Press Up to cycle)", True, (200,200,220))
        hint = self.font_sm.render("Press Esc to return to Menu", True, (180,180,180))
        self.screen.blit(txt1, (48, 140))
        self.screen.blit(txt2, (48, 180))
        self.screen.blit(txt3, (48, 220))
        self.screen.blit(hint, (48, 260))

    def draw_leaderboard(self):
        title = self.font_big.render("Leaderboard", True, (220,220,245))
        self.screen.blit(title, (48, 36))
        if not isinstance(self.leaderboard, list):
            self.leaderboard = []
        y = 120
        for i, entry in enumerate(sorted(self.leaderboard, key=lambda x: x.get('score', 0), reverse=True)[:10], start=1):
            name = entry.get('name', 'Player')
            score = entry.get('score', 0)
            line = self.font_med.render(f"{i}. {name} — {score}", True, (230,230,230))
            self.screen.blit(line, (68, y))
            y += 34
        hint = self.font_sm.render("Press Esc to return to Menu", True, (180,180,180))
        self.screen.blit(hint, (48, self.HEIGHT - 48))

    def draw_game(self):
        score_text = self.font_med.render(f"Score: {self.score}", True, (245,245,245))
        self.screen.blit(score_text, (18, 18))

    def draw_gameover(self):
        title = self.font_big.render("Game Over", True, (255,140,120))
        self.screen.blit(title, (self.WIDTH//2 - title.get_width()//2, 64))
        stat = self.font_med.render(f"Score: {self.score}", True, (240,240,240))
        self.screen.blit(stat, (self.WIDTH//2 - stat.get_width()//2, 150))
        prompt = self.font_med.render("Type name and press Enter to save:", True, (220,220,220))
        self.screen.blit(prompt, (self.WIDTH//2 - prompt.get_width()//2, 200))
        name_txt = self.font_med.render(self.player_name, True, (255,255,255))
        self.screen.blit(name_txt, (self.WIDTH//2 - name_txt.get_width()//2, 240))
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

# ------------------- TYPE RUSH GAME -------------------
class TypeRushGame(BaseMinigame):
    # small built-in word list (can be extended)
    WORDS = [
        "cat","dog","sun","moon","star","apple","banana","rocket","python","keyboard",
        "music","sound","game","stack","bubble","fast","speed","typing","random","skill",
        "forest","river","island","mountain","globe","puzzle","pixel","fluffy","neon",
        "wizard","ninja","castle","robot","guitar","drums","coffee","chocolate","sprint",
        "matrix","signal","light","shadow","mirror","orange","purple","silver","gold"
    ]

    def __init__(self):
        super().__init__()
        self.fall_zone = pygame.Rect(40, 100, self.WIDTH - 80, self.HEIGHT - 180)
        self.words_on_screen: List[Dict] = []  # each: {word,x,y,vy,font_size,spawn_t}
        self.spawn_timer = 0.0
        self.spawn_interval = 1.4
        self.input_buffer = ""
        self.health = 100.0  # when reaches 0 -> game over
        self.base_drain = 6.0  # health per second baseline
        self.word_miss_penalty = 9.0  # on miss
        self.word_clear_reward = 7.0  # on correct
        self.streak = 0
        self.best_streak = 0
        self.game_start = 0.0
        self.elapsed = 0.0
        self.max_words = 5
        self.difficulty_map = {
            "easy": {"spawn_mult": 0.8, "fall_mult": 0.75, "drain_mult": 0.8, "max_words": 4},
            "normal": {"spawn_mult": 1.0, "fall_mult": 1.0, "drain_mult": 1.0, "max_words": 5},
            "hard": {"spawn_mult": 0.72, "fall_mult": 1.35, "drain_mult": 1.25, "max_words": 7},
        }
        self.reset_game_state()

    def reset_game_state(self):
        self.words_on_screen.clear()
        self.spawn_timer = 0.0
        self.input_buffer = ""
        self.health = 100.0
        self.streak = 0
        self.best_streak = 0
        self.score = 0
        self.game_start = time.time()
        self.elapsed = 0.0
        diff = self.settings.get("difficulty", "normal")
        cfg = self.difficulty_map.get(diff, self.difficulty_map["normal"])
        self.spawn_interval = max(0.35, 1.4 * cfg["spawn_mult"])
        self.base_drain = 6.0 * cfg["drain_mult"]
        self.max_words = cfg["max_words"]
        # initial spawn a couple words
        for _ in range(2):
            self.spawn_word()

    def spawn_word(self):
        if len(self.words_on_screen) >= self.max_words:
            return
        w = random.choice(self.WORDS)
        # avoid duplicates on screen
        tries = 0
        while any(w == s["word"] for s in self.words_on_screen) and tries < 6:
            w = random.choice(self.WORDS)
            tries += 1
        font_size = random.randint(20, 36)
        x = random.uniform(self.fall_zone.left + 40, self.fall_zone.right - 40)
        y = -30
        # fall speed affected by difficulty and word length
        diff = self.settings.get("difficulty", "normal")
        fall_mult = self.difficulty_map.get(diff, self.difficulty_map["normal"])["fall_mult"]
        vy = random.uniform(40 + len(w)*6, 80 + len(w)*10) * fall_mult
        self.words_on_screen.append({"word": w, "x": x, "y": y, "vy": vy, "font_size": font_size, "spawn_t": time.time()})

    def start_play(self):
        super().start_play()
        self.reset_game_state()
        self.play_sound("start")

    def handle_input(self, key=None, joy_event=None):
        # typing input handled via KEYDOWN events in handle_events override
        # but we keep this for action mapping (Enter as submit)
        if key == pygame.K_RETURN or key == self.settings.get("keymap", {}).get("action"):
            self.check_submission()

    def check_submission(self):
        buf = self.input_buffer.strip()
        if not buf:
            return
        matched = None
        for s in self.words_on_screen:
            if s["word"] == buf:
                matched = s
                break
        if matched:
            self.on_correct_word(matched)
        else:
            # partial check: if input exactly matches start of any word, do nothing (encouraging)
            # else wrong
            if not any(s["word"].startswith(buf) for s in self.words_on_screen):
                self.on_wrong_submit()
        # clear buffer only on correct or wrong full submit; if buffer matches prefix we keep it.
        # here we will clear when exact or wrong full submit
        if matched or (not any(s["word"].startswith(buf) for s in self.words_on_screen)):
            self.input_buffer = ""

    def on_correct_word(self, s):
        # remove word
        try:
            self.words_on_screen.remove(s)
        except ValueError:
            pass
        # scoring: base = len * 10 * streak multiplier
        base = max(5, len(s["word"]) * 10)
        mult = 1.0 + (self.streak * 0.12)
        gain = int(base * mult)
        self.score += gain
        # health reward & streak
        self.health = min(100.0, self.health + self.word_clear_reward)
        self.streak += 1
        self.best_streak = max(self.best_streak, self.streak)
        # particles & sound
        self.emit_particle(s["x"], s["y"], color=(160, 240, 200), amount=12)
        self.play_sound("correct")
        # spawn a new word to keep flow
        self.spawn_word()

    def on_wrong_submit(self):
        self.health -= 6.0
        self.streak = 0
        self.emit_particle(self.WIDTH//2, self.HEIGHT//2, color=(240,120,120), amount=12)
        self.play_sound("wrong")

    def update_game(self, dt):
        if self.state != "playing":
            return
        self.elapsed = time.time() - self.game_start
        # spawn timer
        self.spawn_timer += dt
        if self.spawn_timer >= self.spawn_interval:
            self.spawn_word()
            self.spawn_timer = 0.0
            # slightly increase spawn frequency with time
            self.spawn_interval = max(0.28, self.spawn_interval * 0.995)

        # update falling words
        for s in list(self.words_on_screen):
            s["y"] += s["vy"] * dt
            # slight horizontal drift
            s["x"] += math.sin((time.time() - s["spawn_t"]) * 0.8 + s["x"]) * 4 * dt
            # if they hit bottom -> miss
            if s["y"] > self.fall_zone.bottom + 16:
                try:
                    self.words_on_screen.remove(s)
                except ValueError:
                    pass
                self.health -= self.word_miss_penalty
                self.streak = 0
                self.emit_particle(s["x"], self.fall_zone.bottom, color=(240,120,120), amount=14)
                self.play_sound("wrong")
                # spawn replacement
                self.spawn_word()

        # health drain over time
        self.health -= self.base_drain * dt
        # clamp
        self.health = max(-10.0, min(120.0, self.health))

        # check death
        if self.health <= 0:
            self._game_over()

        # ambient particle: occasional tiny dust
        if random.random() < 0.015:
            self.emit_particle(random.uniform(self.fall_zone.left, self.fall_zone.right),
                               random.uniform(self.fall_zone.top, self.fall_zone.bottom), color=(200,200,240), amount=1)

    def _game_over(self):
        self.play_sound("gameover")
        self.state = "gameover"
        self.player_name = "Player"
        # final particle burst
        self.emit_particle(self.WIDTH//2, self.HEIGHT//2, color=(255,120,120), amount=80)

    # override handle_events to capture typing chars
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.state in ("settings", "leaderboard"):
                        self.state = "menu"
                        self.play_sound("select")
                    elif self.state == "playing":
                        self.state = "menu"
                        self.play_sound("select")
                    elif self.state == "gameover":
                        self.state = "menu"
                        self.play_sound("select")
                    else:
                        if self.state == "menu":
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
                        self._apply_volume_to_sounds()
                        self.play_sound("select" if self.settings["sound"] else "wrong")
                    elif event.key == pygame.K_UP:
                        # cycle difficulty
                        opts = ["easy","normal","hard"]
                        cur = self.settings.get("difficulty","normal")
                        i = (opts.index(cur) + 1) % len(opts)
                        self.settings["difficulty"] = opts[i]
                        save_json(SETTINGS_FILE, self.settings)
                        self.play_sound("select")
                    elif event.key == pygame.K_DOWN:
                        # cycle other way
                        opts = ["easy","normal","hard"]
                        cur = self.settings.get("difficulty","normal")
                        i = (opts.index(cur) - 1) % len(opts)
                        self.settings["difficulty"] = opts[i]
                        save_json(SETTINGS_FILE, self.settings)
                        self.play_sound("select")

                elif self.state == "playing":
                    # typing: printable characters go into buffer
                    if event.key == pygame.K_BACKSPACE:
                        self.input_buffer = self.input_buffer[:-1]
                        self.play_sound("type")
                    elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                        self.check_submission()
                    else:
                        ch = event.unicode
                        if ch and ch.isprintable():
                            # simple filter: allow letters only and hyphen
                            if len(self.input_buffer) < 32:
                                self.input_buffer += ch
                                self.play_sound("type")
                                # auto-check immediate exact match to speed gameplay
                                for s in list(self.words_on_screen):
                                    if s["word"] == self.input_buffer:
                                        self.on_correct_word(s)
                                        self.input_buffer = ""
                                        break

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
                # map joystick button to submit
                if self.state == "playing":
                    if getattr(event, "type", None) == pygame.JOYBUTTONDOWN:
                        self.check_submission()
                else:
                    # other states: ignore joystick for now
                    pass

            elif event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos
                if self.state == "menu":
                    start_rect = pygame.Rect(self.WIDTH//2 - 160, 240, 320, 48)
                    settings_rect = pygame.Rect(self.WIDTH//2 - 160, 310, 320, 48)
                    leader_rect = pygame.Rect(self.WIDTH//2 - 160, 380, 320, 48)
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
                    # click focuses and appends a space (simulate quick correction)
                    self.input_buffer += " "
                    self.play_sound("type")

    def draw_game(self):
        # clear background
        self.screen.fill((12, 14, 20))
        # header
        score_text = self.font_med.render(f"Score: {self.score}", True, (240,240,240))
        self.screen.blit(score_text, (18, 18))
        time_text = self.font_med.render(f"Time: {int(self.elapsed)}s", True, (240,240,240))
        self.screen.blit(time_text, (160, 18))
        streak_text = self.font_med.render(f"Streak: {self.streak}  Best: {self.best_streak}", True, (240,240,240))
        self.screen.blit(streak_text, (300, 18))

        # draw fall zone box
        pygame.draw.rect(self.screen, (18, 20, 28), self.fall_zone, border_radius=8)
        pygame.draw.rect(self.screen, (40, 40, 50), self.fall_zone, 2, border_radius=8)

        # draw words
        for s in self.words_on_screen:
            f = pygame.font.SysFont("arial", s["font_size"], bold=True)
            txt = f.render(s["word"], True, (230,230,250))
            w = txt.get_width()
            h = txt.get_height()
            self.screen.blit(txt, (int(s["x"] - w/2), int(s["y"] - h/2)))

            # underline if input buffer matches prefix
            if self.input_buffer and s["word"].startswith(self.input_buffer):
                pref_txt = f.render(s["word"][:len(self.input_buffer)], True, (160, 240, 200))
                self.screen.blit(pref_txt, (int(s["x"] - w/2), int(s["y"] - h/2)))

        # draw input box
        inp_rect = pygame.Rect(60, self.HEIGHT - 100, self.WIDTH - 120, 56)
        pygame.draw.rect(self.screen, (30,30,36), inp_rect, border_radius=8)
        pygame.draw.rect(self.screen, (70,70,80), inp_rect, 2, border_radius=8)
        input_txt = self.font_med.render(self.input_buffer, True, (230,230,240))
        self.screen.blit(input_txt, (inp_rect.x + 12, inp_rect.y + 12))

        # draw health bar
        hb_rect = pygame.Rect(self.WIDTH - 320, 18, 240, 24)
        pygame.draw.rect(self.screen, (30,30,36), hb_rect, border_radius=6)
        frac = max(0.0, min(1.0, self.health / 100.0))
        fill_rect = pygame.Rect(hb_rect.x + 4, hb_rect.y + 4, int((hb_rect.width - 8) * frac), hb_rect.height - 8)
        # gradient color
        if frac < 0.35:
            color = (240, 100, 100)
        elif frac < 0.7:
            color = (240, 200, 100)
        else:
            color = (120, 220, 160)
        pygame.draw.rect(self.screen, color, fill_rect, border_radius=6)
        pygame.draw.rect(self.screen, (80,80,90), hb_rect, 2, border_radius=6)
        hp_txt = self.font_sm.render(f"Health: {int(self.health)}%", True, (230,230,230))
        self.screen.blit(hp_txt, (hb_rect.x + 6, hb_rect.y - 22))

        # footer tips
        tip = self.font_sm.render("Type the falling words exactly then press Enter (or auto when exact). Don't let health drop to 0.", True, (200,200,200))
        self.screen.blit(tip, (self.WIDTH//2 - tip.get_width()//2, self.HEIGHT - 28))

# ------------------- RUN -------------------
if __name__ == "__main__":
    game = TypeRushGame()
    game.run()

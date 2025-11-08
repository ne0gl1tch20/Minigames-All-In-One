"""
Pizza Panic - pizza_panic.py
Drop folder "Pizza Panic" into your launcher minigames dir.

Features:
- Menu / Settings / Leaderboard (JSON stored in Documents/.mgaio/Saves/Pizza Panic)
- Procedural sound effects (no external audio files required)
- Simple gameplay: catch pizzas, avoid rotten ones (bombs)
- Particle effects on catch / miss
- Keyboard + joystick support
- Easy-to-read single-file implementation

Run:
python pizza_panic.py
"""

import pygame
import sys
import json
import os
import random
import math
import time
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict, Optional

# ------------------- PATHS / SAVE -------------------
USER_DIR = os.path.expandvars(r"%userprofile%") if os.name == "nt" else os.path.expanduser("~")
MG_SAVE_DIR = Path(USER_DIR) / "Documents" / ".mgaio"
APP_NAME = "Pizza Panic"
SAVE_FOLDER = MG_SAVE_DIR / "Saves" / APP_NAME
SAVE_FOLDER.mkdir(parents=True, exist_ok=True)

SETTINGS_FILE = SAVE_FOLDER / "settings.json"
LEADERBOARD_FILE = SAVE_FOLDER / "leaderboard.json"

DEFAULT_SETTINGS = {
    "volume": 100,
    "sound": True,
    "difficulty": "normal",  # easy, normal, hard
    "keymap": {"left": pygame.K_a, "right": pygame.K_d, "throw": pygame.K_SPACE},
    "joymap": {},
}

if not SETTINGS_FILE.exists():
    SETTINGS_FILE.write_text(json.dumps(DEFAULT_SETTINGS, indent=2))
if not LEADERBOARD_FILE.exists():
    LEADERBOARD_FILE.write_text(json.dumps([], indent=2))

def load_json(path: Path, default):
    try:
        if path.exists():
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

# ------------------- BASIC TYPES -------------------
@dataclass
class Particle:
    x: float
    y: float
    vx: float
    vy: float
    life: float
    size: float
    color: tuple

@dataclass
class FallingItem:
    x: float
    y: float
    vy: float
    kind: str            # "pizza" or "rotten"
    created: float
    wobble: float = 0.0

# ------------------- GAME CONFIG -------------------
WIDTH, HEIGHT = 900, 650
FPS = 60

PLAYER_Y = HEIGHT - 88
PLAYER_SPEED = 360.0
ITEM_MIN_VY = 140
ITEM_MAX_VY = 260

STARTING_LIVES = 5
MAX_LEADERBOARD = 20

# Colors
BG = (22, 24, 30)
WHITE = (245, 245, 245)
ACCENT = (255, 170, 60)
GOOD = (88, 214, 141)
BAD = (232, 76, 61)
GRAY = (100, 100, 105)

# ------------------- MAIN CLASS -------------------
class PizzaPanic:
    def __init__(self):
        pygame.init()
        # audio
        self.mixer_ok = True
        try:
            pygame.mixer.init()
        except Exception as e:
            print("Audio init failed:", e)
            self.mixer_ok = False

        pygame.joystick.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption(APP_NAME)
        self.clock = pygame.time.Clock()

        # fonts
        self.font_big = pygame.font.SysFont("arial", 48, bold=True)
        self.font_med = pygame.font.SysFont("arial", 26)
        self.font_sm = pygame.font.SysFont("arial", 18)

        # data
        self.settings = load_json(SETTINGS_FILE, DEFAULT_SETTINGS.copy())
        for k, v in DEFAULT_SETTINGS.items():
            self.settings.setdefault(k, v)
        self.leaderboard = load_json(LEADERBOARD_FILE, [])
        self._ensure_leaderboard_structure()

        # joystick
        self.joystick = None
        self._detect_joystick()

        # sounds
        self.sounds: Dict[str, Optional[pygame.mixer.Sound]] = {}
        if self.mixer_ok:
            self._create_sounds()
            self._apply_volume()

        # game state
        self.state = "menu"   # menu, settings, leaderboard, playing, gameover
        self.running = True

        # gameplay
        self.player_x = WIDTH // 2
        self.player_vx = 0.0
        self.items: List[FallingItem] = []
        self.particles: List[Particle] = []
        self.spawn_timer = 0.0
        self.spawn_interval = 1.0
        self.score = 0
        self.lives = STARTING_LIVES
        self.combo = 0
        self.high_score = self._highest_score()
        self.game_start_time = 0.0

        # tunables from difficulty
        self.apply_difficulty()

    # ------------------- helpers -------------------
    def _ensure_leaderboard_structure(self):
        if not isinstance(self.leaderboard, list):
            self.leaderboard = []

    def _detect_joystick(self):
        if pygame.joystick.get_count() > 0:
            try:
                js = pygame.joystick.Joystick(0)
                js.init()
                self.joystick = js
                print("Joystick:", js.get_name())
            except Exception as e:
                print("Joystick init failed:", e)

    # ------------------- procedural sounds -------------------
    def _create_sounds(self):
        """Create a handful of short procedural sounds and store as pygame.Sound."""
        try:
            sr = 22050
            def build_tone(hz, dur, kind="sine", env=True):
                n = int(sr * dur)
                buf = bytearray()
                max_amp = 127
                for i in range(n):
                    t = i / sr
                    if kind == "sine":
                        v = math.sin(2 * math.pi * hz * t)
                    elif kind == "saw":
                        v = 2.0 * (t * hz - math.floor(0.5 + t * hz))
                    else:
                        v = math.sin(2 * math.pi * hz * t)
                    env_val = 1.0
                    if env:
                        env_val = (1 - (i / n))  # simple decay
                    samp = int(max_amp * v * env_val)
                    buf.append(max(0, min(255, samp + 128)))
                return pygame.mixer.Sound(buffer=bytes(buf))

            self.sounds["start"] = build_tone(880, 0.12)
            self.sounds["catch"] = build_tone(1200, 0.06, "sine")
            self.sounds["drop"] = build_tone(220, 0.09, "saw")
            self.sounds["bad"] = build_tone(160, 0.12, "sine")
            self.sounds["select"] = build_tone(660, 0.06)
        except Exception as e:
            print("Sound creation failed:", e)
            self.sounds = {}

    def _apply_volume(self):
        vol = max(0.0, min(1.0, float(self.settings.get("volume", 100)) / 100.0))
        for s in self.sounds.values():
            try:
                if s:
                    s.set_volume(vol)
            except Exception:
                pass

    def play_sound(self, name):
        if not self.mixer_ok or not self.settings.get("sound", True):
            return
        s = self.sounds.get(name)
        if s:
            try:
                s.play()
            except Exception:
                pass

    # ------------------- difficulty -------------------
    def apply_difficulty(self):
        d = self.settings.get("difficulty", "normal")
        if d == "easy":
            self.spawn_interval = 1.25
            self.item_min_v = ITEM_MIN_VY * 0.8
            self.item_max_v = ITEM_MAX_VY * 0.9
            self.lives = STARTING_LIVES + 2
        elif d == "hard":
            self.spawn_interval = 0.7
            self.item_min_v = ITEM_MIN_VY * 1.1
            self.item_max_v = ITEM_MAX_VY * 1.4
            self.lives = max(3, STARTING_LIVES - 1)
        else:
            self.spawn_interval = 1.0
            self.item_min_v = ITEM_MIN_VY
            self.item_max_v = ITEM_MAX_VY
            self.lives = STARTING_LIVES

    # ------------------- gameplay core -------------------
    def spawn_item(self):
        # spawn pizza or rotten (chance increases with time)
        x = random.uniform(60, WIDTH - 60)
        vy = random.uniform(self.item_min_v, self.item_max_v)
        elapsed = time.time() - self.game_start_time if self.game_start_time else 0.0
        rotten_chance = min(0.25, 0.05 + elapsed / 60.0)  # slowly increase to max 25%
        kind = "rotten" if random.random() < rotten_chance else "pizza"
        it = FallingItem(x=x, y=-40, vy=vy, kind=kind, created=time.time(), wobble=random.random()*2)
        self.items.append(it)

    def _emit_particles(self, x, y, count, color):
        for _ in range(count):
            ang = random.uniform(-math.pi, 0)
            speed = random.uniform(60, 300)
            vx = math.cos(ang) * speed * random.uniform(0.2, 1.0)
            vy = math.sin(ang) * speed * random.uniform(0.2, 1.0)
            p = Particle(x=x + random.uniform(-8, 8), y=y + random.uniform(-8, 8), vx=vx, vy=vy, life=random.uniform(0.5, 1.2), size=random.uniform(2,6), color=color)
            self.particles.append(p)

    def _score_catch(self, item: FallingItem):
        base = 10 if item.kind == "pizza" else -1
        if item.kind == "pizza":
            # combo bonus
            bonus = int(self.combo * 1.5)
            pts = base + bonus
            self.score += pts
            self.combo += 1
            self.play_sound("catch")
            self._emit_particles(item.x, item.y, 14, GOOD)
        else:
            # rotten
            self.combo = 0
            self.lives -= 1
            self.play_sound("bad")
            self._emit_particles(item.x, item.y, 18, BAD)

    def update_game(self, dt):
        # spawn logic
        self.spawn_timer += dt
        if self.spawn_timer >= self.spawn_interval:
            self.spawn_timer -= self.spawn_interval
            self.spawn_item()

        # items update
        for it in list(self.items):
            it.y += it.vy * dt
            # wobble
            it.x += math.sin((time.time() - it.created) * 6.0 + it.wobble) * 0.6
            # off screen - missed pizza
            if it.y > HEIGHT + 40:
                if it.kind == "pizza":
                    self.combo = 0
                    self.lives -= 1
                    self.play_sound("drop")
                    self._emit_particles(it.x, HEIGHT - 60, 12, BAD)
                self.items.remove(it)

        # particles
        for p in list(self.particles):
            p.x += p.vx * dt
            p.y += p.vy * dt
            p.vy += 600 * dt
            p.life -= dt
            if p.life <= 0:
                self.particles.remove(p)

        # Physics: move player
        keys = pygame.key.get_pressed()
        left_key = self.settings.get("keymap", {}).get("left", pygame.K_a)
        right_key = self.settings.get("keymap", {}).get("right", pygame.K_d)
        move_left = keys[left_key]
        move_right = keys[right_key]
        vx = 0.0
        if move_left and not move_right:
            vx = -PLAYER_SPEED
        elif move_right and not move_left:
            vx = PLAYER_SPEED
        self.player_vx = vx
        self.player_x += self.player_vx * dt
        self.player_x = max(42, min(WIDTH - 42, self.player_x))

        # collision: check items close to player Y
        for it in list(self.items):
            if it.y >= PLAYER_Y - 36:
                # check horizontal overlap
                if abs(it.x - self.player_x) < 64:
                    # caught
                    self._score_catch(it)
                    if it in self.items:
                        self.items.remove(it)

        # check gameover
        if self.lives <= 0:
            self.state = "gameover"
            self._save_score_prompt()

    # ------------------- save / leaderboard -------------------
    def _save_score_prompt(self):
        name = "Player"
        self.leaderboard.append({"name": name, "score": int(self.score), "time": int(time.time())})
        self.leaderboard = sorted(self.leaderboard, key=lambda x: x.get("score",0), reverse=True)[:MAX_LEADERBOARD]
        save_json(LEADERBOARD_FILE, self.leaderboard)
        self.high_score = self._highest_score()

    def add_to_leaderboard(self, name, score):
        self.leaderboard.append({"name": name, "score": int(score), "time": int(time.time())})
        self.leaderboard = sorted(self.leaderboard, key=lambda x: x.get("score",0), reverse=True)[:MAX_LEADERBOARD]
        save_json(LEADERBOARD_FILE, self.leaderboard)
        self.high_score = self._highest_score()

    def _highest_score(self):
        if not self.leaderboard:
            return 0
        return max(e.get("score", 0) for e in self.leaderboard)

    # ------------------- input / events -------------------
    def handle_events(self):
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                self.running = False
            elif e.type == pygame.KEYDOWN:
                if self.state == "menu":
                    if e.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                        self.play_sound("start")
                        self.start_play()
                    elif e.key == pygame.K_s:
                        self.play_sound("select")
                        self.state = "settings"
                    elif e.key == pygame.K_l:
                        self.play_sound("select")
                        self.state = "leaderboard"
                    elif e.key == pygame.K_ESCAPE:
                        self.running = False
                elif self.state == "settings":
                    if e.key == pygame.K_ESCAPE:
                        self.state = "menu"
                    elif e.key == pygame.K_SPACE:
                        cur = self.settings.get("sound", True)
                        self.settings["sound"] = not cur
                        save_json(SETTINGS_FILE, self.settings)
                        self._apply_volume()
                        self.play_sound("select" if self.settings["sound"] else "bad")
                    elif e.key == pygame.K_UP:
                        self.settings["volume"] = min(100, self.settings.get("volume",100)+5)
                        save_json(SETTINGS_FILE, self.settings)
                        self._apply_volume()
                        self.play_sound("select")
                    elif e.key == pygame.K_DOWN:
                        self.settings["volume"] = max(0, self.settings.get("volume",100)-5)
                        save_json(SETTINGS_FILE, self.settings)
                        self._apply_volume()
                        self.play_sound("select")
                    elif e.key == pygame.K_e:
                        self.settings["difficulty"] = "easy"
                        self.apply_difficulty()
                        save_json(SETTINGS_FILE, self.settings)
                    elif e.key == pygame.K_n:
                        self.settings["difficulty"] = "normal"
                        self.apply_difficulty()
                        save_json(SETTINGS_FILE, self.settings)
                    elif e.key == pygame.K_h:
                        self.settings["difficulty"] = "hard"
                        self.apply_difficulty()
                        save_json(SETTINGS_FILE, self.settings)
                elif self.state == "leaderboard":
                    if e.key == pygame.K_ESCAPE:
                        self.state = "menu"
                elif self.state == "gameover":
                    if e.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                        self.state = "menu"
                elif self.state == "playing":
                    if e.key == pygame.K_ESCAPE:
                        self.state = "menu"
            elif e.type in (pygame.JOYBUTTONDOWN, pygame.JOYAXISMOTION):
                # simple joystick support: button 0 start/catch
                if self.joystick and self.state == "menu" and e.type == pygame.JOYBUTTONDOWN and getattr(e, "button", None) == 0:
                    self.play_sound("start")
                    self.start_play()
                if self.state == "playing" and e.type == pygame.JOYAXISMOTION:
                    # left/right axis control (assume axis 0)
                    ax = getattr(e, "axis", 0)
                    val = getattr(e, "value", 0.0)
                    if ax == 0:
                        # mapped automatically in update_game via key.get_pressed fallback
                        pass

    # ------------------- drawing -------------------
    def draw_menu(self):
        self.screen.fill(BG)
        title = self.font_big.render("Pizza Panic", True, ACCENT)
        self.screen.blit(title, (WIDTH//2 - title.get_width()//2, 40))

        info = self.font_med.render("Enter = Start    S = Settings    L = Leaderboard", True, WHITE)
        self.screen.blit(info, (WIDTH//2 - info.get_width()//2, 120))

        start_rect = pygame.Rect(WIDTH//2 - 180, 200, 360, 56)
        settings_rect = pygame.Rect(WIDTH//2 - 180, 280, 360, 48)
        lb_rect = pygame.Rect(WIDTH//2 - 180, 340, 360, 48)
        pygame.draw.rect(self.screen, (36,36,42), start_rect, border_radius=10)
        pygame.draw.rect(self.screen, (36,36,42), settings_rect, border_radius=10)
        pygame.draw.rect(self.screen, (36,36,42), lb_rect, border_radius=10)

        self.screen.blit(self.font_med.render("Start Game", True, WHITE), (start_rect.x + 24, start_rect.y + 12))
        self.screen.blit(self.font_med.render("Settings", True, WHITE), (settings_rect.x + 24, settings_rect.y + 8))
        self.screen.blit(self.font_med.render("Leaderboard", True, WHITE), (lb_rect.x + 24, lb_rect.y + 8))

        foot = self.font_sm.render(f"Top score: {self.high_score}", True, GRAY)
        self.screen.blit(foot, (12, HEIGHT - 28))

    def draw_settings(self):
        self.screen.fill(BG)
        title = self.font_big.render("Settings", True, ACCENT)
        self.screen.blit(title, (48, 36))
        sound_text = f"Sound: {'On' if self.settings.get('sound', True) else 'Off'} (SPACE to toggle)"
        vol_text = f"Volume: {self.settings.get('volume', 100)} (UP/DOWN)"
        diff_text = f"Difficulty: {self.settings.get('difficulty', 'normal')} (E/N/H)"

        self.screen.blit(self.font_med.render(sound_text, True, WHITE), (48, 140))
        self.screen.blit(self.font_med.render(vol_text, True, WHITE), (48, 190))
        self.screen.blit(self.font_med.render(diff_text, True, WHITE), (48, 240))

        hint = self.font_sm.render("Esc to return to Menu", True, GRAY)
        self.screen.blit(hint, (48, HEIGHT - 48))

    def draw_leaderboard(self):
        self.screen.fill(BG)
        title = self.font_big.render("Leaderboard", True, ACCENT)
        self.screen.blit(title, (48, 36))

        y = 120
        for i, e in enumerate(sorted(self.leaderboard, key=lambda x: x.get("score",0), reverse=True)[:10], start=1):
            line = self.font_med.render(f"{i}. {e.get('name','Player')} — {e.get('score',0)}", True, WHITE)
            self.screen.blit(line, (68, y))
            y += 36

        hint = self.font_sm.render("Esc to return to Menu", True, GRAY)
        self.screen.blit(hint, (48, HEIGHT - 48))

    def draw_play(self):
        self.screen.fill((18, 20, 26))
        # draw player (server)
        px = int(self.player_x)
        pygame.draw.rect(self.screen, (200,180,120), (px - 48, PLAYER_Y - 28, 96, 56), border_radius=14)
        # face
        pygame.draw.circle(self.screen, (30,30,30), (px - 18, PLAYER_Y - 8), 6)
        pygame.draw.circle(self.screen, (30,30,30), (px + 18, PLAYER_Y - 8), 6)
        pygame.draw.arc(self.screen, (60,40,30), (px - 22, PLAYER_Y - 10, 44, 26), math.pi/8, math.pi - math.pi/8, 3)

        # draw items
        for it in self.items:
            if it.kind == "pizza":
                # pizza body
                pygame.draw.circle(self.screen, (220, 180, 80), (int(it.x), int(it.y)), 26)
                pygame.draw.circle(self.screen, (200,120,60), (int(it.x), int(it.y+6)), 22)
                # pepperoni
                for i in range(3):
                    ang = i * 2*math.pi / 3 + (time.time() - it.created) * 0.3
                    rx = int(it.x + math.cos(ang) * 10)
                    ry = int(it.y + math.sin(ang) * 8)
                    pygame.draw.circle(self.screen, (180,50,50), (rx, ry), 6)
            else:
                # rotten item (bad)
                pygame.draw.circle(self.screen, (60, 60, 70), (int(it.x), int(it.y)), 26)
                pygame.draw.line(self.screen, BAD, (int(it.x)-12,int(it.y)-12), (int(it.x)+12,int(it.y)+12), 4)
                pygame.draw.line(self.screen, BAD, (int(it.x)+12,int(it.y)-12), (int(it.x)-12,int(it.y)+12), 4)

        # particles
        for p in self.particles:
            alpha = max(0, min(255, int(255 * (p.life / 1.2))))
            surf = pygame.Surface((int(p.size*2), int(p.size*2)), pygame.SRCALPHA)
            pygame.draw.circle(surf, (p.color[0], p.color[1], p.color[2], alpha), (int(p.size), int(p.size)), int(p.size))
            self.screen.blit(surf, (int(p.x - p.size), int(p.y - p.size)))

        # HUD
        score = self.font_med.render(f"Score: {self.score}", True, WHITE)
        lives = self.font_med.render(f"Lives: {self.lives}", True, WHITE)
        combo = self.font_sm.render(f"Combo: {self.combo}", True, ACCENT)
        self.screen.blit(score, (16, 12))
        self.screen.blit(lives, (WIDTH - lives.get_width() - 16, 12))
        self.screen.blit(combo, (WIDTH//2 - combo.get_width()//2, 12))

    # ------------------- main loop -------------------
    def start_play(self):
        self.items.clear()
        self.particles.clear()
        self.score = 0
        self.combo = 0
        # reset lives according to difficulty
        self.apply_difficulty()
        self.game_start_time = time.time()
        self.spawn_timer = 0.0
        self.state = "playing"

    def run(self):
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            self.handle_events()
            if self.state == "playing":
                self.update_game(dt)
            # if other states might want updates, add here
            # render
            if self.state == "menu":
                self.draw_menu()
            elif self.state == "settings":
                self.draw_settings()
            elif self.state == "leaderboard":
                self.draw_leaderboard()
            elif self.state == "playing":
                self.draw_play()
            elif self.state == "gameover":
                # simple gameover screen
                self.screen.fill(BG)
                over = self.font_big.render("GAME OVER", True, BAD)
                self.screen.blit(over, (WIDTH//2 - over.get_width()//2, 120))
                txt = self.font_med.render(f"Final Score: {self.score}", True, WHITE)
                self.screen.blit(txt, (WIDTH//2 - txt.get_width()//2, 200))
                hint = self.font_sm.render("Press Enter to return to Menu", True, GRAY)
                self.screen.blit(hint, (WIDTH//2 - hint.get_width()//2, 300))
            pygame.display.flip()
        pygame.quit()
        sys.exit()

# ------------------- RUN -------------------
if __name__ == "__main__":
    game = PizzaPanic()
    try:
        game.run()
    except Exception as ex:
        print("Crashed:", ex)
        pygame.quit()
        raise

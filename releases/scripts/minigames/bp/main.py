"""
Bubble Pop Minigame (built on your BaseMinigame template)

Run:
pip install pygame
python bubble_pop.py
"""

import pygame
import sys
import json
import os
import math
import random
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict

# ------------------- CONFIG / SAVE PATH -------------------
USER_DIR = os.path.expandvars(r"%userprofile%")
MG_SAVE_DIR = Path(USER_DIR) / "Documents" / ".mgaio"
APP_NAME = "Bubble Pop"
SAVE_FOLDER = MG_SAVE_DIR / "Saves" / APP_NAME
SAVE_FOLDER.mkdir(parents=True, exist_ok=True)

SETTINGS_FILE = SAVE_FOLDER / "settings.json"
LEADERBOARD_FILE = SAVE_FOLDER / "leaderboard.json"

DEFAULT_SETTINGS = {
    "volume": 100,
    "sound": True,
    "difficulty": "normal",
    "keymap": {"action": pygame.K_SPACE},
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

# ------------------- BASE GAME CLASS (your template slightly adapted) -------------------
class BaseMinigame:
    WIDTH, HEIGHT = 800, 600
    FPS = 60

    def __init__(self):
        pygame.init()
        # try init mixer (audio)
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
        # ensure defaults exist
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

        # gameplay core (to be used by subclass)
        self.lives = 3

        # Joystick
        self.joystick = None
        self.detect_joystick()

        # create sounds
        self.sounds: Dict[str, pygame.mixer.Sound] = {}
        if self.mixer_available:
            self._create_sounds()
            self._apply_volume_to_sounds()

        # convenience: last combo time
        self.last_pop_time = 0.0

    # ---------- joystick ----------
    def detect_joystick(self):
        if pygame.joystick.get_count() > 0:
            js = pygame.joystick.Joystick(0)
            js.init()
            self.joystick = js
            print("Joystick detected:", js.get_name())

    # ---------- sound helpers ----------
    def _create_sounds(self):
        """Create small procedural sounds (8-bit unsigned PCM) and store as pygame.mixer.Sound objects."""
        try:
            sample_rate = 22050  # lower rate reduces CPU & memory for tiny sounds
            defs = {
                "select": (660, 0.06),
                "start": (880, 0.12),
                "action": (1200, 0.05),
                "cancel": (220, 0.08),
                "error": (160, 0.12),
                "pop": (900, 0.06),
                "gold": (1400, 0.16),
                "bomb": (120, 0.18),
            }
            for name, (hz, dur) in defs.items():
                n_samples = int(sample_rate * dur)
                buf = bytearray()
                max_amp = 127
                # simple linear envelope to avoid clicks
                for i in range(n_samples):
                    t = i / sample_rate
                    env = 1.0 - (i / n_samples)  # simple decay envelope
                    v = int(max_amp * math.sin(2 * math.pi * hz * t) * env)
                    buf.append(v + 128)  # convert signed [-127..127] -> unsigned [1..255]
                try:
                    snd = pygame.mixer.Sound(buffer=bytes(buf))
                    self.sounds[name] = snd
                except Exception as e:
                    print(f"Failed to create sound {name}:", e)
            for k in ("select", "start", "action", "cancel", "error", "pop", "gold", "bomb"):
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
        """Play sound by name if audio available and sound setting enabled."""
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
        """Override this in subclass or add your game logic here"""
        pass

    def handle_input(self, key=None, joy_event=None):
        """Override this in subclass"""
        if key == self.settings["keymap"]["action"]:
            print("Action key pressed!")
            self.play_sound("action")

    def emit_particle(self, x, y, color=(255, 200, 60), amount=6):
        for _ in range(amount):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(40, 220)
            p = Particle(
                x=x,
                y=y,
                vx=math.cos(angle) * speed,
                vy=math.sin(angle) * speed,
                life=random.uniform(0.4, 1.0),
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
        self.screen.fill((18, 24, 38))
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
        title = self.font_big.render(APP_NAME, True, (180, 230, 255))
        self.screen.blit(title, (self.WIDTH//2 - title.get_width()//2, 60))

        info = self.font_med.render("Enter = Start    S = Settings    L = Leaderboard", True, (200, 200, 200))
        self.screen.blit(info, (self.WIDTH//2 - info.get_width()//2, 150))

        start_rect = pygame.Rect(self.WIDTH//2 - 140, 240, 280, 44)
        settings_rect = pygame.Rect(self.WIDTH//2 - 140, 300, 280, 44)
        leader_rect = pygame.Rect(self.WIDTH//2 - 140, 360, 280, 44)

        pygame.draw.rect(self.screen, (28, 36, 52), start_rect, border_radius=8)
        pygame.draw.rect(self.screen, (28, 36, 52), settings_rect, border_radius=8)
        pygame.draw.rect(self.screen, (28, 36, 52), leader_rect, border_radius=8)

        start_txt = self.font_med.render("Press Enter to Start", True, (230,230,230))
        settings_txt = self.font_med.render("S — Settings", True, (230,230,230))
        leader_txt = self.font_med.render("L — Leaderboard", True, (230,230,230))

        self.screen.blit(start_txt, (start_rect.x + 18, start_rect.y + 8))
        self.screen.blit(settings_txt, (settings_rect.x + 18, settings_rect.y + 8))
        self.screen.blit(leader_txt, (leader_rect.x + 18, leader_rect.y + 8))

        foot = self.font_sm.render("Esc = Quit", True, (150,150,150))
        self.screen.blit(foot, (12, self.HEIGHT - 28))

    def draw_settings(self):
        title = self.font_big.render("Settings", True, (180, 230, 255))
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
        title = self.font_big.render("Leaderboard", True, (180, 230, 255))
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

    # ---------- start / stop ----------
    def start_play(self):
        self.state = "playing"
        self.score = 0
        self.lives = 3

    # ---------- event handling (default, subclasses can override) ----------
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
                elif self.state == "gameover":
                    # basic name input handling default (append chars)
                    if event.key == pygame.K_BACKSPACE:
                        self.player_name = self.player_name[:-1]
                    elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                        # save leaderboard
                        self.save_score_and_return()
                    else:
                        # printable characters
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

    def save_score_and_return(self):
        # Save to leaderboard
        entry = {"name": self.player_name.strip() or "Player", "score": int(self.score)}
        self.leaderboard.append(entry)
        # keep only top 100
        self.leaderboard = sorted(self.leaderboard, key=lambda x: x.get('score', 0), reverse=True)[:100]
        save_json(LEADERBOARD_FILE, self.leaderboard)
        self.play_sound("select")
        self.state = "leaderboard"

# ------------------- BUBBLE POP GAME (subclass) -------------------
class BubblePopGame(BaseMinigame):
    def __init__(self):
        super().__init__()
        # bubble list
        self.bubbles = []
        self.spawn_timer = 0.0
        self.spawn_interval = 0.9  # seconds; will decrease
        self.time_played = 0.0
        self.combo = 0
        self.combo_time = 0.9
        self.slow_until = 0.0
        self.player_name = "Player"

    def start_play(self):
        super().start_play()
        self.bubbles.clear()
        self.spawn_timer = 0.0
        self.spawn_interval = 0.9
        self.time_played = 0.0
        self.combo = 0
        self.combo_expire = 0.0
        self.slow_until = 0.0
        self.player_name = "Player"

    def spawn_bubble(self):
        # bubble properties: x,y,vy,radius,type
        r = random.randint(18, 44)
        x = random.randint(r + 10, self.WIDTH - r - 10)
        y = self.HEIGHT + r + 10
        base_speed = random.uniform(70, 160)
        # difficulty modifies base speed
        diff = self.settings.get("difficulty", "normal")
        if diff == "easy":
            base_speed *= 0.8
        elif diff == "hard":
            base_speed *= 1.2
        # type: normal, gold, bomb, slow
        t_roll = random.random()
        if t_roll < 0.04:
            btype = "gold"
        elif t_roll < 0.08:
            btype = "bomb"
        elif t_roll < 0.13:
            btype = "slow"
        else:
            btype = "normal"
        bubble = {
            "x": x, "y": y, "vy": -base_speed, "r": r,
            "type": btype, "popped": False, "score": 1 if r >= 30 else 2
        }
        # small bubbles worth more (reverse)
        if r < 28:
            bubble["score"] = 3
        if btype == "gold":
            bubble["score"] = 8
        self.bubbles.append(bubble)

    def update_game(self, dt):
        self.time_played += dt
        # difficulty progression: spawn faster over time
        self.spawn_interval = max(0.28, 0.9 - (self.time_played * 0.02))
        self.spawn_timer += dt
        if self.spawn_timer >= self.spawn_interval:
            self.spawn_bubble()
            self.spawn_timer = 0.0

        # active slow power-up reduces speeds
        slow_factor = 0.5 if self.slow_until > pygame.time.get_ticks()/1000.0 else 1.0

        for b in list(self.bubbles):
            b["y"] += b["vy"] * dt * slow_factor
            # slight horizontal drift
            b["x"] += math.sin((b["y"] + b["x"]) * 0.01) * 8 * dt * 60
            # reached top?
            if b["y"] + b["r"] <= 0 and not b.get("popped"):
                # lose life
                self.bubbles.remove(b)
                self.lives -= 1
                # particle effect at top
                self.emit_particle(max(20, min(self.WIDTH-20, b["x"])), 6, color=(180, 40, 40))
                self.play_sound("error")
                # reset combo
                self.combo = 0
                if self.lives <= 0:
                    self.state = "gameover"
                    # prepare name empty for input
                    self.player_name = "Player"
            elif b.get("popped"):
                # popped bubble floats then removed by particle logic
                try:
                    self.bubbles.remove(b)
                except ValueError:
                    pass

        # combo expiry
        if self.combo > 0 and pygame.time.get_ticks()/1000.0 - self.last_pop_time > self.combo_time:
            self.combo = 0

    def handle_input(self, key=None, joy_event=None):
        # action key: pop nearest bubble under pointer (if using keyboard we'll pop nearest bubble to center)
        if key:
            if key == self.settings["keymap"]["action"]:
                # keyboard action: pop the largest visible bubble near center (gamepad)
                cx, cy = self.WIDTH // 2, self.HEIGHT - 80
                popped = self.pop_nearest_point(cx, cy)
                if popped:
                    self.play_sound("action")
        if joy_event:
            # on joystick button press attempt to pop near center as well
            if getattr(joy_event, "type", None) == pygame.JOYBUTTONDOWN:
                btn = joy_event.button
                mapped = self.settings.get("joymap", {}).get("action", {})
                if mapped and mapped.get("type") == "button" and mapped.get("id") == btn:
                    cx, cy = self.WIDTH // 2, self.HEIGHT - 80
                    self.pop_nearest_point(cx, cy)

    def pop_at(self, x, y):
        """Try to pop any bubble at x,y. Returns True if popped."""
        popped_any = False
        popped_list = []
        for b in list(self.bubbles):
            dx = b["x"] - x
            dy = b["y"] - y
            if dx*dx + dy*dy <= (b["r"] * b["r"]):
                popped_list.append(b)

        # if multiple popped by a click, handle them all (combo)
        if popped_list:
            for b in popped_list:
                self._handle_pop(b, x, y)
                popped_any = True
        return popped_any

    def pop_nearest_point(self, x, y):
        # find nearest bubble within a radius
        best = None
        bestd = 999999
        for b in self.bubbles:
            d = (b["x"]-x)**2 + (b["y"]-y)**2
            if d < bestd and d <= ( (b["r"]+40)**2 ):
                bestd = d
                best = b
        if best:
            self._handle_pop(best, x, y)
            return True
        return False

    def _handle_pop(self, b, click_x, click_y):
        # mark popped and spawn particles, adjust score, special effects
        if b.get("popped"):
            return
        b["popped"] = True
        # score
        add = b.get("score", 1)
        # combo: if popped within combo_time, increase multiplier
        now = pygame.time.get_ticks()/1000.0
        if now - self.last_pop_time < self.combo_time:
            self.combo += 1
        else:
            self.combo = 1
        self.last_pop_time = now
        mult = 1 + (self.combo - 1) * 0.25
        add_score = int(add * mult)
        self.score += add_score

        # particles + sound
        color = (120, 200, 255)
        if b["type"] == "gold":
            color = (255, 215, 80)
            self.play_sound("gold")
            # gold grants bonus
            self.score += 4
        elif b["type"] == "bomb":
            self.play_sound("bomb")
            # pop nearby bubbles
            to_explode = [bb for bb in list(self.bubbles) if (bb is not b) and ((bb["x"]-b["x"])**2 + (bb["y"]-b["y"])**2 <= ( (b["r"]*3)**2 ))]
            for bb in to_explode:
                if not bb.get("popped"):
                    self._handle_pop(bb, bb["x"], bb["y"])
            color = (220, 90, 90)
        elif b["type"] == "slow":
            # slow down for 3 seconds
            self.slow_until = pygame.time.get_ticks()/1000.0 + 3.0
            color = (160, 220, 160)
            self.play_sound("select")
        else:
            self.play_sound("pop")

        # spawn particles
        self.emit_particle(b["x"], b["y"], color=color, amount=10)

    # override event handling so clicks pop bubbles while preserving menu behavior
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
                    # keyboard fallback to pop near bottom center
                    if event.key == self.settings.get("keymap", {}).get("action", pygame.K_SPACE):
                        cx, cy = pygame.mouse.get_pos()
                        # if mouse is on screen, pop at cursor; else pop near bottom middle
                        if cx is None:
                            cx, cy = self.WIDTH//2, self.HEIGHT - 80
                        popped = self.pop_at(cx, cy)
                        if not popped:
                            # small penalty or sound for miss
                            self.play_sound("error")
                    else:
                        # other keys could map to joystick actions
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
                    # for simplicity: joystick button press pops nearest bubble to center or mouse
                    if event.type == pygame.JOYBUTTONDOWN:
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
                    # click to pop
                    popped = self.pop_at(mx, my)
                    if not popped:
                        # optionally, small feedback on miss
                        self.play_sound("error")

    def draw_game(self):
        # background gradient-ish (simple)
        self.screen.fill((18, 24, 38))
        # draw bubbles (sorted by radius so small are on top)
        for b in sorted(self.bubbles, key=lambda x: x["r"]):
            # circle with slight highlight
            base_col = (120, 200, 255)
            if b["type"] == "gold":
                base_col = (255, 215, 80)
            elif b["type"] == "bomb":
                base_col = (220, 100, 100)
            elif b["type"] == "slow":
                base_col = (160, 220, 160)
            # draw main circle
            pygame.draw.circle(self.screen, base_col, (int(b["x"]), int(b["y"])), int(b["r"]))
            # highlight
            pygame.draw.circle(self.screen, (255,255,255,50), (int(b["x"] - b["r"]*0.3), int(b["y"] - b["r"]*0.45)), max(2, int(b["r"]*0.35)), 2)

        # ui: score and lives
        score_text = self.font_med.render(f"Score: {self.score}", True, (240,240,240))
        self.screen.blit(score_text, (18, 18))
        lives_text = self.font_med.render("Lives: " + "❤ " * self.lives, True, (255, 140, 140))
        self.screen.blit(lives_text, (18, 48))

        # combo indicator
        if self.combo > 1:
            combo_text = self.font_med.render(f"Combo x{self.combo}", True, (255, 220, 120))
            self.screen.blit(combo_text, (self.WIDTH - combo_text.get_width() - 18, 18))

        # slow status
        if self.slow_until > pygame.time.get_ticks()/1000.0:
            rem = int(self.slow_until - pygame.time.get_ticks()/1000.0)
            slow_text = self.font_sm.render(f"Slow: {rem}s", True, (180,240,180))
            self.screen.blit(slow_text, (18, 80))

        # footer instruction
        footer = self.font_sm.render("Click bubbles to pop • Don't let them escape • Esc to quit", True, (180,180,200))
        self.screen.blit(footer, (self.WIDTH//2 - footer.get_width()//2, self.HEIGHT - 28))

# ------------------- RUN -------------------
if __name__ == "__main__":
    game = BubblePopGame()
    game.run()

"""
Ice Bath Simulator Minigame (Pygame)
Title: Ice Bath Simulator
Description: Mash keys to survive a freezing bath! Keep your body temperature up by rapidly pressing keys/buttons.
Features:
- Start Menu / Settings / Leaderboard (JSON)
- Saveable settings and leaderboard (JSON)
- Keyboard + Joystick + Mouse support
- Particle system (snowflakes when cold, steam when warm)
- Procedural sound effects (no external files)
- Score based on survival time and efficiency
Requirements:
pip install pygame
Run:
python ice_bath_simulator.py
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
APP_NAME = "Ice Bath Simulator"
SAVE_FOLDER = MG_SAVE_DIR / "Saves" / APP_NAME
SAVE_FOLDER.mkdir(parents=True, exist_ok=True)

SETTINGS_FILE = SAVE_FOLDER / "settings.json"
LEADERBOARD_FILE = SAVE_FOLDER / "leaderboard.json"

DEFAULT_SETTINGS = {
    "volume": 90,
    "sound": True,
    "difficulty": "normal",  # easy / normal / hard
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

# ------------------- BASE MINIGAME (adapted) -------------------
class BaseMinigame:
    WIDTH, HEIGHT = 900, 640
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
        """Create tiny procedural sounds (simple sine waves)"""
        try:
            sample_rate = 22050
            defs = {
                "select": (660, 0.06),
                "start": (880, 0.12),
                "mash": (1200, 0.03),
                "shiver": (220, 0.08),
                "steam": (1500, 0.06),
                "fail": (160, 0.18),
                "success": (1400, 0.12),
            }
            for name, (hz, dur) in defs.items():
                n_samples = int(sample_rate * dur)
                buf = bytearray()
                max_amp = 127
                for i in range(n_samples):
                    t = i / sample_rate
                    env = 1.0 - (i / n_samples)
                    # small vibrato for some sounds
                    vib = 1.0 + 0.02 * math.sin(2*math.pi*6*t) if name in ("mash", "steam") else 1.0
                    v = int(max_amp * math.sin(2 * math.pi * hz * t * vib) * env)
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
            self.play_sound("mash")

    def emit_particle(self, x, y, color=(255, 200, 60), amount=6):
        for _ in range(amount):
            angle = random.uniform(-math.pi, 0)
            speed = random.uniform(20, 180)
            p = Particle(
                x=x + random.uniform(-10, 10),
                y=y + random.uniform(-8, 8),
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
                        self.play_sound("select" if self.settings["sound"] else "fail")
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
                    # key mash handling forwarded to game
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
                    start_rect = pygame.Rect(self.WIDTH//2 - 160, 260, 320, 48)
                    settings_rect = pygame.Rect(self.WIDTH//2 - 160, 330, 320, 48)
                    leader_rect = pygame.Rect(self.WIDTH//2 - 160, 400, 320, 48)
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
                    # clicking anywhere counts as a mash (for mobile / mouse)
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
        self.screen.fill((18, 22, 30))
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
        title = self.font_big.render(APP_NAME, True, (200, 230, 255))
        self.screen.blit(title, (self.WIDTH//2 - title.get_width()//2, 52))
        info = self.font_med.render("Enter = Start    S = Settings    L = Leaderboard", True, (200, 200, 200))
        self.screen.blit(info, (self.WIDTH//2 - info.get_width()//2, 140))
        start_rect = pygame.Rect(self.WIDTH//2 - 160, 260, 320, 48)
        settings_rect = pygame.Rect(self.WIDTH//2 - 160, 330, 320, 48)
        leader_rect = pygame.Rect(self.WIDTH//2 - 160, 400, 320, 48)
        pygame.draw.rect(self.screen, (36, 40, 48), start_rect, border_radius=8)
        pygame.draw.rect(self.screen, (36, 40, 48), settings_rect, border_radius=8)
        pygame.draw.rect(self.screen, (36, 40, 48), leader_rect, border_radius=8)
        self.screen.blit(self.font_med.render("Start", True, (240,240,240)), (start_rect.x+26, start_rect.y+12))
        self.screen.blit(self.font_med.render("Settings", True, (240,240,240)), (settings_rect.x+26, settings_rect.y+12))
        self.screen.blit(self.font_med.render("Leaderboard", True, (240,240,240)), (leader_rect.x+26, leader_rect.y+12))
        foot = self.font_sm.render("Esc = Quit", True, (160,160,160))
        self.screen.blit(foot, (12, self.HEIGHT - 28))

    def draw_settings(self):
        title = self.font_big.render("Settings", True, (200,230,255))
        self.screen.blit(title, (48, 36))
        sound_state = self.settings.get("sound", True)
        vol = self.settings.get("volume", 90)
        txt1 = self.font_med.render(f"Sound: {'On' if sound_state else 'Off'} (Press SPACE)", True, (240,240,240))
        txt2 = self.font_med.render(f"Volume: {vol} (Up/Down)", True, (240,240,240))
        diff = self.settings.get("difficulty", "normal")
        txt3 = self.font_med.render(f"Difficulty: {diff} (Up/Down in Settings cycles)", True, (200,200,200))
        hint = self.font_sm.render("Press Esc to return to Menu", True, (180,180,180))
        self.screen.blit(txt1, (48, 140))
        self.screen.blit(txt2, (48, 180))
        self.screen.blit(txt3, (48, 220))
        self.screen.blit(hint, (48, 260))

    def draw_leaderboard(self):
        title = self.font_big.render("Leaderboard", True, (200,230,255))
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
        # to be overridden by minigame
        score_text = self.font_med.render(f"Score: {self.score}", True, (245,245,245))
        self.screen.blit(score_text, (16, 16))

    def draw_gameover(self):
        title = self.font_big.render("Game Over", True, (255, 140, 120))
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

# ------------------- ICE BATH GAME -------------------
class IceBathGame(BaseMinigame):
    def __init__(self):
        super().__init__()
        # game variables
        self.body_temp = 36.5       # degrees Celsius, start normal
        self.min_temp = 25.0        # death threshold
        self.max_temp = 40.0        # "overheated" cap
        self.temp_decay = 4.0       # deg/sec baseline cooling from cold water
        self.mash_power = 0.12      # temp increase per successful mash (tunable)
        self.mash_buffer = 0.0      # accumulative heat from mashes applied smoothly
        self.survival_time = 0.0
        self.alive = True
        self.start_time = 0.0
        self.best_streak = 0
        self.current_streak = 0
        self.last_mash_time = 0.0
        self.mashes_in_second = 0
        self.mash_window = []
        self.difficulty_map = {"easy": 0.7, "normal": 1.0, "hard": 1.3}
        self.player_name = "Player"
        self.cooldown_visual = 0.0

    def start_play(self):
        super().start_play()
        # difficulty affects decay and required mash power
        diff = self.settings.get("difficulty", "normal")
        mult = self.difficulty_map.get(diff, 1.0)
        self.temp_decay = 3.0 * mult + random.uniform(0.0, 1.2) * mult
        self.mash_power = 0.10 / mult
        # reset
        self.body_temp = 34.0  # start slightly chilled
        self.survival_time = 0.0
        self.start_time = time.time()
        self.alive = True
        self.mash_buffer = 0.0
        self.current_streak = 0
        self.best_streak = 0
        self.mash_window = []
        self.cooldown_visual = 0.0
        self.score = 0
        self.play_sound("start")

    def handle_input(self, key=None, joy_event=None):
        # Any keypress (or action key) increases mash count
        pressed = False
        if key:
            # count any printable / action / arrow keys as mash, but ignore Escape
            if key != pygame.K_ESCAPE:
                pressed = True
        if joy_event:
            if getattr(joy_event, "type", None) == pygame.JOYBUTTONDOWN:
                pressed = True
            elif getattr(joy_event, "type", None) == pygame.JOYAXISMOTION:
                # treat axis flicks as mash if large
                if abs(joy_event.value) > 0.8:
                    pressed = True
        if pressed:
            now = time.time()
            # register mash
            self.mash_window.append(now)
            # prune older than 1s
            self.mash_window = [t for t in self.mash_window if now - t <= 1.0]
            self.mashes_in_second = len(self.mash_window)
            # immediate small feedback
            self.mash_buffer += self.mash_power
            self.cooldown_visual = 0.18
            # streak logic: if mashes close together increase combo
            if now - self.last_mash_time <= 0.8:
                self.current_streak += 1
            else:
                self.current_streak = 1
            self.best_streak = max(self.best_streak, self.current_streak)
            self.last_mash_time = now
            # particle + sound feedback
            self.emit_particle(self.WIDTH//2 + random.uniform(-40,40), self.HEIGHT//2 + random.uniform(-60,60), color=(200,230,255), amount=8)
            # mash sound (higher pitch if faster)
            if self.mashes_in_second >= 8:
                self.play_sound("steam")
            else:
                self.play_sound("mash")

    def update_game(self, dt):
        if not self.alive:
            return
        # cooling: body temp drops toward water temperature (assume water ~0C for extremes)
        water_temp = 0.0  # icy bath
        # natural cooling proportional to difference and decay rate
        cooling = (self.body_temp - water_temp) * 0.02 * self.temp_decay
        # plus base decay per second (warmer bodies lose heat faster in water)
        self.body_temp -= cooling * dt
        # apply mash_buffer gradually
        if self.mash_buffer > 0:
            apply = min(self.mash_buffer, 2.0 * dt)  # smooth application
            self.body_temp += apply
            self.mash_buffer -= apply
        # small passive drift down each second to make it challenging
        self.body_temp -= 0.8 * dt * (self.difficulty_map.get(self.settings.get("difficulty", "normal"),1.0))
        # clamp
        self.body_temp = max(self.min_temp - 5.0, min(self.max_temp + 5.0, self.body_temp))
        # survival time and score calc
        self.survival_time = time.time() - self.start_time
        # base score is survival seconds * 10 + streak bonus
        self.score = int(self.survival_time * 10 + self.best_streak * 5)
        # visual cooldown reduction
        self.cooldown_visual = max(0.0, self.cooldown_visual - dt)
        # particles: if very cold produce snow, if warming produce steam
        if self.body_temp <= 30.0 and random.random() < 0.04:
            # snowflake
            x = random.uniform(40, self.WIDTH - 40)
            y = -6
            p = Particle(x=x, y=y, vx=random.uniform(-6,6), vy=random.uniform(30,80), life=random.uniform(2.0,4.0), size=random.uniform(2,4), color=(220,240,255))
            self.particles.append(p)
        if self.body_temp >= 36.8 and random.random() < 0.05:
            # steam near player
            self.emit_particle(self.WIDTH//2, self.HEIGHT//2 - 30, color=(240,240,220), amount=6)

        # check death
        if self.body_temp <= self.min_temp:
            self._die("hypothermia")
        # optional: overheating fail (rare)
        if self.body_temp >= 42.0:
            self._die("overheat")

    def _die(self, reason=""):
        self.alive = False
        self.play_sound("fail")
        # final score includes survival time
        self.state = "gameover"
        self.player_name = "Player"
        # particle burst
        self.emit_particle(self.WIDTH//2, self.HEIGHT//2, color=(240,140,140), amount=80)

    def draw_game(self):
        # background gradient: colder at top, warmer toward bottom
        top = (20, 30, 50)
        bot = (30, 34, 40)
        self.screen.fill(top)
        # subtle rectangle for bath area
        bath_rect = pygame.Rect(60, 100, self.WIDTH - 120, self.HEIGHT - 240)
        pygame.draw.rect(self.screen, (12, 18, 28), bath_rect, border_radius=10)
        # header: score, time, temp
        score_text = self.font_med.render(f"Score: {self.score}", True, (235,235,240))
        self.screen.blit(score_text, (18, 18))
        time_text = self.font_med.render(f"Time: {int(self.survival_time)}s", True, (235,235,240))
        self.screen.blit(time_text, (160, 18))
        temp_text = self.font_med.render(f"Body Temp: {self.body_temp:.1f}°C", True, (235,235,240))
        self.screen.blit(temp_text, (300, 18))
        difficulty = self.settings.get("difficulty", "normal")
        diff_text = self.font_med.render(f"Difficulty: {difficulty}", True, (200,200,220))
        self.screen.blit(diff_text, (520, 18))
        # draw a thermometer-like gauge at right
        gauge_rect = pygame.Rect(self.WIDTH - 120, 80, 36, 420)
        pygame.draw.rect(self.screen, (20,20,30), gauge_rect, border_radius=8)
        # map temp range to gauge
        temp_min = self.min_temp - 5
        temp_max = self.max_temp + 5
        frac = (self.body_temp - temp_min) / (temp_max - temp_min)
        frac = max(0.0, min(1.0, frac))
        fill_h = int(frac * (gauge_rect.height - 12))
        fill_rect = pygame.Rect(gauge_rect.x + 6, gauge_rect.y + gauge_rect.height - 6 - fill_h, gauge_rect.width - 12, fill_h)
        # color transitions blue -> yellow -> red
        if frac < 0.5:
            col = (int(60 + 190 * frac), int(160 + 60 * frac), 240)
        else:
            col = (240, int(200 - 120 * (frac - 0.5) * 2), int(60 - 40 * (frac - 0.5) * 2))
        pygame.draw.rect(self.screen, col, fill_rect, border_radius=6)
        pygame.draw.rect(self.screen, (80,80,90), gauge_rect, 3, border_radius=8)
        # center: a simple silhouette of a person in the bath
        torso_col = (150, 180, 220) if self.body_temp >= 35.5 else (120, 160, 200)
        head_col = (220, 210, 200) if self.body_temp >= 34.0 else (200, 200, 200)
        centerx = self.WIDTH//2
        centery = self.HEIGHT//2 + 20
        # torso rectangle
        pygame.draw.ellipse(self.screen, torso_col, (centerx - 60, centery - 40, 120, 80))
        # head
        pygame.draw.circle(self.screen, head_col, (centerx, centery - 80), 26)
        # goggles/shivering lines if cold
        if self.body_temp < 32.5:
            # draw shiver lines
            for i in range(6):
                x = centerx - 90 + i * 30
                pygame.draw.line(self.screen, (220,240,255), (x, centery - 120), (x - 8, centery - 132), 2)
        # mash indicator (speed)
        mash_bar_rect = pygame.Rect(80, self.HEIGHT - 120, self.WIDTH - 320, 28)
        pygame.draw.rect(self.screen, (40,40,48), mash_bar_rect, border_radius=6)
        # fill proportionally to recent mashes (0..12)
        pct = min(1.0, self.mashes_in_second / 12.0)
        fill = pygame.Rect(mash_bar_rect.x + 2, mash_bar_rect.y + 2, int((mash_bar_rect.width - 4) * pct), mash_bar_rect.height - 4)
        pygame.draw.rect(self.screen, (120, 220, 180), fill, border_radius=6)
        mash_txt = self.font_sm.render(f"Mash Rate: {self.mashes_in_second}/s  Streak: {self.current_streak}", True, (240,240,240))
        self.screen.blit(mash_txt, (mash_bar_rect.x + 8, mash_bar_rect.y - 22))
        # tips / feedback
        if self.cooldown_visual > 0.0:
            tip = self.font_med.render("Good! Keep mashing!", True, (200, 255, 210))
            self.screen.blit(tip, (self.WIDTH//2 - tip.get_width()//2, mash_bar_rect.y - 48))
        elif self.body_temp < 30.5:
            tip = self.font_med.render("Brrr... Mash faster! ❄️", True, (200, 220, 255))
            self.screen.blit(tip, (self.WIDTH//2 - tip.get_width()//2, mash_bar_rect.y - 48))
        else:
            tip = self.font_med.render("You're warming up — keep it up! 🔥", True, (255, 220, 180))
            self.screen.blit(tip, (self.WIDTH//2 - tip.get_width()//2, mash_bar_rect.y - 48))
        # footer
        footer = self.font_sm.render("Press any key / click rapidly to heat up • Press Esc to quit", True, (200,200,200))
        self.screen.blit(footer, (self.WIDTH//2 - footer.get_width()//2, self.HEIGHT - 28))

    # override run to ensure leaderboard exists (already done in base, but keep for clarity)
    def run(self):
        if not Path(LEADERBOARD_FILE).exists():
            save_json(Path(LEADERBOARD_FILE), [])
        super().run()

# ------------------- RUN -------------------
if __name__ == "__main__":
    game = IceBathGame()
    game.run()

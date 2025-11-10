"""
Color Slider Minigame (Pygame)
Title: Color Slider
Description: Adjust a slider to match a moving color bar.
Features:
- Start Menu / Settings / Leaderboard (JSON)
- Keyboard + Joystick support
- Particles
- Procedural sound effects (no external files)
- Full round/timer/score/lives flow
Requirements:
pip install pygame
Run:
python color_slider.py
"""

import pygame
import sys
import json
import os
import math
import random
import colorsys
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict

# ------------------- CONFIG / SAVE PATH -------------------
USER_DIR = os.path.expandvars(r"%userprofile%")
MG_SAVE_DIR = Path(USER_DIR) / "Documents" / ".mgaio"
APP_NAME = "Color Slider"
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

def hsv_to_rgb8(h, s, v):
    """h in [0,360], s,v in [0,1] -> returns (r,g,b) 0-255"""
    r, g, b = colorsys.hsv_to_rgb(h / 360.0, s, v)
    return (int(r * 255), int(g * 255), int(b * 255))

# ------------------- BASE GAME (adapted) -------------------
class BaseMinigame:
    WIDTH, HEIGHT = 900, 600
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
        self.font_big = pygame.font.SysFont("arial", 44, bold=True)
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
                "action": (1200, 0.05),
                "cancel": (220, 0.08),
                "error": (160, 0.12),
                "lock": (1000, 0.06),
                "success": (1400, 0.12),
                "fail": (220, 0.12),
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

    def update_game(self, dt):
        pass

    def handle_input(self, key=None, joy_event=None):
        if key == self.settings["keymap"]["action"]:
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

    def run(self):
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

    def handle_events(self):
        # minimal base; subclass may override
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

    def update_particles(self, dt):
        for p in list(self.particles):
            p.x += p.vx * dt
            p.y += p.vy * dt
            p.vy += 300 * dt
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
        self.screen.fill((20, 22, 28))
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
        title = self.font_big.render(APP_NAME, True, (220, 220, 255))
        self.screen.blit(title, (self.WIDTH//2 - title.get_width()//2, 60))
        info = self.font_med.render("Enter = Start    S = Settings    L = Leaderboard", True, (200, 200, 200))
        self.screen.blit(info, (self.WIDTH//2 - info.get_width()//2, 140))
        start_rect = pygame.Rect(self.WIDTH//2 - 160, 260, 320, 48)
        settings_rect = pygame.Rect(self.WIDTH//2 - 160, 330, 320, 48)
        leader_rect = pygame.Rect(self.WIDTH//2 - 160, 400, 320, 48)
        pygame.draw.rect(self.screen, (36, 40, 56), start_rect, border_radius=8)
        pygame.draw.rect(self.screen, (36, 40, 56), settings_rect, border_radius=8)
        pygame.draw.rect(self.screen, (36, 40, 56), leader_rect, border_radius=8)
        self.screen.blit(self.font_med.render("Start", True, (240,240,240)), (start_rect.x+30, start_rect.y+12))
        self.screen.blit(self.font_med.render("Settings", True, (240,240,240)), (settings_rect.x+30, settings_rect.y+12))
        self.screen.blit(self.font_med.render("Leaderboard", True, (240,240,240)), (leader_rect.x+30, leader_rect.y+12))
        foot = self.font_sm.render("Esc = Quit", True, (150,150,150))
        self.screen.blit(foot, (12, self.HEIGHT - 28))

    def draw_settings(self):
        title = self.font_big.render("Settings", True, (220, 220, 255))
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
        title = self.font_big.render("Leaderboard", True, (220, 220, 255))
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
        score_text = self.font_med.render(f"Score: {self.score}", True, (245, 245, 245))
        self.screen.blit(score_text, (16, 16))

    def draw_gameover(self):
        title = self.font_big.render("Game Over", True, (255, 150, 150))
        self.screen.blit(title, (self.WIDTH//2 - title.get_width()//2, 72))
        stat = self.font_med.render(f"Score: {self.score}", True, (240,240,240))
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

# ------------------- COLOR SLIDER GAME -------------------
class ColorSliderGame(BaseMinigame):
    def __init__(self):
        super().__init__()
        # game variables
        self.slider_hue = 0.0               # player's selected hue (0-360)
        self.target_hue = random.uniform(0, 360)
        self.round_time = 12.0              # seconds per round
        self.time_left = self.round_time
        self.lives = 3
        self.round = 1
        self.bar_offset = 0.0               # pixel offset for moving gradient
        self.bar_speed = 60.0               # pixels/second, increases with rounds
        self.result_show_until = 0.0        # show hit/miss feedback
        self.last_result = None             # ("hit"|"miss", diff)
        self.player_name = "Player"
        # difficulty tweaks
        self.diff_map = {"easy": 0.8, "normal": 1.0, "hard": 1.25}

    def start_play(self):
        super().start_play()
        self.slider_hue = random.uniform(0, 360)
        self.target_hue = random.uniform(0, 360)
        self.time_left = self.round_time
        self.lives = 3
        self.round = 1
        self.bar_speed = 60.0
        self.score = 0
        self.result_show_until = 0.0
        self.last_result = None

    def update_game(self, dt):
        self.time_left -= dt
        self.bar_offset += self.bar_speed * dt
        # loop offset
        if self.bar_offset > self.WIDTH:
            self.bar_offset -= self.WIDTH

        # increase difficulty slowly
        self.bar_speed = 60.0 + (self.round - 1) * 12.0
        self.bar_speed *= self.diff_map.get(self.settings.get("difficulty", "normal"), 1.0)

        # time up -> miss
        if self.time_left <= 0 and self.state == "playing":
            self._handle_miss("Time!")
        # clear result display after 1s
        if self.result_show_until and pygame.time.get_ticks() / 1000.0 > self.result_show_until:
            self.last_result = None
            self.result_show_until = 0.0

    def handle_input(self, key=None, joy_event=None):
        # keyboard arrows adjust slider
        if key:
            if key == pygame.K_LEFT:
                self.slider_hue = (self.slider_hue - 6) % 360
            elif key == pygame.K_RIGHT:
                self.slider_hue = (self.slider_hue + 6) % 360
            elif key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_KP_ENTER):
                self._lock_in()
        if joy_event:
            if getattr(joy_event, "type", None) == pygame.JOYAXISMOTION:
                # assume left-right axis 0 yields -1..1
                ax = joy_event.value
                # small change per motion
                self.slider_hue = (self.slider_hue + ax * 4) % 360
            elif getattr(joy_event, "type", None) == pygame.JOYBUTTONDOWN:
                self._lock_in()

    def _lock_in(self):
        """Player locks current slider hue as guess"""
        if self.state != "playing":
            return
        self.play_sound("lock")
        diff = min(abs(self.slider_hue - self.target_hue), 360 - abs(self.slider_hue - self.target_hue))
        # scoring thresholds
        if diff <= 6:
            pts = 12
            res = "Perfect"
            self.play_sound("success")
        elif diff <= 18:
            pts = 8
            res = "Great"
            self.play_sound("success")
        elif diff <= 36:
            pts = 4
            res = "Good"
            self.play_sound("select")
        else:
            pts = 0
            res = "Miss"
            self.play_sound("fail")
        if pts > 0:
            self.score += pts
        else:
            self.lives -= 1
            self.emit_particle(self.WIDTH//2, self.HEIGHT//2, color=(220,80,80), amount=18)
        self.last_result = (res, diff, pts)
        self.result_show_until = pygame.time.get_ticks() / 1000.0 + 1.0
        # prepare next round or end
        if self.lives <= 0:
            self.state = "gameover"
            self.player_name = "Player"
        else:
            self.round += 1
            self.target_hue = random.uniform(0, 360)
            self.time_left = self.round_time
            # small particle celebration if points
            if pts > 0:
                self.emit_particle(self.WIDTH//2, self.HEIGHT//2, color=(160, 230, 160), amount=12)

    def _handle_miss(self, reason=""):
        self.play_sound("fail")
        self.lives -= 1
        self.last_result = ("Miss", 999, 0)
        self.result_show_until = pygame.time.get_ticks() / 1000.0 + 1.0
        self.emit_particle(self.WIDTH//2, 80, color=(220,120,120), amount=12)
        if self.lives <= 0:
            self.state = "gameover"
            self.player_name = "Player"
        else:
            # next round
            self.round += 1
            self.target_hue = random.uniform(0, 360)
            self.time_left = self.round_time

    def handle_events(self):
        # override to include mouse slider control + menu buttons
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
                # menu clicks
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
                    # slider area
                    slider_rect = pygame.Rect(80, self.HEIGHT - 120, self.WIDTH - 160, 28)
                    lock_rect = pygame.Rect(self.WIDTH - 180, self.HEIGHT - 72, 140, 38)
                    if slider_rect.collidepoint(mx, my):
                        # map x to hue
                        rel = (mx - slider_rect.x) / slider_rect.width
                        self.slider_hue = rel * 360.0
                    elif lock_rect.collidepoint(mx, my):
                        self._lock_in()

    def draw_game(self):
        # background
        self.screen.fill((24, 26, 34))

        # top: target color preview and info
        target_col = hsv_to_rgb8(self.target_hue, 0.8, 0.85)
        pygame.draw.rect(self.screen, target_col, (48, 72, 160, 160), border_radius=8)
        tlabel = self.font_med.render("Target", True, (220,220,220))
        self.screen.blit(tlabel, (48, 44))

        # center: moving gradient bar
        bar_rect = pygame.Rect(240, 96, self.WIDTH - 320, 120)
        self._draw_moving_gradient(bar_rect, offset=self.bar_offset)

        # slider preview (player color)
        player_col = hsv_to_rgb8(self.slider_hue, 0.8, 0.85)
        pygame.draw.rect(self.screen, player_col, (48, 260, 160, 60), border_radius=8)
        plabel = self.font_med.render("Your Color", True, (220,220,220))
        self.screen.blit(plabel, (48, 232))

        # score & lives & round & time
        score_text = self.font_med.render(f"Score: {self.score}", True, (230,230,230))
        self.screen.blit(score_text, (18, 18))
        lives_text = self.font_med.render("Lives: " + "❤ " * self.lives, True, (255,140,140))
        self.screen.blit(lives_text, (140, 18))
        round_text = self.font_med.render(f"Round: {self.round}", True, (230,230,230))
        self.screen.blit(round_text, (300, 18))
        time_text = self.font_med.render(f"Time: {int(self.time_left)}s", True, (230,230,230))
        self.screen.blit(time_text, (420, 18))

        # slider control
        slider_rect = pygame.Rect(80, self.HEIGHT - 120, self.WIDTH - 160, 28)
        pygame.draw.rect(self.screen, (40, 40, 40), slider_rect, border_radius=6)
        # knob position
        kx = slider_rect.x + int((self.slider_hue / 360.0) * slider_rect.width)
        pygame.draw.circle(self.screen, (220,220,220), (kx, slider_rect.centery), 12)
        # shade around knob with player's hue
        pygame.draw.circle(self.screen, player_col, (kx, slider_rect.centery), 9)

        # lock button
        lock_rect = pygame.Rect(self.WIDTH - 180, self.HEIGHT - 72, 140, 38)
        pygame.draw.rect(self.screen, (50, 90, 160), lock_rect, border_radius=8)
        ltxt = self.font_med.render("Lock (Enter/Space)", True, (255,255,255))
        self.screen.blit(ltxt, (lock_rect.x + 10, lock_rect.y + 8))

        # last result display
        if self.last_result:
            res, diff, pts = self.last_result
            res_txt = self.font_big.render(f"{res}", True, (255,255,255))
            self.screen.blit(res_txt, (self.WIDTH//2 - res_txt.get_width()//2, bar_rect.y + bar_rect.height + 16))
            if diff < 999:
                diff_txt = self.font_med.render(f"Diff: {int(diff)}°  (+{pts})", True, (200,200,200))
                self.screen.blit(diff_txt, (self.WIDTH//2 - diff_txt.get_width()//2, bar_rect.y + bar_rect.height + 64))

        # footer instruction
        footer = self.font_sm.render("Drag slider or use ← → to adjust hue • Lock your guess • Don't run out of lives", True, (180,180,200))
        self.screen.blit(footer, (self.WIDTH//2 - footer.get_width()//2, self.HEIGHT - 24))

    def _draw_moving_gradient(self, rect: pygame.Rect, offset: float = 0.0):
        # Draw gradient by columns; map each x to a hue (0..360), shifted by offset
        steps = rect.width
        for i in range(steps):
            # hue maps across width (cycle twice so variation)
            base_hue = ((i + offset) / rect.width) * 360.0 * 1.0
            hue = base_hue % 360.0
            col = hsv_to_rgb8(hue, 0.8, 0.85)
            pygame.draw.line(self.screen, col, (rect.x + i, rect.y), (rect.x + i, rect.y + rect.height))
        # draw border
        pygame.draw.rect(self.screen, (80, 80, 80), rect, 2, border_radius=6)
        # overlay target indicator on the gradient: a small vertical marker where target hue currently appears
        # Find approximate x where target hue is located within this gradient => solve hue = ((i+offset)/w)*360 mod 360
        # We'll search for i that minimizes circular distance:
        best_i = 0
        best_d = 9999
        for i in range(rect.width):
            hue = ((i + offset) / rect.width) * 360.0
            d = min(abs(hue - self.target_hue), 360 - abs(hue - self.target_hue))
            if d < best_d:
                best_d = d
                best_i = i
        tx = rect.x + best_i
        pygame.draw.line(self.screen, (255,255,255), (tx, rect.y), (tx, rect.y + rect.height), 3)
        # tiny arrow
        pygame.draw.polygon(self.screen, (255,255,255), [(tx, rect.y - 8), (tx - 6, rect.y - 2), (tx + 6, rect.y - 2)])

# ------------------- SAVE/LOAD STUBS (for compat) -------------------
def save_json(path: Path, data):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print("Save failed:", e)

def load_json(path: Path, default):
    if path.exists():
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return default

# ------------------- RUN -------------------
if __name__ == "__main__":
    game = ColorSliderGame()
    # make sure leaderboard exists
    if not Path(LEADERBOARD_FILE).exists():
        save_json(Path(LEADERBOARD_FILE), [])
    game.run()

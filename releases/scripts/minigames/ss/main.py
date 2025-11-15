"""
Snack Stack Minigame (Pygame)
Title: Snack Stack
Description: Catch falling snacks on your plate and stack them as high as possible without toppling!
Features:
- Start Menu / Settings / Leaderboard (JSON)
- Saveable settings and leaderboard
- Keyboard + Joystick support
- Particle system (visual flair)
- Procedural sound effects (no external files)
Requirements:
pip install pygame
Run:
python snack_stack.py
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
APP_NAME = "Snack Stack"
SAVE_FOLDER = MG_SAVE_DIR / "Saves" / APP_NAME
SAVE_FOLDER.mkdir(parents=True, exist_ok=True)

SETTINGS_FILE = SAVE_FOLDER / "settings.json"
LEADERBOARD_FILE = SAVE_FOLDER / "leaderboard.json"

DEFAULT_SETTINGS = {
    "volume": 100,
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

# ------------------- BASE GAME (adapted) -------------------
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
        self.font_big = pygame.font.SysFont("segoe ui emoji", 48, bold=True)
        self.font_med = pygame.font.SysFont("segoe ui emoji", 24)
        self.font_sm = pygame.font.SysFont("segoe ui emoji", 16)

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
                "pop": (1200, 0.05),
                "thump": (200, 0.12),
                "fail": (160, 0.12),
                "success": (1400, 0.12),
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
        if key == self.settings["keymap"].get("action"):
            self.play_sound("pop")

    def emit_particle(self, x, y, color=(255, 200, 60), amount=8):
        for _ in range(amount):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(40, 260)
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
        self.screen.fill((22, 20, 26))
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
        title = self.font_big.render(APP_NAME, True, (255, 210, 120))
        self.screen.blit(title, (self.WIDTH//2 - title.get_width()//2, 64))
        info = self.font_med.render("Enter = Start    S = Settings    L = Leaderboard", True, (200,200,200))
        self.screen.blit(info, (self.WIDTH//2 - info.get_width()//2, 140))
        start_rect = pygame.Rect(self.WIDTH//2 - 140, 240, 280, 44)
        settings_rect = pygame.Rect(self.WIDTH//2 - 140, 300, 280, 44)
        leader_rect = pygame.Rect(self.WIDTH//2 - 140, 360, 280, 44)
        pygame.draw.rect(self.screen, (40,40,40), start_rect, border_radius=8)
        pygame.draw.rect(self.screen, (40,40,40), settings_rect, border_radius=8)
        pygame.draw.rect(self.screen, (40,40,40), leader_rect, border_radius=8)
        self.screen.blit(self.font_med.render("Start", True, (240,240,240)), (start_rect.x+26, start_rect.y+10))
        self.screen.blit(self.font_med.render("Settings", True, (240,240,240)), (settings_rect.x+26, settings_rect.y+10))
        self.screen.blit(self.font_med.render("Leaderboard", True, (240,240,240)), (leader_rect.x+26, leader_rect.y+10))
        foot = self.font_sm.render("Esc = Quit", True, (160,160,160))
        self.screen.blit(foot, (12, self.HEIGHT - 28))

    def draw_settings(self):
        title = self.font_big.render("Settings", True, (255, 210, 120))
        self.screen.blit(title, (48, 36))
        sound_state = self.settings.get("sound", True)
        vol = self.settings.get("volume", 100)
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
        title = self.font_big.render("Leaderboard", True, (255, 210, 120))
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
        # placeholder header (subclasses draw content)
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

# ------------------- SNACK STACK GAME -------------------
class SnackStackGame(BaseMinigame):
    SNACK_TYPES = [
        {"name": "Donut", "w": 72, "h": 24, "col": (255, 180, 200)},
        {"name": "Burger", "w": 96, "h": 30, "col": (220, 160, 60)},
        {"name": "Pizza", "w": 88, "h": 28, "col": (240, 200, 90)},
        {"name": "Cupcake", "w": 64, "h": 30, "col": (200, 150, 230)},
        {"name": "Sushi", "w": 56, "h": 20, "col": (180, 220, 200)},
    ]

    def __init__(self):
        super().__init__()
        # plate position
        self.plate_x = self.WIDTH // 2
        self.plate_y = self.HEIGHT - 96
        self.plate_w = 220
        self.plate_h = 16
        self.plate_speed = 420.0  # px/s
        # falling snacks
        self.snacks: List[Dict] = []
        self.spawn_timer = 0.0
        self.spawn_interval = 1.0
        # stack: list of dicts with x offset relative to plate center and height
        self.stack: List[Dict] = []
        self.stack_height = 0.0
        # tilt metric: cumulative offset (simple)
        self.tilt = 0.0
        self.tilt_threshold = 140.0   # collapse if exceeded
        self.lives = 3
        self.round = 1
        self.time_played = 0.0
        self.difficulty_speed = {"easy": 0.8, "normal": 1.0, "hard": 1.25}
        self.player_name = "Player"
        # initial settings
        self.reset_game_state()

    def reset_game_state(self):
        self.snacks.clear()
        self.stack.clear()
        self.stack_height = 0.0
        self.tilt = 0.0
        self.spawn_timer = 0.0
        self.spawn_interval = 1.0
        self.score = 0
        self.lives = 3
        self.round = 1
        self.time_played = 0.0

    def start_play(self):
        super().start_play()
        self.plate_x = self.WIDTH // 2
        self.reset_game_state()
        self.play_sound("start")

    def spawn_snack(self):
        st = random.choice(self.SNACK_TYPES)
        w = st["w"]
        h = st["h"]
        x = random.uniform(80 + w/2, self.WIDTH - 80 - w/2)
        y = -60  # above screen
        vy = random.uniform(140, 220) * self.difficulty_speed.get(self.settings.get("difficulty","normal"),1.0)
        snack = {
            "type": st["name"],
            "w": w, "h": h, "col": st["col"],
            "x": x, "y": y, "vy": vy,
            "landed": False
        }
        self.snacks.append(snack)

    def update_game(self, dt):
        self.time_played += dt
        # spawn faster with time/round
        diff = self.settings.get("difficulty", "normal")
        speed_mult = self.difficulty_speed.get(diff, 1.0)
        self.spawn_interval = max(0.48, 1.0 - (self.time_played * 0.02))
        self.spawn_timer += dt
        if self.spawn_timer >= self.spawn_interval:
            self.spawn_snack()
            self.spawn_timer = 0.0

        # move plate: keyboard or mouse
        keys = pygame.key.get_pressed()
        move = 0.0
        if keys[pygame.K_LEFT]:
            move = -1.0
        elif keys[pygame.K_RIGHT]:
            move = 1.0
        # joystick axis
        if self.joystick:
            try:
                ax = self.joystick.get_axis(0)
                if abs(ax) > 0.15:
                    move = ax
            except Exception:
                pass
        mx, my = pygame.mouse.get_pos()
        if pygame.mouse.get_focused() and (pygame.mouse.get_pressed()[0]):
            # dragging mode while mouse pressed
            move = 0.0
            self.plate_x = mx

        self.plate_x += move * self.plate_speed * dt
        self.plate_x = max(80 + self.plate_w//2, min(self.WIDTH - 80 - self.plate_w//2, self.plate_x))

        # update snacks
        for sn in list(self.snacks):
            if not sn["landed"]:
                sn["y"] += sn["vy"] * dt
                # check collision with top of stack or plate
                target_top_y = self.plate_y - self.stack_height
                # approximate collision when snack bottom reaches target_top_y
                if sn["y"] + sn["h"]/2 >= target_top_y:
                    # compute x offset relative to plate center
                    rel_x = sn["x"] - self.plate_x
                    # allowed offset based on plate width and snack width
                    allowed = (self.plate_w/2) - (sn["w"]/2)
                    # if stack exists, allow slightly less
                    if self.stack:
                        allowed *= 0.85
                    # If snack lands outside allowed, it lands but increases tilt and might fall
                    landed_x = max(-self.plate_w/2 + sn["w"]/2, min(self.plate_w/2 - sn["w"]/2, rel_x))
                    # create landed snack record with offset
                    landed = {
                        "type": sn["type"], "w": sn["w"], "h": sn["h"], "col": sn["col"],
                        "offset": landed_x,
                        "y": target_top_y - sn["h"]/2
                    }
                    self.stack.append(landed)
                    self.stack_height += sn["h"]
                    sn["landed"] = True
                    # tilt increases proportionally to how off-center the snack was
                    self.tilt += abs(rel_x) * 0.6
                    # score
                    gain = max(1, int(10 * (1.0 / (1.0 + abs(rel_x)/self.plate_w)) ))
                    self.score += gain
                    self.emit_particle(self.plate_x + landed_x, landed["y"], color=(200,240,160), amount=10)
                    self.play_sound("pop")
                    # small chance of special snack that reduces tilt
                    if random.random() < 0.06:
                        self.tilt = max(0.0, self.tilt - 18.0)
                        self.play_sound("success")
                    # remove snack object (landed ones we keep in stack)
                    try:
                        self.snacks.remove(sn)
                    except ValueError:
                        pass
                    # check tilt threshold
                    if self.tilt >= self.tilt_threshold:
                        self._collapse_stack()
                        return
            # remove snacks that fall off bottom (miss)
            if sn["y"] - sn["h"]/2 > self.HEIGHT + 60:
                try:
                    self.snacks.remove(sn)
                except ValueError:
                    pass
                # penalty for miss
                self.lives -= 1
                self.emit_particle(self.plate_x, self.plate_y - self.stack_height, color=(220,100,100), amount=14)
                self.play_sound("fail")
                if self.lives <= 0:
                    self.state = "gameover"
                    self.player_name = "Player"

        # slowly reduce tilt over time (player can correct)
        self.tilt = max(0.0, self.tilt - 6.0 * dt)

        # increase difficulty slightly with score
        if self.score // 80 + 1 > self.round:
            self.round += 1
            self.spawn_interval = max(0.4, self.spawn_interval - 0.1)
            self.play_sound("select")
            # nudge plate speed up
            self.plate_speed += 24

    def _collapse_stack(self):
        # emit big particles and play thump
        cx = self.plate_x
        cy = self.plate_y - self.stack_height/2
        self.emit_particle(cx, cy, color=(240,140,120), amount=60)
        self.play_sound("thump")
        # penalty: clear half the stack and lose life
        lose = max(1, len(self.stack)//2)
        for _ in range(lose):
            if self.stack:
                self.stack.pop()
        # recompute stack height
        self.stack_height = sum(s["h"] for s in self.stack)
        # big tilt reset but partial remain
        self.tilt = max(0.0, self.tilt * 0.35)
        self.lives -= 1
        if self.lives <= 0:
            self.state = "gameover"
            self.player_name = "Player"

    def handle_input(self, key=None, joy_event=None):
        # action key drops an emergency weight that reduces tilt slightly
        if key == self.settings.get("keymap", {}).get("action"):
            # drop weight: small reduction in tilt, consumes a small score penalty
            if self.score >= 3:
                self.score -= 3
                self.tilt = max(0.0, self.tilt - 22.0)
                self.emit_particle(self.plate_x, self.plate_y - self.stack_height, color=(160,200,240), amount=18)
                self.play_sound("success")
            else:
                self.play_sound("fail")
        if joy_event:
            if getattr(joy_event, "type", None) == pygame.JOYBUTTONDOWN:
                self.handle_input(key=self.settings.get("keymap", {}).get("action"))
            elif getattr(joy_event, "type", None) == pygame.JOYAXISMOTION:
                # handled in update_game by polling joystick axis
                pass

    def handle_events(self):
        # override to include mouse dragging plate & menu buttons
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
                        # toggle difficulty
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
                    # clicking near plate to move it to position
                    if my > self.plate_y - 140:
                        self.plate_x = mx

    def draw_game(self):
        # background
        self.screen.fill((30, 28, 34))
        # header info
        score_text = self.font_med.render(f"Score: {self.score}", True, (240,240,240))
        self.screen.blit(score_text, (18, 16))
        lives_text = self.font_med.render("Lives: " + "❤ " * self.lives, True, (255,140,140))
        self.screen.blit(lives_text, (160, 16))
        round_text = self.font_med.render(f"Round: {self.round}", True, (240,240,240))
        self.screen.blit(round_text, (320, 16))
        tilt_text = self.font_med.render(f"Tilt: {int(self.tilt)} / {int(self.tilt_threshold)}", True, (240,240,240))
        self.screen.blit(tilt_text, (480, 16))

        # draw plate
        plate_rect = pygame.Rect(int(self.plate_x - self.plate_w/2), int(self.plate_y - self.plate_h/2), self.plate_w, self.plate_h)
        pygame.draw.ellipse(self.screen, (60,60,70), plate_rect)
        pygame.draw.ellipse(self.screen, (90,90,110), plate_rect, 4)

        # draw current falling snacks
        for sn in self.snacks:
            rx = int(sn["x"])
            ry = int(sn["y"])
            rw = int(sn["w"])
            rh = int(sn["h"])
            # simple rounded rect using ellipse + rect
            rect = pygame.Rect(rx - rw//2, ry - rh//2, rw, rh)
            pygame.draw.rect(self.screen, sn["col"], rect, border_radius=8)
            pygame.draw.rect(self.screen, (0,0,0), rect, 2, border_radius=8)
            # label
            lbl = self.font_sm.render(sn["type"], True, (20,20,20))
            self.screen.blit(lbl, (rect.centerx - lbl.get_width()/2, rect.centery - lbl.get_height()/2))

        # draw stack (stacked relative to plate)
        cur_y = self.plate_y - self.plate_h/2
        for s in self.stack:
            cur_y -= s["h"]
            rect = pygame.Rect(int(self.plate_x + s["offset"] - s["w"]/2), int(cur_y - s["h"]/2), int(s["w"]), int(s["h"]))
            pygame.draw.rect(self.screen, s["col"], rect, border_radius=8)
            pygame.draw.rect(self.screen, (10,10,10), rect, 2, border_radius=8)

        # tilt meter (visual)
        meter_rect = pygame.Rect(self.WIDTH - 220, 40, 160, 20)
        pygame.draw.rect(self.screen, (28,28,28), meter_rect, border_radius=6)
        tfrac = min(1.0, self.tilt / self.tilt_threshold)
        fill_rect = pygame.Rect(meter_rect.x + 2, meter_rect.y + 2, int((meter_rect.width - 4) * tfrac), meter_rect.height - 4)
        pygame.draw.rect(self.screen, (240, 120, 120), fill_rect, border_radius=6)
        pygame.draw.rect(self.screen, (80,80,80), meter_rect, 2, border_radius=6)

        # footer instructions
        footer = self.font_sm.render("Move: ← → or mouse • Click or press action to drop emergency weight (costs score)", True, (200,200,200))
        self.screen.blit(footer, (self.WIDTH//2 - footer.get_width()//2, self.HEIGHT - 28))

    # override run to ensure leaderboard exists
    def run(self):
        if not Path(LEADERBOARD_FILE).exists():
            save_json(Path(LEADERBOARD_FILE), [])
        super().run()

# ------------------- RUN -------------------
if __name__ == "__main__":
    game = SnackStackGame()
    game.run()

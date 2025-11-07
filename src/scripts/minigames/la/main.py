"""
LALALALA — Upgraded edition
Features:
- Animated note sprites (procedural)
- Particle burst on hit
- Start screen with settings menu
- Saveable settings and leaderboard (JSON)
- Key remapping
- Gamepad (joystick) support + remapping
- Sound toggles (placeholder tones)
- Clean UI, responsive scaling

Requirements:
pip install pygame

Run:
python lalalala_upgraded.py
"""

import pygame
import random
import sys
import json
import math
import os
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Dict, Any, Optional, List

# ------------------- CONFIG / SAVE PATH -------------------
# Base user folder for MGAIO saves (same as launcher)
USER_DIR = os.path.expandvars(r"%userprofile%")
MGAIO_DIR = Path(USER_DIR) / "Documents" / ".mgaio"

# Lalallaa save folder inside MGAIO
APP_NAME = "Lalallaa"
SAVE_FOLDER = MGAIO_DIR / "Saves" / APP_NAME
SAVE_FOLDER.mkdir(parents=True, exist_ok=True)

# File paths
SETTINGS_FILE = SAVE_FOLDER / "settings.json"
LEADERBOARD_FILE = SAVE_FOLDER / "leaderboard.json"

# Initialize settings if missing
if not SETTINGS_FILE.exists():
    default_settings = {
        "volume": 100,
        "keymap": {},
        "theme": "default"
    }
    SETTINGS_FILE.write_text(json.dumps(default_settings, indent=4))

# Initialize leaderboard if missing
if not LEADERBOARD_FILE.exists():
    default_leaderboard = {}
    LEADERBOARD_FILE.write_text(json.dumps(default_leaderboard, indent=4))

print("Lalallaa Save folder:", SAVE_FOLDER)
print("Settings file:", SETTINGS_FILE)
print("Leaderboard file:", LEADERBOARD_FILE)

WIDTH, HEIGHT = 1000, 700
FPS = 60

LANE_COUNT = 3
NOTE_BASE_WIDTH = 56
NOTE_BASE_HEIGHT = 28
HIT_ZONE_Y = HEIGHT - 150
DEFAULT_HIT_WINDOW = 56

STARTING_LIVES = 5
MAX_LEADERBOARD = 10

# default key mapping (pygame constants)
DEFAULT_KEYMAP = {
    "lane_0": pygame.K_a,
    "lane_1": pygame.K_s,
    "lane_2": pygame.K_d,
    "start": pygame.K_RETURN,
    "back": pygame.K_ESCAPE,
}

# default joystick mapping (button indices or axis thresholds)
DEFAULT_JOYMAP = {
    "lane_0": {"type": "button", "id": 0},
    "lane_1": {"type": "button", "id": 1},
    "lane_2": {"type": "button", "id": 2},
}

DEFAULT_SETTINGS = {
    "keymap": DEFAULT_KEYMAP,
    "joymap": DEFAULT_JOYMAP,
    "sound": True,
    "difficulty": "normal",  # easy, normal, hard
    "hit_window": DEFAULT_HIT_WINDOW,
}

# Colors
WHITE = (245, 245, 245)
BLACK = (12, 12, 12)
GRAY = (54, 57, 63)
ACCENT = (255, 200, 60)
GOOD_GREEN = (88, 214, 141)
BAD_RED = (232, 76, 61)
BLUE = (100, 149, 237)
TRANSPARENT = (0, 0, 0, 0)

# ------------------- HELPERS FOR SAVE/LOAD -------------------
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
        print("Failed saving", path, "->", e)

# ------------------- GAME DATA CLASSES -------------------
@dataclass
class Note:
    lane: int
    y: float
    speed: float
    angle: float = 0.0
    scale: float = 1.0
    hit: bool = False
    created_time: float = 0.0

@dataclass
class Particle:
    x: float
    y: float
    vx: float
    vy: float
    life: float
    size: float

# ------------------- MAIN GAME CLASS -------------------
class Lalalala:
    def __init__(self):
        pygame.init()
        pygame.joystick.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("LALALALA — Upgraded ✨")
        self.clock = pygame.time.Clock()
        self.font_big = pygame.font.SysFont("arial", 56, bold=True)
        self.font_med = pygame.font.SysFont("arial", 28)
        self.font_sm = pygame.font.SysFont("arial", 16)
        self.running = True

        # load settings and leaderboard
        self.settings = load_json(SETTINGS_FILE, DEFAULT_SETTINGS.copy())
        # ensure keys exist
        if "keymap" not in self.settings:
            self.settings["keymap"] = DEFAULT_KEYMAP.copy()
        if "joymap" not in self.settings:
            self.settings["joymap"] = DEFAULT_JOYMAP.copy()

        self.leaderboard = load_json(LEADERBOARD_FILE, [])
        self._ensure_leaderboard()

        # joystick
        self.joystick = None
        self.detect_joystick()

        # game state
        self.state = "menu"  # menu, settings, remap_key, remap_joy, playing, gameover
        self.notes: List[Note] = []
        self.particles: List[Particle] = []
        self.spawn_timer = 0.0
        self.score = 0
        self.combo = 0
        self.lives = STARTING_LIVES
        self.hit_feedback = None  # (text, timer, color)
        self.note_speed = 240.0
        self.spawn_interval = 0.75
        self.last_time = 0.0
        self.time_since_start = 0.0
        self.high_score = self._highest_score()
        self.player_name = "Player"

        # remap helpers
        self.remap_target = None  # ("keymap", "lane_0") etc
        self.remap_prompt = ""
        self.remap_callback = None

        # difficulty tweaks
        self.apply_difficulty()

        # audio placeholders (simple pygame tones using Sound buffers)
        self.sounds = {}
        self._create_sounds()

    # ---------- startup / joystick ----------
    def detect_joystick(self):
        if pygame.joystick.get_count() > 0:
            try:
                js = pygame.joystick.Joystick(0)
                js.init()
                self.joystick = js
                print("Joystick detected:", js.get_name())
            except Exception as e:
                print("Joystick init failed:", e)
                self.joystick = None
        else:
            self.joystick = None

    # ---------- sound creation ----------
    def _create_sounds(self):
        # create short tone sounds procedurally if sound enabled
        # small sine wave buffers
        try:
            freq = 44100
            for name, hz, dur in (("hit", 880, 0.06), ("miss", 220, 0.09), ("start", 440, 0.12)):
                n_samples = int(freq * dur)
                buf = bytearray()
                max_amp = 127
                for i in range(n_samples):
                    t = i / freq
                    v = int(max_amp * math.sin(2 * math.pi * hz * t) * (1.0 - t / dur))
                    # convert to signed 8-bit PCM +128
                    buf.append(v + 128)
                sound = pygame.mixer.Sound(buffer=bytes(buf))
                self.sounds[name] = sound
        except Exception:
            self.sounds = {}

    def play_sound(self, name):
        if not self.settings.get("sound", True):
            return
        s = self.sounds.get(name)
        if s:
            try:
                s.play()
            except Exception:
                pass

    # ---------- difficulty ----------
    def apply_difficulty(self):
        diff = self.settings.get("difficulty", "normal")
        if diff == "easy":
            self.note_speed = 180.0
            self.spawn_interval = 0.9
            self.settings["hit_window"] = DEFAULT_HIT_WINDOW + 12
        elif diff == "hard":
            self.note_speed = 300.0
            self.spawn_interval = 0.6
            self.settings["hit_window"] = max(36, DEFAULT_HIT_WINDOW - 14)
        else:  # normal
            self.note_speed = 240.0
            self.spawn_interval = 0.75
            self.settings["hit_window"] = DEFAULT_HIT_WINDOW

    # ---------- saving / leaderboard ----------
    def _ensure_leaderboard(self):
        if not isinstance(self.leaderboard, list):
            self.leaderboard = []
        # ensure structure
        cleaned = []
        for item in self.leaderboard:
            if isinstance(item, dict) and "name" in item and "score" in item:
                cleaned.append({"name": item["name"], "score": int(item["score"])})
        self.leaderboard = sorted(cleaned, key=lambda x: -x["score"])[:MAX_LEADERBOARD]

    def _highest_score(self):
        if not self.leaderboard:
            return 0
        return max(item["score"] for item in self.leaderboard)

    def save_all(self):
        save_json(SETTINGS_FILE, self.settings)
        save_json(LEADERBOARD_FILE, self.leaderboard)

    def add_to_leaderboard(self, name, score):
        self.leaderboard.append({"name": name, "score": int(score)})
        self.leaderboard = sorted(self.leaderboard, key=lambda x: -x["score"])[:MAX_LEADERBOARD]
        self.save_all()
        self.high_score = self._highest_score()

    # ---------- note spawn / update ----------
    def spawn_note(self):
        lane = random.randrange(0, LANE_COUNT)
        n = Note(lane=lane, y=-NOTE_BASE_HEIGHT - 8, speed=self.note_speed, angle=random.random() * 360, scale=1.0, created_time=self.time_since_start)
        self.notes.append(n)

    def update_game(self, dt):
        self.time_since_start += dt
        # difficulty ramp: gradually increase speed every 15s
        if int(self.time_since_start) % 15 == 0 and self.time_since_start > 0:
            # small ramp but not too often: only when exactly multiple of 15 (simple)
            self.note_speed += 0.2 * dt

        self.spawn_timer += dt
        if self.spawn_timer >= self.spawn_interval:
            self.spawn_timer -= self.spawn_interval
            self.spawn_note()
            # small random spawn tweak
            if random.random() < 0.07:
                self.spawn_interval = max(0.28, self.spawn_interval - 0.01)

        # update notes
        for note in self.notes:
            note.y += note.speed * dt
            note.angle += 90 * dt  # rotate 90 deg/sec
            # pulsing scale using created_time
            note.scale = 0.9 + 0.12 * math.sin((self.time_since_start - note.created_time) * 6.0)

        # notes that pass bottom -> miss
        to_remove = []
        for note in self.notes:
            if note.y > HEIGHT + 40 and not note.hit:
                to_remove.append(note)
                self.combo = 0
                self.lives -= 1
                self.hit_feedback = ("Miss!", 1.0, BAD_RED)
                self.play_sound("miss")
                # burst slight particles at lane bottom
                lane_x = note.lane * (WIDTH / LANE_COUNT) + (WIDTH / LANE_COUNT) / 2
                self._emit_particles(lane_x, HIT_ZONE_Y, 12, BAD_RED)
        for n in to_remove:
            if n in self.notes:
                self.notes.remove(n)

        # particles update
        for p in list(self.particles):
            p.x += p.vx * dt
            p.y += p.vy * dt
            p.vy += 220 * dt  # gravity
            p.life -= dt
            if p.life <= 0:
                self.particles.remove(p)

        # feedback timer
        if self.hit_feedback:
            text, timer, color = self.hit_feedback
            timer -= dt
            if timer <= 0:
                self.hit_feedback = None
            else:
                self.hit_feedback = (text, timer, color)

        if self.lives <= 0:
            self.state = "gameover"
            self.add_to_leaderboard(self.player_name, self.score)

    # ---------- input handling (keys + joystick) ----------
    def handle_keypress_playing(self, key):
        keymap = self.settings.get("keymap", {})
        if key == keymap.get("start") or key == pygame.K_RETURN:
            # pause or restart? we'll ignore start during play
            return
        if key == keymap.get("back") or key == pygame.K_ESCAPE:
            # open menu
            self.state = "menu"
            return
        # map key to lane
        for lane_idx in range(LANE_COUNT):
            map_key = keymap.get(f"lane_{lane_idx}")
            if map_key is not None and key == map_key:
                self._try_hit_lane(lane_idx)
                return
        # unknown key: small penalty? just show feedback
        self.hit_feedback = ("No note!", 0.6, GRAY)

    def handle_joy_event(self, event):
        # handle joystick button presses
        jm = self.settings.get("joymap", {})
        if event.type == pygame.JOYBUTTONDOWN:
            btn = event.button
            for lane_idx in range(LANE_COUNT):
                mapping = jm.get(f"lane_{lane_idx}")
                if mapping and mapping.get("type") == "button" and mapping.get("id") == btn:
                    self._try_hit_lane(lane_idx)
                    return
        # axis mapping (optional) - if mapping uses axis, detect threshold crossing
        if event.type == pygame.JOYAXISMOTION:
            ax = event.axis
            val = event.value
            for lane_idx in range(LANE_COUNT):
                mapping = jm.get(f"lane_{lane_idx}")
                if mapping and mapping.get("type") == "axis":
                    if mapping.get("id") == ax:
                        # mapping direction > 0.5 or < -0.5 triggers
                        dir_needed = mapping.get("dir", 1)
                        thresh = mapping.get("thresh", 0.6)
                        if dir_needed > 0 and val > thresh:
                            self._try_hit_lane(lane_idx)
                            return
                        if dir_needed < 0 and val < -thresh:
                            self._try_hit_lane(lane_idx)
                            return

    def _try_hit_lane(self, lane_idx):
        # find nearest hittable note in lane
        candidates = [n for n in self.notes if n.lane == lane_idx and not n.hit]
        if not candidates:
            # bad tap
            self.combo = 0
            self.hit_feedback = ("No note!", 0.6, GRAY)
            return
        best = min(candidates, key=lambda n: abs(n.y - HIT_ZONE_Y))
        distance = abs(best.y - HIT_ZONE_Y)
        hit_window = self.settings.get("hit_window", DEFAULT_HIT_WINDOW)
        if distance <= hit_window:
            accuracy = max(0.0, 1.0 - (distance / hit_window))
            points = int(120 * accuracy) + 10 * (self.combo // 5)
            self.score += points
            best.hit = True
            if best in self.notes:
                self.notes.remove(best)
            self.combo += 1
            self.hit_feedback = (f"+{points}", 0.9, GOOD_GREEN)
            self.play_sound("hit")
            # particle burst at lane center
            lane_x = lane_idx * (WIDTH / LANE_COUNT) + (WIDTH / LANE_COUNT) / 2
            self._emit_particles(lane_x, HIT_ZONE_Y, 18 + int(6 * accuracy), GOOD_GREEN)
            # tighten spawn interval slightly to ramp up challenge
            self.spawn_interval = max(0.25, self.spawn_interval - 0.006)
        else:
            # miss
            self.combo = 0
            self.lives -= 1
            self.hit_feedback = ("Miss!", 0.9, BAD_RED)
            self.play_sound("miss")
            if best in self.notes:
                self.notes.remove(best)
            lane_x = lane_idx * (WIDTH / LANE_COUNT) + (WIDTH / LANE_COUNT) / 2
            self._emit_particles(lane_x, HIT_ZONE_Y, 8, BAD_RED)

    # ---------- particles ----------
    def _emit_particles(self, x, y, count, color):
        for i in range(count):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(80, 400)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed * -1
            p = Particle(x=x + random.uniform(-8, 8), y=y + random.uniform(-6, 6), vx=vx, vy=vy, life=random.uniform(0.5, 1.1), size=random.uniform(2, 6))
            # attach color as attribute for draw (monkey patch)
            setattr(p, "color", color)
            self.particles.append(p)

    # ---------- UI drawing helpers ----------
    def _draw_button(self, rect, text, active=True, small=False):
        # rect: pygame.Rect
        color = ACCENT if active else GRAY
        pygame.draw.rect(self.screen, color, rect, border_radius=10)
        label = self.font_sm if small else self.font_med
        surf = label.render(text, True, BLACK if active else WHITE)
        self.screen.blit(surf, (rect.centerx - surf.get_width() / 2, rect.centery - surf.get_height() / 2))

    def draw_menu(self):
        title = self.font_big.render("LALALALA", True, ACCENT)
        sub = self.font_med.render("Upgraded — Particles, Animated Notes, Save + Remap", True, WHITE)
        self.screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 60))
        self.screen.blit(sub, (WIDTH // 2 - sub.get_width() // 2, 140))

        # big buttons: Start, Settings, Leaderboard, Quit
        btn_w, btn_h = 340, 56
        start_rect = pygame.Rect(WIDTH // 2 - btn_w // 2, 220, btn_w, btn_h)
        settings_rect = pygame.Rect(WIDTH // 2 - btn_w // 2, 300, btn_w, btn_h)
        leader_rect = pygame.Rect(WIDTH // 2 - btn_w // 2, 380, btn_w, btn_h)
        quit_rect = pygame.Rect(WIDTH // 2 - btn_w // 2, 460, btn_w, btn_h)

        self._draw_button(start_rect, "Start Play (Enter)")
        self._draw_button(settings_rect, "Settings")
        self._draw_button(leader_rect, "Leaderboard")
        self._draw_button(quit_rect, "Quit")

        self.menu_buttons = {
            "start": start_rect,
            "settings": settings_rect,
            "leader": leader_rect,
            "quit": quit_rect,
        }

        footer = self.font_sm.render(f"Save folder: {SAVE_FOLDER}", True, GRAY)
        self.screen.blit(footer, (12, HEIGHT - 28))

    def draw_settings(self):
        title = self.font_big.render("Settings", True, ACCENT)
        self.screen.blit(title, (48, 36))

        # left column: toggles and difficulty
        left_x = 48
        y = 120
        spacing = 48

        sound_text = f"Sound: {'On' if self.settings.get('sound', True) else 'Off'}"
        diff_text = f"Difficulty: {self.settings.get('difficulty', 'normal').capitalize()}"
        hit_text = f"Hit Window: {self.settings.get('hit_window', DEFAULT_HIT_WINDOW)} px"

        self.screen.blit(self.font_med.render(sound_text, True, WHITE), (left_x, y))
        y += spacing
        self.screen.blit(self.font_med.render(diff_text, True, WHITE), (left_x, y))
        y += spacing
        self.screen.blit(self.font_med.render(hit_text, True, WHITE), (left_x, y))
        y += spacing

        # toggles buttons on the right
        right_x = WIDTH // 2 + 40
        btn_w, btn_h = 220, 40
        sound_btn = pygame.Rect(right_x, 120, btn_w, btn_h)
        diff_btn = pygame.Rect(right_x, 168, btn_w, btn_h)
        hit_dec = pygame.Rect(right_x, 216, 48, btn_h)
        hit_inc = pygame.Rect(right_x + 70, 216, 48, btn_h)
        hit_val = pygame.Rect(right_x + 130, 216, 100, btn_h)

        self._draw_button(sound_btn, "Toggle Sound")
        self._draw_button(diff_btn, "Cycle Difficulty")
        self._draw_button(hit_dec, "-")
        self._draw_button(hit_inc, "+")
        self._draw_button(hit_val, str(self.settings.get("hit_window", DEFAULT_HIT_WINDOW)), active=False)

        self.settings_buttons = {
            "sound": sound_btn,
            "diff": diff_btn,
            "hit_dec": hit_dec,
            "hit_inc": hit_inc,
            "hit_val": hit_val,
        }

        # Key remap section
        section_y = 320
        self.screen.blit(self.font_med.render("Key Remapping:", True, WHITE), (48, section_y))
        km_x = 48
        km_y = section_y + 40
        row_h = 44
        keymap = self.settings.get("keymap", {})
        for i in range(LANE_COUNT):
            label = f"Lane {i+1}"
            labelsurf = self.font_sm.render(label, True, WHITE)
            self.screen.blit(labelsurf, (km_x, km_y + i * row_h))
            cur = keymap.get(f"lane_{i}")
            curname = pygame.key.name(cur) if isinstance(cur, int) else str(cur)
            btn = pygame.Rect(km_x + 160, km_y + i * row_h, 240, 34)
            self._draw_button(btn, f"Key: {curname}", active=True, small=True)
            # store rect
            if not hasattr(self, "remap_key_buttons"):
                self.remap_key_buttons = {}
            self.remap_key_buttons[f"lane_{i}"] = btn

        # joystick mapping remap
        jm_y = km_y + LANE_COUNT * row_h + 20
        self.screen.blit(self.font_med.render("Joystick Remapping (if connected):", True, WHITE), (48, jm_y))
        jm_y += 40
        joymap = self.settings.get("joymap", {})
        for i in range(LANE_COUNT):
            lbl = f"Lane {i+1}"
            self.screen.blit(self.font_sm.render(lbl, True, WHITE), (48, jm_y + i * row_h))
            mapping = joymap.get(f"lane_{i}", {})
            if mapping.get("type") == "button":
                desc = f"Button {mapping.get('id')}"
            elif mapping.get("type") == "axis":
                desc = f"Axis {mapping.get('id')} dir {mapping.get('dir')}"
            else:
                desc = "Unset"
            btn = pygame.Rect(48 + 160, jm_y + i * row_h, 260, 34)
            self._draw_button(btn, f"{desc}", active=True, small=True)
            if not hasattr(self, "remap_joy_buttons"):
                self.remap_joy_buttons = {}
            self.remap_joy_buttons[f"lane_{i}"] = btn

        # bottom: back button
        back_rect = pygame.Rect(WIDTH - 220, HEIGHT - 88, 180, 48)
        self._draw_button(back_rect, "Back to Menu")
        self.settings_buttons["back"] = back_rect

    def draw_leaderboard(self):
        title = self.font_big.render("Leaderboard", True, ACCENT)
        self.screen.blit(title, (48, 36))
        y = 120
        for idx, entry in enumerate(self.leaderboard):
            name = entry.get("name", "Player")
            score = entry.get("score", 0)
            line = self.font_med.render(f"{idx+1}. {name} — {score}", True, WHITE)
            self.screen.blit(line, (68, y + idx * 44))

        back_rect = pygame.Rect(WIDTH - 220, HEIGHT - 88, 180, 48)
        self._draw_button(back_rect, "Back")
        self.leader_buttons = {"back": back_rect}

    def draw_game_ui(self):
        # lanes
        lane_w = WIDTH / LANE_COUNT
        for i in range(LANE_COUNT + 1):
            x = int(i * lane_w)
            pygame.draw.line(self.screen, GRAY, (x, 0), (x, HEIGHT), 2)

        # corrected: avoid quote mismatch
        zone_rect = pygame.Rect(0, HIT_ZONE_Y - self.settings.get("hit_window", DEFAULT_HIT_WINDOW), WIDTH, self.settings.get("hit_window", DEFAULT_HIT_WINDOW) * 2)
        s = pygame.Surface((zone_rect.w, zone_rect.h), pygame.SRCALPHA)
        s.fill((255, 255, 255, 12))
        self.screen.blit(s, (zone_rect.x, zone_rect.y))
        # lane labels
        for i in range(LANE_COUNT):
            txt = self.font_sm.render(f"{pygame.key.name(self.settings.get('keymap', {}).get(f'lane_{i}', pygame.K_a))}", True, WHITE)
            x = int(i * lane_w + lane_w / 2 - txt.get_width() / 2)
            y = HIT_ZONE_Y + 14
            self.screen.blit(txt, (x, y))

        # notes: draw animated sprites
        for note in self.notes:
            lane_cx = int(note.lane * lane_w + lane_w / 2)
            w = int(NOTE_BASE_WIDTH * note.scale)
            h = int(NOTE_BASE_HEIGHT * note.scale)
            rect = pygame.Rect(lane_cx - w // 2, int(note.y) - h // 2, w, h)
            # rotating rounded rectangle - simulate by drawing rotated surface
            surf = pygame.Surface((w, h), pygame.SRCALPHA)
            # gradient-ish fill with circle inside
            pygame.draw.ellipse(surf, BLUE, (0, 0, w, h))
            inner = pygame.Surface((w, h), pygame.SRCALPHA)
            pygame.draw.ellipse(inner, (255, 255, 255, 40), (w*0.14, h*0.14, w*0.72, h*0.72))
            surf.blit(inner, (0, 0))
            # rotate
            rotated = pygame.transform.rotate(surf, note.angle)
            rrect = rotated.get_rect(center=rect.center)
            self.screen.blit(rotated, rrect.topleft)
            # small label 'la'
            lbl = self.font_sm.render("la", True, BLACK)
            self.screen.blit(lbl, (rect.centerx - lbl.get_width() / 2, rect.centery - lbl.get_height() / 2))

        # particles
        for p in self.particles:
            alpha = max(0, min(255, int(255 * (p.life / 1.1))))
            col = getattr(p, "color", ACCENT)
            surf = pygame.Surface((int(p.size * 2), int(p.size * 2)), pygame.SRCALPHA)
            pygame.draw.circle(surf, (col[0], col[1], col[2], alpha), (int(p.size), int(p.size)), int(p.size))
            self.screen.blit(surf, (int(p.x - p.size), int(p.y - p.size)))

        # top UI
        score_surf = self.font_med.render(f"Score: {self.score}", True, WHITE)
        combo_surf = self.font_med.render(f"Combo: {self.combo}", True, WHITE)
        lives_surf = self.font_med.render(f"Lives: {self.lives}", True, WHITE)
        self.screen.blit(score_surf, (18, 12))
        self.screen.blit(combo_surf, (WIDTH // 2 - combo_surf.get_width() // 2, 12))
        self.screen.blit(lives_surf, (WIDTH - lives_surf.get_width() - 18, 12))

        # hit feedback big text
        if self.hit_feedback:
            text, timer, color = self.hit_feedback
            surf = self.font_big.render(text, True, color)
            self.screen.blit(surf, (WIDTH // 2 - surf.get_width() // 2, HEIGHT // 2 - surf.get_height() // 2))

    # ---------- main loop / events ----------
    def run(self):
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            self.handle_events()
            self.update(dt)
            self.render()
        pygame.quit()
        sys.exit()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.save_all()
                self.running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos
                if self.state == "menu":
                    for name, rect in self.menu_buttons.items():
                        if rect.collidepoint(mx, my):
                            if name == "start":
                                self.start_play()
                            elif name == "settings":
                                self.state = "settings"
                            elif name == "leader":
                                self.state = "leader"
                            elif name == "quit":
                                self.save_all()
                                self.running = False
                elif self.state == "settings":
                    # check settings buttons and remap buttons
                    for key, rect in getattr(self, "settings_buttons", {}).items():
                        if rect.collidepoint(mx, my):
                            if key == "sound":
                                self.settings["sound"] = not self.settings.get("sound", True)
                                self.save_all()
                                self._create_sounds()
                            elif key == "diff":
                                cur = self.settings.get("difficulty", "normal")
                                nxt = {"easy": "normal", "normal": "hard", "hard": "easy"}[cur]
                                self.settings["difficulty"] = nxt
                                self.apply_difficulty()
                                self.save_all()
                            elif key == "hit_dec":
                                self.settings["hit_window"] = max(20, self.settings.get("hit_window", DEFAULT_HIT_WINDOW) - 4)
                                self.save_all()
                            elif key == "hit_inc":
                                self.settings["hit_window"] = min(140, self.settings.get("hit_window", DEFAULT_HIT_WINDOW) + 4)
                                self.save_all()
                            elif key == "back":
                                self.state = "menu"
                    # remap key buttons
                    for mapkey, rect in getattr(self, "remap_key_buttons", {}).items():
                        if rect.collidepoint(mx, my):
                            # enter remap key mode
                            self.state = "remap_key"
                            self.remap_target = ("keymap", mapkey)
                            self.remap_prompt = f"Press a keyboard key to assign to {mapkey}"
                            self.remap_callback = self._complete_remap_key
                    # remap joystick
                    for mapkey, rect in getattr(self, "remap_joy_buttons", {}).items():
                        if rect.collidepoint(mx, my):
                            self.state = "remap_joy"
                            self.remap_target = ("joymap", mapkey)
                            self.remap_prompt = f"Press joystick button or move axis for {mapkey}"
                            self.remap_callback = self._complete_remap_joy
                elif self.state == "leader":
                    for key, rect in getattr(self, "leader_buttons", {}).items():
                        if rect.collidepoint(mx, my):
                            if key == "back":
                                self.state = "menu"
                elif self.state == "gameover":
                    # clicking anywhere restarts
                    self.start_play()
            elif event.type == pygame.KEYDOWN:
                if self.state == "menu":
                    if event.key == pygame.K_RETURN:
                        self.start_play()
                    elif event.key == pygame.K_s:
                        self.state = "settings"
                elif self.state == "settings":
                    if event.key == pygame.K_ESCAPE:
                        self.state = "menu"
                elif self.state == "leader":
                    if event.key == pygame.K_ESCAPE:
                        self.state = "menu"
                elif self.state == "remap_key":
                    # capture any key and assign
                    if self.remap_callback:
                        self.remap_callback(event.key)
                elif self.state == "remap_joy":
                    # allow pressing keyboard to cancel
                    if event.key == pygame.K_ESCAPE:
                        self.state = "settings"
                elif self.state == "playing":
                    self.handle_keypress_playing(event.key)
                elif self.state == "gameover":
                    if event.key == pygame.K_RETURN:
                        self.start_play()

            # joystick events
            if event.type in (pygame.JOYBUTTONDOWN, pygame.JOYAXISMOTION):
                if self.state == "playing":
                    self.handle_joy_event(event)
                elif self.state == "remap_joy" and self.remap_callback:
                    # pass event for remapping
                    self.remap_callback(event)

    def update(self, dt):
        if self.state == "playing":
            self.update_game(dt)

    def render(self):
        self.screen.fill(BLACK)
        if self.state == "menu":
            self.draw_menu()
        elif self.state == "settings":
            self.draw_settings()
        elif self.state == "leader":
            self.draw_leaderboard()
        elif self.state == "playing":
            self.draw_game_ui()
        elif self.state == "remap_key":
            # show overlay prompt
            msg = self.font_med.render(self.remap_prompt, True, WHITE)
            self.screen.blit(msg, (WIDTH // 2 - msg.get_width() // 2, HEIGHT // 2 - 40))
            cancel = self.font_sm.render("Press Esc to cancel", True, GRAY)
            self.screen.blit(cancel, (WIDTH // 2 - cancel.get_width() // 2, HEIGHT // 2 + 10))
        elif self.state == "remap_joy":
            msg = self.font_med.render(self.remap_prompt, True, WHITE)
            self.screen.blit(msg, (WIDTH // 2 - msg.get_width() // 2, HEIGHT // 2 - 40))
            cancel = self.font_sm.render("Press Esc to cancel", True, GRAY)
            self.screen.blit(cancel, (WIDTH // 2 - cancel.get_width() // 2, HEIGHT // 2 + 10))
        elif self.state == "gameover":
            over = self.font_big.render("GAME OVER", True, BAD_RED)
            score = self.font_med.render(f"Final Score: {self.score}", True, WHITE)
            prompt = self.font_med.render("Click or press Enter to play again", True, WHITE)
            self.screen.blit(over, (WIDTH // 2 - over.get_width() // 2, HEIGHT // 2 - 120))
            self.screen.blit(score, (WIDTH // 2 - score.get_width() // 2, HEIGHT // 2 - 40))
            self.screen.blit(prompt, (WIDTH // 2 - prompt.get_width() // 2, HEIGHT // 2 + 20))

        # draw top-right small leaderboard preview
        preview = self.font_sm.render(f"Top: {self.high_score}", True, WHITE)
        self.screen.blit(preview, (WIDTH - preview.get_width() - 12, 12))

        pygame.display.flip()

    # ---------- remapping callbacks ----------
    def _complete_remap_key(self, pressed_key):
        if not self.remap_target:
            self.state = "settings"
            return
        kind, mapkey = self.remap_target
        if kind != "keymap":
            self.state = "settings"
            return
        # set mapping
        self.settings.setdefault("keymap", {})[mapkey] = pressed_key
        self.save_all()
        self.remap_target = None
        self.state = "settings"

    def _complete_remap_joy(self, event):
        # event can be JOYBUTTONDOWN or JOYAXISMOTION
        if not self.remap_target:
            self.state = "settings"
            return
        kind, mapkey = self.remap_target
        if kind != "joymap":
            self.state = "settings"
            return
        jm = self.settings.setdefault("joymap", {})
        # If event is a pygame event object, handle accordingly
        if isinstance(event, pygame.event.EventType):
            if event.type == pygame.JOYBUTTONDOWN:
                jm[mapkey] = {"type": "button", "id": event.button}
            elif event.type == pygame.JOYAXISMOTION:
                # record axis id and direction (positive or negative)
                dirn = 1 if event.value > 0 else -1
                jm[mapkey] = {"type": "axis", "id": event.axis, "dir": dirn, "thresh": 0.6}
            else:
                # not recognized: abort
                self.state = "settings"
                return
        else:
            # fallback: if event is int button id
            if isinstance(event, int):
                jm[mapkey] = {"type": "button", "id": int(event)}
        self.save_all()
        self.remap_target = None
        self.state = "settings"

    # ---------- game control ----------
    def start_play(self):
        # reset gameplay state
        self.apply_difficulty()
        self.notes = []
        self.particles = []
        self.spawn_timer = 0.0
        self.score = 0
        self.combo = 0
        self.lives = STARTING_LIVES
        self.hit_feedback = None
        self.time_since_start = 0.0
        self.state = "playing"
        self.play_sound("start")

# ------------------- RUN -------------------
if __name__ == "__main__":
    game = Lalalala()
    game.run()

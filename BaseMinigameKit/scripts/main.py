"""
Base Minigame Template for Pygame
Features:
- Start Menu / Settings / Leaderboard
- Saveable settings and leaderboard (JSON)
- Keyboard + Joystick support
- Particle system (optional)
- Simple game loop template for any minigame
- Built-in procedural sound effects (no external files required)

Requirements:
pip install pygame

Run:
python minigame_template.py
"""

import pygame
import sys
import json
import os
import math
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict

# ------------------- CONFIG / SAVE PATH -------------------
USER_DIR = os.path.expandvars(r"%userprofile%")
MG_SAVE_DIR = Path(USER_DIR) / "Documents" / ".mgaio"
APP_NAME = "BaseMinigame"
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

# ------------------- BASE GAME CLASS -------------------
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
        self.font_big = pygame.font.SysFont("segoe ui emoji", 48, bold=True)
        self.font_med = pygame.font.SysFont("segoe ui emoji", 24)
        self.font_sm = pygame.font.SysFont("segoe ui emoji", 18)

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
        """Create small procedural sounds (8-bit unsigned PCM) and store as pygame.mixer.Sound objects."""
        try:
            sample_rate = 22050  # lower rate reduces CPU & memory for tiny sounds
            defs = {
                "select": (660, 0.06),
                "start": (880, 0.12),
                "action": (1200, 0.05),
                "cancel": (220, 0.08),
                "error": (160, 0.12),
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
                    # If creating from buffer fails, skip that sound
                    print(f"Failed to create sound {name}:", e)
            # fallback: ensure keys exist
            for k in ("select", "start", "action", "cancel", "error"):
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

    def emit_particle(self, x, y, color=(255, 200, 60)):
        p = Particle(
            x=x,
            y=y,
            vx=0,
            vy=-100,
            life=0.8,
            size=4,
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
                # Global: allow quitting with Esc in playing or menu (optional)
                if event.key == pygame.K_ESCAPE:
                    if self.state in ("settings", "leaderboard"):
                        # Return to menu from settings/leaderboard
                        self.state = "menu"
                        self.play_sound("cancel")
                    elif self.state == "playing":
                        # optional: go back to menu from play
                        self.state = "menu"
                        self.play_sound("cancel")
                    else:
                        # in menu/gameover: exit
                        if self.state == "menu":
                            self.play_sound("cancel")
                            self.running = False

                # Menu shortcuts — exact behavior you requested:
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

                # In playing state, forward to game-specific handler
                elif self.state == "playing":
                    self.handle_input(event.key)

                # In settings/leaderboard we handle only ESC above; other keys ignored here

            # Joystick events (optional)
            elif event.type in (pygame.JOYBUTTONDOWN, pygame.JOYAXISMOTION):
                if self.state == "playing":
                    self.handle_input(joy_event=event)

            # Mouse support: click to start or open settings/leaderboard (keeps UI friendly)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos
                if self.state == "menu":
                    # approximate button hit regions (centered)
                    # Start region
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
            p.vy += 200 * dt
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
        self.render_particles()
        pygame.display.flip()

    # ---------- menu / UI ----------
    def draw_menu(self):
        title = self.font_big.render(APP_NAME, True, (255, 200, 60))
        self.screen.blit(title, (self.WIDTH//2 - title.get_width()//2, 80))

        # Instructions
        info = self.font_med.render("Enter = Start    S = Settings    L = Leaderboard", True, (200, 200, 200))
        self.screen.blit(info, (self.WIDTH//2 - info.get_width()//2, 170))

        # Button-like regions (visual only)
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

        # small footer
        foot = self.font_sm.render("Esc = Quit", True, (150,150,150))
        self.screen.blit(foot, (12, self.HEIGHT - 28))

    def draw_settings(self):
        title = self.font_big.render("Settings", True, (255, 200, 60))
        self.screen.blit(title, (48, 36))

        # interactive-ish: show sound on/off and allow toggle with SPACE here
        sound_state = self.settings.get("sound", True)
        vol = self.settings.get("volume", 100)
        txt1 = self.font_med.render(f"Sound: {'On' if sound_state else 'Off'} (Press SPACE to toggle)", True, (255,255,255))
        txt2 = self.font_med.render(f"Volume: {vol} (Press Up/Down to change)", True, (255,255,255))
        txt3 = self.font_sm.render("Press Esc to return to Menu", True, (180,180,180))

        self.screen.blit(txt1, (48, 140))
        self.screen.blit(txt2, (48, 190))
        self.screen.blit(txt3, (48, 260))

        # handle keys for settings in a simple way by checking pressed keys
        keys = pygame.key.get_pressed()
        # toggle handled in event loop (below) to avoid instant-repeat issues

    def draw_leaderboard(self):
        title = self.font_big.render("Leaderboard", True, (255, 200, 60))
        self.screen.blit(title, (48, 36))

        if not isinstance(self.leaderboard, list):
            self.leaderboard = []

        # show up to top 10
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

    # ---------- start / stop ----------
    def start_play(self):
        self.state = "playing"
        self.score = 0

    # ---------- override handle_events to catch settings toggles ----------
    def handle_events(self):
        # we override base to add settings key handling (space/up/down)
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
                    # toggle sound with SPACE
                    if event.key == pygame.K_SPACE:
                        cur = self.settings.get("sound", True)
                        self.settings["sound"] = not cur
                        save_json(SETTINGS_FILE, self.settings)
                        self.play_sound("select" if self.settings["sound"] else "cancel")
                    # volume up/down
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
                    # forward to game-specific handler (keeps original API)
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

# ------------------- RUN -------------------
if __name__ == "__main__":
    game = BaseMinigame()
    game.run()

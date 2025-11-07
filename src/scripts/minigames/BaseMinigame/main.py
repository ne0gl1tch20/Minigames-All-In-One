"""
Base Minigame Template for Pygame
Features:
- Start Menu / Settings / Leaderboard
- Saveable settings and leaderboard (JSON)
- Keyboard + Joystick support
- Particle system (optional)
- Simple game loop template for any minigame

Requirements:
pip install pygame

Run:
python minigame_template.py
"""

import pygame
import sys
import json
import os
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
        pygame.joystick.init()
        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT))
        pygame.display.set_caption(APP_NAME)
        self.clock = pygame.time.Clock()
        self.font_big = pygame.font.SysFont("arial", 48, bold=True)
        self.font_med = pygame.font.SysFont("arial", 24)

        # Load settings / leaderboard
        self.settings = load_json(SETTINGS_FILE, DEFAULT_SETTINGS.copy())
        self.leaderboard = load_json(LEADERBOARD_FILE, DEFAULT_LEADERBOARD.copy())

        # Game state
        self.state = "menu"  # menu, settings, playing, gameover
        self.running = True
        self.particles: List[Particle] = []
        self.score = 0
        self.player_name = "Player"

        # Joystick
        self.joystick = None
        self.detect_joystick()

    # ---------- joystick ----------
    def detect_joystick(self):
        if pygame.joystick.get_count() > 0:
            js = pygame.joystick.Joystick(0)
            js.init()
            self.joystick = js
            print("Joystick detected:", js.get_name())

    # ---------- game logic hooks ----------
    def update_game(self, dt):
        """Override this in subclass or add your game logic here"""
        pass

    def handle_input(self, key=None, joy_event=None):
        """Override this in subclass"""
        if key == self.settings["keymap"]["action"]:
            print("Action key pressed!")

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
            elif event.type == pygame.KEYDOWN:
                if self.state == "playing":
                    self.handle_input(event.key)
            elif event.type in (pygame.JOYBUTTONDOWN, pygame.JOYAXISMOTION):
                if self.state == "playing":
                    self.handle_input(joy_event=event)

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
        self.render_particles()
        pygame.display.flip()

    # ---------- menu / UI ----------
    def draw_menu(self):
        title = self.font_big.render(APP_NAME, True, (255, 200, 60))
        self.screen.blit(title, (self.WIDTH//2 - title.get_width()//2, 100))
        start = self.font_med.render("Press Enter to Start", True, (200, 200, 200))
        self.screen.blit(start, (self.WIDTH//2 - start.get_width()//2, 250))

    def draw_settings(self):
        text = self.font_med.render("Settings placeholder", True, (255, 255, 255))
        self.screen.blit(text, (50, 50))

    def draw_game(self):
        score_text = self.font_med.render(f"Score: {self.score}", True, (255, 255, 255))
        self.screen.blit(score_text, (20, 20))

    # ---------- start / stop ----------
    def start_play(self):
        self.state = "playing"
        self.score = 0

# ------------------- RUN -------------------
if __name__ == "__main__":
    game = BaseMinigame()
    game.run()

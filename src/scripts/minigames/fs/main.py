"""
Standalone Flappy Bird Game - Pygame
Features:
- Start Menu / Settings / Leaderboard
- Saveable settings and leaderboard (JSON)
- Keyboard + Joystick support
- Particle system when scoring
- Built-in procedural sound effects
- Fully standalone

Requirements:
pip install pygame

Run:
python flappy_bird.py
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
APP_NAME = "Flappy Bird"
SAVE_FOLDER = MG_SAVE_DIR / "Saves" / APP_NAME
SAVE_FOLDER.mkdir(parents=True, exist_ok=True)

SETTINGS_FILE = SAVE_FOLDER / "settings.json"
LEADERBOARD_FILE = SAVE_FOLDER / "leaderboard.json"

DEFAULT_SETTINGS = {
    "volume": 100,
    "sound": True,
    "keymap": {"flap": pygame.K_SPACE},
    "joymap": {"flap": {"type": "button", "id": 0}},
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

# ------------------- BASE GAME -------------------
class FlappyBirdGame:
    WIDTH, HEIGHT = 480, 640
    FPS = 60

    GRAVITY = 800
    FLAP_STRENGTH = -250
    PIPE_SPEED = 200
    PIPE_GAP = 180
    PIPE_WIDTH = 80
    SPAWN_INTERVAL = 1.5  # seconds

    def __init__(self):
        pygame.init()
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
        for k, v in DEFAULT_SETTINGS.items():
            self.settings.setdefault(k, v)
        self.leaderboard = load_json(LEADERBOARD_FILE, DEFAULT_LEADERBOARD.copy())

        # Game state: "menu", "settings", "leaderboard", "playing", "gameover"
        self.state = "menu"
        self.running = True
        self.particles: List[Particle] = []
        self.score = 0
        self.player_name = "Player"

        # Joystick
        self.joystick = None
        self.detect_joystick()

        # Create sounds
        self.sounds: Dict[str, pygame.mixer.Sound] = {}
        if self.mixer_available:
            self._create_sounds()
            self._apply_volume_to_sounds()

        # Flappy-specific
        self.bird_y = self.HEIGHT / 2
        self.bird_vel = 0
        self.pipes: List[Dict] = []
        self.pipe_timer = 0
        self.bird_radius = 18

    # ---------- joystick ----------
    def detect_joystick(self):
        if pygame.joystick.get_count() > 0:
            js = pygame.joystick.Joystick(0)
            js.init()
            self.joystick = js
            print("Joystick detected:", js.get_name())

    # ---------- sound helpers ----------
    def _create_sounds(self):
        """Create simple procedural sounds"""
        try:
            sample_rate = 22050
            defs = {
                "flap": (800, 0.05),
                "score": (1000, 0.06),
                "hit": (200, 0.1)
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
                    print(f"Failed to create sound {name}: {e}")
            for k in ("flap", "score", "hit"):
                self.sounds.setdefault(k, None)
        except Exception as e:
            print("Sound creation error:", e)
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
        if not self.mixer_available or not self.settings.get("sound", True):
            return
        s = self.sounds.get(name)
        if s:
            try:
                s.play()
            except Exception:
                pass

    # ---------- particles ----------
    def emit_particle(self, x, y, color=(255, 200, 60)):
        p = Particle(x, y, random.uniform(-50,50), random.uniform(-150,-50), 0.8, 4, color)
        self.particles.append(p)

    def update_particles(self, dt):
        for p in list(self.particles):
            p.x += p.vx * dt
            p.y += p.vy * dt
            p.vy += self.GRAVITY * dt * 0.25
            p.life -= dt
            if p.life <= 0:
                self.particles.remove(p)

    def render_particles(self):
        for p in self.particles:
            alpha = max(0, min(255, int(255 * p.life)))
            surf = pygame.Surface((int(p.size*2), int(p.size*2)), pygame.SRCALPHA)
            pygame.draw.circle(surf, (*p.color, alpha), (int(p.size), int(p.size)), int(p.size))
            self.screen.blit(surf, (int(p.x - p.size), int(p.y - p.size)))

    # ---------- game logic ----------
    def flap(self):
        self.bird_vel = self.FLAP_STRENGTH
        self.play_sound("flap")

    def update_game(self, dt):
        self.bird_vel += self.GRAVITY * dt
        self.bird_y += self.bird_vel * dt

        # Pipe spawning
        self.pipe_timer += dt
        if self.pipe_timer >= self.SPAWN_INTERVAL:
            self.pipe_timer = 0
            gap_y = random.randint(150, self.HEIGHT-150)
            self.pipes.append({"x": self.WIDTH, "gap_y": gap_y, "scored": False})

        # Update pipes
        for pipe in self.pipes:
            pipe["x"] -= self.PIPE_SPEED * dt

            # Scoring
            if not pipe["scored"] and pipe["x"] + self.PIPE_WIDTH < self.WIDTH/2:
                self.score += 1
                pipe["scored"] = True
                self.play_sound("score")
                for _ in range(10):
                    self.emit_particle(self.WIDTH/2, self.bird_y)

        # Remove offscreen pipes
        self.pipes = [p for p in self.pipes if p["x"] + self.PIPE_WIDTH > 0]

        # Collision
        for pipe in self.pipes:
            if (self.WIDTH/2 + self.bird_radius > pipe["x"] and self.WIDTH/2 - self.bird_radius < pipe["x"] + self.PIPE_WIDTH):
                if (self.bird_y - self.bird_radius < pipe["gap_y"] - self.PIPE_GAP/2 or
                    self.bird_y + self.bird_radius > pipe["gap_y"] + self.PIPE_GAP/2):
                    self.game_over()
        if self.bird_y - self.bird_radius <= 0 or self.bird_y + self.bird_radius >= self.HEIGHT:
            self.game_over()

    def game_over(self):
        self.play_sound("hit")
        self.state = "gameover"
        # save score
        self.leaderboard.append({"name": self.player_name, "score": self.score})
        save_json(LEADERBOARD_FILE, self.leaderboard)

    # ---------- input ----------
    def handle_input(self, key=None, joy_event=None):
        if key == self.settings["keymap"]["flap"]:
            self.flap()
        elif joy_event:
            if joy_event.type == pygame.JOYBUTTONDOWN:
                mapping = self.settings["joymap"]["flap"]
                if mapping["type"] == "button" and joy_event.button == mapping["id"]:
                    self.flap()

    # ---------- rendering ----------
    def draw_game(self):
        self.screen.fill((100, 200, 255))
        # Draw pipes
        for pipe in self.pipes:
            pygame.draw.rect(self.screen, (0,200,0), (pipe["x"], 0, self.PIPE_WIDTH, pipe["gap_y"]-self.PIPE_GAP/2))
            pygame.draw.rect(self.screen, (0,200,0), (pipe["x"], pipe["gap_y"]+self.PIPE_GAP/2, self.PIPE_WIDTH, self.HEIGHT - pipe["gap_y"] - self.PIPE_GAP/2))
        # Draw bird
        pygame.draw.circle(self.screen, (255,255,0), (int(self.WIDTH/2), int(self.bird_y)), self.bird_radius)
        # Score
        score_text = self.font_big.render(str(self.score), True, (255,255,255))
        self.screen.blit(score_text, (self.WIDTH//2 - score_text.get_width()//2, 20))

    # ---------- menu / settings / leaderboard ----------
    def draw_menu(self):
        self.screen.fill((12,12,12))
        title = self.font_big.render(APP_NAME, True, (255,200,60))
        self.screen.blit(title, (self.WIDTH//2 - title.get_width()//2, 80))
        info = self.font_med.render("Enter = Start    S = Settings    L = Leaderboard", True, (200,200,200))
        self.screen.blit(info, (self.WIDTH//2 - info.get_width()//2, 170))
        foot = self.font_sm.render("Esc = Quit", True, (150,150,150))
        self.screen.blit(foot, (12, self.HEIGHT - 28))

    def draw_settings(self):
        self.screen.fill((12,12,12))
        title = self.font_big.render("Settings", True, (255,200,60))
        self.screen.blit(title, (48, 36))
        sound_state = self.settings.get("sound", True)
        vol = self.settings.get("volume", 100)
        txt1 = self.font_med.render(f"Sound: {'On' if sound_state else 'Off'} (SPACE)", True, (255,255,255))
        txt2 = self.font_med.render(f"Volume: {vol} (UP/DOWN)", True, (255,255,255))
        txt3 = self.font_sm.render("Esc = Return to Menu", True, (180,180,180))
        self.screen.blit(txt1, (48,140))
        self.screen.blit(txt2, (48,190))
        self.screen.blit(txt3, (48,260))

    def draw_leaderboard(self):
        self.screen.fill((12,12,12))
        title = self.font_big.render("Leaderboard", True, (255,200,60))
        self.screen.blit(title, (48,36))
        y = 120
        for i, entry in enumerate(sorted(self.leaderboard, key=lambda x: x.get('score',0), reverse=True)[:10], start=1):
            line = self.font_med.render(f"{i}. {entry.get('name','Player')} - {entry.get('score',0)}", True, (230,230,230))
            self.screen.blit(line, (68, y))
            y += 36
        hint = self.font_sm.render("Esc = Return to Menu", True, (180,180,180))
        self.screen.blit(hint, (48, self.HEIGHT - 48))

    # ---------- start / reset ----------
    def start_play(self):
        self.state = "playing"
        self.score = 0
        self.bird_y = self.HEIGHT / 2
        self.bird_vel = 0
        self.pipes.clear()
        self.pipe_timer = 0
        self.particles.clear()

    # ---------- event loop ----------
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.state in ("settings","leaderboard","gameover"):
                        self.state = "menu"
                    elif self.state == "menu":
                        self.running = False
                elif self.state == "menu":
                    if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                        self.start_play()
                    elif event.key == pygame.K_s:
                        self.state = "settings"
                    elif event.key == pygame.K_l:
                        self.state = "leaderboard"
                elif self.state == "settings":
                    if event.key == pygame.K_SPACE:
                        self.settings["sound"] = not self.settings.get("sound",True)
                        save_json(SETTINGS_FILE, self.settings)
                        self._apply_volume_to_sounds()
                    elif event.key == pygame.K_UP:
                        self.settings["volume"] = min(100, self.settings.get("volume",100)+5)
                        self._apply_volume_to_sounds()
                        save_json(SETTINGS_FILE, self.settings)
                    elif event.key == pygame.K_DOWN:
                        self.settings["volume"] = max(0, self.settings.get("volume",100)-5)
                        self._apply_volume_to_sounds()
                        save_json(SETTINGS_FILE, self.settings)
                elif self.state == "playing":
                    self.handle_input(event.key)
            elif event.type in (pygame.JOYBUTTONDOWN, pygame.JOYAXISMOTION):
                if self.state == "playing":
                    self.handle_input(joy_event=event)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if self.state == "menu":
                    self.start_play()
                elif self.state == "playing":
                    self.flap()

    # ---------- main loop ----------
    def run(self):
        while self.running:
            dt = self.clock.tick(self.FPS)/1000.0
            self.handle_events()
            if self.state == "playing":
                self.update_game(dt)
            self.update_particles(dt)
            # render
            if self.state == "menu":
                self.draw_menu()
            elif self.state == "playing":
                self.draw_game()
            elif self.state == "settings":
                self.draw_settings()
            elif self.state == "leaderboard":
                self.draw_leaderboard()
            elif self.state == "gameover":
                self.draw_game()
                go_text = self.font_big.render("Game Over!", True, (255,50,50))
                self.screen.blit(go_text, (self.WIDTH//2 - go_text.get_width()//2, self.HEIGHT//2 - 50))
            self.render_particles()
            pygame.display.flip()
        pygame.quit()
        sys.exit()

# ------------------- RUN -------------------
if __name__ == "__main__":
    game = FlappyBirdGame()
    game.run()

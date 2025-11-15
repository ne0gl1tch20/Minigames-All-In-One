"""
Pixel Racer - A top-down endless racer built on your BaseMinigame template.

Features:
- Start Menu / Settings / Leaderboard (JSON saves)
- Keyboard + Joystick support
- Particle effects on collisions
- Simple, readable code to expand on
Requirements:
    pip install pygame
Run:
    python pixel_racer.py
"""

import pygame
import sys
import json
import os
import random
import math
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict

# ------------------- CONFIG / SAVE PATH -------------------
USER_DIR = os.path.expandvars(r"%userprofile%")
MG_SAVE_DIR = Path(USER_DIR) / "Documents" / ".mgaio"
APP_NAME = "PixelRacer"
SAVE_FOLDER = MG_SAVE_DIR / "Saves" / APP_NAME
SAVE_FOLDER.mkdir(parents=True, exist_ok=True)

SETTINGS_FILE = SAVE_FOLDER / "settings.json"
LEADERBOARD_FILE = SAVE_FOLDER / "leaderboard.json"

DEFAULT_SETTINGS = {
    "volume": 80,
    "sound": True,
    "difficulty": "normal",
    "keymap": {"left": pygame.K_a, "right": pygame.K_d, "boost": pygame.K_SPACE},
    "joymap": {"steer_axis": 0, "boost_button": 0},
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

# ------------------- BASE GAME CLASS (simplified template) -------------------
class BaseMinigame:
    WIDTH, HEIGHT = 800, 600
    FPS = 60

    def __init__(self):
        pygame.init()
        pygame.joystick.init()
        pygame.mixer.init()
        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT))
        pygame.display.set_caption(APP_NAME)
        self.clock = pygame.time.Clock()
        self.font_big = pygame.font.SysFont("segoe ui emoji", 48, bold=True)
        self.font_med = pygame.font.SysFont("segoe ui emoji", 24)
        self.font_small = pygame.font.SysFont("segoe ui emoji", 16)

        # Load settings / leaderboard
        self.settings = load_json(SETTINGS_FILE, DEFAULT_SETTINGS.copy())
        self.leaderboard = load_json(LEADERBOARD_FILE, DEFAULT_LEADERBOARD.copy())

        # Game state
        self.state = "menu"  # menu, settings, playing, gameover, leaderboard
        self.running = True
        self.particles: List[Particle] = []
        self.score = 0
        self.player_name = "You"

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
        pass

    def emit_particle(self, x, y, color=(255, 200, 60)):
        p = Particle(
            x=x,
            y=y,
            vx=random.uniform(-40,40),
            vy=random.uniform(-80,-20),
            life=0.8 + random.random()*0.6,
            size=random.uniform(2,5),
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
                if self.state == "menu":
                    if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                        self.start_play()
                    elif event.key == pygame.K_s:
                        self.state = "settings"
                elif self.state == "playing":
                    self.handle_input(key=event.key)
                elif self.state == "gameover":
                    if event.key == pygame.K_RETURN:
                        self.state = "menu"
                elif self.state == "settings":
                    if event.key == pygame.K_ESCAPE:
                        self.state = "menu"
            elif event.type in (pygame.JOYBUTTONDOWN, pygame.JOYAXISMOTION):
                if self.state == "playing":
                    self.handle_input(joy_event=event)

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
            alpha = max(0, min(255, int(255 * (p.life / 1.4))))
            surf = pygame.Surface((int(p.size*2), int(p.size*2)), pygame.SRCALPHA)
            pygame.draw.circle(surf, (*p.color, alpha), (int(p.size), int(p.size)), int(p.size))
            self.screen.blit(surf, (int(p.x - p.size), int(p.y - p.size)))

    def render(self):
        self.screen.fill((18, 18, 20))
        if self.state == "menu":
            self.draw_menu()
        elif self.state == "playing":
            self.draw_game()
        elif self.state == "settings":
            self.draw_settings()
        elif self.state == "gameover":
            self.draw_gameover()
        elif self.state == "leaderboard":
            self.draw_leaderboard()
        self.render_particles()
        pygame.display.flip()

    # ---------- menu / UI (simple placeholders) ----------
    def draw_menu(self):
        title = self.font_big.render(APP_NAME, True, (255, 200, 60))
        self.screen.blit(title, (self.WIDTH//2 - title.get_width()//2, 80))
        start = self.font_med.render("Press Enter to Start | S = Settings | L = Leaderboard", True, (200, 200, 200))
        self.screen.blit(start, (self.WIDTH//2 - start.get_width()//2, 260))
        hint = self.font_small.render("Use A/D or Left/Right arrows. Space for boost. Joystick supported.", True, (160,160,160))
        self.screen.blit(hint, (self.WIDTH//2 - hint.get_width()//2, 320))

    def draw_settings(self):
        text = self.font_med.render("Settings", True, (255,255,255))
        self.screen.blit(text, (40, 40))
        vol = self.font_small.render(f"Volume: {self.settings.get('volume',100)} (Up/Down to change)", True, (200,200,200))
        self.screen.blit(vol, (40,100))
        diff = self.font_small.render(f"Difficulty: {self.settings.get('difficulty','normal')} (Left/Right to toggle)", True, (200,200,200))
        self.screen.blit(diff, (40,140))
        back = self.font_small.render("Esc to return to menu", True, (150,150,150))
        self.screen.blit(back, (40, 200))

    def draw_game(self):
        score_text = self.font_med.render(f"Score: {self.score}", True, (255, 255, 255))
        self.screen.blit(score_text, (20, 20))

    def draw_gameover(self):
        over = self.font_big.render("Game Over", True, (220, 80, 80))
        self.screen.blit(over, (self.WIDTH//2 - over.get_width()//2, 120))
        info = self.font_med.render(f"Score: {self.score} - Press Enter to return to Menu", True, (200,200,200))
        self.screen.blit(info, (self.WIDTH//2 - info.get_width()//2, 220))

    def draw_leaderboard(self):
        title = self.font_big.render("Leaderboard", True, (255,200,60))
        self.screen.blit(title, (self.WIDTH//2 - title.get_width()//2, 40))
        if not self.leaderboard:
            none = self.font_med.render("No scores yet.", True, (180,180,180))
            self.screen.blit(none, (self.WIDTH//2 - none.get_width()//2, 200))
            return
        for i, entry in enumerate(self.leaderboard[:10]):
            txt = self.font_med.render(f"{i+1}. {entry.get('name','---')} - {entry.get('score',0)}", True, (220,220,220))
            self.screen.blit(txt, (200, 120 + i*40))

    # ---------- start / stop ----------
    def start_play(self):
        self.state = "playing"
        self.score = 0

# ------------------- Pixel Racer Game -------------------
class PixelRacer(BaseMinigame):
    LANE_COUNT = 3
    LANE_WIDTH = 150
    ROAD_X = 200
    ROAD_W = LANE_WIDTH * LANE_COUNT
    OBSTACLE_TIMER = 1.0  # seconds between obstacles, adjusts with difficulty

    def __init__(self):
        super().__init__()
        self.player = {"x": self.WIDTH//2, "y": self.HEIGHT - 140, "w": 44, "h": 64, "speed": 260, "angle": 0}
        self.obstacles: List[Dict] = []
        self.ob_timer = 0.0
        self.scroll = 0.0
        self.spawn_speed = 200
        self.boost = False
        self.boost_time = 0.0
        self.best_score = 0
        self.load_assets()
        # apply difficulty
        diff = self.settings.get("difficulty", "normal")
        if diff == "easy":
            self.OBSTACLE_TIMER = 1.2
        elif diff == "hard":
            self.OBSTACLE_TIMER = 0.75
        self.load_leaderboard()

    def load_assets(self):
        # simple surfaces used as sprites (rectangles)
        self.car_surf = pygame.Surface((self.player["w"], self.player["h"]), pygame.SRCALPHA)
        pygame.draw.polygon(self.car_surf, (255, 80, 80), [(0,self.player["h"]), (self.player["w"], self.player["h"]), (self.player["w"]*0.75,0), (self.player["w"]*0.25,0)])
        self.obs_surf = pygame.Surface((44, 60), pygame.SRCALPHA)
        pygame.draw.rect(self.obs_surf, (80,160,255), (0,0,44,60))
        # sounds
        try:
            self.snd_boost = pygame.mixer.Sound(os.path.join(os.path.dirname(__file__), "boost.wav")) if os.path.exists(os.path.join(os.path.dirname(__file__), "boost.wav")) else None
            self.snd_crash = pygame.mixer.Sound(os.path.join(os.path.dirname(__file__), "crash.wav")) if os.path.exists(os.path.join(os.path.dirname(__file__), "crash.wav")) else None
            vol = max(0.0, min(1.0, self.settings.get("volume",80)/100))
            if self.snd_boost: self.snd_boost.set_volume(vol)
            if self.snd_crash: self.snd_crash.set_volume(vol)
        except Exception:
            self.snd_boost = self.snd_crash = None

    def load_leaderboard(self):
        self.leaderboard = load_json(LEADERBOARD_FILE, DEFAULT_LEADERBOARD.copy())
        if self.leaderboard:
            try:
                self.best_score = max([e.get("score",0) for e in self.leaderboard])
            except Exception:
                self.best_score = 0

    def spawn_obstacle(self):
        lane = random.randrange(self.LANE_COUNT)
        lane_x = self.ROAD_X + lane * self.LANE_WIDTH + (self.LANE_WIDTH//2)
        obs = {"x": lane_x, "y": -80, "w": 44, "h": 60, "speed": self.spawn_speed + random.uniform(-30,30)}
        self.obstacles.append(obs)

    def update_game(self, dt):
        # move scroll & spawn obstacles
        speed_mod = 1.5 if self.boost else 1.0
        self.scroll += (120 * speed_mod) * dt
        self.ob_timer += dt * speed_mod
        # spawn logic based on timer & difficulty
        if self.ob_timer >= self.OBSTACLE_TIMER:
            self.ob_timer = 0.0
            self.spawn_obstacle()

        # update obstacles
        for obs in list(self.obstacles):
            obs["y"] += obs["speed"] * dt * (1.0 + self.scroll/10000.0)
            if obs["y"] > self.HEIGHT + 100:
                self.obstacles.remove(obs)
                self.score += 10  # passing obstacle yields points

        # boost decay
        if self.boost:
            self.boost_time -= dt
            if self.boost_time <= 0:
                self.boost = False

        # keyboard input (continuous)
        keys = pygame.key.get_pressed()
        steer = 0
        if keys[self.settings["keymap"]["left"]] or keys[pygame.K_LEFT]:
            steer = -1
        if keys[self.settings["keymap"].get("right", pygame.K_d)] or keys[pygame.K_RIGHT]:
            steer = 1

        # joystick steer if available
        if self.joystick:
            try:
                axis = self.joystick.get_axis(self.settings["joymap"].get("steer_axis", 0))
                if abs(axis) > 0.2:
                    steer = axis
            except Exception:
                pass

        # apply steering
        self.player["x"] += steer * self.player["speed"] * dt * (1.2 if self.boost else 1.0)
        # clamp to road
        min_x = self.ROAD_X + 22
        max_x = self.ROAD_X + self.ROAD_W - 22
        self.player["x"] = max(min_x, min(max_x, self.player["x"]))

        # collision
        player_rect = pygame.Rect(self.player["x"] - self.player["w"]//2, self.player["y"] - self.player["h"]//2, self.player["w"], self.player["h"])
        for obs in list(self.obstacles):
            obs_rect = pygame.Rect(obs["x"] - obs["w"]//2, obs["y"] - obs["h"]//2, obs["w"], obs["h"])
            if player_rect.colliderect(obs_rect):
                self.on_crash(obs_rect.centerx, obs_rect.centery)
                return

        # slowly increase difficulty
        if int(self.scroll) % 1000 == 0 and int(self.scroll) > 0:
            self.spawn_speed += 5

    def on_crash(self, x, y):
        # particles
        for _ in range(25):
            self.emit_particle(x + random.uniform(-20,20), y + random.uniform(-20,20), color=(255,120,60))
        # sound
        if self.snd_crash and self.settings.get("sound", True):
            try:
                self.snd_crash.play()
            except Exception:
                pass
        # save score to leaderboard
        self.save_score()
        self.state = "gameover"

    def save_score(self):
        # ask for a short name in console (simple)
        name = self.player_name
        entry = {"name": name, "score": self.score}
        self.leaderboard.append(entry)
        # keep top 10
        self.leaderboard = sorted(self.leaderboard, key=lambda e: e.get("score",0), reverse=True)[:20]
        save_json(LEADERBOARD_FILE, self.leaderboard)
        self.best_score = max(self.best_score, self.score)

    def handle_input(self, key=None, joy_event=None):
        # called for keydown and joystick events
        if key:
            if key == self.settings["keymap"].get("boost", pygame.K_SPACE):
                self.try_boost()
            # quick settings controls while in settings screen (Up/Down/Left/Right)
            if self.state == "settings":
                if key == pygame.K_UP:
                    self.settings["volume"] = min(100, self.settings.get("volume",80) + 5)
                    save_json(SETTINGS_FILE, self.settings)
                elif key == pygame.K_DOWN:
                    self.settings["volume"] = max(0, self.settings.get("volume",80) - 5)
                    save_json(SETTINGS_FILE, self.settings)
                elif key == pygame.K_LEFT or key == pygame.K_RIGHT:
                    diff = self.settings.get("difficulty","normal")
                    order = ["easy","normal","hard"]
                    idx = order.index(diff) if diff in order else 1
                    idx = (idx + (1 if key == pygame.K_RIGHT else -1)) % len(order)
                    self.settings["difficulty"] = order[idx]
                    save_json(SETTINGS_FILE, self.settings)
        if joy_event and self.joystick:
            # check for boost button
            if joy_event.type == pygame.JOYBUTTONDOWN:
                btn = joy_event.button
                if btn == self.settings["joymap"].get("boost_button", 0):
                    self.try_boost()
            elif joy_event.type == pygame.JOYAXISMOTION:
                pass  # continuous axis reading done in update_game

    def try_boost(self):
        if not self.boost:
            self.boost = True
            self.boost_time = 1.2  # seconds
            if self.snd_boost and self.settings.get("sound", True):
                try:
                    self.snd_boost.play()
                except Exception:
                    pass

    # ---------- drawing ----------
    def draw_game(self):
        # draw road
        self.screen.fill((18,18,20))
        pygame.draw.rect(self.screen, (40,40,45), (self.ROAD_X, 0, self.ROAD_W, self.HEIGHT))
        # lane lines
        for i in range(1, self.LANE_COUNT):
            x = self.ROAD_X + i*self.LANE_WIDTH
            for y in range(-50, self.HEIGHT+200, 40):
                yy = (y + (self.scroll % 40))
                pygame.draw.rect(self.screen, (200,200,200), (x-3, yy, 6, 24))
        # obstacles
        for obs in self.obstacles:
            self.screen.blit(self.obs_surf, (obs["x"] - obs["w"]//2, obs["y"] - obs["h"]//2))
        # player
        rotated = pygame.transform.rotate(self.car_surf, self.player["angle"])
        self.screen.blit(rotated, (self.player["x"] - rotated.get_width()//2, self.player["y"] - rotated.get_height()//2))
        # HUD
        score_text = self.font_med.render(f"Score: {self.score}", True, (240,240,240))
        self.screen.blit(score_text, (20,20))
        best_text = self.font_small.render(f"Best: {self.best_score}", True, (200,200,200))
        self.screen.blit(best_text, (20, 52))
        if self.boost:
            boost_text = self.font_small.render("BOOST!", True, (255,200,60))
            self.screen.blit(boost_text, (self.WIDTH - 120, 20))

    def draw_menu(self):
        # override base menu to provide nicer menu
        self.screen.fill((12,12,12))
        title = self.font_big.render("Pixel Racer", True, (255, 200, 60))
        self.screen.blit(title, (self.WIDTH//2 - title.get_width()//2, 60))
        self.screen.blit(self.car_surf, (self.WIDTH//2 - self.car_surf.get_width()//2, 160))
        start = self.font_med.render("Press Enter to Start", True, (200,200,200))
        self.screen.blit(start, (self.WIDTH//2 - start.get_width()//2, 320))
        hint = self.font_small.render("S = Settings | L = Leaderboard", True, (160,160,160))
        self.screen.blit(hint, (self.WIDTH//2 - hint.get_width()//2, 360))

    def draw_settings(self):
        # show settings via base method but also indicate joystick
        super().draw_settings()
        joy_text = "Joystick: " + (self.joystick.get_name() if self.joystick else "None")
        jt = self.font_small.render(joy_text, True, (180,180,180))
        self.screen.blit(jt, (40, 180))

    # override start_play to reset variables
    def start_play(self):
        self.state = "playing"
        self.score = 0
        self.obstacles.clear()
        self.ob_timer = 0.0
        self.scroll = 0.0
        self.spawn_speed = 200
        self.boost = False
        self.boost_time = 0.0
        # center player
        self.player["x"] = self.ROAD_X + self.ROAD_W // 2
        # set difficulty-based parameters
        diff = self.settings.get("difficulty", "normal")
        if diff == "easy":
            self.OBSTACLE_TIMER = 1.2
            self.spawn_speed = 180
        elif diff == "hard":
            self.OBSTACLE_TIMER = 0.75
            self.spawn_speed = 230
        else:
            self.OBSTACLE_TIMER = 1.0
            self.spawn_speed = 200

# ------------------- RUN -------------------
if __name__ == "__main__":
    game = PixelRacer()
    # allow quick keys to open leaderboard or settings from menu
    # minor override to capture L/S keys in event loop
    def custom_handle_events():
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                game.running = False
            elif event.type == pygame.KEYDOWN:
                if game.state == "menu":
                    if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                        game.start_play()
                    elif event.key == pygame.K_s:
                        game.state = "settings"
                    elif event.key == pygame.K_l:
                        game.state = "leaderboard"
                elif game.state == "settings":
                    if event.key == pygame.K_ESCAPE:
                        game.state = "menu"
                    else:
                        game.handle_input(key=event.key)
                elif game.state == "playing":
                    game.handle_input(key=event.key)
                elif game.state == "gameover":
                    if event.key == pygame.K_RETURN:
                        game.state = "menu"
                elif game.state == "leaderboard":
                    if event.key == pygame.K_ESCAPE:
                        game.state = "menu"
            elif event.type in (pygame.JOYBUTTONDOWN, pygame.JOYAXISMOTION):
                if game.state == "playing":
                    game.handle_input(joy_event=event)

    # inject custom event handling while preserving existing methods
    game.handle_events = custom_handle_events

    game.run()

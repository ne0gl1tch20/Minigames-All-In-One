"""
Dodge The Blocks — Fluid 3D Pixels with Power-ups
Single-file Pygame minigame built from the provided BaseMinigame template.

Requirements:
    pip install pygame

Run:
    python dodge_blocks_3d_pixels.py

Features:
- Menu / Settings / Leaderboard (JSON save)
- Keyboard + Joystick support
- Particle system
- Smooth player movement and camera shake
- "3D pixel" voxel-style rendering for blocks (simple fake-3D shading)
- Power-ups: Shield, Slow Time, Shrink, Score Multiplier
- Saveable settings + leaderboard

Author: Generated for user
"""

import pygame
import numpy as np
import sys
import json
import os
import random
import math
import time
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict, Optional

# ------------------- CONFIG / SAVE PATH -------------------
USER_DIR = os.path.expandvars(r"%userprofile%")
MG_SAVE_DIR = Path(USER_DIR) / "Documents" / ".mgaio"
APP_NAME = "Dodge3DPixels"
SAVE_FOLDER = MG_SAVE_DIR / "Saves" / APP_NAME
SAVE_FOLDER.mkdir(parents=True, exist_ok=True)

SETTINGS_FILE = SAVE_FOLDER / "settings.json"
LEADERBOARD_FILE = SAVE_FOLDER / "leaderboard.json"

pygame.mixer.pre_init(44100, -16, 2, 512)
pygame.init()

# default settings (use ints / strings only so JSON is stable)
DEFAULT_SETTINGS = {
    "volume": 80,
    "sound": True,
    "difficulty": "normal",
    "keymap": {"left": pygame.K_a, "right": pygame.K_d, "boost": pygame.K_SPACE},
    "joymap": {"axis_lr": 0, "button_boost": 0},
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

# ------------------- PARTICLE / HELPERS -------------------
@dataclass
class Particle:
    x: float
    y: float
    vx: float
    vy: float
    life: float
    size: float
    color: tuple


# ------------------- GAME ENTITIES -------------------
@dataclass
class Block:
    x: float
    y: float
    w: int
    h: int
    speed: float
    color: tuple
    pixels: List[List[int]]  # 2D pixel grid 1/0 for voxel presence
    id: int

    def rect(self):
        return pygame.Rect(self.x, self.y, self.w, self.h)


@dataclass
class PowerUp:
    x: float
    y: float
    typ: str
    size: int = 20
    lifespan: float = 8.0

    def rect(self):
        return pygame.Rect(self.x - self.size/2, self.y - self.size/2, self.size, self.size)


# ------------------- BASE MINIGAME (lightweight) -------------------
class BaseMinigame:
    WIDTH, HEIGHT = 900, 600
    FPS = 60

    def __init__(self):
        # Pygame already initialized above
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
        self.state = "menu"  # menu, settings, playing, gameover
        self.running = True
        self.particles: List[Particle] = []
        self.score = 0
        self.player_name = "Player"

        # Joystick
        self.joystick = None
        self.detect_joystick()

        # Audio stub
        self.sounds = {}

    def detect_joystick(self):
        pygame.joystick.init()
        if pygame.joystick.get_count() > 0:
            js = pygame.joystick.Joystick(0)
            js.init()
            self.joystick = js
            print("Joystick detected:", js.get_name())

    def emit_particle(self, x, y, color=(255, 200, 60), count=6):
        for _ in range(count):
            ang = random.uniform(0, math.tau)
            speed = random.uniform(40, 220)
            vx = math.cos(ang) * speed
            vy = math.sin(ang) * speed
            p = Particle(x=x, y=y, vx=vx, vy=vy, life=random.uniform(0.4, 1.2), size=random.uniform(2, 5), color=color)
            self.particles.append(p)

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

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if self.state == "menu" and event.key == pygame.K_RETURN:
                    self.start_play()
                elif self.state == "menu" and event.key == pygame.K_s:
                    self.state = "settings"
                elif self.state == "settings" and event.key == pygame.K_ESCAPE:
                    self.state = "menu"
                elif self.state == "gameover" and event.key == pygame.K_RETURN:
                    self.state = "menu"
                elif self.state == "playing":
                    self.handle_input(event.key)
            elif event.type in (pygame.JOYBUTTONDOWN, pygame.JOYAXISMOTION, pygame.JOYHATMOTION):
                if self.state == "playing":
                    self.handle_input(joy_event=event)

    def update_particles(self, dt):
        for p in list(self.particles):
            p.x += p.vx * dt
            p.y += p.vy * dt
            p.vy += 600 * dt
            p.life -= dt
            if p.life <= 0:
                self.particles.remove(p)

    def render_particles(self):
        for p in self.particles:
            alpha = max(0, min(255, int(255 * (p.life / 1.2))))
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
        elif self.state == "gameover":
            self.draw_gameover()
        self.render_particles()
        pygame.display.flip()

    def draw_menu(self):
        title = self.font_big.render(APP_NAME, True, (255, 200, 60))
        self.screen.blit(title, (self.WIDTH//2 - title.get_width()//2, 80))
        start = self.font_med.render("Press Enter to Start", True, (200, 200, 200))
        self.screen.blit(start, (self.WIDTH//2 - start.get_width()//2, 260))
        settings = self.font_small.render("S - Settings    Esc - Quit", True, (180, 180, 180))
        self.screen.blit(settings, (self.WIDTH//2 - settings.get_width()//2, 320))

    def draw_settings(self):
        text = self.font_med.render("Settings - Use JSON file to persist (volume, difficulty)", True, (255, 255, 255))
        self.screen.blit(text, (50, 50))

    def draw_game(self):
        score_text = self.font_med.render(f"Score: {self.score}", True, (255, 255, 255))
        self.screen.blit(score_text, (20, 20))

    def draw_gameover(self):
        over = self.font_big.render("Game Over", True, (250, 100, 80))
        self.screen.blit(over, (self.WIDTH//2 - over.get_width()//2, 120))
        scr = self.font_med.render(f"Score: {self.score}", True, (250, 200, 200))
        self.screen.blit(scr, (self.WIDTH//2 - scr.get_width()//2, 220))
        cont = self.font_small.render("Press Enter to return to menu", True, (200, 200, 200))
        self.screen.blit(cont, (self.WIDTH//2 - cont.get_width()//2, 300))

    # stubs to override
    def update_game(self, dt):
        pass

    def handle_input(self, key=None, joy_event=None):
        pass

    def start_play(self):
        self.state = "playing"
        self.score = 0


# ------------------- DODGE GAME IMPLEMENTATION -------------------
class Dodge3DPixels(BaseMinigame):
    def __init__(self):
        super().__init__()
        # Player
        self.player_w = 64
        self.player_h = 18
        self.player_x = self.WIDTH // 2
        self.player_y = self.HEIGHT - 80
        self.player_vx = 0.0
        self.player_speed = 600.0
        self.player_friction = 12.0
        self.player_shrink = 1.0

        # Blocks and powerups
        self.blocks: List[Block] = []
        self.block_timer = 0.0
        self.spawn_interval = 0.9
        self.block_id_counter = 0

        self.powerups: List[PowerUp] = []
        self.powerup_timer = 0.0

        # gameplay
        self.difficulty_scale = 1.0
        self.running_time = 0.0
        self.score = 0
        self.multiplier = 1.0

        # active effects
        self.shield_time = 0.0
        self.slow_time = 0.0
        self.shrink_time = 0.0
        self.boosting = False

        # visual
        self.camera_shake = 0.0

        # load simple sounds
        self.load_sounds()

    def load_sounds(self):
        """Load procedural chiptune sounds for effects"""
        self.sounds = {}

        if not self.settings.get("sound", True):
            return  # sounds disabled

        volume = self.settings.get("volume", 80) / 100.0

        def make_chiptune(freq=440, duration=0.12, vol=0.5, sample_rate=44100):
            t = np.linspace(0, duration, int(sample_rate*duration), False)
            wave = 0.5 * np.sign(np.sin(2*np.pi*freq*t))  # square wave
            wave = (wave * 32767 * vol).astype(np.int16)

            # Convert to stereo by duplicating channel
            stereo_wave = np.column_stack((wave, wave))

            return pygame.sndarray.make_sound(stereo_wave)


        # assign sounds
        self.sounds["shield"] = make_chiptune(880, 0.15, volume)   # shield absorbs
        self.sounds["shrink"] = make_chiptune(660, 0.12, volume)   # dodge while shrunk
        self.sounds["gameover"] = make_chiptune(330, 0.25, volume) # death
        self.sounds["powerup"] = make_chiptune(1200, 0.12, volume) # powerup collected
        self.sounds["block_destroy"] = make_chiptune(900, 0.10, volume) # block removed

    # --- game lifecycle ---
    def start_play(self):
        super().start_play()
        self.blocks.clear()
        self.powerups.clear()
        self.block_timer = 0
        self.powerup_timer = 6
        self.block_id_counter = 0
        self.difficulty_scale = 1.0
        self.running_time = 0.0
        self.multiplier = 1.0
        self.score = 0
        self.shield_time = 0.0
        self.slow_time = 0.0
        self.shrink_time = 0.0
        self.camera_shake = 0.0

    # --- input ---
    def handle_input(self, key=None, joy_event=None):
        if key:
            if key == self.settings["keymap"].get("boost"):
                self.boosting = True
        if joy_event:
            if joy_event.type == pygame.JOYBUTTONDOWN:
                pass
            elif joy_event.type == pygame.JOYAXISMOTION:
                pass

    # --- entity creation ---
    def make_block_pixels(self, cols=3, rows=2):
        # produce a small random pixel map (1/0) of size cols x rows
        grid = [[1 if random.random() > 0.15 else 0 for _ in range(cols)] for _ in range(rows)]
        return grid

    def spawn_block(self):
        cols = random.choice([2,3,4,5])
        rows = random.choice([1,2,3])
        pixel_w = cols * 6
        pixel_h = rows * 6
        x = random.uniform(40, self.WIDTH - 40 - pixel_w)
        y = -pixel_h - 10
        base_speed = random.uniform(160, 260) * (1.0 + self.difficulty_scale*0.25)
        color = (random.randint(80, 255), random.randint(60, 200), random.randint(60, 220))
        self.block_id_counter += 1
        block = Block(x=x, y=y, w=pixel_w, h=pixel_h, speed=base_speed, color=color, pixels=self.make_block_pixels(cols, rows), id=self.block_id_counter)
        self.blocks.append(block)

    def spawn_powerup(self):
        x = random.uniform(60, self.WIDTH - 60)
        y = -20
        typ = random.choice(["shield", "slow", "shrink", "mult"])
        self.powerups.append(PowerUp(x=x, y=y, typ=typ))

    # --- update loop ---
    def update_game(self, dt):
        # dt affected by slow powerup
        if self.slow_time > 0:
            dt *= 0.55
            self.slow_time -= dt / 0.55
        else:
            self.slow_time = max(0.0, self.slow_time)

        self.running_time += dt
        self.block_timer += dt
        if self.block_timer >= max(0.25, self.spawn_interval - self.difficulty_scale*0.08):
            self.spawn_block()
            self.block_timer = 0
            # increase difficulty slowly
            self.difficulty_scale += 0.01

        self.powerup_timer += dt
        if self.powerup_timer >= 6.0:
            if random.random() < 0.6:
                self.spawn_powerup()
            self.powerup_timer = 0

        # player movement (keyboard + joystick)
        keys = pygame.key.get_pressed()
        mv = 0.0
        if keys[self.settings["keymap"].get("left", pygame.K_a)]:
            mv -= 1.0
        if keys[self.settings["keymap"].get("right", pygame.K_d)]:
            mv += 1.0

        # joystick horizontal axis
        if self.joystick:
            try:
                ax = self.joystick.get_axis(self.settings.get("joymap", {}).get("axis_lr", 0))
                if abs(ax) > 0.15:
                    mv = ax
            except Exception:
                pass

        target_vx = mv * self.player_speed * (1.5 if self.boosting else 1.0)
        # smooth velocity
        self.player_vx += (target_vx - self.player_vx) * min(1, self.player_friction * dt)
        self.player_x += self.player_vx * dt
        self.boosting = False

        # clamp
        half = self.player_w * 0.5 * self.player_shrink
        self.player_x = max(half + 10, min(self.WIDTH - half - 10, self.player_x))

        # update blocks
        for b in list(self.blocks):
            b.y += b.speed * dt
            # add small wobble for "fluid" sense
            wobble = math.sin((self.running_time + b.id*0.3) * 3.0) * 6.0
            b.x += math.sin(self.running_time*0.6 + b.id) * 20 * dt
            # remove if off-screen
            if b.y > self.HEIGHT + 200:
                self.blocks.remove(b)
                self.score += int(10 * self.multiplier)
                self.emit_particle(b.x + b.w/2, self.HEIGHT - 60, color=b.color, count=6)

        # powerups
        for p in list(self.powerups):
            p.y += 140 * dt
            p.lifespan -= dt
            if p.lifespan <= 0 or p.y > self.HEIGHT + 40:
                if p in self.powerups: self.powerups.remove(p)

        # collisions
        player_rect = pygame.Rect(self.player_x - half, self.player_y - self.player_h/2, self.player_w * self.player_shrink, self.player_h)
        for b in list(self.blocks):
            if player_rect.colliderect(b.rect()):
                if self.shield_time > 0:
                    self.shield_time -= 0.8
                    if b in self.blocks: self.blocks.remove(b)
                    self.emit_particle(player_rect.centerx, player_rect.centery, color=(200,255,255), count=12)
                    self.sounds.get("shield") and self.sounds["shield"].play()
                    continue
                if self.shrink_time > 0:
                    if random.random() < 0.45:
                        if b in self.blocks: self.blocks.remove(b)
                        self.emit_particle(player_rect.centerx, player_rect.centery, color=(255,255,120), count=8)
                        self.sounds.get("shrink") and self.sounds["shrink"].play()
                        continue
                # game over
                self.sounds.get("gameover") and self.sounds["gameover"].play()
                self.game_over()
                return

        # player pickup powerups
        # --- inside powerup pickup ---
        for p in list(self.powerups):
            if player_rect.colliderect(p.rect()):
                self.apply_powerup(p.typ)
                if p in self.powerups: self.powerups.remove(p)
                self.emit_particle(p.x, p.y, color=(255,255,255), count=12)
                self.sounds.get("powerup") and self.sounds["powerup"].play()

        # update active timers
        if self.shield_time > 0:
            self.shield_time = max(0.0, self.shield_time - dt)
        if self.shrink_time > 0:
            self.shrink_time = max(0.0, self.shrink_time - dt)
            self.player_shrink = 0.6
        else:
            self.player_shrink = 1.0
        if self.multiplier > 1.0:
            # multiplier naturally decays slowly
            self.multiplier = max(1.0, self.multiplier - dt * 0.02)

        # camera shake decay
        self.camera_shake = max(0.0, self.camera_shake - dt*4.0)

    # --- powerup effects ---
    def apply_powerup(self, typ: str):
        if typ == "shield":
            self.shield_time = max(self.shield_time, 4.0)
        elif typ == "slow":
            self.slow_time = max(self.slow_time, 4.0)
        elif typ == "shrink":
            self.shrink_time = max(self.shrink_time, 5.0)
        elif typ == "mult":
            self.multiplier = min(3.0, self.multiplier + 0.8)
        # small camera shake
        self.camera_shake = 0.6

    # --- render helpers ---
    def draw_voxel(self, x, y, size, color, depth_offset=4):
        """Draws a fake-3D pixel cube by drawing top, left and right faces.
        size = face square size
        depth_offset = offset for shading
        """
        # compute face colors (slightly lighter/darker)
        r, g, b = color
        top = (min(255, int(r*1.05)), min(255, int(g*1.05)), min(255, int(b*1.05)))
        left = (max(0, int(r*0.85)), max(0, int(g*0.85)), max(0, int(b*0.85)))
        right = (max(0, int(r*0.95)), max(0, int(g*0.95)), max(0, int(b*0.95)))

        # top face
        top_poly = [(x, y), (x+size, y), (x+size-depth_offset, y-depth_offset), (x-depth_offset, y-depth_offset)]
        pygame.draw.polygon(self.screen, top, top_poly)
        # left face
        left_poly = [(x-depth_offset, y-depth_offset), (x, y), (x, y+size), (x-depth_offset, y+size-depth_offset)]
        pygame.draw.polygon(self.screen, left, left_poly)
        # right face
        right_poly = [(x+size, y), (x+size-depth_offset, y-depth_offset), (x+size, y+size), (x+size-depth_offset, y+size-depth_offset)]
        pygame.draw.polygon(self.screen, right, right_poly)

    def draw_block_voxels(self, b: Block):
        # render block's pixel grid as small voxel cubes
        cols = len(b.pixels[0]) if b.pixels else 1
        rows = len(b.pixels)
        cell_w = b.w / cols
        cell_h = b.h / rows
        # add wobble for fluid effect
        wob = math.sin((self.running_time + b.id*0.13)*3.5) * 2.2
        for r in range(rows):
            for c in range(cols):
                if b.pixels[r][c]:
                    px = b.x + c * cell_w
                    py = b.y + r * cell_h
                    # jitter and slight perspective
                    dx = math.sin((r+c) * 0.7 + self.running_time*1.2 + b.id) * wob
                    dy = math.cos((r-c) * 0.5 + self.running_time*1.05 + b.id) * wob * 0.6
                    self.draw_voxel(int(px + dx), int(py + dy), int(min(cell_w, cell_h)-2), b.color, depth_offset=4)

    def draw_player(self):
        half = self.player_w*0.5*self.player_shrink
        pr = pygame.Rect(self.player_x-half, self.player_y-self.player_h/2, self.player_w*self.player_shrink, self.player_h)
        pygame.draw.rect(self.screen, (220,220,255) if self.shield_time>0 else (220,220,220), pr, border_radius=6)
        # small glow
        glow = pygame.Surface((int(pr.width+20), int(pr.height+12)), pygame.SRCALPHA)
        pygame.draw.ellipse(glow, (180,200,255,60), glow.get_rect())
        self.screen.blit(glow, (pr.x-10, pr.y-6))

    def draw_hud(self):
        score_text = self.font_med.render(f"Score: {self.score}", True, (240,240,240))
        self.screen.blit(score_text, (14, 10))
        status = []
        if self.shield_time>0: status.append(f"Shield:{int(self.shield_time)}")
        if self.slow_time>0: status.append(f"Slow:{int(self.slow_time)}")
        if self.shrink_time>0: status.append(f"Small:{int(self.shrink_time)}")
        if self.multiplier>1.0: status.append(f"x{self.multiplier:.1f}")
        st = "  ".join(status)
        stt = self.font_small.render(st, True, (210,210,210))
        self.screen.blit(stt, (14, 46))

    def draw_game(self):
        # camera shake
        shake_x = random.uniform(-1,1) * self.camera_shake * 8
        shake_y = random.uniform(-1,1) * self.camera_shake * 6
        # draw background gradient
        for i in range(0, self.HEIGHT, 24):
            shade = 16 + int(60 * (i / self.HEIGHT))
            pygame.draw.rect(self.screen, (shade, shade, shade+8), (0, i, self.WIDTH, 24))

        # create a surface for world to apply camera shift
        world = pygame.Surface((self.WIDTH, self.HEIGHT), pygame.SRCALPHA)

        # draw ground line
        pygame.draw.rect(world, (20,20,26), (0, self.HEIGHT-70, self.WIDTH, 70))

        # draw blocks (voxels)
        for b in self.blocks:
            self.draw_block_voxels(b)

        # draw powerups
        for p in self.powerups:
            # icon style
            pr = p.rect()
            col = (255,220,80) if p.typ=="mult" else (120,200,255) if p.typ=="shield" else (180,255,170) if p.typ=="shrink" else (255,150,150)
            pygame.draw.ellipse(self.screen, col, pr)
            label = self.font_small.render(p.typ[0].upper(), True, (10,10,10))
            self.screen.blit(label, (p.x-6, p.y-10))

        # draw player
        self.draw_player()

        # draw HUD on top
        self.draw_hud()

        # particles are rendered in parent
        # optional: additional scoreboard

    def game_over(self):
        # save to leaderboard
        name = self.player_name or "Player"
        entry = {"name": name, "score": int(self.score), "time": int(time.time())}
        self.leaderboard.append(entry)
        self.leaderboard = sorted(self.leaderboard, key=lambda x: x["score"], reverse=True)[:12]
        save_json(LEADERBOARD_FILE, self.leaderboard)
        # explosion
        self.emit_particle(self.player_x, self.player_y, color=(255,80,40), count=30)
        self.state = "gameover"

# ------------------- RUN -------------------
if __name__ == "__main__":
    game = Dodge3DPixels()
    print("Controls: A/D or ←/→ to move, Space to boost (configurable).")
    print("Objective: avoid falling voxel-blocks. Pick up powerups (shield, slow, shrink, mult).")
    game.run()

"""
Lizard Defender - Upgraded
Features:
- Multiple insect types (different sizes / speeds / points)
- Power-ups (speed boost)
- JSON leaderboard (saved to Documents/.mgaio/Saves/LizardDefender/leaderboard.json)
- Improved "3D fluid" particle system (layered particles + additive blending)
- Menu / Playing / Game Over states
- Joystick support (basic detect)
Requirements:
    pip install pygame
Run:
    python lizard_defender.py
"""

import pygame
import sys
import random
import json
import os
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict
from datetime import datetime

# ------------------- CONFIG / SAVE PATH -------------------
USER_DIR = os.path.expandvars(r"%userprofile%")
MG_SAVE_DIR = Path(USER_DIR) / "Documents" / ".mgaio"
APP_NAME = "LizardDefender"
SAVE_FOLDER = MG_SAVE_DIR / "Saves" / APP_NAME
SAVE_FOLDER.mkdir(parents=True, exist_ok=True)

LEADERBOARD_FILE = SAVE_FOLDER / "leaderboard.json"

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
    layer: int  # used for layered draw (gives 3D look)

@dataclass
class Insect:
    x: float
    y: float
    speed: float
    radius: int
    type: str

@dataclass
class PowerUp:
    x: float
    y: float
    duration: float
    active: bool = False

# ------------------- GAME CLASS -------------------
class LizardDefender:
    WIDTH, HEIGHT = 800, 600
    FPS = 60

    def __init__(self):
        pygame.init()
        pygame.joystick.init()
        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT))
        pygame.display.set_caption(APP_NAME + " 🦎")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("segoe ui emoji", 22)
        self.bigfont = pygame.font.SysFont("segoe ui emoji", 40, bold=True)

        # game data
        self.running = True
        self.state = "menu"   # menu, playing, gameover
        self.score = 0
        self.lives = 3
        self.lizard_x = self.WIDTH // 2
        self.lizard_y = self.HEIGHT - 60
        self.lizard_speed = 300
        self.base_speed = 300
        self.insects: List[Insect] = []
        self.spawn_timer = 0.0
        self.particles: List[Particle] = []
        self.powerups: List[PowerUp] = []
        self.powerup_timer = 0.0
        self.leaderboard: List[Dict] = self.load_leaderboard()
        self.player_name = "Player"
        self.joystick = None
        self.detect_joystick()

        # Visual tweaks for particles
        self.particle_gravity = 200.0
        self.particle_damping = 0.99

    # ---------- JOYSTICK ----------
    def detect_joystick(self):
        if pygame.joystick.get_count() > 0:
            try:
                js = pygame.joystick.Joystick(0)
                js.init()
                self.joystick = js
                print("Joystick detected:", js.get_name())
            except Exception:
                self.joystick = None

    # ---------- LEADERBOARD ----------
    def load_leaderboard(self) -> List[Dict]:
        if LEADERBOARD_FILE.exists():
            try:
                with open(LEADERBOARD_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return []
        return []

    def save_leaderboard(self):
        try:
            entry = {
                "name": self.player_name,
                "score": int(self.score),
                "date": datetime.utcnow().isoformat() + "Z"
            }
            # only append if meaningful score
            if entry["score"] > 0:
                self.leaderboard.append(entry)
            # keep top 10
            self.leaderboard = sorted(self.leaderboard, key=lambda x: x["score"], reverse=True)[:10]
            with open(LEADERBOARD_FILE, "w", encoding="utf-8") as f:
                json.dump(self.leaderboard, f, indent=2)
        except Exception as e:
            print("Failed to save leaderboard:", e)

    # ---------- PARTICLES (3D-fluid-ish) ----------
    def emit_particle(self, x, y, color=(0, 255, 0), count=12):
        # spawn layered particles; layer 0 = big/back, layer 1 = mid, layer 2 = small/bright front
        for _ in range(count):
            layer = random.choices([0, 1, 2], weights=[0.25, 0.45, 0.3])[0]
            size = random.uniform(2.0, 6.0) * (1.0 + layer * 0.6)  # larger on higher layers
            speed_x = random.uniform(-120, 120) * (1.0 + layer * 0.3)
            speed_y = random.uniform(-220, -40) * (1.0 - layer * 0.15)
            life = random.uniform(0.5, 1.2) * (1.0 + layer * 0.4)
            # layer tint variation
            c = tuple(min(255, int(ch * (0.7 + 0.15 * layer))) for ch in color)
            self.particles.append(Particle(x, y, speed_x, speed_y, life, size, c, layer))

    def update_particles(self, dt: float):
        for p in list(self.particles):
            p.vx *= self.particle_damping
            p.vy += self.particle_gravity * dt
            p.x += p.vx * dt
            p.y += p.vy * dt
            # shrink slightly as life decreases
            p.size *= (0.998 ** (dt * 60))
            p.life -= dt
            if p.life <= 0 or p.size < 0.5:
                self.particles.remove(p)

    def render_particles(self):
        # render back-to-front to get a nicer layered 3D effect
        # use additive blending for glow (special_flags=BLEND_ADD)
        # draw larger, more transparent blobs for back layers, small bright for front layers
        layers = sorted(self.particles, key=lambda p: p.layer)
        for p in layers:
            alpha = max(8, min(255, int(255 * (p.life / (1.2 + p.layer * 0.4)))))
            # draw as multiple concentric circles to simulate volume
            surf_size = max(4, int(p.size * 3))
            surf = pygame.Surface((surf_size * 2, surf_size * 2), pygame.SRCALPHA)
            cx = cy = surf_size
            # outer soft circle (low alpha)
            pygame.draw.circle(surf, (*p.color, max(4, alpha // (2 + p.layer))), (cx, cy), int(p.size * 1.6))
            # middle
            pygame.draw.circle(surf, (*p.color, max(8, alpha // (1 + p.layer))), (cx, cy), int(p.size * 1.0))
            # inner bright
            pygame.draw.circle(surf, (*p.color, alpha), (cx, cy), max(1, int(p.size * 0.5)))
            # scale slightly by layer (back layers smaller scale)
            pos = (int(p.x - surf.get_width() // 2), int(p.y - surf.get_height() // 2))
            self.screen.blit(surf, pos, special_flags=pygame.BLEND_ADD)

    # ---------- GAME LOGIC ----------
    def spawn_insect(self):
        x = random.randint(20, self.WIDTH - 20)
        insect_type = random.choices(["red", "blue", "yellow"], weights=[0.45, 0.35, 0.20])[0]
        speed = {"red": random.uniform(60, 120), "blue": random.uniform(40, 85), "yellow": random.uniform(80, 150)}[insect_type]
        radius = {"red": 15, "blue": 10, "yellow": 20}[insect_type]
        self.insects.append(Insect(x, -radius - 5, speed, radius, insect_type))

        # chance to spawn a falling powerup (rare)
        if random.random() < 0.05:
            pu_x = random.randint(50, self.WIDTH - 50)
            self.powerups.append(PowerUp(pu_x, -10, duration=4.5))

    def update_insects(self, dt: float):
        # update insects falling
        for insect in list(self.insects):
            insect.y += insect.speed * dt
            # if insect reaches house bottom (missed), player loses a life
            if insect.y >= self.HEIGHT - 20:
                self.insects.remove(insect)
                self.lives -= 1
                self.emit_particle(insect.x, self.HEIGHT - 30, color=(255, 120, 80), count=20)
                if self.lives <= 0:
                    self.on_game_over()
                continue
            # collision with lizard (catch)
            if abs(insect.x - self.lizard_x) < 30 and abs(insect.y - self.lizard_y) < 25:
                # award score based on type
                gained = {"red": 1, "blue": 2, "yellow": 3}[insect.type]
                self.emit_particle(insect.x, insect.y, color={"red": (255, 60, 60), "blue": (80, 120, 255), "yellow": (255, 230, 100)}[insect.type], count=18)
                self.score += gained
                self.insects.remove(insect)

        # update powerups
        for pu in list(self.powerups):
            pu.y += 110 * dt
            if pu.y >= self.HEIGHT - 30:
                # if powerup hits ground, disappear
                self.powerups.remove(pu)
                continue
            if abs(pu.x - self.lizard_x) < 30 and abs(pu.y - self.lizard_y) < 25:
                # pick up powerup
                self.powerups.remove(pu)
                self.lizard_speed = self.base_speed * 1.8
                self.powerup_timer = pu.duration
                self.emit_particle(pu.x, pu.y, color=(120, 255, 255), count=22)

        # handle active powerup duration
        if self.powerup_timer > 0:
            self.powerup_timer -= dt
            # small visual effect while active
            if random.random() < 0.08:
                self.emit_particle(self.lizard_x + random.uniform(-18, 18), self.lizard_y + random.uniform(-6, 6), color=(160, 255, 255), count=2)
        else:
            self.lizard_speed = self.base_speed

    # ---------- INPUT ----------
    def handle_input(self, dt: float):
        # keyboard
        keys = pygame.key.get_pressed()
        left = keys[pygame.K_LEFT] or keys[pygame.K_a]
        right = keys[pygame.K_RIGHT] or keys[pygame.K_d]
        move = 0.0
        if left:
            move -= 1.0
        if right:
            move += 1.0

        # joystick axis (if available)
        if self.joystick:
            try:
                axis = self.joystick.get_axis(0)
                # apply deadzone
                if abs(axis) > 0.15:
                    move += axis
            except Exception:
                pass

        self.lizard_x += move * self.lizard_speed * dt
        # clamp to screen
        self.lizard_x = max(30, min(self.WIDTH - 30, self.lizard_x))

    # ---------- RENDER ----------
    def draw_game(self):
        # background
        self.screen.fill((40, 120, 40))  # garden green
        # draw distant "ground / house" strip
        pygame.draw.rect(self.screen, (80, 60, 40), (0, self.HEIGHT - 40, self.WIDTH, 40))
        # draw lizard (simple stylized body + eye)
        body_rect = pygame.Rect(self.lizard_x - 28, self.lizard_y - 12, 56, 24)
        pygame.draw.ellipse(self.screen, (20, 160, 20), body_rect)
        # tail
        pygame.draw.polygon(self.screen, (18, 140, 18), [(self.lizard_x - 28, self.lizard_y + 2), (self.lizard_x - 50, self.lizard_y - 4), (self.lizard_x - 28, self.lizard_y - 8)])
        # eye
        pygame.draw.circle(self.screen, (255, 255, 255), (int(self.lizard_x + 14), int(self.lizard_y - 4)), 5)
        pygame.draw.circle(self.screen, (10, 10, 10), (int(self.lizard_x + 15), int(self.lizard_y - 3)), 2)

        # draw insects
        for insect in self.insects:
            color = {"red": (200, 40, 40), "blue": (40, 90, 220), "yellow": (210, 200, 40)}[insect.type]
            pygame.draw.circle(self.screen, color, (int(insect.x), int(insect.y)), insect.radius)
            # little legs as lines
            pygame.draw.line(self.screen, (30, 30, 30), (insect.x - insect.radius/1.2, insect.y + insect.radius/1.8), (insect.x - insect.radius/2, insect.y + insect.radius/0.9), 2)
            pygame.draw.line(self.screen, (30, 30, 30), (insect.x + insect.radius/1.2, insect.y + insect.radius/1.8), (insect.x + insect.radius/2, insect.y + insect.radius/0.9), 2)

        # draw powerups
        for pu in self.powerups:
            rect = pygame.Rect(pu.x - 10, pu.y - 10, 20, 20)
            pygame.draw.rect(self.screen, (60, 220, 220), rect)
            # symbol (lightning)
            pygame.draw.line(self.screen, (255, 255, 255), (pu.x - 3, pu.y - 2), (pu.x + 1, pu.y - 2), 2)
            pygame.draw.line(self.screen, (255, 255, 255), (pu.x - 0, pu.y - 2), (pu.x + 3, pu.y + 3), 2)

        # particles (draw before HUD so glow blends into scene)
        self.render_particles()

        # HUD
        score_text = self.font.render(f"Score: {self.score}", True, (255, 255, 255))
        lives_text = self.font.render(f"Lives: {self.lives}", True, (255, 255, 255))
        speed_text = self.font.render(f"Speed Boost: {int(self.powerup_timer)}s" if self.powerup_timer > 0 else "", True, (200, 255, 240))
        self.screen.blit(score_text, (12, 12))
        self.screen.blit(lives_text, (12, 40))
        self.screen.blit(speed_text, (12, 68))

    def draw_menu(self):
        self.screen.fill((12, 12, 12))
        title = self.bigfont.render("Lizard Defender 🦎", True, (255, 200, 60))
        self.screen.blit(title, (self.WIDTH // 2 - title.get_width() // 2, 80))
        start = self.font.render("Press ENTER to Start", True, (255, 255, 255))
        self.screen.blit(start, (self.WIDTH // 2 - start.get_width() // 2, 180))
        info = self.font.render("Move: ← →  or A/D. Catch insects to score. Missed insects cost lives.", True, (200, 200, 200))
        self.screen.blit(info, (self.WIDTH // 2 - info.get_width() // 2, 230))

        # leaderboard preview
        if self.leaderboard:
            lb_title = self.font.render("Leaderboard:", True, (255, 220, 100))
            self.screen.blit(lb_title, (self.WIDTH // 2 - 80, 280))
            for i, entry in enumerate(self.leaderboard[:6]):
                txt = self.font.render(f"{i+1}. {entry.get('name','Player')[:10]:10s}  {entry.get('score',0):5d}", True, (255, 255, 255))
                self.screen.blit(txt, (self.WIDTH // 2 - 80, 320 + i * 28))

    def draw_gameover(self):
        self.screen.fill((6, 6, 6))
        title = self.bigfont.render("Game Over", True, (255, 80, 80))
        self.screen.blit(title, (self.WIDTH // 2 - title.get_width() // 2, 80))
        score_txt = self.font.render(f"Final Score: {self.score}", True, (255, 255, 255))
        self.screen.blit(score_txt, (self.WIDTH // 2 - score_txt.get_width() // 2, 180))
        hint = self.font.render("Press ENTER to return to menu", True, (200, 200, 200))
        self.screen.blit(hint, (self.WIDTH // 2 - hint.get_width() // 2, 230))

        # show top leaderboard
        if self.leaderboard:
            lb_title = self.font.render("Top Scores:", True, (255, 220, 100))
            self.screen.blit(lb_title, (self.WIDTH // 2 - 80, 280))
            for i, entry in enumerate(self.leaderboard[:6]):
                txt = self.font.render(f"{i+1}. {entry.get('name','Player')[:10]:10s}  {entry.get('score',0):5d}", True, (255, 255, 255))
                self.screen.blit(txt, (self.WIDTH // 2 - 80, 320 + i * 28))

    # ---------- GAME OVER / RESET ----------
    def on_game_over(self):
        # save leaderboard entry and switch state
        # ask for player name via console? keep default "Player" but save timestamped entry
        # (keeping this simple so we don't block the pygame loop)
        self.save_leaderboard()
        self.state = "gameover"

    def reset_for_play(self):
        self.score = 0
        self.lives = 3
        self.spawn_timer = 0.0
        self.insects.clear()
        self.particles.clear()
        self.powerups.clear()
        self.powerup_timer = 0.0
        self.lizard_x = self.WIDTH // 2
        self.lizard_speed = self.base_speed

    # ---------- MAIN LOOP ----------
    def run(self):
        while self.running:
            dt = self.clock.tick(self.FPS) / 1000.0
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    # universal keys
                    if event.key == pygame.K_ESCAPE:
                        self.running = False

                    if self.state == "menu":
                        if event.key == pygame.K_RETURN:
                            # start game
                            self.reset_for_play()
                            self.state = "playing"
                    elif self.state == "gameover":
                        if event.key == pygame.K_RETURN:
                            self.state = "menu"
                    elif self.state == "playing":
                        # debug: press P to spawn powerup on player
                        if event.key == pygame.K_p:
                            self.powerups.append(PowerUp(self.lizard_x, self.lizard_y - 30, duration=4.5))

            # state updates
            if self.state == "menu":
                self.draw_menu()

            elif self.state == "playing":
                # spawn logic (faster spawn as score increases)
                self.spawn_timer += dt
                spawn_interval = max(0.35, 1.1 - (self.score * 0.02))
                if self.spawn_timer >= spawn_interval:
                    self.spawn_insect()
                    self.spawn_timer = 0.0

                self.handle_input(dt)
                self.update_insects(dt)
                self.update_particles(dt)
                self.draw_game()

            elif self.state == "gameover":
                self.draw_gameover()

            pygame.display.flip()

        # on exit
        self.save_leaderboard()
        pygame.quit()
        sys.exit()


# ------------------- RUN -------------------
if __name__ == "__main__":
    game = LizardDefender()
    try:
        game.run()
    except Exception as e:
        print("Error:", e)
        pygame.quit()
        sys.exit(1)

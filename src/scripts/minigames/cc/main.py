"""
Coin Collector - main.py
Drop this file in a folder named `CoinCollector` inside your launcher's `minigames` folder.

It includes:
- A playable Coin Collector minigame (Pygame)
- Start menu, in-game, game over with name entry
- Particle effects on coin collection
- Saveable settings and leaderboard (JSON) in Documents/.mgaio/Saves/CoinCollector
- Keyboard + basic joystick support

Also place this `config.json` beside this file (example provided below) so your launcher shows proper metadata.

config.json example:
{
  "title": "Coin Collector",
  "description": "Collect as many coins as you can before the timer runs out! Avoid hazards and rack up a high score.",
  "how_to_play": "Use arrow keys / WASD to move. Collect coins to increase score. Survive until the timer ends. Press Enter to start.",
  "tags": ["Arcade","Collector","Fast-Paced"]
}

Requirements:
pip install pygame

Run:
python main.py
"""

import pygame
import sys
import json
import os
import random
import time
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict

# ------------------- CONFIG / SAVE PATH -------------------
USER_DIR = os.path.expandvars(r"%userprofile%") if os.name == 'nt' else os.path.expanduser('~')
MG_SAVE_DIR = Path(USER_DIR) / "Documents" / ".mgaio"
APP_NAME = "CoinCollector"
SAVE_FOLDER = MG_SAVE_DIR / "Saves" / APP_NAME
SAVE_FOLDER.mkdir(parents=True, exist_ok=True)

SETTINGS_FILE = SAVE_FOLDER / "settings.json"
LEADERBOARD_FILE = SAVE_FOLDER / "leaderboard.json"

DEFAULT_SETTINGS = {
    "volume": 100,
    "sound": True,
    "difficulty": "normal",
    "keymap": {"left": pygame.K_LEFT, "right": pygame.K_RIGHT, "up": pygame.K_UP, "down": pygame.K_DOWN},
}
DEFAULT_LEADERBOARD: List[Dict] = []

# ------------------- JSON HELPERS -------------------
def load_json(path: Path, default):
    if path.exists():
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return default


def save_json(path: Path, data):
    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print('Save failed:', e)

# ------------------- PARTICLES -------------------
@dataclass
class Particle:
    x: float
    y: float
    vx: float
    vy: float
    life: float
    size: float
    color: tuple

# ------------------- GAME -------------------
class CoinCollector:
    WIDTH, HEIGHT = 800, 600
    FPS = 60
    GAME_TIME = 30  # seconds per run

    def __init__(self):
        pygame.init()
        pygame.joystick.init()
        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT))
        pygame.display.set_caption(f"{APP_NAME}")
        self.clock = pygame.time.Clock()
        self.font_big = pygame.font.SysFont('arial', 48, bold=True)
        self.font_med = pygame.font.SysFont('arial', 24)
        self.font_small = pygame.font.SysFont('arial', 18)

        # Load settings / leaderboard
        self.settings = load_json(SETTINGS_FILE, DEFAULT_SETTINGS.copy())
        self.leaderboard = load_json(LEADERBOARD_FILE, DEFAULT_LEADERBOARD.copy())

        # Game state
        self.state = 'menu'  # menu, playing, gameover
        self.running = True
        self.particles: List[Particle] = []
        self.score = 0
        self.player_name = 'Player'
        self.time_left = self.GAME_TIME

        # player
        self.player = pygame.Rect(self.WIDTH//2 - 18, self.HEIGHT//2 - 18, 36, 36)
        self.speed = 320

        # coins
        self.coins = []  # list of dicts {rect, spawn_time}
        self.coin_radius = 12
        self.spawn_cooldown = 0.8
        self.spawn_timer = 0.0

        # hazards (optional): moving block
        self.hazards = []

        # joystick
        self.joystick = None
        self.detect_joystick()

        # input for name entry
        self.name_input = ''
        self.name_cursor_timer = 0.0

        # difficulty modifier
        self.difficulty = self.settings.get('difficulty','normal')
        if self.difficulty == 'easy':
            self.spawn_cooldown = 1.1
            self.GAME_TIME = 40
        elif self.difficulty == 'hard':
            self.spawn_cooldown = 0.6
            self.GAME_TIME = 25

    def detect_joystick(self):
        if pygame.joystick.get_count() > 0:
            js = pygame.joystick.Joystick(0)
            js.init()
            self.joystick = js
            print('Joystick detected:', js.get_name())

    # ---------- game flow ----------
    def reset_run(self):
        self.score = 0
        self.time_left = self.GAME_TIME
        self.coins.clear()
        self.hazards.clear()
        self.player.topleft = (self.WIDTH//2 - 18, self.HEIGHT//2 - 18)
        self.spawn_timer = 0

    def start_game(self):
        self.reset_run()
        self.state = 'playing'

    def end_game(self):
        self.state = 'gameover'
        # Save to leaderboard after name entry (handled in gameover flow)

    # ---------- core loop ----------
    def run(self):
        while self.running:
            dt = self.clock.tick(self.FPS) / 1000.0
            self.handle_events()
            if self.state == 'playing':
                self.update_game(dt)
            self.update_particles(dt)
            self.render()
        pygame.quit()
        sys.exit()

    # ---------- events ----------
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if self.state == 'menu':
                    if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                        self.start_game()
                elif self.state == 'playing':
                    if event.key == pygame.K_ESCAPE:
                        self.state = 'menu'
                elif self.state == 'gameover':
                    # typing name
                    if event.key == pygame.K_BACKSPACE:
                        self.name_input = self.name_input[:-1]
                    elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                        self.player_name = self.name_input.strip() or 'Player'
                        self.save_score_and_back_to_menu()
                    else:
                        # accept visible ascii only, limit length
                        ch = event.unicode
                        if ch and len(self.name_input) < 16 and (32 <= ord(ch) <= 126):
                            self.name_input += ch
            elif event.type == pygame.JOYBUTTONDOWN:
                if self.state == 'menu' and event.button == 0:
                    self.start_game()
                elif self.state == 'gameover' and event.button == 0:
                    self.player_name = self.name_input.strip() or 'Player'
                    self.save_score_and_back_to_menu()

    # ---------- update ----------
    def update_game(self, dt):
        # update timers
        self.time_left -= dt
        if self.time_left <= 0:
            self.time_left = 0
            self.end_game()
            return

        # spawn coins
        self.spawn_timer -= dt
        if self.spawn_timer <= 0:
            self.spawn_coin()
            self.spawn_timer = self.spawn_cooldown + random.uniform(-0.3, 0.3)

        # player movement
        keys = pygame.key.get_pressed()
        dx = dy = 0
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            dx -= 1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            dx += 1
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            dy -= 1
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            dy += 1

        # joystick axes
        if self.joystick:
            try:
                ax = self.joystick.get_axis(0)
                ay = self.joystick.get_axis(1)
                # deadzone
                if abs(ax) > 0.15:
                    dx += ax
                if abs(ay) > 0.15:
                    dy += ay
            except Exception:
                pass

        # normalize
        if dx != 0 or dy != 0:
            length = (dx*dx + dy*dy) ** 0.5
            dx /= length
            dy /= length
            self.player.x += int(dx * self.speed * dt)
            self.player.y += int(dy * self.speed * dt)

        # clamp
        self.player.clamp_ip(pygame.Rect(0,0,self.WIDTH,self.HEIGHT))

        # update coins
        for c in list(self.coins):
            # coins could have a lifetime or be moving; currently static
            rect = c['rect']
            if rect.colliderect(self.player):
                self.coins.remove(c)
                self.score += 1
                self.emit_particle(rect.centerx, rect.centery)

        # update hazards (not used heavily here)
        # optional future feature

    # ---------- coin logic ----------
    def spawn_coin(self):
        margin = 40
        x = random.randint(margin, self.WIDTH - margin)
        y = random.randint(margin, self.HEIGHT - margin)
        r = self.coin_radius
        rect = pygame.Rect(x-r, y-r, r*2, r*2)
        self.coins.append({'rect': rect, 'spawn': time.time()})

    # ---------- particles ----------
    def emit_particle(self, x, y, color=(255, 215, 0)):
        for _ in range(10):
            p = Particle(
                x=float(x),
                y=float(y),
                vx=random.uniform(-120, 120),
                vy=random.uniform(-220, -60),
                life=random.uniform(0.5, 0.9),
                size=random.uniform(2.0, 5.0),
                color=color
            )
            self.particles.append(p)

    def update_particles(self, dt):
        for p in list(self.particles):
            p.x += p.vx * dt
            p.y += p.vy * dt
            p.vy += 500 * dt
            p.life -= dt
            if p.life <= 0:
                try:
                    self.particles.remove(p)
                except ValueError:
                    pass

    # ---------- render ----------
    def render_particles(self):
        for p in self.particles:
            alpha = max(0, min(255, int(255 * (p.life / 1.0))))
            surf = pygame.Surface((int(p.size*2), int(p.size*2)), pygame.SRCALPHA)
            pygame.draw.circle(surf, (*p.color, alpha), (int(p.size), int(p.size)), int(p.size))
            self.screen.blit(surf, (int(p.x - p.size), int(p.y - p.size)))

    def render(self):
        # background
        self.screen.fill((18, 22, 34))

        if self.state == 'menu':
            self.draw_menu()
        elif self.state == 'playing':
            self.draw_game()
        elif self.state == 'gameover':
            self.draw_gameover()

        # particles on top
        self.render_particles()
        pygame.display.flip()

    def draw_menu(self):
        title = self.font_big.render('Coin Collector', True, (255, 220, 100))
        self.screen.blit(title, (self.WIDTH//2 - title.get_width()//2, 80))

        subtitle = self.font_med.render('Collect coins to get the highest score!', True, (200,200,200))
        self.screen.blit(subtitle, (self.WIDTH//2 - subtitle.get_width()//2, 170))

        info = self.font_med.render('Press ENTER to start — Use arrow keys or WASD to move', True, (180,180,180))
        self.screen.blit(info, (self.WIDTH//2 - info.get_width()//2, 240))

        # show top leaderboard
        lb_title = self.font_med.render('Top Scores', True, (220,220,220))
        self.screen.blit(lb_title, (50, 320))
        for i, e in enumerate(sorted(self.leaderboard, key=lambda x: x.get('score',0), reverse=True)[:5], start=1):
            text = self.font_small.render(f"{i}. {e.get('name','Player')} — {e.get('score',0)}", True, (200,200,200))
            self.screen.blit(text, (50, 320 + i*26))

    def draw_game(self):
        # HUD
        score_text = self.font_med.render(f"Score: {self.score}", True, (240,240,240))
        time_text = self.font_med.render(f"Time: {int(self.time_left)}", True, (240,240,240))
        self.screen.blit(score_text, (20, 20))
        self.screen.blit(time_text, (self.WIDTH - time_text.get_width() - 20, 20))

        # draw player
        pygame.draw.rect(self.screen, (80, 200, 220), self.player, border_radius=6)

        # draw coins
        for c in self.coins:
            rect = c['rect']
            pygame.draw.circle(self.screen, (255, 215, 0), rect.center, self.coin_radius)
            pygame.draw.circle(self.screen, (255, 255, 255), rect.center, self.coin_radius-6)

    def draw_gameover(self):
        # dim background
        overlay = pygame.Surface((self.WIDTH, self.HEIGHT), pygame.SRCALPHA)
        overlay.fill((0,0,0,180))
        self.screen.blit(overlay, (0,0))

        title = self.font_big.render('Game Over', True, (255, 200, 60))
        self.screen.blit(title, (self.WIDTH//2 - title.get_width()//2, 80))

        score_text = self.font_med.render(f'Your score: {self.score}', True, (240,240,240))
        self.screen.blit(score_text, (self.WIDTH//2 - score_text.get_width()//2, 180))

        prompt = self.font_med.render('Enter your name and press Enter to save:', True, (200,200,200))
        self.screen.blit(prompt, (self.WIDTH//2 - prompt.get_width()//2, 240))

        # name input box
        box_w = 380
        box_h = 44
        bx = self.WIDTH//2 - box_w//2
        by = 300
        pygame.draw.rect(self.screen, (40,40,50), (bx, by, box_w, box_h), border_radius=8)
        pygame.draw.rect(self.screen, (255,255,255), (bx, by, box_w, box_h), 2, border_radius=8)

        nm = self.name_input or 'Player'
        name_surf = self.font_med.render(nm, True, (230,230,230))
        self.screen.blit(name_surf, (bx + 12, by + (box_h - name_surf.get_height())//2))

        # blinking cursor
        self.name_cursor_timer += self.clock.get_time() / 1000.0
        if int(self.name_cursor_timer * 2) % 2 == 0:
            cur_x = bx + 12 + name_surf.get_width() + 2
            pygame.draw.rect(self.screen, (230,230,230), (cur_x, by + 10, 2, box_h - 20))

        hint = self.font_small.render('Press Enter to save score and return to menu', True, (180,180,180))
        self.screen.blit(hint, (self.WIDTH//2 - hint.get_width()//2, by + box_h + 18))

    # ---------- leaderboard ----------
    def save_score_and_back_to_menu(self):
        entry = {'name': self.player_name, 'score': int(self.score), 'time': int(time.time())}
        self.leaderboard.append(entry)
        # keep sorted, top 50
        self.leaderboard = sorted(self.leaderboard, key=lambda x: x.get('score',0), reverse=True)[:50]
        save_json(LEADERBOARD_FILE, self.leaderboard)
        # reset name input
        self.name_input = ''
        self.player_name = 'Player'
        # go back to menu
        self.state = 'menu'

# ------------------- RUN -------------------
if __name__ == '__main__':
    game = CoinCollector()
    game.run()

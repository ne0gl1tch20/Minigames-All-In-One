"""
Clean Your Room - Minigame

Features:
- Start Menu / Settings / Leaderboard (JSON saves)
- Click or drag items to the trash to score points
- Keyboard + Joystick support
- Particle effects when picking up items
- Difficulty & volume settings saved per-user

Requirements:
    pip install pygame

Run:
    python clean_your_room.py
"""
import pygame
import sys
import json
import os
import random
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict, Optional

# ------------------- CONFIG / SAVE PATH -------------------
USER_DIR = os.path.expandvars(r"%userprofile%")
MG_SAVE_DIR = Path(USER_DIR) / "Documents" / ".mgaio"
APP_NAME = "CleanYourRoom"
SAVE_FOLDER = MG_SAVE_DIR / "Saves" / APP_NAME
SAVE_FOLDER.mkdir(parents=True, exist_ok=True)

SETTINGS_FILE = SAVE_FOLDER / "settings.json"
LEADERBOARD_FILE = SAVE_FOLDER / "leaderboard.json"

DEFAULT_SETTINGS = {
    "volume": 80,
    "sound": True,
    "difficulty": "normal",  # easy, normal, hard
    "keymap": {"pickup": pygame.K_SPACE, "pause": pygame.K_ESCAPE},
    "joymap": {"pickup_button": 0}
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

# ------------------- ITEM -------------------
@dataclass
class ClutterItem:
    id: int
    type: str
    x: float
    y: float
    w: int
    h: int
    rot: float
    picked: bool = False
    score: int = 10

# ------------------- BASE GAME -------------------
class CleanRoomGame:
    WIDTH, HEIGHT = 900, 600
    FPS = 60
    TRASH_ZONE = pygame.Rect(WIDTH - 160, HEIGHT - 140, 140, 120)

    def __init__(self):
        pygame.init()
        pygame.joystick.init()
        pygame.mixer.init()
        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT))
        pygame.display.set_caption("Clean Your Room")
        self.clock = pygame.time.Clock()

        self.font_big = pygame.font.SysFont("segoe ui emoji", 48, bold=True)
        self.font_med = pygame.font.SysFont("segoe ui emoji", 24)
        self.font_small = pygame.font.SysFont("segoe ui emoji", 16)

        # load settings & leaderboard
        self.settings = load_json(SETTINGS_FILE, DEFAULT_SETTINGS.copy())
        self.leaderboard = load_json(LEADERBOARD_FILE, DEFAULT_LEADERBOARD.copy())

        # Joystick
        self.joystick = None
        self.detect_joystick()

        # Game state
        self.state = "menu"  # menu, settings, playing, gameover, leaderboard
        self.running = True
        self.particles: List[Particle] = []
        self.items: List[ClutterItem] = []
        self.next_item_id = 1
        self.score = 0
        self.timer = 60.0  # seconds per run
        self.spawn_timer = 0.0
        self.spawn_interval = 1.2  # base, modified by difficulty
        self.mouse_dragging: Optional[ClutterItem] = None
        self.mouse_offset = (0,0)
        self.best_score = 0
        self.player_name = "You"
        self.enter_name_mode = False
        self.name_buffer = ""
        self.load_resources()
        self.apply_difficulty()

    def detect_joystick(self):
        if pygame.joystick.get_count() > 0:
            js = pygame.joystick.Joystick(0)
            js.init()
            self.joystick = js
            print("Joystick detected:", js.get_name())

    def load_resources(self):
        # simple color-coded images for items (no external files)
        self.item_templates = {
            "trash": {"w": 44, "h": 44, "color": (180,180,180), "score": 5},
            "plate": {"w": 36, "h": 36, "color": (235,230,200), "score": 8},
            "clothes": {"w": 52, "h": 36, "color": (160,80,200), "score": 12},
            "toy": {"w": 40, "h": 40, "color": (255,150,60), "score": 10},
            "book": {"w": 46, "h": 30, "color": (80,140,200), "score": 9},
        }
        # sounds if provided next to script
        base_dir = os.path.dirname(__file__) if "__file__" in globals() else os.getcwd()
        try:
            self.snd_pick = pygame.mixer.Sound(os.path.join(base_dir, "pickup.wav")) if os.path.exists(os.path.join(base_dir, "pickup.wav")) else None
            self.snd_complete = pygame.mixer.Sound(os.path.join(base_dir, "complete.wav")) if os.path.exists(os.path.join(base_dir, "complete.wav")) else None
            vol = max(0.0, min(1.0, self.settings.get("volume",80)/100))
            if self.snd_pick: self.snd_pick.set_volume(vol)
            if self.snd_complete: self.snd_complete.set_volume(vol)
        except Exception:
            self.snd_pick = self.snd_complete = None

    def apply_difficulty(self):
        diff = self.settings.get("difficulty","normal")
        if diff == "easy":
            self.spawn_interval = 1.5
            self.timer = 75.0
        elif diff == "hard":
            self.spawn_interval = 0.9
            self.timer = 50.0
        else:
            self.spawn_interval = 1.2
            self.timer = 60.0
            
    def start_game(self):
        self.state = "playing"
        self.score = 0
        self.timer = 60.0  # or self.apply_difficulty() to reset time per difficulty
        self.items.clear()
        self.particles.clear()
        self.next_item_id = 1
        for _ in range(4):  # spawn a few starting items
            self.spawn_item()

    # ---------- item management ----------
    def spawn_item(self):
        typ = random.choice(list(self.item_templates.keys()))
        tpl = self.item_templates[typ]
        # avoid spawning inside trash zone
        x = random.randint(40, self.WIDTH - 220)
        y = random.randint(80, self.HEIGHT - 200)
        item = ClutterItem(
            id=self.next_item_id,
            type=typ,
            x=x,
            y=y,
            w=tpl["w"],
            h=tpl["h"],
            rot=random.uniform(-12,12),
            picked=False,
            score=tpl["score"]
        )
        self.items.append(item)
        self.next_item_id += 1

    def item_rect(self, item: ClutterItem) -> pygame.Rect:
        return pygame.Rect(int(item.x - item.w//2), int(item.y - item.h//2), item.w, item.h)

    # ---------- particles ----------
    def emit_particles(self, x, y, amount=12, color=(255,200,60)):
        for _ in range(amount):
            p = Particle(
                x=x + random.uniform(-6,6),
                y=y + random.uniform(-6,6),
                vx=random.uniform(-120,120),
                vy=random.uniform(-200,-40),
                life=0.6 + random.random()*0.8,
                size=random.uniform(2,5),
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
                self.particles.remove(p)

    def draw_particles(self):
        for p in self.particles:
            alpha = max(0, min(255, int(255 * (p.life / 1.4))))
            surf = pygame.Surface((int(p.size*2), int(p.size*2)), pygame.SRCALPHA)
            pygame.draw.circle(surf, (*p.color, alpha), (int(p.size), int(p.size)), int(p.size))
            self.screen.blit(surf, (int(p.x - p.size), int(p.y - p.size)))

    # ---------- main loop ----------
    def run(self):
        while self.running:
            dt = self.clock.tick(self.FPS) / 1000.0
            self.handle_events()
            if self.state == "playing":
                self.update(dt)
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
                if self.state == "menu":
                    if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                        self.start_game()
                    elif event.key == pygame.K_s:
                        self.state = "settings"
                    elif event.key == pygame.K_l:
                        self.state = "leaderboard"
                elif self.state == "settings":
                    if event.key == pygame.K_ESCAPE:
                        self.state = "menu"
                    elif event.key == pygame.K_UP:
                        self.settings["volume"] = min(100, self.settings.get("volume",80) + 5)
                        save_json(SETTINGS_FILE, self.settings)
                    elif event.key == pygame.K_DOWN:
                        self.settings["volume"] = max(0, self.settings.get("volume",80) - 5)
                        save_json(SETTINGS_FILE, self.settings)
                    elif event.key == pygame.K_LEFT:
                        self.cycle_difficulty(-1)
                    elif event.key == pygame.K_RIGHT:
                        self.cycle_difficulty(1)
                elif self.state == "playing":
                    # quick pickup key - picks nearest item to mouse
                    if event.key == self.settings["keymap"].get("pickup", pygame.K_SPACE):
                        self.quick_pick()
                    elif event.key == pygame.K_p:
                        self.state = "menu"
                elif self.state == "gameover":
                    if self.enter_name_mode:
                        if event.key == pygame.K_RETURN:
                            self.commit_name_and_save()
                        elif event.key == pygame.K_BACKSPACE:
                            self.name_buffer = self.name_buffer[:-1]
                        else:
                            # limit name length
                            if len(self.name_buffer) < 12 and event.unicode.isprintable():
                                self.name_buffer += event.unicode
                    else:
                        if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                            self.state = "menu"
                elif self.state == "leaderboard":
                    if event.key == pygame.K_ESCAPE:
                        self.state = "menu"

            elif event.type == pygame.MOUSEBUTTONDOWN:
                mx,my = event.pos
                if self.state == "menu":
                    pass
                elif self.state == "playing":
                    # try to pick item under mouse and start dragging
                    for it in reversed(self.items):
                        if self.item_rect(it).collidepoint(mx,my):
                            self.mouse_dragging = it
                            self.mouse_offset = (it.x - mx, it.y - my)
                            break
                elif self.state == "settings":
                    pass

            elif event.type == pygame.MOUSEBUTTONUP:
                if self.state == "playing":
                    if self.mouse_dragging:
                        # if dropped inside trash zone -> score
                        it = self.mouse_dragging
                        rect = self.item_rect(it)
                        if rect.colliderect(self.TRASH_ZONE):
                            self.pick_item(it)
                        # stop dragging in any case
                        self.mouse_dragging = None

            elif event.type == pygame.MOUSEMOTION:
                if self.state == "playing" and self.mouse_dragging:
                    mx,my = event.pos
                    it = self.mouse_dragging
                    it.x = mx + self.mouse_offset[0]
                    it.y = my + self.mouse_offset[1]

            elif event.type == pygame.JOYBUTTONDOWN:
                if self.joystick:
                    btn = event.button
                    if self.state == "menu" and btn == 0:
                        self.start_game()
                    elif self.state == "playing" and btn == self.settings.get("joymap",{}).get("pickup_button",0):
                        self.quick_pick()

    # ---------- helpers ----------
    def cycle_difficulty(self, dir=1):
        order = ["easy","normal","hard"]
        cur = self.settings.get("difficulty","normal")
        idx = order.index(cur) if cur in order else 1
        idx = (idx + dir) % len(order)
        self.settings["difficulty"] = order[idx]
        save_json(SETTINGS_FILE, self.settings)
        self.apply_difficulty()

    def quick_pick(self):
        # pick nearest item to mouse (simple fallback if player uses key)
        mx,my = pygame.mouse.get_pos()
        nearest = None
        bestd = 1e9
        for it in self.items:
            if it.picked: continue
            dx = it.x - mx
            dy = it.y - my
            d = dx*dx + dy*dy
            if d < bestd:
                nearest = it
                bestd = d
        if nearest and bestd < (200**2):
            # simulate moving it to trash and scoring
            self.pick_item(nearest)

    def pick_item(self, item: ClutterItem):
        if item not in self.items:
            return
        # sound
        if self.snd_pick and self.settings.get("sound", True):
            try:
                self.snd_pick.play()
            except Exception:
                pass
        # score + particles
        self.score += item.score
        self.emit_particles(item.x, item.y, amount=14, color=(150,230,150))
        # remove item
        try:
            self.items.remove(item)
        except ValueError:
            pass

    def update(self, dt):
        # spawn items over time
        self.spawn_timer += dt
        if self.spawn_timer >= max(0.2, self.spawn_interval):
            self.spawn_timer = 0.0
            # spawn a few based on difficulty and current clutter
            cur_count = len(self.items)
            if cur_count < 12:
                self.spawn_item()
        # countdown
        self.timer -= dt
        if self.timer <= 0:
            self.timer = 0
            self.on_gameover()

    def on_gameover(self):
        # commit best score
        self.best_score = max(self.best_score, self.score)
        # ask for name input
        self.enter_name_mode = True
        self.name_buffer = ""
        self.state = "gameover"

    def save_score(self, name: str):
        entry = {"name": name or "You", "score": int(self.score)}
        self.leaderboard.append(entry)
        self.leaderboard = sorted(self.leaderboard, key=lambda e: e.get("score",0), reverse=True)[:20]
        save_json(LEADERBOARD_FILE, self.leaderboard)

    def commit_name_and_save(self):
        if self.name_buffer.strip() == "":
            name = "You"
        else:
            name = self.name_buffer.strip()
        self.save_score(name)
        # optionally play complete sound
        if self.snd_complete and self.settings.get("sound", True):
            try:
                self.snd_complete.play()
            except Exception:
                pass
        self.enter_name_mode = False
        self.state = "leaderboard"

    # ---------- rendering ----------
    def render(self):
        self.screen.fill((28,28,34))
        if self.state == "menu":
            self.draw_menu()
        elif self.state == "settings":
            self.draw_settings()
        elif self.state == "playing":
            self.draw_playfield()
        elif self.state == "gameover":
            self.draw_gameover()
        elif self.state == "leaderboard":
            self.draw_leaderboard()

        # trash zone outline (always visible)
        pygame.draw.rect(self.screen, (40,40,45), self.TRASH_ZONE)
        trash_txt = self.font_small.render("TRASH - Drop Here", True, (210,210,210))
        self.screen.blit(trash_txt, (self.TRASH_ZONE.x + 8, self.TRASH_ZONE.y + 8))

        self.draw_particles()
        pygame.display.flip()

    def draw_menu(self):
        title = self.font_big.render("Clean Your Room", True, (255, 200, 80))
        self.screen.blit(title, (self.WIDTH//2 - title.get_width()//2, 70))
        sub = self.font_med.render("Press Enter to Start  |  S = Settings  |  L = Leaderboard", True, (200,200,200))
        self.screen.blit(sub, (self.WIDTH//2 - sub.get_width()//2, 220))
        hint = self.font_small.render("Click & drag items to the trash, or press SPACE to pick nearest item.", True, (160,160,160))
        self.screen.blit(hint, (self.WIDTH//2 - hint.get_width()//2, 270))

    def draw_settings(self):
        title = self.font_big.render("Settings", True, (255, 200, 80))
        self.screen.blit(title, (40, 40))
        vol = self.font_med.render(f"Volume: {self.settings.get('volume',80)} (Up/Down)", True, (200,200,200))
        self.screen.blit(vol, (40, 130))
        diff = self.font_med.render(f"Difficulty: {self.settings.get('difficulty','normal')} (Left/Right)", True, (200,200,200))
        self.screen.blit(diff, (40, 180))
        esc = self.font_small.render("Esc to return to menu", True, (150,150,150))
        self.screen.blit(esc, (40, 240))

    def draw_playfield(self):
        # background / floor
        pygame.draw.rect(self.screen, (45,45,60), (40, 40, self.WIDTH - 220, self.HEIGHT - 200))
        # scatter carpet texture (dots)
        for x in range(48, self.WIDTH - 168, 120):
            for y in range(56, self.HEIGHT - 170, 120):
                pygame.draw.circle(self.screen, (30,30,40), (x,y), 2)

        # draw items
        for it in self.items:
            rect = self.item_rect(it)
            tpl = self.item_templates[it.type]
            # draw rotated rectangle as item
            surf = pygame.Surface((it.w, it.h), pygame.SRCALPHA)
            pygame.draw.rect(surf, tpl["color"], (0,0,it.w,it.h), border_radius=6)
            # small icon (type letter)
            label = self.font_small.render(it.type[0].upper(), True, (20,20,20))
            surf.blit(label, (4,4))
            rotated = pygame.transform.rotate(surf, it.rot)
            rrect = rotated.get_rect(center=(it.x, it.y))
            self.screen.blit(rotated, rrect.topleft)
        # draw dragging item on top (if any)
        if self.mouse_dragging:
            it = self.mouse_dragging
            rect = self.item_rect(it)
            pygame.draw.rect(self.screen, (255,255,255,50), rect, 2)

        # HUD
        score_txt = self.font_med.render(f"Score: {self.score}", True, (240,240,240))
        self.screen.blit(score_txt, (40, 20))
        timer_txt = self.font_med.render(f"Time: {int(self.timer)}s", True, (240,240,240))
        self.screen.blit(timer_txt, (self.WIDTH//2 - 40, 20))
        best_txt = self.font_small.render(f"Best: {self.best_score}", True, (200,200,200))
        self.screen.blit(best_txt, (40, self.HEIGHT - 110))

    def draw_gameover(self):
        box = pygame.Rect(self.WIDTH//2 - 300, self.HEIGHT//2 - 160, 600, 320)
        pygame.draw.rect(self.screen, (24,24,28), box)
        pygame.draw.rect(self.screen, (70,70,90), box, 3)
        title = self.font_big.render("Time's up!", True, (230,120,100))
        self.screen.blit(title, (box.x + box.width//2 - title.get_width()//2, box.y + 20))
        sc = self.font_med.render(f"Score: {self.score}", True, (230,230,230))
        self.screen.blit(sc, (box.x + box.width//2 - sc.get_width()//2, box.y + 120))

        if self.enter_name_mode:
            prompt = self.font_med.render("Enter name and press Enter:", True, (200,200,200))
            self.screen.blit(prompt, (box.x + 40, box.y + 170))
            name_surface = self.font_med.render(self.name_buffer + "_", True, (255,255,255))
            self.screen.blit(name_surface, (box.x + 40, box.y + 210))
        else:
            hint = self.font_small.render("Press Enter to view leaderboard", True, (180,180,180))
            self.screen.blit(hint, (box.x + box.width//2 - hint.get_width()//2, box.y + 240))

    def draw_leaderboard(self):
        title = self.font_big.render("Leaderboard", True, (255,200,80))
        self.screen.blit(title, (self.WIDTH//2 - title.get_width()//2, 40))
        if not self.leaderboard:
            none = self.font_med.render("No scores yet. Play to set a high score!", True, (180,180,180))
            self.screen.blit(none, (self.WIDTH//2 - none.get_width()//2, 200))
            return
        for i, entry in enumerate(self.leaderboard[:10]):
            txt = self.font_med.render(f"{i+1}. {entry.get('name','---')} - {entry.get('score',0)}", True, (220,220,220))
            self.screen.blit(txt, (self.WIDTH//2 - 120, 120 + i*36))

# ------------------- RUN -------------------
if __name__ == "__main__":
    game = CleanRoomGame()
    # small convenience: spawn a couple items to start
    for _ in range(4):
        game.spawn_item()
    game.run()

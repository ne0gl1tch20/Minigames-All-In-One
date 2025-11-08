"""
LALALALA — Upgraded edition (librosa + background audio support)
Features added in this fork:
- Optional use of librosa to analyze a background audio file for beat times
- "Load Background File" button in Settings to pick a music file
- Spawns notes in time with detected beats (falls back to procedural spawn if no file loaded)
- Saves chosen background file path into settings

Requirements:
pip install pygame librosa soundfile numpy

Run:
python lalalala_upgraded_librosa.py
"""

import pygame
import random
import sys
import json
import math
import os
from pathlib import Path
from dataclasses import dataclass
from typing import List, Optional

# try to import librosa (optional)
try:
    import librosa
    LIBROSA_AVAILABLE = True
except Exception:
    librosa = None
    LIBROSA_AVAILABLE = False

# small helper to show an OS file picker using tkinter
def ask_open_filename(title="Open audio file", filetypes=(("Audio files", "*.mp3;*.wav;*.ogg;*.flac"), ("All files","*.*"))):
    try:
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk()
        root.withdraw()
        path = filedialog.askopenfilename(title=title, filetypes=filetypes)
        root.destroy()
        return path
    except Exception as e:
        print("tkinter file dialog unavailable:", e)
        return None

# ------------------- CONFIG / SAVE PATH -------------------
USER_DIR = os.path.expandvars(r"%userprofile%") if os.name == 'nt' else os.path.expanduser('~')
MGAIO_DIR = Path(USER_DIR) / "Documents" / ".mgaio"
APP_NAME = "Lalallaa"
SAVE_FOLDER = MGAIO_DIR / "Saves" / APP_NAME
SAVE_FOLDER.mkdir(parents=True, exist_ok=True)

SETTINGS_FILE = SAVE_FOLDER / "settings.json"
LEADERBOARD_FILE = SAVE_FOLDER / "leaderboard.json"

# ensure settings exist
if not SETTINGS_FILE.exists():
    default_settings = {
        "keymap": {},
        "joymap": {},
        "sound": True,
        "difficulty": "normal",
        "hit_window": 56,
        "bg_file": None  # path to user-selected background audio
    }
    SETTINGS_FILE.write_text(json.dumps(default_settings, indent=2))

if not LEADERBOARD_FILE.exists():
    LEADERBOARD_FILE.write_text(json.dumps([], indent=2))

# constants
WIDTH, HEIGHT = 1000, 700
FPS = 60
LANE_COUNT = 3
NOTE_BASE_WIDTH = 56
NOTE_BASE_HEIGHT = 28
HIT_ZONE_Y = HEIGHT - 150
DEFAULT_HIT_WINDOW = 56

# default keymap (pygame constants)
DEFAULT_KEYMAP = {
    "lane_0": pygame.K_a,
    "lane_1": pygame.K_s,
    "lane_2": pygame.K_d,
    "start": pygame.K_RETURN,
    "back": pygame.K_ESCAPE,
}

DEFAULT_SETTINGS = {
    "keymap": DEFAULT_KEYMAP,
    "joymap": {},
    "sound": True,
    "difficulty": "normal",
    "hit_window": DEFAULT_HIT_WINDOW,
    "bg_file": None,
}

WHITE = (245, 245, 245)
BLACK = (12, 12, 12)
GRAY = (54, 57, 63)
ACCENT = (255, 200, 60)
GOOD_GREEN = (88, 214, 141)
BAD_RED = (232, 76, 61)
BLUE = (100, 149, 237)

# ------------------- helpers -------------------

def load_json(path: Path, default):
    try:
        if path.exists():
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
        print('Failed saving', path, '->', e)

# ------------------- dataclasses -------------------
from dataclasses import dataclass

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

# ------------------- MAIN CLASS -------------------
class Lalalala:
    def __init__(self):
        pygame.init()
        pygame.mixer.init()
        pygame.joystick.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("LALALALA — Upgraded (librosa)")
        self.clock = pygame.time.Clock()
        self.font_big = pygame.font.SysFont("arial", 56, bold=True)
        self.font_med = pygame.font.SysFont("arial", 28)
        self.font_sm = pygame.font.SysFont("arial", 16)
        self.running = True

        # load settings
        self.settings = load_json(SETTINGS_FILE, DEFAULT_SETTINGS.copy())
        for k, v in DEFAULT_SETTINGS.items():
            self.settings.setdefault(k, v)

        # leaderboard
        self.leaderboard = load_json(LEADERBOARD_FILE, [])

        # joystick
        self.joystick = None
        self.detect_joystick()

        # game state
        self.state = 'menu'
        self.notes: List[Note] = []
        self.particles: List[Particle] = []
        self.spawn_timer = 0.0
        self.score = 0
        self.combo = 0
        self.lives = 5
        self.hit_feedback = None
        self.note_speed = 240.0
        self.spawn_interval = 0.75
        self.time_since_start = 0.0
        # ensure player_name exists to avoid AttributeError when adding to leaderboard
        self.player_name = self.settings.get('player_name', 'Player')

        # beat sync
        self.bg_file: Optional[str] = self.settings.get('bg_file')
        self.beat_times: List[float] = []
        self.next_beat_idx = 0
        self.music_playing = False
        self.music_start_ticks = 0.0

        # remap
        self.remap_target = None
        self.remap_callback = None

        self.apply_difficulty()
        self._create_placeholder_sounds()

        # if a bg file existed in settings, try to load and analyze (best-effort)
        if self.bg_file:
            try:
                self.load_background_file(self.bg_file)
            except Exception as e:
                print('Failed to load bg file from settings:', e)

    def detect_joystick(self):
        if pygame.joystick.get_count() > 0:
            try:
                js = pygame.joystick.Joystick(0)
                js.init()
                self.joystick = js
                print('Joystick detected:', js.get_name())
            except Exception as e:
                print('Joystick init failed:', e)
                self.joystick = None

    def _create_placeholder_sounds(self):
        # basic pygame beep sounds (kept simple)
        try:
            freq = 22050
            self.sounds = {}
            for name, hz, dur in (("hit", 880, 0.06), ("miss", 220, 0.09), ("start", 440, 0.12)):
                arr = bytearray()
                n = int(freq * dur)
                max_amp = 127
                for i in range(n):
                    t = i / freq
                    v = int(max_amp * math.sin(2 * math.pi * hz * t) * (1.0 - t / dur))
                    arr.append(v + 128)
                self.sounds[name] = pygame.mixer.Sound(buffer=bytes(arr))
        except Exception:
            self.sounds = {}

    def play_sound(self, name):
        if not self.settings.get('sound', True):
            return
        s = self.sounds.get(name)
        if s:
            try:
                s.play()
            except Exception:
                pass

    def apply_difficulty(self):
        diff = self.settings.get('difficulty', 'normal')
        if diff == 'easy':
            self.note_speed = 180.0
            self.spawn_interval = 0.9
            self.settings['hit_window'] = DEFAULT_HIT_WINDOW + 12
        elif diff == 'hard':
            self.note_speed = 300.0
            self.spawn_interval = 0.6
            self.settings['hit_window'] = max(36, DEFAULT_HIT_WINDOW - 14)
        else:
            self.note_speed = 240.0
            self.spawn_interval = 0.75
            self.settings['hit_window'] = DEFAULT_HIT_WINDOW

    # ------------------- Background audio & librosa analysis -------------------
    def choose_background_file(self):
        path = ask_open_filename('Choose background audio')
        if not path:
            return
        self.settings['bg_file'] = path
        save_json(SETTINGS_FILE, self.settings)
        try:
            self.load_background_file(path)
            print('Background file loaded and analyzed.')
        except Exception as e:
            print('Failed to analyze background file:', e)

    def load_background_file(self, path: str):
        """Load audio into pygame mixer and (if librosa available) analyze beat times.
        This is blocking — analysis may take a couple seconds for long files."""
        if not os.path.exists(path):
            raise FileNotFoundError(path)
        # load audio for playback
        try:
            pygame.mixer.music.load(path)
            self.bg_file = path
        except Exception as e:
            print('pygame failed to load audio for playback:', e)
            # continue — we may still analyze with librosa
            self.bg_file = path
        # analyze beats with librosa if available
        self.beat_times = []
        self.next_beat_idx = 0
        if LIBROSA_AVAILABLE:
            try:
                print('Analyzing audio with librosa (this may take a moment)...')
                y, sr = librosa.load(path, sr=None)
                # use beat tracker to get frames
                tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
                beat_times = librosa.frames_to_time(beat_frames, sr=sr).tolist()
                # fallback: if no beats, try onset detection
                if not beat_times:
                    onset_frames = librosa.onset.onset_detect(y=y, sr=sr)
                    beat_times = librosa.frames_to_time(onset_frames, sr=sr).tolist()
                self.beat_times = beat_times
                print(f'Detected {len(self.beat_times)} beats (tempo ~ {tempo:.1f})')
            except Exception as e:
                print('librosa analysis failed:', e)
                self.beat_times = []
        else:
            print('librosa not available — background will play but no beat sync will occur')

    # ------------------- spawn / update logic -------------------
    def spawn_note(self, scheduled_time: Optional[float] = None):
        lane = random.randrange(0, LANE_COUNT)
        n = Note(lane=lane, y=-NOTE_BASE_HEIGHT - 8, speed=self.note_speed, angle=random.random() * 360, scale=1.0, created_time=self.time_since_start)
        # if scheduled_time provided, we could adjust created_time for pulsing effect
        if scheduled_time:
            n.created_time = scheduled_time
        self.notes.append(n)

    def update_game(self, dt):
        self.time_since_start += dt
        # beat-driven spawning
        if self.bg_file and self.beat_times:
            # compute current music time
            if self.music_playing:
                current_music_time = (pygame.time.get_ticks() - self.music_start_ticks) / 1000.0
            else:
                current_music_time = self.time_since_start
            # spawn all beats that are due
            while self.next_beat_idx < len(self.beat_times) and current_music_time >= self.beat_times[self.next_beat_idx]:
                bt = self.beat_times[self.next_beat_idx]
                self.spawn_note(scheduled_time=bt)
                self.next_beat_idx += 1
        else:
            # fallback procedural spawning
            self.spawn_timer += dt
            if self.spawn_timer >= self.spawn_interval:
                self.spawn_timer -= self.spawn_interval
                self.spawn_note()

        # update notes
        for note in self.notes:
            note.y += note.speed * dt
            note.angle += 90 * dt
            note.scale = 0.9 + 0.12 * math.sin((self.time_since_start - note.created_time) * 6.0)

        # notes that pass bottom -> miss
        to_remove = []
        for note in self.notes:
            if note.y > HEIGHT + 40 and not note.hit:
                to_remove.append(note)
                self.combo = 0
                self.lives -= 1
                self.hit_feedback = ("Miss!", 1.0, BAD_RED)
                self.play_sound('miss')
                lane_x = note.lane * (WIDTH / LANE_COUNT) + (WIDTH / LANE_COUNT) / 2
                self._emit_particles(lane_x, HIT_ZONE_Y, 12, BAD_RED)
        for n in to_remove:
            if n in self.notes:
                self.notes.remove(n)

        # particles
        for p in list(self.particles):
            p.x += p.vx * dt
            p.y += p.vy * dt
            p.vy += 220 * dt
            p.life -= dt
            if p.life <= 0:
                self.particles.remove(p)

        # feedback
        if self.hit_feedback:
            text, timer, color = self.hit_feedback
            timer -= dt
            if timer <= 0:
                self.hit_feedback = None
            else:
                self.hit_feedback = (text, timer, color)

        if self.lives <= 0:
            self.state = 'gameover'
            self.add_to_leaderboard(self.player_name, self.score)
            # stop music
            try:
                pygame.mixer.music.stop()
            except Exception:
                pass
            self.music_playing = False

    # ------------------- input / hit logic -------------------
    def handle_keypress_playing(self, key):
        keymap = self.settings.get('keymap', {})
        if key == keymap.get('start') or key == pygame.K_RETURN:
            return
        if key == keymap.get('back') or key == pygame.K_ESCAPE:
            self.state = 'menu'
            return
        for lane_idx in range(LANE_COUNT):
            map_key = keymap.get(f'lane_{lane_idx}')
            if map_key is not None and key == map_key:
                self._try_hit_lane(lane_idx)
                return
        self.hit_feedback = ('No note!', 0.6, GRAY)

    def _try_hit_lane(self, lane_idx):
        candidates = [n for n in self.notes if n.lane == lane_idx and not n.hit]
        if not candidates:
            self.combo = 0
            self.hit_feedback = ('No note!', 0.6, GRAY)
            return
        best = min(candidates, key=lambda n: abs(n.y - HIT_ZONE_Y))
        distance = abs(best.y - HIT_ZONE_Y)
        hit_window = self.settings.get('hit_window', DEFAULT_HIT_WINDOW)
        if distance <= hit_window:
            accuracy = max(0.0, 1.0 - (distance / hit_window))
            points = int(120 * accuracy) + 10 * (self.combo // 5)
            self.score += points
            best.hit = True
            if best in self.notes:
                self.notes.remove(best)
            self.combo += 1
            self.hit_feedback = (f'+{points}', 0.9, GOOD_GREEN)
            self.play_sound('hit')
            lane_x = lane_idx * (WIDTH / LANE_COUNT) + (WIDTH / LANE_COUNT) / 2
            self._emit_particles(lane_x, HIT_ZONE_Y, 18 + int(6 * accuracy), GOOD_GREEN)
            self.spawn_interval = max(0.25, self.spawn_interval - 0.006)
        else:
            self.combo = 0
            self.lives -= 1
            self.hit_feedback = ('Miss!', 0.9, BAD_RED)
            self.play_sound('miss')
            if best in self.notes:
                self.notes.remove(best)
            lane_x = lane_idx * (WIDTH / LANE_COUNT) + (WIDTH / LANE_COUNT) / 2
            self._emit_particles(lane_x, HIT_ZONE_Y, 8, BAD_RED)

    # ------------------- particles -------------------
    def _emit_particles(self, x, y, count, color):
        for i in range(count):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(80, 400)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed * -1
            p = Particle(x=x + random.uniform(-8, 8), y=y + random.uniform(-6, 6), vx=vx, vy=vy, life=random.uniform(0.5, 1.1), size=random.uniform(2, 6))
            setattr(p, 'color', color)
            self.particles.append(p)

    # ------------------- UI drawing -------------------
    def _draw_button(self, rect, text, active=True, small=False):
        color = ACCENT if active else GRAY
        pygame.draw.rect(self.screen, color, rect, border_radius=10)
        label = self.font_sm if small else self.font_med
        surf = label.render(text, True, BLACK if active else WHITE)
        self.screen.blit(surf, (rect.centerx - surf.get_width() / 2, rect.centery - surf.get_height() / 2))

    def draw_menu(self):
        title = self.font_big.render('LALALALA', True, ACCENT)
        sub = self.font_med.render('Upgraded — Beat sync with background (optional)', True, WHITE)
        self.screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 60))
        self.screen.blit(sub, (WIDTH // 2 - sub.get_width() // 2, 140))

        btn_w, btn_h = 340, 56
        start_rect = pygame.Rect(WIDTH // 2 - btn_w // 2, 220, btn_w, btn_h)
        settings_rect = pygame.Rect(WIDTH // 2 - btn_w // 2, 300, btn_w, btn_h)
        leader_rect = pygame.Rect(WIDTH // 2 - btn_w // 2, 380, btn_w, btn_h)
        quit_rect = pygame.Rect(WIDTH // 2 - btn_w // 2, 460, btn_w, btn_h)

        self._draw_button(start_rect, 'Start Play (Enter)')
        self._draw_button(settings_rect, 'Settings')
        self._draw_button(leader_rect, 'Leaderboard')
        self._draw_button(quit_rect, 'Quit')

        self.menu_buttons = {'start': start_rect, 'settings': settings_rect, 'leader': leader_rect, 'quit': quit_rect}

        footer = self.font_sm.render(f'Save folder: {SAVE_FOLDER}', True, GRAY)
        self.screen.blit(footer, (12, HEIGHT - 28))

    def draw_settings(self):
        title = self.font_big.render('Settings', True, ACCENT)
        self.screen.blit(title, (48, 36))

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

        right_x = WIDTH // 2 + 40
        btn_w, btn_h = 220, 40
        sound_btn = pygame.Rect(right_x, 120, btn_w, btn_h)
        diff_btn = pygame.Rect(right_x, 168, btn_w, btn_h)
        hit_dec = pygame.Rect(right_x, 216, 48, btn_h)
        hit_inc = pygame.Rect(right_x + 70, 216, 48, btn_h)
        hit_val = pygame.Rect(right_x + 130, 216, 100, btn_h)

        self._draw_button(sound_btn, 'Toggle Sound')
        self._draw_button(diff_btn, 'Cycle Difficulty')
        self._draw_button(hit_dec, '-')
        self._draw_button(hit_inc, '+')
        self._draw_button(hit_val, str(self.settings.get('hit_window', DEFAULT_HIT_WINDOW)), active=False)

        self.settings_buttons = {'sound': sound_btn, 'diff': diff_btn, 'hit_dec': hit_dec, 'hit_inc': hit_inc, 'hit_val': hit_val}

        # load background audio button
        load_bg_rect = pygame.Rect(right_x, 272, btn_w, btn_h)
        self._draw_button(load_bg_rect, 'Load Background File')
        self.settings_buttons['load_bg'] = load_bg_rect
        bg_label = self.font_sm.render(f"Loaded: {os.path.basename(self.settings.get('bg_file')) if self.settings.get('bg_file') else 'None'}", True, WHITE)
        self.screen.blit(bg_label, (right_x, 272 + btn_h + 8))

        # key remap
        section_y = 360
        self.screen.blit(self.font_med.render('Key Remapping:', True, WHITE), (48, section_y))
        km_x = 48
        km_y = section_y + 40
        row_h = 44
        keymap = self.settings.get('keymap', {})
        if not hasattr(self, 'remap_key_buttons'):
            self.remap_key_buttons = {}
        self.remap_key_buttons.clear()
        for i in range(LANE_COUNT):
            label = f'Lane {i+1}'
            labelsurf = self.font_sm.render(label, True, WHITE)
            self.screen.blit(labelsurf, (km_x, km_y + i * row_h))
            cur = keymap.get(f'lane_{i}')
            curname = pygame.key.name(cur) if isinstance(cur, int) else 'None'
            btn = pygame.Rect(km_x + 160, km_y + i * row_h, 240, 34)
            self._draw_button(btn, f'Key: {curname}', active=True, small=True)
            self.remap_key_buttons[f'lane_{i}'] = btn

        # joystick mapping
        jm_y = km_y + LANE_COUNT * row_h + 20
        self.screen.blit(self.font_med.render('Joystick Remapping (if connected):', True, WHITE), (48, jm_y))
        jm_y += 40
        joymap = self.settings.get('joymap', {})
        if not hasattr(self, 'remap_joy_buttons'):
            self.remap_joy_buttons = {}
        self.remap_joy_buttons.clear()
        for i in range(LANE_COUNT):
            lbl = f'Lane {i+1}'
            self.screen.blit(self.font_sm.render(lbl, True, WHITE), (48, jm_y + i * row_h))
            mapping = joymap.get(f'lane_{i}', {})
            if mapping.get('type') == 'button':
                desc = f"Button {mapping.get('id')}"
            elif mapping.get('type') == 'axis':
                desc = f"Axis {mapping.get('id')} dir {mapping.get('dir')}"
            else:
                desc = 'Unset'
            btn = pygame.Rect(48 + 160, jm_y + i * row_h, 260, 34)
            self._draw_button(btn, f'{desc}', active=True, small=True)
            self.remap_joy_buttons[f'lane_{i}'] = btn

        back_rect = pygame.Rect(WIDTH - 220, HEIGHT - 88, 180, 48)
        self._draw_button(back_rect, 'Back to Menu')
        self.settings_buttons['back'] = back_rect

    def draw_leaderboard(self):
        title = self.font_big.render('Leaderboard', True, ACCENT)
        self.screen.blit(title, (48, 36))
        y = 120
        for idx, entry in enumerate(self.leaderboard):
            name = entry.get('name', 'Player')
            score = entry.get('score', 0)
            line = self.font_med.render(f"{idx+1}. {name} — {score}", True, WHITE)
            self.screen.blit(line, (68, y + idx * 44))
        back_rect = pygame.Rect(WIDTH - 220, HEIGHT - 88, 180, 48)
        self._draw_button(back_rect, 'Back')
        self.leader_buttons = {'back': back_rect}

    def draw_game_ui(self):
        lane_w = WIDTH / LANE_COUNT
        for i in range(LANE_COUNT + 1):
            x = int(i * lane_w)
            pygame.draw.line(self.screen, GRAY, (x, 0), (x, HEIGHT), 2)

        zone_rect = pygame.Rect(0, HIT_ZONE_Y - self.settings.get('hit_window', DEFAULT_HIT_WINDOW), WIDTH, self.settings.get('hit_window', DEFAULT_HIT_WINDOW) * 2)
        s = pygame.Surface((zone_rect.w, zone_rect.h), pygame.SRCALPHA)
        s.fill((255, 255, 255, 12))
        self.screen.blit(s, (zone_rect.x, zone_rect.y))

        for i in range(LANE_COUNT):
            txt = self.font_sm.render(f"{pygame.key.name(self.settings.get('keymap', {}).get(f'lane_{i}', pygame.K_a))}", True, WHITE)
            x = int(i * lane_w + lane_w / 2 - txt.get_width() / 2)
            y = HIT_ZONE_Y + 14
            self.screen.blit(txt, (x, y))

        for note in self.notes:
            lane_cx = int(note.lane * lane_w + lane_w / 2)
            w = int(NOTE_BASE_WIDTH * note.scale)
            h = int(NOTE_BASE_HEIGHT * note.scale)
            rect = pygame.Rect(lane_cx - w // 2, int(note.y) - h // 2, w, h)
            surf = pygame.Surface((w, h), pygame.SRCALPHA)
            pygame.draw.ellipse(surf, BLUE, (0, 0, w, h))
            inner = pygame.Surface((w, h), pygame.SRCALPHA)
            pygame.draw.ellipse(inner, (255, 255, 255, 40), (w*0.14, h*0.14, w*0.72, h*0.72))
            surf.blit(inner, (0, 0))
            rotated = pygame.transform.rotate(surf, note.angle)
            rrect = rotated.get_rect(center=rect.center)
            self.screen.blit(rotated, rrect.topleft)
            lbl = self.font_sm.render('la', True, BLACK)
            self.screen.blit(lbl, (rect.centerx - lbl.get_width() / 2, rect.centery - lbl.get_height() / 2))

        for p in self.particles:
            alpha = max(0, min(255, int(255 * (p.life / 1.1))))
            col = getattr(p, 'color', ACCENT)
            surf = pygame.Surface((int(p.size * 2), int(p.size * 2)), pygame.SRCALPHA)
            pygame.draw.circle(surf, (col[0], col[1], col[2], alpha), (int(p.size), int(p.size)), int(p.size))
            self.screen.blit(surf, (int(p.x - p.size), int(p.y - p.size)))

        score_surf = self.font_med.render(f"Score: {self.score}", True, WHITE)
        combo_surf = self.font_med.render(f"Combo: {self.combo}", True, WHITE)
        lives_surf = self.font_med.render(f"Lives: {self.lives}", True, WHITE)
        self.screen.blit(score_surf, (18, 12))
        self.screen.blit(combo_surf, (WIDTH // 2 - combo_surf.get_width() // 2, 12))
        self.screen.blit(lives_surf, (WIDTH - lives_surf.get_width() - 18, 12))

        if self.hit_feedback:
            text, timer, color = self.hit_feedback
            surf = self.font_big.render(text, True, color)
            self.screen.blit(surf, (WIDTH // 2 - surf.get_width() // 2, HEIGHT // 2 - surf.get_height() // 2))

    # ------------------- main loop / events -------------------
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
                if self.state == 'menu':
                    for name, rect in self.menu_buttons.items():
                        if rect.collidepoint(mx, my):
                            if name == 'start':
                                self.start_play()
                            elif name == 'settings':
                                self.state = 'settings'
                            elif name == 'leader':
                                self.state = 'leader'
                            elif name == 'quit':
                                self.save_all()
                                self.running = False
                elif self.state == 'settings':
                    for key, rect in getattr(self, 'settings_buttons', {}).items():
                        if rect.collidepoint(mx, my):
                            if key == 'sound':
                                self.settings['sound'] = not self.settings.get('sound', True)
                                self.save_all()
                                self._create_placeholder_sounds()
                            elif key == 'diff':
                                cur = self.settings.get('difficulty', 'normal')
                                nxt = {'easy': 'normal', 'normal': 'hard', 'hard': 'easy'}[cur]
                                self.settings['difficulty'] = nxt
                                self.apply_difficulty()
                                self.save_all()
                            elif key == 'hit_dec':
                                self.settings['hit_window'] = max(20, self.settings.get('hit_window', DEFAULT_HIT_WINDOW) - 4)
                                self.save_all()
                            elif key == 'hit_inc':
                                self.settings['hit_window'] = min(140, self.settings.get('hit_window', DEFAULT_HIT_WINDOW) + 4)
                                self.save_all()
                            elif key == 'load_bg':
                                # open file dialog and load background
                                path = ask_open_filename('Choose background audio')
                                if path:
                                    self.settings['bg_file'] = path
                                    save_json(SETTINGS_FILE, self.settings)
                                    try:
                                        self.load_background_file(path)
                                    except Exception as e:
                                        print('Background load failed:', e)
                            elif key == 'back':
                                self.state = 'menu'
                    # remap click handling
                    for mapkey, rect in getattr(self, 'remap_key_buttons', {}).items():
                        if rect.collidepoint(mx, my):
                            self.state = 'remap_key'
                            self.remap_target = ('keymap', mapkey)
                            self.remap_callback = self._complete_remap_key
                    for mapkey, rect in getattr(self, 'remap_joy_buttons', {}).items():
                        if rect.collidepoint(mx, my):
                            self.state = 'remap_joy'
                            self.remap_target = ('joymap', mapkey)
                            self.remap_callback = self._complete_remap_joy
                elif self.state == 'leader':
                    for key, rect in getattr(self, 'leader_buttons', {}).items():
                        if rect.collidepoint(mx, my) and key == 'back':
                            self.state = 'menu'
                elif self.state == 'gameover':
                    self.start_play()
            elif event.type == pygame.KEYDOWN:
                if self.state == 'menu':
                    if event.key == pygame.K_RETURN:
                        self.start_play()
                    elif event.key == pygame.K_s:
                        self.state = 'settings'
                elif self.state == 'settings':
                    if event.key == pygame.K_ESCAPE:
                        self.state = 'menu'
                elif self.state == 'leader':
                    if event.key == pygame.K_ESCAPE:
                        self.state = 'menu'
                elif self.state == 'remap_key':
                    if self.remap_callback:
                        self.remap_callback(event.key)
                elif self.state == 'remap_joy':
                    if event.key == pygame.K_ESCAPE:
                        self.state = 'settings'
                elif self.state == 'playing':
                    self.handle_keypress_playing(event.key)
                elif self.state == 'gameover':
                    if event.key == pygame.K_RETURN:
                        self.start_play()
            # joystick events
            if event.type in (pygame.JOYBUTTONDOWN, pygame.JOYAXISMOTION):
                if self.state == 'playing':
                    self.handle_joy_event(event)
                elif self.state == 'remap_joy' and self.remap_callback:
                    self.remap_callback(event)

    def update(self, dt):
        if self.state == 'playing':
            self.update_game(dt)

    def render(self):
        self.screen.fill(BLACK)
        if self.state == 'menu':
            self.draw_menu()
        elif self.state == 'settings':
            self.draw_settings()
        elif self.state == 'leader':
            self.draw_leaderboard()
        elif self.state == 'playing':
            self.draw_game_ui()
        elif self.state == 'remap_key':
            msg = self.font_med.render('Press a key to assign (Esc to cancel)', True, WHITE)
            self.screen.blit(msg, (WIDTH // 2 - msg.get_width() // 2, HEIGHT // 2 - 40))
        elif self.state == 'remap_joy':
            msg = self.font_med.render('Press a joystick button or move an axis (Esc to cancel)', True, WHITE)
            self.screen.blit(msg, (WIDTH // 2 - msg.get_width() // 2, HEIGHT // 2 - 40))
        elif self.state == 'gameover':
            over = self.font_big.render('GAME OVER', True, BAD_RED)
            score = self.font_med.render(f'Final Score: {self.score}', True, WHITE)
            prompt = self.font_med.render('Click or press Enter to play again', True, WHITE)
            self.screen.blit(over, (WIDTH // 2 - over.get_width() // 2, HEIGHT // 2 - 120))
            self.screen.blit(score, (WIDTH // 2 - score.get_width() // 2, HEIGHT // 2 - 40))
            self.screen.blit(prompt, (WIDTH // 2 - prompt.get_width() // 2, HEIGHT // 2 + 20))

        preview = self.font_sm.render(f'Top: {self._highest_score()}', True, WHITE)
        self.screen.blit(preview, (WIDTH - preview.get_width() - 12, 12))

        pygame.display.flip()

    def _complete_remap_key(self, pressed_key):
        if not self.remap_target:
            self.state = 'settings'
            return
        kind, mapkey = self.remap_target
        if kind != 'keymap':
            self.state = 'settings'
            return
        self.settings.setdefault('keymap', {})[mapkey] = pressed_key
        save_json(SETTINGS_FILE, self.settings)
        self.remap_target = None
        self.state = 'settings'

    def _complete_remap_joy(self, event):
        if not self.remap_target:
            self.state = 'settings'
            return
        kind, mapkey = self.remap_target
        if kind != 'joymap':
            self.state = 'settings'
            return
        jm = self.settings.setdefault('joymap', {})
        if isinstance(event, pygame.event.EventType):
            if event.type == pygame.JOYBUTTONDOWN:
                jm[mapkey] = {'type': 'button', 'id': event.button}
            elif event.type == pygame.JOYAXISMOTION:
                dirn = 1 if event.value > 0 else -1
                jm[mapkey] = {'type': 'axis', 'id': event.axis, 'dir': dirn, 'thresh': 0.6}
        else:
            if isinstance(event, int):
                jm[mapkey] = {'type': 'button', 'id': int(event)}
        save_json(SETTINGS_FILE, self.settings)
        self.remap_target = None
        self.state = 'settings'

    # ------------------- game control -------------------
    def start_play(self):
        self.apply_difficulty()
        self.notes = []
        self.particles = []
        self.spawn_timer = 0.0
        self.score = 0
        self.combo = 0
        self.lives = 5
        self.hit_feedback = None
        self.time_since_start = 0.0
        self.next_beat_idx = 0
        self.music_playing = False
        # if we have background and beats, start music and sync
        if self.bg_file:
            try:
                pygame.mixer.music.load(self.bg_file)
                pygame.mixer.music.play()
                self.music_start_ticks = pygame.time.get_ticks()
                self.music_playing = True
            except Exception as e:
                print('Failed to start music playback:', e)
                self.music_playing = False
        self.state = 'playing'
        self.play_sound('start')

    def save_all(self):
        save_json(SETTINGS_FILE, self.settings)
        save_json(LEADERBOARD_FILE, self.leaderboard)

    def add_to_leaderboard(self, name, score):
        self.leaderboard.append({'name': name, 'score': int(score)})
        self.leaderboard = sorted(self.leaderboard, key=lambda x: -x['score'])[:10]
        self.save_all()

    def _highest_score(self):
        if not self.leaderboard:
            return 0
        return max(e['score'] for e in self.leaderboard)

# ------------------- RUN -------------------
if __name__ == '__main__':
    if not LIBROSA_AVAILABLE:
        print('Note: librosa not installed. Beat detection will be unavailable. Install librosa for beat-sync features.')
    game = Lalalala()
    game.run()

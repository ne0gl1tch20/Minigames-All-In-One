"""
Word Scramble - main.py
Place in a folder named `WordScramble` inside your launcher's `minigames` folder.

Now with built-in pygame-generated sound effects (no external .wav files required).
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
import math
import array
from pathlib import Path
from typing import List, Dict

# ------------------- CONFIG / SAVE PATH -------------------
USER_DIR = os.path.expandvars(r"%userprofile%") if os.name == 'nt' else os.path.expanduser('~')
MG_SAVE_DIR = Path(USER_DIR) / "Documents" / ".mgaio"
APP_NAME = "Word Scramble"
SAVE_FOLDER = MG_SAVE_DIR / "Saves" / APP_NAME
SAVE_FOLDER.mkdir(parents=True, exist_ok=True)

SETTINGS_FILE = SAVE_FOLDER / "settings.json"
LEADERBOARD_FILE = SAVE_FOLDER / "leaderboard.json"

DEFAULT_SETTINGS = {
    "volume": 100,
    "sound": True,
    "difficulty": "normal",
}
DEFAULT_LEADERBOARD: List[Dict] = []

# default word list (small). You can add a words.txt file beside main.py with one word per line.
DEFAULT_WORDS = [
    "apple","banana","cherry","orange","grape","melon","kiwi","dragon","python",
    "rocket","galaxy","puzzle","mystery","adventure","castle","wizard","forest","ocean",
    "river","mountain","island","planet","planetary","computer","button","keyboard","screen",
]

# ------------------- HELPERS -------------------
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
        print('Save failed:', e)

def load_words_from_file(folder: Path) -> List[str]:
    p = folder / 'words.txt'
    if p.exists():
        try:
            with open(p, 'r', encoding='utf-8') as f:
                words = [w.strip().lower() for w in f if w.strip()]
                return [w for w in words if w.isalpha()]
        except Exception:
            pass
    return DEFAULT_WORDS.copy()

def scramble_word(word: str) -> str:
    if len(word) <= 2:
        return word
    letters = list(word)
    while True:
        random.shuffle(letters)
        s = ''.join(letters)
        if s != word:
            return s

# ------------------- SOUND GENERATION -------------------
# Pre-init mixer for consistent format
SAMPLE_RATE = 44100
pygame.mixer.pre_init(SAMPLE_RATE, -16, 1, 512)  # 44100 Hz, 16-bit signed, mono, small buffer

# try to use numpy for faster sound array creation; fallback to pure-python
try:
    import numpy as np
    NUMPY_AVAILABLE = True
except Exception:
    np = None
    NUMPY_AVAILABLE = False

def make_tone(frequency=440.0, duration_ms=150, volume=0.5):
    """
    Create a pygame Sound of a sine tone.
    Tries numpy+sndarray if available, otherwise uses array('h') and Sound(buffer=bytes).
    """
    n_samples = int(SAMPLE_RATE * (duration_ms / 1000.0))
    if n_samples <= 0:
        n_samples = 1

    if NUMPY_AVAILABLE:
        t = np.linspace(0, duration_ms/1000.0, n_samples, False)
        wave = np.sin(2 * np.pi * frequency * t)
        # simple envelope (attack+decay)
        envelope = 1.0 - (t / (duration_ms/1000.0))  # linear decay
        wave = wave * envelope
        audio = (wave * volume * 32767).astype(np.int16)
        try:
            sound = pygame.sndarray.make_sound(audio)
            return sound
        except Exception:
            # fallthrough to python fallback
            pass

    # pure python fallback
    buf = array.array('h')
    for i in range(n_samples):
        t = i / SAMPLE_RATE
        envelope = 1.0 - (t / (duration_ms/1000.0))
        s = math.sin(2.0 * math.pi * frequency * t) * envelope
        v = int(s * volume * 32767)
        buf.append(v)
    try:
        sound = pygame.mixer.Sound(buffer=buf.tobytes())
        return sound
    except Exception as e:
        # as ultimate fallback create a silent short sound
        return pygame.mixer.Sound(buffer=b'\x00\x00'*n_samples)

def play_melody_seq(sounds: List[pygame.mixer.Sound], spacing_ms:int = 70, volume:float=1.0):
    """Play a short sequence of Sound objects sequentially (blocking but short)."""
    for s in sounds:
        try:
            s.set_volume(volume)
            s.play()
        except Exception:
            pass
        pygame.time.delay(spacing_ms)

# ------------------- GAME -------------------
class WordScramble:
    WIDTH, HEIGHT = 800, 540
    FPS = 60
    BASE_TIME = 15  # seconds per word (modified by difficulty)

    def __init__(self):
        # init pygame + mixer
        pygame.init()
        # after pre_init, init the mixer (safe guard)
        try:
            pygame.mixer.init()
        except Exception:
            pass

        pygame.joystick.init()
        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT))
        pygame.display.set_caption(APP_NAME)
        self.clock = pygame.time.Clock()
        self.font_big = pygame.font.SysFont('arial', 56, bold=True)
        self.font_med = pygame.font.SysFont('arial', 28)
        self.font_sm = pygame.font.SysFont('arial', 20)

        # Storage
        self.settings = load_json(SETTINGS_FILE, DEFAULT_SETTINGS.copy())
        # ensure keys exist
        for k, v in DEFAULT_SETTINGS.items():
            self.settings.setdefault(k, v)
        self.leaderboard = load_json(LEADERBOARD_FILE, DEFAULT_LEADERBOARD.copy())

        # words
        self.game_folder = Path(__file__).resolve().parent
        self.words = load_words_from_file(self.game_folder)

        # state
        self.state = 'menu'  # menu, playing, gameover
        self.running = True
        self.score = 0
        self.current_word = ''
        self.scrambled = ''
        self.player_input = ''
        self.time_left = 0.0
        self.player_name = 'Player'
        self.name_input = ''
        self.cursor_timer = 0.0
        self.hint_mask = []  # list of revealed letters indexes

        # difficulty
        self.difficulty = self.settings.get('difficulty', 'normal')
        if self.difficulty == 'easy':
            self.time_per_word = int(self.BASE_TIME * 1.4)
        elif self.difficulty == 'hard':
            self.time_per_word = int(self.BASE_TIME * 0.8)
        else:
            self.time_per_word = self.BASE_TIME

        # Build sounds
        self._build_sounds_from_settings()

    def _build_sounds_from_settings(self):
        vol = max(0.0, min(1.0, (self.settings.get('volume', 100) / 100.0)))
        # correct melody (three tones: warm "lalala" feeling)
        c1 = make_tone(660.0, 110, volume=0.65)
        c2 = make_tone(880.0, 110, volume=0.65)
        c3 = make_tone(990.0, 160, volume=0.65)
        self.correct_melody = [c1, c2, c3]
        for s in self.correct_melody:
            try: s.set_volume(vol)
            except Exception: pass

        # hint beep
        self.hint_beep = make_tone(480.0, 180, volume=0.6)
        try: self.hint_beep.set_volume(vol)
        except Exception: pass

        # wrong / penalty beep (low)
        self.wrong_beep = make_tone(220.0, 150, volume=0.7)
        try: self.wrong_beep.set_volume(vol)
        except Exception: pass

        # timeup beep (two descending pings)
        self.timeup1 = make_tone(740.0, 100, volume=0.6)
        self.timeup2 = make_tone(480.0, 140, volume=0.6)
        for s in (self.timeup1, self.timeup2):
            try: s.set_volume(vol)
            except Exception: pass

    def pick_word(self):
        if not self.words:
            self.words = DEFAULT_WORDS.copy()
        self.current_word = random.choice(self.words).lower()
        self.scrambled = scramble_word(self.current_word)
        self.player_input = ''
        self.time_left = float(self.time_per_word)
        self.hint_mask = [False] * len(self.current_word)

    def start_game(self):
        self.score = 0
        self.pick_word()
        self.state = 'playing'

    def end_game(self):
        self.state = 'gameover'
        # show name input etc

    def run(self):
        while self.running:
            dt = self.clock.tick(self.FPS) / 1000.0
            self.handle_events()
            if self.state == 'playing':
                self.update_game(dt)
            self.render()
        pygame.quit()
        sys.exit()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if self.state == 'menu':
                    if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                        self.start_game()
                elif self.state == 'playing':
                    if event.key == pygame.K_BACKSPACE:
                        self.player_input = self.player_input[:-1]
                    elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                        self.submit_answer()
                    elif event.key == pygame.K_1:
                        self.use_hint()
                    elif event.key == pygame.K_2:
                        # reshuffle scrambled
                        self.scrambled = scramble_word(self.current_word)
                    else:
                        ch = event.unicode
                        if ch and ch.isalpha() and len(self.player_input) < len(self.current_word):
                            self.player_input += ch.lower()
                elif self.state == 'gameover':
                    if event.key == pygame.K_BACKSPACE:
                        self.name_input = self.name_input[:-1]
                    elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                        self.player_name = self.name_input.strip() or 'Player'
                        self.save_score_and_back_to_menu()
                    else:
                        ch = event.unicode
                        if ch and len(self.name_input) < 16 and (32 <= ord(ch) <= 126):
                            self.name_input += ch
            elif event.type == pygame.JOYBUTTONDOWN:
                # simple support: button 0 = submit/start
                if event.button == 0:
                    if self.state == 'menu':
                        self.start_game()
                    elif self.state == 'playing':
                        self.submit_answer()
                    elif self.state == 'gameover':
                        self.player_name = self.name_input.strip() or 'Player'
                        self.save_score_and_back_to_menu()

    def use_hint(self):
        # reveal one unrevealed letter in correct position
        unrevealed = [i for i, v in enumerate(self.hint_mask) if not v]
        if not unrevealed:
            return
        idx = random.choice(unrevealed)
        self.hint_mask[idx] = True
        # reduce time slightly
        self.time_left = max(0.5, self.time_left - 2.0)
        if self.settings.get('sound', True):
            try:
                self.hint_beep.play()
            except Exception:
                pass

    def submit_answer(self):
        attempt = self.player_input.strip().lower()
        if not attempt:
            return
        if attempt == self.current_word:
            # correct — compute score: base + time bonus
            base = len(self.current_word) * 10
            time_bonus = int(self.time_left * 5)
            hint_penalty = sum(self.hint_mask) * 5
            gained = max(1, base + time_bonus - hint_penalty)
            self.score += gained

            if self.settings.get('sound', True):
                # play melody (blocking short)
                try:
                    play_melody_seq(self.correct_melody, spacing_ms=80, volume=(self.settings.get('volume',100)/100.0))
                except Exception:
                    # fallback quick play
                    for s in self.correct_melody:
                        try: s.play()
                        except Exception: pass

            # next word
            self.pick_word()
        else:
            # wrong: small penalty and clear input
            self.score = max(0, self.score - 5)
            self.player_input = ''
            if self.settings.get('sound', True):
                try:
                    self.wrong_beep.play()
                except Exception:
                    pass

    def update_game(self, dt):
        self.time_left -= dt
        if self.time_left <= 0:
            # time's up for this word: penalty and new word
            self.score = max(0, self.score - 2)
            self.pick_word()
            if self.settings.get('sound', True):
                # play two-tone timeup
                try:
                    self.timeup1.play()
                    pygame.time.delay(90)
                    self.timeup2.play()
                except Exception:
                    pass

    # ---------- rendering ----------
    def render(self):
        self.screen.fill((18, 24, 40))
        if self.state == 'menu':
            self.draw_menu()
        elif self.state == 'playing':
            self.draw_playing()
        elif self.state == 'gameover':
            self.draw_gameover()
        pygame.display.flip()

    def draw_menu(self):
        title = self.font_big.render('Word Scramble', True, (255, 220, 120))
        self.screen.blit(title, (self.WIDTH//2 - title.get_width()//2, 80))
        info = self.font_med.render('Press ENTER to start — Type the correct word and press Enter', True, (200,200,200))
        self.screen.blit(info, (self.WIDTH//2 - info.get_width()//2, 200))

        # show top scores
        lb_title = self.font_med.render('Top Scores', True, (220,220,220))
        self.screen.blit(lb_title, (50, 280))
        for i, e in enumerate(sorted(self.leaderboard, key=lambda x: x.get('score',0), reverse=True)[:6], start=1):
            text = self.font_sm.render(f"{i}. {e.get('name','Player')} — {e.get('score',0)}", True, (200,200,200))
            self.screen.blit(text, (50, 280 + i*28))

    def draw_playing(self):
        # scramble
        scrambled_surf = self.font_big.render(self.scrambled.upper(), True, (240,240,240))
        self.screen.blit(scrambled_surf, (self.WIDTH//2 - scrambled_surf.get_width()//2, 80))

        # input box
        box_w = 640
        bx = self.WIDTH//2 - box_w//2
        by = 260
        pygame.draw.rect(self.screen, (30,36,50), (bx, by, box_w, 56), border_radius=8)
        pygame.draw.rect(self.screen, (120,120,120), (bx, by, box_w, 56), 2, border_radius=8)

        inp = self.player_input or ''
        input_surf = self.font_med.render(inp, True, (240,240,240))
        self.screen.blit(input_surf, (bx + 14, by + (56 - input_surf.get_height())//2))

        # cursor
        self.cursor_timer += self.clock.get_time() / 1000.0
        if int(self.cursor_timer * 2) % 2 == 0:
            cur_x = bx + 14 + input_surf.get_width() + 2
            pygame.draw.rect(self.screen, (240,240,240), (cur_x, by + 10, 2, 36))

        # HUD: score and time
        score_surf = self.font_med.render(f"Score: {self.score}", True, (220,220,220))
        time_surf = self.font_med.render(f"Time: {int(self.time_left)}", True, (220,220,220))
        self.screen.blit(score_surf, (20, 20))
        self.screen.blit(time_surf, (self.WIDTH - time_surf.get_width() - 20, 20))

        # hint display: show revealed letters in correct positions
        hint_y = by + 80
        display = ''
        for i, ch in enumerate(self.current_word):
            if self.hint_mask[i]:
                display += ch.upper()
            else:
                display += '_'
            display += ' '
        hint_surf = self.font_med.render(display.strip(), True, (180,180,180))
        self.screen.blit(hint_surf, (self.WIDTH//2 - hint_surf.get_width()//2, hint_y))

        # small help
        help_surf = self.font_sm.render('1 = hint (-2s), 2 = reshuffle | Backspace to delete | Enter = submit', True, (160,160,160))
        self.screen.blit(help_surf, (self.WIDTH//2 - help_surf.get_width()//2, hint_y + 40))

    def draw_gameover(self):
        overlay = pygame.Surface((self.WIDTH, self.HEIGHT), pygame.SRCALPHA)
        overlay.fill((0,0,0,200))
        self.screen.blit(overlay, (0,0))
        title = self.font_big.render('Game Over', True, (255, 200, 80))
        self.screen.blit(title, (self.WIDTH//2 - title.get_width()//2, 60))

        score_surf = self.font_med.render(f'Your score: {self.score}', True, (220,220,220))
        self.screen.blit(score_surf, (self.WIDTH//2 - score_surf.get_width()//2, 160))

        prompt = self.font_med.render('Enter your name and press Enter to save:', True, (200,200,200))
        self.screen.blit(prompt, (self.WIDTH//2 - prompt.get_width()//2, 220))

        # name box
        box_w = 420
        bx = self.WIDTH//2 - box_w//2
        by = 280
        pygame.draw.rect(self.screen, (36,40,50), (bx, by, box_w, 48), border_radius=8)
        pygame.draw.rect(self.screen, (200,200,200), (bx, by, box_w, 48), 2, border_radius=8)
        nm = self.name_input or 'Player'
        nm_surf = self.font_med.render(nm, True, (240,240,240))
        self.screen.blit(nm_surf, (bx + 12, by + (48 - nm_surf.get_height())//2))

        # blinking cursor
        self.cursor_timer += self.clock.get_time() / 1000.0
        if int(self.cursor_timer * 2) % 2 == 0:
            cur_x = bx + 12 + nm_surf.get_width() + 2
            pygame.draw.rect(self.screen, (240,240,240), (cur_x, by + 10, 2, 28))

        hint = self.font_sm.render('Press Enter to save score and return to menu', True, (160,160,160))
        self.screen.blit(hint, (self.WIDTH//2 - hint.get_width()//2, by + box_w//6))

    # ---------- leaderboard ----------
    def save_score_and_back_to_menu(self):
        entry = {'name': self.player_name, 'score': int(self.score), 'time': int(time.time())}
        self.leaderboard.append(entry)
        self.leaderboard = sorted(self.leaderboard, key=lambda x: x.get('score',0), reverse=True)[:50]
        save_json(LEADERBOARD_FILE, self.leaderboard)
        self.name_input = ''
        self.player_name = 'Player'
        self.state = 'menu'

# ------------------- RUN -------------------
if __name__ == '__main__':
    game = WordScramble()
    game.run()

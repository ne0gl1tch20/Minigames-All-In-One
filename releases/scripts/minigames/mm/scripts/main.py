#!/usr/bin/env python3
# Math Mania - Pygame
# Requirements: pip install pygame

import pygame, sys, random, json
from pathlib import Path
from datetime import datetime

# ---------- CONFIG / SAVE PATH ----------
APP_NAME = "Math Mania"
SAVE_DIR = Path.home() / "Documents" / ".mgaio" / "Saves" / APP_NAME
SAVE_DIR.mkdir(parents=True, exist_ok=True)
LEADERBOARD_FILE = SAVE_DIR / "leaderboard.json"

# ---------- HELPERS ----------
def load_leaderboard():
    if LEADERBOARD_FILE.exists():
        try:
            return json.loads(LEADERBOARD_FILE.read_text(encoding="utf-8"))
        except Exception:
            return []
    return []

def save_leaderboard(lb):
    try:
        LEADERBOARD_FILE.write_text(json.dumps(lb, indent=2, ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass

# ---------- PYGAME INIT ----------
pygame.init()
W, H = 800, 600
screen = pygame.display.set_mode((W, H))
pygame.display.set_caption(APP_NAME)
clock = pygame.time.Clock()
font_big = pygame.font.SysFont("arial", 48, bold=True)
font_med = pygame.font.SysFont("arial", 28)
font_sm = pygame.font.SysFont("arial", 18)

# ---------- GAME STATE ----------
score = 0
lives = 3
time_left = 8.0
input_buf = ""
current_q = None
game_running = False
leaderboard = load_leaderboard()

def make_question(level=1):
    # level governs operator and magnitude
    ops = ['+','-','*'] if level>=2 else ['+','-']
    op = random.choice(ops)
    if op == '+':
        a = random.randint(1, 10*level)
        b = random.randint(1, 10*level)
        ans = a + b
    elif op == '-':
        a = random.randint(1, 10*level)
        b = random.randint(1, a)
        ans = a - b
    else:
        a = random.randint(1, level+2)
        b = random.randint(1, level+3)
        ans = a * b
    return f"{a} {op} {b} = ?", str(ans)

def new_round():
    global current_q, input_buf, time_left
    difficulty = 1 + score // 10
    q, a = make_question(difficulty)
    current_q = (q, a)
    input_buf = ""
    time_left = max(3.0, 8.0 - (score * 0.05))

def draw_text_center(text, y, fnt, color=(255,255,255)):
    surf = fnt.render(text, True, color)
    screen.blit(surf, (W//2 - surf.get_width()//2, y))

def game_over():
    global leaderboard
    name = "Player"
    # prompt simple: use console input (works when running locally)
    try:
        name = input("Game over! Enter name for leaderboard: ").strip() or "Player"
    except Exception:
        name = "Player"
    leaderboard.append({"name": name, "score": score, "when": datetime.now().isoformat()})
    leaderboard = sorted(leaderboard, key=lambda x: x["score"], reverse=True)[:20]
    save_leaderboard(leaderboard)

# ---------- MAIN LOOP ----------
new_round()
game_running = False

while True:
    dt = clock.tick(60) / 1000.0
    for ev in pygame.event.get():
        if ev.type == pygame.QUIT:
            pygame.quit(); sys.exit()
        if ev.type == pygame.KEYDOWN:
            if not game_running:
                if ev.key == pygame.K_RETURN:
                    score = 0; lives = 3; new_round(); game_running = True
                elif ev.key == pygame.K_l:
                    # show leaderboard in console
                    print("=== Leaderboard ===")
                    for e in leaderboard:
                        print(f"{e['name']} — {e['score']}")
                elif ev.key == pygame.K_ESCAPE:
                    pygame.quit(); sys.exit()
            else:
                if ev.key == pygame.K_BACKSPACE:
                    input_buf = input_buf[:-1]
                elif ev.key == pygame.K_RETURN:
                    # check answer
                    if input_buf.strip() == current_q[1]:
                        score += 1
                        new_round()
                    else:
                        lives -= 1
                        if lives <= 0:
                            game_running = False
                            game_over()
                            new_round()
                        else:
                            new_round()
                else:
                    ch = ev.unicode
                    if ch.isdigit() or (ch == '-' and not input_buf):
                        input_buf += ch

    if game_running:
        time_left -= dt
        if time_left <= 0:
            lives -= 1
            if lives <= 0:
                game_running = False
                game_over()
                new_round()
            else:
                new_round()

    # RENDER
    screen.fill((12,12,20))
    draw_text_center("Math Mania", 40, font_big, (255,200,60))
    if not game_running:
        draw_text_center("Press ENTER to Start  •  L = Leaderboard  •  Esc = Quit", 140, font_med, (220,220,220))
    else:
        draw_text_center(current_q[0], 160, font_big)
        draw_text_center(input_buf or "_", 260, font_big, (180,255,180))
        draw_text_center(f"Score: {score}   Lives: {lives}", 340, font_med)
        draw_text_center(f"Time: {time_left:.1f}s", 380, font_sm)

    # small footer
    draw_text_center("Type the answer then press Enter", H - 40, font_sm, (140,140,140))

    pygame.display.flip()

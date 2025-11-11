#!/usr/bin/env python3
# Word Ladder (Anagram unscramble) - Pygame
import pygame, sys, random, json
from pathlib import Path
from datetime import datetime

APP_NAME = "Word Ladder"
SAVE_DIR = Path.home() / "Documents" / ".mgaio" / "Saves" / APP_NAME
SAVE_DIR.mkdir(parents=True, exist_ok=True)
LEADERBOARD_FILE = SAVE_DIR / "leaderboard.json"

def load_lb():
    try:
        return json.loads(LEADERBOARD_FILE.read_text(encoding="utf-8"))
    except Exception:
        return []

def save_lb(lb):
    try:
        LEADERBOARD_FILE.write_text(json.dumps(lb, indent=2, ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass

WORDS = [
 "apple","orange","banana","planet","rocket","castle","bridge","school","window","summer",
 "puzzle","memory","forest","python","galaxy","bubble","coffee","camera","dragon","friend"
]

pygame.init()
W,H=800,600
screen=pygame.display.set_mode((W,H))
pygame.display.set_caption(APP_NAME)
clock=pygame.time.Clock()
f_big=pygame.font.SysFont("arial",56)
f_med=pygame.font.SysFont("arial",28)
f_sm=pygame.font.SysFont("arial",18)

leaderboard = load_lb()
score=0
input_buf=""
game_on=False
current_word=None
time_left=12.0

def pick_word():
    w=random.choice(WORDS)
    arr=list(w)
    random.shuffle(arr)
    scrambled="".join(arr)
    # ensure scrambled != w
    if scrambled == w:
        return pick_word()
    return w, scrambled

def game_over():
    global leaderboard
    try:
        name=input("Game over! Enter name for leaderboard: ").strip() or "Player"
    except Exception:
        name="Player"
    leaderboard.append({"name":name,"score":score,"when":datetime.now().isoformat()})
    leaderboard=sorted(leaderboard,key=lambda x:x["score"],reverse=True)[:20]
    save_lb(leaderboard)

def new_round():
    global current_word, input_buf, time_left
    current_word = pick_word()
    input_buf=""
    time_left=12.0

new_round()

while True:
    dt=clock.tick(60)/1000.0
    for ev in pygame.event.get():
        if ev.type==pygame.QUIT:
            pygame.quit(); sys.exit()
        if ev.type==pygame.KEYDOWN:
            if not game_on:
                if ev.key==pygame.K_RETURN:
                    score=0; game_on=True; new_round()
                elif ev.key==pygame.K_ESCAPE:
                    pygame.quit(); sys.exit()
            else:
                if ev.key==pygame.K_BACKSPACE:
                    input_buf=input_buf[:-1]
                elif ev.key==pygame.K_RETURN:
                    # check
                    if input_buf.lower().strip() == current_word[0]:
                        score+=1
                        new_round()
                    else:
                        game_on=False
                        game_over()
                        new_round()
                else:
                    ch=ev.unicode
                    if ch.isalpha():
                        input_buf+=ch

    if game_on:
        time_left-=dt
        if time_left<=0:
            # timeout = game over
            game_on=False
            game_over()
            new_round()

    # render
    screen.fill((18,18,30))
    screen.blit(f_big.render("Word Ladder", True, (255,200,60)), (W//2-200,30))
    if not game_on:
        screen.blit(f_med.render("Press Enter to Start  •  Type the correct word from the scrambled letters", True, (220,220,220)), (80,130))
    else:
        scr_text=f_med.render(f"Scrambled: {current_word[1]}", True, (255,255,255))
        screen.blit(scr_text, (W//2 - scr_text.get_width()//2, 180))
        in_text=f_big.render(input_buf or "_", True, (200,255,180))
        screen.blit(in_text, (W//2 - in_text.get_width()//2, 260))
        screen.blit(f_med.render(f"Score: {score}", True, (230,230,230)), (20,20))
        screen.blit(f_sm.render(f"Time: {time_left:.1f}s", True, (200,200,200)), (20,60))
    pygame.display.flip()

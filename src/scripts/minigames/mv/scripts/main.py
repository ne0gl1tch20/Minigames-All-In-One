#!/usr/bin/env python3
# Memory Vault - Pygame memory match
import pygame, sys, random, json
from pathlib import Path
from datetime import datetime

APP_NAME = "Memory Vault"
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

pygame.init()
W,H=800,600
screen=pygame.display.set_mode((W,H))
pygame.display.set_caption(APP_NAME)
clock=pygame.time.Clock()
f_big=pygame.font.SysFont("arial",48)
f_med=pygame.font.SysFont("arial",24)

leaderboard = load_lb()

# grid
ROWS, COLS = 4, 4
CARD_W = 100
MARGIN = 12
grid_origin = ( (W - (COLS*CARD_W + (COLS-1)*MARGIN))//2, 120 )

# symbols (use simple emojis or letters)
SYMBOLS = list("😀😎🦊🐶🐱🍀🍎⭐️🎵🍩🌟🚀🎯🍓🍇🍉")[:(ROWS*COLS)//2]
SYMBOLS = SYMBOLS*2
random.shuffle(SYMBOLS)

cards = []
for r in range(ROWS):
    for c in range(COLS):
        cards.append({
            "pos": (r,c),
            "symbol": SYMBOLS[r*COLS + c],
            "state": "hidden"  # hidden, flipped, matched
        })

first_flip = None
second_flip = None
reveal_time = 0.0
score = 0
moves = 0
game_on = False

def reset_board():
    global cards, first_flip, second_flip, reveal_time, score, moves
    s = list(SYMBOLS)
    random.shuffle(s)
    for i,card in enumerate(cards):
        card["symbol"] = s[i]
        card["state"] = "hidden"
    first_flip = second_flip = None
    reveal_time = 0.0
    score = 0
    moves = 0

reset_board()

def draw_card(i):
    r,c = cards[i]["pos"]
    x0 = grid_origin[0] + c*(CARD_W+MARGIN)
    y0 = grid_origin[1] + r*(CARD_W+MARGIN)
    rect = pygame.Rect(x0,y0,CARD_W,CARD_W)
    state = cards[i]["state"]
    if state == "hidden":
        pygame.draw.rect(screen, (40,40,90), rect, border_radius=8)
    elif state == "flipped":
        pygame.draw.rect(screen, (240,240,240), rect, border_radius=8)
        s = str(cards[i]["symbol"])
        surf = f_big.render(s, True, (20,20,20))
        screen.blit(surf, (x0 + CARD_W//2 - surf.get_width()//2, y0 + CARD_W//2 - surf.get_height()//2))
    elif state == "matched":
        pygame.draw.rect(screen, (80,200,120), rect, border_radius=8)
        s = str(cards[i]["symbol"])
        surf = f_big.render(s, True, (10,10,10))
        screen.blit(surf, (x0 + CARD_W//2 - surf.get_width()//2, y0 + CARD_W//2 - surf.get_height()//2))
    pygame.draw.rect(screen, (10,10,10), rect, 2, border_radius=8)
    return rect

def idx_from_pos(pos):
    x,y = pos
    for i,card in enumerate(cards):
        r,c = card["pos"]
        x0 = grid_origin[0] + c*(CARD_W+MARGIN)
        y0 = grid_origin[1] + r*(CARD_W+MARGIN)
        rect = pygame.Rect(x0,y0,CARD_W,CARD_W)
        if rect.collidepoint(x,y):
            return i
    return None

def game_over():
    name = "Player"
    try:
        name = input("You finished! Enter your name for leaderboard: ").strip() or "Player"
    except Exception:
        name = "Player"
    lb = leaderboard
    lb.append({"name":name,"score":moves,"when":datetime.now().isoformat()})
    lb = sorted(lb, key=lambda x: x["score"])[:20]  # lower moves better
    save_lb(lb)

while True:
    dt = clock.tick(60)/1000.0
    for ev in pygame.event.get():
        if ev.type==pygame.QUIT:
            pygame.quit(); sys.exit()
        if ev.type==pygame.KEYDOWN:
            if ev.key==pygame.K_RETURN:
                game_on = True
                reset_board()
            elif ev.key==pygame.K_ESCAPE:
                pygame.quit(); sys.exit()
        if ev.type==pygame.MOUSEBUTTONDOWN and game_on:
            if reveal_time>0:
                continue
            idx = idx_from_pos(ev.pos)
            if idx is None: continue
            if cards[idx]["state"] != "hidden": continue
            if first_flip is None:
                cards[idx]["state"]="flipped"
                first_flip = idx
            elif second_flip is None:
                cards[idx]["state"]="flipped"
                second_flip = idx
                moves += 1
                # check match
                if cards[first_flip]["symbol"] == cards[second_flip]["symbol"]:
                    cards[first_flip]["state"]="matched"
                    cards[second_flip]["state"]="matched"
                    first_flip = second_flip = None
                    # check finish
                    if all(c["state"]=="matched" for c in cards):
                        game_on=False
                        game_over()
                else:
                    reveal_time = 0.8  # seconds before flip back

    if reveal_time>0:
        reveal_time -= dt
        if reveal_time<=0:
            if first_flip is not None and second_flip is not None:
                cards[first_flip]["state"]="hidden"
                cards[second_flip]["state"]="hidden"
            first_flip = second_flip = None

    # render
    screen.fill((12,12,20))
    screen.blit(f_big.render("Memory Vault", True, (255,200,60)), (W//2-200,20))
    if not game_on:
        screen.blit(f_med.render("Press Enter to Start / Esc to Quit", True, (220,220,220)), (W//2 - 200, 90))
    # draw grid
    for i in range(len(cards)):
        draw_card(i)

    screen.blit(f_med.render(f"Moves: {moves}", True, (230,230,230)), (20,20))
    pygame.display.flip()

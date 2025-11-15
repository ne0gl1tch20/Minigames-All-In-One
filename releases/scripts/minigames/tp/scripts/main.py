#!/usr/bin/env python3
# Target Panic - Pygame rapid clicker
import pygame, sys, random, json
from pathlib import Path
from datetime import datetime

APP_NAME = "Target Panic"
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
f_big=pygame.font.SysFont("segoe ui emoji",48)
f_med=pygame.font.SysFont("segoe ui emoji",24)

leaderboard = load_lb()

targets = []  # dicts: x,y,r,ttl
score = 0
spawn_timer = 0.0
round_time = 30.0
game_on=False

def spawn_target():
    r = random.randint(18,36)
    x = random.randint(r+8, W-r-8)
    y = random.randint(r+120, H-r-8)
    ttl = random.uniform(1.0, 2.8)
    targets.append({"x":x,"y":y,"r":r,"ttl":ttl})

def game_over():
    global leaderboard
    try:
        name = input("Time! Enter name for leaderboard: ").strip() or "Player"
    except Exception:
        name = "Player"
    leaderboard.append({"name":name,"score":score,"when":datetime.now().isoformat()})
    leaderboard = sorted(leaderboard, key=lambda x: x["score"], reverse=True)[:20]
    save_lb(leaderboard)

while True:
    dt = clock.tick(60)/1000.0
    for ev in pygame.event.get():
        if ev.type==pygame.QUIT:
            pygame.quit(); sys.exit()
        if ev.type==pygame.KEYDOWN:
            if ev.key==pygame.K_RETURN and not game_on:
                game_on=True; score=0; targets.clear(); round_time=30.0; spawn_timer=0.0
            elif ev.key==pygame.K_ESCAPE:
                pygame.quit(); sys.exit()
        if ev.type==pygame.MOUSEBUTTONDOWN and game_on:
            mx,my = ev.pos
            for t in targets[:]:
                dx = mx - t["x"]; dy = my - t["y"]
                if dx*dx+dy*dy <= t["r"]*t["r"]:
                    score += 1
                    targets.remove(t)
                    break

    if game_on:
        round_time -= dt
        spawn_timer -= dt
        if spawn_timer <= 0:
            spawn_target()
            spawn_timer = max(0.25, 1.0 - score*0.02)  # faster spawns as you score
        # update targets
        for t in targets[:]:
            t["ttl"] -= dt
            if t["ttl"] <= 0:
                targets.remove(t)
        if round_time <= 0:
            game_on=False
            game_over()

    # render
    screen.fill((8,8,20))
    screen.blit(f_big.render("Target Panic", True, (255,200,60)), (W//2-220,20))
    if not game_on:
        screen.blit(f_med.render("Press Enter to Start - Click targets! - Esc to Quit", True, (220,220,220)), (80,120))
    for t in targets:
        pygame.draw.circle(screen, (255,80,80), (t["x"], t["y"]), t["r"])
        pygame.draw.circle(screen, (255,200,200), (t["x"], t["y"]), max(2, t["r"]//2))
    screen.blit(f_med.render(f"Score: {score}", True, (230,230,230)), (20,20))
    screen.blit(f_med.render(f"Time: {round_time:.1f}s", True, (230,230,230)), (20,60))
    pygame.display.flip()

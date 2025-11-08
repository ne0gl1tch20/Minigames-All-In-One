"""
Number Slider Minigame
Features:
- 4x4 sliding puzzle
- Start Menu / Settings / Leaderboard
- Saveable leaderboard (JSON)
- Keyboard support
- Particle effects when moving tiles
- Procedural SFX
- Score based on moves
"""

import pygame, sys, json, os, random, math
from pathlib import Path
from dataclasses import dataclass

# ------------------- CONFIG / SAVE PATH -------------------
USER_DIR = os.path.expandvars(r"%userprofile%")
MG_SAVE_DIR = Path(USER_DIR) / "Documents" / ".mgaio"
APP_NAME = "NumberSlider"
SAVE_FOLDER = MG_SAVE_DIR / "Saves" / APP_NAME
SAVE_FOLDER.mkdir(parents=True, exist_ok=True)

SETTINGS_FILE = SAVE_FOLDER / "settings.json"
LEADERBOARD_FILE = SAVE_FOLDER / "leaderboard.json"

DEFAULT_SETTINGS = {
    "volume": 100,
    "sound": True,
    "keymap": {
        "up": pygame.K_UP,
        "down": pygame.K_DOWN,
        "left": pygame.K_LEFT,
        "right": pygame.K_RIGHT,
        "action": pygame.K_SPACE
    },
}
DEFAULT_LEADERBOARD: list = []


def load_json(path, default):
    if path.exists():
        try:
            return json.load(open(path,"r",encoding="utf-8"))
        except:
            pass
    return default

def save_json(path, data):
    try:
        with open(path,"w",encoding="utf-8") as f:
            json.dump(data,f,ensure_ascii=False,indent=2)
    except Exception as e:
        print("Save failed:", e)

# ------------------- PARTICLE -------------------
@dataclass
class Particle:
    x:float
    y:float
    vx:float
    vy:float
    life:float
    size:float
    color:tuple

# ------------------- MAIN GAME CLASS -------------------
class NumberSlider:
    WIDTH, HEIGHT = 800,600
    FPS = 60
    GRID_SIZE = 4
    TILE_SIZE = 120
    TILE_PADDING = 10

    def __init__(self):
        pygame.init()
        try:
            pygame.mixer.init()
            self.audio_available = True
        except:
            self.audio_available = False

        self.screen = pygame.display.set_mode((self.WIDTH,self.HEIGHT))
        pygame.display.set_caption("Number Slider")
        self.clock = pygame.time.Clock()
        self.font_big = pygame.font.SysFont("arial",48,bold=True)
        self.font_med = pygame.font.SysFont("arial",24)
        self.font_sm = pygame.font.SysFont("arial",18)

        self.settings = load_json(SETTINGS_FILE, DEFAULT_SETTINGS.copy())
        self.leaderboard = load_json(LEADERBOARD_FILE, DEFAULT_LEADERBOARD.copy())

        self.state = "menu"
        self.running = True
        self.grid = []
        self.empty_pos = (self.GRID_SIZE-1,self.GRID_SIZE-1)
        self.tile_colors = {}
        self.moves = 0
        self.particles = []
        self.score = 0
        self.player_name = "Player"
        self.generate_colors()
        self.init_grid()
        self.create_sounds()
        self.apply_volume()

    # ---------- GRID & COLORS ----------
    def generate_colors(self):
        base = 50
        step = int(205 / (self.GRID_SIZE**2))
        for i in range(1, self.GRID_SIZE**2):
            shade = base + i * step
            r = max(0, min(255, shade))
            g = max(0, min(255, 200 - shade))
            b = max(0, min(255, 120 + shade // 3))
            self.tile_colors[i] = (r, g, b)



    def init_grid(self):
        nums = list(range(1,self.GRID_SIZE**2))+[0]
        random.shuffle(nums)
        self.grid = [nums[i*self.GRID_SIZE:(i+1)*self.GRID_SIZE] for i in range(self.GRID_SIZE)]
        for y in range(self.GRID_SIZE):
            for x in range(self.GRID_SIZE):
                if self.grid[y][x]==0:
                    self.empty_pos=(x,y)

    # ---------- SOUND ----------
    def create_sounds(self):
        self.sounds = {}
        if not self.audio_available: return
        sample_rate = 22050
        defs = {"select":(660,0.06),"start":(880,0.12),"action":(1200,0.05),"cancel":(220,0.08)}
        for name,(hz,dur) in defs.items():
            n_samples=int(sample_rate*dur)
            buf=bytearray()
            max_amp=127
            for i in range(n_samples):
                t=i/sample_rate
                env=1.0-i/n_samples
                v=int(max_amp*math.sin(2*math.pi*hz*t)*env)
                buf.append(v+128)
            try: self.sounds[name]=pygame.mixer.Sound(buffer=bytes(buf))
            except: self.sounds[name]=None

    def apply_volume(self):
        vol = self.settings.get("volume",100)/100
        for s in self.sounds.values():
            if s: s.set_volume(vol)

    def play_sound(self,name):
        if not self.audio_available or not self.settings.get("sound",True): return
        s=self.sounds.get(name)
        if s: s.play()

    # ---------- PARTICLES ----------
    def emit_particle(self,x,y,color=(255,200,60)):
        self.particles.append(Particle(x,y,random.uniform(-50,50),random.uniform(-100,-50),0.8,4,color))

    def update_particles(self,dt):
        for p in list(self.particles):
            p.x+=p.vx*dt
            p.y+=p.vy*dt
            p.vy+=200*dt
            p.life-=dt
            if p.life<=0: self.particles.remove(p)

    def render_particles(self):
        for p in self.particles:
            alpha=max(0, min(255,int(255*p.life)))
            surf=pygame.Surface((int(p.size*2),int(p.size*2)),pygame.SRCALPHA)
            pygame.draw.circle(surf,(*p.color,alpha),(int(p.size),int(p.size)),int(p.size))
            self.screen.blit(surf,(int(p.x-p.size),int(p.y-p.size)))

    # ---------- GAME LOGIC ----------
    def move_tile(self,dx,dy):
        ex,ey=self.empty_pos
        nx,ny=ex+dx,ey+dy
        if 0<=nx<self.GRID_SIZE and 0<=ny<self.GRID_SIZE:
            self.grid[ey][ex],self.grid[ny][nx]=self.grid[ny][nx],self.grid[ey][ex]
            self.empty_pos=(nx,ny)
            self.moves+=1
            self.play_sound("action")
            self.emit_particle(nx*self.TILE_SIZE+60,ny*self.TILE_SIZE+60)
            if self.check_solved():
                self.state="gameover"
                self.save_score()

    def check_solved(self):
        n=1
        for y in range(self.GRID_SIZE):
            for x in range(self.GRID_SIZE):
                if y==self.GRID_SIZE-1 and x==self.GRID_SIZE-1:
                    return self.grid[y][x]==0
                if self.grid[y][x]!=n: return False
                n+=1
        return True

    def save_score(self):
        score=max(0,1000-self.moves*5)
        self.leaderboard.append({"name":self.player_name,"score":score})
        self.leaderboard=sorted(self.leaderboard,key=lambda x:x["score"],reverse=True)
        save_json(LEADERBOARD_FILE,self.leaderboard)

    # ---------- INPUT ----------
    def handle_input(self,key):
        km=self.settings["keymap"]
        if key==km["up"]: self.move_tile(0,1)
        elif key==km["down"]: self.move_tile(0,-1)
        elif key==km["left"]: self.move_tile(1,0)
        elif key==km["right"]: self.move_tile(-1,0)

    # ---------- DRAW ----------
    def draw_game(self):
        self.screen.fill((12,12,12))
        # tiles
        start_x=(self.WIDTH-(self.TILE_SIZE*self.GRID_SIZE+self.TILE_PADDING*(self.GRID_SIZE-1)))//2
        start_y=(self.HEIGHT-(self.TILE_SIZE*self.GRID_SIZE+self.TILE_PADDING*(self.GRID_SIZE-1)))//2
        for y in range(self.GRID_SIZE):
            for x in range(self.GRID_SIZE):
                num=self.grid[y][x]
                rect=pygame.Rect(start_x+x*(self.TILE_SIZE+self.TILE_PADDING),start_y+y*(self.TILE_SIZE+self.TILE_PADDING),self.TILE_SIZE,self.TILE_SIZE)
                if num!=0:
                    color=self.tile_colors.get(num,(200,200,200))
                    pygame.draw.rect(self.screen,color,rect,border_radius=8)
                    text=self.font_big.render(str(num),True,(0,0,0))
                    self.screen.blit(text,(rect.x+rect.width//2-text.get_width()//2,rect.y+rect.height//2-text.get_height()//2))
        # moves
        moves_text=self.font_med.render(f"Moves: {self.moves}",True,(255,255,255))
        self.screen.blit(moves_text,(20,50))

    def draw_menu(self):
        self.screen.fill((12,12,12))
        title=self.font_big.render("Number Slider",True,(255,200,60))
        self.screen.blit(title,(self.WIDTH//2-title.get_width()//2,80))
        info=self.font_med.render("Enter=Start    S=Settings    L=Leaderboard",True,(200,200,200))
        self.screen.blit(info,(self.WIDTH//2-info.get_width()//2,170))

    def draw_settings(self):
        self.screen.fill((12,12,12))
        title=self.font_big.render("Settings",True,(255,200,60))
        self.screen.blit(title,(48,36))
        txt1=self.font_med.render(f"Sound: {'On' if self.settings.get('sound',True) else 'Off'} (SPACE to toggle)",True,(255,255,255))
        txt2=self.font_med.render(f"Volume: {self.settings.get('volume',100)} (Up/Down)",True,(255,255,255))
        txt3=self.font_sm.render("ESC = Back to Menu",True,(180,180,180))
        self.screen.blit(txt1,(48,140))
        self.screen.blit(txt2,(48,190))
        self.screen.blit(txt3,(48,260))

    def draw_leaderboard(self):
        self.screen.fill((12,12,12))
        title=self.font_big.render("Leaderboard",True,(255,200,60))
        self.screen.blit(title,(48,36))
        y=120
        for i,entry in enumerate(sorted(self.leaderboard,key=lambda x:x.get('score',0),reverse=True)[:10],start=1):
            line=self.font_med.render(f"{i}. {entry.get('name','Player')} — {entry.get('score',0)}",True,(230,230,230))
            self.screen.blit(line,(68,y))
            y+=36
        hint=self.font_sm.render("ESC = Back to Menu",True,(180,180,180))
        self.screen.blit(hint,(48,self.HEIGHT-48))

    def draw_gameover(self):
        self.draw_game()
        overlay = pygame.Surface((self.WIDTH,self.HEIGHT),pygame.SRCALPHA)
        overlay.fill((0,0,0,180))
        self.screen.blit(overlay,(0,0))
        txt=self.font_big.render("Solved!",True,(255,255,100))
        self.screen.blit(txt,(self.WIDTH//2-txt.get_width()//2,self.HEIGHT//2-50))
        txt2=self.font_med.render(f"Moves: {self.moves}",True,(255,255,255))
        self.screen.blit(txt2,(self.WIDTH//2-txt2.get_width()//2,self.HEIGHT//2+10))
        txt3=self.font_sm.render("Press Enter to return to Menu",True,(200,200,200))
        self.screen.blit(txt3,(self.WIDTH//2-txt3.get_width()//2,self.HEIGHT//2+50))

    # ---------- START ----------
    def start_play(self):
        self.state="playing"
        self.moves=0
        self.init_grid()

    # ---------- MAIN LOOP ----------
    def run(self):
        while self.running:
            dt=self.clock.tick(self.FPS)/1000
            for event in pygame.event.get():
                if event.type==pygame.QUIT: self.running=False
                elif event.type==pygame.KEYDOWN:
                    if event.key==pygame.K_ESCAPE:
                        if self.state in ("settings","leaderboard","gameover"): self.state="menu"
                        elif self.state=="playing": self.state="menu"
                        else: self.running=False
                    elif self.state=="menu":
                        if event.key in (pygame.K_RETURN,pygame.K_KP_ENTER): self.play_sound("start");self.start_play()
                        elif event.key==pygame.K_s: self.play_sound("select");self.state="settings"
                        elif event.key==pygame.K_l: self.play_sound("select");self.state="leaderboard"
                    elif self.state=="settings":
                        if event.key==pygame.K_SPACE: self.settings["sound"]=not self.settings.get("sound",True);save_json(SETTINGS_FILE,self.settings);self.play_sound("select" if self.settings["sound"] else "cancel")
                        elif event.key==pygame.K_UP: self.settings["volume"]=min(100,self.settings.get("volume",100)+5);self.apply_volume();save_json(SETTINGS_FILE,self.settings);self.play_sound("select")
                        elif event.key==pygame.K_DOWN: self.settings["volume"]=max(0,self.settings.get("volume",100)-5);self.apply_volume();save_json(SETTINGS_FILE,self.settings);self.play_sound("select")
                    elif self.state=="playing":
                        self.handle_input(event.key)
                    elif self.state=="gameover" and event.key in (pygame.K_RETURN,pygame.K_KP_ENTER):
                        self.state="menu"

            if self.state=="playing":
                self.update_particles(dt)

            # RENDER
            if self.state=="menu": self.draw_menu()
            elif self.state=="settings": self.draw_settings()
            elif self.state=="leaderboard": self.draw_leaderboard()
            elif self.state=="playing": self.draw_game()
            elif self.state=="gameover": self.draw_gameover()

            self.render_particles()
            pygame.display.flip()
        pygame.quit()
        sys.exit()

# ------------------- RUN -------------------
if __name__=="__main__":
    NumberSlider().run()

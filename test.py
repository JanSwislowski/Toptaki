"""
Pygame Image Selector — Mobile Edition
────────────────────────────────────────
Pure pygame, no tkinter. Designed for touchscreens.

Views
  BROWSE  — full-screen folder/file list
  IMAGES  — full-screen thumbnail grid

Bottom nav bar
  [ 📁 Browse ]  [ 🖼 Images ]  [ ✓ Confirm ]  [ ✕ Clear ]

Gestures
  Swipe up/down  — scroll
  Tap            — select / navigate
  Long-press     — toggle multi-select (grid)
  Mouse wheel    — scroll (desktop testing)

pip install pygame Pillow
"""

import sys
import math
import threading
import time
from pathlib import Path
import pygame

try:
    from PIL import Image as PILImage
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

# ── Palette ───────────────────────────────────────────────────────────────────
BG        = ( 12,  12,  16)
PANEL     = ( 22,  22,  30)
CARD      = ( 34,  34,  44)
ACCENT    = ( 60, 210, 150)
ACCENT_D  = ( 36, 130,  90)
TEXT_HI   = (238, 238, 244)
TEXT_MID  = (155, 155, 170)
TEXT_LO   = ( 85,  85, 105)
SEP       = ( 38,  38,  52)
MULTI_COL = ( 80, 210, 120)
DIR_COL   = (255, 200,  60)
IMG_COL   = ( 90, 175, 255)

SUPPORTED = {'.jpg','.jpeg','.png','.bmp','.gif',
             '.webp','.tiff','.tif','.ico'}

NAV_H    = 64
CORNER   = 10
LONG_MS  = 450


# ── Helpers ───────────────────────────────────────────────────────────────────
def rr(surf, col, rect, r=CORNER, width=0):
    pygame.draw.rect(surf, col, rect, border_radius=r, width=width)

def txt(surf, s, font, col, x, y, maxw=None, align='left'):
    if maxw:
        while font.size(s)[0] > maxw and len(s) > 3:
            s = s[:-4] + '…'
    ts = font.render(s, True, col)
    if align == 'center': x -= ts.get_width() // 2
    elif align == 'right': x -= ts.get_width()
    surf.blit(ts, (x, y))
    return ts.get_width()

def lerp_col(a, b, t):
    return tuple(int(a[i]+(b[i]-a[i])*t) for i in range(3))

def fmt_size(b):
    if b < 1024: return f'{b} B'
    if b < 1_048_576: return f'{b/1024:.1f} KB'
    return f'{b/1_048_576:.1f} MB'

def pdist(a, b):
    return math.hypot(a[0]-b[0], a[1]-b[1])


# ── Thumbnail cache ───────────────────────────────────────────────────────────
class ThumbCache:
    def __init__(self, size):
        self.size = size
        self._cache: dict = {}
        self._pending: set = set()
        self._lock = threading.Lock()

    def request(self, path: Path):
        with self._lock:
            if path in self._cache or path in self._pending: return
            self._pending.add(path)
        threading.Thread(target=self._load, args=(path,), daemon=True).start()

    def _load(self, path: Path):
        size = self.size
        try:
            if HAS_PIL:
                img = PILImage.open(path).convert('RGBA')
                img.thumbnail((size, size), PILImage.LANCZOS)
                sq = PILImage.new('RGBA', (size, size), (0,0,0,0))
                sq.paste(img, ((size-img.width)//2, (size-img.height)//2))
                surf = pygame.image.fromstring(sq.tobytes(), (size,size), 'RGBA')
            else:
                raw = pygame.image.load(str(path)).convert_alpha()
                w, h = raw.get_size()
                sc = size / max(w, h)
                nw, nh = int(w*sc), int(h*sc)
                raw = pygame.transform.smoothscale(raw, (nw, nh))
                sq = pygame.Surface((size,size), pygame.SRCALPHA)
                sq.blit(raw, ((size-nw)//2, (size-nh)//2))
                surf = sq
        except Exception:
            surf = None
        with self._lock:
            self._cache[path] = surf
            self._pending.discard(path)

    def get(self, path):
        with self._lock: return self._cache.get(path)


# ── Folder browser view ───────────────────────────────────────────────────────
class BrowserView:
    def __init__(self, start: Path):
        self.cwd    = start
        self.entries: list = []
        self.scroll = 0.0
        self._vel   = 0.0
        self._refresh()

    def _refresh(self):
        self.entries = []
        parent = self.cwd.parent
        if parent != self.cwd:
            self.entries.append(('..  (up)', parent, True))
        try:
            items = sorted(self.cwd.iterdir(),
                           key=lambda p: (not p.is_dir(), p.name.lower()))
            for p in items:
                if p.name.startswith('.'): continue
                if p.is_dir():
                    self.entries.append((p.name, p, True))
                elif p.suffix.lower() in SUPPORTED:
                    self.entries.append((p.name, p, False))
        except PermissionError:
            pass
        self.scroll = 0.0
        self._vel   = 0.0

    def navigate(self, path: Path):
        self.cwd = path
        self._refresh()

    def up(self):
        self.navigate(self.cwd.parent)

    def _row_h(self, W): return max(54, W // 7)
    def _total_h(self, W): return len(self.entries) * self._row_h(W)

    def update(self, W, H):
        body_h  = H - NAV_H
        max_s   = max(0, self._total_h(W) - body_h)
        self._vel   *= 0.88
        self.scroll  = max(0, min(self.scroll + self._vel, max_s))

    def draw(self, surf, W, H, f_sm, f_md):
        surf.fill(BG)
        row_h  = self._row_h(W)
        body_h = H - NAV_H

        # header bar
        pygame.draw.rect(surf, PANEL, pygame.Rect(0, 0, W, 44))
        pygame.draw.line(surf, SEP, (0, 44), (W, 44), 1)
        txt(surf, str(self.cwd), f_sm, ACCENT, 12, 13, maxw=W-24)

        for i, (label, path, is_dir) in enumerate(self.entries):
            ry = 48 + i * row_h - int(self.scroll)
            if ry + row_h < 0 or ry > body_h: continue
            row_rect = pygame.Rect(8, ry+3, W-16, row_h-6)
            rr(surf, CARD, row_rect, 8)
            marker = '/' if is_dir else '·'
            col    = DIR_COL if is_dir else IMG_COL
            txt(surf, marker, f_md, col, 22, ry + row_h//2 - 10)
            txt(surf, label, f_md if is_dir else f_sm,
                TEXT_HI if is_dir else TEXT_MID,
                52, ry + row_h//2 - 10, maxw=W-68)

        # scrollbar
        th = self._total_h(W)
        if th > body_h:
            bh = max(30, (body_h-48) * (body_h-48) // th)
            by = 48 + int(self.scroll / max(1, th-(body_h-48)) * ((body_h-48)-bh))
            pygame.draw.rect(surf, SEP, pygame.Rect(W-4, by, 3, bh), border_radius=2)

    def tap(self, x, y, W, H):
        row_h  = self._row_h(W)
        body_h = H - NAV_H
        for i, (label, path, is_dir) in enumerate(self.entries):
            ry = 48 + i * row_h - int(self.scroll)
            if pygame.Rect(0, ry, W, row_h).collidepoint(x, y):
                if is_dir:
                    self.navigate(path)
                    return ('dir', path)
                else:
                    return ('img', path)
        return None

    def kick(self, dy): self._vel = -dy * 1.4


# ── Grid view ─────────────────────────────────────────────────────────────────
class GridView:
    def __init__(self, cache: ThumbCache):
        self.cache    = cache
        self.images   : list = []
        self.selected : int  = -1
        self.multi    : set  = set()
        self.scroll   = 0.0
        self._vel     = 0.0

    def load(self, path: Path):
        try:
            self.images = sorted(
                [p for p in path.iterdir()
                 if p.is_file() and p.suffix.lower() in SUPPORTED],
                key=lambda p: p.name.lower())
        except PermissionError:
            self.images = []
        self.selected = -1
        self.multi.clear()
        self.scroll = 0.0
        self._vel   = 0.0

    def _cols(self, W): return max(2, W // 170)

    def _thumb_sz(self, W):
        c = self._cols(W)
        return (W - 8*(c+1)) // c

    def _cell(self, i, W):
        c   = self._cols(W)
        ts  = self._thumb_sz(W)
        pad = (W - c*ts) // (c+1)
        row, col = divmod(i, c)
        x = pad + col*(ts+pad)
        y = 8 + row*(ts+pad) - int(self.scroll)
        return pygame.Rect(x, y, ts, ts)

    def _total_h(self, W):
        if not self.images: return 0
        c   = self._cols(W)
        ts  = self._thumb_sz(W)
        pad = (W - c*ts) // (c+1)
        rows = math.ceil(len(self.images)/c)
        return rows*(ts+pad) + 8

    def _idx_at(self, x, y, W):
        for i in range(len(self.images)):
            if self._cell(i, W).collidepoint(x, y): return i
        return -1

    def update(self, W, H):
        body_h = H - NAV_H
        max_s  = max(0, self._total_h(W) - body_h)
        self._vel  *= 0.88
        self.scroll = max(0, min(self.scroll + self._vel, max_s))

    def draw(self, surf, W, H, f_sm, f_md):
        surf.fill(BG)
        body_h = H - NAV_H
        t = pygame.time.get_ticks() / 1000.0

        if not self.images:
            txt(surf, 'No images here', f_md, TEXT_LO, W//2, H//3, align='center')
            txt(surf, 'Go to Browse tab', f_sm, TEXT_LO, W//2, H//3+30, align='center')
            return

        for i, path in enumerate(self.images):
            cell = self._cell(i, W)
            if cell.bottom < 0 or cell.top > body_h: continue
            self.cache.request(path)

            is_sel   = i == self.selected
            is_multi = i in self.multi

            rr(surf, CARD, cell, 8)

            thumb = self.cache.get(path)
            if thumb:
                # scale thumb to fill cell
                ts = self._thumb_sz(W)
                if thumb.get_width() != ts or thumb.get_height() != ts:
                    thumb = pygame.transform.smoothscale(thumb, (ts, ts))
                surf.blit(thumb, cell.topleft)
            else:
                rr(surf, (28,28,38), cell, 8)
                txt(surf, '…', f_sm, TEXT_LO, cell.centerx-5, cell.centery-8)

            # selection ring
            if is_multi:
                rr(surf, MULTI_COL, cell.inflate(5,5), 9, width=3)
                br = pygame.Rect(cell.right-28, cell.top+4, 24, 24)
                rr(surf, MULTI_COL, br, 12)
                txt(surf, '✓', f_sm, BG, br.x+5, br.y+4)
            elif is_sel:
                p = 0.5 + 0.5*math.sin(t*4)
                rr(surf, lerp_col(ACCENT_D, ACCENT, p),
                   cell.inflate(5,5), 9, width=3)

        # status strip
        pygame.draw.rect(surf, (0,0,0), pygame.Rect(0,0,W,30))
        ns = len(self.multi) if self.multi else (1 if self.selected>=0 else 0)
        txt(surf, f'{len(self.images)} images', f_sm, TEXT_LO, 10, 8)
        if ns:
            txt(surf, f'{ns} selected', f_sm, ACCENT, W-10, 8, align='right')

        # scrollbar
        th = self._total_h(W)
        if th > body_h:
            bh = max(30, body_h*body_h//th)
            by = int(self.scroll/max(1,th-body_h)*(body_h-bh))
            pygame.draw.rect(surf, SEP, pygame.Rect(W-4, by, 3, bh), border_radius=2)

    def tap(self, x, y, W): return self._idx_at(x, y, W)
    def long_press(self, x, y, W):
        idx = self._idx_at(x, y, W)
        if idx >= 0: self.multi ^= {idx}
        return idx
    def kick(self, dy): self._vel = -dy * 1.4


# ── Nav bar ───────────────────────────────────────────────────────────────────
class NavBar:
    TABS = [('/', 'Browse'), ('*', 'Images'), ('+', 'Confirm'), ('x', 'Clear')]

    def draw(self, surf, W, H, active, f_sm, f_md, multi_n):
        bar = pygame.Rect(0, H-NAV_H, W, NAV_H)
        pygame.draw.rect(surf, PANEL, bar)
        pygame.draw.line(surf, SEP, (0, H-NAV_H), (W, H-NAV_H), 1)
        bw = W // len(self.TABS)
        for i, (icon, label) in enumerate(self.TABS):
            bx = i * bw
            is_act = label == active
            rr(surf, CARD if is_act else PANEL,
               pygame.Rect(bx+3, H-NAV_H+4, bw-6, NAV_H-8), 8)
            if is_act:
                pygame.draw.rect(surf, ACCENT,
                                 pygame.Rect(bx+3, H-NAV_H+4, bw-6, 3),
                                 border_radius=3)
            col   = ACCENT if is_act else TEXT_LO
            disp  = f'{label} ({multi_n})' if label=='Confirm' and multi_n else label
            txt(surf, disp, f_sm, col, bx+bw//2, H-NAV_H+22, align='center')

    def tap(self, x, y, W, H):
        if y < H - NAV_H: return None
        bw = W // len(self.TABS)
        i  = min(x // bw, len(self.TABS)-1)
        return self.TABS[i][1]


# ── Main app ──────────────────────────────────────────────────────────────────
class App:
    def __init__(self, start_dir=None):
        pygame.init()
        info = pygame.display.Info()
        self.W, self.H = info.current_w, info.current_h

        # Portrait window on desktop for testing
        if self.W > 600:
            self.W, self.H = 420, 820

        self.screen = pygame.display.set_mode(
            (self.W, self.H), pygame.RESIZABLE | pygame.SCALED)
        pygame.display.set_caption('Image Selector')

        self._init_fonts()

        # Find a valid start directory
        candidates = [
            start_dir,
            '/sdcard/DCIM/Camera',
            '/sdcard/DCIM',
            '/sdcard/Pictures',
            '/storage/emulated/0/DCIM',
            str(Path.home()),
        ]
        init = Path.home()
        for c in candidates:
            if c and Path(c).exists():
                init = Path(c); break

        thumb_sz   = max(100, self.W // 3)
        self.cache  = ThumbCache(thumb_sz)
        self.browser = BrowserView(init)
        self.grid    = GridView(self.cache)
        self.grid.load(init)
        self.navbar  = NavBar()

        self.tab     = 'Images'
        self.running = True
        self.confirmed: list = []
        self.clock   = pygame.time.Clock()

        # Touch / drag state
        self._fingers: dict  = {}   # fid -> (start_x, start_y, start_t, last_y)
        self._lp_timer       = None  # (x, y, t)

    def _init_fonts(self):
        fs = max(13, self.W // 30)
        self.f_sm = pygame.font.SysFont('monospace', fs)
        self.f_md = pygame.font.SysFont('monospace', fs+3, bold=True)

    # ── touch ─────────────────────────────────────────────────────────────────
    def _fdown(self, fid, x, y):
        self._fingers[fid] = (x, y, time.time(), y)
        if len(self._fingers) == 1:
            self._lp_timer = (x, y, time.time())

    def _fmove(self, fid, x, y):
        if fid not in self._fingers: return
        sx, sy, st, ly = self._fingers[fid]
        dy = y - ly
        self._fingers[fid] = (sx, sy, st, y)

        # cancel long press on movement
        if self._lp_timer:
            lx, _ly, _ = self._lp_timer
            if pdist((lx,_ly),(x,y)) > 12:
                self._lp_timer = None

        # live scroll
        if self.tab == 'Browse':
            self.browser.kick(dy)
        elif self.tab == 'Images':
            self.grid.kick(dy)

    def _fup(self, fid, x, y):
        if fid not in self._fingers: return
        sx, sy, st, ly = self._fingers.pop(fid)
        self._lp_timer = None

        moved = pdist((sx,sy),(x,y))
        dt    = time.time() - st
        is_tap  = moved < 20 and dt < 0.35
        is_long = moved < 20 and dt >= LONG_MS/1000

        if is_tap:   self._on_tap(sx, sy)
        elif is_long: self._on_long(sx, sy)

    def _on_tap(self, x, y):
        W, H = self.W, self.H
        nav = self.navbar.tap(x, y, W, H)
        if nav:
            if nav == 'Browse':   self.tab = 'Browse'
            elif nav == 'Images': self.tab = 'Images'
            elif nav == 'Confirm': self._confirm()
            elif nav == 'Clear':
                self.grid.multi.clear()
                self.grid.selected = -1
            return

        if self.tab == 'Browse':
            result = self.browser.tap(x, y, W, H)
            if result and result[0] == 'img':
                p = result[1]
                self.grid.load(p.parent)
                try: self.grid.selected = self.grid.images.index(p)
                except ValueError: pass
                self.tab = 'Images'

        elif self.tab == 'Images':
            idx = self.grid.tap(x, y, W)
            if idx >= 0:
                if self.grid.multi:
                    self.grid.multi ^= {idx}
                else:
                    self.grid.selected = idx

    def _on_long(self, x, y):
        if self.tab == 'Images' and y < self.H - NAV_H:
            self.grid.long_press(x, y, self.W)

    def _confirm(self):
        imgs  = self.grid.images
        multi = self.grid.multi
        sel   = self.grid.selected
        self.confirmed = (
            [imgs[i] for i in sorted(multi)] if multi else
            ([imgs[sel]] if 0 <= sel < len(imgs) else []))
        self.running = False

    # ── events ────────────────────────────────────────────────────────────────
    def _events(self):
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                self.running = False; return

            elif ev.type == pygame.VIDEORESIZE:
                self.W, self.H = ev.w, ev.h
                self.screen = pygame.display.set_mode(
                    (self.W, self.H), pygame.RESIZABLE | pygame.SCALED)
                self._init_fonts()

            # touch
            elif ev.type == pygame.FINGERDOWN:
                self._fdown(ev.finger_id,
                            int(ev.x*self.W), int(ev.y*self.H))
            elif ev.type == pygame.FINGERMOTION:
                self._fmove(ev.finger_id,
                            int(ev.x*self.W), int(ev.y*self.H))
            elif ev.type == pygame.FINGERUP:
                self._fup(ev.finger_id,
                          int(ev.x*self.W), int(ev.y*self.H))

            # mouse (desktop fallback)
            elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                self._fdown(0, *ev.pos)
            elif ev.type == pygame.MOUSEMOTION and pygame.mouse.get_pressed()[0]:
                self._fmove(0, *ev.pos)
            elif ev.type == pygame.MOUSEBUTTONUP and ev.button == 1:
                self._fup(0, *ev.pos)
            elif ev.type == pygame.MOUSEWHEEL:
                dy = ev.y * 50
                if self.tab == 'Browse': self.browser._vel = -dy
                else: self.grid._vel = -dy

            elif ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    self.grid.multi.clear(); self.grid.selected = -1
                elif ev.key == pygame.K_BACKSPACE:
                    self.browser.up(); self.grid.load(self.browser.cwd)

        # long-press polling
        if self._lp_timer:
            lx, ly, lt = self._lp_timer
            if time.time()-lt >= LONG_MS/1000:
                self._lp_timer = None
                self._on_long(lx, ly)

    # ── main loop ─────────────────────────────────────────────────────────────
    def run(self) -> list:
        while self.running:
            self._events()
            W, H = self.W, self.H

            self.browser.update(W, H)
            self.grid.update(W, H)

            if self.tab == 'Browse':
                self.browser.draw(self.screen, W, H, self.f_sm, self.f_md)
            else:
                self.grid.draw(self.screen, W, H, self.f_sm, self.f_md)

            self.navbar.draw(self.screen, W, H, self.tab,
                             self.f_sm, self.f_md, len(self.grid.multi))

            pygame.display.flip()
            self.clock.tick(60)

        pygame.quit()
        return self.confirmed


# ─────────────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    start = sys.argv[1] if len(sys.argv) > 1 else None
    chosen = App(start_dir=start).run()
    if chosen:
        print('Selected:')
        for p in chosen: print(' ', p)
    else:
        print('Nothing selected.')
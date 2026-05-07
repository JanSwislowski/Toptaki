import os
import pygame
import numpy as np
ID_FILE = "ids.txt"
tokens={}
ids={}
def load_ids():
     with open(ID_FILE, "r") as f:
        for line in f:
            username, id = line.strip().split(":")
            ids[username] = int(id)
def save_ids():
    with open(ID_FILE, "w") as f:
        for username, id in ids.items():
            f.write(f"{username}:{id}\n")

def add_paths(id):
    path=f"C:/Users/Jasiek/PycharmProjects/topoptaki3/users/{id}"
    os.makedirs(path, exist_ok=True)
    path=f"C:/Users/Jasiek/PycharmProjects/topoptaki3/users/{id}/images"
    os.makedirs(path, exist_ok=True)
    path=f"C:/Users/Jasiek/PycharmProjects/topoptaki3/users/{id}/info.txt"
    open(path,"w").close()

def add_info(id,username,password):
    path=f"C:/Users/Jasiek/PycharmProjects/topoptaki3/users/{id}/info.txt"
    with open(path, "w") as f:
        f.write(f"Username:{username}\n")
        f.write(f"Password:{password}\n")
def add_user(username, password):
    cur_id=len(ids)+1
    ids[username]=cur_id
    print(cur_id)
    add_paths(cur_id)
    add_info(cur_id,username,password)
def check_login(username, password):
    if username not in ids:
        return False
    id=ids[username]
    path=f"C:/Users/Jasiek/PycharmProjects/topoptaki3/users/{id}/info.txt"
    with open(path, "r") as f:
        lines=f.readlines()
        stored_password=lines[1].strip().split(":")[1]
        return stored_password==password
def upload_image(token, filename):
    if token not in tokens:
        return False
    username=tokens[token]
    id=ids[username]
    save_path=f"C:/Users/Jasiek/PycharmProjects/topoptaki3/users/{id}/images/{filename}"
    return save_path

from assets import ComentSection
def generate_coment_section(comments: list[dict],width, height):
    c=ComentSection(width, height)
    for comment in comments:
        c.add_comment(user=comment["user"], text=comment["text"])
    return c


def fade_surfaces(surface1: pygame.Surface, surface2: pygame.Surface, ratio: float) -> pygame.Surface:
    ratio = max(0.0, min(1.0, ratio))

    arr1 = pygame.surfarray.array3d(surface1).astype(np.float32)
    arr2 = pygame.surfarray.array3d(surface2).astype(np.float32)

    blended = ((arr1 * (1.0 - ratio)) + (arr2 * ratio)).astype(np.uint8)

    return pygame.surfarray.make_surface(blended)
def darken_rgb(color, factor):
    r = max(0, min(255, int(color[0] * factor)))
    g = max(0, min(255, int(color[1] * factor)))
    b = max(0, min(255, int(color[2] * factor)))
    return (r, g, b)
def get_color_leaderboard(i):
    if i==0:
        color=(255,215,0) #gold
    elif i==1:
        color=(192,192,192) #silver
    elif i==2:
        color=(205,127,50) #bronze
    else:
        color=(100,100,100)
    return color

def scale_rect(rect:pygame.Rect,dx,dy,dw,dh):
    return pygame.Rect(rect.x-dx,rect.y-dy,rect.w+dw+dx,rect.h+dh+dy)
def normalise_scroll(scroll, content_height, view_height):
    if content_height <= view_height:
        return 0
    max_scroll = content_height - view_height
    return max(0, min(scroll, max_scroll))
def cords_to_str(cords):
    return f"N{cords[0][0]}°{cords[0][1]}',E{cords[1][0]}°{cords[1][1]}"
def scale_surface_proportionally(img, max_width, max_height):
    width, height = img.get_size()
    ratio = min(max_width / width, max_height / height)
    new_size = (int(width * ratio), int(height * ratio))
    return pygame.transform.smoothscale(img, new_size)

def create_gradient_numpy(width, height, direction='bottom',
                          color=(0, 0, 0), max_alpha=180, strength=1.0):
    """
    strength < 1.0  → gentle, slow buildup  (e.g. 0.5)
    strength = 1.0  → natural smootherstep
    strength > 1.0  → fast, aggressive fade that still merges cleanly (e.g. 2.0)
    """
    surface = pygame.Surface((width, height), pygame.SRCALPHA)

    size = height if direction in ('bottom', 'top') else width
    t = np.linspace(0.0, 1.0, size)

    if direction in ('top', 'left'):
        t = 1.0 - t

    # shift t by strength, then re-normalize to [0, 1] so it always
    # starts at 0 alpha and ends at max_alpha cleanly
    t_shaped = np.power(t, 1.0 / strength)   # bias the input
    t_smooth = t_shaped * t_shaped * t_shaped * (t_shaped * (t_shaped * 6 - 15) + 10)  # smootherstep

    gradient = (t_smooth * max_alpha).astype(np.uint8)

    arr = pygame.surfarray.pixels_alpha(surface)
    if direction in ('bottom', 'top'):
        arr[:] = gradient[np.newaxis, :]
    else:
        arr[:] = gradient[:, np.newaxis]
    del arr

    rgb_arr = pygame.surfarray.pixels3d(surface)
    rgb_arr[:] = color
    del rgb_arr
    return surface
def create_fade_mask(width, height, direction='right', strength=1.0):
    surface = pygame.Surface((width, height), pygame.SRCALPHA)
    surface.fill((255, 255, 255, 255))  # white, fully opaque — RGB won't affect MULT blend
    size = height if direction in ('top', 'bottom') else width

    t = np.linspace(0.0, 1.0, size)
    if direction in ('bottom', 'right'):
        t = 1.0 - t

    t = np.power(np.clip(t, 0, 1), 1.0 / strength)
    gradient = (t**3 * (t * (t * 6 - 15) + 10) * 255).astype(np.uint8)

    arr = pygame.surfarray.pixels_alpha(surface)
    arr[:] = gradient[np.newaxis, :] if direction in ('top', 'bottom') else gradient[:, np.newaxis]
    del arr

    return surface
def twodistance(cord1, cord2):
    lat1, lon1 = cord1
    lat2, lon2 = cord2
    return ((lat2 - lat1) ** 2 + (lon2 - lon1) ** 2) ** 0.5
def twodistance_sq(cord1, cord2):
    lat1, lon1 = cord1
    lat2, lon2 = cord2
    return (lat2 - lat1) ** 2 + (lon2 - lon1) ** 2


# ── tuneable constants ────────────────────────────────────────────────────────
WAVE_AMPLITUDE = 40  # max horizontal pixel displacement
WAVE_FREQUENCY = 2.0  # full sine cycles visible across the height
WAVE_SPEED = 0.01  # phase speed (radians per second)
EDGE_SOFTNESS = 0.08
def wave_transition(
        surface_from: pygame.Surface,
        surface_to: pygame.Surface,
        duration: float,
        elapsed: float,) -> pygame.Surface:
    global WAVE_AMPLITUDE, WAVE_FREQUENCY, WAVE_SPEED, EDGE_SOFTNESS
    """Return a single composited frame of the wave transition.

    The transition sweeps a distorted, feathered wave front from left to right.
    Everything left of the front shows *surface_to*; everything right shows
    *surface_from*.  Both sides are distorted near the boundary for a liquid feel.

    The function is stateless – call it every frame, passing the current elapsed
    time.  No surface modification of the inputs occurs.
    """
    elapsed = max(0.0, min(elapsed, duration))
    t = elapsed / duration  # 0 → 1, linear progress
    w, h = surface_from.get_size()

    # ── pixel arrays (read-only views, no copy) ───────────────────────────────
    arr_from = pygame.surfarray.pixels3d(surface_from)  # shape (w, h, 3)
    arr_to = pygame.surfarray.pixels3d(surface_to)

    # ── per-row sine offsets (pre-computed once per frame) ────────────────────
    rows = np.arange(h, dtype=np.float32)
    phase = elapsed * WAVE_SPEED
    offsets = (AMPLITUDE_ENVELOPE(t) * WAVE_AMPLITUDE
               * np.sin(2.0 * np.pi * WAVE_FREQUENCY * rows / h + phase)
               ).astype(np.int32)  # shape (h,)

    # ── wave-front x-position for every row ──────────────────────────────────
    # Base front moves from -amplitude to w+amplitude so it fully sweeps.
    base_x = int(t * (w + 2 * WAVE_AMPLITUDE)) - WAVE_AMPLITUDE
    front_x = np.clip(base_x + offsets, 0, w)  # shape (h,)

    # ── build output array (w, h, 3) ─────────────────────────────────────────
    out = np.empty((w, h, 3), dtype=np.uint8)

    # Column indices broadcast with row front positions
    col_idx = np.arange(w, dtype=np.int32)[:, np.newaxis]  # (w, 1)
    row_front = front_x[np.newaxis, :]  # (1, h)

    # Boolean masks
    to_mask = col_idx < row_front  # (w, h) – show surface_to
    from_mask = col_idx >= row_front  # (w, h) – show surface_from

    # --- base fill (non-boundary pixels) -------------------------------------
    out[to_mask] = arr_to[to_mask]
    out[from_mask] = arr_from[from_mask]

    # --- feathered blend near the wave front ---------------------------------
    feather_px = max(1, int(EDGE_SOFTNESS * w))
    lo = row_front - feather_px  # (1, h)
    hi = row_front + feather_px

    # Pixels inside the feather band
    in_band = (col_idx >= lo) & (col_idx <= hi)  # (w, h)

    if in_band.any():
        alpha_to = ((col_idx - lo) / (hi - lo + 1e-6))  # 0 → 1 towards "to"
        alpha_to = np.clip(alpha_to, 0.0, 1.0)
        alpha_fr = 1.0 - alpha_to

        # Only compute blend for band pixels (saves time on full array mult)
        band_cols, band_rows = np.where(in_band)

        a_to = alpha_to[band_cols, band_rows, np.newaxis]
        a_fr = alpha_fr[band_cols, band_rows, np.newaxis]

        src_to = arr_to[band_cols, band_rows].astype(np.float32)
        src_fr = arr_from[band_cols, band_rows].astype(np.float32)

        out[band_cols, band_rows] = np.clip(
            a_to * src_to + a_fr * src_fr, 0, 255
        ).astype(np.uint8)

    # ── distort the "to" side near the front (ripple effect) -----------------
    ripple_px = feather_px * 3
    ripple_lo = np.maximum(row_front - ripple_px, 0)
    ripple_hi = row_front  # only left side

    in_ripple = (col_idx >= ripple_lo) & (col_idx < ripple_hi) & (~in_band)

    if in_ripple.any():
        rc, rr = np.where(in_ripple)
        dist_ratio = 1.0 - (row_front[0, rr] - rc) / (ripple_px + 1e-6)
        displacement = (
                dist_ratio * 12
                * np.sin(2.0 * np.pi * rr / h * WAVE_FREQUENCY * 2 + phase * 1.5)
        ).astype(np.int32)

        src_cols = np.clip(rc + displacement, 0, w - 1)
        out[rc, rr] = arr_to[src_cols, rr]

    # ── release pixel array locks, build surface ─────────────────────────────
    del arr_from, arr_to

    result = pygame.surfarray.make_surface(out)
    return result


# ── helper: amplitude envelope ────────────────────────────────────────────────
def AMPLITUDE_ENVELOPE(t: float) -> float:
    """Bell curve – wave is strongest at mid-transition, gentle at edges."""
    # 4t(1-t) peaks at 1.0 when t=0.5, zero at t=0 and t=1
    return 4.0 * t * (1.0 - t)


def melt_transition(
        surface_from: pygame.Surface,
        surface_to: pygame.Surface,
        duration: float,
        elapsed: float,
) -> pygame.Surface:
    elapsed = max(0.0, min(elapsed, duration))
    t = elapsed / duration
    w, h = surface_from.get_size()

    arr_from = pygame.surfarray.pixels3d(surface_from)  # (w, h, 3) – view
    arr_to = pygame.surfarray.pixels3d(surface_to)

    out = np.empty((w, h, 3), dtype=np.uint8)

    # ── profil przesunięcia per-kolumna ───────────────────────────────────────
    # Każda kolumna ma swój "start delay" i prędkość – efekt nierównego topnienia.
    col_idx = np.arange(w, dtype=np.float32)

    # Opóźnienie startu topnienia: kolumny zaczynają w losowej kolejności,
    # ale deterministycznie (sin daje powtarzalny wzór).
    delay = (
            0.12 * np.sin(col_idx / w * np.pi * 6.0 + 0.5) +
            0.08 * np.sin(col_idx / w * np.pi * 11.0 + 1.8) +
            0.05 * np.cos(col_idx / w * np.pi * 17.0 + 3.1)
    )  # (w,)  zakres ≈ -0.25 … +0.25
    delay = (delay - delay.min()) / (delay.max() - delay.min() + 1e-6)
    delay *= 0.35  # max 35% opóźnienia

    # Lokalne t dla każdej kolumny (uwzględnia opóźnienie)
    t_local = np.clip((t - delay) / (1.0 - delay + 1e-6), 0.0, 1.0)  # (w,)

    # Easing: wolny start, szybki koniec (ease-in cubic)
    t_ease = t_local ** 2.5

    # Melt phase: piksele przesuwają się o max h+kilka pikseli w dół
    # "kilka pikseli" żeby upewnić się że dotarły za ekran
    max_offset = h + 40
    offset = (t_ease * max_offset).astype(np.int32)  # (w,)

    # ── wypełnij każdą kolumnę ────────────────────────────────────────────────
    # Vectorized po kolumnach (pętla w numpy, nie Python)
    row_src = np.arange(h, dtype=np.int32)  # (h,)

    # Dla wydajności: buduj wszystkie kolumny przez advanced indexing
    # src_row[x, y] = y - offset[x]  →  clamp do [0, h-1]
    # Jeśli src_row < 0: pokaż surface_to (obszar "odsłonięty")

    # (w, h) tablica źródłowych wierszy
    src_rows = row_src[np.newaxis, :] - offset[:, np.newaxis]  # (w, h)

    in_bounds = src_rows >= 0  # (w, h)
    src_rows_clamped = np.clip(src_rows, 0, h - 1)

    # Indeksy kolumn
    col_grid = np.arange(w, dtype=np.int32)[:, np.newaxis] * np.ones(h, dtype=np.int32)

    # Piksele z surface_from (przesunięte w dół)
    out_from = arr_from[col_grid, src_rows_clamped]  # (w, h, 3)

    # Piksele z surface_to (odsłonięty obszar u góry) – używamy oryginalnych wierszy [0..h-1]
    row_grid = row_src[np.newaxis, :] * np.ones(w, dtype=np.int32)[:, np.newaxis]  # (w, h)
    out_to = arr_to[col_grid, row_grid]  # (w, h, 3)

    # Maska: gdzie jest surface_from (src_row >= 0), gdzie surface_to
    mask = in_bounds[:, :, np.newaxis]  # (w, h, 1)
    out = np.where(mask, out_from, out_to).astype(np.uint8)

    # ── efekt "drip" – miękka krawędź dolna spływającej masy ────────────────
    # Pas drip_px pikseli POWYŻEJ krawędzi topnienia (ostatnie wiersze surface_from
    # zanim przejdą w surface_to). Alpha from: 1→0 od góry do dołu pasa.
    drip_px = 18
    drip_screen_rows = offset[:, np.newaxis] - drip_px + np.arange(drip_px)[np.newaxis, :]
    # (w, drip_px) – wiersze na ekranie

    valid = (drip_screen_rows >= 0) & (drip_screen_rows < h)

    if valid.any():
        # alpha: 1.0 na górze pasa → 0.0 tuż przy krawędzi (from zanika do zera)
        drip_alpha_from = np.linspace(1.0, 0.0, drip_px)[np.newaxis, :]  # (1, drip_px)

        drip_rows_c = np.clip(drip_screen_rows, 0, h - 1)
        col_drip = (np.arange(w, dtype=np.int32)[:, np.newaxis]
                    * np.ones(drip_px, dtype=np.int32))

        src_drip_row = np.clip(drip_rows_c - offset[:, np.newaxis], 0, h - 1)

        px_from = arr_from[col_drip, src_drip_row].astype(np.float32)  # (w, drip_px, 3)
        px_to = arr_to[col_drip, drip_rows_c].astype(np.float32)  # (w, drip_px, 3)

        a = drip_alpha_from[:, :, np.newaxis]  # (1, drip_px, 1)
        blended = (px_from * a + px_to * (1.0 - a)).astype(np.uint8)

        ww, rr = np.where(valid)
        out[ww, drip_rows_c[ww, rr]] = blended[ww, rr]

    del arr_from, arr_to
    return pygame.surfarray.make_surface(out)


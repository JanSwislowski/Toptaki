import pygame
import math
pygame.init()

def add_vectors(v1, v2):
    return (v1[0] + v2[0], v1[1] + v2[1])

class TextBox:
    """
    A Pygame text input box with:
    - Polish character support (ą ć ę ł ń ó ś ź ż and uppercase)
    - Cursor movement via LEFT / RIGHT arrow keys
    - HOME / END jump to start / end
    - Ctrl+LEFT / Ctrl+RIGHT jump word-by-word
    - Hold BACKSPACE to delete repeatedly (initial delay then fast repeat)
    - Scrolling viewport when text is longer than the box

    Public API
    ----------
    handle_event(event)   – call inside your event loop
    update()              – call once per frame (handles hold-repeat timing)
    draw(surface)         – render the widget
    get_text() -> str     – return current text
    set_text(text)        – programmatically set text
    clear()               – empty the box
    """

    POLISH_CHARS = set("ąćęłńóśźżĄĆĘŁŃÓŚŹŻ")

    # Key-repeat timing (milliseconds)
    _REPEAT_DELAY = 400   # time before repeat starts
    _REPEAT_RATE  = 45    # interval between repeats once started

    def __init__(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        font=None,
        font_size: int = 24,
        max_length: int = 0,
        placeholder: str = "",
        color_inactive: tuple = (160, 160, 175),
        color_active:   tuple = (80, 120, 255),
        color_bg:       tuple = (245, 245, 250),
        color_text:     tuple = (30, 30, 40),
        color_cursor:   tuple = (80, 120, 255),
        color_placeholder: tuple = (180, 180, 195),
        border_radius: int = 6,
        border_width:  int = 2,
        padding:       int = 8,
    ):
        self.rect        = pygame.Rect(x, y, width, height)
        self.max_length  = max_length
        self.placeholder = placeholder

        self.color_inactive    = color_inactive
        self.color_active      = color_active
        self.color_bg          = color_bg
        self.color_text        = color_text
        self.color_cursor      = color_cursor
        self.color_placeholder = color_placeholder
        self.border_radius     = border_radius
        self.border_width      = border_width
        self.padding           = padding

        self.font = font if font is not None else self._load_default_font(font_size)

        # text state
        self._text:   str = ""
        self._cursor: int = 0   # insertion point index into _text

        # cursor blink
        self.active:           bool = False
        self._cursor_visible:  bool = True
        self._cursor_timer:    int  = 0
        self._cursor_blink_ms: int  = 500

        # hold-key repeat state
        self._held_key:       object = None  # pygame key constant or None
        self._held_key_time:  int    = 0
        self._next_repeat_at: int    = 0
        self._in_repeat:      bool   = False

        # scroll offset (pixels)
        self._scroll: int = 0

    # ----------------------------------------------------------------
    # Public API
    # ----------------------------------------------------------------

    def handle_event(self, event,mouse_delta=(0,0)) -> None:
        """Feed a pygame event to the text box."""
        mouse_pos=add_vectors(pygame.mouse.get_pos(), mouse_delta)
        if event.type == pygame.MOUSEBUTTONDOWN:
            newly_active = self.rect.collidepoint(mouse_pos)
            if newly_active and not self.active:
                self._reset_blink()
            self.active = newly_active

        if not self.active:
            return

        if event.type == pygame.KEYDOWN:
            self._on_keydown(event)

        if event.type == pygame.KEYUP:
            if event.key == self._held_key:
                self._held_key = None

    def update(self) -> None:
        """Call once per frame – drives cursor blink and hold-key repeat."""
        now = pygame.time.get_ticks()

        # Cursor blink
        if now - self._cursor_timer >= self._cursor_blink_ms:
            self._cursor_visible = not self._cursor_visible
            self._cursor_timer   = now

        # Hold-key repeat
        if self.active and self._held_key is not None:
            if not self._in_repeat:
                if now >= self._next_repeat_at:
                    self._in_repeat      = True
                    self._next_repeat_at = now + self._REPEAT_RATE
                    self._apply_key(self._held_key)
            else:
                while now >= self._next_repeat_at:
                    self._next_repeat_at += self._REPEAT_RATE
                    self._apply_key(self._held_key)

    def draw(self, surface) -> None:
        """Render the text box onto *surface*."""
        # Background
        pygame.draw.rect(surface, self.color_bg, self.rect,
                         border_radius=self.border_radius)
        # Border
        border_color = self.color_active if self.active else self.color_inactive
        pygame.draw.rect(surface, border_color, self.rect,
                         width=self.border_width,
                         border_radius=self.border_radius)

        inner_x = self.rect.x + self.padding
        inner_y = self.rect.y + (self.rect.height - self.font.get_height()) // 2
        max_w   = self.rect.width - 2 * self.padding

        # Placeholder
        if not self._text and self.placeholder and not self.active:
            ph = self.font.render(self.placeholder, True, self.color_placeholder)
            surface.blit(ph, (inner_x, inner_y))
            return

        # Cursor pixel position within the full text surface
        cursor_px = self.font.size(self._text[:self._cursor])[0]

        # Keep cursor inside the visible viewport
        if cursor_px - self._scroll > max_w:
            self._scroll = cursor_px - max_w
        elif cursor_px - self._scroll < 0:
            self._scroll = cursor_px

        # Clip to inner area so text doesn't bleed over the border
        clip_rect = pygame.Rect(inner_x,
                                self.rect.y + self.border_width,
                                max_w,
                                self.rect.height - 2 * self.border_width)
        old_clip = surface.get_clip()
        surface.set_clip(clip_rect)

        # Render full text
        text_surf = self.font.render(self._text, True, self.color_text)
        surface.blit(text_surf, (inner_x - self._scroll, inner_y))

        # Cursor bar
        if self.active and self._cursor_visible:
            cx = inner_x + cursor_px - self._scroll
            pygame.draw.line(
                surface, self.color_cursor,
                (cx, inner_y),
                (cx, inner_y + self.font.get_height() - 1),
                2,
            )

        surface.set_clip(old_clip)

    def get_text(self) -> str:
        """Return the current text content."""
        return self._text

    def set_text(self, text: str) -> None:
        """Programmatically set text and move cursor to end."""
        self._text   = text
        self._cursor = len(text)
        self._scroll = 0

    def clear(self) -> None:
        """Clear text and reset cursor."""
        self._text   = ""
        self._cursor = 0
        self._scroll = 0

    # ----------------------------------------------------------------
    # Internal helpers
    # ----------------------------------------------------------------

    def _on_keydown(self, event) -> None:
        key = event.key
        repeatable = {
            pygame.K_BACKSPACE,
            pygame.K_LEFT,
            pygame.K_RIGHT,
            pygame.K_HOME,
            pygame.K_END,
        }
        self._apply_key(key, event=event)
        self._reset_blink()
        if key in repeatable:
            self._held_key       = key
            self._held_key_time  = pygame.time.get_ticks()
            self._next_repeat_at = self._held_key_time + self._REPEAT_DELAY
            self._in_repeat      = False

    def _apply_key(self, key, event=None) -> None:
        """Execute the action for a key (used on first press and on each repeat)."""
        ctrl = pygame.key.get_mods() & pygame.KMOD_CTRL

        if key == pygame.K_BACKSPACE:
            self._do_backspace(ctrl)

        elif key == pygame.K_LEFT:
            if ctrl:
                self._cursor = self._word_left()
            else:
                self._cursor = max(0, self._cursor - 1)

        elif key == pygame.K_RIGHT:
            if ctrl:
                self._cursor = self._word_right()
            else:
                self._cursor = min(len(self._text), self._cursor + 1)

        elif key == pygame.K_HOME:
            self._cursor = 0

        elif key == pygame.K_END:
            self._cursor = len(self._text)

        elif key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            self.active    = False
            self._held_key = None

        elif event is not None:
            char = event.unicode
            if char and self._is_accepted(char):
                if self.max_length == 0 or len(self._text) < self.max_length:
                    self._text    = self._text[:self._cursor] + char + self._text[self._cursor:]
                    self._cursor += 1

    def _do_backspace(self, ctrl: bool) -> None:
        if ctrl:
            new_pos      = self._word_left()
            self._text   = self._text[:new_pos] + self._text[self._cursor:]
            self._cursor = new_pos
        else:
            if self._cursor > 0:
                self._text    = self._text[:self._cursor - 1] + self._text[self._cursor:]
                self._cursor -= 1

    def _word_left(self) -> int:
        pos = self._cursor
        while pos > 0 and self._text[pos - 1] == " ":
            pos -= 1
        while pos > 0 and self._text[pos - 1] != " ":
            pos -= 1
        return pos

    def _word_right(self) -> int:
        pos  = self._cursor
        size = len(self._text)
        while pos < size and self._text[pos] != " ":
            pos += 1
        while pos < size and self._text[pos] == " ":
            pos += 1
        return pos

    def _reset_blink(self) -> None:
        self._cursor_visible = True
        self._cursor_timer   = pygame.time.get_ticks()

    @staticmethod
    def _load_default_font(size: int):
        for name in ("dejavusans", "freesans", "liberationsans",
                     "arial", "calibri", "segoeui", "noto"):
            f = pygame.font.SysFont(name, size)
            if f:
                return f
        return pygame.font.Font(None, size)

    @staticmethod
    def _is_accepted(char: str) -> bool:
        if char in TextBox.POLISH_CHARS:
            return True
        return len(char) == 1 and char.isprintable()


class Button:
    """
    A polished Pygame button with click animations, hover effects,
    and support for a text label, an image, or both side-by-side.

    Animation layers
    ----------------
    1. Hover  – smoothly brightens background and lifts with a shadow
    2. Press  – shrinks slightly (scale-down) and darkens instantly
    3. Release ripple – an expanding translucent circle fades out
    4. Idle   – subtle breathing pulse on the shadow (optional)

    Constructor
    -----------
    x, y, width, height  – position and size
    label                – text string (may be "" or None)
    image                – pygame.Surface (optional icon/image)
    image_size           – (w, h) to scale image to; None = use as-is
    callback             – callable invoked on successful click (optional)

    Style knobs
    -----------
    font / font_size     – label font
    color_bg             – base background colour
    color_hover          – background on hover
    color_press          – background while pressed
    color_text           – label colour
    color_ripple         – ripple colour (alpha handled internally)
    border_radius        – corner rounding
    border_width         – 0 = no border
    border_color         – border colour
    padding_x/y          – inner padding
    icon_gap             – gap between icon and label (pixels)
    shadow               – draw drop shadow
    shadow_color         – shadow rgba

    Public API
    ----------
    handle_event(event)  – call in your event loop
    update()             – call once per frame
    draw(surface)        – render
    is_hovered()         – bool
    enable() / disable() – toggle interactive state
    """

    # Animation timing (seconds)
    _HOVER_SPEED = 8.0  # lerp speed for hover colour transition
    _RIPPLE_LIFE = 0.45  # seconds a ripple lives
    _PRESS_SCALE = 0.94  # scale factor while pressed
    _SHADOW_NORMAL = 4  # shadow blur radius at rest
    _SHADOW_HOVER = 8  # shadow blur radius on hover

    def __init__(
            self,
            x: int,
            y: int,
            width: int,
            height: int,
            label: str = "",
            image: "pygame.Surface | None" = None,
            image_size: "tuple[int,int] | None" = None,
            callback=None,
            # style
            font=None,
            font_size: int = 22,
            color_bg: tuple = (255, 255, 255),
            color_hover: tuple = (230, 238, 255),
            color_press: tuple = (200, 215, 245),
            color_text: tuple = (30, 35, 60),
            color_ripple: tuple = (100, 140, 255),
            border_radius: int = 10,
            border_width: int = 2,
            border_color: tuple = (180, 195, 230),
            padding_x: int = 18,
            padding_y: int = 10,
            icon_gap: int = 10,
            shadow: bool = True,
            shadow_color: tuple = (80, 100, 160, 60),
            enabled: bool = True,
    ):
        self._base_rect = pygame.Rect(x, y, width, height)
        self.rect = self._base_rect.copy()

        self.label = label or ""
        self.callback = callback
        self.enabled = enabled

        # colours
        self._color_bg = color_bg
        self._color_hover = color_hover
        self._color_press = color_press
        self._color_text = color_text
        self._color_ripple = color_ripple
        self._border_radius = border_radius
        self._border_width = border_width
        self._border_color = border_color
        self._padding_x = padding_x
        self._padding_y = padding_y
        self._icon_gap = icon_gap
        self._shadow = shadow
        self._shadow_color = shadow_color

        # font
        if font is not None:
            self._font = font
        else:
            self._font = self._load_font(font_size)

        # image / icon
        if image is not None and image_size is not None:
            self._image = pygame.transform.smoothscale(image, image_size)
        else:
            self._image = image

        # animation state
        self._hovered: bool = False
        self._pressed: bool = False
        self._hover_t: float = 0.0  # 0=normal, 1=fully hovered
        self._scale: float = 1.0
        self._ripples: list = []  # [(cx,cy,birth_time)]
        self._clock_ref: int = pygame.time.get_ticks()

        # disabled style
        self._alpha_disabled = 120

    # ----------------------------------------------------------------
    # Public API
    # ----------------------------------------------------------------

    def handle_event(self, event) -> bool:
        """
        Feed a pygame event.
        Returns True if the button was clicked (and callback fired).
        """
        if not self.enabled:
            return False

        if event.type == pygame.MOUSEMOTION:
            self._hovered = self._base_rect.collidepoint(event.pos)

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self._base_rect.collidepoint(event.pos):
                self._pressed = True

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            was_pressed = self._pressed
            self._pressed = False
            if was_pressed and self._base_rect.collidepoint(event.pos):
                # Spawn ripple at click position
                self._ripples.append({
                    "cx": event.pos[0] - self._base_rect.x,
                    "cy": event.pos[1] - self._base_rect.y,
                    "born": pygame.time.get_ticks() / 1000.0,
                })
                if self.callback:
                    self.callback()
                return True
        return False

    def update(self) -> None:
        """Call once per frame."""
        now = pygame.time.get_ticks() / 1000.0
        dt = now - self._clock_ref / 1000.0
        self._clock_ref = pygame.time.get_ticks()

        # Smooth hover lerp
        target = 1.0 if (self._hovered and not self._pressed) else 0.0
        self._hover_t += (target - self._hover_t) * min(1.0, self._HOVER_SPEED * dt)

        # Scale spring
        target_scale = self._PRESS_SCALE if self._pressed else 1.0
        self._scale += (target_scale - self._scale) * min(1.0, 18.0 * dt)

        # Prune dead ripples
        self._ripples = [r for r in self._ripples
                         if now - r["born"] < self._RIPPLE_LIFE]

    def draw(self, surface: pygame.Surface) -> None:
        """Render the button."""
        now = pygame.time.get_ticks() / 1000.0

        # Compute scaled rect (centred on base rect)
        cx = self._base_rect.centerx
        cy = self._base_rect.centery
        sw = int(self._base_rect.width * self._scale)
        sh = int(self._base_rect.height * self._scale)
        draw_rect = pygame.Rect(cx - sw // 2, cy - sh // 2, sw, sh)

        # ── draw onto an intermediate surface so we can alpha-fade when disabled
        buf = pygame.Surface((self._base_rect.width, self._base_rect.height),
                             pygame.SRCALPHA)
        local_rect = pygame.Rect(0, 0, sw, sh)
        local_rect.center = (self._base_rect.width // 2,
                             self._base_rect.height // 2)

        # Current background colour (lerp between normal and hover/press)
        if self._pressed:
            bg = self._color_press
        else:
            bg = self._lerp_color(self._color_bg, self._color_hover, self._hover_t)

        # ── shadow ──────────────────────────────────────────────────
        if self._shadow:
            shadow_alpha = int(self._shadow_color[3] if len(self._shadow_color) > 3 else 60)
            blur = int(self._lerp(self._SHADOW_NORMAL, self._SHADOW_HOVER, self._hover_t))
            for b in range(blur, 0, -1):
                sc = (
                    max(0, min(255, self._shadow_color[0])),
                    max(0, min(255, self._shadow_color[1])),
                    max(0, min(255, self._shadow_color[2])),
                    max(0, int(shadow_alpha * b / blur * 0.4)),
                )
                sr = local_rect.inflate(b * 2, b * 2).move(0, b)
                pygame.draw.rect(buf, sc, sr,
                                 border_radius=self._border_radius + b)

        # ── body ────────────────────────────────────────────────────
        pygame.draw.rect(buf, (*bg, 255), local_rect,
                         border_radius=self._border_radius)

        # ── ripples (clipped to body) ────────────────────────────────
        if self._ripples:
            ripple_surf = pygame.Surface(
                (self._base_rect.width, self._base_rect.height), pygame.SRCALPHA)
            for r in self._ripples:
                age = now - r["born"]
                progress = age / self._RIPPLE_LIFE  # 0→1
                max_r = math.hypot(self._base_rect.width,
                                   self._base_rect.height) * 0.75
                radius = int(max_r * self._ease_out(progress))
                alpha = int(180 * (1.0 - progress))
                pygame.draw.circle(
                    ripple_surf,
                    (max(0, min(255, self._color_ripple[0])),
                     max(0, min(255, self._color_ripple[1])),
                     max(0, min(255, self._color_ripple[2])),
                     max(0, min(255, alpha))),
                    (int(r["cx"] * self._scale +
                         self._base_rect.width * (1 - self._scale) / 2),
                     int(r["cy"] * self._scale +
                         self._base_rect.height * (1 - self._scale) / 2)),
                    radius,
                )
            # Mask ripple to the button body shape
            mask_surf = pygame.Surface(
                (self._base_rect.width, self._base_rect.height), pygame.SRCALPHA)
            pygame.draw.rect(mask_surf, (255, 255, 255, 255), local_rect,
                             border_radius=self._border_radius)
            ripple_surf.blit(mask_surf, (0, 0),
                             special_flags=pygame.BLEND_RGBA_MIN)
            buf.blit(ripple_surf, (0, 0))

        # ── border ──────────────────────────────────────────────────
        if self._border_width:
            pygame.draw.rect(buf,
                             (max(0, min(255, self._border_color[0])),
                              max(0, min(255, self._border_color[1])),
                              max(0, min(255, self._border_color[2])),
                              255),
                             local_rect,
                             width=self._border_width,
                             border_radius=self._border_radius)

        # ── content (icon + label) ──────────────────────────────────
        self._draw_content(buf, local_rect)

        # ── disabled overlay ────────────────────────────────────────
        if not self.enabled:
            overlay = pygame.Surface(
                (self._base_rect.width, self._base_rect.height), pygame.SRCALPHA)
            overlay.fill((255, 255, 255, 255 - self._alpha_disabled))
            buf.blit(overlay, (0, 0))

        surface.blit(buf, draw_rect.topleft)

    def is_hovered(self) -> bool:
        return self._hovered and self.enabled

    def enable(self) -> None:
        self.enabled = True

    def disable(self) -> None:
        self.enabled = False

    # ----------------------------------------------------------------
    # Private helpers
    # ----------------------------------------------------------------

    def _draw_content(self, buf: pygame.Surface, rect: pygame.Rect) -> None:
        """Render icon and/or label, centred inside rect."""
        pieces = []  # list of surfaces to blit left-to-right

        if self._image is not None:
            pieces.append(self._image)

        label_surf = None
        if self.label:
            color = self._color_text if self.enabled else (*self._color_text[:3],)
            label_surf = self._font.render(self.label, True, color)
            pieces.append(label_surf)

        if not pieces:
            return

        gap = self._icon_gap if len(pieces) > 1 else 0
        total_w = sum(p.get_width() for p in pieces) + gap * (len(pieces) - 1)
        total_h = max(p.get_height() for p in pieces)

        x = rect.centerx - total_w // 2
        y = rect.centery - total_h // 2

        for i, piece in enumerate(pieces):
            py = y + (total_h - piece.get_height()) // 2
            buf.blit(piece, (x, py))
            x += piece.get_width() + gap

    @staticmethod
    def _lerp(a: float, b: float, t: float) -> float:
        return a + (b - a) * max(0.0, min(1.0, t))

    @staticmethod
    def _lerp_color(c1: tuple, c2: tuple, t: float) -> tuple:
        t = max(0.0, min(1.0, t))
        return tuple(max(0, min(255, int(a + (b - a) * t))) for a, b in zip(c1[:3], c2[:3]))

    @staticmethod
    def _ease_out(t: float) -> float:
        return 1.0 - (1.0 - t) ** 3

    @staticmethod
    def _load_font(size: int):
        for name in ("dejavusans", "freesans", "liberationsans",
                     "segoeui", "calibri", "noto"):
            f = pygame.font.SysFont(name, size)
            if f:
                return f
        return pygame.font.Font(None, size)


class Label:
    """
    A Pygame label widget for displaying text or an image (or both).

    Features
    --------
    - Text with full Polish character support
    - Optional icon/image beside the text
    - Horizontal and vertical alignment
    - Word-wrap with a fixed max width
    - Optional background, border, and padding
    - Smooth fade-in on first draw (optional)
    - Chainable set_text() / set_image() for live updates

    Constructor
    -----------
    x, y            – top-left position
    text            – string to display (may contain Polish characters)
    image           – pygame.Surface icon (optional)
    image_size      – (w,h) to scale image to; None = use as-is
    max_width       – wrap text at this pixel width (0 = no wrap)
    align           – horizontal text alignment: "left" | "center" | "right"
    valign          – vertical alignment inside a fixed height: "top"|"center"|"bottom"
    fixed_height    – lock widget height (0 = auto)

    Style knobs
    -----------
    font / font_size
    color_text
    color_bg        – None = transparent background
    color_border    – None = no border
    border_width
    border_radius
    padding_x / padding_y
    icon_gap        – pixels between icon and text
    icon_side       – "left" | "right"
    line_spacing    – extra pixels between wrapped lines
    fade_in         – True = alpha fades from 0 → 255 on first draw

    Public API
    ----------
    draw(surface)
    set_text(text)  → self
    set_image(surf, size=None) → self
    set_color(color) → self
    get_rect() → pygame.Rect   (bounding box of the whole widget)
    """

    def __init__(
        self,
        x: int,
        y: int,
        text: str = "",
        image: "pygame.Surface | None" = None,
        image_size: "tuple[int,int] | None" = None,
        max_width:  int   = 0,
        align:      str   = "left",
        valign:     str   = "top",
        fixed_height: int = 0,
        # style
        font=None,
        font_size:    int   = 22,
        color_text:   tuple = (30, 32, 45),
        color_bg:     "tuple | None" = None,
        color_border: "tuple | None" = None,
        border_width: int   = 1,
        border_radius: int  = 6,
        padding_x:    int   = 0,
        padding_y:    int   = 0,
        icon_gap:     int   = 8,
        icon_side:    str   = "left",
        line_spacing: int   = 4,
        fade_in:      bool  = False,
        pos_type:      str   = "topleft",
    ):
        self._x            = x
        self._y            = y
        self._text         = text
        self._max_width    = max_width
        self._align        = align
        self._valign       = valign
        self._fixed_height = fixed_height
        self._color_text   = color_text
        self._color_bg     = color_bg
        self._color_border = color_border
        self._border_width = border_width
        self._border_radius = border_radius
        self._padding_x    = padding_x
        self._padding_y    = padding_y
        self._icon_gap     = icon_gap
        self._icon_side    = icon_side
        self._line_spacing = line_spacing
        # font
        self._font = font if font is not None else self._load_font(font_size)

        # image
        self._image = self._scale_image(image, image_size)

        # fade-in
        self._alpha      = 0 if fade_in else 255
        self._fade_in    = fade_in
        self._fade_speed = 420   # alpha units per second

        # cache (rebuilt on set_text / set_image)
        self._dirty   = True
        self._cache:  "pygame.Surface | None" = None

        self._last_tick = pygame.time.get_ticks()
        w,h=self.get_rect().size
        if pos_type == "center":
            self._x-=w//2
            self._y-=h//2
        if pos_type=="leftcenter":
            self._y-=h//2
        if pos_type=="center_top":
            self._x-=w//2
        if pos_type=="right_top":
            self._x-=w
        if pos_type=="right_center":
            self._x-=w
            self._y-=h//2
        self._rect.topleft = (self._x, self._y)


    # ----------------------------------------------------------------
    # Public API
    # ----------------------------------------------------------------
    def move_y(self, dy: int):
        self._y+=dy
        self._rect.topleft = (self._x, self._y)
    def set_y(self, y: int):
        self._y=y
        self._rect.topleft = (self._x, self._y)

    def set_text(self, text: str) -> "Label":
        self._text  = text
        self._dirty = True
        return self

    def set_image(self, surf: "pygame.Surface | None",
                  size: "tuple[int,int] | None" = None) -> "Label":
        self._image = self._scale_image(surf, size)
        self._dirty = True
        return self

    def set_color(self, color: tuple) -> "Label":
        self._color_text = color
        self._dirty      = True
        return self

    def get_rect(self) -> pygame.Rect:
        self._ensure_cache()
        return self._rect.copy()

    def draw(self, surface: pygame.Surface) -> None:
        """Render the label onto *surface*."""
        now = pygame.time.get_ticks()
        dt  = (now - self._last_tick) / 1000.0
        self._last_tick = now

        # Fade-in alpha
        if self._alpha < 255:
            self._alpha = min(255, self._alpha + int(self._fade_speed * dt))

        self._ensure_cache()

        if self._alpha < 255:
            tmp = self._cache.copy()
            tmp.set_alpha(self._alpha)
            surface.blit(tmp, self._rect.topleft)
        else:
            surface.blit(self._cache, self._rect.topleft)

    # ----------------------------------------------------------------
    # Cache / rendering
    # ----------------------------------------------------------------

    def _ensure_cache(self) -> None:
        if not self._dirty:
            return
        self._dirty = False
        self._cache = self._render()

    def _render(self) -> pygame.Surface:
        """Build and return a Surface with everything composited."""

        # 1. Render text lines
        lines      = self._wrap_text()
        line_surfs = [self._font.render(l, True, self._color_text) for l in lines]
        self.first_line_w=line_surfs[0].get_width() if line_surfs else 0

        line_h     = self._font.get_linesize()
        text_w     = max((s.get_width() for s in line_surfs), default=0)
        text_h     = max(len(line_surfs) * (line_h + self._line_spacing) - self._line_spacing, 0)

        # 2. Image dimensions
        img_w = img_h = 0
        if self._image is not None:
            img_w = self._image.get_width()
            img_h = self._image.get_height()

        # 3. Content bounding box (icon + gap + text, or just one)
        if self._image and self._text:
            content_w = img_w + self._icon_gap + text_w
            content_h = max(img_h, text_h)
        elif self._image:
            content_w, content_h = img_w, img_h
        else:
            content_w, content_h = text_w, text_h

        # 4. Widget size
        widget_w = content_w + 2 * self._padding_x
        widget_h = content_h + 2 * self._padding_y
        if self._fixed_height:
            widget_h = self._fixed_height

        # 5. Surface
        surf = pygame.Surface((max(1, widget_w), max(1, widget_h)), pygame.SRCALPHA)

        # 6. Background
        if self._color_bg is not None:
            pygame.draw.rect(surf, (*self._color_bg, 255),
                             surf.get_rect(), border_radius=self._border_radius)

        # 7. Layout icon + text inside padded content area
        avail_h  = widget_h - 2 * self._padding_y
        # vertical start of content block
        if self._valign == "center":
            vy = self._padding_y + (avail_h - content_h) // 2
        elif self._valign == "bottom":
            vy = widget_h - self._padding_y - content_h
        else:
            vy = self._padding_y

        # horizontal start of content block
        avail_w = widget_w - 2 * self._padding_x
        cx = self._padding_x  # left edge of content block (align handles lines below)

        # Place icon
        if self._image is not None:
            icon_y = vy + (content_h - img_h) // 2
            if self._icon_side == "left":
                surf.blit(self._image, (cx, icon_y))
                text_x0 = cx + img_w + self._icon_gap
            else:   # right – place text first, icon after
                text_x0 = cx
                # icon placed after text block
                icon_x  = cx + text_w + self._icon_gap
                surf.blit(self._image, (icon_x, icon_y))
        else:
            text_x0 = cx

        # Place each text line
        for i, ls in enumerate(line_surfs):
            ly = vy + i * (line_h + self._line_spacing) + (content_h - text_h) // 2

            if self._align == "center":
                lx = text_x0 + (text_w - ls.get_width()) // 2
            elif self._align == "right":
                lx = text_x0 + text_w - ls.get_width()
            else:
                lx = text_x0
            surf.blit(ls, (lx, ly))

        # 8. Border
        if self._color_border is not None and self._border_width:
            pygame.draw.rect(surf, (*self._color_border, 255),
                             surf.get_rect(),
                             width=self._border_width,
                             border_radius=self._border_radius)

        self._rect = pygame.Rect(self._x, self._y, widget_w, widget_h)
        return surf

    def _wrap_text(self) -> list:
        """Split _text into lines respecting max_width (and hard newlines)."""
        if not self._text:
            return [""]
        hard_lines = self._text.split(r"\n")
        if not self._max_width:
            return hard_lines
        result = []
        for hard in hard_lines:
            words  = hard.split(" ")
            line   = ""
            for word in words:
                test = (line + " " + word).strip()
                if self._font.size(test)[0] <= self._max_width:
                    line = test
                else:
                    if line:
                        result.append(line)
                    line = word
            result.append(line)
        return result or [""]

    # ----------------------------------------------------------------
    # Helpers
    # ----------------------------------------------------------------

    @staticmethod
    def _scale_image(surf, size):
        if surf is None:
            return None
        if size is not None:
            return pygame.transform.smoothscale(surf, size)
        return surf

    @staticmethod
    def _load_font(size: int):
        for name in ("dejavusans", "freesans", "liberationsans",
                     "segoeui", "calibri", "noto"):
            f = pygame.font.SysFont(name, size)
            if f:
                return f
        return pygame.font.Font(None, size)
class Icon:
    """
    A circular avatar widget that clips any image into a circle,
    with click detection, hover highlight, press animation, and
    an optional ripple effect on click.

    Constructor
    -----------
    x, y            – centre position of the circle
    radius          – circle radius in pixels
    image           – pygame.Surface to display (cropped + scaled to fit)
    callback        – callable fired on click (optional)

    Style knobs
    -----------
    border_color    – ring colour (None = no ring)
    border_width    – ring thickness in pixels
    border_hover    – ring colour on hover (None = same as border_color)
    color_highlight – overlay tint on hover (RGBA)
    color_ripple    – ripple colour (RGB)
    shadow          – draw a soft drop-shadow behind the circle
    shadow_color    – shadow colour (RGBA)
    badge_text      – short string drawn in a small badge (e.g. "3")
    badge_color     – badge background colour
    badge_text_color
    fade_in         – alpha fades 0 → 255 on first draw

    Public API
    ----------
    handle_event(event) → bool   (True if clicked)
    update()
    draw(surface)
    set_image(surf)     → self
    is_hovered() → bool
    enable() / disable()
    """

    _RIPPLE_LIFE   = 0.50   # seconds
    _HOVER_SPEED   = 9.0    # lerp speed
    _PRESS_SCALE   = 0.91
    _FADE_SPEED    = 380    # alpha / second

    def __init__(
        self,
        x: int,
        y: int,
        radius: int,
        image: "pygame.Surface | None" = None,
        callback=None,
        # style
        border_color:      "tuple | None" = (255, 255, 255),
        border_width:      int            = 3,
        border_hover:      "tuple | None" = None,
        color_highlight:   tuple          = (255, 255, 255, 55),
        color_ripple:      tuple          = (255, 255, 255),
        shadow:            bool           = True,
        shadow_color:      tuple          = (0, 0, 0, 60),
        badge_text:        str            = "",
        badge_color:       tuple          = (230, 50, 60),
        badge_text_color:  tuple          = (255, 255, 255),
        enabled:           bool           = True,
        fade_in:           bool           = False,
    ):
        self._cx        = x
        self._cy        = y
        self._radius    = radius
        self._callback  = callback
        self.enabled    = enabled

        self._border_color     = border_color
        self._border_width     = border_width
        self._border_hover     = border_hover or border_color
        self._color_highlight  = color_highlight
        self._color_ripple     = color_ripple
        self._shadow           = shadow
        self._shadow_color     = shadow_color
        self._badge_text       = badge_text
        self._badge_color      = badge_color
        self._badge_text_color = badge_text_color

        # Circular image cache
        self._source_image: "pygame.Surface | None" = None
        self._circle_surf:  "pygame.Surface | None" = None
        if image is not None:
            self._bake_circle(image)

        # Badge font
        badge_font_size = max(10, radius // 2)
        self._badge_font = self._load_font(badge_font_size)

        # Animation state
        self._hovered:      bool  = False
        self._pressed:      bool  = False
        self._hover_t:      float = 0.0
        self._scale:        float = 1.0
        self._ripples:      list  = []

        # Fade-in
        self._alpha      = 0 if fade_in else 255
        self._fade_in    = fade_in

        self._last_tick  = pygame.time.get_ticks()

    # ----------------------------------------------------------------
    # Public API
    # ----------------------------------------------------------------

    def handle_event(self, event,mouse_delta=(0,0)) -> bool:
        """Feed a pygame event. Returns True if the icon was clicked."""
        if not self.enabled:
            return False
        mouse_pos=add_vectors(pygame.mouse.get_pos(),mouse_delta)
        if event.type == pygame.MOUSEMOTION:
            self._hovered = self._hit(mouse_pos)

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self._hit(mouse_pos):
                self._pressed = True

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            was_pressed   = self._pressed
            self._pressed = False
            if was_pressed and self._hit(mouse_pos):
                self._ripples.append({
                    "born": pygame.time.get_ticks() / 1000.0,
                })
                if self._callback:
                    self._callback()
                return True
        return False

    def update(self) -> None:
        """Call once per frame."""
        now  = pygame.time.get_ticks() / 1000.0
        dt   = (now - self._last_tick / 1000.0 if hasattr(self, "_last_tick")
                else 0.016)
        self._last_tick = pygame.time.get_ticks()

        # Fade-in
        if self._alpha < 255:
            self._alpha = min(255, self._alpha + int(self._FADE_SPEED * dt))

        # Hover lerp
        target_h = 1.0 if (self._hovered and not self._pressed) else 0.0
        self._hover_t += (target_h - self._hover_t) * min(1.0, self._HOVER_SPEED * dt)

        # Scale spring
        target_s = self._PRESS_SCALE if self._pressed else 1.0
        self._scale += (target_s - self._scale) * min(1.0, 20.0 * dt)

        # Prune dead ripples
        self._ripples = [r for r in self._ripples
                         if now - r["born"] < self._RIPPLE_LIFE]

    def draw(self, surface: pygame.Surface) -> None:
        """Render the icon onto *surface*."""
        now = pygame.time.get_ticks() / 1000.0

        # Scaled radius and centre
        sr  = int(self._radius * self._scale)
        cx, cy = self._cx, self._cy

        # Work on a buffer big enough for shadow bleed
        pad = self._radius + 12
        buf_size = (pad * 2, pad * 2)
        buf  = pygame.Surface(buf_size, pygame.SRCALPHA)
        bcx, bcy = pad, pad   # local centre

        # ── shadow ────────────────────────────────────────────────
        if self._shadow:
            sa   = self._shadow_color[3] if len(self._shadow_color) > 3 else 60
            blur = 7 + int(4 * self._hover_t)
            for b in range(blur, 0, -1):
                sc = (*self._shadow_color[:3],
                      max(0, int(sa * b / blur * 0.5)))
                pygame.draw.circle(buf, sc,
                                   (bcx, bcy + b), sr + b)

        # ── image circle ──────────────────────────────────────────
        if self._circle_surf is not None:
            scaled = pygame.transform.smoothscale(
                self._circle_surf,
                (sr * 2, sr * 2),
            )
            buf.blit(scaled, (bcx - sr, bcy - sr))
        else:
            # Fallback grey circle
            pygame.draw.circle(buf, (180, 180, 190), (bcx, bcy), sr)

        # ── hover highlight overlay ────────────────────────────────
        if self._hover_t > 0.01:
            hl_alpha = int(self._color_highlight[3] * self._hover_t)
            hl_surf  = pygame.Surface((sr * 2, sr * 2), pygame.SRCALPHA)
            pygame.draw.circle(hl_surf, (*self._color_highlight[:3], hl_alpha),
                               (sr, sr), sr)
            buf.blit(hl_surf, (bcx - sr, bcy - sr))

        # ── ripples ───────────────────────────────────────────────
        for r in self._ripples:
            age      = now - r["born"]
            progress = age / self._RIPPLE_LIFE
            rr       = int(sr * self._ease_out(progress))
            alpha    = int(200 * (1.0 - progress))
            rsurf    = pygame.Surface((sr * 2, sr * 2), pygame.SRCALPHA)
            pygame.draw.circle(rsurf, (*self._color_ripple, alpha),
                               (sr, sr), rr)
            # mask to circle shape
            mask = pygame.Surface((sr * 2, sr * 2), pygame.SRCALPHA)
            pygame.draw.circle(mask, (255, 255, 255, 255), (sr, sr), sr)
            rsurf.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
            buf.blit(rsurf, (bcx - sr, bcy - sr))

        # ── border ring ───────────────────────────────────────────
        if self._border_color and self._border_width:
            bc = self._lerp_color(self._border_color,
                                  self._border_hover,
                                  self._hover_t)
            pygame.draw.circle(buf, (*bc, 255),
                               (bcx, bcy), sr,
                               width=self._border_width)

        # ── disabled overlay ──────────────────────────────────────
        if not self.enabled:
            ov = pygame.Surface(buf_size, pygame.SRCALPHA)
            pygame.draw.circle(ov, (255, 255, 255, 140), (bcx, bcy), sr)
            buf.blit(ov, (0, 0))

        # ── blit buffer to screen ─────────────────────────────────
        if self._alpha < 255:
            buf.set_alpha(self._alpha)
        surface.blit(buf, (cx - pad, cy - pad))

        # ── badge (drawn directly on screen, not scaled) ──────────
        if self._badge_text:
            self._draw_badge(surface)

    def set_image(self, surf: "pygame.Surface | None") -> "Icon":
        self._bake_circle(surf)
        return self

    def is_hovered(self) -> bool:
        return self._hovered and self.enabled

    def enable(self)  -> None:  self.enabled = True
    def disable(self) -> None:  self.enabled = False

    def set_badge(self, text: str) -> "Icon":
        self._badge_text = text
        return self

    # ----------------------------------------------------------------
    # Private helpers
    # ----------------------------------------------------------------

    def _hit(self, pos) -> bool:
        """True if *pos* is inside the circle."""
        dx, dy = pos[0] - self._cx, pos[1] - self._cy
        return math.hypot(dx, dy) <= self._radius

    def _bake_circle(self, surf: pygame.Surface) -> None:
        """
        Pre-render the image clipped to a circle of diameter 2*_radius.
        We store it at native size; draw() smoothscales to the current scale.
        """
        d    = self._radius * 2
        self._source_image = surf

        # Scale source to fill the circle
        sw, sh = surf.get_size()
        scale  = max(d / sw, d / sh)
        nw, nh = int(sw * scale), int(sh * scale)
        scaled = pygame.transform.smoothscale(surf, (nw, nh))

        # Centre-crop
        ox = (nw - d) // 2
        oy = (nh - d) // 2
        cropped = scaled.subsurface(pygame.Rect(ox, oy, d, d)).copy()

        # Apply circular mask
        circle_surf = pygame.Surface((d, d), pygame.SRCALPHA)
        pygame.draw.circle(circle_surf, (255, 255, 255, 255), (d // 2, d // 2), d // 2)
        cropped = cropped.convert_alpha()
        cropped.blit(circle_surf, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)

        self._circle_surf = cropped

    def _draw_badge(self, surface: pygame.Surface) -> None:
        txt  = self._badge_font.render(self._badge_text, True, self._badge_text_color)
        tw, th = txt.get_size()
        br   = max(tw, th) // 2 + 5
        bx   = self._cx + int(self._radius * 0.68)
        by   = self._cy - int(self._radius * 0.68)
        pygame.draw.circle(surface, self._badge_color, (bx, by), br)
        pygame.draw.circle(surface, (255, 255, 255), (bx, by), br, width=2)
        surface.blit(txt, (bx - tw // 2, by - th // 2))

    @staticmethod
    def _lerp_color(c1, c2, t):
        if c1 is None or c2 is None:
            return c1 or c2
        t = max(0.0, min(1.0, t))
        return tuple(int(a + (b - a) * t) for a, b in zip(c1[:3], c2[:3]))

    @staticmethod
    def _ease_out(t: float) -> float:
        return 1.0 - (1.0 - t) ** 3

    @staticmethod
    def _load_font(size: int):
        for name in ("dejavusans", "freesans", "liberationsans",
                     "segoeui", "calibri", "noto"):
            f = pygame.font.SysFont(name, size)
            if f:
                return f
        return pygame.font.Font(None, size)

class Comment:
    def __init__(self,width,text="",icon=None,user=""):
        self.color=(50,50,50,180)
        self.padding=10

        icon_r=15
        self.icon=Icon(icon_r,icon_r+2,icon_r,image=icon)
        font_size=18
        self.user_name=Label(2*icon_r+10,int(icon_r/2),text=user,color_text=(200,200,255),font_size=font_size)


        text_x=self.padding
        text_y=40
        self.text=Label(text_x,text_y,text=text,max_width=width-text_x-self.padding,color_text=(220,220,255),font_size=16)
        self.w=width

        self.h=text_y+self.text.get_rect().h+self.padding
        self.surface=pygame.Surface((width,self.h),pygame.SRCALPHA)
    def draw(self):
        self.surface.fill(self.color)
        self.user_name.draw(self.surface)
        self.icon.draw(self.surface)
        self.text.draw(self.surface)
        return self.surface
    def update(self):
        self.icon.update()

    def handle_event(self,event,mouse_delta=(0,0)):
        self.icon.handle_event(event,mouse_delta)
class ComentSection:
    def __init__(self,width,height):
        self.surface=pygame.Surface((width,height),pygame.SRCALPHA)
        self.width=width
        self.height=height
        self.rect=self.surface.get_rect()

        self.comments=[]
        self.c_height=0

        self.diff=3
        self.scroll=0
        self.curent_scroll=0
        self.prev_mouse_y=None
        self.is_scrolled=False
    def get_height(self):
        h=0
        for comment in self.comments:
            h+=comment.h+self.diff
        return h
    def add_comment(self,text="",icon=None,user=""):
        self.comments.append(Comment(self.width,text,icon,user))
        self.c_height=self.get_height()
    def draw(self):
        self.surface.fill((0,0,0,0))
        scroll=self.scroll+self.curent_scroll
        # print(scroll)
        y=-max(min(scroll,self.c_height-self.height),0)
        for comment in self.comments:
            self.surface.blit(comment.draw(),(0,y))
            y+=comment.h+self.diff
            pygame.draw.rect(self.surface,(200,200,200),(0,y-self.diff,self.width,self.diff))
        return self.surface
    def is_hovered(self,mp):
        return self.rect.collidepoint(mp)
    def update(self,mouse_delta=(0,0)):
        mouse_pos=add_vectors(pygame.mouse.get_pos(),mouse_delta)

        for comment in self.comments:
            comment.update()
        if pygame.mouse.get_pressed()[0] and self.is_scrolled:
            self.curent_scroll=self.prev_mouse_y-pygame.mouse.get_pos()[1]
        elif pygame.mouse.get_pressed()[0] and self.is_hovered(mouse_pos):
            self.prev_mouse_y=pygame.mouse.get_pos()[1]
            self.is_scrolled=True
        else:
            self.scroll+=self.curent_scroll
            self.scroll=max(min(self.scroll,self.c_height-self.height),0)
            self.curent_scroll=0
            self.prev_mouse_y=None
            self.is_scrolled=False

    def handle_events(self,event,mouse_delta=(0,0)):
        scroll=self.scroll+self.curent_scroll
        y=-max(min(scroll,self.c_height-self.height),0)
        for comment in self.comments:
            comment.handle_event(event,add_vectors(mouse_delta,(0,-y)))
            y+=comment.h+self.diff

class image_gallery:
    def __init__(self,width,height,images=[]):
        self.width=width
        if len(images)==0: self.height=0
        else: self.height=height

        self.color=(50,50,50,180)
        self.surface=pygame.Surface((width,self.height),pygame.SRCALPHA)

        self.rect=pygame.Rect(0,0,width,height)

        self.scroll=0
        self.curent_scroll=0
        self.prev_mouse_x=None
        self.is_scrolled=False

        self.circle_r=3
        self.cicle_diff=10
        self.circle_color=(200,200,255)
        self.circle_y=height-20

        self.l=len(images)
        self.max_width=width*self.l

        self.images=self.scale_images(images)
    def scale_images(self,images):
        scaled=[]
        for img in images:
            w,h=img.get_size()
            if w>h:
                scale=(self.width)/w
            else:
                scale=self.height/h
            nw=int(w*scale)
            nh=int(h*scale)
            scaled.append(pygame.transform.smoothscale(img,(nw,nh)))
        return scaled
    def draw(self):
        scroll=self.scroll+self.curent_scroll
        self.surface.fill(self.color)
        x=-max(min(scroll,self.max_width-self.width),0)
        for img in self.images:
            curx=x+self.width/2-img.get_width()/2
            cury=self.height/2-img.get_height()/2
            self.surface.blit(img,(curx,cury))
            x+=self.width

        x=self.width/2-self.circle_r/2*self.l-self.cicle_diff*(self.l-1)/2

        for i in range(self.l):
            c_color=self.circle_color
            r=self.circle_r
            if abs(scroll-self.width*i)<self.width/2:
                c_color=(255,255,255)
                r*=1.5
            pygame.draw.circle(self.surface,c_color,(int(x),self.circle_y),r)
            x+=self.circle_r+self.cicle_diff
        return self.surface
    def is_hovered(self,mp):
        return self.rect.collidepoint(mp)
    def update(self,mouse_delta=(0,0)):
        mouse_pos=add_vectors(pygame.mouse.get_pos(),mouse_delta)
        if pygame.mouse.get_pressed()[0] and self.is_scrolled:
            self.curent_scroll=self.prev_mouse_x-pygame.mouse.get_pos()[0]
        elif pygame.mouse.get_pressed()[0] and self.is_hovered(mouse_pos):
            self.prev_mouse_x=pygame.mouse.get_pos()[0]
            self.is_scrolled=True
        else:
            self.prev_mouse_x=0
            self.scroll+=self.curent_scroll
            self.scroll=max(min(self.scroll,self.max_width-self.width),0)
            self.curent_scroll=0
            self.is_scrolled=False
from functions import generate_coment_section
class Post:
    def __init__(self,width,user,icon,comments=[],text="",images=[],image_height=300,comments_height=200,text_box_height=40):
        self.color=(50,50,50,180)

        self.padding=15

        self.width=width
        if len(images)==0: self.image_height=0
        else: self.image_height=image_height

        self.icon=Icon(15+self.padding,15+self.padding,15,image=icon,shadow=False)

        text_y=self.icon._cy+self.icon._radius+5

        self.user=Label(self.icon._cx+self.icon._radius+self.padding,self.padding,text=user,color_text=(200,200,255),font_size=20)
        self.text=Label(self.padding,text_y,text=text,color_text=(220,220,255),font_size=18,max_width=width)


        self.images=image_gallery(width-self.padding*2,image_height,images)
        self.images_pos=(self.padding,self.text.get_rect().h+self.padding+self.text._y)

        self.text_box=TextBox(self.padding,self.images_pos[1]+self.image_height+self.padding,width-self.padding*2,text_box_height)

        self.comment_section=generate_coment_section(comments,width-self.padding*2,comments_height,)

        self.comments_pos=(self.padding,self.text_box.rect.bottom+self.padding)


        self.height=self.comments_pos[1]+self.comment_section.height+self.padding

        self.surface=pygame.Surface((width,self.height),pygame.SRCALPHA)
        self.scrolling= False
    def draw(self):

        self.surface.fill(self.color)
        self.user.draw(self.surface)
        self.icon.draw(self.surface)
        self.text.draw(self.surface)
        self.text_box.draw(self.surface)

        self.surface.blit(self.images.draw(),self.images_pos)

        self.surface.blit(self.comment_section.draw(),self.comments_pos)
        return self.surface
    def check_scrolling(self):
        self.scrolling=self.images.is_scrolled or self.comment_section.is_scrolled
    def update(self,mouse_delta=(0,0)):
        self.icon.update()
        self.text_box.update()
        if not self.comment_section.is_scrolled: self.images.update(add_vectors(mouse_delta,(-self.images_pos[0],-self.images_pos[1])))
        if not self.images.is_scrolled: self.comment_section.update(add_vectors(mouse_delta,(-self.comments_pos[0],-self.comments_pos[1])))
        self.check_scrolling()
    def handle_events(self,event,mouse_delta=(0,0)):
        if not self.images.is_scrolled: self.comment_section.handle_events(event,add_vectors(mouse_delta,(-self.comments_pos[0],-self.comments_pos[1])))
        self.icon.handle_event(event,mouse_delta)
        self.text_box.handle_event(event,mouse_delta)
class Picker:
    def __init__(self,cx,y,width,height,font_size,options=[],color=(50,50,50),chosen_color=(100,100,100),text_color=(220,220,255)):
        self.font_size=font_size
        x=cx-width/2
        self.rect=pygame.Rect(x,y,width,height)
        self.options=options
        self.color=color
        self.chosen_color=chosen_color
        self.text_color=text_color
        self.chosen=0
        self.height=height
    def draw(self,surface):
        w=self.rect.width/len(self.options)
        for i,option in enumerate(self.options):
            color=self.chosen_color if i==self.chosen else self.color
            option_rect=pygame.Rect(self.rect.x+i*w,self.rect.y,w,self.height)
            pygame.draw.rect(surface,color,option_rect)
            label=Label(option_rect.centerx,option_rect.centery,text=option,color_text=self.text_color,font_size=self.font_size,pos_type="center")
            label.draw(surface)
    def update(self):
        if pygame.mouse.get_pressed()[0]:
            mouse_pos=pygame.mouse.get_pos()
            if self.rect.collidepoint(mouse_pos):
                w=self.rect.width/len(self.options)
                clicked_option=int((mouse_pos[0]-self.rect.x)/w)
                self.chosen=clicked_option
    def get_chosen(self):
        return self.options[self.chosen]
    def rest(self):
        self.chosen=0

from functions import get_color_leaderboard,darken_rgb,scale_rect,normalise_scroll
class Bar:
    def __init__(self,width,height,label,title,elo,bg):
        self.rect=pygame.Rect(0,0,width,height)

        self.surface=pygame.Surface((width,height))
        self.surface.fill(bg)

        label_x=5
        lebal_y=height/2
        self.label=Label(label_x,lebal_y,text=label,color_text=(0,0,0),font_size=18,pos_type="leftcenter")

        title_x=50
        self.title=Label(title_x,lebal_y,text=title,color_text=(0,0,0),font_size=18,pos_type="leftcenter")

        elo_x=width-30
        self.elo=Label(elo_x,lebal_y,text=str(elo),color_text=(0,0,0),font_size=18,pos_type="center")

    def draw(self,color,border_color):
        r=10
        pygame.draw.rect(self.surface,color,self.rect,border_radius=r)
        pygame.draw.rect(self.surface,border_color,self.rect,width=3,border_radius=r)
        self.label.draw(self.surface)
        self.title.draw(self.surface)
        self.elo.draw(self.surface)
        return self.surface
    def hit(self,pos):
        return self.rect.collidepoint(pos)
class Leader_board:
    def __init__(self, width, heiht,label,players=None):
        if players is None:
            players = []
        self.width=width
        self.height=heiht
        self.surface=pygame.Surface((width,heiht))

        self.label=Label(width/2,20,text=label,color_text=(255,255,255),font_size=40,pos_type="center_top")

        self.legend_name_x=60
        self.legend_y=100

        self.legend_name=Label(self.legend_name_x,self.legend_y,text="Name",color_text=(200,200,200),font_size=18,pos_type="left")
        self.legend_rank=Label(width-100,self.legend_y,text="Elo",color_text=(200,200,200),font_size=18,pos_type="left")

        d=10
        self.legend_rect=scale_rect(pygame.Rect(self.legend_name_x,self.legend_y,self.legend_rank.get_rect().right-self.legend_name_x,self.legend_rank.get_rect().h),d,d,d,d)

        self.players=players

        self.padding_y=3
        self.bar_padding=20
        self.color=(80,80,80)
        self.bar_width=width-self.bar_padding*2
        self.bars=[Bar(self.bar_width,40,player["label"],player["name"],player["elo"],self.color) for player in players]
        self.bar_height=self.get_bar_height()
        self.bar_start_y=150
        self.bar_end=self.height-30

        self.scroll=0
        self.is_scrolled=False
        self.prev_mouse_y=None
    def get_bar_height(self):
        h=0
        for bar in self.bars:
            h+=bar.rect.height+self.padding_y
        return h-self.padding_y
    def draw(self):
        r=15
        w=4
        color=self.color
        pygame.draw.rect(self.surface,color,(0,0,self.width,self.height),border_radius=r)#bg


        start=self.bar_start_y
        y=start-self.scroll
        padding=self.padding_y
        bar_end=self.bar_end

        for i,bar in enumerate(self.bars):
            if y+bar.rect.height<start:
                y+=bar.rect.height+padding
                continue
            c=get_color_leaderboard(i)
            border_color=darken_rgb(c,0.5)
            self.surface.blit(bar.draw(c,border_color),(self.bar_padding,y))
            y+=bar.rect.height+padding
            if y>bar_end:
                break

        pygame.draw.rect(self.surface,color,(self.bar_padding,0,self.bar_width,self.bar_start_y))

        pygame.draw.rect(self.surface, (30, 30, 30), self.legend_rect, border_radius=5)#legend

        self.label.draw(self.surface)
        self.legend_rank.draw(self.surface)
        self.legend_name.draw(self.surface)

        pygame.draw.rect(self.surface,color,(self.bar_padding,bar_end,self.bar_width,self.height-bar_end-w))

        pygame.draw.rect(self.surface,darken_rgb(color,0.5),(0,0,self.width,self.height),width=w,border_radius=r) #border

        # d=8
        # rect=scale_rect(pygame.Rect(self.bar_padding,start,self.bar_width,bar_end-start),d,d,d,0)
        # pygame.draw.rect(self.surface,(5,5,5),rect,border_radius=10,width=3)
        return self.surface
    def update(self,mouse_delta=(0,0)):
        mp=add_vectors(pygame.mouse.get_pos(),mouse_delta)
        if self.is_scrolled and pygame.mouse.get_pressed()[0]:
            self.scroll=normalise_scroll(self.scroll-mp[1]+self.prev_mouse_y,self.get_bar_height(),self.bar_end-self.bar_start_y)
            self.prev_mouse_y=mp[1]
        elif pygame.mouse.get_pressed()[0]:
            y=self.bar_start_y-self.scroll
            for i,bar in enumerate(self.bars):
                if bar.hit((mp[0]-self.bar_padding,mp[1]-y)):
                    return i
                y+=bar.rect.height+self.padding_y
            self.is_scrolled=True
            self.prev_mouse_y=mp[1]
        else:
            self.is_scrolled=False
            self.prev_mouse_y=None
        return None
from functions import cords_to_str,create_gradient_numpy

from functions import create_fade_mask,twodistance_sq
class Description:
    def __init__(self,width,height,text):
        self.surface=pygame.Surface((width,height),pygame.SRCALPHA)
        self.rect=self.surface.get_rect()

        self.padding_x=10
        self.padding_y=10

        font_size=23
        self.text=Label(self.padding_x,self.padding_y,text=text,color_text=(255,255,255),font_size=font_size,max_width=width-self.padding_x*2)

        x=self.text.first_line_w+10
        self.inactive_label=Label(x,self.padding_y,text="[...]",color_text=(255,255,255),font_size=font_size)

        self.active=False
        self.pressed=False

        self.scrolling=False
        self.scroll=0
        self.prev_mouse_pos=None
        # self.scroll
        self.fade_h=15
        self.fade_surface_up=create_fade_mask(width,self.fade_h,strength=0.5,direction="top").convert_alpha()
        self.fade_surface_down=create_fade_mask(width,self.fade_h,strength=0.5,direction="bottom").convert_alpha()

        self.txt_h=self.text.get_rect().h
    def draw(self):
        self.surface.fill((0,0,0,0))
        if not self.active:
            self.scroll=0
            self.inactive_label.draw(self.surface)
        self.text.set_y(self.padding_y-self.scroll)
        self.text.draw(self.surface)
        self.surface.blit(self.fade_surface_up,(0,0), special_flags=pygame.BLEND_RGBA_MULT)
        self.surface.blit(self.fade_surface_down,(0,self.rect.height-self.fade_h), special_flags=pygame.BLEND_RGBA_MULT)
        return self.surface
    def check_swipe(self,mp):
        r=4
        if twodistance_sq(mp,self.prev_mouse_pos)<=r*r:
            return False
        return True
    def check_press(self,mouse_delta=(0,0)):
        mp=add_vectors(pygame.mouse.get_pos(),mouse_delta)
        mp_global=pygame.mouse.get_pos()
        mc=pygame.mouse.get_pressed()[0]

        if self.scrolling and not mc:
            self.scrolling=False
            self.prev_mouse_pos=None
            self.pressed=False
        elif self.scrolling and mc:
            self.scroll-=mp_global[1]-self.prev_mouse_pos[1]
            self.scroll=normalise_scroll(self.scroll,self.txt_h+self.padding_y*2,self.rect.height)

            self.prev_mouse_pos=mp_global
            return False

        if self.prev_mouse_pos is None and mc and self.rect.collidepoint(mp):
            self.prev_mouse_pos=mp_global
        elif mc and self.prev_mouse_pos is not None and self.check_swipe(mp_global) :
            self.prev_mouse_pos=mp_global
            self.scrolling=True
            return False
        elif not mc:
            self.prev_mouse_pos = None
        if self.scrolling: print("scrolling")
        if mc and self.rect.collidepoint(mp):
            self.pressed=True
        elif self.rect.collidepoint(mp) and self.pressed:
            self.active=not self.active
            self.pressed=False
            return True
        else:
            self.pressed=False
        return False
class CompCard:
    def __init__(self,width,height,img:pygame.surface.Surface,avatar:pygame.Surface,name,title,date,cords,description):
        self.surface=pygame.Surface((width,height),pygame.SRCALPHA)
        self.img=img
        self.img_pos=(width/2-img.get_width()/2,height/2-img.get_height()/2)
        self.h=height


        gradient_h=80
        self.gradient=create_gradient_numpy(width,gradient_h,max_alpha=250,direction="top",strength=2).convert_alpha()

        avatar_r=30
        avatar_x=10+avatar_r
        avatar_y=10+avatar_r
        self.avatar=Icon(avatar_x,avatar_y,avatar_r,image=avatar,shadow=False)

        font_size=20

        name_x=avatar_x+avatar_r*2+10
        name_y=10
        self.name_label=Label(name_x,name_y,text=name,color_text=(255,255,255),font_size=font_size,pos_type="left_top")

        font_size=15
        date_x=width-20
        date_y=5
        self.date_label=Label(date_x,date_y,text=date,color_text=(200,200,200),font_size=font_size,pos_type="right_top")

        cords_x=date_x-self.date_label.get_rect().w-100
        cords_y=date_y
        self.cords_label=Label(cords_x,cords_y,text=cords_to_str(cords),color_text=(200,200,200),font_size=font_size,pos_type="right_top")

        self.desc_h_na=50
        self.desc_h_active=200

        self.description=Description(width,self.desc_h_active,description)
        self.desc_h_active=min(self.desc_h_active,self.description.txt_h+self.description.padding_y*2)
        self.desc_y=height-self.desc_h_na


        sliding_cycles=10
        self.sliding_dy=(self.desc_h_active-self.desc_h_na)/sliding_cycles
        self.sliding="down"
        self.darken_color=(0,0,0,200)
    def update(self,mouse_delta=(0,0)):
        mp=add_vectors(pygame.mouse.get_pos(),mouse_delta)
        if self.sliding=="up":
            self.desc_y=max(self.desc_y-self.sliding_dy,self.h-self.desc_h_active)
        elif self.sliding=="down":
            self.desc_y=min(self.desc_y+self.sliding_dy,self.h-self.desc_h_na)
        if not self.surface.get_rect().collidepoint(mp):
            return
        self.avatar.update()
        if self.description.check_press((mouse_delta[0],mouse_delta[1]-self.desc_y)):
            if self.sliding=="down":
                self.sliding="up"
            else:
                self.sliding="down"
    def darken(self,alpha):
        darken = pygame.Surface(self.surface.get_size())
        darken.fill((alpha, alpha, alpha))  # lower values = darker
        self.surface.blit(darken, (0, 0), special_flags=pygame.BLEND_RGB_MULT)
    def draw(self):
        color=(50,50,50)
        self.surface.fill(color)
        self.surface.blit(self.img,self.img_pos)
        self.surface.blit(self.gradient,(0,0))

        self.avatar.draw(self.surface)
        self.name_label.draw(self.surface)
        self.date_label.draw(self.surface)
        self.cords_label.draw(self.surface)

        if self.description.active:
            self.darken(100)
        self.surface.blit(self.description.draw(),(0,self.desc_y))
        return self.surface





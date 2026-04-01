import pygame
import sys


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

    def handle_event(self, event) -> None:
        """Feed a pygame event to the text box."""
        if event.type == pygame.MOUSEBUTTONDOWN:
            newly_active = self.rect.collidepoint(event.pos)
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


# -----------------------------------------------------------------------
# Demo – run this file directly to try everything out
# -----------------------------------------------------------------------
def demo():
    pygame.init()
    screen = pygame.display.set_mode((600, 300))
    pygame.display.set_caption("TextBox – arrows • hold backspace • Polish chars")
    clock = pygame.time.Clock()

    hint_font  = pygame.font.SysFont("dejavusans", 14) or pygame.font.Font(None, 17)
    label_font = pygame.font.SysFont("dejavusans", 16) or pygame.font.Font(None, 19)

    boxes = [
        TextBox(60, 52,  480, 44, font_size=23,
                placeholder="Wpisz imię… (Łukasz, Żaneta)"),
        TextBox(60, 158, 480, 44, font_size=23,
                placeholder="Zażółć gęślą jaźń…"),
    ]

    HINT = "← → move cursor  |  Ctrl+← → word jump  |  Home / End  |  hold ⌫"
    BG   = (228, 228, 238)

    while True:
        clock.tick(60)
        screen.fill(BG)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            for box in boxes:
                box.handle_event(event)

        for i, box in enumerate(boxes):
            box.update()
            base_y = 52 + i * 106
            # hint above the box
            h = hint_font.render(HINT, True, (140, 140, 160))
            screen.blit(h, (60, base_y - 17))
            box.draw(screen)
            # get_text() readout below the box
            out = label_font.render(f'get_text() → "{box.get_text()}"',
                                    True, (70, 70, 105))
            screen.blit(out, (60, base_y + 51))

        pygame.display.flip()


if __name__ == "__main__":
    demo()
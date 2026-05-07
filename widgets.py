import math
from datetime import datetime

from kivy.animation import Animation
from kivy.app import App
from kivy.core.window import Window
from kivy.graphics import Color, Ellipse, Line, Mesh, Rectangle, RoundedRectangle
from kivy.metrics import dp, sp
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget

from theme import (
    BG, ERROR, PRIMARY, STATUS_COLORS, SUCCESS, TXT, TXT2, WHITE,
)


def _fmt_dt(iso_str):
    """Format an ISO datetime string to a compact readable form, e.g. '05 Jan, 15:30'."""
    if not iso_str:
        return ""
    try:
        dt = datetime.fromisoformat(str(iso_str).replace("Z", "+00:00"))
        return dt.strftime("%d %b, %H:%M")
    except Exception:
        return ""


class PrimaryBtn(Button):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.background_normal = ""
        self.background_color = (0, 0, 0, 0)
        self.color = WHITE
        self.size_hint_y = None
        self.height = dp(48)
        self.font_size = sp(15)
        self.bold = True
        with self.canvas.before:
            self._bg_col = Color(*PRIMARY)
            self._bg = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(10)])
        self.bind(pos=self._sync, size=self._sync)

    def _sync(self, *_):
        self._bg.pos = self.pos
        self._bg.size = self.size


class OutlineBtn(Button):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.background_normal = ""
        self.background_color = (0, 0, 0, 0)
        self.color = PRIMARY
        self.size_hint_y = None
        self.height = dp(44)
        self.font_size = sp(14)
        with self.canvas.after:
            self._border_c = Color(*PRIMARY)
            self._border = Line(rounded_rectangle=[0, 0, 100, 100, dp(10)], width=1.5)
        self.bind(pos=self._sync_b, size=self._sync_b)

    def _sync_b(self, *_):
        self._border.rounded_rectangle = [self.x, self.y, self.width, self.height, dp(10)]


class DangerBtn(Button):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.background_normal = ""
        self.background_color = (0, 0, 0, 0)
        self.color = WHITE
        self.size_hint_y = None
        self.height = dp(48)
        self.font_size = sp(15)
        self.bold = True
        with self.canvas.before:
            self._bg_col = Color(*ERROR)
            self._bg = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(10)])
        self.bind(pos=self._sync, size=self._sync)

    def _sync(self, *_):
        self._bg.pos = self.pos
        self._bg.size = self.size


class StyledInput(TextInput):
    def __init__(self, **kw):
        self._max_len = kw.pop("max_len", None)
        kw.setdefault("multiline", False)
        kw.setdefault("size_hint_y", None)
        kw.setdefault("height", dp(42))
        super().__init__(**kw)
        self.background_normal = ""
        self.background_active = ""
        self.background_color = WHITE
        self.foreground_color = TXT
        self.cursor_color = PRIMARY
        self.hint_text_color = (0.55, 0.55, 0.55, 1)
        self.padding = [dp(12), dp(10)]
        self.font_size = sp(13)
        with self.canvas.after:
            Color(0.86, 0.86, 0.88, 1)
            self._border_ln = Line(rounded_rectangle=[0, 0, 1, 1, dp(6)], width=0.8)
        self.bind(pos=self._sync_border, size=self._sync_border)
        if self._max_len:
            self.bind(text=self._enforce_max_len)

    def _sync_border(self, *_):
        self._border_ln.rounded_rectangle = [self.x, self.y, self.width, self.height, dp(6)]

    def _enforce_max_len(self, instance, value):
        if len(value) > self._max_len:
            instance.text = value[: self._max_len]


class HamburgerBtn(ButtonBehavior, Widget):
    """Three white bars drawn on canvas — works regardless of font support."""

    def __init__(self, **kw):
        super().__init__(**kw)
        self.size_hint = (None, None)
        self.size = (dp(44), dp(44))
        self.bind(pos=self._draw, size=self._draw)

    def _draw(self, *_):
        self.canvas.after.clear()
        with self.canvas.after:
            Color(*WHITE)
            bw, bh = dp(22), dp(2.5)
            cx = self.x + self.width / 2 - bw / 2
            cy = self.y + self.height / 2
            for offset in (dp(7), 0, -dp(7)):
                Rectangle(pos=(cx, cy + offset - bh / 2), size=(bw, bh))

    def on_press(self, *_):
        App.get_running_app().toggle_drawer()


class BellBtn(ButtonBehavior, Widget):
    """Canvas-drawn bell icon button for the TopBar."""

    def __init__(self, **kw):
        super().__init__(**kw)
        self.size_hint = (None, None)
        self.size = (dp(44), dp(44))
        self.bind(pos=self._draw, size=self._draw)

    def _draw(self, *_):
        self.canvas.after.clear()
        cx, cy = self.center_x, self.center_y + dp(2)
        rx, ry = dp(7), dp(5)
        with self.canvas.after:
            Color(*WHITE)

            # Arc points: left-base → peak → right-base (13 points, ∩ shape)
            arc = [
                (cx - rx * math.cos(math.pi * i / 12),
                 cy + ry * math.sin(math.pi * i / 12))
                for i in range(13)
            ]

            # Filled dome — triangle fan from (cx, cy) to each arc segment
            dome_verts = [cx, cy, 0, 0]
            for px, py in arc:
                dome_verts += [px, py, 0, 0]
            dome_idx = []
            for i in range(12):
                dome_idx += [0, i + 1, i + 2]
            Mesh(vertices=dome_verts, indices=dome_idx, mode='triangles')

            # Filled body — trapezoid widening toward the rim
            bx = dp(9)
            body_verts = [
                arc[0][0],  arc[0][1],  0, 0,   # top-left  (= cx-rx, cy)
                arc[-1][0], arc[-1][1], 0, 0,   # top-right (= cx+rx, cy)
                cx + bx,    cy - dp(8), 0, 0,   # bottom-right
                cx - bx,    cy - dp(8), 0, 0,   # bottom-left
            ]
            Mesh(vertices=body_verts, indices=[0, 1, 2, 0, 2, 3], mode='triangles')

            # Filled rim bar
            Rectangle(pos=(cx - dp(11), cy - dp(10)), size=(dp(22), dp(3)))

            # Clapper
            Ellipse(pos=(cx - dp(2), cy - dp(14)), size=(dp(4), dp(4)))


class TopBar(BoxLayout):
    """Blue app bar. Hamburger on left; back arrow on left for sub-screens."""

    def __init__(self, title="", on_back=None, show_menu=True, on_bell=None, **kw):
        super().__init__(**kw)
        self.orientation = "horizontal"
        self.size_hint_y = None
        self.height = dp(48)
        self.padding = [dp(4), dp(4)]
        self.spacing = dp(4)

        with self.canvas.before:
            Color(*PRIMARY)
            self._rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._sync, size=self._sync)

        # Left side: hamburger (main screens) or back arrow (sub-screens)
        if show_menu and not on_back:
            self.add_widget(HamburgerBtn())
        elif on_back:
            b = Button(
                text="‹",
                size_hint=(None, None), size=(dp(36), dp(44)),
                background_normal="", background_color=(0, 0, 0, 0),
                color=WHITE, font_size=sp(20), bold=False,
            )
            b.bind(on_press=lambda *_: on_back())
            self.add_widget(b)

        lbl = Label(text=title, color=WHITE, font_size=sp(16), bold=True,
                    halign="left", valign="middle")
        lbl.bind(size=lbl.setter("text_size"))
        self.add_widget(lbl)

        # Right side: bell (main screens) or hamburger (sub-screens)
        if on_bell:
            bell = BellBtn()
            bell.bind(on_press=lambda *_: on_bell())
            self.add_widget(bell)
        elif show_menu and on_back:
            self.add_widget(HamburgerBtn())

    def _sync(self, *_):
        self._rect.pos = self.pos
        self._rect.size = self.size


DRAWER_WIDTH = dp(308)


class DrawerOverlay(Widget):
    """Semi-transparent backdrop; tap it to close the drawer."""

    def __init__(self, **kw):
        super().__init__(**kw)
        self.size_hint = (1, 1)
        self.opacity = 0
        self.disabled = True
        with self.canvas:
            Color(0, 0, 0, 1)
            self._rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._sync, size=self._sync)

    def _sync(self, *_):
        self._rect.pos = self.pos
        self._rect.size = self.size

    def on_touch_down(self, touch):
        if self.disabled:
            return False
        if self.collide_point(*touch.pos):
            App.get_running_app().close_drawer()
            return True
        return False


class DrawerPanel(BoxLayout):
    """Slide-in navigation drawer."""

    def __init__(self, nav_items, on_nav, **kw):
        super().__init__(**kw)
        self.orientation = "vertical"
        self.size_hint = (None, 1)
        self.width = Window.width * 0.80
        self._nav_btns = {}

        with self.canvas.before:
            Color(*WHITE)
            self._bg = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._sync_bg, size=self._sync_bg)

        # Header — white background, dark title
        header = BoxLayout(
            orientation="vertical",
            size_hint_y=None, height=dp(72),
            padding=[dp(20), dp(18), dp(16), dp(10)],
        )
        lbl = Label(
            text="Hyperlocal", color=TXT, font_size=sp(21), bold=True,
            halign="left", valign="bottom",
        )
        lbl.bind(size=lbl.setter("text_size"))
        header.add_widget(lbl)
        self.add_widget(header)

        # Thin divider below header
        div = Widget(size_hint_y=None, height=dp(1))
        with div.canvas:
            Color(0.88, 0.88, 0.90, 1)
            self._div_r = Rectangle(pos=div.pos, size=div.size)
        div.bind(
            pos=lambda i, v: setattr(self._div_r, "pos", v),
            size=lambda i, v: setattr(self._div_r, "size", v),
        )
        self.add_widget(div)

        # Nav items
        for item in nav_items:
            btn = Button(
                text=item["label"],
                size_hint_y=None, height=dp(52),
                background_normal="", background_color=WHITE,
                color=(0.25, 0.25, 0.28, 1),
                font_size=sp(16),
                halign="left", valign="middle",
                padding=[dp(20), 0, dp(8), 0],
            )
            btn.bind(size=lambda b, v: setattr(b, "text_size", (v[0] - dp(28), None)))
            btn.bind(on_press=lambda *_, s=item["screen"]: on_nav(s))
            self._nav_btns[item["screen"]] = btn
            self.add_widget(btn)

        self.add_widget(Widget())

    def set_active(self, screen):
        for s, btn in self._nav_btns.items():
            # Clear any previous active canvas
            btn.canvas.before.clear()
            if hasattr(btn, "_active_sync"):
                btn.unbind(pos=btn._active_sync, size=btn._active_sync)

            if s == screen:
                with btn.canvas.before:
                    Color(0.92, 0.95, 1.0, 1)
                    _bg = Rectangle(pos=btn.pos, size=btn.size)
                    Color(*PRIMARY)
                    _bar = Rectangle(pos=btn.pos, size=(dp(4), btn.height))

                def _sync(i, v, b=btn, bg=_bg, bar=_bar):
                    bg.pos  = b.pos
                    bg.size = b.size
                    bar.pos  = b.pos
                    bar.size = (dp(4), b.height)

                btn._active_sync = _sync
                btn.bind(pos=_sync, size=_sync)
                btn.background_color = (0, 0, 0, 0)
                btn.color = PRIMARY
                btn.bold = True
            else:
                btn.background_color = WHITE
                btn.color = (0.25, 0.25, 0.28, 1)
                btn.bold = False

    def _sync_bg(self, *_):
        self._bg.pos = self.pos
        self._bg.size = self.size


class StatusBadge(Label):
    def __init__(self, status="", **kw):
        super().__init__(**kw)
        self.text = status.upper()
        self.color = WHITE
        self.size_hint = (None, None)
        self.size = (dp(80), dp(20))
        self.font_size = sp(9)
        self.bold = True
        clr = STATUS_COLORS.get(status, (0.5, 0.5, 0.5, 1))
        with self.canvas.before:
            Color(*clr)
            self._rr = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(4)])
        self.bind(pos=self._sync, size=self._sync)

    def _sync(self, *_):
        self._rr.pos = self.pos
        self._rr.size = self.size


class TypeBadge(Label):
    """Pill showing 'REQUEST' or 'OFFER' — same dimensions as StatusBadge."""

    def __init__(self, task_type="request", **kw):
        super().__init__(**kw)
        self.text = "OFFER" if task_type == "offer" else "REQUEST"
        self.color = WHITE
        self.size_hint = (None, None)
        self.size = (dp(80), dp(20))
        self.font_size = sp(9)
        self.bold = True
        clr = ERROR if task_type == "offer" else SUCCESS
        with self.canvas.before:
            Color(*clr)
            self._rr = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(4)])
        self.bind(pos=self._sync, size=self._sync)

    def _sync(self, *_):
        self._rr.pos = self.pos
        self._rr.size = self.size


class FieldLabel(Label):
    def __init__(self, text, **kw):
        kw.setdefault("color", TXT2)
        kw.setdefault("font_size", sp(12))
        kw.setdefault("size_hint_y", None)
        kw.setdefault("height", dp(20))
        kw.setdefault("halign", "left")
        kw.setdefault("valign", "middle")
        super().__init__(text=text, **kw)
        self.bind(size=self.setter("text_size"))


class ErrLabel(Label):
    def __init__(self, **kw):
        kw.setdefault("color", ERROR)
        kw.setdefault("font_size", sp(13))
        kw.setdefault("size_hint_y", None)
        kw.setdefault("height", dp(28))
        kw.setdefault("halign", "left")
        super().__init__(**kw)
        self.bind(size=self.setter("text_size"))


_STAR_YELLOW = (1.0, 0.80, 0.0, 1)
_STAR_EMPTY  = (0.70, 0.70, 0.70, 1)


class RatingStars(BoxLayout):
    """Read-only star rating row.

    Stars are drawn directly in canvas.before (no child widgets per star),
    so there is exactly one canvas scope and one colour reset.
    canvas.after holds a permanent Color(1,1,1,1) that always fires last,
    guaranteeing the yellow star colour never bleeds into subsequent widgets.
    """

    def __init__(self, rating=None, star_size=dp(14), **kw):
        kw.setdefault("orientation", "horizontal")
        kw.setdefault("size_hint_y", None)
        kw.setdefault("height",      star_size + dp(4))
        super().__init__(**kw)
        self._rating    = rating
        self._star_size = star_size
        # Permanent reset — locked in once, survives set_rating() calls.
        with self.canvas.after:
            Color(1, 1, 1, 1)
        self.bind(pos=self._draw_stars, size=self._draw_stars)
        self._apply(rating)

    def set_rating(self, rating):
        self._rating = rating
        self.clear_widgets()
        self._apply(rating)

    def _apply(self, rating):
        self.canvas.before.clear()
        if rating is None:
            lbl = Label(
                text="No rating yet",
                color=TXT2, font_size=sp(11),
                halign="left", valign="middle",
            )
            lbl.bind(size=lbl.setter("text_size"))
            self.add_widget(lbl)
        else:
            self._draw_stars()

    def _draw_stars(self, *_):
        self.canvas.before.clear()
        if self._rating is None:
            return
        filled = round(self._rating)
        ss, gap = self._star_size, dp(2)
        with self.canvas.before:
            for i in range(5):
                cx    = self.x + ss * 0.5 + i * (ss + gap)
                cy    = self.center_y
                r_out = ss * 0.44
                r_in  = r_out * 0.40
                pts, mesh = [], []
                for j in range(10):
                    a = math.pi / 2 - j * math.pi / 5
                    r = r_out if j % 2 == 0 else r_in
                    x = cx + r * math.cos(a)
                    y = cy + r * math.sin(a)
                    pts  += [x, y]
                    mesh += [x, y, 0, 0]
                if i < filled:
                    Color(*_STAR_YELLOW)
                    verts = [cx, cy, 0, 0] + mesh
                    idxs  = []
                    for k in range(10):
                        idxs += [0, k + 1, (k + 1) % 10 + 1]
                    Mesh(vertices=verts, indices=idxs, mode="triangles")
                else:
                    Color(*_STAR_EMPTY)
                    Line(points=pts, width=1.0, close=True)


class StarWidget(ButtonBehavior, Widget):
    """Single canvas-drawn star; no font dependency."""

    def __init__(self, val, **kw):
        super().__init__(size_hint_y=1, **kw)
        self._val = val
        self._filled = False
        self.bind(pos=self._draw, size=self._draw)

    def set_filled(self, filled):
        self._filled = filled
        self._draw()

    def _draw(self, *_):
        self.canvas.clear()
        cx, cy = self.center_x, self.center_y
        r_out = min(self.width, self.height) * 0.38
        r_in = r_out * 0.42
        flat_pts, mesh_pts = [], []
        for i in range(10):
            angle = math.pi / 2 - i * math.pi / 5
            r = r_out if i % 2 == 0 else r_in
            x = cx + r * math.cos(angle)
            y = cy + r * math.sin(angle)
            flat_pts += [x, y]
            mesh_pts += [x, y, 0, 0]
        with self.canvas:
            Color(*(PRIMARY if self._filled else TXT2))
            if self._filled:
                verts = [cx, cy, 0, 0] + mesh_pts
                idxs = []
                for i in range(10):
                    idxs += [0, i + 1, (i + 1) % 10 + 1]
                Mesh(vertices=verts, indices=idxs, mode='triangles')
            else:
                Line(points=flat_pts, width=1.5, close=True)


class StarRow(BoxLayout):
    """Five tappable canvas stars; read .rating for the selected value (0 = none)."""

    def __init__(self, **kw):
        super().__init__(
            orientation="horizontal", spacing=dp(4),
            size_hint_y=None, height=dp(48), **kw,
        )
        self.rating = 0
        self._stars = []
        for i in range(1, 6):
            star = StarWidget(val=i)
            star.bind(on_press=lambda s, *_: self._tapped(s))
            self._stars.append(star)
            self.add_widget(star)

    def _tapped(self, star):
        self.rating = star._val
        self._refresh()

    def _refresh(self):
        for star in self._stars:
            star.set_filled(star._val <= self.rating)

    def reset(self):
        self.rating = 0
        self._refresh()


class FilterChips(BoxLayout):
    """Filter-by dropdown row. Calls on_filter(key) on selection."""

    _OPTIONS = [("all", "All"), ("request", "Requests"), ("offer", "Offers")]

    def __init__(self, on_filter, **kw):
        kw.setdefault("size_hint_y", None)
        kw.setdefault("height", dp(36))
        super().__init__(
            orientation="horizontal",
            padding=[dp(12), dp(4), dp(12), dp(4)],
            spacing=dp(8),
            **kw,
        )
        self._on_filter = on_filter
        self._active = "all"
        self._labels = dict(self._OPTIONS)
        self._panel = None

        # Filter icon: three horizontal lines drawn on canvas
        icon = Widget(size_hint=(None, 1), width=dp(20))
        with icon.canvas:
            self._ic = [Color(*TXT2)]
            for idx, w in enumerate([dp(14), dp(10), dp(6)]):
                self._ic.append(Line(width=1.4))
        def _draw_icon(*_):
            cx = icon.center_x
            for idx, w in enumerate([dp(14), dp(10), dp(6)]):
                y = icon.center_y + dp(4) - idx * dp(4)
                self._ic[idx + 1].points = [cx - w/2, y, cx + w/2, y]
        icon.bind(pos=_draw_icon, size=_draw_icon)
        self.add_widget(icon)

        lbl = Label(
            text="Filter by:",
            color=TXT2, font_size=sp(12),
            size_hint=(None, 1), width=dp(76),
            halign="left", valign="middle",
            text_size=(dp(76), None),
        )
        self.add_widget(lbl)

        self._btn = Button(
            text="All",
            background_normal="", background_color=WHITE,
            color=TXT, font_size=sp(13), bold=True,
            size_hint=(1, 1),
            padding=[dp(10), 0, dp(26), 0],
        )
        with self._btn.canvas.after:
            Color(0.78, 0.78, 0.80, 1)
            self._border = Line(rounded_rectangle=[0, 0, 1, 1, dp(6)], width=1)
            Color(*TXT2)
            self._chevron = Line(points=[0, 0, 0, 0, 0, 0], width=1.4,
                                 cap='round', joint='round')
        self._btn.bind(pos=self._sync_border, size=self._sync_border)
        self._btn.bind(on_press=self._toggle)
        self.add_widget(self._btn)

    def _sync_border(self, *_):
        b = self._btn
        self._border.rounded_rectangle = [b.x, b.y, b.width, b.height, dp(6)]
        # Chevron: small "v" shape on the right side of the button
        ax = b.right - dp(14)
        ay = b.center_y + dp(2)
        s  = dp(4)
        self._chevron.points = [ax - s, ay, ax, ay - s, ax + s, ay]

    def _toggle(self, *_):
        if self._panel:
            self._dismiss()
        else:
            self._open()

    def _open(self):
        from kivy.core.window import Window

        n = len(self._OPTIONS)
        panel_h = dp(36) * n

        # Button's bottom-left in window coordinates
        bx, by = self._btn.to_window(*self._btn.pos)

        panel = BoxLayout(
            orientation="vertical",
            size_hint=(None, None),
            size=(self._btn.width, panel_h),
            pos=(bx, by - panel_h),
        )
        with panel.canvas.before:
            Color(*WHITE)
            _r = Rectangle(pos=panel.pos, size=panel.size)
        panel.bind(
            pos=lambda _, v: setattr(_r, "pos", v),
            size=lambda _, v: setattr(_r, "size", v),
        )
        with panel.canvas.after:
            Color(0.82, 0.82, 0.84, 1)
            Line(rectangle=[panel.x, panel.y, panel.width, panel.height], width=1)

        for key, label in self._OPTIONS:
            item = Button(
                text=label,
                size_hint_y=None, height=dp(36),
                background_normal="", background_color=WHITE,
                color=TXT, font_size=sp(13), bold=True,
                halign="left", valign="middle",
                padding=[dp(16), 0],
            )
            item.bind(size=item.setter("text_size"))
            item.bind(on_release=lambda b, k=key: self._select(k))
            panel.add_widget(item)

        Window.add_widget(panel)
        self._panel = panel
        Window.bind(on_touch_down=self._on_window_touch)

    def _on_window_touch(self, _win, touch):
        if self._panel and not self._panel.collide_point(*touch.pos):
            self._dismiss()

    def _dismiss(self):
        from kivy.core.window import Window
        if self._panel:
            Window.remove_widget(self._panel)
            self._panel = None
            Window.unbind(on_touch_down=self._on_window_touch)

    def _select(self, key):
        self._active = key
        self._btn.text = self._labels[key]
        self._dismiss()
        self._on_filter(key)

    def reset(self):
        self._active = "all"
        self._btn.text = "All"
        self._dismiss()


class TaskCard(ButtonBehavior, BoxLayout):
    """Tappable card showing task summary."""

    def __init__(self, task, active_tab=None, full_desc=False, **kw):
        super().__init__(**kw)
        self.task = task
        self.orientation = "vertical"
        self.size_hint_y = None
        self.padding = [dp(14), dp(10), dp(14), dp(10)]
        self.spacing = dp(4)
        self.bind(minimum_height=self.setter("height"))

        accent_color = ERROR if task.get("task_type") == "offer" else SUCCESS
        with self.canvas.before:
            Color(0, 0, 0, 0.04)
            self._shadow = RoundedRectangle(
                pos=(self.x + dp(1), self.y - dp(1)),
                size=self.size, radius=[dp(10)],
            )
            Color(*WHITE)
            self._bg = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(10)])
            Color(0.90, 0.90, 0.92, 1)
            self._card_border = Line(
                rounded_rectangle=[*self.pos, *self.size, dp(10)], width=0.6
            )
            Color(*accent_color)
            self._accent = RoundedRectangle(
                pos=self.pos, size=(dp(4), self.height),
                radius=[dp(10), 0, 0, dp(10)],
            )
        self.bind(pos=self._sync, size=self._sync)

        # Row 1 — title + status badge (unchanged from original)
        display_status = "deleted" if task.get("hidden_from_creator") else task.get("status", "open")
        reward    = task.get("reward")
        task_type = task.get("task_type", "request")
        row1 = BoxLayout(size_hint_y=None, height=dp(28))
        t = Label(
            text=task.get("title", ""),
            color=TXT, font_size=sp(14), bold=True,
            halign="left", valign="middle",
        )
        t.bind(size=t.setter("text_size"))
        row1.add_widget(t)
        row1.add_widget(StatusBadge(status=display_status))
        self.add_widget(row1)

        desc = task.get("description")
        if desc:
            if full_desc:
                d = Label(
                    text=desc, color=TXT2, font_size=sp(12),
                    halign="left", valign="top",
                    size_hint_y=None, height=dp(20),
                )
                d.bind(
                    width=lambda inst, w: setattr(inst, "text_size", (w, None)),
                    texture_size=lambda inst, ts: setattr(inst, "height", max(ts[1], dp(20))),
                )
            else:
                d = Label(
                    text=desc, color=TXT2, font_size=sp(12),
                    halign="left", valign="top",
                    size_hint_y=None, height=dp(34),
                    shorten=True, shorten_from="right",
                )
                d.bind(size=d.setter("text_size"))
            self.add_widget(d)

        # Abort reason — auto-height so it never clips
        abort_reason = task.get("abort_reason")
        if abort_reason and task.get("status") == "aborted":
            acc_name = task.get("acceptor_name") or "Acceptor"
            ar = Label(
                text=f"Aborted by {acc_name}: {abort_reason}",
                color=ERROR, font_size=sp(11),
                halign="left", valign="top",
                size_hint_y=None, height=dp(20),
            )
            ar.bind(
                width=lambda inst, w: setattr(inst, "text_size", (w, None)),
                texture_size=lambda inst, ts: setattr(inst, "height", max(ts[1], dp(20))),
            )
            self.add_widget(ar)

        # Price amount + (price label | type badge) row
        if reward is not None:
            reward_color = ERROR if task_type == "offer" else SUCCESS
            price_label  = "Price Charged" if task_type == "offer" else "Price Offered"
            r = Label(
                text=f"₹{reward:g}", color=reward_color, font_size=sp(14), bold=True,
                size_hint_y=None, height=dp(22),
                halign="left", valign="middle",
            )
            r.bind(size=r.setter("text_size"))
            self.add_widget(r)
            # Price label on left, type badge on right — same row
            pl_row = BoxLayout(size_hint_y=None, height=dp(20))
            pl = Label(
                text=price_label, color=TXT2, font_size=sp(11),
                halign="left", valign="middle",
            )
            pl.bind(size=pl.setter("text_size"))
            pl_row.add_widget(pl)
            pl_row.add_widget(TypeBadge(task_type=task_type))
            self.add_widget(pl_row)
        else:
            # No price — type badge right-aligned on its own row
            type_row = BoxLayout(size_hint_y=None, height=dp(20))
            type_row.add_widget(Widget())
            type_row.add_widget(TypeBadge(task_type=task_type))
            self.add_widget(type_row)

        # Bottom rows — person name + timestamp, then star rating
        if active_tab == "posted":
            if task.get("accepted_by"):
                person_name   = f"Taken By: {task.get('acceptor_name') or str(task['accepted_by'])}"
                person_rating = task.get("acceptor_rating")
            else:
                person_name   = None
                person_rating = None
        elif active_tab == "taken":
            person_name   = f"Posted By: {task.get('creator_name') or str(task.get('created_by', ''))}"
            person_rating = task.get("creator_rating")
        else:
            person_name   = f"Posted By: {task.get('creator_name') or str(task.get('created_by', ''))}"
            person_rating = task.get("creator_rating")

        status = task.get("status", "open")
        ts_raw = (
            task.get("updated_at") if status != "open" else None
        ) or task.get("created_at", "")
        ts = _fmt_dt(ts_raw)

        if person_name or ts:
            name_row = BoxLayout(size_hint_y=None, height=dp(18))
            # Always add the name label — when empty it acts as a spacer
            # that keeps the timestamp pinned to the right edge.
            by_lbl = Label(
                text=person_name or "", color=TXT2, font_size=sp(10),
                halign="left", valign="middle",
            )
            by_lbl.bind(size=by_lbl.setter("text_size"))
            name_row.add_widget(by_lbl)
            if ts:
                ts_lbl = Label(
                    text=ts, color=TXT2, font_size=sp(10),
                    size_hint=(None, 1), width=dp(90),
                    halign="right", valign="middle",
                    text_size=(dp(90), None),
                )
                name_row.add_widget(ts_lbl)
            self.add_widget(name_row)

        if person_name is not None:
            self.add_widget(RatingStars(rating=person_rating, star_size=dp(11)))

    def on_press(self):
        Animation(opacity=0.82, duration=0.07).start(self)

    def on_release(self):
        Animation(opacity=1.0, duration=0.14).start(self)

    def _sync(self, *_):
        self._shadow.pos = (self.x + dp(1), self.y - dp(2))
        self._shadow.size = self.size
        self._bg.pos = self.pos
        self._bg.size = self.size
        self._card_border.rounded_rectangle = [*self.pos, *self.size, dp(10)]
        self._accent.pos = self.pos
        self._accent.size = (dp(4), self.height)

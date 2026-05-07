from datetime import datetime, timezone

from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.metrics import dp, sp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget

from api import api
from widgets import TopBar
from theme import BG, ERROR, PRIMARY, TXT, TXT2, WHITE


def _fmt_time(iso_str):
    if not iso_str:
        return ""
    try:
        dt = datetime.fromisoformat(str(iso_str).replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        diff = now - dt
        if diff.days == 0:
            h = diff.seconds // 3600
            m = (diff.seconds % 3600) // 60
            if h > 0:
                return f"{h}h ago"
            return f"{m}m ago" if m > 0 else "just now"
        if diff.days == 1:
            return "yesterday"
        return dt.strftime("%d %b")
    except Exception:
        return ""


class _NotifCard(BoxLayout):
    def __init__(self, notif, **kw):
        super().__init__(**kw)
        self.orientation = "vertical"
        self.size_hint_y = None
        self.padding = [dp(14), dp(12)]
        self.spacing = dp(4)
        self.bind(minimum_height=self.setter("height"))

        is_read = notif.get("is_read", True)
        accent = PRIMARY if not is_read else (0.82, 0.82, 0.85, 1)

        with self.canvas.before:
            Color(*WHITE)
            self._bg = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(10)])
            Color(*accent)
            self._bar = RoundedRectangle(
                pos=self.pos, size=(dp(4), self.height),
                radius=[dp(10), 0, 0, dp(10)],
            )
        self.bind(pos=self._sync, size=self._sync)

        title_lbl = Label(
            text=notif.get("title", ""),
            color=TXT, font_size=sp(14), bold=True,
            halign="left", valign="top",
            size_hint_y=None, height=dp(20),
        )
        title_lbl.bind(
            width=lambda inst, w: setattr(inst, "text_size", (w, None)),
            texture_size=lambda inst, ts: setattr(inst, "height", max(ts[1], dp(20))),
        )
        self.add_widget(title_lbl)

        body_lbl = Label(
            text=notif.get("body", ""),
            color=TXT2, font_size=sp(13),
            halign="left", valign="top",
            size_hint_y=None, height=dp(18),
        )
        body_lbl.bind(
            width=lambda inst, w: setattr(inst, "text_size", (w, None)),
            texture_size=lambda inst, ts: setattr(inst, "height", max(ts[1], dp(18))),
        )
        self.add_widget(body_lbl)

        time_lbl = Label(
            text=_fmt_time(notif.get("created_at")),
            color=(0.60, 0.60, 0.63, 1), font_size=sp(11),
            halign="right", valign="middle",
            size_hint_y=None, height=dp(16),
        )
        time_lbl.bind(size=time_lbl.setter("text_size"))
        self.add_widget(time_lbl)

    def _sync(self, *_):
        self._bg.pos = self.pos
        self._bg.size = self.size
        self._bar.pos = self.pos
        self._bar.size = (dp(4), self.height)


class NotificationsScreen(Screen):
    def __init__(self, **kw):
        kw.setdefault("name", "notifications")
        super().__init__(**kw)
        self._build()

    def _build(self):
        root = BoxLayout(orientation="vertical")
        with root.canvas.before:
            Color(*BG)
            self._bg = Rectangle(pos=root.pos, size=root.size)
        root.bind(
            pos=lambda _, v: setattr(self._bg, "pos", v),
            size=lambda _, v: setattr(self._bg, "size", v),
        )

        root.add_widget(TopBar(
            title="Notifications",
            on_back=lambda: setattr(self.manager, "current", self._from_screen),
            show_menu=False,
        ))

        self._status = Label(
            text="Loading…", color=TXT2, font_size=sp(15),
            size_hint_y=None, height=dp(40),
        )
        root.add_widget(self._status)

        scroll = ScrollView()
        self._grid = GridLayout(
            cols=1, spacing=dp(8),
            padding=[dp(12), dp(8), dp(12), dp(24)],
            size_hint_y=None,
        )
        self._grid.bind(minimum_height=self._grid.setter("height"))
        scroll.add_widget(self._grid)
        root.add_widget(scroll)
        self.add_widget(root)

        self._from_screen = "task_list"

    def on_pre_enter(self):
        self._grid.clear_widgets()
        self._status.text = "Loading…"
        self._status.opacity = 1

    def on_enter(self):
        api("GET", "/notifications/mine",
            on_success=self._show, on_error=self._on_err)

    def _show(self, notifs):
        self._grid.clear_widgets()
        if not notifs:
            self._status.text = "No notifications in the last 7 days"
            self._status.opacity = 1
            return
        self._status.opacity = 0
        for n in notifs:
            self._grid.add_widget(_NotifCard(notif=n))

    def _on_err(self, error):
        self._status.text = f"Error: {error}"
        self._status.opacity = 1

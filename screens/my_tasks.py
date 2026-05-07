from kivy.animation import Animation
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle
from kivy.metrics import dp, sp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget

from api import api
from widgets import FilterChips, TaskCard, TopBar
from theme import BG, PRIMARY, TXT2, WHITE


_POLL_FALLBACK_SECONDS = 15


class MyTasksScreen(Screen):
    def __init__(self, **kw):
        kw.setdefault("name", "my_tasks")
        super().__init__(**kw)
        self._active_tab = "posted"
        self._tasks = []
        self._filter = "all"
        self._ind_colors = {}
        self._poll_event = None
        self._build()

    def _build(self):
        outer = FloatLayout()

        main = BoxLayout(orientation="vertical")
        with main.canvas.before:
            Color(*BG)
            self._rbg = Rectangle(pos=main.pos, size=main.size)
        main.bind(
            pos=lambda i, v: setattr(self._rbg, "pos", v),
            size=lambda i, v: setattr(self._rbg, "size", v),
        )

        main.add_widget(TopBar(
            title="My Tasks",
            on_bell=lambda: self._go_notifications(),
        ))

        # Sub-tabs
        tab_area = BoxLayout(
            orientation="vertical",
            size_hint_y=None, height=dp(47),
        )
        with tab_area.canvas.before:
            Color(*WHITE)
            _tab_area_bg = Rectangle(pos=tab_area.pos, size=tab_area.size)
        tab_area.bind(
            pos=lambda i, v: setattr(_tab_area_bg, "pos", v),
            size=lambda i, v: setattr(_tab_area_bg, "size", v),
        )

        tab_row = BoxLayout(
            orientation="horizontal",
            size_hint_y=None, height=dp(44),
            padding=[dp(12), dp(4), dp(12), dp(0)],
            spacing=dp(8),
        )
        self._tab_posted = self._make_tab("Posted by Me", "posted")
        self._tab_taken  = self._make_tab("Taken by Me",  "taken")
        tab_row.add_widget(self._tab_posted)
        tab_row.add_widget(self._tab_taken)
        tab_area.add_widget(tab_row)

        # Underline indicator bar
        ind_row = BoxLayout(
            orientation="horizontal",
            size_hint_y=None, height=dp(3),
            padding=[dp(12), 0, dp(12), 0],
            spacing=dp(8),
        )
        for key in ("posted", "taken"):
            ind = Widget(size_hint_x=1)
            with ind.canvas:
                c = Color(0, 0, 0, 0)
                r = Rectangle(pos=ind.pos, size=ind.size)
            ind.bind(
                pos=lambda i, v, _r=r: setattr(_r, "pos", v),
                size=lambda i, v, _r=r: setattr(_r, "size", v),
            )
            self._ind_colors[key] = c
            ind_row.add_widget(ind)
        tab_area.add_widget(ind_row)

        main.add_widget(tab_area)
        self._filter_row = FilterChips(on_filter=self._apply_filter)
        main.add_widget(self._filter_row)

        self._status = Label(
            text="Loading…", color=TXT2, font_size=sp(15),
            size_hint_y=None, height=dp(40),
        )
        main.add_widget(self._status)

        scroll = ScrollView()
        self._grid = GridLayout(
            cols=1, spacing=dp(10),
            padding=[dp(16), dp(8), dp(16), dp(80)],
            size_hint_y=None,
        )
        self._grid.bind(minimum_height=self._grid.setter("height"))
        scroll.add_widget(self._grid)
        main.add_widget(scroll)
        outer.add_widget(main)

        # Floating action button — fixed at bottom-right, only shown on Posted tab
        self._fab = Button(
            text="+",
            size_hint=(None, None), size=(dp(56), dp(56)),
            background_normal="", background_color=PRIMARY,
            color=WHITE, font_size=sp(28), bold=True,
            pos_hint={"right": 0.96, "y": 0.03},
        )
        self._fab.bind(on_press=lambda *_: setattr(self.manager, "current", "create_task"))
        outer.add_widget(self._fab)

        self.add_widget(outer)

    def _make_tab(self, text, key):
        btn = Button(
            text=text,
            background_normal="", background_color=WHITE,
            font_size=sp(13), bold=True,
            color=TXT2,
        )
        btn.bind(on_press=lambda *_, k=key: self._switch_tab(k))
        return btn

    def _switch_tab(self, key):
        self._active_tab = key
        self._refresh_tabs()
        self._filter = "all"
        self._filter_row.reset()
        self._fab.opacity = 1 if key == "posted" else 0
        self._fab.disabled = key != "posted"
        self._load()

    def _refresh_tabs(self):
        for btn, key in [(self._tab_posted, "posted"), (self._tab_taken, "taken")]:
            if key == self._active_tab:
                btn.background_color = WHITE
                btn.color = PRIMARY
                btn.bold = True
                self._ind_colors[key].rgba = PRIMARY
            else:
                btn.background_color = WHITE
                btn.color = TXT2
                btn.bold = False
                self._ind_colors[key].rgba = (0, 0, 0, 0)

    def on_pre_enter(self):
        self._grid.clear_widgets()
        self._status.text = "Loading…"
        self._status.opacity = 1

    def on_enter(self):
        self._refresh_tabs()
        self._fab.opacity = 1 if self._active_tab == "posted" else 0
        self._fab.disabled = self._active_tab != "posted"
        self._load()
        self._poll_event = Clock.schedule_interval(
            lambda dt: self._bg_refresh(), _POLL_FALLBACK_SECONDS
        )

    def on_leave(self):
        if self._poll_event:
            self._poll_event.cancel()
            self._poll_event = None

    def _load(self):
        self._status.text = "Loading…"
        self._status.opacity = 1
        self._grid.clear_widgets()
        path = "/tasks/mine/posted" if self._active_tab == "posted" else "/tasks/mine/taken"
        api("GET", path, on_success=self._show, on_error=self._on_err)

    def _show(self, tasks):
        self._tasks = tasks
        self._render_filtered()

    def _bg_refresh(self):
        path = "/tasks/mine/posted" if self._active_tab == "posted" else "/tasks/mine/taken"
        api("GET", path, on_success=self._bg_show, on_error=None)

    def _bg_show(self, tasks):
        if self._tasks_changed(tasks):
            self._tasks = tasks
            self._render_filtered(animate=False)

    def _tasks_changed(self, new_tasks):
        if len(new_tasks) != len(self._tasks):
            return True
        for old, new in zip(self._tasks, new_tasks):
            if old.get("id") != new.get("id") or old.get("status") != new.get("status"):
                return True
        return False

    def _apply_filter(self, key):
        self._filter = key
        self._render_filtered()

    def _render_filtered(self, animate=True):
        self._grid.clear_widgets()
        filtered = (
            self._tasks if self._filter == "all"
            else [t for t in self._tasks if t.get("task_type", "request") == self._filter]
        )
        if not filtered:
            self._status.text = "No tasks match the selected filter"
            self._status.opacity = 1
            return
        self._status.opacity = 0
        for i, task in enumerate(filtered):
            card = TaskCard(task=task, active_tab=self._active_tab)
            if animate:
                card.opacity = 0
            card.bind(on_press=lambda *_, t=task: self._go_detail(t["id"]))
            self._grid.add_widget(card)
            if animate:
                Clock.schedule_once(
                    lambda dt, c=card: Animation(opacity=1, duration=0.25, t='out_quad').start(c),
                    i * 0.05,
                )

    def _on_err(self, error):
        self._status.text = f"Error: {error}"

    def _go_notifications(self):
        notif_screen = self.manager.get_screen("notifications")
        notif_screen._from_screen = "my_tasks"
        self.manager.current = "notifications"

    def _go_detail(self, task_id):
        if self.manager.current != "my_tasks":
            return
        detail = self.manager.get_screen("task_detail")
        detail.task_id = task_id
        detail._from_screen = "my_tasks"
        self.manager.current = "task_detail"

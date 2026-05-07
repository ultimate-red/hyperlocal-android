from kivy.animation import Animation
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle
from kivy.metrics import dp, sp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.uix.scrollview import ScrollView

from api import api
from widgets import FilterChips, TaskCard, TopBar
from theme import BG, TXT2


_POLL_FALLBACK_SECONDS = 15


class TaskListScreen(Screen):
    def __init__(self, **kw):
        kw.setdefault("name", "task_list")
        super().__init__(**kw)
        self._tasks = []
        self._filter = "all"
        self._poll_event = None
        self._build()

    def _build(self):
        root = FloatLayout()

        main = BoxLayout(orientation="vertical")
        with main.canvas.before:
            Color(*BG)
            self._bg = Rectangle(pos=main.pos, size=main.size)
        main.bind(
            pos=lambda i, v: setattr(self._bg, "pos", v),
            size=lambda i, v: setattr(self._bg, "size", v),
        )

        main.add_widget(TopBar(
            title="Open Tasks",
            on_bell=lambda: self._go_notifications(),
        ))
        self._filter_row = FilterChips(on_filter=self._apply_filter)
        main.add_widget(self._filter_row)

        self._status = Label(
            text="Loading…", color=TXT2, font_size=sp(15),
            size_hint_y=None, height=dp(40),
        )
        main.add_widget(self._status)

        scroll = ScrollView()
        self._grid = GridLayout(
            cols=1, spacing=dp(6),
            padding=[dp(12), dp(6), dp(12), dp(80)],
            size_hint_y=None,
        )
        self._grid.bind(minimum_height=self._grid.setter("height"))
        scroll.add_widget(self._grid)
        main.add_widget(scroll)
        root.add_widget(main)
        self.add_widget(root)

    def on_pre_enter(self):
        self._grid.clear_widgets()
        self._status.text = "Loading…"
        self._status.opacity = 1

    def on_enter(self):
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
        api("GET", "/tasks/", on_success=self._show, on_error=self._on_err)

    def _show(self, tasks):
        self._tasks = tasks
        self._render_filtered()

    def _bg_refresh(self):
        api("GET", "/tasks/", on_success=self._bg_show, on_error=None)

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
            card = TaskCard(task=task)
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
        notif_screen._from_screen = "task_list"
        self.manager.current = "notifications"

    def _go_detail(self, task_id):
        if self.manager.current != "task_list":
            return
        detail = self.manager.get_screen("task_detail")
        detail.task_id = task_id
        detail._from_screen = "task_list"
        self.manager.current = "task_detail"

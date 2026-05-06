from kivy.graphics import Color, Line, Rectangle, RoundedRectangle
from kivy.metrics import dp, sp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.screenmanager import Screen
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget

from api import api
from widgets import ErrLabel, FieldLabel, PrimaryBtn, StyledInput, TopBar
from theme import BG, PRIMARY, TXT, TXT2, WHITE


class CreateTaskScreen(Screen):
    def __init__(self, **kw):
        kw.setdefault("name", "create_task")
        super().__init__(**kw)
        self._task_type = "request"
        self._build()

    def _build(self):
        root = BoxLayout(orientation="vertical")
        root.add_widget(TopBar(title="Create Task"))

        content = BoxLayout(
            orientation="vertical",
            padding=[dp(16), dp(12)],
            spacing=dp(10),
            size_hint_y=None,
        )
        content.bind(minimum_height=content.setter("height"))

        with content.canvas.before:
            Color(*BG)
            self._bg = Rectangle(pos=content.pos, size=content.size)
        content.bind(
            pos=lambda i, v: setattr(self._bg, "pos", v),
            size=lambda i, v: setattr(self._bg, "size", v),
        )

        scroll = ScrollView()

        content.add_widget(FieldLabel("Task Type"))

        # Pill segmented control
        pill = BoxLayout(
            orientation="horizontal",
            size_hint_y=None, height=dp(38),
        )
        with pill.canvas.before:
            Color(0.86, 0.86, 0.88, 1)
            self._pill_track = RoundedRectangle(pos=pill.pos, size=pill.size, radius=[dp(19)])
        pill.bind(
            pos=lambda i, v: setattr(self._pill_track, "pos", v),
            size=lambda i, v: setattr(self._pill_track, "size", v),
        )
        self._type_btns = {}
        for key, label in [("request", "I need help"), ("offer", "I'm offering")]:
            btn = Button(
                text=label,
                background_normal="", background_color=(0, 0, 0, 0),
                font_size=sp(13), bold=True,
            )
            btn.bind(on_press=lambda *_, k=key: self._set_type(k))
            self._type_btns[key] = btn
            pill.add_widget(btn)
        content.add_widget(pill)
        self._refresh_type_btns()

        content.add_widget(FieldLabel("Title *"))
        self._title = StyledInput(hint_text="Task title (required)", height=dp(50))
        content.add_widget(self._title)

        content.add_widget(FieldLabel("Description"))
        self._desc = TextInput(
            hint_text="Optional description",
            background_normal="", background_active="", background_color=WHITE,
            foreground_color=TXT, cursor_color=PRIMARY,
            hint_text_color=(0.55, 0.55, 0.55, 1),
            size_hint_y=None, height=dp(216),
            padding=[dp(12), dp(10)], font_size=sp(13), multiline=True,
        )
        with self._desc.canvas.after:
            Color(0.86, 0.86, 0.88, 1)
            self._desc_border = Line(rounded_rectangle=[0, 0, 1, 1, dp(6)], width=0.8)
        self._desc.bind(pos=self._sync_desc_border, size=self._sync_desc_border)
        content.add_widget(self._desc)

        self._reward_lbl = FieldLabel("Reward (₹)")
        content.add_widget(self._reward_lbl)
        self._reward = StyledInput(hint_text="Amount in ₹ (optional)",
                                   input_filter="float", height=dp(50))
        content.add_widget(self._reward)
        content.add_widget(Widget(size_hint_y=None, height=dp(12)))

        with root.canvas.before:
            Color(*BG)
            self._rbg = Rectangle(pos=root.pos, size=root.size)
        root.bind(
            pos=lambda i, v: setattr(self._rbg, "pos", v),
            size=lambda i, v: setattr(self._rbg, "size", v),
        )

        scroll.add_widget(content)
        root.add_widget(scroll)

        # Pinned bottom bar — always visible, not inside the scroll
        bottom = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            padding=[dp(16), dp(10), dp(16), dp(14)],
            spacing=dp(4),
        )
        bottom.bind(minimum_height=bottom.setter("height"))
        with bottom.canvas.before:
            Color(*BG)
            self._bbg = Rectangle(pos=bottom.pos, size=bottom.size)
        bottom.bind(
            pos=lambda i, v: setattr(self._bbg, "pos", v),
            size=lambda i, v: setattr(self._bbg, "size", v),
        )
        self._btn = PrimaryBtn(text="Create Task")
        self._btn.bind(on_press=self._submit)
        bottom.add_widget(self._btn)
        self._err = ErrLabel(text="")
        bottom.add_widget(self._err)
        root.add_widget(bottom)

        self.add_widget(root)

    def _sync_desc_border(self, *_):
        d = self._desc
        self._desc_border.rounded_rectangle = [d.x, d.y, d.width, d.height, dp(6)]

    def on_leave(self):
        self._err.text = ""

    def _set_type(self, key):
        self._task_type = key
        self._refresh_type_btns()
        self._reward_lbl.text = "Price (₹)" if key == "offer" else "Reward (₹)"

    def _refresh_type_btns(self):
        for key, btn in self._type_btns.items():
            btn.canvas.before.clear()
            if hasattr(btn, "_pill_sync"):
                btn.unbind(pos=btn._pill_sync, size=btn._pill_sync)
            if key == self._task_type:
                with btn.canvas.before:
                    Color(*WHITE)
                    btn._pill_rr = RoundedRectangle(
                        pos=(btn.x + dp(3), btn.y + dp(3)),
                        size=(btn.width - dp(6), btn.height - dp(6)),
                        radius=[dp(17)],
                    )
                def _sync(i, v, b=btn):
                    b._pill_rr.pos  = (b.x + dp(3), b.y + dp(3))
                    b._pill_rr.size = (b.width - dp(6), b.height - dp(6))
                btn._pill_sync = _sync
                btn.bind(pos=_sync, size=_sync)
                btn.color = TXT
                btn.bold = True
            else:
                btn.color = TXT2
                btn.bold = False

    def _submit(self, *_):
        title = self._title.text.strip()
        if not title:
            self._err.text = "Title is required."
            return
        self._err.text = ""
        self._btn.text = "Creating…"
        self._btn.disabled = True

        body = {"title": title, "task_type": self._task_type}
        desc = self._desc.text.strip()
        if desc:
            body["description"] = desc
        rwd = self._reward.text.strip()
        if rwd:
            try:
                body["reward"] = float(rwd)
            except ValueError:
                self._err.text = "Enter a valid reward amount."
                self._btn.text = "Create Task"
                self._btn.disabled = False
                return

        api("POST", "/tasks/", body=body,
            on_success=self._created, on_error=self._on_err)

    def _created(self, _):
        self._title.text = ""
        self._desc.text = ""
        self._reward.text = ""
        self._btn.text = "Create Task"
        self._btn.disabled = False
        self._task_type = "request"
        self._refresh_type_btns()
        self._reward_lbl.text = "Reward (₹)"
        if self.manager and self.manager.current == "create_task":
            self.manager.current = "task_list"

    def _on_err(self, error):
        self._err.text = str(error)
        self._btn.text = "Create Task"
        self._btn.disabled = False

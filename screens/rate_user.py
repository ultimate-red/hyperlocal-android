from kivy.graphics import Color, Line, Rectangle
from kivy.metrics import dp, sp
from kivy.properties import NumericProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput

from api import api
from widgets import ErrLabel, FieldLabel, PrimaryBtn, StarRow, TopBar
from theme import BG, PRIMARY, TXT, WHITE


class RateUserScreen(Screen):
    task_id = NumericProperty(0)

    def __init__(self, **kw):
        kw.setdefault("name", "rate_user")
        super().__init__(**kw)
        self.reviewee_name = ""
        self._from_screen = "task_detail"
        self._build()

    def _build(self):
        root = BoxLayout(orientation="vertical")
        with root.canvas.before:
            Color(*BG)
            self._bg = Rectangle(pos=root.pos, size=root.size)
        root.bind(
            pos=lambda i, v: setattr(self._bg, "pos", v),
            size=lambda i, v: setattr(self._bg, "size", v),
        )
        root.add_widget(TopBar(
            title="Rate User",
            on_back=self._go_back,
            show_menu=False,
        ))

        content = BoxLayout(
            orientation="vertical",
            padding=[dp(16), dp(16)],
            spacing=dp(12),
            size_hint_y=None,
        )
        content.bind(minimum_height=content.setter("height"))

        scroll = ScrollView()

        self._name_lbl = Label(
            text="",
            color=TXT, font_size=sp(15), bold=True,
            halign="left", valign="middle",
            size_hint_y=None, height=dp(32),
        )
        self._name_lbl.bind(size=self._name_lbl.setter("text_size"))
        content.add_widget(self._name_lbl)

        self._star_row = StarRow()
        content.add_widget(self._star_row)

        content.add_widget(FieldLabel("Comment (optional)"))

        self._comment = TextInput(
            hint_text="Share your experience…",
            multiline=True,
            background_normal="", background_active="", background_color=WHITE,
            foreground_color=TXT, cursor_color=PRIMARY,
            hint_text_color=(0.55, 0.55, 0.55, 1),
            size_hint_y=None, height=dp(330),
            padding=[dp(12), dp(12)],
            font_size=sp(13),
        )
        with self._comment.canvas.after:
            Color(0.86, 0.86, 0.88, 1)
            self._comment_border = Line(rounded_rectangle=[0, 0, 1, 1, dp(10)], width=0.8)
        self._comment.bind(pos=self._sync_border, size=self._sync_border)
        content.add_widget(self._comment)

        scroll.add_widget(content)
        root.add_widget(scroll)

        # Pinned bottom bar
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
        self._btn = PrimaryBtn(text="Submit Rating")
        self._btn.bind(on_press=self._submit)
        bottom.add_widget(self._btn)
        self._err = ErrLabel(text="")
        bottom.add_widget(self._err)
        root.add_widget(bottom)

        self.add_widget(root)

    def on_pre_enter(self):
        self._name_lbl.text = f"Rate {self.reviewee_name}"
        self._star_row.reset()
        self._comment.text = ""
        self._err.text = ""
        self._btn.text = "Submit Rating"
        self._btn.disabled = False

    def _sync_border(self, *_):
        c = self._comment
        self._comment_border.rounded_rectangle = [c.x, c.y, c.width, c.height, dp(10)]

    def _go_back(self):
        if self.manager:
            self.manager.current = self._from_screen

    def _submit(self, *_):
        if self._star_row.rating == 0:
            self._err.text = "Please select a star rating."
            return
        self._err.text = ""
        self._btn.text = "Submitting…"
        self._btn.disabled = True
        body = {
            "rating": self._star_row.rating,
            "comment": self._comment.text.strip() or None,
        }
        api(
            "POST", f"/tasks/{self.task_id}/review",
            body=body,
            on_success=self._submitted,
            on_error=self._on_err,
        )

    def _submitted(self, _):
        self._btn.text = "Submit Rating"
        self._btn.disabled = False
        if self.manager:
            self.manager.current = self._from_screen

    def _on_err(self, error):
        self._btn.text = "Submit Rating"
        self._btn.disabled = False
        self._err.text = str(error)

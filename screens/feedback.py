from kivy.clock import Clock
from kivy.graphics import Color, Line, Rectangle
from kivy.metrics import dp, sp
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.dropdown import DropDown
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget

from api import api
from widgets import ErrLabel, FieldLabel, PrimaryBtn, TopBar
from theme import BG, PRIMARY, TXT, TXT2, WHITE

CATEGORIES = ["Bug Report", "Feature Request", "General"]


class _Trigger(ButtonBehavior, BoxLayout):
    pass


class FeedbackScreen(Screen):
    def __init__(self, **kw):
        kw.setdefault("name", "feedback")
        super().__init__(**kw)
        self._selected_category = CATEGORIES[0]
        self._cat_dropdown = None
        self._cat_trigger = None
        self._build()

    def _build(self):
        root = BoxLayout(orientation="vertical")
        with root.canvas.before:
            Color(*BG)
            self._rbg = Rectangle(pos=root.pos, size=root.size)
        root.bind(
            pos=lambda i, v: setattr(self._rbg, "pos", v),
            size=lambda i, v: setattr(self._rbg, "size", v),
        )

        root.add_widget(TopBar(title="Feedback"))

        scroll = ScrollView()
        content = BoxLayout(
            orientation="vertical",
            padding=[dp(24), dp(20)],
            spacing=dp(12),
            size_hint_y=None,
        )
        content.bind(minimum_height=content.setter("height"))

        subtitle = Label(
            text="Tell us what's on your mind — bugs, ideas, or anything else.",
            color=TXT2, font_size=sp(13),
            size_hint_y=None, height=dp(36),
            halign="left", valign="top",
        )
        subtitle.bind(
            size=subtitle.setter("text_size"),
            texture_size=lambda inst, ts: setattr(inst, "height", max(ts[1], dp(36))),
        )
        content.add_widget(subtitle)

        content.add_widget(Widget(size_hint_y=None, height=dp(4)))

        # Category selector
        content.add_widget(FieldLabel("Category"))

        self._cat_dropdown = DropDown(auto_width=False)
        for cat in CATEGORIES:
            item = Button(
                text=cat,
                size_hint_y=None, height=dp(44),
                background_normal="", background_color=WHITE,
                color=TXT, font_size=sp(14),
                halign="left", valign="middle",
            )
            item.bind(
                size=lambda inst, v: setattr(inst, "text_size", (v[0] - dp(24), v[1])),
                on_press=lambda inst, c=cat: self._cat_dropdown.select(c),
            )
            self._cat_dropdown.add_widget(item)

        self._cat_trigger = _Trigger(
            size_hint_y=None, height=dp(48),
            orientation="horizontal",
            padding=[dp(12), 0, dp(12), 0],
        )
        with self._cat_trigger.canvas.before:
            Color(*WHITE)
            self._trigger_bg = Rectangle(
                pos=self._cat_trigger.pos, size=self._cat_trigger.size
            )
        self._cat_trigger.bind(
            pos=lambda inst, v: setattr(self._trigger_bg, "pos", v),
            size=lambda inst, v: setattr(self._trigger_bg, "size", v),
        )
        with self._cat_trigger.canvas.after:
            self._border_color = Color(0.78, 0.78, 0.80, 1)
            self._border_line = Line(
                rounded_rectangle=[0, 0, 100, 100, dp(6)], width=1
            )
        self._cat_trigger.bind(
            pos=self._sync_trigger_canvas,
            size=self._sync_trigger_canvas,
            on_press=self._open_dropdown,
        )

        self._cat_label = Label(
            text=CATEGORIES[0],
            color=TXT, font_size=sp(14),
            halign="left", valign="middle",
        )
        self._cat_label.bind(size=self._cat_label.setter("text_size"))

        chevron_lbl = Label(
            text="▾",
            color=TXT2, font_size=sp(16),
            size_hint_x=None, width=dp(20),
            halign="center", valign="middle",
        )
        chevron_lbl.bind(size=chevron_lbl.setter("text_size"))

        self._cat_trigger.add_widget(self._cat_label)
        self._cat_trigger.add_widget(chevron_lbl)
        self._cat_dropdown.bind(
            on_select=lambda inst, cat: self._select_category(cat),
            on_dismiss=self._on_dropdown_dismiss,
        )
        content.add_widget(self._cat_trigger)

        content.add_widget(Widget(size_hint_y=None, height=dp(4)))

        # Message input
        content.add_widget(FieldLabel("Your feedback"))
        self._msg_input = TextInput(
            hint_text="Describe the bug, feature, or feedback in detail…",
            multiline=True,
            size_hint_y=None, height=dp(180),
            background_color=WHITE,
            foreground_color=TXT,
            cursor_color=PRIMARY,
            padding=[dp(12), dp(12)],
            font_size=sp(14),
        )
        content.add_widget(self._msg_input)

        content.add_widget(Widget(size_hint_y=None, height=dp(8)))

        self._submit_btn = PrimaryBtn(text="Submit Feedback")
        self._submit_btn.bind(on_press=self._submit)
        content.add_widget(self._submit_btn)

        self._err = ErrLabel(text="")
        content.add_widget(self._err)

        self._success_lbl = Label(
            text="",
            color=(0.10, 0.65, 0.28, 1), font_size=sp(13),
            size_hint_y=None, height=dp(28),
            halign="left",
        )
        self._success_lbl.bind(size=self._success_lbl.setter("text_size"))
        content.add_widget(self._success_lbl)

        content.add_widget(Widget(size_hint_y=None, height=dp(24)))

        scroll.add_widget(content)
        root.add_widget(scroll)
        self.add_widget(root)

    def on_enter(self):
        self._err.text = ""
        self._success_lbl.text = ""

    def _open_dropdown(self, inst):
        self._cat_dropdown.width = inst.width
        self._border_color.rgba = (*PRIMARY[:3], 1)
        self._cat_dropdown.open(inst)

    def _sync_trigger_canvas(self, *_):
        t = self._cat_trigger
        self._border_line.rounded_rectangle = [t.x, t.y, t.width, t.height, dp(6)]

    def _on_dropdown_dismiss(self, *_):
        self._border_color.rgba = (0.78, 0.78, 0.80, 1)

    def _select_category(self, cat):
        self._selected_category = cat
        self._cat_label.text = cat
        self._border_color.rgba = (0.78, 0.78, 0.80, 1)

    def _submit(self, *_):
        message = self._msg_input.text.strip()
        if not message:
            self._err.text = "Please write your feedback before submitting."
            return

        self._err.text = ""
        self._success_lbl.text = ""
        self._submit_btn.text = "Submitting…"
        self._submit_btn.disabled = True

        api(
            "POST", "/feedback",
            body={"category": self._selected_category, "message": message},
            on_success=self._on_success,
            on_error=self._on_error,
        )

    def _on_success(self, _data):
        self._submit_btn.text = "Submit Feedback"
        self._submit_btn.disabled = False
        self._msg_input.text = ""
        self._success_lbl.text = "Thank you! Your feedback has been submitted."
        Clock.schedule_once(lambda _dt: setattr(self._success_lbl, "text", ""), 4)

    def _on_error(self, error):
        self._submit_btn.text = "Submit Feedback"
        self._submit_btn.disabled = False
        self._err.text = str(error)

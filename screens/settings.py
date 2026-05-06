from kivy.graphics import Color, Rectangle
from kivy.metrics import dp, sp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget

from api import clear_auth
from settings_store import FONT_SIZES, get_font_label, save_setting
from widgets import DangerBtn, PrimaryBtn, TopBar
from theme import BG, PRIMARY, TXT, TXT2, WHITE


class SettingsScreen(Screen):
    def __init__(self, **kw):
        kw.setdefault("name", "settings")
        super().__init__(**kw)
        self._font_btns = {}
        self._selected_font = get_font_label()
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

        root.add_widget(TopBar(title="Settings"))

        scroll = ScrollView()
        content = BoxLayout(
            orientation="vertical",
            padding=[dp(24), dp(20)],
            spacing=dp(14),
            size_hint_y=None,
        )
        content.bind(minimum_height=content.setter("height"))

        # ── Font Size ──────────────────────────────────────────────────────────
        content.add_widget(_SectionLabel("Font Size"))

        font_row = BoxLayout(
            orientation="horizontal", spacing=dp(8),
            size_hint_y=None, height=dp(48),
        )
        for label in FONT_SIZES:
            btn = Button(
                text=label,
                size_hint_x=1,
                background_normal="",
                font_size=sp(13), bold=True,
            )
            btn.bind(on_press=lambda *_, l=label: self._select_font(l))
            self._font_btns[label] = btn
            font_row.add_widget(btn)
        content.add_widget(font_row)

        hint = Label(
            text="Changes apply immediately on save.",
            color=TXT2, font_size=sp(12),
            size_hint_y=None, height=dp(22),
            halign="left",
        )
        hint.bind(size=hint.setter("text_size"))
        content.add_widget(hint)

        content.add_widget(Widget(size_hint_y=None, height=dp(8)))

        # ── Save ───────────────────────────────────────────────────────────────
        save_btn = PrimaryBtn(text="Save Settings")
        save_btn.bind(on_press=self._save)
        content.add_widget(save_btn)

        content.add_widget(Widget(size_hint_y=None, height=dp(24)))

        logout_btn = DangerBtn(text="Logout")
        logout_btn.bind(on_press=lambda *_: self._logout())
        content.add_widget(logout_btn)

        content.add_widget(Widget(size_hint_y=None, height=dp(24)))

        scroll.add_widget(content)
        root.add_widget(scroll)
        self.add_widget(root)

    def on_enter(self):
        self._select_font(get_font_label(), save=False)

    def _select_font(self, label, save=True):
        self._selected_font = label
        for lbl, btn in self._font_btns.items():
            if lbl == label:
                btn.background_color = PRIMARY
                btn.color = WHITE
            else:
                btn.background_color = (0.82, 0.82, 0.84, 1)
                btn.color = (0.25, 0.25, 0.25, 1)
        if save:
            save_setting("font_size", label)

    def _save(self, *_):
        save_setting("font_size", self._selected_font)
        from kivy.app import App
        App.get_running_app().rebuild_ui(return_to="settings")

    def _logout(self):
        clear_auth()
        self.manager.current = "login"



class _SectionLabel(Label):
    def __init__(self, text, **kw):
        kw.setdefault("color", TXT)
        kw.setdefault("font_size", sp(15))
        kw.setdefault("bold", True)
        kw.setdefault("size_hint_y", None)
        kw.setdefault("height", dp(30))
        kw.setdefault("halign", "left")
        kw.setdefault("valign", "middle")
        super().__init__(text=text, **kw)
        self.bind(size=self.setter("text_size"))

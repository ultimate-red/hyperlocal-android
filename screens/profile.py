from kivy.clock import Clock
from kivy.graphics import Color, Rectangle
from kivy.metrics import dp, sp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget

from api import api, clear_auth
from widgets import ErrLabel, FieldLabel, PrimaryBtn, RatingStars, StyledInput, TopBar
from theme import BG, TXT, TXT2


class ProfileScreen(Screen):
    def __init__(self, **kw):
        kw.setdefault("name", "profile")
        super().__init__(**kw)
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

        root.add_widget(TopBar(title="Profile"))

        # ── Profile header (PRIMARY band) ──────────────────────────────────
        header = BoxLayout(
            orientation="vertical",
            size_hint_y=None, height=dp(128),
            padding=[dp(24), dp(20), dp(24), dp(16)],
            spacing=dp(4),
        )
        with header.canvas.before:
            Color(0.15, 0.40, 0.80, 1)
            self._hdr_bg = Rectangle(pos=header.pos, size=header.size)
        header.bind(
            pos=lambda i, v: setattr(self._hdr_bg, "pos", v),
            size=lambda i, v: setattr(self._hdr_bg, "size", v),
        )

        self._name_display = Label(
            text="",
            color=(1, 1, 1, 1), font_size=sp(22), bold=True,
            size_hint_y=None, height=dp(36),
            halign="center",
        )
        self._name_display.bind(size=self._name_display.setter("text_size"))
        header.add_widget(self._name_display)

        self._email_display = Label(
            text="",
            color=(1, 1, 1, 0.78), font_size=sp(13),
            size_hint_y=None, height=dp(22),
            halign="center",
        )
        self._email_display.bind(size=self._email_display.setter("text_size"))
        header.add_widget(self._email_display)

        self._rating_row = BoxLayout(
            orientation="horizontal",
            size_hint_y=None, height=dp(24),
            spacing=dp(6),
        )
        self._stars = RatingStars(rating=None, star_size=dp(15), height=dp(24))
        self._rating_row.add_widget(self._stars)
        self._review_count_lbl = Label(
            text="",
            color=(1, 1, 1, 0.75), font_size=sp(11),
            size_hint=(None, 1), width=dp(64),
            halign="left", valign="middle",
            text_size=(dp(64), None),
        )
        self._rating_row.add_widget(self._review_count_lbl)
        header.add_widget(self._rating_row)

        root.add_widget(header)

        # ── Edit form ──────────────────────────────────────────────────────
        scroll = ScrollView()
        content = BoxLayout(
            orientation="vertical",
            padding=[dp(24), dp(20)],
            spacing=dp(12),
            size_hint_y=None,
        )
        content.bind(minimum_height=content.setter("height"))

        for label, attr, hint in [
            ("Display Name", "_in_name",     "Your name"),
            ("Bio",          "_in_bio",      "A short bio"),
            ("Location",     "_in_location", "City, Country"),
            ("Phone",        "_in_phone",    "10-digit number"),
        ]:
            content.add_widget(FieldLabel(label))
            inp = StyledInput(hint_text=hint)
            setattr(self, attr, inp)
            content.add_widget(inp)

        content.add_widget(Widget(size_hint_y=None, height=dp(8)))

        self._save_btn = PrimaryBtn(text="Save Profile")
        self._save_btn.bind(on_press=self._save)
        content.add_widget(self._save_btn)

        self._err = ErrLabel(text="")
        content.add_widget(self._err)

        self._msg = Label(
            text="",
            color=(0.18, 0.55, 0.18, 1), font_size=sp(13),
            size_hint_y=None, height=dp(28),
            halign="left",
        )
        self._msg.bind(size=self._msg.setter("text_size"))
        content.add_widget(self._msg)

        content.add_widget(Widget(size_hint_y=None, height=dp(24)))

        scroll.add_widget(content)
        root.add_widget(scroll)
        self.add_widget(root)

    def on_enter(self):
        self._err.text = ""
        self._msg.text = ""
        api("GET", "/users/me", on_success=self._load_profile, on_error=self._on_err)

    def _load_profile(self, data):
        self._name_display.text  = data.get("name")  or ""
        self._email_display.text = data.get("email") or ""
        avg   = data.get("average_rating")
        count = data.get("review_count", 0)
        self._stars.set_rating(avg)
        self._review_count_lbl.text = (
            f"({count} review{'s' if count != 1 else ''})" if avg is not None else ""
        )
        self._in_name.text     = data.get("name")     or ""
        self._in_bio.text      = data.get("bio")      or ""
        self._in_location.text = data.get("location") or ""
        self._in_phone.text    = data.get("phone")    or ""

    def _save(self, *_):
        self._err.text = ""
        self._msg.text = ""
        self._save_btn.text = "Saving…"
        self._save_btn.disabled = True
        body = {
            "name":     self._in_name.text.strip()     or None,
            "bio":      self._in_bio.text.strip()      or None,
            "location": self._in_location.text.strip() or None,
            "phone":    self._in_phone.text.strip()    or None,
        }
        api("PUT", "/users/me", body=body,
            on_success=self._saved, on_error=self._on_err)

    def _saved(self, data):
        self._save_btn.text = "Save Profile"
        self._save_btn.disabled = False
        self._name_display.text  = data.get("name")  or ""
        self._email_display.text = data.get("email") or ""
        self._msg.text = "Profile updated!"
        Clock.schedule_once(lambda dt: setattr(self._msg, "text", ""), 3)

    def _on_err(self, error):
        self._err.text = str(error)
        self._save_btn.text = "Save Profile"
        self._save_btn.disabled = False

    def _logout(self):
        clear_auth()
        self.manager.current = "login"

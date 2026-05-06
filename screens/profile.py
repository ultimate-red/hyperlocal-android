from kivy.clock import Clock
from kivy.graphics import Color, Rectangle
from kivy.metrics import dp, sp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget

from api import api, clear_auth
from fcm import get_fcm_token
from widgets import ErrLabel, FieldLabel, PrimaryBtn, StyledInput, TopBar
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

        self._rating_display = Label(
            text="",
            color=(1, 1, 1, 0.85), font_size=sp(13),
            size_hint_y=None, height=dp(22),
            halign="center",
        )
        self._rating_display.bind(size=self._rating_display.setter("text_size"))
        header.add_widget(self._rating_display)

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

        # Debug FCM button
        self._fcm_btn = PrimaryBtn(text="Test FCM Registration")
        self._fcm_btn.bind(on_press=self._test_fcm)
        content.add_widget(self._fcm_btn)

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
        if avg is not None:
            self._rating_display.text = f"{avg} / 5  ({count} review{'s' if count != 1 else ''})"
        else:
            self._rating_display.text = "No reviews yet"
        self._in_name.text     = data.get("name")     or ""
        self._in_bio.text      = data.get("bio")      or ""
        self._in_location.text = data.get("location") or ""
        self._in_phone.text    = data.get("phone")    or ""

    def _test_fcm(self, *_):
        print("DEBUG: _test_fcm called")
        use_popup = False
        try:
            from kivy.uix.toast import toast
        except ImportError:
            try:
                from kivy.toast import toast
            except ImportError:
                # Fallback: use popup
                use_popup = True
        
        if use_popup:
            from kivy.uix.popup import Popup
            from kivy.uix.label import Label
            popup = Popup(title="Testing FCM", content=Label(text="Testing FCM..."), size_hint=(0.8, 0.4))
            popup.open()
            print("DEBUG: Using popup for toast")
        else:
            toast("Testing FCM...")
        
        print("DEBUG: About to call get_fcm_token")
        get_fcm_token(self._on_fcm_test_success, on_error=self._on_fcm_test_error)

    def _on_fcm_test_success(self, token):
        print(f"DEBUG: FCM test success with token: {token[:20]}...")
        def show_msg():
            try:
                from kivy.uix.toast import toast
            except ImportError:
                try:
                    from kivy.toast import toast
                except ImportError:
                    from kivy.uix.popup import Popup
                    from kivy.uix.label import Label
                    popup = Popup(title="FCM Success", content=Label(text=f"FCM test success: {token[:10]}..."), size_hint=(0.8, 0.4))
                    popup.open()
                    return
            toast(f"FCM test success: {token[:10]}...")
        
        show_msg()

    def _on_fcm_test_error(self, error):
        print(f"DEBUG: FCM test error: {error}")
        def show_msg():
            from kivy.uix.popup import Popup
            from kivy.uix.textinput import TextInput
            ti = TextInput(text=error, readonly=True, multiline=True, font_size='12sp')
            popup = Popup(title="FCM Error", content=ti, size_hint=(0.95, 0.75))
            popup.open()
        show_msg()

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

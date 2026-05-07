import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlencode, urlparse

from kivy.clock import Clock
from kivy.graphics import Color, Rectangle
from kivy.metrics import dp, sp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.uix.widget import Widget

from api import api, register_fcm_token, save_auth
from fcm import get_fcm_token
from widgets import ErrLabel, PrimaryBtn, TopBar
from theme import BG, TXT, TXT2

LOCAL_PORT = 8765
LOCAL_REDIRECT = f"http://localhost:{LOCAL_PORT}"


class _CallbackHandler(BaseHTTPRequestHandler):
    """Captures ?token=...&user_id=... sent by the backend redirect."""

    callback = None

    def do_GET(self):
        params = parse_qs(urlparse(self.path).query)
        token = params.get("token", [None])[0]
        user_id = params.get("user_id", [None])[0]

        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(
            b"<html><body><h2>Login successful! You can close this tab.</h2></body></html>"
        )

        if token and user_id and _CallbackHandler.callback:
            Clock.schedule_once(
                lambda dt: _CallbackHandler.callback(token, int(user_id)), 0
            )

    def log_message(self, format, *args):
        pass  # suppress console noise


class LoginScreen(Screen):
    def __init__(self, **kw):
        kw.setdefault("name", "login")
        super().__init__(**kw)
        self._server = None
        self._waiting = False
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

        root.add_widget(TopBar(title="Hyperlocal Platform", show_menu=False))

        content = BoxLayout(
            orientation="vertical",
            padding=[dp(40), dp(20)],
            spacing=dp(0),
        )

        # Top flex spacer — pushes content to vertical center
        content.add_widget(Widget())

        app_name = Label(
            text="Hyperlocal",
            font_size=sp(30), bold=True, color=TXT,
            size_hint_y=None, height=dp(44),
            halign="center",
        )
        app_name.bind(size=app_name.setter("text_size"))
        content.add_widget(app_name)

        content.add_widget(Widget(size_hint_y=None, height=dp(12)))

        subtitle = Label(
            text="Your local task marketplace.\nSign in with Google to get started.",
            font_size=sp(14), color=TXT2,
            size_hint_y=None, height=dp(48),
            halign="center", valign="middle",
        )
        subtitle.bind(size=subtitle.setter("text_size"))
        content.add_widget(subtitle)

        content.add_widget(Widget(size_hint_y=None, height=dp(40)))

        self._btn = PrimaryBtn(text="Continue with Google")
        self._btn.bind(on_press=self._start_oauth)
        content.add_widget(self._btn)

        content.add_widget(Widget(size_hint_y=None, height=dp(8)))

        self._err = ErrLabel(text="")
        content.add_widget(self._err)

        # Bottom flex spacer — balanced with top
        content.add_widget(Widget())

        root.add_widget(content)
        self.add_widget(root)

    def _start_oauth(self, *_):
        if self._waiting:
            self._cancel_oauth()
            return
        self._waiting = True
        self._btn.text = "Opening browser…"
        self._btn.disabled = True
        self._err.text = ""
        path = "/auth/google/url?" + urlencode({"local_redirect": LOCAL_REDIRECT})
        api("GET", path, on_success=self._got_url, on_error=self._on_err, auth=False)

    def _got_url(self, result):
        url = result.get("url")
        if not url:
            self._on_err("No URL returned from server.")
            return
        self._start_local_server()
        webbrowser.open(url)
        self._btn.text = "Cancel Login"
        self._btn.disabled = False

    def _cancel_oauth(self):
        if self._server:
            threading.Thread(target=self._server.shutdown, daemon=True).start()
            self._server = None
        self._waiting = False
        self._btn.text = "Continue with Google"
        self._btn.disabled = False

    def _start_local_server(self):
        _CallbackHandler.callback = self._oauth_done
        self._server = HTTPServer(("localhost", LOCAL_PORT), _CallbackHandler)
        threading.Thread(target=self._server.serve_forever, daemon=True).start()

    def _oauth_done(self, token, user_id):
        self._waiting = False
        if self._server:
            threading.Thread(target=self._server.shutdown, daemon=True).start()
            self._server = None
        save_auth(token, user_id)
        self._btn.text = "Continue with Google"
        self._btn.disabled = False
        Clock.schedule_once(lambda dt: get_fcm_token(register_fcm_token), 0)
        self.manager.current = "task_list"

    def _on_err(self, error):
        self._waiting = False
        self._err.text = str(error)
        self._btn.text = "Continue with Google"
        self._btn.disabled = False

    def on_leave(self):
        if self._server:
            threading.Thread(target=self._server.shutdown, daemon=True).start()
            self._server = None
        self._waiting = False

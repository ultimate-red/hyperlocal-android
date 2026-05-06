from kivy.config import Config
Config.set('graphics', 'width',  '390')
Config.set('graphics', 'height', '844')
Config.set('graphics', 'resizable', '0')

from kivy.animation import Animation
from kivy.app import App
from kivy.clock import Clock
from kivy.metrics import dp, Metrics
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.screenmanager import NoTransition, ScreenManager, SlideTransition
from kivy.core.window import Window
import logging
import platform

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Check if running on Android
try:
    from jnius import autoclass
    IS_ANDROID = True
except ImportError:
    IS_ANDROID = False

from settings_store import get_font_scale
Metrics.fontscale = get_font_scale()

from api import get_token, register_fcm_token
from config import NAV_ITEMS
from fcm import get_fcm_token
from widgets import DrawerOverlay, DrawerPanel
from screens.login import LoginScreen
from screens.task_list import TaskListScreen
from screens.my_tasks import MyTasksScreen
from screens.create_task import CreateTaskScreen
from screens.task_detail import TaskDetailScreen
from screens.profile import ProfileScreen
from screens.settings import SettingsScreen
from screens.feedback import FeedbackScreen
from screens.rate_user import RateUserScreen

def log_touch(window, touch):
    print("touch:", touch.pos, touch.device, touch.profile)


class HyperlocalApp(App):
    def build(self):
        logger.info("Building HyperlocalApp...")
        self.title = "Hyperlocal Platform"
        self._root = FloatLayout()
        self._sm = self._build_sm()
        self._root.add_widget(self._sm)
        self._overlay, self._drawer = self._build_drawer()
        self._root.add_widget(self._overlay)
        self._root.add_widget(self._drawer)
        
        logger.info(f"IS_ANDROID: {IS_ANDROID}")
        logger.info(f"get_token(): {get_token()}")
        
        # Test toast on any platform
        try:
            from kivy.uix.toast import toast
        except ImportError:
            try:
                from kivy.toast import toast
            except ImportError:
                from kivy.uix.popup import Popup
                from kivy.uix.label import Label
                popup = Popup(title="App Started", content=Label(text="App started!"), size_hint=(0.8, 0.4))
                popup.open()
            else:
                toast("App started!")
        else:
            toast("App started!")
        
        if IS_ANDROID and get_token():
            logger.info("✓ On Android with auth token, setting up notifications...")
            self._request_notification_permission()
            get_fcm_token(self._on_fcm_token, on_error=self._on_fcm_error)
        elif not IS_ANDROID:
            logger.info("✗ Desktop mode - skipping FCM setup")
        else:
            logger.info("✗ No auth token, skipping notification setup")
        
        # Window.bind(on_touch_down=log_touch)

        return self._root

    def _request_notification_permission(self):
        logger.info("Requesting POST_NOTIFICATIONS permission...")
        try:
            from android.permissions import request_permissions, Permission
            request_permissions([Permission.POST_NOTIFICATIONS])
            logger.info("Notification permission request sent")
        except Exception as e:
            logger.warning(f"Could not request notification permission (may not be on Android 13+): {e}")

    def _on_fcm_token(self, token):
        print(f"DEBUG: _on_fcm_token called with token: {token[:20]}...")
        logger.info(f"✓ FCM token callback received: {token[:20]}...")
        def show_msg():
            try:
                from kivy.uix.toast import toast
            except ImportError:
                try:
                    from kivy.toast import toast
                except ImportError:
                    from kivy.uix.popup import Popup
                    from kivy.uix.label import Label
                    popup = Popup(title="FCM Token", content=Label(text=f"FCM Token: {token[:10]}..."), size_hint=(0.8, 0.4))
                    popup.open()
                    return
            toast(f"FCM Token: {token[:10]}...")
        show_msg()
        register_fcm_token(token)
    
    def _on_fcm_error(self, error):
        print(f"DEBUG: _on_fcm_error called with error: {error}")
        logger.error(f"✗ FCM token error callback: {error}")
        def show_msg():
            from kivy.uix.popup import Popup
            from kivy.uix.textinput import TextInput
            ti = TextInput(text=error, readonly=True, multiline=True,
                           font_size=dp(12), size_hint=(1, 1))
            popup = Popup(title="FCM Error", content=ti, size_hint=(0.95, 0.75))
            popup.open()
        show_msg()

    def _build_sm(self, current=""):
        sm = ScreenManager(transition=NoTransition())
        sm.add_widget(LoginScreen())
        sm.add_widget(TaskListScreen())
        sm.add_widget(MyTasksScreen())
        sm.add_widget(CreateTaskScreen())
        sm.add_widget(TaskDetailScreen())
        sm.add_widget(ProfileScreen())
        sm.add_widget(SettingsScreen())
        sm.add_widget(FeedbackScreen())
        sm.add_widget(RateUserScreen())
        sm.current = current or ("task_list" if get_token() else "login")
        sm.transition = SlideTransition()
        return sm

    def _build_drawer(self):
        overlay = DrawerOverlay()
        drawer = DrawerPanel(nav_items=NAV_ITEMS, on_nav=self._navigate)
        drawer.x = -drawer.width
        return overlay, drawer

    # ── Drawer API ─────────────────────────────────────────────────────────────

    def toggle_drawer(self):
        if self._drawer.x < 0:
            self.open_drawer()
        else:
            self.close_drawer()

    def open_drawer(self):
        self._drawer.set_active(self._sm.current)
        self._overlay.disabled = False
        Animation(opacity=0.30, duration=0.22).start(self._overlay)
        Animation(x=0, duration=0.22, t="out_quad").start(self._drawer)

    def close_drawer(self):
        Animation(opacity=0, duration=0.2).start(self._overlay)
        anim = Animation(x=-self._drawer.width, duration=0.2, t="in_quad")
        anim.bind(on_complete=lambda *_: setattr(self._overlay, "disabled", True))
        anim.start(self._drawer)

    def _navigate(self, screen):
        self.close_drawer()
        Clock.schedule_once(lambda dt: setattr(self._sm, "current", screen), 0.22)

    # ── UI rebuild (font change) ────────────────────────────────────────────────

    def rebuild_ui(self, return_to="settings"):
        Metrics.fontscale = get_font_scale()
        def _do(_dt):
            self._root.clear_widgets()
            self._sm = self._build_sm(return_to)
            self._root.add_widget(self._sm)
            self._overlay, self._drawer = self._build_drawer()
            self._root.add_widget(self._overlay)
            self._root.add_widget(self._drawer)
        Clock.schedule_once(_do, 0)


if __name__ == "__main__":
    HyperlocalApp().run()

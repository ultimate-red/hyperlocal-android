import json
import logging

from kivy.network.urlrequest import UrlRequest
from kivy.storage.jsonstore import JsonStore

from config import BASE_URL

logger = logging.getLogger(__name__)
_store = JsonStore("hyperlocal_auth.json")


# ── Auth helpers ──────────────────────────────────────────────────────────────

def get_token():
    return _store.get("auth")["token"] if _store.exists("auth") else None


def get_user_id():
    return _store.get("auth")["user_id"] if _store.exists("auth") else None


def save_auth(token, user_id):
    _store.put("auth", token=token, user_id=user_id)


def clear_auth():
    if _store.exists("auth"):
        _store.delete("auth")


def register_fcm_token(token):
    print(f"DEBUG: register_fcm_token called with token: {token[:20]}...")
    def _success(result):
        print("DEBUG: FCM token registration success")
        logger.info(f"✓ FCM token registered successfully: {token[:20]}...")
        def show_msg():
            try:
                from kivy.uix.toast import toast
            except ImportError:
                try:
                    from kivy.toast import toast
                except ImportError:
                    from kivy.uix.popup import Popup
                    from kivy.uix.label import Label
                    popup = Popup(title="FCM Registered", content=Label(text="FCM token registered!"), size_hint=(0.8, 0.4))
                    popup.open()
                    return
            toast("FCM token registered!")
        show_msg()
    
    def _error(error):
        print(f"DEBUG: FCM token registration error: {error}")
        logger.error(f"✗ Failed to register FCM token: {error}")
        def show_msg():
            try:
                from kivy.uix.toast import toast
            except ImportError:
                try:
                    from kivy.toast import toast
                except ImportError:
                    from kivy.uix.popup import Popup
                    from kivy.uix.label import Label
                    popup = Popup(title="FCM Registration Failed", content=Label(text=f"FCM registration failed: {error[:30]}"), size_hint=(0.8, 0.4))
                    popup.open()
                    return
            toast(f"FCM registration failed: {error[:30]}")
        show_msg()
    
    print("DEBUG: Making API call to register FCM token")
    logger.info(f"→ Registering FCM token with backend: {token[:20]}...")
    api("PUT", "/users/me/fcm-token", body={"token": token}, on_success=_success, on_error=_error)


# ── API helper ────────────────────────────────────────────────────────────────

def api(method, path, body=None, on_success=None, on_error=None, auth=True):
    url = BASE_URL + path
    headers = {"Content-Type": "application/json"}
    if auth:
        token = get_token()
        if token:
            headers["Authorization"] = f"Bearer {token}"

    req_body = json.dumps(body).encode("utf-8") if body else None

    def _ok(req, result):
        if on_success:
            on_success(result)

    def _err(req, error):
        if on_error:
            on_error(str(error))

    def _fail(req, result):
        if on_error:
            msg = (
                result.get("detail", str(result))
                if isinstance(result, dict)
                else str(result)
            )
            on_error(msg)

    def _cancel(_):
        if on_error:
            on_error("Request timed out. Is the backend running?")

    UrlRequest(
        url,
        method=method,
        req_body=req_body,
        req_headers=headers,
        on_success=_ok,
        on_error=_err,
        on_failure=_fail,
        on_cancel=_cancel,
        timeout=10,
    )

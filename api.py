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
    logger.info(f"→ Registering FCM token: {token[:20]}...")
    def _success(result):
        logger.info(f"✓ FCM token registered: {token[:20]}...")
    def _error(error):
        logger.error(f"✗ Failed to register FCM token: {error}")
    api("PUT", "/users/me/fcm-token", body={"token": token}, on_success=_success, on_error=_error)


def send_app_log(level, message, screen=None):
    """Send an error/warning log to the backend. Silent — never shows UI."""
    body = {"level": level, "message": message}
    if screen:
        body["screen"] = screen
    api("POST", "/app-logs", body=body, on_success=None, on_error=None)


# ── API helper ────────────────────────────────────────────────────────────────

def api(method, path, body=None, on_success=None, on_error=None, auth=True):
    url = BASE_URL + path
    headers = {"Content-Type": "application/json"}
    if auth:
        token = get_token()
        if token:
            headers["Authorization"] = f"Bearer {token}"

    req_body = json.dumps(body).encode("utf-8") if body else None

    def _log_error(msg):
        # Skip logging errors from the log endpoint itself to avoid loops
        if path != "/app-logs":
            send_app_log("error", f"{method} {path} — {msg}")

    def _ok(req, result):
        if on_success:
            on_success(result)

    def _err(req, error):
        msg = str(error)
        _log_error(msg)
        if on_error:
            on_error(msg)

    def _fail(req, result):
        msg = (
            result.get("detail", str(result))
            if isinstance(result, dict)
            else str(result)
        )
        _log_error(msg)
        if on_error:
            on_error(msg)

    def _cancel(_):
        msg = "Request timed out. Is the backend running?"
        _log_error(msg)
        if on_error:
            on_error(msg)

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

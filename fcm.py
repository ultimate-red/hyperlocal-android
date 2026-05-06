import threading
import logging
from kivy.clock import Clock

logger = logging.getLogger(__name__)


def get_fcm_token(callback, on_error=None):
    """
    Must be called from the main Kivy thread.
    Firebase classes are loaded here (main thread has correct ClassLoader).
    The blocking Tasks.await() runs on a background thread so UI is not blocked.
    """
    try:
        from jnius import autoclass
    except ImportError:
        msg = "jnius not available - FCM only works on Android"
        if on_error:
            Clock.schedule_once(lambda dt: on_error(msg), 0)
        return

    # Step 1: context
    try:
        context = autoclass('org.kivy.android.PythonActivity').mActivity
        print("DEBUG FCM: got context")
    except Exception as e:
        msg = f"Step 1 failed (context): {e}"
        print(f"DEBUG FCM: {msg}")
        if on_error:
            Clock.schedule_once(lambda dt: on_error(msg), 0)
        return

    # Step 2: init Firebase if needed
    try:
        FirebaseApp = autoclass('com.google.firebase.FirebaseApp')
        if FirebaseApp.getApps(context).isEmpty():
            print("DEBUG FCM: initializing Firebase")
            B = autoclass('com.google.firebase.FirebaseOptions$Builder')
            b = B()
            b.setApplicationId('1:252773985780:android:ffec27008c677272a69da1')
            b.setProjectId('hyperlocal-platform-app')
            b.setApiKey('AIzaSyCL2nV-soHYJlWsI2rMNXsoYqqCeWCso_0')
            b.setGcmSenderId('252773985780')
            FirebaseApp.initializeApp(context, b.build())
            print("DEBUG FCM: Firebase initialized")
        else:
            print("DEBUG FCM: Firebase already initialized")
    except Exception as e:
        msg = f"Step 2 failed (Firebase init): {e}"
        print(f"DEBUG FCM: {msg}")
        if on_error:
            Clock.schedule_once(lambda dt: on_error(msg), 0)
        return

    # Step 3: preload classes and create task on main thread (ClassLoader OK here)
    try:
        FirebaseMessaging = autoclass('com.google.firebase.messaging.FirebaseMessaging')
        Tasks = autoclass('com.google.android.gms.tasks.Tasks')
        TimeUnit = autoclass('java.util.concurrent.TimeUnit')
        task = FirebaseMessaging.getInstance().getToken()
        print("DEBUG FCM: task created, awaiting on background thread")
    except Exception as e:
        msg = f"Step 3 failed (create task): {e}"
        print(f"DEBUG FCM: {msg}")
        if on_error:
            Clock.schedule_once(lambda dt: on_error(msg), 0)
        return

    # Step 4: await the task on a background thread so UI is not blocked.
    # Tasks and task are already loaded — pyjnius caches them so the background
    # thread can use them without needing to resolve classes again.
    def _await():
        try:
            token = getattr(Tasks, 'await')(task, 30, TimeUnit.SECONDS)
            if token:
                print(f"DEBUG FCM: token={str(token)[:20]}...")
                tok = str(token)
                Clock.schedule_once(lambda dt: callback(tok), 0)
            else:
                msg = "Token is None - check Firebase project config"
                print(f"DEBUG FCM: {msg}")
                if on_error:
                    Clock.schedule_once(lambda dt: on_error(msg), 0)
        except Exception as e:
            msg = f"Step 4 failed (await): {e}"
            print(f"DEBUG FCM: {msg}")
            if on_error:
                Clock.schedule_once(lambda dt: on_error(msg), 0)

    threading.Thread(target=_await, daemon=True).start()

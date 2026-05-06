# Hyperlocal Platform — Android App

Python/Kivy Android app for the Hyperlocal Platform. Connects to the [hyperlocal-backend](https://github.com/your-org/hyperlocal-backend) API.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3 |
| UI Framework | Kivy |
| HTTP | Kivy `UrlRequest` (async, built-in) |
| Auth storage | Kivy `JsonStore` (persists across restarts) |
| Build tool | Buildozer → APK |

## Project Structure

```
hyperlocal-android/
├── main.py           ← Full app — all screens in one file
├── buildozer.spec    ← Android build configuration
└── requirements.txt  ← Desktop testing dependencies
```

### `main.py` layout

| Section | Description |
|---------|-------------|
| `BASE_URL` + auth helpers | Server URL, token read/write/clear |
| `api()` | Async HTTP wrapper around `UrlRequest` (10s timeout) |
| Reusable widgets | `PrimaryBtn`, `TopBar`, `StatusBadge`, `TaskCard`, … |
| `LoginScreen` | Phone → Request OTP → Enter OTP → Verify |
| `TaskListScreen` | Scrollable task cards + FAB + Logout |
| `CreateTaskScreen` | Title / Description / Reward form |
| `TaskDetailScreen` | Task details + Accept / Complete actions |
| `HyperlocalApp` | App entry point, wires `ScreenManager` |

## Prerequisites

- Python 3.8+
- `pip install kivy` (desktop testing)
- Buildozer + Android SDK/NDK (APK build — downloaded automatically)

## Setup & Running

### Option A — Desktop (fastest, no device needed)

```bash
pip install -r requirements.txt
```

Edit `main.py` line 32 — set the backend URL:
```python
BASE_URL = "http://localhost:8000"       # backend on same machine
# BASE_URL = "https://yourapp.railway.app"  # cloud deployment
```

Run:
```bash
python main.py
```

### Option B — Build APK for Android

```bash
pip install buildozer
```

Edit `main.py` line 32:
```python
BASE_URL = "http://10.0.2.2:8000"       # Android emulator
# BASE_URL = "http://192.168.x.x:8000"  # physical device (your LAN IP)
# BASE_URL = "https://yourapp.railway.app"  # cloud deployment
```

Find your LAN IP:
```bash
ifconfig | grep "inet " | grep -v 127.0.0.1
```

Build and install:
```bash
buildozer android debug          # first build ~20 min (downloads SDK/NDK)
adb install bin/hyperlocal*.apk
```

## Screens

### Login
- Enter phone number → tap **Request OTP**
- OTP is displayed on screen (Phase 0 convenience — remove in production)
- Enter OTP → tap **Verify OTP**
- Token saved locally; navigates to task list

### Task List
- Scrollable cards showing title, status badge, reward, creator
- **+** button (bottom-right) to create a task
- **Logout** button top-right

### Create Task
- Title (required), Description (optional), Reward ₹ (optional)
- Tap **Create Task** → returns to list

### Task Detail
- Shows full task info + status badge
- **Accept Task** — shown to non-creators when status is `open`
- **Mark as Completed** — shown to creator when status is `accepted`
- **✓ Task Completed** banner when done

## Testing with Multiple Users

**Desktop**: delete `hyperlocal_auth.json` between users:
```bash
rm hyperlocal_auth.json
python main.py
```

**Android device**: Settings → Apps → Hyperlocal → Storage → Clear Data

## Troubleshooting

### Button stuck on "Sending…"
- Backend is not reachable — check `BASE_URL` in `main.py`
- Request will time out after 10 seconds and show an error message

### Cannot connect to backend
| Setup | BASE_URL |
|-------|---------|
| Desktop | `http://localhost:8000` |
| Android emulator | `http://10.0.2.2:8000` |
| Physical device | `http://<your-LAN-IP>:8000` |
| Cloud | `https://yourapp.railway.app` |

### Clipboard warning on Linux desktop
```bash
sudo apt install xclip
```

### App crashes on Android
```bash
adb logcat -s python    # view Python tracebacks
```

### Buildozer build fails
```bash
buildozer android clean
buildozer android debug
```
Ensure `android.accept_sdk_license = True` in `buildozer.spec`.

## Deployment

Update `BASE_URL` to your cloud backend URL, then rebuild the APK:
```bash
buildozer android debug
adb install bin/hyperlocal*.apk
```

## Phase 0 Notes

- OTP is displayed on screen — intentional for testing, remove before production
- No client-side input validation beyond basic length checks
- Auth token stored in plain `hyperlocal_auth.json` — use encrypted storage in production

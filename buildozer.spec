[app]
title = Hyperlocal Platform
package.name = hyperlocal
package.domain = com.hyperlocal

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json

# Exclude junk
source.exclude_dirs = env,__pycache__,.git,env2,bin
source.exclude_patterns = hyperlocal_auth.json
source.include_patterns = google-services.json

version = 1.0.0

requirements = python3,kivy==2.3.0,pillow,pyjnius

# Orientation: portrait
orientation = portrait

# Android SDK / NDK
android.api = 33
android.minapi = 21
android.ndk = 25b
android.accept_sdk_license = True

# Firebase Cloud Messaging SDK
android.gradle_dependencies = com.google.firebase:firebase-messaging:23.4.0

# Google Services plugin
android.gradle_repositories = google()

# Custom Java source — FCMService for foreground notifications
android.add_src = android_src

# Custom manifest template — adds FCMService declaration inside <application>
android.manifest.template = AndroidManifest.tmpl.xml

# Use SDL2 bootstrap (default for Kivy)
p4a.bootstrap = sdl2

# Arch — build for both arm64 and armv7a so it covers most devices
android.archs = arm64-v8a, armeabi-v7a

# Logcat filter for debugging
android.logcat_filters = *:S python:D

# Required for modern Android
android.enable_androidx = True

# Add location permission (you'll need it)
android.permissions = INTERNET, ACCESS_FINE_LOCATION, POST_NOTIFICATIONS

# Firebase configuration
android.meta_data = google_app_id=1:252773985780:android:ffec27008c677272a69da1

[buildozer]
log_level = 2
warn_on_root = 1

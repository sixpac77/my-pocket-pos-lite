[app]
title = My Pocket POS
package.name = MyPocketPOS
package.domain = org.homepos
source.dir = .
source.include_exts = py,kv,png,jpg,jpeg,svg,ttf,otf,ini,json,csv
version = 0.1.0
requirements = python3,kivy==2.3.0,opencv-python-headless,certifi,urllib3,requests
orientation = portrait
fullscreen = 0
log_level = 1
android.archs = arm64-v8a, armeabi-v7a
# Make sure Kivy keeps the soft keyboard below inputs
android.manifest.intent_filters = 
# Keep app data across reinstalls if same signing key
android.allow_backup = True

# ---- STORAGE PERMISSIONS (fixes empty inventory) ----
# Android 13+ media permissions:
android.permissions = READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE, READ_MEDIA_IMAGES, READ_MEDIA_VIDEO, READ_MEDIA_AUDIO
# Target API 33 is stable for Kivy/Buildozer as of 2025
android.api = 33
android.minapi = 24
# Use Gradle (default in modern Buildozer)
android.gradle_dependencies = 
android.ndk_api = 24

# Optional icons/splash (safe to leave empty)
icon.filename = %(source.dir)s/icon.png
presplash.filename = %(source.dir)s/presplash.png

# Where your app expects inventory:
# NOTE: Your Python code should read this exact path:
# /storage/emulated/0/personal/App/flea_inventory.csv
# No extra config here; just a reminder.

# Reduce APK size a bit
android.strip = True

[buildozer]
log_level = 2
warn_on_root = 0

[app:source.exclude_patterns]
# exclude dev files from APK
.git
.github
venv
__pycache__
*.md
*.yml

[app:pythonversions]
# keep default

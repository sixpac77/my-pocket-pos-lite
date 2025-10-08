[app]
title = My Pocket POS
package.name = pocketpos
package.domain = org.pocketpos
source.dir = .
source.include_exts = py,png,jpg,jpeg,txt,kv,ini,csv,json
version = 0.1.0

requirements = python3,kivy
orientation = portrait
fullscreen = 0

# Storage & network (minimal for your Lite build)
android.permissions = INTERNET, READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE
android.accept_sdk_license = True

# --- Android / toolchain versions ---
android.api = 33
android.minapi = 24
android.ndk = 25b
android.archs = arm64-v8a, armeabi-v7a
p4a.branch = master
android.gradle_build_tools_version = 8.1.1
android.sdk_build_tools = 34.0.0
android.sdk = 34

# Logging
log_level = 2

[buildozer]
log_level = 2
warn_on_root = 0

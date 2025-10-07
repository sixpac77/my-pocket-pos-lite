[app]
title = My Pocket POS
package.name = mypocketpos
package.domain = org.pocketpos
source.dir = .
source.include_exts = py,png,jpg,jpeg,txt,kv,ini,csv,json
version = 0.1.0

# Your app only uses Kivy + stdlib
requirements = python3,kivy

orientation = portrait
fullscreen = 0

# You read/write JSON under /storage/emulated/0/projects/...
# On modern Android these classic permissions may still be needed for user-visible files.
android.permissions = INTERNET, READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE, READ_MEDIA_IMAGES, READ_MEDIA_VIDEO, READ_MEDIA_AUDIO

# Modern Android / toolchain versions
android.api = 34
android.minapi = 24
android.ndk = 25b
android.archs = arm64-v8a, armeabi-v7a
p4a.branch = master
android.gradle_build_tools_version = 8.1.1
android.sdk = 34

# Logging
log_level = 2

[buildozer]
log_level = 2
warn_on_root = 0

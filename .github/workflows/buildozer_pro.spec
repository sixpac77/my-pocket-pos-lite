[app]
title = My Pocket POS
package.name = MyPocketPOS
package.domain = org.homepos
source.dir = .
source.include_exts = py,kv,png,jpg,jpeg,svg,ttf,otf,ini,json,csv
version = 0.2.0
requirements = python3,kivy==2.3.0
orientation = portrait
fullscreen = 0
log_level = 1
android.archs = arm64-v8a, armeabi-v7a
android.allow_backup = True

# External storage/media permissions for Import/Export to Downloads
android.permissions = READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE, READ_MEDIA_IMAGES, READ_MEDIA_VIDEO, READ_MEDIA_AUDIO

android.api = 33
android.minapi = 24
android.ndk_api = 24
android.strip = True

icon.filename = %(source.dir)s/icon.png
presplash.filename = %(source.dir)s/presplash.png

[buildozer]
log_level = 2
warn_on_root = 0

[app:source.exclude_patterns]
.git
.github
__pycache__
*.yml
*.md

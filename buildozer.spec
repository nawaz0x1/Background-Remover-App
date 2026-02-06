[app]

# App info
title = Background Remover
package.name = backgroundremover
package.domain = app.quantflow
source.dir = .
source.include_exts = py,png,jpg,jpeg,kv,atlas,onnx,txt
source.include_patterns = models/*.onnx
source.exclude_dirs = __pycache__,.git,.venv,venv,build,.buildozer,p4a-recipes

version = 1.0.0

# Requirements - Android compatible
# Direct ONNX inference – no rembg/scipy/scikit-image (need gfortran / legacy NDK).
requirements = python3,kivy==2.3.1,kivymd==1.2.0,pillow,plyer,numpy,onnxruntime

# Android configuration
# Storage: READ/WRITE for <API 33, READ_MEDIA_IMAGES for API 33+
android.permissions = INTERNET,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE,READ_MEDIA_IMAGES
android.api = 33
android.minapi = 24
android.ndk = 25b
android.accept_sdk_license = True
android.arch = arm64-v8a

# Gradle / Java
android.gradle_dependencies =
android.enable_androidx = True

# Build
fullscreen = 0
orientation = portrait

# Icon and presplash (create these files for branding)
# icon.filename = %(source.dir)s/assets/icon.png
# presplash.filename = %(source.dir)s/assets/presplash.png

# Include the ONNX model in the APK
android.add_src = models/

# Privacy – opt out of advertising ID (Play Store requirement)
android.meta_data = com.google.android.gms.ads.AD_MANAGER_APP=false

# Custom p4a recipes (onnxruntime has no upstream recipe)
p4a.local_recipes = ./p4a-recipes

# Logging
log_level = 2

# P4A settings
p4a.branch = develop

[buildozer]
log_level = 2
warn_on_root = 1

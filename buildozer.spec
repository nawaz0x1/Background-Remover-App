[app]

# App info
title = Background Remover
package.name = backgroundremover
package.domain = app.quantflow
source.dir = .
source.include_exts = py,png,jpg,jpeg,kv,atlas,onnx,txt
source.include_patterns = models/*.onnx
source.exclude_dirs = __pycache__,.git,.venv,venv,build,.buildozer

version = 1.0.0

# Requirements - Android compatible
# We do direct ONNX inference (no rembg/scipy/scikit-image – they need
# a legacy NDK with gfortran which is unavailable on modern toolchains).
requirements = python3,kivy==2.3.1,kivymd==1.2.0,pillow,plyer,onnxruntime,numpy

# Android configuration
# Storage: READ/WRITE for <API 33, READ_MEDIA_IMAGES for API 33+
android.permissions = INTERNET,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE,READ_MEDIA_IMAGES
android.api = 33
android.minapi = 24
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

# Logging
log_level = 2

# P4A settings
p4a.branch = develop

[buildozer]
log_level = 2
warn_on_root = 1

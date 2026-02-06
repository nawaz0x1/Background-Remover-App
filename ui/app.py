"""
KivyMD App Definition
"""

import os
import sys
from kivymd.app import MDApp
from kivy.core.window import Window
from kivy.utils import platform
from kivy.properties import BooleanProperty
from ui.screens import MainScreen


class RemoveBGApp(MDApp):
    """Main application class"""

    # True once storage permission is granted (always True on desktop)
    storage_permission_granted = BooleanProperty(platform != "android")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.title = "BG Remover"

        # Only set window size on desktop
        if platform not in ("android", "ios"):
            Window.size = (400, 700)

    def build(self):
        """Build the application UI"""
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Teal"

        self._main_screen = MainScreen(name="main")

        # Request Android permissions with proper callback
        if platform == "android":
            from kivy.clock import Clock
            Clock.schedule_once(lambda dt: self._request_android_permissions(), 0.5)

        return self._main_screen

    def on_start(self):
        """Called when the app starts"""
        import threading
        thread = threading.Thread(target=self._preload_model, daemon=True)
        thread.start()

    def _preload_model(self):
        """Pre-load the background removal model"""
        try:
            from bg_remover import get_session
            get_session()
        except Exception:
            pass

    # ---- Android permission handling ----

    def _request_android_permissions(self):
        """Request storage permissions appropriate for the Android API level."""
        try:
            from android.permissions import request_permissions, Permission, check_permission
            from android import api_version

            perms = []
            if int(api_version) >= 33:
                # Android 13+ uses granular media permissions
                perms.append(Permission.READ_MEDIA_IMAGES)
            else:
                perms.append(Permission.READ_EXTERNAL_STORAGE)
                perms.append(Permission.WRITE_EXTERNAL_STORAGE)

            # Already granted?
            if all(check_permission(p) for p in perms):
                self.storage_permission_granted = True
                return

            request_permissions(perms, self._on_permission_result)

        except Exception:
            # Fallback – assume granted (desktop / import failure)
            self.storage_permission_granted = True

    def _on_permission_result(self, permissions, grant_results):
        """Callback after user responds to the permission dialog."""
        from kivy.clock import Clock
        if all(grant_results):
            self.storage_permission_granted = True
        else:
            self.storage_permission_granted = False
            Clock.schedule_once(
                lambda dt: setattr(
                    self._main_screen, "status_text",
                    "Storage permission denied – cannot load/save images."
                ), 0
            )

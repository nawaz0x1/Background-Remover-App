"""
KivyMD App Definition
"""

import os
import sys
from kivymd.app import MDApp
from kivy.core.window import Window
from kivy.utils import platform
from ui.screens import MainScreen


class RemoveBGApp(MDApp):
    """Main application class"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.title = "BG Remover"
        
        # Only set window size on desktop
        if platform not in ('android', 'ios'):
            Window.size = (400, 700)
    
    def build(self):
        """Build the application UI"""
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Teal"
        
        # Request Android permissions
        if platform == 'android':
            self._request_android_permissions()
        
        return MainScreen(name="main")
    
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
    
    def _request_android_permissions(self):
        """Request storage permissions on Android"""
        try:
            from android.permissions import request_permissions, Permission
            request_permissions([
                Permission.READ_EXTERNAL_STORAGE,
                Permission.WRITE_EXTERNAL_STORAGE,
                Permission.READ_MEDIA_IMAGES,
            ])
        except ImportError:
            pass

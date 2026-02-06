"""
KivyMD Screen Definitions
"""

from kivy.lang import Builder
from kivy.properties import StringProperty, BooleanProperty, ListProperty, NumericProperty
from kivy.clock import Clock
from kivy.uix.colorpicker import ColorPicker
from kivy.uix.modalview import ModalView
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.graphics.texture import Texture
from kivy.graphics import Color, Rectangle
from kivy.uix.widget import Widget
from kivy.utils import platform
from kivymd.uix.screen import MDScreen
from plyer import filechooser
import threading
import os
import tempfile
import shutil
from PIL import Image as PILImage

# Path for generated checkerboard image
_CHECKER_PATH = os.path.join(tempfile.gettempdir(), "rembg_checker.png")


def _create_checker_image():
    """Create a checkerboard PNG file for transparent background preview"""
    if os.path.exists(_CHECKER_PATH):
        return _CHECKER_PATH
    # Classic white/light-grey checkerboard
    square_size = 10
    cols, rows = 40, 40
    w = cols * square_size
    h = rows * square_size
    img = PILImage.new('RGB', (w, h))
    pixels = img.load()
    c1 = (255, 255, 255)
    c2 = (204, 204, 204)
    for y in range(h):
        for x in range(w):
            if (x // square_size + y // square_size) % 2 == 0:
                pixels[x, y] = c1
            else:
                pixels[x, y] = c2
    img.save(_CHECKER_PATH)
    return _CHECKER_PATH


class ImagePreview(Widget):
    """Widget that draws bg color/checkerboard behind image, matching image aspect ratio"""
    source = StringProperty("")
    bg_color = ListProperty([0, 0, 0, 0])
    show_checker = BooleanProperty(True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._image = None
        self._checker_image = None
        self.bind(source=self._redraw, bg_color=self._redraw,
                  show_checker=self._redraw, size=self._redraw, pos=self._redraw)

    def _get_image_rect(self):
        """Calculate centered rect that preserves image aspect ratio"""
        if not self._image or not self._image.texture:
            return self.pos[0], self.pos[1], self.size[0], self.size[1]
        tw, th = self._image.texture.size
        if tw == 0 or th == 0:
            return self.pos[0], self.pos[1], self.size[0], self.size[1]
        aspect = tw / th
        w, h = self.size
        if w / h > aspect:
            new_w = h * aspect
            new_h = h
        else:
            new_w = w
            new_h = w / aspect
        x = self.pos[0] + (w - new_w) / 2
        y = self.pos[1] + (h - new_h) / 2
        return x, y, new_w, new_h

    def _redraw(self, *args):
        if not self.source:
            # Hide checker and image when no source
            if self._checker_image:
                self._checker_image.opacity = 0
            if self._image:
                self._image.opacity = 0
            return

        # Lazy create child widgets
        if self._checker_image is None:
            from kivy.uix.image import Image as KivyImage
            self._checker_image = KivyImage(
                allow_stretch=True, keep_ratio=True, opacity=0
            )
            self.add_widget(self._checker_image)

        if self._image is None:
            from kivy.uix.image import Image as KivyImage
            self._image = KivyImage(
                allow_stretch=True, keep_ratio=True
            )
            self.add_widget(self._image)

        self._image.source = self.source
        self._image.size = self.size
        self._image.pos = self.pos
        self._image.opacity = 1

        x, y, w, h = self._get_image_rect()

        # Show checkerboard or solid color behind image
        self.canvas.before.clear()
        if self.show_checker:
            # Use checkerboard image behind the actual image
            checker_path = _create_checker_image()
            self._checker_image.source = checker_path
            self._checker_image.pos = (x, y)
            self._checker_image.size = (w, h)
            self._checker_image.opacity = 1
        else:
            self._checker_image.opacity = 0
            with self.canvas.before:
                Color(*self.bg_color)
                Rectangle(pos=(x, y), size=(w, h))


KV = '''
<ColorDot@MDIconButton>:
    icon: "circle"
    size_hint: None, None
    size: dp(32), dp(32)
    user_font_size: dp(20)

<MainScreen>:
    MDBoxLayout:
        orientation: "vertical"
        padding: dp(16)
        spacing: dp(10)
        
        # ---- WELCOME STATE (no image) ----
        MDBoxLayout:
            orientation: "vertical"
            size_hint_y: 1 if not root.image_source else 0.001
            opacity: 1 if not root.image_source else 0
            spacing: dp(8)
            
            Widget:
                size_hint_y: 1
            
            MDIconButton:
                icon: "image-plus"
                pos_hint: {"center_x": 0.5}
                user_font_size: dp(80)
                theme_text_color: "Hint"
                on_release: root.select_image()
            
            MDLabel:
                text: "Tap to select an image"
                halign: "center"
                theme_text_color: "Hint"
                font_style: "Subtitle1"
                size_hint_y: None
                height: dp(30)
            
            MDLabel:
                text: "Supports PNG, JPG, WEBP, BMP"
                halign: "center"
                theme_text_color: "Hint"
                font_style: "Caption"
                size_hint_y: None
                height: dp(20)
            
            Widget:
                size_hint_y: 1
            
            MDRaisedButton:
                text: "Select Image"
                pos_hint: {"center_x": 0.5}
                on_release: root.select_image()
                size_hint_x: 0.6
            
            Widget:
                size_hint_y: 0.3
        
        # ---- IMAGE STATE ----
        ImagePreview:
            id: img_preview
            size_hint_y: 1 if root.image_source else 0.001
            opacity: 1 if root.image_source else 0
            source: root.image_source
            bg_color: root.preview_bg_color
            show_checker: root.show_checker
        
        # Background color options
        MDBoxLayout:
            orientation: "vertical"
            size_hint_y: None
            height: dp(64) if root.result_available else 0
            opacity: 1 if root.result_available else 0
            spacing: dp(2)
            
            MDLabel:
                text: "Background"
                halign: "center"
                size_hint_y: None
                height: dp(18)
                font_style: "Caption"
                theme_text_color: "Secondary"
            
            ScrollView:
                size_hint_y: None
                height: dp(40)
                do_scroll_y: False
                
                MDBoxLayout:
                    id: color_row
                    orientation: "horizontal"
                    size_hint_x: None
                    width: self.minimum_width
                    spacing: dp(4)
                    padding: [dp(4), dp(2), dp(4), dp(2)]
                    
                    MDIconButton:
                        id: btn_transparent
                        icon: "checkerboard"
                        size_hint: None, None
                        size: dp(32), dp(32)
                        user_font_size: dp(18)
                        on_release: root.set_bg_transparent()
                        theme_text_color: "Custom"
                        text_color: [0.6, 0.6, 0.6, 1]
                        md_bg_color: root.selected_btn_bg if root.selected_color_name == "transparent" else [0, 0, 0, 0]
                    
                    ColorDot:
                        id: btn_white
                        on_release: root.set_bg_color(1, 1, 1, 1, "white")
                        theme_text_color: "Custom"
                        text_color: [1, 1, 1, 1]
                        md_bg_color: [0.95, 0.95, 0.95, 1] if root.selected_color_name != "white" else root.selected_btn_bg
                    
                    ColorDot:
                        id: btn_black
                        on_release: root.set_bg_color(0, 0, 0, 1, "black")
                        theme_text_color: "Custom"
                        text_color: [0.1, 0.1, 0.1, 1]
                        md_bg_color: [0.12, 0.12, 0.12, 1] if root.selected_color_name != "black" else root.selected_btn_bg
                    
                    ColorDot:
                        id: btn_blue
                        on_release: root.set_bg_color(0.13, 0.59, 0.95, 1, "blue")
                        theme_text_color: "Custom"
                        text_color: [0.13, 0.59, 0.95, 1]
                        md_bg_color: [0.13, 0.59, 0.95, 1] if root.selected_color_name != "blue" else root.selected_btn_bg
                    
                    ColorDot:
                        id: btn_green
                        on_release: root.set_bg_color(0.3, 0.69, 0.31, 1, "green")
                        theme_text_color: "Custom"
                        text_color: [0.3, 0.69, 0.31, 1]
                        md_bg_color: [0.3, 0.69, 0.31, 1] if root.selected_color_name != "green" else root.selected_btn_bg
                    
                    ColorDot:
                        id: btn_red
                        on_release: root.set_bg_color(0.96, 0.26, 0.21, 1, "red")
                        theme_text_color: "Custom"
                        text_color: [0.96, 0.26, 0.21, 1]
                        md_bg_color: [0.96, 0.26, 0.21, 1] if root.selected_color_name != "red" else root.selected_btn_bg
                    
                    ColorDot:
                        id: btn_yellow
                        on_release: root.set_bg_color(1, 0.76, 0.03, 1, "yellow")
                        theme_text_color: "Custom"
                        text_color: [1, 0.76, 0.03, 1]
                        md_bg_color: [1, 0.76, 0.03, 1] if root.selected_color_name != "yellow" else root.selected_btn_bg
                    
                    MDIconButton:
                        id: btn_custom
                        icon: "palette"
                        size_hint: None, None
                        size: dp(32), dp(32)
                        user_font_size: dp(18)
                        on_release: root.open_color_picker()
                        theme_text_color: "Custom"
                        text_color: app.theme_cls.primary_color
                        md_bg_color: root.selected_btn_bg if root.selected_color_name == "custom" else [0, 0, 0, 0]
        
        # Status text
        MDLabel:
            id: status_label
            text: root.status_text
            halign: "center"
            size_hint_y: None
            height: dp(20)
            font_style: "Caption"
            theme_text_color: "Secondary"
        
        # Progress indicator
        MDSpinner:
            id: progress
            size_hint: None, None
            size: dp(36), dp(36)
            pos_hint: {"center_x": 0.5}
            active: root.is_processing
        
        # Action buttons (when image is loaded)
        MDBoxLayout:
            orientation: "vertical"
            spacing: dp(8)
            size_hint_y: None
            height: dp(110) if root.image_source else 0
            opacity: 1 if root.image_source else 0
            
            MDBoxLayout:
                orientation: "horizontal"
                spacing: dp(12)
                size_hint_y: None
                height: dp(46)
                
                MDRaisedButton:
                    text: "Select Image"
                    on_release: root.select_image()
                    size_hint_x: 1
                
                MDRaisedButton:
                    text: "Remove BG"
                    on_release: root.process_image()
                    disabled: not root.image_source or root.is_processing
                    size_hint_x: 1
            
            MDRaisedButton:
                text: "Save Result"
                on_release: root.save_image()
                disabled: not root.result_available
                size_hint_x: 1
                size_hint_y: None
                height: dp(46)
'''

# Load KV before class definition
Builder.load_string(KV)


class MainScreen(MDScreen):
    """Main screen for background removal app"""
    
    image_source = StringProperty("")
    status_text = StringProperty("")
    is_processing = BooleanProperty(False)
    result_available = BooleanProperty(False)
    bg_color = ListProperty([0, 0, 0, 0])
    preview_bg_color = ListProperty([0.18, 0.18, 0.18, 1])
    show_checker = BooleanProperty(False)
    selected_color_name = StringProperty("transparent")
    selected_btn_bg = ListProperty([0.0, 0.75, 0.65, 0.4])  # Teal highlight
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._original_path = None
        self._result_path = None
        self._result_image = None
        self._temp_input_path = None  # temp copy of selected image on Android
    
    def select_image(self):
        """Open file chooser to select an image"""
        try:
            filechooser.open_file(
                on_selection=self._on_file_selected,
                filters=[("Images", "*.png", "*.jpg", "*.jpeg", "*.webp", "*.bmp")]
            )
        except Exception as e:
            self.status_text = f"Error: {str(e)}"
    
    def _resolve_android_uri(self, uri):
        """
        On Android, plyer returns a content:// URI which Kivy/PIL cannot
        read directly. Copy the file to a local temp path via the
        ContentResolver and return the temp path.
        """
        try:
            from jnius import autoclass
            PythonActivity = autoclass("org.kivy.android.PythonActivity")
            context = PythonActivity.mActivity
            resolver = context.getContentResolver()
            InputStream = autoclass("java.io.InputStream")
            Uri = autoclass("android.net.Uri")

            parsed = Uri.parse(uri)
            stream = resolver.openInputStream(parsed)

            # Determine a reasonable extension from the URI or MIME type
            ext = ".jpg"
            mime = resolver.getType(parsed)
            if mime:
                if "png" in mime:
                    ext = ".png"
                elif "webp" in mime:
                    ext = ".webp"
                elif "bmp" in mime:
                    ext = ".bmp"

            fd, tmp = tempfile.mkstemp(suffix=ext)
            os.close(fd)

            # Read bytes from InputStream and write to temp file
            with open(tmp, "wb") as fout:
                buf = bytearray(8192)
                while True:
                    n = stream.read(buf)
                    if n == -1:
                        break
                    fout.write(bytes(buf[:n]))
            stream.close()

            return tmp
        except Exception as e:
            print(f"[BG Remover] _resolve_android_uri failed: {e}")
            return None
    
    def _on_file_selected(self, selection):
        """Handle file selection — schedule on main thread for safety."""
        Clock.schedule_once(lambda dt: self._handle_selection(selection), 0)
    
    def _handle_selection(self, selection):
        """Process the selected file path (main-thread)."""
        if not selection:
            return

        path = selection[0]

        # Clean up previous temp input
        if self._temp_input_path and os.path.exists(self._temp_input_path):
            try:
                os.remove(self._temp_input_path)
            except OSError:
                pass
            self._temp_input_path = None

        # On Android, resolve content:// URIs to a local temp file
        if platform == "android" and str(path).startswith("content://"):
            self.status_text = "Loading image..."
            resolved = self._resolve_android_uri(path)
            if resolved is None:
                self.status_text = "Error: could not read file"
                return
            self._temp_input_path = resolved
            path = resolved

        self._original_path = path
        self.image_source = path
        self.status_text = f"Loaded: {os.path.basename(path)}"
        self.result_available = False
        self._result_image = None
        self.bg_color = [0, 0, 0, 0]
    
    def process_image(self):
        """Process the image to remove background"""
        if not self.image_source or self.is_processing:
            return
        
        self.is_processing = True
        self.status_text = "Processing..."
        
        # Run in background thread
        thread = threading.Thread(target=self._process_in_thread)
        thread.start()
    
    def _process_in_thread(self):
        """Background thread for image processing"""
        try:
            from bg_remover import remove_background
            
            # Create temp file for result
            fd, temp_path = tempfile.mkstemp(suffix=".png")
            os.close(fd)
            
            # Process image and keep PIL result
            result_img = remove_background(self._original_path, temp_path)
            
            self._result_path = temp_path
            self._result_image = result_img
            
            # Update UI on main thread
            Clock.schedule_once(lambda dt: self._on_process_complete(True))
            
        except Exception as e:
            Clock.schedule_once(lambda dt: self._on_process_complete(False, str(e)))
    
    def _on_process_complete(self, success, error=None):
        """Called when processing completes"""
        self.is_processing = False
        
        if success:
            self.image_source = self._result_path
            self.status_text = "Done! Pick a background color below."
            self.result_available = True
            self.bg_color = [0, 0, 0, 0]
            self.show_checker = True
            self.selected_color_name = "transparent"
        else:
            self.status_text = f"Error: {error}"
    
    def set_bg_transparent(self):
        """Set background to transparent checkerboard"""
        self.bg_color = [0, 0, 0, 0]
        self.show_checker = True
        self.selected_color_name = "transparent"
        self.status_text = "Transparent (saves as PNG)"
    
    def set_bg_color(self, r, g, b, a, name=""):
        """Set background color and update preview"""
        self.bg_color = [r, g, b, a]
        self.preview_bg_color = [r, g, b, 1]
        self.show_checker = False
        self.selected_color_name = name
        self.status_text = "Background color set"
    
    def open_color_picker(self):
        """Open Kivy's built-in color picker in a popup"""
        popup = ModalView(size_hint=(0.9, 0.7))
        
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        picker = ColorPicker()
        layout.add_widget(picker)
        
        btn_layout = BoxLayout(size_hint_y=None, height=50, spacing=10)
        
        select_btn = Button(text='Select', background_color=(0.2, 0.7, 0.4, 1))
        cancel_btn = Button(text='Cancel', background_color=(0.5, 0.5, 0.5, 1))
        
        def on_select(_):
            c = picker.color
            self.set_bg_color(c[0], c[1], c[2], 1, "custom")
            popup.dismiss()
        
        def on_cancel(_):
            popup.dismiss()
        
        select_btn.bind(on_release=on_select)
        cancel_btn.bind(on_release=on_cancel)
        
        btn_layout.add_widget(cancel_btn)
        btn_layout.add_widget(select_btn)
        layout.add_widget(btn_layout)
        
        popup.add_widget(layout)
        popup.open()
    
    def save_image(self):
        """Save the processed image"""
        if not self._result_path:
            return
        
        try:
            # Get save location
            filechooser.save_file(
                on_selection=self._on_save_location_selected,
                filters=[("PNG Image", "*.png")]
            )
        except Exception as e:
            # Fallback: save next to original
            self._save_next_to_original()
    
    def _on_save_location_selected(self, selection):
        """Handle save location selection"""
        if selection:
            save_path = selection[0]
            if not save_path.lower().endswith('.png'):
                save_path += '.png'
            self._do_save(save_path)
    
    def _save_next_to_original(self):
        """Save result to a known location as fallback."""
        if platform == "android":
            # On Android, save to shared Pictures directory
            try:
                from android.storage import primary_external_storage_path
                pictures = os.path.join(primary_external_storage_path(), "Pictures")
                os.makedirs(pictures, exist_ok=True)
                base = os.path.splitext(os.path.basename(self._original_path or "image"))[0]
                save_path = os.path.join(pictures, f"{base}_nobg.png")
            except Exception:
                save_path = os.path.join(tempfile.gettempdir(), "result_nobg.png")
        elif self._original_path:
            base, ext = os.path.splitext(self._original_path)
            save_path = f"{base}_nobg.png"
        else:
            save_path = os.path.join(tempfile.gettempdir(), "result_nobg.png")
        self._do_save(save_path)
    
    def _do_save(self, save_path):
        """Actually save the file with background color applied"""
        try:
            if self._result_image and self.bg_color[3] > 0:
                result = self._apply_bg_color(self._result_image)
                result.save(save_path)
            else:
                shutil.copy2(self._result_path, save_path)
            
            self.status_text = f"Saved: {os.path.basename(save_path)}"
        except Exception as e:
            self.status_text = f"Save failed: {str(e)}"
    
    def _apply_bg_color(self, img):
        """Apply background color to image"""
        if img.mode != 'RGBA':
            return img
        
        r = int(self.bg_color[0] * 255)
        g = int(self.bg_color[1] * 255)
        b = int(self.bg_color[2] * 255)
        
        background = PILImage.new('RGBA', img.size, (r, g, b, 255))
        background.paste(img, mask=img.split()[3])
        
        return background

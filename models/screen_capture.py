import io
import mss
from PIL import Image


class ScreenCapture:
    def __init__(self, config):
        self.settings = config.get('screenshot_settings', {})
        self.quality = self.settings.get('quality', 80)
        self.ratio = self.settings.get('resize_ratio', 1.0)
        self.enabled = self.settings.get('enabled', False)

    def capture_to_memory(self):
        """
        Captures the primary screen, optimizes it, and returns bytes.
        Returns: (bytes_data, filename) or (None, None)
        """
        if not self.enabled:
            return None, None

        try:
            with mss.mss() as sct:
                # Capture Primary Monitor (monitor 1)
                sct_img = sct.grab(sct.monitors[1])

                # Convert to Pillow Image
                img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")

                # Resize if requested (Optimization)
                if self.ratio != 1.0:
                    new_size = (int(img.width * self.ratio), int(img.height * self.ratio))
                    img = img.resize(new_size, Image.Resampling.LANCZOS)

                # Save to Memory Buffer (RAM) as WebP
                buffer = io.BytesIO()
                img.save(buffer, format="WEBP", quality=self.quality, method=4)
                buffer.seek(0)

                return buffer, "screenshot.webp"

        except Exception as e:
            print(f"❌ Screenshot Failed: {e}")
            return None, None

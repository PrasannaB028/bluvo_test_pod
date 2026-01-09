import cv2
import numpy as np
from pathlib import Path

class StyleEngine:
    """
    Production-safe style selector for car videos
    """

    def __init__(self, fonts_dir="fonts"):
        self.fonts_dir = Path(fonts_dir)

    # --------------------------------------------------
    # BRIGHTNESS CHECK (ONLY FOR GLOW)
    # --------------------------------------------------

    def _get_brightness(self, video):
        frames = np.linspace(0, min(video.duration, 3), 3)
        values = []

        for t in frames:
            frame = video.get_frame(t)
            gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
            values.append(np.mean(gray))

        return "dark" if np.mean(values) < 130 else "light"

    # --------------------------------------------------
    # STYLE PRESETS
    # --------------------------------------------------

    def generate_style(self, video, mode="luxury"):
        brightness = self._get_brightness(video)

        # ---------- COLOR PRESETS ----------
        if mode == "sport":
            number_color = (0, 180, 255, 255)    # blue
            desc_color   = (255, 255, 255, 255)
        elif mode == "luxury":
            number_color = (220, 180, 90, 255)   # gold
            desc_color   = (0, 180, 255, 255)
        else:
            number_color = (255, 204, 0, 255)    # yellow
            desc_color   = (255, 255, 255, 255)

        glow = (0, 0, 0, 180) if brightness == "light" else (255, 255, 255, 120)

        return {
            # Fonts (LOCKED, not random)
            "FONT_NUMBER": str(self.fonts_dir / "Monoton-Regular.ttf"),
            "FONT_DESC": str(self.fonts_dir / "BungeeTint-Regular.ttf"),

            # Sizes
            "NUMBER_FONT_SIZE": 88,
            "DESC_FONT_SIZE": 84,

            # Colors
            "NUMBER_COLOR": number_color,
            "DESC_COLOR": desc_color,

            # Glow
            "GLOW_COLOR": glow,
            "GLOW_BLUR": 16,

            # Layout
            "LINE_GAP": 14,
            "PADDING": 42,
            "FADE": 0.15,
        }

from PIL import Image, ImageDraw, ImageFont, ImageFilter
import random


class TextRenderer:
    def __init__(self, config):
        self.cfg = config
        self.font_path_desc = config["FONT_DESC"]
        self.font_path_number = config["FONT_NUMBER"]
        self.base_font_size = config["DESC_FONT_SIZE"]

    # ======================================================
    # FONT SCALING (CRITICAL FIX)
    # ======================================================
    def _get_fonts(self, video_width):
        """
        Scale font size based on video width.
        1920px is treated as baseline.
        """
        scale = video_width / 1920.0
        size = int(self.base_font_size * scale)
        size = max(40, min(size, 96))  # clamp for safety

        return {
            "desc": ImageFont.truetype(self.font_path_desc, size),
            "number": ImageFont.truetype(self.font_path_number, int(size * 1.05)),
        }

    # ======================================================
    # SMART SEMANTIC LINE SPLIT
    # ======================================================
    def _smart_split(self, text, max_chars=18):
        """
        Break lines semantically instead of character-wrap.
        """
        words = text.split()
        lines = []
        line = []

        for w in words:
            test = " ".join(line + [w])
            if len(test) > max_chars:
                lines.append(" ".join(line))
                line = [w]
            else:
                line.append(w)

        if line:
            lines.append(" ".join(line))

        return lines

    # ======================================================
    # MAIN HIGHLIGHT RENDER
    # ======================================================
    def render_highlight(self, text, align="center", video_width=1920):
        pad = self.cfg["PADDING"]
        gap = self.cfg["LINE_GAP"]

        text = text.strip()

        # CASE RULES
        styled_words = []
        char_count = len(text)

        for w in text.split():
            if any(c.isdigit() for c in w):
                styled_words.append(w.upper())
            else:
                if char_count <= 20:
                    styled_words.append(w.upper())
                elif char_count <= 30:
                    styled_words.append(random.choice([w.upper(), w.title()]))
                else:
                    styled_words.append(random.choice([w.upper(), w.title(), w.lower()]))

        styled_text = " ".join(styled_words)

        # SMART SPLIT
        lines = self._smart_split(styled_text)

        # FONTS (VIDEO AWARE)
        fonts = self._get_fonts(video_width)

        dummy = Image.new("RGBA", (10, 10))
        d = ImageDraw.Draw(dummy)

        # MEASURE
        line_info = []
        max_w = 0

        for line in lines:
            font = fonts["number"] if any(c.isdigit() for c in line) else fonts["desc"]
            bbox = d.textbbox((0, 0), line, font=font)
            w = bbox[2] - bbox[0]
            h = bbox[3] - bbox[1]
            line_info.append((line, font, w, h))
            max_w = max(max_w, w)

        ascent, descent = fonts["desc"].getmetrics()
        img_w = max_w + pad * 2
        img_h = sum(h for _, _, _, h in line_info) + gap * (len(lines) - 1) + pad * 2 + descent

        base = Image.new("RGBA", (img_w, img_h), (0, 0, 0, 0))

        # --------------------------------------------------
        # GLOW
        # --------------------------------------------------
        glow = Image.new("RGBA", base.size, (0, 0, 0, 0))
        gd = ImageDraw.Draw(glow)

        y = pad
        for line, font, w, h in line_info:
            if align == "center":
                x = (img_w - w) // 2
            elif align == "right":
                x = img_w - w - pad
            else:
                x = pad

            gd.text((x, y), line, font=font, fill=self.cfg["GLOW_COLOR"])
            y += h + gap

        glow = glow.filter(ImageFilter.GaussianBlur(self.cfg["GLOW_BLUR"]))
        base = Image.alpha_composite(base, glow)

        # --------------------------------------------------
        # MAIN TEXT
        # --------------------------------------------------
        dr = ImageDraw.Draw(base)
        y = pad

        for line, font, w, h in line_info:
            if align == "center":
                x = (img_w - w) // 2
            elif align == "right":
                x = img_w - w - pad
            else:
                x = pad

            color = self.cfg["NUMBER_COLOR"] if any(c.isdigit() for c in line) else self.cfg["DESC_COLOR"]
            dr.text((x, y), line, font=font, fill=color)
            y += h + gap

        return base

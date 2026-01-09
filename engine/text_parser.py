import re

class TextParser:
    @staticmethod
    def extract(text: str):
        """
        Extracts leading numeric value ONLY for feature cards.
        Does NOT interfere with highlight text.
        """
        text = text.upper().strip()

        # Match ONLY pure numeric titles like:
        # "200 KM RANGE", "6 SPEED MANUAL", "350 LITERS BOOT SPACE"
        match = re.match(
            r'^(\d+(?:\.\d+)?)(?:\s+)([A-Z].*)',
            text
        )

        if match:
            number = match.group(1).strip()
            desc = match.group(2).strip()
            return number, desc

        return None, text

    @staticmethod
    def split_lines(text, max_chars=22):
        """
        Safe line split for UI cards (not highlights)
        """
        words = text.split()
        lines, line = [], []

        for w in words:
            if len(" ".join(line + [w])) <= max_chars:
                line.append(w)
            else:
                lines.append(" ".join(line))
                line = [w]

        if line:
            lines.append(" ".join(line))

        return lines

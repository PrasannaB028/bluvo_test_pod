from .production_highlight_matcher import extract_highlights

class HighlightEngine:
    def __init__(self, audio_path):
        self.audio_path = audio_path

    def run(self, highlights):
        return extract_highlights(self.audio_path, highlights)

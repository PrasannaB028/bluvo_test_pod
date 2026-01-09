from faster_whisper import WhisperModel

def normalize(text):
    return (
        text.upper()
        .replace(",", "")
        .replace(".", "")
        .replace("-", " ")
        .strip()
    )

class WhisperAligner:
    def __init__(self, model="large-v3"):
        self.model = WhisperModel(
            model,
            device="cuda",
            compute_type="float16"
        )

    def transcribe_words(self, audio_path):
        segments, info = self.model.transcribe(
            audio_path,
            language="en",          # 🔒 FORCE ENGLISH
            task="transcribe",      # 🔒 NO TRANSLATION
            word_timestamps=True,
            vad_filter=True,        # optional but good
            beam_size=5
        )

        words = []
        for seg in segments:
            for w in seg.words:
                words.append({
                    "word": normalize(w.word),
                    "start": w.start,
                    "end": w.end
                })
        return words

    def match_highlights(self, whisper_words, highlights):
        stream = [w["word"] for w in whisper_words]
        results = []

        for h in highlights:
            h_words = normalize(h).split()
            L = len(h_words)

            for i in range(len(stream) - L + 1):
                if stream[i:i+L] == h_words:
                    results.append({
                        "text": h,
                        "start": whisper_words[i]["start"],
                        "end": whisper_words[i+L-1]["end"]
                    })
                    break

        return results

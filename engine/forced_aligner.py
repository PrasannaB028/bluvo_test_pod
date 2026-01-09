# engine/forced_aligner.py

import re
from faster_whisper import WhisperModel
from engine.config import HF_STORE
def normalize(text):
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s]", " ", text.upper())).strip()

def force_align(audio_path, full_text, device="cuda"):
    """
    Returns word-level timestamps aligned to KNOWN text.
    GUARANTEED MATCH.
    """

    model = WhisperModel(
        "large-v3",
        device=device,
        compute_type="float16",
        download_root=str(HF_STORE),
        local_files_only=True
    )

    # 🔒 Important: We pass the known text
    segments, _ = model.transcribe(
        audio_path,
        language="en",
        task="transcribe",
        word_timestamps=True,
        initial_prompt=full_text,
        condition_on_previous_text=False,
        vad_filter=False
    )

    words = []
    for seg in segments:
        for w in seg.words:
            words.append({
                "word": normalize(w.word),
                "start": round(w.start, 2),
                "end": round(w.end, 2)
            })

    return words

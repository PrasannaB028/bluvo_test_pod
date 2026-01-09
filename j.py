from faster_whisper import WhisperModel
from engine.config import HF_STORE

model = WhisperModel(
    "large-v3",
    device="cuda",
    compute_type="float16",
)

print("Whisper loaded successfully")

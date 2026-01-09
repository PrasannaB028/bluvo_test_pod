from dotenv import load_dotenv
load_dotenv()

import os
import streamlit as st
from io import BytesIO
from elevenlabs.client import ElevenLabs

from engine.voice_registry import (
    list_voices,
    get_voice_id,
    add_voice
)
from pipeline.process_clip import process_single_clip
from pipeline.combine_clips import combine_clips

UPLOAD_DIR = "uploads"
CLIPS_DIR = "clips_output"
LOGO_PATH = "bluvo-logo.png"
FINAL_VIDEO = "final.mp4"

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(CLIPS_DIR, exist_ok=True)

CONFIG = {
    "BLUR_PLATE": True,
    "PLATE_MODEL_PATH": "models/lp_key_point.pt"
}

st.set_page_config(layout="wide")
st.title("🚗 AI Car Video Generator")

# ================= VOICE SECTION =================
st.header("🎙 Voice Selection")

mode = st.radio("Voice Mode", ["Use existing", "Create new"])
voice_id = None

if mode == "Use existing":
    voices = list_voices()
    if voices:
        name = st.selectbox("Choose voice", voices)
        voice_id = get_voice_id(name)
    else:
        st.warning("No voices saved")

else:
    name = st.text_input("Voice name")
    sample = st.file_uploader("Upload voice sample", type=["wav","mp3"])

    if sample and name and st.button("Clone Voice"):
        client = ElevenLabs(api_key=os.getenv("ELEVEN_API_KEY"))
        voice = client.voices.ivc.create(
            name=name,
            files=[BytesIO(sample.read())]
        )
        add_voice(name, voice.voice_id)
        voice_id = voice.voice_id
        st.success("Voice saved")

if not voice_id:
    st.stop()

# ================= CLIPS =================
CLIPS = ["Front View", "Back View", "Driver Side", "Passenger Side", "Interior"]
done = {}

for i, label in enumerate(CLIPS, 1):
    st.divider()
    st.subheader(label)

    video = st.file_uploader(f"{label} video", key=f"v{i}")
    tts = st.text_area("TTS Script", key=f"t{i}")
    highlights = st.text_area("Highlights (1 per line)", key=f"h{i}")

    if video and tts and highlights:
        if st.button(f"Generate {label}", key=f"g{i}"):
            raw = f"{UPLOAD_DIR}/{i}.mp4"
            out = f"{CLIPS_DIR}/{i}.mp4"
            with open(raw, "wb") as f:
                f.write(video.read())

            process_single_clip(
                raw,
                tts,
                highlights.splitlines(),
                out,
                CONFIG,
                voice_id
            )

            done[i] = out
            st.video(out)

# ================= FINAL =================
st.divider()
if len(done) == 5:
    if st.button("Combine All"):
        combine_clips(CLIPS_DIR, FINAL_VIDEO, LOGO_PATH)
        st.video(FINAL_VIDEO)

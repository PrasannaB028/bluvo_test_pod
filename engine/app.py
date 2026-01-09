from dotenv import load_dotenv
load_dotenv()


import os
import streamlit as st

from pipeline.process_clip import process_single_clip
from pipeline.combine_clips import combine_clips

# ======================================================
# PATHS
# ======================================================

UPLOAD_DIR = "uploads"
CLIPS_DIR = "clips_output"
FINAL_OUTPUT = "combined_output.mp4"
LOGO_PATH = "bluvo-logo.png"

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(CLIPS_DIR, exist_ok=True)

# ======================================================
# CONFIG (shared with backend)
# ======================================================

CONFIG = {
    "FONT_NUMBER": "fonts/BungeeTint-Regular.ttf",
    "FONT_DESC": "fonts/BungeeInline-Regular.ttf",

    "NUMBER_FONT_SIZE": 86,
    "DESC_FONT_SIZE": 86,

    "NUMBER_COLOR": (255, 255, 255, 255),
    "DESC_COLOR": (255, 200, 0, 255),
    "GLOW_COLOR": (120, 100, 0, 220),
    "GLOW_BLUR": 16,

    "LINE_GAP": 12,
    "PADDING": 40,
    "FADE": 0.15,

    "BLUR_PLATE": True,
    "PLATE_MODEL_PATH": "models/lp_key_point.pt",
}

CLIP_LABELS = [
    "Front View",
    "Back View",
    "Driver Side",
    "Passenger Side",
    "Interior",
]

# ======================================================
# STREAMLIT UI
# ======================================================

st.set_page_config(layout="wide")
st.title("🚗 AI Car Video Generator")

if "done" not in st.session_state:
    st.session_state.done = {}

for idx, label in enumerate(CLIP_LABELS, start=1):
    st.divider()
    st.subheader(f"{idx}. {label}")

    video = st.file_uploader(
        f"Upload {label} Video",
        type=["mp4"],
        key=f"vid_{idx}"
    )

    tts = st.text_area(
        "TTS Script (Tamil / English)",
        key=f"tts_{idx}",
        height=120
    )

    highlights = st.text_area(
        "Highlight Texts (English – one per line)",
        key=f"hl_{idx}",
        height=120
    )

    if video and tts and highlights:
        if st.button(f"Generate {label}", key=f"gen_{idx}"):
            with st.status(f"Processing {label}...", expanded=True):
                raw_path = os.path.join(UPLOAD_DIR, f"{idx}.mp4")
                out_path = os.path.join(CLIPS_DIR, f"{idx}.mp4")

                with open(raw_path, "wb") as f:
                    f.write(video.read())

                hl_list = [h.strip() for h in highlights.splitlines() if h.strip()]

                process_single_clip(
                    video_path=raw_path,
                    tts_script=tts,
                    highlights=hl_list,
                    output_path=out_path,
                    config=CONFIG
                )

                st.session_state.done[idx] = out_path
                st.success(f"{label} generated successfully")

    if idx in st.session_state.done:
        st.video(st.session_state.done[idx])
        st.caption("✔ You can regenerate this clip without affecting others")

# ---------------- FINAL MERGE ----------------

st.divider()
st.header("🎬 Final Output")

if len(st.session_state.done) == 5:
    if st.button("Combine All Clips"):
        with st.status("Rendering final video...", expanded=True):
            combine_clips(
                clips_dir=CLIPS_DIR,
                output_path=FINAL_OUTPUT,
                logo_path=LOGO_PATH
            )
        st.success("Final video ready")
        st.video(FINAL_OUTPUT)
else:
    st.warning(f"{5 - len(st.session_state.done)} clip(s) pending")

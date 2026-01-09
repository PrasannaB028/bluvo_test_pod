import os
import gradio as gr
from io import BytesIO
from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs

from engine.voice_registry import (
    list_voices,
    get_voice_id,
    add_voice
)

from pipeline.process_clip import process_single_clip
from pipeline.combine_clips import combine_clips

# --------------------------------------------------
# ENV
# --------------------------------------------------
load_dotenv()

UPLOAD_DIR = "uploads"
CLIPS_DIR = "clips_output"
FINAL_VIDEO = "final.mp4"
LOGO_PATH = "bluvo-logo.png"

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(CLIPS_DIR, exist_ok=True)

CONFIG = {
    "BLUR_PLATE": True,
    "PLATE_MODEL_PATH": "models/lp_key_point.pt"
}

# --------------------------------------------------
# Voice handlers
# --------------------------------------------------
def clone_voice(name, sample):
    if not name or not sample:
        raise gr.Error("Voice name and sample required")

    client = ElevenLabs(api_key=os.getenv("ELEVEN_API_KEY"))
    voice = client.voices.ivc.create(
        name=name,
        files=[BytesIO(sample)]
    )

    add_voice(name, voice.voice_id)
    return gr.update(choices=list_voices()), "✅ Voice cloned"

# --------------------------------------------------
# Main pipeline
# --------------------------------------------------
def generate_all(
    voice_name,

    front_v, front_t, front_h,
    rear_v, rear_t, rear_h,
    driver_v, driver_t, driver_h,
    passenger_v, passenger_t, passenger_h,
    interior_v, interior_t, interior_h,
):
    voice_id = get_voice_id(voice_name)
    if not voice_id:
        raise gr.Error("Invalid voice selected")

    clips = [
        front_v, rear_v, driver_v, passenger_v, interior_v
    ]
    texts = [
        front_t, rear_t, driver_t, passenger_t, interior_t
    ]
    highlights = [
        front_h, rear_h, driver_h, passenger_h, interior_h
    ]

    for i in range(5):
        if not clips[i] or not texts[i] or not highlights[i]:
            raise gr.Error(f"Section {i+1} incomplete")

        raw = f"{UPLOAD_DIR}/{i+1}.mp4"
        out = f"{CLIPS_DIR}/{i+1}.mp4"

        with open(raw, "wb") as f:
            f.write(clips[i])

        process_single_clip(
            video_path=raw,
            tts_script=texts[i],
            highlights=highlights[i].splitlines(),
            output_path=out,
            config=CONFIG,
            voice_id=voice_id
        )

    combine_clips(
        clips_dir=CLIPS_DIR,
        output_path=FINAL_VIDEO,
        logo_path=LOGO_PATH,
        compress=True,
        compression_crf=24
    )

    return FINAL_VIDEO

# --------------------------------------------------
# UI
# --------------------------------------------------
with gr.Blocks(title="AI Car Video Generator") as demo:
    gr.Markdown("# 🚗 AI Car Video Generator")

    # ---------------- Voice ----------------
    gr.Markdown("## 🎙 Voice Selection")

    voice_dropdown = gr.Dropdown(
        label="Choose Existing Voice",
        choices=list_voices()
    )

    with gr.Accordion("➕ Create New Voice", open=False):
        new_voice_name = gr.Textbox(label="Voice Name")
        new_voice_sample = gr.File(type="binary", label="Voice Sample")
        clone_btn = gr.Button("Clone Voice")
        clone_status = gr.Textbox(show_label=False)

        clone_btn.click(
            clone_voice,
            inputs=[new_voice_name, new_voice_sample],
            outputs=[voice_dropdown, clone_status]
        )

    # ---------------- Sections ----------------
    def section(title):
        gr.Markdown(f"### {title}")
        v = gr.File(type="binary", label="Video")
        t = gr.Textbox(label="TTS Script", lines=4)
        h = gr.Textbox(label="Highlights (1 per line)", lines=4)
        return v, t, h

    front_v, front_t, front_h = section("Front View")
    rear_v, rear_t, rear_h = section("Rear View")
    driver_v, driver_t, driver_h = section("Driver Side")
    passenger_v, passenger_t, passenger_h = section("Passenger Side")
    interior_v, interior_t, interior_h = section("Interior")

    # ---------------- Generate ----------------
    generate_btn = gr.Button("🔥 Generate Final Video", variant="primary")
    output_video = gr.Video(label="Final Output")

    generate_btn.click(
        generate_all,
        inputs=[
            voice_dropdown,

            front_v, front_t, front_h,
            rear_v, rear_t, rear_h,
            driver_v, driver_t, driver_h,
            passenger_v, passenger_t, passenger_h,
            interior_v, interior_t, interior_h,
        ],
        outputs=output_video
    )

demo.launch()

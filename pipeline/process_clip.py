import os
from moviepy.editor import VideoFileClip, AudioFileClip

from engine.elevenlabs_engine import ElevenLabsEngine
from engine.highlight_engine import HighlightEngine
from engine.text_renderer import TextRenderer
from engine.video_builder import VideoBuilder
from engine.plate_processor import PlateBlurProcessor
from engine.zone_allocator import ZoneAllocator
from engine.style_engine import StyleEngine


def process_single_clip(
    video_path: str,
    tts_script: str,
    highlights: list[str],
    output_path: str,
    config: dict,
    voice_id: str,
) -> str:

    temp_audio = None
    blurred_video = None
    voice = video = final = None

    try:
        # --------------------------------------------------
        # 1️⃣ License plate blur (GPU – YOLO)
        # --------------------------------------------------
        if config.get("BLUR_PLATE", False):
            processor = PlateBlurProcessor(
                model_path=config["PLATE_MODEL_PATH"],
                conf=config.get("PLATE_CONF", 0.5),
                buffer_size=config.get("PLATE_SMOOTH", 5),
            )

            blurred_video = output_path.replace(".mp4", "_blur.mp4")
            video_path = processor.process(video_path, blurred_video)

        # --------------------------------------------------
        # 2️⃣ ElevenLabs TTS (API)
        # --------------------------------------------------
        tts_engine = ElevenLabsEngine(voice_id)
        temp_audio = tts_engine.synthesize(tts_script)

        # --------------------------------------------------
        # 3️⃣ Faster-Whisper (GPU)
        # --------------------------------------------------
        highlight_engine = HighlightEngine(temp_audio)
        timed_highlights = highlight_engine.run(highlights)

        if not timed_highlights:
            raise RuntimeError("No highlights matched audio")

        # --------------------------------------------------
        # 4️⃣ Load video + audio (CPU – unavoidable)
        # --------------------------------------------------
        voice = AudioFileClip(temp_audio)
        video = VideoFileClip(video_path).loop(duration=voice.duration)

        # --------------------------------------------------
        # 5️⃣ Styling + layout (CPU)
        # --------------------------------------------------
        style_engine = StyleEngine(fonts_dir="fonts")
        style_config = style_engine.generate_style(video)
        render_config = {**config, **style_config}

        renderer = TextRenderer(render_config)
        builder = VideoBuilder(video, render_config)
        zones = ZoneAllocator()

        for h in timed_highlights:
            zone = zones.choose(
                start=h["start"],
                end=h["end"],
                prefer_upper=any(c.isdigit() for c in h["text"])
            )

            align = "center"
            if zone.endswith("left"):
                align = "left"
            elif zone.endswith("right"):
                align = "right"

            img = renderer.render_highlight(
                text=h["text"],
                align=align,
                video_width=video.w
            )

            builder.add_highlight(
                img=img,
                start=h["start"],
                end=h["end"],
                position=zone
            )

        # --------------------------------------------------
        # 6️⃣ EXPORT (GPU ENCODE – NVENC)
        # --------------------------------------------------
        final = builder.render(return_clip=True).set_audio(voice)

        final.write_videofile(
            output_path,
            codec="libx264",
            audio_codec="aac",
            fps=video.fps,
            threads=4,
            logger=None,
            ffmpeg_params=[
                "-preset", "ultrafast",
                "-crf", "23",
                "-pix_fmt", "yuv420p",
                "-movflags", "+faststart"
            ]
        )


        return output_path

    finally:
        for obj in (voice, video, final):
            try:
                if obj:
                    obj.close()
            except Exception:
                pass

        for f in (temp_audio, blurred_video):
            try:
                if f and os.path.exists(f):
                    os.remove(f)
            except Exception:
                pass

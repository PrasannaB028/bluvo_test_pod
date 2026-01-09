import os
import re
import subprocess
from moviepy.editor import (
    VideoFileClip,
    ImageClip,
    CompositeVideoClip,
    concatenate_videoclips
)

# --------------------------------------------------
# Helpers
# --------------------------------------------------

def numeric_sort(filename):
    m = re.search(r"(\d+)", filename)
    return int(m.group(1)) if m else 9999


def compress_video(input_path: str, output_path: str, crf: int = 24):
    """
    Compress final video WITHOUT changing visuals.
    Typical:
      80–120MB → 20–35MB
    """
    cmd = [
        "ffmpeg", "-y",
        "-i", input_path,
        "-c:v", "libx264",
        "-preset", "medium",        # 🔥 balanced speed/size
        "-crf", str(crf),
        "-pix_fmt", "yuv420p",
        "-profile:v", "high",
        "-level", "4.2",
        "-movflags", "+faststart",
        "-c:a", "aac",
        "-b:a", "128k",
        output_path
    ]
    subprocess.run(cmd, check=True)


# --------------------------------------------------
# Main combiner
# --------------------------------------------------

def combine_clips(
    clips_dir: str,
    output_path: str,
    logo_path: str,
    target_w=1920,
    target_h=1080,
    top_logo_scale=0.12,
    watermark_scale=0.28,
    watermark_opacity=0.5,
    margin=40,
    compress=True,
    compression_crf=24
):
    files = sorted(
        [f for f in os.listdir(clips_dir) if f.endswith(".mp4")],
        key=numeric_sort
    )

    if not files:
        raise RuntimeError("No clips found")

    processed = []
    final = None
    target_ratio = target_w / target_h

    try:
        # ------------------------------------------
        # Resize + letterbox
        # ------------------------------------------
        for f in files:
            clip = VideoFileClip(os.path.join(clips_dir, f))

            scale = (
                target_w / clip.w
                if (clip.w / clip.h) > target_ratio
                else target_h / clip.h
            )

            clip = clip.resize(scale).on_color(
                size=(target_w, target_h),
                color=(0, 0, 0),
                pos=("center", "center")
            )

            processed.append(clip)

        base = concatenate_videoclips(processed, method="compose")

        # ------------------------------------------
        # Logos
        # ------------------------------------------
        logo = ImageClip(logo_path).set_duration(base.duration)

        top_logo = (
            logo.resize(width=int(target_w * top_logo_scale))
            .set_position((target_w - int(target_w * top_logo_scale) - margin, margin))
        )

        watermark = (
            logo.resize(width=int(target_w * watermark_scale))
            .set_opacity(watermark_opacity)
            .set_position("center")
        )

        final = CompositeVideoClip([base, top_logo, watermark])

        # ------------------------------------------
        # Write master (high quality)
        # ------------------------------------------
        temp_master = output_path.replace(".mp4", "_master.mp4")

        final.write_videofile(
            temp_master,
            codec="libx264",
            audio_codec="aac",
            fps=base.fps,
            preset="fast",
            ffmpeg_params=[
                "-pix_fmt", "yuv420p",
                "-profile:v", "high",
                "-level", "4.2",
                "-crf", "19",              # visually lossless
                "-movflags", "+faststart"
            ],
            threads=4,
            logger=None
        )

        # ------------------------------------------
        # Compress
        # ------------------------------------------
        if compress:
            compress_video(
                temp_master,
                output_path,
                crf=compression_crf
            )
            os.remove(temp_master)
        else:
            os.rename(temp_master, output_path)

        return output_path

    finally:
        # ------------------------------------------
        # Cleanup
        # ------------------------------------------
        for c in processed:
            try:
                c.close()
            except:
                pass

        try:
            if final:
                final.close()
        except:
            pass


# def run_combine_from_folder():
#     """
#     Run video merge using clips inside the clips folder.
#     Files must be named like: 1.mp4, 2.mp4, 3.mp4 ...
#     """

#     clips_dir = r"D:\test\Video_Voice_automation\clips_output"              # folder containing clips
#     output_path = "1_final_output.mp4" # final merged video
#     logo_path = r"D:\test\Video_Voice_automation\bluvo-logo.png"            # your logo image

#     if not os.path.exists(clips_dir):
#         raise RuntimeError(f"Clips folder not found: {clips_dir}")

#     if not os.path.exists(logo_path):
#         raise RuntimeError(f"Logo file not found: {logo_path}")

#     print("▶ Merging clips from:", clips_dir)

#     combine_clips(
#         clips_dir=clips_dir,
#         output_path=output_path,
#         logo_path=logo_path,
#         compress=True,
#         compression_crf=24
#     )

#     print("✅ Final video created:", output_path)


# if __name__ == "__main__":
#     run_combine_from_folder()

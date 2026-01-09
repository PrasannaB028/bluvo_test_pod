import os
import uuid
import shutil
import base64
import requests
import runpod

from pipeline.process_clip import process_single_clip
from pipeline.combine_clips import combine_clips

# --------------------------------------------------
# CONSTANTS
# --------------------------------------------------
TMP_ROOT = "/tmp"
LOGO_PATH = "bluvo-logo.png"

CONFIG = {
    "BLUR_PLATE": True,
    "PLATE_MODEL_PATH": "models/lp_key_point.pt",          
}

# --------------------------------------------------
# HELPERS fine i will do it myself
# --------------------------------------------------
def download_file(url: str, dst: str):
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    with requests.get(url, stream=True, timeout=180) as r:
        r.raise_for_status()
        with open(dst, "wb") as f:
            for chunk in r.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    f.write(chunk)


def to_base64(path: str) -> str:
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


# --------------------------------------------------
# HANDLER
# --------------------------------------------------
def handler(event):
    """
    Expected input JSON:

    {
      "voice_id": "xxxxxxxx",
      "clips": [
        {
          "video_url": "https://...",
          "tts": "Text to speak",
          "highlights": ["Line 1", "Line 2"]
        }
      ]
    }
    """

    inp = event.get("input", {})
    voice_id = inp.get("voice_id")
    clips = inp.get("clips", [])

    if not voice_id:
        raise ValueError("voice_id is required")

    if not clips:
        raise ValueError("At least one clip is required")

    job_id = uuid.uuid4().hex[:8]

    upload_dir = f"{TMP_ROOT}/uploads_{job_id}"
    clips_dir = f"{TMP_ROOT}/clips_{job_id}"
    output_dir = f"{TMP_ROOT}/output_{job_id}"

    os.makedirs(upload_dir, exist_ok=True)
    os.makedirs(clips_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)

    final_video = f"{output_dir}/final.mp4"

    try:
        outputs = []

        # --------------------------------------------------
        # PROCESS CLIPS
        # --------------------------------------------------
        for idx, clip in enumerate(clips, start=1):
            raw_video = f"{upload_dir}/{idx}.mp4"
            out_video = f"{clips_dir}/{idx}.mp4"

            download_file(clip["video_url"], raw_video)

            process_single_clip(
                video_path=raw_video,
                tts_script=clip["tts"],
                highlights=clip["highlights"],
                output_path=out_video,
                config=CONFIG,
                voice_id=voice_id
            )

            outputs.append(out_video)

        # --------------------------------------------------
        # COMBINE (ONLY IF MULTIPLE)
        # --------------------------------------------------
        if len(outputs) > 1:
            combine_clips(
                clips_dir=clips_dir,
                output_path=final_video,
                logo_path=LOGO_PATH,
                compress=True,
                compression_crf=24
            )
            result_path = final_video
        else:
            result_path = outputs[0]

        # --------------------------------------------------
        # BASE64 RESPONSE
        # --------------------------------------------------
        return {
            "status": "success",
            "clips_processed": len(outputs),
            "video_base64": to_base64(result_path)
        }

    finally:
        # --------------------------------------------------
        # CLEANUP (SERVERLESS SAFE)
        # --------------------------------------------------
        shutil.rmtree(upload_dir, ignore_errors=True)
        shutil.rmtree(clips_dir, ignore_errors=True)
        shutil.rmtree(output_dir, ignore_errors=True)


# --------------------------------------------------
# START SERVERLESS
# --------------------------------------------------
runpod.serverless.start({
    "handler": handler
})

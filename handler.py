import runpod
import os
import uuid
import shutil
import requests
import base64

from pipeline.process_clip import process_single_clip
from pipeline.combine_clips import combine_clips

# --------------------------------------------------
# CONFIG
# --------------------------------------------------
TMP = "/tmp"
LOGO_PATH = "bluvo-logo.png"

CONFIG = {
    "BLUR_PLATE": True,
    "PLATE_MODEL_PATH": "models/lp_key_point.pt",
}

# --------------------------------------------------
# Helpers
# --------------------------------------------------
def download_file(url: str, out_path: str):
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    r = requests.get(url, stream=True, timeout=120)
    r.raise_for_status()
    with open(out_path, "wb") as f:
        for chunk in r.iter_content(1024 * 1024):
            if chunk:
                f.write(chunk)


def file_to_base64(path: str) -> str:
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


# --------------------------------------------------
# Handler
# --------------------------------------------------
def handler(event):
    inp = event["input"]

    voice_id = inp["voice_id"]
    clips = inp["clips"]

    if not clips:
        raise ValueError("At least one clip is required")

    job_id = str(uuid.uuid4())[:8]

    upload_dir = f"{TMP}/uploads_{job_id}"
    clips_dir = f"{TMP}/clips_{job_id}"
    output_dir = f"{TMP}/output_{job_id}"
    final_video = f"{output_dir}/final.mp4"

    os.makedirs(upload_dir, exist_ok=True)
    os.makedirs(clips_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)

    outputs = []

    try:
        # ----------------------------------
        # Process each clip
        # ----------------------------------
        for idx, clip in enumerate(clips, start=1):
            print(f"▶ Processing clip {idx}/{len(clips)}")

            raw = f"{upload_dir}/{idx}.mp4"
            out = f"{clips_dir}/{idx}.mp4"

            download_file(clip["video_url"], raw)

            process_single_clip(
                video_path=raw,
                tts_script=clip["tts"],
                highlights=clip["highlights"],
                output_path=out,
                config=CONFIG,
                voice_id=voice_id
            )

            outputs.append(out)
            print(f"✔ Clip {idx} done")

        # ----------------------------------
        # Combine if 5 clips
        # ----------------------------------
        if len(outputs) == 5:
            print("▶ Combining 5 clips")
            combine_clips(
                clips_dir=clips_dir,
                output_path=final_video,
                logo_path=LOGO_PATH
            )
            result_path = final_video
        else:
            # Single clip result
            result_path = outputs[0]

        # ----------------------------------
        # Encode Base64 (FINAL OUTPUT)
        # ----------------------------------
        video_b64 = file_to_base64(result_path)

        return {
            "status": "success",
            "clips_processed": len(outputs),
            "video_base64": video_b64
        }

    finally:
        # ----------------------------------
        # Cleanup temp inputs (keep output during response)
        # ----------------------------------
        shutil.rmtree(upload_dir, ignore_errors=True)
        shutil.rmtree(clips_dir, ignore_errors=True)
        # NOTE: output_dir intentionally NOT deleted until response is sent


runpod.serverless.start({"handler": handler})

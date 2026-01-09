import numpy as np
from moviepy.editor import ImageClip, CompositeVideoClip


class VideoBuilder:
    def __init__(self, video_clip, cfg):
        self.video = video_clip
        self.cfg = cfg
        self.clips = [video_clip]

    # =====================================================
    # POSITION RESOLVER (9 POSITIONS)
    # =====================================================

    def resolve_position(self, img_w, img_h, position):
        margin = 60

        positions = {
            "top-left": (margin, margin),
            "top-center": ((self.video.w - img_w) // 2, margin),
            "top-right": (self.video.w - img_w - margin, margin),

            "center-left": (margin, (self.video.h - img_h) // 2),
            "center": ((self.video.w - img_w) // 2, (self.video.h - img_h) // 2),
            "center-right": (self.video.w - img_w - margin, (self.video.h - img_h) // 2),

            "bottom-left": (margin, self.video.h - img_h - margin),
            "bottom-center": ((self.video.w - img_w) // 2, self.video.h - img_h - margin),
            "bottom-right": (self.video.w - img_w - margin, self.video.h - img_h - margin),
        }

        return positions[position]

    # =====================================================
    # HIGHLIGHT OVERLAY
    # =====================================================

    def add_highlight(self, img, start, end, position):
        iw, ih = img.size
        duration = end - start

        x, y = self.resolve_position(iw, ih, position)

        clip = (
            ImageClip(np.array(img))
            .set_start(start)
            .set_duration(duration)
            .set_position((x, y))
            .fadein(self.cfg["FADE"])
            .fadeout(self.cfg["FADE"])
        )

        self.clips.append(clip)

    # =====================================================
    # FINAL RENDER
    # =====================================================

    def render(self, output_path="output.mp4", return_clip=False):
        final = CompositeVideoClip(self.clips, size=self.video.size)

        if return_clip:
            return final

        final.write_videofile(
            output_path,
            codec="libx264",
            audio_codec="aac",
            fps=self.video.fps
        )

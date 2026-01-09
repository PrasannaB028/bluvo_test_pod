# engine/plate_processor.py

import cv2
import numpy as np
from ultralytics import YOLO


class PlateBlurProcessor:
    def __init__(
        self,
        model_path: str,
        conf: float = 0.5,
        buffer_size: int = 5,
        blur_kernel=(49, 49),
    ):
        self.model = YOLO(model_path)
        self.conf = conf
        self.buffer_size = buffer_size
        self.blur_kernel = blur_kernel
        self.bbox_buffer = []

    def _smooth_bbox(self, bbox):
        self.bbox_buffer.append(bbox)
        if len(self.bbox_buffer) > self.buffer_size:
            self.bbox_buffer.pop(0)
        return np.mean(self.bbox_buffer, axis=0).astype(int)

    def process(self, input_video: str, output_video: str) -> str:
        cap = cv2.VideoCapture(input_video)
        if not cap.isOpened():
            raise RuntimeError("❌ Cannot open input video")

        fps = cap.get(cv2.CAP_PROP_FPS)
        W = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        H = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        writer = cv2.VideoWriter(
            output_video,
            cv2.VideoWriter_fourcc(*"mp4v"),
            fps,
            (W, H)
        )

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            results = self.model(frame, conf=self.conf, verbose=False)

            if results and len(results[0].boxes) > 0:
                x1, y1, x2, y2 = map(
                    int,
                    results[0].boxes.xyxy[0].cpu().numpy()
                )

                x1, y1, x2, y2 = self._smooth_bbox([x1, y1, x2, y2])

                h, w = frame.shape[:2]
                x1, y1 = max(0, x1), max(0, y1)
                x2, y2 = min(w, x2), min(h, y2)

                if x2 > x1 and y2 > y1:
                    roi = frame[y1:y2, x1:x2]
                    if roi.size > 0:
                        frame[y1:y2, x1:x2] = cv2.GaussianBlur(
                            roi, self.blur_kernel, 0
                        )

            writer.write(frame)

        cap.release()
        writer.release()

        return output_video

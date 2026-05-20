from __future__ import annotations

import cv2
import mediapipe as mp


class PoseExtractor:
    """OpenCV로 영상 → 프레임 + MediaPipe Pose → 33점 좌표."""

    def __init__(self, sample_fps: int = 10, max_frames: int = 300):
        self.sample_fps = sample_fps
        self.max_frames = max_frames
        self._pose = mp.solutions.pose.Pose(
            static_image_mode=False,
            model_complexity=1,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
        )

    def _sample_frames(self, video_path: str) -> list:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return []
        src_fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        step = max(1, int(src_fps / max(self.sample_fps, 1)))
        frames: list = []
        idx = 0
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            if idx % step == 0:
                frames.append(frame)
                if len(frames) >= self.max_frames:
                    break
            idx += 1
        cap.release()
        return frames

    def extract_from_frames(self, frames: list) -> list[list[dict]]:
        """각 프레임의 33점 좌표 리스트. 사람 없는 프레임은 스킵."""
        out: list[list[dict]] = []
        for f in frames[: self.max_frames]:
            rgb = cv2.cvtColor(f, cv2.COLOR_BGR2RGB)
            result = self._pose.process(rgb)
            if result.pose_landmarks is None:
                continue
            points = []
            for lm in result.pose_landmarks.landmark:
                points.append(
                    {"x": lm.x, "y": lm.y, "z": lm.z, "visibility": lm.visibility}
                )
            out.append(points)
        return out

    def extract_from_video(self, video_path: str) -> list[list[dict]]:
        frames = self._sample_frames(video_path)
        return self.extract_from_frames(frames)

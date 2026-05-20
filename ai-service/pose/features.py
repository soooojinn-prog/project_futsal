from __future__ import annotations

import math

import numpy as np

# MediaPipe Pose landmark indices
LEFT_SHOULDER = 11
RIGHT_SHOULDER = 12
LEFT_ELBOW = 13
RIGHT_ELBOW = 14
LEFT_WRIST = 15
RIGHT_WRIST = 16
LEFT_HIP = 23
RIGHT_HIP = 24
LEFT_KNEE = 25
RIGHT_KNEE = 26
LEFT_ANKLE = 27
RIGHT_ANKLE = 28
LEFT_FOOT = 31
RIGHT_FOOT = 32
NOSE = 0

# 각도 12개 (a, b, c) — b가 꼭짓점
ANGLE_TRIPLES = [
    (LEFT_HIP, LEFT_KNEE, LEFT_ANKLE),
    (RIGHT_HIP, RIGHT_KNEE, RIGHT_ANKLE),
    (LEFT_KNEE, LEFT_ANKLE, LEFT_FOOT),
    (RIGHT_KNEE, RIGHT_ANKLE, RIGHT_FOOT),
    (LEFT_SHOULDER, LEFT_HIP, LEFT_KNEE),
    (RIGHT_SHOULDER, RIGHT_HIP, RIGHT_KNEE),
    (NOSE, LEFT_SHOULDER, LEFT_ELBOW),
    (NOSE, RIGHT_SHOULDER, RIGHT_ELBOW),
    (LEFT_SHOULDER, LEFT_ELBOW, LEFT_WRIST),
    (RIGHT_SHOULDER, RIGHT_ELBOW, RIGHT_WRIST),
    (LEFT_ELBOW, LEFT_WRIST, LEFT_HIP),
    (RIGHT_ELBOW, RIGHT_WRIST, RIGHT_HIP),
]

RELATIVE_POINTS = [LEFT_FOOT, RIGHT_FOOT, LEFT_WRIST, RIGHT_WRIST, NOSE]


class FeatureBuilder:
    """33점 좌표 시퀀스 → 고정 길이 feature 벡터."""

    def feature_dim(self) -> int:
        return len(ANGLE_TRIPLES) * 2 + len(RELATIVE_POINTS) * 2 * 2

    @staticmethod
    def _joint_angle(landmarks: list[dict], a: int, b: int, c: int) -> float:
        pa = np.array([landmarks[a]["x"], landmarks[a]["y"]])
        pb = np.array([landmarks[b]["x"], landmarks[b]["y"]])
        pc = np.array([landmarks[c]["x"], landmarks[c]["y"]])
        v1 = pa - pb
        v2 = pc - pb
        n1 = float(np.linalg.norm(v1))
        n2 = float(np.linalg.norm(v2))
        if n1 < 1e-9 or n2 < 1e-9:
            return 180.0
        cos = float(np.dot(v1, v2) / (n1 * n2))
        cos = max(-1.0, min(1.0, cos))
        return math.degrees(math.acos(cos))

    @staticmethod
    def _normalized_position(landmarks: list[dict], idx: int) -> tuple[float, float]:
        hx = (landmarks[LEFT_HIP]["x"] + landmarks[RIGHT_HIP]["x"]) / 2.0
        hy = (landmarks[LEFT_HIP]["y"] + landmarks[RIGHT_HIP]["y"]) / 2.0
        return landmarks[idx]["x"] - hx, landmarks[idx]["y"] - hy

    def build_single(self, frame_landmarks: list[list[dict]]) -> list[float]:
        if not frame_landmarks:
            raise ValueError("frame_landmarks is empty")
        angles_per_frame: list[list[float]] = []
        positions_per_frame: list[list[float]] = []
        for lm in frame_landmarks:
            angles_per_frame.append(
                [self._joint_angle(lm, a, b, c) for (a, b, c) in ANGLE_TRIPLES]
            )
            positions_per_frame.append(
                [v for idx in RELATIVE_POINTS for v in self._normalized_position(lm, idx)]
            )
        angles = np.array(angles_per_frame)
        positions = np.array(positions_per_frame)
        vec: list[float] = []
        vec.extend(angles.mean(axis=0).tolist())
        vec.extend(angles.std(axis=0).tolist())
        vec.extend(positions.mean(axis=0).tolist())
        vec.extend(positions.std(axis=0).tolist())
        return [float(v) for v in vec]

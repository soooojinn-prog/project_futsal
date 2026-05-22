"""MediaPipe 33점 → AI Hub 학습 feature와 호환되는 14차원 벡터 생성.

학습 데이터(AI Hub `extract_features.py`)와 동일한 컬럼 순서·정의를 유지해야
`classifier.predict`에 그대로 넣을 수 있다. 영상은 여러 frame을 가지므로 각
frame에서 14 feature를 계산한 뒤 평균값으로 단일 vector 반환.

14 feature 순서:
    좌/우 절대각 6개: left_knee_angle, right_knee_angle, left_hip_angle,
                       right_hip_angle, left_ankle_angle, right_ankle_angle
    체격 2개: torso_lean, hip_width
    좌/우 derived 6개: knee_diff, knee_max, knee_min,
                       ankle_diff, ankle_max, hip_diff
"""
from __future__ import annotations

import math

import numpy as np

# MediaPipe Pose landmark indices (BlazePose 33점)
NOSE = 0
LEFT_SHOULDER = 11
RIGHT_SHOULDER = 12
LEFT_HIP = 23
RIGHT_HIP = 24
LEFT_KNEE = 25
RIGHT_KNEE = 26
LEFT_ANKLE = 27
RIGHT_ANKLE = 28
LEFT_FOOT = 31  # left_foot_index (엄지발가락)
RIGHT_FOOT = 32  # right_foot_index


def _angle(landmarks: list[dict], a: int, b: int, c: int) -> float:
    """세 점 (b가 꼭짓점) 사이의 각도(°). 좌표 결손이면 180°."""
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


def _dist(landmarks: list[dict], a: int, b: int) -> float:
    pa = np.array([landmarks[a]["x"], landmarks[a]["y"]])
    pb = np.array([landmarks[b]["x"], landmarks[b]["y"]])
    return float(np.linalg.norm(pa - pb))


def _torso_lean(landmarks: list[dict]) -> float:
    sh_l = landmarks[LEFT_SHOULDER]
    sh_r = landmarks[RIGHT_SHOULDER]
    hp_l = landmarks[LEFT_HIP]
    hp_r = landmarks[RIGHT_HIP]
    sh_mid_x = (sh_l["x"] + sh_r["x"]) / 2
    sh_mid_y = (sh_l["y"] + sh_r["y"]) / 2
    hp_mid_x = (hp_l["x"] + hp_r["x"]) / 2
    hp_mid_y = (hp_l["y"] + hp_r["y"]) / 2
    dx = sh_mid_x - hp_mid_x
    dy = sh_mid_y - hp_mid_y
    if abs(dy) < 1e-9:
        return 0.0
    return math.degrees(math.atan2(dx, -dy))


def _frame_feature_vector(lm: list[dict]) -> list[float]:
    left_knee = _angle(lm, LEFT_HIP, LEFT_KNEE, LEFT_ANKLE)
    right_knee = _angle(lm, RIGHT_HIP, RIGHT_KNEE, RIGHT_ANKLE)
    left_hip = _angle(lm, LEFT_SHOULDER, LEFT_HIP, LEFT_KNEE)
    right_hip = _angle(lm, RIGHT_SHOULDER, RIGHT_HIP, RIGHT_KNEE)
    left_ankle = _angle(lm, LEFT_KNEE, LEFT_ANKLE, LEFT_FOOT)
    right_ankle = _angle(lm, RIGHT_KNEE, RIGHT_ANKLE, RIGHT_FOOT)
    torso = _torso_lean(lm)
    hip_w = _dist(lm, LEFT_HIP, RIGHT_HIP)
    return [
        left_knee, right_knee, left_hip, right_hip, left_ankle, right_ankle,
        torso, hip_w,
        abs(left_knee - right_knee),  # knee_diff
        max(left_knee, right_knee),  # knee_max
        min(left_knee, right_knee),  # knee_min
        abs(left_ankle - right_ankle),  # ankle_diff
        max(left_ankle, right_ankle),  # ankle_max
        abs(left_hip - right_hip),  # hip_diff
    ]


class FeatureBuilder:
    """MediaPipe 33점 frame 시퀀스 → 8차원 평균 feature 벡터.

    학습은 frame 단일 sample이지만, 추론은 frame 다수. frame별 8차원을 평균내서
    단일 vector 반환 — 학습 분포와 distribution 일치 (frame 평균 ≈ 분포 중심).
    """

    def feature_dim(self) -> int:
        return 14

    def build_single(self, frame_landmarks: list[list[dict]]) -> list[float]:
        if not frame_landmarks:
            raise ValueError("frame_landmarks is empty")
        per_frame = np.array([_frame_feature_vector(lm) for lm in frame_landmarks])
        mean_vec = per_frame.mean(axis=0)
        return [float(v) for v in mean_vec]

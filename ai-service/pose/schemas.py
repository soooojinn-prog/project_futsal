from typing import Literal

from pydantic import BaseModel, Field

PoseClass = Literal[
    "GOOD_KICK", "BAD_KICK_KNEE_LOCKED", "GOOD_DRIBBLE", "BAD_DRIBBLE_OVERREACH"
]

CLASS_NAMES_KO: dict[str, str] = {
    "GOOD_KICK": "좋은 킥",
    "BAD_KICK_KNEE_LOCKED": "킥 — 무릎 잠김",
    "GOOD_DRIBBLE": "좋은 드리블",
    "BAD_DRIBBLE_OVERREACH": "드리블 — 과도 리치",
}


class AngleStats(BaseModel):
    mean: float
    min: float
    max: float


class KeyAngles(BaseModel):
    left_knee: AngleStats
    right_knee: AngleStats
    left_ankle: AngleStats
    right_ankle: AngleStats


class TimingMs(BaseModel):
    frame_extract: int
    mediapipe: int
    classify: int
    feedback: int
    total: int


class PoseAnalysisResponse(BaseModel):
    pose_class: PoseClass
    class_name: str
    confidence: float = Field(ge=0.0, le=1.0)
    class_probabilities: dict[str, float]
    key_angles: KeyAngles
    feedback: str
    timing_ms: TimingMs

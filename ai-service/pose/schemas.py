from typing import Literal

from pydantic import BaseModel, Field

PoseClass = Literal["INSIDE_KICK", "INSTEP_KICK", "INFRONT_KICK"]

CLASS_NAMES_KO: dict[str, str] = {
    "INSIDE_KICK": "인사이드킥",
    "INSTEP_KICK": "인스텝킥",
    "INFRONT_KICK": "인프런트킥",
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

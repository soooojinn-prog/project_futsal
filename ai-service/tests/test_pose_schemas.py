from pose.schemas import (
    AngleStats,
    KeyAngles,
    PoseAnalysisResponse,
    TimingMs,
)


def test_angle_stats():
    a = AngleStats(mean=145.0, min=130.0, max=160.0)
    assert a.mean == 145.0


def test_key_angles():
    k = KeyAngles(
        left_knee=AngleStats(mean=160, min=150, max=170),
        right_knee=AngleStats(mean=145, min=130, max=160),
        left_ankle=AngleStats(mean=90, min=82, max=100),
        right_ankle=AngleStats(mean=92, min=85, max=99),
    )
    assert k.left_knee.mean == 160


def test_timing_ms_total_field():
    t = TimingMs(frame_extract=420, mediapipe=1850, classify=12, feedback=1200, total=3500)
    assert t.total == 3500


def test_pose_class_literal():
    for c in ["GOOD_KICK", "BAD_KICK_KNEE_LOCKED", "GOOD_DRIBBLE", "BAD_DRIBBLE_OVERREACH"]:
        r = PoseAnalysisResponse(
            pose_class=c,
            class_name=c,
            confidence=0.9,
            class_probabilities={c: 0.9},
            key_angles=KeyAngles(
                left_knee=AngleStats(mean=160, min=150, max=170),
                right_knee=AngleStats(mean=145, min=130, max=160),
                left_ankle=AngleStats(mean=90, min=82, max=100),
                right_ankle=AngleStats(mean=92, min=85, max=99),
            ),
            feedback="ok",
            timing_ms=TimingMs(frame_extract=1, mediapipe=1, classify=1, feedback=1, total=4),
        )
        assert r.pose_class == c


def test_pose_class_invalid_rejected():
    import pytest
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        PoseAnalysisResponse(
            pose_class="WRONG",
            class_name="x",
            confidence=0.5,
            class_probabilities={},
            key_angles=KeyAngles(
                left_knee=AngleStats(mean=160, min=150, max=170),
                right_knee=AngleStats(mean=145, min=130, max=160),
                left_ankle=AngleStats(mean=90, min=82, max=100),
                right_ankle=AngleStats(mean=92, min=85, max=99),
            ),
            feedback="x",
            timing_ms=TimingMs(frame_extract=1, mediapipe=1, classify=1, feedback=1, total=4),
        )

from unittest.mock import MagicMock

from pose.feedback import FeedbackGenerator
from pose.schemas import AngleStats, KeyAngles


def _angles():
    return KeyAngles(
        left_knee=AngleStats(mean=168, min=158, max=175),
        right_knee=AngleStats(mean=145, min=130, max=160),
        left_ankle=AngleStats(mean=90, min=82, max=100),
        right_ankle=AngleStats(mean=92, min=85, max=99),
    )


def test_feedback_includes_class_and_angles_in_prompt():
    claude = MagicMock()
    claude.chat.return_value = "디딤발 무릎이 거의 펴진 상태예요. 조금 더 굽혀보세요."

    gen = FeedbackGenerator(claude_client=claude)
    out = gen.generate(
        pose_class="INSTEP_KICK",
        confidence=0.87,
        key_angles=_angles(),
    )

    assert "디딤발" in out
    _, kwargs = claude.chat.call_args
    user = kwargs["user"]
    assert "INSTEP_KICK" in user
    assert "168" in user or "168.0" in user
    assert "0.87" in user or "87" in user


def test_feedback_falls_back_on_claude_error():
    claude = MagicMock()
    claude.chat.side_effect = RuntimeError("api down")
    gen = FeedbackGenerator(claude_client=claude)
    out = gen.generate(pose_class="INSIDE_KICK", confidence=0.95, key_angles=_angles())
    assert "분류 결과" in out

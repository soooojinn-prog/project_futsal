from __future__ import annotations

from rag.claude_client import ClaudeClient

from .schemas import KeyAngles

SYSTEM_PROMPT = (
    "당신은 풋살 코치입니다. 사용자의 자세 분류 결과와 핵심 관절 각도를 보고, "
    "2~4문장의 친근한 한국어 피드백을 작성하세요. "
    "구체적인 각도 수치를 한 번만 인용하고, 실천 가능한 개선 팁을 1가지 제시하세요. "
    "이모지·과장된 표현은 피하세요."
)


class FeedbackGenerator:
    def __init__(self, claude_client: ClaudeClient):
        self._claude = claude_client

    def generate(
        self, pose_class: str, confidence: float, key_angles: KeyAngles
    ) -> str:
        user = (
            f"분류 결과: {pose_class} (신뢰도 {confidence:.2f})\n\n"
            f"핵심 관절 각도(평균):\n"
            f"- 좌 무릎: {key_angles.left_knee.mean:.1f}도\n"
            f"- 우 무릎: {key_angles.right_knee.mean:.1f}도\n"
            f"- 좌 발목: {key_angles.left_ankle.mean:.1f}도\n"
            f"- 우 발목: {key_angles.right_ankle.mean:.1f}도\n\n"
            "이 결과에 대한 친근한 한국어 피드백을 작성해주세요."
        )
        try:
            return self._claude.chat(
                system=SYSTEM_PROMPT, user=user, max_tokens=300
            ).strip()
        except Exception:
            return f"분류 결과는 {pose_class}입니다. 자세 분석을 다시 시도해 주세요."

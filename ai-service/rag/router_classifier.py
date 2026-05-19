from __future__ import annotations

from .claude_client import ClaudeClient
from .schemas import ClassifyResponse

CLASSIFY_TOOL = {
    "name": "classify_intent",
    "description": (
        "사용자 메시지의 의도를 분류한다. KNOWLEDGE는 풋살 규칙·전술·훈련 등 "
        "사실 기반 지식 질문, ADVICE는 사용자의 개인 상황·감정·고민 또는 추천성 질문."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "intent": {
                "type": "string",
                "enum": ["KNOWLEDGE", "ADVICE"],
                "description": "분류된 의도 (KNOWLEDGE 또는 ADVICE)",
            },
            "confidence": {
                "type": "number",
                "description": "0.0~1.0 범위 신뢰도",
            },
        },
        "required": ["intent", "confidence"],
    },
}


SYSTEM_PROMPT = (
    "당신은 풋살 챗봇의 의도 분류기입니다. 사용자 메시지가 (a) 풋살 규칙·전술·훈련 등 "
    "사실 기반 지식 질문(KNOWLEDGE)인지, (b) 사용자의 팀 상황·고민·개인 추천(ADVICE)인지 "
    "이분 분류한 뒤 classify_intent 도구로 결과를 반환하세요."
)


class RouterClassifier:
    def __init__(self, claude_client: ClaudeClient):
        self._claude = claude_client

    def classify(self, user_message: str) -> ClassifyResponse:
        result = self._claude.chat_with_tool(
            system=SYSTEM_PROMPT,
            user=user_message,
            tool=CLASSIFY_TOOL,
        )
        return ClassifyResponse(**result)

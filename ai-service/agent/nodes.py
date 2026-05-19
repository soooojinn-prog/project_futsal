from __future__ import annotations

from rag.claude_client import ClaudeClient

from .state import AgentState

INTENT_TOOL = {
    "name": "extract_intent",
    "description": (
        "사용자의 풋살 코디네이터 요청에서 의도와 슬롯을 추출한다. "
        "intent가 SINGLE이면 단일 매치, TOURNAMENT면 토너먼트 기획. "
        "팀 수가 명시 안 되면 team_count=1."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "intent": {"type": "string", "enum": ["SINGLE", "TOURNAMENT"]},
            "region": {"type": "string"},
            "date_from": {"type": "string"},
            "date_to": {"type": "string"},
            "team_count": {"type": "integer"},
        },
        "required": ["intent"],
    },
}

PARSE_SYSTEM = (
    "당신은 풋살 매치 코디네이터의 의도 분류기입니다. "
    "사용자 입력에서 SINGLE(단일 매치)/TOURNAMENT(토너먼트)를 분류하고, "
    "지역·날짜 범위·팀 수를 슬롯으로 추출하세요. "
    "정보가 없으면 해당 슬롯을 비웁니다. extract_intent 도구로 반환하세요."
)


def parse_intent(state: AgentState, claude_client: ClaudeClient) -> AgentState:
    """사용자 입력을 intent + slots로 분류."""
    try:
        result = claude_client.chat_with_tool(
            system=PARSE_SYSTEM,
            user=state["user_input"],
            tool=INTENT_TOOL,
        )
        state["intent"] = result.get("intent", "UNKNOWN")
        state["slots"] = {
            "region": result.get("region"),
            "date_from": result.get("date_from"),
            "date_to": result.get("date_to"),
            "team_count": result.get("team_count", 1),
        }
    except Exception as e:
        state["intent"] = "UNKNOWN"
        state["errors"].append(f"intent 분류 실패: {e}")
    return state

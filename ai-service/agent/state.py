from typing import Literal, NotRequired, TypedDict


class AgentState(TypedDict):
    user_input: str
    user_id: int
    intent: Literal["SINGLE", "TOURNAMENT", "UNKNOWN"]
    slots: dict
    stadium_candidates: list[dict]
    team_info: dict
    proposals: list[dict]
    bracket: dict | None
    warnings: list[str]
    errors: list[str]
    # 노드/sub-agent가 호출한 Tool 흔적 (평가용). 예: ["search_stadium", "list_stadium_slots", ...]
    tool_calls: list[str]
    proposal_id: NotRequired[str]


def make_initial_state(
    user_input: str, user_id: int, team_info: dict | None = None
) -> AgentState:
    return AgentState(
        user_input=user_input,
        user_id=user_id,
        intent="UNKNOWN",
        slots={},
        stadium_candidates=[],
        team_info=team_info or {},
        proposals=[],
        bracket=None,
        warnings=[],
        errors=[],
        tool_calls=[],
    )

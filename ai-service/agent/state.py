from typing import Literal, TypedDict


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


def make_initial_state(user_input: str, user_id: int) -> AgentState:
    return AgentState(
        user_input=user_input,
        user_id=user_id,
        intent="UNKNOWN",
        slots={},
        stadium_candidates=[],
        team_info={},
        proposals=[],
        bracket=None,
        warnings=[],
        errors=[],
    )

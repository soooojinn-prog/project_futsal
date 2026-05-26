from typing import Literal

from pydantic import BaseModel, Field


class AgentRequest(BaseModel):
    user_input: str = Field(min_length=1, max_length=500)
    user_id: int
    # Spring AgentService가 세션 user의 소속 팀을 미리 조회해 전달하면
    # 토너먼트 모드에서 conflict 체크가 실제로 동작한다. 미지정 시 None.
    # 형식 예: {"team_id": 5, "team_name": "FC강남",
    #           "team_ids": [5, 7], "team_names": {5: "FC강남", 7: "FC홍대"}}
    team_info: dict | None = None


class TeamSummary(BaseModel):
    id: int | None = None
    name: str


class MatchProposal(BaseModel):
    stadium_id: int
    stadium_name: str
    start_time: str
    duration_min: int = 60
    team_a: TeamSummary
    team_b: TeamSummary | None = None
    stage: str | None = None


class BracketDTO(BaseModel):
    rounds: list[list[dict]]


class ProposalResponse(BaseModel):
    proposal_id: str
    intent: Literal["SINGLE", "TOURNAMENT", "UNKNOWN"]
    warnings: list[str] = []
    matches: list[MatchProposal] = []
    bracket: BracketDTO | None = None


class ConfirmValidateRequest(BaseModel):
    proposal_id: str
    matches: list[MatchProposal]

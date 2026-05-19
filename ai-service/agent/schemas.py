from typing import Literal

from pydantic import BaseModel, Field


class AgentRequest(BaseModel):
    user_input: str = Field(min_length=1, max_length=500)
    user_id: int


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

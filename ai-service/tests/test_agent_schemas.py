from agent.schemas import (
    AgentRequest,
    BracketDTO,
    ConfirmValidateRequest,
    MatchProposal,
    ProposalResponse,
    TeamSummary,
)


def test_agent_request_min():
    r = AgentRequest(user_input="강남 매치", user_id=1)
    assert r.user_input == "강남 매치"
    assert r.user_id == 1


def test_match_proposal_optional_team_b():
    m = MatchProposal(
        stadium_id=1,
        stadium_name="강남풋살장",
        start_time="2026-05-23T14:00",
        duration_min=60,
        team_a=TeamSummary(id=1, name="A팀"),
    )
    assert m.team_b is None
    assert m.stage is None


def test_proposal_response_with_bracket():
    bracket = BracketDTO(
        rounds=[[{"matchIdx": 0}], [{"matchIdx": 1, "depends_on": [0]}]]
    )
    r = ProposalResponse(
        proposal_id="p1",
        intent="TOURNAMENT",
        warnings=[],
        matches=[],
        bracket=bracket,
    )
    assert r.bracket is not None
    assert len(r.bracket.rounds) == 2


def test_confirm_validate_request_min():
    r = ConfirmValidateRequest(proposal_id="p1", matches=[])
    assert r.matches == []

from unittest.mock import MagicMock

from agent.subagents import MatchAgent, StadiumAgent, TeamAgent


def test_stadium_agent_returns_candidates_and_slots():
    tools = MagicMock()
    tools.search_stadium.return_value = [
        {"id": 1, "name": "강남"},
        {"id": 2, "name": "역삼"},
    ]
    tools.list_stadium_slots.side_effect = [
        [{"start": "2026-05-26T10:00", "end": "2026-05-26T11:00"}],
        [{"start": "2026-05-26T11:00", "end": "2026-05-26T12:00"}],
    ]

    agent = StadiumAgent(tools=tools)
    result = agent.run(region="강남", date="2026-05-26", needed_matches=2)

    assert len(result["candidates"]) == 2
    assert len(result["slots"]) >= 2


def test_team_agent_returns_members_per_team():
    tools = MagicMock()
    tools.list_team_members.side_effect = [
        [{"id": 1, "nickname": "A1"}],
        [{"id": 2, "nickname": "B1"}],
    ]
    tools.find_team_conflicts.return_value = []

    agent = TeamAgent(tools=tools)
    result = agent.run(team_ids=[1, 2], date_from="2026-05-26", date_to="2026-05-26")

    assert len(result["teams"]) == 2
    assert result["teams"][0]["members"][0]["nickname"] == "A1"


def test_match_agent_generates_bracket_and_proposals():
    agent = MatchAgent()
    teams = [
        {"id": 1, "name": "A"},
        {"id": 2, "name": "B"},
        {"id": 3, "name": "C"},
        {"id": 4, "name": "D"},
    ]
    slots = [
        {"stadium_id": 10, "stadium_name": "강남", "start": "2026-05-26T10:00"},
        {"stadium_id": 10, "stadium_name": "강남", "start": "2026-05-26T11:00"},
        {"stadium_id": 10, "stadium_name": "강남", "start": "2026-05-26T12:00"},
    ]

    result = agent.run(teams=teams, slots=slots)

    assert len(result["proposals"]) == 3
    assert result["bracket"]["total_matches"] == 3
    assert result["proposals"][0]["stage"] in ("SEMIFINAL", "FINAL")


def test_match_agent_warns_when_not_enough_slots():
    agent = MatchAgent()
    teams = [
        {"id": 1, "name": "A"},
        {"id": 2, "name": "B"},
        {"id": 3, "name": "C"},
        {"id": 4, "name": "D"},
    ]
    slots = [
        {"stadium_id": 10, "stadium_name": "강남", "start": "2026-05-26T10:00"},
    ]

    result = agent.run(teams=teams, slots=slots)
    assert len(result["proposals"]) == 1
    assert any("슬롯 부족" in w for w in result["warnings"])

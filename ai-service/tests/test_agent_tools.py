from unittest.mock import MagicMock

import pytest

from agent.tools import Tools, generate_bracket, propose_match


def test_search_stadium_delegates_to_client():
    client = MagicMock()
    client.search_stadium.return_value = [{"id": 1, "name": "강남풋살장"}]
    tools = Tools(client=client)
    result = tools.search_stadium("강남", "2026-05-23", "2026-05-24")
    assert result == [{"id": 1, "name": "강남풋살장"}]
    client.search_stadium.assert_called_once_with("강남", "2026-05-23", "2026-05-24")


def test_list_stadium_slots():
    client = MagicMock()
    client.list_stadium_slots.return_value = [{"start": "14:00", "end": "15:00"}]
    tools = Tools(client=client)
    result = tools.list_stadium_slots(1, "2026-05-23")
    assert len(result) == 1


def test_list_team_members():
    client = MagicMock()
    client.list_team_members.return_value = [{"id": 10, "nickname": "수진"}]
    tools = Tools(client=client)
    result = tools.list_team_members(5)
    assert result[0]["nickname"] == "수진"


def test_find_team_conflicts():
    client = MagicMock()
    client.find_team_conflicts.return_value = []
    tools = Tools(client=client)
    result = tools.find_team_conflicts(5, "2026-05-23", "2026-05-24")
    assert result == []


def test_generate_bracket_4teams():
    bracket = generate_bracket([1, 2, 3, 4])
    assert len(bracket["rounds"]) == 2
    assert len(bracket["rounds"][0]) == 2
    assert len(bracket["rounds"][1]) == 1


def test_generate_bracket_8teams():
    bracket = generate_bracket([1, 2, 3, 4, 5, 6, 7, 8])
    assert len(bracket["rounds"]) == 3
    assert len(bracket["rounds"][0]) == 4
    assert len(bracket["rounds"][1]) == 2
    assert len(bracket["rounds"][2]) == 1


def test_generate_bracket_invalid_team_count():
    with pytest.raises(ValueError):
        generate_bracket([1, 2, 3])


def test_propose_match_assembles_dict():
    p = propose_match(
        stadium_id=1,
        stadium_name="강남",
        start_time="2026-05-23T14:00",
        team_a={"id": 1, "name": "A"},
        team_b={"id": 2, "name": "B"},
        stage="SEMIFINAL",
    )
    assert p["stadium_id"] == 1
    assert p["team_b"]["name"] == "B"
    assert p["stage"] == "SEMIFINAL"
    assert p["duration_min"] == 60

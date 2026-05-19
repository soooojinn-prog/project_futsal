from unittest.mock import MagicMock

from agent.nodes import parse_intent
from agent.state import make_initial_state


def test_parse_intent_single_match():
    claude = MagicMock()
    claude.chat_with_tool.return_value = {
        "intent": "SINGLE",
        "region": "강남",
        "date_from": "2026-05-23",
        "date_to": "2026-05-24",
        "team_count": 1,
    }
    state = make_initial_state("강남 토요일 매치", user_id=1)
    new_state = parse_intent(state, claude_client=claude)

    assert new_state["intent"] == "SINGLE"
    assert new_state["slots"]["region"] == "강남"
    assert new_state["slots"]["date_from"] == "2026-05-23"


def test_parse_intent_tournament():
    claude = MagicMock()
    claude.chat_with_tool.return_value = {
        "intent": "TOURNAMENT",
        "region": "강남",
        "date_from": "2026-05-26",
        "date_to": "2026-05-26",
        "team_count": 4,
    }
    state = make_initial_state("4팀 토너먼트 강남", user_id=1)
    new_state = parse_intent(state, claude_client=claude)

    assert new_state["intent"] == "TOURNAMENT"
    assert new_state["slots"]["team_count"] == 4


def test_parse_intent_falls_back_to_unknown_on_error():
    claude = MagicMock()
    claude.chat_with_tool.side_effect = RuntimeError("boom")
    state = make_initial_state("아무말", user_id=1)
    new_state = parse_intent(state, claude_client=claude)

    assert new_state["intent"] == "UNKNOWN"
    assert "intent 분류 실패" in new_state["errors"][0]


# ---------- 단일 매치 흐름 노드 ----------
from agent.nodes import (
    single_match_node,
    single_review_node,
    single_stadium_node,
    single_team_node,
)


def _filled_state(team_count=1):
    s = make_initial_state("강남 매치", user_id=1)
    s["intent"] = "SINGLE"
    s["slots"] = {
        "region": "강남",
        "date_from": "2026-05-23",
        "date_to": "2026-05-24",
        "team_count": team_count,
    }
    return s


def test_single_stadium_node_populates_candidates():
    tools = MagicMock()
    tools.search_stadium.return_value = [
        {"id": 1, "name": "강남풋살장"},
        {"id": 2, "name": "역삼풋살장"},
    ]
    state = _filled_state()
    new_state = single_stadium_node(state, tools=tools)
    assert len(new_state["stadium_candidates"]) == 2


def test_single_stadium_node_warns_when_empty():
    tools = MagicMock()
    tools.search_stadium.return_value = []
    state = _filled_state()
    new_state = single_stadium_node(state, tools=tools)
    assert new_state["stadium_candidates"] == []
    assert any("경기장" in w for w in new_state["warnings"])


def test_single_team_node_fetches_user_team():
    tools = MagicMock()
    tools.list_team_members.return_value = [{"id": 10, "nickname": "수진"}]
    tools.find_team_conflicts.return_value = []
    state = _filled_state()
    state["team_info"] = {"team_id": 5, "team_name": "A팀"}
    new_state = single_team_node(state, tools=tools)
    assert new_state["team_info"]["members"] == [{"id": 10, "nickname": "수진"}]
    assert new_state["team_info"]["conflicts"] == []


def test_single_match_node_proposes_one():
    tools = MagicMock()
    tools.list_stadium_slots.return_value = [
        {"start": "2026-05-23T14:00", "end": "2026-05-23T15:00"}
    ]
    state = _filled_state()
    state["stadium_candidates"] = [{"id": 1, "name": "강남풋살장"}]
    state["team_info"] = {"team_id": 5, "team_name": "A팀", "conflicts": []}
    new_state = single_match_node(state, tools=tools)
    assert len(new_state["proposals"]) == 1
    assert new_state["proposals"][0]["stadium_id"] == 1


def test_single_match_node_skips_conflict():
    tools = MagicMock()
    tools.list_stadium_slots.return_value = [
        {"start": "2026-05-23T14:00", "end": "2026-05-23T15:00"}
    ]
    state = _filled_state()
    state["stadium_candidates"] = [{"id": 1, "name": "강남풋살장"}]
    state["team_info"] = {
        "team_id": 5,
        "team_name": "A팀",
        "conflicts": [{"start": "2026-05-23T14:00", "end": "2026-05-23T15:00"}],
    }
    new_state = single_match_node(state, tools=tools)
    assert len(new_state["proposals"]) == 0
    assert any("충돌" in w for w in new_state["warnings"])


def test_single_review_node_validates_at_least_one_proposal():
    state = _filled_state()
    state["proposals"] = [
        {"stadium_id": 1, "start_time": "2026-05-23T14:00", "duration_min": 60}
    ]
    new_state = single_review_node(state, tools=MagicMock())
    assert new_state.get("errors", []) == []

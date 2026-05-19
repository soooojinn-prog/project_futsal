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

from agent.state import AgentState, make_initial_state


def test_make_initial_state_defaults():
    s = make_initial_state(user_input="강남 매치", user_id=42)
    assert s["user_input"] == "강남 매치"
    assert s["user_id"] == 42
    assert s["intent"] == "UNKNOWN"
    assert s["slots"] == {}
    assert s["stadium_candidates"] == []
    assert s["proposals"] == []
    assert s["bracket"] is None
    assert s["warnings"] == []
    assert s["errors"] == []

from unittest.mock import MagicMock

from agent.graph import build_agent_graph
from agent.state import make_initial_state


def test_graph_single_flow_invokes_single_nodes():
    claude = MagicMock()
    claude.chat_with_tool.return_value = {
        "intent": "SINGLE",
        "region": "강남",
        "date_from": "2026-05-23",
        "date_to": "2026-05-24",
        "team_count": 1,
    }
    tools = MagicMock()
    tools.search_stadium.return_value = [{"id": 1, "name": "강남풋살장"}]
    tools.list_stadium_slots.return_value = [
        {"start": "2026-05-23T14:00", "end": "2026-05-23T15:00"}
    ]
    tools.list_team_members.return_value = []
    tools.find_team_conflicts.return_value = []

    graph = build_agent_graph(claude_client=claude, tools=tools)

    state = make_initial_state("강남 토요일 매치", user_id=1)
    state["team_info"] = {"team_id": 5, "team_name": "내 팀"}
    final = graph.invoke(state)

    assert final["intent"] == "SINGLE"
    assert "proposal_id" in final
    assert len(final["proposals"]) >= 1


def test_graph_tournament_flow():
    claude = MagicMock()
    claude.chat_with_tool.return_value = {
        "intent": "TOURNAMENT",
        "region": "강남",
        "date_from": "2026-05-26",
        "date_to": "2026-05-26",
        "team_count": 4,
    }
    tools = MagicMock()
    tools.search_stadium.return_value = [{"id": 10, "name": "강남"}]
    tools.list_stadium_slots.return_value = [
        {"start": "2026-05-26T10:00", "end": "2026-05-26T11:00"},
        {"start": "2026-05-26T11:00", "end": "2026-05-26T12:00"},
        {"start": "2026-05-26T12:00", "end": "2026-05-26T13:00"},
    ]
    tools.list_team_members.return_value = []
    tools.find_team_conflicts.return_value = []

    graph = build_agent_graph(claude_client=claude, tools=tools)

    state = make_initial_state("4팀 토너먼트 강남 일요일", user_id=1)
    state["team_info"] = {
        "team_ids": [1, 2, 3, 4],
        "team_names": {1: "A", 2: "B", 3: "C", 4: "D"},
    }
    final = graph.invoke(state)

    assert final["intent"] == "TOURNAMENT"
    assert final["bracket"] is not None
    assert len(final["proposals"]) == 3

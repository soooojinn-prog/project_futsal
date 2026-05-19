import importlib
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def test_client(tmp_path, monkeypatch):
    monkeypatch.setenv("RAG_CHROMA_DIR", str(tmp_path / "no_such"))
    import main as _main

    importlib.reload(_main)

    fake_graph = MagicMock()
    fake_graph.invoke.return_value = {
        "intent": "SINGLE",
        "warnings": [],
        "proposals": [
            {
                "stadium_id": 1,
                "stadium_name": "강남",
                "start_time": "2026-05-23T14:00",
                "duration_min": 60,
                "team_a": {"id": 5, "name": "내 팀"},
                "team_b": None,
                "stage": None,
            }
        ],
        "bracket": None,
        "proposal_id": "prop_abc12345",
    }
    _main.agent_graph = fake_graph

    with TestClient(_main.app) as client:
        yield client


def test_agent_run_returns_proposal(test_client):
    resp = test_client.post(
        "/agent/run",
        json={"user_input": "강남 토요일 매치", "user_id": 1},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["proposal_id"].startswith("prop_")
    assert body["intent"] == "SINGLE"
    assert len(body["matches"]) == 1


def test_agent_run_validates_empty_input(test_client):
    resp = test_client.post(
        "/agent/run", json={"user_input": "", "user_id": 1}
    )
    assert resp.status_code == 422

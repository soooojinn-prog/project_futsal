import importlib
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def test_client(tmp_path, monkeypatch):
    """RAG_CHROMA_DIR을 존재하지 않는 경로로 가리켜 lifespan의 실제 RAG 초기화를 건너뛰고,
    rag_chain·router_classifier 모듈 globals에 mock 객체를 직접 주입한다."""
    monkeypatch.setenv("RAG_CHROMA_DIR", str(tmp_path / "no_such"))
    import main as _main

    importlib.reload(_main)

    from rag.schemas import Citation, ClassifyResponse, RagResponse

    _main.rag_chain = MagicMock()
    _main.router_classifier = MagicMock()
    _main.rag_chain.answer.return_value = RagResponse(
        answer="default-answer",
        citations=[Citation(source="S", section="Sec", page=1, snippet="snip", score=0.8)],
        retrieved_chunks=1,
    )
    _main.router_classifier.classify.return_value = ClassifyResponse(
        intent="KNOWLEDGE", confidence=0.9
    )

    with TestClient(_main.app) as client:
        yield client, _main


def test_chat_rag_returns_answer_and_citations(test_client):
    client, _ = test_client
    resp = client.post("/chat/rag", json={"user_message": "오프사이드?"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["answer"] == "default-answer"
    assert body["retrieved_chunks"] >= 1
    assert isinstance(body["citations"], list)
    assert body["citations"][0]["source"] == "S"


def test_router_classify_returns_intent(test_client):
    client, m = test_client
    from rag.schemas import ClassifyResponse

    m.router_classifier.classify.return_value = ClassifyResponse(
        intent="ADVICE", confidence=0.7
    )
    resp = client.post("/router/classify", json={"user_message": "팀이 자꾸 져요"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["intent"] == "ADVICE"
    assert 0 <= body["confidence"] <= 1


def test_chat_rag_validates_empty_message(test_client):
    client, _ = test_client
    resp = client.post("/chat/rag", json={"user_message": ""})
    assert resp.status_code == 422


def test_health_still_works(test_client):
    client, _ = test_client
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert "rag_enabled" in body


def test_chat_rag_with_user_context(test_client):
    client, _ = test_client
    payload = {
        "user_message": "내 등급에 맞는 포메이션 추천해줘",
        "user_context": {
            "nickname": "수진",
            "grade": "BRONZE",
            "preferred_position": "GK",
        },
    }
    resp = client.post("/chat/rag", json=payload)
    assert resp.status_code == 200

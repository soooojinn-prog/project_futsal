from rag.schemas import (
    Citation,
    ClassifyRequest,
    ClassifyResponse,
    RagRequest,
    RagResponse,
    UserContext,
)


def test_citation_required_fields():
    c = Citation(source="FIFA Futsal Laws", section="Law 11", page=14, snippet="...", score=0.87)
    assert c.source == "FIFA Futsal Laws"
    assert c.page == 14


def test_rag_request_minimal():
    req = RagRequest(user_message="오프사이드 규칙?")
    assert req.user_message == "오프사이드 규칙?"
    assert req.user_context is None


def test_rag_request_with_context():
    req = RagRequest(
        user_message="포메이션",
        user_context=UserContext(nickname="수진", grade="BRONZE", preferred_position="GK"),
    )
    assert req.user_context.nickname == "수진"


def test_rag_response_with_citations():
    resp = RagResponse(
        answer="풋살에는 오프사이드가 없습니다.",
        citations=[
            Citation(source="FIFA", section="Law 11", page=14, snippet="...", score=0.9)
        ],
        retrieved_chunks=4,
    )
    assert len(resp.citations) == 1
    assert resp.retrieved_chunks == 4


def test_classify_response_intent_literal():
    r = ClassifyResponse(intent="KNOWLEDGE", confidence=0.92)
    assert r.intent == "KNOWLEDGE"


def test_classify_request_validates_min_length():
    import pytest
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        ClassifyRequest(user_message="")

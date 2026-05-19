from unittest.mock import MagicMock

from rag.router_classifier import RouterClassifier
from rag.schemas import ClassifyResponse


def test_classifier_returns_knowledge():
    claude = MagicMock()
    claude.chat_with_tool.return_value = {"intent": "KNOWLEDGE", "confidence": 0.92}

    rc = RouterClassifier(claude_client=claude)
    result = rc.classify("4-0 포메이션 뭐야?")

    assert isinstance(result, ClassifyResponse)
    assert result.intent == "KNOWLEDGE"
    assert result.confidence == 0.92


def test_classifier_returns_advice():
    claude = MagicMock()
    claude.chat_with_tool.return_value = {"intent": "ADVICE", "confidence": 0.81}

    rc = RouterClassifier(claude_client=claude)
    result = rc.classify("우리 팀이 자꾸 지는데")

    assert result.intent == "ADVICE"
    assert result.confidence == 0.81


def test_classifier_uses_classify_tool_schema():
    claude = MagicMock()
    claude.chat_with_tool.return_value = {"intent": "KNOWLEDGE", "confidence": 0.9}

    rc = RouterClassifier(claude_client=claude)
    rc.classify("질문")

    tool = claude.chat_with_tool.call_args.kwargs["tool"]
    assert tool["name"] == "classify_intent"
    schema = tool["input_schema"]
    assert "intent" in schema["properties"]
    assert "confidence" in schema["properties"]
    assert set(schema["properties"]["intent"]["enum"]) == {"KNOWLEDGE", "ADVICE"}


def test_classifier_passes_user_message_to_claude():
    claude = MagicMock()
    claude.chat_with_tool.return_value = {"intent": "ADVICE", "confidence": 0.7}

    rc = RouterClassifier(claude_client=claude)
    rc.classify("우리 팀 5명인데 한 명이 없어")

    assert claude.chat_with_tool.call_args.kwargs["user"] == "우리 팀 5명인데 한 명이 없어"

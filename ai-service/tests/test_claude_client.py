from unittest.mock import MagicMock, patch

from rag.claude_client import ClaudeClient


def test_chat_returns_text_from_first_content_block():
    fake_response = MagicMock()
    fake_response.content = [MagicMock(text="안녕하세요")]
    with patch("rag.claude_client.anthropic.Anthropic") as mock_anthropic_cls:
        client_instance = mock_anthropic_cls.return_value
        client_instance.messages.create.return_value = fake_response

        client = ClaudeClient(api_key="sk-test")
        result = client.chat(system="sys", user="hi")

    assert result == "안녕하세요"
    client_instance.messages.create.assert_called_once()
    _, kwargs = client_instance.messages.create.call_args
    assert kwargs["model"] == "claude-sonnet-4-6"
    assert kwargs["system"] == "sys"
    assert kwargs["max_tokens"] == 2048


def test_chat_with_tool_returns_tool_input_dict():
    tool_block = MagicMock()
    tool_block.type = "tool_use"
    tool_block.input = {"intent": "KNOWLEDGE", "confidence": 0.9}
    fake_response = MagicMock()
    fake_response.content = [tool_block]

    with patch("rag.claude_client.anthropic.Anthropic") as mock_anthropic_cls:
        client_instance = mock_anthropic_cls.return_value
        client_instance.messages.create.return_value = fake_response

        client = ClaudeClient(api_key="sk-test")
        result = client.chat_with_tool(
            system="sys",
            user="msg",
            tool={"name": "classify", "description": "d", "input_schema": {}},
        )

    assert result == {"intent": "KNOWLEDGE", "confidence": 0.9}
    _, kwargs = client_instance.messages.create.call_args
    assert kwargs["tools"][0]["name"] == "classify"
    assert kwargs["tool_choice"] == {"type": "tool", "name": "classify"}


def test_init_raises_without_api_key(monkeypatch):
    import pytest

    monkeypatch.delenv("CLAUDE_API_KEY", raising=False)
    with pytest.raises(RuntimeError):
        ClaudeClient(api_key=None)


def test_chat_returns_empty_string_when_no_content():
    fake_response = MagicMock()
    fake_response.content = []
    with patch("rag.claude_client.anthropic.Anthropic") as mock_anthropic_cls:
        mock_anthropic_cls.return_value.messages.create.return_value = fake_response
        client = ClaudeClient(api_key="sk-test")
        assert client.chat(system="s", user="u") == ""

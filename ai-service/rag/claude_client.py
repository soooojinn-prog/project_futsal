import os

import anthropic


class ClaudeClient:
    """Anthropic SDK 얇은 래퍼 — 단위 테스트 시 Mock 가능."""

    DEFAULT_MODEL = "claude-sonnet-4-6"
    DEFAULT_MAX_TOKENS = 2048

    def __init__(self, api_key: str | None = None, model: str = DEFAULT_MODEL):
        key = api_key or os.environ.get("CLAUDE_API_KEY")
        if not key:
            raise RuntimeError("CLAUDE_API_KEY가 설정되지 않았습니다.")
        self._client = anthropic.Anthropic(api_key=key)
        self._model = model

    def chat(self, system: str, user: str, max_tokens: int = DEFAULT_MAX_TOKENS) -> str:
        resp = self._client.messages.create(
            model=self._model,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        if not resp.content:
            return ""
        return resp.content[0].text

    def chat_with_tool(
        self, system: str, user: str, tool: dict, max_tokens: int = 512
    ) -> dict:
        """Tool Use로 structured output 강제. tool은 {name, description, input_schema} 형태."""
        resp = self._client.messages.create(
            model=self._model,
            max_tokens=max_tokens,
            system=system,
            tools=[tool],
            tool_choice={"type": "tool", "name": tool["name"]},
            messages=[{"role": "user", "content": user}],
        )
        for block in resp.content:
            if getattr(block, "type", None) == "tool_use":
                return block.input
        raise RuntimeError(f"tool_use 블록을 찾을 수 없음: {resp.content!r}")

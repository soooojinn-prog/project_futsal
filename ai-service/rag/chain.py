from __future__ import annotations

from .claude_client import ClaudeClient
from .retriever import Retriever
from .schemas import Citation, RagResponse, UserContext

try:
    from langsmith import traceable
except Exception:  # langsmith 미설치 환경 fallback — 데코레이터를 no-op로
    def traceable(*args, **kwargs):  # type: ignore[no-redef]
        if args and callable(args[0]):
            return args[0]

        def _decorator(fn):
            return fn

        return _decorator


def _format_context_block(citations: list[Citation]) -> str:
    if not citations:
        return (
            "(검색된 풋살 지식 문서가 없습니다. 일반 지식으로 정중하게 답하되, "
            "확실하지 않은 내용은 추측하지 말고 모른다고 답하세요.)"
        )
    lines = []
    for i, c in enumerate(citations, start=1):
        page_part = f" p.{c.page}" if c.page else ""
        lines.append(f"[{i}] {c.source} / {c.section}{page_part}\n{c.snippet}")
    return "\n\n".join(lines)


def _format_user_context(ctx: UserContext | None) -> str:
    if ctx is None:
        return ""
    parts = []
    if ctx.nickname:
        parts.append(f"닉네임: {ctx.nickname}")
    if ctx.grade:
        parts.append(f"실력 등급: {ctx.grade}")
    if ctx.preferred_position:
        parts.append(f"선호 포지션: {ctx.preferred_position}")
    if not parts:
        return ""
    return "현재 유저 정보:\n- " + "\n- ".join(parts) + "\n\n"


def build_system_prompt(citations: list[Citation], user_context: UserContext | None) -> str:
    return (
        "당신은 풋살 전문 AI 어시스턴트입니다. 아래 [참고 문서] 블록에 인용된 내용을 우선적으로 활용해 "
        "정확하고 간결하게 답하세요. 참고 문서에 없는 내용은 추측하지 말고 모른다고 답하세요. "
        "풋살과 무관한 질문은 정중히 거절하세요.\n\n"
        f"{_format_user_context(user_context)}"
        "[참고 문서]\n"
        f"{_format_context_block(citations)}"
    )


class RagChain:
    def __init__(self, retriever: Retriever, claude_client: ClaudeClient, top_k: int = 4):
        self._retriever = retriever
        self._claude = claude_client
        self._top_k = top_k

    @traceable(name="rag_answer", run_type="chain")
    def answer(self, query: str, user_context: UserContext | None) -> RagResponse:
        citations = self._retriever.search(query, k=self._top_k)
        system_prompt = build_system_prompt(citations, user_context)
        answer_text = self._claude.chat(system=system_prompt, user=query)
        return RagResponse(
            answer=answer_text,
            citations=citations,
            retrieved_chunks=len(citations),
        )

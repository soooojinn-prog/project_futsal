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
        "당신은 풋살 전문 AI 어시스턴트입니다. 아래 [참고 문서]에 답변에 필요한 정보가 들어 있습니다. "
        "문서의 사실을 활용해 질문에 정확히 답하세요.\n\n"
        "답변 규칙:\n"
        "1. 참고 문서에서 질문과 관련된 핵심 사실을 찾아 1~3문장의 한국어 줄글로 답합니다.\n"
        "2. 숫자·규칙·정의(시간·거리·인원 등)는 문서 표기 그대로 정확히 인용합니다.\n"
        "3. 문서 내용을 자연스럽게 풀어 요약·설명해도 좋습니다. 단, 문서에 없는 새로운 사실·수치·예시는 만들어내지 마세요.\n"
        "4. 마크다운 헤더(`#`)·목록·이모지·강조는 사용하지 마세요. 줄글 위주로 답합니다.\n"
        "5. 참고 문서 어디에도 관련 정보가 정말 없을 때에 한해 \"해당 정보는 풋살 규칙 문서에서 찾지 못했습니다.\"라고 답합니다. "
        "문서에 부분이라도 단서가 있으면 그 단서를 근거로 충실히 답하세요.\n"
        "6. 풋살과 무관한 질문은 정중히 거절합니다.\n\n"
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

from unittest.mock import MagicMock

from rag.chain import RagChain
from rag.schemas import Citation, UserContext


def test_chain_uses_retrieved_chunks_in_prompt():
    retriever = MagicMock()
    retriever.search.return_value = [
        Citation(source="FIFA", section="Law 11", page=14, snippet="There is no offside.", score=0.9),
        Citation(source="FIFA", section="Law 12", page=15, snippet="Five fouls limit.", score=0.7),
    ]
    claude = MagicMock()
    claude.chat.return_value = "풋살에는 오프사이드가 없습니다."

    chain = RagChain(retriever=retriever, claude_client=claude)
    resp = chain.answer("오프사이드 규칙이 뭐야?", user_context=None)

    assert resp.answer == "풋살에는 오프사이드가 없습니다."
    assert resp.retrieved_chunks == 2
    assert len(resp.citations) == 2

    system_arg = claude.chat.call_args.kwargs["system"]
    assert "There is no offside." in system_arg
    assert "Law 11" in system_arg


def test_chain_empty_retrieval_still_calls_claude():
    retriever = MagicMock()
    retriever.search.return_value = []
    claude = MagicMock()
    claude.chat.return_value = "관련 문서를 찾지 못했습니다."

    chain = RagChain(retriever=retriever, claude_client=claude)
    resp = chain.answer("이상한 질문", user_context=None)

    assert resp.retrieved_chunks == 0
    assert resp.citations == []
    claude.chat.assert_called_once()


def test_chain_includes_user_context_in_prompt():
    retriever = MagicMock()
    retriever.search.return_value = [
        Citation(source="X", section="Y", page=1, snippet="text", score=0.5),
    ]
    claude = MagicMock()
    claude.chat.return_value = "답"

    chain = RagChain(retriever=retriever, claude_client=claude)
    ctx = UserContext(nickname="수진", grade="BRONZE", preferred_position="GK")
    chain.answer("질문", user_context=ctx)

    system_arg = claude.chat.call_args.kwargs["system"]
    assert "수진" in system_arg
    assert "BRONZE" in system_arg


def test_chain_passes_query_as_user_message():
    retriever = MagicMock()
    retriever.search.return_value = []
    claude = MagicMock()
    claude.chat.return_value = "답"

    chain = RagChain(retriever=retriever, claude_client=claude)
    chain.answer("내 질문", user_context=None)

    user_arg = claude.chat.call_args.kwargs["user"]
    assert user_arg == "내 질문"


def test_chain_top_k_is_passed_to_retriever():
    retriever = MagicMock()
    retriever.search.return_value = []
    claude = MagicMock()
    claude.chat.return_value = ""

    chain = RagChain(retriever=retriever, claude_client=claude, top_k=6)
    chain.answer("질문", user_context=None)

    retriever.search.assert_called_once_with("질문", k=6)

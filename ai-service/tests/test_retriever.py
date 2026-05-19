import uuid

import chromadb
import pytest

from rag.retriever import Retriever


@pytest.fixture
def in_memory_collection():
    client = chromadb.EphemeralClient()
    coll = client.create_collection(
        name=f"test_futsal_{uuid.uuid4().hex[:8]}",
        metadata={"hnsw:space": "cosine"},
    )
    return coll


class FakeEmbedder:
    """결정적 더미 임베더. ChromaDB cosine 거리 계산에 충분한 3차원 벡터를 반환."""

    def encode(self, text: str) -> list[float]:
        return [float(len(text) % 7), float(sum(map(ord, text)) % 13), 1.0]


@pytest.fixture
def fake_embedder():
    return FakeEmbedder()


def test_search_returns_top_k_citations(in_memory_collection, fake_embedder):
    docs = [
        ("d1", "풋살에는 오프사이드 규칙이 없다", {"source": "FIFA", "section": "Law 11", "page": 14}),
        ("d2", "4-0 포메이션은 수비라인이 없다", {"source": "Tactics", "section": "Formations", "page": 5}),
        ("d3", "코너킥은 4초 안에 차야 한다", {"source": "FIFA", "section": "Law 17", "page": 22}),
    ]
    in_memory_collection.add(
        ids=[d[0] for d in docs],
        documents=[d[1] for d in docs],
        metadatas=[d[2] for d in docs],
        embeddings=[fake_embedder.encode(d[1]) for d in docs],
    )

    retriever = Retriever(collection=in_memory_collection, embedder=fake_embedder)
    citations = retriever.search("오프사이드", k=2)

    assert len(citations) == 2
    assert all(c.source for c in citations)
    assert all(c.snippet for c in citations)
    assert all(0.0 <= c.score <= 1.0 for c in citations)


def test_search_empty_when_no_docs(in_memory_collection, fake_embedder):
    retriever = Retriever(collection=in_memory_collection, embedder=fake_embedder)
    citations = retriever.search("질문", k=4)
    assert citations == []


def test_snippet_is_truncated_if_long(in_memory_collection, fake_embedder):
    long_text = "가" * 500
    in_memory_collection.add(
        ids=["long"],
        documents=[long_text],
        metadatas=[{"source": "S", "section": "Sec", "page": 1}],
        embeddings=[fake_embedder.encode(long_text)],
    )
    retriever = Retriever(collection=in_memory_collection, embedder=fake_embedder)
    citations = retriever.search("질문", k=1)
    assert len(citations[0].snippet) <= 200

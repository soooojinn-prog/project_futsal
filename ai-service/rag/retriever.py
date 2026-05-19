from __future__ import annotations

from pathlib import Path

import chromadb
from chromadb.api.models.Collection import Collection
from sentence_transformers import SentenceTransformer

from .schemas import Citation

SNIPPET_MAX = 200
DEFAULT_COLLECTION = "futsal_knowledge"


class SentenceTransformerEmbedder:
    """sentence-transformers 모델 래퍼. 테스트에서는 인터페이스 호환 가짜 객체로 교체."""

    def __init__(self, model_name: str = "jhgan/ko-sroberta-multitask"):
        self._model = SentenceTransformer(model_name)

    def encode(self, text: str) -> list[float]:
        return self._model.encode(text, normalize_embeddings=True).tolist()


class Retriever:
    def __init__(self, collection: Collection, embedder):
        self._collection = collection
        self._embedder = embedder

    def search(self, query: str, k: int = 4) -> list[Citation]:
        emb = self._embedder.encode(query)
        result = self._collection.query(query_embeddings=[emb], n_results=k)

        ids = result.get("ids", [[]])[0]
        if not ids:
            return []

        docs = result.get("documents", [[]])[0]
        metas = result.get("metadatas", [[]])[0]
        dists = result.get("distances", [[]])[0]

        citations: list[Citation] = []
        for doc, meta, dist in zip(docs, metas, dists):
            score = max(0.0, min(1.0, 1.0 - float(dist)))
            snippet = doc[:SNIPPET_MAX]
            citations.append(
                Citation(
                    source=meta.get("source", "unknown"),
                    section=meta.get("section", ""),
                    page=meta.get("page"),
                    snippet=snippet,
                    score=score,
                )
            )
        return citations


def open_persistent_retriever(
    persist_dir: Path | str, collection_name: str = DEFAULT_COLLECTION
) -> Retriever:
    """운영용 헬퍼: 디스크에 저장된 ChromaDB와 실제 임베더 로드."""
    path = Path(persist_dir)
    if not path.exists():
        raise RuntimeError(
            f"ChromaDB persist 디렉토리가 없음: {path}. build_index.py를 먼저 실행하세요."
        )
    client = chromadb.PersistentClient(path=str(path))
    collection = client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"},
    )
    embedder = SentenceTransformerEmbedder()
    return Retriever(collection=collection, embedder=embedder)

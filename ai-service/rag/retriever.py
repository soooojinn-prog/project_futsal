from __future__ import annotations

from pathlib import Path

import chromadb
import numpy as np
from chromadb.api.models.Collection import Collection
from sentence_transformers import SentenceTransformer

from .schemas import Citation

SNIPPET_MAX = 200
DEFAULT_COLLECTION = "futsal_knowledge"


def _mmr_select(
    query_emb: np.ndarray,
    candidate_embs: np.ndarray,
    k: int,
    lambda_mult: float,
) -> list[int]:
    """Maximal Marginal Relevance — k개 청크를 관련성·다양성 균형으로 선택.

    lambda_mult=1.0이면 순수 top-k, 0.0이면 다양성만. 기본 0.6 (관련성 우선 + 다양성 약간).
    """
    n = candidate_embs.shape[0]
    if n == 0:
        return []
    # 코사인 유사도 — 임베딩이 이미 normalize=True로 단위 벡터.
    sim_to_query = candidate_embs @ query_emb
    sim_pairwise = candidate_embs @ candidate_embs.T

    selected: list[int] = []
    remaining = set(range(n))
    while remaining and len(selected) < k:
        if not selected:
            best = int(np.argmax(sim_to_query))
        else:
            best, best_score = -1, -np.inf
            for i in remaining:
                max_sim_to_selected = max(sim_pairwise[i, j] for j in selected)
                mmr = (
                    lambda_mult * sim_to_query[i]
                    - (1.0 - lambda_mult) * max_sim_to_selected
                )
                if mmr > best_score:
                    best, best_score = i, mmr
        selected.append(best)
        remaining.discard(best)
    return selected


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

    def search(
        self,
        query: str,
        k: int = 4,
        *,
        use_mmr: bool = True,
        mmr_fetch_k: int | None = None,
        mmr_lambda: float = 0.6,
    ) -> list[Citation]:
        """top-k 청크 검색.

        use_mmr=True (기본)면 fetch_k=max(k*3, 12)로 먼저 받고 MMR로 k개 선택 —
        관련성·다양성 균형. False면 순수 top-k.
        """
        emb = self._embedder.encode(query)
        if use_mmr:
            fetch = mmr_fetch_k or max(k * 3, 12)
            result = self._collection.query(
                query_embeddings=[emb], n_results=fetch,
                include=["documents", "metadatas", "distances", "embeddings"],
            )
        else:
            result = self._collection.query(query_embeddings=[emb], n_results=k)

        ids = result.get("ids", [[]])[0]
        if not ids:
            return []

        docs = result.get("documents", [[]])[0]
        metas = result.get("metadatas", [[]])[0]
        dists = result.get("distances", [[]])[0]

        if use_mmr:
            cand_embs = np.array(result["embeddings"][0])
            query_emb = np.array(emb)
            chosen = _mmr_select(query_emb, cand_embs, k, mmr_lambda)
            docs = [docs[i] for i in chosen]
            metas = [metas[i] for i in chosen]
            dists = [dists[i] for i in chosen]

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

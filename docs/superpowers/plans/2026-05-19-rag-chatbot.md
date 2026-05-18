# RAG 풋살 지식 챗봇 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 기존 단순 챗봇을 라우터 + RAG 하이브리드로 업그레이드 — 풋살 지식 질문은 ChromaDB 검색 → Claude 증강 응답 + Citation, 개인 조언은 기존 경로 유지. 골든셋 20문항으로 정량 평가.

**Architecture:** Python ai-service에 `/chat/rag`·`/router/classify` 엔드포인트를 추가하고, Spring `AiService`는 키워드 사전 매칭 1차 → 애매하면 Python LLM 분류기로 라우팅. RAG 실패 시 기존 Claude 직접 호출 경로로 우아하게 폴백.

**Tech Stack:** Spring MVC + RestTemplate (Java), FastAPI + LangChain + ChromaDB + sentence-transformers (jhgan/ko-sroberta-multitask) + Claude API (Python), pytest, JUnit, MyBatis(영향 없음).

**Spec:** [docs/superpowers/specs/2026-05-19-rag-chatbot-design.md](../specs/2026-05-19-rag-chatbot-design.md)

---

## File Structure

**Python (`ai-service/`)**

| 경로 | 책임 |
|---|---|
| `rag/__init__.py` | 패키지 마커 |
| `rag/schemas.py` | Pydantic DTO (RagRequest, RagResponse, Citation, ClassifyRequest, ClassifyResponse) |
| `rag/claude_client.py` | Anthropic SDK 래퍼 (테스트 시 mock spec 가능하도록) |
| `rag/retriever.py` | 임베더 + ChromaDB persistent client, top-k 검색 |
| `rag/chain.py` | retriever + claude_client 조합, 시스템 프롬프트 + 청크 컨텍스트로 답변·citation 생성 |
| `rag/router_classifier.py` | Claude Tool Use 기반 KNOWLEDGE/ADVICE 분류 |
| `rag/build_index.py` | CLI: PDF/MD → 청크 → 임베딩 → ChromaDB persist |
| `eval/golden_set.jsonl` | 평가 골든셋 20문항 |
| `eval/run_eval.py` | retrieval@k, faithfulness 측정 + report.md 생성 |
| `tests/test_retriever.py` | Retriever 단위 테스트 (EphemeralClient) |
| `tests/test_chain.py` | RagChain 단위 테스트 (mock claude) |
| `tests/test_router_classifier.py` | RouterClassifier 단위 테스트 |
| `tests/test_main_endpoints.py` | FastAPI TestClient로 /chat/rag, /router/classify |
| `main.py` *(변경)* | 신규 엔드포인트 등록, startup retriever 초기화 |
| `requirements.txt` *(변경)* | langchain, chromadb, sentence-transformers, pypdf, anthropic 추가 |

**Java (`src/main/java/io/github/wizwix/letsfutsal/`)**

| 경로 | 책임 |
|---|---|
| `dto/CitationDTO.java` | `{source, section, page, snippet, score}` |
| `dto/ChatResponseDTO.java` | `{message, mode, citations}` |
| `ai/RagClient.java` | RestTemplate으로 /chat/rag, /router/classify 호출, 폴백 시 예외 던짐 |
| `ai/IntentRouter.java` | 키워드 사전 매칭 → 미스 시 RagClient.classify → 결정 |
| `ai/AiService.java` *(변경)* | `chat()` 진입점에서 라우팅, `chatAdvice()` 메서드 추출 |
| `ai/ChatController.java` *(변경)* | ChatResponseDTO 반환 |
| `test/java/.../ai/IntentRouterTest.java` | 키워드 매칭 + LLM 폴백 동작 |
| `test/java/.../ai/RagClientTest.java` | RestTemplate mock으로 정상/실패 동작 |

**문서**

| 경로 | 책임 |
|---|---|
| `ai-service/README.md` *(변경)* | RAG 빌드/실행/평가 절차 추가 |
| `CLAUDE.md` *(변경)* | "AI 기능 구조" 섹션 갱신 |

---

## Decomposition Principles

- **Python을 먼저** 완성: Spring이 Python에 의존하므로 Python `/chat/rag`, `/router/classify`가 curl로 동작한 뒤 Java를 시작
- **TDD**: 테스트 가능한 유닛(`Retriever`, `RagChain`, `RouterClassifier`, `IntentRouter`, `RagClient`)은 실패 테스트 → 구현 → 통과 → 커밋 순서
- **CLI/설정/데이터 수집** 같은 TDD가 어색한 작업은 명확한 검증 명령으로 대체
- **각 Task 끝에 commit** — `feat:`, `test:`, `docs:`, `chore:` 프리픽스 사용 (저장소 컨벤션과 일치)

---

## Task 0: 풋살 지식 문서 코퍼스 수집

**Files:**
- Create: `ai-service/data/raw/` (디렉토리)
- Modify: `ai-service/.gitignore` (없다면 생성)

- [ ] **Step 1: 작업 디렉토리 생성**

```powershell
New-Item -ItemType Directory -Force ai-service/data/raw | Out-Null
New-Item -ItemType Directory -Force ai-service/data/chroma_db | Out-Null
```

- [ ] **Step 2: ai-service/.gitignore 생성·갱신**

`ai-service/.gitignore` 내용:
```
venv/
__pycache__/
*.pyc
data/raw/
data/chroma_db/
eval/report.md
```

- [ ] **Step 3: 문서 5~7개 수집**

다음 자료를 `data/raw/` 아래에 PDF 또는 마크다운 형식으로 정리한다.

| 파일명 (예시) | 출처 | 형식 |
|---|---|---|
| `fifa_futsal_laws_kr.pdf` | FIFA 풋살 경기규칙 한국어판 (KFA 번역본 또는 한국어 위키 정리본) | PDF |
| `kfa_futsal_rules_2024.pdf` | 대한축구협회 풋살 규정 | PDF |
| `formations_4_0.md` | 4-0 포메이션 설명 (위키·블로그 정리) | Markdown |
| `formations_3_1.md` | 3-1 포메이션 설명 | Markdown |
| `formations_2_2.md` | 2-2 포메이션 설명 | Markdown |
| `tactics_pressing.md` | 압박·카운터 전술 | Markdown |
| `training_basics.md` | 풋살 기초 훈련 가이드 | Markdown |

각 마크다운 파일은 다음 구조로 작성:
```markdown
# [문서 제목]

> Source: [원본 출처 URL 또는 출판물명]
> Section: [규칙 조항 또는 챕터]

## [섹션 제목]

[본문 내용]
```

- [ ] **Step 4: 수집 결과 확인**

```powershell
Get-ChildItem ai-service/data/raw
```
Expected: 최소 5개 파일 존재.

- [ ] **Step 5: Commit (raw 데이터 자체는 gitignore이므로 .gitignore만 커밋)**

```powershell
git add ai-service/.gitignore
git commit -m "chore: ai-service 데이터 디렉토리 gitignore 추가"
```

> **Risk note:** Day 1 오전 안에 5개 미만 확보 시 FIFA 영문판(`fifa_futsal_laws_en.pdf`)을 보충해도 됨. 다국어 임베딩이 아니지만 ko-sroberta-multitask는 영문도 어느 정도 처리 가능.

---

## Task 1: Python 의존성 추가 + rag/ 패키지 골격

**Files:**
- Modify: `ai-service/requirements.txt`
- Create: `ai-service/rag/__init__.py`

- [ ] **Step 1: requirements.txt에 의존성 추가**

`ai-service/requirements.txt`에 아래를 추가:
```
anthropic==0.39.0
langchain==0.3.7
langchain-community==0.3.5
chromadb==0.5.20
sentence-transformers==3.3.1
pypdf==5.1.0
pytest==8.3.3
httpx==0.27.2
```

- [ ] **Step 2: 가상환경 활성화 + 설치**

```powershell
cd ai-service
. venv/Scripts/Activate.ps1
pip install -r requirements.txt
```
Expected: 모든 패키지 설치 완료 (수 분 소요). sentence-transformers는 첫 import 시 모델 가중치 다운로드.

- [ ] **Step 3: rag/__init__.py 생성**

`ai-service/rag/__init__.py`:
```python
"""RAG (Retrieval-Augmented Generation) module for futsal knowledge chatbot."""
```

- [ ] **Step 4: 패키지 import 검증**

```powershell
python -c "import rag; print(rag.__doc__)"
```
Expected: `RAG (Retrieval-Augmented Generation) module for futsal knowledge chatbot.`

- [ ] **Step 5: Commit**

```powershell
git add ai-service/requirements.txt ai-service/rag/__init__.py
git commit -m "chore: RAG 의존성 추가 및 rag 패키지 골격 생성"
```

---

## Task 2: Pydantic 스키마 정의

**Files:**
- Create: `ai-service/rag/schemas.py`
- Create: `ai-service/tests/__init__.py` (없다면)
- Create: `ai-service/tests/test_schemas.py`

- [ ] **Step 1: 실패 테스트 작성**

`ai-service/tests/test_schemas.py`:
```python
from rag.schemas import Citation, RagRequest, RagResponse, ClassifyRequest, ClassifyResponse, UserContext


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
```

- [ ] **Step 2: 실패 확인**

```powershell
cd ai-service
pytest tests/test_schemas.py -v
```
Expected: FAIL — `ModuleNotFoundError: No module named 'rag.schemas'`

- [ ] **Step 3: 스키마 구현**

`ai-service/rag/schemas.py`:
```python
from typing import Literal
from pydantic import BaseModel, Field


class UserContext(BaseModel):
    nickname: str | None = None
    grade: str | None = None
    preferred_position: str | None = None


class Citation(BaseModel):
    source: str
    section: str
    page: int | None = None
    snippet: str
    score: float


class RagRequest(BaseModel):
    user_message: str = Field(min_length=1, max_length=500)
    user_context: UserContext | None = None


class RagResponse(BaseModel):
    answer: str
    citations: list[Citation] = []
    retrieved_chunks: int = 0


class ClassifyRequest(BaseModel):
    user_message: str = Field(min_length=1, max_length=500)


class ClassifyResponse(BaseModel):
    intent: Literal["KNOWLEDGE", "ADVICE"]
    confidence: float = Field(ge=0.0, le=1.0)
```

- [ ] **Step 4: 통과 확인**

```powershell
pytest tests/test_schemas.py -v
```
Expected: 5 passed.

- [ ] **Step 5: Commit**

```powershell
git add ai-service/rag/schemas.py ai-service/tests/test_schemas.py
git commit -m "feat(rag): Pydantic 스키마 정의 (Citation, RagRequest/Response, Classify)"
```

---

## Task 3: Claude SDK 래퍼

**Files:**
- Create: `ai-service/rag/claude_client.py`
- Create: `ai-service/tests/test_claude_client.py`

이 래퍼는 Anthropic SDK를 얇게 감싸 단위 테스트에서 `Mock(spec=ClaudeClient)`로 치환할 수 있게 한다.

- [ ] **Step 1: 실패 테스트 작성**

`ai-service/tests/test_claude_client.py`:
```python
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
    args, kwargs = client_instance.messages.create.call_args
    assert kwargs["model"] == "claude-sonnet-4-6"
    assert kwargs["system"] == "sys"
    assert kwargs["max_tokens"] == 2048


def test_chat_with_tools_passes_tools_param():
    fake_response = MagicMock()
    fake_response.content = [MagicMock(type="tool_use", input={"intent": "KNOWLEDGE", "confidence": 0.9})]
    with patch("rag.claude_client.anthropic.Anthropic") as mock_anthropic_cls:
        client_instance = mock_anthropic_cls.return_value
        client_instance.messages.create.return_value = fake_response

        client = ClaudeClient(api_key="sk-test")
        result = client.chat_with_tool(system="sys", user="msg", tool={"name": "classify", "input_schema": {}})

    assert result == {"intent": "KNOWLEDGE", "confidence": 0.9}
```

- [ ] **Step 2: 실패 확인**

```powershell
pytest tests/test_claude_client.py -v
```
Expected: FAIL — module 없음.

- [ ] **Step 3: 구현**

`ai-service/rag/claude_client.py`:
```python
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

    def chat_with_tool(self, system: str, user: str, tool: dict, max_tokens: int = 512) -> dict:
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
```

- [ ] **Step 4: 통과 확인**

```powershell
pytest tests/test_claude_client.py -v
```
Expected: 2 passed.

- [ ] **Step 5: Commit**

```powershell
git add ai-service/rag/claude_client.py ai-service/tests/test_claude_client.py
git commit -m "feat(rag): Claude SDK 래퍼 추가 (chat, chat_with_tool)"
```

---

## Task 4: Retriever (ChromaDB persistent + sentence-transformers)

**Files:**
- Create: `ai-service/rag/retriever.py`
- Create: `ai-service/tests/test_retriever.py`

- [ ] **Step 1: 실패 테스트 작성**

`ai-service/tests/test_retriever.py`:
```python
import pytest
import chromadb
from unittest.mock import MagicMock
from rag.retriever import Retriever


@pytest.fixture
def in_memory_collection():
    client = chromadb.EphemeralClient()
    coll = client.create_collection(name="test_futsal", metadata={"hnsw:space": "cosine"})
    return coll


@pytest.fixture
def fake_embedder():
    # 입력 문자열 길이에 따라 차이가 나는 결정적 가짜 임베딩
    class FakeEmbedder:
        def encode(self, text: str) -> list[float]:
            return [float(len(text) % 7), float(sum(map(ord, text)) % 13), 1.0]

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
```

- [ ] **Step 2: 실패 확인**

```powershell
pytest tests/test_retriever.py -v
```
Expected: FAIL — module 없음.

- [ ] **Step 3: 구현**

`ai-service/rag/retriever.py`:
```python
from __future__ import annotations
from pathlib import Path
import chromadb
from chromadb.api.models.Collection import Collection
from sentence_transformers import SentenceTransformer

from .schemas import Citation


SNIPPET_MAX = 200


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


def open_persistent_retriever(persist_dir: Path | str, collection_name: str = "futsal_knowledge") -> Retriever:
    """운영용 헬퍼: 디스크에 저장된 ChromaDB와 실제 임베더 로드."""
    path = Path(persist_dir)
    if not path.exists():
        raise RuntimeError(f"ChromaDB persist 디렉토리가 없음: {path}. build_index.py를 먼저 실행하세요.")
    client = chromadb.PersistentClient(path=str(path))
    collection = client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"},
    )
    embedder = SentenceTransformerEmbedder()
    return Retriever(collection=collection, embedder=embedder)
```

- [ ] **Step 4: 통과 확인**

```powershell
pytest tests/test_retriever.py -v
```
Expected: 3 passed.

- [ ] **Step 5: Commit**

```powershell
git add ai-service/rag/retriever.py ai-service/tests/test_retriever.py
git commit -m "feat(rag): Retriever 구현 (ChromaDB + sentence-transformers, 단위 테스트 포함)"
```

---

## Task 5: build_index.py CLI

**Files:**
- Create: `ai-service/rag/build_index.py`

이 단계는 외부 데이터(원본 문서)에 의존하므로 자동 테스트는 어렵다. CLI 동작과 산출물(ChromaDB 디렉토리)을 수동 검증한다.

- [ ] **Step 1: build_index.py 작성**

`ai-service/rag/build_index.py`:
```python
"""풋살 지식 문서를 청크 분할·임베딩하여 ChromaDB에 영구 저장한다.

사용법:
    python -m rag.build_index --raw data/raw --out data/chroma_db
"""
from __future__ import annotations
import argparse
import uuid
from pathlib import Path

import chromadb
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader

from .retriever import SentenceTransformerEmbedder


COLLECTION_NAME = "futsal_knowledge"
CHUNK_SIZE = 500
CHUNK_OVERLAP = 80
SEPARATORS = ["\n\n", "\n", ". ", " "]


def load_pdf(path: Path) -> list[tuple[str, int]]:
    """returns list of (text, page_number)."""
    reader = PdfReader(str(path))
    out: list[tuple[str, int]] = []
    for i, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        if text.strip():
            out.append((text, i))
    return out


def load_markdown(path: Path) -> list[tuple[str, int]]:
    text = path.read_text(encoding="utf-8")
    # Markdown은 페이지 번호 없음 → None 대신 0
    return [(text, 0)] if text.strip() else []


def derive_metadata(path: Path) -> dict:
    stem = path.stem.replace("_", " ")
    return {"source": stem, "section": ""}


def build(raw_dir: Path, persist_dir: Path) -> int:
    persist_dir.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(persist_dir))
    # 기존 collection 있으면 비워서 멱등 재실행 가능
    try:
        client.delete_collection(name=COLLECTION_NAME)
    except Exception:
        pass
    collection = client.create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=SEPARATORS,
    )
    embedder = SentenceTransformerEmbedder()

    total_chunks = 0
    for path in sorted(raw_dir.glob("*")):
        if path.suffix.lower() == ".pdf":
            pages = load_pdf(path)
        elif path.suffix.lower() in (".md", ".markdown"):
            pages = load_markdown(path)
        else:
            print(f"[skip] {path.name} (지원하지 않는 형식)")
            continue

        base_meta = derive_metadata(path)
        for text, page_no in pages:
            chunks = splitter.split_text(text)
            for chunk in chunks:
                if not chunk.strip():
                    continue
                meta = {**base_meta, "page": page_no, "lang": "ko"}
                collection.add(
                    ids=[str(uuid.uuid4())],
                    documents=[chunk],
                    metadatas=[meta],
                    embeddings=[embedder.encode(chunk)],
                )
                total_chunks += 1
        print(f"[ok] {path.name}: {len(pages)}페이지 처리")

    print(f"\n총 {total_chunks}개 청크 인덱싱 완료. 저장 위치: {persist_dir}")
    return total_chunks


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw", default="data/raw", type=Path)
    parser.add_argument("--out", default="data/chroma_db", type=Path)
    args = parser.parse_args()

    count = build(args.raw, args.out)
    if count == 0:
        raise SystemExit("0개 청크 — data/raw에 유효한 문서가 있는지 확인하세요.")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: CLI 실행**

```powershell
cd ai-service
. venv/Scripts/Activate.ps1
$env:PYTHONIOENCODING="utf-8"
python -m rag.build_index --raw data/raw --out data/chroma_db
```
Expected: 각 파일별 `[ok]` 로그 + `총 N개 청크 인덱싱 완료` 마지막 줄. N은 문서 수에 따라 50~500 사이.

- [ ] **Step 3: chroma.sqlite3 생성 확인**

```powershell
Test-Path ai-service/data/chroma_db/chroma.sqlite3
```
Expected: `True`

- [ ] **Step 4: 검색 정상 동작 smoke test**

```powershell
python -c "from rag.retriever import open_persistent_retriever; r = open_persistent_retriever('data/chroma_db'); cits = r.search('오프사이드'); [print(c.source, c.score, c.snippet[:60]) for c in cits]"
```
Expected: 최소 1개 이상의 citation 출력.

- [ ] **Step 5: Commit**

```powershell
git add ai-service/rag/build_index.py
git commit -m "feat(rag): build_index CLI 추가 (PDF/Markdown → ChromaDB persist)"
```

---

## Task 6: RagChain (retriever + claude_client 조합)

**Files:**
- Create: `ai-service/rag/chain.py`
- Create: `ai-service/tests/test_chain.py`

- [ ] **Step 1: 실패 테스트 작성**

`ai-service/tests/test_chain.py`:
```python
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

    # 시스템 프롬프트에 청크가 들어갔는지 확인
    system_arg = claude.chat.call_args.kwargs["system"]
    assert "There is no offside." in system_arg
    assert "Law 11" in system_arg


def test_chain_empty_retrieval_falls_back():
    retriever = MagicMock()
    retriever.search.return_value = []
    claude = MagicMock()
    claude.chat.return_value = "관련 문서를 찾지 못했습니다."

    chain = RagChain(retriever=retriever, claude_client=claude)
    resp = chain.answer("이상한 질문", user_context=None)

    assert resp.retrieved_chunks == 0
    assert resp.citations == []
    # 청크 없을 때도 Claude는 호출됨 (일반 답변)
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
```

- [ ] **Step 2: 실패 확인**

```powershell
pytest tests/test_chain.py -v
```
Expected: FAIL — module 없음.

- [ ] **Step 3: 구현**

`ai-service/rag/chain.py`:
```python
from __future__ import annotations

from .claude_client import ClaudeClient
from .retriever import Retriever
from .schemas import Citation, RagResponse, UserContext


def _format_context_block(citations: list[Citation]) -> str:
    if not citations:
        return "(검색된 풋살 지식 문서가 없습니다. 일반 지식으로 정중하게 답하되, 확실하지 않은 내용은 추측하지 마세요.)"
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
        "정확하고 간결하게 답하세요. 참고 문서에 없는 내용은 추측하지 말고 모른다고 하세요. "
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

    def answer(self, query: str, user_context: UserContext | None) -> RagResponse:
        citations = self._retriever.search(query, k=self._top_k)
        system_prompt = build_system_prompt(citations, user_context)
        answer_text = self._claude.chat(system=system_prompt, user=query)
        return RagResponse(
            answer=answer_text,
            citations=citations,
            retrieved_chunks=len(citations),
        )
```

- [ ] **Step 4: 통과 확인**

```powershell
pytest tests/test_chain.py -v
```
Expected: 3 passed.

- [ ] **Step 5: Commit**

```powershell
git add ai-service/rag/chain.py ai-service/tests/test_chain.py
git commit -m "feat(rag): RagChain 구현 (시스템 프롬프트 + Claude + citation)"
```

---

## Task 7: RouterClassifier (Claude Tool Use)

**Files:**
- Create: `ai-service/rag/router_classifier.py`
- Create: `ai-service/tests/test_router_classifier.py`

- [ ] **Step 1: 실패 테스트 작성**

`ai-service/tests/test_router_classifier.py`:
```python
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
```

- [ ] **Step 2: 실패 확인**

```powershell
pytest tests/test_router_classifier.py -v
```
Expected: FAIL — module 없음.

- [ ] **Step 3: 구현**

`ai-service/rag/router_classifier.py`:
```python
from __future__ import annotations

from .claude_client import ClaudeClient
from .schemas import ClassifyResponse


CLASSIFY_TOOL = {
    "name": "classify_intent",
    "description": "사용자 메시지의 의도를 분류한다. KNOWLEDGE는 풋살 규칙·전술·훈련 등 사실 기반 지식 질문, ADVICE는 사용자의 개인 상황·감정·고민 또는 추천성 질문.",
    "input_schema": {
        "type": "object",
        "properties": {
            "intent": {
                "type": "string",
                "enum": ["KNOWLEDGE", "ADVICE"],
                "description": "분류된 의도 (KNOWLEDGE 또는 ADVICE)",
            },
            "confidence": {
                "type": "number",
                "description": "0.0~1.0 범위 신뢰도",
            },
        },
        "required": ["intent", "confidence"],
    },
}


SYSTEM_PROMPT = (
    "당신은 풋살 챗봇의 의도 분류기입니다. 사용자 메시지가 (a) 풋살 규칙·전술·훈련 등 "
    "사실 기반 지식 질문(KNOWLEDGE)인지, (b) 사용자의 팀 상황·고민·개인 추천(ADVICE)인지 "
    "이분 분류한 뒤 classify_intent 도구로 결과를 반환하세요."
)


class RouterClassifier:
    def __init__(self, claude_client: ClaudeClient):
        self._claude = claude_client

    def classify(self, user_message: str) -> ClassifyResponse:
        result = self._claude.chat_with_tool(
            system=SYSTEM_PROMPT,
            user=user_message,
            tool=CLASSIFY_TOOL,
        )
        return ClassifyResponse(**result)
```

- [ ] **Step 4: 통과 확인**

```powershell
pytest tests/test_router_classifier.py -v
```
Expected: 3 passed.

- [ ] **Step 5: Commit**

```powershell
git add ai-service/rag/router_classifier.py ai-service/tests/test_router_classifier.py
git commit -m "feat(rag): RouterClassifier 구현 (Claude Tool Use 기반 의도 분류)"
```

---

## Task 8: FastAPI 엔드포인트 통합 (/chat/rag, /router/classify)

**Files:**
- Modify: `ai-service/main.py`
- Create: `ai-service/tests/test_main_endpoints.py`

- [ ] **Step 1: 실패 테스트 작성**

`ai-service/tests/test_main_endpoints.py`:
```python
import importlib
import pytest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient


@pytest.fixture
def test_client(tmp_path, monkeypatch):
    """RAG_CHROMA_DIR을 존재하지 않는 경로로 가리켜 lifespan의 RAG 초기화 분기를 건너뛰고,
    rag_chain·router_classifier 모듈 globals에 mock 객체를 직접 주입한다."""
    monkeypatch.setenv("RAG_CHROMA_DIR", str(tmp_path / "no_such"))
    import main as _main
    importlib.reload(_main)  # 모듈 캐시 리셋으로 RAG_CHROMA_DIR 반영

    from rag.schemas import RagResponse, Citation, ClassifyResponse
    _main.rag_chain = MagicMock()
    _main.router_classifier = MagicMock()
    _main.rag_chain.answer.return_value = RagResponse(
        answer="default-answer",
        citations=[Citation(source="S", section="Sec", page=1, snippet="snip", score=0.8)],
        retrieved_chunks=1,
    )
    _main.router_classifier.classify.return_value = ClassifyResponse(
        intent="KNOWLEDGE", confidence=0.9
    )

    with TestClient(_main.app) as client:
        yield client, _main


def test_chat_rag_returns_answer_and_citations(test_client):
    client, _ = test_client
    resp = client.post("/chat/rag", json={"user_message": "오프사이드?"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["answer"] == "default-answer"
    assert body["retrieved_chunks"] >= 1
    assert isinstance(body["citations"], list)


def test_router_classify_returns_intent(test_client):
    client, m = test_client
    from rag.schemas import ClassifyResponse
    m.router_classifier.classify.return_value = ClassifyResponse(
        intent="ADVICE", confidence=0.7
    )
    resp = client.post("/router/classify", json={"user_message": "팀이 자꾸 져요"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["intent"] == "ADVICE"
    assert 0 <= body["confidence"] <= 1


def test_chat_rag_validates_empty_message(test_client):
    client, _ = test_client
    resp = client.post("/chat/rag", json={"user_message": ""})
    assert resp.status_code == 422


def test_health_still_works(test_client):
    client, _ = test_client
    resp = client.get("/health")
    assert resp.status_code == 200
```

- [ ] **Step 2: 실패 확인**

```powershell
pytest tests/test_main_endpoints.py -v
```
Expected: FAIL — main에 RagChain 등 import 없음.

- [ ] **Step 3: main.py 수정**

`ai-service/main.py` (전체 교체):
```python
from contextlib import asynccontextmanager
import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from data_generator import generate_matches
from recommender import Recommender

from rag.chain import RagChain
from rag.claude_client import ClaudeClient
from rag.retriever import open_persistent_retriever
from rag.router_classifier import RouterClassifier
from rag.schemas import (
    ClassifyRequest,
    ClassifyResponse,
    RagRequest,
    RagResponse,
)

recommender: Recommender | None = None
rag_chain: RagChain | None = None
router_classifier: RouterClassifier | None = None

CHROMA_DIR = Path(os.environ.get("RAG_CHROMA_DIR", "data/chroma_db"))


@asynccontextmanager
async def lifespan(app: FastAPI):
    global recommender, rag_chain, router_classifier

    matches = generate_matches(300)
    recommender = Recommender(matches)

    # RAG 초기화: persist 디렉토리 존재 시에만 활성화. 없으면 RAG는 비활성(엔드포인트가 503).
    if CHROMA_DIR.exists():
        retriever = open_persistent_retriever(CHROMA_DIR)
        claude = ClaudeClient()
        rag_chain = RagChain(retriever=retriever, claude_client=claude)
        router_classifier = RouterClassifier(claude_client=claude)
    yield


app = FastAPI(title="letsfutsal AI Service", lifespan=lifespan)


from pydantic import BaseModel


class UserProfile(BaseModel):
    userId: int
    preferredPosition: str
    gender: str
    grade: int


class RecommendResponse(BaseModel):
    matchIds: list[int]


@app.get("/health")
def health():
    return {
        "status": "ok",
        "rag_enabled": rag_chain is not None,
    }


@app.post("/recommend/matches", response_model=RecommendResponse)
def recommend_matches(user: UserProfile):
    if recommender is None:
        return RecommendResponse(matchIds=[])
    ids = recommender.recommend(user.preferredPosition, user.gender, user.grade)
    return RecommendResponse(matchIds=ids)


@app.post("/chat/rag", response_model=RagResponse)
def chat_rag(req: RagRequest):
    if rag_chain is None:
        raise HTTPException(status_code=503, detail="RAG가 초기화되지 않았습니다. build_index를 먼저 실행하세요.")
    return rag_chain.answer(req.user_message, user_context=req.user_context)


@app.post("/router/classify", response_model=ClassifyResponse)
def router_classify(req: ClassifyRequest):
    if router_classifier is None:
        raise HTTPException(status_code=503, detail="라우터 분류기가 초기화되지 않았습니다.")
    return router_classifier.classify(req.user_message)
```

- [ ] **Step 4: 통과 확인**

```powershell
pytest tests/test_main_endpoints.py -v
```
Expected: 4 passed.

- [ ] **Step 5: 전체 Python 테스트 통과 확인**

```powershell
pytest -v
```
Expected: 모든 테스트 passed (schemas 5 + claude_client 2 + retriever 3 + chain 3 + router_classifier 3 + endpoints 4 = 20 passed).

- [ ] **Step 6: 서버 manual smoke test**

```powershell
# 별도 터미널에서 서버 실행 (env: CLAUDE_API_KEY 필요)
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

다른 터미널에서:
```powershell
curl http://localhost:8000/health
curl -X POST http://localhost:8000/chat/rag `
     -H "Content-Type: application/json" `
     -d '{\"user_message\": \"오프사이드 규칙이 뭐야?\"}'
```
Expected: `/health`에 `rag_enabled: true`, `/chat/rag`에 `answer` + `citations` 배열 반환.

- [ ] **Step 7: Commit**

```powershell
git add ai-service/main.py ai-service/tests/test_main_endpoints.py
git commit -m "feat(rag): FastAPI /chat/rag, /router/classify 엔드포인트 추가"
```

---

## Task 9: Java DTO — CitationDTO, ChatResponseDTO

**Files:**
- Create: `src/main/java/io/github/wizwix/letsfutsal/dto/CitationDTO.java`
- Create: `src/main/java/io/github/wizwix/letsfutsal/dto/ChatResponseDTO.java`

이 DTO들은 단순 데이터 보관용이므로 별도 테스트 없이 다음 Task의 RagClient 테스트에서 자연스럽게 검증된다.

- [ ] **Step 1: CitationDTO 생성**

`src/main/java/io/github/wizwix/letsfutsal/dto/CitationDTO.java`:
```java
package io.github.wizwix.letsfutsal.dto;

import com.fasterxml.jackson.annotation.JsonProperty;

public class CitationDTO {
  private String source;
  private String section;
  private Integer page;
  private String snippet;
  private Double score;

  public String getSource() { return source; }
  public void setSource(String source) { this.source = source; }

  public String getSection() { return section; }
  public void setSection(String section) { this.section = section; }

  public Integer getPage() { return page; }
  public void setPage(Integer page) { this.page = page; }

  public String getSnippet() { return snippet; }
  public void setSnippet(String snippet) { this.snippet = snippet; }

  public Double getScore() { return score; }
  public void setScore(Double score) { this.score = score; }
}
```

- [ ] **Step 2: ChatResponseDTO 생성**

`src/main/java/io/github/wizwix/letsfutsal/dto/ChatResponseDTO.java`:
```java
package io.github.wizwix.letsfutsal.dto;

import java.util.List;

public class ChatResponseDTO {
  public enum Mode { RAG, ADVICE }

  private String message;
  private Mode mode;
  private List<CitationDTO> citations;

  public ChatResponseDTO() {}

  public ChatResponseDTO(String message, Mode mode, List<CitationDTO> citations) {
    this.message = message;
    this.mode = mode;
    this.citations = citations;
  }

  public String getMessage() { return message; }
  public void setMessage(String message) { this.message = message; }

  public Mode getMode() { return mode; }
  public void setMode(Mode mode) { this.mode = mode; }

  public List<CitationDTO> getCitations() { return citations; }
  public void setCitations(List<CitationDTO> citations) { this.citations = citations; }
}
```

- [ ] **Step 3: Maven 컴파일 확인**

```powershell
mvn -q compile
```
Expected: BUILD SUCCESS.

- [ ] **Step 4: Commit**

```powershell
git add src/main/java/io/github/wizwix/letsfutsal/dto/CitationDTO.java src/main/java/io/github/wizwix/letsfutsal/dto/ChatResponseDTO.java
git commit -m "feat(ai): CitationDTO, ChatResponseDTO 추가 (RAG 응답 스키마)"
```

---

## Task 10: RagClient (Spring → Python REST)

**Files:**
- Create: `src/main/java/io/github/wizwix/letsfutsal/ai/RagClient.java`
- Create: `src/test/java/io/github/wizwix/letsfutsal/ai/RagClientTest.java`

`RecommendService`와 동일하게 `RestTemplate` 빈을 주입받는다. (이미 `RootConfig`에 등록되어 있음.)

- [ ] **Step 1: 실패 테스트 작성**

`src/test/java/io/github/wizwix/letsfutsal/ai/RagClientTest.java`:
```java
package io.github.wizwix.letsfutsal.ai;

import com.fasterxml.jackson.databind.ObjectMapper;
import io.github.wizwix.letsfutsal.dto.UserDTO;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.http.HttpMethod;
import org.springframework.http.MediaType;
import org.springframework.test.web.client.MockRestServiceServer;
import org.springframework.web.client.RestTemplate;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.springframework.test.web.client.match.MockRestRequestMatchers.method;
import static org.springframework.test.web.client.match.MockRestRequestMatchers.requestTo;
import static org.springframework.test.web.client.response.MockRestResponseCreators.withServerError;
import static org.springframework.test.web.client.response.MockRestResponseCreators.withSuccess;

class RagClientTest {

  private RestTemplate restTemplate;
  private MockRestServiceServer server;
  private RagClient client;
  private UserDTO user;

  @BeforeEach
  void setUp() {
    restTemplate = new RestTemplate();
    server = MockRestServiceServer.createServer(restTemplate);
    client = new RagClient(restTemplate, new ObjectMapper(), "http://fake-ai:8000");
    user = new UserDTO();
    user.setNickname("수진");
    user.setGrade(1);
  }

  @Test
  void askRag_parsesAnswerAndCitations() {
    String json = """
        {
          "answer": "풋살에 오프사이드 없음",
          "citations": [
            {"source":"FIFA","section":"Law 11","page":14,"snippet":"no offside","score":0.9}
          ],
          "retrieved_chunks": 1
        }
        """;
    server.expect(requestTo("http://fake-ai:8000/chat/rag"))
        .andExpect(method(HttpMethod.POST))
        .andRespond(withSuccess(json, MediaType.APPLICATION_JSON));

    RagClient.RagResult result = client.askRag(user, "오프사이드?");

    assertThat(result.answer()).isEqualTo("풋살에 오프사이드 없음");
    assertThat(result.citations()).hasSize(1);
    assertThat(result.citations().get(0).getSource()).isEqualTo("FIFA");
    assertThat(result.citations().get(0).getPage()).isEqualTo(14);
    server.verify();
  }

  @Test
  void askRag_throwsOnServerError() {
    server.expect(requestTo("http://fake-ai:8000/chat/rag"))
        .andRespond(withServerError());

    assertThatThrownBy(() -> client.askRag(user, "질문"))
        .isInstanceOf(RagClient.RagUnavailableException.class);
  }

  @Test
  void classify_returnsIntent() {
    String json = "{\"intent\":\"KNOWLEDGE\",\"confidence\":0.92}";
    server.expect(requestTo("http://fake-ai:8000/router/classify"))
        .andExpect(method(HttpMethod.POST))
        .andRespond(withSuccess(json, MediaType.APPLICATION_JSON));

    RagClient.Intent intent = client.classify("4-0 포메이션?");

    assertThat(intent).isEqualTo(RagClient.Intent.KNOWLEDGE);
    server.verify();
  }

  @Test
  void classify_throwsOnServerError() {
    server.expect(requestTo("http://fake-ai:8000/router/classify"))
        .andRespond(withServerError());

    assertThatThrownBy(() -> client.classify("질문"))
        .isInstanceOf(RagClient.RagUnavailableException.class);
  }
}
```

- [ ] **Step 2: 실패 확인**

```powershell
mvn -q -Dtest=RagClientTest test
```
Expected: FAIL — RagClient 클래스 없음 (compile error).

- [ ] **Step 3: RagClient 구현**

`src/main/java/io/github/wizwix/letsfutsal/ai/RagClient.java`:
```java
package io.github.wizwix.letsfutsal.ai;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import io.github.wizwix.letsfutsal.dto.CitationDTO;
import io.github.wizwix.letsfutsal.dto.UserDTO;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestTemplate;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

@Component
public class RagClient {
  private static final Logger log = LoggerFactory.getLogger(RagClient.class);

  public enum Intent { KNOWLEDGE, ADVICE }

  public static class RagUnavailableException extends RuntimeException {
    public RagUnavailableException(String msg, Throwable cause) { super(msg, cause); }
  }

  public record RagResult(String answer, List<CitationDTO> citations) {}

  private final RestTemplate restTemplate;
  private final ObjectMapper objectMapper;
  private final String baseUrl;

  public RagClient(RestTemplate restTemplate, ObjectMapper objectMapper) {
    this(restTemplate, objectMapper,
        System.getenv().getOrDefault("AI_SERVICE_URL", "http://localhost:8000"));
  }

  // 테스트용 명시 baseUrl 주입 생성자
  public RagClient(RestTemplate restTemplate, ObjectMapper objectMapper, String baseUrl) {
    this.restTemplate = restTemplate;
    this.objectMapper = objectMapper;
    this.baseUrl = baseUrl;
  }

  public RagResult askRag(UserDTO user, String message) {
    Map<String, Object> body = new HashMap<>();
    body.put("user_message", message);
    if (user != null) {
      Map<String, Object> ctx = new HashMap<>();
      ctx.put("nickname", user.getNickname());
      ctx.put("grade", String.valueOf(user.getGrade()));
      ctx.put("preferred_position",
          user.getPreferredPosition() != null ? user.getPreferredPosition().toString() : null);
      body.put("user_context", ctx);
    }

    try {
      String json = restTemplate.postForObject(baseUrl + "/chat/rag", body, String.class);
      JsonNode root = objectMapper.readTree(json);
      String answer = root.path("answer").asText("");
      List<CitationDTO> citations = parseCitations(root.path("citations"));
      return new RagResult(answer, citations);
    } catch (Exception e) {
      log.warn("RAG 호출 실패: {}", e.getMessage());
      throw new RagUnavailableException("RAG 서비스 호출 실패", e);
    }
  }

  public Intent classify(String message) {
    Map<String, Object> body = Map.of("user_message", message);
    try {
      String json = restTemplate.postForObject(baseUrl + "/router/classify", body, String.class);
      JsonNode root = objectMapper.readTree(json);
      String intent = root.path("intent").asText("ADVICE");
      return "KNOWLEDGE".equals(intent) ? Intent.KNOWLEDGE : Intent.ADVICE;
    } catch (Exception e) {
      log.warn("Router classify 호출 실패: {}", e.getMessage());
      throw new RagUnavailableException("라우터 분류기 호출 실패", e);
    }
  }

  private List<CitationDTO> parseCitations(JsonNode arr) {
    List<CitationDTO> out = new ArrayList<>();
    if (arr == null || !arr.isArray()) return out;
    for (JsonNode n : arr) {
      CitationDTO c = new CitationDTO();
      c.setSource(n.path("source").asText(""));
      c.setSection(n.path("section").asText(""));
      if (n.hasNonNull("page")) c.setPage(n.get("page").asInt());
      c.setSnippet(n.path("snippet").asText(""));
      c.setScore(n.path("score").asDouble(0.0));
      out.add(c);
    }
    return out;
  }
}
```

- [ ] **Step 4: 통과 확인**

```powershell
mvn -q -Dtest=RagClientTest test
```
Expected: Tests run: 4, Failures: 0.

- [ ] **Step 5: Commit**

```powershell
git add src/main/java/io/github/wizwix/letsfutsal/ai/RagClient.java src/test/java/io/github/wizwix/letsfutsal/ai/RagClientTest.java
git commit -m "feat(ai): RagClient 추가 (Python /chat/rag, /router/classify 호출)"
```

---

## Task 11: IntentRouter (키워드 + LLM 폴백)

**Files:**
- Create: `src/main/java/io/github/wizwix/letsfutsal/ai/IntentRouter.java`
- Create: `src/test/java/io/github/wizwix/letsfutsal/ai/IntentRouterTest.java`

- [ ] **Step 1: 실패 테스트 작성**

`src/test/java/io/github/wizwix/letsfutsal/ai/IntentRouterTest.java`:
```java
package io.github.wizwix.letsfutsal.ai;

import org.junit.jupiter.api.Test;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.Mockito.*;

class IntentRouterTest {

  @Test
  void keywordMatch_routesToKnowledge_directly() {
    RagClient rag = mock(RagClient.class);
    IntentRouter router = new IntentRouter(rag);

    IntentRouter.Decision d = router.route("오프사이드 규칙이 뭐야?");

    assertThat(d.intent()).isEqualTo(RagClient.Intent.KNOWLEDGE);
    assertThat(d.keywordHit()).isTrue();
    verifyNoInteractions(rag);
  }

  @Test
  void keywordMiss_callsClassifier_andReturnsItsAnswer() {
    RagClient rag = mock(RagClient.class);
    when(rag.classify(anyString())).thenReturn(RagClient.Intent.ADVICE);
    IntentRouter router = new IntentRouter(rag);

    IntentRouter.Decision d = router.route("우리 팀이 자꾸 지는데");

    assertThat(d.intent()).isEqualTo(RagClient.Intent.ADVICE);
    assertThat(d.keywordHit()).isFalse();
    verify(rag).classify("우리 팀이 자꾸 지는데");
  }

  @Test
  void classifier_failure_fallsBackToAdvice() {
    RagClient rag = mock(RagClient.class);
    when(rag.classify(anyString())).thenThrow(new RagClient.RagUnavailableException("down", null));
    IntentRouter router = new IntentRouter(rag);

    IntentRouter.Decision d = router.route("애매한 질문");

    assertThat(d.intent()).isEqualTo(RagClient.Intent.ADVICE);
    assertThat(d.keywordHit()).isFalse();
  }

  @Test
  void multipleKeywords_match() {
    RagClient rag = mock(RagClient.class);
    when(rag.classify(anyString())).thenReturn(RagClient.Intent.ADVICE);
    IntentRouter router = new IntentRouter(rag);

    assertThat(router.route("4-0 포메이션 알려줘").intent()).isEqualTo(RagClient.Intent.KNOWLEDGE);
    assertThat(router.route("드리블 훈련법은?").intent()).isEqualTo(RagClient.Intent.KNOWLEDGE);
    // "오늘 날씨 어때"는 모든 키워드 미스 → 분류기 호출 → 위 stub으로 ADVICE 반환
    assertThat(router.route("오늘 날씨 어때").intent()).isEqualTo(RagClient.Intent.ADVICE);
  }
}
```

- [ ] **Step 2: 실패 확인**

```powershell
mvn -q -Dtest=IntentRouterTest test
```
Expected: FAIL — IntentRouter 없음.

- [ ] **Step 3: IntentRouter 구현**

`src/main/java/io/github/wizwix/letsfutsal/ai/IntentRouter.java`:
```java
package io.github.wizwix.letsfutsal.ai;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Component;

import java.util.Set;

@Component
public class IntentRouter {
  private static final Logger log = LoggerFactory.getLogger(IntentRouter.class);

  private static final Set<String> KNOWLEDGE_KEYWORDS = Set.of(
      "규칙", "반칙", "오프사이드", "파울", "프리킥", "페널티킥", "킥인", "코너킥",
      "포메이션", "4-0", "3-1", "2-2", "전술", "압박", "카운터",
      "드리블", "패스", "슈팅", "트래핑", "훈련", "연습"
  );

  public record Decision(RagClient.Intent intent, boolean keywordHit) {}

  private final RagClient ragClient;

  public IntentRouter(RagClient ragClient) {
    this.ragClient = ragClient;
  }

  public Decision route(String message) {
    if (message == null) {
      return new Decision(RagClient.Intent.ADVICE, false);
    }
    String normalized = message.toLowerCase();
    for (String kw : KNOWLEDGE_KEYWORDS) {
      if (normalized.contains(kw.toLowerCase())) {
        log.info("Routing: keyword HIT '{}' → KNOWLEDGE", kw);
        return new Decision(RagClient.Intent.KNOWLEDGE, true);
      }
    }
    try {
      RagClient.Intent intent = ragClient.classify(message);
      log.info("Routing: keyword MISS, LLM classifier → {}", intent);
      return new Decision(intent, false);
    } catch (RagClient.RagUnavailableException e) {
      log.warn("Routing: classifier 실패, ADVICE로 폴백");
      return new Decision(RagClient.Intent.ADVICE, false);
    }
  }
}
```

- [ ] **Step 4: 통과 확인**

```powershell
mvn -q -Dtest=IntentRouterTest test
```
Expected: Tests run: 4, Failures: 0.

- [ ] **Step 5: Commit**

```powershell
git add src/main/java/io/github/wizwix/letsfutsal/ai/IntentRouter.java src/test/java/io/github/wizwix/letsfutsal/ai/IntentRouterTest.java
git commit -m "feat(ai): IntentRouter 추가 (키워드 사전 + LLM 폴백)"
```

---

## Task 12: AiService 리팩터 (라우팅 진입점)

**Files:**
- Modify: `src/main/java/io/github/wizwix/letsfutsal/ai/AiService.java`

기존 `chat()` 메서드를 라우팅 진입점으로 바꾸고, 기존 Claude 직접 호출 로직은 `chatAdvice()`로 추출. 라우터·RagClient 의존성 추가.

이 단계는 기존 동작을 깨지 않는 리팩터링이므로 기존 manual smoke test(브라우저에서 챗봇 전송)로 검증한다.

- [ ] **Step 1: AiService.java 수정**

`src/main/java/io/github/wizwix/letsfutsal/ai/AiService.java` (전체 교체):
```java
package io.github.wizwix.letsfutsal.ai;

import com.fasterxml.jackson.databind.ObjectMapper;
import io.github.wizwix.letsfutsal.dto.ChatResponseDTO;
import io.github.wizwix.letsfutsal.dto.MatchDTO;
import io.github.wizwix.letsfutsal.dto.UserDTO;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.web.util.HtmlUtils;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.util.Collections;
import java.util.List;

@Service
public class AiService {
  private static final Logger log = LoggerFactory.getLogger(AiService.class);
  private static final String CLAUDE_API_URL = "https://api.anthropic.com/v1/messages";
  private static final int MAX_MESSAGE_LENGTH = 500;

  private final HttpClient httpClient = HttpClient.newHttpClient();
  private final ObjectMapper objectMapper;
  private final IntentRouter intentRouter;
  private final RagClient ragClient;
  private final String apiKey;

  public AiService(ObjectMapper objectMapper, IntentRouter intentRouter, RagClient ragClient) {
    this.objectMapper = objectMapper;
    this.intentRouter = intentRouter;
    this.ragClient = ragClient;
    String raw = System.getenv("CLAUDE_API_KEY");
    this.apiKey = (raw != null) ? raw.trim() : null;
    if (this.apiKey == null || this.apiKey.isBlank()) {
      log.warn("CLAUDE_API_KEY 환경변수가 설정되지 않았습니다. 챗봇 기능이 비활성화됩니다.");
    } else {
      log.info("CLAUDE_API_KEY 로드 완료 (길이: {}자)", this.apiKey.length());
    }
  }

  public ChatResponseDTO chat(UserDTO user, String rawMessage, List<MatchDTO> recentMatches) {
    if (apiKey == null || apiKey.isBlank()) {
      return new ChatResponseDTO(
          "AI 서비스가 설정되지 않았습니다. (서버에 API 키가 없습니다)",
          ChatResponseDTO.Mode.ADVICE, Collections.emptyList());
    }

    String message = rawMessage.length() > MAX_MESSAGE_LENGTH
        ? rawMessage.substring(0, MAX_MESSAGE_LENGTH) : rawMessage;
    String safeMessage = HtmlUtils.htmlEscape(message);

    IntentRouter.Decision decision = intentRouter.route(safeMessage);
    log.info("Routing: keywordHit={}, intent={}", decision.keywordHit(), decision.intent());

    if (decision.intent() == RagClient.Intent.KNOWLEDGE) {
      try {
        RagClient.RagResult result = ragClient.askRag(user, safeMessage);
        return new ChatResponseDTO(result.answer(), ChatResponseDTO.Mode.RAG, result.citations());
      } catch (RagClient.RagUnavailableException e) {
        log.warn("RAG 실패 → ADVICE 폴백: {}", e.getMessage());
        // fallthrough
      }
    }

    return new ChatResponseDTO(
        chatAdvice(user, safeMessage, recentMatches),
        ChatResponseDTO.Mode.ADVICE,
        Collections.emptyList());
  }

  String chatAdvice(UserDTO user, String message, List<MatchDTO> recentMatches) {
    try {
      String requestBody = buildRequestBody(buildSystemPrompt(user, recentMatches), message);
      HttpRequest request = HttpRequest.newBuilder()
          .uri(URI.create(CLAUDE_API_URL))
          .header("Content-Type", "application/json")
          .header("x-api-key", apiKey)
          .header("anthropic-version", "2023-06-01")
          .POST(HttpRequest.BodyPublishers.ofString(requestBody))
          .build();

      HttpResponse<String> response = httpClient.send(request, HttpResponse.BodyHandlers.ofString());
      log.info("Claude API 응답 상태코드: {}", response.statusCode());
      if (response.statusCode() != 200) {
        log.error("Claude API 오류 응답: {}", response.body());
        return parseErrorResponse(response.body());
      }
      return parseResponse(response.body());
    } catch (Exception e) {
      log.error("Claude API 호출 중 예외 발생: {} - {}", e.getClass().getSimpleName(), e.getMessage(), e);
      return "AI 서비스 오류: " + e.getClass().getSimpleName() + " - " + e.getMessage();
    }
  }

  private String buildSystemPrompt(UserDTO user, List<MatchDTO> recentMatches) {
    StringBuilder sb = new StringBuilder();
    sb.append("당신은 풋살 전문 AI 어시스턴트입니다.\n");
    sb.append("현재 유저 정보:\n");
    sb.append("- 닉네임: ").append(user.getNickname()).append("\n");
    sb.append("- 선호 포지션: ").append(
        user.getPreferredPosition() != null ? user.getPreferredPosition() : "없음").append("\n");
    sb.append("- 실력 등급: ").append(user.getGrade()).append("\n");
    if (recentMatches != null && !recentMatches.isEmpty()) {
      sb.append("- 최근 매치: ");
      recentMatches.stream().limit(3).forEach(m ->
          sb.append(m.getMatchDate()).append(" ").append(m.getRegion()).append(" | "));
    }
    sb.append("\n이 정보를 바탕으로 개인화된 풋살 조언을 제공하세요. ");
    sb.append("풋살과 무관한 질문은 정중히 거절하세요.");
    return sb.toString();
  }

  private String buildRequestBody(String systemPrompt, String userMessage) throws Exception {
    String systemJson = objectMapper.writeValueAsString(systemPrompt);
    String messageJson = objectMapper.writeValueAsString(userMessage);
    return String.format(
        "{\"model\":\"claude-sonnet-4-6\",\"max_tokens\":2048,\"system\":%s,\"messages\":[{\"role\":\"user\",\"content\":%s}]}",
        systemJson, messageJson);
  }

  private String parseResponse(String responseBody) throws Exception {
    var root = objectMapper.readTree(responseBody);
    var content = root.path("content");
    if (content.isArray() && content.size() > 0) {
      return content.get(0).path("text").asText("응답 텍스트를 읽을 수 없습니다.");
    }
    log.error("Claude API 응답에 content 배열 없음: {}", responseBody);
    return "잠시 후 다시 시도해주세요.";
  }

  private String parseErrorResponse(String responseBody) {
    try {
      var root = objectMapper.readTree(responseBody);
      String errorType = root.path("error").path("type").asText("unknown");
      String errorMsg = root.path("error").path("message").asText("알 수 없는 오류");
      return "AI 오류 [" + errorType + "]: " + errorMsg;
    } catch (Exception ex) {
      return "AI 서비스 오류가 발생했습니다.";
    }
  }
}
```

- [ ] **Step 2: 컴파일 확인**

```powershell
mvn -q compile
```
Expected: BUILD SUCCESS.

- [ ] **Step 3: 기존 테스트 영향 확인**

```powershell
mvn -q test
```
Expected: 기존 테스트 통과 + 새 테스트(RagClientTest, IntentRouterTest) 통과.

> **참고:** 이 시점에서 ChatController는 아직 `String` 반환을 기대하므로 컴파일 오류가 발생한다. Step 4에서 ChatController가 함께 수정될 것이므로 commit은 Task 13 끝에서 함께.

- [ ] **Step 4: (커밋은 Task 13 완료 후 함께)**

---

## Task 13: ChatController 응답 형식 변경

**Files:**
- Modify: `src/main/java/io/github/wizwix/letsfutsal/ai/ChatController.java`
- Modify: `src/main/webapp/WEB-INF/views/include/header.jsp` (옵션 — citation UI 표시. 본 Task에서는 최소 변경)

- [ ] **Step 1: ChatController.java 수정**

`src/main/java/io/github/wizwix/letsfutsal/ai/ChatController.java` (전체 교체):
```java
package io.github.wizwix.letsfutsal.ai;

import io.github.wizwix.letsfutsal.dto.ChatRequestDTO;
import io.github.wizwix.letsfutsal.dto.ChatResponseDTO;
import io.github.wizwix.letsfutsal.dto.UserDTO;
import jakarta.servlet.http.HttpSession;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.time.LocalDate;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/ai")
public class ChatController {
  private static final int DAILY_LIMIT = 30;
  private static final String COUNT_KEY = "aiChatCount";
  private static final String DATE_KEY = "aiChatDate";

  private final AiService aiService;

  public ChatController(AiService aiService) {
    this.aiService = aiService;
  }

  @PostMapping("/chat")
  public ResponseEntity<?> chat(
      @RequestBody ChatRequestDTO req,
      HttpSession session) {
    UserDTO user = (UserDTO) session.getAttribute("loginUser");
    if (user == null) {
      return ResponseEntity.status(401).body(Map.of("error", "로그인이 필요합니다."));
    }
    if (req.getMessage() == null || req.getMessage().isBlank()) {
      return ResponseEntity.badRequest().body(Map.of("error", "메시지를 입력해주세요."));
    }
    if (isRateLimited(session)) {
      return ResponseEntity.status(429).body(Map.of("error", "오늘 사용 한도(30회)에 도달했습니다."));
    }

    ChatResponseDTO response = aiService.chat(user, req.getMessage(), List.of());
    incrementCount(session);
    return ResponseEntity.ok(response);
  }

  private boolean isRateLimited(HttpSession session) {
    String today = LocalDate.now().toString();
    if (!today.equals(session.getAttribute(DATE_KEY))) {
      session.setAttribute(DATE_KEY, today);
      session.setAttribute(COUNT_KEY, 0);
    }
    Integer count = (Integer) session.getAttribute(COUNT_KEY);
    return count != null && count >= DAILY_LIMIT;
  }

  private void incrementCount(HttpSession session) {
    Integer count = (Integer) session.getAttribute(COUNT_KEY);
    session.setAttribute(COUNT_KEY, count == null ? 1 : count + 1);
  }
}
```

- [ ] **Step 2: 프론트엔드 챗봇 위젯 응답 처리 수정**

`src/main/webapp/WEB-INF/views/include/header.jsp` 또는 챗봇 위젯이 위치한 JSP에서 응답 JSON 파싱 부분을 찾는다. 기존 `data.message`를 그대로 사용하되, RAG 모드일 때 citation을 보여주도록 최소 변경:

(파일 내 `fetch('/ai/chat'...` 영역 근처를 찾아 응답 처리 블록을 다음과 같이 변경)

```javascript
.then(data => {
  let bubble = data.message;
  if (data.mode === 'RAG' && Array.isArray(data.citations) && data.citations.length) {
    const refs = data.citations
      .map(c => {
        const p = c.page ? ' p.' + c.page : '';
        return '[' + c.source + ' / ' + c.section + p + ']';
      })
      .join(' ');
    bubble += '\n\n📚 ' + refs;
  }
  appendMessage('bot', bubble);
})
```

> 정확한 위치는 JSP 파일에서 `/ai/chat` 호출 코드를 grep하여 찾는다.

- [ ] **Step 3: 전체 빌드**

```powershell
mvn -q package
```
Expected: BUILD SUCCESS, `target/letsfutsal.war` 생성.

- [ ] **Step 4: 모든 테스트 통과 확인**

```powershell
mvn -q test
```
Expected: 모든 테스트 그린.

- [ ] **Step 5: Task 12 + 13 합쳐서 Commit**

```powershell
git add src/main/java/io/github/wizwix/letsfutsal/ai/AiService.java `
        src/main/java/io/github/wizwix/letsfutsal/ai/ChatController.java `
        src/main/webapp/WEB-INF/views/include/header.jsp
git commit -m "feat(ai): AiService 라우팅 + ChatResponseDTO 도입, 위젯 citation 표시"
```

(`header.jsp` 외에 다른 챗봇 위젯 JSP가 있으면 함께 add)

---

## Task 14: 평가 골든셋 + run_eval.py + report 생성

**Files:**
- Create: `ai-service/eval/__init__.py`
- Create: `ai-service/eval/golden_set.jsonl`
- Create: `ai-service/eval/run_eval.py`

- [ ] **Step 1: 골든셋 작성**

`ai-service/eval/__init__.py`: (빈 파일)

`ai-service/eval/golden_set.jsonl` (20행, 실제 코퍼스에 맞게 작성):

```jsonl
{"id":"q01","query":"풋살에 오프사이드 규칙이 있어?","expected_source":"fifa futsal laws kr","expected_section":"","reference":"풋살에는 오프사이드 규칙이 없다."}
{"id":"q02","query":"풋살 경기 시간은 몇 분이야?","expected_source":"fifa futsal laws kr","expected_section":"","reference":"전후반 각 20분, 총 40분이다."}
{"id":"q03","query":"풋살에서 누적 파울이 몇 개를 넘으면 어떻게 돼?","expected_source":"fifa futsal laws kr","expected_section":"","reference":"한 팀의 누적 파울 5개를 넘으면 상대팀에게 10m 페널티킥이 주어진다."}
{"id":"q04","query":"4-0 포메이션이 뭐야?","expected_source":"formations 4 0","expected_section":"","reference":"수비라인 없이 네 명의 필드 플레이어가 일렬로 움직이는 공격적 포메이션이다."}
{"id":"q05","query":"3-1 포메이션의 특징은?","expected_source":"formations 3 1","expected_section":"","reference":"세 명의 수비/미드와 한 명의 피보로 구성된 균형형 포메이션이다."}
{"id":"q06","query":"2-2 포메이션 어떨 때 써?","expected_source":"formations 2 2","expected_section":"","reference":"두 명씩 전·후방으로 나뉘어 좌우 균형을 가져가는 기본 포메이션."}
{"id":"q07","query":"코너킥은 몇 초 안에 차야 해?","expected_source":"fifa futsal laws kr","expected_section":"","reference":"4초 이내에 차야 한다."}
{"id":"q08","query":"킥인 규칙 알려줘","expected_source":"fifa futsal laws kr","expected_section":"","reference":"사이드라인을 벗어났을 때 발로 차서 재개하는 방식이며 4초 이내에 차야 한다."}
{"id":"q09","query":"풋살에서 압박 전술이란?","expected_source":"tactics pressing","expected_section":"","reference":"상대 빌드업 단계에서 공간을 빠르게 좁혀 패스 미스를 유도하는 전술."}
{"id":"q10","query":"카운터 공격은 어떻게 만들어?","expected_source":"tactics pressing","expected_section":"","reference":"수비 후 빠른 전환으로 상대 수비가 정비되기 전에 공격을 마무리한다."}
{"id":"q11","query":"드리블 기본 훈련법은?","expected_source":"training basics","expected_section":"","reference":"공을 발 가까이 두고 좌우 발 인사이드/아웃사이드로 부드럽게 운반하는 연습이 기본이다."}
{"id":"q12","query":"패스 연습 어떻게 해?","expected_source":"training basics","expected_section":"","reference":"두 명이 마주보고 인사이드 패스를 반복하며, 거리와 속도를 점진적으로 늘린다."}
{"id":"q13","query":"슈팅 기본 자세는?","expected_source":"training basics","expected_section":"","reference":"디딤발을 공 옆에 두고 발등으로 임팩트, 상체는 약간 앞으로 기울인다."}
{"id":"q14","query":"풋살 골키퍼는 손으로 어디까지 잡을 수 있어?","expected_source":"fifa futsal laws kr","expected_section":"","reference":"자신의 페널티 에어리어 안에서 손을 사용할 수 있다."}
{"id":"q15","query":"풋살에서 슬라이딩 태클 돼?","expected_source":"fifa futsal laws kr","expected_section":"","reference":"공을 가진 선수에 대한 슬라이딩 태클은 금지된다."}
{"id":"q16","query":"피보 포지션이 뭐야?","expected_source":"formations 4 0","expected_section":"","reference":"풋살의 최전방 공격수로, 등을 진 상태에서 볼을 받아 키핑·연결하는 역할."}
{"id":"q17","query":"알라 포지션 설명","expected_source":"formations 3 1","expected_section":"","reference":"좌우 측면 공격수로, 수비-공격을 모두 담당한다."}
{"id":"q18","query":"수비 시 압박을 어떻게 시작해?","expected_source":"tactics pressing","expected_section":"","reference":"공을 가진 선수에게 가장 가까운 한 명이 적극적으로 압박하고 나머지는 패스 경로를 차단한다."}
{"id":"q19","query":"우리 팀이 자꾸 지는데 어떡하지?","expected_source":"__ADVICE__","expected_section":"","reference":"개인 조언성 질문(분류 검증용)"}
{"id":"q20","query":"오늘 풋살하기 좋은 날씨인가?","expected_source":"__ADVICE__","expected_section":"","reference":"풋살과 무관/조언성 질문(분류 검증용)"}
```

> **참고:** `expected_source`는 build_index.py가 `Path.stem.replace("_"," ")`로 채우므로 파일명(언더스코어→공백, 확장자 제외)을 사용. 실제 수집한 파일명에 맞게 수정.
> ADVICE 항목(q19, q20)은 분류 정확도 측정용으로 retrieval 지표에서 제외한다(`expected_source = "__ADVICE__"`).

- [ ] **Step 2: run_eval.py 작성**

`ai-service/eval/run_eval.py`:
```python
"""RAG 시스템 정량 평가.

사용법:
    python -m eval.run_eval --out eval/report.md
"""
from __future__ import annotations
import argparse
import json
from datetime import date
from pathlib import Path

from rag.chain import RagChain
from rag.claude_client import ClaudeClient
from rag.retriever import open_persistent_retriever
from rag.router_classifier import RouterClassifier


def load_golden(path: Path) -> list[dict]:
    out = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            out.append(json.loads(line))
    return out


def judge_faithfulness(claude: ClaudeClient, answer: str, reference: str) -> int:
    system = (
        "당신은 사실 일치 판정자입니다. ANSWER가 REFERENCE의 핵심 사실과 모순 없이 일치하면 1, "
        "사실이 누락되거나 모순되면 0을 출력하세요. 출력은 0 또는 1 한 글자만."
    )
    user = f"REFERENCE:\n{reference}\n\nANSWER:\n{answer}\n\n0 또는 1만 출력:"
    out = claude.chat(system=system, user=user, max_tokens=4).strip()
    return 1 if out.startswith("1") else 0


def evaluate(golden: list[dict], persist_dir: Path) -> dict:
    retriever = open_persistent_retriever(persist_dir)
    claude = ClaudeClient()
    chain = RagChain(retriever=retriever, claude_client=claude)
    classifier = RouterClassifier(claude_client=claude)

    knowledge_items = [g for g in golden if g["expected_source"] != "__ADVICE__"]
    advice_items = [g for g in golden if g["expected_source"] == "__ADVICE__"]

    retrieval_1_hits = 0
    retrieval_4_hits = 0
    citation_present = 0
    faithful_hits = 0
    failures: list[dict] = []

    for item in knowledge_items:
        resp = chain.answer(item["query"], user_context=None)
        if resp.citations:
            citation_present += 1
            top1 = resp.citations[0].source.lower()
            if item["expected_source"].lower() in top1:
                retrieval_1_hits += 1
            if any(item["expected_source"].lower() in c.source.lower() for c in resp.citations):
                retrieval_4_hits += 1
            else:
                failures.append({"id": item["id"], "query": item["query"], "top": top1})
        faithful_hits += judge_faithfulness(claude, resp.answer, item["reference"])

    classifier_correct = sum(
        1 for it in advice_items
        if classifier.classify(it["query"]).intent == "ADVICE"
    )

    n_k = max(1, len(knowledge_items))
    n_a = max(1, len(advice_items))
    return {
        "retrieval_at_1": retrieval_1_hits / n_k,
        "retrieval_at_4": retrieval_4_hits / n_k,
        "citation_present": citation_present / n_k,
        "answer_faithfulness": faithful_hits / n_k,
        "advice_classification_acc": classifier_correct / n_a,
        "knowledge_count": len(knowledge_items),
        "advice_count": len(advice_items),
        "failures": failures,
    }


TARGETS = {
    "retrieval_at_1": 0.70,
    "retrieval_at_4": 0.90,
    "citation_present": 0.95,
    "answer_faithfulness": 0.80,
    "advice_classification_acc": 0.90,
}


def render_report(metrics: dict) -> str:
    lines = [
        "# RAG Evaluation Report",
        f"- Date: {date.today().isoformat()}",
        f"- Model: claude-sonnet-4-6 / Embedding: jhgan/ko-sroberta-multitask",
        f"- Knowledge questions: {metrics['knowledge_count']}, Advice questions: {metrics['advice_count']}",
        "",
        "| Metric | Score | Target | Pass |",
        "|---|---|---|---|",
    ]
    for key, target in TARGETS.items():
        score = metrics[key]
        passed = "✅" if score >= target else "❌"
        lines.append(f"| {key} | {score:.2f} | {target:.2f} | {passed} |")

    if metrics["failures"]:
        lines.append("\n## Retrieval Failures")
        for f in metrics["failures"]:
            lines.append(f"- {f['id']}: \"{f['query']}\" — top1=`{f['top']}`")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--golden", default="eval/golden_set.jsonl", type=Path)
    parser.add_argument("--chroma", default="data/chroma_db", type=Path)
    parser.add_argument("--out", default="eval/report.md", type=Path)
    args = parser.parse_args()

    golden = load_golden(args.golden)
    metrics = evaluate(golden, args.chroma)
    report = render_report(metrics)
    args.out.write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
```

- [ ] **Step 3: 평가 실행**

```powershell
cd ai-service
. venv/Scripts/Activate.ps1
python -m eval.run_eval --out eval/report.md
```
Expected: 콘솔에 report.md 내용 출력 + `eval/report.md` 파일 생성. 각 지표가 목표를 충족해야 함. 미달 시 골든셋 `expected_source`가 실제 소스 이름과 일치하는지 점검(파일명 stem과 정확히 매칭).

- [ ] **Step 4: 평가 결과 확인 + 문제 시 재조정**

목표 미달인 경우 한 가지를 조정:
- `retrieval_at_4 < 0.9`: chunk_size를 400으로 줄이고 `build_index` 재실행
- `citation_present < 0.95`: KNOWLEDGE 항목 중 검색 0건이 있는지 점검 — 코퍼스 보강
- `advice_classification_acc < 0.9`: `router_classifier.py`의 SYSTEM_PROMPT에 예시 추가

- [ ] **Step 5: Commit**

```powershell
git add ai-service/eval/__init__.py ai-service/eval/golden_set.jsonl ai-service/eval/run_eval.py
git commit -m "feat(rag): 평가 골든셋 20문항 + run_eval 스크립트 추가"
```

> `eval/report.md`는 `.gitignore`에 의해 제외되므로 커밋 대상 아님. 포트폴리오 시 별도 첨부.

---

## Task 15: README + CLAUDE.md 업데이트

**Files:**
- Modify: `ai-service/README.md` (없으면 신규)
- Modify: `CLAUDE.md`

- [ ] **Step 1: ai-service/README.md 작성/갱신**

`ai-service/README.md` 전체:
````markdown
# letsfutsal AI Service

FastAPI 기반 AI 마이크로서비스. 매치 추천(Content-Based Filtering) + 풋살 지식 RAG 챗봇 + 의도 라우터 분류기를 제공한다.

## 엔드포인트

| Method | Path | 용도 |
|---|---|---|
| GET | `/health` | 헬스체크 (rag_enabled 플래그 포함) |
| POST | `/recommend/matches` | 사용자 프로필 기반 매치 추천 |
| POST | `/chat/rag` | RAG 풋살 지식 질의응답 (citation 포함) |
| POST | `/router/classify` | KNOWLEDGE/ADVICE 의도 분류 |

## 설치

```powershell
python -m venv venv
. venv/Scripts/Activate.ps1
pip install -r requirements.txt
```

환경 변수:
- `CLAUDE_API_KEY` (필수, RAG 사용 시)
- `RAG_CHROMA_DIR` (옵션, 기본 `data/chroma_db`)

## RAG 인덱스 빌드

`data/raw/`에 PDF/Markdown 풋살 자료를 넣은 뒤:

```powershell
python -m rag.build_index --raw data/raw --out data/chroma_db
```

산출물: `data/chroma_db/chroma.sqlite3`. ChromaDB persistent client가 이 디렉토리를 읽는다.

## 서버 실행

```powershell
$env:CLAUDE_API_KEY = "sk-ant-..."
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

`/health`의 `rag_enabled`가 `false`면 `data/chroma_db`가 비어있다 → `build_index`를 먼저 실행.

## 평가

```powershell
python -m eval.run_eval --out eval/report.md
```

`eval/golden_set.jsonl`의 20문항으로 retrieval@1·@4, citation 표시율, answer faithfulness(LLM-as-judge), ADVICE 분류 정확도를 측정. 결과는 `eval/report.md` 마크다운으로 저장.

## 테스트

```powershell
pytest -v
```
````

- [ ] **Step 2: CLAUDE.md 업데이트**

`CLAUDE.md`의 "Architecture" 또는 "도메인 목록" 섹션 뒤에 다음 블록 추가/갱신:

```markdown
### AI 기능 구조 (2026-05 RAG 업그레이드 후)

- 추천: Spring `RecommendService` → FastAPI `/recommend/matches` (scikit-learn CBF)
- 챗봇:
  - Spring `ChatController` → `AiService.chat()` → `IntentRouter`
  - 라우터: 한국어 키워드 사전 매칭 1차 → MISS 시 Python `/router/classify` (Claude Tool Use) 폴백
  - KNOWLEDGE → Python `/chat/rag` (LangChain + ChromaDB + sentence-transformers)
  - ADVICE → 기존 `chatAdvice()` (Spring → Claude API 직접 호출)
- 응답: `ChatResponseDTO {message, mode, citations[]}` — RAG 시 citation 자동 첨부
- 폴백: RAG/분류기 실패는 ADVICE 경로로 우아하게 폴백
- 평가: `ai-service/eval/run_eval.py`로 retrieval@k, faithfulness 측정 → `eval/report.md`
```

- [ ] **Step 3: Commit**

```powershell
git add ai-service/README.md CLAUDE.md
git commit -m "docs: RAG 챗봇 운영 가이드 README/CLAUDE.md 갱신"
```

---

## Task 16: 엔드투엔드 수동 검증 + 최종 정리

이 단계는 실제 사용자 경험을 검증한다. 자동 테스트가 잡지 못하는 통합 결함을 잡는다.

- [ ] **Step 1: 사전 준비**

```powershell
# 1) Python 인덱스가 빌드되어 있는지
Test-Path ai-service/data/chroma_db/chroma.sqlite3

# 2) Python 서버 기동 (별도 터미널)
cd ai-service
. venv/Scripts/Activate.ps1
$env:CLAUDE_API_KEY = "sk-ant-..."
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# 3) Spring WAR 빌드 & Tomcat 배포
mvn package
# (C:/tomcat/11015/webapps에 target/letsfutsal.war 복사 및 Tomcat 재시작)
```

- [ ] **Step 2: 시나리오 1 — RAG (키워드 직격)**

브라우저에서 로그인 → 챗봇 위젯 열기 → "오프사이드 규칙이 뭐야?" 입력.

Expected:
- 본문에 "풋살에는 오프사이드가 없다" 류 답변
- 본문 하단에 `📚 [FIFA Futsal Laws ...]` citation 표시
- Tomcat 로그에 `Routing: keywordHit=true, intent=KNOWLEDGE`
- Python 로그에 `/chat/rag` 호출

- [ ] **Step 3: 시나리오 2 — RAG (라우터 LLM 폴백 → KNOWLEDGE)**

"4-0과 3-1 중에 뭐가 좋아?" 입력.

Expected:
- 키워드는 "4-0", "3-1"이 들어있어 직격 가능 — 라우터 LLM 폴백 검증을 위해 키워드에 없는 질문으로 변경:

"세트 피스 종류 좀 알려줘" (키워드 사전에 없음)

Expected:
- Tomcat 로그에 `Routing: keywordHit=false, intent=KNOWLEDGE`
- citation 1개 이상

- [ ] **Step 4: 시나리오 3 — ADVICE (개인 조언)**

"우리 팀이 자꾸 져서 의욕이 떨어져" 입력.

Expected:
- 답변에 개인화 응답 (유저 닉네임 활용 가능)
- citation 없음
- 응답 mode가 ADVICE
- Tomcat 로그에 `Routing: keywordHit=false, intent=ADVICE`

- [ ] **Step 5: 시나리오 4 — RAG 폴백**

Python 서버 종료 → 챗봇에 "오프사이드 규칙?" 다시 입력.

Expected:
- 응답이 정상적으로 오되, mode=ADVICE, citation 없음
- Tomcat 로그에 `RAG 실패 → ADVICE 폴백`
- 사용자 시점에서는 에러 없이 응답 도착

- [ ] **Step 6: 시나리오 5 — Rate Limit (기존 기능 회귀 확인)**

30회 채팅 송신 → 31번째에서 "오늘 사용 한도(30회)에 도달했습니다." 표시.

Expected: 기존 동작 유지.

- [ ] **Step 7: 평가 리포트 첨부 준비**

```powershell
cd ai-service
. venv/Scripts/Activate.ps1
python -m eval.run_eval --out eval/report.md
Get-Content eval/report.md
```

`eval/report.md`를 포트폴리오·이력서 첨부용으로 보관(별도 디렉토리 또는 PR 본문에 첨부).

- [ ] **Step 8: 최종 통합 빌드 + 테스트**

```powershell
mvn package
cd ai-service
. venv/Scripts/Activate.ps1
pytest -v
```
Expected: 모두 그린.

- [ ] **Step 9: 작업 브랜치 정리 / 최종 커밋 (필요 시)**

만약 위 시나리오 디버깅 중 작은 수정이 있었다면:
```powershell
git add -p   # 변경 파일 골라서 staging
git commit -m "fix(ai): 엔드투엔드 검증 중 발견한 [구체 이슈] 수정"
```

수정이 없으면 별도 커밋 불필요.

---

## 완료 기준

다음이 모두 충족되면 본 plan 완료:

- [ ] Python pytest 20개 + Java JUnit 8개 모두 통과
- [ ] `ai-service/eval/report.md` 생성, 4/5 지표 목표 달성
- [ ] 브라우저 챗봇에서 시나리오 1~4 모두 의도대로 동작
- [ ] `mvn package` 그린, `target/letsfutsal.war` 생성
- [ ] `CLAUDE.md` 업데이트로 라우터+RAG 구조 명시
- [ ] 모든 변경이 commit, `main` 브랜치에 머지 가능 상태

---

## Spec ↔ Plan 매핑 (Self-review)

| Spec 섹션 | Plan 태스크 |
|---|---|
| 3.1 전체 흐름 | Task 12, 13 (Spring 라우팅), Task 8 (Python 엔드포인트) |
| 3.2 컴포넌트 분리 | Task 4~7 (Python), Task 10~13 (Java) |
| 4.1 Spring↔Client DTO | Task 9, 13 |
| 4.2 Spring↔Python DTO | Task 2, 8, 10 |
| 4.3 시나리오 A/B/C | Task 16 |
| 4.4 키워드 사전 | Task 11 |
| 4.5 ChromaDB 레이아웃 | Task 5 |
| 4.6 청킹 전략 | Task 5 |
| 5 에러 처리 | Task 10 (RagClient 예외), Task 11 (분류기 실패 폴백), Task 12 (RAG 폴백) |
| 6 평가 설계 | Task 14 |
| 7 테스트 | Task 2~11에 분산 + Task 16 수동 시나리오 |
| 8 파일 변경 목록 | 본 plan의 File Structure 섹션과 일치 |
| 9 의존성·환경 | Task 1 |
| 10 일정 | Task 0~16 순서가 spec 일정과 1:1 매핑 |
| 11 YAGNI 제외 | 본 plan에서 어떤 task도 streaming, multi-turn, reranker, hybrid search 포함하지 않음 |

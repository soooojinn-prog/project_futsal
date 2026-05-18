# RAG 풋살 지식 챗봇 설계 (Feature 2)

> 포트폴리오·취업 목적 AI 기능 확장 — 기능 2 (RAG 챗봇)
> 작성일: 2026-05-19
> 관련 로드맵: [docs/ai-features-roadmap.md](../../ai-features-roadmap.md)

---

## 1. 목표 및 배경

현재 챗봇(`src/main/java/io/github/wizwix/letsfutsal/ai/AiService.java`)은 Spring → Claude API 직접 호출 구조로, 개인화된 시스템 프롬프트만 사용한다. "오프사이드 규칙이 뭐야?", "4-0 포메이션 설명해줘" 같은 사실 기반 질문에 정확한 출처 없이 모델 지식만으로 답한다.

본 설계는 다음을 달성한다.

- 풋살 공식 자료(FIFA 규칙, KFA 자료, 한글 전술/훈련 가이드)를 RAG 파이프라인으로 색인
- **Intent Router**로 지식 질문은 RAG, 개인 조언 질문은 기존 경로로 동적 분기
- Citation 자동 첨부로 hallucination 방지
- 골든셋 20문항 기반 정량 평가(retrieval@k, answer faithfulness)

**이력서 문구 후보**

> LangChain + ChromaDB 기반 한국어 RAG 챗봇 설계·구현. 키워드 사전과 Claude 분류기를 결합한 하이브리드 Intent Router로 RAG/일반 LLM 경로를 동적 분기, retrieval@4 0.95·faithfulness 0.85 달성. Citation 자동 첨부로 hallucination 방지.

---

## 2. 의사결정 요약

| 항목 | 결정 | 근거 |
|---|---|---|
| 스코프 | 라우터 + RAG (지식 질문만 RAG) | 무관 컨텍스트가 응답 품질을 떨어뜨리는 한계 회피, 면접 트레이드오프 설명 가능 |
| 문서 | 한국어 중심 (KFA 풋살 규칙 + 한글 전술/훈련 자료 5~10개) | 한국어 임베딩 모델 경험 어필, 자료 수집 부담 최소화 |
| 통합 | Python ai-service에 RAG 엔드포인트, Spring은 HTTP 호출 | LangChain/ChromaDB Python 생태계 표준, 기존 RestTemplate 패턴 재활용 |
| 라우터 | 하이브리드: 키워드 1차 → 애매하면 Claude 분류기 폴백 | 정확도와 비용의 균형, 면접에서 "2단계 라우터" 설명 가능 |
| 임베딩 | jhgan/ko-sroberta-multitask | 한국어 특화, <500MB 가벼움, 국내 NLP 익숙도 어필 |
| 벡터 스토어 | ChromaDB persistent | 디스크 persist로 서버 재시작 후에도 인덱스 유지 |
| 어필 요소 | Citation 표시 + 골든셋 20문항 평가 | 면접 임팩트 최상, 정량 지표 제시 |
| 운영 | CLI 사전 인덱싱 + Single-turn | 1~2.5일 일정 유지, 구조 단순 |

---

## 3. 아키텍처

### 3.1 전체 흐름

```
[브라우저: 챗봇 위젯]
        │ POST /ai/chat  { message }
        ▼
[Spring ChatController]
        │ 1. 로그인/Rate Limit 검사 (기존 그대로)
        ▼
[Spring AiService.chat()]
        │ 2. IntentRouter — 키워드 매칭 (한국어 풋살 지식 사전)
        │    ├─ HIT  → POST http://localhost:8000/chat/rag
        │    └─ MISS → Claude 분류기 폴백 (POST /router/classify)
        │                ├─ KNOWLEDGE → POST /chat/rag
        │                └─ ADVICE    → 기존 Claude 직접 호출 (chatAdvice)
        ▼
[Python FastAPI ai-service]
   /chat/rag
        │ 3. 사용자 질문 → ko-sroberta 임베딩
        │ 4. ChromaDB 유사도 검색 top-k=4
        │ 5. 검색 청크 + 시스템 프롬프트 → Claude API
        │ 6. {answer, citations[]} 반환
        ▼
[Spring → 클라이언트] { message, mode, citations[] }
```

### 3.2 컴포넌트 분리 (한 책임씩)

**Java (Spring) 측**

- `AiService.chat()` — 라우팅 진입점 (변경됨). 결정 후 RAG 또는 advice 경로 위임만.
- `AiService.chatAdvice()` — 기존 Claude 직접 호출 로직 (메서드만 추출, 로직 변경 없음)
- `IntentRouter` (신규) — 키워드 매칭 + LLM 폴백 결정
- `RagClient` (신규) — Python `/chat/rag`, `/router/classify` REST 호출, DTO 매핑

**Python (ai-service/) 측**

- `rag/build_index.py` — 오프라인 인덱스 빌드 CLI
- `rag/retriever.py` — ChromaDB persistent client + 임베딩 모델 로드
- `rag/chain.py` — LangChain RetrievalQA 체인 (Claude 연동, citation 추출)
- `rag/router_classifier.py` — Claude 폴백 분류 (KNOWLEDGE/ADVICE 단일 호출)
- `rag/schemas.py` — Pydantic DTO
- `main.py` — `/chat/rag`, `/router/classify` 엔드포인트 추가

**데이터 디렉토리**

- `ai-service/data/raw/` — 원본 PDF/마크다운 문서 (gitignore)
- `ai-service/data/chroma_db/` — persistent ChromaDB (gitignore)
- `ai-service/eval/golden_set.jsonl` — 평가셋 20문항 (커밋)
- `ai-service/eval/run_eval.py` — 평가 실행 스크립트 (커밋)

---

## 4. 데이터 흐름 & DTO 계약

### 4.1 Spring ↔ 클라이언트 (변경)

```json
// POST /ai/chat
// Request (기존 유지)
{ "message": "오프사이드 규칙이 뭐야?" }

// Response (변경: mode, citations 추가)
{
  "message": "풋살에는 오프사이드 규칙이 없습니다 ...",
  "mode": "RAG",                        // "RAG" | "ADVICE"
  "citations": [
    {
      "source": "FIFA Futsal Laws",
      "section": "Law 11",
      "page": 14,
      "snippet": "There is no offside in Futsal.",
      "score": 0.87
    }
  ]
}
```

`citations`는 ADVICE 모드에서는 항상 빈 배열. RAG 모드에서 검색 결과 0건이면 빈 배열 가능(섹션 5 참고).

### 4.2 Spring ↔ Python (신규 내부 API)

**POST `/chat/rag`**
```json
// Request
{
  "user_message": "오프사이드 규칙이 뭐야?",
  "user_context": {
    "nickname": "수진",
    "grade": "BRONZE",
    "preferred_position": "GOALKEEPER"
  }
}

// Response
{
  "answer": "풋살에는 오프사이드 규칙이 없습니다 ...",
  "citations": [
    { "source": "FIFA Futsal Laws", "section": "Law 11", "page": 14, "snippet": "...", "score": 0.87 }
  ],
  "retrieved_chunks": 4
}
```

**POST `/router/classify`** (라우터 LLM 폴백 전용)
```json
// Request
{ "user_message": "포메이션 추천해줘" }

// Response
{ "intent": "KNOWLEDGE", "confidence": 0.92 }
```

`confidence`는 Claude 호출 시 Tool Use(structured output)로 `{"intent": "KNOWLEDGE"|"ADVICE", "confidence": float}` 스키마를 강제하여 채운다. 라우팅 결정은 `intent`만 사용하고 `confidence`는 로깅·디버깅용.

### 4.3 시나리오별 흐름

**시나리오 A — 키워드 직격 (대부분의 케이스)**
```
"오프사이드 규칙이 뭐야?"
  → IntentRouter.keywordMatch() → HIT ("규칙")
  → RagClient.askRag(...) → Python /chat/rag
  → 응답: { mode:"RAG", citations:[...] }
```

**시나리오 B — 키워드 미스, LLM 폴백 → ADVICE**
```
"우리 팀이 자꾸 지는데"
  → keywordMatch() → MISS
  → /router/classify → "ADVICE"
  → chatAdvice() (기존 Claude 직접 호출)
  → 응답: { mode:"ADVICE", citations:[] }
```

**시나리오 C — 키워드 미스, LLM 폴백 → KNOWLEDGE**
```
"4-0과 3-1 중에 우리 팀에 뭐가 맞아?"
  → keywordMatch() → MISS
  → /router/classify → "KNOWLEDGE"
  → /chat/rag → answer + citations
```

### 4.4 IntentRouter 키워드 사전 (초기 안)

```
규칙, 반칙, 오프사이드, 파울, 프리킥, 페널티킥, 킥인, 코너킥,
포메이션, 4-0, 3-1, 2-2, 전술, 압박, 카운터,
드리블, 패스, 슈팅, 트래핑, 훈련, 연습법
```

매칭 규칙: 메시지 정규화(공백/대소문자 무시) 후 `contains()` 1회라도 매칭되면 KNOWLEDGE.

### 4.5 ChromaDB 저장 레이아웃

```
ai-service/data/chroma_db/
├── chroma.sqlite3
└── <collection-uuid>/...

Collection: "futsal_knowledge"
Distance: cosine
Embedding: 768-dim (ko-sroberta-multitask 출력)

Document fields:
  id          : str (uuid)
  text        : str (chunk)
  metadata    : {
    source    : "FIFA Futsal Laws",
    section   : "Law 11",
    page      : 14,
    lang      : "ko"
  }
```

### 4.6 청킹 전략

- LangChain `RecursiveCharacterTextSplitter`
- `chunk_size=500` 문자, `chunk_overlap=80`
- 분리자 우선순위: `["\n\n", "\n", ". ", " "]`
- 한국어 문장 자연 단위 우선 유지

---

## 5. 에러 처리

**원칙**: RAG 실패는 사용자 경험을 깨지 않는다. 항상 기존 챗봇 경로로 우아하게 폴백.

| 실패 지점 | 감지 방법 | 동작 |
|---|---|---|
| Python ai-service 다운 | RagClient HTTP timeout/connect 예외 | **폴백**: `chatAdvice()` 직접 호출 → mode="ADVICE", citations=[] |
| Python /chat/rag 5xx | HTTP 상태 코드 | **폴백**: `chatAdvice()` + ERROR 로그 |
| Python에서 Claude API 실패 | FastAPI try/except | Python 4xx 반환 → Spring 폴백 |
| ChromaDB 검색 결과 0건 | retriever 빈 리스트 | Python: 일반 Claude 답변(citations 빈 배열)으로 응답 |
| 임베딩 모델 로드 실패 | FastAPI startup event 예외 | **Fail fast**: 서버 부팅 실패 |
| ChromaDB persist 디렉토리 없음 | startup 검증 | **Fail fast** — "build_index.py를 먼저 실행하세요" |
| LLM 분류기 폴백 실패 | /router/classify 5xx/timeout | **보수적 분기**: ADVICE로 처리 |
| Rate limit (Spring 일 30회) | 기존 로직 | 그대로 유지 — 라우팅 전 검사 |

**타임아웃**
- Spring → Python: connect 2s, read 30s (Python의 retriever + Claude 응답 5~10s + 여유분)
- Python → Claude: SDK 기본값 (~60s)
- `/router/classify`는 별도로 read 5s (분류는 짧은 응답이며, 폴백 자체가 빠르게 실패해야 함)

**로깅**
- Spring: `log.info("Routing: keyword={}, intent={}, mode={}", keywordHit, llmIntent, finalMode)`
- Python: 검색된 청크 id·score를 DEBUG로 (운영 시 INFO로 낮춤)

---

## 6. 평가 설계

### 6.1 골든셋 — `ai-service/eval/golden_set.jsonl`

```json
{"id":"q01","query":"풋살에 오프사이드 있어?","expected_source":"FIFA Futsal Laws","expected_section":"Law 11","reference":"풋살에는 오프사이드 규칙이 없습니다."}
{"id":"q02","query":"4-0 포메이션이 뭐야?","expected_source":"Tactics Guide","expected_section":"Formations","reference":"수비라인 없이 ..."}
```

- KNOWLEDGE 카테고리 18문항 + edge case 2문항 (ADVICE성 질문 — 라우터 분류 정확도 확인용)
- 항목 추가는 같은 JSONL에 append

### 6.2 지표 및 목표

| 지표 | 정의 | 목표 |
|---|---|---|
| `retrieval@1` | top-1 청크의 `source`가 `expected_source`와 일치하는 비율 | ≥ 0.70 |
| `retrieval@4` | top-4 청크 중 하나라도 `expected_source` 포함 비율 | ≥ 0.90 |
| `answer_faithfulness` | Claude judge 호출로 "답변이 reference와 의미상 일치하는가" (LLM-as-judge, 0/1) | ≥ 0.80 |
| `citation_present` | citations 배열이 비어있지 않은 비율 (KNOWLEDGE 쿼리에서) | ≥ 0.95 |

### 6.3 실행

```bash
cd ai-service
python -m eval.run_eval --out eval/report.md
```

산출물: `ai-service/eval/report.md`. 포트폴리오 첨부 가능한 마크다운 리포트.

---

## 7. 테스트

**Python (pytest)**
- `tests/test_router_classifier.py` — Mock Claude로 KNOWLEDGE/ADVICE 분류 응답 파싱 검증
- `tests/test_retriever.py` — 임시 ChromaDB collection에 3 doc 인덱싱 → 쿼리 → top-k 형식 검증
- `tests/test_rag_endpoint.py` — FastAPI TestClient, retriever·Claude 모두 Mock하여 `/chat/rag` 스키마 검증

**Java (JUnit)**
- `IntentRouterTest` — 키워드 사전 매칭 케이스 (HIT/MISS) 단위 테스트
- `RagClientTest` — `MockWebServer` 또는 RestTemplate Mock으로 Python 다운 시 폴백 검증

**수동 데모 시나리오** (PR 본문 첨부용)
1. "오프사이드 규칙이 뭐야?" → RAG, citation 표시
2. "4-0 포메이션 설명해줘" → RAG
3. "우리 팀이 자꾸 져" → ADVICE (개인화 답변, citation 없음)
4. Python 서버 중지 후 위 질문 → 모두 ADVICE 폴백, 사용자에게는 정상 응답

---

## 8. 파일 변경 목록

### 8.1 Java (Spring) — 변경 3 / 신규 6

| 경로 | 변경 | 책임 |
|---|---|---|
| `src/main/java/.../ai/AiService.java` | 변경 | 라우팅 진입점으로 리팩터. 기존 Claude 호출 → `chatAdvice()`로 메서드 추출 |
| `src/main/java/.../ai/ChatController.java` | 변경 | `ChatResponseDTO` 반환 |
| `src/main/java/.../ai/IntentRouter.java` | 신규 | 키워드 사전 + Python 분류기 폴백 |
| `src/main/java/.../ai/RagClient.java` | 신규 | Python REST 호출 |
| `src/main/java/.../dto/ChatResponseDTO.java` | 신규 | `{message, mode, citations}` |
| `src/main/java/.../dto/CitationDTO.java` | 신규 | `{source, section, page, snippet, score}` |
| `src/main/java/.../config/RootConfig.java` 또는 properties | 변경 | `ai.python.baseUrl` 외부화 |
| `src/test/java/.../ai/IntentRouterTest.java` | 신규 | 키워드 매칭 단위 테스트 |
| `src/test/java/.../ai/RagClientTest.java` | 신규 | 폴백 검증 |

### 8.2 Python (ai-service) — 변경 2 / 신규 11

| 경로 | 변경 | 책임 |
|---|---|---|
| `ai-service/main.py` | 변경 | `/chat/rag`, `/router/classify` 등록, startup retriever 초기화 |
| `ai-service/requirements.txt` | 변경 | langchain, chromadb, sentence-transformers, pypdf 추가 |
| `ai-service/rag/__init__.py` | 신규 | |
| `ai-service/rag/build_index.py` | 신규 | CLI 인덱싱 |
| `ai-service/rag/retriever.py` | 신규 | ChromaDB client + 임베딩 |
| `ai-service/rag/chain.py` | 신규 | RetrievalQA 체인 |
| `ai-service/rag/router_classifier.py` | 신규 | Claude 분류기 |
| `ai-service/rag/schemas.py` | 신규 | Pydantic DTO |
| `ai-service/data/raw/` | 신규 디렉토리 | 원본 문서 (.gitignore) |
| `ai-service/data/chroma_db/` | 신규 디렉토리 | persistent DB (.gitignore) |
| `ai-service/eval/golden_set.jsonl` | 신규 | 평가셋 20문항 |
| `ai-service/eval/run_eval.py` | 신규 | 평가 실행 |
| `ai-service/tests/test_router_classifier.py` | 신규 | pytest |
| `ai-service/tests/test_retriever.py` | 신규 | pytest |
| `ai-service/tests/test_rag_endpoint.py` | 신규 | pytest |

### 8.3 문서

| 경로 | 변경 | 책임 |
|---|---|---|
| `ai-service/README.md` | 변경 | RAG 빌드/실행/평가 명령 추가 |
| `docs/superpowers/specs/2026-05-19-rag-chatbot-design.md` | 신규 | 본 spec |
| `CLAUDE.md` | 변경 | "AI 기능 구조" 섹션 갱신 |

---

## 9. 의존성 & 환경

**Python (`ai-service/requirements.txt` 추가)**
```
langchain==0.3.x
langchain-anthropic==0.3.x
langchain-community==0.3.x
chromadb==0.5.x
sentence-transformers==3.x
pypdf==4.x
```

**Java** — 신규 의존성 없음 (RestTemplate, Jackson 이미 있음)

**환경 변수**
- 기존 `CLAUDE_API_KEY` — Python 서버 실행 셸에서 동일 변수 export 필요
- 신규: 없음

---

## 10. 일정 (총 ~2.5일)

| Day | 작업 | 산출물 |
|---|---|---|
| **Day 1 오전** | 원본 문서 5~7개 수집 + `data/raw/` 정리 | KFA 풋살 규칙·전술 PDF/MD |
| Day 1 오후 | `build_index.py` 구현 → ChromaDB persist | `chroma_db/` 생성 |
| **Day 2 오전** | `retriever.py` + `chain.py` + `/chat/rag` 엔드포인트 | curl 동작 확인 |
| Day 2 오후 | `router_classifier.py` + `/router/classify` + Python 테스트 3종 | pytest 그린 |
| **Day 3 오전** | Java `IntentRouter`, `RagClient`, DTO, Controller 변경 + 단위 테스트 | mvn test 그린 |
| Day 3 오후 (½일) | `golden_set.jsonl` 20문항 + `run_eval.py` + `report.md` | 평가 통과 + README 업데이트 |

**Risk**: 데이터 수집·정제. Day 1 오전 안에 5개 미만 확보 시 FIFA 영문판 1~2개로 보충.

---

## 11. 명시적으로 제외하는 것 (YAGNI)

- Multi-turn 대화 메모리
- Reranker (단순 코사인 검색만)
- Hybrid search (BM25 + 벡터)
- 인덱싱 자동 트리거 (수동 CLI만)
- 다국어 (한국어만)
- 사용자 피드백 수집 (👍/👎)
- Streaming 응답
- 사용자별 RAG 결과 캐싱

---

## 12. 다음 단계

본 spec 승인 → `superpowers:writing-plans` skill로 전환하여 구현 계획(plan.md) 작성 → 구현 진행.

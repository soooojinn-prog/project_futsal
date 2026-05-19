# letsfutsal AI Service

풋살 매칭 추천 + 풋살 지식 RAG 챗봇을 제공하는 Python FastAPI 서비스. Spring (`letsfutsal.war`)에서 RestTemplate으로 호출.

## 구성 요소

- **매치 추천** (`recommender.py`) — scikit-learn 기반, 사용자 등급·포지션·성별 매칭
- **RAG 챗봇** (`rag/`) — LangChain + ChromaDB + sentence-transformers + Claude API
- **라우터** (`rag/router_classifier.py`) — Claude Tool Use로 KNOWLEDGE/ADVICE 의도 분류
- **LangGraph 에이전트** (`agent/`) — 단일 매치 / 토너먼트 코디네이터, StateGraph + conditional edge + ThreadPoolExecutor 병렬 sub-agent
- **평가** (`eval/`) — 골든셋 20문항(RAG) + 시나리오 8개(에이전트) 기반 정량 측정

## 디렉토리

```
ai-service/
├── main.py                 # FastAPI 앱 (lifespan + 엔드포인트)
├── recommender.py          # 매치 추천 엔진
├── data_generator.py       # 추천 학습용 더미 매치 데이터
├── rag/
│   ├── schemas.py          # Pydantic DTO (Citation, RagRequest/Response, Classify)
│   ├── claude_client.py    # Anthropic SDK 얇은 래퍼 (chat + chat_with_tool)
│   ├── retriever.py        # ChromaDB + sentence-transformers (jhgan/ko-sroberta-multitask)
│   ├── chain.py            # RAG 체인 (retriever → 시스템 프롬프트 → Claude)
│   ├── router_classifier.py # Claude Tool Use 기반 KNOWLEDGE/ADVICE 분류
│   └── build_index.py      # CLI: PDF/Markdown → 청크 → 임베딩 → ChromaDB persist
├── data/
│   ├── raw/                # 풋살 지식 코퍼스 마크다운 (git 포함)
│   ├── chroma_db/          # 인덱싱 결과 (gitignore)
│   └── excluded_pdf/       # 본문 추출 실패한 한글 PDF (gitignore)
├── eval/
│   ├── golden_set.jsonl    # 평가 골든셋 20문항
│   └── run_eval.py         # 평가 실행 + report.md 생성
├── tests/                  # pytest (36 tests)
├── .env.example            # 환경 변수 템플릿
├── .env                    # 실제 키 (gitignore)
└── requirements.txt
```

## 엔드포인트

| Method | Path | 설명 |
|---|---|---|
| GET  | `/health` | 헬스 체크 + `rag_enabled` |
| POST | `/recommend/matches` | 매치 추천 (Spring 호출용) |
| POST | `/chat/rag` | RAG 답변 + citation |
| POST | `/router/classify` | KNOWLEDGE/ADVICE 분류 |
| POST | `/agent/run` | LangGraph 에이전트 실행 → ProposalDTO |

## 설치

```powershell
# 가상환경
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt

# 환경 변수 (.env 생성)
Copy-Item .env.example .env
notepad .env   # CLAUDE_API_KEY 채우기
```

## RAG 사전 인덱싱 (서버 띄우기 전 1회)

```powershell
$env:PYTHONIOENCODING="utf-8"
python -m rag.build_index --raw data/raw --out data/chroma_db
```

- `data/raw/` 아래의 PDF/Markdown 문서를 LangChain `RecursiveCharacterTextSplitter`로 청크 분할 (`chunk_size=500`, `overlap=80`)
- `jhgan/ko-sroberta-multitask`로 임베딩 (첫 실행 시 모델 ~430MB 다운로드)
- ChromaDB persistent client로 `data/chroma_db/`에 저장 (cosine distance)
- 결과 예시: 18개 마크다운 → 38청크

## 서버 실행

```powershell
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

기동 시 lifespan이 `RAG_CHROMA_DIR`(기본 `data/chroma_db`) 존재 여부를 보고 RAG를 활성화한다. 없으면 `/chat/rag` 엔드포인트는 503을 반환한다.

## 호출 예

```powershell
# 헬스
curl http://localhost:8000/health

# RAG 질문
$body = '{"user_message":"풋살에 오프사이드 있어?"}'
curl -X POST http://localhost:8000/chat/rag `
  -H "Content-Type: application/json; charset=utf-8" `
  --data-binary $body
```

응답:
```json
{
  "answer": "풋살에는 오프사이드 규칙이 없습니다 ...",
  "citations": [
    {"source": "rules 11 offside", "section": "", "page": 0, "snippet": "...", "score": 0.76}
  ],
  "retrieved_chunks": 4
}
```

## 에이전트 실행

별도 사전 인덱싱 불필요. `/agent/run` 호출 시 `main.py` lifespan에서 빌드된 StateGraph가 즉시 실행.

내부 흐름:
- `parse_intent` 노드가 SINGLE/TOURNAMENT 분류 → conditional edge로 분기
- SINGLE: stadium → team → match → review 순차
- TOURNAMENT: StadiumAgent + TeamAgent를 ThreadPoolExecutor 병렬 실행 → MatchAgent로 대진표·매치 통합

Spring 측 `AgentService`가 `/agent/run` 호출 → 사용자 미리보기 편집 → `/ai/agent/confirm` → `game_match` INSERT.

## 에이전트 평가

```powershell
python -m eval.run_agent_eval
```

4개 지표:
- `intent_acc` — 의도 분류 정확도 (목표 ≥ 0.90)
- `tool_correctness` — 기대 Tool 호출 흔적 (LLM judge, 목표 ≥ 0.85)
- `proposal_validity` — 시나리오별 최소 제안 수 충족 (목표 ≥ 0.90)
- `e2e_success` — 전체 통과 (목표 ≥ 0.75)

산출물: `eval/agent_report_<timestamp>.md` (덮어쓰기 방지로 매 실행마다 새 파일).

## RAG 평가

```powershell
python -m eval.run_eval --out eval/report.md
```

5개 지표 산출:

| 지표 | 정의 | 목표 |
|---|---|---|
| `retrieval@1` | top-1 청크의 source가 expected_source와 일치하는 비율 | ≥ 0.70 |
| `retrieval@4` | top-4 청크 중 하나라도 expected_source 포함 비율 | ≥ 0.90 |
| `citation_present` | citations 비어있지 않은 비율 | ≥ 0.95 |
| `answer_faithfulness` | LLM-as-judge로 answer/reference 의미 일치 | ≥ 0.80 |
| `advice_classification_acc` | ADVICE 질문이 ADVICE로 분류되는 비율 | ≥ 0.90 |

산출물: `eval/report.md` (마크다운, gitignore — 포트폴리오 첨부용 별도 보관)

## 테스트

```powershell
pytest -v
```

총 36개 테스트 (schemas 6 + claude_client 4 + retriever 3 + chain 5 + router_classifier 4 + main_endpoints 5 + recommender 5 + data_generator 4).

## Spring 통합

Spring `RagClient`가 환경 변수 `AI_SERVICE_URL`(기본 `http://localhost:8000`)로 본 서비스를 호출. `AiService.chat()`이 `IntentRouter`로 분기하여:

- **KNOWLEDGE**: `/chat/rag` 호출 → RAG 답변 + citation
- **ADVICE**: Spring에서 Claude API 직접 호출 (개인화 시스템 프롬프트)
- **RAG 실패**: ADVICE 경로로 우아하게 폴백

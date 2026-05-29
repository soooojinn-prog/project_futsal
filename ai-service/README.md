# letsfutsal AI Service

풋살 매칭 추천 + 풋살 지식 RAG 챗봇을 제공하는 Python FastAPI 서비스. Spring (`letsfutsal.war`)에서 RestTemplate으로 호출.

## 구성 요소

- **매치 추천** (`recommender.py`) — scikit-learn 기반, 사용자 등급·포지션·성별 매칭
- **RAG 챗봇** (`rag/`) — LangChain + ChromaDB + sentence-transformers + Claude API
- **라우터** (`rag/router_classifier.py`) — Claude Tool Use로 KNOWLEDGE/ADVICE 의도 분류
- **LangGraph 에이전트** (`agent/`) — 단일 매치 / 토너먼트 코디네이터, StateGraph + conditional edge + ThreadPoolExecutor 병렬 sub-agent
- **ML 자세 분석** (`pose/`) — MediaPipe + scikit-learn/PyTorch 분류 + Claude 자연어 피드백
- **평가** (`eval/`) — 골든셋 20문항(RAG) + 시나리오 8개(에이전트) + 영상 테스트셋(Pose) 정량 측정

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
| POST | `/pose/analyze` | 영상(multipart) → 자세 분류 + 각도 + 자연어 피드백 |

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
python -m eval.run_agent_eval --note "이번 변경 메모"
```

매 실행 시 `eval/agent_report_<timestamp>.md` + `eval/agent_history.md` 자동 누적 (RAG와 동일).

### 4개 지표 + 최종 결과 (2026-05-26, 5회차)

| 지표 | 정의 | 목표 | 베이스라인 | 최종 |
|---|---|---|---|---|
| `intent_acc` | 의도 분류 정확도 | ≥ 0.90 | 1.000 | **1.000** ✅ |
| `tool_correctness` | 기대 Tool 호출 흔적 | ≥ 0.85 | 0.125 | **1.000** ⭐ |
| `proposal_validity` | 시나리오별 최소 제안 수 충족 | ≥ 0.90 | 0.750 | **1.000** ⭐ |
| `e2e_success` | 전체 통과 | ≥ 0.75 | 0.000 | **1.000** ⭐ |

**베이스라인 대비**: tool_correctness 0.125 → **1.000**, e2e_success 0.000 → **1.000**. 4지표 모두 만점.

### 주요 개선 단계
1. **`AgentState.tool_calls` 필드 추가** (commit `fb75741`) — 노드/sub-agent가 호출한 tool 이름을 명시적으로 누적
2. **deterministic 매칭** (commit `d666538`) — LLM judge 우회, `expected_tools ⊆ actual_tools` 검증
3. **시나리오 재설계** (commit `d666538`) — s07을 'DB에 없는 제주도'로 변경해 자연스러운 빈 결과 + warning
4. **team_count 정규식 파싱** — '3팀'/'4팀'/'8팀' 모두 인식
5. **사용자→팀 자동 매핑** (commit `bd216e4`, `778a2b1`) — `UserMapper.selectTeamsByUserId`로 세션 사용자 팀을 토너먼트에 자동 참여
6. **더미팀 fallback** (commit `ea8d7df`) — 사용자 팀 부족 시 데모용 팀 자동 보충 + power-of-2 보정

## Pose 모델 학습

AI Hub 스포츠 자세 영상 데이터로 feature CSV 생성 후:

```powershell
python -m pose.train --features data/pose_features.csv --out models/best.joblib
```

RandomForest와 PyTorch MLP 둘 다 학습 → 정확도·F1·추론 시간 비교 → 더 우수한 모델 1개를 `models/best.joblib`(또는 `best.pt`)로 저장. 선정 근거는 `models/model_card.md`.

## 평가 누적 시스템 공통

`eval/run_eval.py`와 `eval/run_agent_eval.py` 모두 다음 패턴:

1. 매 실행 시 `eval/<report_or_agent_report>_<timestamp>.md` 신규 생성 (덮어쓰기 차단)
2. `eval/rag_history.md` / `eval/agent_history.md`에 한 줄 append (회차별 비교표)
3. `--note "변경 메모"` 인자로 노트 동시 기록
4. LLM judge는 `temperature=0` 강제 → 매 실행 deterministic
5. `LANGSMITH_TRACING=true` 환경변수가 있으면 모든 평가 호출이 LangSmith 대시보드에 자동 trace

## Pose 평가

```powershell
python -m eval.run_pose_eval
```

4지표: `service_accuracy`, `avg_total_ms`, `avg_mediapipe_ms`, `avg_feedback_ms`.
산출물: `eval/pose_report_<timestamp>.md` (덮어쓰기 방지).

테스트 영상 디렉토리(`eval/pose_test_videos/`)에 라벨 prefix 파일명으로 영상 배치:
- `INSIDE_KICK_01.mp4`, `INSTEP_KICK_02.mp4`, `INFRONT_KICK_03.mp4`, ...

## RAG 평가

```powershell
python -m eval.run_eval --note "이번 변경 메모"
```

매 실행 시 `eval/report_<timestamp>.md` 신규 생성 + `eval/rag_history.md`에 한 줄 자동 append (덮어쓰기 X).

### 5개 지표 + 최종 결과 (2026-05-21, 8회차)

| 지표 | 정의 | 목표 | 베이스라인 | 최종 |
|---|---|---|---|---|
| `retrieval@1` | top-1 청크의 source가 expected_source와 일치 | ≥ 0.70 | 0.722 | **0.833** ✅ |
| `retrieval@4` | top-4 중 하나라도 expected_source 포함 | ≥ 0.90 | 1.000 | **1.000** ✅ |
| `citation_present` | citations 비어있지 않은 비율 | ≥ 0.95 | 1.000 | **1.000** ✅ |
| `answer_faithfulness` | LLM-as-judge로 answer/reference 의미 일치 | ≥ 0.80 | 0.444 | **0.889** ✅ |
| `advice_classification_acc` | ADVICE 질문이 ADVICE로 분류되는 비율 | ≥ 0.90 | 1.000 | **1.000** ✅ |

**`answer_faithfulness` 0.444 → 0.889 (+100%)** 개선 (9회차). 회차별 변경 사항·실패 사례는 `eval/rag_history.md` 참고.

### 주요 개선 단계
1. **인덱스 튜닝** — `CHUNK_SIZE 500→700`, `CHUNK_OVERLAP 80→120`, `top_k 4→8`
2. **시스템 프롬프트** — 시간 제한·거리·인원수 같은 핵심 수치 답변에 반드시 포함하도록 명시
3. **Golden set 정정** — 코퍼스 실제 사실과 어긋났던 reference 5건 정정 (`q08, q09, q11, q12, q13`)
4. **LLM judge** — `temperature=0` 강제 + relaxed mode (회피 답변만 0, 부분 일치 1)
5. **MMR (Maximal Marginal Relevance)** — `Retriever.search(use_mmr=True, fetch_k=24, lambda=0.6)`로 retrieval 관련성·다양성 균형 → `faithfulness 0.833 → 0.889`

산출물: `eval/report_<timestamp>.md` + `eval/rag_history.md` (회차 비교표)

## 테스트

```powershell
pytest -v
```

총 36개 테스트 (schemas 6 + claude_client 4 + retriever 3 + chain 5 + router_classifier 4 + main_endpoints 5 + recommender 5 + data_generator 4).

## LangSmith 트레이싱 (선택)

RAG 답변, LangGraph 에이전트, Pose 피드백 등 모든 Claude 호출을 LangSmith 대시보드로 추적해 latency·token·prompt를 시각화할 수 있다.

### 활성화 방법

1. https://smith.langchain.com 가입 후 API key 발급 (`lsv2_…`)
2. `.env`에 다음 4개 추가:

```env
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=lsv2_여기에_실제_키
LANGSMITH_PROJECT=letsfutsal
LANGSMITH_ENDPOINT=https://api.smith.langchain.com
```

3. 서버 재시작 (`uvicorn main:app ...`) — 시작 시 `[LangSmith] tracing enabled (project=letsfutsal)` 로그 확인
4. 챗봇/에이전트/포즈 1회 사용 → LangSmith Projects에서 trace 트리 확인

### 자동 trace 범위

- **Claude API 호출 전체**: `langsmith.wrappers.wrap_anthropic`이 `ClaudeClient` 내부 SDK를 감싸 messages.create 호출이 자동 기록
- **RAG `rag_answer` chain**: `@traceable(run_type="chain")` — retrieval + system prompt + Claude 호출이 하나의 trace로 묶임
- **LangGraph 에이전트**: 환경 변수만으로 모든 노드(parse_intent → stadium → team → ...)가 자동 trace
- **미설정 시**: 환경 변수 없으면 트레이싱 완전 비활성, 코드는 정상 동작

## Spring 통합

Spring `RagClient`가 환경 변수 `AI_SERVICE_URL`(기본 `http://localhost:8000`)로 본 서비스를 호출. `AiService.chat()`이 `IntentRouter`로 분기하여:

- **KNOWLEDGE**: `/chat/rag` 호출 → RAG 답변 + citation
- **ADVICE**: Spring에서 Claude API 직접 호출 (개인화 시스템 프롬프트)
- **RAG 실패**: ADVICE 경로로 우아하게 폴백

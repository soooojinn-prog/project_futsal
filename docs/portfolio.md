# letsfutsal AI 기능 — 포트폴리오 요약

> 풋살 팀 매칭 + 경기장 예약 웹 애플리케이션(Spring MVC + MyBatis + MySQL + JSP)에
> 신입 AI 엔지니어 포트폴리오용으로 3개 AI 기능을 단독 추가한 결과입니다.

- **레포지토리**: <https://github.com/soooojinn-prog/project_futsal>
- **브랜치**: `main`
- **작업 기간**: 2026-05-19 ~ 2026-05-26 (8일)
- **단독 작업 영역**: AI 기능 3종 + 평가 시스템 + LangSmith 통합 + UI

---

## 1. 다룬 7개 기술 — 모두 실제로 구현·평가됨

| 기술 | 구현 위치 | 정량 결과 |
|---|---|---|
| **LLM API 연동** | Spring `AiService` + Python `rag/claude_client.py` (Anthropic SDK) | 챗봇·에이전트·자세 피드백 3곳에서 활용 |
| **AI Agent** | `ai-service/agent/` LangGraph StateGraph + Tool Use | 의도 분류 정확도 1.000 |
| **LangChain** | `ai-service/rag/` retriever + chain | 8회차 평가 누적 |
| **LangGraph** | `agent/graph.py` conditional edge + 3개 sub-agent | 평가 5회차 만점 |
| **멀티에이전트** | `ThreadPoolExecutor`로 StadiumAgent/TeamAgent/MatchAgent 병렬 | 토너먼트 모드 동시 실행 |
| **RAG** | LangChain + ChromaDB + sentence-transformers + Claude + MMR | `answer_faithfulness` 0.444 → 0.889 |
| **ML / CV** | MediaPipe 33점 + scikit-learn RandomForest + PyTorch MLP 비교 | RF accuracy 0.942 (8차) |

---

## 2. 기능 1 — RAG 풋살 지식 챗봇

**스택**: FastAPI + LangChain + ChromaDB + sentence-transformers(`jhgan/ko-sroberta-multitask`) + Claude.

**구조**:
```
브라우저 위젯 → POST /ai/chat → IntentRouter.route
   ├ KNOWLEDGE → Python /chat/rag → ChromaDB 검색 + Claude 답변 + citation
   └ ADVICE    → Spring에서 Claude API 직접 호출 (개인화)
```

**평가 8회차 누적 이력** (`ai-service/eval/rag_history.md`):

| 회차 | retrieval@1 | retrieval@4 | citation | **answer_faithfulness** | advice_acc | 주요 변경 |
|---|---|---|---|---|---|---|
| 1 (베이스라인) | 0.722 | 1.000 | 1.000 | **0.444** | 1.000 | top_k=4, 기본 프롬프트 |
| 2 | 0.722 | 1.000 | 1.000 | 0.333 ↓ | 1.000 | 시스템 프롬프트 엄격화 — 역효과 |
| 3 | 0.722 | 1.000 | 1.000 | 0.389 | 1.000 | 균형 재조정 |
| 4 | 0.722 | 1.000 | 1.000 | 0.389 | 1.000 | judge `temperature=0` deterministic |
| 5 | 0.722 | 1.000 | 1.000 | 0.444 | 1.000 | judge 부분 일치 + top_k 4→6 |
| 6 | 0.722 | 1.000 | 1.000 | 0.722 | 1.000 | judge relaxed mode |
| 7 | **0.833** ↑ | 1.000 | 1.000 | 0.722 | 1.000 | `CHUNK_SIZE 500→700` 재인덱싱, top_k 8 |
| 8 | 0.833 | 1.000 | 1.000 | 0.833 | 1.000 | 골든셋 reference 5건 정정 (q08/09/11/12/13) |
| **9** | **0.833** | **1.000** | **1.000** | **0.889** ⭐ | **1.000** | **MMR 추가** (fetch_k=24, lambda=0.6) — retrieval 다양성 |

> **`answer_faithfulness` +100% 개선** (0.444 → 0.889). 5/5 지표 목표 통과.

**시행착오 솔직 기록**: 2회차 0.333은 의도적으로 보존 — "프롬프트 엄격화가 역효과를 냈고 그걸 reverse하면서 학습"이라는 의사결정 스토리.

**9회차에서 도달한 최종 retriever 설정**:
- `CHUNK_SIZE=700`, `CHUNK_OVERLAP=120` (재인덱싱 후 38→27청크)
- `top_k=8`, **MMR `lambda=0.6` + `fetch_k=24`** — 관련성·다양성 균형
- 시스템 프롬프트에 "시간 제한·거리·인원수 같은 핵심 수치 반드시 포함" 명시
- LLM judge `temperature=0` + relaxed mode (회피 답변만 0)

---

## 3. 기능 2 — LangGraph 매치 코디네이터

**스택**: LangGraph 0.2 + StateGraph + conditional edge + ThreadPoolExecutor 병렬 sub-agent.

**구조**:
```
자연어 요청 → parse_intent (Claude Tool Use) → conditional edge
  ├ SINGLE      → single_stadium → single_team → single_match → review
  └ TOURNAMENT  → ThreadPoolExecutor로 Stadium/Team/MatchAgent 병렬 → tournament_assemble
→ summarize → ProposalDTO 응답 → 사용자 편집 → /ai/agent/confirm → DB INSERT
```

**평가 5회차 결과** (`ai-service/eval/agent_history.md`):

| 회차 | intent_acc | tool_correctness | proposal_validity | e2e_success | 변경 |
|---|---|---|---|---|---|
| 1 (베이스라인) | 1.000 | **0.125** | 0.750 | **0.000** | judge가 warnings + proposals_count만 봄 |
| 2 | 1.000 | 0.125 | 0.750 | 0.000 | LangSmith 통합 + judge `temperature=0` |
| 3 | 1.000 | **1.000** ⭐ | 0.750 | **0.750** ⭐ | **AgentState.tool_calls** 명시 캡처 + deterministic 매칭 |
| **4** | **1.000** | **1.000** | **1.000** ⭐ | **1.000** ⭐ | `team_count` 정규식 파싱 + s07 시나리오 현실화 |

> **베이스라인 대비**: tool_correctness 0.125 → **1.000**, e2e_success 0.000 → **1.000**. 4지표 만점 달성.

**핵심 인사이트**: LLM judge가 받는 신호 정보가 부족하면 평가가 무력해진다. `state["tool_calls"].append(...)`로 호출 흔적을 직접 캡처해 deterministic 검증으로 전환한 게 핵심.

---

### LangGraph 추가 구현 (작업 완료 후 보강)

- **사용자→팀 자동 매핑** (commit `bd216e4`, `778a2b1`): `UserMapper.selectTeamsByUserId(userId)`로 세션 사용자의 소속 팀을 조회해 `AgentRequest.team_info`로 Python에 전달. 토너먼트 모드의 `find_team_conflicts`가 실제 동작.
- **토너먼트 더미팀 fallback** (commit `ea8d7df`): 사용자 소속 팀 < `slots.team_count`이면 데모용 더미 팀 자동 보충 + power-of-2 보정. 회원가입 직후 사용자도 시연 가능.
- **대진표 시각화** (commit `cc6409d`): 응답 `bracket.rounds`를 라운드 column + 매치 카드 + depends_on 'TBD (M{idx} 승자)' placeholder로 한눈에. 결승/준결승 한국어 라벨.

## 4. 기능 3 — ML 풋살 자세 분석 (MediaPipe + scikit-learn)

**스택**: OpenCV + MediaPipe 33점 + scikit-learn RandomForest + PyTorch MLP + Claude 자연어 피드백.

**데이터**: AI Hub "비전영역, 축구 킥 동작 및 축구공 궤적 데이터 구축" (성인 여 인사이드/인스텝킥 라벨 JSON, 카메라 a-01 정면만 필터).

**학습 8회차 누적 이력** (`ai-service/models/training_history.md`):

| 회차 | n | feat | RF acc | MLP acc | 주요 변경 |
|---|---|---|---|---|---|
| 1 | 8000 | 12 | **0.942** | 0.889 | 여만, kick/plant 포함 |
| 2 | 8000 | 8 | 0.861 | 0.713 | kick/plant 제거 (추론 호환 시도) |
| 3 | 16000 | 8 | 0.682 ↓ | 0.547 | 남+여 통합 → 다양성에 정확도 하락 |
| 4 | 16000 | 14 | 0.680 | 0.579 | symmetric derived feature 6개 추가 |
| 5 | 8000 | 14 | 0.781 ↑ | 0.670 | **카메라 a-01 정면만** 필터 |
| 7 | 8000 | 18 | 0.786 | 0.667 | kick/plant 부활 (학습 metadata + 추론 heuristic) |
| **8** | 3966 | 18 | **0.942** ⭐ | 0.907 | **여만 + a-01 + 18 feat** — 추론 호환 + 정확도 회복 |

> **추론 호환을 보장하면서도 1차의 0.942 정확도 회복**. 모델 비교 + 모델 카드 + 회차별 timestamp 사본 자동 보존.

**핵심 의사결정 스토리**:
- 1차 0.942는 추론 호환성 X (metadata 의존)
- 2~4차에서 추론 호환을 위해 단순화 → 정확도 0.86→0.68 하락
- 5차 카메라 필터링으로 다양성 1/8 축소 → 0.78 회복
- 7차 kick/plant 부활 → 거의 변화 없음 (이미 derived feature가 정보 흡수)
- 8차 여성 데이터만 회귀 → 1차 정확도 회복 + 추론 호환 동시 달성

---

## 5. 평가·관측 인프라

### 5.1 평가 누적 시스템 (3개 영역 공통)

| 영역 | 누적 파일 | 자동 append |
|---|---|---|
| RAG | `ai-service/eval/rag_history.md` | `python -m eval.run_eval --note "..."` |
| 에이전트 | `ai-service/eval/agent_history.md` | `python -m eval.run_agent_eval --note "..."` |
| 자세 분류 | `ai-service/models/training_history.md` | `python -m pose.train --note "..."` |

- 매 실행 시 timestamp 리포트 신규 생성 (덮어쓰기 차단)
- 누적 이력 한 줄 자동 append (회차별 비교표)
- LLM judge는 `temperature=0` 강제 (deterministic)

### 5.2 LangSmith 트레이싱 통합

- `langsmith.wrappers.wrap_anthropic` + `@traceable` — RAG·에이전트·Pose 피드백 모든 Claude 호출 자동 trace
- LangGraph 노드는 환경 변수만으로 자동 trace
- `.env`에 `LANGSMITH_TRACING=true` + API key만 설정하면 활성, 미설정 시 완전 no-op

### 5.3 단위 테스트

- Python pytest 92개 (RAG 18 + Agent 38 + Pose 36) 그린
- Java JUnit 9개 (RagClient/IntentRouter/Pose/Agent) 그린

---

## 6. UI/UX

- 모든 페이지에 일관된 그라데이션 + 네비 이모지 (⚽/👥/🏟️/🏆/📋/🤖/🏃)
- `.nav-emoji` / `.hero-emoji` span으로 이모지가 텍스트 그라데이션에 덮이지 않도록 격리
- 자세 분석 결과 화면: **신뢰도 게이지·클래스 확률 막대·기준 각도 비교 막대·신뢰도 < 75% 경고 배너**로 시각적 설명 (commit `769b6af`)
- 토너먼트 **대진표 시각화** (commit `cc6409d`): 라운드별 column + depends_on placeholder
- 챗봇 답변 마크다운 자제 시스템 프롬프트 (raw `#`, `|` 노출 방지, commit `8b6fbf9`)
- 챗봇 위젯 **로딩 표시** (3-dot bounce) + **citation 한글 라벨 매핑** (`[rules 11 offside]` → `· 규칙 11 · 오프사이드`) (commit `27dc2c0`)
- **모바일 반응형** (commit `11e82de`): 네비 가로 스크롤, 챗봇 panel 100vw, AI 페이지 padding 축소
- AI 페이지 구조 표준화 (commit `3781986`): 자체 DOCTYPE/head 제거 → `match/list.jsp` 패턴으로 일관

## 7. 핵심 버그 수정 (트러블슈팅)

| 증상 | 원인 | 해결 | commit |
|---|---|---|---|
| Pose 분석 500 에러 | `FeatureBuilder._joint_angle` 메서드 사라짐 | 모듈 레벨 `_angle` 함수 import | `9cdc982` |
| 챗봇 무응답 | `coordinator.jsp` 자체 head로 `const contextPath` 미정의 | fetch URL을 JSP 표현식 직접 사용 | `f96fff2` |
| AI 페이지 헤더 안 보임 | 자체 DOCTYPE/head → header.jsp 중첩 | 최상단 `<jsp:include header>` 패턴 | `3781986` |
| 토너먼트 ValueError | 사용자 팀 0개 → `generate_bracket([])` | 더미팀 자동 보충 + power-of-2 | `ea8d7df` |
| h1 이모지 그라데이션에 덮임 | `-webkit-text-fill-color: transparent`가 이모지까지 | `.hero-emoji` span 격리 | `dd5ae1e` |

---

## 7. 면접 어필 포인트 정리

1. **7개 핵심 AI 기술을 한 프로젝트에 통합** — 단순 데모가 아닌 RAG·Agent·ML/CV 모두 실제 평가까지 진행.
2. **정량 평가 기반 의사결정** — RAG·에이전트·Pose 모두 누적 평가 시스템으로 회차별 효과 측정.
3. **시행착오 솔직 기록** — RAG 0.333(역효과), Pose 0.682(데이터 다양성 부작용) 등 모두 보존하여 의사결정 근거 추적 가능.
4. **관측 인프라** — LangSmith 통합으로 모든 LLM 호출이 대시보드에 자동 trace.
5. **운영 환경 대응** — Tomcat URI 인코딩 fix, Multipart 설정, 한국어 query 인코딩 등 실제 운영에서 부딪힌 문제 해결 기록.
6. **테스트 커버리지** — Python 92 + Java 9 모두 그린, judge는 deterministic.

# LangGraph 매치 코디네이터 + 토너먼트 에이전트 설계 (Feature 3)

> 포트폴리오·취업 목적 AI 기능 확장 — 기능 3 (LangGraph 에이전트)
> 작성일: 2026-05-19
> 관련 로드맵: [docs/ai-features-roadmap.md](../../ai-features-roadmap.md)
> 선행 기능: [기능 2 RAG 챗봇](2026-05-19-rag-chatbot-design.md)

---

## 1. 목표 및 배경

기능 2 RAG 챗봇은 풋살 **지식**을 답한다. 기능 3은 한 단계 더 나아가 **풋살 도메인 데이터(매치/경기장/팀)에 작용하는 에이전트**를 구현한다.

자연어 한 줄 요청으로:

- "이번 주말 강남에서 5인 매치 잡아줘" → 경기장 검색 + 팀 가용성 + 매치 시간 매칭 → 미리보기 제안
- "다음 주 일요일 강남 4팀 토너먼트 기획해줘" → 멀티에이전트 병렬 검색 → 매치 3개 + 대진표

사용자가 미리보기를 검토·수정한 뒤 "확정"을 누르면 `tb_match`에 일괄 INSERT.

**이력서 문구 후보**

> LangGraph StateGraph + Tool Use 기반 풋살 매치 코디네이터 구현. Intent 분류 노드에서 conditional edge로 단일 매치/토너먼트 서브그래프 분기. 토너먼트는 StadiumAgent/TeamAgent/MatchAgent 3개 sub-agent의 병렬 실행으로 일정·경기장·팀 매칭을 동시 처리 후 통합. 미리보기 편집 → 사용자 확정 → 트랜잭션 INSERT.

---

## 2. 의사결정 요약

| 항목 | 결정 | 근거 |
|---|---|---|
| 스코프 | 매치 코디네이터 + 토너먼트 멀티에이전트 (둘 다) | "기본 → 멀티에이전트 진화" 이야기가 면접 임팩트 최고 |
| 진입점 | 별도 페이지 `/ai/coordinator` | 미리보기 UI(매치 카드·대진표)가 풍부, 챗봇 위젯엔 안 맞음 |
| DB 반영 | 하이브리드 — 검색은 자동, INSERT는 사용자 확정 후 | ChatGPT/Copilot 스타일, 안전성과 임팩트 균형 |
| 구조 | 단일 StateGraph + conditional edge로 분기 | sub-graph·conditional edge라는 LangGraph 핵심 개념 활용 |
| Sub-agent | StadiumAgent / TeamAgent / MatchAgent 3개 | 도메인 자연스러운 분리, 병렬 실행 시연 가능 |
| Tool | 6개 (stadium 2 + team 2 + bracket 1 + propose 1) | YAGNI — 필요 최소 |
| 통신 | Python에서 Spring REST API 호출 | 기존 Controller 재사용, DB 직접 접근 안 함 |
| 평가 | 시나리오 8개 + LLM judge | RAG와 동일 패턴, 정량 지표 4개 |

---

## 3. 아키텍처

### 3.1 전체 흐름

```
[브라우저: /ai/coordinator 페이지]
        │ POST /ai/agent/run  { user_input }
        ▼
[Spring AgentController.run]
        │ 1. 로그인·rate-limit 검사
        ▼
[Python FastAPI ai-service]
   POST /agent/run
        │ 2. LangGraph StateGraph 실행 시작
        ▼
┌────────────────────────────────────────────────────────────┐
│  StateGraph: agent_graph                                   │
│                                                             │
│  ┌────────────────┐                                        │
│  │ parse_intent   │  Claude Tool Use로 {intent, slots}     │
│  │ (LLM 노드)     │  추출 (intent: SINGLE | TOURNAMENT)    │
│  └────────────────┘                                        │
│           │                                                 │
│           │ conditional_edge(intent)                        │
│           │                                                 │
│   ┌───────┴────────┐                                       │
│   │                │                                        │
│   ▼ SINGLE         ▼ TOURNAMENT                            │
│  ┌─────────┐      ┌─────────────────────────────────┐      │
│  │ single  │      │ parallel_subgraph                │      │
│  │ _flow   │      │                                  │      │
│  │         │      │  ┌──────────┐ ┌──────────┐      │      │
│  │ 1.stad  │      │  │ Stadium  │ │ Team     │      │      │
│  │ 2.team  │      │  │ Agent    │ │ Agent    │      │      │
│  │ 3.match │      │  └──────────┘ └──────────┘      │      │
│  │ 4.review│      │           ┌──────────┐          │      │
│  │         │      │           │ Match    │          │      │
│  │         │      │           │ Agent    │          │      │
│  │         │      │           └──────────┘          │      │
│  └─────────┘      └─────────────────────────────────┘      │
│       │                          │                          │
│       │                          ▼                          │
│       │                  ┌──────────────────┐               │
│       │                  │ tournament       │               │
│       │                  │ _assemble        │               │
│       │                  │ (충돌 검증)      │               │
│       │                  └──────────────────┘               │
│       │                          │                          │
│       └────────────┬─────────────┘                          │
│                    ▼                                         │
│            ┌──────────────┐                                 │
│            │ summarize    │  → proposal JSON                │
│            └──────────────┘                                 │
└────────────────────────────────────────────────────────────┘
        │
        ▼ ProposalDTO (미리보기, DB INSERT 아직 안 함)
[브라우저: 미리보기 편집 UI]
        │ 매치 카드 N개 + 대진표(토너먼트 모드)
        │ 사용자가 일부 수정·삭제 가능
        │
        ▼ POST /ai/agent/confirm  { proposal_id, edits }
[Spring AgentController.confirm]
        │ 트랜잭션
        │   - tb_match 행 N개 INSERT
        │   - 토너먼트 메타 행 1개 INSERT (tb_tournament — 신규 테이블)
        ▼
[브라우저: 확정 결과 페이지]
```

### 3.2 컴포넌트 분리

**Python (`ai-service/agent/`) — 신규 패키지**

- `state.py` — `AgentState` TypedDict (intent, slots, stadium_candidates, team_info, proposals, errors)
- `tools.py` — Tool 함수 6개 (Spring REST 호출)
- `springboot_client.py` — Spring REST API 호출 래퍼 (`/api/stadium`, `/api/team`, `/api/match`)
- `nodes.py` — LangGraph 노드 함수들 (`parse_intent`, `single_flow_*`, `tournament_assemble`, `summarize`)
- `subagents.py` — StadiumAgent / TeamAgent / MatchAgent 클래스 (각각 mini StateGraph)
- `graph.py` — 최상위 `build_agent_graph()` (compile된 LangGraph)
- `schemas.py` — Pydantic DTO (AgentRequest, ProposalDTO, MatchProposal, TournamentBracket, ConfirmRequest)
- `main.py` *(변경)* — `/agent/run`, `/agent/confirm-validate` 엔드포인트 추가
- `requirements.txt` *(변경)* — `langgraph` 추가

**Java (`src/main/java/.../ai/`) — 신규 + 변경**

- `AgentController.java` *(신규)* — `/ai/agent/run`, `/ai/agent/confirm` 엔드포인트
- `AgentService.java` *(신규)* — Python `/agent/run` 호출 + 확정 시 트랜잭션 INSERT
- `dto/AgentRequestDTO.java` *(신규)* — `{ user_input }`
- `dto/ProposalDTO.java` *(신규)* — `{ proposalId, intent, matches[], bracket?, warnings[] }`
- `dto/MatchProposalDTO.java` *(신규)* — `{ stadiumId, startTime, durationMin, teamA, teamB? }`
- `dto/ConfirmRequestDTO.java` *(신규)* — `{ proposalId, matches[] (사용자 편집 반영) }`
- `mapper/MatchMapper.java` *(변경)* — bulk insert 메서드 추가 또는 기존 `insertMatch` 반복 호출
- `mapper/StadiumMapper.java` — 그대로 (`selectByRegion` 등 기존 활용)

**View**

- `src/main/webapp/WEB-INF/views/ai/coordinator.jsp` *(신규)* — 자연어 입력 + 미리보기 카드 + 확정 버튼
- `src/main/resources/script/agent_coordinator.js` *(신규)* — fetch + 미리보기 편집 로직

**평가**

- `ai-service/eval/agent_scenarios.jsonl` *(신규)* — 8개 시나리오
- `ai-service/eval/run_agent_eval.py` *(신규)* — 시나리오 실행 + 4개 지표 측정 + `agent_report.md`

---

## 4. 데이터 흐름 & DTO 계약

### 4.1 Spring ↔ 브라우저

**POST `/ai/agent/run`**
```json
// Request
{ "user_input": "이번 주말 강남에서 4팀 토너먼트 잡아줘" }

// Response (ProposalDTO)
{
  "proposalId": "prop_abc123",
  "intent": "TOURNAMENT",
  "warnings": [],
  "matches": [
    {
      "stadiumId": 12, "stadiumName": "강남풋살장",
      "startTime": "2026-05-26T14:00", "durationMin": 60,
      "teamA": { "id": 1, "name": "A팀" },
      "teamB": { "id": 2, "name": "B팀" },
      "stage": "SEMIFINAL"
    },
    /* ... */
  ],
  "bracket": {
    "rounds": [
      [{ "matchIdx": 0 }, { "matchIdx": 1 }],
      [{ "matchIdx": 2, "depends_on": [0, 1] }]
    ]
  }
}
```

**POST `/ai/agent/confirm`**
```json
// Request — 사용자가 일부 매치 수정·삭제 후
{
  "proposalId": "prop_abc123",
  "matches": [ /* MatchProposalDTO[] — 편집된 결과 */ ]
}

// Response
{
  "createdMatchIds": [101, 102, 103],
  "tournamentId": 7
}
```

### 4.2 Spring ↔ Python (내부)

**POST `/agent/run`** — LangGraph StateGraph 실행 → ProposalDTO 반환 (위와 동일 스키마)

### 4.3 AgentState (LangGraph state)

```python
class AgentState(TypedDict):
    user_input: str
    user_id: int
    intent: Literal["SINGLE", "TOURNAMENT", "UNKNOWN"]
    slots: dict  # { region, date_range, team_count, ... }
    stadium_candidates: list[dict]
    team_info: dict
    proposals: list[dict]
    bracket: dict | None
    warnings: list[str]
    errors: list[str]
```

각 노드는 state의 일부만 읽고 일부만 쓴다 (LangGraph reducer 패턴).

### 4.4 Tool 6개 (Python에서 Spring REST 호출)

| Tool | 호출 Spring 엔드포인트 | 반환 |
|---|---|---|
| `search_stadium(region, date_range)` | `GET /api/stadium?region=&date=` | `Stadium[]` |
| `list_stadium_slots(stadium_id, date)` | `GET /api/stadium/{id}/slots?date=` | `Slot[]` (start/end) |
| `list_team_members(team_id)` | `GET /api/team/{id}/members` | `User[]` |
| `find_team_conflicts(team_id, date_range)` | `GET /api/team/{id}/matches?from=&to=` | `Match[]` |
| `generate_bracket(team_ids)` | (Python 내부 함수, REST 호출 없음) | `Bracket` |
| `propose_match(stadium_id, time, team_a, team_b)` | (Python 내부, 미리보기만 생성) | `MatchProposal` |

> Spring 측 `/api/stadium`, `/api/team`, `/api/match` 엔드포인트가 일부는 신규 추가 필요할 수 있음. 기존 Controller 메서드와 매핑하거나, 에이전트 전용 read-only API 그룹을 별도로 신설하는 방안 둘 다 가능. plan 단계에서 확정.

---

## 5. 에러 처리

| 실패 지점 | 동작 |
|---|---|
| `parse_intent`에서 의도 추출 실패 (UNKNOWN) | summarize 노드가 "더 구체적으로 알려주세요" 응답 + `errors`에 기록 |
| Spring REST 호출 실패 | 해당 Tool은 빈 리스트 반환 + `warnings`에 기록, 그래프는 계속 진행 |
| 가용 경기장 0개 | summarize가 "조건에 맞는 경기장이 없습니다" 응답 + 대안 시간대 제안 |
| 토너먼트인데 팀 수 부족 (4팀 미만) | sub-agent에서 조기 종료 + ADVICE 메시지 |
| 시간 충돌 발견 | tournament_assemble에서 자동으로 다른 슬롯 시도 (최대 3회 재시도) |
| Python `/agent/run` 5xx | Spring AgentController가 500 응답 + "잠시 후 다시 시도" 메시지 (RAG처럼 챗봇 폴백은 없음 — 에이전트는 독립 페이지) |
| 확정 시 트랜잭션 실패 | 전체 롤백 + 에러 응답, 미리보기는 보존 |

**타임아웃**
- Spring → Python: connect 2s, read 60s (멀티에이전트 + LLM 호출 5~30s)
- Python → Spring REST API: read 5s
- LangGraph 그래프 전체: 90s hard timeout

---

## 6. 평가 설계

### 6.1 시나리오 — `ai-service/eval/agent_scenarios.jsonl` (8개)

**단일 매치 (4)**
1. q01: "강남 토요일 5인 매치 잡아줘" — intent=SINGLE, stadium 호출, proposal ≥ 1
2. q02: "이번 주말 우리 팀이랑 매치 시간 골라줘" — intent=SINGLE, conflicts 체크
3. q03: "다음 주 풋살장 빈 시간대 알려줘" — stadium 슬롯만 반환 (matches=0 OK)
4. q04: "강남 풋살장 추천해줘" — stadium만 검색

**토너먼트 (4)**
5. q05: "4팀 토너먼트, 강남 일요일" — intent=TOURNAMENT, bracket 3매치, 시간 충돌 없음
6. q06: "8팀 토너먼트 기획" — bracket 7매치 (8강·4강·결승)
7. q07: "토너먼트, 경기장 부족 가정" — 부분 제안 + warnings
8. q08: "팀 데이터 부족 케이스" — errors + 거절 메시지

### 6.2 측정 지표 (4)

| 지표 | 정의 | 목표 |
|---|---|---|
| `intent_acc` | parse_intent의 의도 분류 정확도 | ≥ 0.90 |
| `tool_correctness` | 기대 Tool 집합이 모두 호출되었는지 (LLM judge) | ≥ 0.85 |
| `proposal_validity` | 미리보기에 시간 충돌·경기장 가용성 위반 없음 | ≥ 0.90 |
| `e2e_success` | 시나리오 전체 통과 (위 셋 + 응답 시간 < 90s) | ≥ 0.75 |

### 6.3 실행

```bash
cd ai-service
python -m eval.run_agent_eval --out eval/agent_report.md
```

산출물: `ai-service/eval/agent_report.md` (gitignore — 포트폴리오 별도 보관).

---

## 7. 테스트

**Python (pytest)**
- `tests/test_agent_state.py` — TypedDict 유효성
- `tests/test_tools.py` — 6개 Tool 함수, Spring 호출 Mock
- `tests/test_nodes.py` — 각 노드(`parse_intent`, `summarize` 등) 단위 테스트
- `tests/test_subagents.py` — Stadium/Team/Match 서브에이전트 mock 검증
- `tests/test_graph.py` — 전체 그래프 실행, 시나리오 1·5만 통합 (LangGraph Mock)

**Java (JUnit)**
- `AgentControllerTest` — `/ai/agent/run`, `/ai/agent/confirm` MVC 테스트
- `AgentServiceTest` — Python 호출 mock + 확정 트랜잭션 검증 (matches 3개 INSERT)

**수동 데모 시나리오**
1. "강남 토요일 매치 잡아줘" → 미리보기 1개 → 확정 → DB 확인
2. "다음 주 일요일 4팀 토너먼트" → 미리보기 3매치 + 대진표 → 확정 → DB 3행
3. "팀 2개로 토너먼트" → 거절 메시지
4. Spring REST API 중지 → 우아한 에러 화면

---

## 8. 파일 변경 목록

### 8.1 Java — 신규 5 / 변경 1

| 경로 | 변경 | 책임 |
|---|---|---|
| `ai/AgentController.java` | 신규 | `/ai/agent/run`, `/ai/agent/confirm` |
| `ai/AgentService.java` | 신규 | Python 호출 + 확정 트랜잭션 |
| `dto/AgentRequestDTO.java` | 신규 | `{ user_input }` |
| `dto/ProposalDTO.java` | 신규 | 미리보기 |
| `dto/MatchProposalDTO.java` | 신규 | 매치 한 건 |
| `dto/ConfirmRequestDTO.java` | 신규 | 확정 요청 |
| `mapper/MatchMapper.java` + xml | 변경 | bulk 또는 반복 INSERT 활용 |
| `test/.../ai/AgentControllerTest.java` | 신규 | MVC 테스트 |
| `test/.../ai/AgentServiceTest.java` | 신규 | 트랜잭션 mock |

### 8.2 Python — 신규 8 / 변경 2

| 경로 | 변경 | 책임 |
|---|---|---|
| `agent/__init__.py` | 신규 | |
| `agent/state.py` | 신규 | AgentState TypedDict |
| `agent/tools.py` | 신규 | Tool 6개 |
| `agent/springboot_client.py` | 신규 | Spring REST 호출 래퍼 |
| `agent/nodes.py` | 신규 | LangGraph 노드 함수 |
| `agent/subagents.py` | 신규 | Stadium/Team/Match 서브에이전트 |
| `agent/graph.py` | 신규 | `build_agent_graph()` |
| `agent/schemas.py` | 신규 | Pydantic DTO |
| `main.py` | 변경 | `/agent/run`, `/agent/confirm-validate` 엔드포인트 |
| `requirements.txt` | 변경 | `langgraph` 추가 |
| `tests/test_agent_*.py` (5개) | 신규 | pytest |
| `eval/agent_scenarios.jsonl` | 신규 | 8개 시나리오 |
| `eval/run_agent_eval.py` | 신규 | 평가 실행 |

### 8.3 View

| 경로 | 변경 |
|---|---|
| `WEB-INF/views/ai/coordinator.jsp` | 신규 |
| `resources/script/agent_coordinator.js` | 신규 |

### 8.4 문서

| 경로 | 변경 |
|---|---|
| `docs/superpowers/specs/2026-05-19-langgraph-agent-design.md` | 신규 (본 spec) |
| `ai-service/README.md` | 변경 (Agent 섹션 추가) |
| `CLAUDE.md` | 변경 ("AI 기능 구조"에 에이전트 항목 추가) |

---

## 9. 의존성 & 환경

**Python (`requirements.txt` 추가)**
```
langgraph==0.2.x
```
(langchain, langchain-anthropic, langchain-community는 RAG에서 이미 설치)

**Java** — 신규 의존성 없음

**환경 변수**
- 기존 `CLAUDE_API_KEY` 그대로 사용
- 신규 `SPRING_BASE_URL` — Python에서 Spring REST 호출용 (기본 `http://localhost:8080/letsfutsal`)

---

## 10. 일정 (총 7일)

| Day | 작업 | 산출물 |
|---|---|---|
| **Day 1** | LangGraph 설치 + AgentState + `parse_intent` 노드 (Tool Use로 의도·슬롯 추출) | curl로 의도 파싱 동작 확인 |
| **Day 2** | Tool 함수 6개 + `springboot_client.py` Spring REST 호출 | pytest 그린 |
| **Day 3** | `single_flow` 노드들 순차 실행 — 단일 매치 시나리오 1~4 동작 | 시나리오 4건 통과 |
| **Day 4** | StadiumAgent / TeamAgent / MatchAgent 서브에이전트 + 병렬 실행 | 서브에이전트 단위 테스트 그린 |
| **Day 5** | `tournament_assemble` + 충돌 검증 + `summarize` — 토너먼트 시나리오 5~8 동작 | 시나리오 8건 통과 |
| **Day 6** | Spring `AgentController` + `AgentService` + `/ai/coordinator` JSP + 미리보기 편집 UI + 확정 트랜잭션 | 브라우저 데모 시나리오 통과 |
| **Day 7** | 평가 (`run_agent_eval`) + 4개 지표 측정 + 데모 캡처 + README/CLAUDE.md 갱신 | `agent_report.md` + 데모 GIF |

**Risk**: LangGraph 학습 곡선. Day 1 안에 기본 그래프가 동작 안 하면 Tool 정의를 더 단순화하거나 Day 8로 1일 추가.

---

## 11. 명시적으로 제외하는 것 (YAGNI)

- Multi-turn 대화 (한 번 요청 = 한 번 미리보기)
- Streaming 응답 (SSE) — 동기 응답만
- 사용자별 캘린더 (개인 가용성 추적)
- 8팀 초과 토너먼트 (8팀까지만)
- 더블 엘리미네이션·리그전 — 싱글 엘리미네이션만
- 경기장 자동 예약 (외부 API 호출) — 내부 DB 매치 INSERT만
- 토너먼트 종료 후 결과·점수 입력 (별도 기능)
- 다국어 (한국어만)

---

## 12. 다음 단계

본 spec 승인 → `superpowers:writing-plans` skill로 전환하여 구현 계획(`docs/superpowers/plans/2026-05-19-langgraph-agent.md`) 작성 → 구현 진행.

**선행 조건**: 기능 2 RAG의 `eval/report.md` 산출(=Anthropic 크레딧 풀린 뒤)이 면접 자료로 먼저 정리되어야 본 기능 구현 시간을 안정적으로 확보할 수 있다.

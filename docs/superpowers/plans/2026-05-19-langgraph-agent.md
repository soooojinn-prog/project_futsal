# LangGraph 매치 코디네이터 + 토너먼트 에이전트 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 자연어 한 줄로 풋살 매치/토너먼트를 자동 기획하는 LangGraph 에이전트 구현 — 단일 매치는 순차 노드, 토너먼트는 StadiumAgent/TeamAgent/MatchAgent 3개 sub-agent 병렬 실행, 사용자 확정 후 DB INSERT.

**Architecture:** Python ai-service에 `agent/` 패키지 신설. LangGraph StateGraph에서 `parse_intent` 노드가 SINGLE/TOURNAMENT 분류 → conditional edge로 분기 → `summarize`가 ProposalDTO 반환. Spring `AgentController`가 미리보기→사용자 편집→트랜잭션 INSERT 처리.

**Tech Stack:** Python 3.12 + LangGraph 0.2 + LangChain + Anthropic SDK + FastAPI(기존). Java 21 + Spring MVC + RestTemplate + MyBatis + JSP. 테스트는 pytest / JUnit5+Mockito+AssertJ+spring-test(JDK 21 강제 필수, Mockito 호환).

**Spec:** [docs/superpowers/specs/2026-05-19-langgraph-agent-design.md](../specs/2026-05-19-langgraph-agent-design.md)

**선행 조건:** 기능 2 RAG 챗봇 완료(`feature/rag-chatbot` 브랜치에 머지됨). Anthropic 크레딧 활성 (LLM 노드·평가 judge 호출 필수).

---

## 환경 prefix (모든 mvn 명령에 사용)

```powershell
$env:JAVA_HOME = "C:\Program Files\Eclipse Adoptium\jdk-21.0.9.10-hotspot"
$mvn = "C:\Program Files\JetBrains\IntelliJ IDEA 2025.3.2\plugins\maven\lib\maven3\bin\mvn.cmd"
```

이후 plan에서 `mvn ...`은 위 두 변수 설정 + `& $mvn ...` 호출을 의미한다. Python venv는 `ai-service/venv/` 활용.

---

## File Structure

**Python (`ai-service/agent/`)** — 신규 패키지

| 경로 | 책임 |
|---|---|
| `agent/__init__.py` | 패키지 마커 |
| `agent/state.py` | `AgentState` TypedDict 정의 |
| `agent/schemas.py` | Pydantic DTO (AgentRequest, MatchProposal, Bracket, ProposalResponse, ConfirmValidateRequest) |
| `agent/springboot_client.py` | Spring REST 호출 래퍼 (`/api/agent-data/...`) |
| `agent/tools.py` | Tool 함수 6개 (search_stadium, list_stadium_slots, list_team_members, find_team_conflicts, generate_bracket, propose_match) |
| `agent/nodes.py` | LangGraph 노드 (parse_intent, single_flow_*, tournament_assemble, summarize) |
| `agent/subagents.py` | StadiumAgent / TeamAgent / MatchAgent (병렬 실행 단위) |
| `agent/graph.py` | `build_agent_graph()` — 최상위 StateGraph compile |

**Eval (`ai-service/eval/`)**

| 경로 | 책임 |
|---|---|
| `eval/agent_scenarios.jsonl` | 시나리오 8개 (SINGLE 4 + TOURNAMENT 4) |
| `eval/run_agent_eval.py` | 시나리오 실행 + 4지표 계산 + 마크다운 리포트 |

**Tests (`ai-service/tests/`)**

| 경로 | 책임 |
|---|---|
| `tests/test_agent_state.py` | AgentState TypedDict |
| `tests/test_agent_schemas.py` | Pydantic DTO |
| `tests/test_springboot_client.py` | Spring REST 호출 mock |
| `tests/test_agent_tools.py` | Tool 6개 단위 테스트 |
| `tests/test_agent_nodes.py` | parse_intent, single_flow_* 노드 |
| `tests/test_subagents.py` | Stadium/Team/Match sub-agent |
| `tests/test_agent_graph.py` | 전체 그래프 — 시나리오 1·5 mock 통합 |
| `tests/test_agent_endpoints.py` | FastAPI `/agent/run` |

**Main (`ai-service/`)** — 변경

| 경로 | 책임 |
|---|---|
| `main.py` *(변경)* | `/agent/run` 엔드포인트 추가 |
| `requirements.txt` *(변경)* | `langgraph==0.2.x` 추가 |

**Java (`src/main/java/io/github/wizwix/letsfutsal/`)**

| 경로 | 책임 |
|---|---|
| `dto/AgentRequestDTO.java` | `{ user_input }` |
| `dto/ProposalDTO.java` | `{ proposalId, intent, warnings[], matches[], bracket? }` |
| `dto/MatchProposalDTO.java` | `{ stadiumId, stadiumName, startTime, durationMin, teamA, teamB?, stage? }` |
| `dto/BracketDTO.java` | `{ rounds[][] }` |
| `dto/ConfirmRequestDTO.java` | `{ proposalId, matches[] }` |
| `dto/AgentTeamSummaryDTO.java` | `{ id, name }` (DTO 안 내장 nested) |
| `ai/AgentController.java` | `/ai/agent/run`, `/ai/agent/confirm` |
| `ai/AgentService.java` | Python 호출 + 확정 트랜잭션 |
| `ai/AgentDataController.java` | 에이전트용 read-only API (`/api/agent-data/stadium`, `/api/agent-data/team-members/{id}`, `/api/agent-data/team-conflicts/{id}`) |
| `mapper/MatchMapper.java` + xml | bulk insert (반복 호출도 가능, 트랜잭션은 Service 측) |

**Java Tests**

| 경로 | 책임 |
|---|---|
| `test/.../ai/AgentServiceTest.java` | Python mock + 확정 트랜잭션 mock |
| `test/.../ai/AgentControllerTest.java` | MockMvc MVC 테스트 (`MockMvcBuilders.standaloneSetup`) |

**View / Static**

| 경로 | 책임 |
|---|---|
| `src/main/webapp/WEB-INF/views/ai/coordinator.jsp` | 자연어 입력 + 미리보기 + 확정 |
| `src/main/webapp/resources/script/agent_coordinator.js` | fetch + 미리보기 편집 |

**Docs**

| 경로 | 책임 |
|---|---|
| `ai-service/README.md` *(변경)* | Agent 섹션 추가 |
| `CLAUDE.md` *(변경)* | "AI 기능 구조"에 에이전트 흐름 추가 |
| `docs/ai-features-roadmap.md` *(변경)* | 기능 3 완료 표시 |

---

## Decomposition Principles

- **Python을 먼저 완성**: Spring이 Python의 `/agent/run`에 의존. 그래프가 mock 시나리오로 동작하면 Java 시작.
- **TDD**: 모든 Python 클래스/노드는 실패 테스트 → 구현 → 통과 → 커밋.
- **Tool 함수는 mock으로 단위 테스트**: 실제 Spring 호출은 Task 9 끝나야 가능. 그 전까지는 Tool 단위 테스트는 `requests`/`httpx` mock.
- **LangGraph 통합 테스트는 mock Claude**: 그래프 흐름·노드 호출 순서 검증만. 실제 LLM 호출은 평가(Task 15)에서 한 번.
- **각 Task 끝에 commit + push** (저장소 컨벤션).

---

## Task 0: langgraph 의존성 추가 + agent 패키지 골격

**Files:**
- Modify: `ai-service/requirements.txt`
- Create: `ai-service/agent/__init__.py`

- [ ] **Step 1: requirements.txt에 langgraph 추가**

`ai-service/requirements.txt` 마지막 줄에 추가:
```
langgraph==0.2.55
```

- [ ] **Step 2: 가상환경에 설치**

```powershell
cd ai-service
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```
Expected: `langgraph-0.2.55` installed (langchain-core 의존성은 RAG에서 이미 설치됨).

- [ ] **Step 3: agent/__init__.py 생성**

`ai-service/agent/__init__.py`:
```python
"""LangGraph 매치 코디네이터 + 토너먼트 에이전트 모듈."""
```

- [ ] **Step 4: import 검증**

```powershell
python -c "import agent; from langgraph.graph import StateGraph; print('OK')"
```
Expected: `OK`

- [ ] **Step 5: Commit**

```powershell
git add ai-service/requirements.txt ai-service/agent/__init__.py
git commit -m "chore(agent): langgraph 의존성 추가 + agent 패키지 골격"
git push origin feature/rag-chatbot
```

---

## Task 1: AgentState TypedDict + Pydantic schemas

**Files:**
- Create: `ai-service/agent/state.py`
- Create: `ai-service/agent/schemas.py`
- Create: `ai-service/tests/test_agent_state.py`
- Create: `ai-service/tests/test_agent_schemas.py`

- [ ] **Step 1: 실패 테스트 작성 (state)**

`ai-service/tests/test_agent_state.py`:
```python
from agent.state import AgentState, make_initial_state


def test_make_initial_state_defaults():
    s = make_initial_state(user_input="강남 매치", user_id=42)
    assert s["user_input"] == "강남 매치"
    assert s["user_id"] == 42
    assert s["intent"] == "UNKNOWN"
    assert s["slots"] == {}
    assert s["stadium_candidates"] == []
    assert s["proposals"] == []
    assert s["bracket"] is None
    assert s["warnings"] == []
    assert s["errors"] == []
```

- [ ] **Step 2: 실패 확인**

```powershell
pytest tests/test_agent_state.py -v
```
Expected: FAIL — `ModuleNotFoundError: agent.state`

- [ ] **Step 3: state.py 구현**

`ai-service/agent/state.py`:
```python
from typing import Literal, TypedDict


class AgentState(TypedDict):
    user_input: str
    user_id: int
    intent: Literal["SINGLE", "TOURNAMENT", "UNKNOWN"]
    slots: dict
    stadium_candidates: list[dict]
    team_info: dict
    proposals: list[dict]
    bracket: dict | None
    warnings: list[str]
    errors: list[str]


def make_initial_state(user_input: str, user_id: int) -> AgentState:
    return AgentState(
        user_input=user_input,
        user_id=user_id,
        intent="UNKNOWN",
        slots={},
        stadium_candidates=[],
        team_info={},
        proposals=[],
        bracket=None,
        warnings=[],
        errors=[],
    )
```

- [ ] **Step 4: state 테스트 통과 확인**

```powershell
pytest tests/test_agent_state.py -v
```
Expected: 1 passed.

- [ ] **Step 5: 실패 테스트 작성 (schemas)**

`ai-service/tests/test_agent_schemas.py`:
```python
from agent.schemas import (
    AgentRequest,
    BracketDTO,
    ConfirmValidateRequest,
    MatchProposal,
    ProposalResponse,
    TeamSummary,
)


def test_agent_request_min():
    r = AgentRequest(user_input="강남 매치", user_id=1)
    assert r.user_input == "강남 매치"
    assert r.user_id == 1


def test_match_proposal_optional_team_b():
    m = MatchProposal(
        stadium_id=1, stadium_name="강남풋살장",
        start_time="2026-05-23T14:00", duration_min=60,
        team_a=TeamSummary(id=1, name="A팀"),
    )
    assert m.team_b is None
    assert m.stage is None


def test_proposal_response_with_bracket():
    bracket = BracketDTO(rounds=[[{"matchIdx": 0}], [{"matchIdx": 1, "depends_on": [0]}]])
    r = ProposalResponse(
        proposal_id="p1", intent="TOURNAMENT",
        warnings=[], matches=[], bracket=bracket,
    )
    assert r.bracket is not None
    assert len(r.bracket.rounds) == 2


def test_confirm_validate_request_min():
    r = ConfirmValidateRequest(proposal_id="p1", matches=[])
    assert r.matches == []
```

- [ ] **Step 6: 실패 확인**

```powershell
pytest tests/test_agent_schemas.py -v
```
Expected: FAIL — module 없음.

- [ ] **Step 7: schemas.py 구현**

`ai-service/agent/schemas.py`:
```python
from typing import Literal

from pydantic import BaseModel, Field


class AgentRequest(BaseModel):
    user_input: str = Field(min_length=1, max_length=500)
    user_id: int


class TeamSummary(BaseModel):
    id: int
    name: str


class MatchProposal(BaseModel):
    stadium_id: int
    stadium_name: str
    start_time: str  # ISO 8601 string, 검증은 Spring 측에서
    duration_min: int = 60
    team_a: TeamSummary
    team_b: TeamSummary | None = None
    stage: str | None = None  # "SEMIFINAL", "FINAL", etc.


class BracketRoundSlot(BaseModel):
    matchIdx: int
    depends_on: list[int] | None = None


class BracketDTO(BaseModel):
    rounds: list[list[dict]]  # raw dict 형태 그대로 통과


class ProposalResponse(BaseModel):
    proposal_id: str
    intent: Literal["SINGLE", "TOURNAMENT", "UNKNOWN"]
    warnings: list[str] = []
    matches: list[MatchProposal] = []
    bracket: BracketDTO | None = None


class ConfirmValidateRequest(BaseModel):
    proposal_id: str
    matches: list[MatchProposal]
```

- [ ] **Step 8: schemas 테스트 통과**

```powershell
pytest tests/test_agent_schemas.py -v
```
Expected: 4 passed.

- [ ] **Step 9: Commit**

```powershell
git add ai-service/agent/state.py ai-service/agent/schemas.py `
        ai-service/tests/test_agent_state.py ai-service/tests/test_agent_schemas.py
git commit -m "feat(agent): AgentState + Pydantic schemas 정의"
git push origin feature/rag-chatbot
```

---

## Task 2: SpringbootClient (Spring REST 호출 래퍼)

**Files:**
- Create: `ai-service/agent/springboot_client.py`
- Create: `ai-service/tests/test_springboot_client.py`

- [ ] **Step 1: 실패 테스트 작성**

`ai-service/tests/test_springboot_client.py`:
```python
from unittest.mock import MagicMock, patch

import httpx
import pytest

from agent.springboot_client import SpringbootClient


def _fake_response(status: int, json_data):
    resp = MagicMock(spec=httpx.Response)
    resp.status_code = status
    resp.json.return_value = json_data
    resp.raise_for_status = MagicMock()
    if status >= 400:
        resp.raise_for_status.side_effect = httpx.HTTPStatusError(
            "err", request=MagicMock(), response=resp
        )
    return resp


def test_search_stadium_returns_list():
    with patch("agent.springboot_client.httpx.Client") as mock_cls:
        c = mock_cls.return_value.__enter__.return_value
        c.get.return_value = _fake_response(
            200, [{"id": 1, "name": "강남풋살장", "region": "강남"}]
        )
        client = SpringbootClient(base_url="http://fake:8080/letsfutsal")
        result = client.search_stadium(region="강남", date_from="2026-05-23", date_to="2026-05-24")

    assert len(result) == 1
    assert result[0]["name"] == "강남풋살장"


def test_list_team_members_returns_list():
    with patch("agent.springboot_client.httpx.Client") as mock_cls:
        c = mock_cls.return_value.__enter__.return_value
        c.get.return_value = _fake_response(
            200, [{"id": 10, "nickname": "수진"}, {"id": 11, "nickname": "철수"}]
        )
        client = SpringbootClient(base_url="http://fake:8080/letsfutsal")
        result = client.list_team_members(team_id=5)

    assert len(result) == 2


def test_returns_empty_on_404():
    with patch("agent.springboot_client.httpx.Client") as mock_cls:
        c = mock_cls.return_value.__enter__.return_value
        c.get.return_value = _fake_response(404, {})
        client = SpringbootClient(base_url="http://fake:8080/letsfutsal")
        result = client.search_stadium(region="없는동네")

    assert result == []


def test_raises_on_500():
    with patch("agent.springboot_client.httpx.Client") as mock_cls:
        c = mock_cls.return_value.__enter__.return_value
        c.get.return_value = _fake_response(500, {})
        client = SpringbootClient(base_url="http://fake:8080/letsfutsal")
        with pytest.raises(httpx.HTTPStatusError):
            client.list_team_members(team_id=5)
```

- [ ] **Step 2: 실패 확인**

```powershell
pytest tests/test_springboot_client.py -v
```
Expected: FAIL — module 없음.

- [ ] **Step 3: SpringbootClient 구현**

`ai-service/agent/springboot_client.py`:
```python
from __future__ import annotations

import os

import httpx


class SpringbootClient:
    """Spring read-only API 호출 래퍼. 4xx는 빈 결과, 5xx는 raise."""

    def __init__(self, base_url: str | None = None, timeout: float = 5.0):
        self._base_url = base_url or os.environ.get(
            "SPRING_BASE_URL", "http://localhost:8080/letsfutsal"
        )
        self._timeout = timeout

    def _get(self, path: str, params: dict | None = None) -> list[dict] | dict:
        with httpx.Client(timeout=self._timeout) as c:
            resp = c.get(f"{self._base_url}{path}", params=params)
            if resp.status_code == 404:
                return []
            resp.raise_for_status()
            return resp.json()

    def search_stadium(
        self,
        region: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> list[dict]:
        params = {}
        if region:
            params["region"] = region
        if date_from:
            params["dateFrom"] = date_from
        if date_to:
            params["dateTo"] = date_to
        result = self._get("/api/agent-data/stadium", params)
        return result if isinstance(result, list) else []

    def list_stadium_slots(self, stadium_id: int, date: str) -> list[dict]:
        result = self._get(
            f"/api/agent-data/stadium/{stadium_id}/slots", {"date": date}
        )
        return result if isinstance(result, list) else []

    def list_team_members(self, team_id: int) -> list[dict]:
        result = self._get(f"/api/agent-data/team-members/{team_id}")
        return result if isinstance(result, list) else []

    def find_team_conflicts(
        self, team_id: int, date_from: str, date_to: str
    ) -> list[dict]:
        result = self._get(
            f"/api/agent-data/team-conflicts/{team_id}",
            {"dateFrom": date_from, "dateTo": date_to},
        )
        return result if isinstance(result, list) else []
```

- [ ] **Step 4: 통과 확인**

```powershell
pytest tests/test_springboot_client.py -v
```
Expected: 4 passed.

- [ ] **Step 5: Commit**

```powershell
git add ai-service/agent/springboot_client.py ai-service/tests/test_springboot_client.py
git commit -m "feat(agent): SpringbootClient — Spring read-only API REST 호출 래퍼"
git push origin feature/rag-chatbot
```

---

## Task 3: Tool 함수 6개

**Files:**
- Create: `ai-service/agent/tools.py`
- Create: `ai-service/tests/test_agent_tools.py`

LangGraph가 LLM에 노출할 함수 정의. `@tool` 데코레이터로 LangChain Tool 인터페이스 충족.

- [ ] **Step 1: 실패 테스트 작성**

`ai-service/tests/test_agent_tools.py`:
```python
from unittest.mock import MagicMock

from agent.tools import (
    Tools,
    generate_bracket,
    propose_match,
)


def test_search_stadium_delegates_to_client():
    client = MagicMock()
    client.search_stadium.return_value = [{"id": 1, "name": "강남풋살장"}]
    tools = Tools(client=client)
    result = tools.search_stadium("강남", "2026-05-23", "2026-05-24")
    assert result == [{"id": 1, "name": "강남풋살장"}]
    client.search_stadium.assert_called_once_with("강남", "2026-05-23", "2026-05-24")


def test_list_stadium_slots():
    client = MagicMock()
    client.list_stadium_slots.return_value = [{"start": "14:00", "end": "15:00"}]
    tools = Tools(client=client)
    result = tools.list_stadium_slots(1, "2026-05-23")
    assert len(result) == 1


def test_list_team_members():
    client = MagicMock()
    client.list_team_members.return_value = [{"id": 10, "nickname": "수진"}]
    tools = Tools(client=client)
    result = tools.list_team_members(5)
    assert result[0]["nickname"] == "수진"


def test_find_team_conflicts():
    client = MagicMock()
    client.find_team_conflicts.return_value = []
    tools = Tools(client=client)
    result = tools.find_team_conflicts(5, "2026-05-23", "2026-05-24")
    assert result == []


def test_generate_bracket_4teams():
    bracket = generate_bracket([1, 2, 3, 4])
    assert len(bracket["rounds"]) == 2  # 준결승 + 결승
    assert len(bracket["rounds"][0]) == 2  # 준결승 매치 2개
    assert len(bracket["rounds"][1]) == 1  # 결승 1개


def test_generate_bracket_8teams():
    bracket = generate_bracket([1, 2, 3, 4, 5, 6, 7, 8])
    assert len(bracket["rounds"]) == 3  # 8강 + 4강 + 결승
    assert len(bracket["rounds"][0]) == 4
    assert len(bracket["rounds"][1]) == 2
    assert len(bracket["rounds"][2]) == 1


def test_generate_bracket_invalid_team_count():
    import pytest

    with pytest.raises(ValueError):
        generate_bracket([1, 2, 3])  # 2의 거듭제곱 아님


def test_propose_match_assembles_dict():
    p = propose_match(
        stadium_id=1,
        stadium_name="강남",
        start_time="2026-05-23T14:00",
        team_a={"id": 1, "name": "A"},
        team_b={"id": 2, "name": "B"},
        stage="SEMIFINAL",
    )
    assert p["stadium_id"] == 1
    assert p["team_b"]["name"] == "B"
    assert p["stage"] == "SEMIFINAL"
    assert p["duration_min"] == 60
```

- [ ] **Step 2: 실패 확인**

```powershell
pytest tests/test_agent_tools.py -v
```
Expected: FAIL — module 없음.

- [ ] **Step 3: tools.py 구현**

`ai-service/agent/tools.py`:
```python
from __future__ import annotations

import math

from .springboot_client import SpringbootClient


def generate_bracket(team_ids: list[int]) -> dict:
    """싱글 엘리미네이션 대진표. 팀 수는 2의 거듭제곱이어야 함 (2, 4, 8)."""
    n = len(team_ids)
    if n < 2 or (n & (n - 1)) != 0:
        raise ValueError(f"team count must be a power of 2 (>=2): got {n}")

    rounds: list[list[dict]] = []
    round_size = n // 2
    match_idx = 0
    # 1라운드 (시드 매칭: 1-N, 2-(N-1), ...)
    first_round = []
    for i in range(round_size):
        first_round.append({"matchIdx": match_idx, "teamA": team_ids[i], "teamB": team_ids[n - 1 - i]})
        match_idx += 1
    rounds.append(first_round)

    # 다음 라운드부터는 depends_on
    prev_count = round_size
    while prev_count > 1:
        next_round = []
        for i in range(prev_count // 2):
            depends = [
                rounds[-1][2 * i]["matchIdx"],
                rounds[-1][2 * i + 1]["matchIdx"],
            ]
            next_round.append({"matchIdx": match_idx, "depends_on": depends})
            match_idx += 1
        rounds.append(next_round)
        prev_count //= 2

    return {"rounds": rounds, "total_matches": match_idx}


def propose_match(
    stadium_id: int,
    stadium_name: str,
    start_time: str,
    team_a: dict,
    team_b: dict | None = None,
    duration_min: int = 60,
    stage: str | None = None,
) -> dict:
    """미리보기 매치 한 건 생성 (DB 저장 안 함)."""
    return {
        "stadium_id": stadium_id,
        "stadium_name": stadium_name,
        "start_time": start_time,
        "duration_min": duration_min,
        "team_a": team_a,
        "team_b": team_b,
        "stage": stage,
    }


class Tools:
    """LangGraph 노드에서 호출하는 Tool 묶음. SpringbootClient를 dependency injection."""

    def __init__(self, client: SpringbootClient):
        self._client = client

    def search_stadium(
        self, region: str | None, date_from: str | None, date_to: str | None
    ) -> list[dict]:
        return self._client.search_stadium(region, date_from, date_to)

    def list_stadium_slots(self, stadium_id: int, date: str) -> list[dict]:
        return self._client.list_stadium_slots(stadium_id, date)

    def list_team_members(self, team_id: int) -> list[dict]:
        return self._client.list_team_members(team_id)

    def find_team_conflicts(
        self, team_id: int, date_from: str, date_to: str
    ) -> list[dict]:
        return self._client.find_team_conflicts(team_id, date_from, date_to)
```

- [ ] **Step 4: 통과 확인**

```powershell
pytest tests/test_agent_tools.py -v
```
Expected: 8 passed.

- [ ] **Step 5: Commit**

```powershell
git add ai-service/agent/tools.py ai-service/tests/test_agent_tools.py
git commit -m "feat(agent): Tool 함수 6개 (Spring 호출 4 + bracket/propose 2)"
git push origin feature/rag-chatbot
```

---

## Task 4: parse_intent 노드 (Claude Tool Use로 의도+슬롯 추출)

**Files:**
- Create: `ai-service/agent/nodes.py` (parse_intent 부분만)
- Create: `ai-service/tests/test_agent_nodes.py` (parse_intent 케이스)

- [ ] **Step 1: 실패 테스트 작성**

`ai-service/tests/test_agent_nodes.py`:
```python
from unittest.mock import MagicMock

from agent.nodes import parse_intent
from agent.state import make_initial_state


def test_parse_intent_single_match():
    claude = MagicMock()
    claude.chat_with_tool.return_value = {
        "intent": "SINGLE",
        "region": "강남",
        "date_from": "2026-05-23",
        "date_to": "2026-05-24",
        "team_count": 1,
    }
    state = make_initial_state("강남 토요일 매치", user_id=1)
    new_state = parse_intent(state, claude_client=claude)

    assert new_state["intent"] == "SINGLE"
    assert new_state["slots"]["region"] == "강남"
    assert new_state["slots"]["date_from"] == "2026-05-23"


def test_parse_intent_tournament():
    claude = MagicMock()
    claude.chat_with_tool.return_value = {
        "intent": "TOURNAMENT",
        "region": "강남",
        "date_from": "2026-05-26",
        "date_to": "2026-05-26",
        "team_count": 4,
    }
    state = make_initial_state("4팀 토너먼트 강남", user_id=1)
    new_state = parse_intent(state, claude_client=claude)

    assert new_state["intent"] == "TOURNAMENT"
    assert new_state["slots"]["team_count"] == 4


def test_parse_intent_falls_back_to_unknown_on_error():
    claude = MagicMock()
    claude.chat_with_tool.side_effect = RuntimeError("boom")
    state = make_initial_state("아무말", user_id=1)
    new_state = parse_intent(state, claude_client=claude)

    assert new_state["intent"] == "UNKNOWN"
    assert "intent 분류 실패" in new_state["errors"][0]
```

- [ ] **Step 2: 실패 확인**

```powershell
pytest tests/test_agent_nodes.py -v
```
Expected: FAIL — module 없음.

- [ ] **Step 3: nodes.py 초기 구현 (parse_intent만)**

`ai-service/agent/nodes.py`:
```python
from __future__ import annotations

from rag.claude_client import ClaudeClient

from .state import AgentState

INTENT_TOOL = {
    "name": "extract_intent",
    "description": (
        "사용자의 풋살 코디네이터 요청에서 의도와 슬롯을 추출한다. "
        "intent가 SINGLE이면 단일 매치, TOURNAMENT면 토너먼트 기획. "
        "팀 수가 명시 안 되면 team_count=1."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "intent": {"type": "string", "enum": ["SINGLE", "TOURNAMENT"]},
            "region": {"type": "string"},
            "date_from": {"type": "string"},
            "date_to": {"type": "string"},
            "team_count": {"type": "integer"},
        },
        "required": ["intent"],
    },
}

PARSE_SYSTEM = (
    "당신은 풋살 매치 코디네이터의 의도 분류기입니다. "
    "사용자 입력에서 SINGLE(단일 매치)/TOURNAMENT(토너먼트)를 분류하고, "
    "지역·날짜 범위·팀 수를 슬롯으로 추출하세요. "
    "정보가 없으면 해당 슬롯을 비웁니다. extract_intent 도구로 반환하세요."
)


def parse_intent(state: AgentState, claude_client: ClaudeClient) -> AgentState:
    """사용자 입력을 intent + slots로 분류."""
    try:
        result = claude_client.chat_with_tool(
            system=PARSE_SYSTEM,
            user=state["user_input"],
            tool=INTENT_TOOL,
        )
        state["intent"] = result.get("intent", "UNKNOWN")
        state["slots"] = {
            "region": result.get("region"),
            "date_from": result.get("date_from"),
            "date_to": result.get("date_to"),
            "team_count": result.get("team_count", 1),
        }
    except Exception as e:
        state["intent"] = "UNKNOWN"
        state["errors"].append(f"intent 분류 실패: {e}")
    return state
```

- [ ] **Step 4: 통과 확인**

```powershell
pytest tests/test_agent_nodes.py -v
```
Expected: 3 passed.

- [ ] **Step 5: Commit**

```powershell
git add ai-service/agent/nodes.py ai-service/tests/test_agent_nodes.py
git commit -m "feat(agent): parse_intent 노드 (Claude Tool Use 의도+슬롯 추출)"
git push origin feature/rag-chatbot
```

---

## Task 5: single_flow 노드 4개 (stadium / team / match / review)

**Files:**
- Modify: `ai-service/agent/nodes.py` (4개 노드 추가)
- Modify: `ai-service/tests/test_agent_nodes.py` (단위 테스트 추가)

순차 실행되는 단일 매치 흐름. 각 노드는 mock Tools 받아서 동작.

- [ ] **Step 1: 실패 테스트 작성 (test_agent_nodes.py에 append)**

`ai-service/tests/test_agent_nodes.py` 끝에 추가:
```python
from unittest.mock import MagicMock as _MM

from agent.nodes import single_match_node, single_review_node, single_stadium_node, single_team_node


def _filled_state(intent="SINGLE", team_count=1):
    s = make_initial_state("강남 매치", user_id=1)
    s["intent"] = intent
    s["slots"] = {
        "region": "강남",
        "date_from": "2026-05-23",
        "date_to": "2026-05-24",
        "team_count": team_count,
    }
    return s


def test_single_stadium_node_populates_candidates():
    tools = _MM()
    tools.search_stadium.return_value = [
        {"id": 1, "name": "강남풋살장"},
        {"id": 2, "name": "역삼풋살장"},
    ]
    state = _filled_state()
    new_state = single_stadium_node(state, tools=tools)
    assert len(new_state["stadium_candidates"]) == 2


def test_single_stadium_node_warns_when_empty():
    tools = _MM()
    tools.search_stadium.return_value = []
    state = _filled_state()
    new_state = single_stadium_node(state, tools=tools)
    assert new_state["stadium_candidates"] == []
    assert any("경기장" in w for w in new_state["warnings"])


def test_single_team_node_fetches_user_team():
    tools = _MM()
    tools.list_team_members.return_value = [{"id": 10, "nickname": "수진"}]
    tools.find_team_conflicts.return_value = []
    state = _filled_state()
    state["team_info"] = {"team_id": 5, "team_name": "A팀"}
    new_state = single_team_node(state, tools=tools)
    assert new_state["team_info"]["members"] == [{"id": 10, "nickname": "수진"}]
    assert new_state["team_info"]["conflicts"] == []


def test_single_match_node_proposes_one():
    tools = _MM()
    tools.list_stadium_slots.return_value = [
        {"start": "2026-05-23T14:00", "end": "2026-05-23T15:00"}
    ]
    state = _filled_state()
    state["stadium_candidates"] = [{"id": 1, "name": "강남풋살장"}]
    state["team_info"] = {"team_id": 5, "team_name": "A팀", "conflicts": []}
    new_state = single_match_node(state, tools=tools)
    assert len(new_state["proposals"]) == 1
    assert new_state["proposals"][0]["stadium_id"] == 1


def test_single_match_node_skips_conflict():
    tools = _MM()
    tools.list_stadium_slots.return_value = [
        {"start": "2026-05-23T14:00", "end": "2026-05-23T15:00"}
    ]
    state = _filled_state()
    state["stadium_candidates"] = [{"id": 1, "name": "강남풋살장"}]
    state["team_info"] = {
        "team_id": 5,
        "team_name": "A팀",
        "conflicts": [{"start": "2026-05-23T14:00", "end": "2026-05-23T15:00"}],
    }
    new_state = single_match_node(state, tools=tools)
    assert len(new_state["proposals"]) == 0
    assert any("충돌" in w for w in new_state["warnings"])


def test_single_review_node_validates_at_least_one_proposal():
    state = _filled_state()
    state["proposals"] = [
        {"stadium_id": 1, "start_time": "2026-05-23T14:00", "duration_min": 60}
    ]
    new_state = single_review_node(state, tools=_MM())
    assert new_state.get("errors", []) == []
```

- [ ] **Step 2: 실패 확인**

```powershell
pytest tests/test_agent_nodes.py -v
```
Expected: 새 케이스들 FAIL — 노드 없음.

- [ ] **Step 3: nodes.py에 4개 노드 추가 (append)**

`ai-service/agent/nodes.py` 끝에 추가:
```python
from .tools import Tools, propose_match


def single_stadium_node(state: AgentState, tools: Tools) -> AgentState:
    slots = state["slots"]
    candidates = tools.search_stadium(
        region=slots.get("region"),
        date_from=slots.get("date_from"),
        date_to=slots.get("date_to"),
    )
    state["stadium_candidates"] = candidates
    if not candidates:
        state["warnings"].append("조건에 맞는 경기장이 없습니다.")
    return state


def single_team_node(state: AgentState, tools: Tools) -> AgentState:
    team_info = state["team_info"]
    team_id = team_info.get("team_id")
    if team_id is None:
        state["warnings"].append("팀 정보가 없어 멤버·일정을 조회하지 못했습니다.")
        return state

    team_info["members"] = tools.list_team_members(team_id)
    team_info["conflicts"] = tools.find_team_conflicts(
        team_id,
        state["slots"].get("date_from", ""),
        state["slots"].get("date_to", ""),
    )
    state["team_info"] = team_info
    return state


def _slot_conflicts(slot: dict, conflicts: list[dict]) -> bool:
    s_start = slot.get("start")
    s_end = slot.get("end")
    for c in conflicts:
        if s_start == c.get("start"):
            return True
        # 겹침 검사 (구간)
        if s_start and s_end and c.get("start") and c.get("end"):
            if not (s_end <= c["start"] or s_start >= c["end"]):
                return True
    return False


def single_match_node(state: AgentState, tools: Tools) -> AgentState:
    candidates = state["stadium_candidates"]
    team_info = state["team_info"]
    conflicts = team_info.get("conflicts", []) if team_info else []
    team_a = {"id": team_info.get("team_id"), "name": team_info.get("team_name", "내 팀")}

    proposals: list[dict] = []
    date = state["slots"].get("date_from", "")

    for stadium in candidates[:5]:  # 상위 5개만
        slots = tools.list_stadium_slots(stadium["id"], date)
        for slot in slots:
            if _slot_conflicts(slot, conflicts):
                state["warnings"].append(
                    f"시간 충돌 — {stadium['name']} {slot.get('start')}"
                )
                continue
            proposals.append(
                propose_match(
                    stadium_id=stadium["id"],
                    stadium_name=stadium["name"],
                    start_time=slot.get("start", ""),
                    team_a=team_a,
                )
            )
            if len(proposals) >= 3:  # 최대 3개 제안
                break
        if len(proposals) >= 3:
            break

    state["proposals"] = proposals
    return state


def single_review_node(state: AgentState, tools: Tools) -> AgentState:
    """검증 노드. 현재는 단순 통과 — 향후 충돌·예산 검증 확장 위치."""
    if not state["proposals"] and not state["warnings"]:
        state["warnings"].append("적합한 매치 슬롯이 없습니다.")
    return state
```

- [ ] **Step 4: 통과 확인**

```powershell
pytest tests/test_agent_nodes.py -v
```
Expected: 9 passed (기존 3 + 신규 6).

- [ ] **Step 5: Commit**

```powershell
git add ai-service/agent/nodes.py ai-service/tests/test_agent_nodes.py
git commit -m "feat(agent): single_flow 노드 4개 (stadium/team/match/review)"
git push origin feature/rag-chatbot
```

---

## Task 6: Sub-agent 3종 (StadiumAgent / TeamAgent / MatchAgent)

**Files:**
- Create: `ai-service/agent/subagents.py`
- Create: `ai-service/tests/test_subagents.py`

각 sub-agent는 자체 mini-graph 또는 단순 함수. 본 plan은 **함수로 시작**해서 단순화 (LangGraph sub-graph 컴파일 부담 제거). 병렬 실행은 Task 7 `tournament_assemble`에서 `concurrent.futures.ThreadPoolExecutor`로.

- [ ] **Step 1: 실패 테스트 작성**

`ai-service/tests/test_subagents.py`:
```python
from unittest.mock import MagicMock

from agent.subagents import MatchAgent, StadiumAgent, TeamAgent


def test_stadium_agent_returns_candidates_and_slots():
    tools = MagicMock()
    tools.search_stadium.return_value = [{"id": 1, "name": "강남"}, {"id": 2, "name": "역삼"}]
    tools.list_stadium_slots.side_effect = [
        [{"start": "2026-05-26T10:00", "end": "2026-05-26T11:00"}],
        [{"start": "2026-05-26T11:00", "end": "2026-05-26T12:00"}],
    ]

    agent = StadiumAgent(tools=tools)
    result = agent.run(region="강남", date="2026-05-26", needed_matches=2)

    assert len(result["candidates"]) == 2
    assert len(result["slots"]) >= 2  # 합쳐서 최소 2개


def test_team_agent_returns_members_per_team():
    tools = MagicMock()
    tools.list_team_members.side_effect = [
        [{"id": 1, "nickname": "A1"}],
        [{"id": 2, "nickname": "B1"}],
    ]
    tools.find_team_conflicts.return_value = []

    agent = TeamAgent(tools=tools)
    result = agent.run(team_ids=[1, 2], date_from="2026-05-26", date_to="2026-05-26")

    assert len(result["teams"]) == 2
    assert result["teams"][0]["members"][0]["nickname"] == "A1"


def test_match_agent_generates_bracket_and_proposals():
    agent = MatchAgent()
    # 4팀 + 2 stadium slot (준결승 2개 + 결승 1개 = 3 matches 필요)
    teams = [
        {"id": 1, "name": "A"}, {"id": 2, "name": "B"},
        {"id": 3, "name": "C"}, {"id": 4, "name": "D"},
    ]
    slots = [
        {"stadium_id": 10, "stadium_name": "강남", "start": "2026-05-26T10:00"},
        {"stadium_id": 10, "stadium_name": "강남", "start": "2026-05-26T11:00"},
        {"stadium_id": 10, "stadium_name": "강남", "start": "2026-05-26T12:00"},
    ]

    result = agent.run(teams=teams, slots=slots)

    assert len(result["proposals"]) == 3  # 준결승 2 + 결승 1
    assert result["bracket"]["total_matches"] == 3
    assert result["proposals"][0]["stage"] in ("SEMIFINAL", "FINAL")


def test_match_agent_warns_when_not_enough_slots():
    agent = MatchAgent()
    teams = [
        {"id": 1, "name": "A"}, {"id": 2, "name": "B"},
        {"id": 3, "name": "C"}, {"id": 4, "name": "D"},
    ]
    slots = [
        {"stadium_id": 10, "stadium_name": "강남", "start": "2026-05-26T10:00"},
    ]  # 1개만

    result = agent.run(teams=teams, slots=slots)
    assert len(result["proposals"]) == 1
    assert any("슬롯 부족" in w for w in result["warnings"])
```

- [ ] **Step 2: 실패 확인**

```powershell
pytest tests/test_subagents.py -v
```
Expected: FAIL — module 없음.

- [ ] **Step 3: subagents.py 구현**

`ai-service/agent/subagents.py`:
```python
from __future__ import annotations

from .tools import Tools, generate_bracket, propose_match


class StadiumAgent:
    """경기장 후보 + 시간 슬롯 검색."""

    def __init__(self, tools: Tools):
        self._tools = tools

    def run(self, region: str | None, date: str, needed_matches: int) -> dict:
        candidates = self._tools.search_stadium(region, date, date) or []
        slots: list[dict] = []
        for s in candidates[:5]:
            stadium_slots = self._tools.list_stadium_slots(s["id"], date) or []
            for slot in stadium_slots:
                slots.append(
                    {
                        "stadium_id": s["id"],
                        "stadium_name": s["name"],
                        "start": slot.get("start", ""),
                        "end": slot.get("end", ""),
                    }
                )
                if len(slots) >= needed_matches * 2:  # 여유분 확보
                    break
            if len(slots) >= needed_matches * 2:
                break
        return {"candidates": candidates, "slots": slots}


class TeamAgent:
    """팀별 멤버·일정 충돌 조회."""

    def __init__(self, tools: Tools):
        self._tools = tools

    def run(self, team_ids: list[int], date_from: str, date_to: str) -> dict:
        teams = []
        for tid in team_ids:
            members = self._tools.list_team_members(tid) or []
            conflicts = self._tools.find_team_conflicts(tid, date_from, date_to) or []
            teams.append({"id": tid, "members": members, "conflicts": conflicts})
        return {"teams": teams}


class MatchAgent:
    """대진표 생성 + 슬롯 매칭으로 매치 제안 N개 생성."""

    def run(self, teams: list[dict], slots: list[dict]) -> dict:
        team_ids = [t["id"] for t in teams]
        warnings: list[str] = []
        try:
            bracket = generate_bracket(team_ids)
        except ValueError as e:
            return {
                "bracket": None,
                "proposals": [],
                "warnings": [f"대진표 생성 실패: {e}"],
            }

        total_matches_needed = bracket["total_matches"]
        proposals: list[dict] = []

        # 1라운드 — 팀 짝짓기 + 슬롯 매칭
        for round_idx, round_matches in enumerate(bracket["rounds"]):
            stage = self._stage_label(round_idx, len(bracket["rounds"]))
            for m in round_matches:
                if len(proposals) >= len(slots):
                    break
                slot = slots[len(proposals)]
                # 첫 라운드는 teamA/teamB 직접, 다음 라운드는 placeholder
                if "teamA" in m:
                    team_a = next(t for t in teams if t["id"] == m["teamA"])
                    team_b = next(t for t in teams if t["id"] == m["teamB"])
                    proposals.append(
                        propose_match(
                            stadium_id=slot["stadium_id"],
                            stadium_name=slot["stadium_name"],
                            start_time=slot["start"],
                            team_a={"id": team_a["id"], "name": team_a.get("name", str(team_a["id"]))},
                            team_b={"id": team_b["id"], "name": team_b.get("name", str(team_b["id"]))},
                            stage=stage,
                        )
                    )
                else:
                    # depends_on 라운드 — 팀은 TBD
                    proposals.append(
                        propose_match(
                            stadium_id=slot["stadium_id"],
                            stadium_name=slot["stadium_name"],
                            start_time=slot["start"],
                            team_a={"id": 0, "name": f"TBD (match {m['depends_on'][0]} 승자)"},
                            team_b={"id": 0, "name": f"TBD (match {m['depends_on'][1]} 승자)"},
                            stage=stage,
                        )
                    )

        if len(proposals) < total_matches_needed:
            warnings.append(
                f"슬롯 부족 — 필요 {total_matches_needed}개, 확보 {len(proposals)}개"
            )

        return {"bracket": bracket, "proposals": proposals, "warnings": warnings}

    @staticmethod
    def _stage_label(round_idx: int, total_rounds: int) -> str:
        if round_idx == total_rounds - 1:
            return "FINAL"
        if round_idx == total_rounds - 2:
            return "SEMIFINAL"
        return f"ROUND_{round_idx + 1}"
```

- [ ] **Step 4: 통과 확인**

```powershell
pytest tests/test_subagents.py -v
```
Expected: 4 passed.

- [ ] **Step 5: Commit**

```powershell
git add ai-service/agent/subagents.py ai-service/tests/test_subagents.py
git commit -m "feat(agent): Sub-agent 3종 (StadiumAgent/TeamAgent/MatchAgent)"
git push origin feature/rag-chatbot
```

---

## Task 7: tournament_assemble + summarize 노드 (병렬 실행)

**Files:**
- Modify: `ai-service/agent/nodes.py`
- Modify: `ai-service/tests/test_agent_nodes.py`

토너먼트 흐름의 핵심. 3개 sub-agent를 `ThreadPoolExecutor`로 병렬 실행 → 결과 통합.

- [ ] **Step 1: 실패 테스트 작성 (append)**

`ai-service/tests/test_agent_nodes.py` 끝에 추가:
```python
from agent.nodes import summarize_node, tournament_assemble_node


def _tournament_state(team_count=4):
    s = make_initial_state("4팀 토너먼트", user_id=1)
    s["intent"] = "TOURNAMENT"
    s["slots"] = {
        "region": "강남",
        "date_from": "2026-05-26",
        "date_to": "2026-05-26",
        "team_count": team_count,
    }
    s["team_info"] = {
        "team_ids": [1, 2, 3, 4],
        "team_names": {1: "A", 2: "B", 3: "C", 4: "D"},
    }
    return s


def test_tournament_assemble_combines_subagent_results():
    tools = _MM()
    # StadiumAgent mock — Tools 메서드 호출 시 결과 정의
    tools.search_stadium.return_value = [{"id": 10, "name": "강남"}]
    tools.list_stadium_slots.return_value = [
        {"start": "2026-05-26T10:00", "end": "2026-05-26T11:00"},
        {"start": "2026-05-26T11:00", "end": "2026-05-26T12:00"},
        {"start": "2026-05-26T12:00", "end": "2026-05-26T13:00"},
    ]
    tools.list_team_members.return_value = []
    tools.find_team_conflicts.return_value = []

    state = _tournament_state()
    new_state = tournament_assemble_node(state, tools=tools)

    assert new_state["bracket"] is not None
    assert len(new_state["proposals"]) == 3


def test_summarize_node_adds_proposal_id():
    state = _tournament_state()
    state["proposals"] = [
        {"stadium_id": 1, "start_time": "2026-05-26T10:00", "duration_min": 60}
    ]
    new_state = summarize_node(state)
    assert "proposal_id" in new_state
    assert new_state["proposal_id"].startswith("prop_")
```

- [ ] **Step 2: 실패 확인**

```powershell
pytest tests/test_agent_nodes.py -v
```
Expected: 새 케이스 FAIL.

- [ ] **Step 3: nodes.py에 추가**

`ai-service/agent/nodes.py` 끝에 추가:
```python
import uuid
from concurrent.futures import ThreadPoolExecutor

from .subagents import MatchAgent, StadiumAgent, TeamAgent


def tournament_assemble_node(state: AgentState, tools: Tools) -> AgentState:
    """3개 sub-agent를 병렬 실행 후 결과 통합."""
    slots = state["slots"]
    team_info = state["team_info"]
    team_ids: list[int] = team_info.get("team_ids", [])
    date = slots.get("date_from", "")

    stadium_agent = StadiumAgent(tools=tools)
    team_agent = TeamAgent(tools=tools)
    match_agent = MatchAgent()

    needed_matches = max(len(team_ids) - 1, 1)

    with ThreadPoolExecutor(max_workers=2) as ex:
        f_stadium = ex.submit(
            stadium_agent.run, slots.get("region"), date, needed_matches
        )
        f_team = ex.submit(
            team_agent.run, team_ids, date, slots.get("date_to", date)
        )
        stadium_result = f_stadium.result()
        team_result = f_team.result()

    teams_with_names = [
        {"id": t["id"], "name": team_info.get("team_names", {}).get(t["id"], str(t["id"]))}
        for t in team_result["teams"]
    ]

    match_result = match_agent.run(teams=teams_with_names, slots=stadium_result["slots"])

    state["stadium_candidates"] = stadium_result["candidates"]
    state["team_info"] = {**team_info, "details": team_result["teams"]}
    state["bracket"] = match_result["bracket"]
    state["proposals"] = match_result["proposals"]
    state["warnings"].extend(match_result.get("warnings", []))
    return state


def summarize_node(state: AgentState) -> AgentState:
    """proposal_id 부여하고 최종 정리."""
    state["proposal_id"] = "prop_" + uuid.uuid4().hex[:8]
    if not state["proposals"] and not state["errors"]:
        state["warnings"].append("제안할 매치가 없습니다. 조건을 완화해보세요.")
    return state
```

> 주의: `AgentState`는 TypedDict라 `proposal_id` 같은 신규 키 추가는 mypy 경고를 발생시킬 수 있다. 본 plan에선 런타임 dict 동작에 의존. mypy strict 사용 시 `AgentState`에 `proposal_id: NotRequired[str]` 추가 (`from typing import NotRequired`).

- [ ] **Step 4: 통과 확인**

```powershell
pytest tests/test_agent_nodes.py -v
```
Expected: 11 passed (기존 9 + 신규 2).

- [ ] **Step 5: Commit**

```powershell
git add ai-service/agent/nodes.py ai-service/tests/test_agent_nodes.py
git commit -m "feat(agent): tournament_assemble (3 sub-agent 병렬) + summarize 노드"
git push origin feature/rag-chatbot
```

---

## Task 8: build_agent_graph (StateGraph 컴파일)

**Files:**
- Create: `ai-service/agent/graph.py`
- Create: `ai-service/tests/test_agent_graph.py`

- [ ] **Step 1: 실패 테스트 작성**

`ai-service/tests/test_agent_graph.py`:
```python
from unittest.mock import MagicMock

from agent.graph import build_agent_graph
from agent.state import make_initial_state


def test_graph_single_flow_invokes_single_nodes():
    claude = MagicMock()
    claude.chat_with_tool.return_value = {
        "intent": "SINGLE",
        "region": "강남",
        "date_from": "2026-05-23",
        "date_to": "2026-05-24",
        "team_count": 1,
    }
    tools = MagicMock()
    tools.search_stadium.return_value = [{"id": 1, "name": "강남풋살장"}]
    tools.list_stadium_slots.return_value = [
        {"start": "2026-05-23T14:00", "end": "2026-05-23T15:00"}
    ]
    tools.list_team_members.return_value = []
    tools.find_team_conflicts.return_value = []

    graph = build_agent_graph(claude_client=claude, tools=tools)

    state = make_initial_state("강남 토요일 매치", user_id=1)
    state["team_info"] = {"team_id": 5, "team_name": "내 팀"}
    final = graph.invoke(state)

    assert final["intent"] == "SINGLE"
    assert "proposal_id" in final
    assert len(final["proposals"]) >= 1


def test_graph_tournament_flow():
    claude = MagicMock()
    claude.chat_with_tool.return_value = {
        "intent": "TOURNAMENT",
        "region": "강남",
        "date_from": "2026-05-26",
        "date_to": "2026-05-26",
        "team_count": 4,
    }
    tools = MagicMock()
    tools.search_stadium.return_value = [{"id": 10, "name": "강남"}]
    tools.list_stadium_slots.return_value = [
        {"start": "2026-05-26T10:00", "end": "2026-05-26T11:00"},
        {"start": "2026-05-26T11:00", "end": "2026-05-26T12:00"},
        {"start": "2026-05-26T12:00", "end": "2026-05-26T13:00"},
    ]
    tools.list_team_members.return_value = []
    tools.find_team_conflicts.return_value = []

    graph = build_agent_graph(claude_client=claude, tools=tools)

    state = make_initial_state("4팀 토너먼트 강남 일요일", user_id=1)
    state["team_info"] = {
        "team_ids": [1, 2, 3, 4],
        "team_names": {1: "A", 2: "B", 3: "C", 4: "D"},
    }
    final = graph.invoke(state)

    assert final["intent"] == "TOURNAMENT"
    assert final["bracket"] is not None
    assert len(final["proposals"]) == 3
```

- [ ] **Step 2: 실패 확인**

```powershell
pytest tests/test_agent_graph.py -v
```
Expected: FAIL — module 없음.

- [ ] **Step 3: graph.py 구현**

`ai-service/agent/graph.py`:
```python
from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from rag.claude_client import ClaudeClient

from .nodes import (
    parse_intent,
    single_match_node,
    single_review_node,
    single_stadium_node,
    single_team_node,
    summarize_node,
    tournament_assemble_node,
)
from .state import AgentState
from .tools import Tools


def _route_after_parse(state: AgentState) -> str:
    if state["intent"] == "TOURNAMENT":
        return "tournament_assemble"
    if state["intent"] == "SINGLE":
        return "single_stadium"
    return "summarize"  # UNKNOWN — 바로 요약 (에러 응답)


def build_agent_graph(claude_client: ClaudeClient, tools: Tools):
    g: StateGraph[AgentState] = StateGraph(AgentState)

    g.add_node("parse_intent", lambda s: parse_intent(s, claude_client=claude_client))
    g.add_node("single_stadium", lambda s: single_stadium_node(s, tools=tools))
    g.add_node("single_team", lambda s: single_team_node(s, tools=tools))
    g.add_node("single_match", lambda s: single_match_node(s, tools=tools))
    g.add_node("single_review", lambda s: single_review_node(s, tools=tools))
    g.add_node("tournament_assemble", lambda s: tournament_assemble_node(s, tools=tools))
    g.add_node("summarize", summarize_node)

    g.add_edge(START, "parse_intent")
    g.add_conditional_edges(
        "parse_intent",
        _route_after_parse,
        {
            "single_stadium": "single_stadium",
            "tournament_assemble": "tournament_assemble",
            "summarize": "summarize",
        },
    )
    g.add_edge("single_stadium", "single_team")
    g.add_edge("single_team", "single_match")
    g.add_edge("single_match", "single_review")
    g.add_edge("single_review", "summarize")
    g.add_edge("tournament_assemble", "summarize")
    g.add_edge("summarize", END)

    return g.compile()
```

- [ ] **Step 4: 통과 확인**

```powershell
pytest tests/test_agent_graph.py -v
```
Expected: 2 passed.

- [ ] **Step 5: Commit**

```powershell
git add ai-service/agent/graph.py ai-service/tests/test_agent_graph.py
git commit -m "feat(agent): build_agent_graph — StateGraph + conditional edge 분기"
git push origin feature/rag-chatbot
```

---

## Task 9: Spring 에이전트용 read-only API (AgentDataController)

**Files:**
- Create: `src/main/java/io/github/wizwix/letsfutsal/ai/AgentDataController.java`
- Modify: `src/main/java/io/github/wizwix/letsfutsal/mapper/StadiumMapper.java` (필요 메서드 추가)
- Modify: `src/main/resources/mybatis/mapper_stadium.xml` (필요 SQL)
- Modify: `src/main/java/io/github/wizwix/letsfutsal/mapper/MatchMapper.java` (필요 메서드 추가)
- Modify: `src/main/resources/mybatis/mapper_match.xml`

이 컨트롤러는 LoginInterceptor 대상 제외 (내부 호출용). 기존 Interceptor 설정 확인 후 `/api/agent-data/**`도 통과되도록 조정.

- [ ] **Step 1: WebConfig 인터셉터 제외 경로 확인**

`src/main/java/.../config/WebConfig.java` 열어서 `addInterceptors`에서 `LoginInterceptor`의 `excludePathPatterns`에 `/api/agent-data/**` 추가:

```java
registry
    .addInterceptor(new LoginInterceptor())
    .addPathPatterns("/**")
    .excludePathPatterns(
        "/user/login", "/user/register", "/user/check-id",
        "/resources/**",
        "/api/agent-data/**"  // 신규
    );
```

(기존 excludePathPatterns 값은 그대로 두고 `/api/agent-data/**`만 추가.)

- [ ] **Step 2: StadiumMapper에 메서드 추가**

`mapper/StadiumMapper.java`에 추가:
```java
List<StadiumDTO> selectByRegion(@Param("region") String region);

List<MatchDTO> selectMatchesByStadiumAndDate(
    @Param("stadiumId") int stadiumId, @Param("date") String date);
```

(메서드 시그니처만 추가 — 기존 다른 메서드들은 손대지 말 것.)

- [ ] **Step 3: mapper_stadium.xml에 SQL 추가**

`mapper_stadium.xml`에 추가:
```xml
<select id="selectByRegion" parameterType="String" resultType="StadiumDTO">
  SELECT * FROM tb_stadium
  WHERE region LIKE CONCAT('%', #{region}, '%')
  ORDER BY stadium_id ASC
  LIMIT 20
</select>

<select id="selectMatchesByStadiumAndDate" resultType="MatchDTO">
  SELECT * FROM tb_match
  WHERE stadium_id = #{stadiumId}
    AND DATE(match_date) = #{date}
  ORDER BY match_date ASC
</select>
```

- [ ] **Step 4: MatchMapper에 conflicts 메서드 추가**

`mapper/MatchMapper.java`에 추가:
```java
List<MatchDTO> selectByTeamAndDateRange(
    @Param("teamId") int teamId,
    @Param("dateFrom") String dateFrom,
    @Param("dateTo") String dateTo);
```

`mapper_match.xml`에 추가:
```xml
<select id="selectByTeamAndDateRange" resultType="MatchDTO">
  SELECT * FROM tb_match
  WHERE (team_a_id = #{teamId} OR team_b_id = #{teamId})
    AND DATE(match_date) BETWEEN #{dateFrom} AND #{dateTo}
  ORDER BY match_date ASC
</select>
```

(스키마에 `team_a_id`/`team_b_id` 컬럼 가정. 실제 컬럼명은 `sql/letsfutsal_init.sql` 확인 후 일치시킬 것. 다를 경우 SQL의 컬럼 부분만 수정.)

- [ ] **Step 5: AgentDataController 구현**

`src/main/java/io/github/wizwix/letsfutsal/ai/AgentDataController.java`:
```java
package io.github.wizwix.letsfutsal.ai;

import io.github.wizwix.letsfutsal.dto.MatchDTO;
import io.github.wizwix.letsfutsal.dto.StadiumDTO;
import io.github.wizwix.letsfutsal.dto.UserDTO;
import io.github.wizwix.letsfutsal.mapper.MatchMapper;
import io.github.wizwix.letsfutsal.mapper.StadiumMapper;
import io.github.wizwix.letsfutsal.mapper.TeamMapper;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/agent-data")
public class AgentDataController {

  private final StadiumMapper stadiumMapper;
  private final MatchMapper matchMapper;
  private final TeamMapper teamMapper;

  public AgentDataController(
      StadiumMapper stadiumMapper, MatchMapper matchMapper, TeamMapper teamMapper) {
    this.stadiumMapper = stadiumMapper;
    this.matchMapper = matchMapper;
    this.teamMapper = teamMapper;
  }

  @GetMapping("/stadium")
  public List<StadiumDTO> searchStadium(
      @RequestParam(required = false) String region,
      @RequestParam(required = false) String dateFrom,
      @RequestParam(required = false) String dateTo) {
    return stadiumMapper.selectByRegion(region == null ? "" : region);
  }

  @GetMapping("/stadium/{id}/slots")
  public List<Map<String, String>> listStadiumSlots(
      @PathVariable("id") int stadiumId, @RequestParam("date") String date) {
    // 24시간을 1시간 단위 슬롯으로 분할 후 매치 시간과 겹치지 않는 슬롯만 반환
    List<MatchDTO> booked = stadiumMapper.selectMatchesByStadiumAndDate(stadiumId, date);
    List<Map<String, String>> slots = new java.util.ArrayList<>();
    LocalDate d = LocalDate.parse(date);
    for (int hour = 9; hour <= 22; hour++) {
      LocalDateTime start = d.atTime(hour, 0);
      LocalDateTime end = start.plusHours(1);
      boolean conflict = false;
      for (MatchDTO m : booked) {
        if (m.getMatchDate() != null) {
          LocalDateTime ms = m.getMatchDate().toLocalDateTime();
          LocalDateTime me = ms.plusMinutes(60);
          if (!(end.isBefore(ms) || start.isAfter(me) || end.equals(ms))) {
            conflict = true;
            break;
          }
        }
      }
      if (!conflict) {
        Map<String, String> slot = new HashMap<>();
        slot.put("start", start.toString());
        slot.put("end", end.toString());
        slots.add(slot);
      }
    }
    return slots;
  }

  @GetMapping("/team-members/{teamId}")
  public List<UserDTO> teamMembers(@PathVariable int teamId) {
    return teamMapper.selectMembersByTeamId(teamId);
  }

  @GetMapping("/team-conflicts/{teamId}")
  public List<MatchDTO> teamConflicts(
      @PathVariable int teamId,
      @RequestParam("dateFrom") String dateFrom,
      @RequestParam("dateTo") String dateTo) {
    return matchMapper.selectByTeamAndDateRange(teamId, dateFrom, dateTo);
  }
}
```

> **주의**: `teamMapper.selectMembersByTeamId(teamId)`가 없다면 `TeamMapper`에 동일 시그니처와 `mapper_team.xml`에 SQL 추가 필요. 본 plan에선 메서드명이 존재한다고 가정 — 실행 시 컴파일 에러로 검증.

- [ ] **Step 6: TeamMapper 메서드 확인 + 필요 시 추가**

`mapper/TeamMapper.java`에 `selectMembersByTeamId`가 없다면 추가:
```java
List<UserDTO> selectMembersByTeamId(@Param("teamId") int teamId);
```

`mapper_team.xml`에 추가:
```xml
<select id="selectMembersByTeamId" parameterType="int" resultType="UserDTO">
  SELECT u.*
  FROM tb_user u
  JOIN tb_team_member tm ON tm.user_id = u.user_id
  WHERE tm.team_id = #{teamId}
</select>
```

(`tb_team_member` 조인 컬럼명은 스키마 확인 후 일치시킬 것.)

- [ ] **Step 7: 컴파일 + 빠른 수동 확인**

```powershell
$env:JAVA_HOME = "C:\Program Files\Eclipse Adoptium\jdk-21.0.9.10-hotspot"
$mvn = "C:\Program Files\JetBrains\IntelliJ IDEA 2025.3.2\plugins\maven\lib\maven3\bin\mvn.cmd"
cd C:\letsfutsal
& $mvn -q compile
```
Expected: BUILD SUCCESS.

- [ ] **Step 8: 통합 수동 smoke test (Tomcat 띄워서)**

Tomcat 배포 후:
```powershell
curl "http://localhost:8080/letsfutsal/api/agent-data/stadium?region=강남"
```
Expected: JSON 배열 (DB에 강남 경기장이 있어야 결과 있음). 401/403 안 나오는지 확인 (인터셉터 제외 성공).

- [ ] **Step 9: Commit**

```powershell
git add src/main/java/io/github/wizwix/letsfutsal/ai/AgentDataController.java `
        src/main/java/io/github/wizwix/letsfutsal/mapper/StadiumMapper.java `
        src/main/java/io/github/wizwix/letsfutsal/mapper/MatchMapper.java `
        src/main/java/io/github/wizwix/letsfutsal/mapper/TeamMapper.java `
        src/main/java/io/github/wizwix/letsfutsal/config/WebConfig.java `
        src/main/resources/mybatis/mapper_stadium.xml `
        src/main/resources/mybatis/mapper_match.xml `
        src/main/resources/mybatis/mapper_team.xml
git commit -m "feat(api): AgentDataController + Mapper SQL (에이전트용 read-only API)"
git push origin feature/rag-chatbot
```

---

## Task 10: FastAPI /agent/run 엔드포인트

**Files:**
- Modify: `ai-service/main.py`
- Create: `ai-service/tests/test_agent_endpoints.py`

- [ ] **Step 1: 실패 테스트 작성**

`ai-service/tests/test_agent_endpoints.py`:
```python
import importlib
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def test_client(tmp_path, monkeypatch):
    monkeypatch.setenv("RAG_CHROMA_DIR", str(tmp_path / "no_such"))
    import main as _main

    importlib.reload(_main)

    # agent_graph는 lifespan에서 빌드되지만 mock으로 교체
    fake_graph = MagicMock()
    fake_graph.invoke.return_value = {
        "intent": "SINGLE",
        "warnings": [],
        "proposals": [
            {
                "stadium_id": 1, "stadium_name": "강남",
                "start_time": "2026-05-23T14:00", "duration_min": 60,
                "team_a": {"id": 5, "name": "내 팀"}, "team_b": None, "stage": None,
            }
        ],
        "bracket": None,
        "proposal_id": "prop_abc12345",
    }
    _main.agent_graph = fake_graph

    with TestClient(_main.app) as client:
        yield client


def test_agent_run_returns_proposal(test_client):
    resp = test_client.post(
        "/agent/run",
        json={"user_input": "강남 토요일 매치", "user_id": 1},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["proposal_id"].startswith("prop_")
    assert body["intent"] == "SINGLE"
    assert len(body["matches"]) == 1


def test_agent_run_validates_empty_input(test_client):
    resp = test_client.post(
        "/agent/run", json={"user_input": "", "user_id": 1}
    )
    assert resp.status_code == 422
```

- [ ] **Step 2: 실패 확인**

```powershell
pytest tests/test_agent_endpoints.py -v
```
Expected: FAIL — endpoint 없음.

- [ ] **Step 3: main.py에 agent_graph + endpoint 추가**

`ai-service/main.py` 에 추가 (기존 코드 유지, import 보강 + 글로벌 + endpoint 추가):

```python
# 기존 import 아래에 추가
from agent.graph import build_agent_graph
from agent.schemas import (
    AgentRequest,
    ProposalResponse,
    MatchProposal,
    TeamSummary,
    BracketDTO,
)
from agent.springboot_client import SpringbootClient
from agent.tools import Tools

# 기존 globals 아래에 추가
agent_graph = None
```

`lifespan` 함수에서 `rag_chain = ...` 이후에 추가:

```python
    # Agent graph (RAG와 같은 Claude 클라이언트 + Spring 호출 도구로 빌드)
    global agent_graph
    spring_client = SpringbootClient()
    agent_tools = Tools(client=spring_client)
    if rag_chain is not None:
        # rag_chain 내부 claude_client를 그대로 재사용
        agent_graph = build_agent_graph(
            claude_client=rag_chain._claude, tools=agent_tools
        )
```

`/recommend/matches` 라우트 아래에 추가:

```python
@app.post("/agent/run", response_model=ProposalResponse)
def agent_run(req: AgentRequest):
    if agent_graph is None:
        raise HTTPException(
            status_code=503, detail="에이전트가 초기화되지 않았습니다."
        )
    from agent.state import make_initial_state

    state = make_initial_state(user_input=req.user_input, user_id=req.user_id)
    # 사용자 팀 정보 채우기 — MVP는 user_id만 주고 Spring에서 조회하도록.
    # 본 plan에선 단순화를 위해 team_info를 비워두고 single_team_node가 warning 발생.
    final = agent_graph.invoke(state)

    matches = [_match_dict_to_proposal(m) for m in final.get("proposals", [])]
    bracket = (
        BracketDTO(rounds=final["bracket"]["rounds"])
        if final.get("bracket") else None
    )

    return ProposalResponse(
        proposal_id=final.get("proposal_id", "prop_unknown"),
        intent=final.get("intent", "UNKNOWN"),
        warnings=final.get("warnings", []),
        matches=matches,
        bracket=bracket,
    )


def _match_dict_to_proposal(m: dict) -> MatchProposal:
    return MatchProposal(
        stadium_id=m["stadium_id"],
        stadium_name=m["stadium_name"],
        start_time=m["start_time"],
        duration_min=m.get("duration_min", 60),
        team_a=TeamSummary(**m["team_a"]),
        team_b=TeamSummary(**m["team_b"]) if m.get("team_b") else None,
        stage=m.get("stage"),
    )
```

- [ ] **Step 4: 통과 확인**

```powershell
pytest tests/test_agent_endpoints.py -v
```
Expected: 2 passed.

- [ ] **Step 5: 전체 Python 테스트 확인**

```powershell
pytest -v
```
Expected: 모든 테스트 그린 (RAG 36 + agent ~30 ≈ 66 passed).

- [ ] **Step 6: Commit**

```powershell
git add ai-service/main.py ai-service/tests/test_agent_endpoints.py
git commit -m "feat(agent): FastAPI /agent/run 엔드포인트 + lifespan에서 그래프 빌드"
git push origin feature/rag-chatbot
```

---

## Task 11: Java DTO 5개

**Files:**
- Create: `src/main/java/io/github/wizwix/letsfutsal/dto/AgentRequestDTO.java`
- Create: `src/main/java/io/github/wizwix/letsfutsal/dto/ProposalDTO.java`
- Create: `src/main/java/io/github/wizwix/letsfutsal/dto/MatchProposalDTO.java`
- Create: `src/main/java/io/github/wizwix/letsfutsal/dto/BracketDTO.java`
- Create: `src/main/java/io/github/wizwix/letsfutsal/dto/ConfirmRequestDTO.java`

테스트 없이 — 다음 Task의 AgentServiceTest에서 자연스럽게 검증됨.

- [ ] **Step 1: AgentRequestDTO**

```java
package io.github.wizwix.letsfutsal.dto;

public class AgentRequestDTO {
  private String userInput;

  public String getUserInput() { return userInput; }
  public void setUserInput(String userInput) { this.userInput = userInput; }
}
```

- [ ] **Step 2: MatchProposalDTO**

```java
package io.github.wizwix.letsfutsal.dto;

import com.fasterxml.jackson.annotation.JsonProperty;

public class MatchProposalDTO {
  @JsonProperty("stadium_id")
  private int stadiumId;

  @JsonProperty("stadium_name")
  private String stadiumName;

  @JsonProperty("start_time")
  private String startTime;

  @JsonProperty("duration_min")
  private int durationMin = 60;

  @JsonProperty("team_a")
  private TeamSummary teamA;

  @JsonProperty("team_b")
  private TeamSummary teamB;

  private String stage;

  public static class TeamSummary {
    private int id;
    private String name;
    public int getId() { return id; }
    public void setId(int id) { this.id = id; }
    public String getName() { return name; }
    public void setName(String name) { this.name = name; }
  }

  public int getStadiumId() { return stadiumId; }
  public void setStadiumId(int stadiumId) { this.stadiumId = stadiumId; }
  public String getStadiumName() { return stadiumName; }
  public void setStadiumName(String stadiumName) { this.stadiumName = stadiumName; }
  public String getStartTime() { return startTime; }
  public void setStartTime(String startTime) { this.startTime = startTime; }
  public int getDurationMin() { return durationMin; }
  public void setDurationMin(int durationMin) { this.durationMin = durationMin; }
  public TeamSummary getTeamA() { return teamA; }
  public void setTeamA(TeamSummary teamA) { this.teamA = teamA; }
  public TeamSummary getTeamB() { return teamB; }
  public void setTeamB(TeamSummary teamB) { this.teamB = teamB; }
  public String getStage() { return stage; }
  public void setStage(String stage) { this.stage = stage; }
}
```

- [ ] **Step 3: BracketDTO**

```java
package io.github.wizwix.letsfutsal.dto;

import java.util.List;
import java.util.Map;

public class BracketDTO {
  private List<List<Map<String, Object>>> rounds;
  public List<List<Map<String, Object>>> getRounds() { return rounds; }
  public void setRounds(List<List<Map<String, Object>>> rounds) { this.rounds = rounds; }
}
```

- [ ] **Step 4: ProposalDTO**

```java
package io.github.wizwix.letsfutsal.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import java.util.List;

public class ProposalDTO {
  @JsonProperty("proposal_id")
  private String proposalId;
  private String intent;
  private List<String> warnings;
  private List<MatchProposalDTO> matches;
  private BracketDTO bracket;

  public String getProposalId() { return proposalId; }
  public void setProposalId(String proposalId) { this.proposalId = proposalId; }
  public String getIntent() { return intent; }
  public void setIntent(String intent) { this.intent = intent; }
  public List<String> getWarnings() { return warnings; }
  public void setWarnings(List<String> warnings) { this.warnings = warnings; }
  public List<MatchProposalDTO> getMatches() { return matches; }
  public void setMatches(List<MatchProposalDTO> matches) { this.matches = matches; }
  public BracketDTO getBracket() { return bracket; }
  public void setBracket(BracketDTO bracket) { this.bracket = bracket; }
}
```

- [ ] **Step 5: ConfirmRequestDTO**

```java
package io.github.wizwix.letsfutsal.dto;

import java.util.List;

public class ConfirmRequestDTO {
  private String proposalId;
  private List<MatchProposalDTO> matches;

  public String getProposalId() { return proposalId; }
  public void setProposalId(String proposalId) { this.proposalId = proposalId; }
  public List<MatchProposalDTO> getMatches() { return matches; }
  public void setMatches(List<MatchProposalDTO> matches) { this.matches = matches; }
}
```

- [ ] **Step 6: 컴파일 확인**

```powershell
& $mvn -q compile
```
Expected: BUILD SUCCESS.

- [ ] **Step 7: Commit**

```powershell
git add src/main/java/io/github/wizwix/letsfutsal/dto/AgentRequestDTO.java `
        src/main/java/io/github/wizwix/letsfutsal/dto/ProposalDTO.java `
        src/main/java/io/github/wizwix/letsfutsal/dto/MatchProposalDTO.java `
        src/main/java/io/github/wizwix/letsfutsal/dto/BracketDTO.java `
        src/main/java/io/github/wizwix/letsfutsal/dto/ConfirmRequestDTO.java
git commit -m "feat(ai): Agent DTO 5종 (Request, Proposal, MatchProposal, Bracket, ConfirmRequest)"
git push origin feature/rag-chatbot
```

---

## Task 12: AgentService + JUnit (Python 호출 + 확정 트랜잭션)

**Files:**
- Create: `src/main/java/io/github/wizwix/letsfutsal/ai/AgentService.java`
- Create: `src/test/java/io/github/wizwix/letsfutsal/ai/AgentServiceTest.java`

- [ ] **Step 1: 실패 테스트 작성**

`src/test/java/io/github/wizwix/letsfutsal/ai/AgentServiceTest.java`:
```java
package io.github.wizwix.letsfutsal.ai;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.times;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import com.fasterxml.jackson.databind.ObjectMapper;
import io.github.wizwix.letsfutsal.dto.ConfirmRequestDTO;
import io.github.wizwix.letsfutsal.dto.MatchProposalDTO;
import io.github.wizwix.letsfutsal.dto.ProposalDTO;
import io.github.wizwix.letsfutsal.mapper.MatchMapper;
import java.util.List;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.test.web.client.MockRestServiceServer;
import org.springframework.web.client.RestTemplate;
import static org.springframework.test.web.client.match.MockRestRequestMatchers.method;
import static org.springframework.test.web.client.match.MockRestRequestMatchers.requestTo;
import static org.springframework.test.web.client.response.MockRestResponseCreators.withSuccess;
import org.springframework.http.HttpMethod;
import org.springframework.http.MediaType;

class AgentServiceTest {

  private RestTemplate restTemplate;
  private MockRestServiceServer server;
  private MatchMapper matchMapper;
  private AgentService service;

  @BeforeEach
  void setUp() {
    restTemplate = new RestTemplate();
    server = MockRestServiceServer.createServer(restTemplate);
    matchMapper = mock(MatchMapper.class);
    service = new AgentService(restTemplate, new ObjectMapper(), matchMapper, "http://fake:8000");
  }

  @Test
  void run_parsesProposalFromPython() {
    String json = "{\"proposal_id\":\"prop_x1\",\"intent\":\"SINGLE\",\"warnings\":[],"
        + "\"matches\":[{\"stadium_id\":1,\"stadium_name\":\"강남\","
        + "\"start_time\":\"2026-05-23T14:00\",\"duration_min\":60,"
        + "\"team_a\":{\"id\":5,\"name\":\"A\"},\"team_b\":null,\"stage\":null}],"
        + "\"bracket\":null}";
    server.expect(requestTo("http://fake:8000/agent/run"))
        .andExpect(method(HttpMethod.POST))
        .andRespond(withSuccess(json, MediaType.APPLICATION_JSON));

    ProposalDTO p = service.run(1, "강남 토요일 매치");

    assertThat(p.getProposalId()).isEqualTo("prop_x1");
    assertThat(p.getIntent()).isEqualTo("SINGLE");
    assertThat(p.getMatches()).hasSize(1);
  }

  @Test
  void confirm_insertsAllMatches() {
    when(matchMapper.insertMatch(any())).thenReturn(1);

    MatchProposalDTO m1 = new MatchProposalDTO();
    m1.setStadiumId(1);
    m1.setStartTime("2026-05-23T14:00");
    MatchProposalDTO.TeamSummary t = new MatchProposalDTO.TeamSummary();
    t.setId(5);
    t.setName("A");
    m1.setTeamA(t);

    ConfirmRequestDTO req = new ConfirmRequestDTO();
    req.setProposalId("prop_x1");
    req.setMatches(List.of(m1, m1));  // 2개 매치

    List<Integer> ids = service.confirm(req, /* userId */ 1);

    assertThat(ids).hasSize(2);
    verify(matchMapper, times(2)).insertMatch(any());
  }
}
```

- [ ] **Step 2: 실패 확인**

```powershell
& $mvn -q "-Dtest=AgentServiceTest" test
```
Expected: 컴파일 에러 — AgentService 없음.

- [ ] **Step 3: AgentService 구현**

`src/main/java/io/github/wizwix/letsfutsal/ai/AgentService.java`:
```java
package io.github.wizwix.letsfutsal.ai;

import com.fasterxml.jackson.databind.ObjectMapper;
import io.github.wizwix.letsfutsal.dto.ConfirmRequestDTO;
import io.github.wizwix.letsfutsal.dto.MatchDTO;
import io.github.wizwix.letsfutsal.dto.MatchProposalDTO;
import io.github.wizwix.letsfutsal.dto.ProposalDTO;
import io.github.wizwix.letsfutsal.mapper.MatchMapper;
import java.sql.Timestamp;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.client.RestTemplate;

@Service
public class AgentService {
  private static final Logger log = LoggerFactory.getLogger(AgentService.class);

  private final RestTemplate restTemplate;
  private final ObjectMapper objectMapper;
  private final MatchMapper matchMapper;
  private final String aiBaseUrl;

  @Autowired
  public AgentService(
      RestTemplate restTemplate, ObjectMapper objectMapper, MatchMapper matchMapper) {
    this(
        restTemplate,
        objectMapper,
        matchMapper,
        System.getenv().getOrDefault("AI_SERVICE_URL", "http://localhost:8000"));
  }

  public AgentService(
      RestTemplate restTemplate,
      ObjectMapper objectMapper,
      MatchMapper matchMapper,
      String aiBaseUrl) {
    this.restTemplate = restTemplate;
    this.objectMapper = objectMapper;
    this.matchMapper = matchMapper;
    this.aiBaseUrl = aiBaseUrl;
  }

  public ProposalDTO run(int userId, String userInput) {
    Map<String, Object> body = new HashMap<>();
    body.put("user_input", userInput);
    body.put("user_id", userId);

    try {
      return restTemplate.postForObject(
          aiBaseUrl + "/agent/run", body, ProposalDTO.class);
    } catch (Exception e) {
      log.warn("Agent /agent/run 호출 실패: {}", e.getMessage());
      throw new RuntimeException("에이전트 서비스 호출 실패", e);
    }
  }

  @Transactional
  public List<Integer> confirm(ConfirmRequestDTO req, int userId) {
    List<Integer> createdIds = new ArrayList<>();
    for (MatchProposalDTO p : req.getMatches()) {
      MatchDTO m = new MatchDTO();
      m.setStadiumId(p.getStadiumId());
      m.setMatchDate(Timestamp.valueOf(LocalDateTime.parse(p.getStartTime())));
      // 팀 ID — 매핑 가능한 필드만 세팅. 실제 MatchDTO 스키마에 맞게 조정 필요.
      // m.setTeamAId(p.getTeamA() != null ? p.getTeamA().getId() : 0);
      // m.setTeamBId(p.getTeamB() != null ? p.getTeamB().getId() : 0);
      m.setHostUserId(userId);
      int result = matchMapper.insertMatch(m);
      if (result > 0 && m.getMatchId() != null) {
        createdIds.add(m.getMatchId());
      } else {
        createdIds.add(0);  // 신원 미회수 — Mapper가 useGeneratedKeys 활성이라야 0 아닌 값
      }
    }
    log.info("Agent 확정 — 사용자 {} 매치 {}개 생성", userId, createdIds.size());
    return createdIds;
  }
}
```

> **주의**: `MatchDTO` 필드(`teamAId`, `teamBId`, `hostUserId` 등)와 `MatchMapper.insertMatch` 시그니처는 실제 코드에 맞게 조정 필요. 위 코드의 주석 처리된 라인은 스키마 확인 후 활성화. `useGeneratedKeys=true`가 mapper XML에 없으면 `createdIds`가 0으로 채워지는데, 평가만 영향 X.

- [ ] **Step 4: 통과 확인**

```powershell
& $mvn -q "-Dtest=AgentServiceTest" test
```
Expected: 2 tests passed. (`MatchMapper.insertMatch` 시그니처 차이로 컴파일 에러 나면 위 코드의 setter/mapper 호출을 실제와 일치시킨다.)

- [ ] **Step 5: Commit**

```powershell
git add src/main/java/io/github/wizwix/letsfutsal/ai/AgentService.java `
        src/test/java/io/github/wizwix/letsfutsal/ai/AgentServiceTest.java
git commit -m "feat(ai): AgentService — Python /agent/run 호출 + 확정 트랜잭션 INSERT"
git push origin feature/rag-chatbot
```

---

## Task 13: AgentController + JSP coordinator 페이지

**Files:**
- Create: `src/main/java/io/github/wizwix/letsfutsal/ai/AgentController.java`
- Create: `src/test/java/io/github/wizwix/letsfutsal/ai/AgentControllerTest.java`
- Create: `src/main/webapp/WEB-INF/views/ai/coordinator.jsp`
- Create: `src/main/webapp/resources/script/agent_coordinator.js`

- [ ] **Step 1: AgentControllerTest 작성**

`src/test/java/io/github/wizwix/letsfutsal/ai/AgentControllerTest.java`:
```java
package io.github.wizwix.letsfutsal.ai;

import static org.mockito.ArgumentMatchers.anyInt;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import io.github.wizwix.letsfutsal.dto.ProposalDTO;
import io.github.wizwix.letsfutsal.dto.UserDTO;
import jakarta.servlet.http.HttpSession;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.mock.web.MockHttpSession;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;

class AgentControllerTest {

  private MockMvc mockMvc;
  private AgentService agentService;
  private MockHttpSession session;

  @BeforeEach
  void setUp() {
    agentService = mock(AgentService.class);
    AgentController controller = new AgentController(agentService);
    mockMvc = MockMvcBuilders.standaloneSetup(controller).build();

    session = new MockHttpSession();
    UserDTO user = new UserDTO();
    user.setUserId(1);
    user.setNickname("수진");
    session.setAttribute("loginUser", user);
  }

  @Test
  void run_returns200WithProposal() throws Exception {
    ProposalDTO p = new ProposalDTO();
    p.setProposalId("prop_x1");
    p.setIntent("SINGLE");
    when(agentService.run(anyInt(), anyString())).thenReturn(p);

    mockMvc
        .perform(
            post("/ai/agent/run")
                .session(session)
                .contentType("application/json")
                .content("{\"userInput\":\"강남 매치\"}"))
        .andExpect(status().isOk())
        .andExpect(jsonPath("$.proposal_id").value("prop_x1"));
  }

  @Test
  void run_returns401WithoutLogin() throws Exception {
    mockMvc
        .perform(
            post("/ai/agent/run")
                .contentType("application/json")
                .content("{\"userInput\":\"매치\"}"))
        .andExpect(status().isUnauthorized());
  }

  @Test
  void coordinatorPage_returns200() throws Exception {
    mockMvc.perform(get("/ai/coordinator").session(session)).andExpect(status().isOk());
  }
}
```

- [ ] **Step 2: 실패 확인**

```powershell
& $mvn -q "-Dtest=AgentControllerTest" test
```
Expected: 컴파일 에러 — Controller 없음.

- [ ] **Step 3: AgentController 구현**

`src/main/java/io/github/wizwix/letsfutsal/ai/AgentController.java`:
```java
package io.github.wizwix.letsfutsal.ai;

import io.github.wizwix.letsfutsal.dto.AgentRequestDTO;
import io.github.wizwix.letsfutsal.dto.ConfirmRequestDTO;
import io.github.wizwix.letsfutsal.dto.ProposalDTO;
import io.github.wizwix.letsfutsal.dto.UserDTO;
import jakarta.servlet.http.HttpSession;
import java.util.List;
import java.util.Map;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.ResponseBody;

@Controller
@RequestMapping("/ai")
public class AgentController {
  private final AgentService agentService;

  public AgentController(AgentService agentService) {
    this.agentService = agentService;
  }

  @GetMapping("/coordinator")
  public String page() {
    return "ai/coordinator";
  }

  @PostMapping("/agent/run")
  @ResponseBody
  public ResponseEntity<?> run(@RequestBody AgentRequestDTO req, HttpSession session) {
    UserDTO user = (UserDTO) session.getAttribute("loginUser");
    if (user == null) {
      return ResponseEntity.status(401).body(Map.of("error", "로그인이 필요합니다."));
    }
    if (req.getUserInput() == null || req.getUserInput().isBlank()) {
      return ResponseEntity.badRequest().body(Map.of("error", "요청 내용을 입력해주세요."));
    }
    ProposalDTO p = agentService.run(user.getUserId(), req.getUserInput());
    return ResponseEntity.ok(p);
  }

  @PostMapping("/agent/confirm")
  @ResponseBody
  public ResponseEntity<?> confirm(
      @RequestBody ConfirmRequestDTO req, HttpSession session) {
    UserDTO user = (UserDTO) session.getAttribute("loginUser");
    if (user == null) {
      return ResponseEntity.status(401).body(Map.of("error", "로그인이 필요합니다."));
    }
    List<Integer> ids = agentService.confirm(req, user.getUserId());
    return ResponseEntity.ok(Map.of("createdMatchIds", ids));
  }
}
```

- [ ] **Step 4: coordinator.jsp 작성**

`src/main/webapp/WEB-INF/views/ai/coordinator.jsp`:
```jsp
<%@ page contentType="text/html;charset=UTF-8" language="java" %>
<%@ taglib uri="jakarta.tags.core" prefix="c" %>
<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <title>매치 코디네이터</title>
  <link rel="stylesheet" href="${pageContext.request.contextPath}/resources/css/common.css">
</head>
<body>
<jsp:include page="/WEB-INF/views/common/header.jsp"/>

<main class="container py-4">
  <h2>AI 매치 코디네이터</h2>
  <p class="text-muted">자연어로 매치 또는 토너먼트 요청을 입력하세요.</p>

  <div class="card p-3 mb-3">
    <textarea id="userInput" class="form-control" rows="3"
      placeholder="예: 이번 주말 강남에서 4팀 토너먼트 잡아줘"></textarea>
    <button id="runBtn" class="btn btn-primary mt-2">에이전트 실행</button>
  </div>

  <div id="proposalArea" style="display:none">
    <h3>미리보기</h3>
    <div id="warningsBox" class="alert alert-warning" style="display:none"></div>
    <div id="matchList"></div>
    <button id="confirmBtn" class="btn btn-success mt-3">매치 확정 (DB 저장)</button>
  </div>

  <div id="resultArea" style="display:none" class="alert alert-success mt-3"></div>
</main>

<script>
  window.AGENT_CTX = '${pageContext.request.contextPath}';
</script>
<script src="${pageContext.request.contextPath}/resources/script/agent_coordinator.js"></script>
</body>
</html>
```

- [ ] **Step 5: agent_coordinator.js 작성**

`src/main/webapp/resources/script/agent_coordinator.js`:
```javascript
(function() {
  const ctx = window.AGENT_CTX || '';
  let currentProposal = null;

  document.getElementById('runBtn').addEventListener('click', async function() {
    const text = document.getElementById('userInput').value.trim();
    if (!text) return;

    this.disabled = true;
    this.textContent = '에이전트 실행 중...';

    try {
      const resp = await fetch(ctx + '/ai/agent/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ userInput: text })
      });
      const data = await resp.json();
      if (!resp.ok) {
        alert(data.error || '오류가 발생했습니다.');
        return;
      }
      currentProposal = data;
      renderProposal(data);
    } catch (e) {
      alert('연결 오류: ' + e.message);
    } finally {
      this.disabled = false;
      this.textContent = '에이전트 실행';
    }
  });

  document.getElementById('confirmBtn').addEventListener('click', async function() {
    if (!currentProposal) return;
    this.disabled = true;
    this.textContent = '저장 중...';

    try {
      const resp = await fetch(ctx + '/ai/agent/confirm', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          proposalId: currentProposal.proposal_id,
          matches: currentProposal.matches
        })
      });
      const data = await resp.json();
      if (!resp.ok) {
        alert(data.error || '저장 실패');
        return;
      }
      document.getElementById('resultArea').style.display = 'block';
      document.getElementById('resultArea').textContent =
        '매치 ' + data.createdMatchIds.length + '건 생성 완료. IDs: ' + data.createdMatchIds.join(', ');
      document.getElementById('proposalArea').style.display = 'none';
    } catch (e) {
      alert('저장 오류: ' + e.message);
    } finally {
      this.disabled = false;
      this.textContent = '매치 확정 (DB 저장)';
    }
  });

  function renderProposal(p) {
    document.getElementById('proposalArea').style.display = 'block';

    const warnBox = document.getElementById('warningsBox');
    if (p.warnings && p.warnings.length) {
      warnBox.style.display = 'block';
      warnBox.innerHTML = '<strong>경고:</strong><br>' + p.warnings.map(w => '• ' + w).join('<br>');
    } else {
      warnBox.style.display = 'none';
    }

    const list = document.getElementById('matchList');
    list.innerHTML = '';
    (p.matches || []).forEach(function(m, idx) {
      const card = document.createElement('div');
      card.className = 'card mb-2 p-2';
      card.innerHTML =
        '<div><strong>' + (m.stage || '매치') + '</strong> — ' +
        '<input type="datetime-local" value="' + m.start_time.substring(0, 16) + '" data-idx="' + idx + '" data-field="start_time"></div>' +
        '<div>경기장: ' + m.stadium_name + ' (id ' + m.stadium_id + ')</div>' +
        '<div>팀: ' + (m.team_a ? m.team_a.name : '?') +
        (m.team_b ? ' vs ' + m.team_b.name : '') + '</div>' +
        '<button class="btn btn-sm btn-danger" data-remove="' + idx + '">삭제</button>';
      list.appendChild(card);
    });

    // 편집 핸들러
    list.querySelectorAll('input[data-field=start_time]').forEach(function(input) {
      input.addEventListener('change', function() {
        const idx = parseInt(input.dataset.idx, 10);
        currentProposal.matches[idx].start_time = input.value;
      });
    });
    list.querySelectorAll('[data-remove]').forEach(function(btn) {
      btn.addEventListener('click', function() {
        const idx = parseInt(btn.dataset.remove, 10);
        currentProposal.matches.splice(idx, 1);
        renderProposal(currentProposal);
      });
    });
  }
})();
```

- [ ] **Step 6: WebConfig에 /ai/coordinator 인증 필요 (인터셉터 그대로)**

`/ai/coordinator`는 LoginInterceptor에서 인증 검사 적용 — 기본 동작. 별도 수정 불필요.

- [ ] **Step 7: 통과 확인 (Controller 테스트)**

```powershell
& $mvn -q "-Dtest=AgentControllerTest" test
```
Expected: 3 tests passed.

- [ ] **Step 8: 전체 빌드 + 패키지**

```powershell
& $mvn -q package "-DskipTests"
```
Expected: BUILD SUCCESS, `target/letsfutsal.war` 생성.

- [ ] **Step 9: Commit**

```powershell
git add src/main/java/io/github/wizwix/letsfutsal/ai/AgentController.java `
        src/test/java/io/github/wizwix/letsfutsal/ai/AgentControllerTest.java `
        src/main/webapp/WEB-INF/views/ai/coordinator.jsp `
        src/main/webapp/resources/script/agent_coordinator.js
git commit -m "feat(ai): AgentController + /ai/coordinator JSP 페이지 + 편집 JS"
git push origin feature/rag-chatbot
```

---

## Task 14: 평가 시나리오 8개 + run_agent_eval

**Files:**
- Create: `ai-service/eval/agent_scenarios.jsonl`
- Create: `ai-service/eval/run_agent_eval.py`

LLM judge로 `intent_acc`, `tool_correctness`, `proposal_validity`, `e2e_success` 4지표 측정.

- [ ] **Step 1: 시나리오 작성**

`ai-service/eval/agent_scenarios.jsonl`:
```jsonl
{"id":"s01","user_input":"강남 토요일 5인 매치 잡아줘","expected_intent":"SINGLE","expected_tools":["search_stadium","list_stadium_slots"],"min_proposals":1}
{"id":"s02","user_input":"이번 주말 우리 팀이랑 매치 시간 골라줘","expected_intent":"SINGLE","expected_tools":["search_stadium","find_team_conflicts"],"min_proposals":1}
{"id":"s03","user_input":"다음 주 풋살장 빈 시간대만 알려줘","expected_intent":"SINGLE","expected_tools":["search_stadium","list_stadium_slots"],"min_proposals":0}
{"id":"s04","user_input":"강남 풋살장 추천해줘","expected_intent":"SINGLE","expected_tools":["search_stadium"],"min_proposals":0}
{"id":"s05","user_input":"4팀 토너먼트, 강남 일요일","expected_intent":"TOURNAMENT","expected_tools":["search_stadium","list_stadium_slots","list_team_members"],"min_proposals":3}
{"id":"s06","user_input":"8팀 토너먼트 기획해줘","expected_intent":"TOURNAMENT","expected_tools":["search_stadium","list_stadium_slots"],"min_proposals":7}
{"id":"s07","user_input":"토너먼트 — 경기장 부족 가정해서","expected_intent":"TOURNAMENT","expected_tools":["search_stadium"],"min_proposals":0,"expect_warning":true}
{"id":"s08","user_input":"3팀으로 토너먼트 해줘","expected_intent":"TOURNAMENT","expected_tools":[],"min_proposals":0,"expect_warning":true}
```

- [ ] **Step 2: run_agent_eval.py 작성**

`ai-service/eval/run_agent_eval.py`:
```python
"""LangGraph 에이전트 정량 평가.

사용법:
    python -m eval.run_agent_eval --out eval/agent_report.md
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

load_dotenv()

from agent.graph import build_agent_graph
from agent.springboot_client import SpringbootClient
from agent.state import make_initial_state
from agent.tools import Tools
from rag.claude_client import ClaudeClient


def load_scenarios(path: Path) -> list[dict[str, Any]]:
    out = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            out.append(json.loads(line))
    return out


def judge_tool_correctness(
    claude: ClaudeClient, expected_tools: list[str], actual_warnings: list[str]
) -> int:
    """LLM judge: warnings/errors 패턴으로 기대 Tool 호출 흔적을 점검."""
    if not expected_tools:
        return 1
    system = (
        "당신은 LangGraph 에이전트의 Tool 호출 검증자입니다. "
        "EXPECTED_TOOLS에 포함된 도구들이 모두 호출된 흔적이 ACTUAL_NOTES에 보이면 1, "
        "누락이 있으면 0을 출력하세요. 출력은 0 또는 1만."
    )
    user = (
        f"EXPECTED_TOOLS: {expected_tools}\n\n"
        f"ACTUAL_NOTES: {actual_warnings}\n\n0 또는 1만:"
    )
    out = claude.chat(system=system, user=user, max_tokens=4).strip()
    return 1 if out.startswith("1") else 0


def run_one(scenario: dict, graph, claude: ClaudeClient) -> dict:
    state = make_initial_state(scenario["user_input"], user_id=1)
    state["team_info"] = {
        "team_ids": [1, 2, 3, 4, 5, 6, 7, 8][: 4 if "4팀" in scenario["user_input"] else 8],
        "team_names": {i: f"T{i}" for i in range(1, 9)},
        "team_id": 5,
        "team_name": "T5",
    }
    final = graph.invoke(state)

    intent_ok = 1 if final["intent"] == scenario["expected_intent"] else 0
    proposal_ok = 1 if len(final.get("proposals", [])) >= scenario["min_proposals"] else 0
    tool_ok = judge_tool_correctness(
        claude,
        scenario.get("expected_tools", []),
        final.get("warnings", []) + final.get("errors", []),
    )
    e2e_ok = 1 if (intent_ok and proposal_ok and tool_ok) else 0

    if scenario.get("expect_warning") and not final.get("warnings"):
        proposal_ok = 0
        e2e_ok = 0

    return {
        "id": scenario["id"],
        "user_input": scenario["user_input"],
        "expected_intent": scenario["expected_intent"],
        "actual_intent": final["intent"],
        "intent_ok": bool(intent_ok),
        "proposal_ok": bool(proposal_ok),
        "tool_ok": bool(tool_ok),
        "e2e_ok": bool(e2e_ok),
        "actual_proposals": len(final.get("proposals", [])),
        "warnings_count": len(final.get("warnings", [])),
    }


def evaluate(scenarios: list[dict]) -> dict:
    claude = ClaudeClient()
    spring = SpringbootClient()  # 실제 Spring 호출 — 또는 mock으로 교체 가능
    tools = Tools(client=spring)
    graph = build_agent_graph(claude_client=claude, tools=tools)

    results = [run_one(s, graph, claude) for s in scenarios]
    n = len(results)
    return {
        "intent_acc": sum(r["intent_ok"] for r in results) / n,
        "tool_correctness": sum(r["tool_ok"] for r in results) / n,
        "proposal_validity": sum(r["proposal_ok"] for r in results) / n,
        "e2e_success": sum(r["e2e_ok"] for r in results) / n,
        "results": results,
    }


def format_report(metrics: dict) -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = [
        "# LangGraph 에이전트 평가 리포트",
        "",
        f"- 실행 시각: {now}",
        f"- 시나리오 수: {len(metrics['results'])}",
        "",
        "## 핵심 지표",
        "",
        "| 지표 | 값 | 목표 | 통과 |",
        "|---|---|---|---|",
        f"| intent_acc | {metrics['intent_acc']:.3f} | ≥ 0.90 | "
        f"{'✅' if metrics['intent_acc'] >= 0.90 else '❌'} |",
        f"| tool_correctness | {metrics['tool_correctness']:.3f} | ≥ 0.85 | "
        f"{'✅' if metrics['tool_correctness'] >= 0.85 else '❌'} |",
        f"| proposal_validity | {metrics['proposal_validity']:.3f} | ≥ 0.90 | "
        f"{'✅' if metrics['proposal_validity'] >= 0.90 else '❌'} |",
        f"| e2e_success | {metrics['e2e_success']:.3f} | ≥ 0.75 | "
        f"{'✅' if metrics['e2e_success'] >= 0.75 else '❌'} |",
        "",
        "## 시나리오별 결과",
        "",
        "| id | input | intent | proposal | tool | e2e |",
        "|---|---|---|---|---|---|",
    ]
    for r in metrics["results"]:
        lines.append(
            f"| {r['id']} | {r['user_input']} | "
            f"{'✅' if r['intent_ok'] else '❌'} ({r['actual_intent']}) | "
            f"{'✅' if r['proposal_ok'] else '❌'} ({r['actual_proposals']}) | "
            f"{'✅' if r['tool_ok'] else '❌'} | "
            f"{'✅' if r['e2e_ok'] else '❌'} |"
        )
    return "\n".join(lines) + "\n"


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--scenarios", default="eval/agent_scenarios.jsonl", type=Path)
    p.add_argument("--out", default="eval/agent_report.md", type=Path)
    args = p.parse_args()

    scenarios = load_scenarios(args.scenarios)
    print(f"시나리오 {len(scenarios)}개 로드. 평가 시작 (LLM judge 호출됨)...")
    metrics = evaluate(scenarios)
    report = format_report(metrics)
    args.out.write_text(report, encoding="utf-8")

    print()
    print(f"intent_acc        : {metrics['intent_acc']:.3f}")
    print(f"tool_correctness  : {metrics['tool_correctness']:.3f}")
    print(f"proposal_validity : {metrics['proposal_validity']:.3f}")
    print(f"e2e_success       : {metrics['e2e_success']:.3f}")
    print()
    print(f"리포트 저장: {args.out}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 3: 파싱 sanity check (실행은 크레딧 필요)**

```powershell
cd ai-service
python -c "from pathlib import Path; from eval.run_agent_eval import load_scenarios; print(len(load_scenarios(Path('eval/agent_scenarios.jsonl'))))"
```
Expected: `8`

- [ ] **Step 4: Commit**

```powershell
git add ai-service/eval/agent_scenarios.jsonl ai-service/eval/run_agent_eval.py
git commit -m "feat(agent): 평가 시나리오 8개 + run_agent_eval 스크립트"
git push origin feature/rag-chatbot
```

---

## Task 15: 통합 수동 smoke test (크레딧 필요)

**Files:** (없음 — 검증 단계)

이 Task는 자동 테스트 없고 수동 시나리오 확인. Anthropic 크레딧 활성 + Tomcat 실행 + Python 서버 실행 필요.

- [ ] **Step 1: Python 서버 실행 (백그라운드)**

```powershell
cd ai-service
.\venv\Scripts\Activate.ps1
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

- [ ] **Step 2: Tomcat에 letsfutsal.war 배포**

`target/letsfutsal.war`를 Tomcat `webapps/`에 복사 또는 IntelliJ run configuration으로 실행. `CLAUDE_API_KEY` 환경변수가 Tomcat 프로세스에 주입되어 있어야 함.

- [ ] **Step 3: 브라우저에서 시나리오 4개 수동 시도**

`http://localhost:8080/letsfutsal/ai/coordinator` 접속:

1. "이번 주 토요일 강남 매치 잡아줘" → SINGLE, matches ≥ 1, 미리보기 표시
2. "다음 주 일요일 4팀 토너먼트 기획" → TOURNAMENT, matches 3, bracket 표시
3. 미리보기에서 매치 1개 시간 변경 후 "확정" → DB INSERT 성공, `createdMatchIds` 응답
4. Python 서버 중지 후 다시 시도 → 500 에러 화면 + 사용자 친화 메시지

각 시나리오 결과 캡처 (스크린샷 또는 GIF). PR 본문 첨부용.

- [ ] **Step 4: DB 확인**

```sql
SELECT * FROM tb_match WHERE host_user_id = 1 ORDER BY match_id DESC LIMIT 10;
```
3개 시나리오에서 생성된 매치들이 보여야 함.

- [ ] **Step 5: 평가 실행 (선택, 크레딧 ~ $1)**

```powershell
cd ai-service
python -m eval.run_agent_eval --out eval/agent_report.md
```
Expected: 4지표 출력 + `eval/agent_report.md` 생성. 4지표 목표 통과 확인.

- [ ] **Step 6: 메모리 + 진행 노트 갱신**

`C:\Users\emdak\.claude\projects\C--letsfutsal\memory\project_rag_chatbot_progress.md`(또는 신규 `project_langgraph_agent_progress.md`)에 결과 기록:

- 평가 지표 4개 실측치
- 데모 시나리오 통과 여부
- 발견된 버그·개선점

- [ ] **Step 7: smoke test commit (코드 변경 없음, 메모리만)**

이 Task는 코드 변경이 없어 별도 commit 불필요. 다음 Task에서 문서·메모리 한 번에 commit.

---

## Task 16: 문서 업데이트 + 로드맵 완료 표시

**Files:**
- Modify: `ai-service/README.md`
- Modify: `CLAUDE.md`
- Modify: `docs/ai-features-roadmap.md`

- [ ] **Step 1: ai-service/README.md에 Agent 섹션 추가**

`ai-service/README.md`의 "## 구성 요소" 아래에 추가:

```markdown
- **LangGraph 에이전트** (`agent/`) — 단일 매치 / 토너먼트 코디네이터, StateGraph + conditional edge + ThreadPoolExecutor 병렬 sub-agent
```

`## 엔드포인트` 표에 추가:

```markdown
| POST | `/agent/run` | LangGraph 에이전트 실행 → ProposalDTO |
```

`## RAG 사전 인덱싱` 다음에 신규 섹션 추가:

```markdown
## 에이전트 실행

별도 사전 인덱싱 불필요. `/agent/run` 호출 시 lifespan에서 빌드된 그래프가 즉시 실행.
요청에 사용자 팀 정보를 포함시키려면 Spring 측에서 `team_info`를 채워 전달 (현재 MVP는 user_id만 전달, 향후 확장).

## 에이전트 평가

\`\`\`powershell
python -m eval.run_agent_eval --out eval/agent_report.md
\`\`\`

4개 지표:
- `intent_acc` — 의도 분류 정확도 (목표 ≥ 0.90)
- `tool_correctness` — 기대 Tool 호출 검증 (목표 ≥ 0.85)
- `proposal_validity` — 미리보기 유효성 (목표 ≥ 0.90)
- `e2e_success` — 시나리오 전체 통과 (목표 ≥ 0.75)
```

- [ ] **Step 2: CLAUDE.md "AI 기능 구조"에 에이전트 항목 추가**

`### AI 기능 구조` 섹션 끝에 추가:

```markdown
**LangGraph 에이전트** (기능 3, `/ai/coordinator` 페이지)

별도 페이지에서 자연어 요청을 받아 LangGraph StateGraph로 처리:

\`\`\`
사용자 입력 → parse_intent (Claude Tool Use) → conditional edge
  ├─ SINGLE      → single_stadium → single_team → single_match → review
  └─ TOURNAMENT  → ThreadPoolExecutor로 Stadium/Team/MatchAgent 병렬 → tournament_assemble
→ summarize → ProposalDTO 응답 → 사용자 편집 → /ai/agent/confirm → DB INSERT
\`\`\`

- **Spring 측**: `ai/AgentController.java`, `ai/AgentService.java`, `ai/AgentDataController.java` (에이전트용 read-only API), `dto/AgentRequestDTO.java`, `dto/ProposalDTO.java`, `dto/MatchProposalDTO.java`, `dto/BracketDTO.java`, `dto/ConfirmRequestDTO.java`
- **Python ai-service** (`ai-service/agent/`): LangGraph 0.2 + Tool 6개 + StateGraph + 3개 sub-agent. 자세히는 [`ai-service/README.md`](ai-service/README.md).
```

- [ ] **Step 3: docs/ai-features-roadmap.md "기능 3" 섹션 완료 표시**

기능 3 헤더를 다음으로 변경:

```markdown
## 기능 3. LangGraph 매치 코디네이터 + 토너먼트 에이전트 ✅ 구현 완료 (YYYY-MM-DD)
```

각 sub-섹션 채움 — RAG 기능 2와 동일 패턴 (구현 결과, 산출물, 기술 스택, 기간, 이력서 포인트).

"## 다음 단계"의 2번 마크다운을 `~~`로 감싸 완료 표시:

```markdown
2. ~~**브레인스토밍 #2**: 기능 3 (LangGraph 에이전트)~~ ✅ YYYY-MM-DD 구현 완료
```

- [ ] **Step 4: Commit**

```powershell
git add ai-service/README.md CLAUDE.md docs/ai-features-roadmap.md
git commit -m "docs: LangGraph 에이전트 구현 완료 반영 (README, CLAUDE.md, 로드맵)"
git push origin feature/rag-chatbot
```

- [ ] **Step 5: 메모리 갱신**

`C:\Users\emdak\.claude\projects\C--letsfutsal\memory\` 에 신규 파일:

`project_langgraph_agent_progress.md`:
```markdown
---
name: langgraph-agent-progress
description: LangGraph 매치 코디네이터 + 토너먼트 에이전트 구현 완료 — Task 0~16 모두 마침
metadata:
  type: project
---

# LangGraph 에이전트 구현 완료 (YYYY-MM-DD)

브랜치: `feature/rag-chatbot` (또는 신규 머지 브랜치)
Spec: docs/superpowers/specs/2026-05-19-langgraph-agent-design.md
Plan: docs/superpowers/plans/2026-05-19-langgraph-agent.md
관련: [[project_ai_roadmap]] [[rag-chatbot-progress]]

## 산출물
- Python `agent/` 패키지 6개 모듈 + 평가 8 시나리오
- Java AgentController/AgentService/AgentDataController + DTO 5종
- /ai/coordinator JSP 페이지 + 편집 JS
- 단위 테스트 ~40개 통과
- 평가 지표 실측치: intent_acc=..., tool_correctness=..., proposal_validity=..., e2e_success=...

## 이력서 포인트
> LangGraph StateGraph + Tool Use 기반 풋살 매치 코디네이터 구현. Intent 분류 노드에서 conditional edge로 단일 매치/토너먼트 서브그래프 분기. 토너먼트는 StadiumAgent/TeamAgent/MatchAgent 3개 sub-agent의 ThreadPoolExecutor 병렬 실행으로 일정·경기장·팀 매칭을 동시 처리 후 통합. 미리보기 편집 → 사용자 확정 → 트랜잭션 INSERT.

## 다음 단계
- 기능 1 (ML 포즈 분석) 브레인스토밍 시작
```

`MEMORY.md`에 인덱스 추가:
```
- [LangGraph 에이전트 완료](project_langgraph_agent_progress.md) — 기능 3 구현 완료, Spec/Plan 참조
```

- [ ] **Step 6: 메모리 commit (별도)**

메모리 파일은 git 추적 외. 단순 파일 시스템 변경.

---

## 최종 점검 체크리스트

- [ ] 모든 Python 테스트 그린 (`pytest -v` — RAG 36 + agent ~30 ≈ 66 passed)
- [ ] 모든 Java 테스트 그린 (`mvn test`)
- [ ] WAR 빌드 성공 (`mvn package`)
- [ ] 평가 4지표 목표 통과 (`agent_report.md`)
- [ ] 수동 시나리오 4개 데모 캡처
- [ ] 메모리에 진행 상태 갱신
- [ ] 모든 commit이 `origin/feature/rag-chatbot`에 push됨
- [ ] PR 본문 초안 작성 (Spec 링크 + Plan 링크 + 데모 캡처 + 평가 지표 표)

---

## 발견 시 plan 갱신할 만한 위험

| 위험 | 대응 |
|---|---|
| LangGraph 0.2 API 변경 (`StateGraph.add_conditional_edges` 시그니처) | Task 8 실패 시 langgraph 공식 docs 참고하여 시그니처 보정 |
| `MatchDTO` 스키마와 `MatchProposalDTO` 매핑 불일치 | Task 12 컴파일 에러로 노출 — setter/getter 즉시 보정 |
| `team_info` 자동 채우기 (Spring → Python) 누락 | 초기 MVP는 user_id만, 향후 `team_info` 사전 조회 추가 |
| Anthropic 크레딧 부족 | Task 15 보류 가능. 코드는 그대로 완성. 크레딧 풀리면 평가만 1회 |
| Tomcat에 `CLAUDE_API_KEY` 환경변수 미주입 | `setenv.bat`/IntelliJ run config로 주입 확인 후 재기동 |

---

## 다음 단계 (이 plan 완료 후)

기능 1 (MediaPipe ML 포즈 분석) 브레인스토밍 → spec → plan → 구현. 별도 사이클.

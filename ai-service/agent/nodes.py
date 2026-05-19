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


# ---------- 단일 매치 흐름 노드 ----------
from .tools import Tools, propose_match  # noqa: E402


def single_stadium_node(state: AgentState, tools: Tools) -> AgentState:
    """슬롯에서 region/date를 꺼내 경기장 후보 검색."""
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
    """팀 멤버 + 이미 잡힌 매치(충돌) 조회."""
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
        if s_start and s_end and c.get("start") and c.get("end"):
            if not (s_end <= c["start"] or s_start >= c["end"]):
                return True
    return False


def single_match_node(state: AgentState, tools: Tools) -> AgentState:
    """경기장 후보 × 시간 슬롯에서 충돌 없는 매치 제안 최대 3개 생성."""
    candidates = state["stadium_candidates"]
    team_info = state["team_info"]
    conflicts = team_info.get("conflicts", []) if team_info else []
    team_a = {
        "id": team_info.get("team_id"),
        "name": team_info.get("team_name", "내 팀"),
    }
    proposals: list[dict] = []
    date = state["slots"].get("date_from", "")

    for stadium in candidates[:5]:
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
            if len(proposals) >= 3:
                break
        if len(proposals) >= 3:
            break

    state["proposals"] = proposals
    return state


def single_review_node(state: AgentState, tools: Tools) -> AgentState:
    """단순 검증 — 제안 0 + warnings 없으면 경고 추가."""
    if not state["proposals"] and not state["warnings"]:
        state["warnings"].append("적합한 매치 슬롯이 없습니다.")
    return state

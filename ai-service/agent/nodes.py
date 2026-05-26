from __future__ import annotations

from datetime import date as _date, timedelta

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

def _build_parse_system() -> str:
    today = _date.today()
    weekday_names = ["월요일", "화요일", "수요일", "목요일", "금요일", "토요일", "일요일"]
    this_sat = today + timedelta(days=(5 - today.weekday()) % 7)
    this_sun = today + timedelta(days=(6 - today.weekday()) % 7)
    next_mon = today + timedelta(days=(7 - today.weekday()) % 7 or 7)
    return (
        "당신은 풋살 매치 코디네이터의 의도 분류기입니다. "
        "사용자 입력에서 SINGLE(단일 매치)/TOURNAMENT(토너먼트)를 분류하고, "
        "지역·날짜 범위·팀 수를 슬롯으로 추출하세요.\n\n"
        f"**기준 날짜**: 오늘은 {today.isoformat()} ({weekday_names[today.weekday()]})입니다.\n"
        f"- '이번 주말' = {this_sat.isoformat()}(토) ~ {this_sun.isoformat()}(일)\n"
        f"- '다음 주' = {next_mon.isoformat()}부터 시작하는 주\n"
        "- 사용자가 날짜를 명시하지 않으면 가장 가까운 토요일을 기본값으로 사용하세요.\n"
        "- 모든 날짜는 ISO 형식(YYYY-MM-DD)으로 반환하세요.\n\n"
        "정보가 없으면 해당 슬롯을 비웁니다. extract_intent 도구로 반환하세요."
    )


def parse_intent(state: AgentState, claude_client: ClaudeClient) -> AgentState:
    """사용자 입력을 intent + slots로 분류 (현재 날짜 컨텍스트 포함)."""
    try:
        result = claude_client.chat_with_tool(
            system=_build_parse_system(),
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
    state["tool_calls"].append("search_stadium")
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

    slots = state["slots"]
    date_from = slots.get("date_from") or _date.today().isoformat()
    date_to = slots.get("date_to") or date_from
    team_info["members"] = tools.list_team_members(team_id)
    team_info["conflicts"] = tools.find_team_conflicts(team_id, date_from, date_to)
    state["tool_calls"].extend(["list_team_members", "find_team_conflicts"])
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
    from datetime import date as _date, timedelta

    candidates = state["stadium_candidates"]
    team_info = state["team_info"]
    conflicts = team_info.get("conflicts", []) if team_info else []
    team_a = {
        "id": team_info.get("team_id"),
        "name": team_info.get("team_name", "내 팀"),
    }
    proposals: list[dict] = []
    date = state["slots"].get("date_from") or ""
    if not date:
        # LLM이 날짜 추출 못한 경우 — 오늘 기준 가장 가까운 토요일
        today = _date.today()
        days_to_sat = (5 - today.weekday()) % 7
        next_sat = today + timedelta(days=days_to_sat)
        date = next_sat.isoformat()
        state["warnings"].append(
            f"날짜가 명시되지 않아 이번 주 토요일({date})로 가정합니다."
        )

    for stadium in candidates[:5]:
        slots = tools.list_stadium_slots(stadium["id"], date)
        state["tool_calls"].append("list_stadium_slots")
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


# ---------- 토너먼트 흐름 노드 ----------
import uuid
from concurrent.futures import ThreadPoolExecutor

from .subagents import MatchAgent, StadiumAgent, TeamAgent


def _round_to_power_of_2(n: int) -> int:
    """2/4/8/16 중 가장 가까운 거듭제곱(generate_bracket 호환). 최소 2, 최대 16."""
    n = max(2, min(int(n), 16))
    powers = [2, 4, 8, 16]
    return min(powers, key=lambda p: (abs(p - n), -p))


def tournament_assemble_node(state: AgentState, tools: Tools) -> AgentState:
    """3개 sub-agent를 병렬 실행 후 결과 통합.

    사용자 소속 팀이 부족하면 slots.team_count 기준으로 데모용 더미 팀을 자동
    보충(power-of-2 보정). 실제 토너먼트 운영 시 모집 팀을 따로 받아야 한다는
    안내 warning 함께 표시.
    """
    slots = state["slots"]
    team_info = state["team_info"]
    team_ids: list[int] = list(team_info.get("team_ids", []))
    team_names: dict = dict(team_info.get("team_names", {}))
    desired = slots.get("team_count") or 4
    desired = _round_to_power_of_2(desired)

    if len(team_ids) < desired:
        existing = set(team_ids)
        next_id = 1
        added: list[int] = []
        while len(team_ids) < desired:
            if next_id not in existing:
                team_ids.append(next_id)
                team_names.setdefault(next_id, f"데모팀 T{next_id}")
                added.append(next_id)
                existing.add(next_id)
            next_id += 1
        if added:
            state["warnings"].append(
                f"실제 소속 팀이 부족해 데모용 팀({', '.join('T'+str(i) for i in added)})을 "
                f"자동 추가했습니다. 운영 시에는 모집 팀을 따로 등록해 주세요."
            )
        # 보정된 team_info를 state에도 반영해 sub-graph 결과 통합 시 이름 lookup 가능
        team_info = {**team_info, "team_ids": team_ids, "team_names": team_names}

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

    # team_result["teams"]가 비어 있어도 보정된 team_ids로 진행
    if not team_result["teams"]:
        teams_with_names = [
            {"id": tid, "name": team_names.get(tid, f"T{tid}")} for tid in team_ids
        ]
    else:
        teams_with_names = [
            {
                "id": t["id"],
                "name": team_names.get(t["id"], str(t["id"])),
            }
            for t in team_result["teams"]
        ]

    match_result = match_agent.run(
        teams=teams_with_names, slots=stadium_result["slots"]
    )

    state["stadium_candidates"] = stadium_result["candidates"]
    state["team_info"] = {**team_info, "details": team_result["teams"]}
    state["bracket"] = match_result["bracket"]
    state["proposals"] = match_result["proposals"]
    state["warnings"].extend(match_result.get("warnings", []))
    # StadiumAgent: search_stadium + list_stadium_slots / TeamAgent: list_team_members + find_team_conflicts /
    # MatchAgent: generate_bracket + propose_match
    state["tool_calls"].extend(
        [
            "search_stadium",
            "list_stadium_slots",
            "list_team_members",
            "find_team_conflicts",
            "generate_bracket",
            "propose_match",
        ]
    )
    return state


def summarize_node(state: AgentState) -> AgentState:
    """proposal_id 부여 + 최종 정리."""
    state["proposal_id"] = "prop_" + uuid.uuid4().hex[:8]
    if not state["proposals"] and not state["errors"]:
        state["warnings"].append("제안할 매치가 없습니다. 조건을 완화해보세요.")
    return state

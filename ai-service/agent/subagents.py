from __future__ import annotations

from .tools import Tools, generate_bracket, propose_match


class StadiumAgent:
    """경기장 후보 + 시간 슬롯 검색 전담 sub-agent."""

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
                if len(slots) >= needed_matches * 2:
                    break
            if len(slots) >= needed_matches * 2:
                break
        return {"candidates": candidates, "slots": slots}


class TeamAgent:
    """팀별 멤버·일정 충돌 조회 전담 sub-agent."""

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
    """대진표 생성 + 슬롯 매칭으로 매치 제안 N개 생성하는 sub-agent."""

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

        for round_idx, round_matches in enumerate(bracket["rounds"]):
            stage = self._stage_label(round_idx, len(bracket["rounds"]))
            for m in round_matches:
                if len(proposals) >= len(slots):
                    break
                slot = slots[len(proposals)]
                if "teamA" in m:
                    team_a = next(t for t in teams if t["id"] == m["teamA"])
                    team_b = next(t for t in teams if t["id"] == m["teamB"])
                    proposals.append(
                        propose_match(
                            stadium_id=slot["stadium_id"],
                            stadium_name=slot["stadium_name"],
                            start_time=slot["start"],
                            team_a={
                                "id": team_a["id"],
                                "name": team_a.get("name", str(team_a["id"])),
                            },
                            team_b={
                                "id": team_b["id"],
                                "name": team_b.get("name", str(team_b["id"])),
                            },
                            stage=stage,
                        )
                    )
                else:
                    proposals.append(
                        propose_match(
                            stadium_id=slot["stadium_id"],
                            stadium_name=slot["stadium_name"],
                            start_time=slot["start"],
                            team_a={
                                "id": 0,
                                "name": f"TBD (match {m['depends_on'][0]} 승자)",
                            },
                            team_b={
                                "id": 0,
                                "name": f"TBD (match {m['depends_on'][1]} 승자)",
                            },
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

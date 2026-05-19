from __future__ import annotations

from .springboot_client import SpringbootClient


def generate_bracket(team_ids: list[int]) -> dict:
    """싱글 엘리미네이션 대진표. 팀 수는 2의 거듭제곱 (2, 4, 8)."""
    n = len(team_ids)
    if n < 2 or (n & (n - 1)) != 0:
        raise ValueError(f"team count must be a power of 2 (>=2): got {n}")

    rounds: list[list[dict]] = []
    match_idx = 0

    # 1라운드 — 시드 매칭 (1-N, 2-(N-1), ...)
    first_round = []
    round_size = n // 2
    for i in range(round_size):
        first_round.append(
            {
                "matchIdx": match_idx,
                "teamA": team_ids[i],
                "teamB": team_ids[n - 1 - i],
            }
        )
        match_idx += 1
    rounds.append(first_round)

    # 다음 라운드 — depends_on
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
    """LangGraph 노드에서 호출하는 Tool 묶음. SpringbootClient를 DI."""

    def __init__(self, client: SpringbootClient):
        self._client = client

    def search_stadium(
        self,
        region: str | None,
        date_from: str | None,
        date_to: str | None,
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

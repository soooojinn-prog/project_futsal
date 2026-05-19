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

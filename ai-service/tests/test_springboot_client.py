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
        result = client.search_stadium(
            region="강남", date_from="2026-05-23", date_to="2026-05-24"
        )

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

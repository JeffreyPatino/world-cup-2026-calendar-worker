from __future__ import annotations

import pytest

from src.fixtures import KV_FIXTURE_KEY
from src.main import Default


class FakeKV:
    def __init__(self) -> None:
        self.store: dict[str, str] = {}

    async def get(self, key: str) -> str | None:
        return self.store.get(key)

    async def put(self, key: str, value: str) -> None:
        self.store[key] = value


@pytest.mark.asyncio
async def test_scheduled_refresh_writes_only_after_success(monkeypatch) -> None:
    async def fake_fetch(token: str):
        assert token == "token"
        return {
            "matches": [
                {
                    "id": 123456,
                    "utcDate": "2026-06-11T19:00:00Z",
                    "status": "TIMED",
                    "stage": "GROUP_STAGE",
                    "group": "GROUP_A",
                    "matchday": 1,
                    "homeTeam": {"name": "Mexico", "tla": "MEX"},
                    "awayTeam": {"name": "South Africa", "tla": "RSA"},
                    "venue": "Mexico City Stadium",
                    "score": None,
                }
            ]
        }

    monkeypatch.setattr("src.main.fetch_world_cup_matches", fake_fetch)
    kv = FakeKV()

    await Default().scheduled(None, {"FOOTBALL_DATA_API_TOKEN": "token", "MATCH_DATA": kv}, None)

    assert KV_FIXTURE_KEY in kv.store
    assert "football-data:123456" in kv.store[KV_FIXTURE_KEY]


@pytest.mark.asyncio
async def test_failed_scheduled_refresh_preserves_existing_kv(monkeypatch) -> None:
    async def fake_fetch(token: str):
        raise RuntimeError("upstream failed")

    monkeypatch.setattr("src.main.fetch_world_cup_matches", fake_fetch)
    kv = FakeKV()
    kv.store[KV_FIXTURE_KEY] = "existing"

    with pytest.raises(RuntimeError):
        await Default().scheduled(None, {"FOOTBALL_DATA_API_TOKEN": "token", "MATCH_DATA": kv}, None)

    assert kv.store[KV_FIXTURE_KEY] == "existing"


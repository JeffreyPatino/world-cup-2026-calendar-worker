from __future__ import annotations

import json

import pytest

from src.fixtures import KV_FIXTURE_KEY, load_fixture_payload, write_fixture_payload
from src.models import FixturePayload


class FakeKV:
    def __init__(self, initial: dict[str, str] | None = None) -> None:
        self.store = initial or {}

    async def get(self, key: str) -> str | None:
        return self.store.get(key)

    async def put(self, key: str, value: str) -> None:
        self.store[key] = value


def _payload() -> FixturePayload:
    return FixturePayload.from_dict(
        {
            "last_updated": "2026-06-10T10:00:00Z",
            "source": "test",
            "matches": [
                {
                    "fixture_id": "fixture-1",
                    "stage": "GROUP_STAGE",
                    "group": None,
                    "matchday": 1,
                    "home_team": "A",
                    "away_team": "B",
                    "home_team_code": "AAA",
                    "away_team_code": "BBB",
                    "kickoff_utc": "2026-06-11T19:00:00Z",
                    "duration_minutes": 120,
                    "venue": {"name": "Venue", "city": None, "country": None},
                    "status": "SCHEDULED",
                    "score": None,
                    "source_url": "https://example.com/",
                }
            ],
        }
    )


@pytest.mark.asyncio
async def test_loads_valid_kv_payload_first() -> None:
    payload = _payload()
    env = {"MATCH_DATA": FakeKV({KV_FIXTURE_KEY: json.dumps(payload.to_dict())})}

    loaded = await load_fixture_payload(env)

    assert loaded.source == "test"
    assert loaded.matches[0].fixture_id == "fixture-1"


@pytest.mark.asyncio
async def test_invalid_kv_payload_falls_back_to_bundled_data() -> None:
    env = {"MATCH_DATA": FakeKV({KV_FIXTURE_KEY: "{bad-json"})}

    loaded = await load_fixture_payload(env)

    assert loaded.source == "bundled-fallback"
    assert loaded.matches


@pytest.mark.asyncio
async def test_write_fixture_payload_uses_current_key() -> None:
    kv = FakeKV()
    payload = _payload()

    await write_fixture_payload({"MATCH_DATA": kv}, payload)

    assert KV_FIXTURE_KEY in kv.store
    assert json.loads(kv.store[KV_FIXTURE_KEY])["source"] == "test"


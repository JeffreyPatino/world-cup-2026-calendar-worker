from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.fallback_data import FALLBACK_FIXTURE_DATA
from src.models import FixturePayload, FixtureValidationError


KV_FIXTURE_KEY = "worldcup:fixtures:current"
FALLBACK_DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "matches.json"
LOCAL_DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "matches.local.json"


async def load_fixture_payload(env: Any | None = None) -> FixturePayload:
    if env is not None:
        kv_payload = await _load_from_kv(env)
        if kv_payload is not None:
            return kv_payload
    return load_fallback_payload()


def load_fallback_payload() -> FixturePayload:
    if LOCAL_DATA_PATH.exists():
        with LOCAL_DATA_PATH.open("r", encoding="utf-8") as file:
            data = json.load(file)
    elif FALLBACK_DATA_PATH.exists():
        with FALLBACK_DATA_PATH.open("r", encoding="utf-8") as file:
            data = json.load(file)
    else:
        data = FALLBACK_FIXTURE_DATA
    return FixturePayload.from_dict(data)


def write_local_fixture_payload(payload: FixturePayload) -> None:
    LOCAL_DATA_PATH.write_text(
        json.dumps(payload.to_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


async def write_fixture_payload(env: Any, payload: FixturePayload) -> None:
    kv = _get_match_data_binding(env)
    if kv is None:
        raise RuntimeError("MATCH_DATA KV binding is not configured")
    await kv.put(KV_FIXTURE_KEY, json.dumps(payload.to_dict(), separators=(",", ":")))


async def _load_from_kv(env: Any) -> FixturePayload | None:
    kv = _get_match_data_binding(env)
    if kv is None:
        return None
    raw = await kv.get(KV_FIXTURE_KEY)
    if raw is None:
        return None
    try:
        data = json.loads(raw)
        return FixturePayload.from_dict(data)
    except (json.JSONDecodeError, FixtureValidationError, TypeError):
        return None


def _get_match_data_binding(env: Any) -> Any | None:
    if isinstance(env, dict):
        return env.get("MATCH_DATA")
    return getattr(env, "MATCH_DATA", None)

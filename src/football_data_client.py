from __future__ import annotations

from typing import Any
from urllib.parse import urlencode


FOOTBALL_DATA_BASE_URL = "https://api.football-data.org/v4"
WORLD_CUP_MATCHES_PATH = "/competitions/WC/matches"


class FootballDataClientError(RuntimeError):
    """Raised when football-data.org data cannot be fetched."""


async def fetch_world_cup_matches(token: str, season: int = 2026) -> dict[str, Any]:
    if not token:
        raise FootballDataClientError("FOOTBALL_DATA_API_TOKEN is not configured")

    try:
        from workers import fetch
    except ImportError as exc:
        raise FootballDataClientError("workers.fetch is only available in the Worker runtime") from exc

    query = urlencode({"season": str(season)})
    response = await fetch(
        f"{FOOTBALL_DATA_BASE_URL}{WORLD_CUP_MATCHES_PATH}?{query}",
        headers={
            "X-Auth-Token": token,
            "Accept": "application/json",
        },
    )
    if response.status < 200 or response.status >= 300:
        raise FootballDataClientError(f"football-data.org returned HTTP {response.status}")
    return await response.json()


def get_api_token(env: Any) -> str | None:
    if isinstance(env, dict):
        return env.get("FOOTBALL_DATA_API_TOKEN")
    return getattr(env, "FOOTBALL_DATA_API_TOKEN", None)

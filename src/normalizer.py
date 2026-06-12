from __future__ import annotations

from typing import Any

try:
    from src.models import FixturePayload, utc_now_iso
except ModuleNotFoundError:
    from models import FixturePayload, utc_now_iso


SOURCE_URL = "https://www.football-data.org/"


def normalize_football_data_response(data: dict[str, Any], *, last_updated: str | None = None) -> FixturePayload:
    raw_matches = data.get("matches")
    if not isinstance(raw_matches, list) or not raw_matches:
        raise ValueError("football-data.org response must include a non-empty matches list")

    normalized = {
        "last_updated": last_updated or utc_now_iso(),
        "source": "football-data.org",
        "matches": [_normalize_match(match) for match in raw_matches],
    }
    return FixturePayload.from_dict(normalized)


def _normalize_match(match: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(match, dict):
        raise ValueError("match must be an object")

    match_id = match.get("id")
    if match_id is None:
        raise ValueError("match id is required")

    home_team = _team_name(match.get("homeTeam"))
    away_team = _team_name(match.get("awayTeam"))

    return {
        "fixture_id": f"football-data:{match_id}",
        "stage": _optional_str(match.get("stage")) or "UNKNOWN",
        "group": _optional_str(match.get("group")),
        "matchday": match.get("matchday"),
        "home_team": home_team,
        "away_team": away_team,
        "home_team_code": _team_code(match.get("homeTeam")),
        "away_team_code": _team_code(match.get("awayTeam")),
        "kickoff_utc": _required_str(match, "utcDate"),
        "duration_minutes": _duration_minutes(match),
        "venue": {
            "name": _optional_str(match.get("venue")),
            "city": None,
            "country": None,
        },
        "status": _optional_str(match.get("status")) or "SCHEDULED",
        "score": _normalize_score(match.get("score")),
        "source_url": SOURCE_URL,
    }


def _team_name(team: Any) -> str | None:
    if not isinstance(team, dict):
        return None
    return _optional_str(team.get("name")) or _optional_str(team.get("shortName")) or _optional_str(team.get("tla"))


def _team_code(team: Any) -> str | None:
    if not isinstance(team, dict):
        return None
    return _optional_str(team.get("tla"))


def _duration_minutes(match: dict[str, Any]) -> int:
    stage = str(match.get("stage") or "").upper()
    if stage in {"LAST_32", "LAST_16", "QUARTER_FINALS", "SEMI_FINALS", "THIRD_PLACE", "FINAL"}:
        return 150
    return 120


def _normalize_score(score: Any) -> dict[str, Any] | None:
    if not isinstance(score, dict):
        return None
    full_time = score.get("fullTime")
    if isinstance(full_time, dict):
        return {
            "winner": score.get("winner"),
            "full_time": {
                "home": full_time.get("home"),
                "away": full_time.get("away"),
            },
        }
    return {"winner": score.get("winner")}


def _required_str(data: dict[str, Any], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"{key} is required")
    return value


def _optional_str(value: Any) -> str | None:
    if isinstance(value, str) and value:
        return value
    return None

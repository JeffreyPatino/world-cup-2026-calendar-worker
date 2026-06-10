from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any


DEFAULT_DURATION_MINUTES = 120


class FixtureValidationError(ValueError):
    """Raised when fixture payload data is not usable."""


@dataclass(frozen=True)
class Venue:
    name: str | None = None
    city: str | None = None
    country: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "Venue":
        if data is None:
            return cls()
        if not isinstance(data, dict):
            raise FixtureValidationError("venue must be an object or null")
        return cls(
            name=_optional_str(data.get("name")),
            city=_optional_str(data.get("city")),
            country=_optional_str(data.get("country")),
        )

    def display(self) -> str:
        parts = [part for part in (self.name, self.city, self.country) if part]
        return ", ".join(parts)

    def to_dict(self) -> dict[str, str | None]:
        return {"name": self.name, "city": self.city, "country": self.country}


@dataclass(frozen=True)
class Fixture:
    fixture_id: str
    stage: str
    group: str | None
    matchday: int | None
    home_team: str | None
    away_team: str | None
    home_team_code: str | None
    away_team_code: str | None
    kickoff_utc: str
    duration_minutes: int
    venue: Venue
    status: str
    score: dict[str, Any] | None
    source_url: str | None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Fixture":
        if not isinstance(data, dict):
            raise FixtureValidationError("fixture must be an object")

        fixture_id = _required_str(data, "fixture_id")
        stage = _required_str(data, "stage")
        kickoff_utc = _required_str(data, "kickoff_utc")
        parse_utc_datetime(kickoff_utc)

        duration_minutes = data.get("duration_minutes", DEFAULT_DURATION_MINUTES)
        if duration_minutes is None:
            duration_minutes = DEFAULT_DURATION_MINUTES
        if not isinstance(duration_minutes, int) or duration_minutes <= 0:
            raise FixtureValidationError("duration_minutes must be a positive integer")

        matchday = data.get("matchday")
        if matchday is not None and (not isinstance(matchday, int) or matchday <= 0):
            raise FixtureValidationError("matchday must be a positive integer or null")

        score = data.get("score")
        if score is not None and not isinstance(score, dict):
            raise FixtureValidationError("score must be an object or null")

        return cls(
            fixture_id=fixture_id,
            stage=stage,
            group=_optional_str(data.get("group")),
            matchday=matchday,
            home_team=_optional_str(data.get("home_team")),
            away_team=_optional_str(data.get("away_team")),
            home_team_code=_optional_str(data.get("home_team_code")),
            away_team_code=_optional_str(data.get("away_team_code")),
            kickoff_utc=kickoff_utc,
            duration_minutes=duration_minutes,
            venue=Venue.from_dict(data.get("venue")),
            status=_required_str(data, "status"),
            score=score,
            source_url=_optional_str(data.get("source_url")),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "fixture_id": self.fixture_id,
            "stage": self.stage,
            "group": self.group,
            "matchday": self.matchday,
            "home_team": self.home_team,
            "away_team": self.away_team,
            "home_team_code": self.home_team_code,
            "away_team_code": self.away_team_code,
            "kickoff_utc": self.kickoff_utc,
            "duration_minutes": self.duration_minutes,
            "venue": self.venue.to_dict(),
            "status": self.status,
            "score": self.score,
            "source_url": self.source_url,
        }


@dataclass(frozen=True)
class FixturePayload:
    last_updated: str
    source: str
    matches: list[Fixture]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "FixturePayload":
        if not isinstance(data, dict):
            raise FixtureValidationError("fixture payload must be an object")
        last_updated = _required_str(data, "last_updated")
        parse_utc_datetime(last_updated)
        source = _required_str(data, "source")
        raw_matches = data.get("matches")
        if not isinstance(raw_matches, list) or not raw_matches:
            raise FixtureValidationError("matches must be a non-empty list")

        matches = [Fixture.from_dict(raw_match) for raw_match in raw_matches]
        fixture_ids = [match.fixture_id for match in matches]
        if len(fixture_ids) != len(set(fixture_ids)):
            raise FixtureValidationError("fixture_id values must be unique")

        return cls(last_updated=last_updated, source=source, matches=matches)

    def to_dict(self) -> dict[str, Any]:
        return {
            "last_updated": self.last_updated,
            "source": self.source,
            "matches": [match.to_dict() for match in self.matches],
        }


def parse_utc_datetime(value: str) -> datetime:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise FixtureValidationError("datetime values must be UTC ISO strings ending in Z")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise FixtureValidationError(f"invalid UTC datetime: {value}") from exc
    if parsed.tzinfo is None:
        raise FixtureValidationError("datetime must include timezone information")
    return parsed.astimezone(UTC)


def utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _required_str(data: dict[str, Any], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value:
        raise FixtureValidationError(f"{key} must be a non-empty string")
    return value


def _optional_str(value: Any) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise FixtureValidationError("optional string field must be a string or null")
    return value or None


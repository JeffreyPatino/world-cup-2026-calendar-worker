from __future__ import annotations

from datetime import UTC, timedelta
from hashlib import sha256

from icalendar import Calendar, Event

try:
    from src.models import Fixture, FixturePayload, parse_utc_datetime
except ModuleNotFoundError:
    from models import Fixture, FixturePayload, parse_utc_datetime


CALENDAR_NAME = "FIFA World Cup 2026"
CALENDAR_DESCRIPTION = "Match schedule for the FIFA World Cup 2026"
PRODID = "-//world-cup-2026-calendar-worker//FIFA World Cup 2026//EN"
UID_DOMAIN = "world-cup-2026-calendar"


def build_calendar(payload: FixturePayload) -> str:
    calendar = Calendar()
    calendar.add("prodid", PRODID)
    calendar.add("version", "2.0")
    calendar.add("calscale", "GREGORIAN")
    calendar.add("method", "PUBLISH")
    calendar.add("x-wr-calname", CALENDAR_NAME)
    calendar.add("x-wr-caldesc", CALENDAR_DESCRIPTION)

    for fixture in sorted(payload.matches, key=lambda match: (match.kickoff_utc, match.fixture_id)):
        calendar.add_component(_build_event(fixture))

    return calendar.to_ical().decode("utf-8")


def stable_uid(fixture_id: str) -> str:
    digest = sha256(f"fifa-world-cup-2026:{fixture_id}".encode("utf-8")).hexdigest()[:32]
    return f"{digest}@{UID_DOMAIN}"


def _build_event(fixture: Fixture) -> Event:
    starts_at = parse_utc_datetime(fixture.kickoff_utc)
    ends_at = starts_at + timedelta(minutes=fixture.duration_minutes)

    event = Event()
    event.add("uid", stable_uid(fixture.fixture_id))
    event.add("dtstamp", starts_at.astimezone(UTC))
    event.add("dtstart", starts_at)
    event.add("dtend", ends_at)
    event.add("summary", _summary(fixture))

    location = fixture.venue.display()
    if location:
        event.add("location", location)

    description = _description(fixture)
    if description:
        event.add("description", description)

    event.add("status", _ical_status(fixture.status))
    return event


def _summary(fixture: Fixture) -> str:
    home = fixture.home_team or "TBD"
    away = fixture.away_team or "TBD"
    return f"{home} vs {away}"


def _description(fixture: Fixture) -> str:
    parts = [f"Stage: {fixture.stage}", f"Status: {fixture.status}"]
    if fixture.group:
        parts.append(f"Group: {fixture.group}")
    if fixture.matchday:
        parts.append(f"Matchday: {fixture.matchday}")
    score = _score_line(fixture)
    if score:
        parts.append(score)
    if fixture.source_url:
        parts.append(f"Source: {fixture.source_url}")
    return "\n".join(parts)


def _score_line(fixture: Fixture) -> str | None:
    if not fixture.score:
        return None
    full_time = fixture.score.get("full_time") or fixture.score.get("fullTime")
    if isinstance(full_time, dict):
        home = full_time.get("home")
        away = full_time.get("away")
        if home is not None and away is not None:
            return f"Score: {home}-{away}"
    return None


def _ical_status(status: str) -> str:
    normalized = status.upper()
    if normalized in {"CANCELLED", "CANCELED"}:
        return "CANCELLED"
    if normalized in {"POSTPONED", "SUSPENDED"}:
        return "TENTATIVE"
    return "CONFIRMED"

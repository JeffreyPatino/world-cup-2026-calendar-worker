from __future__ import annotations

from collections import defaultdict
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

    group_teams = _build_group_teams_map(payload)

    for fixture in sorted(payload.matches, key=lambda match: (match.kickoff_utc, match.fixture_id)):
        calendar.add_component(_build_event(fixture, group_teams))

    return calendar.to_ical().decode("utf-8")


def _build_group_teams_map(payload: FixturePayload) -> dict[str, list[str]]:
    """Return a mapping of group name -> sorted list of unique team names."""
    teams_by_group: dict[str, set[str]] = defaultdict(set)
    for fixture in payload.matches:
        if not fixture.group:
            continue
        if fixture.home_team:
            teams_by_group[fixture.group].add(fixture.home_team)
        if fixture.away_team:
            teams_by_group[fixture.group].add(fixture.away_team)
    return {group: sorted(teams) for group, teams in teams_by_group.items()}


def stable_uid(fixture_id: str) -> str:
    digest = sha256(f"fifa-world-cup-2026:{fixture_id}".encode("utf-8")).hexdigest()[:32]
    return f"{digest}@{UID_DOMAIN}"


def _build_event(fixture: Fixture, group_teams: dict[str, list[str]]) -> Event:
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

    description = _description(fixture, group_teams)
    if description:
        event.add("description", description)

    event.add("status", _ical_status(fixture.status))
    return event


def _summary(fixture: Fixture) -> str:
    home = fixture.home_team or "TBD"
    away = fixture.away_team or "TBD"
    return f"{home} vs {away}"


def _description(fixture: Fixture, group_teams: dict[str, list[str]]) -> str:
    parts = [f"Stage: {fixture.stage}", f"Status: {fixture.status}"]
    if fixture.group:
        teams = group_teams.get(fixture.group)
        group_line = f"Group: {fixture.group}"
        if teams:
            group_line += f" ({', '.join(teams)})"
        parts.append(group_line)
    if fixture.matchday:
        parts.append(f"Matchday: {fixture.matchday}")
    venue = fixture.venue.display()
    if venue:
        parts.append(f"Venue: {venue}")
    score = _score_line(fixture)
    if score:
        parts.append(score)
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

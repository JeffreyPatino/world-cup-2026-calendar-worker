from __future__ import annotations

from icalendar import Calendar

from src.calendar_builder import build_calendar, stable_uid
from src.models import FixturePayload


def _payload(home_team: str = "Mexico") -> FixturePayload:
    return FixturePayload.from_dict(
        {
            "last_updated": "2026-06-10T10:00:00Z",
            "source": "test",
            "matches": [
                {
                    "fixture_id": "fwc2026-001",
                    "stage": "GROUP_STAGE",
                    "group": "GROUP_A",
                    "matchday": 1,
                    "home_team": home_team,
                    "away_team": "South Africa",
                    "home_team_code": "MEX",
                    "away_team_code": "RSA",
                    "kickoff_utc": "2026-06-11T19:00:00Z",
                    "duration_minutes": 120,
                    "venue": {"name": "Mexico City Stadium", "city": "Mexico City", "country": "Mexico"},
                    "status": "SCHEDULED",
                    "score": None,
                    "source_url": "https://www.fifa.com/",
                }
            ],
        }
    )


def test_calendar_has_global_properties_and_event() -> None:
    calendar = Calendar.from_ical(build_calendar(_payload()))

    assert str(calendar["X-WR-CALNAME"]) == "FIFA World Cup 2026"
    assert str(calendar["X-WR-CALDESC"]) == "Match schedule for the FIFA World Cup 2026"

    events = [component for component in calendar.walk() if component.name == "VEVENT"]
    assert len(events) == 1
    assert str(events[0]["SUMMARY"]) == "Mexico vs South Africa"
    assert str(events[0]["UID"]) == stable_uid("fwc2026-001")
    assert events[0].decoded("DTSTART").isoformat() == "2026-06-11T19:00:00+00:00"
    assert events[0].decoded("DTEND").isoformat() == "2026-06-11T21:00:00+00:00"


def test_uid_stays_stable_when_match_label_changes() -> None:
    first = Calendar.from_ical(build_calendar(_payload("Winner Group A")))
    second = Calendar.from_ical(build_calendar(_payload("Mexico")))

    first_event = [component for component in first.walk() if component.name == "VEVENT"][0]
    second_event = [component for component in second.walk() if component.name == "VEVENT"][0]

    assert str(first_event["UID"]) == str(second_event["UID"])
    assert str(first_event["SUMMARY"]) == "Winner Group A vs South Africa"
    assert str(second_event["SUMMARY"]) == "Mexico vs South Africa"


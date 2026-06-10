from __future__ import annotations

import pytest

from src.normalizer import normalize_football_data_response


def test_normalizes_football_data_match() -> None:
    payload = normalize_football_data_response(
        {
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
                    "score": {"winner": None, "fullTime": {"home": None, "away": None}},
                }
            ]
        },
        last_updated="2026-06-10T10:00:00Z",
    )

    fixture = payload.matches[0]
    assert payload.source == "football-data.org"
    assert fixture.fixture_id == "football-data:123456"
    assert fixture.home_team == "Mexico"
    assert fixture.away_team_code == "RSA"
    assert fixture.venue.name == "Mexico City Stadium"


def test_knockout_match_gets_longer_duration() -> None:
    payload = normalize_football_data_response(
        {
            "matches": [
                {
                    "id": 999,
                    "utcDate": "2026-07-19T19:00:00Z",
                    "status": "TIMED",
                    "stage": "FINAL",
                    "matchday": None,
                    "homeTeam": {"name": "Winner Semi-final 1", "tla": None},
                    "awayTeam": {"name": "Winner Semi-final 2", "tla": None},
                    "venue": "New York New Jersey Stadium",
                    "score": None,
                }
            ]
        },
        last_updated="2026-06-10T10:00:00Z",
    )

    assert payload.matches[0].duration_minutes == 150


def test_rejects_empty_match_list() -> None:
    with pytest.raises(ValueError):
        normalize_football_data_response({"matches": []})


# FIFA World Cup 2026 Calendar Worker

A Cloudflare Worker that serves an auto-updating iCalendar feed for the FIFA World Cup 2026.

The project is intentionally small: FastAPI handles the HTTP route, Cloudflare KV stores the latest normalized fixture data, a scheduled Worker refreshes that data daily from football-data.org, and the `/world-cup.ics` endpoint renders a standards-friendly calendar feed.

## Features

- Serves `GET /world-cup.ics` as `text/calendar`
- Uses stable event UIDs so subscribed calendars update matches instead of duplicating them
- Stores refreshed match data in Cloudflare KV
- Falls back to `data/matches.json` when KV is empty or unavailable
- Refreshes fixture data daily with a Cloudflare Cron Trigger
- Keeps all match times in UTC so calendar apps localize correctly

## Architecture

```text
football-data.org API
        |
        | daily cron
        v
Cloudflare Worker scheduled handler
        |
        | normalize + validate
        v
Cloudflare KV: worldcup:fixtures:current
        |
        | calendar request
        v
GET /world-cup.ics -> FastAPI -> iCalendar response
```

The most important design choice is the event UID. Each match uses an immutable `fixture_id`, and the iCalendar UID is a hash of that ID. During knockout rounds, the event title can change from a placeholder like `Winner Group A vs Runner-up Group B` to real teams while keeping the same UID, which lets Apple Calendar and other clients update the existing event.

## Project Layout

```text
.
├── data/
│   └── matches.json              # bundled fallback fixture data
├── src/
│   ├── main.py                   # Worker entrypoint and FastAPI routes
│   ├── calendar_builder.py       # iCalendar generation
│   ├── fixtures.py               # KV-first fixture loading
│   ├── football_data_client.py   # football-data.org API client
│   ├── models.py                 # validation and data models
│   └── normalizer.py             # API response -> internal schema
├── tests/
├── pyproject.toml
├── requirements-dev.txt
└── wrangler.jsonc
```

## Prerequisites

- Python 3.12 or newer
- Node.js and npm
- A Cloudflare account
- A free football-data.org API token
- `uv`, required by Cloudflare's Python Worker tooling through `pywrangler`

On macOS:

```bash
brew install python@3.12 node uv
```

## Local Setup

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
```

Run the test suite:

```bash
pytest
```

## Cloudflare Setup

Log in to Cloudflare:

```bash
npx wrangler login
```

Store the football-data.org token as a Worker secret:

```bash
pywrangler secret put FOOTBALL_DATA_API_TOKEN
```

Start the local Worker dev server:

```bash
pywrangler dev
```

Then test the calendar endpoint:

```bash
curl http://localhost:8787/world-cup.ics
```

Trigger the scheduled refresh locally:

```bash
curl "http://localhost:8787/cdn-cgi/handler/scheduled?format=json"
```

Deploy:

```bash
pywrangler deploy
```

## Data Model

The internal schema is deliberately simple:

```json
{
  "last_updated": "2026-06-10T10:00:00Z",
  "source": "football-data.org",
  "matches": [
    {
      "fixture_id": "football-data:123456",
      "stage": "GROUP_STAGE",
      "group": "GROUP_A",
      "matchday": 1,
      "home_team": "Mexico",
      "away_team": "South Africa",
      "home_team_code": "MEX",
      "away_team_code": "RSA",
      "kickoff_utc": "2026-06-11T19:00:00Z",
      "duration_minutes": 120,
      "venue": {
        "name": "Mexico City Stadium",
        "city": null,
        "country": null
      },
      "status": "SCHEDULED",
      "score": null,
      "source_url": "https://www.football-data.org/"
    }
  ]
}
```

Keep `fixture_id` stable once a match is published. That is what makes calendar updates reliable.

## Notes

Apple Calendar and other clients decide how often to refresh subscribed calendars. The Worker always serves the latest data it has, but client refresh timing is not controlled by this app.


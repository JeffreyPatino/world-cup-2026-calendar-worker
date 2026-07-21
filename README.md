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

## Production Endpoint & Subscribing

Once deployed to Cloudflare, your worker will be available at a URL similar to:
`https://world-cup-2026-calendar-worker.<your-username>.workers.dev`

The calendar feed is served at the `/world-cup.ics` path. 

**Calendar Feed URL:**
`https://world-cup-2026-calendar-worker.<your-username>.workers.dev/world-cup.ics`

### How to Subscribe

**Apple Calendar (iOS / macOS)**
1. Open the Calendar app.
2. Go to **File > New Calendar Subscription...** (or Settings > Calendar > Accounts > Add Account > Other > Add Subscribed Calendar on iOS).
3. Paste the **Calendar Feed URL** and click Subscribe.
4. Set Auto-refresh to **Every Day** so you receive knockout stage updates!

**Google Calendar**
1. Open Google Calendar on the web.
2. On the left sidebar, click the **+** next to "Other calendars" and select **From URL**.
3. Paste the **Calendar Feed URL** and click Add Calendar.
*(Note: Google Calendar refreshes automatically, but it can sometimes take up to 24 hours to sync updates).*

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
- A Cloudflare account
- A free football-data.org API token

On macOS:

```bash
brew install python@3.12
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

## Cloudflare Setup (GitHub Integration)

Instead of manually deploying with command-line tools, this repository is designed to be connected directly to Cloudflare via the dashboard.

1. **Push to GitHub**: Make sure this repository is pushed to your GitHub account.
2. **Connect in Cloudflare**: Go to **Workers & Pages** in the Cloudflare Dashboard and click **Create application**.
3. Select the **Workers** tab and choose **Connect to GitHub** (or set it up via the Workers CI/CD options).
4. Follow the prompts to authorize Cloudflare and select this repository. Cloudflare will automatically handle building and deploying your Worker whenever you push to the `main` branch.
5. **Configure Secrets & KV**: Once connected, go to your new Worker's **Settings > Variables** in the Cloudflare Dashboard to add your `FOOTBALL_DATA_API_TOKEN` secret and create/bind the `MATCH_DATA` KV Namespace.

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

## Post-Tournament Archival
Since the 2026 tournament has concluded, this microservice has been transitioned to a dormant state to minimize compute overhead and optimize resource usage:
- The cron triggers have been removed from `wrangler.jsonc`.
- The `Cache-Control` header in `src/main.py` has been bumped to 30 days (`max-age=2592000`).

**When bringing this back online for 2030:**
1. Restore the daily cron triggers in `wrangler.jsonc`.
2. Revert the `Cache-Control` header in `src/main.py` back to `max-age=900` (15 mins) so calendar apps fetch live score updates.
3. Update the hardcoded `season=2026` parameter in `src/football_data_client.py` and UIDs.

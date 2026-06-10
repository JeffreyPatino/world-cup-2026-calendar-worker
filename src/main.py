from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse, Response

from src.calendar_builder import build_calendar
from src.fixtures import load_fixture_payload, write_fixture_payload
from src.football_data_client import fetch_world_cup_matches, get_api_token
from src.normalizer import normalize_football_data_response


try:
    import asgi
except ImportError:
    asgi = None

try:
    from workers import WorkerEntrypoint
except ImportError:
    class WorkerEntrypoint:  # type: ignore[no-redef]
        def __init__(self) -> None:
            self.env = None


app = FastAPI(title="FIFA World Cup 2026 Calendar")


class Default(WorkerEntrypoint):
    async def fetch(self, request):
        if asgi is None:
            raise RuntimeError("Cloudflare ASGI adapter is not available")
        return await asgi.fetch(app, request, self.env)

    async def scheduled(self, controller, env, ctx):
        token = get_api_token(env)
        raw_data = await fetch_world_cup_matches(token or "")
        payload = normalize_football_data_response(raw_data)
        await write_fixture_payload(env, payload)


@app.get("/", response_class=PlainTextResponse)
async def root() -> str:
    return "FIFA World Cup 2026 calendar feed: /world-cup.ics"


@app.get("/world-cup.ics")
async def world_cup_calendar(request: Request) -> Response:
    env = request.scope.get("env")
    payload = await load_fixture_payload(env)
    calendar_text = build_calendar(payload)
    return Response(
        content=calendar_text,
        media_type="text/calendar",
        headers={
            "Cache-Control": "public, max-age=900",
        },
    )

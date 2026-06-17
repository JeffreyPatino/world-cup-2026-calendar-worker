from __future__ import annotations

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse, PlainTextResponse, Response

try:
    from src.calendar_builder import build_calendar
    from src.fixtures import load_fixture_payload, write_fixture_payload
    from src.football_data_client import fetch_world_cup_matches, get_api_token
    from src.normalizer import normalize_football_data_response
except ModuleNotFoundError:
    from calendar_builder import build_calendar
    from fixtures import load_fixture_payload, write_fixture_payload
    from football_data_client import fetch_world_cup_matches, get_api_token
    from normalizer import normalize_football_data_response


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

    async def scheduled(self, controller, env=None, ctx=None):
        worker_env = env if env is not None else self.env
        await refresh_fixture_data(worker_env)


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


@app.post("/admin/refresh")
async def refresh_fixtures(
    request: Request,
    x_refresh_token: str | None = Header(default=None),
) -> JSONResponse:
    env = request.scope.get("env")
    expected_token = _get_env_value(env, "REFRESH_TOKEN")
    if not expected_token:
        raise HTTPException(status_code=503, detail="REFRESH_TOKEN is not configured")
    if x_refresh_token != expected_token:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    payload = await refresh_fixture_data(env)
    return JSONResponse(
        {
            "ok": True,
            "source": payload.source,
            "last_updated": payload.last_updated,
            "match_count": len(payload.matches),
        }
    )


async def refresh_fixture_data(env):
    token = get_api_token(env)
    raw_data = await fetch_world_cup_matches(token or "")
    payload = normalize_football_data_response(raw_data)
    await write_fixture_payload(env, payload)
    return payload


def _get_env_value(env, key: str) -> str | None:
    if isinstance(env, dict):
        return env.get(key)
    return getattr(env, key, None)

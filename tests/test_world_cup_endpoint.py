from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from src.main import app


@pytest.mark.asyncio
async def test_world_cup_ics_endpoint_returns_calendar() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/world-cup.ics")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/calendar")
    assert "BEGIN:VCALENDAR" in response.text
    assert "X-WR-CALNAME:FIFA World Cup 2026" in response.text
    assert "BEGIN:VEVENT" in response.text


@pytest.mark.asyncio
async def test_admin_refresh_requires_configured_token() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post("/admin/refresh")

    assert response.status_code == 503

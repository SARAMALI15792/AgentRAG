"""Integration tests for server/app.py — HTTP transport via httpx."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from agentrag.server.app import create_app


@pytest.fixture
async def client() -> AsyncClient:
    """Create async HTTP client for FastAPI app."""
    app, _ = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.mark.anyio
async def test_health_endpoint(client: AsyncClient) -> None:
    """Health endpoint returns ok status."""
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.anyio
async def test_mcp_sse_endpoint_mounted(client: AsyncClient) -> None:
    """MCP SSE endpoint is mounted at /sse."""
    # SSE endpoint should respond (even if we don't complete handshake)
    response = await client.get("/sse")
    # FastMCP SSE app will return some response (not 404)
    assert response.status_code != 404

"""Thin async client for a local Ollama server."""

import json
from collections.abc import AsyncIterator

import httpx

from app.core.config import settings


def make_client(transport: httpx.AsyncBaseTransport | None = None) -> httpx.AsyncClient:
    return httpx.AsyncClient(
        base_url=settings.ollama_base_url,
        timeout=httpx.Timeout(5.0, read=120.0),
        transport=transport,
    )


async def is_available(client: httpx.AsyncClient | None = None) -> bool:
    own = client is None
    client = client or make_client()
    try:
        return (await client.get("/api/version")).status_code == 200
    except httpx.HTTPError:
        return False
    finally:
        if own:
            await client.aclose()


async def list_models(client: httpx.AsyncClient | None = None) -> list[str]:
    own = client is None
    client = client or make_client()
    try:
        res = await client.get("/api/tags")
        res.raise_for_status()
        return [m["name"] for m in res.json().get("models", [])]
    except httpx.HTTPError:
        return []
    finally:
        if own:
            await client.aclose()


async def chat_stream(
    messages: list[dict],
    model: str | None = None,
    client: httpx.AsyncClient | None = None,
) -> AsyncIterator[str]:
    """Yield assistant text deltas from Ollama's NDJSON chat stream."""
    own = client is None
    client = client or make_client()
    try:
        async with client.stream(
            "POST",
            "/api/chat",
            json={"model": model or settings.ollama_model, "messages": messages, "stream": True},
        ) as res:
            res.raise_for_status()
            async for line in res.aiter_lines():
                if not line.strip():
                    continue
                chunk = json.loads(line)
                delta = chunk.get("message", {}).get("content", "")
                if delta:
                    yield delta
                if chunk.get("done"):
                    break
    finally:
        if own:
            await client.aclose()

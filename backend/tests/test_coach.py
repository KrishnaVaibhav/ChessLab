import json

import httpx
import pytest

from app.services import ollama
from app.services.coach import (
    MoveContext,
    build_messages,
    default_question,
    describe_context,
    uci_to_san,
)

START_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"


def _ctx(**overrides) -> MoveContext:
    base = dict(
        ply=6,
        san="Nf6",
        fen_before="r1bqkbnr/pppp1ppp/2n5/4p2Q/2B1P3/8/PPPP1PPP/RNB1K1NR b KQkq - 3 3",
        fen_after="r1bqkb1r/pppp1ppp/2n2n2/4p2Q/2B1P3/8/PPPP1PPP/RNB1K1NR w KQkq - 4 4",
        judgment="blunder",
        score_label="M1",
        win_pct=100.0,
        better_san="g6",
        best_reply_san="Qxf7#",
    )
    base.update(overrides)
    return MoveContext(**base)


def test_uci_to_san():
    assert uci_to_san(START_FEN, "g1f3") == "Nf3"
    assert uci_to_san(START_FEN, None) is None
    assert uci_to_san(START_FEN, "e2e5") is None  # illegal


def test_describe_context_mentions_move_eval_and_alternative():
    text = describe_context({"White": "Alice", "Black": "Bob"}, _ctx())
    assert "3... Nf6" in text
    assert "M1" in text
    assert "blunder" in text
    assert "g6" in text
    assert "Qxf7#" in text


def test_default_question_targets_mistakes():
    assert "blunder" in default_question(_ctx())
    assert "position" in default_question(_ctx(judgment="ok"))


def test_build_messages_history_replaces_default_question():
    ctx = _ctx()
    auto = build_messages({}, ctx)
    assert auto[0]["role"] == "system"
    assert auto[-1]["role"] == "user"
    followup = build_messages(
        {}, ctx, [{"role": "user", "content": "Was there a defense?"}]
    )
    assert followup[-1]["content"] == "Was there a defense?"
    assert len(followup) == 3


def _mock_client(handler) -> httpx.AsyncClient:
    return ollama.make_client(transport=httpx.MockTransport(handler))


@pytest.mark.asyncio
async def test_chat_stream_yields_deltas():
    ndjson = "\n".join(
        json.dumps(c)
        for c in [
            {"message": {"role": "assistant", "content": "Nf6 hangs "}, "done": False},
            {"message": {"role": "assistant", "content": "f7."}, "done": True},
        ]
    )

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/chat"
        body = json.loads(request.content)
        assert body["messages"][0]["role"] == "system"
        return httpx.Response(200, text=ndjson)

    client = _mock_client(handler)
    chunks = [
        d
        async for d in ollama.chat_stream(
            [{"role": "system", "content": "x"}], client=client
        )
    ]
    await client.aclose()
    assert chunks == ["Nf6 hangs ", "f7."]


@pytest.mark.asyncio
async def test_availability_and_models():
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/version":
            return httpx.Response(200, json={"version": "0.9.0"})
        return httpx.Response(200, json={"models": [{"name": "qwen3:8b"}]})

    client = _mock_client(handler)
    assert await ollama.is_available(client) is True
    assert await ollama.list_models(client) == ["qwen3:8b"]
    await client.aclose()


@pytest.mark.asyncio
async def test_unreachable_server_degrades_gracefully():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("refused")

    client = _mock_client(handler)
    assert await ollama.is_available(client) is False
    assert await ollama.list_models(client) == []
    await client.aclose()

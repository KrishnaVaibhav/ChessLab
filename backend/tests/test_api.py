"""API route tests over ASGI transport. No engine binary required —
engine-dependent paths are forced to their error branches by pointing
the configured Stockfish path at a nonexistent file.
"""

import chess

from app.core.config import settings

SAMPLE = """[Event "Test"]
[White "Alice"]
[Black "Bob"]
[Result "1-0"]

1. e4 e5 2. Nf3 Nc6 3. Bb5 1-0
"""


async def test_health(client):
    r = await client.get("/api/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert isinstance(body["stockfish"], bool)
    assert body["engine_depth"] == settings.engine_depth


async def test_parse_valid_pgn(client):
    r = await client.post("/api/games/parse", json={"pgn": SAMPLE})
    assert r.status_code == 200
    games = r.json()["games"]
    assert len(games) == 1
    assert games[0]["headers"]["White"] == "Alice"
    assert len(games[0]["moves"]) == 5
    assert games[0]["moves"][0]["uci"] == "e2e4"


async def test_parse_empty_pgn_422(client):
    r = await client.post("/api/games/parse", json={"pgn": ""})
    assert r.status_code == 422


async def test_import_list_get_roundtrip(client):
    r = await client.post("/api/games", json={"pgn": SAMPLE})
    assert r.status_code == 201
    imported = r.json()["games"]
    assert len(imported) == 1
    game_id = imported[0]["id"]
    assert imported[0]["move_count"] == 5

    r = await client.get("/api/games")
    listed = r.json()["games"]
    assert [g["id"] for g in listed] == [game_id]
    assert listed[0]["white"] == "Alice"

    r = await client.get(f"/api/games/{game_id}")
    assert r.status_code == 200
    detail = r.json()
    assert detail["result"] == "1-0"
    assert len(detail["moves"]) == 5
    # Not analyzed yet — every move has a null evaluation.
    assert all(m["evaluation"] is None for m in detail["moves"])


async def test_import_empty_pgn_422(client):
    r = await client.post("/api/games", json={"pgn": ""})
    assert r.status_code == 422


async def test_get_missing_game_404(client):
    r = await client.get("/api/games/999")
    assert r.status_code == 404


async def test_analyze_missing_game_404(client):
    r = await client.post("/api/analysis/games/999")
    assert r.status_code == 404


async def test_evaluate_invalid_fen_422(client):
    r = await client.post("/api/analysis/evaluate", json={"fen": "not a fen"})
    assert r.status_code == 422


async def test_evaluate_without_engine_503(client, monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "stockfish_path", str(tmp_path / "missing.exe"))
    r = await client.post(
        "/api/analysis/evaluate", json={"fen": chess.STARTING_FEN}
    )
    assert r.status_code == 503


async def test_analyze_game_without_engine_503(client, monkeypatch, tmp_path):
    r = await client.post("/api/games", json={"pgn": SAMPLE})
    game_id = r.json()["games"][0]["id"]

    monkeypatch.setattr(settings, "stockfish_path", str(tmp_path / "missing.exe"))
    r = await client.post(f"/api/analysis/games/{game_id}")
    assert r.status_code == 503
    r = await client.get(f"/api/analysis/games/{game_id}/stream")
    assert r.status_code == 503

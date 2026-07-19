import json
from dataclasses import asdict

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.db.models import Evaluation, Game, Move
from app.db.session import SessionFactory, get_session
from app.services import coach as coach_service
from app.services import engine as engine_service
from app.services import ollama as ollama_service
from app.services.analysis import GameAnalysis, analyze_game
from app.services.pgn import ParsedMove, parse_pgn

START_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"

router = APIRouter(prefix="/api")


@router.get("/health")
async def health() -> dict:
    return {
        "status": "ok",
        "stockfish": engine_service.engine_available(),
        "engine_depth": settings.engine_depth,
    }


class PgnUpload(BaseModel):
    pgn: str


@router.post("/games/parse")
async def parse_games(payload: PgnUpload) -> dict:
    games = parse_pgn(payload.pgn)
    if not games:
        raise HTTPException(status_code=422, detail="No games found in PGN")
    return {
        "games": [
            {
                "headers": g.headers,
                "moves": [vars(m) for m in g.moves],
            }
            for g in games
        ]
    }


@router.post("/games", status_code=201)
async def import_games(
    payload: PgnUpload, session: AsyncSession = Depends(get_session)
) -> dict:
    parsed = parse_pgn(payload.pgn)
    if not parsed:
        raise HTTPException(status_code=422, detail="No games found in PGN")
    imported = []
    for g in parsed:
        game = Game(
            white=g.headers.get("White"),
            black=g.headers.get("Black"),
            result=g.headers.get("Result"),
            event=g.headers.get("Event"),
            date=g.headers.get("Date"),
            eco=g.headers.get("ECO"),
            pgn=payload.pgn,
            moves=[
                Move(ply=m.ply, san=m.san, uci=m.uci, fen_after=m.fen_after)
                for m in g.moves
            ],
        )
        session.add(game)
        await session.flush()
        imported.append(
            {"id": game.id, "headers": g.headers, "move_count": len(g.moves)}
        )
    await session.commit()
    return {"games": imported}


@router.get("/games")
async def list_games(session: AsyncSession = Depends(get_session)) -> dict:
    rows = (await session.execute(select(Game).order_by(Game.id.desc()))).scalars()
    return {
        "games": [
            {
                "id": g.id,
                "white": g.white,
                "black": g.black,
                "result": g.result,
                "event": g.event,
                "date": g.date,
                "eco": g.eco,
            }
            for g in rows
        ]
    }


async def _load_game(session: AsyncSession, game_id: int) -> Game:
    game = (
        await session.execute(
            select(Game)
            .where(Game.id == game_id)
            .options(selectinload(Game.moves).selectinload(Move.evaluation))
        )
    ).scalar_one_or_none()
    if game is None:
        raise HTTPException(status_code=404, detail="Game not found")
    return game


@router.get("/games/{game_id}")
async def get_game(
    game_id: int, session: AsyncSession = Depends(get_session)
) -> dict:
    game = await _load_game(session, game_id)
    return {
        "id": game.id,
        "white": game.white,
        "black": game.black,
        "result": game.result,
        "event": game.event,
        "date": game.date,
        "eco": game.eco,
        "moves": [
            {
                "ply": m.ply,
                "san": m.san,
                "uci": m.uci,
                "fen_after": m.fen_after,
                "evaluation": (
                    {
                        "depth": m.evaluation.depth,
                        "score_cp": m.evaluation.score_cp,
                        "mate_in": m.evaluation.mate_in,
                        "best_move_uci": m.evaluation.best_move_uci,
                        "judgment": m.evaluation.judgment,
                        "win_pct": m.evaluation.win_pct,
                    }
                    if m.evaluation
                    else None
                ),
            }
            for m in game.moves
        ],
    }


class EvalRequest(BaseModel):
    fen: str
    depth: int | None = None


@router.post("/analysis/evaluate")
async def evaluate(payload: EvalRequest) -> dict:
    try:
        result = await engine_service.evaluate_fen(payload.fen, payload.depth)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=f"Invalid FEN: {exc}") from exc
    return vars(result)


def _initial_fen(game: Game) -> str | None:
    for line in game.pgn.splitlines():
        if line.startswith('[FEN "'):
            return line[6:].rstrip('"]')
    return None


async def _persist_analysis(
    session: AsyncSession, game: Game, analysis: GameAnalysis
) -> None:
    by_ply = {m.ply: m for m in game.moves}
    for ma in analysis.moves:
        move = by_ply.get(ma.ply)
        if move is None:
            continue
        if move.evaluation is None:
            move.evaluation = Evaluation(move_id=move.id, depth=ma.depth)
        ev = move.evaluation
        ev.depth = ma.depth
        ev.score_cp = ma.score_cp
        ev.mate_in = ma.mate_in
        ev.best_move_uci = ma.best_move_uci
        ev.judgment = ma.judgment
        ev.win_pct = ma.win_pct
    await session.commit()


class AnalyzeRequest(BaseModel):
    depth: int | None = None


@router.post("/analysis/games/{game_id}")
async def analyze_stored_game(
    game_id: int,
    payload: AnalyzeRequest | None = None,
    session: AsyncSession = Depends(get_session),
) -> dict:
    game = await _load_game(session, game_id)
    parsed = [
        ParsedMove(ply=m.ply, san=m.san, uci=m.uci, fen_after=m.fen_after)
        for m in game.moves
    ]
    depth = payload.depth if payload else None
    try:
        analysis: GameAnalysis | None = None
        async for event in analyze_game(parsed, depth, _initial_fen(game)):
            if event["type"] == "result":
                analysis = event["analysis"]
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    assert analysis is not None
    await _persist_analysis(session, game, analysis)
    return asdict(analysis)


@router.get("/analysis/games/{game_id}/stream")
async def analyze_stored_game_stream(
    game_id: int,
    depth: int | None = None,
    session: AsyncSession = Depends(get_session),
) -> StreamingResponse:
    """SSE stream: `progress` events per ply, then a final `result` event."""
    game = await _load_game(session, game_id)
    parsed = [
        ParsedMove(ply=m.ply, san=m.san, uci=m.uci, fen_after=m.fen_after)
        for m in game.moves
    ]
    if not engine_service.engine_available():
        raise HTTPException(status_code=503, detail="Stockfish not installed")

    initial_fen = _initial_fen(game)

    async def stream():
        # The request-scoped session is closed before this generator runs,
        # so persistence gets its own session.
        async for event in analyze_game(parsed, depth, initial_fen):
            if event["type"] == "progress":
                yield f"event: progress\ndata: {json.dumps(event)}\n\n"
            else:
                analysis = event["analysis"]
                async with SessionFactory() as own_session:
                    fresh = await _load_game(own_session, game_id)
                    await _persist_analysis(own_session, fresh, analysis)
                yield f"event: result\ndata: {json.dumps(asdict(analysis))}\n\n"

    return StreamingResponse(stream(), media_type="text/event-stream")


@router.get("/coach/health")
async def coach_health() -> dict:
    client = ollama_service.make_client()
    try:
        available = await ollama_service.is_available(client)
        models = await ollama_service.list_models(client) if available else []
    finally:
        await client.aclose()
    return {
        "available": available,
        "models": models,
        "default_model": settings.ollama_model,
    }


class ChatMessage(BaseModel):
    role: str
    content: str


class CoachRequest(BaseModel):
    game_id: int
    ply: int
    model: str | None = None
    messages: list[ChatMessage] | None = None


def _score_label(ev: Evaluation | None) -> str | None:
    if ev is None:
        return None
    if ev.mate_in is not None:
        return f"M{abs(ev.mate_in)}"
    if ev.score_cp is None:
        return None
    pawns = ev.score_cp / 100
    return f"{'+' if pawns > 0 else ''}{pawns:.2f}"


@router.post("/coach/explain")
async def coach_explain(
    payload: CoachRequest, session: AsyncSession = Depends(get_session)
) -> StreamingResponse:
    """SSE stream of the coach's answer: `data: {"delta": …}` chunks, then `event: done`."""
    if not await ollama_service.is_available():
        raise HTTPException(
            status_code=503,
            detail="Ollama is not running — install it from ollama.com and pull a model.",
        )
    game = await _load_game(session, payload.game_id)
    by_ply = {m.ply: m for m in game.moves}
    move = by_ply.get(payload.ply)
    if move is None:
        raise HTTPException(status_code=404, detail="Ply not found in game")
    prev = by_ply.get(payload.ply - 1)
    fen_before = (
        prev.fen_after if prev else (_initial_fen(game) or START_FEN)
    )
    ev = move.evaluation
    prev_ev = prev.evaluation if prev else None
    ctx = coach_service.MoveContext(
        ply=move.ply,
        san=move.san,
        fen_before=fen_before,
        fen_after=move.fen_after,
        judgment=ev.judgment if ev else None,
        score_label=_score_label(ev),
        win_pct=ev.win_pct if ev else None,
        better_san=coach_service.uci_to_san(
            fen_before, prev_ev.best_move_uci if prev_ev else None
        ),
        best_reply_san=coach_service.uci_to_san(
            move.fen_after, ev.best_move_uci if ev else None
        ),
    )
    headers = {"White": game.white or "?", "Black": game.black or "?"}
    history = (
        [{"role": m.role, "content": m.content} for m in payload.messages]
        if payload.messages
        else None
    )
    messages = coach_service.build_messages(headers, ctx, history)

    async def stream():
        try:
            async for delta in ollama_service.chat_stream(messages, payload.model):
                yield f"data: {json.dumps({'delta': delta})}\n\n"
            yield "event: done\ndata: {}\n\n"
        except Exception as exc:  # surface model errors to the client mid-stream
            yield f"event: error\ndata: {json.dumps({'detail': str(exc)})}\n\n"

    return StreamingResponse(stream(), media_type="text/event-stream")

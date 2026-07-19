from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.config import settings
from app.services import engine as engine_service
from app.services.pgn import parse_pgn

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

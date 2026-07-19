"""Stockfish integration over UCI via python-chess."""

from dataclasses import dataclass
from pathlib import Path

import chess
import chess.engine

from app.core.config import settings


@dataclass
class Evaluation:
    fen: str
    depth: int
    score_cp: int | None  # centipawns from side-to-move perspective; None if mate
    mate_in: int | None
    best_move_uci: str | None
    pv: list[str]


def engine_available() -> bool:
    return Path(settings.stockfish_path).is_file()


async def evaluate_fen(fen: str, depth: int | None = None) -> Evaluation:
    """Run a single-position analysis. Raises FileNotFoundError if Stockfish is missing."""
    if not engine_available():
        raise FileNotFoundError(
            f"Stockfish not found at {settings.stockfish_path}. "
            "Place the binary there or set CHESSLAB_STOCKFISH_PATH."
        )
    depth = depth or settings.engine_depth
    transport, engine = await chess.engine.popen_uci(settings.stockfish_path)
    try:
        board = chess.Board(fen)
        info = await engine.analyse(board, chess.engine.Limit(depth=depth))
        score = info["score"].relative
        pv_moves = info.get("pv", [])
        return Evaluation(
            fen=fen,
            depth=info.get("depth", depth),
            score_cp=score.score(),
            mate_in=score.mate(),
            best_move_uci=pv_moves[0].uci() if pv_moves else None,
            pv=[m.uci() for m in pv_moves],
        )
    finally:
        await engine.quit()

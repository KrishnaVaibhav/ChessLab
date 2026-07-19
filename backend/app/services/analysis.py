"""Full-game analysis: evaluate every position, classify moves, compute accuracy.

Win% and accuracy follow the lichess model:
  win% = 50 + 50 * (2 / (1 + exp(-0.00368208 * cp)) - 1)
  move accuracy% = 103.1668 * exp(-0.04354 * win_drop) - 3.1669
Judgment thresholds on the mover's win% drop: >=30 blunder, >=20 mistake,
>=10 inaccuracy.
"""

import math
from collections.abc import AsyncIterator
from dataclasses import dataclass, field

import chess
import chess.engine

from app.core.config import settings
from app.services import engine as engine_service
from app.services.pgn import ParsedMove


def _win_pct_white(score: chess.engine.PovScore) -> float:
    white = score.white()
    mate = white.mate()
    if mate is not None:
        return 100.0 if mate > 0 else 0.0
    cp = max(-1000, min(1000, white.score() or 0))
    return 50 + 50 * (2 / (1 + math.exp(-0.00368208 * cp)) - 1)


def _win_pct_white_on(board: chess.Board, score: chess.engine.PovScore) -> float:
    """Terminal positions get their exact result — the engine reports
    checkmate as Mate(0) whose sign doesn't identify the winner."""
    if board.is_checkmate():
        return 0.0 if board.turn == chess.WHITE else 100.0
    if board.is_game_over():
        return 50.0
    return _win_pct_white(score)


def _judge(win_drop: float) -> str:
    if win_drop >= 30:
        return "blunder"
    if win_drop >= 20:
        return "mistake"
    if win_drop >= 10:
        return "inaccuracy"
    return "ok"


def _move_accuracy(win_drop: float) -> float:
    raw = 103.1668 * math.exp(-0.04354 * win_drop) - 3.1669
    return max(0.0, min(100.0, raw))


@dataclass
class MoveAnalysis:
    ply: int
    san: str
    uci: str
    fen_after: str
    depth: int
    score_cp: int | None  # White perspective; None if mate
    mate_in: int | None  # White perspective
    best_move_uci: str | None
    win_pct: float  # White win%, after the move
    judgment: str
    accuracy: float


@dataclass
class GameAnalysis:
    depth: int
    moves: list[MoveAnalysis] = field(default_factory=list)
    white_accuracy: float = 0.0
    black_accuracy: float = 0.0
    judgment_counts: dict[str, dict[str, int]] = field(default_factory=dict)


async def _eval_position(
    engine: chess.engine.Protocol, board: chess.Board, depth: int
) -> tuple[chess.engine.PovScore, str | None, int]:
    info = await engine.analyse(board, chess.engine.Limit(depth=depth))
    pv = info.get("pv", [])
    best = pv[0].uci() if pv else None
    return info["score"], best, info.get("depth", depth)


async def analyze_game(
    moves: list[ParsedMove],
    depth: int | None = None,
    initial_fen: str | None = None,
) -> AsyncIterator[dict]:
    """Yield ``{"type": "progress", ...}`` per evaluated ply, then one
    ``{"type": "result", "analysis": GameAnalysis}``."""
    depth = depth or settings.engine_depth
    total = len(moves)
    result = GameAnalysis(depth=depth)
    counts = {
        "white": {"ok": 0, "inaccuracy": 0, "mistake": 0, "blunder": 0},
        "black": {"ok": 0, "inaccuracy": 0, "mistake": 0, "blunder": 0},
    }
    white_accs: list[float] = []
    black_accs: list[float] = []

    async with engine_service.pool.acquire() as engine:
        board = chess.Board(initial_fen) if initial_fen else chess.Board()
        score, _, _ = await _eval_position(engine, board, depth)
        prev_win_white = _win_pct_white_on(board, score)

        for i, mv in enumerate(moves, start=1):
            mover_is_white = board.turn == chess.WHITE
            board.push(chess.Move.from_uci(mv.uci))
            score, best, reached = await _eval_position(engine, board, depth)
            win_white = _win_pct_white_on(board, score)

            win_before = prev_win_white if mover_is_white else 100 - prev_win_white
            win_after = win_white if mover_is_white else 100 - win_white
            drop = max(0.0, win_before - win_after)
            judgment = _judge(drop)
            accuracy = _move_accuracy(drop)

            side = "white" if mover_is_white else "black"
            counts[side][judgment] += 1
            (white_accs if mover_is_white else black_accs).append(accuracy)

            white_score = score.white()
            result.moves.append(
                MoveAnalysis(
                    ply=mv.ply,
                    san=mv.san,
                    uci=mv.uci,
                    fen_after=mv.fen_after,
                    depth=reached,
                    score_cp=white_score.score(),
                    mate_in=white_score.mate(),
                    best_move_uci=best,
                    win_pct=round(win_white, 2),
                    judgment=judgment,
                    accuracy=round(accuracy, 2),
                )
            )
            prev_win_white = win_white
            yield {"type": "progress", "ply": i, "total": total}

    result.white_accuracy = round(
        sum(white_accs) / len(white_accs), 2) if white_accs else 100.0
    result.black_accuracy = round(
        sum(black_accs) / len(black_accs), 2) if black_accs else 100.0
    result.judgment_counts = counts
    yield {"type": "result", "analysis": result}

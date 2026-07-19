"""Stockfish integration over UCI via python-chess.

A small pool of persistent engine processes is started with the app
(``pool.start`` in the FastAPI lifespan) so requests don't pay process
spawn + UCI handshake per evaluation.
"""

import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
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


class EnginePool:
    """Fixed-size pool of persistent UCI engine processes."""

    def __init__(self, size: int) -> None:
        self.size = size
        self._idle: asyncio.Queue[chess.engine.Protocol] = asyncio.Queue()
        self._all: list[chess.engine.Protocol] = []
        self._started = False

    async def start(self) -> None:
        if self._started or not engine_available():
            return
        for _ in range(self.size):
            _, engine = await chess.engine.popen_uci(settings.stockfish_path)
            await engine.configure({"Threads": settings.engine_threads})
            self._all.append(engine)
            self._idle.put_nowait(engine)
        self._started = True

    async def stop(self) -> None:
        for engine in self._all:
            try:
                await engine.quit()
            except chess.engine.EngineError:
                pass
        self._all.clear()
        self._idle = asyncio.Queue()
        self._started = False

    @asynccontextmanager
    async def acquire(self) -> AsyncIterator[chess.engine.Protocol]:
        """Yield a persistent engine, or a throwaway process if the pool
        isn't running (engine installed after startup, tests)."""
        if not engine_available():
            raise FileNotFoundError(
                f"Stockfish not found at {settings.stockfish_path}. "
                "Place the binary there or set CHESSLAB_STOCKFISH_PATH."
            )
        if self._started:
            engine = await self._idle.get()
            try:
                yield engine
            finally:
                self._idle.put_nowait(engine)
        else:
            _, engine = await chess.engine.popen_uci(settings.stockfish_path)
            try:
                yield engine
            finally:
                await engine.quit()


pool = EnginePool(settings.engine_pool_size)


async def evaluate_board(
    engine: chess.engine.Protocol, board: chess.Board, depth: int
) -> Evaluation:
    info = await engine.analyse(board, chess.engine.Limit(depth=depth))
    score = info["score"].relative
    pv_moves = info.get("pv", [])
    return Evaluation(
        fen=board.fen(),
        depth=info.get("depth", depth),
        score_cp=score.score(),
        mate_in=score.mate(),
        best_move_uci=pv_moves[0].uci() if pv_moves else None,
        pv=[m.uci() for m in pv_moves],
    )


async def evaluate_fen(fen: str, depth: int | None = None) -> Evaluation:
    """Run a single-position analysis. Raises FileNotFoundError if Stockfish is missing."""
    board = chess.Board(fen)  # raises ValueError on invalid FEN before acquiring
    async with pool.acquire() as engine:
        return await evaluate_board(engine, board, depth or settings.engine_depth)

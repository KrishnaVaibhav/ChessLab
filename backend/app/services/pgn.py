"""PGN parsing: turn raw PGN text into structured game data with per-move FENs."""

import io
from dataclasses import dataclass, field

import chess.pgn


@dataclass
class ParsedMove:
    ply: int
    san: str
    uci: str
    fen_after: str


@dataclass
class ParsedGame:
    headers: dict[str, str]
    moves: list[ParsedMove] = field(default_factory=list)


def parse_pgn(pgn_text: str) -> list[ParsedGame]:
    """Parse one or more games from a PGN string."""
    games: list[ParsedGame] = []
    stream = io.StringIO(pgn_text)
    while True:
        game = chess.pgn.read_game(stream)
        if game is None:
            break
        parsed = ParsedGame(headers=dict(game.headers))
        board = game.board()
        for ply, move in enumerate(game.mainline_moves(), start=1):
            san = board.san(move)
            board.push(move)
            parsed.moves.append(
                ParsedMove(ply=ply, san=san, uci=move.uci(), fen_after=board.fen())
            )
        games.append(parsed)
    return games

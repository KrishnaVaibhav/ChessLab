"""Analysis math + full-game analysis against a real engine (skipped if absent)."""

import pytest

from app.services.analysis import _judge, _move_accuracy, _win_pct_white, analyze_game
from app.services.engine import engine_available
from app.services.pgn import parse_pgn

# Scholar's mate: 3... Nf6?? allows 4. Qxf7#
SCHOLARS_MATE = (
    '[Event "Test"]\n\n'
    "1. e4 e5 2. Bc4 Nc6 3. Qh5 Nf6 4. Qxf7# 1-0\n"
)


def test_judge_thresholds():
    assert _judge(0) == "ok"
    assert _judge(9.9) == "ok"
    assert _judge(10) == "inaccuracy"
    assert _judge(20) == "mistake"
    assert _judge(30) == "blunder"
    assert _judge(85) == "blunder"


def test_move_accuracy_bounds():
    assert _move_accuracy(0) == pytest.approx(100.0, abs=0.01)
    assert _move_accuracy(100) == 0.0
    assert 0 < _move_accuracy(20) < 100


class _FakeScore:
    def __init__(self, cp=None, mate=None):
        self._cp, self._mate = cp, mate

    def white(self):
        return self

    def score(self):
        return self._cp

    def mate(self):
        return self._mate


def test_win_pct_white():
    assert _win_pct_white(_FakeScore(cp=0)) == 50.0
    assert _win_pct_white(_FakeScore(cp=300)) > 70
    assert _win_pct_white(_FakeScore(cp=-300)) < 30
    assert _win_pct_white(_FakeScore(mate=2)) == 100.0
    assert _win_pct_white(_FakeScore(mate=-2)) == 0.0


@pytest.mark.skipif(not engine_available(), reason="Stockfish not installed")
@pytest.mark.asyncio
async def test_analyze_game_finds_blunder():
    game = parse_pgn(SCHOLARS_MATE)[0]
    events = []
    async for event in analyze_game(game.moves, depth=8):
        events.append(event)

    progress = [e for e in events if e["type"] == "progress"]
    assert len(progress) == 7
    assert progress[-1] == {"type": "progress", "ply": 7, "total": 7}

    analysis = events[-1]["analysis"]
    assert len(analysis.moves) == 7
    # 3... Nf6 (ply 6) hangs mate — must be a blunder.
    assert analysis.moves[5].judgment == "blunder"
    # Final position is checkmate, White winning.
    assert analysis.moves[-1].win_pct == 100.0
    assert analysis.judgment_counts["black"]["blunder"] >= 1
    assert analysis.white_accuracy > analysis.black_accuracy

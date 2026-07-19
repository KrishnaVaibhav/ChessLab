from app.services.pgn import parse_pgn

SAMPLE = """[Event "Test"]
[White "Alice"]
[Black "Bob"]
[Result "1-0"]

1. e4 e5 2. Nf3 Nc6 3. Bb5 1-0
"""


def test_parse_single_game():
    games = parse_pgn(SAMPLE)
    assert len(games) == 1
    game = games[0]
    assert game.headers["White"] == "Alice"
    assert len(game.moves) == 5
    assert game.moves[0].san == "e4"
    assert game.moves[0].uci == "e2e4"
    assert game.moves[-1].san == "Bb5"
    assert game.moves[0].fen_after.startswith("rnbqkbnr/pppppppp/8/8/4P3")


def test_parse_empty_returns_no_games():
    assert parse_pgn("") == []
    assert parse_pgn("   \n\n  ") == []


def test_parse_multiple_games():
    games = parse_pgn(SAMPLE + "\n" + SAMPLE.replace("Alice", "Carol"))
    assert len(games) == 2
    assert games[0].headers["White"] == "Alice"
    assert games[1].headers["White"] == "Carol"
    assert len(games[0].moves) == len(games[1].moves) == 5


def test_parse_movetext_without_headers():
    games = parse_pgn("1. d4 d5 2. c4 *")
    assert len(games) == 1
    assert [m.san for m in games[0].moves] == ["d4", "d5", "c4"]
    assert games[0].moves[2].ply == 3


def test_parse_game_from_fen_header():
    pgn = (
        '[SetUp "1"]\n'
        '[FEN "4k3/8/8/8/8/8/4P3/4K3 w - - 0 1"]\n\n'
        "1. e4 Kd7 *"
    )
    games = parse_pgn(pgn)
    assert len(games) == 1
    assert games[0].moves[0].san == "e4"
    # FEN start position is respected — board has only 3 pieces.
    assert games[0].moves[0].fen_after.startswith("4k3/8/8/8/4P3/8/8/4K3")

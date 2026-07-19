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

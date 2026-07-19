"""Prompt building for the AI coach: position and mistake explanations."""

from dataclasses import dataclass

import chess

SYSTEM_PROMPT = (
    "You are a patient, encouraging chess coach. You are given the state of a "
    "chess game and Stockfish's evaluation of it. Explain ideas in plain "
    "language for a club player: name the key pieces, threats, and plans. "
    "Keep answers under 150 words unless asked for more. Never invent moves "
    "or squares — only reason from the positions and engine lines you are given."
)


@dataclass
class MoveContext:
    ply: int
    san: str
    fen_before: str
    fen_after: str
    judgment: str | None = None
    score_label: str | None = None  # e.g. "+0.85" or "M3", White perspective
    win_pct: float | None = None  # White win%, after the move
    better_san: str | None = None  # engine's preferred move instead of san
    best_reply_san: str | None = None  # engine's best move in the new position


def uci_to_san(fen: str, uci: str | None) -> str | None:
    if not uci:
        return None
    try:
        board = chess.Board(fen)
        move = chess.Move.from_uci(uci)
        if move not in board.legal_moves:
            return None
        return board.san(move)
    except ValueError:
        return None


def describe_context(headers: dict, ctx: MoveContext) -> str:
    move_no = (ctx.ply + 1) // 2
    dots = "." if ctx.ply % 2 == 1 else "..."
    lines = [
        f"Game: {headers.get('White', '?')} (White) vs {headers.get('Black', '?')} (Black).",
        f"Position after {move_no}{dots} {ctx.san} (FEN: {ctx.fen_after}).",
    ]
    if ctx.score_label is not None:
        lines.append(f"Stockfish evaluation: {ctx.score_label} (White perspective).")
    if ctx.win_pct is not None:
        lines.append(f"White winning chances: {ctx.win_pct:.0f}%.")
    if ctx.judgment and ctx.judgment != "ok":
        lines.append(f"The engine classified {ctx.san} as a {ctx.judgment}.")
    if ctx.better_san:
        lines.append(f"Stockfish preferred {ctx.better_san} instead.")
    if ctx.best_reply_san:
        lines.append(f"In the new position the engine's best move is {ctx.best_reply_san}.")
    return "\n".join(lines)


def default_question(ctx: MoveContext) -> str:
    if ctx.judgment in ("inaccuracy", "mistake", "blunder"):
        alt = f" Why is {ctx.better_san} better?" if ctx.better_san else ""
        return f"Why was {ctx.san} a {ctx.judgment}?{alt}"
    return "Explain what is going on in this position and the plans for both sides."


def build_messages(
    headers: dict, ctx: MoveContext, history: list[dict] | None = None
) -> list[dict]:
    """System prompt + position context, then chat history (or the default question)."""
    messages: list[dict] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "system", "content": describe_context(headers, ctx)},
    ]
    if history:
        messages.extend({"role": m["role"], "content": m["content"]} for m in history)
    else:
        messages.append({"role": "user", "content": default_question(ctx)})
    return messages

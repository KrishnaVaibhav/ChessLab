"""ORM models: Game, Move, Evaluation."""

from datetime import datetime, timezone

from sqlalchemy import ForeignKey, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Game(Base):
    __tablename__ = "games"

    id: Mapped[int] = mapped_column(primary_key=True)
    white: Mapped[str | None]
    black: Mapped[str | None]
    result: Mapped[str | None]
    event: Mapped[str | None]
    date: Mapped[str | None]  # PGN date string, e.g. "2026.07.19"
    eco: Mapped[str | None]
    pgn: Mapped[str] = mapped_column(Text)
    imported_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc)
    )

    moves: Mapped[list["Move"]] = relationship(
        back_populates="game", cascade="all, delete-orphan", order_by="Move.ply"
    )


class Move(Base):
    __tablename__ = "moves"
    __table_args__ = (UniqueConstraint("game_id", "ply"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    game_id: Mapped[int] = mapped_column(ForeignKey("games.id", ondelete="CASCADE"))
    ply: Mapped[int]
    san: Mapped[str]
    uci: Mapped[str]
    fen_after: Mapped[str]

    game: Mapped[Game] = relationship(back_populates="moves")
    evaluation: Mapped["Evaluation | None"] = relationship(
        back_populates="move", cascade="all, delete-orphan", uselist=False
    )


class Evaluation(Base):
    __tablename__ = "evaluations"

    id: Mapped[int] = mapped_column(primary_key=True)
    move_id: Mapped[int] = mapped_column(
        ForeignKey("moves.id", ondelete="CASCADE"), unique=True
    )
    depth: Mapped[int]
    # Score after the move, from White's perspective (centipawns); None if mate.
    score_cp: Mapped[int | None]
    mate_in: Mapped[int | None]
    best_move_uci: Mapped[str | None]
    # Classification of the move that led here: ok/inaccuracy/mistake/blunder.
    judgment: Mapped[str | None]
    # Win probability for White after the move, 0-100.
    win_pct: Mapped[float | None]

    move: Mapped[Move] = relationship(back_populates="evaluation")

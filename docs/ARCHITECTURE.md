# ChessLab Architecture

## Overview

ChessLab is a local-first chess analysis app. Web-first development, packaged later as a desktop app with Tauri. One codebase serves both.

```
                React
   ┌──────────────────────────────┐
   │ Chess Board    Move List     │
   │ Analysis       Settings      │
   │ AI Chat        Statistics    │
   └──────────────┬───────────────┘
                  │  REST /api
   ┌──────────────┴───────────────┐
   │           FastAPI            │
   │     Analysis Coordinator     │
   └───┬──────────┬──────────┬────┘
       ▼          ▼          ▼
   Stockfish    Ollama     SQLite
   (UCI sub-   (local      (games,
   process)     LLM)       analyses)
```

Everything runs locally. No internet required after setup.

## Components

### Frontend — `frontend/`

React + TypeScript + Vite + Tailwind CSS v4.

| Concern | Library |
|---|---|
| Board rendering | react-chessboard |
| Move legality / SAN | chess.js |
| Styling | Tailwind v4 (Vite plugin) |

Dev server proxies `/api` to the backend (see `vite.config.ts`), so the frontend never hardcodes a backend URL.

Planned UI regions: board, move list, engine eval bar/graph, AI coach chat, opening explorer, accuracy/blunder report, statistics dashboard, training view, settings.

### Backend — `backend/`

FastAPI app, layered:

```
app/
  main.py        FastAPI instance, CORS, router mounting
  api/           HTTP layer (routes.py) — thin, no business logic
  core/          config.py — pydantic-settings, CHESSLAB_ env prefix
  services/      pgn.py (parse), engine.py (Stockfish UCI)
  models/        SQLAlchemy models (pending)
```

Design rule: the API is treated as public from day one — stable JSON shapes, proper status codes — so alternative frontends (CLI, mobile) can reuse it.

### Engine — `engine/`

Stockfish binary dropped at `engine/bin/stockfish.exe` (gitignored) or pointed to via `CHESSLAB_STOCKFISH_PATH`. Backend talks UCI through `python-chess`'s async engine API. Missing binary → `/api/analysis/evaluate` returns 503 with instructions; `/api/health` reports availability.

### Local AI

Ollama at `http://127.0.0.1:11434` (configurable). Default model `qwen3`. The AI provider is an implementation detail behind a service interface — cloud providers (OpenAI/Anthropic/Gemini) can be added later without architecture changes.

### Database

SQLite via SQLAlchemy + aiosqlite. File at repo root (`chesslab.sqlite3`, gitignored). PostgreSQL optional later for server deployments — that is why access goes through SQLAlchemy, not raw sqlite3.

## Configuration

All settings via `CHESSLAB_`-prefixed env vars or `backend/.env`:

| Variable | Default | Purpose |
|---|---|---|
| `CHESSLAB_STOCKFISH_PATH` | `engine/bin/stockfish.exe` | Engine binary |
| `CHESSLAB_DATABASE_URL` | `sqlite+aiosqlite:///.../chesslab.sqlite3` | DB |
| `CHESSLAB_OLLAMA_BASE_URL` | `http://127.0.0.1:11434` | LLM runtime |
| `CHESSLAB_OLLAMA_MODEL` | `qwen3` | Default model |
| `CHESSLAB_ENGINE_DEPTH` | `18` | Analysis depth |
| `CHESSLAB_ENGINE_MULTIPV` | `1` | Lines per position |

## Desktop packaging (planned)

Tauri shell wrapping the built frontend. Known hard problem: Tauri cannot bundle a Python runtime, so the FastAPI backend must ship as a PyInstaller sidecar binary (large, slow cold start, antivirus false positives). Decision deferred until the web core is stable. Fallback option: distribute as `pip install chesslab` that opens the browser.

First-launch flow (planned): detect/download Stockfish, detect existing Ollama or install, pull recommended model, fetch opening database — then fully offline.

## Data flow: analyzing a game

1. User uploads PGN → `POST /api/games/parse` → per-move SAN/UCI/FEN.
2. (Planned) Coordinator queues each FEN for Stockfish eval, stores results in SQLite, computes accuracy/blunders from eval deltas.
3. (Planned) AI coach receives position + eval context, generates explanation via Ollama.
4. Frontend renders eval graph, annotated move list, coach chat.

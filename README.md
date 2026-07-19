# ChessLab

Local-first chess analysis. Upload your games, get Stockfish evaluation, accuracy reports, and plain-language coaching from a local LLM — everything runs on your machine, no accounts, no API keys, no internet after setup.

## Features

**Working now**
- PGN parsing → structured moves with per-position FENs
- Stockfish position evaluation over UCI (bring your own binary)
- REST API with interactive docs

**Planned** (full tracker: [docs/ROADMAP.md](docs/ROADMAP.md))
- Interactive board with move navigation and eval graph
- Full-game analysis: accuracy %, blunder/mistake detection
- AI coach — explains your mistakes via Ollama (Qwen, Gemma, Llama, Mistral…)
- Opening explorer, statistics, blunder-replay training
- Desktop app via Tauri with one-click first-launch setup

## Architecture

```
React (frontend/)  ──/api──>  FastAPI (backend/)
                                  ├── Stockfish (UCI subprocess)
                                  ├── Ollama (local LLM)
                                  └── SQLite
```

Web-first, packaged later as a Tauri desktop app — one codebase for both. The backend API is designed as public from day one so alternative frontends (CLI, mobile) stay possible. Details: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Stack

| Layer | Tech |
|---|---|
| Frontend | React, TypeScript, Vite, Tailwind CSS v4, chess.js, react-chessboard |
| Backend | FastAPI, python-chess, SQLAlchemy, SQLite (aiosqlite) |
| Engine | Stockfish via UCI |
| Local AI | Ollama (model configurable) |
| Desktop (planned) | Tauri |

## Development setup

Prerequisites: Python ≥ 3.12, Node ≥ 20.

```powershell
git clone https://github.com/<you>/ChessLab
cd ChessLab

# Backend — venv lives inside the project, nothing touches system Python
cd backend
python -m venv .venv
.\.venv\Scripts\python -m pip install -e ".[dev]"

# Frontend
cd ..\frontend
npm install

# Launch everything (backend :8000 + frontend :5173)
cd ..
.\scripts\dev.ps1
```

- App: http://127.0.0.1:5173
- API docs (Swagger): http://127.0.0.1:8000/docs

### Engine setup

Download Stockfish from [stockfishchess.org](https://stockfishchess.org/download/) and place the binary at `engine/bin/stockfish.exe`, or point `CHESSLAB_STOCKFISH_PATH` at an existing install. Until then, eval endpoints return 503 and `/api/health` shows `"stockfish": false`.

### Local AI setup (optional, for coach features)

Install [Ollama](https://ollama.com) and pull a model:

```powershell
ollama pull qwen3
```

## Configuration

Env vars (or `backend/.env`), all prefixed `CHESSLAB_`:

| Variable | Default |
|---|---|
| `CHESSLAB_STOCKFISH_PATH` | `engine/bin/stockfish.exe` |
| `CHESSLAB_DATABASE_URL` | project-root SQLite file |
| `CHESSLAB_OLLAMA_BASE_URL` | `http://127.0.0.1:11434` |
| `CHESSLAB_OLLAMA_MODEL` | `qwen3` |
| `CHESSLAB_ENGINE_DEPTH` | `18` |
| `CHESSLAB_ENGINE_MULTIPV` | `1` |

## API

| Endpoint | Method | Purpose |
|---|---|---|
| `/api/health` | GET | Status + engine availability |
| `/api/games/parse` | POST | PGN → per-move SAN/UCI/FEN |
| `/api/analysis/evaluate` | POST | Stockfish evaluation of a FEN |

## Tests

```powershell
cd backend
.\.venv\Scripts\python -m pytest
```

## Repo layout

```
frontend/   React app (Vite + TS + Tailwind)
backend/    FastAPI app — app/api (routes), app/core (config),
            app/services (pgn, engine), app/models (DB, pending)
engine/     Stockfish drop-in (bin/ gitignored)
scripts/    dev.ps1 — one-command dev environment
docs/       ARCHITECTURE.md, ROADMAP.md (build tracker)
```

## Project docs

- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — components, data flow, config, packaging plan
- [docs/ROADMAP.md](docs/ROADMAP.md) — what's built, what's next, phase by phase

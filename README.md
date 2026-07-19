# ChessLab

Local-first chess analysis: Stockfish evaluation, AI coaching via a local LLM, and game statistics — all running on your machine.

## Architecture

```
React (frontend/)  ──/api──>  FastAPI (backend/)
                                  ├── Stockfish (UCI subprocess)
                                  ├── Ollama (local LLM)
                                  └── SQLite
```

Web-first; a Tauri desktop shell is planned once the core is stable.

## Stack

- **Frontend:** React + TypeScript + Vite + Tailwind CSS v4, chess.js, react-chessboard
- **Backend:** FastAPI, python-chess, SQLAlchemy + SQLite
- **Engine:** Stockfish (UCI) — place the binary at `engine/bin/stockfish.exe` or set `CHESSLAB_STOCKFISH_PATH`
- **Local AI:** Ollama (default model configurable via `CHESSLAB_OLLAMA_MODEL`)

## Development setup

```powershell
# Backend (venv lives in the project, not the system Python)
cd backend
python -m venv .venv
.\.venv\Scripts\python -m pip install -e ".[dev]"

# Frontend
cd ..\frontend
npm install

# Run everything
cd ..
.\scripts\dev.ps1
```

- API docs: http://127.0.0.1:8000/docs
- App: http://127.0.0.1:5173

## Tests

```powershell
cd backend
.\.venv\Scripts\python -m pytest
```

## API

| Endpoint | Method | Purpose |
|---|---|---|
| `/api/health` | GET | Status + engine availability |
| `/api/games/parse` | POST | PGN → per-move SAN/UCI/FEN |
| `/api/analysis/evaluate` | POST | Stockfish evaluation of a FEN |

## Repo layout

```
frontend/   React app
backend/    FastAPI app (app/api, app/core, app/services, app/models)
engine/     Stockfish binary drop-in (bin/ is gitignored)
scripts/    Dev tooling
docs/       Documentation
```

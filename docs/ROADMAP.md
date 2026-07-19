# ChessLab Build Tracker

Status of what is built and what remains. Update this file as work lands — each item should map to one or more commits.

## ✅ Built

### Phase 0 — Scaffold (2026-07-19)
- [x] Repo structure: `frontend/`, `backend/`, `engine/`, `scripts/`, `docs/`
- [x] Frontend: Vite + React + TypeScript scaffold
- [x] Tailwind CSS v4 wired via Vite plugin
- [x] chess.js + react-chessboard installed
- [x] Dev proxy `/api` → FastAPI :8000
- [x] Backend: FastAPI app, CORS for Vite dev server
- [x] Config via pydantic-settings (`CHESSLAB_` env prefix)
- [x] PGN parsing service → per-move SAN/UCI/FEN (`/api/games/parse`)
- [x] Stockfish UCI service, single-FEN eval (`/api/analysis/evaluate`)
- [x] `/api/health` with engine availability
- [x] pytest suite (PGN parsing)
- [x] `scripts/dev.ps1` one-command dev environment
- [x] Project venv at `backend/.venv` (nothing global)

### Phase 1 — Core analysis loop (2026-07-19)
- [x] Stockfish 18 via `scripts/get-stockfish.ps1` (binary gitignored), eval verified end-to-end
- [x] SQLAlchemy async models: Game, Move, Evaluation (`app/db/models.py`)
- [x] DB session wiring; migrations = `create_all` on startup, Alembic deferred until schema must evolve
- [x] Full-game analysis: `POST /api/analysis/games/{id}` evaluates every ply, persists evals
- [x] Persistent engine pool (`EnginePool`, size/threads configurable) via app lifespan
- [x] Lichess-model win%, accuracy %, ok/inaccuracy/mistake/blunder judgments
- [x] SSE progress: `GET /api/analysis/games/{id}/stream` (progress events + final result)
- [x] Game import/list/detail: `POST/GET /api/games`, `GET /api/games/{id}`

### Phase 2 — Frontend core (2026-07-19)
- [x] Board component with move navigation (react-chessboard + chess.js)
- [x] PGN upload UI (paste or .pgn file), game list
- [x] Move list with annotations (?!, ?, ??)
- [x] Eval bar + win% eval graph (judgment markers, hover tooltip, click-to-seek)
- [x] Analysis dashboard layout (board / move list / eval / panels)
- [x] SSE analysis progress bar; keyboard nav (←/→/Home/End, f to flip)

## 🔨 Next up

### Phase 3 — AI coach
- [ ] Ollama service client (health check, model list, generate)
- [ ] Prompt templates: position explanation, mistake explanation
- [ ] `/api/coach/explain` endpoint (position + eval context → explanation)
- [ ] Chat UI panel with streaming responses
- [ ] Model picker in settings

### Phase 4 — Insights
- [ ] Opening detection (ECO codes) + opening explorer panel
- [ ] Per-player statistics across imported games
- [ ] Blunder review / training mode (replay mistakes as puzzles)

### Phase 5 — Distribution
- [ ] Settings UI (engine depth, threads, model, paths)
- [ ] First-launch setup flow: detect/download Stockfish, Ollama, model
- [ ] Tauri desktop shell (decide: PyInstaller sidecar vs alternatives — see ARCHITECTURE.md)
- [ ] Installers: Windows `.msi`, macOS `.dmg`, Linux `.AppImage`
- [x] CI: lint + test on push (`.github/workflows/ci.yml`) + Dependabot (npm, pip, actions)

### Later / optional
- [ ] Cloud AI providers (OpenAI, Anthropic, Gemini) behind provider interface
- [ ] Stockfish WASM fallback for zero-install browser demo
- [ ] PostgreSQL support for hosted deployments
- [ ] Chess.com / Lichess game import

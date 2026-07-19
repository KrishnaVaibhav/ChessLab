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

## 🔨 Next up

### Phase 1 — Core analysis loop
- [ ] Download/place Stockfish binary, verify eval endpoint end-to-end
- [ ] SQLAlchemy models: Game, Move, Evaluation
- [ ] DB session wiring + migrations strategy
- [ ] Full-game analysis: batch-evaluate every position of a parsed game
- [ ] Persistent engine process (pool) instead of spawn-per-request
- [ ] Accuracy % + blunder/mistake/inaccuracy classification from eval deltas
- [ ] Progress reporting for long analyses (SSE or WebSocket)

### Phase 2 — Frontend core
- [ ] Board component with move navigation (react-chessboard + chess.js)
- [ ] PGN upload UI
- [ ] Move list with annotations (?!, ?, ??)
- [ ] Eval bar + eval graph
- [ ] Analysis dashboard layout (board / move list / eval / panels)

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
- [ ] CI: lint + test on push (`.github/workflows`)

### Later / optional
- [ ] Cloud AI providers (OpenAI, Anthropic, Gemini) behind provider interface
- [ ] Stockfish WASM fallback for zero-install browser demo
- [ ] PostgreSQL support for hosted deployments
- [ ] Chess.com / Lichess game import

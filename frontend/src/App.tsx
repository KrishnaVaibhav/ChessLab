import { useCallback, useEffect, useRef, useState } from 'react'
import { analyzeGameStream, getGame, importPgn, listGames } from './api'
import AnalysisPanel from './components/AnalysisPanel'
import Board from './components/Board'
import CoachPanel from './components/CoachPanel'
import EvalBar from './components/EvalBar'
import EvalGraph from './components/EvalGraph'
import GameList from './components/GameList'
import MoveList from './components/MoveList'
import PgnUpload from './components/PgnUpload'
import { START_FEN, evalLabel } from './lib/chess'
import type { AnalysisProgress, GameDetail, GameSummary } from './types'

function NavButton({
  onClick,
  disabled,
  children,
  title,
}: {
  onClick: () => void
  disabled?: boolean
  children: React.ReactNode
  title: string
}) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      title={title}
      className="rounded bg-neutral-800 px-3 py-1.5 text-sm text-neutral-200 hover:bg-neutral-700 disabled:opacity-30"
    >
      {children}
    </button>
  )
}

function Panel({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="rounded-lg border border-neutral-800 bg-neutral-900/60 p-3">
      <h2 className="mb-2 text-xs font-semibold uppercase tracking-wide text-neutral-500">
        {title}
      </h2>
      {children}
    </section>
  )
}

export default function App() {
  const [games, setGames] = useState<GameSummary[]>([])
  const [game, setGame] = useState<GameDetail | null>(null)
  const [ply, setPly] = useState(0)
  const [orientation, setOrientation] = useState<'white' | 'black'>('white')
  const [analyzing, setAnalyzing] = useState(false)
  const [progress, setProgress] = useState<AnalysisProgress | null>(null)
  const [analysisError, setAnalysisError] = useState<string | null>(null)
  const stopStream = useRef<(() => void) | null>(null)

  const refreshGames = useCallback(async () => {
    setGames((await listGames()).games)
  }, [])

  useEffect(() => {
    refreshGames().catch(() => {})
    return () => stopStream.current?.()
  }, [refreshGames])

  const loadGame = useCallback(async (id: number) => {
    const detail = await getGame(id)
    setGame(detail)
    setPly(0)
    setAnalysisError(null)
  }, [])

  const onImport = useCallback(
    async (pgn: string) => {
      const res = await importPgn(pgn)
      await refreshGames()
      const first = res.games[0]
      if (first) await loadGame(first.id)
    },
    [refreshGames, loadGame],
  )

  const onAnalyze = useCallback(() => {
    if (!game || analyzing) return
    setAnalyzing(true)
    setProgress(null)
    setAnalysisError(null)
    stopStream.current = analyzeGameStream(game.id, {
      onProgress: setProgress,
      onResult: () => {
        setAnalyzing(false)
        loadGame(game.id).catch(() => {})
      },
      onError: (message) => {
        setAnalyzing(false)
        setAnalysisError(message)
      },
    })
  }, [game, analyzing, loadGame])

  const moveCount = game?.moves.length ?? 0
  const clampPly = useCallback(
    (p: number) => Math.max(0, Math.min(moveCount, p)),
    [moveCount],
  )
  const goTo = useCallback((p: number) => setPly(clampPly(p)), [clampPly])

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.target instanceof HTMLTextAreaElement || e.target instanceof HTMLInputElement)
        return
      if (e.key === 'ArrowLeft') goTo(ply - 1)
      else if (e.key === 'ArrowRight') goTo(ply + 1)
      else if (e.key === 'Home') goTo(0)
      else if (e.key === 'End') goTo(moveCount)
      else if (e.key === 'f') setOrientation((o) => (o === 'white' ? 'black' : 'white'))
      else return
      e.preventDefault()
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [ply, moveCount, goTo])

  const currentMove = ply > 0 ? (game?.moves[ply - 1] ?? null) : null
  const fen = currentMove?.fen_after ?? START_FEN
  const evaluation = currentMove?.evaluation ?? null

  return (
    <div className="min-h-screen bg-neutral-950 text-neutral-100">
      <header className="border-b border-neutral-800 px-6 py-3">
        <h1 className="text-lg font-bold">
          ChessLab
          <span className="ml-2 text-sm font-normal text-neutral-500">
            local analysis with Stockfish
          </span>
        </h1>
      </header>
      <main className="mx-auto flex max-w-6xl flex-col gap-6 p-6 lg:flex-row lg:items-start">
        <section className="flex w-full gap-2 lg:max-w-xl">
          <EvalBar
            winPct={evaluation?.win_pct ?? (ply === 0 ? 50 : null)}
            label={evalLabel(evaluation)}
            orientation={orientation}
          />
          <div className="min-w-0 flex-1">
            <Board
              fen={fen}
              lastMoveUci={currentMove?.uci ?? null}
              bestMoveUci={evaluation?.best_move_uci ?? null}
              orientation={orientation}
            />
            <div className="mt-2 flex items-center gap-1.5">
              <NavButton title="Start (Home)" onClick={() => goTo(0)} disabled={ply === 0}>
                ⏮
              </NavButton>
              <NavButton title="Back (←)" onClick={() => goTo(ply - 1)} disabled={ply === 0}>
                ◀
              </NavButton>
              <NavButton
                title="Forward (→)"
                onClick={() => goTo(ply + 1)}
                disabled={ply >= moveCount}
              >
                ▶
              </NavButton>
              <NavButton
                title="End (End)"
                onClick={() => goTo(moveCount)}
                disabled={ply >= moveCount}
              >
                ⏭
              </NavButton>
              <span className="ml-2 font-mono text-xs text-neutral-500">
                {ply}/{moveCount}
              </span>
              <NavButton
                title="Flip board (f)"
                onClick={() =>
                  setOrientation((o) => (o === 'white' ? 'black' : 'white'))
                }
              >
                ⇅
              </NavButton>
            </div>
          </div>
        </section>
        <aside className="flex w-full min-w-0 flex-col gap-4 lg:max-w-md">
          <Panel title="Import PGN">
            <PgnUpload onImport={onImport} />
            <div className="mt-2">
              <GameList
                games={games}
                selectedId={game?.id ?? null}
                onSelect={(id) => loadGame(id).catch(() => {})}
              />
            </div>
          </Panel>
          {game && (
            <Panel title="Analysis">
              <AnalysisPanel
                game={game}
                analyzing={analyzing}
                progress={progress}
                error={analysisError}
                onAnalyze={onAnalyze}
              />
            </Panel>
          )}
          {game && (
            <Panel title="Coach">
              <CoachPanel game={game} ply={ply} />
            </Panel>
          )}
          {game && (
            <Panel title="Eval graph">
              <EvalGraph moves={game.moves} currentPly={ply} onSelect={goTo} />
            </Panel>
          )}
          <Panel title="Moves">
            <MoveList moves={game?.moves ?? []} currentPly={ply} onSelect={goTo} />
          </Panel>
        </aside>
      </main>
    </div>
  )
}

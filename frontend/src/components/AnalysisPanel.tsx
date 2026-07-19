import { JUDGMENT_COLOR, accuracySummary } from '../lib/chess'
import type { AnalysisProgress, GameDetail, Judgment } from '../types'
import type { SideSummary } from '../lib/chess'

interface AnalysisPanelProps {
  game: GameDetail | null
  analyzing: boolean
  progress: AnalysisProgress | null
  error: string | null
  onAnalyze: () => void
}

const GLYPH_ROWS: { judgment: Judgment; label: string; glyph: string }[] = [
  { judgment: 'inaccuracy', label: 'Inaccuracies', glyph: '?!' },
  { judgment: 'mistake', label: 'Mistakes', glyph: '?' },
  { judgment: 'blunder', label: 'Blunders', glyph: '??' },
]

function SideColumn({ name, summary }: { name: string; summary: SideSummary }) {
  return (
    <div className="flex-1">
      <p className="truncate text-xs text-neutral-500">{name}</p>
      <p className="text-2xl font-bold tabular-nums text-neutral-100">
        {summary.accuracy !== null ? `${summary.accuracy.toFixed(1)}%` : '—'}
      </p>
      <dl className="mt-1 space-y-0.5">
        {GLYPH_ROWS.map(({ judgment, label, glyph }) => (
          <div key={judgment} className="flex justify-between text-xs">
            <dt className="text-neutral-400">
              <span
                className="mr-1 font-mono font-bold"
                style={{ color: JUDGMENT_COLOR[judgment] }}
              >
                {glyph}
              </span>
              {label}
            </dt>
            <dd className="tabular-nums text-neutral-200">
              {summary.counts[judgment]}
            </dd>
          </div>
        ))}
      </dl>
    </div>
  )
}

export default function AnalysisPanel({
  game,
  analyzing,
  progress,
  error,
  onAnalyze,
}: AnalysisPanelProps) {
  if (!game) return null
  const analyzed = game.moves.some((m) => m.evaluation)
  const summary = analyzed ? accuracySummary(game.moves) : null
  const pct =
    progress && progress.total > 0
      ? Math.round((progress.ply / progress.total) * 100)
      : 0

  return (
    <div className="flex flex-col gap-3">
      {summary ? (
        <div className="flex gap-4">
          <SideColumn name={game.white ?? 'White'} summary={summary.white} />
          <SideColumn name={game.black ?? 'Black'} summary={summary.black} />
        </div>
      ) : (
        <p className="text-sm text-neutral-500">
          Not analyzed yet — run Stockfish to get accuracy and move judgments.
        </p>
      )}
      {analyzing ? (
        <div>
          <div className="h-1.5 overflow-hidden rounded bg-neutral-800">
            <div
              className="h-full bg-neutral-200 transition-all"
              style={{ width: `${pct}%` }}
            />
          </div>
          <p className="mt-1 text-xs text-neutral-500">
            Evaluating… {progress ? `${progress.ply}/${progress.total}` : ''}
          </p>
        </div>
      ) : (
        <button
          onClick={onAnalyze}
          className="self-start rounded bg-neutral-200 px-3 py-1.5 text-sm font-semibold text-neutral-900 hover:bg-white"
        >
          {analyzed ? 'Re-analyze' : 'Analyze with Stockfish'}
        </button>
      )}
      {error && <p className="text-sm text-[#d03b3b]">{error}</p>}
    </div>
  )
}

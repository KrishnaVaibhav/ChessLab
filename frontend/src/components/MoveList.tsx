import { useEffect, useRef } from 'react'
import { JUDGMENT_COLOR, JUDGMENT_GLYPH } from '../lib/chess'
import type { GameMove } from '../types'

interface MoveListProps {
  moves: GameMove[]
  currentPly: number
  onSelect: (ply: number) => void
}

function MoveButton({
  move,
  current,
  onSelect,
}: {
  move: GameMove
  current: boolean
  onSelect: (ply: number) => void
}) {
  const ref = useRef<HTMLButtonElement>(null)
  useEffect(() => {
    if (current) ref.current?.scrollIntoView({ block: 'nearest' })
  }, [current])
  const judgment = move.evaluation?.judgment ?? 'ok'
  const glyph = JUDGMENT_GLYPH[judgment]
  return (
    <button
      ref={ref}
      onClick={() => onSelect(move.ply)}
      className={`rounded px-1.5 py-0.5 text-left font-mono text-sm ${
        current
          ? 'bg-neutral-200 text-neutral-900'
          : 'text-neutral-200 hover:bg-neutral-800'
      }`}
    >
      {move.san}
      {glyph && (
        <span
          className="ml-0.5 font-bold"
          style={current ? undefined : { color: JUDGMENT_COLOR[judgment] }}
        >
          {glyph}
        </span>
      )}
    </button>
  )
}

export default function MoveList({ moves, currentPly, onSelect }: MoveListProps) {
  if (moves.length === 0) {
    return (
      <p className="px-2 py-4 text-sm text-neutral-500">
        Import a game to see its moves.
      </p>
    )
  }
  const rows: { no: number; white?: GameMove; black?: GameMove }[] = []
  for (const m of moves) {
    const no = Math.ceil(m.ply / 2)
    let row = rows[rows.length - 1]
    if (!row || row.no !== no) {
      row = { no }
      rows.push(row)
    }
    if (m.ply % 2 === 1) row.white = m
    else row.black = m
  }
  return (
    <div className="max-h-64 overflow-y-auto">
      <div className="grid grid-cols-[2.5rem_1fr_1fr] items-center gap-x-1 gap-y-0.5 pr-2">
        {rows.map((row) => (
          <div key={row.no} className="contents">
            <span className="text-right font-mono text-xs text-neutral-500">
              {row.no}.
            </span>
            {row.white ? (
              <MoveButton
                move={row.white}
                current={currentPly === row.white.ply}
                onSelect={onSelect}
              />
            ) : (
              <span className="px-1.5 text-neutral-600">…</span>
            )}
            {row.black ? (
              <MoveButton
                move={row.black}
                current={currentPly === row.black.ply}
                onSelect={onSelect}
              />
            ) : (
              <span />
            )}
          </div>
        ))}
      </div>
    </div>
  )
}

import { useLayoutEffect, useRef, useState } from 'react'
import { JUDGMENT_COLOR, JUDGMENT_GLYPH, evalLabel } from '../lib/chess'
import type { GameMove } from '../types'

interface EvalGraphProps {
  moves: GameMove[]
  currentPly: number
  onSelect: (ply: number) => void
}

const H = 96

export default function EvalGraph({ moves, currentPly, onSelect }: EvalGraphProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const [width, setWidth] = useState(0)
  const [hoverPly, setHoverPly] = useState<number | null>(null)

  useLayoutEffect(() => {
    const el = containerRef.current
    if (!el) return
    const ro = new ResizeObserver(() => setWidth(el.clientWidth))
    ro.observe(el)
    setWidth(el.clientWidth)
    return () => ro.disconnect()
  }, [])

  const evaluated = moves.filter((m) => m.evaluation)
  if (evaluated.length === 0) {
    return (
      <div className="flex h-24 items-center justify-center rounded bg-neutral-900 text-sm text-neutral-500">
        Run analysis to see the eval graph.
      </div>
    )
  }

  const n = moves.length
  // Point 0 is the start position (~50% before any move); the ply-0 eval is
  // not persisted, matching the accuracy baseline in lib/chess.ts.
  const x = (ply: number) => (n === 0 ? 0 : (ply / n) * width)
  const y = (winPct: number) => H - (winPct / 100) * H
  const winAt = (ply: number) =>
    ply === 0 ? 50 : (moves[ply - 1]?.evaluation?.win_pct ?? 50)

  const points: [number, number][] = [[x(0), y(50)]]
  for (const m of moves) {
    points.push([x(m.ply), y(m.evaluation ? m.evaluation.win_pct : 50)])
  }
  const line = points.map(([px, py]) => `${px},${py}`).join(' ')
  const area = `${line} ${width},${H} 0,${H}`

  const plyFromEvent = (e: React.MouseEvent) => {
    const rect = containerRef.current!.getBoundingClientRect()
    const ply = Math.round(((e.clientX - rect.left) / rect.width) * n)
    return Math.max(0, Math.min(n, ply))
  }

  const hovered = hoverPly !== null && hoverPly > 0 ? moves[hoverPly - 1] : null
  const tooltipLeft = hoverPly !== null ? x(hoverPly) : 0
  const flip = width > 0 && tooltipLeft > width - 120

  return (
    <div
      ref={containerRef}
      className="relative h-24 cursor-pointer select-none overflow-hidden rounded bg-neutral-900"
      onMouseMove={(e) => setHoverPly(plyFromEvent(e))}
      onMouseLeave={() => setHoverPly(null)}
      onClick={(e) => onSelect(plyFromEvent(e))}
    >
      {width > 0 && (
        <svg width={width} height={H} className="block">
          {/* white's share, filled from below; the dark surface is black's */}
          <polygon points={area} fill="#e5e5e5" />
          <polyline
            points={line}
            fill="none"
            stroke="#a3a3a3"
            strokeWidth="2"
          />
          <line
            x1={0}
            y1={H / 2}
            x2={width}
            y2={H / 2}
            stroke="#525252"
            strokeWidth="1"
            strokeDasharray="3 4"
          />
          {evaluated
            .filter((m) => m.evaluation!.judgment !== 'ok')
            .map((m) => (
              <circle
                key={m.ply}
                cx={x(m.ply)}
                cy={y(m.evaluation!.win_pct)}
                r="4"
                fill={JUDGMENT_COLOR[m.evaluation!.judgment]}
                stroke="#171717"
                strokeWidth="2"
              />
            ))}
          {hoverPly !== null && (
            <line
              x1={x(hoverPly)}
              y1={0}
              x2={x(hoverPly)}
              y2={H}
              stroke="#737373"
              strokeWidth="1"
              strokeDasharray="2 3"
            />
          )}
          <line
            x1={x(currentPly)}
            y1={0}
            x2={x(currentPly)}
            y2={H}
            stroke="#fafafa"
            strokeWidth="1.5"
          />
        </svg>
      )}
      {hoverPly !== null && (
        <div
          className="pointer-events-none absolute top-1 rounded bg-neutral-800/95 px-2 py-1 font-mono text-xs text-neutral-100 shadow"
          style={flip ? { right: width - tooltipLeft + 6 } : { left: tooltipLeft + 6 }}
        >
          {hovered ? (
            <>
              {Math.ceil(hovered.ply / 2)}
              {hovered.ply % 2 === 1 ? '. ' : '… '}
              {hovered.san}
              {hovered.evaluation && (
                <span
                  className="font-bold"
                  style={{ color: JUDGMENT_COLOR[hovered.evaluation.judgment] || undefined }}
                >
                  {JUDGMENT_GLYPH[hovered.evaluation.judgment]}
                </span>
              )}{' '}
              <span className="text-neutral-400">
                {evalLabel(hovered.evaluation)} · {winAt(hovered.ply).toFixed(0)}%
              </span>
            </>
          ) : (
            'Start'
          )}
        </div>
      )}
    </div>
  )
}

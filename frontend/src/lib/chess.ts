import type { GameMove, Judgment, MoveEvaluation } from '../types'

export const START_FEN =
  'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'

export function uciSquares(uci: string) {
  return { from: uci.slice(0, 2), to: uci.slice(2, 4) }
}

export function evalLabel(
  ev: Pick<MoveEvaluation, 'score_cp' | 'mate_in'> | null | undefined,
): string {
  if (!ev) return '—'
  if (ev.mate_in !== null) return `M${Math.abs(ev.mate_in)}`
  if (ev.score_cp === null) return '—'
  const pawns = ev.score_cp / 100
  return `${pawns > 0 ? '+' : ''}${pawns.toFixed(2)}`
}

export const JUDGMENT_GLYPH: Record<Judgment, string> = {
  ok: '',
  inaccuracy: '?!',
  mistake: '?',
  blunder: '??',
}

// Status palette steps (warning / serious / critical), all ≥3:1 on the dark
// surface; always rendered next to the ?!/?/?? glyph, never color alone.
export const JUDGMENT_COLOR: Record<Judgment, string> = {
  ok: '',
  inaccuracy: '#fab219',
  mistake: '#ec835a',
  blunder: '#d03b3b',
}

export interface SideSummary {
  accuracy: number | null
  counts: Record<Judgment, number>
}

// Mirrors the backend lichess accuracy model. The ply-0 evaluation is not
// persisted, so the first move's baseline uses the 50% standard-start
// approximation — off by under a percent for normal games.
export function accuracySummary(moves: GameMove[]): {
  white: SideSummary
  black: SideSummary
} {
  const empty = (): Record<Judgment, number> => ({
    ok: 0,
    inaccuracy: 0,
    mistake: 0,
    blunder: 0,
  })
  const counts = { white: empty(), black: empty() }
  const accs: Record<'white' | 'black', number[]> = { white: [], black: [] }
  let prevWinWhite = 50
  for (const m of moves) {
    const ev = m.evaluation
    if (!ev) continue
    const side = m.ply % 2 === 1 ? 'white' : 'black'
    const before = side === 'white' ? prevWinWhite : 100 - prevWinWhite
    const after = side === 'white' ? ev.win_pct : 100 - ev.win_pct
    const drop = Math.max(0, before - after)
    counts[side][ev.judgment] += 1
    accs[side].push(
      Math.max(0, Math.min(100, 103.1668 * Math.exp(-0.04354 * drop) - 3.1669)),
    )
    prevWinWhite = ev.win_pct
  }
  const avg = (xs: number[]) =>
    xs.length ? xs.reduce((a, b) => a + b, 0) / xs.length : null
  return {
    white: { accuracy: avg(accs.white), counts: counts.white },
    black: { accuracy: avg(accs.black), counts: counts.black },
  }
}

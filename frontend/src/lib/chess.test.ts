import { describe, expect, it } from 'vitest'
import type { GameMove, MoveEvaluation } from '../types'
import {
  JUDGMENT_COLOR,
  JUDGMENT_GLYPH,
  accuracySummary,
  evalLabel,
  uciSquares,
} from './chess'

describe('uciSquares', () => {
  it('splits from/to squares', () => {
    expect(uciSquares('e2e4')).toEqual({ from: 'e2', to: 'e4' })
  })

  it('ignores the promotion suffix', () => {
    expect(uciSquares('e7e8q')).toEqual({ from: 'e7', to: 'e8' })
  })
})

describe('evalLabel', () => {
  const ev = (
    score_cp: number | null,
    mate_in: number | null = null,
  ): Pick<MoveEvaluation, 'score_cp' | 'mate_in'> => ({ score_cp, mate_in })

  it('formats centipawns as signed pawns', () => {
    expect(evalLabel(ev(137))).toBe('+1.37')
    expect(evalLabel(ev(-50))).toBe('-0.50')
    expect(evalLabel(ev(0))).toBe('0.00')
  })

  it('formats mate scores as M<n> regardless of sign', () => {
    expect(evalLabel(ev(null, 3))).toBe('M3')
    expect(evalLabel(ev(null, -2))).toBe('M2')
  })

  it('falls back to em dash when nothing is known', () => {
    expect(evalLabel(null)).toBe('—')
    expect(evalLabel(undefined)).toBe('—')
    expect(evalLabel(ev(null))).toBe('—')
  })
})

describe('judgment display', () => {
  it('pairs every colored judgment with a glyph (never color alone)', () => {
    for (const j of ['inaccuracy', 'mistake', 'blunder'] as const) {
      expect(JUDGMENT_GLYPH[j]).not.toBe('')
      expect(JUDGMENT_COLOR[j]).toMatch(/^#[0-9a-f]{6}$/)
    }
    expect(JUDGMENT_GLYPH.ok).toBe('')
  })
})

describe('accuracySummary', () => {
  const move = (
    ply: number,
    win_pct: number,
    judgment: MoveEvaluation['judgment'] = 'ok',
  ): GameMove => ({
    ply,
    san: 'e4',
    uci: 'e2e4',
    fen_after: '',
    evaluation: {
      depth: 18,
      score_cp: 0,
      mate_in: null,
      best_move_uci: null,
      judgment,
      win_pct,
    },
  })

  it('returns null accuracy and zero counts with no evaluations', () => {
    const { white, black } = accuracySummary([
      { ply: 1, san: 'e4', uci: 'e2e4', fen_after: '', evaluation: null },
    ])
    expect(white.accuracy).toBeNull()
    expect(black.accuracy).toBeNull()
    expect(white.counts).toEqual({ ok: 0, inaccuracy: 0, mistake: 0, blunder: 0 })
  })

  it('gives ~100% when no win% is ever lost', () => {
    const { white, black } = accuracySummary([move(1, 50), move(2, 50)])
    expect(white.accuracy).toBeCloseTo(100, 1)
    expect(black.accuracy).toBeCloseTo(100, 1)
  })

  it('penalizes only the side whose win% dropped', () => {
    // Black's move takes White 50 → 90: a 40-point drop for Black.
    const { white, black } = accuracySummary([move(1, 50), move(2, 90)])
    expect(white.accuracy).toBeCloseTo(100, 1)
    expect(black.accuracy).toBeLessThan(30)
  })

  it('tallies judgment counts per side', () => {
    const { white, black } = accuracySummary([
      move(1, 50, 'ok'),
      move(2, 80, 'blunder'),
      move(3, 75, 'inaccuracy'),
    ])
    expect(white.counts.ok).toBe(1)
    expect(white.counts.inaccuracy).toBe(1)
    expect(black.counts.blunder).toBe(1)
    expect(black.counts.ok).toBe(0)
  })

  it('keeps accuracy within [0, 100] even on catastrophic swings', () => {
    const { white } = accuracySummary([move(1, 0)])
    expect(white.accuracy).toBeGreaterThanOrEqual(0)
    expect(white.accuracy).toBeLessThanOrEqual(100)
  })

  it('skips unevaluated moves without corrupting the baseline', () => {
    const gap: GameMove = { ply: 2, san: 'e5', uci: 'e7e5', fen_after: '', evaluation: null }
    const { white } = accuracySummary([move(1, 55), gap, move(3, 55)])
    expect(white.accuracy).toBeCloseTo(100, 1)
  })
})

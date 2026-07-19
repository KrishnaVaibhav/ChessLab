export type Judgment = 'ok' | 'inaccuracy' | 'mistake' | 'blunder'

export interface GameSummary {
  id: number
  white: string | null
  black: string | null
  result: string | null
  event: string | null
  date: string | null
  eco: string | null
}

export interface MoveEvaluation {
  depth: number
  score_cp: number | null
  mate_in: number | null
  best_move_uci: string | null
  judgment: Judgment
  win_pct: number
}

export interface GameMove {
  ply: number
  san: string
  uci: string
  fen_after: string
  evaluation: MoveEvaluation | null
}

export interface GameDetail extends GameSummary {
  moves: GameMove[]
}

export interface AnalysisProgress {
  ply: number
  total: number
}

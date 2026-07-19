import type { CSSProperties } from 'react'
import { Chessboard } from 'react-chessboard'
import { uciSquares } from '../lib/chess'

interface BoardProps {
  fen: string
  lastMoveUci: string | null
  bestMoveUci: string | null
  orientation: 'white' | 'black'
}

const HIGHLIGHT: CSSProperties = { backgroundColor: 'rgba(250, 178, 25, 0.35)' }

export default function Board({
  fen,
  lastMoveUci,
  bestMoveUci,
  orientation,
}: BoardProps) {
  const squareStyles: Record<string, CSSProperties> = {}
  if (lastMoveUci) {
    const { from, to } = uciSquares(lastMoveUci)
    squareStyles[from] = HIGHLIGHT
    squareStyles[to] = HIGHLIGHT
  }
  const arrows = bestMoveUci
    ? [
        {
          startSquare: uciSquares(bestMoveUci).from,
          endSquare: uciSquares(bestMoveUci).to,
          color: '#0ca30c',
        },
      ]
    : []

  return (
    <Chessboard
      options={{
        position: fen,
        boardOrientation: orientation,
        allowDragging: false,
        arrows,
        squareStyles,
        animationDurationInMs: 150,
        darkSquareStyle: { backgroundColor: '#4b7399' },
        lightSquareStyle: { backgroundColor: '#e8edf9' },
        boardStyle: { borderRadius: '4px', overflow: 'hidden' },
      }}
    />
  )
}

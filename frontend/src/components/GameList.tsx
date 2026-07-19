import type { GameSummary } from '../types'

interface GameListProps {
  games: GameSummary[]
  selectedId: number | null
  onSelect: (id: number) => void
}

export default function GameList({ games, selectedId, onSelect }: GameListProps) {
  if (games.length === 0) return null
  return (
    <ul className="max-h-40 divide-y divide-neutral-800 overflow-y-auto rounded border border-neutral-800">
      {games.map((g) => (
        <li key={g.id}>
          <button
            onClick={() => onSelect(g.id)}
            className={`flex w-full items-baseline justify-between gap-2 px-3 py-2 text-left text-sm ${
              g.id === selectedId
                ? 'bg-neutral-800 text-neutral-100'
                : 'text-neutral-300 hover:bg-neutral-900'
            }`}
          >
            <span className="truncate">
              {g.white ?? '?'} — {g.black ?? '?'}
            </span>
            <span className="shrink-0 font-mono text-xs text-neutral-500">
              {g.result ?? '*'}
              {g.eco ? ` · ${g.eco}` : ''}
            </span>
          </button>
        </li>
      ))}
    </ul>
  )
}

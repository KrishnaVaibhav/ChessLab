import type { AnalysisProgress, GameDetail, GameSummary } from './types'

async function json<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const body = await res.json().catch(() => null)
    const detail = body && typeof body.detail === 'string' ? body.detail : null
    throw new Error(detail ?? `${res.status} ${res.statusText}`)
  }
  return res.json() as Promise<T>
}

export async function importPgn(pgn: string) {
  return json<{ games: { id: number; move_count: number }[] }>(
    await fetch('/api/games', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ pgn }),
    }),
  )
}

export async function listGames() {
  return json<{ games: GameSummary[] }>(await fetch('/api/games'))
}

export async function getGame(id: number) {
  return json<GameDetail>(await fetch(`/api/games/${id}`))
}

export function analyzeGameStream(
  id: number,
  handlers: {
    onProgress: (p: AnalysisProgress) => void
    onResult: () => void
    onError: (message: string) => void
  },
): () => void {
  const source = new EventSource(`/api/analysis/games/${id}/stream`)
  let finished = false
  source.addEventListener('progress', (e) => {
    handlers.onProgress(JSON.parse((e as MessageEvent).data) as AnalysisProgress)
  })
  source.addEventListener('result', () => {
    finished = true
    source.close()
    handlers.onResult()
  })
  source.onerror = () => {
    source.close()
    if (!finished) handlers.onError('Analysis stream failed — is Stockfish installed?')
  }
  return () => source.close()
}

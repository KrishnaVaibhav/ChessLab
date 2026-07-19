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

export interface CoachHealth {
  available: boolean
  models: string[]
  default_model: string
}

export async function coachHealth() {
  return json<CoachHealth>(await fetch('/api/coach/health'))
}

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
}

// SSE over POST, so EventSource doesn't fit — parse the stream by hand.
export async function coachExplain(
  body: {
    game_id: number
    ply: number
    model?: string
    messages?: ChatMessage[]
  },
  onDelta: (text: string) => void,
  signal?: AbortSignal,
): Promise<void> {
  const res = await fetch('/api/coach/explain', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
    signal,
  })
  if (!res.ok || !res.body) {
    const detail = await res.json().catch(() => null)
    throw new Error(
      detail && typeof detail.detail === 'string'
        ? detail.detail
        : `${res.status} ${res.statusText}`,
    )
  }
  const reader = res.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  for (;;) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    const events = buffer.split('\n\n')
    buffer = events.pop() ?? ''
    for (const event of events) {
      const isError = event.includes('event: error')
      const dataLine = event.split('\n').find((l) => l.startsWith('data: '))
      if (!dataLine) continue
      const payload = JSON.parse(dataLine.slice(6))
      if (isError) throw new Error(payload.detail ?? 'Coach stream failed')
      if (payload.delta) onDelta(payload.delta)
    }
  }
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

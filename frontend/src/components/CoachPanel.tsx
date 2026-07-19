import { useCallback, useEffect, useRef, useState } from 'react'
import { coachExplain, coachHealth } from '../api'
import type { ChatMessage, CoachHealth } from '../api'
import type { GameDetail } from '../types'

interface CoachPanelProps {
  game: GameDetail
  ply: number
}

export default function CoachPanel({ game, ply }: CoachPanelProps) {
  const [health, setHealth] = useState<CoachHealth | null>(null)
  const [model, setModel] = useState<string | undefined>(undefined)
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const abortRef = useRef<AbortController | null>(null)
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    coachHealth()
      .then((h) => {
        setHealth(h)
        // The select must show the model actually used: fall back to the
        // first installed model when the configured default isn't pulled.
        setModel(
          h.models.includes(h.default_model) ? h.default_model : h.models[0],
        )
      })
      .catch(() => setHealth(null))
  }, [])

  // A new game means a new conversation.
  useEffect(() => {
    setMessages([])
    setError(null)
    abortRef.current?.abort()
  }, [game.id])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ block: 'nearest' })
  }, [messages])

  const ask = useCallback(
    async (question: string | null) => {
      if (busy || ply === 0) return
      setBusy(true)
      setError(null)
      const history: ChatMessage[] = question
        ? [...messages, { role: 'user', content: question }]
        : []
      setMessages([...history, { role: 'assistant', content: '' }])
      const controller = new AbortController()
      abortRef.current = controller
      try {
        await coachExplain(
          {
            game_id: game.id,
            ply,
            model,
            messages: question ? history : undefined,
          },
          (delta) =>
            setMessages((prev) => {
              const next = [...prev]
              const last = next[next.length - 1]
              next[next.length - 1] = {
                role: 'assistant',
                content: (last?.content ?? '') + delta,
              }
              return next
            }),
          controller.signal,
        )
      } catch (e) {
        if (!controller.signal.aborted) {
          setError(e instanceof Error ? e.message : 'Coach request failed')
          setMessages((prev) =>
            prev[prev.length - 1]?.content === '' ? prev.slice(0, -1) : prev,
          )
        }
      } finally {
        setBusy(false)
      }
    },
    [busy, ply, messages, game.id, model],
  )

  const submit = () => {
    const q = input.trim()
    if (!q) return
    setInput('')
    ask(q)
  }

  if (health && !health.available) {
    return (
      <p className="text-sm text-neutral-500">
        Ollama not detected. Install it from{' '}
        <span className="text-neutral-300">ollama.com</span>, then{' '}
        <code className="rounded bg-neutral-800 px-1">
          ollama pull {health.default_model}
        </code>{' '}
        and reload.
      </p>
    )
  }

  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-center gap-2">
        <button
          onClick={() => ask(null)}
          disabled={busy || ply === 0}
          className="rounded bg-neutral-200 px-3 py-1.5 text-sm font-semibold text-neutral-900 hover:bg-white disabled:opacity-40"
          title={ply === 0 ? 'Pick a move first' : 'Explain the current position'}
        >
          Explain this position
        </button>
        {health && health.models.length > 0 && (
          <select
            value={model ?? health.models[0]}
            onChange={(e) => setModel(e.target.value)}
            className="ml-auto rounded border border-neutral-700 bg-neutral-900 px-2 py-1 text-xs text-neutral-300"
            title="Ollama model"
          >
            {health.models.map((m) => (
              <option key={m} value={m}>
                {m}
              </option>
            ))}
          </select>
        )}
      </div>
      {messages.length > 0 && (
        <div className="flex max-h-72 flex-col gap-2 overflow-y-auto rounded bg-neutral-900 p-2">
          {messages.map((m, i) => (
            <div
              key={i}
              className={
                m.role === 'user'
                  ? 'self-end rounded-lg bg-neutral-700 px-3 py-1.5 text-sm text-neutral-100'
                  : 'self-start whitespace-pre-wrap rounded-lg bg-neutral-800 px-3 py-1.5 text-sm text-neutral-200'
              }
            >
              {m.content || (busy && i === messages.length - 1 ? '…' : '')}
            </div>
          ))}
          <div ref={bottomRef} />
        </div>
      )}
      <div className="flex gap-2">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && submit()}
          placeholder={ply === 0 ? 'Navigate to a move first…' : 'Ask the coach…'}
          disabled={busy || ply === 0}
          className="min-w-0 flex-1 rounded border border-neutral-700 bg-neutral-900 px-2 py-1.5 text-sm text-neutral-200 placeholder:text-neutral-600 focus:border-neutral-500 focus:outline-none disabled:opacity-50"
        />
        <button
          onClick={submit}
          disabled={busy || ply === 0 || !input.trim()}
          className="rounded border border-neutral-700 px-3 py-1.5 text-sm text-neutral-300 hover:border-neutral-500 disabled:opacity-40"
        >
          Ask
        </button>
      </div>
      {error && <p className="text-sm text-[#d03b3b]">{error}</p>}
    </div>
  )
}

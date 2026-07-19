import { useState } from 'react'

interface PgnUploadProps {
  onImport: (pgn: string) => Promise<void>
}

export default function PgnUpload({ onImport }: PgnUploadProps) {
  const [pgn, setPgn] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const submit = async () => {
    if (!pgn.trim()) return
    setBusy(true)
    setError(null)
    try {
      await onImport(pgn)
      setPgn('')
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Import failed')
    } finally {
      setBusy(false)
    }
  }

  const onFile = async (file: File | undefined) => {
    if (file) setPgn(await file.text())
  }

  return (
    <div className="flex flex-col gap-2">
      <textarea
        value={pgn}
        onChange={(e) => setPgn(e.target.value)}
        placeholder={'Paste a PGN here…\n\n1. e4 e5 2. Nf3 …'}
        rows={4}
        className="w-full resize-y rounded border border-neutral-700 bg-neutral-900 p-2 font-mono text-xs text-neutral-200 placeholder:text-neutral-600 focus:border-neutral-500 focus:outline-none"
      />
      <div className="flex items-center gap-2">
        <button
          onClick={submit}
          disabled={busy || !pgn.trim()}
          className="rounded bg-neutral-200 px-3 py-1.5 text-sm font-semibold text-neutral-900 hover:bg-white disabled:opacity-40"
        >
          {busy ? 'Importing…' : 'Import'}
        </button>
        <label className="cursor-pointer rounded border border-neutral-700 px-3 py-1.5 text-sm text-neutral-300 hover:border-neutral-500">
          Open .pgn file
          <input
            type="file"
            accept=".pgn,text/plain"
            className="hidden"
            onChange={(e) => onFile(e.target.files?.[0])}
          />
        </label>
      </div>
      {error && <p className="text-sm text-[#d03b3b]">{error}</p>}
    </div>
  )
}

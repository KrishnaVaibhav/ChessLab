interface EvalBarProps {
  winPct: number | null
  label: string
  orientation: 'white' | 'black'
}

export default function EvalBar({ winPct, label, orientation }: EvalBarProps) {
  const white = winPct ?? 50
  const whiteAtBottom = orientation === 'white'
  return (
    <div
      className="relative w-5 shrink-0 overflow-hidden rounded bg-neutral-800"
      title={`White ${white.toFixed(1)}%`}
    >
      <div
        className="absolute inset-x-0 bg-neutral-200 transition-all duration-300"
        style={{
          height: `${white}%`,
          [whiteAtBottom ? 'bottom' : 'top']: 0,
        }}
      />
      <span
        className={`absolute inset-x-0.5 rounded-sm bg-neutral-200/90 text-center text-[9px] font-semibold text-neutral-900 ${
          whiteAtBottom ? 'bottom-1' : 'top-1'
        }`}
      >
        {label}
      </span>
    </div>
  )
}

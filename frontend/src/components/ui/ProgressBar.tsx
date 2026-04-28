'use client'

interface Props {
  value: number     // 0 ~ 100
  animated?: boolean
  className?: string
}

export default function ProgressBar({ value, animated, className = '' }: Props) {
  const clamped = Math.min(100, Math.max(0, value))

  return (
    <div
      className={`w-full h-1.5 rounded-full overflow-hidden ${className}`}
      style={{ background: 'var(--surface-3)' }}
    >
      <div
        className="h-full rounded-full transition-all duration-700 ease-out"
        style={{
          width: `${clamped}%`,
          background: animated
            ? 'linear-gradient(90deg, #6366f1, #8b5cf6, #a855f7)'
            : 'linear-gradient(90deg, #6366f1, #8b5cf6)',
          backgroundSize: animated ? '200% 100%' : '100% 100%',
          animation: animated ? 'shimmer 2s infinite' : undefined,
        }}
      />
    </div>
  )
}

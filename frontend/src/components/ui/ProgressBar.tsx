'use client'

interface Props {
  value: number     // 0 ~ 100
  animated?: boolean
  className?: string
}

export default function ProgressBar({ value, animated, className = '' }: Props) {
  return (
    <div className={`w-full h-2 bg-gray-100 rounded-full overflow-hidden ${className}`}>
      <div
        className={`h-full bg-[#1a1a2e] rounded-full transition-all duration-500 ${
          animated ? 'animate-pulse' : ''
        }`}
        style={{ width: `${Math.min(100, Math.max(0, value))}%` }}
      />
    </div>
  )
}

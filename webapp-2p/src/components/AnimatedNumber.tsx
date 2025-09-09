import React, { useEffect, useRef, useState } from 'react'

export default function AnimatedNumber({ value, className }: { value: number, className?: string }) {
  const [pulse, setPulse] = useState(false)
  const prev = useRef(value)
  useEffect(() => {
    if (prev.current !== value) {
      setPulse(true)
      prev.current = value
      const t = setTimeout(() => setPulse(false), 320)
      return () => clearTimeout(t)
    }
  }, [value])
  return <span className={`count ${className || ''} ${pulse ? 'pulse' : ''}`}>{value}</span>
}


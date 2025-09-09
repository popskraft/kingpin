import React from 'react'

export default function OpponentHandThumbnails({ count }: { count: number }) {
  const n = Math.max(0, count)
  const shown = Math.min(n, 12)
  return (
    <div className="opp-hand" aria-label={`Opponent hand: ${n} cards`}>
      <div className="opp-hand-title">Opponent Hand ({n})</div>
      <div className="opp-hand-row">
        {Array.from({ length: shown }).map((_, i) => (
          <div key={i} className="opp-thumb" title="Face-down card" />
        ))}
        {n > shown ? <div className="opp-extra">+{n - shown}</div> : null}
      </div>
    </div>
  )
}


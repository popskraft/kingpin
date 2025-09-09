import React from 'react'

type TokenDrag = { kind: 'money' | 'shield', owner: 'you' | 'opponent' | 'bank', slotIndex?: number }

export default function MoneyThumbnails({ count, draggableTokens = false, owner = 'you' }:
  { count: number, draggableTokens?: boolean, owner?: 'you' | 'bank' }): JSX.Element {
  const n = Math.max(0, count)
  const shown = Math.min(n, 10)
  return (
    <div className="money-list">
      {Array.from({ length: shown }).map((_, i) => (
        <div
          key={i}
          className="money-token"
          draggable={draggableTokens}
          onDragStart={draggableTokens ? (e) => {
            const payload: TokenDrag = { kind: 'money', owner }
            e.dataTransfer.setData('application/x-token', JSON.stringify(payload))
          } : undefined}
          title={draggableTokens ? 'Drag to a card to add a shield' : undefined}
        />
      ))}
      {n > shown ? <div className="money-extra">+{n - shown}</div> : null}
    </div>
  )
}


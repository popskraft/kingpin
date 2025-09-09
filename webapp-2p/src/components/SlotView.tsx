import React from 'react'
import type { Slot, Card } from '../types'
import CardView from './CardView'

type DragPayload = { from: 'hand' | 'slot' | 'shelf'; fromIndex: number }
type TokenDrag = { kind: 'money' | 'shield', owner: 'you' | 'opponent' | 'bank', slotIndex?: number }

export default function SlotView({ slot, onFlip, onDropToSlot, index, editable, owner, onTokenPlus, onTokenPlusFromBank, onTokenMinus, canAddShield, canRemoveShield, onReceiveShieldFrom, extraClassName, onClickCard, onHoverStart, onHoverEnd, onDragAnyStart, onDragAnyEnd, onSlotDragStart, bonusHp = 0, bonusD = 0, bonusR = 0, pairInfo = null }:
  { slot: Slot, index: number, editable?: boolean, owner: 'you' | 'opponent', onFlip?: () => void, onDropToSlot?: (from: DragPayload) => void, onTokenPlus?: () => void, onTokenPlusFromBank?: () => void, onTokenMinus?: () => void, canAddShield?: boolean, canRemoveShield?: boolean, onReceiveShieldFrom?: (srcIndex: number) => void, extraClassName?: string, onClickCard?: () => void, onHoverStart?: () => void, onHoverEnd?: () => void, onDragAnyStart?: () => void, onDragAnyEnd?: () => void, onSlotDragStart?: (index: number) => void, bonusHp?: number, bonusD?: number, bonusR?: number, pairInfo?: { hp: number, d: number, r: number } | null }): JSX.Element {
  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
  }
  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    const data = e.dataTransfer.getData('application/json')
    if (data) {
      try {
        const from = JSON.parse(data) as DragPayload
        onDropToSlot?.(from)
        return
      } catch {}
    }
    // Token movement
    const tokenData = e.dataTransfer.getData('application/x-token')
    if (tokenData) {
      try {
        const tok = JSON.parse(tokenData) as TokenDrag
        // Money -> Shield on your slot
        if (tok.kind === 'money' && owner === 'you') {
          if (tok.owner === 'you') onTokenPlus?.()
          else if (tok.owner === 'bank') onTokenPlusFromBank?.()
        }
        // Shield moved between your slots
        if (tok.kind === 'shield' && owner === 'you' && typeof tok.slotIndex === 'number') {
          if (tok.slotIndex !== index) {
            onReceiveShieldFrom?.(tok.slotIndex)
          }
        }
      } catch {}
    }
  }
  const draggable = editable && !!slot.card
  const handleDragStart = (e: React.DragEvent) => {
    onDragAnyStart?.()
    onSlotDragStart?.(index)
    e.dataTransfer.setData('application/json', JSON.stringify({ from: 'slot', fromIndex: index }))
  }
  return (
    <div className={`slot ${extraClassName || ''}`} onDragOver={handleDragOver} onDrop={handleDrop}>
      <div className="shield-thumbs" title={`Shield defenders: ${Math.min(4, Math.max(0, slot.muscles))}`} onDragOver={(e) => e.preventDefault()}>
        {Array.from({ length: 4 }).map((_, i) => {
          const filled = i < Math.min(4, Math.max(0, slot.muscles))
          return (
            <div
              key={i}
              className={`shield-thumb ${filled ? 'filled' : 'empty'}`}
              aria-label={filled ? 'defender' : 'placeholder'}
              draggable={filled}
              onDragStart={filled ? (e) => {
                const payload: TokenDrag = { kind: 'shield', owner, slotIndex: index }
                e.dataTransfer.setData('application/x-token', JSON.stringify(payload))
              } : undefined}
            />
          )
        })}
      </div>
      <div className="slot-header">
        {editable ? (
          <div className="shield-compact">
            <button className="mini-btn" onClick={onTokenMinus} title="-shield" disabled={!(canRemoveShield ?? true) || (slot.muscles ?? 0) <= 0}>−</button>
            <div className="shield-chip" title="Shield tokens"><span className="chip-icon">🛡</span><span className="chip-count">{slot.muscles}</span></div>
            <button className="mini-btn" onClick={onTokenPlus} title="+shield" disabled={!(canAddShield ?? true)}>＋</button>
          </div>
        ) : (
          <div className="shield-compact readonly">
            <div className="shield-chip" title="Shield tokens"><span className="chip-icon">🛡</span><span className="chip-count">{slot.muscles}</span></div>
          </div>
        )}
      </div>
      <div className="slot-inner">
        <div className="card-wrap" draggable={draggable} onDragStart={draggable ? handleDragStart : undefined} onDragEnd={onDragAnyEnd} onDoubleClick={onFlip} onClick={onClickCard} onMouseEnter={onHoverStart} onMouseLeave={onHoverEnd}>
          <CardView card={slot.card as Card | null} faceUp={slot.face_up} bonusHp={bonusHp} bonusD={bonusD} bonusR={bonusR} pairInfo={pairInfo} />
        </div>
      </div>
    </div>
  )
}


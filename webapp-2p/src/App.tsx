import React, { useEffect, useMemo, useRef, useState } from 'react'
import { io, Socket } from 'socket.io-client'
import type { ViewState, Card, Slot, LogEntry, AttackMeta } from './types'

const SERVER_URL = (import.meta as any).env?.VITE_SERVER_URL || 'http://localhost:8000'
const ROOM = (import.meta as any).env?.VITE_ROOM || 'demo'

function getCardEmoji(card: Card): string {
  const text = `${card.name} ${(card.type || '')} ${(card.notes || '')}`.toLowerCase()
  const has = (s: string) => text.includes(s)
  // Role/name based
  if (has('boss') || has('king') || has('queen') || has('leader') || has('chief') || has('босс') || has('король') || has('королева') || has('лидер') || has('вож') ) return '👑'
  if (has('assassin') || has('killer') || has('rogue') || has('ninja') || has('убий') || has('килл') || has('разбой') || has('ниндзя')) return '🗡️'
  if (has('sniper') || has('shooter') || has('gunner') || has('hitman') || has('снайпер') || has('стрел')) return '🎯'
  if (has('tank') || has('guard') || has('bodyguard') || has('shield') || has('танк') || has('гвард') || has('охран') || has('щит')) return '🛡️'
  if (has('doctor') || has('medic') || has('healer') || has('nurse') || has('врач') || has('медик') || has('лекар')) return '🩺'
  if (has('engineer') || has('mechanic') || has('tech') || has('инжен') || has('механ')) return '🛠️'
  if (has('hacker') || has('cyber') || has('хакер') || has('кибер')) return '💻'
  if (has('mage') || has('wizard') || has('sorcer') || has('маг') || has('чарод') || has('колдун')) return '✨'
  if (has('thief') || has('pickpocket') || has('smuggler') || has('spy') || has('scout') || has('вор') || has('шпион') || has('развед')) return '🕵️'
  if (has('robot') || has('android') || has('mech') || has('робот') || has('андроид') || has('мех')) return '🤖'
  if (has('zombie') || has('undead') || has('ghoul') || has('зомби') || has('нежить') || has('упыр')) return '🧟'
  if (has('priest') || has('monk') || has('cleric') || has('свящ') || has('монах') || has('жрец')) return '🙏'
  if (has('bard') || has('бард')) return '🎵'
  if (has('fire') || has('flame') || has('pyro') || has('огонь') || has('плам')) return '🔥'
  if (has('ice') || has('frost') || has('лед') || has('мороз')) return '❄️'
  if (has('poison') || has('toxic') || has('venom') || has('яд') || has('токс')) return '☠️'
  if (has('wolf') || has('tiger') || has('bear') || has('beast') || has('волк') || has('тигр') || has('медвед') || has('звер')) return '🐾'
  // Stat-based fallback
  if ((card.atk || 0) >= 5) return '⚔️'
  if ((card.hp || 0) >= 5) return '🛡️'
  return '🃏'
}

function getCasteIcon(caste?: string): string | null {
  const c = (caste || '').toLowerCase()
  if (!c) return null
  if (c.includes('gang')) return '🕶️'
  if (c.includes('author')) return '🏛️'
  if (c.includes('loner') || c.includes('solo')) return '🧍'
  return '🎴'
}

function CardView({ card, faceUp }: { card: Card | null, faceUp: boolean }) {
  if (!card) return (
    <div className="card empty">
      <div className="card-title">—</div>
    </div>
  )
  if (!faceUp) return (
    <div className="card facedown">
      <div className="card-title">🎴 Face-down</div>
    </div>
  )
  return (
    <div className="card">
      <div className="card-title">
        {card.caste ? <span className="caste-icon" title={`Caste: ${card.caste}`}>{getCasteIcon(card.caste)}</span> : null}
        {card.name}
      </div>
      <div className="card-illustration" aria-hidden="true">{getCardEmoji(card)}</div>
      <div className="card-row card-stats">
        <span className="stat hp">HP: <b>{card.hp ?? 0}</b></span>
        {' '}•{' '}
        <span className="stat atk">ATK: <b>{card.atk ?? 0}</b></span>
        {' '}•{' '}
        <span className="stat def">D: <b>{card.d ?? 0}</b></span>
        {(card.rage ?? 0) > 0 && (
          <>{' '}•{' '}<span className="stat rage">R: <b>{card.rage}</b></span></>
        )}
      </div>
      {((card.price ?? 0) > 0 || (card.corruption ?? 0) > 0) && (
        <div className="card-row card-economy">
          {(card.price ?? 0) > 0 && <span className="stat price">$: <b>{card.price}</b></span>}
          {(card.price ?? 0) > 0 && (card.corruption ?? 0) > 0 && ' • '}
          {(card.corruption ?? 0) > 0 && <span className="stat corruption">CRP: <b>{card.corruption}</b></span>}
        </div>
      )}
      {card.faction ? (
        <div className="card-row card-faction">Faction: <b>{card.faction}</b></div>
      ) : null}
      <div className="card-notes">{card.notes}</div>
    </div>
  )
}

type DragPayload = { from: 'hand' | 'slot' | 'shelf'; fromIndex: number }
type TokenDrag = { kind: 'money' | 'shield', owner: 'you' | 'opponent' | 'bank', slotIndex?: number }

function OpponentHandThumbnails({ count }: { count: number }) {
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

function MoneyThumbnails({ count, draggableTokens = false, owner = 'you' }: { count: number, draggableTokens?: boolean, owner?: 'you' | 'bank' }): JSX.Element {
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

function AnimatedNumber({ value, className }: { value: number, className?: string }) {
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

function SlotView({ slot, onFlip, onDropToSlot, index, editable, owner, onTokenPlus, onTokenPlusFromBank, onTokenMinus, canAddShield, canRemoveShield, onReceiveShieldFrom, extraClassName, onClickCard, onHoverStart, onHoverEnd, onDragAnyStart, onDragAnyEnd, onSlotDragStart }:
  { slot: Slot, index: number, editable?: boolean, owner: 'you' | 'opponent', onFlip?: () => void, onDropToSlot?: (from: DragPayload) => void, onTokenPlus?: () => void, onTokenPlusFromBank?: () => void, onTokenMinus?: () => void, canAddShield?: boolean, canRemoveShield?: boolean, onReceiveShieldFrom?: (srcIndex: number) => void, extraClassName?: string, onClickCard?: () => void, onHoverStart?: () => void, onHoverEnd?: () => void, onDragAnyStart?: () => void, onDragAnyEnd?: () => void, onSlotDragStart?: (index: number) => void }): JSX.Element {
  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
  }
  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    // Card movement
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
          <CardView card={slot.card} faceUp={slot.face_up} />
        </div>
      </div>
    </div>
  )
}

export default function App(): JSX.Element {
  const [socket, setSocket] = useState<Socket | null>(null)
  const [view, setView] = useState<ViewState | null>(null)
  const [source, setSource] = useState<'yaml' | 'csv'>('yaml')
  const [seat, setSeat] = useState<'P1' | 'P2' | null>(null)
  const boardRef = useRef<HTMLDivElement | null>(null)
  const [oppCursor, setOppCursor] = useState<{ x: number, y: number, visible: boolean }>({ x: 0.5, y: 0.5, visible: false })
  const lastSent = useRef<number>(0)
  // Attack selection state (client-side)
  const [selectedAttackers, setSelectedAttackers] = useState<number[]>([])
  // Local attack modal state
  const [localAttackModal, setLocalAttackModal] = useState<{
    targetSlot: number
    targetPid: string
    markedShields: number[]
    cardMarkedForDestroy: boolean
  } | null>(null)

  // Hover preview side modal state
  const [preview, setPreview] = useState<{ card: Card, faceUp: boolean } | null>(null)
  const previewTimerRef = useRef<number | null>(null)
  const previewSuppressedRef = useRef<boolean>(false)

  // Dragging card origin to highlight valid drop zones
  const [dragCardFrom, setDragCardFrom] = useState<DragPayload | null>(null)

  const handlePreviewHoverStart = (card: Card | null, faceUp: boolean) => {
    if (!card) return
    if (previewSuppressedRef.current) return
    if (previewTimerRef.current) {
      clearTimeout(previewTimerRef.current)
      previewTimerRef.current = null
    }
    previewTimerRef.current = window.setTimeout(() => {
      setPreview({ card, faceUp })
    }, 1500)
  }

  const handlePreviewHoverEnd = () => {
    if (previewTimerRef.current) {
      clearTimeout(previewTimerRef.current)
    }
    previewTimerRef.current = null
    setPreview(null)
    previewSuppressedRef.current = false
  }

  const forceClosePreview = () => {
    setPreview(null)
    previewSuppressedRef.current = true
  }

  // Turn "no moves" alert state
  const [turnAlert, setTurnAlert] = useState(false)
  const turnAlertDismissedRef = useRef<number | null>(null)

  // Title reflects current seat to differentiate tabs
  useEffect(() => {
    document.title = `KINGPIN — Seat ${seat ?? '—'}`
  }, [seat])

  useEffect(() => {
    const s = io(SERVER_URL, { transports: ['websocket'] })
    setSocket(s)

    s.on('connect', () => {
      // wait for acknowledged 'connected'
    })
    s.on('connected', () => {
      s.emit('join_room', { room: ROOM, source })
    })
    s.on('joined', (payload: any) => {
      setSeat(payload.seat)
      if (payload?.source === 'yaml' || payload?.source === 'csv') {
        setSource(payload.source)
      }
    })
    s.on('state', (st: ViewState) => {
      setView(st)
    })
    s.on('room_full', () => {
      alert('Room is full')
    })
    s.on('cursor', (payload: any) => {
      // Ignore our own echo (server already skips, but be safe)
      if (!payload) return
      if (payload.pid === seat) return
      const x = Math.max(0, Math.min(1, Number(payload.x) || 0))
      const y = Math.max(0, Math.min(1, Number(payload.y) || 0))
      const visible = !!payload.visible
      setOppCursor({ x, y, visible })
    })
    s.on('error', (payload: any) => {
      if (payload?.msg === 'deck_empty') {
        alert('Deck is empty')
      } else {
        console.warn('Server error', payload)
      }
    })

    return () => {
      s.disconnect()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const you = view?.you
  const opp = view?.opponent
  const turn = view?.meta?.turn
  const isYourTurn = seat != null && turn?.active === seat
  const attack: AttackMeta | undefined = view?.meta?.attack
  const isAttacker = attack && seat ? attack.attacker === seat : false
  const isTarget = attack && seat ? attack.target.pid === seat : false

  // --- Client-side estimation helpers for global buffs ---
  const parseGivesGlobalAtk = (card: Card | null | undefined): number => {
    if (!card) return 0
    const type = (card.type || '').toLowerCase()
    if (type === 'boss') return 1 // Boss Rage: +1 ATK всем
    const txt = `${card.name} ${(card.notes || '')}`.toLowerCase()
    if (/\+\s*1\s*atk.*(всем|all)/i.test(txt)) return 1
    if (/получают\s*\+\s*1\s*atk/i.test(txt)) return 1
    const m = (card.notes || '').match(/rage\s*:\s*([1-9]\d*)/i)
    if (m) return parseInt(m[1], 10)
    return 0
  }

  const calcRagePerCard = (sideBoard?: Slot[]): number =>
    (sideBoard || []).reduce((acc, sl) => acc + parseGivesGlobalAtk(sl.card), 0)

  const calcGlobalDefend = (sideBoard?: Slot[]): number => {
    const base = (sideBoard || []).reduce((acc, sl) => acc + (sl.card?.d ?? 0), 0)
    const bossBonus = (sideBoard || []).some(sl => (sl.card?.type || '').toLowerCase() === 'boss') ? 1 : 0
    return base + bossBonus
  }

  const ragePerCardYou = useMemo(() => calcRagePerCard(you?.board), [you?.board])
  const defendGlobalOpp = useMemo(() => calcGlobalDefend(opp?.board), [opp?.board])

  // Shared bank (Golden fund): total 40 tokens across both players
  const TOTAL_MONEY_TOKENS = 40
  const yourMoney = you?.tokens?.reserve_money ?? 0
  const oppMoney = opp?.tokens?.reserve_money ?? 0
  // Shields on boards
  const totalYourShields = useMemo(() => (you?.board ?? []).reduce((acc, sl) => acc + (sl?.muscles ?? 0), 0), [you?.board])
  const totalOppShields = useMemo(() => (opp?.board ?? []).reduce((acc, sl) => acc + (sl?.muscles ?? 0), 0), [opp?.board])
  // Bank holds everything not in reserves and not on boards as shields
  const bankMoney = Math.max(0, TOTAL_MONEY_TOKENS - yourMoney - oppMoney - totalYourShields - totalOppShields)
  // Your actual reserve (spendable money)
  const availableMoney = Math.max(0, (yourMoney ?? 0))

  // Auto prompt to end turn if no obvious moves remain
  useEffect(() => {
    if (!isYourTurn || !turn) { setTurnAlert(false); return }
    if (attack) { setTurnAlert(false); return }
    if (turnAlertDismissedRef.current === turn.number) return

    const boardYou = you?.board ?? []
    const boardOpp = opp?.board ?? []
    const hasEmptySlot = boardYou.some(sl => !sl.card)
    const hasCardOnBoard = boardYou.some(sl => !!sl.card)
    const canPlayFromHand = (you?.hand?.length ?? 0) > 0 && hasEmptySlot
    const canRelocate = hasCardOnBoard && hasEmptySlot
    const canAddShieldMove = (yourMoney ?? 0) > 0
    const canRemoveShieldMove = boardYou.some(sl => (sl?.muscles ?? 0) > 0)
    const canAttackMove = boardYou.some(sl => (sl.card?.atk ?? 0) > 0) && boardOpp.some(sl => !!sl.card)
    const canDrawMove = (view?.shared?.deckCount ?? 0) > 0

    const hasMoves = canPlayFromHand || canRelocate || canAddShieldMove || canRemoveShieldMove || (canAttackMove && !localAttackModal) || canDrawMove
    setTurnAlert(!hasMoves)
  }, [isYourTurn, turn?.number, you, opp, view?.shared?.deckCount, yourMoney, attack, localAttackModal])

  const dismissTurnAlert = () => {
    setTurnAlert(false)
    if (turn?.number != null) turnAlertDismissedRef.current = turn.number
  }

  const handleDraw = () => socket?.emit('draw', { room: ROOM })
  const handleFlip = (i: number) => socket?.emit('flip_card', { room: ROOM, slotIndex: i })
  const moveFromHandToSlot = (handIndex: number, slotIndex: number) => socket?.emit('move_card', { room: ROOM, from: 'hand', to: 'slot', fromIndex: handIndex, toIndex: slotIndex })
  const moveFromSlotToSlot = (fromIndex: number, toIndex: number) => socket?.emit('move_card', { room: ROOM, from: 'slot', to: 'slot', fromIndex, toIndex })
  const moveFromSlotToHand = (slotIndex: number) => socket?.emit('move_card', { room: ROOM, from: 'slot', to: 'hand', fromIndex: slotIndex })
  const sendSetVisible = (n: number) => socket?.emit('set_visible_slots', { room: ROOM, count: n })
  // Shield ops
  const addShieldFromReserve = (i: number) => socket?.emit('add_shield_from_reserve', { room: ROOM, slotIndex: i, count: 1 })
  const removeShieldToReserve = (i: number) => socket?.emit('remove_shield_to_reserve', { room: ROOM, slotIndex: i, count: 1 })
  const addShieldOnly = (i: number) => socket?.emit('add_shield_only', { room: ROOM, slotIndex: i, count: 1 })
  const removeShieldOnly = (i: number) => socket?.emit('remove_shield_only', { room: ROOM, slotIndex: i, count: 1 })
  const addMoney = (n: number) => socket?.emit('add_token', { room: ROOM, kind: 'money', count: n })
  const removeMoney = (n: number) => socket?.emit('remove_token', { room: ROOM, kind: 'money', count: n })
  const shuffleDeck = () => socket?.emit('shuffle_deck', { room: ROOM })
  const resetRoom = () => {
    if (confirm('Reset the room and drop all game progress? This cannot be undone.')) {
      socket?.emit('reset_room', { room: ROOM, source })
    }
  }
  const endTurn = () => socket?.emit('end_turn', { room: ROOM })

  // Attack socket helpers
  const emitStartAttack = (attackerSlots: number[], targetSlot: number) => socket?.emit('start_attack', { room: ROOM, attackerSlots, targetSlot })
  const emitUpdatePlan = (patch: Partial<{ removeShields: number, destroyCard: boolean }>) => socket?.emit('attack_update_plan', { room: ROOM, ...patch })
  const emitPropose = () => socket?.emit('attack_propose', { room: ROOM })
  const emitAccept = () => socket?.emit('attack_accept', { room: ROOM })
  const emitCancel = () => socket?.emit('attack_cancel', { room: ROOM })

  const visibleYou = view?.meta?.visible_slots?.you ?? 6

  const emitCursor = (x: number, y: number, visible = true) => {
    const now = performance.now()
    if (now - (lastSent.current || 0) < 40) return // ~25 fps throttle
    lastSent.current = now
    socket?.emit('cursor', { room: ROOM, x, y, visible })
  }

  const onBoardMouseMove = (e: React.MouseEvent) => {
    const el = boardRef.current
    if (!el) return
    const rect = el.getBoundingClientRect()
    const x = (e.clientX - rect.left) / rect.width
    const y = (e.clientY - rect.top) / rect.height
    emitCursor(Math.max(0, Math.min(1, x)), Math.max(0, Math.min(1, y)), true)
  }
  const onBoardMouseLeave = () => emitCursor(0, 0, false)

  // Attack selection handlers
  const toggleSelectAttacker = (i: number) => {
    if (!you?.board?.[i]?.card) return
    const atk = (you?.board?.[i]?.card?.atk ?? 0)
    if (atk <= 0) return
    setSelectedAttackers((prev) => prev.includes(i) ? prev.filter(x => x !== i) : [...prev, i])
  }
  const clearAttackSelection = () => { 
    setSelectedAttackers([])
    setLocalAttackModal(null)
  }
  const handleTargetClick = (i: number) => {
    if (selectedAttackers.length === 0) return
    // Open local attack modal instead of immediately emitting
    const targetPid = opp?.id || 'opponent'
    setLocalAttackModal({
      targetSlot: i,
      targetPid,
      markedShields: [],
      cardMarkedForDestroy: false
    })
  }

  // Local attack modal handlers
  const toggleShieldMark = (shieldIndex: number) => {
    if (!localAttackModal) return
    setLocalAttackModal(prev => {
      if (!prev) return null
      const marked = prev.markedShields.includes(shieldIndex)
      return {
        ...prev,
        markedShields: marked 
          ? prev.markedShields.filter(i => i !== shieldIndex)
          : [...prev.markedShields, shieldIndex]
      }
    })
  }

  const toggleCardDestroy = () => {
    if (!localAttackModal) return
    setLocalAttackModal(prev => prev ? { ...prev, cardMarkedForDestroy: !prev.cardMarkedForDestroy } : null)
  }

  const confirmAttack = () => {
    if (!localAttackModal) return
    // Send attack to server with marked shields and destroy flag
    emitStartAttack(selectedAttackers.slice().sort((a,b) => a-b), localAttackModal.targetSlot)
    
    // Wait a bit then send the plan and propose
    setTimeout(() => {
      emitUpdatePlan({ 
        removeShields: localAttackModal.markedShields.length, 
        destroyCard: localAttackModal.cardMarkedForDestroy 
      })
      // Auto-propose after setting plan
      setTimeout(() => {
        emitPropose()
      }, 100)
    }, 100)
    
    // Clear local state
    clearAttackSelection()
  }

  const cancelLocalAttack = () => {
    setLocalAttackModal(null)
  }

  const handleDropToSlot = (slotIndex: number, from: DragPayload) => {
    setDragCardFrom(null)
    if (!from) return
    if (from.from === 'hand') return moveFromHandToSlot(from.fromIndex, slotIndex)
    if (from.from === 'slot') return moveFromSlotToSlot(from.fromIndex, slotIndex)
    if (from.from === 'shelf') return socket?.emit('move_card', { room: ROOM, from: 'shelf', to: 'slot', fromIndex: from.fromIndex, toIndex: slotIndex })
  }

  const onHandDragStart = (i: number, e: React.DragEvent<HTMLDivElement>) => {
    handlePreviewHoverEnd()
    setDragCardFrom({ from: 'hand', fromIndex: i })
    e.dataTransfer.setData('application/json', JSON.stringify({ from: 'hand', fromIndex: i }))
  }

  const onShelfDragStart = (i: number, e: React.DragEvent<HTMLDivElement>) => {
    handlePreviewHoverEnd()
    setDragCardFrom({ from: 'shelf', fromIndex: i })
    e.dataTransfer.setData('application/json', JSON.stringify({ from: 'shelf', fromIndex: i }))
  }

  const onHandDrop = (e: React.DragEvent) => {
    e.preventDefault()
    const data = e.dataTransfer.getData('application/json')
    try {
      const from = JSON.parse(data) as DragPayload
      if (from.from === 'slot') {
        moveFromSlotToHand(from.fromIndex)
      } else if (from.from === 'shelf') {
        socket?.emit('move_card', { room: ROOM, from: 'shelf', to: 'hand', fromIndex: from.fromIndex })
      }
    } catch {}
    setDragCardFrom(null)
  }

  const onDiscardDrop = (e: React.DragEvent) => {
    e.preventDefault()
    const data = e.dataTransfer.getData('application/json')
    try {
      const from = JSON.parse(data) as DragPayload
      if (from.from === 'hand') {
        socket?.emit('move_card', { room: ROOM, from: 'hand', to: 'discard', fromIndex: from.fromIndex })
      } else if (from.from === 'slot') {
        socket?.emit('move_card', { room: ROOM, from: 'slot', to: 'discard', fromIndex: from.fromIndex })
      }
    } catch {}
    setDragCardFrom(null)
  }

  const onShelfDrop = (e: React.DragEvent) => {
    e.preventDefault()
    const data = e.dataTransfer.getData('application/json')
    try {
      const from = JSON.parse(data) as DragPayload
      if (from.from === 'hand') {
        socket?.emit('move_card', { room: ROOM, from: 'hand', to: 'shelf', fromIndex: from.fromIndex })
      } else if (from.from === 'slot') {
        socket?.emit('move_card', { room: ROOM, from: 'slot', to: 'shelf', fromIndex: from.fromIndex })
      }
    } catch {}
    setDragCardFrom(null)
  }

  return (
    <div className="page" id="app_page">
      <header className="topbar" id="topbar">
        <div className="brand" id="brand">KINGPIN — 2P Table — Seat: {seat ?? '—'}</div>
        {turn ? (
          <div className={`turn-badge ${isYourTurn ? 'you' : 'op'}`} id="turn_badge" title={`Turn ${turn.number} · Phase ${turn.phase}`}>
            {isYourTurn ? 'Your turn' : `Opponent turn (${turn.active})`} · T{turn.number}
          </div>
        ) : null}
        <div className="spacer" />
        <div className="controls" id="controls">
          <label id="visible_label">Visible slots: {visibleYou}</label>
          <input id="visible_slider" type="range" min={6} max={9} step={1} value={visibleYou} onChange={(e: React.ChangeEvent<HTMLInputElement>) => sendSetVisible(parseInt(e.target.value))} />
          <button id="btn_shuffle" onClick={shuffleDeck}>Shuffle</button>
          <button id="btn_draw_top" onClick={handleDraw}>Draw</button>
          <button id="btn_end_turn" onClick={endTurn} disabled={!isYourTurn} title="End turn">End Turn</button>
          {selectedAttackers.length > 0 && <button id="btn_clear_selection" onClick={clearAttackSelection} disabled={!!attack || !!localAttackModal} title="Clear attack selection">Clear Selection ({selectedAttackers.length})</button>}
          <button id="btn_reset" className="danger" onClick={resetRoom} title="Reset room (drop progress)">Reset</button>
        </div>
      </header>

      <div className="main" id="main">
        <div className="board" id="board" ref={boardRef} onMouseMove={onBoardMouseMove} onMouseLeave={onBoardMouseLeave}>
          {oppCursor.visible && (
            <div className="op-cursor" style={{ left: `${oppCursor.x * 100}%`, top: `${oppCursor.y * 100}%` }} title="Opponent cursor" />
          )}
          <section className={`opponent ${turn && !isYourTurn ? 'active-turn' : ''}`} id="section_opponent">
            <h3 id="opponent_title">Opponent Board ({opp?.id ?? '—'})</h3>
            <OpponentHandThumbnails count={opp?.handCount ?? 0} />
            <div className="slots-grid" id="opp_slots">
              {opp?.board?.map((s: Slot, i: number) => (
                <SlotView
                  key={i}
                  slot={s}
                  index={i}
                  editable={false}
                  owner="opponent"
                  extraClassName={selectedAttackers.length > 0 && s.card ? 'targetable' : ''}
                  onClickCard={() => handleTargetClick(i)}
                  onHoverStart={() => handlePreviewHoverStart(s.card, s.face_up)}
                  onHoverEnd={handlePreviewHoverEnd}
                  onDragAnyStart={handlePreviewHoverEnd}
                />
              ))}
            </div>
            <div className="tokens-row" id="opp_tokens_row">
              <div className="money" id="opp_money">💰 {opp?.tokens?.reserve_money ?? 0}</div>
            </div>
          </section>

          <section className={`you ${isYourTurn ? 'active-turn' : ''}`} id="section_you">
            <h3 id="your_title">Your Board ({you?.id ?? '—'})</h3>
            <div className="slots-grid" id="you_slots">
              {you?.board?.map((s: Slot, i: number) => (
                <SlotView
                  key={i}
                  slot={s}
                  index={i}
                  editable
                  owner="you"
                  extraClassName={`${selectedAttackers.includes(i) ? 'attacker-selected' : ''} ${(
                    !!dragCardFrom &&
                    !s.card &&
                    ((((dragCardFrom as DragPayload).from === 'slot') && (dragCardFrom as DragPayload).fromIndex !== i) ||
                     (dragCardFrom as DragPayload).from === 'hand' ||
                     (dragCardFrom as DragPayload).from === 'shelf')
                  ) ? 'drop-highlight' : ''}`}
                  onClickCard={() => toggleSelectAttacker(i)}
                  onFlip={() => handleFlip(i)}
                  onDropToSlot={(from) => handleDropToSlot(i, from)}
                  canAddShield={(yourMoney ?? 0) > 0}
                  canRemoveShield={(s?.muscles ?? 0) > 0}
                  onTokenPlus={() => { // Spend from your reserve to place a shield
                    if ((yourMoney ?? 0) > 0) { addShieldFromReserve(i) }
                  }}
                  onTokenPlusFromBank={() => { // Bank tokens are not draggable; fallback to reserve spend
                    if ((yourMoney ?? 0) > 0) { addShieldFromReserve(i) }
                  }}
                  onTokenMinus={() => { // Return shield back to your reserve
                    if ((s?.muscles ?? 0) > 0) { removeShieldToReserve(i) }
                  }}
                  onReceiveShieldFrom={(srcIndex: number) => { if (srcIndex !== i) { removeShieldOnly(srcIndex); addShieldOnly(i) } }}
                  onHoverStart={() => handlePreviewHoverStart(s.card, s.face_up)}
                  onHoverEnd={handlePreviewHoverEnd}
                  onDragAnyStart={handlePreviewHoverEnd}
                  onSlotDragStart={(idx: number) => { handlePreviewHoverEnd(); setDragCardFrom({ from: 'slot', fromIndex: idx }) }}
                  onDragAnyEnd={() => setDragCardFrom(null)}
                />
              ))}
            </div>

            <div className={`hand ${dragCardFrom && (((dragCardFrom as DragPayload).from === 'slot') || ((dragCardFrom as DragPayload).from === 'shelf')) ? 'drop-highlight' : ''}`} id="your_hand" onDragOver={(e: React.DragEvent) => e.preventDefault()} onDrop={onHandDrop}>
              <div className="hand-title" id="your_hand_title">Your Hand ({you?.hand?.length ?? 0})</div>
              <div className="hand-cards" id="your_hand_cards">
                {you?.hand?.map((c: Card, i: number) => (
                  <div 
                    key={c.id + '_' + i} 
                    className="card-wrap" 
                    draggable 
                    onDragStart={(e: React.DragEvent<HTMLDivElement>) => onHandDragStart(i, e)}
                    onDragEnd={() => setDragCardFrom(null)}
                    onMouseEnter={() => handlePreviewHoverStart(c, true)}
                    onMouseLeave={handlePreviewHoverEnd}
                  >
                    <CardView card={c} faceUp={true} />
                  </div>
                ))}
              </div>
            </div>

            <div className="your-tokens" id="your_tokens">
              <div className="money" id="your_money" title={`Your reserve: ${yourMoney}`}>
                <button id="btn_money_minus" className="tkn-btn" onClick={() => removeMoney(1)} disabled={yourMoney <= 0}>−</button>
                💰 <AnimatedNumber value={availableMoney} />
                <button id="btn_money_plus" className="tkn-btn" onClick={() => addMoney(1)} disabled={bankMoney <= 0}>＋</button>
                <MoneyThumbnails count={availableMoney} draggableTokens={true} owner="you" />
              </div>
              <div className="otboy" id="your_otboy">♻️ {you?.tokens?.otboy ?? 0}</div>
            </div>
          </section>
        </div>

        <aside className="sidebar" id="sidebar">
          <div className="pile-box pile-draw">
            <div className="pile-title" id="pile_draw_title">Draw pile</div>
            <div className="pile-count" id="pile_draw_count">{view?.shared?.deckCount ?? 0}</div>
            <button id="btn_draw_sidebar" onClick={handleDraw}>Draw</button>
          </div>
          <div className="pile-box pile-reserve" id="pile_safe_bank" title={`Bank (Golden fund): ${bankMoney} (total ${TOTAL_MONEY_TOKENS} − reserves ${yourMoney + oppMoney} − shields ${totalYourShields + totalOppShields})`} onDragOver={(e: React.DragEvent) => e.preventDefault()} onDrop={(e: React.DragEvent) => {
            const data = e.dataTransfer.getData('application/x-token')
            if (!data) return
            try {
              const tok = JSON.parse(data) as TokenDrag
              if (tok.kind === 'shield') {
                if (tok.owner === 'you' && typeof tok.slotIndex === 'number') {
                  // Convert your shield back to your reserve (bank unchanged)
                  removeShieldToReserve(tok.slotIndex)
                } else if (tok.owner === 'opponent' && typeof tok.slotIndex === 'number') {
                  socket?.emit('remove_op_shield', { room: ROOM, slotIndex: tok.slotIndex })
                }
              }
            } catch {}
          }}>
            <div className="pile-title" id="pile_safe_bank_title">Bank</div>
            <div className="pile-count" id="pile_safe_bank_count">💰 <AnimatedNumber value={bankMoney} /></div>
            {/* Do not allow dragging tokens from bank to avoid reserve/bank changes during internal distribution */}
            <MoneyThumbnails count={bankMoney} draggableTokens={false} owner="bank" />
          </div>
          <div className={`pile-box pile-reserve ${dragCardFrom && (((dragCardFrom as DragPayload).from === 'hand') || ((dragCardFrom as DragPayload).from === 'slot')) ? 'drop-highlight' : ''}`} id="pile_reserve" onDragOver={(e: React.DragEvent) => e.preventDefault()} onDrop={onShelfDrop}>
            <div className="pile-title" id="pile_reserve_title">Reserve pile</div>
            <div className="pile-count" id="pile_reserve_count">{view?.shared?.shelfCount ?? 0}</div>
            <div className="shelf-list">
              {view?.shared?.shelf?.map((c, i) => (
                <div key={c.id + '_' + i} className="shelf-item" draggable onDragStart={(e: React.DragEvent<HTMLDivElement>) => onShelfDragStart(i, e)} onDragEnd={() => setDragCardFrom(null)} title={c.notes || c.name} onMouseEnter={() => handlePreviewHoverStart(c, true)} onMouseLeave={handlePreviewHoverEnd}>
                  <div className="shelf-card-name">{c.name}</div>
                  {c.caste && <div className="shelf-card-caste">{c.caste}</div>}
                  {c.faction && <div className="shelf-card-faction">{c.faction}</div>}
                  {(c.rage ?? 0) > 0 && (
                    <div className="card-row card-stats shelf-stats">
                      <span className="stat rage">R: <b>{c.rage}</b></span>
                    </div>
                  )}
                  {((c.price ?? 0) > 0 || (c.corruption ?? 0) > 0) && (
                    <div className="card-row card-economy shelf-economy">
                      {(c.price ?? 0) > 0 && <span className="stat price">$: <b>{c.price}</b></span>}
                      {(c.price ?? 0) > 0 && (c.corruption ?? 0) > 0 && ' • '}
                      {(c.corruption ?? 0) > 0 && <span className="stat corruption">CRP: <b>{c.corruption}</b></span>}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
          {/* Legend removed as per requirements */}
          <div className={`pile-box pile-discard ${dragCardFrom && (((dragCardFrom as DragPayload).from === 'hand') || ((dragCardFrom as DragPayload).from === 'slot')) ? 'drop-highlight' : ''}`} id="pile_discard" onDragOver={(e: React.DragEvent) => e.preventDefault()} onDrop={onDiscardDrop}>
            <div className="pile-title" id="pile_discard_title">Discard pile</div>
            <div className="pile-count" id="pile_discard_count">{view?.shared?.discardCount ?? 0}</div>
          </div>
          <div className="pile-box log-box" id="game_log">
            <div className="pile-title" id="game_log_title">Game Log</div>
            <div className="log-list" id="log_list">
              {[...(view?.meta?.log ?? [])].slice(-30).reverse().map((e: LogEntry) => (
                <div key={e.id} className={`log-row kind-${e.kind}`}>
                  <span className={`who ${e.actor === seat ? 'you' : e.actor ? 'op' : 'sys'}`}>{e.actor ?? 'SYS'}</span>
                  <span className="msg">{e.msg}</span>
                </div>
              ))}
            </div>
          </div>
        </aside>
      </div>

      {/* Side Card Preview Modal */}
      {preview && (
        <div className="side-modal" role="dialog" aria-modal="false">
          <div className="side-modal-header">
            <div className="modal-title">{preview.card.name}</div>
            <button className="close-btn" aria-label="Close" onClick={forceClosePreview}>×</button>
          </div>
          <div className="side-modal-content">
            <div className="modal-card">
              <div className="card-wrap">
                <CardView card={preview.card} faceUp={preview.faceUp} />
              </div>
            </div>
            <div className="preview-props">
              <div className="prop"><b>Тип:</b> {preview.card.type || '—'}</div>
              <div className="prop"><b>Фракция:</b> {preview.card.faction || '—'}</div>
              <div className="prop"><b>Каста:</b> {preview.card.caste || '—'}</div>
              <div className="prop"><b>HP:</b> {preview.card.hp ?? 0}</div>
              <div className="prop"><b>ATK:</b> {preview.card.atk ?? 0}</div>
              <div className="prop"><b>D:</b> {preview.card.d ?? 0}</div>
              {(preview.card.rage ?? 0) > 0 && <div className="prop"><b>Rage:</b> {preview.card.rage}</div>}
              {(preview.card.price ?? 0) > 0 && <div className="prop"><b>Price:</b> {preview.card.price}</div>}
              {(preview.card.corruption ?? 0) > 0 && <div className="prop"><b>Corruption:</b> {preview.card.corruption}</div>}
              {preview.card.notes && <div className="prop"><b>Примечания:</b> {preview.card.notes}</div>}
            </div>
          </div>
        </div>
      )}

      {/* Local Attack Modal */}
      {localAttackModal && (
        <div className="modal-overlay" role="dialog" aria-modal="true">
          <div className="modal attack-modal">
            <div className="modal-header">
              <div className="modal-title">Планирование атаки</div>
              <div className="modal-sub">Атакующие: {selectedAttackers.map(i => `#${i + 1}`).join(', ')} → Цель: слот {localAttackModal.targetSlot + 1}</div>
            </div>
            <div className="modal-content">
              {/* Target card with exact replica */}
              <div className="modal-card">
                <div className="card-wrap" style={{ opacity: localAttackModal.cardMarkedForDestroy ? 0.5 : 1 }}>
                  <CardView 
                    card={opp?.board?.[localAttackModal.targetSlot]?.card ?? null} 
                    faceUp={opp?.board?.[localAttackModal.targetSlot]?.face_up ?? false} 
                  />
                </div>
                {/* Interactive shields */}
                <div className="shield-thumbs modal-shields">
                  {Array.from({ length: 4 }).map((_, i) => {
                    const slotData = opp?.board?.[localAttackModal.targetSlot]
                    const muscles = Math.min(4, Math.max(0, slotData?.muscles ?? 0))
                    const filled = i < muscles
                    const marked = localAttackModal.markedShields.includes(i)
                    return (
                      <div 
                        key={i} 
                        className={`shield-thumb ${filled ? 'filled' : 'empty'} ${marked ? 'marked-for-removal' : ''}`}
                        style={{ 
                          opacity: marked ? 0.5 : 1,
                          cursor: filled ? 'pointer' : 'default'
                        }}
                        onClick={filled ? () => toggleShieldMark(i) : undefined}
                        title={filled ? (marked ? 'Отменить удаление щита' : 'Отметить щит для удаления') : ''}
                      />
                    )
                  })}
                </div>
              </div>

              {/* Attack summary */}
              <div className="attackers">
                <div className="label">Атакующие карты</div>
                <div className="list">
                  {selectedAttackers.map(i => {
                    const card = you?.board?.[i]?.card
                    return card ? `#${i + 1}: ${card.name} (ATK: ${card.atk})` : `#${i + 1}`
                  }).join(', ')}
                </div>
              </div>

              {/* Calculations: total ATK and defender HP */}
              <div className="calc-block">
                {(() => {
                  // Total ATK
                  const atkCards = selectedAttackers.map(i => you?.board?.[i]?.card).filter(Boolean) as Card[]
                  const baseSum = atkCards.reduce((s, c) => s + (c.atk ?? 0), 0)
                  const perCardBuff = ragePerCardYou
                  const buffSum = (perCardBuff > 0 ? selectedAttackers.length * perCardBuff : 0)
                  const shieldsOnAttackers = selectedAttackers.reduce((s, i) => s + (you?.board?.[i]?.muscles ?? 0), 0)
                  const shieldsBonus = shieldsOnAttackers * 0.25
                  const totalAtk = baseSum + buffSum + shieldsBonus
                  // Defender HP
                  const tSlot = localAttackModal.targetSlot
                  const defSlot = opp?.board?.[tSlot]
                  const defCard = defSlot?.card
                  const baseHP = defCard?.hp ?? 0
                  const shields = defSlot?.muscles ?? 0
                  const totalHP = baseHP + shields
                  return (
                    <>
                      <div className="calc-row"><b>Суммарная атака:</b> {atkCards.map(c => c.atk ?? 0).join(' + ')}{perCardBuff > 0 ? ` + ${selectedAttackers.length}×${perCardBuff}` : ''}{shieldsOnAttackers > 0 ? ` + 0.25×${shieldsOnAttackers}` : ''} = <b>{totalAtk}</b></div>
                      <div className="calc-row"><b>Защита цели (HP):</b> {baseHP}{shields > 0 ? ` + ${Array.from({length: shields}).map(() => '1').join(' + ')}` : ''} = <b>{totalHP}</b></div>
                    </>
                  )
                })()}
              </div>

              {/* Controls */}
              <div className="modal-controls">
                <div className="control-row">
                  <div className="info">
                    {localAttackModal.markedShields.length > 0 && `Щиты к удалению: ${localAttackModal.markedShields.length}`}
                    {localAttackModal.cardMarkedForDestroy && ' • Карта отмечена для уничтожения'}
                    {localAttackModal.markedShields.length === 0 && !localAttackModal.cardMarkedForDestroy && 'Выберите щиты для удаления или отметьте карту для уничтожения'}
                  </div>
                </div>
                
                <div className="control-row">
                  <button 
                    className={`toggle ${localAttackModal.cardMarkedForDestroy ? 'on' : ''}`} 
                    onClick={toggleCardDestroy}
                  >
                    {localAttackModal.cardMarkedForDestroy ? '✓ Карта будет уничтожена' : 'Уничтожить карту'}
                  </button>
                </div>

                <div className="control-row">
                  <button 
                    onClick={confirmAttack} 
                    disabled={localAttackModal.markedShields.length === 0 && !localAttackModal.cardMarkedForDestroy}
                    className="primary"
                  >
                    Отправить предложение
                  </button>
                  <button onClick={cancelLocalAttack} className="danger">
                    Отменить
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Server Attack Modal (for opponent responses) */}
      {attack && (
        <div className="modal-overlay" role="dialog" aria-modal="true">
          <div className="modal attack-modal">
            <div className="modal-header">
              <div className="modal-title">Подтверждение атаки</div>
              <div className="modal-sub">Атакующий: {attack.attacker} → Цель: {attack.target.pid} слот {attack.target.slot + 1}</div>
            </div>
            <div className="modal-content">
              {/* Target preview */}
              <div className="modal-card">
                <div className="card-wrap" style={{ opacity: attack.plan.destroyCard ? 0.5 : 1 }}>
                  {attack.target.pid === you?.id ? (
                    <CardView card={you?.board?.[attack.target.slot]?.card ?? null} faceUp={you?.board?.[attack.target.slot]?.face_up ?? false} />
                  ) : (
                    <CardView card={opp?.board?.[attack.target.slot]?.card ?? null} faceUp={opp?.board?.[attack.target.slot]?.face_up ?? false} />
                  )}
                </div>
                {/* Shields with marked removals */}
                <div className="shield-thumbs modal-shields">
                  {Array.from({ length: 4 }).map((_, i) => {
                    const slotData = attack.target.pid === you?.id ? you?.board?.[attack.target.slot] : opp?.board?.[attack.target.slot]
                    const muscles = Math.min(4, Math.max(0, slotData?.muscles ?? 0))
                    const filled = i < muscles
                    const marked = attack.plan.removeShields > 0 && i < attack.plan.removeShields
                    return (
                      <div 
                        key={i} 
                        className={`shield-thumb ${filled ? 'filled' : 'empty'} ${marked ? 'marked' : ''}`}
                        style={{ opacity: marked ? 0.5 : 1 }}
                      />
                    )
                  })}
                </div>
              </div>

              {/* Attackers list */}
              <div className="attackers">
                <div className="label">Атакующие</div>
                <div className="list">{attack.attackerSlots.map(i => `#${i + 1}`).join(', ')}</div>
              </div>

              {/* Calculations: total ATK and defender HP (visible обеим сторонам) */}
              <div className="calc-block">
                {(() => {
                  const atkIsYou = attack.attacker === you?.id
                  const attBoard = atkIsYou ? (you?.board || []) : (opp?.board || [])
                  const defIsYou = attack.target.pid === you?.id
                  const defBoard = defIsYou ? (you?.board || []) : (opp?.board || [])

                  // Total ATK
                  const atkCards = attack.attackerSlots
                    .map(i => attBoard?.[i]?.card)
                    .filter(Boolean) as Card[]
                  const baseSum = atkCards.reduce((s, c) => s + (c.atk ?? 0), 0)
                  const perCardBuff = calcRagePerCard(attBoard)
                  const buffSum = (perCardBuff > 0 ? attack.attackerSlots.length * perCardBuff : 0)
                  const shieldsOnAttackers = attack.attackerSlots.reduce((s, i) => s + (attBoard?.[i]?.muscles ?? 0), 0)
                  const shieldsBonus = shieldsOnAttackers * 0.25
                  const totalAtk = baseSum + buffSum + shieldsBonus

                  // Defender HP
                  const tSlot = attack.target.slot
                  const defSlot = defBoard?.[tSlot]
                  const defCard = defSlot?.card
                  const baseHP = defCard?.hp ?? 0
                  const shields = defSlot?.muscles ?? 0
                  const totalHP = baseHP + shields

                  return (
                    <>
                      <div className="calc-row"><b>Суммарная атака:</b> {atkCards.map(c => c.atk ?? 0).join(' + ')}{perCardBuff > 0 ? ` + ${attack.attackerSlots.length}×${perCardBuff}` : ''}{shieldsOnAttackers > 0 ? ` + 0.25×${shieldsOnAttackers}` : ''} = <b>{totalAtk}</b></div>
                      <div className="calc-row"><b>Защита цели (HP):</b> {baseHP}{shields > 0 ? ` + ${Array.from({length: shields}).map(() => '1').join(' + ')}` : ''} = <b>{totalHP}</b></div>
                    </>
                  )
                })()}
              </div>

              {/* Controls for defender */}
              <div className="modal-controls">
                {!isAttacker ? (
                  <>
                    <div className="control-row">
                      <div className="info">
                        {attack.status === 'planning' ? 'Ожидание предложения от атакующего...' : 
                         attack.plan.destroyCard ? 'Атакующий предлагает уничтожить эту карту.' : 
                         `Атакующий предлагает удалить ${attack.plan.removeShields} щит(ов).`}
                      </div>
                    </div>
                    <div className="control-row">
                      <button 
                        onClick={emitAccept} 
                        disabled={attack.status !== 'proposed'}
                        className="primary"
                      >
                        {attack.plan.destroyCard ? 'Согласен на уничтожение' : 'Согласен'}
                      </button>
                      <button onClick={emitCancel} className="danger">Отменить</button>
                    </div>
                  </>
                ) : (
                  <div className="control-row">
                    <div className="info">Ожидание ответа от защищающегося...</div>
                    <button onClick={emitCancel} className="danger">Отменить</button>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* No-moves Turn Alert */}
      {turnAlert && (
        <div className="modal-overlay" role="dialog" aria-modal="true">
          <div className="modal attack-modal turn-modal">
            <div className="modal-header">
              <div className="modal-title">Нет доступных ходов?</div>
              <div className="modal-sub">Похоже, у вас закончились возможные действия.</div>
            </div>
            <div className="modal-content" style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              <div className="calc-block">
                <div className="calc-row">Вы можете закончить ход или продолжить, если хотите перепроверить.</div>
              </div>
              <div className="modal-controls">
                <div className="control-row">
                  <button className="primary" onClick={() => { setTurnAlert(false); endTurn() }}>Закончить ход</button>
                  <button onClick={dismissTurnAlert}>Продолжить</button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      <footer className="bottombar" id="bottombar">
        <div>Seat: {seat ?? '—'} · Source: {source.toUpperCase()} · Room: {ROOM} · Server: {SERVER_URL}</div>
        <div className="spacer" />
        <div className="foot-controls" id="foot_controls">
          <button id="btn_use_yaml" onClick={() => setSource('yaml')}>Use YAML</button>
          <button id="btn_use_csv" onClick={() => setSource('csv')}>Use CSV</button>
        </div>
      </footer>
    </div>
  )
}

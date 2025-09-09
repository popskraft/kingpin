import React, { useEffect, useMemo, useRef, useState } from 'react'
import { useSocket } from './services/useSocket'
import type { ViewState, Card, Slot, LogEntry, AttackMeta } from './types'
import CardView from './components/CardView'
import { getClanStripeClass } from './components/cardHelpers'
import OpponentHandThumbnails from './components/OpponentHandThumbnails'
import MoneyThumbnails from './components/MoneyThumbnails'
import AnimatedNumber from './components/AnimatedNumber'
import SlotView from './components/SlotView'

const SERVER_URL = (import.meta as any).env?.VITE_SERVER_URL || 'http://localhost:8000'
const ROOM = (import.meta as any).env?.VITE_ROOM || 'demo'

// CardView and helper utilities moved to components/

type DragPayload = { from: 'hand' | 'slot' | 'shelf'; fromIndex: number }
type TokenDrag = { kind: 'money' | 'shield', owner: 'you' | 'opponent' | 'bank', slotIndex?: number }

// OpponentHandThumbnails moved to components/

// MoneyThumbnails moved to components/

// AnimatedNumber moved to components/

// SlotView moved to components/

export default function App(): JSX.Element {
  const [source, setSource] = useState<'yaml' | 'csv'>('yaml')
  const boardRef = useRef<HTMLDivElement | null>(null)
  const {
    socket, view, seat, oppCursor,
    draw, flip, moveFromHandToSlot, moveFromSlotToSlot, moveFromSlotToHand,
    setVisibleSlots, addShieldFromReserve, removeShieldToReserve, addShieldOnly, removeShieldOnly,
    addMoney, removeMoney, shuffleDeck, resetRoom, endTurn,
    startAttack, updateAttackPlan, proposeAttack, acceptAttack, cancelAttack,
    emitCursor,
  } = useSocket(SERVER_URL, ROOM)
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
  const [preview, setPreview] = useState<{ card: Card, faceUp: boolean, owner?: 'you' | 'opponent' } | null>(null)
  const previewTimerRef = useRef<number | null>(null)
  const previewSuppressedRef = useRef<boolean>(false)

  // Dragging card origin to highlight valid drop zones
  const [dragCardFrom, setDragCardFrom] = useState<DragPayload | null>(null)

  const handlePreviewHoverStart = (card: Card | null, faceUp: boolean, owner?: 'you' | 'opponent') => {
    if (!card) return
    if (previewSuppressedRef.current) return
    if (previewTimerRef.current) {
      clearTimeout(previewTimerRef.current)
      previewTimerRef.current = null
    }
    previewTimerRef.current = window.setTimeout(() => {
      setPreview({ card, faceUp, owner })
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

  // Track source from 'joined' payload via socket
  useEffect(() => {
    if (!socket) return
    const handler = (payload: any) => {
      if (payload?.source === 'yaml' || payload?.source === 'csv') setSource(payload.source)
    }
    socket.on('joined', handler)
    return () => { socket.off('joined', handler) }
  }, [socket])

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
    if (type === 'boss') return 1 // Boss Rage: +1 ATK to all
    const txt = `${card.name} ${(card.notes || '')}`.toLowerCase()
    if (/\+\s*1\s*atk.*(all)/i.test(txt)) return 1
    if (/(gain|gives|give|grant|grants)\s*\+\s*1\s*atk/i.test(txt)) return 1
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

  // --- Synergy helpers (generic) ---
  const detectClanSynergyKey = (sideBoard?: Slot[]): 'gangsters' | 'authorities' | 'loners' | null => {
    const clans = (sideBoard || [])
      .map(sl => (((sl.card?.clan || '') as string).toLowerCase().trim()))
      .filter(Boolean)
    if (clans.length === 0) return null
    const uniq = Array.from(new Set(clans))
    if (uniq.length !== 1) return null
    const c = uniq[0]
    if (c.includes('gang')) return 'gangsters'
    if (c.includes('author')) return 'authorities'
    if (c.includes('loner')) return 'loners'
    return null
  }
  const synergyRForBoard = (sideBoard?: Slot[]): number => {
    const k = detectClanSynergyKey(sideBoard)
    return (k === 'gangsters' || k === 'loners') ? 1 : 0
  }
  const synergyHpBonusForBoard = (sideBoard?: Slot[]): number => {
    const k = detectClanSynergyKey(sideBoard)
    return (k === 'authorities' || k === 'loners') ? 1 : 0
  }
  const synergyDBonusForBoard = (sideBoard?: Slot[]): number => {
    const k = detectClanSynergyKey(sideBoard)
    return (k === 'gangsters' || k === 'authorities') ? 1 : 0
  }
  
  // New: Pair-based synergy (2+ cards same clan or same faction as the target) and per-card bonuses
  const hasPairSynergyForCard = (sideBoard?: Slot[], card?: Card | null): boolean => {
    if (!card) return false
    const board = sideBoard || []
    const cardClan = (((card.clan || '') as string).trim().toLowerCase())
    const cardFaction = (card.faction || '').trim()
    const sameClan = board.filter(sl => ((((sl.card?.clan || '') as string).trim().toLowerCase()) === cardClan)).length >= 2
    const sameFaction = board.filter(sl => (sl.card?.faction || '').trim() === cardFaction).length >= 2
    return sameClan || sameFaction
  }

  const classifyClan = (clan?: string): 'gangsters' | 'authorities' | 'loners' | null => {
    const c = (clan || '').toLowerCase()
    if (!c) return null
    if (c.includes('gang')) return 'gangsters'
    if (c.includes('author')) return 'authorities'
    if (c.includes('loner') || c.includes('solo')) return 'loners'
    return null
  }

  const synergyBonusesForCardPair = (sideBoard?: Slot[], card?: Card | null): { hp: number, d: number, r: number } => {
    if (!card) return { hp: 0, d: 0, r: 0 }
    if (!hasPairSynergyForCard(sideBoard, card)) return { hp: 0, d: 0, r: 0 }
    // Use the per-card pair_* fields provided by the backend
    const hp = card.pair_hp ?? 0
    const d = card.pair_d ?? 0
    const r = card.pair_r ?? 0
    return { hp, d, r }
  }

  const ragePerCardYou = useMemo(() => calcRagePerCard(you?.board), [you?.board])
  const defendGlobalOpp = useMemo(() => calcGlobalDefend(opp?.board), [opp?.board])

  // --- Synergy Systems (Your side) ---
  const yourClanSynergy = useMemo(() => {
    const clans = (you?.board ?? [])
      .map(sl => (((sl.card?.clan || '') as string).toLowerCase().trim()))
      .filter(Boolean)
    if (clans.length === 0) return null as null | { name: string, effect: string }
    const unique = Array.from(new Set(clans))
    if (unique.length !== 1) return null
    const c = unique[0]
    if (c.includes('gang')) return { name: 'Gangsters', effect: '+1 R, +1 D' }
    if (c.includes('author')) return { name: 'Authorities', effect: '+1 HP, +1 D' }
    if (c.includes('loner') || c.includes('solo')) return { name: 'Loners', effect: '+1 R, +1 HP' }
    return null
  }, [you?.board])

  const yourFactionSingle = useMemo(() => {
    const factions = (you?.board ?? [])
      .map(sl => (sl.card?.faction || '').trim())
      .filter(Boolean)
    if (factions.length === 0) return null as null | string
    const unique = Array.from(new Set(factions))
    return unique.length === 1 ? unique[0] : null
  }, [you?.board])

  // --- Synergy Systems (Opponent side) ---
  const oppClanSynergy = useMemo(() => {
    const key = detectClanSynergyKey(opp?.board)
    if (!key) return null as null | { name: string, effect: string }
    if (key === 'gangsters') return { name: 'Gangsters', effect: '+1 R, +1 D' }
    if (key === 'authorities') return { name: 'Authorities', effect: '+1 HP, +1 D' }
    if (key === 'loners') return { name: 'Loners', effect: '+1 R, +1 HP' }
    return null
  }, [opp?.board])
  const oppFactionSingle = useMemo(() => {
    const factions = (opp?.board ?? [])
      .map(sl => (sl.card?.faction || '').trim())
      .filter(Boolean)
    if (factions.length === 0) return null as null | string
    const unique = Array.from(new Set(factions))
    return unique.length === 1 ? unique[0] : null
  }, [opp?.board])

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

  const handleDraw = () => draw()
  const handleFlip = (i: number) => flip(i)
  const sendSetVisible = (n: number) => setVisibleSlots(n)
  // Shield ops
  // shield/money helpers provided by useSocket via imported names
  // resetRoomLocal: minimal reset with confirmation
  const resetRoomLocal = () => {
    if (window.confirm('Reset room and reload from CSV? This drops all progress for both players.')) {
      resetRoom('csv')
      // Clear local-only UI state
      setSelectedAttackers([])
      setLocalAttackModal(null)
      setPreview(null)
      turnAlertDismissedRef.current = null
    }
  }
  const endTurnLocal = () => endTurn()

  // Attack socket helpers
  const emitStartAttack = (attackerSlots: number[], targetSlot: number) => startAttack(attackerSlots, targetSlot)
  const emitUpdatePlan = (patch: Partial<{ removeShields: number, destroyCard: boolean }>) => updateAttackPlan(patch)
  const emitPropose = () => proposeAttack()
  const emitAccept = () => acceptAttack()
  const emitCancel = () => cancelAttack()
  const emitApprove = emitAccept

  const visibleYou = view?.meta?.visible_slots?.you ?? 6

  const onBoardMouseMove = (e: React.MouseEvent) => {
    const el = boardRef.current
    if (!el) return
    const rect = el.getBoundingClientRect()
    const x = (e.clientX - rect.left) / rect.width
    const y = (e.clientY - rect.top) / rect.height
    emitCursor(Math.max(0, Math.min(1, x)), Math.max(0, Math.min(1, y)), true)
  }
  const onBoardMouseLeave = () => emitCursor(0, 0, false)

  // Attack selection handlers (max 3 attackers; unlimited if mono-clan board; no faction requirement)
  const toggleSelectAttacker = (i: number) => {
    const card = you?.board?.[i]?.card
    if (!card) return
    const atk = (card.atk ?? 0)
    if (atk <= 0) return
    // Determine if your board is mono-clan (all cards on board share the same clan)
    const monoClan = detectClanSynergyKey(you?.board) != null
    setSelectedAttackers(prev => {
      // Toggle off if already selected
      if (prev.includes(i)) return prev.filter(x => x !== i)
      // Enforce attacker-count cap: 3 unless mono-clan
      if (!monoClan && prev.length >= 3) return prev
      return [...prev, i]
    })
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
          <button id="btn_reset" className="danger" onClick={resetRoomLocal} title="Reset room (drop progress)">Reset</button>
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
                  owner={'opponent'}
                  extraClassName={selectedAttackers.length > 0 && s.card ? 'targetable' : ''}
                  onClickCard={() => handleTargetClick(i)}
                  onHoverStart={() => handlePreviewHoverStart(s.card, s.face_up, 'opponent')}
                  onHoverEnd={handlePreviewHoverEnd}
                  onDragAnyStart={handlePreviewHoverEnd}
                  bonusHp={synergyBonusesForCardPair(opp?.board, s.card).hp}
                  bonusD={synergyBonusesForCardPair(opp?.board, s.card).d}
                  bonusR={synergyBonusesForCardPair(opp?.board, s.card).r}
                  pairInfo={(() => { 
                    if (!s?.card) return null
                    const active = hasPairSynergyForCard(opp?.board, s.card)
                    if (!active) return null
                    const p = synergyBonusesForCardPair(opp?.board, s.card)
                    return (p.hp||p.d||p.r) ? p : null 
                  })()}
                />
              ))}
            </div>
            <div className="opp-info" id="opp_info">
              <div className="opp-tokens" id="opp_tokens">
                <div className="money" id="opp_money">💰 {opp?.tokens?.reserve_money ?? 0}</div>
              </div>
              {(oppClanSynergy || oppFactionSingle) && (
            <div className={`opp-synergy ${(() => { const k = detectClanSynergyKey(opp?.board); return k ? 'clan-' + k : '' })()}`} id="opp_synergy">
              <div className="synergy-title">Synergy</div>
              <div className="synergy-row">
                <span className="synergy-label">Clan:</span>{' '}
                {oppClanSynergy ? (<><b>{oppClanSynergy.name}</b> → {oppClanSynergy.effect}</>) : '—'}
              </div>
              {oppFactionSingle && (
                <div className="synergy-row">
                  <span className="synergy-label">Faction:</span>{' '}
                  <b>{oppFactionSingle}</b> → cascades are disabled in this version
                </div>
              )}
            </div>
          )}
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
                  onHoverStart={() => handlePreviewHoverStart(s.card, s.face_up, 'you')}
                  onHoverEnd={handlePreviewHoverEnd}
                  onDragAnyStart={handlePreviewHoverEnd}
                  onSlotDragStart={(idx: number) => { handlePreviewHoverEnd(); setDragCardFrom({ from: 'slot', fromIndex: idx }) }}
                  onDragAnyEnd={() => setDragCardFrom(null)}
                  bonusHp={synergyBonusesForCardPair(you?.board, s.card).hp}
                  bonusD={synergyBonusesForCardPair(you?.board, s.card).d}
                  bonusR={synergyBonusesForCardPair(you?.board, s.card).r}
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
                    onMouseEnter={() => handlePreviewHoverStart(c, true, 'you')}
                    onMouseLeave={handlePreviewHoverEnd}
                  >
                    <CardView card={c} faceUp={true} />
                  </div>
                ))}
              </div>
            </div>

            <div className="your-info" id="your_info">
              <div className="your-tokens" id="your_tokens">
                <div className="money" id="your_money" title={`Your reserve: ${yourMoney}`}>
                  <button id="btn_money_minus" className="tkn-btn" onClick={() => removeMoney(1)} disabled={yourMoney <= 0}>−</button>
                  💰 <AnimatedNumber value={availableMoney} />
                  <button id="btn_money_plus" className="tkn-btn" onClick={() => addMoney(1)} disabled={bankMoney <= 0}>＋</button>
                  <MoneyThumbnails count={availableMoney} draggableTokens={true} owner="you" />
                </div>
              </div>
              {(yourClanSynergy || yourFactionSingle) && (
                <div className={`your-synergy ${(() => { const k = detectClanSynergyKey(you?.board); return k ? 'clan-' + k : '' })()}`} id="your_synergy">
                  <div className="synergy-title">Synergy</div>
                  <div className="synergy-row">
                    <span className="synergy-label">Clan:</span>{' '}
                    {yourClanSynergy ? (<><b>{yourClanSynergy.name}</b> → {yourClanSynergy.effect}</>) : '—'}
                  </div>
                  {yourFactionSingle && (
                    <div className="synergy-row">
                      <span className="synergy-label">Faction:</span>{' '}
                      <b>{yourFactionSingle}</b> → cascades are disabled in this version
                    </div>
                  )}
                </div>
              )}
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
                  {c.clan && <div className="shelf-card-clan">{c.clan}</div>}
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
                <CardView 
                  card={preview.card} 
                  faceUp={preview.faceUp}
                  bonusHp={(() => { const b = preview.owner === 'you' ? you?.board : preview.owner === 'opponent' ? opp?.board : undefined; return synergyBonusesForCardPair(b, preview.card).hp })()}
                  bonusD={(() => { const b = preview.owner === 'you' ? you?.board : preview.owner === 'opponent' ? opp?.board : undefined; return synergyBonusesForCardPair(b, preview.card).d })()}
                  bonusR={(() => { const b = preview.owner === 'you' ? you?.board : preview.owner === 'opponent' ? opp?.board : undefined; return synergyBonusesForCardPair(b, preview.card).r })()}
                  pairInfo={(() => { const b = preview.owner === 'you' ? you?.board : preview.owner === 'opponent' ? opp?.board : undefined; if (!hasPairSynergyForCard(b, preview.card)) return null; const p = synergyBonusesForCardPair(b, preview.card); return (p.hp||p.d||p.r) ? p : null })()}
                />
              </div>
            </div>
            <div className="preview-props">
              <div className="prop"><b>Type:</b> {preview.card.type || '—'}</div>
              <div className="prop"><b>Faction:</b> {preview.card.faction || '—'}</div>
              <div className="prop"><b>Clan:</b> {preview.card.clan || '—'}</div>
              {(() => {
                const b = preview.owner === 'you' ? you?.board : preview.owner === 'opponent' ? opp?.board : undefined
                const pair = synergyBonusesForCardPair(b, preview.card)
                const hp = (preview.card.hp ?? 0) + pair.hp
                const atk = (preview.card.atk ?? 0)
                const def = (preview.card.d ?? 0) + pair.d
                const r = (preview.card.rage ?? 0) + pair.r
                return (
                  <>
                    <div className="prop"><b>HP:</b> {hp}</div>
                    <div className="prop"><b>ATK:</b> {atk}</div>
                    <div className="prop"><b>D:</b> {def}</div>
                    {r > 0 && <div className="prop"><b>Rage:</b> {r}</div>}
                  </>
                )
              })()}
              {(preview.card.price ?? 0) > 0 && <div className="prop"><b>Price:</b> {preview.card.price}</div>}
              {(preview.card.corruption ?? 0) > 0 && <div className="prop"><b>Corruption:</b> {preview.card.corruption}</div>}
              {preview.card.notes && <div className="prop"><b>Notes:</b> {preview.card.notes}</div>}
            </div>
          </div>
        </div>
      )}

      {/* Local Attack Modal */}
      {localAttackModal && (
        <div className="modal-overlay" role="dialog" aria-modal="true">
          <div className="modal attack-modal">
            <div className="modal-header">
              <div className="modal-title">Attack Planning</div>
              <div className="modal-sub">Attackers: {selectedAttackers.map(i => `#${i + 1}`).join(', ')} → Target: slot {localAttackModal.targetSlot + 1}</div>
            </div>
            <div className="modal-content">
              {/* Target card with exact replica */}
              <div className="modal-card">
                <div className="card-wrap" style={{ opacity: localAttackModal.cardMarkedForDestroy ? 0.5 : 1 }}>
                  <CardView 
                    card={opp?.board?.[localAttackModal.targetSlot]?.card ?? null} 
                    faceUp={opp?.board?.[localAttackModal.targetSlot]?.face_up ?? false}
                    bonusHp={synergyBonusesForCardPair(opp?.board, opp?.board?.[localAttackModal.targetSlot]?.card ?? null).hp}
                    bonusD={synergyBonusesForCardPair(opp?.board, opp?.board?.[localAttackModal.targetSlot]?.card ?? null).d}
                    bonusR={synergyBonusesForCardPair(opp?.board, opp?.board?.[localAttackModal.targetSlot]?.card ?? null).r}
                    pairInfo={(() => { const c = opp?.board?.[localAttackModal.targetSlot]?.card ?? null; if (!c) return null; if (!hasPairSynergyForCard(opp?.board, c)) return null; const p = synergyBonusesForCardPair(opp?.board, c); return (p.hp||p.d||p.r) ? p : null })()} 
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
                        title={filled ? (marked ? 'Unmark shield removal' : 'Mark shield for removal') : ''}
                      />
                    )
                  })}
                </div>
              </div>

              {/* Attack summary */}
              <div className="attackers">
                <div className="label">Attacking cards</div>
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
                  const perCardBaseR = ragePerCardYou
                  const perCardPairRSum = selectedAttackers.reduce((s, i) => {
                    const c = you?.board?.[i]?.card
                    return s + (c ? synergyBonusesForCardPair(you?.board, c).r : 0)
                  }, 0)
                  const buffSum = (perCardBaseR > 0 ? selectedAttackers.length * perCardBaseR : 0) + perCardPairRSum
                  // Shields on attackers add +0.25 ATK each (decimal totals kept)
                  const shieldAtkCount = selectedAttackers.reduce((s, i) => s + (you?.board?.[i]?.muscles ?? 0), 0)
                  const shieldAtk = shieldAtkCount * 0.25
                  const totalAtk = baseSum + buffSum + shieldAtk
                  // Defender HP = base HP + shields (no D, no synergy)
                  const tSlot = localAttackModal.targetSlot
                  const defSlot = opp?.board?.[tSlot]
                  const defCard = defSlot?.card
                  const baseHP = defCard?.hp ?? 0
                  const shields = defSlot?.muscles ?? 0
                  const totalHP = baseHP + shields
                  return (
                    <>
                      <div className="calc-row"><b>Total attack:</b> {atkCards.map(c => c.atk ?? 0).join(' + ')}{perCardBaseR > 0 ? ` + ${selectedAttackers.length}×${perCardBaseR}` : ''}{perCardPairRSum > 0 ? ` + pairR:${perCardPairRSum}` : ''}{shieldAtkCount > 0 ? ` + ${shieldAtkCount}×0.25` : ''} = <b>{totalAtk}</b></div>
                      <div className="calc-row"><b>Target defense:</b> {`${baseHP}`}{shields > 0 ? ` + ${Array.from({length: shields}).map(() => '1').join(' + ')}` : ''} = <b>{totalHP}</b></div>
                    </>
                  )
                })()}
              </div>

              {/* Controls */}
              <div className="modal-controls">
                <div className="control-row">
                  <div className="info">
                    {localAttackModal.markedShields.length > 0 && `Shields to remove: ${localAttackModal.markedShields.length}`}
                    {localAttackModal.cardMarkedForDestroy && ' • Card marked for destruction'}
                    {localAttackModal.markedShields.length === 0 && !localAttackModal.cardMarkedForDestroy && 'Select shields to remove or mark the card for destruction'}
                  </div>
                </div>
                
                <div className="control-row">
                  <button 
                    className={`toggle ${localAttackModal.cardMarkedForDestroy ? 'on' : ''}`} 
                    onClick={toggleCardDestroy}
                  >
                    {localAttackModal.cardMarkedForDestroy ? '✓ Card will be destroyed' : 'Destroy card'}
                  </button>
                </div>

                <div className="control-row">
                  <button 
                    onClick={confirmAttack} 
                    disabled={localAttackModal.markedShields.length === 0 && !localAttackModal.cardMarkedForDestroy}
                    className="primary"
                  >
                    Send proposal
                  </button>
                  <button onClick={cancelLocalAttack} className="danger">
                    Cancel
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
              <div className="modal-title">Attack Confirmation</div>
              <div className="modal-sub">Attacker: {attack.attacker} → Target: {attack.target.pid} slot {attack.target.slot + 1}</div>
            </div>
            <div className="modal-content">
              {/* Target preview */}
              <div className="modal-card">
                <div className="card-wrap" style={{ opacity: attack.plan.destroyCard ? 0.5 : 1 }}>
                  {attack.target.pid === you?.id ? (
                    <CardView 
                      card={you?.board?.[attack.target.slot]?.card ?? null} 
                      faceUp={you?.board?.[attack.target.slot]?.face_up ?? false}
                      bonusHp={synergyHpBonusForBoard(you?.board)}
                      bonusD={synergyDBonusForBoard(you?.board)}
                      bonusR={synergyRForBoard(you?.board)}
                    />
                  ) : (
                    <CardView 
                      card={opp?.board?.[attack.target.slot]?.card ?? null} 
                      faceUp={opp?.board?.[attack.target.slot]?.face_up ?? false}
                      bonusHp={synergyHpBonusForBoard(opp?.board)}
                      bonusD={synergyDBonusForBoard(opp?.board)}
                      bonusR={synergyRForBoard(opp?.board)}
                    />
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
                <div className="label">Attackers</div>
                <div className="list">{attack.attackerSlots.map(i => `#${i + 1}`).join(', ')}</div>
              </div>

              {/* Calculations: total ATK and defender HP (visible to both sides) */}
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
                  const perCardBaseR = calcRagePerCard(attBoard)
                  const perCardSynergyR = synergyRForBoard(attBoard)
                  const perCardBuff = perCardBaseR + perCardSynergyR
                  const buffSum = (perCardBuff > 0 ? attack.attackerSlots.length * perCardBuff : 0)
                  // Shields on attackers add +0.25 ATK each
                  const shieldAtkCount = attack.attackerSlots.reduce((s, i) => s + (attBoard?.[i]?.muscles ?? 0), 0)
                  const shieldAtk = shieldAtkCount * 0.25
                  const totalAtk = baseSum + buffSum + shieldAtk

                  // Defender HP = base HP + shields (no D, no synergy)
                  const tSlot = attack.target.slot
                  const defSlot = defBoard?.[tSlot]
                  const defCard = defSlot?.card
                  const baseHP = defCard?.hp ?? 0
                  const shields = defSlot?.muscles ?? 0
                  const totalHP = baseHP + shields

                  return (
                    <>
                      <div className="calc-row"><b>Total attack:</b> {atkCards.map(c => c.atk ?? 0).join(' + ')}{perCardBaseR > 0 ? ` + ${attack.attackerSlots.length}×${perCardBaseR}` : ''}{perCardSynergyR > 0 ? ` + ${attack.attackerSlots.length}×${perCardSynergyR}` : ''}{shieldAtkCount > 0 ? ` + ${shieldAtkCount}×0.25` : ''} = <b>{totalAtk}</b></div>
                      <div className="calc-row"><b>Target defense:</b> {`${baseHP}`}{shields > 0 ? ` + ${Array.from({length: shields}).map(() => '1').join(' + ')}` : ''} = <b>{totalHP}</b></div>
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
                        {attack.status === 'planning' ? 'Waiting for the attacker\'s proposal...' : 
                         attack.plan.destroyCard ? 'The attacker proposes to destroy this card.' : 
                         `The attacker proposes to remove ${attack.plan.removeShields} shield(s).`}
                      </div>
                    </div>
                    <div className="control-row">
                      <button 
                        onClick={emitApprove}
                        disabled={attack.status !== 'proposed'}
                        className="primary"
                      >
                        {attack.plan.destroyCard ? 'Agree to destruction' : 'Agree'}
                      </button>
                      <button onClick={emitCancel} className="danger">Cancel</button>
                    </div>
                  </>
                ) : (
                  <div className="control-row">
                    <div className="info">Waiting for defender's response...</div>
                    <button onClick={emitCancel} className="danger">Cancel</button>
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
              <div className="modal-title">No moves available?</div>
              <div className="modal-sub">It seems you have no actions left.</div>
            </div>
            <div className="modal-content" style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              <div className="calc-block">
                <div className="calc-row">You can end your turn or continue if you want to double-check.</div>
              </div>
              <div className="modal-controls">
                <div className="control-row">
                  <button className="primary" onClick={() => { setTurnAlert(false); endTurn() }}>End turn</button>
                  <button onClick={dismissTurnAlert}>Continue</button>
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

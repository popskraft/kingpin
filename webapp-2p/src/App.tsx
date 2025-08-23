import React, { useEffect, useMemo, useRef, useState } from 'react'
import { io, Socket } from 'socket.io-client'
import type { ViewState, Card, Slot, LogEntry } from './types'

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
      </div>
      {card.faction ? (
        <div className="card-row card-faction">Faction: <b>{card.faction}</b></div>
      ) : null}
      <div className="card-notes">{card.notes}</div>
    </div>
  )
}

type DragPayload = { from: 'hand' | 'slot' | 'shelf'; fromIndex: number }

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

function MoneyThumbnails({ count }: { count: number }): JSX.Element {
  const n = Math.max(0, count)
  const shown = Math.min(n, 10)
  return (
    <div className="money-list">
      {Array.from({ length: shown }).map((_, i) => (
        <div key={i} className="money-token" />
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

function SlotView({ slot, onFlip, onDropToSlot, index, editable, onTokenPlus, onTokenMinus, canAddShield, canRemoveShield }:
  { slot: Slot, index: number, editable?: boolean, onFlip?: () => void, onDropToSlot?: (from: DragPayload) => void, onTokenPlus?: () => void, onTokenMinus?: () => void, canAddShield?: boolean, canRemoveShield?: boolean }): JSX.Element {
  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
  }
  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    const data = e.dataTransfer.getData('application/json')
    try {
      const from = JSON.parse(data) as DragPayload
      onDropToSlot?.(from)
    } catch {}
  }
  const draggable = editable && !!slot.card
  const handleDragStart = (e: React.DragEvent) => {
    e.dataTransfer.setData('application/json', JSON.stringify({ from: 'slot', fromIndex: index }))
  }
  return (
    <div className="slot" onDragOver={handleDragOver} onDrop={handleDrop}>
      <div className="shield-thumbs" title={`Shield defenders: ${Math.min(4, Math.max(0, slot.muscles))}`}>
        {Array.from({ length: 4 }).map((_, i) => (
          <div
            key={i}
            className={`shield-thumb ${i < Math.min(4, Math.max(0, slot.muscles)) ? 'filled' : 'empty'}`}
            aria-label={i < Math.min(4, Math.max(0, slot.muscles)) ? 'defender' : 'placeholder'}
          />
        ))}
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
        <div className="card-wrap" draggable={draggable} onDragStart={draggable ? handleDragStart : undefined} onDoubleClick={onFlip}>
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

  // Shared bank: total 36 tokens across both players
  const TOTAL_MONEY_TOKENS = 36
  const yourMoney = you?.tokens?.reserve_money ?? 0
  const oppMoney = opp?.tokens?.reserve_money ?? 0
  const bankMoney = Math.max(0, TOTAL_MONEY_TOKENS - yourMoney - oppMoney)

  const handleDraw = () => socket?.emit('draw', { room: ROOM })
  const handleFlip = (i: number) => socket?.emit('flip_card', { room: ROOM, slotIndex: i })
  const moveFromHandToSlot = (handIndex: number, slotIndex: number) => socket?.emit('move_card', { room: ROOM, from: 'hand', to: 'slot', fromIndex: handIndex, toIndex: slotIndex })
  const moveFromSlotToSlot = (fromIndex: number, toIndex: number) => socket?.emit('move_card', { room: ROOM, from: 'slot', to: 'slot', fromIndex, toIndex })
  const moveFromSlotToHand = (slotIndex: number) => socket?.emit('move_card', { room: ROOM, from: 'slot', to: 'hand', fromIndex: slotIndex })
  const sendSetVisible = (n: number) => socket?.emit('set_visible_slots', { room: ROOM, count: n })
  const addShield = (i: number) => socket?.emit('add_token', { room: ROOM, kind: 'shield', slotIndex: i, count: 1 })
  const removeShield = (i: number) => socket?.emit('remove_token', { room: ROOM, kind: 'shield', slotIndex: i, count: 1 })
  const addMoney = (n: number) => socket?.emit('add_token', { room: ROOM, kind: 'money', count: n })
  const removeMoney = (n: number) => socket?.emit('remove_token', { room: ROOM, kind: 'money', count: n })
  const shuffleDeck = () => socket?.emit('shuffle_deck', { room: ROOM })
  const resetRoom = () => {
    if (confirm('Reset the room and drop all game progress? This cannot be undone.')) {
      socket?.emit('reset_room', { room: ROOM, source })
    }
  }
  const endTurn = () => socket?.emit('end_turn', { room: ROOM })

  const visibleYou = view?.meta?.visible_slots?.you ?? 6

  const handleDropToSlot = (slotIndex: number, from: DragPayload) => {
    if (!from) return
    if (from.from === 'hand') return moveFromHandToSlot(from.fromIndex, slotIndex)
    if (from.from === 'slot') return moveFromSlotToSlot(from.fromIndex, slotIndex)
    if (from.from === 'shelf') return socket?.emit('move_card', { room: ROOM, from: 'shelf', to: 'slot', fromIndex: from.fromIndex, toIndex: slotIndex })
  }

  const onHandDragStart = (i: number, e: React.DragEvent<HTMLDivElement>) => {
    e.dataTransfer.setData('application/json', JSON.stringify({ from: 'hand', fromIndex: i }))
  }

  const onShelfDragStart = (i: number, e: React.DragEvent<HTMLDivElement>) => {
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
          <button id="btn_reset" className="danger" onClick={resetRoom} title="Reset room (drop progress)">Reset</button>
        </div>
      </header>

      <div className="main" id="main">
        <div className="board" id="board">
          <section className={`opponent ${turn && !isYourTurn ? 'active-turn' : ''}`} id="section_opponent">
            <h3 id="opponent_title">Opponent Board ({opp?.id ?? '—'})</h3>
            <OpponentHandThumbnails count={opp?.handCount ?? 0} />
            <div className="slots-grid" id="opp_slots">
              {opp?.board?.map((s: Slot, i: number) => (
                <SlotView key={i} slot={s} index={i} editable={false} />
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
                  onFlip={() => handleFlip(i)}
                  onDropToSlot={(from) => handleDropToSlot(i, from)}
                  canAddShield={(yourMoney ?? 0) > 0}
                  canRemoveShield={(s?.muscles ?? 0) > 0}
                  onTokenPlus={() => { if ((yourMoney ?? 0) > 0) { addShield(i); removeMoney(1) } }}
                  onTokenMinus={() => { if ((s?.muscles ?? 0) > 0) { removeShield(i); addMoney(1) } }}
                />
              ))}
            </div>

            <div className="hand" id="your_hand" onDragOver={(e: React.DragEvent) => e.preventDefault()} onDrop={onHandDrop}>
              <div className="hand-title" id="your_hand_title">Your Hand ({you?.hand?.length ?? 0})</div>
              <div className="hand-cards" id="your_hand_cards">
                {you?.hand?.map((c: Card, i: number) => (
                  <div key={c.id + '_' + i} className="card-wrap" draggable onDragStart={(e: React.DragEvent<HTMLDivElement>) => onHandDragStart(i, e)}>
                    <CardView card={c} faceUp={true} />
                  </div>
                ))}
              </div>
            </div>

            <div className="your-tokens" id="your_tokens">
              <div className="money" id="your_money">
                <button id="btn_money_minus" className="tkn-btn" onClick={() => removeMoney(1)} disabled={yourMoney <= 0}>−</button>
                💰 <AnimatedNumber value={yourMoney} />
                <button id="btn_money_plus" className="tkn-btn" onClick={() => addMoney(1)} disabled={bankMoney <= 0}>＋</button>
                <MoneyThumbnails count={yourMoney} />
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
          <div className="pile-box pile-reserve" id="pile_safe_bank" title={`Всего 36, осталось ${bankMoney}`}>
            <div className="pile-title" id="pile_safe_bank_title">Safe (bank)</div>
            <div className="pile-count" id="pile_safe_bank_count">💰 <AnimatedNumber value={bankMoney} /></div>
            <MoneyThumbnails count={bankMoney} />
          </div>
          <div className="pile-box pile-rejected" id="pile_reserve" onDragOver={(e: React.DragEvent) => e.preventDefault()} onDrop={onShelfDrop}>
            <div className="pile-title" id="pile_reserve_title">Reserve</div>
            <div className="pile-count" id="pile_reserve_count">{view?.shared?.shelfCount ?? 0}</div>
            <div className="shelf-list">
              {view?.shared?.shelf?.map((c, i) => (
                <div key={c.id + '_' + i} className="shelf-item" draggable onDragStart={(e: React.DragEvent<HTMLDivElement>) => onShelfDragStart(i, e)} title={c.notes || c.name}>
                  <div className="shelf-card-name">{c.name}</div>
                  {c.caste && <div className="shelf-card-caste">{c.caste}</div>}
                  {c.faction && <div className="shelf-card-faction">{c.faction}</div>}
                </div>
              ))}
            </div>
          </div>
          <div className="pile-box pile-discard" id="pile_discard" onDragOver={(e: React.DragEvent) => e.preventDefault()} onDrop={onDiscardDrop}>
            <div className="pile-title" id="pile_discard_title">Discard</div>
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

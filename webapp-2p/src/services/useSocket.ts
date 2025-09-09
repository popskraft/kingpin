import { useEffect, useRef, useState } from 'react'
import type { ViewState, AttackMeta } from '../types'
import { connectSocket, Socket } from './socket'

export function useSocket(serverUrl: string, room: string) {
  const [socket, setSocket] = useState<Socket | null>(null)
  const [seat, setSeat] = useState<'P1' | 'P2' | null>(null)
  const [view, setView] = useState<ViewState | null>(null)
  const [oppCursor, setOppCursor] = useState<{ x: number, y: number, visible: boolean }>({ x: 0.5, y: 0.5, visible: false })
  const lastSent = useRef<number>(0)

  useEffect(() => {
    const s = connectSocket(serverUrl)
    setSocket(s)
    s.on('connected', () => {
      s.emit('join_room', { room })
    })
    s.on('joined', (payload: any) => {
      setSeat(payload.seat)
    })
    s.on('state', (st: ViewState) => setView(st))
    s.on('room_full', () => alert('Room is full'))
    s.on('cursor', (payload: any) => {
      if (!payload) return
      const x = Math.max(0, Math.min(1, Number(payload.x) || 0))
      const y = Math.max(0, Math.min(1, Number(payload.y) || 0))
      const visible = !!payload.visible
      setOppCursor({ x, y, visible })
    })
    s.on('error', (payload: any) => {
      if (payload?.msg === 'deck_empty') alert('Deck is empty')
    })
    return () => { s.disconnect() }
  }, [serverUrl, room])

  // Emit helpers
  const draw = () => socket?.emit('draw', { room })
  const flip = (i: number) => socket?.emit('flip_card', { room, slotIndex: i })
  const moveFromHandToSlot = (fromIndex: number, toIndex: number) => socket?.emit('move_card', { room, from: 'hand', to: 'slot', fromIndex, toIndex })
  const moveFromSlotToSlot = (fromIndex: number, toIndex: number) => socket?.emit('move_card', { room, from: 'slot', to: 'slot', fromIndex, toIndex })
  const moveFromSlotToHand = (fromIndex: number) => socket?.emit('move_card', { room, from: 'slot', to: 'hand', fromIndex })
  const setVisibleSlots = (n: number) => socket?.emit('set_visible_slots', { room, count: n })
  const addShieldFromReserve = (i: number) => socket?.emit('add_shield_from_reserve', { room, slotIndex: i, count: 1 })
  const removeShieldToReserve = (i: number) => socket?.emit('remove_shield_to_reserve', { room, slotIndex: i, count: 1 })
  const addShieldOnly = (i: number) => socket?.emit('add_shield_only', { room, slotIndex: i, count: 1 })
  const removeShieldOnly = (i: number) => socket?.emit('remove_shield_only', { room, slotIndex: i, count: 1 })
  const addMoney = (n: number) => socket?.emit('add_token', { room, kind: 'money', count: n })
  const removeMoney = (n: number) => socket?.emit('remove_token', { room, kind: 'money', count: n })
  const shuffleDeck = () => socket?.emit('shuffle_deck', { room })
  const resetRoom = (source?: 'yaml' | 'csv') => socket?.emit('reset_room', { room, source })
  const endTurn = () => socket?.emit('end_turn', { room })

  // Attack API
  const startAttack = (attackerSlots: number[], targetSlot: number) => socket?.emit('start_attack', { room, attackerSlots, targetSlot })
  const updateAttackPlan = (patch: Partial<{ removeShields: number, destroyCard: boolean }>) => socket?.emit('attack_update_plan', { room, ...patch })
  const proposeAttack = () => socket?.emit('attack_propose', { room })
  const acceptAttack = () => socket?.emit('attack_accept', { room })
  const cancelAttack = () => socket?.emit('attack_cancel', { room })

  // Cursor emit (throttled)
  const emitCursor = (x: number, y: number, visible = true) => {
    const now = performance.now()
    if (now - (lastSent.current || 0) < 40) return
    lastSent.current = now
    socket?.emit('cursor', { room, x, y, visible })
  }

  return {
    socket, seat, view, oppCursor,
    draw, flip, moveFromHandToSlot, moveFromSlotToSlot, moveFromSlotToHand,
    setVisibleSlots, addShieldFromReserve, removeShieldToReserve, addShieldOnly, removeShieldOnly,
    addMoney, removeMoney, shuffleDeck, resetRoom, endTurn,
    startAttack, updateAttackPlan, proposeAttack, acceptAttack, cancelAttack,
    emitCursor,
  }
}


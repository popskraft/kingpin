export type Card = {
  id: string
  name: string
  type?: string
  faction?: string
  clan?: string
  hp?: number
  atk?: number
  d?: number
  price?: number
  corruption?: number
  rage?: number
  notes?: string
  // Optional per-card pair synergy bonuses (apply when pair synergy is active on the side)
  pair_hp?: number
  pair_d?: number
  pair_r?: number
}

export type Slot = {
  card: Card | null
  face_up: boolean
  muscles: number
}

export type Tokens = {
  reserve_money: number
  otboy: number
}

export type SideView = {
  id: 'P1' | 'P2'
  hand?: Card[]
  handCount?: number
  board: Slot[]
  tokens: Tokens
}

export type LogEntry = {
  id: number
  t: number
  kind: string
  msg: string
  actor?: 'P1' | 'P2' | null
  turn?: number
  active?: 'P1' | 'P2' | null
}

export type AttackMeta = {
  attacker: 'P1' | 'P2'
  attackerSlots: number[]
  target: { pid: 'P1' | 'P2', slot: number }
  plan: { removeShields: number, destroyCard: boolean }
  status: 'planning' | 'proposed'
} | null

export type SharedView = {
  deckCount: number
  shelfCount: number
  shelf: Card[]
  discardCount: number
}

export type ViewState = {
  you: SideView
  opponent: SideView
  shared: SharedView
  meta: {
    visible_slots: {
      you: number
      opponent: number
    }
    turn?: {
      active: 'P1' | 'P2'
      number: number
      phase: string
    }
    log?: LogEntry[]
    attack?: AttackMeta
  }
}

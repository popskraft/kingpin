export type Card = {
  id: string
  name: string
  type?: string
  faction?: string
  caste?: string
  hp?: number
  atk?: number
  d?: number
  notes?: string
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
  }
}

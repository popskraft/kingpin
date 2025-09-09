import type { Card, Slot } from '../types'

export const parseGivesGlobalAtk = (card: Card | null | undefined): number => {
  if (!card) return 0
  const type = (card.type || '').toLowerCase()
  if (type === 'boss') return 1
  const txt = `${card.name} ${(card.notes || '')}`.toLowerCase()
  if (/\+\s*1\s*atk.*(all)/i.test(txt)) return 1
  if (/(gain|gives|give|grant|grants)\s*\+\s*1\s*atk/i.test(txt)) return 1
  const m = (card.notes || '').match(/rage\s*:\s*([1-9]\d*)/i)
  if (m) return parseInt(m[1], 10)
  return 0
}

export const calcRagePerCard = (sideBoard?: Slot[]): number =>
  (sideBoard || []).reduce((acc, sl) => acc + parseGivesGlobalAtk(sl.card as Card | null), 0)

export const calcGlobalDefend = (sideBoard?: Slot[]): number => {
  const base = (sideBoard || []).reduce((acc, sl) => acc + ((sl.card as Card | null)?.d ?? 0), 0)
  const bossBonus = (sideBoard || []).some(sl => (((sl.card as Card | null)?.type || '').toLowerCase() === 'boss')) ? 1 : 0
  return base + bossBonus
}

export const detectClanSynergyKey = (sideBoard?: Slot[]): 'gangsters' | 'authorities' | 'loners' | null => {
  const clans = (sideBoard || [])
    .map(sl => ((((sl.card as Card | null)?.clan || '') as string).toLowerCase().trim()))
    .filter(Boolean)
  if (clans.length === 0) return null
  const uniq = Array.from(new Set(clans))
  if (uniq.length !== 1) return null
  const c = uniq[0]
  if (c.includes('gang')) return 'gangsters'
  if (c.includes('author')) return 'authorities'
  if (c.includes('loner') || c.includes('solo')) return 'loners'
  return null
}

export const hasPairSynergyForCard = (sideBoard?: Slot[], card?: Card | null): boolean => {
  if (!card) return false
  const board = sideBoard || []
  const cardClan = (((card.clan || '') as string).trim().toLowerCase())
  const cardFaction = (card.faction || '').trim()
  const sameClan = board.filter(sl => ((((sl.card as Card | null)?.clan || '') as string).trim().toLowerCase()) === cardClan).length >= 2
  const sameFaction = board.filter(sl => (((sl.card as Card | null)?.faction || '').trim()) === cardFaction).length >= 2
  return sameClan || sameFaction
}

export const synergyBonusesForCardPair = (sideBoard?: Slot[], card?: Card | null): { hp: number, d: number, r: number } => {
  if (!card) return { hp: 0, d: 0, r: 0 }
  if (!hasPairSynergyForCard(sideBoard, card)) return { hp: 0, d: 0, r: 0 }
  const hp = card.pair_hp ?? 0
  const d = card.pair_d ?? 0
  const r = card.pair_r ?? 0
  return { hp, d, r }
}

export const classifyClan = (clan?: string): 'gangsters' | 'authorities' | 'loners' | null => {
  const c = (clan || '').toLowerCase()
  if (!c) return null
  if (c.includes('gang')) return 'gangsters'
  if (c.includes('author')) return 'authorities'
  if (c.includes('loner') || c.includes('solo')) return 'loners'
  return null
}


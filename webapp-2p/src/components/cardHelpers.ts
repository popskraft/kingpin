import type { Card } from '../types'

export function getCardEmoji(card: Card): string {
  const text = `${card.name} ${(card.type || '')} ${(card.notes || '')}`.toLowerCase()
  const has = (s: string) => text.includes(s)
  if (has('boss') || has('king') || has('queen') || has('leader') || has('chief')) return '👑'
  if (has('assassin') || has('killer') || has('rogue') || has('ninja')) return '🗡️'
  if (has('sniper') || has('shooter') || has('gunner') || has('hitman')) return '🎯'
  if (has('tank') || has('guard') || has('bodyguard') || has('shield')) return '🛡️'
  if (has('doctor') || has('medic') || has('healer') || has('nurse')) return '🩺'
  if (has('engineer') || has('mechanic') || has('tech')) return '🛠️'
  if (has('hacker') || has('cyber')) return '💻'
  if (has('mage') || has('wizard') || has('sorcer')) return '✨'
  if (has('thief') || has('pickpocket') || has('smuggler') || has('spy') || has('scout')) return '🕵️'
  if (has('robot') || has('android') || has('mech')) return '🤖'
  if (has('zombie') || has('undead') || has('ghoul')) return '🧟'
  if (has('priest') || has('monk') || has('cleric')) return '🙏'
  if (has('bard')) return '🎵'
  if (has('fire') || has('flame') || has('pyro')) return '🔥'
  if (has('ice') || has('frost')) return '❄️'
  if (has('poison') || has('toxic') || has('venom')) return '☠️'
  if (has('wolf') || has('tiger') || has('bear') || has('beast')) return '🐾'
  if ((card.atk || 0) >= 5) return '⚔️'
  if ((card.hp || 0) >= 5) return '🛡️'
  return '🃏'
}

export function getClanIcon(clan?: string): string | null {
  const c = (clan || '').toLowerCase()
  if (!c) return null
  if (c.includes('gang')) return '🕶️'
  if (c.includes('author')) return '🏛️'
  if (c.includes('loner')) return '🧍'
  return null
}

export function getClanStripeClass(card: Card): string {
  const clanRaw = ((card.clan || '') as string).toLowerCase()
  const factionRaw = (card.faction || '').toLowerCase()
  if (clanRaw === 'gangsters') return 'gangsters'
  if (clanRaw === 'authorities') return 'authorities'
  if (clanRaw === 'loners') return 'loners'
  if (clanRaw === 'solo') return 'solo'
  if (factionRaw.includes('specialist')) return 'specialists'
  if (factionRaw.includes('head')) return 'heads'
  if (factionRaw.includes('storm')) return 'stormers'
  if (factionRaw.includes('slip')) return 'slippery'
  if (factionRaw) return 'faction'
  return ''
}


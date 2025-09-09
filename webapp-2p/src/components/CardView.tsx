import React from 'react'
import type { Card } from '../types'
import { getCardEmoji, getClanIcon, getClanStripeClass } from './cardHelpers'

export default function CardView({ card, faceUp, bonusHp = 0, bonusD = 0, bonusR = 0, pairInfo = null }:
  { card: Card | null, faceUp: boolean, bonusHp?: number, bonusD?: number, bonusR?: number, pairInfo?: { hp: number, d: number, r: number } | null }) {
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
  const hpDisp = (card.hp ?? 0) + (bonusHp || 0)
  const atkDisp = (card.atk ?? 0)
  const defDisp = (card.d ?? 0) + (bonusD || 0)
  const rageDisp = (card.rage ?? 0) + (bonusR || 0)
  const hasActivePair = !!(pairInfo && ((pairInfo.hp ?? 0) !== 0 || (pairInfo.d ?? 0) !== 0 || (pairInfo.r ?? 0) !== 0))
  const clanRaw = (card.clan || '').toLowerCase()
  const factionRaw = (card.faction || '').toLowerCase()
  const stripeClan = clanRaw === 'gangsters' ? 'gangsters'
    : clanRaw === 'authorities' ? 'authorities'
    : clanRaw === 'loners' ? 'loners'
    : clanRaw === 'solo' ? 'solo'
    : factionRaw.includes('specialist') ? 'specialists'
    : factionRaw.includes('head') ? 'heads'
    : factionRaw.includes('stormer') ? 'stormers'
    : factionRaw.includes('slippery') ? 'slippery'
    : factionRaw ? 'faction'
    : ''
  const clanStripeClass = getClanStripeClass(card)
  
  return (
    <div className="card">
      {clanStripeClass ? <div className={`clan-stripe ${clanStripeClass}`} title={`Clan/Faction: ${clanStripeClass}`} /> : null}
      {hasActivePair && stripeClan ? <div className={`synergy-stripe ${stripeClan}`} title={`Pair synergy: ${stripeClan}`} /> : null}
      <div className="card-title">
        {card.clan ? (
          <span className="clan-icon" title={`Clan: ${card.clan}`}>
            {getCardIcon(card.clan)}
          </span>
        ) : null}
        {card.name}
        {hasActivePair ? (
          <span className="pair-badge" title={`Pair synergy +HP/+D/+R: ${pairInfo!.hp}/${pairInfo!.d}/${pairInfo!.r}`}> 🔗</span>
        ) : null}
      </div>
      <div className="card-illustration" aria-hidden="true">{getCardEmoji(card)}</div>
      <div className="card-row card-stats">
        <span className="stat hp">HP: <b>{hpDisp}</b></span>
        {' '}•{' '}
        <span className="stat atk">ATK: <b>{atkDisp}</b></span>
        {' '}•{' '}
        <span className="stat def">D: <b>{defDisp}</b></span>
        {rageDisp > 0 && (
          <>{' '}•{' '}<span className="stat rage">R: <b>{rageDisp}</b></span></>
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
        <div className="card-row card-faction"><b>{card.faction}</b></div>
      ) : null}
      <div className="card-notes">{card.notes}</div>
    </div>
  )
}

function getCardIcon(clan: string) {
  const icon = getClanIcon(clan)
  return icon ?? ''
}


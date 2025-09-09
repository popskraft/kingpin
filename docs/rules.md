# Kingpin - Game Rules

Strategic card game for 2-3 players with economics, tactical combat, and clan/faction synergy elements.

## Overview

### Victory Condition
Destroy opponent's Boss by reducing its HP to 0 or below.

### Core Principles
- **Clans and factions**: dual synergy system
- **Card bribery**: buying opponent's cards for money
- **Resource management**: 💰/🛡️ tokens and their redistribution
- **Golden Fund**: shared money resource pool (total 40 tokens: 36 base [12 × 3 clans] + 4 additional)

---

## 1. Game Components

> Card Data Note
>
> Single source of truth for all cards is `config/cards.csv` file. The `docs/cards.csv` file has been removed and is no longer used.

### 1.1 Game Zones
- **Player Board**: 6 slots for cards in play (face up)
- **Player Hand**: hidden cards (limit 6 cards total: hand + board)
- **Draw Pile**: shared closed deck (37 cards), source of new cards
- **Reserve Pile**: shared open zone for returned and rejected cards. Initially empty.
- **Player Safe**: money storage (💰 face up)
- **Bank**: shared zone for discarded money tokens
- **Golden Fund**: shared money resource pool (total 40 tokens: 36 base [12 × 3 clans] + 4 additional)
- **Discard Pile**: permanent card removal zone

### 1.2 Tokens (Total 40 tokens: 36 base [12 × 3 clans] + 4 additional)
**Double-sided tokens 💰 ↔ 🛡️**:
- **Money (💰)**: resource for purchases and enhancements
- **Shield (🛡️)**: defensive units (HP=1, ATK=0.25). When the host card participates in an attack, each shield on it contributes +0.25 to that attack's total. Corruption cost to bribe: 3 (gangsters, loners), 2 (authorities)

Note on ammunition: see section 6.1 for how 💰 can be spent to increase attack damage.

### 1.3 Deck Structure
- **18 clan cards**: 6 cards × 3 clans (gangsters, authorities, loners)
- **6 solo cards**: neutral cards with special abilities
- **3 unique cards**: 1 per clan (maximum 1 per player)
- **10 events/actions**: instant effects
- **3 Boss cards**: not in deck, selected at game start

Total: 37 cards in deck (+ 3 Bosses outside deck).

### 1.4 Card Types
- **Boss**: starting card for each player (not in deck)
- **Common**: main deck mass with various parameters
- **Unique**: special cards with global effects
- **Event/Action**: instant effects, don't occupy slots
- **Token**: double-sided 💰/🛡️, not cards

### 1.5 Card Parameters
- **Price**: purchase cost (money not spent, requires amount in safe)
- **Corruption**: bribery cost = Corruption (spent from safe)
- **HP**: health points (card destroyed when HP ≤ 0)
- **Attack**: damage when attacking
- **Clan**: clan (gangsters, authorities, loners) - intra-clan synergies
- **Faction**: faction (heads, specialists, stormers, slippery) - cross-clan synergies
- **Defend (D)**: base shield limit (🛡️) for this card. Effective shield limit = `min(4, D + Authority_auras)`.
- **Rage**: per-card attack aura. Adds +R ATK to every attacking card you control (i.e., a combined attack of N cards gets +N×R). Stacks across multiple sources.
- **Authority**: aura increasing shield limit of all your cards by +N while source is in play
- **Ability**: special card abilities

### 1.6 Notation Legend
- **ATK** — card's base attack
- **HP** — card's health
- **D (Defend)** — card's base shield limit; effective limit: `min(4, D + sum of Authority auras)`
- **S 🛡️ (shield)** — blocks 1 damage; removed when absorbed
- **Rage (R)** — per-attacking-card bonus (+R to each attacking card; combined attacks get +N×R)
- **Authority** — aura that increases shield limit of your cards by +N while source is in play
- **Unbribable** — card cannot be bribed (see Glossary)

---

## 2. Game Setup

### 2.1 Initial Setup
1. Each player draws a Boss card blindly from the 3 Boss cards, then takes it to hand
2. Each player receives 12💰 to their safe
3. Main deck is shuffled and placed as Draw Pile
4. **For 2 players**: 12 tokens of the missing third player + 4 additional → Golden Fund
5. Starting player is determined randomly

Note: At game start, Reserve Pile is empty (0 cards). The entire shared deck (except Bosses) is shuffled and placed in Draw Pile; cards appear in Reserve Pile only through game effects and rules.

### 2.2 Starting Bosses
Source of truth: `config/cards.csv` file. Current values:
- **Gangster Boss**: HP=10, ATK=2, Corruption=12, Defend=3, Rage=1, Authority=1; Clan=gangsters, Faction=heads
- **Authority Boss**: HP=10, ATK=2, Corruption=12, Defend=3, Rage=1, Authority=1; Clan=authorities, Faction=heads
- **Loner Boss**: HP=10, ATK=2, Corruption=12, Defend=3, Rage=1, Authority=1; Clan=loners, Faction=heads

---

## 3. Player Turn Structure

### 3.1 Defense Management Phase (no turn loss)
**Available actions**:
- Redistribute 🛡️ tokens between your cards, not exceeding each card's limit (see 6.4)
- Flip 🛡️ to 💰 and place in safe
- Flip 💰 from safe to 🛡️ and place on cards within their limits
- Add defense when playing new card (can add up to its current limit)

### 3.2 Main Action (choose one)

#### 3.2.1 Buy New Card
- Take card from Draw Pile
- Take card from Reserve Pile if available
- Condition: player's safe amount ≥ card's Price
- Money NOT spent, only checked for availability (availability check rule)
- Placement: to hand or board (if space available)
- When placed on board: card plays immediately + can add defense

Note: This rule intentionally models “credit-based affordability.” Players must hold at least the Price in their safe but do not pay the Price to acquire the card.

#### 3.2.2 Bribe Opponent's Card
- Cost: card's Corruption (spent from player's safe)
- Card moves to buyer's hand
- Limitations: once per turn; cooldown requires skipping at least one of your own turns between bribes (you cannot bribe on two consecutive turns)
- Some cards have bribery protection

#### 3.2.3 Attack Opponent
- Select attacking cards (ATK > 0)
- Combined attack size: up to 3 attackers.
- Exception — Mono-clan board: if all cards on your board share the same clan (see 4.1), you may select any number of your cards to attack together (no limit).
- No same-faction requirement for combined attacks.
- Ammunition (💰 spending): after choosing attackers and before damage calculation, you may spend any amount of 💰 from your safe to add +1.0 ATK per 1💰 to this attack. Spent 💰 is permanently removed from your safe.
- Total damage: ATK + Rage + shields contribution + ammunition (💰)
- Damage absorption order: 🛡️ → card HP
- Destroyed 🛡️ go to shared Bank
- When HP ≤ 0 card is destroyed
- Can attack with multiple cards or combined

#### 3.2.4 Discard Card to Discard Pile
- Remove unwanted card permanently
- Defense from card: redistributed or to safe

### 3.3 Turn Transition
Turn passes to next player clockwise

---

## 4. Synergy Systems

### 4.1 Clan Synergies (active when all cards on your board share the same clan)
- **Gangsters**: +1 R and +1 D (enhanced aggression and defense)
- **Authorities**: +1 HP and +1 D (enhanced durability and defense)
- **Loners**: +1 R and +1 HP (enhanced aggression and durability)

### 4.2 Faction Synergies
- **Heads**: Leadership abilities
- **Specialists**: Economic and technical effects
- **Stormers**: Enhanced attack and aggressive abilities
- **Slippery**: Evasion, stealth, economic manipulation

Distribution guideline (deck composition):
- Heads + Specialists + Stormers together ≈ 80% of all cards
- Slippery ≈ 10%
- Remaining ≈ 10% are neutral/solo or non-factioned cards and events/actions

Note: faction cascades are disabled in this version and will be added later.

---

## 5. Golden Fund
- Tokens are stored in the fund, including destroyed shields
- Players can take money tokens from here according to game conditions
- Tokens in the fund are used as 💰

---

## 6. Combat Rules

### 6.1 Damage Calculation
**Total damage (combined attack)** = sum of attackers' ATK + (Rage per attacking card × number of attacking cards) + (0.25 × total shields on the attacking cards participating in the attack) + ammunition (💰, if any)

- Notes:
  - Rage applies per attacking card. Example: with R=1 and 2 attackers → +2 total.
  - Shield tokens contribute +0.25 each only when their host card participates in the attack.
  - Damage totals can be fractional (no rounding in preview or resolution).
  - Defense equals target HP + actual shields only; no global defense bonus.
- **Damage absorption**: first 🛡️ (1 HP per token), then card HP.
- **Destruction**: when HP ≤ 0 card goes to Discard Pile.

Ammonition (💰) details:
- You may spend any amount of 💰 from your safe to add +1.0 ATK per 1💰 to the current attack.
- Declare spending after selecting attackers, before calculating damage.
- Spent 💰 is removed from your safe immediately.

Example:
- Two attackers: A(ATK=2, 2🛡️) and B(ATK=1, 1🛡️); total Rage on your board = R=1.
- Shields contribution: A contributes +0.5, B contributes +0.25 → +0.75 total.
- Rage contribution: +2 (R=1 per each of 2 attackers).
- Base ATK: 2 + 1 = 3.
- You spend 2💰 as ammunition → +2.
- Total damage = 3 + 2 + 0.75 + 2 = 7.75.

### 6.2 Combined Attacks
- Up to 3 cards can attack together in a combined attack
- Exception — Mono-clan board: if all cards on your board share the same clan (see 4.1), any number of your cards may attack together (no limit)
- No same-faction requirement for combined attacks
- Can remove defense first, then attack
- Can bribe defenders, then attack

### 6.3 Defense Mechanics
- 🛡️ tokens can be redistributed at any moment during turn, respecting card limits
- Some cards provide **Authority** (aura) that increases shield limit of all your cards; **Defend (D)** parameter on each card is its base limit
- Optional variant — Emergency defense: if a card in hand is attacked, defender may, before damage calculation, treat it as if it were on board for defense purposes:
  - temporarily consider the card "on board" (auras, adjacent effects, "Unbribable" etc. apply if applicable before damage)
  - may immediately redistribute 🛡️ to it within its effective limit (see 6.4)
  - damage to the card is calculated considering all such defensive aspects
  - these emergency actions don't consume the main action and are only available when the attack targets a card in hand

### 6.4 Shield Limits (🛡️)
- Effective card shield limit = `min(4, D + player's total Authority_auras)`
- Tokens cannot be added beyond current limit
- If limit increased (Authority aura appeared) — can add up to new limit
- If limit decreased (aura disappeared/reduced) and current shields exceed new limit — excess removed immediately and returned to bank/source
- If choice required, player chooses which shields to remove; for undifferentiated shields — removed automatically

#### Examples
- Card with `D=1`, no Authority aura → limit 1
- Card with `D=1`, with total `Authority=+1` → limit 2
- Card with `D=3`, with total `Authority=+2` → limit 4 (hits global ceiling)

### 6.5 Glossary
- **Unbribable** — card cannot be bribed. Such cards cannot be target of "Bribe Opponent's Card" action (see 3.2.2).
- **Bribery immunity** — use term "Unbribable".

---

## 7. Events and Actions

### 7.1 Mechanics
- Trigger immediately when revealed from deck
- Don't occupy board slots
- Removed from game after resolution
- Can affect economy, defense, attack, or game zones

### 7.2 Effect Types
- **Economic**: token returns, bonuses, penalties
- **Combat**: defense removal, direct damage
- **System**: ability blocking, rule changes
- **Social**: mass effects, resource redistribution

---

## 8. Victory Conditions

### 8.1 Primary Victory
**Boss Destruction**: opponent's Boss HP ≤ 0

### 8.2 Alternative Conditions
Optional variants (not required in the base game):
**Economic Collapse**: opponent cannot perform mandatory actions
**Domination**: control over a critical amount of resources (define thresholds before play)

---

## 9. Strategic Aspects

### 9.1 Strategy Selection
- **Aggressive**: fast attacks, many Stormers
- **Defensive**: shield stacking and Authority auras, resource management
- **Economic**: Specialists, card bribery
- **Hybrid**: balanced development

### 9.2 Resource Management
- Balance between 💰 in safe and 🛡️ on cards
- Planning purchases and bribes
- Using Golden Fund (in 2-player game)

### 9.3 Tactical Decisions
- When to bribe opponent's cards
- How to distribute defense
- Choosing attack targets
- Using combined actions

---

## 10. Notes

### 10.1 Game Balance
- Total cards: 40 (37 in deck + 3 Bosses outside deck). Total tokens: 40.
- Each clan has exactly 8 cards (including Boss) for equal balance
- Factions create cross-clan synergies
- Solo cards provide additional variability
- Golden Fund compensates for missing third player

### 10.3 References
- Cards database (single source of truth): `config/cards.csv`
- Consider adding an auto-generated appendix with card summaries derived from `config/cards.csv`.

### 10.2 Variability
- Can play with 2-3 players
- Different starting Bosses create varied gameplay
- Deck randomness ensures replayability
- Multiple paths to victory
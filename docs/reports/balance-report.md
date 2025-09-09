# Report — Balance (KINGPIN)

## Methodology

**Base Metrics:**
- **CPR (Card Power Rating)**: (HP × 0.8) + (ATK × 1.2) + (Defend × 1.0) + (Rage × 0.5)
- **AV (Ability Value)**: Expert Valuation of Card Abilities
- **CE (Cost Efficiency)**: (CPR + AV) / Price
- **SI (Survivability Index)**: HP + (Defend × 2) - (Corruption Risk × 2)
- **COR (Card Overall Rating)**: (CPR × 0.3) + (AV × 0.4) + (CE × 0.2) + (SI × 0.1)

## Clan Analysis

### AUTHORITIES
- **Number of Cards**: 7
- **Average HP**: 5.3
- **Average ATK**: 2.4
- **Average Price**: 2.9💰
- **Average Corruption**: 1.0
- **Power Rating**: 9.64
- **Ability Value**: 1.21
- **Cost Efficiency**: 3.75
- **Survivability Index**: 9.17
- **OVERALL RATING**: **5.05**
- **Specialization**: 1.38
- **Faction Distribution**: stormers(1), specialists(4), heads(2)

### LONERS
- **Number of cards**: 7
- **Average HP**: 4.0
- **Average ATK**: 2.1
- **Average Price**: 2.1💰
- **Average Corruption**: 2.7
- **Power Rating**: 7.27
- **Ability Value**: 2.19
- **Cost Efficiency**: 5.02
- **Survivability Index**: 5.28
- **OVERALL RATING**: **4.59**
- **Specialization**: 1.84
- **Faction Distribution**: stormers(1), specialists(3), slippery(2), heads(1)

### GANGSTERS
- **Number of cards**: 7
- **Average HP**: 4.3
- **Average ATK**: 1.9
- **Average Price**: 2.7💰
- **Average Corruption**: 2.1
- **Power Rating**: 6.94
- **Ability Value**: 1.00
- **Cost Efficiency**: 3.32
- **Survivability Index**: 5.04
- **OVERALL RATING**: **3.65**
- **Specialization**: 1.95
- **Faction Distribution**: stormers(2), specialists(2), slippery(1), heads(2)

### SOLO
- **Number of cards**: 6
- **Average HP**: 3.3
- **Average ATK**: 2.2
- **Average Price**: 1.8💰
- **Average Corruption**: 3.0
- **Power Rating**: 6.85
- **Ability Value**: 0.50
- **Cost Efficiency**: 4.64
- **Survivability Index**: 4.17
- **OVERALL RATING**: **3.60**
- **Specialization**: 1.46
- **Faction Distribution**: stormers(1), specialists(2), slippery(3)

## Balance Recommendations

**Balance gap**: 1.45
⚠️ **CRITICAL IMBALANCE** — the gap exceeds 1.0

**Weakest group**: solo (3.60)
**Strongest group**: authorities (5.05)

---

## Strategic Analysis of Clans

### AUTHORITIES — Defensive Specialization
**Strengths:**
- High HP (5.3) and Defend (2.4 average)
- Low corruption (1.0) — resistant to bribery
- Best survivability index (9.17)
- Specialization toward specialists (4 cards)

**Recommended Cards:**
- `authority_shieldbearer` (HP 6, Defend 3) — top defender
- `unique_authority` (HP 8, Defend 3) — unique card
- `authority_commissar` (HP 5, Defend 2) — team support

**Strategy:**
- Focus on defense and board control
- Use Authority auras to increase shield limits
- Slow but stable gameplay

### LONERS — Economic Specialization
**Strengths:**
- High cost efficiency (5.02)
- Best ability value (2.19)
- Good faction distribution
- Economic cards: `loner_trader`, `loner_mechanic`

**Recommended Cards:**
- `loner_trader` (Price 1, Corruption 3) — economy card
- `loner_mechanic` (Repair ability) — restoration
- `loner_sniper` (ATK 3, Precision) — accurate strikes

**Strategy:**
- Economic dominance
- Use trade and repair abilities
- Flexibly adapt to the situation

### GANGSTERS — Aggressive Specialization
**Strengths:**
- Good faction distribution
- Specialization toward stormers (2 cards)
- Balanced parameters

**Recommended Cards:**
- `gangster_valkyrie` (ATK 3, Rage 1) — offensive buffer
- `gangster_fighter` (ATK 2, Rage 1) — enter-the-battlefield attack
- `gangster_racketeer` (Extort ability) — economic pressure

**Strategy:**
- Aggressive play leveraging Rage
- Apply economic pressure via bribery
- Combined attacks

### SOLO — Flexible Specialization
**Strengths:**
- Lowest card prices (1.8💰)
- High cost efficiency (4.64)
- Diverse abilities

**Recommended Cards:**
- `solo_killer` (ATK 4, Lethal) — high damage
- `solo_broker` (Economy ability) — economy
- `solo_watchman` (Defend 3, Guard) — defense

**Strategy:**
- Adapt to the opponent’s plan
- Leverage unique abilities
- Flexible deck-building

---

## Faction Analysis

### STORMERS — Offensive Faction
**Traits:**
- High ATK and Rage
- Offensive abilities
- Fast gameplay

**Top Cards:**
- `solo_killer` (ATK 4, Lethal)
- `loner_sniper` (ATK 3, Precision)
- `authority_swat` (ATK 3, Tactical)

### SPECIALISTS — Support Faction
**Traits:**
- High Defend
- Support abilities
- Stable gameplay

**Top Cards:**
- `authority_shieldbearer` (Defend 3, Guard)
- `loner_nurse` (Heal ability)
- `solo_watchman` (Defend 3, Guard)

### SLIPPERY — Economic Faction
**Traits:**
- Economic abilities
- Low price
- Resource manipulation

**Top Cards:**
- `solo_broker` (Economy ability)
- `loner_trader` (Trade ability)
- `gangster_thief` (Steal ability)

### HEADS — Leadership Faction
**Traits:**
- Authority abilities
- High HP
- Global effects

**Top Cards:**
- `unique_authority` (Authority 2)
- `unique_gangster` (Authority 2)
- `unique_loner` (Authority 2)

---

## Recommendations for Improving Balance

### Critical Fixes

1. **Buff SOLO clan:**
   - Increase card HP by 0.5–1.0
   - Add more Authority cards
   - Improve unique card abilities

2. **Nerf AUTHORITIES:**
   - Reduce average HP by 0.5
   - Decrease effectiveness of defensive abilities
   - Increase card prices

3. **Adjust GANGSTERS:**
   - Improve offensive abilities
   - Add more Rage effects
   - Reduce corruption for better survivability

### Long-Term Improvements

1. **Add cards:**
   - More cards per clan (8–10 instead of 6–7)
   - New factions for variety
   - More economic cards

2. **Improve synergies:**
   - Strengthen clan bonuses
   - Add faction combinations
   - Create unique strategies per clan

3. **Balance monitoring:**
   - Regular tournament simulations
   - Analyze win rates by clan
   - Gather player feedback

---

## Calculation Formulas (Current)

### Card Power Rating (CPR)
```python
CPR = (HP × 0.8) + (ATK × 1.2) + (Defend × 1.0) + (Rage × 0.5)
```

### Ability Value (AV)
Ability valuation based on type and effectiveness:
- Economic: +1.5–2.5
- Combat: +1.8–2.2
- Support: +2.0–2.5
- Authority: +1.5–3.0

### Cost Efficiency (CE)
```python
CE = (CPR + AV) / max(Price, 1)
```

### Survivability Index (SI)
```python
SI = HP + (Defend × 2) - (Corruption_Risk × 2)
```

### Card Overall Rating (COR)
```python
COR = (CPR × 0.3) + (AV × 0.4) + (CE × 0.2) + (SI × 0.1)
```

---

## Balance Monitoring

### Key metrics to track:
- Win rates by clan (target: 40–60% each)
- Card popularity in tournaments
- Ability effectiveness
- Game length by clan

### Thresholds:
- **Critical imbalance**: gap > 1.0 in COR
- **Moderate imbalance**: gap 0.5–1.0
- **Good balance**: gap < 0.5

### Monitoring recommendations:
1. Run tournament simulations weekly
2. Analyze top-used cards
3. Collect player feedback
4. Adjust balance based on data

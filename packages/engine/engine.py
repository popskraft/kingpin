from __future__ import annotations
from typing import List, Dict
import random
from pydantic import BaseModel, Field
from .models import GameState, PlayerState, Slot, TurnPhase
from .actions import Action, Attack, Defend, Influence, DiscardCard, Draw


class Ctx(BaseModel):
    state: GameState
    log: List[Dict] = Field(default_factory=list)


def _card_trait(card, key: str, default: int = 0) -> int:
    """Read trait value from card.abl (if dict) or fallback to deprecated card.inf/meta."""
    try:
        # abl can be int or dict
        if isinstance(getattr(card, "abl", None), dict):
            v = card.abl.get(key, default)
            return int(v) if isinstance(v, (int, bool)) or str(v).isdigit() else default
    except Exception:
        pass
    try:
        # fallback to old inf dict
        if isinstance(getattr(card, "inf", None), dict):
            v = card.inf.get(key, default)
            return int(v) if isinstance(v, (int, bool)) or str(v).isdigit() else default
    except Exception:
        pass
    try:
        v = card.meta.get(key, default)
        return int(v) if isinstance(v, (int, bool)) or str(v).isdigit() else default
    except Exception:
        return default


def _maybe_trigger_cascade(ctx: Ctx, pid: str) -> None:
    st = ctx.state
    if not st.config.cascade_enabled:
        return
    p = st.get_player(pid)
    # Limit the number of triggers
    if p.cascade_triggers >= st.config.cascade_max_triggers:
        return
    # Count by factions: need 2-2-2 across three main factions
    counts: Dict[str, int] = {"gangsters": 0, "government": 0, "mercenaries": 0}
    for s in p.slots:
        if s.card and s.card.type != "event":
            fac = str(s.card.faction)
            if fac in counts:
                counts[fac] += 1
    if all(counts[k] >= 2 for k in counts.keys()):
        reward = max(0, st.config.cascade_reward)
        if reward > 0:
            p.tokens.reserve_money += reward
        p.cascade_triggers += 1
        ctx.log.append({"type": "cascade_trigger", "pattern": "2-2-2", "reward": reward, "triggers": p.cascade_triggers})


def _authority_bonus(p: PlayerState) -> int:
    bonus = 0
    for s in p.slots:
        if s.card and getattr(s.card, "type", None) == "boss":
            # прямой вызов локальной функции без динамического импорта
            bonus = max(bonus, _card_trait(s.card, "authority", 0))
    return bonus


def _defense_quota(ctx: Ctx, pid: str, slot: Slot) -> int:
    if not slot.card:
        return 0
    base = max(0, slot.card.d)
    extra = _card_trait(slot.card, "extra_defense", 0)
    p = ctx.state.get_player(pid)
    auth = _authority_bonus(p)
    return max(0, base + extra + auth)


def _on_enter_slot(ctx: Ctx, owner_pid: str, slot_index: int) -> None:
    """Generic hook when a card enters a board slot face-up.
    Applies on-enter effects and then checks cascade.
    """
    p = ctx.state.get_player(owner_pid)
    s = p.slots[slot_index]
    if not s.card:
        return
    card = s.card
    # Data-driven on-enter effects via abl.on_enter
    try:
        on_enter = None
        if isinstance(getattr(card, "abl", None), dict):
            on_enter = card.abl.get("on_enter")
        if isinstance(on_enter, dict):
            # Effect: gain N coins into owner's reserve
            if "gain" in on_enter:
                amount = int(on_enter.get("gain", 0))
                if amount > 0:
                    p.tokens.reserve_money += amount
                ctx.log.append({
                    "type": "on_enter",
                    "card": getattr(card, "id", "unknown"),
                    "effect": "gain",
                    "amount": max(0, int(on_enter.get("gain", 0))),
                    "to": owner_pid,
                })
            # Effect: steal N from opponent reserve (up to available)
            if "steal" in on_enter:
                amount = int(on_enter.get("steal", 0))
                take = 0
                # определяем оппонента заранее для корректного логирования
                op = ctx.state.get_player(ctx.state.opponent_id() if owner_pid == ctx.state.active_player else ctx.state.active_player)
                if amount > 0:
                    take = min(amount, max(0, op.tokens.reserve_money))
                    if take > 0:
                        op.tokens.reserve_money -= take
                        p.tokens.reserve_money += take
                ctx.log.append({
                    "type": "on_enter",
                    "card": getattr(card, "id", "unknown"),
                    "effect": "steal",
                    "amount": take,
                    "from": getattr(op, "id", "OP"),
                    "to": owner_pid,
                })
            # Effect: bribe N — place up to N muscles on this slot, capped by defense quota; free placement
            if "bribe" in on_enter:
                want = int(on_enter.get("bribe", 0))
                placed = 0
                if want > 0:
                    quota = _defense_quota(ctx, owner_pid, s)
                    already = s.muscles
                    can_place = max(0, min(want, max(0, quota - already)))
                    if can_place > 0:
                        s.muscles += can_place
                        placed = can_place
                ctx.log.append({
                    "type": "on_enter",
                    "card": getattr(card, "id", "unknown"),
                    "effect": "bribe",
                    "requested": max(0, want),
                    "placed": placed,
                    "quota": _defense_quota(ctx, owner_pid, s),
                })
    except Exception:
        # Fail-safe: on-enter should never crash the flow
        ctx.log.append({"type": "on_enter_error", "card": getattr(card, "id", "unknown")})
    # After per-card enter effects, attempt cascade check
    _maybe_trigger_cascade(ctx, owner_pid)


def _apply_damage(slot: Slot, damage: int, ctx: Ctx, owner_pid: str):
    if damage <= 0 or slot.card is None:
        return
    # Muscles burn first (block damage first)
    burn = min(slot.muscles, damage)
    slot.muscles -= burn
    # Muscles and spent ammo always go to the discard (otboy) of the defending card's owner
    ctx.state.players[owner_pid].tokens.otboy += burn
    remain = damage - burn
    if remain > 0:
        slot.card.hp -= remain


def _economic_collapse_check(p: PlayerState) -> bool:
    # 0 money and 0 muscles on the board
    total_muscles = sum(s.muscles for s in p.slots)
    return p.tokens.reserve_money == 0 and total_muscles == 0


def resolve_event(ctx: Ctx, card) -> None:
    """Simple event resolution (demo implementation for cards from config)."""
    st = ctx.state
    ap = st.get_player(st.active_player)
    op = st.get_player(st.opponent_id())
    if card.id == "event_plus_cash":
        # Return up to 2 tokens from the active player's discard to reserve
        take = min(2, ap.tokens.otboy)
        ap.tokens.otboy -= take
        ap.tokens.reserve_money += take
        ctx.log.append({"type": "event_plus_cash", "moved": take})
    elif card.id == "event_minus_raid":
        # Remove 1 muscle from the first opponent slot that has any
        for i, s in enumerate(op.slots):
            if s.muscles > 0:
                s.muscles -= 1
                op.tokens.otboy += 1
                ctx.log.append({"type": "event_minus_raid", "slot": i})
                break
    else:
        # Log only for now
        ctx.log.append({"type": "event_unknown", "id": card.id})


def initialize_game(state: GameState):
    # Prepare turn flags
    state.phase = TurnPhase.upkeep
    state.turn_number = 1
    state.flags.update({
        "micro_bribe_used": False,
    })


def next_turn(ctx: Ctx):
    # Switch active player and reset per-turn flags
    ctx.state.active_player = ctx.state.opponent_id()
    ctx.state.turn_number += 1
    ctx.state.phase = TurnPhase.upkeep
    ctx.state.flags["micro_bribe_used"] = False
    # Auto-reveal face-down cards on the active player's board
    ap = ctx.state.get_player(ctx.state.active_player)
    # Reset cascade flags for the new turn
    ap.cascade_used = False
    ap.cascade_triggers = 0
    for s in ap.slots:
        if s.card and not s.face_up:
            s.face_up = True


def apply_action(ctx: Ctx, action: Action) -> Dict:
    st = ctx.state
    ap = st.get_player(st.active_player)
    op = st.get_player(st.opponent_id())

    if isinstance(action, Attack):
        # Spend ammo
        ammo = max(0, min(st.config.ammo_max_bonus, action.ammo_spend))
        if ap.tokens.reserve_money < ammo:
            ammo = ap.tokens.reserve_money
        ap.tokens.reserve_money -= ammo
        ap.tokens.otboy += ammo

        dmg = action.base_damage if action.base_damage > 0 else 0
        # If attacker is specified, add its base attack
        if action.attacker_slot is not None:
            slot_att = ap.slots[action.attacker_slot]
            if slot_att.card:
                dmg += slot_att.card.atk
        dmg += ammo

        # Target selection: prioritize opponent's board; if target_slot is None and board is empty, allow targeting from hand
        opponent_has_board = any(s.card is not None for s in op.slots)
        if action.target_slot is not None:
            # Explicit slot is given — attack the card on the board
            target_slot = op.slots[action.target_slot]
            _apply_damage(target_slot, dmg, ctx, owner_pid=op.id)
        else:
            # No slot specified
            if opponent_has_board:
                # Cannot attack the hand if there are cards on the board
                ctx.log.append({"type": "attack_skipped", "reason": "opponent_has_board"})
            else:
                # Opponent has no cards on board: may target a card from hand (if hand mode enabled)
                if st.config.hand_enabled and op.hand:
                    # By default, attack the first card in hand
                    hand_card = op.hand[0]
                    # Try to emergency-deploy the card to the first free slot and defend it
                    free_idx = None
                    for i, s in enumerate(op.slots):
                        if s.card is None:
                            free_idx = i
                            break
                    if free_idx is not None:
                        target_slot = op.slots[free_idx]
                        target_slot.card = hand_card
                        target_slot.face_up = True
                        # Generic enter-slot hook (applies on-enter and cascade)
                        _on_enter_slot(ctx, op.id, free_idx)
                        # Remove the card from hand (played it forcibly under attack)
                        op.hand.pop(0)
                        # Emergency defense quota: no more than D + extra_defense + authority
                        quota = _defense_quota(ctx, op.id, target_slot)
                        # How many muscles are already on the slot before reinforcement
                        already = target_slot.muscles
                        remaining_quota = max(0, quota - already)

                        # Immediate defense: hire, but not exceeding remaining_quota
                        if remaining_quota > 0 and op.tokens.reserve_money > 0:
                            can_hire = min(op.tokens.reserve_money, remaining_quota)
                            if can_hire > 0:
                                op.tokens.reserve_money -= can_hire
                                target_slot.muscles += can_hire
                                remaining_quota -= can_hire
                        # Reassign muscles from other slots (free), within the remaining quota
                        need_block = max(0, dmg - target_slot.muscles)
                        if need_block > 0 and remaining_quota > 0:
                            for i, s in enumerate(op.slots):
                                if i == free_idx:
                                    continue
                                if s.muscles > 0 and need_block > 0 and remaining_quota > 0:
                                    move = min(s.muscles, need_block, remaining_quota)
                                    if move <= 0:
                                        continue
                                    s.muscles -= move
                                    target_slot.muscles += move
                                    need_block -= move
                                    remaining_quota -= move
                                    ctx.log.append({"type": "reassign_muscles", "from": i, "to": free_idx, "count": move})
                        # Now apply damage in the usual way, considering muscles
                        _apply_damage(target_slot, dmg, ctx, owner_pid=op.id)
                        ctx.log.append({"type": "attack_hand_deployed", "slot": free_idx, "dmg": dmg})
                    else:
                        # If there is no free slot — damage directly to the HP of the card in hand
                        hand_card.hp -= max(0, dmg)
                        if hand_card.hp <= 0:
                            ctx.state.discard_out_of_game.append(hand_card)
                            op.hand.pop(0)
                            ctx.log.append({"type": "attack_hand", "dmg": dmg, "killed": True})
                        else:
                            ctx.log.append({"type": "attack_hand", "dmg": dmg, "killed": False})
                else:
                    ctx.log.append({"type": "attack_skipped", "reason": "no_target"})

        ctx.log.append({"type": "attack", "dmg": dmg})
        st.phase = TurnPhase.resolution

    elif isinstance(action, Defend):
        s = ap.slots[action.target_slot]
        if not s.card:
            return {"error": "No card in slot"}
        quota = _defense_quota(ctx, ap.id, s)
        already = s.muscles
        remaining_quota = max(0, quota - already)
        hire = max(0, min(action.hire_count, remaining_quota, ap.tokens.reserve_money))
        ap.tokens.reserve_money -= hire
        s.muscles += hire
        ctx.log.append({"type": "defend", "hired": hire})
        st.phase = TurnPhase.resolution

    elif isinstance(action, Influence):
        # Micro-bribe
        if action.micro_bribe_target_player and action.micro_bribe_target_slot is not None:
            if st.config.micro_bribe_once_per_turn and st.flags.get("micro_bribe_used", False):
                return {"error": "micro_bribe_already_used"}
            if ap.tokens.reserve_money >= 2:
                ap.tokens.reserve_money -= 2
                ap.tokens.otboy += 2
                tp = st.get_player(action.micro_bribe_target_player)
                ts = tp.slots[action.micro_bribe_target_slot]
                if ts.muscles > 0:
                    ts.muscles -= 1
                    tp.tokens.otboy += 1
                st.flags["micro_bribe_used"] = True
                ctx.log.append({"type": "micro_bribe", "slot": action.micro_bribe_target_slot})
        st.phase = TurnPhase.resolution

    elif isinstance(action, DiscardCard):
        s = ap.slots[action.own_slot]
        if s.card:
            ctx.state.discard_out_of_game.append(s.card)
            s.card = None
            s.muscles = 0
            ctx.log.append({"type": "discard", "slot": action.own_slot})
        st.phase = TurnPhase.resolution

    elif isinstance(action, Draw):
        # Draw as a main action: placement options — hand / face-up slot / face-up shelf
        # Limit: if hand is enabled, drawing is allowed only if (hand + board) < hand_limit
        if st.config.hand_enabled:
            combined = len(ap.hand) + len(ap.active_cards())
            if combined >= ap.hand_limit:
                return {"error": "draw_limit_reached", "combined": combined, "limit": ap.hand_limit}
        if not st.deck:
            # If the deck is empty but there are cards on the shelf — shuffle the shelf into a new face-down deck
            if st.shelf:
                random.shuffle(st.shelf)
                st.deck.extend(st.shelf)
                st.shelf.clear()
                ctx.log.append({"type": "shelf_recycled"})
            if not st.deck:
                return {"error": "deck_empty"}
        card = st.deck.pop(0)
        # Immediate resolution of event cards — they do not occupy a slot/hand/shelf
        if getattr(card, "type", None) == "event":
            resolve_event(ctx, card)
            ctx.log.append({"type": "draw_event", "card": card.id})
            st.phase = TurnPhase.resolution
            return {"phase": st.phase}
        placed = None
        if action.place == "hand":
            if not st.config.hand_enabled:
                return {"error": "hand_disabled"}
            ap.hand.append(card)
            placed = {"zone": "hand"}
        elif action.place == "slot":
            if action.slot_index is None:
                return {"error": "slot_index_required"}
            if action.slot_index < 0 or action.slot_index >= len(ap.slots):
                return {"error": "bad_slot_index"}
            slot = ap.slots[action.slot_index]
            if slot.card is not None:
                return {"error": "slot_not_empty"}
            slot.card = card
            slot.face_up = True
            placed = {"zone": "slot", "slot": action.slot_index}
            # Generic enter-slot hook (applies on-enter and cascade)
            _on_enter_slot(ctx, ap.id, action.slot_index)
        elif action.place == "shelf":
            st.shelf.append(card)
            placed = {"zone": "shelf"}
        else:
            return {"error": "bad_place"}
        ctx.log.append({"type": "draw", "card": card.id, "placed": placed})
        st.phase = TurnPhase.resolution

    # Win by killing the Boss
    # By default — a card of type "boss" on the opponent's board
    boss_dead = False
    for s in op.slots:
        if s.card and s.card.type == "boss" and s.card.hp <= 0:
            boss_dead = True
            break

    result = {"phase": st.phase}

    if st.phase == TurnPhase.resolution:
        # End of turn and check for economic collapse of the active player
        st.phase = TurnPhase.end
        if _economic_collapse_check(ap):
            result["winner"] = st.opponent_id()
            result["win_reason"] = "economic_collapse"
            return result
        if boss_dead:
            result["winner"] = st.active_player
            result["win_reason"] = "boss_killed"
            return result
        # Pass the turn
        next_turn(ctx)
        result["phase"] = st.phase

    return result

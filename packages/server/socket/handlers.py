from __future__ import annotations
from typing import Any, Callable, Dict
import random
from packages.engine.models import GameState


async def connect_handler(sio, sid: str) -> None:
    await sio.emit("connected", {"sid": sid}, to=sid)


async def disconnect_handler(sid: str, rooms: Dict[str, dict], sid_index: Dict[str, Dict[str, str]]) -> None:
    info = sid_index.pop(sid, None)
    if not info:
        return
    room = info.get("room")
    pid = info.get("pid")
    r = rooms.get(room)
    if not r:
        return
    if r["seats"].get(pid) == sid:
        r["seats"][pid] = None


async def set_visible_slots_handler(
    sid: str,
    data: Dict[str, Any],
    rooms: Dict[str, dict],
    sid_index: Dict[str, Dict[str, str]],
    *,
    INIT_VISIBLE_SLOTS: int,
    MAX_SLOTS: int,
    log_fn: Callable[[str, str, str], None],
    emit_views_fn: Callable[[str], Any],
) -> None:
    info = sid_index.get(sid)
    if not info:
        return
    room = info["room"]
    pid = info["pid"]
    r = rooms.get(room)
    if not r:
        return
    try:
        n = int(data.get("count", INIT_VISIBLE_SLOTS))
    except Exception:
        n = INIT_VISIBLE_SLOTS
    n = max(6, min(MAX_SLOTS, n))
    r.setdefault("visible_slots", {"P1": INIT_VISIBLE_SLOTS, "P2": INIT_VISIBLE_SLOTS})
    r["visible_slots"][pid] = n
    log_fn(room, "ui", f"{pid} set visible slots to {n}")
    await emit_views_fn(room)


async def add_shield_from_reserve_handler(
    sid: str,
    data: Dict[str, Any],
    rooms: Dict[str, dict],
    sid_index: Dict[str, Dict[str, str]],
    *,
    log_fn: Callable[[str, str, str], None],
    emit_views_fn: Callable[[str], Any],
) -> None:
    info = sid_index.get(sid)
    if not info:
        return
    room = info["room"]
    pid = info["pid"]
    st: GameState = rooms.get(room, {}).get("state")
    if not st:
        return
    try:
        si = int(data.get("slotIndex", -1))
        count = int(data.get("count", 1))
    except Exception:
        return
    if si < 0 or si >= len(st.players[pid].slots):
        return
    n = max(0, count)
    if n <= 0:
        return
    p = st.players[pid]
    take = min(n, max(0, p.tokens.reserve_money))
    if take <= 0:
        return
    p.tokens.reserve_money -= take
    p.slots[si].muscles += take
    log_fn(room, "token", f"{pid} spent {take} money → +{take} shield on slot {si+1}")
    await emit_views_fn(room)


async def draw_handler(
    sio,
    sid: str,
    data: Dict[str, Any],
    rooms: Dict[str, dict],
    sid_index: Dict[str, Dict[str, str]],
    *,
    log_fn: Callable[[str, str, str], None],
    emit_views_fn: Callable[[str], Any],
) -> None:
    info = sid_index.get(sid)
    if not info:
        return
    room = info["room"]
    pid = info["pid"]
    r = rooms.get(room)
    if not r:
        return
    st: GameState = r["state"]
    if not st.deck:
        if st.shelf:
            random.shuffle(st.shelf)
            st.deck.extend(st.shelf)
            st.shelf.clear()
    if not st.deck:
        await sio.emit("error", {"msg": "deck_empty"}, to=sid)
        return
    card = st.deck.pop(0)
    st.players[pid].hand.append(card)
    log_fn(room, "draw", f"{pid} drew a card")
    await emit_views_fn(room)


async def move_card_handler(
    sio,
    sid: str,
    data: Dict[str, Any],
    rooms: Dict[str, dict],
    sid_index: Dict[str, Dict[str, str]],
    *,
    log_fn: Callable[[str, str, str], None],
    emit_views_fn: Callable[[str], Any],
) -> None:
    info = sid_index.get(sid)
    if not info:
        return
    room = info["room"]
    pid = info["pid"]
    r = rooms.get(room)
    if not r:
        return
    st: GameState = r["state"]
    from_zone = data.get("from")
    to_zone = data.get("to")
    from_index = data.get("fromIndex")
    to_index = data.get("toIndex")

    p = st.players[pid]
    if from_zone == "hand" and to_zone == "slot":
        try:
            card = p.hand.pop(int(from_index))
        except Exception:
            return
        try:
            si = int(to_index)
        except Exception:
            p.hand.append(card)
            return
        if si < 0 or si >= len(p.slots):
            p.hand.append(card)
            return
        slot = p.slots[si]
        if slot.card is None:
            slot.card = card
            slot.face_up = True
            log_fn(room, "play", f"{pid} played {card.name} to slot {si+1}")
        else:
            p.hand.append(slot.card)
            slot.card = card
            slot.face_up = True
            log_fn(room, "swap", f"{pid} swapped card into slot {si+1}")
    elif from_zone == "slot" and to_zone == "hand":
        try:
            si = int(from_index)
        except Exception:
            return
        if si < 0 or si >= len(p.slots):
            return
        slot = p.slots[si]
        if slot.card is None:
            return
        card = slot.card
        p.hand.append(card)
        slot.card = None
        slot.muscles = 0
        log_fn(room, "pickup", f"{pid} picked up {card.name} from slot {si+1}")
    elif from_zone == "slot" and to_zone == "slot":
        try:
            si = int(from_index)
            di = int(to_index)
        except Exception:
            return
        if si < 0 or si >= len(p.slots) or di < 0 or di >= len(p.slots):
            return
        s_from = p.slots[si]
        s_to = p.slots[di]
        s_from.card, s_to.card = s_to.card, s_from.card
        s_from.face_up = True if s_from.card else s_from.face_up
        s_to.face_up = True if s_to.card else s_to.face_up
        log_fn(room, "rearrange", f"{pid} rearranged slots {si+1} ⇄ {di+1}")
    elif to_zone == "discard":
        if from_zone == "hand":
            try:
                card = p.hand.pop(int(from_index))
            except Exception:
                return
            st.discard_out_of_game.append(card)
            log_fn(room, "discard", f"{pid} discarded {card.name} to Discard pile")
        elif from_zone == "slot":
            try:
                si = int(from_index)
            except Exception:
                return
            if si < 0 or si >= len(p.slots):
                return
            slot = p.slots[si]
            if slot.card is None:
                return
            card = slot.card
            st.discard_out_of_game.append(card)
            slot.card = None
            slot.muscles = 0
            log_fn(room, "discard", f"{pid} discarded {card.name} from slot {si+1} to Discard pile")
    elif to_zone == "shelf":
        if from_zone == "hand":
            try:
                card = p.hand.pop(int(from_index))
            except Exception:
                return
            st.shelf.append(card)
            log_fn(room, "shelve", f"{pid} placed {card.name} on Reserve pile")
        elif from_zone == "slot":
            try:
                si = int(from_index)
            except Exception:
                return
            if si < 0 or si >= len(p.slots):
                return
            slot = p.slots[si]
            if slot.card is None:
                return
            card = slot.card
            st.shelf.append(card)
            slot.card = None
            slot.muscles = 0
            log_fn(room, "shelve", f"{pid} moved {card.name} from slot {si+1} to Reserve pile")
    elif from_zone == "shelf" and to_zone == "hand":
        if pid != st.active_player:
            await sio.emit("error", {"msg": "not_your_turn"}, to=sid)
            return
        try:
            idx = int(from_index)
            if idx < 0 or idx >= len(st.shelf):
                return
        except Exception:
            return
        card = st.shelf.pop(idx)
        p.hand.append(card)
        log_fn(room, "unshelve", f"{pid} took {card.name} from Reserve pile to hand")
    elif from_zone == "shelf" and to_zone == "slot":
        if pid != st.active_player:
            await sio.emit("error", {"msg": "not_your_turn"}, to=sid)
            return
        try:
            idx = int(from_index)
            si = int(to_index)
        except Exception:
            return
        if idx < 0 or idx >= len(st.shelf) or si < 0 or si >= len(p.slots):
            return
        slot = p.slots[si]
        if slot.card is not None:
            return
        card = st.shelf.pop(idx)
        slot.card = card
        slot.face_up = True
        log_fn(room, "unshelve", f"{pid} played {card.name} from shelf to slot {si+1}")
    else:
        return
    await emit_views_fn(room)


async def remove_shield_to_reserve_handler(
    sid: str,
    data: Dict[str, Any],
    rooms: Dict[str, dict],
    sid_index: Dict[str, Dict[str, str]],
    *,
    log_fn: Callable[[str, str, str], None],
    emit_views_fn: Callable[[str], Any],
) -> None:
    info = sid_index.get(sid)
    if not info:
        return
    room = info["room"]
    pid = info["pid"]
    st: GameState = rooms.get(room, {}).get("state")
    if not st:
        return
    try:
        si = int(data.get("slotIndex", -1))
        count = int(data.get("count", 1))
    except Exception:
        return
    if si < 0 or si >= len(st.players[pid].slots):
        return
    n = max(0, count)
    if n <= 0:
        return
    p = st.players[pid]
    give = min(n, max(0, p.slots[si].muscles))
    if give <= 0:
        return
    p.slots[si].muscles -= give
    p.tokens.reserve_money += give
    log_fn(room, "token", f"{pid} returned {give} shield → +{give} money to reserve from slot {si+1}")
    await emit_views_fn(room)


async def flip_card_handler(
    sid: str,
    data: Dict[str, Any],
    rooms: Dict[str, dict],
    sid_index: Dict[str, Dict[str, str]],
    *,
    log_fn: Callable[[str, str, str], None],
    emit_views_fn: Callable[[str], Any],
) -> None:
    info = sid_index.get(sid)
    if not info:
        return
    room = info["room"]
    pid = info["pid"]
    st: GameState = rooms.get(room, {}).get("state")
    if not st:
        return
    try:
        si = int(data.get("slotIndex", -1))
    except Exception:
        return
    if si < 0 or si >= len(st.players[pid].slots):
        return
    slot = st.players[pid].slots[si]
    if slot.card is None:
        return
    slot.face_up = not slot.face_up
    name = slot.card.name if slot.card else "Card"
    log_fn(room, "flip", f"{pid} flipped {name} {'up' if slot.face_up else 'down'}")
    await emit_views_fn(room)


async def add_token_handler(
    sid: str,
    data: Dict[str, Any],
    rooms: Dict[str, dict],
    sid_index: Dict[str, Dict[str, str]],
    *,
    log_fn: Callable[[str, str, str], None],
    emit_views_fn: Callable[[str], Any],
) -> None:
    info = sid_index.get(sid)
    if not info:
        return
    room = info["room"]
    pid = info["pid"]
    st: GameState = rooms.get(room, {}).get("state")
    if not st:
        return
    kind = (data.get("kind") or "shield").lower()
    count = int(data.get("count", 1))
    if kind == "shield":
        si = int(data.get("slotIndex", -1))
        if 0 <= si < len(st.players[pid].slots):
            st.players[pid].slots[si].muscles += max(0, count)
            log_fn(room, "token", f"{pid} +{max(0, count)} shield on slot {si+1}")
    elif kind == "money":
        st.players[pid].tokens.reserve_money += max(0, count)
        log_fn(room, "token", f"{pid} +{max(0, count)} money")
    await emit_views_fn(room)


async def remove_token_handler(
    sid: str,
    data: Dict[str, Any],
    rooms: Dict[str, dict],
    sid_index: Dict[str, Dict[str, str]],
    *,
    log_fn: Callable[[str, str, str], None],
    emit_views_fn: Callable[[str], Any],
) -> None:
    info = sid_index.get(sid)
    if not info:
        return
    room = info["room"]
    pid = info["pid"]
    st: GameState = rooms.get(room, {}).get("state")
    if not st:
        return
    kind = (data.get("kind") or "shield").lower()
    count = int(data.get("count", 1))
    if kind == "shield":
        si = int(data.get("slotIndex", -1))
        if 0 <= si < len(st.players[pid].slots):
            st.players[pid].slots[si].muscles = max(0, st.players[pid].slots[si].muscles - max(0, count))
            log_fn(room, "token", f"{pid} -{max(0, count)} shield on slot {si+1}")
    elif kind == "money":
        st.players[pid].tokens.reserve_money = max(0, st.players[pid].tokens.reserve_money - max(0, count))
        log_fn(room, "token", f"{pid} -{max(0, count)} money")
    await emit_views_fn(room)


async def shuffle_deck_handler(
    sid: str,
    rooms: Dict[str, dict],
    sid_index: Dict[str, Dict[str, str]],
    *,
    emit_views_fn: Callable[[str], Any],
    log_fn: Callable[[str, str, str], None],
) -> None:
    info = sid_index.get(sid)
    if not info:
        return
    room = info["room"]
    st: GameState = rooms.get(room, {}).get("state")
    if not st:
        return
    random.shuffle(st.deck)
    log_fn(room, "shuffle", "Deck shuffled")
    await emit_views_fn(room)


async def end_turn_handler(
    sid: str,
    rooms: Dict[str, dict],
    sid_index: Dict[str, Dict[str, str]],
    *,
    emit_views_fn: Callable[[str], Any],
    log_fn: Callable[[str, str, str], None],
) -> None:
    info = sid_index.get(sid)
    if not info:
        return
    room = info["room"]
    pid = info["pid"]
    st: GameState = rooms.get(room, {}).get("state")
    if not st:
        return
    if pid != st.active_player:
        return
    prev = st.active_player
    st.active_player = "P2" if st.active_player == "P1" else "P1"
    st.turn_number += 1
    try:
        from packages.engine.models import TurnPhase
        st.phase = TurnPhase.upkeep
    except Exception:
        pass
    log_fn(room, "end_turn", f"{prev} ended turn. Now {st.active_player}'s turn · Turn {st.turn_number}")
    await emit_views_fn(room)


async def remove_op_shield_handler(
    sid: str,
    data: Dict[str, Any],
    rooms: Dict[str, dict],
    sid_index: Dict[str, Dict[str, str]],
    *,
    log_fn: Callable[[str, str, str], None],
    emit_views_fn: Callable[[str], Any],
) -> None:
    info = sid_index.get(sid)
    if not info:
        return
    room = info["room"]
    pid = info["pid"]
    r = rooms.get(room)
    if not r:
        return
    st: GameState = r["state"]
    op_pid = "P2" if pid == "P1" else "P1"
    try:
        si = int(data.get("slotIndex", -1))
    except Exception:
        return
    if si < 0 or si >= len(st.players[op_pid].slots):
        return
    slot = st.players[op_pid].slots[si]
    if slot.muscles > 0:
        slot.muscles -= 1
        log_fn(room, "token", f"{pid} destroyed 1 shield on {op_pid}'s slot {si+1}")
        await emit_views_fn(room)


async def add_shield_only_handler(
    sid: str,
    data: Dict[str, Any],
    rooms: Dict[str, dict],
    sid_index: Dict[str, Dict[str, str]],
    *,
    log_fn: Callable[[str, str, str], None],
    emit_views_fn: Callable[[str], Any],
) -> None:
    info = sid_index.get(sid)
    if not info:
        return
    room = info["room"]
    pid = info["pid"]
    st: GameState = rooms.get(room, {}).get("state")
    if not st:
        return
    try:
        si = int(data.get("slotIndex", -1))
        count = int(data.get("count", 1))
    except Exception:
        return
    if si < 0 or si >= len(st.players[pid].slots):
        return
    st.players[pid].slots[si].muscles += max(0, count)
    log_fn(room, "token", f"{pid} +{max(0, count)} shield on slot {si+1} (internal)")
    await emit_views_fn(room)


async def remove_shield_only_handler(
    sid: str,
    data: Dict[str, Any],
    rooms: Dict[str, dict],
    sid_index: Dict[str, Dict[str, str]],
    *,
    log_fn: Callable[[str, str, str], None],
    emit_views_fn: Callable[[str], Any],
) -> None:
    info = sid_index.get(sid)
    if not info:
        return
    room = info["room"]
    pid = info["pid"]
    st: GameState = rooms.get(room, {}).get("state")
    if not st:
        return
    try:
        si = int(data.get("slotIndex", -1))
        count = int(data.get("count", 1))
    except Exception:
        return
    if si < 0 or si >= len(st.players[pid].slots):
        return
    st.players[pid].slots[si].muscles = max(0, st.players[pid].slots[si].muscles - max(0, count))
    log_fn(room, "token", f"{pid} -{max(0, count)} shield on slot {si+1} (internal)")
    await emit_views_fn(room)


async def start_attack_handler(
    sid: str,
    data: Dict[str, Any],
    rooms: Dict[str, dict],
    sid_index: Dict[str, Dict[str, str]],
    *,
    emit_views_fn: Callable[[str], Any],
    log_fn: Callable[[str, str, str], None],
) -> None:
    info = sid_index.get(sid)
    if not info:
        return
    room = info["room"]
    pid = info["pid"]
    r = rooms.get(room)
    if not r:
        return
    st: GameState = r["state"]
    try:
        attacker_slots = list({int(i) for i in (data.get("attackerSlots") or [])})
        attacker_slots.sort()
        target_slot = int(data.get("targetSlot", -1))
    except Exception:
        return
    if not attacker_slots:
        return
    op_pid = "P2" if pid == "P1" else "P1"
    if pid != getattr(st, "active_player", None):
        return
    if target_slot < 0 or target_slot >= len(st.players[op_pid].slots):
        return
    if st.players[op_pid].slots[target_slot].card is None:
        return
    valid_attackers: list[int] = []
    for i in attacker_slots:
        if 0 <= i < len(st.players[pid].slots):
            s = st.players[pid].slots[i]
            try:
                atk = int(getattr(s.card, "atk", 0)) if s.card else 0
            except Exception:
                atk = 0
            if s.card is not None and atk > 0:
                valid_attackers.append(i)
    if not valid_attackers:
        return
    try:
        slots = st.players[pid].slots
        board_clans = [((getattr(sl.card, "clan", "") or "").strip()) for sl in slots if getattr(sl, "card", None) is not None]
        mono_clan = (len(board_clans) > 0) and (len(set(board_clans)) == 1) and (board_clans[0] != "")
    except Exception:
        mono_clan = False
    if not mono_clan and len(valid_attackers) > 3:
        valid_attackers = valid_attackers[:3]
    r["attack"] = {
        "attacker": pid,
        "attackerSlots": valid_attackers,
        "target": {"pid": op_pid, "slot": target_slot},
        "plan": {"removeShields": 0, "destroyCard": False},
        "status": "planning",
    }
    log_fn(room, "attack", f"{pid} started attack → {op_pid} slot {target_slot+1} (attackers: {', '.join(str(i+1) for i in valid_attackers)})")
    await emit_views_fn(room)


async def attack_update_plan_handler(
    sid: str,
    data: Dict[str, Any],
    rooms: Dict[str, dict],
    sid_index: Dict[str, Dict[str, str]],
    *,
    emit_views_fn: Callable[[str], Any],
) -> None:
    info = sid_index.get(sid)
    if not info:
        return
    room = info["room"]
    pid = info["pid"]
    r = rooms.get(room)
    if not r or not r.get("attack"):
        return
    atk = r["attack"]
    if atk.get("attacker") != pid:
        return
    st: GameState = r["state"]
    target = atk.get("target") or {}
    tpid = target.get("pid")
    tsi = int(target.get("slot", -1))
    if tpid not in ("P1", "P2") or tsi < 0 or tsi >= len(st.players[tpid].slots):
        return
    slot = st.players[tpid].slots[tsi]
    rm = atk.setdefault("plan", {}).get("removeShields", 0)
    dc = atk.setdefault("plan", {}).get("destroyCard", False)
    if "removeShields" in data:
        try:
            rm = max(0, int(data.get("removeShields", 0)))
        except Exception:
            rm = 0
        rm = min(rm, max(0, slot.muscles))
    if "destroyCard" in data:
        dc = bool(data.get("destroyCard", False))
    atk["plan"] = {"removeShields": rm, "destroyCard": dc}
    await emit_views_fn(room)


async def attack_propose_handler(
    sid: str,
    rooms: Dict[str, dict],
    sid_index: Dict[str, Dict[str, str]],
    *,
    emit_views_fn: Callable[[str], Any],
    log_fn: Callable[[str, str, str], None],
) -> None:
    info = sid_index.get(sid)
    if not info:
        return
    room = info["room"]
    pid = info["pid"]
    r = rooms.get(room)
    if not r or not r.get("attack"):
        return
    atk = r["attack"]
    if atk.get("attacker") != pid:
        return
    atk["status"] = "proposed"
    log_fn(room, "attack", f"{pid} proposed destruction: shields={atk.get('plan', {}).get('removeShields', 0)}, card={atk.get('plan', {}).get('destroyCard', False)}")
    await emit_views_fn(room)


async def attack_accept_handler(
    sid: str,
    rooms: Dict[str, dict],
    sid_index: Dict[str, Dict[str, str]],
    *,
    emit_views_fn: Callable[[str], Any],
    log_fn: Callable[[str, str, str], None],
) -> None:
    info = sid_index.get(sid)
    if not info:
        return
    room = info["room"]
    pid = info["pid"]
    r = rooms.get(room)
    if not r or not r.get("attack"):
        return
    atk = r["attack"]
    attacker = atk.get("attacker")
    target = atk.get("target") or {}
    tpid = target.get("pid")
    tsi = int(target.get("slot", -1))
    if pid != tpid:
        return
    if atk.get("status") != "proposed":
        return
    st: GameState = r["state"]
    if tpid not in ("P1", "P2") or tsi < 0 or tsi >= len(st.players[tpid].slots):
        return
    slot = st.players[tpid].slots[tsi]
    plan = atk.get("plan") or {}
    remove_n = max(0, int(plan.get("removeShields", 0)))
    remove_n = min(remove_n, max(0, slot.muscles))
    destroy_card = bool(plan.get("destroyCard", False))
    if remove_n > 0:
        slot.muscles = max(0, slot.muscles - remove_n)
    if destroy_card and slot.card is not None:
        card = slot.card
        st.discard_out_of_game.append(card)
        slot.card = None
        slot.muscles = 0
        log_fn(room, "destroy", f"{attacker} destroyed {tpid}'s {getattr(card, 'name', 'card')} on slot {tsi+1}")
    else:
        log_fn(room, "attack", f"{attacker} removed {remove_n} shield(s) from {tpid}'s slot {tsi+1}")
    r["attack"] = None
    await emit_views_fn(room)


async def attack_cancel_handler(
    sid: str,
    rooms: Dict[str, dict],
    sid_index: Dict[str, Dict[str, str]],
    *,
    emit_views_fn: Callable[[str], Any],
    log_fn: Callable[[str, str, str], None],
) -> None:
    info = sid_index.get(sid)
    if not info:
        return
    room = info["room"]
    pid = info["pid"]
    r = rooms.get(room)
    if not r or not r.get("attack"):
        return
    atk = r["attack"]
    target = (atk or {}).get("target") or {}
    if pid not in (atk.get("attacker"), target.get("pid")):
        return
    r["attack"] = None
    log_fn(room, "attack", f"{pid} canceled the attack")
    await emit_views_fn(room)


async def cursor_handler(
    sio,
    sid: str,
    data: Dict[str, Any],
    sid_index: Dict[str, Dict[str, str]],
) -> None:
    info = sid_index.get(sid)
    if not info:
        return
    room = info.get("room")
    pid = info.get("pid")
    if not room:
        return
    try:
        x = float(data.get("x", 0))
        y = float(data.get("y", 0))
        visible = bool(data.get("visible", True))
    except Exception:
        x, y, visible = 0.0, 0.0, False
    payload = {"pid": pid, "x": max(0.0, min(1.0, x)), "y": max(0.0, min(1.0, y)), "visible": visible}
    await sio.emit("cursor", payload, room=room, skip_sid=sid)


async def reset_room_handler(
    sio,
    sid: str,
    data: Dict[str, Any],
    rooms: Dict[str, dict],
    sid_index: Dict[str, Dict[str, str]],
    *,
    build_state_cb: Callable[[], tuple[GameState, dict]],
    emit_views_fn: Callable[[str], Any],
    log_fn: Callable[[str, str, str], None],
) -> None:
    info = sid_index.get(sid)
    if not info:
        return
    room = info["room"]
    r = rooms.get(room)
    if not r:
        return
    try:
        req_source = (data.get("source") or "").lower()
    except Exception:
        req_source = ""
    if req_source in {"yaml", "csv"}:
        r["source"] = req_source
    state, cfg = build_state_cb()
    r["state"] = state
    r["cfg"] = cfg
    # reset visible slots
    r["visible_slots"] = {"P1": r.get("visible_slots", {}).get("P1", 6), "P2": r.get("visible_slots", {}).get("P2", 6)}
    # clear log
    r.setdefault("log", []).clear()
    log_fn(room, "load", f"After reset: shelf={len(state.shelf)}, deck={len(state.deck)}")
    log_fn(room, "reset", f"Room reset (source={r.get('source', 'csv').upper()})")
    log_fn(room, "turn_start", f"Game started. Active: {state.active_player} · Turn {state.turn_number}")
    seats = r.get("seats", {})
    for pid, psid in seats.items():
        if psid:
            await sio.emit("joined", {"room": room, "seat": pid, "source": r.get("source", "yaml"), "visibleSlots": r["visible_slots"].get(pid, 6)}, to=psid)
    await emit_views_fn(room)


async def join_room_handler(
    sio,
    sid: str,
    data: Dict[str, Any],
    rooms: Dict[str, dict],
    sid_index: Dict[str, Dict[str, str]],
    *,
    INIT_VISIBLE_SLOTS: int,
    build_state_cb: Callable[[], tuple[GameState, dict]],
    emit_views_fn: Callable[[str], Any],
    log_fn: Callable[[str, str, str], None],
) -> None:
    room = data.get("room", "demo")
    await sio.enter_room(sid, room)
    if room not in rooms:
        state, cfg = build_state_cb()
        rooms[room] = {
            "state": state,
            "cfg": cfg,
            "seats": {"P1": None, "P2": None},
            "visible_slots": {"P1": INIT_VISIBLE_SLOTS, "P2": INIT_VISIBLE_SLOTS},
            "source": "csv",
            "log": [],
        }
        log_fn(room, "load", f"CSV loaded: Reserve pile={len(state.shelf)}, Draw pile={len(state.deck)}")
        log_fn(room, "room", f"Room created (source=CSV)")
        log_fn(room, "turn_start", f"Game started. Active: {state.active_player} · Turn {state.turn_number}")
    r = rooms[room]
    seat: str | None = None
    if r["seats"].get("P1") is None:
        seat = "P1"
    elif r["seats"].get("P2") is None:
        seat = "P2"
    else:
        await sio.emit("room_full", {"room": room}, to=sid)
        return
    r["seats"][seat] = sid
    sid_index[sid] = {"room": room, "pid": seat}
    log_fn(room, "join", f"{seat} joined")
    await sio.emit("joined", {"room": room, "seat": seat, "source": r.get("source", "yaml"), "visibleSlots": r["visible_slots"][seat]}, to=sid)
    await emit_views_fn(room)

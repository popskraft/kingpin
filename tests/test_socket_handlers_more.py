"""
Дополнительные тесты для packages/server/socket/handlers.py, покрывающие
ветки перемещения карт, добора, токенов и цикла атаки.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from packages.server.socket import handlers as H
from tests.test_helpers import TestDataBuilder


def _mk_room_with_state():
    state = TestDataBuilder.create_game_state()
    rooms = {"room": {"state": state, "seats": {"P1": "sid1", "P2": "sid2"}}}
    sid_index = {"sid1": {"room": "room", "pid": "P1"}, "sid2": {"room": "room", "pid": "P2"}}
    return state, rooms, sid_index


@pytest.mark.asyncio
async def test_move_card_hand_to_slot_and_swap():
    sio = AsyncMock()
    log_fn = MagicMock()
    emit_views = AsyncMock()
    state, rooms, idx = _mk_room_with_state()
    # hand -> slot empty -> play
    c1 = TestDataBuilder.create_basic_card("c1")
    state.players["P1"].hand = [c1]
    res = await H.move_card_handler(
        sio, "sid1", {"from": "hand", "to": "slot", "fromIndex": 0, "toIndex": 0}, rooms, idx,
        log_fn=log_fn, emit_views_fn=emit_views
    )
    assert res is None
    assert state.players["P1"].slots[0].card is c1 and state.players["P1"].hand == []
    # hand -> slot occupied -> swap
    c2 = TestDataBuilder.create_basic_card("c2")
    state.players["P1"].hand = [c2]
    res = await H.move_card_handler(
        sio, "sid1", {"from": "hand", "to": "slot", "fromIndex": 0, "toIndex": 0}, rooms, idx,
        log_fn=log_fn, emit_views_fn=emit_views
    )
    assert res is None
    assert state.players["P1"].slots[0].card is c2 and state.players["P1"].hand == [c1]


@pytest.mark.asyncio
async def test_move_card_slot_to_hand_and_slot_to_slot_and_discard_shelf():
    sio = AsyncMock()
    log_fn = MagicMock()
    emit_views = AsyncMock()
    state, rooms, idx = _mk_room_with_state()
    # prepare two slots
    c1 = TestDataBuilder.create_basic_card("c1")
    c2 = TestDataBuilder.create_basic_card("c2")
    state.players["P1"].slots[0].card = c1
    state.players["P1"].slots[1].card = c2
    # slot -> hand
    res = await H.move_card_handler(
        sio, "sid1", {"from": "slot", "to": "hand", "fromIndex": 0}, rooms, idx,
        log_fn=log_fn, emit_views_fn=emit_views
    )
    assert res is None
    assert state.players["P1"].hand[-1] is c1 and state.players["P1"].slots[0].card is None
    # slot -> slot
    res = await H.move_card_handler(
        sio, "sid1", {"from": "slot", "to": "slot", "fromIndex": 1, "toIndex": 0}, rooms, idx,
        log_fn=log_fn, emit_views_fn=emit_views
    )
    assert res is None
    assert state.players["P1"].slots[0].card is c2
    # hand -> discard
    res = await H.move_card_handler(
        sio, "sid1", {"from": "hand", "to": "discard", "fromIndex": 0}, rooms, idx,
        log_fn=log_fn, emit_views_fn=emit_views
    )
    assert res is None
    assert state.discard_out_of_game and state.discard_out_of_game[-1].id == "c1"
    # slot -> shelf
    res = await H.move_card_handler(
        sio, "sid1", {"from": "slot", "to": "shelf", "fromIndex": 0}, rooms, idx,
        log_fn=log_fn, emit_views_fn=emit_views
    )
    assert res is None
    assert state.shelf and state.shelf[-1].id == "c2"
    # shelf -> hand: success only for active player
    state.active_player = "P1"
    res = await H.move_card_handler(
        sio, "sid1", {"from": "shelf", "to": "hand", "fromIndex": 0}, rooms, idx,
        log_fn=log_fn, emit_views_fn=emit_views
    )
    assert res is None
    assert state.players["P1"].hand[-1].id == "c2" and not state.shelf
    # shelf -> slot into empty
    c3 = TestDataBuilder.create_basic_card("c3")
    state.shelf.append(c3)
    res = await H.move_card_handler(
        sio, "sid1", {"from": "shelf", "to": "slot", "fromIndex": 0, "toIndex": 5}, rooms, idx,
        log_fn=log_fn, emit_views_fn=emit_views
    )
    assert res is None
    assert state.players["P1"].slots[5].card is c3


@pytest.mark.asyncio
async def test_move_card_errors_paths():
    sio = AsyncMock()
    log_fn = MagicMock()
    emit_views = AsyncMock()
    state, rooms, idx = _mk_room_with_state()
    # bad request
    out = await H.move_card_handler(sio, "sid1", {"from": "x", "to": "y"}, rooms, idx, log_fn=log_fn, emit_views_fn=emit_views)
    assert out == {"error": "bad_request"}
    # shelf -> hand not your turn
    state.shelf = [TestDataBuilder.create_basic_card("x")]  # non-empty
    state.active_player = "P2"
    out = await H.move_card_handler(sio, "sid1", {"from": "shelf", "to": "hand", "fromIndex": 0}, rooms, idx, log_fn=log_fn, emit_views_fn=emit_views)
    assert out == {"error": "not_your_turn"}
    # flip_card invalid inputs (cover guards)
    await H.flip_card_handler("sid1", {"slotIndex": "x"}, rooms, idx, log_fn=log_fn, emit_views_fn=emit_views)
    await H.flip_card_handler("sid1", {"slotIndex": 99}, rooms, idx, log_fn=log_fn, emit_views_fn=emit_views)
    # remove_shield_to_reserve bad_count and no_shields
    out = await H.remove_shield_to_reserve_handler("sid1", {"slotIndex": 1, "count": 0}, rooms, idx, log_fn=log_fn, emit_views_fn=emit_views)
    assert out == {"error": "bad_count"}
    out = await H.remove_shield_to_reserve_handler("sid1", {"slotIndex": 1, "count": 3}, rooms, idx, log_fn=log_fn, emit_views_fn=emit_views)
    assert out == {"error": "no_shields"}
    # end_turn guard paths
    await H.end_turn_handler("unknown_sid", rooms, idx, emit_views_fn=emit_views, log_fn=log_fn)
    await H.end_turn_handler("sid1", {"no": "room"}, {"other": {}}, emit_views_fn=emit_views, log_fn=log_fn)  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_add_remove_shield_from_reserve_handler():
    log_fn = MagicMock()
    emit_views = AsyncMock()
    state, rooms, idx = _mk_room_with_state()
    p = state.players["P1"]
    p.tokens.reserve_money = 2
    # success add from reserve
    out = await H.add_shield_from_reserve_handler("sid1", {"slotIndex": 0, "count": 2}, rooms, idx, log_fn=log_fn, emit_views_fn=emit_views)
    assert out is None and p.tokens.reserve_money == 0 and p.slots[0].muscles == 2
    # remove to reserve
    out = await H.remove_shield_to_reserve_handler("sid1", {"slotIndex": 0, "count": 1}, rooms, idx, log_fn=log_fn, emit_views_fn=emit_views)
    assert out is None and p.tokens.reserve_money == 1 and p.slots[0].muscles == 1
    # partial spend when requesting more than available
    out = await H.add_shield_from_reserve_handler("sid1", {"slotIndex": 0, "count": 5}, rooms, idx, log_fn=log_fn, emit_views_fn=emit_views)
    assert out is None and p.tokens.reserve_money == 0 and p.slots[0].muscles == 2


@pytest.mark.asyncio
async def test_add_remove_token_money_and_shield():
    log_fn = MagicMock()
    emit_views = AsyncMock()
    state, rooms, idx = _mk_room_with_state()
    # add money
    await H.add_token_handler("sid1", {"kind": "money", "count": 3}, rooms, idx, log_fn=log_fn, emit_views_fn=emit_views)
    assert state.players["P1"].tokens.reserve_money >= 15
    # remove money
    await H.remove_token_handler("sid1", {"kind": "money", "count": 2}, rooms, idx, log_fn=log_fn, emit_views_fn=emit_views)
    # add/remove shield
    await H.add_token_handler("sid1", {"kind": "shield", "slotIndex": 2, "count": 2}, rooms, idx, log_fn=log_fn, emit_views_fn=emit_views)
    await H.remove_token_handler("sid1", {"kind": "shield", "slotIndex": 2, "count": 1}, rooms, idx, log_fn=log_fn, emit_views_fn=emit_views)
    assert state.players["P1"].slots[2].muscles == 1


@pytest.mark.asyncio
async def test_draw_handler_deck_empty_and_shelf_fallback():
    sio = AsyncMock()
    log_fn = MagicMock()
    emit_views = AsyncMock()
    state, rooms, idx = _mk_room_with_state()
    # deck empty and shelf empty -> error
    state.deck = []
    state.shelf = []
    out = await H.draw_handler(sio, "sid1", {}, rooms, idx, log_fn=log_fn, emit_views_fn=emit_views)
    assert out == {"error": "deck_empty"}
    sio.emit.assert_called_with("error", {"msg": "deck_empty"}, to="sid1")
    # shelf fallback: move to deck and draw
    c1 = TestDataBuilder.create_basic_card("d1")
    state.shelf = [c1]
    out = await H.draw_handler(sio, "sid1", {}, rooms, idx, log_fn=log_fn, emit_views_fn=emit_views)
    assert out is None and state.players["P1"].hand and state.players["P1"].hand[-1].id == "d1"


@pytest.mark.asyncio
async def test_start_attack_update_propose_accept_cancel():
    log_fn = MagicMock()
    emit_views = AsyncMock()
    state, rooms, idx = _mk_room_with_state()
    # setup attackers and target
    a1 = TestDataBuilder.create_basic_card("a1")
    a1.atk = 2; a1.clan = "gangsters"
    a2 = TestDataBuilder.create_basic_card("a2")
    a2.atk = 3; a2.clan = "authorities"
    a3 = TestDataBuilder.create_basic_card("a3")
    a3.atk = 1; a3.clan = "loners"
    a4 = TestDataBuilder.create_basic_card("a4")
    a4.atk = 2; a4.clan = "solo"
    state.players["P1"].slots[0].card = a1
    state.players["P1"].slots[1].card = a2
    state.players["P1"].slots[2].card = a3
    state.players["P1"].slots[3].card = a4
    t = TestDataBuilder.create_basic_card("t")
    state.players["P2"].slots[1].card = t
    state.active_player = "P1"
    # Start with 4 attackers, not mono-clan -> trimmed to 3
    out = await H.start_attack_handler("sid1", {"attackerSlots": [0, 1, 2, 3], "targetSlot": 1}, rooms, idx, log_fn=log_fn, emit_views_fn=emit_views)
    assert out is None and rooms["room"]["attack"] is not None
    assert len(rooms["room"]["attack"]["attackerSlots"]) == 3
    # Update plan: set removeShields beyond current muscles and destroyCard
    state.players["P2"].slots[1].muscles = 1
    await H.attack_update_plan_handler("sid1", {"removeShields": 5, "destroyCard": True}, rooms, idx, emit_views_fn=emit_views)
    plan = rooms["room"]["attack"]["plan"]
    assert plan == {"removeShields": 1, "destroyCard": True}
    # Propose destruction
    await H.attack_propose_handler("sid1", rooms, idx, emit_views_fn=emit_views, log_fn=log_fn)
    assert rooms["room"]["attack"]["status"] == "proposed"
    # Accept by defender (P2)
    await H.attack_accept_handler("sid2", rooms, idx, emit_views_fn=emit_views, log_fn=log_fn)
    assert rooms["room"].get("attack") is None
    # Start another attack and cancel by attacker or defender
    state.players["P2"].slots[1].card = TestDataBuilder.create_basic_card("t2")
    await H.start_attack_handler("sid1", {"attackerSlots": [0], "targetSlot": 1}, rooms, idx, log_fn=log_fn, emit_views_fn=emit_views)
    await H.attack_cancel_handler("sid2", rooms, idx, emit_views_fn=emit_views, log_fn=log_fn)
    assert rooms["room"].get("attack") is None

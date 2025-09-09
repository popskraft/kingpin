"""
Branch/guard coverage for packages/server/socket/handlers.py.
Covers early returns and error branches not hit by happy-path tests.
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
async def test_connect_and_disconnect_handlers():
    sio = AsyncMock()
    # connect emits payload to sid
    await H.connect_handler(sio, "sidX")
    sio.emit.assert_awaited_with("connected", {"sid": "sidX"}, to="sidX")

    # disconnect with unknown sid: no crash
    rooms = {"room": {"seats": {"P1": "sid1", "P2": None}}}
    sid_index = {}
    await H.disconnect_handler("unknown", rooms, sid_index)
    # disconnect clears seat only if matches
    sid_index = {"sid1": {"room": "room", "pid": "P1"}}
    await H.disconnect_handler("sid1", rooms, sid_index)
    assert rooms["room"]["seats"]["P1"] is None


@pytest.mark.asyncio
async def test_set_visible_slots_handler_guards_and_casting():
    log_fn = MagicMock()
    emit_views = AsyncMock()
    state, rooms, idx = _mk_room_with_state()
    # bad session
    out = await H.set_visible_slots_handler("bad", {"count": 10}, rooms, idx, INIT_VISIBLE_SLOTS=6, MAX_SLOTS=9, log_fn=log_fn, emit_views_fn=emit_views)
    assert out == {"error": "bad_session"}
    # room not found
    out = await H.set_visible_slots_handler("sid1", {"count": 10}, {}, idx, INIT_VISIBLE_SLOTS=6, MAX_SLOTS=9, log_fn=log_fn, emit_views_fn=emit_views)
    assert out == {"error": "room_not_found"}
    # invalid count (string) -> default INIT_VISIBLE_SLOTS
    out = await H.set_visible_slots_handler("sid1", {"count": "oops"}, rooms, idx, INIT_VISIBLE_SLOTS=6, MAX_SLOTS=9, log_fn=log_fn, emit_views_fn=emit_views)
    assert out is None
    assert rooms["room"]["visible_slots"]["P1"] == 6


@pytest.mark.asyncio
async def test_draw_handler_guards():
    sio = AsyncMock()
    log_fn = MagicMock()
    emit_views = AsyncMock()
    state, rooms, idx = _mk_room_with_state()
    # bad session
    out = await H.draw_handler(sio, "bad", {}, rooms, idx, log_fn=log_fn, emit_views_fn=emit_views)
    assert out == {"error": "bad_session"}
    # room not found
    out = await H.draw_handler(sio, "sid1", {}, {}, idx, log_fn=log_fn, emit_views_fn=emit_views)
    assert out == {"error": "room_not_found"}


@pytest.mark.asyncio
async def test_token_handlers_bad_session_or_room():
    log_fn = MagicMock()
    emit_views = AsyncMock()
    state, rooms, idx = _mk_room_with_state()
    # add_token bad sid
    await H.add_token_handler("bad", {"kind": "money", "count": 1}, rooms, idx, log_fn=log_fn, emit_views_fn=emit_views)
    # remove_token room missing
    await H.remove_token_handler("sid1", {"kind": "money", "count": 1}, {}, idx, log_fn=log_fn, emit_views_fn=emit_views)


@pytest.mark.asyncio
async def test_remove_op_shield_handler_invalid_index():
    log_fn = MagicMock()
    emit_views = AsyncMock()
    state, rooms, idx = _mk_room_with_state()
    # invalid index string -> except path
    await H.remove_op_shield_handler("sid1", {"slotIndex": "no"}, rooms, idx, log_fn=log_fn, emit_views_fn=emit_views)
    # out-of-range index -> return
    await H.remove_op_shield_handler("sid1", {"slotIndex": 99}, rooms, idx, log_fn=log_fn, emit_views_fn=emit_views)


@pytest.mark.asyncio
async def test_move_card_more_errors():
    sio = AsyncMock()
    log_fn = MagicMock()
    emit_views = AsyncMock()
    state, rooms, idx = _mk_room_with_state()
    # slot->discard empty slot -> empty_slot
    out = await H.move_card_handler(sio, "sid1", {"from": "slot", "to": "discard", "fromIndex": 0}, rooms, idx, log_fn=log_fn, emit_views_fn=emit_views)
    assert out == {"error": "empty_slot"}
    # hand->discard bad index -> bad_index
    out = await H.move_card_handler(sio, "sid1", {"from": "hand", "to": "discard", "fromIndex": 5}, rooms, idx, log_fn=log_fn, emit_views_fn=emit_views)
    assert out == {"error": "bad_index"}
    # slot->slot with invalid indices
    out = await H.move_card_handler(sio, "sid1", {"from": "slot", "to": "slot", "fromIndex": -1, "toIndex": 99}, rooms, idx, log_fn=log_fn, emit_views_fn=emit_views)
    assert out == {"error": "bad_index"}


@pytest.mark.asyncio
async def test_attack_update_not_attacker_and_propose_accept_variants():
    log_fn = MagicMock()
    emit_views = AsyncMock()
    state, rooms, idx = _mk_room_with_state()
    # prepare minimal attack state
    a = TestDataBuilder.create_basic_card("a"); a.atk = 1
    t = TestDataBuilder.create_basic_card("t")
    state.players["P1"].slots[0].card = a
    state.players["P2"].slots[0].card = t
    state.active_player = "P1"
    await H.start_attack_handler("sid1", {"attackerSlots": [0], "targetSlot": 0}, rooms, idx, log_fn=log_fn, emit_views_fn=emit_views)
    # not attacker trying to update
    await H.attack_update_plan_handler("sid2", {"removeShields": 1}, rooms, idx, emit_views_fn=emit_views)
    # propose by not attacker should no-op
    await H.attack_propose_handler("sid2", rooms, idx, emit_views_fn=emit_views, log_fn=log_fn)
    # accept with removeShields only branch
    state.players["P2"].slots[0].muscles = 1
    await H.attack_update_plan_handler("sid1", {"removeShields": 1, "destroyCard": False}, rooms, idx, emit_views_fn=emit_views)
    await H.attack_propose_handler("sid1", rooms, idx, emit_views_fn=emit_views, log_fn=log_fn)
    await H.attack_accept_handler("sid2", rooms, idx, emit_views_fn=emit_views, log_fn=log_fn)
    assert rooms["room"].get("attack") is None


@pytest.mark.asyncio
async def test_attack_cancel_no_attack_and_cursor_clamp():
    log_fn = MagicMock()
    emit_views = AsyncMock()
    sio = AsyncMock()
    state, rooms, idx = _mk_room_with_state()
    # cancel with no attack -> no-op
    await H.attack_cancel_handler("sid1", rooms, idx, emit_views_fn=emit_views, log_fn=log_fn)
    # cursor clamp and skip_sid path
    await H.cursor_handler(sio, "sid1", {"x": 5.0, "y": -3.0, "visible": False}, idx)
    sio.emit.assert_awaited_with("cursor", {"pid": "P1", "x": 1.0, "y": 0.0, "visible": False}, room="room", skip_sid="sid1")


@pytest.mark.asyncio
async def test_shuffle_and_add_remove_shield_only_guards():
    log_fn = MagicMock()
    emit_views = AsyncMock()
    state, rooms, idx = _mk_room_with_state()
    # shuffle with bad session should no-op
    await H.shuffle_deck_handler("bad", rooms, idx, emit_views_fn=emit_views, log_fn=log_fn)
    # shield-only bad inputs
    await H.add_shield_only_handler("bad", {"slotIndex": 0, "count": 1}, rooms, idx, log_fn=log_fn, emit_views_fn=emit_views)
    await H.remove_shield_only_handler("bad", {"slotIndex": 0, "count": 1}, rooms, idx, log_fn=log_fn, emit_views_fn=emit_views)
    # flip on empty slot: early return
    await H.flip_card_handler("sid1", {"slotIndex": 0}, rooms, idx, log_fn=log_fn, emit_views_fn=emit_views)


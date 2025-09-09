from __future__ import annotations
from typing import Dict, Optional, List, Tuple
import time
import random
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import socketio
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from engine.loader import load_game, load_yaml_config, build_state_from_config, load_cards_from_csv
from engine.models import GameState, PlayerState, Slot, Card
from engine.engine import initialize_game
from .api.routes import router as api_router
from .services.cards_index import _load_cards_index
from .services.state import _filtered_view, _serialize_slot_for_view
from .services.logging import append_log as _append_log
from .socket.handlers import (
    connect_handler,
    disconnect_handler,
    draw_handler,
    move_card_handler,
    add_shield_from_reserve_handler,
    remove_shield_to_reserve_handler,
    flip_card_handler,
    add_token_handler,
    remove_token_handler,
    shuffle_deck_handler,
    end_turn_handler,
    reset_room_handler,
    join_room_handler,
    remove_op_shield_handler,
    add_shield_only_handler,
    remove_shield_only_handler,
    start_attack_handler,
    attack_update_plan_handler,
    attack_propose_handler,
    attack_accept_handler,
    attack_cancel_handler,
    cursor_handler,
    set_visible_slots_handler,
)
from .services.setup import _build_state_from_csv as _build_state_from_csv_service

# Socket.IO сервер (ASGI)
sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*")
app_fastapi = FastAPI()
app_fastapi.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app_fastapi.include_router(api_router)
app = socketio.ASGIApp(sio, other_asgi_app=app_fastapi)

MAX_SLOTS = 9
INIT_VISIBLE_SLOTS = 6

rooms: Dict[str, dict] = {}
sid_index: Dict[str, Dict[str, str]] = {}


def _build_state_from_csv() -> Tuple[GameState, dict]:
    # Delegate to services implementation, keeping same signature for tests
    return _build_state_from_csv_service(MAX_SLOTS)


# Removed: now using unified ABL parsing from engine.loader


def _log(room_id: str, kind: str, msg: str, actor: Optional[str] = None) -> None:
    # thin wrapper for tests, delegates to services
    _append_log(rooms, room_id, kind, msg, actor)


async def _emit_views(room_id: str) -> None:
    r = rooms.get(room_id)
    if not r:
        return
    st: GameState = r["state"]
    vs = r.get("visible_slots", {"P1": INIT_VISIBLE_SLOTS, "P2": INIT_VISIBLE_SLOTS})
    for pid, sid in r.get("seats", {}).items():
        if not sid:
            continue
        view = _filtered_view(st, pid, visible_you=vs.get(pid, INIT_VISIBLE_SLOTS), visible_op=vs.get("P2" if pid == "P1" else "P1", INIT_VISIBLE_SLOTS))
        # append ephemeral meta
        meta = view.setdefault("meta", {})
        meta["attack"] = r.get("attack")
        # append last N log entries
        meta["log"] = (r.get("log") or [])[-50:]
        await sio.emit("state", view, to=sid)


    # routes moved to api.routes


@sio.event
async def connect(sid, environ):
    await connect_handler(sio, sid)


@sio.event
async def join_room(sid, data):
    room = data.get("room", "demo")
    # Always use CSV as the single source of truth for card data
    # Подключаемся к комнате
    await sio.enter_room(sid, room)

    if room not in rooms:
        # Инициализация комнаты
        state, cfg = _build_state_from_csv()
        rooms[room] = {
            "state": state,
            "cfg": cfg,
            "seats": {"P1": None, "P2": None},
            "visible_slots": {"P1": INIT_VISIBLE_SLOTS, "P2": INIT_VISIBLE_SLOTS},
            "source": "csv",
            "log": [],
        }
        # Debug: log and print Reserve/Draw sizes after CSV load
        try:
            print(f"[ROOM {room}] CSV loaded: Reserve pile={len(state.shelf)}, Draw pile={len(state.deck)}")
        except Exception:
            pass
        _log(room, "load", f"CSV loaded: Reserve pile={len(state.shelf)}, Draw pile={len(state.deck)}")
        _log(room, "room", f"Room created (source=CSV)")
        _log(room, "turn_start", f"Game started. Active: {state.active_player} · Turn {state.turn_number}")

    r = rooms[room]
    # Назначение места
    seat: Optional[str] = None
    if r["seats"].get("P1") is None:
        seat = "P1"
    elif r["seats"].get("P2") is None:
        seat = "P2"
    else:
        await sio.emit("room_full", {"room": room}, to=sid)
        return

    r["seats"][seat] = sid
    sid_index[sid] = {"room": room, "pid": seat}
    _log(room, "join", f"{seat} joined", actor=seat)
    await sio.emit("joined", {"room": room, "seat": seat, "source": r.get("source", "yaml"), "visibleSlots": r["visible_slots"][seat]}, to=sid)
    await _emit_views(room)


@sio.event
async def remove_op_shield(sid, data):
    async def emit(room_id: str):
        await _emit_views(room_id)

    def log(room_id: str, kind: str, msg: str):
        _log(room_id, kind, msg, actor=sid_index.get(sid, {}).get("pid"))

    resp = await remove_op_shield_handler(sid, data, rooms, sid_index, log_fn=log, emit_views_fn=emit)
    if isinstance(resp, dict) and resp.get("error"):
        await sio.emit("error", {"msg": resp["error"]}, to=sid)


@sio.event
async def add_shield_only(sid, data):
    async def emit(room_id: str):
        await _emit_views(room_id)

    def log(room_id: str, kind: str, msg: str):
        _log(room_id, kind, msg, actor=sid_index.get(sid, {}).get("pid"))

    resp = await add_shield_only_handler(sid, data, rooms, sid_index, log_fn=log, emit_views_fn=emit)
    if isinstance(resp, dict) and resp.get("error"):
        await sio.emit("error", {"msg": resp["error"]}, to=sid)


@sio.event
async def remove_shield_only(sid, data):
    async def emit(room_id: str):
        await _emit_views(room_id)

    def log(room_id: str, kind: str, msg: str):
        _log(room_id, kind, msg, actor=sid_index.get(sid, {}).get("pid"))

    resp = await remove_shield_only_handler(sid, data, rooms, sid_index, log_fn=log, emit_views_fn=emit)
    if isinstance(resp, dict) and resp.get("error"):
        await sio.emit("error", {"msg": resp["error"]}, to=sid)


@sio.event
async def add_shield_from_reserve(sid, data):
    async def emit(room_id: str):
        await _emit_views(room_id)

    def log(room_id: str, kind: str, msg: str):
        _log(room_id, kind, msg, actor=sid_index.get(sid, {}).get("pid"))

    resp = await add_shield_from_reserve_handler(sid, data, rooms, sid_index, log_fn=log, emit_views_fn=emit)
    if isinstance(resp, dict) and resp.get("error"):
        await sio.emit("error", {"msg": resp["error"]}, to=sid)


@sio.event
async def remove_shield_to_reserve(sid, data):
    async def emit(room_id: str):
        await _emit_views(room_id)

    def log(room_id: str, kind: str, msg: str):
        _log(room_id, kind, msg, actor=sid_index.get(sid, {}).get("pid"))

    resp = await remove_shield_to_reserve_handler(sid, data, rooms, sid_index, log_fn=log, emit_views_fn=emit)
    if isinstance(resp, dict) and resp.get("error"):
        await sio.emit("error", {"msg": resp["error"]}, to=sid)


@sio.event
async def start_attack(sid, data):
    async def emit(room_id: str):
        await _emit_views(room_id)

    def log(room_id: str, kind: str, msg: str):
        _log(room_id, kind, msg, actor=sid_index.get(sid, {}).get("pid"))

    resp = await start_attack_handler(sid, data, rooms, sid_index, emit_views_fn=emit, log_fn=log)
    if isinstance(resp, dict) and resp.get("error"):
        await sio.emit("error", {"msg": resp["error"]}, to=sid)


@sio.event
async def attack_update_plan(sid, data):
    async def emit(room_id: str):
        await _emit_views(room_id)

    resp = await attack_update_plan_handler(sid, data, rooms, sid_index, emit_views_fn=emit)
    if isinstance(resp, dict) and resp.get("error"):
        await sio.emit("error", {"msg": resp["error"]}, to=sid)


@sio.event
async def attack_propose(sid, data):
    async def emit(room_id: str):
        await _emit_views(room_id)

    def log(room_id: str, kind: str, msg: str):
        _log(room_id, kind, msg, actor=sid_index.get(sid, {}).get("pid"))

    resp = await attack_propose_handler(sid, rooms, sid_index, emit_views_fn=emit, log_fn=log)
    if isinstance(resp, dict) and resp.get("error"):
        await sio.emit("error", {"msg": resp["error"]}, to=sid)


@sio.event
async def attack_accept(sid, data):
    async def emit(room_id: str):
        await _emit_views(room_id)

    def log(room_id: str, kind: str, msg: str):
        _log(room_id, kind, msg, actor=sid_index.get(sid, {}).get("pid"))

    resp = await attack_accept_handler(sid, rooms, sid_index, emit_views_fn=emit, log_fn=log)
    if isinstance(resp, dict) and resp.get("error"):
        await sio.emit("error", {"msg": resp["error"]}, to=sid)


@sio.event
async def attack_cancel(sid, data):
    async def emit(room_id: str):
        await _emit_views(room_id)

    def log(room_id: str, kind: str, msg: str):
        _log(room_id, kind, msg, actor=sid_index.get(sid, {}).get("pid"))

    resp = await attack_cancel_handler(sid, rooms, sid_index, emit_views_fn=emit, log_fn=log)
    if isinstance(resp, dict) and resp.get("error"):
        await sio.emit("error", {"msg": resp["error"]}, to=sid)


@sio.event
async def cursor(sid, data):
    await cursor_handler(sio, sid, data, sid_index)


@sio.event
async def disconnect(sid):
    await disconnect_handler(sid, rooms, sid_index)


@sio.event
async def draw(sid, data):
    async def emit(room_id: str):
        await _emit_views(room_id)

    def log(room_id: str, kind: str, msg: str):
        _log(room_id, kind, msg, actor=sid_index.get(sid, {}).get("pid"))

    resp = await draw_handler(sio, sid, data, rooms, sid_index, log_fn=log, emit_views_fn=emit)
    if isinstance(resp, dict) and resp.get("error") and resp["error"] != "deck_empty":
        await sio.emit("error", {"msg": resp["error"]}, to=sid)


@sio.event
async def move_card(sid, data):
    async def emit(room_id: str):
        await _emit_views(room_id)

    def log(room_id: str, kind: str, msg: str):
        _log(room_id, kind, msg, actor=sid_index.get(sid, {}).get("pid"))

    resp = await move_card_handler(sio, sid, data, rooms, sid_index, log_fn=log, emit_views_fn=emit)
    if isinstance(resp, dict) and resp.get("error"):
        await sio.emit("error", {"msg": resp["error"]}, to=sid)


@sio.event
async def end_turn(sid, data):
    info = sid_index.get(sid)
    if not info:
        return
    room = info["room"]
    pid = info["pid"]
    st: GameState = rooms.get(room, {}).get("state")
    if not st:
        return
    if pid != st.active_player:
        await sio.emit("error", {"msg": "not_your_turn"}, to=sid)
        return
    prev = st.active_player
    st.active_player = "P2" if st.active_player == "P1" else "P1"
    st.turn_number += 1
    # Сброс фазы к началу хода
    try:
        from packages.engine.models import TurnPhase
        st.phase = TurnPhase.upkeep
    except Exception:
        pass
    _log(room, "end_turn", f"{prev} ended turn. Now {st.active_player}'s turn · Turn {st.turn_number}")
    await _emit_views(room)


@sio.event
async def flip_card(sid, data):
    async def emit(room_id: str):
        await _emit_views(room_id)

    def log(room_id: str, kind: str, msg: str):
        _log(room_id, kind, msg, actor=sid_index.get(sid, {}).get("pid"))

    resp = await flip_card_handler(sid, data, rooms, sid_index, log_fn=log, emit_views_fn=emit)
    if isinstance(resp, dict) and resp.get("error"):
        await sio.emit("error", {"msg": resp["error"]}, to=sid)


@sio.event
async def add_token(sid, data):
    async def emit(room_id: str):
        await _emit_views(room_id)

    def log(room_id: str, kind: str, msg: str):
        _log(room_id, kind, msg, actor=sid_index.get(sid, {}).get("pid"))

    resp = await add_token_handler(sid, data, rooms, sid_index, log_fn=log, emit_views_fn=emit)
    if isinstance(resp, dict) and resp.get("error"):
        await sio.emit("error", {"msg": resp["error"]}, to=sid)


@sio.event
async def remove_token(sid, data):
    async def emit(room_id: str):
        await _emit_views(room_id)

    def log(room_id: str, kind: str, msg: str):
        _log(room_id, kind, msg, actor=sid_index.get(sid, {}).get("pid"))

    resp = await remove_token_handler(sid, data, rooms, sid_index, log_fn=log, emit_views_fn=emit)
    if isinstance(resp, dict) and resp.get("error"):
        await sio.emit("error", {"msg": resp["error"]}, to=sid)


@sio.event
async def shuffle_deck(sid, data):
    async def emit(room_id: str):
        await _emit_views(room_id)

    def log(room_id: str, kind: str, msg: str):
        _log(room_id, kind, msg)

    resp = await shuffle_deck_handler(sid, rooms, sid_index, emit_views_fn=emit, log_fn=log)
    if isinstance(resp, dict) and resp.get("error"):
        await sio.emit("error", {"msg": resp["error"]}, to=sid)


@sio.event
async def set_visible_slots(sid, data):
    async def emit(room_id: str):
        await _emit_views(room_id)

    def log(room_id: str, kind: str, msg: str):
        _log(room_id, kind, msg, actor=sid_index.get(sid, {}).get("pid"))

    await set_visible_slots_handler(
        sid,
        data,
        rooms,
        sid_index,
        INIT_VISIBLE_SLOTS=INIT_VISIBLE_SLOTS,
        MAX_SLOTS=MAX_SLOTS,
        log_fn=log,
        emit_views_fn=emit,
    )


@sio.event
async def reset_room(sid, data):
    async def emit(room_id: str):
        await _emit_views(room_id)

    def log(room_id: str, kind: str, msg: str):
        _log(room_id, kind, msg)

    await reset_room_handler(
        sio,
        sid,
        data,
        rooms,
        sid_index,
        build_state_cb=_build_state_from_csv,
        emit_views_fn=emit,
        log_fn=log,
    )

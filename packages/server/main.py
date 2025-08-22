from __future__ import annotations
from typing import Dict
from fastapi import FastAPI
import socketio
from packages.engine.loader import load_game
from packages.engine.engine import Ctx, apply_action, initialize_game
from packages.engine.actions import Attack, Defend, Influence, DiscardCard
from packages.engine.models import Slot, Card

# Socket.IO сервер (ASGI)
sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*")
app_fastapi = FastAPI()
app = socketio.ASGIApp(sio, other_asgi_app=app_fastapi)


rooms: Dict[str, dict] = {}


def _place_starters(state, cfg):
    starters = cfg.get("starters", {})
    for pid, cards in starters.items():
        for i, cdata in enumerate(cards):
            if i >= len(state.players[pid].slots):
                break
            state.players[pid].slots[i] = Slot(card=Card(**cdata), face_up=True, muscles=0)


@app_fastapi.get("/health")
async def health():
    return {"ok": True}


@sio.event
async def connect(sid, environ):
    await sio.emit("connected", {"sid": sid}, to=sid)


@sio.event
async def join(sid, data):
    room = data.get("room", "demo")
    await sio.enter_room(sid, room)

    if room not in rooms:
        state, cfg = load_game("config/default.yaml")
        _place_starters(state, cfg)
        initialize_game(state)
        rooms[room] = {"state": state, "cfg": cfg, "ctx": Ctx(state=state, log=[])}

    await sio.emit("state", rooms[room]["state"].model_dump(), room=room)


@sio.event
async def action(sid, data):
    room = data.get("room", "demo")
    r = rooms.get(room)
    if not r:
        return
    kind = data.get("kind")

    act = None
    if kind == "attack":
        act = Attack(**data)
    elif kind == "defend":
        act = Defend(**data)
    elif kind == "influence":
        act = Influence(**data)
    elif kind == "discard":
        act = DiscardCard(**data)

    if act is None:
        return

    res = apply_action(r["ctx"], act)
    await sio.emit("state", r["state"].model_dump() | {"last": res}, room=room)

from __future__ import annotations
from typing import Dict, Optional
import time
from packages.engine.models import GameState


def append_log(rooms: Dict[str, dict], room_id: str, kind: str, msg: str, actor: Optional[str] = None) -> None:
    room = rooms.get(room_id)
    if not room:
        return
    st: GameState = room.get("state")
    entry = {
        "id": len(room.setdefault("log", [])) + 1,
        "t": time.time(),
        "kind": kind,
        "msg": msg,
        "actor": actor,
        "turn": getattr(st, "turn_number", 0),
        "active": getattr(st, "active_player", None),
    }
    room["log"].append(entry)


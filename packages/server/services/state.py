from __future__ import annotations
from typing import Dict

from packages.engine.models import GameState, Slot


def _serialize_slot_for_view(s: Slot, for_owner: bool) -> dict:
    if for_owner:
        return s.model_dump()
    # For opponent, only show face-up cards; hide face-down as empty
    if s.face_up and s.card is not None:
        return s.model_dump()
    return {"card": None, "face_up": False, "muscles": 0}


def _filtered_view(state: GameState, viewer_pid: str, visible_you: int, visible_op: int) -> dict:
    you = state.players[viewer_pid]
    op_pid = "P2" if viewer_pid == "P1" else "P1"
    op = state.players[op_pid]
    you_board = [_serialize_slot_for_view(s, True) for s in you.slots[:visible_you]]
    op_board = [_serialize_slot_for_view(s, False) for s in op.slots[:visible_op]]
    return {
        "you": {
            "id": viewer_pid,
            "hand": [c.model_dump() for c in you.hand],
            "board": you_board,
            "tokens": you.tokens.model_dump(),
        },
        "opponent": {
            "id": op_pid,
            # hide opponent hand identities; only provide count
            "board": op_board,
            "handCount": len(op.hand),
            "tokens": op.tokens.model_dump(),
        },
        "shared": {
            "deckCount": len(state.deck),
            "shelfCount": len(state.shelf),
            "shelf": [c.model_dump() for c in state.shelf],
            "discardCount": len(state.discard_out_of_game),
        },
        "meta": {
            "visible_slots": {"you": visible_you, "opponent": visible_op},
            "turn": {
                "active": state.active_player,
                "number": state.turn_number,
                "phase": state.phase.value if hasattr(state.phase, "value") else str(state.phase),
            },
        },
    }


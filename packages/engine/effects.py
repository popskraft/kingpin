from __future__ import annotations
from typing import Callable, Dict, Any

EffectFunc = Callable[[Any, dict], None]

_registry: Dict[str, EffectFunc] = {}


def register(effect_id: str):
    def _wrap(fn: EffectFunc):
        _registry[effect_id] = fn
        return fn
    return _wrap


def get(effect_id: str) -> EffectFunc | None:
    return _registry.get(effect_id)


# Example effects (placeholders)
@register("heal_self_1")
def effect_heal_self_1(ctx, payload):
    # payload: {"player": "P1", "slot": 0}
    slot = ctx.state.get_slot(payload["player"], payload["slot"])
    if slot.card:
        slot.card.hp += 1
        ctx.log.append({"type": "effect", "id": "heal_self_1", "delta": 1})

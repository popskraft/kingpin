from __future__ import annotations
from typing import Optional, Literal
from pydantic import BaseModel


class Action(BaseModel):
    kind: str


class Attack(Action):
    kind: Literal["attack"] = "attack"
    target_player: Literal["P1", "P2"]
    target_slot: Optional[int] = None  # None => target from hand if allowed by rules
    ammo_spend: int = 0  # 0..config.ammo_max_bonus
    base_damage: int = 0  # if 0, use attacker's atk (when attacker specified in meta)
    # meta fields
    attacker_slot: Optional[int] = None  # who is attacking from active player board


class Defend(Action):
    kind: Literal["defend"] = "defend"
    target_slot: int
    hire_count: int  # must be <= card.d


class Influence(Action):
    kind: Literal["influence"] = "influence"
    # for now just supports micro-bribe
    micro_bribe_target_player: Optional[Literal["P1", "P2"]] = None
    micro_bribe_target_slot: Optional[int] = None


class DiscardCard(Action):
    kind: Literal["discard"] = "discard"
    own_slot: int


class Draw(Action):
    kind: Literal["draw"] = "draw"
    # Placement option after drawing a card from the deck
    # hand: put to hand (hidden)
    # slot: place immediately to a free slot face-up (requires slot_index)
    # shelf: reveal to open shelf (face-up pool)
    place: Literal["hand", "slot", "shelf"]
    slot_index: Optional[int] = None  # required when place == "slot"

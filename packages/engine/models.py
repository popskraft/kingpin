from __future__ import annotations
from enum import Enum
from typing import List, Dict, Optional, Literal
from pydantic import BaseModel, Field, root_validator


class CardType(str, Enum):
    boss = "boss"
    unique = "unique"
    common = "common"
    event = "event"
    action = "action"  # instant actions/events
    token = "token"  # double-sided tokens


class Faction(str, Enum):
    neutral = "neutral"
    # Add factions in config and map to strings


class PaidAbility(BaseModel):
    id: str
    cost: int = 1
    cooldown_per_turn: int = 1  # default: once per turn
    effect_id: str


class Card(BaseModel):
    id: str
    name: str
    type: CardType = CardType.common
    faction: Faction | str = Faction.neutral
    # Primary terminology
    clan: Optional[str] = None
    # Deprecated legacy field kept for backward compatibility
    caste: Optional[str] = None
    hp: int = 1
    atk: int = 0
    d: int = 0  # base defend (shield limit)
    price: int = 0  # card price
    corruption: int = 0  # corruption cost (bribe)
    rage: int = 0  # rage aura
    # Ability: numeric value or dict of traits (incl. nested). String values allowed
    # for special markers like "all": {"anti_corruption": "all"}
    abl: int | Dict[str, int | str | dict] = 0
    # DEPRECATED: legacy field name; supported for backward compatibility and migrated to abl
    inf: Optional[int | Dict[str, int]] = None
    paid: List[PaidAbility] = Field(default_factory=list)
    # Extra fields for flexibility (DEPRECATED: move keys into abl dict)
    meta: Dict[str, int | str | bool] = Field(default_factory=dict)
    # Short player-facing description (for card/UI display)
    notes: str = ""
    # Per-card bonuses when pair synergy is active on the side. Optional, default 0.
    pair_hp: int = 0
    pair_d: int = 0
    pair_r: int = 0

    @root_validator(pre=True)
    def _migrate_inf_to_abl(cls, values):  # type: ignore[override]
        # If abl is missing but legacy inf present — migrate it
        if "abl" not in values and "inf" in values:
            values["abl"] = values.get("inf")
        # Normalize typo for old faction value: goverment -> government
        fac = values.get("faction")
        if isinstance(fac, str) and fac == "goverment":
            values["faction"] = "government"
        # Populate legacy 'caste' from 'clan' if only clan provided (and vice versa) for compatibility
        clan = values.get("clan")
        caste = values.get("caste")
        if clan and not caste:
            values["caste"] = clan
        if caste and not clan:
            values["clan"] = caste
        return values


class Slot(BaseModel):
    card: Optional[Card] = None
    face_up: bool = True
    muscles: int = 0  # shields on the card


class TokenPools(BaseModel):
    reserve_money: int = 12  # default starting amount
    otboy: int = 0


class PlayerState(BaseModel):
    id: Literal["P1", "P2"]
    hand_limit: int = 0
    hand: List[Card] = Field(default_factory=list)
    slots: List[Slot] = Field(default_factory=lambda: [Slot() for _ in range(6)])
    tokens: TokenPools = Field(default_factory=TokenPools)
    cascade_used: bool = False
    cascade_triggers: int = 0  # 0..3

    def active_cards(self) -> List[Card]:
        return [s.card for s in self.slots if s.card is not None]


class TurnPhase(str, Enum):
    upkeep = "upkeep"
    main = "main"
    resolution = "resolution"
    end = "end"


class GameConfig(BaseModel):
    hand_enabled: bool = False
    events_enabled: bool = True
    micro_bribe_once_per_turn: bool = True
    ammo_max_bonus: int = 2
    cascade_enabled: bool = True
    cascade_reward: int = 2
    cascade_max_triggers: int = 3


class GameState(BaseModel):
    seed: int = 0
    config: GameConfig = Field(default_factory=GameConfig)
    deck: List[Card] = Field(default_factory=list)  # кладовая (закрытая)
    shelf: List[Card] = Field(default_factory=list)  # полка (открытая)
    discard_out_of_game: List[Card] = Field(default_factory=list)
    players: Dict[str, PlayerState] = Field(default_factory=dict)
    active_player: Literal["P1", "P2"] = "P1"
    phase: TurnPhase = TurnPhase.upkeep
    turn_number: int = 1
    flags: Dict[str, bool] = Field(default_factory=dict)  # временные ограничения/эффекты

    def opponent_id(self) -> str:
        return "P2" if self.active_player == "P1" else "P1"

    def get_player(self, pid: str) -> PlayerState:
        return self.players[pid]

    def get_slot(self, pid: str, idx: int) -> Slot:
        return self.players[pid].slots[idx]

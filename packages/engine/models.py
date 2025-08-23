from __future__ import annotations
from enum import Enum
from typing import List, Dict, Optional, Literal
from pydantic import BaseModel, Field, root_validator


class CardType(str, Enum):
    boss = "boss"
    unique = "unique"
    common = "common"
    event = "event"
    action = "action"  # мгновенные действия/события


class Faction(str, Enum):
    neutral = "neutral"
    # Добавляйте фракции в конфиге и мапьте к строкам


class PaidAbility(BaseModel):
    id: str
    cost: int = 1
    cooldown_per_turn: int = 1  # по умолчанию 1 раз в ход
    effect_id: str


class Card(BaseModel):
    id: str
    name: str
    type: CardType = CardType.common
    faction: Faction | str = Faction.neutral
    caste: Optional[str] = None
    hp: int = 1
    atk: int = 0
    d: int = 0  # темп найма Братков
    # Способность: числовое значение или словарь трейтов (в т.ч. вложенные). Допускаем строковые значения
    # для спец-маркеров вроде "all": {"anti_corruption": "all"}
    abl: int | Dict[str, int | str | dict] = 0
    # DEPRECATED: старое имя поля; поддерживаем для обратной совместимости и мигрируем в abl
    inf: Optional[int | Dict[str, int]] = None
    paid: List[PaidAbility] = Field(default_factory=list)
    # Доп. поля для гибкости (DEPRECATED: переносим ключи в inf-словарь)
    meta: Dict[str, int | str | bool] = Field(default_factory=dict)
    # Короткое текстовое описание для игрока (отображение на карте/в UI)
    notes: str = ""

    @root_validator(pre=True)
    def _migrate_inf_to_abl(cls, values):  # type: ignore[override]
        # Если abl не задан, а инфо пришло в старом поле inf — перенесём
        if "abl" not in values and "inf" in values:
            values["abl"] = values.get("inf")
        # Нормализация опечатки фракции в старых данных: goverment -> government
        fac = values.get("faction")
        if isinstance(fac, str) and fac == "goverment":
            values["faction"] = "government"
        return values


class Slot(BaseModel):
    card: Optional[Card] = None
    face_up: bool = True
    muscles: int = 0  # Братки на карте


class TokenPools(BaseModel):
    reserve_money: int = 12  # стартовое количество по умолчанию
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

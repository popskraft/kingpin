"""
Вспомогательные функции и фикстуры для тестирования
"""

import pytest
from typing import Dict, List
from packages.engine.models import (
    GameState, PlayerState, Slot, Card, TokenPools, GameConfig,
    CardType, Faction, TurnPhase
)
from packages.engine.engine import Ctx


class TestDataBuilder:
    """Builder для создания тестовых данных"""
    
    @staticmethod
    def create_basic_card(
        card_id: str = "test_card",
        name: str = "Test Card",
        card_type: CardType = CardType.common,
        faction: Faction = Faction.neutral,
        hp: int = 3,
        atk: int = 2,
        d: int = 1,
        price: int = 2,
        corruption: int = 1,
        abl: Dict = None
    ) -> Card:
        """Создать базовую тестовую карту"""
        return Card(
            id=card_id,
            name=name,
            type=card_type,
            faction=faction,
            hp=hp,
            atk=atk,
            d=d,
            price=price,
            corruption=corruption,
            abl=abl or {}
        )
    
    @staticmethod
    def create_boss_card(
        card_id: str = "test_boss",
        name: str = "Test Boss",
        authority: int = 1,
        hp: int = 10,
        atk: int = 2
    ) -> Card:
        """Создать тестового босса"""
        return Card(
            id=card_id,
            name=name,
            type=CardType.boss,
            faction=Faction.neutral,
            hp=hp,
            atk=atk,
            d=3,
            abl={"authority": authority}
        )
    
    @staticmethod
    def create_slot_with_card(
        card: Card = None,
        face_up: bool = True,
        muscles: int = 0
    ) -> Slot:
        """Создать слот с картой"""
        if card is None:
            card = TestDataBuilder.create_basic_card()
        
        return Slot(card=card, face_up=face_up, muscles=muscles)
    
    @staticmethod
    def create_empty_slot() -> Slot:
        """Создать пустой слот"""
        return Slot(card=None, face_up=True, muscles=0)
    
    @staticmethod
    def create_player_state(
        player_id: str = "P1",
        hand_limit: int = 6,
        hand_cards: List[Card] = None,
        slot_cards: List[Card] = None,
        reserve_money: int = 12,
        otboy: int = 0
    ) -> PlayerState:
        """Создать состояние игрока"""
        # Создать руку
        hand = hand_cards or []
        
        # Создать слоты
        slots = []
        slot_cards = slot_cards or []
        
        for i in range(6):  # Стандартное количество слотов
            if i < len(slot_cards) and slot_cards[i] is not None:
                slots.append(Slot(card=slot_cards[i], face_up=True, muscles=0))
            else:
                slots.append(Slot(card=None, face_up=True, muscles=0))
        
        # Создать токены
        tokens = TokenPools(reserve_money=reserve_money, otboy=otboy)
        
        return PlayerState(
            id=player_id,
            hand_limit=hand_limit,
            hand=hand,
            slots=slots,
            tokens=tokens
        )
    
    @staticmethod
    def create_game_state(
        active_player: str = "P1",
        turn_number: int = 1,
        phase: TurnPhase = TurnPhase.upkeep,
        p1_cards: List[Card] = None,
        p2_cards: List[Card] = None,
        config_overrides: Dict = None
    ) -> GameState:
        """Создать игровое состояние"""
        # Создать конфигурацию
        config_data = {
            "hand_enabled": True,
            "events_enabled": True,
            "micro_bribe_once_per_turn": True,
            "ammo_max_bonus": 2,
            "cascade_enabled": True,
            "cascade_reward": 3,
            "cascade_max_triggers": 2
        }
        
        if config_overrides:
            config_data.update(config_overrides)
        
        config = GameConfig(**config_data)
        
        # Создать игроков
        p1 = TestDataBuilder.create_player_state("P1", slot_cards=p1_cards)
        p2 = TestDataBuilder.create_player_state("P2", slot_cards=p2_cards)
        
        return GameState(
            config=config,
            players={"P1": p1, "P2": p2},
            active_player=active_player,
            phase=phase,
            turn_number=turn_number,
            flags={}
        )
    
    @staticmethod
    def create_context(
        game_state: GameState = None,
        log_entries: List[Dict] = None
    ) -> Ctx:
        """Создать игровой контекст"""
        if game_state is None:
            game_state = TestDataBuilder.create_game_state()
        
        return Ctx(
            state=game_state,
            log=log_entries or []
        )


class CardTemplates:
    """Шаблоны карт для тестирования"""
    
    BASIC_GANGSTER = {
        "id": "gangster_thug",
        "name": "Gangster Thug",
        "type": CardType.common,
        "faction": "gangsters",
        "hp": 3,
        "atk": 2,
        "d": 1,
        "price": 2,
        "corruption": 1
    }
    
    AUTHORITY_OFFICER = {
        "id": "authority_officer",
        "name": "Authority Officer",
        "type": CardType.common,
        "faction": "authorities",
        "hp": 4,
        "atk": 1,
        "d": 2,
        "price": 3,
        "corruption": 2,
        "abl": {"authority": 1}
    }
    
    LONER_HACKER = {
        "id": "loner_hacker",
        "name": "Loner Hacker",
        "type": CardType.common,
        "faction": "loners",
        "hp": 2,
        "atk": 3,
        "d": 0,
        "price": 2,
        "corruption": 1,
        "abl": {"hack": 1}
    }
    
    THIEF_WITH_STEAL = {
        "id": "thief",
        "name": "Thief",
        "type": CardType.common,
        "faction": "gangsters",
        "hp": 2,
        "atk": 1,
        "d": 1,
        "price": 2,
        "corruption": 2,
        "abl": {"on_enter": {"steal": 2}}
    }
    
    BOSS_GANGSTER = {
        "id": "boss_gangster",
        "name": "Gangster Boss",
        "type": CardType.boss,
        "faction": "gangsters",
        "hp": 10,
        "atk": 2,
        "d": 3,
        "price": 0,
        "corruption": 12,
        "abl": {"authority": 1}
    }


@pytest.fixture
def basic_card():
    """Фикстура базовой карты"""
    return TestDataBuilder.create_basic_card()


@pytest.fixture
def boss_card():
    """Фикстура карты босса"""
    return TestDataBuilder.create_boss_card()


@pytest.fixture
def empty_game_state():
    """Фикстура пустого игрового состояния"""
    return TestDataBuilder.create_game_state()


@pytest.fixture
def game_context():
    """Фикстура игрового контекста"""
    return TestDataBuilder.create_context()


@pytest.fixture
def populated_game_state():
    """Фикстура игрового состояния с картами на поле"""
    p1_cards = [
        Card(**CardTemplates.BASIC_GANGSTER),
        Card(**CardTemplates.AUTHORITY_OFFICER),
        None,  # Пустой слот
        Card(**CardTemplates.LONER_HACKER)
    ]
    
    p2_cards = [
        Card(**CardTemplates.BOSS_GANGSTER),
        Card(**CardTemplates.THIEF_WITH_STEAL)
    ]
    
    return TestDataBuilder.create_game_state(
        p1_cards=p1_cards,
        p2_cards=p2_cards
    )


class TestAssertions:
    """Кастомные проверки для тестов"""
    
    @staticmethod
    def assert_card_in_slot(player: PlayerState, slot_index: int, expected_card_id: str):
        """Проверить что карта находится в слоте"""
        slot = player.slots[slot_index]
        assert slot.card is not None, f"Slot {slot_index} is empty"
        assert slot.card.id == expected_card_id, f"Expected {expected_card_id}, got {slot.card.id}"
    
    @staticmethod
    def assert_slot_empty(player: PlayerState, slot_index: int):
        """Проверить что слот пустой"""
        slot = player.slots[slot_index]
        assert slot.card is None, f"Slot {slot_index} should be empty"
    
    @staticmethod
    def assert_money_change(player: PlayerState, expected_reserve: int, expected_otboy: int):
        """Проверить изменение денег"""
        assert player.tokens.reserve_money == expected_reserve, f"Expected reserve {expected_reserve}, got {player.tokens.reserve_money}"
        assert player.tokens.otboy == expected_otboy, f"Expected otboy {expected_otboy}, got {player.tokens.otboy}"
    
    @staticmethod
    def assert_log_contains(log: List[Dict], event_type: str, **kwargs):
        """Проверить что лог содержит событие определённого типа"""
        matching_events = [entry for entry in log if entry.get("type") == event_type]
        assert len(matching_events) > 0, f"No events of type {event_type} found in log"
        
        if kwargs:
            for event in matching_events:
                match = all(event.get(key) == value for key, value in kwargs.items())
                if match:
                    return
            assert False, f"No {event_type} event found with parameters {kwargs}"


# Декораторы для тестов
def skip_if_no_cards(test_func):
    """Пропустить тест если нет карт для тестирования"""
    def wrapper(*args, **kwargs):
        # Здесь можно добавить логику проверки наличия карт
        return test_func(*args, **kwargs)
    return wrapper


def parametrize_card_types(*card_types):
    """Параметризовать тест для разных типов карт"""
    return pytest.mark.parametrize("card_type", card_types)

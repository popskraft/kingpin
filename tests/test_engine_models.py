"""
Unit-тесты для модели данных engine/models.py
"""

import pytest
from packages.engine.models import (
    Card, CardType, Faction, Slot, PlayerState, GameState, 
    TokenPools, GameConfig, TurnPhase
)
from tests.test_helpers import TestDataBuilder, CardTemplates


class TestCard:
    """Тесты модели Card"""
    
    def test_card_creation_basic(self):
        """Тест создания базовой карты"""
        card = Card(
            id="test_card",
            name="Test Card",
            hp=5,
            atk=3,
            d=2
        )
        
        assert card.id == "test_card"
        assert card.name == "Test Card"
        assert card.hp == 5
        assert card.atk == 3
        assert card.d == 2
        assert card.type == CardType.common  # default
        assert card.faction == Faction.neutral  # default
        assert card.price == 0  # default
        assert card.abl == 0  # default
    
    def test_card_creation_with_abilities(self):
        """Тест создания карты со способностями"""
        card = Card(
            id="ability_card",
            name="Ability Card",
            abl={"authority": 2, "steal": 1}
        )
        
        assert isinstance(card.abl, dict)
        assert card.abl["authority"] == 2
        assert card.abl["steal"] == 1
    
    def test_card_type_validation(self):
        """Тест валидации типа карты"""
        # Валидные типы
        for card_type in [CardType.boss, CardType.unique, CardType.common, CardType.event]:
            card = Card(id="test", name="Test", type=card_type)
            assert card.type == card_type
    
    def test_faction_validation(self):
        """Тест валидации фракции"""
        card = Card(id="test", name="Test", faction="gangsters")
        assert card.faction == "gangsters"
        
        card2 = Card(id="test2", name="Test2", faction=Faction.neutral)
        assert card2.faction == Faction.neutral
    
    def test_card_with_legacy_inf_migration(self):
        """Тест миграции старого поля inf в abl"""
        # Имитируем старые данные с inf вместо abl
        card_data = {
            "id": "legacy_card",
            "name": "Legacy Card",
            "inf": {"authority": 3}
        }
        
        card = Card(**card_data)
        assert card.abl == {"authority": 3}
    
    def test_card_faction_typo_correction(self):
        """Тест исправления опечатки в фракции"""
        card_data = {
            "id": "typo_card",
            "name": "Typo Card",
            "faction": "goverment"  # опечатка
        }
        
        card = Card(**card_data)
        assert card.faction == "government"  # исправлено
    
    def test_card_clan_field_only(self):
        """Тест поля clan (legacy 'caste' больше не поддерживается)."""
        card = Card(id="test1", name="Test1", clan="warriors")
        assert card.clan == "warriors"


class TestSlot:
    """Тесты модели Slot"""
    
    def test_empty_slot_creation(self):
        """Тест создания пустого слота"""
        slot = Slot()
        
        assert slot.card is None
        assert slot.face_up is True  # default
        assert slot.muscles == 0  # default
    
    def test_slot_with_card(self):
        """Тест слота с картой"""
        card = TestDataBuilder.create_basic_card()
        slot = Slot(card=card, face_up=False, muscles=3)
        
        assert slot.card == card
        assert slot.face_up is False
        assert slot.muscles == 3


class TestTokenPools:
    """Тесты модели TokenPools"""
    
    def test_token_pools_creation(self):
        """Тест создания пулов токенов"""
        tokens = TokenPools()
        
        assert tokens.reserve_money == 12  # default
        assert tokens.otboy == 0  # default
    
    def test_token_pools_custom_values(self):
        """Тест создания с кастомными значениями"""
        tokens = TokenPools(reserve_money=15, otboy=5)
        
        assert tokens.reserve_money == 15
        assert tokens.otboy == 5


class TestPlayerState:
    """Тесты модели PlayerState"""
    
    def test_player_creation_basic(self):
        """Тест создания базового игрока"""
        player = PlayerState(id="P1")
        
        assert player.id == "P1"
        assert player.hand_limit == 0  # default
        assert len(player.hand) == 0
        assert len(player.slots) == 6  # default количество слотов
        assert player.tokens.reserve_money == 12  # default
        assert player.cascade_used is False
        assert player.cascade_triggers == 0
    
    def test_player_with_cards(self):
        """Тест игрока с картами"""
        card1 = TestDataBuilder.create_basic_card("card1")
        card2 = TestDataBuilder.create_basic_card("card2")
        
        player = PlayerState(
            id="P2",
            hand_limit=6,
            hand=[card1, card2]
        )
        
        assert len(player.hand) == 2
        assert player.hand[0].id == "card1"
        assert player.hand[1].id == "card2"
    
    def test_active_cards_method(self):
        """Тест метода получения активных карт"""
        player = PlayerState(id="P1")
        
        # Добавим карты в слоты
        card1 = TestDataBuilder.create_basic_card("active1")
        card2 = TestDataBuilder.create_basic_card("active2")
        
        player.slots[0].card = card1
        player.slots[2].card = card2
        # slots[1] остается пустым
        
        active_cards = player.active_cards()
        
        assert len(active_cards) == 2
        assert active_cards[0].id == "active1"
        assert active_cards[1].id == "active2"


class TestGameConfig:
    """Тесты модели GameConfig"""
    
    def test_game_config_defaults(self):
        """Тест значений по умолчанию"""
        config = GameConfig()
        
        assert config.hand_enabled is False
        assert config.events_enabled is True
        assert config.micro_bribe_once_per_turn is True
        assert config.ammo_max_bonus == 2
        assert config.cascade_enabled is True
        assert config.cascade_reward == 2
        assert config.cascade_max_triggers == 3
    
    def test_game_config_custom(self):
        """Тест кастомной конфигурации"""
        config = GameConfig(
            hand_enabled=True,
            ammo_max_bonus=5,
            cascade_reward=10
        )
        
        assert config.hand_enabled is True
        assert config.ammo_max_bonus == 5
        assert config.cascade_reward == 10
        # Остальные значения должны остаться по умолчанию
        assert config.events_enabled is True


class TestGameState:
    """Тесты модели GameState"""
    
    def test_game_state_creation(self):
        """Тест создания игрового состояния"""
        state = GameState()
        
        assert state.seed == 0  # default
        assert isinstance(state.config, GameConfig)
        assert len(state.deck) == 0
        assert len(state.shelf) == 0
        assert len(state.discard_out_of_game) == 0
        assert len(state.players) == 0
        assert state.active_player == "P1"
        assert state.phase == TurnPhase.upkeep
        assert state.turn_number == 1
        assert isinstance(state.flags, dict)
    
    def test_game_state_with_players(self):
        """Тест игрового состояния с игроками"""
        p1 = PlayerState(id="P1")
        p2 = PlayerState(id="P2")
        
        state = GameState(
            players={"P1": p1, "P2": p2},
            active_player="P2",
            turn_number=5
        )
        
        assert len(state.players) == 2
        assert "P1" in state.players
        assert "P2" in state.players
        assert state.active_player == "P2"
        assert state.turn_number == 5
    
    def test_opponent_id_method(self):
        """Тест метода получения ID противника"""
        state = GameState(active_player="P1")
        assert state.opponent_id() == "P2"
        
        state.active_player = "P2"
        assert state.opponent_id() == "P1"
    
    def test_get_player_method(self):
        """Тест метода получения игрока"""
        p1 = PlayerState(id="P1")
        p2 = PlayerState(id="P2")
        
        state = GameState(players={"P1": p1, "P2": p2})
        
        retrieved_p1 = state.get_player("P1")
        retrieved_p2 = state.get_player("P2")
        
        assert retrieved_p1 == p1
        assert retrieved_p2 == p2
        assert retrieved_p1.id == "P1"
        assert retrieved_p2.id == "P2"
    
    def test_get_slot_method(self):
        """Тест метода получения слота"""
        player = PlayerState(id="P1")
        card = TestDataBuilder.create_basic_card()
        player.slots[2].card = card
        
        state = GameState(players={"P1": player})
        
        slot = state.get_slot("P1", 2)
        assert slot.card == card
        
        empty_slot = state.get_slot("P1", 0)
        assert empty_slot.card is None


class TestEnums:
    """Тесты перечислений"""
    
    def test_card_type_enum(self):
        """Тест перечисления типов карт"""
        assert CardType.boss == "boss"
        assert CardType.unique == "unique"
        assert CardType.common == "common"
        assert CardType.event == "event"
        assert CardType.action == "action"
        assert CardType.token == "token"
    
    def test_faction_enum(self):
        """Тест перечисления фракций"""
        assert Faction.neutral == "neutral"
    
    def test_turn_phase_enum(self):
        """Тест перечисления фаз хода"""
        assert TurnPhase.upkeep == "upkeep"
        assert TurnPhase.main == "main"
        assert TurnPhase.resolution == "resolution"
        assert TurnPhase.end == "end"


class TestPaidAbility:
    """Тесты модели PaidAbility"""
    
    def test_paid_ability_creation(self):
        """Тест создания платной способности"""
        from packages.engine.models import PaidAbility
        
        ability = PaidAbility(
            id="heal_ability",
            cost=3,
            cooldown_per_turn=2,
            effect_id="heal_self_1"
        )
        
        assert ability.id == "heal_ability"
        assert ability.cost == 3
        assert ability.cooldown_per_turn == 2
        assert ability.effect_id == "heal_self_1"
    
    def test_paid_ability_defaults(self):
        """Тест значений по умолчанию"""
        from packages.engine.models import PaidAbility
        
        ability = PaidAbility(
            id="basic_ability",
            effect_id="basic_effect"
        )
        
        assert ability.cost == 1  # default
        assert ability.cooldown_per_turn == 1  # default

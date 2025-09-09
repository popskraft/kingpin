"""
Unit-тесты для основной логики engine/engine.py
"""

import pytest
from packages.engine.engine import (
    _card_trait, _maybe_trigger_cascade, _authority_bonus, 
    _defense_quota, _on_enter_slot, _apply_damage,
    _economic_collapse_check, resolve_event, initialize_game,
    next_turn, apply_action, Ctx
)
from packages.engine.models import (
    Card, CardType, PlayerState, GameState, Slot, TurnPhase
)
from packages.engine.actions import Attack, Defend, Influence, DiscardCard, Draw
from tests.test_helpers import TestDataBuilder, CardTemplates, TestAssertions


class TestCardTrait:
    """Тесты функции _card_trait"""
    
    def test_extract_from_abl_dict(self):
        """Тест извлечения значения из словаря abl"""
        card = Card(
            id="test",
            name="Test",
            abl={"authority": 3, "steal": 2}
        )
        
        assert _card_trait(card, "authority", 0) == 3
        assert _card_trait(card, "steal", 0) == 2
        assert _card_trait(card, "nonexistent", 5) == 5  # default
    
    def test_extract_from_inf_dict_fallback(self):
        """Тест извлечения из legacy поля inf"""
        card = Card(id="test", name="Test")
        # Принудительно установим inf (обходим валидацию)
        card.inf = {"authority": 2}
        
        # Должен найти в inf если abl не содержит ключ
        assert _card_trait(card, "authority", 0) == 2
    
    def test_extract_from_meta_fallback(self):
        """Тест извлечения из поля meta"""
        card = Card(
            id="test",
            name="Test",
            meta={"special_power": 4}
        )
        
        assert _card_trait(card, "special_power", 0) == 4
    
    def test_handle_boolean_values(self):
        """Тест обработки булевых значений"""
        card = Card(
            id="test",
            name="Test",
            abl={"unbribable": True, "disabled": False}
        )
        
        assert _card_trait(card, "unbribable", 0) == 1  # True -> 1
        assert _card_trait(card, "disabled", 0) == 0   # False -> 0
    
    def test_handle_string_numbers(self):
        """Тест обработки строковых чисел"""
        card = Card(
            id="test",
            name="Test",
            abl={"power": "5", "invalid": "not_a_number"}
        )
        
        assert _card_trait(card, "power", 0) == 5
        assert _card_trait(card, "invalid", 0) == 0  # default для некорректной строки
    
    def test_handle_invalid_abl_type(self):
        """Тест обработки некорректного типа abl"""
        # Создаём карту с валидным abl, затем принудительно меняем его
        card = Card(id="test", name="Test", abl={})
        # Принудительно устанавливаем некорректный тип (обходим Pydantic)
        card.__dict__["abl"] = "invalid_string"
        
        assert _card_trait(card, "anything", 10) == 10  # должен вернуть default
    
    def test_handle_missing_abl(self):
        """Тест обработки отсутствующего abl"""
        card = Card(id="test", name="Test")  # abl = 0 by default
        
        assert _card_trait(card, "anything", 7) == 7  # должен вернуть default


class TestAuthorityBonus:
    """Тесты функции _authority_bonus"""
    
    def test_no_boss_cards(self):
        """Тест без карт босса"""
        player = TestDataBuilder.create_player_state()
        
        assert _authority_bonus(player) == 0
    
    def test_single_boss_with_authority(self):
        """Тест с одним боссом с авторитетом"""
        player = TestDataBuilder.create_player_state()
        boss = Card(
            id="boss1",
            name="Boss",
            type=CardType.boss,
            abl={"authority": 3}
        )
        player.slots[0].card = boss
        
        assert _authority_bonus(player) == 3
    
    def test_multiple_bosses_max_authority(self):
        """Тест с несколькими боссами - берёт максимальный авторитет"""
        player = TestDataBuilder.create_player_state()
        
        boss1 = Card(id="boss1", name="Boss1", type=CardType.boss, abl={"authority": 2})
        boss2 = Card(id="boss2", name="Boss2", type=CardType.boss, abl={"authority": 5})
        boss3 = Card(id="boss3", name="Boss3", type=CardType.boss, abl={"authority": 1})
        
        player.slots[0].card = boss1
        player.slots[1].card = boss2
        player.slots[2].card = boss3
        
        assert _authority_bonus(player) == 5  # максимальное значение
    
    def test_boss_without_authority(self):
        """Тест босса без авторитета"""
        player = TestDataBuilder.create_player_state()
        boss = Card(id="boss", name="Boss", type=CardType.boss)  # без abl
        player.slots[0].card = boss
        
        assert _authority_bonus(player) == 0
    
    def test_non_boss_cards_ignored(self):
        """Тест что не-боссы игнорируются"""
        player = TestDataBuilder.create_player_state()
        
        # Обычная карта с authority - не должна учитываться
        regular_card = Card(
            id="regular",
            name="Regular",
            type=CardType.common,
            abl={"authority": 10}
        )
        player.slots[0].card = regular_card
        
        assert _authority_bonus(player) == 0


class TestDefenseQuota:
    """Тесты функции _defense_quota"""
    
    def test_empty_slot(self):
        """Тест пустого слота"""
        ctx = TestDataBuilder.create_context()
        player = ctx.state.get_player("P1")
        empty_slot = player.slots[0]  # пустой по умолчанию
        
        assert _defense_quota(ctx, "P1", empty_slot) == 0
    
    def test_basic_defense_quota(self):
        """Тест базовой квоты защиты"""
        ctx = TestDataBuilder.create_context()
        player = ctx.state.get_player("P1")
        
        card = Card(id="test", name="Test", d=3)
        slot = Slot(card=card)
        player.slots[0] = slot
        
        assert _defense_quota(ctx, "P1", slot) == 3
    
    def test_defense_quota_with_extra_defense(self):
        """Тест квоты с дополнительной защитой"""
        ctx = TestDataBuilder.create_context()
        player = ctx.state.get_player("P1")
        
        card = Card(
            id="test",
            name="Test",
            d=2,
            abl={"extra_defense": 2}
        )
        slot = Slot(card=card)
        player.slots[0] = slot
        
        assert _defense_quota(ctx, "P1", slot) == 4  # 2 (base) + 2 (extra)
    
    def test_defense_quota_with_authority_bonus(self):
        """Тест квоты с бонусом авторитета"""
        ctx = TestDataBuilder.create_context()
        player = ctx.state.get_player("P1")
        
        # Босс с авторитетом
        boss = Card(
            id="boss",
            name="Boss",
            type=CardType.boss,
            abl={"authority": 2}
        )
        player.slots[0].card = boss
        
        # Обычная карта
        regular_card = Card(id="regular", name="Regular", d=1)
        slot = Slot(card=regular_card)
        player.slots[1] = slot
        
        # Квота = base(1) + extra(0) + authority(2) = 3
        assert _defense_quota(ctx, "P1", slot) == 3
    
    def test_defense_quota_combined_bonuses(self):
        """Тест квоты со всеми бонусами"""
        ctx = TestDataBuilder.create_context()
        player = ctx.state.get_player("P1")
        
        # Босс с авторитетом
        boss = Card(
            id="boss",
            name="Boss",
            type=CardType.boss,
            abl={"authority": 1}
        )
        player.slots[0].card = boss
        
        # Карта с дополнительной защитой
        card = Card(
            id="test",
            name="Test",
            d=2,
            abl={"extra_defense": 1}
        )
        slot = Slot(card=card)
        player.slots[1] = slot
        
        # Квота = base(2) + extra(1) + authority(1) = 4
        assert _defense_quota(ctx, "P1", slot) == 4


class TestApplyDamage:
    """Тесты функции _apply_damage"""
    
    def test_no_damage(self):
        """Тест без урона"""
        ctx = TestDataBuilder.create_context()
        card = Card(id="test", name="Test", hp=5)
        slot = Slot(card=card, muscles=2)
        
        _apply_damage(slot, 0, ctx, "P1")
        
        assert slot.card.hp == 5  # без изменений
        assert slot.muscles == 2   # без изменений
    
    def test_damage_absorbed_by_muscles(self):
        """Тест урона, поглощённого мышцами"""
        ctx = TestDataBuilder.create_context()
        card = Card(id="test", name="Test", hp=5)
        slot = Slot(card=card, muscles=3)
        
        _apply_damage(slot, 2, ctx, "P1")
        
        assert slot.card.hp == 5   # HP не изменилось
        assert slot.muscles == 1   # потеряли 2 мышцы
        assert ctx.state.players["P1"].tokens.otboy == 2  # мышцы в отбой
    
    def test_damage_exceeds_muscles(self):
        """Тест урона, превышающего количество мышц"""
        ctx = TestDataBuilder.create_context()
        card = Card(id="test", name="Test", hp=5)
        slot = Slot(card=card, muscles=2)
        
        _apply_damage(slot, 4, ctx, "P1")
        
        assert slot.card.hp == 3   # потеряли 2 HP (4 урона - 2 мышцы)
        assert slot.muscles == 0   # все мышцы потеряны
        assert ctx.state.players["P1"].tokens.otboy == 2  # мышцы в отбой
    
    def test_damage_kills_card(self):
        """Тест смертельного урона"""
        ctx = TestDataBuilder.create_context()
        card = Card(id="test", name="Test", hp=3)
        slot = Slot(card=card, muscles=1)
        
        _apply_damage(slot, 5, ctx, "P1")
        
        assert slot.card.hp == -1  # убита (3 HP - 4 реального урона)
        assert slot.muscles == 0   # все мышцы потеряны
        assert ctx.state.players["P1"].tokens.otboy == 1


class TestEconomicCollapseCheck:
    """Тесты функции _economic_collapse_check"""
    
    def test_no_collapse_with_money(self):
        """Тест без коллапса при наличии денег"""
        player = TestDataBuilder.create_player_state(reserve_money=5)
        
        assert _economic_collapse_check(player) is False
    
    def test_no_collapse_with_muscles(self):
        """Тест без коллапса при наличии мышц на поле"""
        player = TestDataBuilder.create_player_state(reserve_money=0)
        card = Card(id="test", name="Test")
        player.slots[0] = Slot(card=card, muscles=3)
        
        assert _economic_collapse_check(player) is False
    
    def test_no_collapse_with_both(self):
        """Тест без коллапса при наличии и денег и мышц"""
        player = TestDataBuilder.create_player_state(reserve_money=2)
        card = Card(id="test", name="Test")
        player.slots[0] = Slot(card=card, muscles=1)
        
        assert _economic_collapse_check(player) is False
    
    def test_economic_collapse(self):
        """Тест экономического коллапса"""
        player = TestDataBuilder.create_player_state(reserve_money=0)
        # Все слоты либо пусты, либо без мышц
        card = Card(id="test", name="Test")
        player.slots[0] = Slot(card=card, muscles=0)
        
        assert _economic_collapse_check(player) is True


class TestCascadeTrigger:
    """Тесты функции _maybe_trigger_cascade"""
    
    def test_cascade_disabled(self):
        """Тест при отключенном каскаде"""
        ctx = TestDataBuilder.create_context()
        ctx.state.config.cascade_enabled = False
        
        player = ctx.state.get_player("P1")
        # Добавим карты для каскада 2-2-2
        player.slots[0].card = Card(id="g1", name="G1", faction="gangsters")
        player.slots[1].card = Card(id="g2", name="G2", faction="gangsters")
        player.slots[2].card = Card(id="a1", name="A1", faction="authorities")
        player.slots[3].card = Card(id="a2", name="A2", faction="authorities")
        player.slots[4].card = Card(id="l1", name="L1", faction="loners")
        player.slots[5].card = Card(id="l2", name="L2", faction="loners")
        
        initial_money = player.tokens.reserve_money
        _maybe_trigger_cascade(ctx, "P1")
        
        assert player.tokens.reserve_money == initial_money  # без изменений
        assert player.cascade_triggers == 0
    
    def test_cascade_insufficient_cards(self):
        """Тест каскада при недостаточном количестве карт"""
        ctx = TestDataBuilder.create_context()
        player = ctx.state.get_player("P1")
        
        # Только 2 карты одной фракции
        player.slots[0].card = Card(id="g1", name="G1", faction="gangsters")
        player.slots[1].card = Card(id="g2", name="G2", faction="gangsters")
        
        initial_money = player.tokens.reserve_money
        _maybe_trigger_cascade(ctx, "P1")
        
        assert player.tokens.reserve_money == initial_money  # без изменений
        assert player.cascade_triggers == 0
    
    def test_cascade_trigger_2_2_2(self):
        """Тест успешного каскада 2-2-2"""
        ctx = TestDataBuilder.create_context()
        ctx.state.config.cascade_reward = 5
        
        player = ctx.state.get_player("P1")
        
        # Создаём каскад 2-2-2 с правильными фракциями
        player.slots[0].card = Card(id="g1", name="G1", type=CardType.common, faction="gangsters")
        player.slots[1].card = Card(id="g2", name="G2", type=CardType.common, faction="gangsters")
        player.slots[2].card = Card(id="a1", name="A1", type=CardType.common, faction="government")
        player.slots[3].card = Card(id="a2", name="A2", type=CardType.common, faction="government")
        player.slots[4].card = Card(id="l1", name="L1", type=CardType.common, faction="mercenaries")
        player.slots[5].card = Card(id="l2", name="L2", type=CardType.common, faction="mercenaries")
        
        initial_money = player.tokens.reserve_money
        _maybe_trigger_cascade(ctx, "P1")
        
        assert player.tokens.reserve_money == initial_money + 5  # получил награду
        assert player.cascade_triggers == 1
        
        # Проверим лог
        TestAssertions.assert_log_contains(
            ctx.log, 
            "cascade_trigger",
            pattern="2-2-2",
            reward=5,
            triggers=1
        )
    
    def test_cascade_max_triggers_limit(self):
        """Тест лимита каскадных триггеров"""
        ctx = TestDataBuilder.create_context()
        ctx.state.config.cascade_max_triggers = 2
        
        player = ctx.state.get_player("P1")
        player.cascade_triggers = 2  # уже достиг лимита
        
        # Создаём каскад 2-2-2 с правильными фракциями
        player.slots[0].card = Card(id="g1", name="G1", type=CardType.common, faction="gangsters")
        player.slots[1].card = Card(id="g2", name="G2", type=CardType.common, faction="gangsters")
        player.slots[2].card = Card(id="a1", name="A1", type=CardType.common, faction="government")
        player.slots[3].card = Card(id="a2", name="A2", type=CardType.common, faction="government")
        player.slots[4].card = Card(id="l1", name="L1", type=CardType.common, faction="mercenaries")
        player.slots[5].card = Card(id="l2", name="L2", type=CardType.common, faction="mercenaries")
        
        initial_money = player.tokens.reserve_money
        _maybe_trigger_cascade(ctx, "P1")
        
        assert player.tokens.reserve_money == initial_money  # не получил награду
        assert player.cascade_triggers == 2  # не изменилось
    
    def test_cascade_ignores_event_cards(self):
        """Тест что каскад игнорирует event карты"""
        ctx = TestDataBuilder.create_context()
        player = ctx.state.get_player("P1")
        
        # Смешанные карты включая event
        player.slots[0].card = Card(id="g1", name="G1", type=CardType.common, faction="gangsters")
        player.slots[1].card = Card(id="g2", name="G2", type=CardType.common, faction="gangsters")
        player.slots[2].card = Card(id="event", name="Event", type=CardType.event, faction="gangsters")  # event
        player.slots[3].card = Card(id="a1", name="A1", type=CardType.common, faction="government")
        player.slots[4].card = Card(id="a2", name="A2", type=CardType.common, faction="government")
        player.slots[5].card = Card(id="l1", name="L1", type=CardType.common, faction="mercenaries")
        
        initial_money = player.tokens.reserve_money
        _maybe_trigger_cascade(ctx, "P1")
        
        # Event карта не должна учитываться, значит только 2 gangsters, 2 authorities, 1 loner
        # Каскад не сработает
        assert player.tokens.reserve_money == initial_money
        assert player.cascade_triggers == 0


class TestInitializeGame:
    """Тесты функции initialize_game"""
    
    def test_initialize_game_basic(self):
        """Тест базовой инициализации игры"""
        state = TestDataBuilder.create_game_state()
        
        initialize_game(state)
        
        assert state.phase == TurnPhase.upkeep
        assert state.turn_number == 1
        assert "micro_bribe_used" in state.flags
        assert state.flags["micro_bribe_used"] is False


class TestNextTurn:
    """Тесты функции next_turn"""
    
    def test_next_turn_switch_player(self):
        """Тест смены активного игрока"""
        ctx = TestDataBuilder.create_context()
        ctx.state.active_player = "P1"
        ctx.state.turn_number = 3
        
        next_turn(ctx)
        
        assert ctx.state.active_player == "P2"
        assert ctx.state.turn_number == 4
        assert ctx.state.phase == TurnPhase.upkeep
        assert ctx.state.flags["micro_bribe_used"] is False
    
    def test_next_turn_reveal_cards(self):
        """Тест автооткрытия карт"""
        ctx = TestDataBuilder.create_context()
        ctx.state.active_player = "P1"
        
        # P2 имеет закрытую карту
        player_p2 = ctx.state.get_player("P2")
        card = Card(id="hidden", name="Hidden Card")
        player_p2.slots[0] = Slot(card=card, face_up=False)
        
        next_turn(ctx)  # Переключаемся на P2
        
        # Карта P2 должна открыться
        assert player_p2.slots[0].face_up is True
    
    def test_next_turn_reset_cascade_flags(self):
        """Тест сброса флагов каскада"""
        ctx = TestDataBuilder.create_context()
        ctx.state.active_player = "P1"
        
        # P2 имеет активные флаги каскада
        player_p2 = ctx.state.get_player("P2")
        player_p2.cascade_used = True
        player_p2.cascade_triggers = 2
        
        next_turn(ctx)  # Переключаемся на P2
        
        # Флаги P2 должны сброситься
        assert player_p2.cascade_used is False
        assert player_p2.cascade_triggers == 0

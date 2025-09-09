"""
Unit-тесты для действий engine/actions.py и их применения
"""

import pytest
from packages.engine.actions import (
    Action, Attack, Defend, Influence, DiscardCard, Draw
)
from packages.engine.engine import apply_action
from packages.engine.models import Card, CardType, TurnPhase
from tests.test_helpers import TestDataBuilder, CardTemplates, TestAssertions


class TestActionModels:
    """Тесты моделей действий"""
    
    def test_base_action_creation(self):
        """Тест создания базового действия"""
        action = Action(kind="test_action")
        
        assert action.kind == "test_action"
    
    def test_attack_action_creation(self):
        """Тест создания действия атаки"""
        attack = Attack(
            target_player="P2",
            target_slot=3,
            ammo_spend=2,
            base_damage=5,
            attacker_slot=1
        )
        
        assert attack.kind == "attack"
        assert attack.target_player == "P2"
        assert attack.target_slot == 3
        assert attack.ammo_spend == 2
        assert attack.base_damage == 5
        assert attack.attacker_slot == 1
    
    def test_attack_action_defaults(self):
        """Тест значений по умолчанию для атаки"""
        attack = Attack(target_player="P2")
        
        assert attack.kind == "attack"
        assert attack.target_slot is None
        assert attack.ammo_spend == 0
        assert attack.base_damage == 0
        assert attack.attacker_slot is None
    
    def test_defend_action_creation(self):
        """Тест создания действия защиты"""
        defend = Defend(target_slot=2, hire_count=3)
        
        assert defend.kind == "defend"
        assert defend.target_slot == 2
        assert defend.hire_count == 3
    
    def test_influence_action_creation(self):
        """Тест создания действия влияния"""
        influence = Influence(
            micro_bribe_target_player="P1",
            micro_bribe_target_slot=1
        )
        
        assert influence.kind == "influence"
        assert influence.micro_bribe_target_player == "P1"
        assert influence.micro_bribe_target_slot == 1
    
    def test_influence_action_defaults(self):
        """Тест значений по умолчанию для влияния"""
        influence = Influence()
        
        assert influence.kind == "influence"
        assert influence.micro_bribe_target_player is None
        assert influence.micro_bribe_target_slot is None
    
    def test_discard_action_creation(self):
        """Тест создания действия сброса"""
        discard = DiscardCard(own_slot=4)
        
        assert discard.kind == "discard"
        assert discard.own_slot == 4
    
    def test_draw_action_creation(self):
        """Тест создания действия взятия карты"""
        draw = Draw(place="hand")
        
        assert draw.kind == "draw"
        assert draw.place == "hand"
        assert draw.slot_index is None
    
    def test_draw_action_to_slot(self):
        """Тест взятия карты в слот"""
        draw = Draw(place="slot", slot_index=2)
        
        assert draw.place == "slot"
        assert draw.slot_index == 2


class TestAttackActions:
    """Тесты применения действий атаки"""
    
    def test_basic_attack_with_attacker(self):
        """Тест базовой атаки с атакующей картой"""
        ctx = TestDataBuilder.create_context()
        
        # Настроим атакующего
        attacker = Card(id="attacker", name="Attacker", atk=3)
        ctx.state.players["P1"].slots[0].card = attacker
        
        # Настроим цель
        target = Card(id="target", name="Target", hp=5)
        ctx.state.players["P2"].slots[1].card = target
        
        # Создаём действие атаки
        attack = Attack(
            target_player="P2",
            target_slot=1,
            attacker_slot=0,
            ammo_spend=0
        )
        
        result = apply_action(ctx, attack)
        
        # Проверяем результат
        assert result["phase"] == "resolution"
        
        # Цель должна получить урон 3 (атака атакующего)
        target_card = ctx.state.players["P2"].slots[1].card
        assert target_card.hp == 2  # 5 - 3 = 2
        
        # Проверяем лог
        TestAssertions.assert_log_contains(ctx.log, "attack", dmg=3)
    
    def test_attack_with_ammo(self):
        """Тест атаки с тратой боеприпасов"""
        ctx = TestDataBuilder.create_context()
        
        # Настроим атакующего
        attacker = Card(id="attacker", name="Attacker", atk=2)
        ctx.state.players["P1"].slots[0].card = attacker
        ctx.state.players["P1"].tokens.reserve_money = 5
        
        # Настроим цель
        target = Card(id="target", name="Target", hp=8)
        ctx.state.players["P2"].slots[1].card = target
        
        # Атака с тратой 2 боеприпасов
        attack = Attack(
            target_player="P2",
            target_slot=1,
            attacker_slot=0,
            ammo_spend=2
        )
        
        result = apply_action(ctx, attack)
        
        # Проверяем урон: 2 (атака) + 2 (боеприпасы) = 4
        target_card = ctx.state.players["P2"].slots[1].card
        assert target_card.hp == 4  # 8 - 4 = 4
        
        # Проверяем трату денег
        attacker_player = ctx.state.players["P1"]
        assert attacker_player.tokens.reserve_money == 3  # 5 - 2 = 3
        assert attacker_player.tokens.otboy == 2  # боеприпасы в отбой
        
        TestAssertions.assert_log_contains(ctx.log, "attack", dmg=4)
    
    def test_attack_insufficient_ammo(self):
        """Тест атаки с недостаточными боеприпасами"""
        ctx = TestDataBuilder.create_context()
        
        # Атакующий с малым количеством денег
        attacker = Card(id="attacker", name="Attacker", atk=1)
        ctx.state.players["P1"].slots[0].card = attacker
        ctx.state.players["P1"].tokens.reserve_money = 1  # только 1 деньга
        
        # Цель
        target = Card(id="target", name="Target", hp=5)
        ctx.state.players["P2"].slots[1].card = target
        
        # Пытаемся потратить 3 боеприпаса, но доступна только 1
        attack = Attack(
            target_player="P2",
            target_slot=1,
            attacker_slot=0,
            ammo_spend=3
        )
        
        result = apply_action(ctx, attack)
        
        # Урон: 1 (атака) + 1 (реально доступный боеприпас) = 2
        target_card = ctx.state.players["P2"].slots[1].card
        assert target_card.hp == 3  # 5 - 2 = 3
        
        # Потратили только 1 деньгу
        attacker_player = ctx.state.players["P1"]
        assert attacker_player.tokens.reserve_money == 0
        assert attacker_player.tokens.otboy == 1
    
    def test_attack_with_muscles_blocking(self):
        """Тест атаки с блокированием мышцами"""
        ctx = TestDataBuilder.create_context()
        
        # Атакующий
        attacker = Card(id="attacker", name="Attacker", atk=4)
        ctx.state.players["P1"].slots[0].card = attacker
        
        # Цель с защитой
        target = Card(id="target", name="Target", hp=5)
        target_slot = ctx.state.players["P2"].slots[1]
        target_slot.card = target
        target_slot.muscles = 2  # 2 мышцы для защиты
        
        attack = Attack(
            target_player="P2",
            target_slot=1,
            attacker_slot=0
        )
        
        result = apply_action(ctx, attack)
        
        # 4 урона: 2 поглощено мышцами, 2 прошло в HP
        assert target.hp == 3  # 5 - 2 = 3
        assert target_slot.muscles == 0  # все мышцы уничтожены
        
        # Мышцы ушли в отбой защитника
        defender_player = ctx.state.players["P2"]
        assert defender_player.tokens.otboy == 2
    
    def test_attack_killing_card(self):
        """Тест смертельной атаки"""
        ctx = TestDataBuilder.create_context()
        
        # Сильный атакующий
        attacker = Card(id="attacker", name="Attacker", atk=10)
        ctx.state.players["P1"].slots[0].card = attacker
        
        # Слабая цель
        target = Card(id="target", name="Target", hp=3)
        ctx.state.players["P2"].slots[1].card = target
        
        attack = Attack(
            target_player="P2",
            target_slot=1,
            attacker_slot=0
        )
        
        result = apply_action(ctx, attack)
        
        # Карта должна умереть
        target_card = ctx.state.players["P2"].slots[1].card
        assert target_card.hp == -7  # 3 - 10 = -7
    
    def test_attack_hand_when_no_board(self):
        """Тест атаки по руке когда нет карт на поле"""
        ctx = TestDataBuilder.create_context()
        ctx.state.config.hand_enabled = True
        
        # Атакующий
        attacker = Card(id="attacker", name="Attacker", atk=3)
        ctx.state.players["P1"].slots[0].card = attacker
        
        # P2 без карт на поле, но с картой в руке
        hand_card = Card(id="hand_card", name="Hand Card", hp=5)
        ctx.state.players["P2"].hand = [hand_card]
        
        attack = Attack(
            target_player="P2",
            target_slot=None,  # атака по руке
            attacker_slot=0
        )
        
        result = apply_action(ctx, attack)
        
        # Должна сработать атака по руке
        # Карта должна быть размещена на поле или получить урон напрямую
        TestAssertions.assert_log_contains(ctx.log, "attack")


class TestDefendActions:
    """Тесты применения действий защиты"""
    
    def test_basic_defend(self):
        """Тест базовой защиты"""
        ctx = TestDataBuilder.create_context()
        
        # Карта для защиты
        card = Card(id="defender", name="Defender", d=3)
        ctx.state.players["P1"].slots[1].card = card
        ctx.state.players["P1"].tokens.reserve_money = 5
        
        defend = Defend(target_slot=1, hire_count=2)
        
        result = apply_action(ctx, defend)
        
        assert result["phase"] == "resolution"
        
        # Проверяем защиту
        defender_slot = ctx.state.players["P1"].slots[1]
        assert defender_slot.muscles == 2
        
        # Проверяем трату денег
        player = ctx.state.players["P1"]
        assert player.tokens.reserve_money == 3  # 5 - 2 = 3
        
        TestAssertions.assert_log_contains(ctx.log, "defend", hired=2)
    
    def test_defend_exceeding_quota(self):
        """Тест защиты сверх квоты"""
        ctx = TestDataBuilder.create_context()
        
        # Карта с квотой защиты 2
        card = Card(id="defender", name="Defender", d=2)
        ctx.state.players["P1"].slots[1].card = card
        ctx.state.players["P1"].tokens.reserve_money = 10
        
        # Пытаемся нанять 5 мышц, но квота только 2
        defend = Defend(target_slot=1, hire_count=5)
        
        result = apply_action(ctx, defend)
        
        # Должно нанять только 2 мышцы (в пределах квоты)
        defender_slot = ctx.state.players["P1"].slots[1]
        assert defender_slot.muscles == 2
        
        # Потратить только 2 деньги
        player = ctx.state.players["P1"]
        assert player.tokens.reserve_money == 8  # 10 - 2 = 8
        
        TestAssertions.assert_log_contains(ctx.log, "defend", hired=2)
    
    def test_defend_insufficient_money(self):
        """Тест защиты при недостатке денег"""
        ctx = TestDataBuilder.create_context()
        
        # Карта с хорошей квотой защиты
        card = Card(id="defender", name="Defender", d=5)
        ctx.state.players["P1"].slots[1].card = card
        ctx.state.players["P1"].tokens.reserve_money = 2  # мало денег
        
        defend = Defend(target_slot=1, hire_count=4)
        
        result = apply_action(ctx, defend)
        
        # Должно нанять только 2 мышцы (сколько денег есть)
        defender_slot = ctx.state.players["P1"].slots[1]
        assert defender_slot.muscles == 2
        
        # Потратить все деньги
        player = ctx.state.players["P1"]
        assert player.tokens.reserve_money == 0
        
        TestAssertions.assert_log_contains(ctx.log, "defend", hired=2)
    
    def test_defend_empty_slot(self):
        """Тест защиты пустого слота"""
        ctx = TestDataBuilder.create_context()
        
        # Слот пустой
        defend = Defend(target_slot=1, hire_count=2)
        
        result = apply_action(ctx, defend)
        
        assert result.get("error") == "No card in slot"
        assert result.get("phase") == ""
    
    def test_defend_with_existing_muscles(self):
        """Тест защиты при уже имеющихся мышцах"""
        ctx = TestDataBuilder.create_context()
        
        # Карта с уже имеющейся защитой
        card = Card(id="defender", name="Defender", d=4)
        slot = ctx.state.players["P1"].slots[1]
        slot.card = card
        slot.muscles = 2  # уже есть 2 мышцы
        ctx.state.players["P1"].tokens.reserve_money = 5
        
        defend = Defend(target_slot=1, hire_count=3)
        
        result = apply_action(ctx, defend)
        
        # Квота 4, уже есть 2, можем добавить ещё 2
        assert slot.muscles == 4  # 2 + 2 = 4
        
        # Потратили только 2 деньги (не 3)
        player = ctx.state.players["P1"]
        assert player.tokens.reserve_money == 3  # 5 - 2 = 3
        
        TestAssertions.assert_log_contains(ctx.log, "defend", hired=2)


class TestInfluenceActions:
    """Тесты применения действий влияния"""
    
    def test_micro_bribe_success(self):
        """Тест успешного микро-подкупа"""
        ctx = TestDataBuilder.create_context()
        
        # Атакующий с деньгами
        ctx.state.players["P1"].tokens.reserve_money = 5
        
        # Цель с мышцами
        target_slot = ctx.state.players["P2"].slots[2]
        target_slot.card = Card(id="target", name="Target")
        target_slot.muscles = 3
        
        influence = Influence(
            micro_bribe_target_player="P2",
            micro_bribe_target_slot=2
        )
        
        result = apply_action(ctx, influence)
        
        assert result["phase"] == "resolution"
        
        # Проверяем трату денег атакующим
        attacker = ctx.state.players["P1"]
        assert attacker.tokens.reserve_money == 3  # 5 - 2 = 3
        assert attacker.tokens.otboy == 2
        
        # Проверяем потерю мышцы целью
        assert target_slot.muscles == 2  # 3 - 1 = 2
        
        # Мышца цели ушла в её отбой
        target_player = ctx.state.players["P2"]
        assert target_player.tokens.otboy == 1
        
        # Флаг использования должен быть установлен
        assert ctx.state.flags["micro_bribe_used"] is True
        
        TestAssertions.assert_log_contains(ctx.log, "micro_bribe", slot=2)
    
    def test_micro_bribe_insufficient_money(self):
        """Тест микро-подкупа при недостатке денег"""
        ctx = TestDataBuilder.create_context()
        
        # Атакующий без денег
        ctx.state.players["P1"].tokens.reserve_money = 1  # меньше чем нужно
        
        # Цель с мышцами
        target_slot = ctx.state.players["P2"].slots[2]
        target_slot.card = Card(id="target", name="Target")
        target_slot.muscles = 3
        
        influence = Influence(
            micro_bribe_target_player="P2",
            micro_bribe_target_slot=2
        )
        
        result = apply_action(ctx, influence)
        
        # Микро-подкуп не должен произойти
        assert target_slot.muscles == 3  # без изменений
        assert ctx.state.players["P1"].tokens.reserve_money == 1  # без изменений
        assert ctx.state.flags.get("micro_bribe_used", False) is False
    
    def test_micro_bribe_target_no_muscles(self):
        """Тест микро-подкупа цели без мышц"""
        ctx = TestDataBuilder.create_context()
        
        # Атакующий с деньгами
        ctx.state.players["P1"].tokens.reserve_money = 5
        
        # Цель без мышц
        target_slot = ctx.state.players["P2"].slots[2]
        target_slot.card = Card(id="target", name="Target")
        target_slot.muscles = 0
        
        influence = Influence(
            micro_bribe_target_player="P2",
            micro_bribe_target_slot=2
        )
        
        result = apply_action(ctx, influence)
        
        # Деньги должны потратиться, но мышцы не убираются
        attacker = ctx.state.players["P1"]
        assert attacker.tokens.reserve_money == 3  # 5 - 2 = 3
        assert attacker.tokens.otboy == 2
        
        # Мышцы цели остаются 0
        assert target_slot.muscles == 0
        
        # Флаг использования установлен
        assert ctx.state.flags["micro_bribe_used"] is True
    
    def test_micro_bribe_once_per_turn_restriction(self):
        """Тест ограничения микро-подкупа раз в ход"""
        ctx = TestDataBuilder.create_context()
        ctx.state.config.micro_bribe_once_per_turn = True
        ctx.state.flags["micro_bribe_used"] = True  # уже использовали
        
        # Атакующий с деньгами
        ctx.state.players["P1"].tokens.reserve_money = 5
        
        # Цель с мышцами
        target_slot = ctx.state.players["P2"].slots[2]
        target_slot.card = Card(id="target", name="Target")
        target_slot.muscles = 3
        
        influence = Influence(
            micro_bribe_target_player="P2",
            micro_bribe_target_slot=2
        )
        
        result = apply_action(ctx, influence)
        
        assert result.get("error") == "micro_bribe_already_used"
        
        # Состояние не должно измениться
        assert ctx.state.players["P1"].tokens.reserve_money == 5
        assert target_slot.muscles == 3
    
    def test_influence_without_micro_bribe(self):
        """Тест действия влияния без микро-подкупа"""
        ctx = TestDataBuilder.create_context()
        
        # Пустое действие влияния
        influence = Influence()
        
        result = apply_action(ctx, influence)
        
        assert result["phase"] == "resolution"
        
        # Никаких изменений не должно быть
        assert ctx.state.players["P1"].tokens.reserve_money == 12  # default
        assert ctx.state.flags.get("micro_bribe_used", False) is False


class TestDiscardActions:
    """Тесты применения действий сброса"""
    
    def test_discard_card_success(self):
        """Тест успешного сброса карты"""
        ctx = TestDataBuilder.create_context()
        
        # Карта для сброса
        card = Card(id="discard_me", name="Discard Me")
        slot = ctx.state.players["P1"].slots[3]
        slot.card = card
        slot.muscles = 2
        
        discard = DiscardCard(own_slot=3)
        
        result = apply_action(ctx, discard)
        
        assert result["phase"] == "resolution"
        
        # Слот должен очиститься
        assert slot.card is None
        assert slot.muscles == 0
        
        # Карта должна попасть в отбой
        assert len(ctx.state.discard_out_of_game) == 1
        assert ctx.state.discard_out_of_game[0].id == "discard_me"
        
        TestAssertions.assert_log_contains(ctx.log, "discard", slot=3)
    
    def test_discard_empty_slot(self):
        """Тест сброса из пустого слота"""
        ctx = TestDataBuilder.create_context()
        
        # Слот пустой
        discard = DiscardCard(own_slot=3)
        
        result = apply_action(ctx, discard)
        
        assert result["phase"] == "resolution"
        
        # Отбой должен остаться пустым
        assert len(ctx.state.discard_out_of_game) == 0
        
        # Лог может содержать событие или не содержать
        # Это зависит от реализации


class TestDrawActions:
    """Тесты применения действий взятия карт"""
    
    def test_draw_to_hand(self):
        """Тест взятия карты в руку"""
        ctx = TestDataBuilder.create_context()
        ctx.state.config.hand_enabled = True
        
        # Добавим карту в колоду
        card = Card(id="drawn_card", name="Drawn Card")
        ctx.state.deck = [card]
        
        draw = Draw(place="hand")
        
        result = apply_action(ctx, draw)
        
        assert result["phase"] == "resolution"
        
        # Карта должна попасть в руку
        player = ctx.state.players["P1"]
        assert len(player.hand) == 1
        assert player.hand[0].id == "drawn_card"
        
        # Колода должна опустеть
        assert len(ctx.state.deck) == 0
        
        TestAssertions.assert_log_contains(
            ctx.log, 
            "draw", 
            card="drawn_card"
        )
    
    def test_draw_to_slot(self):
        """Тест взятия карты в слот"""
        ctx = TestDataBuilder.create_context()
        
        # Добавим карту в колоду
        card = Card(id="drawn_card", name="Drawn Card")
        ctx.state.deck = [card]
        
        draw = Draw(place="slot", slot_index=2)
        
        result = apply_action(ctx, draw)
        
        assert result["phase"] == "resolution"
        
        # Карта должна попасть в слот
        player = ctx.state.players["P1"]
        target_slot = player.slots[2]
        assert target_slot.card is not None
        assert target_slot.card.id == "drawn_card"
        assert target_slot.face_up is True
        
        # Колода должна опустеть
        assert len(ctx.state.deck) == 0
        
        TestAssertions.assert_log_contains(
            ctx.log, 
            "draw", 
            card="drawn_card"
        )
    
    def test_draw_to_shelf(self):
        """Тест взятия карты на полку"""
        ctx = TestDataBuilder.create_context()
        
        # Добавим карту в колоду
        card = Card(id="drawn_card", name="Drawn Card")
        ctx.state.deck = [card]
        
        draw = Draw(place="shelf")
        
        result = apply_action(ctx, draw)
        
        assert result["phase"] == "resolution"
        
        # Карта должна попасть на полку
        assert len(ctx.state.shelf) == 1
        assert ctx.state.shelf[0].id == "drawn_card"
        
        # Колода должна опустеть
        assert len(ctx.state.deck) == 0
        
        TestAssertions.assert_log_contains(
            ctx.log, 
            "draw", 
            card="drawn_card"
        )
    
    def test_draw_empty_deck(self):
        """Тест взятия карты из пустой колоды"""
        ctx = TestDataBuilder.create_context()
        
        # Пустая колода
        ctx.state.deck = []
        
        draw = Draw(place="hand")
        
        result = apply_action(ctx, draw)
        
        assert result.get("error") == "deck_empty"
        
        # Рука должна остаться пустой
        player = ctx.state.players["P1"]
        assert len(player.hand) == 0
    
    def test_draw_recycle_shelf(self):
        """Тест переработки полки в колоду"""
        ctx = TestDataBuilder.create_context()
        
        # Пустая колода, но карты на полке
        ctx.state.deck = []
        shelf_card = Card(id="shelf_card", name="Shelf Card")
        ctx.state.shelf = [shelf_card]
        
        draw = Draw(place="hand")
        
        result = apply_action(ctx, draw)
        
        assert result["phase"] == "resolution"
        
        # Карта должна попасть в руку
        player = ctx.state.players["P1"]
        assert len(player.hand) == 1
        assert player.hand[0].id == "shelf_card"
        
        # Полка должна опустеть
        assert len(ctx.state.shelf) == 0
        
        TestAssertions.assert_log_contains(ctx.log, "shelf_recycled")
    
    def test_draw_event_card(self):
        """Тест взятия event карты"""
        ctx = TestDataBuilder.create_context()
        
        # Event карта в колоде
        event_card = Card(
            id="event_plus_cash",
            name="Event Card",
            type=CardType.event
        )
        ctx.state.deck = [event_card]
        
        # P1 имеет токены в отбое для события
        ctx.state.players["P1"].tokens.otboy = 3
        
        draw = Draw(place="hand")
        
        result = apply_action(ctx, draw)
        
        assert result["phase"] == "resolution"
        
        # Event карта не должна попасть в руку (выполняется сразу)
        player = ctx.state.players["P1"]
        assert len(player.hand) == 0
        
        # Должен сработать эффект события (возврат токенов из отбоя)
        # Для event_plus_cash: возвращает до 2 токенов из otboy в reserve
        assert player.tokens.reserve_money == 14  # 12 + 2
        assert player.tokens.otboy == 1  # 3 - 2
        
        TestAssertions.assert_log_contains(ctx.log, "draw_event", card="event_plus_cash")
    
    def test_draw_hand_disabled(self):
        """Тест взятия в руку при отключённой руке"""
        ctx = TestDataBuilder.create_context()
        ctx.state.config.hand_enabled = False
        
        # Карта в колоде
        card = Card(id="drawn_card", name="Drawn Card")
        ctx.state.deck = [card]
        
        draw = Draw(place="hand")
        
        result = apply_action(ctx, draw)
        
        assert result.get("error") == "hand_disabled"
        
        # Карта должна остаться в колоде
        assert len(ctx.state.deck) == 1
        assert ctx.state.deck[0].id == "drawn_card"
    
    def test_draw_to_occupied_slot(self):
        """Тест взятия карты в занятый слот"""
        ctx = TestDataBuilder.create_context()
        
        # Занятый слот
        existing_card = Card(id="existing", name="Existing")
        ctx.state.players["P1"].slots[2].card = existing_card
        
        # Карта для взятия
        new_card = Card(id="new_card", name="New Card")
        ctx.state.deck = [new_card]
        
        draw = Draw(place="slot", slot_index=2)
        
        result = apply_action(ctx, draw)
        
        assert result.get("error") == "slot_not_empty"
        
        # Состояние не должно измениться
        assert ctx.state.players["P1"].slots[2].card.id == "existing"
        assert len(ctx.state.deck) == 1
        assert ctx.state.deck[0].id == "new_card"

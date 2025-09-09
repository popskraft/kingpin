"""
Unit-тесты для системы эффектов engine/effects.py
"""

import pytest
from packages.engine.effects import register, get, _registry


class TestEffectsRegistry:
    """Тесты реестра эффектов"""
    
    def setup_method(self):
        """Очистка реестра перед каждым тестом"""
        _registry.clear()
    
    def test_register_effect(self):
        """Тест регистрации эффекта"""
        @register("test_effect")
        def test_function(ctx, payload):
            return "test_result"
        
        # Проверяем что функция зарегистрирована
        assert "test_effect" in _registry
        assert _registry["test_effect"] == test_function
        
        # Проверяем что декоратор возвращает оригинальную функцию
        assert test_function(None, None) == "test_result"
    
    def test_get_existing_effect(self):
        """Тест получения существующего эффекта"""
        @register("existing_effect")
        def existing_function(ctx, payload):
            return "existing_result"
        
        retrieved_function = get("existing_effect")
        
        assert retrieved_function is not None
        assert retrieved_function == existing_function
        assert retrieved_function(None, None) == "existing_result"
    
    def test_get_nonexistent_effect(self):
        """Тест получения несуществующего эффекта"""
        result = get("nonexistent_effect")
        
        assert result is None
    
    def test_register_multiple_effects(self):
        """Тест регистрации нескольких эффектов"""
        @register("effect_1")
        def effect_1(ctx, payload):
            return "result_1"
        
        @register("effect_2")
        def effect_2(ctx, payload):
            return "result_2"
        
        @register("effect_3")
        def effect_3(ctx, payload):
            return "result_3"
        
        # Проверяем что все эффекты зарегистрированы
        assert len(_registry) == 3
        assert get("effect_1") == effect_1
        assert get("effect_2") == effect_2
        assert get("effect_3") == effect_3
    
    def test_register_overwrites_existing(self):
        """Тест перезаписи существующего эффекта"""
        @register("overwrite_test")
        def original_function(ctx, payload):
            return "original"
        
        @register("overwrite_test")
        def new_function(ctx, payload):
            return "new"
        
        # Проверяем что новая функция перезаписала старую
        retrieved = get("overwrite_test")
        assert retrieved == new_function
        assert retrieved(None, None) == "new"
    
    def test_register_preserves_function_properties(self):
        """Тест сохранения свойств функции после регистрации"""
        @register("function_with_props")
        def function_with_docstring(ctx, payload):
            """This is a test function with docstring"""
            return "result"
        
        retrieved = get("function_with_props")
        
        # Проверяем что свойства функции сохранились
        assert retrieved.__name__ == "function_with_docstring"
        assert retrieved.__doc__ == "This is a test function with docstring"
    
    def test_effect_function_signature(self):
        """Тест правильной сигнатуры функций эффектов"""
        @register("signature_test")
        def effect_function(ctx, payload):
            # Функция должна принимать ctx и payload
            assert ctx is not None
            assert payload is not None
            return f"ctx: {ctx}, payload: {payload}"
        
        # Тестируем вызов с параметрами
        result = effect_function("test_ctx", "test_payload")
        assert result == "ctx: test_ctx, payload: test_payload"
    
    def test_registry_isolation(self):
        """Тест изоляции реестра между тестами"""
        # Этот тест проверяет что setup_method правильно очищает реестр
        
        # Реестр должен быть пустым в начале
        assert len(_registry) == 0
        
        # Добавим эффект
        @register("isolation_test")
        def test_effect(ctx, payload):
            return "test"
        
        assert len(_registry) == 1
        
        # После очистки в следующем тесте реестр должен быть пустым снова


class TestPredefinedEffects:
    """Тесты предопределённых эффектов"""
    
    def setup_method(self):
        """Настройка перед каждым тестом"""
        _registry.clear()
    
    def test_heal_self_effect_exists(self):
        """Тест существования эффекта heal_self_1"""
        # Импортируем effects.py для загрузки предопределённых эффектов
        from packages.engine import effects
        
        # Проверяем что эффект зарегистрирован
        heal_effect = get("heal_self_1")
        assert heal_effect is not None
    
    def test_heal_self_effect_functionality(self):
        """Тест функциональности эффекта heal_self_1"""
        from packages.engine import effects
        from packages.engine.engine import Ctx
        from packages.engine.models import GameState, PlayerState, Card, Slot
        from tests.test_helpers import TestDataBuilder
        
        # Получаем эффект
        heal_effect = get("heal_self_1")
        
        if heal_effect is None:
            pytest.skip("heal_self_1 effect not implemented yet")
        
        # Создаём контекст для тестирования
        ctx = TestDataBuilder.create_context()
        
        # Создаём карту с уроном
        damaged_card = Card(id="damaged", name="Damaged Card", hp=3)
        damaged_card.hp = 1  # получила урон
        
        slot = Slot(card=damaged_card)
        ctx.state.players["P1"].slots[0] = slot
        
        # Тестируем эффект
        payload = {"target_slot": 0, "player": "P1"}
        heal_effect(ctx, payload)
        
        # Проверяем что карта получила лечение
        # (точная логика зависит от реализации эффекта)
        healed_card = ctx.state.players["P1"].slots[0].card
        assert healed_card.hp > 1  # должна быть вылечена


class TestEffectIntegration:
    """Интеграционные тесты системы эффектов"""
    
    def setup_method(self):
        """Настройка перед каждым тестом"""
        _registry.clear()
    
    def test_effect_call_from_game_logic(self):
        """Тест вызова эффекта из игровой логики"""
        # Регистрируем тестовый эффект
        effect_calls = []  # для отслеживания вызовов
        
        @register("test_game_effect")
        def test_game_effect(ctx, payload):
            effect_calls.append({
                "ctx": ctx,
                "payload": payload,
                "player_id": payload.get("player_id"),
                "effect_power": payload.get("power", 1)
            })
            
            # Имитируем изменение состояния игры
            if payload.get("player_id") and ctx:
                player = ctx.state.players.get(payload["player_id"])
                if player:
                    player.tokens.reserve_money += payload.get("power", 1)
        
        # Создаём игровой контекст
        from tests.test_helpers import TestDataBuilder
        ctx = TestDataBuilder.create_context()
        
        # "Вызываем эффект из игровой логики"
        effect_function = get("test_game_effect")
        payload = {"player_id": "P1", "power": 3}
        effect_function(ctx, payload)
        
        # Проверяем что эффект был вызван и сработал
        assert len(effect_calls) == 1
        assert effect_calls[0]["player_id"] == "P1"
        assert effect_calls[0]["effect_power"] == 3
        
        # Проверяем изменение состояния
        player = ctx.state.players["P1"]
        assert player.tokens.reserve_money == 15  # 12 (default) + 3 (effect)
    
    def test_multiple_effects_chain(self):
        """Тест цепочки из нескольких эффектов"""
        execution_order = []
        
        @register("chain_effect_1")
        def chain_effect_1(ctx, payload):
            execution_order.append("effect_1")
            # Первый эффект добавляет деньги
            if ctx and payload.get("player_id"):
                player = ctx.state.players[payload["player_id"]]
                player.tokens.reserve_money += 2
        
        @register("chain_effect_2")
        def chain_effect_2(ctx, payload):
            execution_order.append("effect_2")
            # Второй эффект удваивает текущие деньги
            if ctx and payload.get("player_id"):
                player = ctx.state.players[payload["player_id"]]
                player.tokens.reserve_money *= 2
        
        @register("chain_effect_3")
        def chain_effect_3(ctx, payload):
            execution_order.append("effect_3")
            # Третий эффект вычитает 5
            if ctx and payload.get("player_id"):
                player = ctx.state.players[payload["player_id"]]
                player.tokens.reserve_money -= 5
        
        # Выполняем цепочку эффектов
        from tests.test_helpers import TestDataBuilder
        ctx = TestDataBuilder.create_context()
        
        # Начальные деньги: 12
        payload = {"player_id": "P1"}
        
        get("chain_effect_1")(ctx, payload)  # 12 + 2 = 14
        get("chain_effect_2")(ctx, payload)  # 14 * 2 = 28
        get("chain_effect_3")(ctx, payload)  # 28 - 5 = 23
        
        # Проверяем порядок выполнения
        assert execution_order == ["effect_1", "effect_2", "effect_3"]
        
        # Проверяем финальное состояние
        player = ctx.state.players["P1"]
        assert player.tokens.reserve_money == 23
    
    def test_effect_error_handling(self):
        """Тест обработки ошибок в эффектах"""
        @register("error_effect")
        def error_effect(ctx, payload):
            raise ValueError("Test error in effect")
        
        # Получаем эффект
        effect_function = get("error_effect")
        
        # Проверяем что эффект существует
        assert effect_function is not None
        
        # Проверяем что ошибка в эффекте поднимается
        from tests.test_helpers import TestDataBuilder
        ctx = TestDataBuilder.create_context()
        
        with pytest.raises(ValueError, match="Test error in effect"):
            effect_function(ctx, {})
    
    def test_effect_with_complex_payload(self):
        """Тест эффекта со сложным payload"""
        @register("complex_payload_effect")
        def complex_payload_effect(ctx, payload):
            # Эффект обрабатывает сложную структуру данных
            targets = payload.get("targets", [])
            effect_type = payload.get("type", "heal")
            amount = payload.get("amount", 1)
            conditions = payload.get("conditions", {})
            
            results = []
            
            for target in targets:
                player_id = target.get("player")
                slot_index = target.get("slot")
                
                if ctx and player_id and slot_index is not None:
                    player = ctx.state.players.get(player_id)
                    if player and 0 <= slot_index < len(player.slots):
                        slot = player.slots[slot_index]
                        
                        if effect_type == "heal" and slot.card:
                            # Проверяем условия
                            min_hp = conditions.get("min_hp", 0)
                            if slot.card.hp >= min_hp:
                                slot.card.hp += amount
                                results.append(f"healed_{player_id}_{slot_index}")
                        
                        elif effect_type == "shield" and slot.card:
                            max_shields = conditions.get("max_shields", 10)
                            if slot.muscles < max_shields:
                                slot.muscles += amount
                                results.append(f"shielded_{player_id}_{slot_index}")
            
            return results
        
        # Тестируем со сложным payload
        from tests.test_helpers import TestDataBuilder
        ctx = TestDataBuilder.create_context()
        
        # Подготавливаем карты
        card1 = TestDataBuilder.create_basic_card("card1")
        card1.hp = 2  # повреждённая
        ctx.state.players["P1"].slots[0].card = card1
        
        card2 = TestDataBuilder.create_basic_card("card2")
        card2.hp = 5  # здоровая
        ctx.state.players["P2"].slots[1].card = card2
        ctx.state.players["P2"].slots[1].muscles = 1
        
        # Сложный payload
        complex_payload = {
            "type": "heal",
            "amount": 2,
            "targets": [
                {"player": "P1", "slot": 0},
                {"player": "P2", "slot": 1},
                {"player": "P1", "slot": 5}  # пустой слот
            ],
            "conditions": {
                "min_hp": 1  # лечить только карты с HP >= 1
            }
        }
        
        # Выполняем эффект
        effect_function = get("complex_payload_effect")
        results = effect_function(ctx, complex_payload)
        
        # Проверяем результаты
        assert "healed_P1_0" in results  # card1 была вылечена
        assert "healed_P2_1" in results  # card2 была вылечена
        assert len(results) == 2  # пустой слот не обработан
        
        # Проверяем изменения
        assert ctx.state.players["P1"].slots[0].card.hp == 4  # 2 + 2
        assert ctx.state.players["P2"].slots[1].card.hp == 7  # 5 + 2

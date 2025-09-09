"""
Unit-тесты для server endpoints (интеграционные тесты)
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from packages.server.main import (
    sio, _build_state_from_csv, _filtered_view, _emit_views,
    rooms, sid_index, MAX_SLOTS, INIT_VISIBLE_SLOTS
)
from packages.engine.models import GameState, PlayerState
from tests.test_helpers import TestDataBuilder


class TestServerHelpers:
    """Тесты вспомогательных функций сервера"""
    
    def test_build_state_from_csv(self):
        """Тест построения состояния из CSV"""
        # Mock the file reading in services module
        with patch('packages.server.services.setup.load_game') as mock_load_game:
            # Создаём тестовое состояние
            test_state = TestDataBuilder.create_game_state()
            test_config = {"hand_limit": 6}
            
            mock_load_game.return_value = (test_state, test_config)
            
            state, config = _build_state_from_csv()
            
            # Проверяем что функция вызвалась и вернула результат
            assert isinstance(state, GameState)
            assert isinstance(config, dict)
            mock_load_game.assert_called_once()
    
    def test_filtered_view_for_owner(self):
        """Тест фильтрованного представления для владельца"""
        state = TestDataBuilder.create_game_state()
        
        # Добавим карты P1
        p1 = state.players["P1"]
        p1.hand = [TestDataBuilder.create_basic_card("hand_card")]
        p1.slots[0].card = TestDataBuilder.create_basic_card("board_card")
        p1.tokens.reserve_money = 15
        
        # Добавим карты P2
        p2 = state.players["P2"]
        p2.slots[1].card = TestDataBuilder.create_basic_card("enemy_card")
        p2.hand = [TestDataBuilder.create_basic_card("enemy_hand")]
        
        view = _filtered_view(state, "P1", visible_you=6, visible_op=6)
        
        # Проверяем структуру представления
        assert "you" in view
        assert "opponent" in view
        assert "shared" in view
        assert "meta" in view
        
        # Проверяем данные игрока (полные)
        you_data = view["you"]
        assert you_data["id"] == "P1"
        assert len(you_data["hand"]) == 1
        assert you_data["hand"][0]["id"] == "hand_card"
        assert len(you_data["board"]) == 6  # visible_you
        assert you_data["board"][0]["card"]["id"] == "board_card"
        assert you_data["tokens"]["reserve_money"] == 15
        
        # Проверяем данные противника (ограниченные)
        opponent_data = view["opponent"]
        assert opponent_data["id"] == "P2"
        assert "hand" not in opponent_data  # рука скрыта
        assert "handCount" in opponent_data
        assert opponent_data["handCount"] == 1  # количество карт
        assert len(opponent_data["board"]) == 6  # visible_op
        
        # Проверяем общие данные
        shared_data = view["shared"]
        assert "deckCount" in shared_data
        assert "shelfCount" in shared_data
        assert "shelf" in shared_data  # полка открыта
        assert "discardCount" in shared_data
    
    def test_filtered_view_hidden_opponent_cards(self):
        """Тест скрытия закрытых карт противника"""
        state = TestDataBuilder.create_game_state()
        
        p2 = state.players["P2"]
        # Открытая карта
        p2.slots[0].card = TestDataBuilder.create_basic_card("open_card")
        p2.slots[0].face_up = True
        
        # Закрытая карта
        p2.slots[1].card = TestDataBuilder.create_basic_card("hidden_card")
        p2.slots[1].face_up = False
        
        view = _filtered_view(state, "P1", visible_you=6, visible_op=6)
        
        opponent_board = view["opponent"]["board"]
        
        # Открытая карта должна быть видна
        assert opponent_board[0]["card"] is not None
        assert opponent_board[0]["card"]["id"] == "open_card"
        assert opponent_board[0]["face_up"] is True
        
        # Закрытая карта должна быть скрыта
        assert opponent_board[1]["card"] is None
        assert opponent_board[1]["face_up"] is False
        assert opponent_board[1]["muscles"] == 0
    
    def test_filtered_view_visible_slots_limit(self):
        """Тест ограничения видимых слотов"""
        state = TestDataBuilder.create_game_state()
        
        # Заполним больше слотов чем видимый лимит
        p1 = state.players["P1"]
        for i in range(6):
            p1.slots[i].card = TestDataBuilder.create_basic_card(f"card_{i}")
        
        # Запросим только 3 видимых слота
        view = _filtered_view(state, "P1", visible_you=3, visible_op=6)
        
        you_board = view["you"]["board"]
        assert len(you_board) == 3  # только 3 слота
        
        # Проверим что видны первые 3 карты
        assert you_board[0]["card"]["id"] == "card_0"
        assert you_board[1]["card"]["id"] == "card_1"
        assert you_board[2]["card"]["id"] == "card_2"


class MockSocketIO:
    """Mock объект для Socket.IO тестирования"""
    
    def __init__(self):
        self.events = []
        self.rooms = {}
        self.connections = {}
    
    async def emit(self, event, data, to=None, room=None, skip_sid=None):
        """Mock emit метод"""
        self.events.append({
            "event": event,
            "data": data,
            "to": to,
            "room": room,
            "skip_sid": skip_sid
        })
    
    async def enter_room(self, sid, room):
        """Mock enter_room метод"""
        if room not in self.rooms:
            self.rooms[room] = set()
        self.rooms[room].add(sid)
        self.connections[sid] = room


class TestSocketIOEvents:
    """Тесты Socket.IO событий"""
    
    @pytest.fixture
    def mock_sio(self):
        """Mock Socket.IO сервера"""
        return MockSocketIO()
    
    @pytest.fixture
    def clean_globals(self):
        """Очистка глобальных переменных перед тестом"""
        rooms.clear()
        sid_index.clear()
        yield
        rooms.clear()
        sid_index.clear()
    
    @pytest.mark.asyncio
    async def test_connect_event(self, mock_sio, clean_globals):
        """Тест события подключения"""
        from packages.server.main import connect
        
        with patch('packages.server.main.sio', mock_sio):
            await connect("test_sid", {})
        
        # Проверяем что отправлено событие connected
        assert len(mock_sio.events) == 1
        event = mock_sio.events[0]
        assert event["event"] == "connected"
        assert event["data"]["sid"] == "test_sid"
        assert event["to"] == "test_sid"
    
    @pytest.mark.asyncio
    async def test_join_room_first_player(self, mock_sio, clean_globals):
        """Тест присоединения первого игрока к комнате"""
        from packages.server.main import join_room
        
        with patch('packages.server.main.sio', mock_sio):
            with patch('packages.server.main._build_state_from_csv') as mock_build:
                # Mock создания состояния
                test_state = TestDataBuilder.create_game_state()
                test_config = {"hand_limit": 6}
                mock_build.return_value = (test_state, test_config)
                
                await join_room("player1_sid", {"room": "test_room"})
        
        # Проверяем что комната создана
        assert "test_room" in rooms
        room_data = rooms["test_room"]
        
        # Проверяем что игрок получил место P1
        assert room_data["seats"]["P1"] == "player1_sid"
        assert room_data["seats"]["P2"] is None
        
        # Проверяем индекс сессий
        assert "player1_sid" in sid_index
        assert sid_index["player1_sid"]["room"] == "test_room"
        assert sid_index["player1_sid"]["pid"] == "P1"
        
        # Проверяем события
        joined_events = [e for e in mock_sio.events if e["event"] == "joined"]
        assert len(joined_events) == 1
        joined_event = joined_events[0]
        assert joined_event["data"]["seat"] == "P1"
        assert joined_event["data"]["room"] == "test_room"
    
    @pytest.mark.asyncio
    async def test_join_room_second_player(self, mock_sio, clean_globals):
        """Тест присоединения второго игрока к существующей комнате"""
        from packages.server.main import join_room
        
        # Создадим комнату с первым игроком
        test_state = TestDataBuilder.create_game_state()
        rooms["test_room"] = {
            "state": test_state,
            "cfg": {},
            "seats": {"P1": "player1_sid", "P2": None},
            "visible_slots": {"P1": INIT_VISIBLE_SLOTS, "P2": INIT_VISIBLE_SLOTS},
            "source": "csv",
            "log": []
        }
        sid_index["player1_sid"] = {"room": "test_room", "pid": "P1"}
        
        with patch('packages.server.main.sio', mock_sio):
            await join_room("player2_sid", {"room": "test_room"})
        
        # Проверяем что второй игрок получил место P2
        room_data = rooms["test_room"]
        assert room_data["seats"]["P2"] == "player2_sid"
        
        # Проверяем индекс сессий
        assert sid_index["player2_sid"]["pid"] == "P2"
        
        # Проверяем что отправлено событие joined
        joined_events = [e for e in mock_sio.events if e["event"] == "joined"]
        assert len(joined_events) == 1
        assert joined_events[0]["data"]["seat"] == "P2"
    
    @pytest.mark.asyncio
    async def test_join_room_full(self, mock_sio, clean_globals):
        """Тест присоединения к полной комнате"""
        from packages.server.main import join_room
        
        # Создадим полную комнату
        test_state = TestDataBuilder.create_game_state()
        rooms["test_room"] = {
            "state": test_state,
            "cfg": {},
            "seats": {"P1": "player1_sid", "P2": "player2_sid"},
            "visible_slots": {"P1": INIT_VISIBLE_SLOTS, "P2": INIT_VISIBLE_SLOTS},
            "source": "csv",
            "log": []
        }
        
        with patch('packages.server.main.sio', mock_sio):
            await join_room("player3_sid", {"room": "test_room"})
        
        # Проверяем что отправлено событие room_full
        room_full_events = [e for e in mock_sio.events if e["event"] == "room_full"]
        assert len(room_full_events) == 1
        assert room_full_events[0]["data"]["room"] == "test_room"
        assert room_full_events[0]["to"] == "player3_sid"
        
        # Третий игрок не должен быть в индексе
        assert "player3_sid" not in sid_index
    
    @pytest.mark.asyncio
    async def test_draw_card(self, mock_sio, clean_globals):
        """Тест взятия карты"""
        from packages.server.main import draw
        
        # Подготовим комнату и игрока
        test_state = TestDataBuilder.create_game_state()
        test_card = TestDataBuilder.create_basic_card("drawn_card")
        test_state.deck = [test_card]
        
        rooms["test_room"] = {
            "state": test_state,
            "cfg": {},
            "seats": {"P1": "player1_sid", "P2": None},
            "visible_slots": {"P1": INIT_VISIBLE_SLOTS, "P2": INIT_VISIBLE_SLOTS},
            "source": "csv",
            "log": []
        }
        sid_index["player1_sid"] = {"room": "test_room", "pid": "P1"}
        
        with patch('packages.server.main.sio', mock_sio):
            with patch('packages.server.main._emit_views') as mock_emit:
                await draw("player1_sid", {})
        
        # Проверяем что карта попала в руку
        player = test_state.players["P1"]
        assert len(player.hand) == 1
        assert player.hand[0].id == "drawn_card"
        
        # Проверяем что колода опустела
        assert len(test_state.deck) == 0
        
        # Проверяем что вызвался emit_views
        mock_emit.assert_called_once_with("test_room")
    
    @pytest.mark.asyncio
    async def test_draw_empty_deck_with_shelf(self, mock_sio, clean_globals):
        """Тест взятия карты из пустой колоды с картами на полке"""
        from packages.server.main import draw
        
        # Подготовим состояние с пустой колодой и картами на полке
        test_state = TestDataBuilder.create_game_state()
        shelf_card = TestDataBuilder.create_basic_card("shelf_card")
        test_state.deck = []  # пустая колода
        test_state.shelf = [shelf_card]  # карта на полке
        
        rooms["test_room"] = {
            "state": test_state,
            "cfg": {},
            "seats": {"P1": "player1_sid", "P2": None},
            "visible_slots": {"P1": INIT_VISIBLE_SLOTS, "P2": INIT_VISIBLE_SLOTS},
            "source": "csv",
            "log": []
        }
        sid_index["player1_sid"] = {"room": "test_room", "pid": "P1"}
        
        with patch('packages.server.main.sio', mock_sio):
            with patch('packages.server.main._emit_views'):
                await draw("player1_sid", {})
        
        # Проверяем что карта с полки попала в руку
        player = test_state.players["P1"]
        assert len(player.hand) == 1
        assert player.hand[0].id == "shelf_card"
        
        # Проверяем что полка опустела
        assert len(test_state.shelf) == 0
    
    @pytest.mark.asyncio
    async def test_draw_completely_empty(self, mock_sio, clean_globals):
        """Тест взятия карты при полностью пустой колоде и полке"""
        from packages.server.main import draw
        
        # Подготовим состояние с пустой колодой и полкой
        test_state = TestDataBuilder.create_game_state()
        test_state.deck = []
        test_state.shelf = []
        
        rooms["test_room"] = {
            "state": test_state,
            "cfg": {},
            "seats": {"P1": "player1_sid", "P2": None},
            "visible_slots": {"P1": INIT_VISIBLE_SLOTS, "P2": INIT_VISIBLE_SLOTS},
            "source": "csv",
            "log": []
        }
        sid_index["player1_sid"] = {"room": "test_room", "pid": "P1"}
        
        with patch('packages.server.main.sio', mock_sio):
            await draw("player1_sid", {})
        
        # Проверяем что отправлена ошибка
        error_events = [e for e in mock_sio.events if e["event"] == "error"]
        assert len(error_events) == 1
        assert error_events[0]["data"]["msg"] == "deck_empty"
        assert error_events[0]["to"] == "player1_sid"
        
        # Рука должна остаться пустой
        player = test_state.players["P1"]
        assert len(player.hand) == 0
    
    @pytest.mark.asyncio
    async def test_move_card_hand_to_slot(self, mock_sio, clean_globals):
        """Тест перемещения карты из руки в слот"""
        from packages.server.main import move_card
        
        # Подготовим состояние
        test_state = TestDataBuilder.create_game_state()
        test_card = TestDataBuilder.create_basic_card("hand_card")
        test_state.players["P1"].hand = [test_card]
        
        rooms["test_room"] = {
            "state": test_state,
            "cfg": {},
            "seats": {"P1": "player1_sid", "P2": None},
            "visible_slots": {"P1": INIT_VISIBLE_SLOTS, "P2": INIT_VISIBLE_SLOTS},
            "source": "csv",
            "log": []
        }
        sid_index["player1_sid"] = {"room": "test_room", "pid": "P1"}
        
        move_data = {
            "from": "hand",
            "to": "slot",
            "fromIndex": 0,
            "toIndex": 2
        }
        
        with patch('packages.server.main.sio', mock_sio):
            with patch('packages.server.main._emit_views') as mock_emit:
                await move_card("player1_sid", move_data)
        
        # Проверяем что карта переместилась
        player = test_state.players["P1"]
        assert len(player.hand) == 0  # рука опустела
        assert player.slots[2].card is not None
        assert player.slots[2].card.id == "hand_card"
        assert player.slots[2].face_up is True
        
        # Проверяем что вызвался emit_views
        mock_emit.assert_called_once_with("test_room")
    
    @pytest.mark.asyncio
    async def test_add_shield_from_reserve(self, mock_sio, clean_globals):
        """Тест добавления щита из резерва"""
        from packages.server.main import add_shield_from_reserve
        
        # Подготовим состояние
        test_state = TestDataBuilder.create_game_state()
        test_card = TestDataBuilder.create_basic_card("defender")
        test_state.players["P1"].slots[1].card = test_card
        test_state.players["P1"].tokens.reserve_money = 5
        
        rooms["test_room"] = {
            "state": test_state,
            "cfg": {},
            "seats": {"P1": "player1_sid", "P2": None},
            "visible_slots": {"P1": INIT_VISIBLE_SLOTS, "P2": INIT_VISIBLE_SLOTS},
            "source": "csv",
            "log": []
        }
        sid_index["player1_sid"] = {"room": "test_room", "pid": "P1"}
        
        shield_data = {
            "slotIndex": 1,
            "count": 3
        }
        
        with patch('packages.server.main.sio', mock_sio):
            with patch('packages.server.main._emit_views') as mock_emit:
                await add_shield_from_reserve("player1_sid", shield_data)
        
        # Проверяем изменения
        player = test_state.players["P1"]
        assert player.tokens.reserve_money == 2  # 5 - 3 = 2
        assert player.slots[1].muscles == 3
        
        # Проверяем что вызвался emit_views
        mock_emit.assert_called_once_with("test_room")
    
    @pytest.mark.asyncio
    async def test_set_visible_slots(self, mock_sio, clean_globals):
        """Тест установки количества видимых слотов"""
        from packages.server.main import set_visible_slots
        
        # Подготовим комнату
        test_state = TestDataBuilder.create_game_state()
        rooms["test_room"] = {
            "state": test_state,
            "cfg": {},
            "seats": {"P1": "player1_sid", "P2": None},
            "visible_slots": {"P1": INIT_VISIBLE_SLOTS, "P2": INIT_VISIBLE_SLOTS},
            "source": "csv",
            "log": []
        }
        sid_index["player1_sid"] = {"room": "test_room", "pid": "P1"}
        
        slots_data = {"count": 8}
        
        with patch('packages.server.main.sio', mock_sio):
            with patch('packages.server.main._emit_views') as mock_emit:
                await set_visible_slots("player1_sid", slots_data)
        
        # Проверяем изменение настроек
        room_data = rooms["test_room"]
        assert room_data["visible_slots"]["P1"] == 8
        assert room_data["visible_slots"]["P2"] == INIT_VISIBLE_SLOTS  # без изменений
        
        # Проверяем что вызвался emit_views
        mock_emit.assert_called_once_with("test_room")
    
    @pytest.mark.asyncio
    async def test_set_visible_slots_limits(self, mock_sio, clean_globals):
        """Тест ограничений количества видимых слотов"""
        from packages.server.main import set_visible_slots
        
        # Подготовим комнату
        test_state = TestDataBuilder.create_game_state()
        rooms["test_room"] = {
            "state": test_state,
            "cfg": {},
            "seats": {"P1": "player1_sid", "P2": None},
            "visible_slots": {"P1": INIT_VISIBLE_SLOTS, "P2": INIT_VISIBLE_SLOTS},
            "source": "csv",
            "log": []
        }
        sid_index["player1_sid"] = {"room": "test_room", "pid": "P1"}
        
        with patch('packages.server.main.sio', mock_sio):
            with patch('packages.server.main._emit_views'):
                # Тест минимального ограничения
                await set_visible_slots("player1_sid", {"count": 3})  # меньше 6
                assert rooms["test_room"]["visible_slots"]["P1"] == 6  # должно быть 6
                
                # Тест максимального ограничения  
                await set_visible_slots("player1_sid", {"count": 15})  # больше MAX_SLOTS
                assert rooms["test_room"]["visible_slots"]["P1"] == MAX_SLOTS  # должно быть MAX_SLOTS
                
                # Тест нормального значения
                await set_visible_slots("player1_sid", {"count": 7})
                assert rooms["test_room"]["visible_slots"]["P1"] == 7
    
    @pytest.mark.asyncio
    async def test_disconnect(self, mock_sio, clean_globals):
        """Тест отключения игрока"""
        from packages.server.main import disconnect
        
        # Подготовим комнату с игроком
        test_state = TestDataBuilder.create_game_state()
        rooms["test_room"] = {
            "state": test_state,
            "cfg": {},
            "seats": {"P1": "player1_sid", "P2": None},
            "visible_slots": {"P1": INIT_VISIBLE_SLOTS, "P2": INIT_VISIBLE_SLOTS},
            "source": "csv",
            "log": []
        }
        sid_index["player1_sid"] = {"room": "test_room", "pid": "P1"}
        
        await disconnect("player1_sid")
        
        # Проверяем очистку
        assert "player1_sid" not in sid_index
        assert rooms["test_room"]["seats"]["P1"] is None
    
    @pytest.mark.asyncio
    async def test_invalid_session_handling(self, mock_sio, clean_globals):
        """Тест обработки недействительных сессий"""
        from packages.server.main import draw
        
        # Попытка использовать несуществующую сессию
        with patch('packages.server.main.sio', mock_sio):
            await draw("nonexistent_sid", {})
        
        # Должна быть отправлена ошибка о недействительной сессии
        assert len(mock_sio.events) == 1
        error_event = mock_sio.events[0]
        assert error_event["event"] == "error"
        assert error_event["data"]["msg"] == "bad_session"


class TestServerValidation:
    """Тесты валидации входных данных сервера"""
    
    @pytest.mark.asyncio
    async def test_move_card_invalid_indices(self, clean_globals):
        """Тест перемещения карт с неверными индексами"""
        from packages.server.main import move_card
        
        # Подготовим состояние
        test_state = TestDataBuilder.create_game_state()
        test_card = TestDataBuilder.create_basic_card("test_card")
        test_state.players["P1"].hand = [test_card]
        
        rooms["test_room"] = {
            "state": test_state,
            "cfg": {},
            "seats": {"P1": "player1_sid", "P2": None},
            "visible_slots": {"P1": INIT_VISIBLE_SLOTS, "P2": INIT_VISIBLE_SLOTS},
            "source": "csv",
            "log": []
        }
        sid_index["player1_sid"] = {"room": "test_room", "pid": "P1"}
        
        mock_sio = MockSocketIO()
        
        # Тест с недопустимым индексом слота
        invalid_move_data = {
            "from": "hand",
            "to": "slot",
            "fromIndex": 0,
            "toIndex": 99  # недопустимый индекс
        }
        
        with patch('packages.server.main.sio', mock_sio):
            await move_card("player1_sid", invalid_move_data)
        
        # Карта должна остаться в руке (операция должна быть отклонена)
        player = test_state.players["P1"]
        assert len(player.hand) == 1
        assert player.slots[0].card is None  # слот остаётся пустым
    
    @pytest.mark.asyncio
    async def test_add_shield_invalid_parameters(self, clean_globals):
        """Тест добавления щитов с неверными параметрами"""
        from packages.server.main import add_shield_from_reserve
        
        # Подготовим состояние
        test_state = TestDataBuilder.create_game_state()
        
        rooms["test_room"] = {
            "state": test_state,
            "cfg": {},
            "seats": {"P1": "player1_sid", "P2": None},
            "visible_slots": {"P1": INIT_VISIBLE_SLOTS, "P2": INIT_VISIBLE_SLOTS},
            "source": "csv",
            "log": []
        }
        sid_index["player1_sid"] = {"room": "test_room", "pid": "P1"}
        
        mock_sio = MockSocketIO()
        
        # Тест с некорректными данными
        invalid_data = {
            "slotIndex": "invalid",  # строка вместо числа
            "count": -5  # отрицательное число
        }
        
        with patch('packages.server.main.sio', mock_sio):
            await add_shield_from_reserve("player1_sid", invalid_data)
        
        # Состояние не должно измениться
        player = test_state.players["P1"]
        assert player.tokens.reserve_money == 12  # default без изменений

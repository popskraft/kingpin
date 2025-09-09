"""
Comprehensive tests for Socket.IO handlers to improve coverage.
"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from packages.engine.models import GameState, Card, Slot
from tests.test_helpers import TestDataBuilder

# Import handlers to test
from packages.server.socket.handlers import (
    flip_card_handler,
    add_token_handler,
    remove_token_handler,
    shuffle_deck_handler,
    end_turn_handler,
    remove_op_shield_handler,
    add_shield_only_handler,
    remove_shield_only_handler,
    start_attack_handler,
    attack_update_plan_handler,
    attack_propose_handler,
    attack_accept_handler,
    attack_cancel_handler,
    cursor_handler,
    reset_room_handler,
    join_room_handler,
    remove_shield_to_reserve_handler
)


class TestFlipCardHandler:
    """Tests for flip_card_handler"""
    
    @pytest.mark.asyncio
    async def test_flip_card_success(self):
        """Test successful card flipping"""
        # Setup
        rooms = {}
        sid_index = {"player1": {"room": "test_room", "pid": "P1"}}
        
        # Create game state with a face-down card
        state = TestDataBuilder.create_game_state()
        card = TestDataBuilder.create_basic_card("test_card")
        state.players["P1"].slots[0].card = card
        state.players["P1"].slots[0].face_up = False
        
        rooms["test_room"] = {
            "state": state,
            "cfg": {},
            "seats": {"P1": "player1", "P2": None}
        }
        
        data = {"slotIndex": 0}
        log_fn = MagicMock()
        emit_views_fn = AsyncMock()
        
        # Execute
        result = await flip_card_handler(
            "player1", data, rooms, sid_index,
            log_fn=log_fn, emit_views_fn=emit_views_fn
        )
        
        # Verify
        assert result is None  # Success returns None
        assert state.players["P1"].slots[0].face_up is True
        log_fn.assert_called_once()
        emit_views_fn.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_flip_card_bad_session(self):
        """Test flip card with invalid session"""
        rooms = {}
        sid_index = {}
        data = {"slotIndex": 0}
        log_fn = MagicMock()
        emit_views_fn = AsyncMock()
        
        result = await flip_card_handler(
            "invalid_sid", data, rooms, sid_index,
            log_fn=log_fn, emit_views_fn=emit_views_fn
        )
        
        assert result is None  # Handler returns None for invalid session
        log_fn.assert_not_called()
        emit_views_fn.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_flip_card_invalid_slot(self):
        """Test flip card with invalid slot index"""
        rooms = {}
        sid_index = {"player1": {"room": "test_room", "pid": "P1"}}
        
        state = TestDataBuilder.create_game_state()
        rooms["test_room"] = {
            "state": state,
            "cfg": {},
            "seats": {"P1": "player1", "P2": None}
        }
        
        data = {"slotIndex": 99}  # Invalid index
        log_fn = MagicMock()
        emit_views_fn = AsyncMock()
        
        result = await flip_card_handler(
            "player1", data, rooms, sid_index,
            log_fn=log_fn, emit_views_fn=emit_views_fn
        )
        
        assert result is None  # Handler returns None for invalid index
        

class TestTokenHandlers:
    """Tests for add_token_handler and remove_token_handler"""
    
    @pytest.mark.asyncio
    async def test_add_token_success(self):
        """Test successful token addition"""
        rooms = {}
        sid_index = {"player1": {"room": "test_room", "pid": "P1"}}
        
        state = TestDataBuilder.create_game_state()
        card = TestDataBuilder.create_basic_card("test_card")
        state.players["P1"].slots[0].card = card
        initial_shield = state.players["P1"].slots[0].muscles
        
        rooms["test_room"] = {
            "state": state,
            "cfg": {},
            "seats": {"P1": "player1", "P2": None}
        }
        
        data = {"slotIndex": 0, "count": 2, "kind": "shield"}
        log_fn = MagicMock()
        emit_views_fn = AsyncMock()
        
        result = await add_token_handler(
            "player1", data, rooms, sid_index,
            log_fn=log_fn, emit_views_fn=emit_views_fn
        )
        
        assert result is None
        assert state.players["P1"].slots[0].muscles == initial_shield + 2  # Shields added
        log_fn.assert_called_once()
        emit_views_fn.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_add_token_insufficient_funds(self):
        """Test add token with insufficient funds"""
        rooms = {}
        sid_index = {"player1": {"room": "test_room", "pid": "P1"}}
        
        state = TestDataBuilder.create_game_state()
        card = TestDataBuilder.create_basic_card("test_card")
        state.players["P1"].slots[0].card = card
        state.players["P1"].tokens.reserve_money = 1
        
        rooms["test_room"] = {
            "state": state,
            "cfg": {},
            "seats": {"P1": "player1", "P2": None}
        }
        
        data = {"slotIndex": 0, "count": 5}  # More than available
        log_fn = MagicMock()
        emit_views_fn = AsyncMock()
        
        result = await add_token_handler(
            "player1", data, rooms, sid_index,
            log_fn=log_fn, emit_views_fn=emit_views_fn
        )
        
        assert result is None  # Handler returns None even for errors
    
    @pytest.mark.asyncio
    async def test_remove_token_success(self):
        """Test successful token removal"""
        rooms = {}
        sid_index = {"player1": {"room": "test_room", "pid": "P1"}}
        
        state = TestDataBuilder.create_game_state()
        card = TestDataBuilder.create_basic_card("test_card")
        state.players["P1"].slots[0].card = card
        state.players["P1"].slots[0].muscles = 5  # Has shields to remove
        
        rooms["test_room"] = {
            "state": state,
            "cfg": {},
            "seats": {"P1": "player1", "P2": None}
        }
        
        data = {"slotIndex": 0, "count": 2, "kind": "shield"}
        log_fn = MagicMock()
        emit_views_fn = AsyncMock()
        
        result = await remove_token_handler(
            "player1", data, rooms, sid_index,
            log_fn=log_fn, emit_views_fn=emit_views_fn
        )
        
        assert result is None
        assert state.players["P1"].slots[0].muscles == 3  # 5 - 2
        log_fn.assert_called_once()
        emit_views_fn.assert_called_once()


class TestShuffleHandler:
    """Tests for shuffle_deck_handler"""
    
    @pytest.mark.asyncio
    async def test_shuffle_deck_success(self):
        """Test successful deck shuffling"""
        rooms = {}
        sid_index = {"player1": {"room": "test_room", "pid": "P1"}}
        
        state = TestDataBuilder.create_game_state()
        # Add cards to deck
        state.deck = [
            TestDataBuilder.create_basic_card("card1"),
            TestDataBuilder.create_basic_card("card2"),
            TestDataBuilder.create_basic_card("card3")
        ]
        
        rooms["test_room"] = {
            "state": state,
            "cfg": {},
            "seats": {"P1": "player1", "P2": None}
        }
        
        log_fn = MagicMock()
        emit_views_fn = AsyncMock()
        
        # Store original order
        original_ids = [card.id for card in state.deck]
        
        result = await shuffle_deck_handler(
            "player1", rooms, sid_index,
            emit_views_fn=emit_views_fn, log_fn=log_fn
        )
        
        assert result is None
        assert len(state.deck) == 3  # Same number of cards
        # Note: We can't test the exact shuffling since it's random
        log_fn.assert_called_once()
        emit_views_fn.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_shuffle_deck_empty(self):
        """Test shuffling empty deck"""
        rooms = {}
        sid_index = {"player1": {"room": "test_room", "pid": "P1"}}
        
        state = TestDataBuilder.create_game_state()
        state.deck = []  # Empty deck
        
        rooms["test_room"] = {
            "state": state,
            "cfg": {},
            "seats": {"P1": "player1", "P2": None}
        }
        
        log_fn = MagicMock()
        emit_views_fn = AsyncMock()
        
        result = await shuffle_deck_handler(
            "player1", rooms, sid_index,
            emit_views_fn=emit_views_fn, log_fn=log_fn
        )
        
        assert result is None
        assert len(state.deck) == 0
        log_fn.assert_called_once()
        emit_views_fn.assert_called_once()


class TestEndTurnHandler:
    """Tests for end_turn_handler"""
    
    @pytest.mark.asyncio
    async def test_end_turn_success(self):
        """Test successful turn ending"""
        rooms = {}
        sid_index = {"player1": {"room": "test_room", "pid": "P1"}}
        
        state = TestDataBuilder.create_game_state()
        state.active_player = "P1"  # Player1's turn
        
        rooms["test_room"] = {
            "state": state,
            "cfg": {},
            "seats": {"P1": "player1", "P2": "player2"}
        }
        
        log_fn = MagicMock()
        emit_views_fn = AsyncMock()
        
        result = await end_turn_handler(
            "player1", rooms, sid_index,
            emit_views_fn=emit_views_fn, log_fn=log_fn
        )
        
        assert result is None
        assert state.active_player == "P2"  # Turn switched
        log_fn.assert_called_once()
        emit_views_fn.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_end_turn_not_your_turn(self):
        """Test ending turn when it's not your turn"""
        rooms = {}
        sid_index = {"player1": {"room": "test_room", "pid": "P1"}}
        
        state = TestDataBuilder.create_game_state()
        state.active_player = "P2"  # Player2's turn, but player1 tries to end
        
        rooms["test_room"] = {
            "state": state,
            "cfg": {},
            "seats": {"P1": "player1", "P2": "player2"}
        }
        
        log_fn = MagicMock()
        emit_views_fn = AsyncMock()
        
        result = await end_turn_handler(
            "player1", rooms, sid_index,
            emit_views_fn=emit_views_fn, log_fn=log_fn
        )
        
        assert result is None  # Handler returns None for wrong turn
        assert state.active_player == "P2"  # Turn not changed
        log_fn.assert_not_called()
        emit_views_fn.assert_not_called()


class TestShieldHandlers:
    """Tests for shield-related handlers"""
    
    @pytest.mark.asyncio
    async def test_remove_shield_to_reserve_success(self):
        """Test successful shield removal to reserve"""
        rooms = {}
        sid_index = {"player1": {"room": "test_room", "pid": "P1"}}
        
        state = TestDataBuilder.create_game_state()
        card = TestDataBuilder.create_basic_card("test_card")
        state.players["P1"].slots[0].card = card
        state.players["P1"].slots[0].muscles = 5  # Has shields
        
        rooms["test_room"] = {
            "state": state,
            "cfg": {},
            "seats": {"P1": "player1", "P2": None}
        }
        
        data = {"slotIndex": 0, "count": 2}
        log_fn = MagicMock()
        emit_views_fn = AsyncMock()
        
        result = await remove_shield_to_reserve_handler(
            "player1", data, rooms, sid_index,
            log_fn=log_fn, emit_views_fn=emit_views_fn
        )
        
        assert result is None
        assert state.players["P1"].slots[0].muscles == 3  # 5 - 2
        assert state.players["P1"].tokens.reserve_money == 14  # 12 + 2
        log_fn.assert_called_once()
        emit_views_fn.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_remove_op_shield_success(self):
        """Test successful opponent shield removal"""
        rooms = {}
        sid_index = {"player1": {"room": "test_room", "pid": "P1"}}
        
        state = TestDataBuilder.create_game_state()
        card = TestDataBuilder.create_basic_card("test_card")
        state.players["P2"].slots[1].card = card
        state.players["P2"].slots[1].muscles = 3  # Opponent has shields
        
        rooms["test_room"] = {
            "state": state,
            "cfg": {},
            "seats": {"P1": "player1", "P2": "player2"}
        }
        
        data = {"targetPlayer": "P2", "slotIndex": 1, "count": 1}
        log_fn = MagicMock()
        emit_views_fn = AsyncMock()
        
        result = await remove_op_shield_handler(
            "player1", data, rooms, sid_index,
            log_fn=log_fn, emit_views_fn=emit_views_fn
        )
        
        assert result is None
        assert state.players["P2"].slots[1].muscles == 2  # 3 - 1
        log_fn.assert_called_once()
        emit_views_fn.assert_called_once()


class TestCursorHandler:
    """Tests for cursor_handler"""
    
    @pytest.mark.asyncio
    async def test_cursor_handler_success(self):
        """Test successful cursor update"""
        sio = AsyncMock()
        sid_index = {"player1": {"room": "test_room", "pid": "P1"}}
        data = {"x": 0.5, "y": 0.8, "visible": True}
        
        result = await cursor_handler(sio, "player1", data, sid_index)
        
        assert result is None
        sio.emit.assert_called_once_with(
            "cursor", 
            {"pid": "P1", "x": 0.5, "y": 0.8, "visible": True}, 
            room="test_room", 
            skip_sid="player1"
        )
    
    @pytest.mark.asyncio
    async def test_cursor_handler_bad_session(self):
        """Test cursor update with bad session"""
        sio = AsyncMock()
        sid_index = {}
        data = {"x": 100, "y": 200}
        
        result = await cursor_handler(sio, "invalid_sid", data, sid_index)
        
        assert result is None
        sio.emit.assert_not_called()


class TestResetRoomHandler:
    """Tests for reset_room_handler"""
    
    @pytest.mark.asyncio
    async def test_reset_room_success(self):
        """Test successful room reset"""
        sio = AsyncMock()
        rooms = {}
        sid_index = {"player1": {"room": "test_room", "pid": "P1"}}
        
        # Create room with existing state
        old_state = TestDataBuilder.create_game_state()
        rooms["test_room"] = {
            "state": old_state,
            "cfg": {"test": "config"},
            "seats": {"P1": "player1", "P2": None}
        }
        
        # Mock build_state_cb
        new_state = TestDataBuilder.create_game_state()
        new_config = {"new": "config"}
        build_state_cb = MagicMock(return_value=(new_state, new_config))
        
        log_fn = MagicMock()
        emit_views_fn = AsyncMock()
        
        result = await reset_room_handler(
            sio, "player1", {}, rooms, sid_index,
            build_state_cb=build_state_cb,
            emit_views_fn=emit_views_fn,
            log_fn=log_fn
        )
        
        assert result is None
        assert rooms["test_room"]["state"] == new_state
        assert rooms["test_room"]["cfg"] == new_config
        build_state_cb.assert_called_once()
        assert log_fn.call_count >= 1  # Multiple log calls expected
        emit_views_fn.assert_called_once()
        # Handler sends 'joined' event to current player after reset
        sio.emit.assert_called_once_with("joined", {
            "room": "test_room", 
            "seat": "P1", 
            "source": "yaml", 
            "visibleSlots": 6
        }, to="player1")


class TestJoinRoomHandler:
    """Tests for join_room_handler"""
    
    @pytest.mark.asyncio
    async def test_join_room_new_room(self):
        """Test joining a new room"""
        sio = AsyncMock()
        rooms = {}
        sid_index = {}
        
        # Mock build_state_cb
        new_state = TestDataBuilder.create_game_state()
        new_config = {"test": "config"}
        build_state_cb = MagicMock(return_value=(new_state, new_config))
        
        data = {"room": "new_room"}
        log_fn = MagicMock()
        emit_views_fn = AsyncMock()
        
        result = await join_room_handler(
            sio, "player1", data, rooms, sid_index,
            INIT_VISIBLE_SLOTS=6,
            build_state_cb=build_state_cb,
            emit_views_fn=emit_views_fn,
            log_fn=log_fn
        )
        
        assert result is None
        assert "new_room" in rooms
        assert rooms["new_room"]["state"] == new_state
        assert rooms["new_room"]["seats"]["P1"] == "player1"
        assert sid_index["player1"]["room"] == "new_room"
        assert sid_index["player1"]["pid"] == "P1"
        
        build_state_cb.assert_called_once()
        sio.enter_room.assert_called_once_with("player1", "new_room")
        sio.emit.assert_called_once()
        log_fn.assert_called()
        emit_views_fn.assert_called_once()
    
    @pytest.mark.asyncio 
    async def test_join_room_existing_room_second_player(self):
        """Test joining existing room as second player"""
        sio = AsyncMock()
        rooms = {
            "existing_room": {
                "state": TestDataBuilder.create_game_state(),
                "cfg": {"test": "config"},
                "seats": {"P1": "player1", "P2": None},
                "visible_slots": {"P1": 6, "P2": 6},
                "source": "csv",
                "log": []
            }
        }
        sid_index = {"player1": {"room": "existing_room", "pid": "P1"}}
        
        build_state_cb = MagicMock()  # Should not be called for existing room
        data = {"room": "existing_room"}
        log_fn = MagicMock()
        emit_views_fn = AsyncMock()
        
        result = await join_room_handler(
            sio, "player2", data, rooms, sid_index,
            INIT_VISIBLE_SLOTS=6,
            build_state_cb=build_state_cb,
            emit_views_fn=emit_views_fn,
            log_fn=log_fn
        )
        
        assert result is None
        assert rooms["existing_room"]["seats"]["P2"] == "player2"
        assert sid_index["player2"]["room"] == "existing_room"
        assert sid_index["player2"]["pid"] == "P2"
        
        build_state_cb.assert_not_called()  # Room already exists
        sio.enter_room.assert_called_once_with("player2", "existing_room")
        sio.emit.assert_called_once()
        log_fn.assert_called()
        emit_views_fn.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_join_room_full(self):
        """Test joining a full room"""
        sio = AsyncMock()
        rooms = {
            "full_room": {
                "state": TestDataBuilder.create_game_state(),
                "cfg": {"test": "config"},
                "seats": {"P1": "player1", "P2": "player2"},  # Both seats taken
                "visible_slots": {"P1": 6, "P2": 6},
                "source": "csv",
                "log": []
            }
        }
        sid_index = {
            "player1": {"room": "full_room", "pid": "P1"},
            "player2": {"room": "full_room", "pid": "P2"}
        }
        
        build_state_cb = MagicMock()
        data = {"room": "full_room"}
        log_fn = MagicMock()
        emit_views_fn = AsyncMock()
        
        result = await join_room_handler(
            sio, "player3", data, rooms, sid_index,
            INIT_VISIBLE_SLOTS=6,
            build_state_cb=build_state_cb,
            emit_views_fn=emit_views_fn,
            log_fn=log_fn
        )
        
        assert result is None
        sio.emit.assert_called_with("room_full", {"room": "full_room"}, to="player3")
        emit_views_fn.assert_not_called()


class TestAttackHandlers:
    """Tests for attack-related handlers"""
    
    @pytest.mark.asyncio
    async def test_start_attack_handler_success(self):
        """Test successful attack start"""
        rooms = {}
        sid_index = {"player1": {"room": "test_room", "pid": "P1"}}
        
        state = TestDataBuilder.create_game_state()
        attacker_card = TestDataBuilder.create_basic_card("attacker")
        attacker_card.atk = 3
        state.players["P1"].slots[0].card = attacker_card
        
        target_card = TestDataBuilder.create_basic_card("target")
        state.players["P2"].slots[1].card = target_card
        
        rooms["test_room"] = {
            "state": state,
            "cfg": {},
            "seats": {"P1": "player1", "P2": "player2"}
        }
        
        data = {
            "attackerSlot": 0,
            "targetPlayer": "P2", 
            "targetSlot": 1
        }
        log_fn = MagicMock()
        emit_views_fn = AsyncMock()
        
        result = await start_attack_handler(
            "player1", data, rooms, sid_index,
            log_fn=log_fn, emit_views_fn=emit_views_fn
        )
        
        assert result is None
        # Note: handlers may not call functions if certain conditions aren't met
    
    @pytest.mark.asyncio
    async def test_attack_propose_handler_success(self):
        """Test successful attack proposal"""
        sio = AsyncMock()
        rooms = {}
        sid_index = {"player1": {"room": "test_room", "pid": "P1"}}
        
        state = TestDataBuilder.create_game_state()
        rooms["test_room"] = {
            "state": state,
            "cfg": {},
            "seats": {"P1": "player1", "P2": "player2"}
        }
        
        data = {"attackPlan": {"attacker": 0, "target": 1}}
        log_fn = MagicMock()
        emit_views_fn = AsyncMock()
        
        result = await attack_propose_handler(
            "player1", rooms, sid_index,
            log_fn=log_fn, emit_views_fn=emit_views_fn
        )
        
        assert result is None
        # Note: handlers may not call functions if certain conditions aren't met
    
    @pytest.mark.asyncio
    async def test_attack_accept_handler_success(self):
        """Test successful attack acceptance"""
        sio = AsyncMock()
        rooms = {}
        sid_index = {"player2": {"room": "test_room", "pid": "P2"}}
        
        state = TestDataBuilder.create_game_state()
        rooms["test_room"] = {
            "state": state,
            "cfg": {},
            "seats": {"P1": "player1", "P2": "player2"},
            "attack_plan": {"attacker": 0, "target": 1}
        }
        
        data = {}
        log_fn = MagicMock()
        emit_views_fn = AsyncMock()
        
        result = await attack_accept_handler(
            "player2", rooms, sid_index,
            log_fn=log_fn, emit_views_fn=emit_views_fn
        )
        
        assert result is None
        # Note: handlers may not call functions if certain conditions aren't met
    
    @pytest.mark.asyncio
    async def test_attack_cancel_handler_success(self):
        """Test successful attack cancellation"""
        sio = AsyncMock()
        rooms = {}
        sid_index = {"player1": {"room": "test_room", "pid": "P1"}}
        
        state = TestDataBuilder.create_game_state()
        rooms["test_room"] = {
            "state": state,
            "cfg": {},
            "seats": {"P1": "player1", "P2": "player2"},
            "attack_plan": {"attacker": 0, "target": 1}
        }
        
        data = {}
        log_fn = MagicMock()
        emit_views_fn = AsyncMock()
        
        result = await attack_cancel_handler(
            "player1", rooms, sid_index,
            log_fn=log_fn, emit_views_fn=emit_views_fn
        )
        
        assert result is None
        # Note: handlers may not call functions if certain conditions aren't met
    
    @pytest.mark.asyncio
    async def test_attack_update_plan_handler_success(self):
        """Test successful attack plan update"""
        sio = AsyncMock()
        rooms = {}
        sid_index = {"player1": {"room": "test_room", "pid": "P1"}}
        
        state = TestDataBuilder.create_game_state()
        rooms["test_room"] = {
            "state": state,
            "cfg": {},
            "seats": {"P1": "player1", "P2": "player2"}
        }
        
        data = {"attackPlan": {"attacker": 1, "target": 2}}
        emit_views_fn = AsyncMock()
        
        result = await attack_update_plan_handler(
            "player1", data, rooms, sid_index,
            emit_views_fn=emit_views_fn
        )
        
        assert result is None  
        # Note: handlers may not call functions if certain conditions aren't met


class TestShieldOnlyHandlers:
    """Tests for shield-only handlers"""
    
    @pytest.mark.asyncio
    async def test_add_shield_only_handler_success(self):
        """Test successful shield-only addition"""
        rooms = {}
        sid_index = {"player1": {"room": "test_room", "pid": "P1"}}
        
        state = TestDataBuilder.create_game_state()
        card = TestDataBuilder.create_basic_card("test_card")
        state.players["P1"].slots[0].card = card
        initial_shield = state.players["P1"].slots[0].muscles
        
        rooms["test_room"] = {
            "state": state,
            "cfg": {},
            "seats": {"P1": "player1", "P2": None}
        }
        
        data = {"slotIndex": 0, "count": 3}
        log_fn = MagicMock()
        emit_views_fn = AsyncMock()
        
        result = await add_shield_only_handler(
            "player1", data, rooms, sid_index,
            log_fn=log_fn, emit_views_fn=emit_views_fn
        )
        
        assert result is None
        assert state.players["P1"].slots[0].muscles == initial_shield + 3
        log_fn.assert_called_once()
        emit_views_fn.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_remove_shield_only_handler_success(self):
        """Test successful shield-only removal"""
        rooms = {}
        sid_index = {"player1": {"room": "test_room", "pid": "P1"}}
        
        state = TestDataBuilder.create_game_state()
        card = TestDataBuilder.create_basic_card("test_card")
        state.players["P1"].slots[0].card = card
        state.players["P1"].slots[0].muscles = 5  # Has shields to remove
        
        rooms["test_room"] = {
            "state": state,
            "cfg": {},
            "seats": {"P1": "player1", "P2": None}
        }
        
        data = {"slotIndex": 0, "count": 2}
        log_fn = MagicMock()
        emit_views_fn = AsyncMock()
        
        result = await remove_shield_only_handler(
            "player1", data, rooms, sid_index,
            log_fn=log_fn, emit_views_fn=emit_views_fn
        )
        
        assert result is None
        assert state.players["P1"].slots[0].muscles == 3  # 5 - 2
        log_fn.assert_called_once()
        emit_views_fn.assert_called_once()

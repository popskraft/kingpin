"""
Дополнительные тесты для server/services/setup.py для повышения покрытия:
- _is_boss_card, _guess_owner_from_text
- _ensure_slots, _place_starters, _ensure_bosses_in_hands
"""

import pytest
from unittest.mock import patch

from packages.server.services import setup as srv_setup
from packages.engine.models import GameState, PlayerState, Card, Slot
from tests.test_helpers import TestDataBuilder


class TestSetupHelpers:
    def test_is_boss_card_matches_english_and_russian(self):
        c1 = Card(id="b1", name="Some Boss", notes="", type="boss")
        c2 = Card(id="b2", name="Random", notes="Босс мафии")
        c3 = Card(id="n1", name="Regular", notes="", type="common")
        assert srv_setup._is_boss_card(c1) is True
        assert srv_setup._is_boss_card(c2) is True
        assert srv_setup._is_boss_card(c3) is False

    @pytest.mark.parametrize(
        "text,owner",
        [
            ("Attack P1 only", "P1"),
            ("Protect p2 slot", "P2"),
            ("для П1 особый эффект", "P1"),
            ("рандомный текст", None),
        ],
    )
    def test_guess_owner_from_text(self, text, owner):
        assert srv_setup._guess_owner_from_text(text) == owner

    def test_ensure_slots_expands_to_required_count(self):
        st = TestDataBuilder.create_game_state()
        # Уменьшим количество слотов у P1
        st.players["P1"].slots = [Slot() for _ in range(2)]
        # Удалим P2, чтобы проверить пересоздание
        del st.players["P2"]
        srv_setup._ensure_slots(st, 6)
        assert len(st.players["P1"].slots) == 6
        assert len(st.players["P2"].slots) == 6

    def test_place_starters_supports_str_and_dict_entries(self):
        st = TestDataBuilder.create_game_state()
        # базовые данные карт в индексе
        cards_index = {
            "boss_gangster": {"id": "boss_gangster", "name": "Gangster Boss", "type": "boss"},
            "boss_authority": {"id": "boss_authority", "name": "Authority Boss", "type": "boss"},
        }
        cfg = {
            "starters": {
                "P1": ["boss_gangster", {"id": "boss_authority", "name": "Overridden Name"}],
                "P2": [
                    {"id": "unknown", "name": "Direct Card"},  # не в индексе — использовать как есть
                ],
            }
        }
        with patch("packages.server.services.setup._load_cards_index", return_value=cards_index):
            srv_setup._place_starters(st, cfg)
        # Проверяем, что P1 получил 2 карты из стартовых (строка + словарь-оверрайд)
        assert [c.id for c in st.players["P1"].hand] == ["boss_gangster", "boss_authority"]
        assert st.players["P1"].hand[1].name == "Overridden Name"
        # P2 получил прямую карту
        assert st.players["P2"].hand and st.players["P2"].hand[0].id == "unknown"

    def test_ensure_bosses_in_hands_moves_from_deck(self):
        # Подготовим стейт: боссы лежат в колоде
        st = GameState(players={
            "P1": PlayerState(id="P1", hand_limit=6),
            "P2": PlayerState(id="P2", hand_limit=6),
        })
        # Босс с указанием владельца (в notes)
        boss_p1 = Card(id="b_p1", name="Boss Alpha", notes="for P1 only", type="boss")
        boss_any = Card(id="b_any", name="Just Boss", type="boss")
        st.deck = [boss_p1, boss_any]
        # До вызова у игроков нет боссов на руках
        assert not any(srv_setup._is_boss_card(c) for c in st.players["P1"].hand)
        assert not any(srv_setup._is_boss_card(c) for c in st.players["P2"].hand)
        srv_setup._ensure_bosses_in_hands(st)
        # После вызова P1 получает своего босса, P2 — любого оставшегося
        assert any(c.id == "b_p1" for c in st.players["P1"].hand)
        assert any(c.id == "b_any" for c in st.players["P2"].hand)


"""
Unit-тесты для загрузчика engine/loader.py
"""

import pytest
import tempfile
import csv
import yaml
from pathlib import Path
from packages.engine.loader import (
    load_yaml_config, load_cards_from_csv, _parse_abl_text,
    build_state_from_config, load_game
)
from packages.engine.models import Card, CardType, GameState, GameConfig
from tests.test_helpers import TestDataBuilder


class TestYamlConfigLoader:
    """Тесты загрузки YAML конфигурации"""
    
    def test_load_yaml_config_basic(self):
        """Тест загрузки базовой YAML конфигурации"""
        config_data = {
            "rules": {
                "hand_enabled": True,
                "ammo_max_bonus": 3
            },
            "hand_limit": 7,
            "starters": {
                "P1": ["boss_gangster"],
                "P2": ["boss_authority"]
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            temp_path = f.name
        
        try:
            loaded_config = load_yaml_config(temp_path)
            
            assert loaded_config["rules"]["hand_enabled"] is True
            assert loaded_config["rules"]["ammo_max_bonus"] == 3
            assert loaded_config["hand_limit"] == 7
            assert loaded_config["starters"]["P1"] == ["boss_gangster"]
        finally:
            Path(temp_path).unlink()
    
    def test_load_yaml_config_removes_cards(self):
        """Тест что cards удаляются из конфигурации"""
        config_data = {
            "rules": {"hand_enabled": True},
            "cards": [  # это должно быть удалено
                {"id": "card1", "name": "Card 1"},
                {"id": "card2", "name": "Card 2"}
            ]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            temp_path = f.name
        
        try:
            loaded_config = load_yaml_config(temp_path)
            
            assert "rules" in loaded_config
            assert "cards" not in loaded_config  # должно быть удалено
        finally:
            Path(temp_path).unlink()


class TestCsvCardLoader:
    """Тесты загрузки карт из CSV"""
    
    def create_test_csv(self, cards_data):
        """Создать временный CSV файл с данными карт"""
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, newline='')
        
        if cards_data:
            fieldnames = cards_data[0].keys()
            writer = csv.DictWriter(temp_file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(cards_data)
        
        temp_file.close()
        return temp_file.name
    
    def test_load_cards_basic(self):
        """Тест загрузки базовых карт"""
        cards_data = [
            {
                "ID": "test_card_1",
                "Name": "Test Card 1",
                "Type": "common",
                "Faction": "gangsters",
                "HP": "3",
                "ATK": "2",
                "Defend": "1",
                "Price": "2",
                "Corruption": "1",
                "InDeck": "✓"
            },
            {
                "ID": "test_card_2",
                "Name": "Test Card 2",
                "Type": "boss",
                "Faction": "authorities",
                "HP": "10",
                "ATK": "2",
                "Defend": "3",
                "Price": "0",
                "Corruption": "12",
                "InDeck": "✓"
            }
        ]
        
        csv_path = self.create_test_csv(cards_data)
        
        try:
            cards = load_cards_from_csv(csv_path)
            
            assert len(cards) == 2
            
            # Проверим первую карту
            card1 = cards[0]
            assert card1.id == "test_card_1"
            assert card1.name == "Test Card 1"
            assert card1.type == CardType.common
            assert card1.faction == "gangsters"
            assert card1.hp == 3
            assert card1.atk == 2
            assert card1.d == 1
            assert card1.price == 2
            assert card1.corruption == 1
            
            # Проверим вторую карту
            card2 = cards[1]
            assert card2.id == "test_card_2"
            assert card2.type == CardType.boss
            assert card2.faction == "authorities"
            assert card2.hp == 10
            
        finally:
            Path(csv_path).unlink()
    
    def test_load_cards_with_abilities(self):
        """Тест загрузки карт со способностями"""
        cards_data = [
            {
                "ID": "ability_card",
                "Name": "Ability Card",
                "Type": "common",
                "HP": "3",
                "ATK": "1",
                "Defend": "1",
                "ABL": "authority:2; steal:1",
                "InDeck": "✓"
            }
        ]
        
        csv_path = self.create_test_csv(cards_data)
        
        try:
            cards = load_cards_from_csv(csv_path)
            
            assert len(cards) == 1
            card = cards[0]
            
            assert isinstance(card.abl, dict)
            assert card.abl["authority"] == 2
            assert card.abl["on_enter"]["steal"] == 1
            
        finally:
            Path(csv_path).unlink()
    
    def test_load_cards_indeck_filtering(self):
        """Тест фильтрации карт по InDeck"""
        cards_data = [
            {
                "ID": "in_deck_card",
                "Name": "In Deck Card",
                "InDeck": "✓"
            },
            {
                "ID": "not_in_deck_card",
                "Name": "Not In Deck Card",
                "InDeck": "✗"
            },
            {
                "ID": "yes_card",
                "Name": "Yes Card",
                "InDeck": "yes"
            },
            {
                "ID": "no_card",
                "Name": "No Card",
                "InDeck": "no"
            }
        ]
        
        csv_path = self.create_test_csv(cards_data)
        
        try:
            # Загрузить только карты в колоде
            deck_cards = load_cards_from_csv(csv_path, include_all=False)
            assert len(deck_cards) == 2  # только ✓ и yes
            assert {card.id for card in deck_cards} == {"in_deck_card", "yes_card"}
            
            # Загрузить все карты
            all_cards = load_cards_from_csv(csv_path, include_all=True)
            assert len(all_cards) == 4
            
        finally:
            Path(csv_path).unlink()
    
    def test_load_cards_with_clan(self):
        """Тест загрузки карт с полем clan"""
        cards_data = [
            {
                "ID": "clan_card",
                "Name": "Clan Card",
                "Clan": "warriors",
                "InDeck": "✓"
            },
            
        ]
        
        csv_path = self.create_test_csv(cards_data)
        
        try:
            cards = load_cards_from_csv(csv_path)
            
            assert len(cards) == 1
            
            clan_card = next(c for c in cards if c.id == "clan_card")
            assert clan_card.clan == "warriors"
            
        finally:
            Path(csv_path).unlink()
    
    def test_load_cards_numeric_parsing(self):
        """Тест парсинга числовых значений"""
        cards_data = [
            {
                "ID": "numeric_card",
                "Name": "Numeric Card",
                "HP": "3.5",  # float
                "ATK": "n/a",  # специальное значение
                "Defend": "",  # пустое
                "Price": "2",  # обычное число
                "InDeck": "✓"
            }
        ]
        
        csv_path = self.create_test_csv(cards_data)
        
        try:
            cards = load_cards_from_csv(csv_path)
            
            card = cards[0]
            assert card.hp == 3  # float округлён до int
            assert card.atk == 0  # n/a -> default
            assert card.d == 0    # пустое -> default
            assert card.price == 2  # нормально распарсилось
            
        finally:
            Path(csv_path).unlink()
    
    def test_load_cards_pair_synergy_fields(self):
        """Тест загрузки полей парной синергии"""
        cards_data = [
            {
                "ID": "pair_card",
                "Name": "Pair Card",
                "PairHP": "2",
                "PairD": "1",
                "PairR": "1",
                "InDeck": "✓"
            }
        ]
        
        csv_path = self.create_test_csv(cards_data)
        
        try:
            cards = load_cards_from_csv(csv_path)
            
            card = cards[0]
            assert card.pair_hp == 2
            assert card.pair_d == 1
            assert card.pair_r == 1
            
        finally:
            Path(csv_path).unlink()


class TestAblTextParser:
    """Тесты парсера ABL текста"""
    
    def test_parse_empty_abl(self):
        """Тест парсинга пустого ABL"""
        assert _parse_abl_text("") == 0
        assert _parse_abl_text(None) == 0
        assert _parse_abl_text("   ") == 0
    
    def test_parse_simple_abilities(self):
        """Тест парсинга простых способностей"""
        result = _parse_abl_text("authority:2; steal:1; hack:3")
        
        assert isinstance(result, dict)
        assert result["authority"] == 2
        assert result["on_enter"]["steal"] == 1
        assert result["hack"] == 3
    
    def test_parse_on_enter_abilities(self):
        """Тест парсинга способностей on_enter"""
        result = _parse_abl_text("steal:2; gain:3; bribe:1")
        
        assert isinstance(result, dict)
        assert "on_enter" in result
        assert result["on_enter"]["steal"] == 2
        assert result["on_enter"]["gain"] == 3
        assert result["on_enter"]["bribe"] == 1
    
    def test_parse_mixed_abilities(self):
        """Тест парсинга смешанных способностей"""
        result = _parse_abl_text("authority:1; steal:2; extra_defense:1")
        
        assert isinstance(result, dict)
        assert result["authority"] == 1
        assert result["extra_defense"] == 1
        assert "on_enter" in result
        assert result["on_enter"]["steal"] == 2
    
    def test_parse_boolean_flags(self):
        """Тест парсинга булевых флагов"""
        result = _parse_abl_text("unbribable; stealth")
        
        assert isinstance(result, dict)
        assert result["unbribable"] == 1
        assert result["stealth"] == 1
    
    def test_parse_special_values(self):
        """Тест парсинга специальных значений"""
        result = _parse_abl_text("anti_corruption:all; disabled:n/a")
        
        assert isinstance(result, dict)
        assert result["anti_corruption"] == "all"
        assert result["disabled"] == "n/a"
    
    def test_parse_comma_and_semicolon_separators(self):
        """Тест парсинга с разными разделителями"""
        result1 = _parse_abl_text("authority:2, steal:1")
        result2 = _parse_abl_text("authority:2; steal:1")
        
        # Оба должны дать одинаковый результат
        assert result1 == result2
        assert result1["authority"] == 2
        assert result1["on_enter"]["steal"] == 1


class TestStateBuilder:
    """Тесты построения игрового состояния"""
    
    def test_build_state_basic(self):
        """Тест базового построения состояния"""
        config_data = {
            "rules": {
                "hand_enabled": True,
                "ammo_max_bonus": 3
            },
            "hand_limit": 7
        }
        
        cards = [
            Card(id="card1", name="Card 1"),
            Card(id="card2", name="Card 2")
        ]
        
        state = build_state_from_config(config_data, cards)
        
        assert isinstance(state, GameState)
        assert isinstance(state.config, GameConfig)
        assert state.config.hand_enabled is True
        assert state.config.ammo_max_bonus == 3
        
        # Проверим игроков
        assert "P1" in state.players
        assert "P2" in state.players
        assert state.players["P1"].hand_limit == 7
        assert state.players["P2"].hand_limit == 7
    
    def test_build_state_default_config(self):
        """Тест построения состояния с конфигурацией по умолчанию"""
        config_data = {}  # пустая конфигурация
        cards = []
        
        state = build_state_from_config(config_data, cards)
        
        # Должны применяться значения по умолчанию
        assert state.config.hand_enabled is False  # default
        assert state.config.ammo_max_bonus == 2   # default
        assert state.players["P1"].hand_limit == 0  # default из config_data


class TestGameLoader:
    """Тесты основного загрузчика игры"""
    
    def test_load_game_basic(self):
        """Тест базовой загрузки игры"""
        # Создадим временные файлы
        config_data = {
            "rules": {"hand_enabled": True},
            "hand_limit": 6
        }
        
        cards_data = [
            {
                "ID": "test_card",
                "Name": "Test Card",
                "HP": "3",
                "ATK": "2",
                "InDeck": "✓"
            }
        ]
        
        # YAML файл
        yaml_file = tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False)
        yaml.dump(config_data, yaml_file)
        yaml_file.close()
        
        # CSV файл
        csv_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, newline='')
        fieldnames = cards_data[0].keys()
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(cards_data)
        csv_file.close()
        
        try:
            state, config = load_game(yaml_file.name, csv_file.name)
            
            assert isinstance(state, GameState)
            assert isinstance(config, dict)
            
            # Проверим конфигурацию
            assert config["rules"]["hand_enabled"] is True
            assert config["hand_limit"] == 6
            
            # Проверим состояние
            assert state.config.hand_enabled is True
            assert state.players["P1"].hand_limit == 6
            
            # Проверим карты
            # Первые 10 карт должны быть на полке, остальные в колоде
            total_cards = len(state.shelf) + len(state.deck)
            assert total_cards == 1  # одна карта из CSV
            
        finally:
            Path(yaml_file.name).unlink()
            Path(csv_file.name).unlink()
    
    def test_load_game_default_csv_path(self):
        """Тест загрузки с автоматическим путём к CSV"""
        config_data = {"rules": {"hand_enabled": True}}
        
        # Создадим временную директорию
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # YAML файл
            yaml_path = temp_path / "config.yaml"
            with open(yaml_path, 'w') as f:
                yaml.dump(config_data, f)
            
            # CSV файл рядом с YAML
            csv_path = temp_path / "cards.csv"
            with open(csv_path, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=["ID", "Name", "InDeck"])
                writer.writeheader()
                writer.writerow({"ID": "auto_card", "Name": "Auto Card", "InDeck": "✓"})
            
            state, config = load_game(yaml_path)  # без указания CSV пути
            
            # Должна загрузиться карта из автоматически найденного CSV
            total_cards = len(state.shelf) + len(state.deck)
            assert total_cards == 1
    
    def test_load_game_missing_csv(self):
        """Тест загрузки при отсутствующем CSV файле"""
        config_data = {"rules": {"hand_enabled": True}}
        
        yaml_file = tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False)
        yaml.dump(config_data, yaml_file)
        yaml_file.close()
        
        try:
            # Указываем несуществующий CSV путь
            fake_csv_path = "/nonexistent/path/cards.csv"
            
            state, config = load_game(yaml_file.name, fake_csv_path)
            
            # Игра должна загрузиться без карт
            assert isinstance(state, GameState)
            assert len(state.deck) == 0
            assert len(state.shelf) == 0
            
        finally:
            Path(yaml_file.name).unlink()
    
    def test_load_game_card_distribution(self):
        """Тест распределения карт между колодой и полкой"""
        config_data = {"rules": {"hand_enabled": True}}
        
        # Создадим много карт для тестирования распределения
        cards_data = []
        for i in range(15):  # больше чем 10 (размер полки)
            cards_data.append({
                "ID": f"card_{i}",
                "Name": f"Card {i}",
                "InDeck": "✓"
            })
        
        yaml_file = tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False)
        yaml.dump(config_data, yaml_file)
        yaml_file.close()
        
        csv_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, newline='')
        fieldnames = cards_data[0].keys()
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(cards_data)
        csv_file.close()
        
        try:
            state, config = load_game(yaml_file.name, csv_file.name)
            
            # Первые 10 карт должны быть на полке
            assert len(state.shelf) == 10
            
            # Остальные 5 карт в колоде
            assert len(state.deck) == 5
            
            # Общее количество карт
            total_cards = len(state.shelf) + len(state.deck)
            assert total_cards == 15
            
        finally:
            Path(yaml_file.name).unlink()
            Path(csv_file.name).unlink()

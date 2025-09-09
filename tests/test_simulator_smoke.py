"""
Лёгкие smoke-тесты для пакета simulator, чтобы включить его в покрытие и
проверить основные сценарии без длительного прогона.
"""

import pytest

from packages.simulator.cli import _place_starters
from packages.simulator.game_simulator import GameSimulator
from packages.engine.loader import load_game


def test_cli_place_starters_places_cards_from_cfg():
    # Загружаем состояние из стандартного YAML/CSV
    state, cfg = load_game("config/default.yaml")
    # Имитируем простые стартовые карточные данные с минимальными полями
    starters_cfg = {
        "starters": {
            "P1": [{"id": "s1", "name": "Starter 1"}],
            "P2": [{"id": "s2", "name": "Starter 2"}],
        }
    }
    _place_starters(state, starters_cfg)
    # В CLI стартеры кладутся на поле (в слоты), а не в руку
    assert state.players["P1"].slots[0].card is not None
    assert state.players["P1"].slots[0].card.id == "s1"
    assert state.players["P2"].slots[0].card is not None
    assert state.players["P2"].slots[0].card.id == "s2"


def test_game_simulator_minimal_flow():
    # Используем реальный CSV из config/cards.csv
    sim = GameSimulator("config/cards.csv")
    # Создание колоды конкретного клана и одиночная игра
    deck = sim.create_deck("gangsters", deck_size=4)
    # Должны получить список GameCard, пусть даже пустой при отсутствии клана
    assert isinstance(deck, list)

    # Избегаем тяжёлых путей боя, ограничимся проверками сборки данных
    # и отчёта, не вызывая simulate_game/run_matchup_simulation
    # Генерация отчёта по синтетическим данным (без тяжёлых расчётов)
    report = sim.generate_simulation_report({
        "tournament_results": {},
        "clan_statistics": {
            "gangsters": {"win_rate": 50.0, "wins": 1, "losses": 1, "draws": 0, "games": 2},
            "authorities": {"win_rate": 50.0, "wins": 1, "losses": 1, "draws": 0, "games": 2},
            "loners": {"win_rate": 0.0, "wins": 0, "losses": 0, "draws": 0, "games": 0},
            "solo": {"win_rate": 0.0, "wins": 0, "losses": 0, "draws": 0, "games": 0},
        },
        "games_per_matchup": 1,
        "total_games": 0,
    })
    assert isinstance(report, str) and "ОТЧЕТ" in report

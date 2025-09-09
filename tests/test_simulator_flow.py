"""
Интеграционные тесты для симулятора: проверяем simulate_game и простую серию.
"""

from packages.simulator.game_simulator import GameSimulator


def test_simulate_single_game_finishes():
    sim = GameSimulator("config/cards.csv")
    result = sim.simulate_game("gangsters", "authorities")
    assert set(["winner", "turns", "clan1", "clan2"]).issubset(result.keys())
    assert result["clan1"] == "gangsters"
    assert result["clan2"] == "authorities"


def test_run_matchup_single_game():
    sim = GameSimulator("config/cards.csv")
    summary = sim.run_matchup_simulation("gangsters", "authorities", games=1)
    assert summary["games_played"] == 1
    assert summary["clan1"] == "gangsters"
    assert summary["clan2"] == "authorities"

"""
Kingpin Game Simulator
Симулятор множественных игровых тестов для анализа баланса
"""

import random
import math
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field as dataclass_field
from collections import defaultdict
from enum import Enum
import copy
import sys
from pathlib import Path

# Add parent directory to path for engine imports
sys.path.append(str(Path(__file__).parent.parent))
from engine.loader import load_cards_from_csv
from engine.models import Card as EngineCard

class GamePhase(Enum):
    SETUP = "setup"
    MAIN = "main"
    COMBAT = "combat"
    END = "end"

class ActionType(Enum):
    PLAY_CARD = "play_card"
    ATTACK = "attack"
    USE_ABILITY = "use_ability"
    END_TURN = "end_turn"

@dataclass
class GameCard:
    """Simulator-specific wrapper around engine Card model."""
    engine_card: EngineCard
    in_play: bool = False
    shields: int = 0
    used_abilities: List[str] = dataclass_field(default_factory=list)
    turn_played: int = 0
    kills: int = 0
    current_hp: Optional[int] = None
    current_atk: Optional[int] = None
    
    def __post_init__(self):
        # Initialize current stats from engine card
        if self.current_hp is None:
            self.current_hp = self.engine_card.hp
        if self.current_atk is None:
            self.current_atk = self.engine_card.atk
    
    # Property accessors for compatibility
    @property
    def id(self) -> str:
        return self.engine_card.id
    
    @property
    def name(self) -> str:
        return self.engine_card.name
    
    @property
    def caste(self) -> str:
        return self.engine_card.caste or ''
    
    @property
    def faction(self) -> str:
        return str(self.engine_card.faction)
    
    @property
    def hp(self) -> int:
        return self.current_hp or 0
    
    @property
    def max_hp(self) -> int:
        return self.engine_card.hp
    
    @property
    def atk(self) -> int:
        return self.current_atk or 0
    
    @property
    def base_atk(self) -> int:
        return self.engine_card.atk
    
    @property
    def price(self) -> int:
        return self.engine_card.price
    
    @property
    def corruption(self) -> int:
        return self.engine_card.corruption
    
    @property
    def defend(self) -> int:
        return self.engine_card.d
    
    @property
    def rage(self) -> int:
        return self.engine_card.rage
    
    @property
    def abilities(self) -> List[str]:
        # Convert ABL to string list for compatibility
        abl = self.engine_card.abl
        if isinstance(abl, dict):
            return [f"{k}:{v}" for k, v in abl.items()]
        elif isinstance(abl, int) and abl > 0:
            return [str(abl)]
        return []
    
    @classmethod
    def from_engine_card(cls, engine_card: EngineCard) -> 'GameCard':
        return cls(engine_card=engine_card)

@dataclass
class Player:
    name: str
    caste: str
    deck: List[GameCard]
    hand: List[GameCard] = dataclass_field(default_factory=list)
    field: List[GameCard] = dataclass_field(default_factory=list)
    graveyard: List[GameCard] = dataclass_field(default_factory=list)
    money: int = 3
    authority: int = 0
    corruption_resistance: bool = False
    
    def draw_card(self) -> Optional[GameCard]:
        if self.deck:
            card = self.deck.pop(0)
            self.hand.append(card)
            return card
        return None
    
    def play_card(self, card: GameCard, turn: int) -> bool:
        if card in self.hand and self.money >= card.price:
            self.hand.remove(card)
            self.field.append(card)
            card.in_play = True
            card.turn_played = turn
            self.money -= card.price
            return True
        return False
    
    def get_total_authority(self) -> int:
        authority = self.authority
        for card in self.field:
            if 'authority:' in str(card.abilities):
                for ability in card.abilities:
                    if 'authority:' in ability:
                        auth_val = int(ability.split(':')[1].strip().split()[0])
                        authority += auth_val
        return authority

@dataclass
class GameState:
    player1: Player
    player2: Player
    turn: int = 1
    phase: GamePhase = GamePhase.SETUP
    current_player: int = 1
    winner: Optional[str] = None
    max_turns: int = 20
    
    def get_current_player(self) -> Player:
        return self.player1 if self.current_player == 1 else self.player2
    
    def get_opponent(self) -> Player:
        return self.player2 if self.current_player == 1 else self.player1
    
    def switch_player(self):
        self.current_player = 2 if self.current_player == 1 else 1

class GameSimulator:
    def __init__(self, cards_file: str):
        self.cards_data = self.load_cards_from_csv(cards_file)
        self.castes = ['gangsters', 'authorities', 'loners', 'solo']
        
    def load_cards_from_csv(self, csv_file: str) -> Dict[str, List[GameCard]]:
        """Load cards from CSV using unified engine loader and organize by caste"""
        cards_by_caste = {
            'gangsters': [],
            'authorities': [],
            'loners': [],
            'solo': []
        }
        
        # Use unified card loader from engine
        engine_cards = load_cards_from_csv(csv_file, include_all=False)
        
        for engine_card in engine_cards:
            game_card = GameCard.from_engine_card(engine_card)
            caste = game_card.caste.lower()
            if caste in cards_by_caste:
                cards_by_caste[caste].append(game_card)
            elif caste == '':
                # Handle cards without caste as solo
                cards_by_caste['solo'].append(game_card)
        
        return cards_by_caste

    def create_deck(self, caste: str, deck_size: int = 8) -> List[GameCard]:
        """Создает колоду для указанной касты"""
        caste_cards = [card for card in self.cards_data[caste] if card.caste == caste]
        
        # Берем все доступные карты касты или случайную выборку
        if len(caste_cards) <= deck_size:
            deck = copy.deepcopy(caste_cards)
        else:
            deck = copy.deepcopy(random.sample(caste_cards, deck_size))
        
        # Перемешиваем колоду
        random.shuffle(deck)
        return deck
    
    def apply_card_abilities(self, card: GameCard, player: Player, opponent: Player, game_state: GameState):
        """Применяет способности карты"""
        for ability in card.abilities:
            ability_lower = ability.lower()
            
            # Экономические способности
            if 'steal:' in ability_lower:
                amount = int(ability.split(':')[1].strip().split()[0])
                stolen = min(amount, opponent.money)
                opponent.money -= stolen
                player.money += stolen
                
            elif 'gain:' in ability_lower or 'economy:' in ability_lower:
                if 'gain:' in ability_lower:
                    amount = int(ability.split(':')[1].strip().split()[0])
                else:
                    amount = int(ability.split(':')[1].strip().split()[0])
                player.money += amount
                
            elif 'audit:' in ability_lower:
                amount = int(ability.split(':')[1].strip().split()[0])
                opponent.money = max(0, opponent.money - amount)
            
            # Защитные способности
            elif 'bribe:' in ability_lower or 'extort:' in ability_lower:
                card.shields += 1
                
            elif 'authority:' in ability_lower:
                auth_amount = int(ability.split(':')[1].strip().split()[0])
                player.authority += auth_amount
            
            # Боевые способности
            elif 'berserker:' in ability_lower:
                damage_taken = card.max_hp - card.hp
                card.atk = card.base_atk + damage_taken
                
            elif 'assault:' in ability_lower:
                card.atk += card.kills
                
            elif 'lethal:' in ability_lower:
                card.atk += 1  # Дополнительный урон
    
    def combat_phase(self, attacker: GameCard, defender: GameCard) -> Tuple[bool, bool]:
        """Симулирует бой между двумя картами"""
        attacker_damage = max(0, attacker.atk - defender.shields)
        defender_damage = max(0, defender.atk - attacker.shields)
        
        # Применяем урон
        defender.hp -= attacker_damage
        attacker.hp -= defender_damage
        
        # Убираем щиты
        defender.shields = max(0, defender.shields - 1)
        attacker.shields = max(0, attacker.shields - 1)
        
        attacker_died = attacker.hp <= 0
        defender_died = defender.hp <= 0
        
        return attacker_died, defender_died
    
    def simulate_turn(self, game_state: GameState) -> bool:
        """Симулирует один ход игры"""
        current_player = game_state.get_current_player()
        opponent = game_state.get_opponent()
        
        # Фаза добора карты
        current_player.draw_card()
        
        # Фаза игры карт (простая AI)
        playable_cards = [card for card in current_player.hand if card.price <= current_player.money]
        if playable_cards:
            card_to_play = random.choice(playable_cards)
            current_player.play_card(card_to_play, game_state.turn)
            self.apply_card_abilities(card_to_play, current_player, opponent, game_state)
        
        # Фаза атаки
        for attacker in current_player.field:
            if opponent.field:
                # Атакуем случайную карту противника
                defender = random.choice(opponent.field)
                attacker_died, defender_died = self.combat_phase(attacker, defender)
                
                if attacker_died:
                    current_player.field.remove(attacker)
                    current_player.graveyard.append(attacker)
                
                if defender_died:
                    opponent.field.remove(defender)
                    opponent.graveyard.append(defender)
                    attacker.kills += 1
        
        # Проверка условий победы
        if not opponent.field and not opponent.hand and not opponent.deck:
            game_state.winner = current_player.name
            return True
        
        if game_state.turn >= game_state.max_turns:
            # Победа по очкам (количество карт на поле)
            p1_score = len(game_state.player1.field)
            p2_score = len(game_state.player2.field)
            
            if p1_score > p2_score:
                game_state.winner = game_state.player1.name
            elif p2_score > p1_score:
                game_state.winner = game_state.player2.name
            else:
                game_state.winner = "Draw"
            return True
        
        return False
    
    def simulate_game(self, caste1: str, caste2: str) -> Dict[str, Any]:
        """Симулирует одну игру между двумя кастами"""
        deck1 = self.create_deck(caste1)
        deck2 = self.create_deck(caste2)
        
        player1 = Player(name=f"Player_{caste1}", caste=caste1, deck=deck1)
        player2 = Player(name=f"Player_{caste2}", caste=caste2, deck=deck2)
        
        # Начальная раздача
        for _ in range(3):
            player1.draw_card()
            player2.draw_card()
        
        game_state = GameState(player1=player1, player2=player2)
        
        # Симулируем игру
        while not self.simulate_turn(game_state):
            game_state.switch_player()
            if game_state.current_player == 1:
                game_state.turn += 1
        
        return {
            'winner': game_state.winner,
            'turns': game_state.turn,
            'caste1': caste1,
            'caste2': caste2,
            'p1_cards_played': len(player1.graveyard) + len(player1.field),
            'p2_cards_played': len(player2.graveyard) + len(player2.field),
            'p1_final_field': len(player1.field),
            'p2_final_field': len(player2.field)
        }
    
    def run_matchup_simulation(self, caste1: str, caste2: str, games: int = 100) -> Dict[str, Any]:
        """Запускает серию игр между двумя кастами"""
        results = []
        wins = {caste1: 0, caste2: 0, 'Draw': 0}
        total_turns = 0
        
        for _ in range(games):
            result = self.simulate_game(caste1, caste2)
            results.append(result)
            
            if result['winner'] == f"Player_{caste1}":
                wins[caste1] += 1
            elif result['winner'] == f"Player_{caste2}":
                wins[caste2] += 1
            else:
                wins['Draw'] += 1
            
            total_turns += result['turns']
        
        return {
            'caste1': caste1,
            'caste2': caste2,
            'games_played': games,
            'wins': wins,
            'win_rates': {
                caste1: wins[caste1] / games * 100,
                caste2: wins[caste2] / games * 100,
                'Draw': wins['Draw'] / games * 100
            },
            'avg_game_length': total_turns / games,
            'detailed_results': results
        }
    
    def run_full_tournament(self, games_per_matchup: int = 50) -> Dict[str, Any]:
        """Запускает полный турнир между всеми кастами"""
        tournament_results = {}
        caste_stats = {caste: {'wins': 0, 'losses': 0, 'draws': 0, 'games': 0} for caste in self.castes}
        
        # Все возможные матчапы
        for i, caste1 in enumerate(self.castes):
            for j, caste2 in enumerate(self.castes):
                if i < j:  # Избегаем дублирования матчапов
                    matchup_key = f"{caste1}_vs_{caste2}"
                    result = self.run_matchup_simulation(caste1, caste2, games_per_matchup)
                    tournament_results[matchup_key] = result
                    
                    # Обновляем статистику кастов
                    caste_stats[caste1]['wins'] += result['wins'][caste1]
                    caste_stats[caste1]['losses'] += result['wins'][caste2]
                    caste_stats[caste1]['draws'] += result['wins']['Draw']
                    caste_stats[caste1]['games'] += games_per_matchup
                    
                    caste_stats[caste2]['wins'] += result['wins'][caste2]
                    caste_stats[caste2]['losses'] += result['wins'][caste1]
                    caste_stats[caste2]['draws'] += result['wins']['Draw']
                    caste_stats[caste2]['games'] += games_per_matchup
        
        # Вычисляем общие винрейты
        for caste in self.castes:
            stats = caste_stats[caste]
            if stats['games'] > 0:
                stats['win_rate'] = stats['wins'] / stats['games'] * 100
                stats['loss_rate'] = stats['losses'] / stats['games'] * 100
                stats['draw_rate'] = stats['draws'] / stats['games'] * 100
        
        return {
            'tournament_results': tournament_results,
            'caste_statistics': caste_stats,
            'games_per_matchup': games_per_matchup,
            'total_games': len(tournament_results) * games_per_matchup
        }
    
    def generate_simulation_report(self, tournament_data: Dict[str, Any]) -> str:
        """Генерирует отчет по результатам симуляции"""
        report = "# ОТЧЕТ ПО ИГРОВОЙ СИМУЛЯЦИИ KINGPIN\n\n"
        
        caste_stats = tournament_data['caste_statistics']
        games_per_matchup = tournament_data['games_per_matchup']
        
        report += f"**Общая информация:**\n"
        report += f"- Игр на матчап: {games_per_matchup}\n"
        report += f"- Всего игр: {tournament_data['total_games']}\n"
        report += f"- Матчапов: {len(tournament_data['tournament_results'])}\n\n"
        
        # Общий рейтинг кастов по винрейту
        sorted_castes = sorted(caste_stats.items(), key=lambda x: x[1]['win_rate'], reverse=True)
        
        report += "## Общий рейтинг кастов\n\n"
        for i, (caste, stats) in enumerate(sorted_castes, 1):
            report += f"{i}. **{caste.upper()}**\n"
            report += f"   - Винрейт: {stats['win_rate']:.1f}%\n"
            report += f"   - Побед: {stats['wins']}/{stats['games']}\n"
            report += f"   - Поражений: {stats['losses']}/{stats['games']}\n"
            report += f"   - Ничьих: {stats['draws']}/{stats['games']}\n\n"
        
        # Детальные результаты матчапов
        report += "## Детальные результаты матчапов\n\n"
        
        for matchup_key, result in tournament_data['tournament_results'].items():
            caste1, caste2 = result['caste1'], result['caste2']
            report += f"### {caste1.upper()} vs {caste2.upper()}\n"
            report += f"- **{caste1}**: {result['win_rates'][caste1]:.1f}% ({result['wins'][caste1]} побед)\n"
            report += f"- **{caste2}**: {result['win_rates'][caste2]:.1f}% ({result['wins'][caste2]} побед)\n"
            report += f"- **Ничьи**: {result['win_rates']['Draw']:.1f}% ({result['wins']['Draw']})\n"
            report += f"- Средняя длина игры: {result['avg_game_length']:.1f} ходов\n\n"
        
        # Анализ баланса
        report += "## Анализ баланса\n\n"
        win_rates = [stats['win_rate'] for stats in caste_stats.values()]
        max_wr = max(win_rates)
        min_wr = min(win_rates)
        balance_gap = max_wr - min_wr
        
        report += f"**Разрыв в винрейтах**: {balance_gap:.1f}%\n"
        
        if balance_gap > 20:
            report += "⚠️ **КРИТИЧЕСКИЙ ДИСБАЛАНС** - разрыв превышает 20%\n"
        elif balance_gap > 10:
            report += "⚡ **УМЕРЕННЫЙ ДИСБАЛАНС** - разрыв превышает 10%\n"
        else:
            report += "✅ **ХОРОШИЙ БАЛАНС** - разрыв менее 10%\n"
        
        strongest_caste = max(sorted_castes, key=lambda x: x[1]['win_rate'])
        weakest_caste = min(sorted_castes, key=lambda x: x[1]['win_rate'])
        
        report += f"\n**Самая сильная каста**: {strongest_caste[0]} ({strongest_caste[1]['win_rate']:.1f}%)\n"
        report += f"**Самая слабая каста**: {weakest_caste[0]} ({weakest_caste[1]['win_rate']:.1f}%)\n"
        
        return report

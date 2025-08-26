"""
Kingpin Card Balance Analyzer
Методика расчета эффективности и баланса кланов на основе свойств карт
"""

import csv
import math
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass
from collections import defaultdict

@dataclass
class Card:
    id: str
    name: str
    type: str
    caste: str
    faction: str
    hp: float
    atk: float
    price: float
    corruption: float
    defend: float
    rage: float
    abl: str
    independence: float
    in_deck: bool
    description: str

class BalanceAnalyzer:
    """Анализатор баланса карт и кланов"""
    
    def __init__(self, cards_file: str):
        self.cards = self._load_cards(cards_file)
        self.castes = ['gangsters', 'authorities', 'loners', 'solo']
        
    def _load_cards(self, filename: str) -> List[Card]:
        """Загружает карты из CSV файла"""
        cards = []
        with open(filename, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Обработка числовых значений
                hp = self._parse_numeric(row['HP'])
                atk = self._parse_numeric(row['ATK'])
                price = self._parse_numeric(row['Price'])
                corruption = self._parse_numeric(row['Corruption'])
                defend = self._parse_numeric(row['Defend'])
                rage = self._parse_numeric(row['Rage'])
                independence = self._parse_numeric(row['Independence'])
                in_deck = row['В_колоде'] == '✓'
                
                # Prefer new header 'Клан', fallback to legacy 'Каста'
                clan_value = row.get('Клан') or row.get('Каста') or ''

                card = Card(
                    id=row['ID'],
                    name=row['Название'],
                    type=row['Тип'],
                    caste=clan_value,
                    faction=row['Фракция'],
                    hp=hp,
                    atk=atk,
                    price=price,
                    corruption=corruption,
                    defend=defend,
                    rage=rage,
                    abl=row['ABL'],
                    independence=independence,
                    in_deck=in_deck,
                    description=row['Описание']
                )
                cards.append(card)
        return cards
    
    def _parse_numeric(self, value: str) -> float:
        """Парсит числовые значения, обрабатывая n/a и пустые строки"""
        if not value or value.lower() in ['n/a', '']:
            return 0.0
        try:
            return float(value)
        except ValueError:
            return 0.0
    
    def calculate_card_power_rating(self, card: Card) -> float:
        """
        Базовый рейтинг мощности карты (CPR - Card Power Rating)
        Формула: CPR = (HP × 0.8) + (ATK × 1.2) + (Defend × 1.0) + (Rage × 0.5)
        """
        if card.type in ['event', 'token']:
            return 0.0
            
        base_power = (card.hp * 0.8 + 
                     card.atk * 1.2 + 
                     card.defend * 1.0 + 
                     card.rage * 0.5)
        return base_power
    
    def calculate_ability_value(self, card: Card) -> float:
        """
        Оценка ценности способностей карты (AV - Ability Value)
        """
        if not card.abl or card.abl == '0':
            return 0.0
            
        ability_value = 0.0
        abl_text = card.abl.lower()
        
        # Экономические способности
        if 'steal' in abl_text:
            ability_value += 2.5  # Кража денег
        if 'gain' in abl_text:
            ability_value += 1.5  # Получение денег
        if 'bribe' in abl_text:
            ability_value += 2.0  # Подкуп/защита
        if 'trade' in abl_text:
            ability_value += 1.8  # Торговые скидки
            
        # Боевые способности
        if 'precision' in abl_text:
            ability_value += 2.2  # Пробивание защиты
        if 'hack' in abl_text:
            ability_value += 1.8  # Снятие защиты
        if 'stealth' in abl_text:
            ability_value += 1.5  # Скрытность/бафы
            
        # Лечение и поддержка
        if 'heal' in abl_text:
            ability_value += 2.0  # Лечение
        if 'repair' in abl_text:
            ability_value += 2.5  # Восстановление карт
        if 'authority' in abl_text:
            if '2' in abl_text:
                ability_value += 3.0  # Authority: 2
            else:
                ability_value += 1.5  # Authority: 1
                
        # Информационные способности
        if 'intel' in abl_text:
            ability_value += 1.2  # Просмотр колоды
        if 'tech' in abl_text:
            ability_value += 2.8  # Дополнительные карты
            
        # Защитные способности
        if 'escape' in abl_text:
            ability_value += 1.0  # Защита от подкупа
        if 'discipline' in abl_text:
            ability_value += 2.0  # Увеличение защиты
            
        return ability_value
    
    def calculate_cost_efficiency(self, card: Card) -> float:
        """
        Эффективность стоимости карты (CE - Cost Efficiency)
        Формула: CE = (CPR + AV) / max(Price, 1)
        """
        if card.type in ['event', 'token', 'boss']:
            return 0.0
            
        total_value = self.calculate_card_power_rating(card) + self.calculate_ability_value(card)
        cost = max(card.price, 1)  # Избегаем деления на 0
        
        return total_value / cost
    
    def calculate_corruption_risk(self, card: Card) -> float:
        """
        Риск коррупции карты (CR - Corruption Risk)
        Формула: CR = Corruption / max(HP, 1)
        """
        if card.corruption == 0 or card.type in ['event', 'token']:
            return 0.0
            
        return card.corruption / max(card.hp, 1)
    
    def calculate_survivability_index(self, card: Card) -> float:
        """
        Индекс выживаемости карты (SI - Survivability Index)
        Формула: SI = HP + (Defend × 2) - (Corruption_Risk × 2)
        """
        if card.type in ['event', 'token']:
            return 0.0
            
        corruption_risk = self.calculate_corruption_risk(card)
        survivability = card.hp + (card.defend * 2) - (corruption_risk * 2)
        
        return max(survivability, 0)
    
    def calculate_card_overall_rating(self, card: Card) -> float:
        """
        Общий рейтинг карты (COR - Card Overall Rating)
        Формула: COR = (CPR × 0.3) + (AV × 0.4) + (CE × 0.2) + (SI × 0.1)
        """
        if card.type in ['event', 'token']:
            return 0.0
            
        cpr = self.calculate_card_power_rating(card)
        av = self.calculate_ability_value(card)
        ce = self.calculate_cost_efficiency(card)
        si = self.calculate_survivability_index(card)
        
        overall = (cpr * 0.3) + (av * 0.4) + (ce * 0.2) + (si * 0.1)
        return overall
    
    def analyze_caste_balance(self) -> Dict[str, Dict[str, float]]:
        """
        Анализ баланса кланов
        """
        caste_stats = {}
        
        for caste in self.castes:
            caste_cards = [c for c in self.cards if c.caste == caste and c.in_deck and c.type != 'boss']
            
            if not caste_cards:
                continue
                
            # Базовые статистики
            total_cards = len(caste_cards)
            avg_hp = sum(c.hp for c in caste_cards) / total_cards
            avg_atk = sum(c.atk for c in caste_cards) / total_cards
            avg_price = sum(c.price for c in caste_cards) / total_cards
            avg_corruption = sum(c.corruption for c in caste_cards) / total_cards
            
            # Расчетные метрики
            avg_power_rating = sum(self.calculate_card_power_rating(c) for c in caste_cards) / total_cards
            avg_ability_value = sum(self.calculate_ability_value(c) for c in caste_cards) / total_cards
            avg_cost_efficiency = sum(self.calculate_cost_efficiency(c) for c in caste_cards) / total_cards
            avg_survivability = sum(self.calculate_survivability_index(c) for c in caste_cards) / total_cards
            avg_overall_rating = sum(self.calculate_card_overall_rating(c) for c in caste_cards) / total_cards
            
            # Специализация клана
            faction_distribution = defaultdict(int)
            for card in caste_cards:
                if card.faction != 'n/a':
                    faction_distribution[card.faction] += 1
            
            caste_stats[caste] = {
                'card_count': total_cards,
                'avg_hp': avg_hp,
                'avg_atk': avg_atk,
                'avg_price': avg_price,
                'avg_corruption': avg_corruption,
                'avg_power_rating': avg_power_rating,
                'avg_ability_value': avg_ability_value,
                'avg_cost_efficiency': avg_cost_efficiency,
                'avg_survivability': avg_survivability,
                'avg_overall_rating': avg_overall_rating,
                'faction_distribution': dict(faction_distribution),
                'specialization_score': self._calculate_specialization_score(caste_cards)
            }
            
        return caste_stats
    
    def _calculate_specialization_score(self, cards: List[Card]) -> float:
        """
        Оценка специализации клана (насколько уникальны его карты)
        """
        if not cards:
            return 0.0
            
        # Анализ распределения по фракциям
        faction_counts = defaultdict(int)
        for card in cards:
            if card.faction != 'n/a':
                faction_counts[card.faction] += 1
        
        if not faction_counts:
            return 0.0
            
        # Расчет энтропии распределения (чем выше, тем более разнообразен клан)
        total = sum(faction_counts.values())
        entropy = 0.0
        for count in faction_counts.values():
            if count > 0:
                p = count / total
                entropy -= p * math.log2(p)
        
        return entropy
    
    def generate_balance_report(self) -> str:
        """
        Генерирует полный отчет по балансу
        """
        caste_stats = self.analyze_caste_balance()
        
        report = "# ОТЧЕТ ПО БАЛАНСУ КЛАНОВ KINGPIN\n\n"
        report += "## Методология расчета\n\n"
        report += "**Базовые метрики:**\n"
        report += "- **CPR (Card Power Rating)**: (HP × 0.8) + (ATK × 1.2) + (Defend × 1.0) + (Rage × 0.5)\n"
        report += "- **AV (Ability Value)**: Оценка ценности способностей карты\n"
        report += "- **CE (Cost Efficiency)**: (CPR + AV) / Price\n"
        report += "- **SI (Survivability Index)**: HP + (Defend × 2) - (Corruption_Risk × 2)\n"
        report += "- **COR (Card Overall Rating)**: (CPR × 0.3) + (AV × 0.4) + (CE × 0.2) + (SI × 0.1)\n\n"
        
        report += "## Анализ по кланам\n\n"
        
        # Сортировка кланов по общему рейтингу
        sorted_castes = sorted(caste_stats.items(), 
                             key=lambda x: x[1]['avg_overall_rating'], 
                             reverse=True)
        
        for caste, stats in sorted_castes:
            report += f"### {caste.upper()}\n"
            report += f"- **Количество карт**: {stats['card_count']}\n"
            report += f"- **Средний HP**: {stats['avg_hp']:.1f}\n"
            report += f"- **Средний ATK**: {stats['avg_atk']:.1f}\n"
            report += f"- **Средняя цена**: {stats['avg_price']:.1f}💰\n"
            report += f"- **Средняя коррупция**: {stats['avg_corruption']:.1f}\n"
            report += f"- **Рейтинг мощности**: {stats['avg_power_rating']:.2f}\n"
            report += f"- **Ценность способностей**: {stats['avg_ability_value']:.2f}\n"
            report += f"- **Эффективность стоимости**: {stats['avg_cost_efficiency']:.2f}\n"
            report += f"- **Индекс выживаемости**: {stats['avg_survivability']:.2f}\n"
            report += f"- **ОБЩИЙ РЕЙТИНГ**: **{stats['avg_overall_rating']:.2f}**\n"
            report += f"- **Специализация**: {stats['specialization_score']:.2f}\n"
            
            if stats['faction_distribution']:
                report += "- **Распределение по фракциям**: "
                factions = [f"{k}({v})" for k, v in stats['faction_distribution'].items()]
                report += ", ".join(factions) + "\n"
            report += "\n"
        
        # Рекомендации по балансу
        report += "## Рекомендации по балансу\n\n"
        
        ratings = [stats['avg_overall_rating'] for stats in caste_stats.values()]
        if ratings:
            max_rating = max(ratings)
            min_rating = min(ratings)
            balance_gap = max_rating - min_rating
            
            report += f"**Разрыв в балансе**: {balance_gap:.2f}\n"
            
            if balance_gap > 1.0:
                report += "⚠️ **КРИТИЧЕСКИЙ ДИСБАЛАНС** - разрыв превышает 1.0\n"
            elif balance_gap > 0.5:
                report += "⚡ **УМЕРЕННЫЙ ДИСБАЛАНС** - требуется корректировка\n"
            else:
                report += "✅ **ХОРОШИЙ БАЛАНС** - кланы примерно равны\n"
            
            # Конкретные рекомендации
            weakest_caste = min(sorted_castes, key=lambda x: x[1]['avg_overall_rating'])
            strongest_caste = max(sorted_castes, key=lambda x: x[1]['avg_overall_rating'])
            
            report += f"\n**Самый слабый клан**: {weakest_caste[0]} ({weakest_caste[1]['avg_overall_rating']:.2f})\n"
            report += f"**Самый сильный клан**: {strongest_caste[0]} ({strongest_caste[1]['avg_overall_rating']:.2f})\n"
        
        return report
    
    def get_top_cards_by_rating(self, limit: int = 10) -> List[Tuple[Card, float]]:
        """
        Возвращает топ карт по общему рейтингу
        """
        deck_cards = [c for c in self.cards if c.in_deck and c.type not in ['event', 'token', 'boss']]
        card_ratings = [(card, self.calculate_card_overall_rating(card)) for card in deck_cards]
        card_ratings.sort(key=lambda x: x[1], reverse=True)
        
        return card_ratings[:limit]
    
    def get_weakest_cards(self, limit: int = 10) -> List[Tuple[Card, float]]:
        """
        Возвращает самые слабые карты по общему рейтингу
        """
        deck_cards = [c for c in self.cards if c.in_deck and c.type not in ['event', 'token', 'boss']]
        card_ratings = [(card, self.calculate_card_overall_rating(card)) for card in deck_cards]
        card_ratings.sort(key=lambda x: x[1])
        
        return card_ratings[:limit]

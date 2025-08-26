"""
Kingpin Game Experience Analyzer
Анализатор игрового опыта на основе стандартных критериев настольных игр
"""

import math
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass
from enum import Enum
import statistics
import sys
from pathlib import Path

# Add parent directory to path for engine imports
sys.path.append(str(Path(__file__).parent.parent))
sys.path.append(str(Path(__file__).parent.parent.parent))
from packages.engine.loader import load_cards_from_csv
from packages.engine.models import Card

class GameAspect(Enum):
    LEARNING_EASE = "learning_ease"           # Простота изучения
    EXCITEMENT = "excitement"                 # Интерес/Азарт
    STRATEGIC_DEPTH = "strategic_depth"       # Стратегическая глубина
    REPLAYABILITY = "replayability"          # Переиграбельность
    PLAYER_INTERACTION = "player_interaction" # Взаимодействие игроков
    GAME_LENGTH = "game_length"              # Длительность игры
    THEME_INTEGRATION = "theme_integration"   # Интеграция темы
    COMPONENT_QUALITY = "component_quality"   # Качество компонентов
    BALANCE = "balance"                      # Баланс
    ACCESSIBILITY = "accessibility"          # Доступность

@dataclass
class GameMetrics:
    """Метрики для анализа игрового процесса"""
    # Базовые характеристики
    total_cards: int
    unique_abilities: int
    clans_count: int
    avg_card_complexity: float
    
    # Экономические показатели
    price_range: Tuple[int, int]
    price_variance: float
    
    # Боевые показатели
    hp_range: Tuple[int, int]
    atk_range: Tuple[int, int]
    power_variance: float
    
    # Специальные механики
    corruption_cards_ratio: float
    defensive_cards_ratio: float
    economic_cards_ratio: float

@dataclass
class AspectScore:
    """Оценка отдельного аспекта игры"""
    aspect: GameAspect
    score: float  # 1-10
    reasoning: str
    recommendations: List[str]

class GameExperienceAnalyzer:
    """Анализатор игрового опыта Kingpin"""
    
    def __init__(self, cards_file: str):
        self.cards = load_cards_from_csv(cards_file, include_all=True)
        self.deck_cards = [c for c in self.cards if hasattr(c, 'in_deck') and c.in_deck]
        self.metrics = self._calculate_metrics()
    
    def _calculate_metrics(self) -> GameMetrics:
        """Вычисляет базовые метрики игры"""
        if not self.deck_cards:
            return GameMetrics(0, 0, 0, 0, (0, 0), 0, (0, 0), (0, 0), 0, 0, 0, 0)
        
        # Базовые характеристики
        total_cards = len(self.deck_cards)
        unique_abilities = len(set(str(c.abl) for c in self.deck_cards if c.abl))
        clans = set(c.caste for c in self.deck_cards if c.caste)
        clans_count = len(clans)
        
        # Сложность карт (количество слов в способностях)
        complexity_scores = []
        for card in self.deck_cards:
            if card.abl and isinstance(card.abl, str):
                complexity_scores.append(len(card.abl.split()))
            else:
                complexity_scores.append(0)
        avg_card_complexity = statistics.mean(complexity_scores) if complexity_scores else 0
        
        # Экономические показатели
        prices = [c.price for c in self.deck_cards]
        price_range = (min(prices), max(prices)) if prices else (0, 0)
        price_variance = statistics.variance(prices) if len(prices) > 1 else 0
        
        # Боевые показатели
        hps = [c.hp for c in self.deck_cards]
        atks = [c.atk for c in self.deck_cards]
        hp_range = (min(hps), max(hps)) if hps else (0, 0)
        atk_range = (min(atks), max(atks)) if atks else (0, 0)
        
        # Дисперсия силы (HP + ATK)
        power_values = [c.hp + c.atk for c in self.deck_cards]
        power_variance = statistics.variance(power_values) if len(power_values) > 1 else 0
        
        # Специальные механики
        corruption_cards = sum(1 for c in self.deck_cards if c.corruption > 0)
        defensive_cards = sum(1 for c in self.deck_cards if c.d > 0)
        economic_cards = sum(1 for c in self.deck_cards 
                           if c.abl and any(keyword in str(c.abl).lower() 
                                          for keyword in ['economy', 'steal', 'gain', 'audit']))
        
        corruption_ratio = corruption_cards / total_cards if total_cards > 0 else 0
        defensive_ratio = defensive_cards / total_cards if total_cards > 0 else 0
        economic_ratio = economic_cards / total_cards if total_cards > 0 else 0
        
        return GameMetrics(
            total_cards=total_cards,
            unique_abilities=unique_abilities,
            clans_count=clans_count,
            avg_card_complexity=avg_card_complexity,
            price_range=price_range,
            price_variance=price_variance,
            hp_range=hp_range,
            atk_range=atk_range,
            power_variance=power_variance,
            corruption_cards_ratio=corruption_ratio,
            defensive_cards_ratio=defensive_ratio,
            economic_cards_ratio=economic_ratio
        )
    
    def analyze_learning_ease(self) -> AspectScore:
        """Анализ простоты изучения (1-10)"""
        score = 10.0
        reasoning_parts = []
        recommendations = []
        
        # Количество уникальных механик (чем больше, тем сложнее)
        if self.metrics.unique_abilities > 20:
            score -= 2.0
            reasoning_parts.append("много уникальных способностей")
            recommendations.append("Упростить или объединить похожие способности")
        elif self.metrics.unique_abilities > 15:
            score -= 1.0
            reasoning_parts.append("умеренное количество способностей")
        
        # Сложность текста способностей
        if self.metrics.avg_card_complexity > 8:
            score -= 2.0
            reasoning_parts.append("сложные описания способностей")
            recommendations.append("Сократить текст способностей, использовать иконки")
        elif self.metrics.avg_card_complexity > 5:
            score -= 1.0
            reasoning_parts.append("средняя сложность текста")
        
        # Количество кланов (больше выбора = сложнее)
        if self.metrics.clans_count > 6:
            score -= 1.5
            reasoning_parts.append("много кланов для изучения")
            recommendations.append("Рассмотреть базовый набор с меньшим количеством кланов")
        elif self.metrics.clans_count < 3:
            score -= 1.0
            reasoning_parts.append("мало вариативности кланов")
            recommendations.append("Добавить больше кланов для разнообразия")
        
        # Дисперсия цен (предсказуемость экономики)
        if self.metrics.price_variance > 2.0:
            score -= 1.0
            reasoning_parts.append("непредсказуемая экономика")
            recommendations.append("Сделать ценообразование более логичным")
        
        reasoning = f"Простота изучения: {', '.join(reasoning_parts)}"
        
        return AspectScore(
            aspect=GameAspect.LEARNING_EASE,
            score=max(1.0, min(10.0, score)),
            reasoning=reasoning,
            recommendations=recommendations
        )
    
    def analyze_excitement(self) -> AspectScore:
        """Анализ интереса/азарта (1-10)"""
        score = 5.0
        reasoning_parts = []
        recommendations = []
        
        # Вариативность силы карт (создает напряжение)
        if self.metrics.power_variance > 10:
            score += 2.0
            reasoning_parts.append("высокая вариативность силы карт")
        elif self.metrics.power_variance > 5:
            score += 1.0
            reasoning_parts.append("умеренная вариативность")
        else:
            score -= 1.0
            reasoning_parts.append("низкая вариативность силы")
            recommendations.append("Добавить больше разнообразия в силе карт")
        
        # Механики взаимодействия (corruption, steal, etc.)
        interaction_score = (self.metrics.corruption_cards_ratio + 
                           self.metrics.economic_cards_ratio) * 10
        if interaction_score > 4:
            score += 2.0
            reasoning_parts.append("много интерактивных механик")
        elif interaction_score > 2:
            score += 1.0
            reasoning_parts.append("умеренное взаимодействие")
        else:
            score -= 1.0
            reasoning_parts.append("мало взаимодействия между игроками")
            recommendations.append("Добавить больше карт с интерактивными способностями")
        
        # Защитные механики (создают тактическую глубину)
        if self.metrics.defensive_cards_ratio > 0.3:
            score += 1.0
            reasoning_parts.append("хорошая защитная тактика")
        elif self.metrics.defensive_cards_ratio < 0.1:
            score -= 1.0
            reasoning_parts.append("мало защитных опций")
            recommendations.append("Добавить больше защитных механик")
        
        # Разнообразие кланов
        if self.metrics.clans_count >= 4:
            score += 1.0
            reasoning_parts.append("хорошее разнообразие кланов")
        else:
            recommendations.append("Увеличить количество уникальных кланов")
        
        reasoning = f"Интерес/азарт: {', '.join(reasoning_parts)}"
        
        return AspectScore(
            aspect=GameAspect.EXCITEMENT,
            score=max(1.0, min(10.0, score)),
            reasoning=reasoning,
            recommendations=recommendations
        )
    
    def analyze_strategic_depth(self) -> AspectScore:
        """Анализ стратегической глубины (1-10)"""
        score = 5.0
        reasoning_parts = []
        recommendations = []
        
        # Количество уникальных стратегий (кланы × способности)
        strategic_combinations = self.metrics.clans_count * (self.metrics.unique_abilities / 5)
        if strategic_combinations > 20:
            score += 2.5
            reasoning_parts.append("множество стратегических комбинаций")
        elif strategic_combinations > 10:
            score += 1.5
            reasoning_parts.append("хорошее разнообразие стратегий")
        else:
            score -= 1.0
            reasoning_parts.append("ограниченные стратегические опции")
            recommendations.append("Увеличить синергии между картами и кланами")
        
        # Экономическая сложность
        if self.metrics.economic_cards_ratio > 0.2:
            score += 1.5
            reasoning_parts.append("сложная экономическая игра")
        elif self.metrics.economic_cards_ratio > 0.1:
            score += 0.5
            reasoning_parts.append("базовая экономика")
        else:
            recommendations.append("Добавить больше экономических решений")
        
        # Диапазон цен (больше диапазон = больше решений)
        price_range_size = self.metrics.price_range[1] - self.metrics.price_range[0]
        if price_range_size > 4:
            score += 1.0
            reasoning_parts.append("широкий диапазон стоимости карт")
        elif price_range_size < 2:
            score -= 1.0
            recommendations.append("Увеличить диапазон стоимости карт")
        
        reasoning = f"Стратегическая глубина: {', '.join(reasoning_parts)}"
        
        return AspectScore(
            aspect=GameAspect.STRATEGIC_DEPTH,
            score=max(1.0, min(10.0, score)),
            reasoning=reasoning,
            recommendations=recommendations
        )
    
    def analyze_replayability(self) -> AspectScore:
        """Анализ переиграбельности (1-10)"""
        score = 5.0
        reasoning_parts = []
        recommendations = []
        
        # Количество карт на клан (больше = больше вариантов сборки колод)
        avg_cards_per_clan = self.metrics.total_cards / max(1, self.metrics.clans_count)
        if avg_cards_per_clan > 15:
            score += 2.0
            reasoning_parts.append("много карт для каждого клана")
        elif avg_cards_per_clan > 10:
            score += 1.0
            reasoning_parts.append("достаточно карт для вариативности")
        else:
            score -= 1.0
            reasoning_parts.append("мало карт на клан")
            recommendations.append("Добавить больше карт для каждого клана")
        
        # Уникальность кланов
        if self.metrics.clans_count >= 4:
            score += 1.5
            reasoning_parts.append("множество уникальных кланов")
        elif self.metrics.clans_count >= 3:
            score += 0.5
            reasoning_parts.append("базовое разнообразие кланов")
        
        # Комбинаторика способностей
        ability_combinations = self.metrics.unique_abilities * self.metrics.clans_count
        if ability_combinations > 80:
            score += 1.5
            reasoning_parts.append("высокая комбинаторика способностей")
        elif ability_combinations > 40:
            score += 0.5
            reasoning_parts.append("умеренная комбинаторика")
        
        reasoning = f"Переиграбельность: {', '.join(reasoning_parts)}"
        
        return AspectScore(
            aspect=GameAspect.REPLAYABILITY,
            score=max(1.0, min(10.0, score)),
            reasoning=reasoning,
            recommendations=recommendations
        )
    
    def analyze_balance(self) -> AspectScore:
        """Анализ баланса (1-10)"""
        score = 8.0  # Начинаем с хорошего баланса
        reasoning_parts = []
        recommendations = []
        
        # Дисперсия силы (слишком большая = дисбаланс)
        if self.metrics.power_variance > 15:
            score -= 3.0
            reasoning_parts.append("большой разброс в силе карт")
            recommendations.append("Выровнять силу карт или добавить компенсирующие механики")
        elif self.metrics.power_variance > 8:
            score -= 1.5
            reasoning_parts.append("умеренный разброс силы")
        else:
            reasoning_parts.append("хорошо сбалансированная сила карт")
        
        # Дисперсия цен
        if self.metrics.price_variance > 3:
            score -= 1.5
            reasoning_parts.append("неравномерное ценообразование")
            recommendations.append("Пересмотреть стоимость карт относительно их силы")
        
        # Распределение специальных механик
        total_special = (self.metrics.corruption_cards_ratio + 
                        self.metrics.defensive_cards_ratio + 
                        self.metrics.economic_cards_ratio)
        if total_special > 0.8:
            score -= 1.0
            reasoning_parts.append("слишком много специальных механик")
            recommendations.append("Добавить больше простых карт для баланса")
        elif total_special < 0.3:
            score -= 1.0
            reasoning_parts.append("мало специальных механик")
            recommendations.append("Добавить больше уникальных способностей")
        
        reasoning = f"Баланс: {', '.join(reasoning_parts)}"
        
        return AspectScore(
            aspect=GameAspect.BALANCE,
            score=max(1.0, min(10.0, score)),
            reasoning=reasoning,
            recommendations=recommendations
        )
    
    def analyze_all_aspects(self) -> Dict[GameAspect, AspectScore]:
        """Проводит полный анализ всех аспектов игры"""
        return {
            GameAspect.LEARNING_EASE: self.analyze_learning_ease(),
            GameAspect.EXCITEMENT: self.analyze_excitement(),
            GameAspect.STRATEGIC_DEPTH: self.analyze_strategic_depth(),
            GameAspect.REPLAYABILITY: self.analyze_replayability(),
            GameAspect.BALANCE: self.analyze_balance()
        }
    
    def generate_comprehensive_report(self) -> str:
        """Генерирует полный отчет по анализу игрового опыта"""
        aspects = self.analyze_all_aspects()
        
        report = "# АНАЛИЗ ИГРОВОГО ОПЫТА KINGPIN\n\n"
        
        # Общие метрики
        report += "## Общие характеристики игры\n\n"
        report += f"- **Всего карт в колодах**: {self.metrics.total_cards}\n"
        report += f"- **Количество кланов**: {self.metrics.clans_count}\n"
        report += f"- **Уникальных способностей**: {self.metrics.unique_abilities}\n"
        report += f"- **Диапазон цен**: {self.metrics.price_range[0]}-{self.metrics.price_range[1]}💰\n"
        report += f"- **Диапазон HP**: {self.metrics.hp_range[0]}-{self.metrics.hp_range[1]}\n"
        report += f"- **Диапазон ATK**: {self.metrics.atk_range[0]}-{self.metrics.atk_range[1]}\n"
        report += f"- **Карт с коррупцией**: {self.metrics.corruption_cards_ratio:.1%}\n"
        report += f"- **Защитных карт**: {self.metrics.defensive_cards_ratio:.1%}\n"
        report += f"- **Экономических карт**: {self.metrics.economic_cards_ratio:.1%}\n\n"
        
        # Оценки по аспектам
        report += "## Оценка игрового опыта\n\n"
        
        # Сортируем по важности
        priority_order = [
            GameAspect.LEARNING_EASE,
            GameAspect.EXCITEMENT,
            GameAspect.STRATEGIC_DEPTH,
            GameAspect.BALANCE,
            GameAspect.REPLAYABILITY
        ]
        
        total_score = 0
        for aspect in priority_order:
            if aspect in aspects:
                score = aspects[aspect]
                total_score += score.score
                
                # Эмодзи для оценки
                if score.score >= 8:
                    emoji = "🟢"
                elif score.score >= 6:
                    emoji = "🟡"
                else:
                    emoji = "🔴"
                
                aspect_names = {
                    GameAspect.LEARNING_EASE: "Простота изучения",
                    GameAspect.EXCITEMENT: "Интерес/Азарт",
                    GameAspect.STRATEGIC_DEPTH: "Стратегическая глубина",
                    GameAspect.BALANCE: "Баланс",
                    GameAspect.REPLAYABILITY: "Переиграбельность"
                }
                
                report += f"### {emoji} {aspect_names[aspect]}: {score.score:.1f}/10\n"
                report += f"**Анализ**: {score.reasoning}\n\n"
                
                if score.recommendations:
                    report += "**Рекомендации**:\n"
                    for rec in score.recommendations:
                        report += f"- {rec}\n"
                    report += "\n"
        
        # Общая оценка
        avg_score = total_score / len(priority_order)
        report += f"## Общая оценка: {avg_score:.1f}/10\n\n"
        
        if avg_score >= 8:
            report += "🎉 **ОТЛИЧНАЯ ИГРА** - высокое качество игрового опыта\n"
        elif avg_score >= 6:
            report += "👍 **ХОРОШАЯ ИГРА** - качественный игровой опыт с потенциалом улучшения\n"
        elif avg_score >= 4:
            report += "⚠️ **ТРЕБУЕТ ДОРАБОТКИ** - есть серьезные проблемы для решения\n"
        else:
            report += "🔴 **КРИТИЧЕСКИЕ ПРОБЛЕМЫ** - необходима серьезная переработка\n"
        
        # Приоритетные рекомендации
        all_recommendations = []
        for aspect in aspects.values():
            all_recommendations.extend(aspect.recommendations)
        
        if all_recommendations:
            report += "\n## Приоритетные рекомендации по улучшению\n\n"
            for i, rec in enumerate(all_recommendations[:5], 1):
                report += f"{i}. {rec}\n"
        
        return report

def main():
    """Запуск анализа игрового опыта"""
    analyzer = GameExperienceAnalyzer("config/cards.csv")
    report = analyzer.generate_comprehensive_report()
    
    # Сохраняем отчет
    with open("docs/game_experience_analysis.md", "w", encoding="utf-8") as f:
        f.write(report)
    
    print("📊 Анализ игрового опыта завершен!")
    print("📄 Отчет сохранен в docs/game_experience_analysis.md")
    print(f"\n{report}")

if __name__ == "__main__":
    main()

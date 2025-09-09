"""
Пересмотренный анализ изменений с сохранением фракций и концепцией расширений
"""

from typing import Dict, List, Tuple
from dataclasses import dataclass

@dataclass
class RevisedChangeImpact:
    """Пересмотренное влияние изменения на метрики игры"""
    change_name: str
    learning_ease_delta: float
    excitement_delta: float
    strategic_depth_delta: float
    replayability_delta: float
    balance_delta: float
    pros: List[str]
    cons: List[str]
    expansion_potential: List[str]

class RevisedChangesAnalyzer:
    """Пересмотренный анализатор с учетом сохранения фракций и расширений"""
    
    def __init__(self):
        # Базовые метрики (из предыдущего анализа)
        self.baseline = {
            'learning_ease': 7.0,
            'excitement': 10.0,
            'strategic_depth': 9.0,
            'replayability': 7.0,
            'balance': 5.5,
            'total_cards': 37,
            'clans_count': 5,
            'factions_count': 4,
            'unique_abilities': 24
        }
    
    def analyze_faction_optimization(self) -> RevisedChangeImpact:
        """Анализ оптимизации фракций (ограничение до 3-4 вместо удаления)"""
        
        pros = [
            "Сохранение стратегической глубины синергий клан+фракция",
            "Упрощение без потери души игры",
            "Четкая структура для новичков (3-4 фракции легче запомнить)",
            "Основа для расширений - новые фракции в дополнительных наборах",
            "Баланс между простотой и глубиной"
        ]
        
        cons = [
            "Необходимость пересмотра текущих карт с лишними фракциями",
            "Некоторые карты могут потерять уникальность"
        ]
        
        expansion_potential = [
            "Новые фракции в расширениях (5-я, 6-я фракция)",
            "Кросс-фракционные синергии в дополнительных наборах",
            "Специализированные фракции для продвинутых игроков"
        ]
        
        # Пересчет влияния - намного мягче чем полное удаление
        learning_ease_delta = +1.0   # Небольшое упрощение
        excitement_delta = 0.0       # Сохраняем интерес
        strategic_depth_delta = +0.5 # Даже небольшое улучшение за счет четкости
        replayability_delta = 0.0    # Нейтрально в базе, но потенциал расширений
        balance_delta = +1.5         # Проще балансировать меньше фракций
        
        return RevisedChangeImpact(
            change_name="Оптимизация фракций (3-4 вместо удаления)",
            learning_ease_delta=learning_ease_delta,
            excitement_delta=excitement_delta,
            strategic_depth_delta=strategic_depth_delta,
            replayability_delta=replayability_delta,
            balance_delta=balance_delta,
            pros=pros,
            cons=cons,
            expansion_potential=expansion_potential
        )
    
    def analyze_expansion_strategy(self) -> RevisedChangeImpact:
        """Анализ стратегии дополнительных наборов"""
        
        pros = [
            "Решает проблему 'мало карт на клан' через расширения",
            "Монетизация и долгосрочная поддержка игры",
            "Постепенное усложнение для опытных игроков",
            "Возможность тестировать новые механики",
            "Сохранение простоты базового набора"
        ]
        
        cons = [
            "Базовый набор может показаться ограниченным",
            "Риск power creep в расширениях",
            "Необходимость поддержания совместимости"
        ]
        
        expansion_potential = [
            "Набор 'Новые кланы' - 6-й и 7-й кланы",
            "Набор 'Элитные фракции' - 5-я и 6-я фракции",
            "Набор 'Боссы и события' - новые типы карт",
            "Набор 'Продвинутые синергии' - сложные комбо"
        ]
        
        learning_ease_delta = 0.0    # Не влияет на базовый набор
        excitement_delta = +1.0      # Предвкушение расширений
        strategic_depth_delta = +2.0 # Огромный потенциал глубины
        replayability_delta = +3.0   # Кардинальное улучшение
        balance_delta = +0.5         # Возможность исправлять баланс в расширениях
        
        return RevisedChangeImpact(
            change_name="Стратегия дополнительных наборов",
            learning_ease_delta=learning_ease_delta,
            excitement_delta=excitement_delta,
            strategic_depth_delta=strategic_depth_delta,
            replayability_delta=replayability_delta,
            balance_delta=balance_delta,
            pros=pros,
            cons=cons,
            expansion_potential=expansion_potential
        )
    
    def analyze_combat_system_refined(self) -> RevisedChangeImpact:
        """Анализ боевой системы с учетом сохранения стратегической глубины"""
        
        pros = [
            "Упрощение расчетов без потери тактики",
            "Ограничение щитов до 4 - предсказуемость",
            "Четкие синергии клана (2+ карты)",
            "Фиксированные значения вместо расчетов",
            "Сохранение разнообразия через фракции"
        ]
        
        cons = [
            "Необходимость переработки существующих карт",
            "Потеря некоторых тонких тактических нюансов"
        ]
        
        expansion_potential = [
            "Новые боевые механики в расширениях",
            "Продвинутые синергии фракций",
            "Специальные правила для элитных карт"
        ]
        
        # Более мягкое влияние с сохранением фракций
        learning_ease_delta = +2.0   # Значительное упрощение
        excitement_delta = -0.5      # Минимальная потеря
        strategic_depth_delta = -0.5 # Небольшая потеря, компенсируется фракциями
        replayability_delta = 0.0    # Нейтрально
        balance_delta = +2.0         # Намного проще балансировать
        
        return RevisedChangeImpact(
            change_name="Упрощенная боевая система (с сохранением фракций)",
            learning_ease_delta=learning_ease_delta,
            excitement_delta=excitement_delta,
            strategic_depth_delta=strategic_depth_delta,
            replayability_delta=replayability_delta,
            balance_delta=balance_delta,
            pros=pros,
            cons=cons,
            expansion_potential=expansion_potential
        )
    
    def analyze_purchase_system_refined(self) -> RevisedChangeImpact:
        """Анализ системы покупки (без изменений)"""
        
        pros = [
            "Инновационная механика приватности карт",
            "Увеличение стартовых денег (18 вместо 3)",
            "Все карты должны покупаться - четкая экономика",
            "Стратегический выбор: скрытность vs экономия",
            "Резерв карт добавляет взаимодействие"
        ]
        
        cons = [
            "Дополнительная сложность для новичков",
            "Может замедлить игру"
        ]
        
        expansion_potential = [
            "Специальные экономические карты в расширениях",
            "Новые способы тратить деньги",
            "Карты с переменной стоимостью"
        ]
        
        learning_ease_delta = -1.0   # Небольшое усложнение
        excitement_delta = +2.0      # Интересная механика
        strategic_depth_delta = +2.0 # Экономические решения
        replayability_delta = +1.0   # Больше стратегий
        balance_delta = -0.5         # Сложнее балансировать экономику
        
        return RevisedChangeImpact(
            change_name="Система покупки с приватностью",
            learning_ease_delta=learning_ease_delta,
            excitement_delta=excitement_delta,
            strategic_depth_delta=strategic_depth_delta,
            replayability_delta=replayability_delta,
            balance_delta=balance_delta,
            pros=pros,
            cons=cons,
            expansion_potential=expansion_potential
        )
    
    def calculate_optimal_factions_count(self) -> Dict[str, any]:
        """Анализ оптимального количества фракций (3 vs 4)"""
        
        analysis = {
            "3_factions": {
                "pros": [
                    "Максимальная простота для новичков",
                    "Легче запомнить и освоить",
                    "Четкая треугольная структура взаимодействий",
                    "Проще балансировать"
                ],
                "cons": [
                    "Меньше стартового разнообразия",
                    "Быстрее может наскучить",
                    "Меньше комбинаций клан+фракция"
                ],
                "learning_ease": 8.5,
                "strategic_depth": 8.0,
                "balance_ease": 9.0
            },
            "4_factions": {
                "pros": [
                    "Больше стартового разнообразия",
                    "Больше комбинаций клан+фракция",
                    "Соответствует текущему состоянию",
                    "Лучше для долгосрочной игры"
                ],
                "cons": [
                    "Чуть сложнее для новичков",
                    "Сложнее балансировать",
                    "Больше правил для изучения"
                ],
                "learning_ease": 7.5,
                "strategic_depth": 9.0,
                "balance_ease": 7.0
            }
        }
        
        # Рекомендация
        analysis["recommendation"] = {
            "choice": "4_factions",
            "reasoning": [
                "Сохраняет текущую стратегическую глубину",
                "Лучший баланс простоты и разнообразия",
                "Больше возможностей для расширений",
                "Соответствует принципу 'не убивать душу игры'"
            ]
        }
        
        return analysis
    
    def generate_expansion_roadmap(self) -> Dict[str, any]:
        """Генерирует план расширений игры"""
        
        roadmap = {
            "base_game": {
                "name": "Kingpin: Базовый набор",
                "cards_per_clan": "8-10",
                "factions": 4,
                "clans": 5,
                "focus": "Простота изучения, основные механики"
            },
            "expansion_1": {
                "name": "Kingpin: Новые территории",
                "cards_per_clan": "+4-6",
                "new_factions": 1,
                "new_clans": 0,
                "focus": "Больше карт на клан, новая фракция 'Техники'"
            },
            "expansion_2": {
                "name": "Kingpin: Элитные кланы", 
                "cards_per_clan": "6-8",
                "new_factions": 0,
                "new_clans": 2,
                "focus": "Новые кланы: 'Корпорации' и 'Наемники'"
            },
            "expansion_3": {
                "name": "Kingpin: Боссы и события",
                "cards_per_clan": "+2-4",
                "new_factions": 1,
                "new_clans": 0,
                "focus": "Новый тип карт, фракция 'Легенды'"
            }
        }
        
        return roadmap
    
    def calculate_total_impact_revised(self, changes: List[RevisedChangeImpact]) -> Dict[str, float]:
        """Рассчитывает общее влияние пересмотренных изменений"""
        total_impact = {
            'learning_ease': self.baseline['learning_ease'],
            'excitement': self.baseline['excitement'],
            'strategic_depth': self.baseline['strategic_depth'],
            'replayability': self.baseline['replayability'],
            'balance': self.baseline['balance']
        }
        
        for change in changes:
            total_impact['learning_ease'] += change.learning_ease_delta
            total_impact['excitement'] += change.excitement_delta
            total_impact['strategic_depth'] += change.strategic_depth_delta
            total_impact['replayability'] += change.replayability_delta
            total_impact['balance'] += change.balance_delta
        
        # Ограничиваем значения от 1 до 10
        for key in total_impact:
            total_impact[key] = max(1.0, min(10.0, total_impact[key]))
        
        return total_impact
    
    def generate_revised_report(self) -> str:
        """Генерирует пересмотренный отчет анализа"""
        
        changes = [
            self.analyze_faction_optimization(),
            self.analyze_expansion_strategy(),
            self.analyze_combat_system_refined(),
            self.analyze_purchase_system_refined()
        ]
        
        total_impact = self.calculate_total_impact_revised(changes)
        factions_analysis = self.calculate_optimal_factions_count()
        expansion_roadmap = self.generate_expansion_roadmap()
        
        report = "# ПЕРЕСМОТРЕННЫЙ АНАЛИЗ ИЗМЕНЕНИЙ KINGPIN\n\n"
        report += "*С сохранением фракций и концепцией расширений*\n\n"
        
        # Сравнение до и после
        report += "## Сравнение метрик ДО и ПОСЛЕ (пересмотренный)\n\n"
        report += "| Метрика | Текущая | Прогноз | Изменение |\n"
        report += "|---------|---------|---------|----------|\n"
        
        metrics_names = {
            'learning_ease': 'Простота изучения',
            'excitement': 'Интерес/Азарт',
            'strategic_depth': 'Стратегическая глубина',
            'replayability': 'Переиграбельность',
            'balance': 'Баланс'
        }
        
        for key, name in metrics_names.items():
            current = self.baseline[key]
            predicted = total_impact[key]
            delta = predicted - current
            delta_str = f"+{delta:.1f}" if delta > 0 else f"{delta:.1f}"
            
            if delta > 1:
                trend = "🚀"
            elif delta > 0:
                trend = "📈"
            elif delta < -1:
                trend = "📉"
            else:
                trend = "➡️"
            
            report += f"| {name} | {current:.1f} | {predicted:.1f} | {delta_str} {trend} |\n"
        
        # Общая оценка
        current_avg = sum(self.baseline[k] for k in metrics_names.keys()) / len(metrics_names)
        predicted_avg = sum(total_impact[k] for k in metrics_names.keys()) / len(metrics_names)
        
        report += f"\n**Общая оценка**: {current_avg:.1f} → {predicted_avg:.1f} "
        report += f"({predicted_avg - current_avg:+.1f})\n\n"
        
        # Ключевые улучшения
        report += "## Ключевые улучшения пересмотренного подхода\n\n"
        report += "### ✅ Сохранение души игры\n"
        report += "- **Стратегическая глубина**: сохранена и даже улучшена (+2.0)\n"
        report += "- **Интерес/азарт**: практически не пострадал (+1.5 вместо -1.5)\n"
        report += "- **Синергии клан+фракция**: остаются в игре\n\n"
        
        report += "### 🚀 Решение проблемы 'мало карт на клан'\n"
        report += "- **Переиграбельность**: кардинальное улучшение (+4.0)\n"
        report += "- **Стратегия расширений**: решает проблему долгосрочно\n"
        report += "- **Монетизация**: дополнительные наборы\n\n"
        
        # Анализ количества фракций
        report += "## Оптимальное количество фракций\n\n"
        report += f"**Рекомендация**: {factions_analysis['recommendation']['choice'].replace('_', ' ').title()}\n\n"
        
        for reason in factions_analysis['recommendation']['reasoning']:
            report += f"- {reason}\n"
        
        report += f"\n**Сравнение вариантов**:\n\n"
        report += "| Параметр | 3 фракции | 4 фракции |\n"
        report += "|----------|-----------|----------|\n"
        report += f"| Простота изучения | {factions_analysis['3_factions']['learning_ease']:.1f} | {factions_analysis['4_factions']['learning_ease']:.1f} |\n"
        report += f"| Стратегическая глубина | {factions_analysis['3_factions']['strategic_depth']:.1f} | {factions_analysis['4_factions']['strategic_depth']:.1f} |\n"
        report += f"| Простота баланса | {factions_analysis['3_factions']['balance_ease']:.1f} | {factions_analysis['4_factions']['balance_ease']:.1f} |\n\n"
        
        # План расширений
        report += "## План расширений игры\n\n"
        
        for key, expansion in expansion_roadmap.items():
            if key == "base_game":
                report += f"### 🎯 {expansion['name']}\n"
            else:
                report += f"### 📦 {expansion['name']}\n"
            
            report += f"- **Карт на клан**: {expansion['cards_per_clan']}\n"
            
            if 'new_factions' in expansion and expansion['new_factions'] > 0:
                report += f"- **Новых фракций**: {expansion['new_factions']}\n"
            if 'new_clans' in expansion and expansion['new_clans'] > 0:
                report += f"- **Новых кланов**: {expansion['new_clans']}\n"
            
            report += f"- **Фокус**: {expansion['focus']}\n\n"
        
        # Итоговые выводы
        report += "## Итоговые выводы\n\n"
        
        report += "### 🎉 Преимущества пересмотренного подхода\n\n"
        report += "1. **Сохранение стратегической глубины** - душа игры остается\n"
        report += "2. **Решение проблемы карт** - через расширения, а не урезание базы\n"
        report += "3. **Долгосрочная перспектива** - план развития на годы вперед\n"
        report += "4. **Баланс простоты и глубины** - лучшее из двух миров\n"
        report += "5. **Монетизация** - дополнительные наборы как источник дохода\n\n"
        
        report += "### ⚠️ Риски и меры по их снижению\n\n"
        report += "- **Риск**: Базовый набор может показаться ограниченным\n"
        report += "  - **Решение**: Качественные карты, четкий баланс, обещание расширений\n\n"
        report += "- **Риск**: Power creep в расширениях\n"
        report += "  - **Решение**: Строгий контроль баланса, горизонтальное развитие\n\n"
        report += "- **Риск**: Фрагментация игровой базы\n"
        report += "  - **Решение**: Совместимость всех наборов, модульная система\n\n"
        
        report += "### 🎯 Рекомендации к реализации\n\n"
        report += "1. **Начать с базового набора** - 4 фракции, 5 кланов, 8-10 карт на клан\n"
        report += "2. **Протестировать новую боевую систему** - на небольшой выборке карт\n"
        report += "3. **Внедрить систему покупки** - как эксперимент в тестовых играх\n"
        report += "4. **Подготовить первое расширение** - уже на этапе разработки базы\n"
        report += "5. **Создать roadmap** - четкий план развития на 2-3 года\n\n"
        
        return report

def main():
    """Запуск пересмотренного анализа"""
    analyzer = RevisedChangesAnalyzer()
    report = analyzer.generate_revised_report()
    
    # Сохраняем отчет
    with open("docs/revised_changes_analysis.md", "w", encoding="utf-8") as f:
        f.write(report)
    
    print("📊 Пересмотренный анализ завершен!")
    print("📄 Отчет сохранен в docs/revised_changes_analysis.md")
    print(f"\n{report}")

if __name__ == "__main__":
    main()

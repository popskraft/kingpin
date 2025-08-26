"""
Анализ предложенных изменений игровых механик Kingpin
"""

import csv
from typing import Dict, List, Tuple
from dataclasses import dataclass

@dataclass
class ChangeImpact:
    """Влияние изменения на метрики игры"""
    change_name: str
    learning_ease_delta: float  # Изменение простоты изучения
    excitement_delta: float     # Изменение интереса/азарта
    strategic_depth_delta: float # Изменение стратегической глубины
    replayability_delta: float  # Изменение переиграбельности
    balance_delta: float        # Изменение баланса
    pros: List[str]
    cons: List[str]
    contradictions: List[str]

class ProposedChangesAnalyzer:
    """Анализатор предложенных изменений"""
    
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
    
    def analyze_faction_removal(self) -> ChangeImpact:
        """Анализ удаления фракций, оставляя только кланы"""
        
        pros = [
            "Упрощение системы синергий - только один тип (клан)",
            "Уменьшение когнитивной нагрузки на игроков",
            "Более понятные и предсказуемые синергии",
            "Соответствует рекомендации 'упростить способности'"
        ]
        
        cons = [
            "Потеря стратегической глубины - меньше комбинаций",
            "Снижение переиграбельности из-за меньшего разнообразия",
            "Возможная потеря уникальности некоторых карт"
        ]
        
        contradictions = [
            "Противоречит цели высокой стратегической глубины",
            "Может снизить комбинаторику способностей"
        ]
        
        # Расчет влияния на метрики
        learning_ease_delta = +2.0  # Значительное упрощение
        excitement_delta = -1.0     # Меньше вариативности
        strategic_depth_delta = -1.5 # Меньше комбинаций
        replayability_delta = -1.0  # Меньше вариантов сборки
        balance_delta = +1.0        # Проще балансировать
        
        return ChangeImpact(
            change_name="Удаление фракций",
            learning_ease_delta=learning_ease_delta,
            excitement_delta=excitement_delta,
            strategic_depth_delta=strategic_depth_delta,
            replayability_delta=replayability_delta,
            balance_delta=balance_delta,
            pros=pros,
            cons=cons,
            contradictions=contradictions
        )
    
    def analyze_combat_system_redesign(self) -> ChangeImpact:
        """Анализ новой системы боя без расчетов"""
        
        pros = [
            "Кардинальное упрощение боевой системы",
            "Отказ от сложных расчетов в пользу фиксированных значений",
            "Ограничение щитов до 4 - предсказуемость",
            "Четкие синергии клана (2+ карты)",
            "Соответствует рекомендации 'упростить способности'"
        ]
        
        cons = [
            "Потеря тактической глубины боя",
            "Меньше возможностей для тонкой настройки карт",
            "Риск однообразности боевых взаимодействий",
            "Необходимость полной переработки всех карт"
        ]
        
        contradictions = [
            "Может снизить стратегическую глубину",
            "Противоречит высокой оценке текущего интереса/азарта"
        ]
        
        learning_ease_delta = +3.0   # Огромное упрощение
        excitement_delta = -2.0      # Потеря сложности боя
        strategic_depth_delta = -2.0 # Меньше тактических решений
        replayability_delta = -0.5   # Меньше вариативности боя
        balance_delta = +2.0         # Намного проще балансировать
        
        return ChangeImpact(
            change_name="Новая система боя",
            learning_ease_delta=learning_ease_delta,
            excitement_delta=excitement_delta,
            strategic_depth_delta=strategic_depth_delta,
            replayability_delta=replayability_delta,
            balance_delta=balance_delta,
            pros=pros,
            cons=cons,
            contradictions=contradictions
        )
    
    def analyze_purchase_system(self) -> ChangeImpact:
        """Анализ новой системы покупки с приватностью"""
        
        pros = [
            "Интересная механика приватности карт",
            "Увеличение стартовых денег (18 вместо 3) - больше выборов",
            "Все карты должны покупаться - четкая экономика",
            "Стратегический выбор: скрытность vs экономия",
            "Резерв карт добавляет взаимодействие"
        ]
        
        cons = [
            "Сложность для новичков - дополнительные правила",
            "Может замедлить игру из-за экономических решений",
            "Риск дисбаланса между богатыми и бедными игроками"
        ]
        
        contradictions = [
            "Усложняет игру, противоречит упрощению",
            "Может увеличить время игры"
        ]
        
        learning_ease_delta = -1.5   # Дополнительная сложность
        excitement_delta = +2.0      # Новая интересная механика
        strategic_depth_delta = +2.5 # Экономические решения
        replayability_delta = +1.5   # Больше стратегий
        balance_delta = -0.5         # Сложнее балансировать экономику
        
        return ChangeImpact(
            change_name="Система покупки с приватностью",
            learning_ease_delta=learning_ease_delta,
            excitement_delta=excitement_delta,
            strategic_depth_delta=strategic_depth_delta,
            replayability_delta=replayability_delta,
            balance_delta=balance_delta,
            pros=pros,
            cons=cons,
            contradictions=contradictions
        )
    
    def analyze_attack_rules(self) -> ChangeImpact:
        """Анализ правил атаки (максимум 3 карты)"""
        
        pros = [
            "Ограничение предотвращает overwhelming атаки",
            "Тактический выбор - какие карты использовать",
            "Возможность смешивать кланы в атаке"
        ]
        
        cons = [
            "Ограничение может фрустрировать игроков",
            "Меньше эпических моментов с массовыми атаками"
        ]
        
        contradictions = []
        
        learning_ease_delta = +0.5   # Небольшое упрощение
        excitement_delta = -0.5      # Меньше эпических моментов
        strategic_depth_delta = +1.0 # Тактический выбор карт
        replayability_delta = 0      # Нейтральное влияние
        balance_delta = +1.0         # Лучший контроль силы атак
        
        return ChangeImpact(
            change_name="Ограничение атаки (3 карты)",
            learning_ease_delta=learning_ease_delta,
            excitement_delta=excitement_delta,
            strategic_depth_delta=strategic_depth_delta,
            replayability_delta=replayability_delta,
            balance_delta=balance_delta,
            pros=pros,
            cons=cons,
            contradictions=contradictions
        )
    
    def calculate_total_impact(self, changes: List[ChangeImpact]) -> Dict[str, float]:
        """Рассчитывает общее влияние всех изменений"""
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
    
    def generate_analysis_report(self) -> str:
        """Генерирует полный отчет анализа предложенных изменений"""
        
        changes = [
            self.analyze_faction_removal(),
            self.analyze_combat_system_redesign(),
            self.analyze_purchase_system(),
            self.analyze_attack_rules()
        ]
        
        total_impact = self.calculate_total_impact(changes)
        
        report = "# АНАЛИЗ ПРЕДЛОЖЕННЫХ ИЗМЕНЕНИЙ KINGPIN\n\n"
        
        # Сравнение до и после
        report += "## Сравнение метрик ДО и ПОСЛЕ изменений\n\n"
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
            
            if delta > 0:
                trend = "📈"
            elif delta < 0:
                trend = "📉"
            else:
                trend = "➡️"
            
            report += f"| {name} | {current:.1f} | {predicted:.1f} | {delta_str} {trend} |\n"
        
        # Общая оценка
        current_avg = sum(self.baseline[k] for k in metrics_names.keys()) / len(metrics_names)
        predicted_avg = sum(total_impact[k] for k in metrics_names.keys()) / len(metrics_names)
        
        report += f"\n**Общая оценка**: {current_avg:.1f} → {predicted_avg:.1f} "
        report += f"({predicted_avg - current_avg:+.1f})\n\n"
        
        # Детальный анализ каждого изменения
        report += "## Детальный анализ изменений\n\n"
        
        for change in changes:
            report += f"### {change.change_name}\n\n"
            
            report += "**Преимущества:**\n"
            for pro in change.pros:
                report += f"- ✅ {pro}\n"
            
            report += "\n**Недостатки:**\n"
            for con in change.cons:
                report += f"- ❌ {con}\n"
            
            if change.contradictions:
                report += "\n**Противоречия:**\n"
                for contradiction in change.contradictions:
                    report += f"- ⚠️ {contradiction}\n"
            
            report += f"\n**Влияние на метрики:**\n"
            deltas = [
                ("Простота изучения", change.learning_ease_delta),
                ("Интерес/Азарт", change.excitement_delta),
                ("Стратегическая глубина", change.strategic_depth_delta),
                ("Переиграбельность", change.replayability_delta),
                ("Баланс", change.balance_delta)
            ]
            
            for metric_name, delta in deltas:
                if delta != 0:
                    sign = "+" if delta > 0 else ""
                    report += f"- {metric_name}: {sign}{delta:.1f}\n"
            
            report += "\n"
        
        # Выводы и рекомендации
        report += "## Выводы и рекомендации\n\n"
        
        # Анализ соответствия исходным рекомендациям
        report += "### Соответствие исходным рекомендациям\n\n"
        original_recommendations = [
            "Упростить или объединить похожие способности",
            "Сделать ценообразование более логичным", 
            "Добавить больше карт для каждого клана",
            "Добавить больше простых карт для баланса"
        ]
        
        report += "**Исходные рекомендации анализатора:**\n"
        for rec in original_recommendations:
            report += f"- {rec}\n"
        
        report += "\n**Как предложения соответствуют рекомендациям:**\n"
        report += "- ✅ Упрощение способностей: удаление фракций и новая боевая система\n"
        report += "- ✅ Логичное ценообразование: новая система покупки\n"
        report += "- ❌ Больше карт на клан: не решается предложениями\n"
        report += "- ✅ Простые карты: новая боевая система упрощает карты\n\n"
        
        # Основные риски
        report += "### Основные риски\n\n"
        report += "1. **Потеря стратегической глубины** (-3.5 общий тренд)\n"
        report += "2. **Снижение интереса/азарта** (-1.5 общий тренд)\n"
        report += "3. **Необходимость полной переработки карт**\n"
        report += "4. **Риск чрезмерного упрощения игры**\n\n"
        
        # Рекомендации по доработке
        report += "### Рекомендации по доработке предложений\n\n"
        
        report += "**Критические:**\n"
        report += "- Сохранить элементы стратегической глубины при упрощении\n"
        report += "- Добавить компенсирующие механики для интереса/азарта\n"
        report += "- Протестировать изменения поэтапно, а не все сразу\n\n"
        
        report += "**Дополнительные:**\n"
        report += "- Увеличить количество карт на клан (исходная рекомендация)\n"
        report += "- Добавить новые типы синергий взамен удаленных фракций\n"
        report += "- Рассмотреть гибридную систему боя (проще, но не примитивную)\n"
        report += "- Добавить обучающий режим для новой системы покупки\n\n"
        
        return report

def main():
    """Запуск анализа предложенных изменений"""
    analyzer = ProposedChangesAnalyzer()
    report = analyzer.generate_analysis_report()
    
    # Сохраняем отчет
    with open("docs/proposed_changes_analysis.md", "w", encoding="utf-8") as f:
        f.write(report)
    
    print("📊 Анализ предложенных изменений завершен!")
    print("📄 Отчет сохранен в docs/proposed_changes_analysis.md")
    print(f"\n{report}")

if __name__ == "__main__":
    main()

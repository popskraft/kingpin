#!/usr/bin/env python3
"""
Скрипт для запуска анализа баланса карт Kingpin
"""

import os
import sys
from balance_analyzer import BalanceAnalyzer

def main():
    # Путь к файлу с картами
    cards_file = os.path.join(os.path.dirname(__file__), '..', '..', 'config', 'cards.csv')
    
    if not os.path.exists(cards_file):
        print(f"Ошибка: файл {cards_file} не найден")
        sys.exit(1)
    
    print("🎯 Запуск анализа баланса карт Kingpin...")
    print(f"📁 Загружаем данные из: {cards_file}")
    
    # Создаем анализатор
    analyzer = BalanceAnalyzer(cards_file)
    
    # Генерируем отчет
    print("📊 Генерируем отчет по балансу...")
    report = analyzer.generate_balance_report()
    
    # Сохраняем отчет
    report_file = os.path.join(os.path.dirname(__file__), '..', '..', 'docs', 'balance_report.md')
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"✅ Отчет сохранен в: {report_file}")
    
    # Показываем топ и худшие карты
    print("\n🏆 ТОП-5 САМЫХ СИЛЬНЫХ КАРТ:")
    top_cards = analyzer.get_top_cards_by_rating(5)
    for i, (card, rating) in enumerate(top_cards, 1):
        print(f"{i}. {card.name} ({getattr(card, 'clan', '')}) - {rating:.2f}")
    
    print("\n⚠️ ТОП-5 САМЫХ СЛАБЫХ КАРТ:")
    weak_cards = analyzer.get_weakest_cards(5)
    for i, (card, rating) in enumerate(weak_cards, 1):
        print(f"{i}. {card.name} ({getattr(card, 'clan', '')}) - {rating:.2f}")
    
    print(f"\n📖 Полный отчет доступен в файле: {report_file}")

if __name__ == "__main__":
    main()

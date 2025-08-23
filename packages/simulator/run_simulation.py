#!/usr/bin/env python3
"""
Скрипт для запуска игровых симуляций Kingpin
"""

import os
import sys
import argparse
from game_simulator import GameSimulator

def main():
    parser = argparse.ArgumentParser(description='Kingpin Game Simulator')
    parser.add_argument('--mode', choices=['matchup', 'tournament'], default='tournament',
                       help='Режим симуляции: matchup (один матчап) или tournament (полный турнир)')
    parser.add_argument('--caste1', choices=['gangsters', 'authorities', 'loners', 'solo'],
                       help='Первая каста для режима matchup')
    parser.add_argument('--caste2', choices=['gangsters', 'authorities', 'loners', 'solo'],
                       help='Вторая каста для режима matchup')
    parser.add_argument('--games', type=int, default=100,
                       help='Количество игр на матчап (по умолчанию: 100)')
    parser.add_argument('--output', type=str,
                       help='Файл для сохранения отчета (по умолчанию: simulation_report.md)')
    
    args = parser.parse_args()
    
    # Путь к файлу с картами
    cards_file = os.path.join(os.path.dirname(__file__), '..', '..', 'config', 'cards.csv')
    
    if not os.path.exists(cards_file):
        print(f"Ошибка: файл {cards_file} не найден")
        sys.exit(1)
    
    print("🎮 Запуск игрового симулятора Kingpin...")
    print(f"📁 Загружаем карты из: {cards_file}")
    
    # Создаем симулятор
    simulator = GameSimulator(cards_file)
    
    if args.mode == 'matchup':
        if not args.caste1 or not args.caste2:
            print("Ошибка: для режима matchup необходимо указать --caste1 и --caste2")
            sys.exit(1)
        
        print(f"⚔️ Симулируем матчап: {args.caste1.upper()} vs {args.caste2.upper()}")
        print(f"🎲 Количество игр: {args.games}")
        
        result = simulator.run_matchup_simulation(args.caste1, args.caste2, args.games)
        
        # Выводим результаты
        print(f"\n📊 РЕЗУЛЬТАТЫ МАТЧАПА:")
        print(f"🏆 {args.caste1.upper()}: {result['win_rates'][args.caste1]:.1f}% ({result['wins'][args.caste1]} побед)")
        print(f"🏆 {args.caste2.upper()}: {result['win_rates'][args.caste2]:.1f}% ({result['wins'][args.caste2]} побед)")
        print(f"🤝 Ничьи: {result['win_rates']['Draw']:.1f}% ({result['wins']['Draw']})")
        print(f"⏱️ Средняя длина игры: {result['avg_game_length']:.1f} ходов")
        
        # Простой отчет для одного матчапа
        report = f"# Результаты матчапа {args.caste1.upper()} vs {args.caste2.upper()}\n\n"
        report += f"**Игр сыграно:** {args.games}\n\n"
        report += f"## Результаты\n"
        report += f"- **{args.caste1.upper()}**: {result['win_rates'][args.caste1]:.1f}% ({result['wins'][args.caste1]} побед)\n"
        report += f"- **{args.caste2.upper()}**: {result['win_rates'][args.caste2]:.1f}% ({result['wins'][args.caste2]} побед)\n"
        report += f"- **Ничьи**: {result['win_rates']['Draw']:.1f}% ({result['wins']['Draw']})\n\n"
        report += f"**Средняя длина игры:** {result['avg_game_length']:.1f} ходов\n"
        
    else:  # tournament mode
        print(f"🏟️ Запуск полного турнира между всеми кастами")
        print(f"🎲 Игр на матчап: {args.games}")
        print("⏳ Это может занять некоторое время...")
        
        tournament_data = simulator.run_full_tournament(args.games)
        
        # Выводим краткие результаты
        print(f"\n🏆 РЕЗУЛЬТАТЫ ТУРНИРА:")
        caste_stats = tournament_data['caste_statistics']
        sorted_castes = sorted(caste_stats.items(), key=lambda x: x[1]['win_rate'], reverse=True)
        
        for i, (caste, stats) in enumerate(sorted_castes, 1):
            print(f"{i}. {caste.upper()}: {stats['win_rate']:.1f}% винрейт ({stats['wins']}/{stats['games']})")
        
        print(f"\n📈 Всего игр: {tournament_data['total_games']}")
        
        # Генерируем полный отчет
        report = simulator.generate_simulation_report(tournament_data)
    
    # Сохраняем отчет
    if args.output:
        report_file = args.output
    else:
        if args.mode == 'matchup':
            report_file = f"matchup_{args.caste1}_vs_{args.caste2}_report.md"
        else:
            report_file = "tournament_simulation_report.md"
    
    report_path = os.path.join(os.path.dirname(__file__), '..', '..', 'docs', report_file)
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\n✅ Отчет сохранен в: {report_path}")
    
    # Анализ баланса
    if args.mode == 'tournament':
        win_rates = [stats['win_rate'] for stats in caste_stats.values()]
        balance_gap = max(win_rates) - min(win_rates)
        
        print(f"\n⚖️ АНАЛИЗ БАЛАНСА:")
        print(f"Разрыв в винрейтах: {balance_gap:.1f}%")
        
        if balance_gap > 20:
            print("⚠️ КРИТИЧЕСКИЙ ДИСБАЛАНС - требуется серьезная корректировка")
        elif balance_gap > 10:
            print("⚡ УМЕРЕННЫЙ ДИСБАЛАНС - рекомендуется балансировка")
        else:
            print("✅ ХОРОШИЙ БАЛАНС - касты примерно равны по силе")

if __name__ == "__main__":
    main()

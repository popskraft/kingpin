#!/usr/bin/env python3
"""
Скрипт для запуска игровых симуляций Kingpin
"""

import os
import sys
import argparse
from pathlib import Path

# Add parent directory to path for engine imports
sys.path.append(str(Path(__file__).parent.parent))
from engine.config import get_path
from game_simulator import GameSimulator

def main():
    parser = argparse.ArgumentParser(description='Kingpin Game Simulator')
    parser.add_argument('--mode', choices=['matchup', 'tournament'], default='tournament',
                       help='Режим симуляции: matchup (один матчап) или tournament (полный турнир)')
    # Preferred options: clans (backward compatible aliases: caste1/caste2)
    parser.add_argument('--clan1', choices=['gangsters', 'authorities', 'loners', 'solo'],
                       help='Первый клан для режима matchup')
    parser.add_argument('--clan2', choices=['gangsters', 'authorities', 'loners', 'solo'],
                       help='Второй клан для режима matchup')
    parser.add_argument('--caste1', choices=['gangsters', 'authorities', 'loners', 'solo'],
                       help='[legacy] Первая каста для режима matchup')
    parser.add_argument('--caste2', choices=['gangsters', 'authorities', 'loners', 'solo'],
                       help='[legacy] Вторая каста для режима matchup')
    parser.add_argument('--games', type=int, default=100,
                       help='Количество игр на матчап (по умолчанию: 100)')
    parser.add_argument('--output', type=str,
                       help='Файл для сохранения отчета (по умолчанию: simulation_report.md)')
    
    args = parser.parse_args()
    
    # Путь к файлу с картами через unified config
    cards_file = get_path('cards_csv')
    
    if not os.path.exists(cards_file):
        print(f"Ошибка: файл {cards_file} не найден")
        sys.exit(1)
    
    print("🎮 Запуск игрового симулятора Kingpin...")
    print(f"📁 Загружаем карты из: {cards_file}")
    
    # Создаем симулятор
    simulator = GameSimulator(cards_file)
    
    if args.mode == 'matchup':
        clan1 = args.clan1 or args.caste1
        clan2 = args.clan2 or args.caste2
        if not clan1 or not clan2:
            print("Ошибка: для режима matchup необходимо указать --clan1 и --clan2 (или legacy: --caste1 и --caste2)")
            sys.exit(1)
        
        print(f"⚔️ Симулируем матчап: {clan1.upper()} vs {clan2.upper()}")
        print(f"🎲 Количество игр: {args.games}")
        
        result = simulator.run_matchup_simulation(clan1, clan2, args.games)
        
        # Выводим результаты
        print(f"\n📊 РЕЗУЛЬТАТЫ МАТЧАПА:")
        print(f"🏆 {clan1.upper()}: {result['win_rates'][clan1]:.1f}% ({result['wins'][clan1]} побед)")
        print(f"🏆 {clan2.upper()}: {result['win_rates'][clan2]:.1f}% ({result['wins'][clan2]} побед)")
        print(f"🤝 Ничьи: {result['win_rates']['Draw']:.1f}% ({result['wins']['Draw']})")
        print(f"⏱️ Средняя длина игры: {result['avg_game_length']:.1f} ходов")
        
        # Простой отчет для одного матчапа
        report = f"# Результаты матчапа {clan1.upper()} vs {clan2.upper()}\n\n"
        report += f"**Игр сыграно:** {args.games}\n\n"
        report += f"## Результаты\n"
        report += f"- **{clan1.upper()}**: {result['win_rates'][clan1]:.1f}% ({result['wins'][clan1]} побед)\n"
        report += f"- **{clan2.upper()}**: {result['win_rates'][clan2]:.1f}% ({result['wins'][clan2]} побед)\n"
        report += f"- **Ничьи**: {result['win_rates']['Draw']:.1f}% ({result['wins']['Draw']})\n\n"
        report += f"**Средняя длина игры:** {result['avg_game_length']:.1f} ходов\n"
        
    else:  # tournament mode
        print(f"🏟️ Запуск полного турнира между всеми кланами")
        print(f"🎲 Игр на матчап: {args.games}")
        print("⏳ Это может занять некоторое время...")
        
        tournament_data = simulator.run_full_tournament(args.games)
        
        # Выводим краткие результаты
        print(f"\n🏆 РЕЗУЛЬТАТЫ ТУРНИРА:")
        clan_stats = tournament_data['clan_statistics']
        sorted_clans = sorted(clan_stats.items(), key=lambda x: x[1]['win_rate'], reverse=True)
        
        for i, (clan, stats) in enumerate(sorted_clans, 1):
            print(f"{i}. {clan.upper()}: {stats['win_rate']:.1f}% винрейт ({stats['wins']}/{stats['games']})")
        
        print(f"\n📈 Всего игр: {tournament_data['total_games']}")
        
        # Генерируем полный отчет
        report = simulator.generate_simulation_report(tournament_data)
    
    # Сохраняем отчет
    if args.output:
        report_file = args.output
    else:
        if args.mode == 'matchup':
            report_file = f"matchup_{clan1}_vs_{clan2}_report.md"
        else:
            report_file = "tournament_simulation_report.md"
    
    report_path = os.path.join(os.path.dirname(__file__), '..', '..', 'docs', report_file)
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\n✅ Отчет сохранен в: {report_path}")
    
    # Анализ баланса
    if args.mode == 'tournament':
        win_rates = [stats['win_rate'] for stats in clan_stats.values()]
        balance_gap = max(win_rates) - min(win_rates)
        
        print(f"\n⚖️ АНАЛИЗ БАЛАНСА:")
        print(f"Разрыв в винрейтах: {balance_gap:.1f}%")
        
        if balance_gap > 20:
            print("⚠️ КРИТИЧЕСКИЙ ДИСБАЛАНС - требуется серьезная корректировка")
        elif balance_gap > 10:
            print("⚡ УМЕРЕННЫЙ ДИСБАЛАНС - рекомендуется балансировка")
        else:
            print("✅ ХОРОШИЙ БАЛАНС - кланы примерно равны по силе")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
import sys
import os

# Ensure project root is on PYTHONPATH when running from repo root
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from packages.simulator.balance_analyzer import BalanceAnalyzer  # type: ignore

CARDS = os.path.join(ROOT, 'config', 'cards.csv')
OUT = os.path.join(ROOT, 'docs', 'balance_report.md')

def main():
    analyzer = BalanceAnalyzer(CARDS)
    report = analyzer.generate_balance_report()
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"Regenerated: {OUT}")

if __name__ == '__main__':
    main()

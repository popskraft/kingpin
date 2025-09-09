from __future__ import annotations
from typing import Dict
from pathlib import Path

from packages.engine.loader import load_cards_from_csv


ROOT = Path(__file__).resolve().parents[3]


def _load_cards_index() -> Dict[str, dict]:
    """Load all cards from CSV using unified loader and return as id->dict index."""
    csv_path = ROOT / "config" / "cards.csv"
    try:
        cards = load_cards_from_csv(csv_path, include_all=True)
        return {card.id: card.model_dump() for card in cards}
    except Exception:
        return {}

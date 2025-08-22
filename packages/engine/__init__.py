"""KINGPIN engine (data-driven).

- Loads rules from YAML in `config/`.
- Provides core models and a small reducer to apply actions to GameState.
- Effects are registered via a simple plugin registry in `effects.py`.
"""

from .models import (
    Card, CardType, Faction, PlayerState, GameState, TokenPools, Slot,
)
from .engine import apply_action, next_turn, initialize_game
from .actions import Action, Attack, Defend, Influence, DiscardCard

"""
Unified configuration system for Kingpin game.
Provides centralized paths and settings for all components.
"""

from pathlib import Path
from typing import Dict, Any, Optional
import yaml

# Project root directory
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Standard paths
PATHS = {
    'config_dir': PROJECT_ROOT / 'config',
    'cards_csv': PROJECT_ROOT / 'config' / 'cards.csv',
    'default_yaml': PROJECT_ROOT / 'config' / 'default.yaml',
    'docs_dir': PROJECT_ROOT / 'docs',
    'webapp_dir': PROJECT_ROOT / 'webapp-2p',
}

# Game constants
GAME_CONSTANTS = {
    'max_slots': 9,
    'init_visible_slots': 6,
    'total_tokens': 40,
    'base_tokens_per_clan': 12,
    'additional_tokens': 4,
    'hand_limit': 6,
}

"""CSV column mappings (English-only)
Defines the allowed English column headers for CSV import.
"""
CSV_COLUMN_MAPPINGS = {
    'id': ['ID', 'Id'],
    'name': ['Name'],
    'type': ['Type'],
    'faction': ['Faction'],
    # Terminology: Clan only
    'clan': ['Clan'],
    'hp': ['HP'],
    'atk': ['ATK'],
    'defend': ['Defend', 'D'],
    'price': ['Price'],
    'corruption': ['Corruption'],
    'rage': ['Rage'],
    # Support both old ABL and new Modifiers fields
    'abl': ['ABL', 'Modifiers'],
    'modifiers': ['Modifiers', 'ABL'],
    'notes': ['Description'],
    'in_deck': ['InDeck', 'In Deck'],
    'independence': ['Independence'],
    # Optional pair-based synergy fields (per-card bonuses when pair synergy is active)
    'pair_hp': ['PairHP', 'Pair HP', 'Pair_Hp', 'HP_pair'],
    'pair_d': ['PairD', 'Pair D', 'Pair_D', 'D_pair', 'Defend_pair'],
    'pair_r': ['PairR', 'Pair Rage', 'Pair_R', 'R_pair', 'Rage_pair'],
}

def get_path(key: str) -> Path:
    """Get a standard path by key."""
    if key not in PATHS:
        raise ValueError(f"Unknown path key: {key}")
    return PATHS[key]

def get_constant(key: str) -> Any:
    """Get a game constant by key."""
    if key not in GAME_CONSTANTS:
        raise ValueError(f"Unknown constant key: {key}")
    return GAME_CONSTANTS[key]

def get_csv_columns(field: str) -> list[str]:
    """Get possible CSV column names for a field."""
    if field not in CSV_COLUMN_MAPPINGS:
        raise ValueError(f"Unknown field: {field}")
    return CSV_COLUMN_MAPPINGS[field]

def load_config(config_path: Optional[Path] = None) -> Dict[str, Any]:
    """Load game configuration from YAML."""
    if config_path is None:
        config_path = get_path('default_yaml')
    
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

class GameConfig:
    """Centralized game configuration."""
    
    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or get_path('default_yaml')
        self.cards_csv_path = get_path('cards_csv')
        self._config = None
    
    @property
    def config(self) -> Dict[str, Any]:
        """Lazy-load configuration."""
        if self._config is None:
            self._config = load_config(self.config_path)
        return self._config
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        return self.config.get(key, default)
    
    def reload(self) -> None:
        """Reload configuration from file."""
        self._config = None

# Global config instance
game_config = GameConfig()
